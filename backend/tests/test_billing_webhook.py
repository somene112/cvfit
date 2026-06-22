"""Security and idempotency tests for the public payOS webhook route."""

from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import billing
from app.db.models import PaymentOrder, PaymentWebhookEvent, UserEntitlement
from app.db.session import get_db
from app.services.billing.webhooks import canonicalize_payos_data


TEST_CHECKSUM_KEY = "deterministic-test-checksum-key"


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter(self, *expressions):
        rows = self.rows
        for expression in expressions:
            key = expression.left.key
            value = expression.right.value
            rows = [row for row in rows if getattr(row, key) == value]
        return FakeQuery(rows)

    def first(self):
        return self.rows[0] if self.rows else None

    def with_for_update(self):
        return self


class FakeDb:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.pending = []

    def query(self, model):
        return FakeQuery([row for row in self.rows if isinstance(row, model)])

    def add(self, row):
        self.rows.append(row)
        self.pending.append(row)

    def flush(self):
        pass

    def commit(self):
        self.pending.clear()

    def rollback(self):
        for row in self.pending:
            if row in self.rows:
                self.rows.remove(row)
        self.pending.clear()


def make_order(*, status="pending", amount=20000, currency="VND"):
    now = datetime.utcnow()
    return PaymentOrder(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider="payos",
        provider_order_code="123456",
        provider_payment_link_id="safe-payment-link-id",
        plan_code="starter_pack",
        amount_vnd=amount,
        currency=currency,
        status=status,
        created_at=now,
        updated_at=now,
        paid_at=now if status == "paid" else None,
    )


def sign_data(data):
    canonical = canonicalize_payos_data(data)
    return hmac.new(
        TEST_CHECKSUM_KEY.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def make_payload(order_code="123456", amount=20000, currency="VND", reference="TX-001"):
    data = {
        "orderCode": int(order_code),
        "amount": amount,
        "description": "CVFIT3456",
        "accountNumber": "",
        "reference": reference,
        "transactionDateTime": "2026-06-22 12:00:00",
        "currency": currency,
        "paymentLinkId": "safe-payment-link-id",
        "code": "00",
        "desc": "success",
    }
    return {
        "code": "00",
        "desc": "success",
        "success": True,
        "data": data,
        "signature": sign_data(data),
    }


def make_client(db, monkeypatch, *, checksum_key=TEST_CHECKSUM_KEY):
    monkeypatch.setattr(billing.settings, "ENABLE_BILLING", True)
    monkeypatch.setattr(billing.settings, "PAYOS_CHECKSUM_KEY", checksum_key)
    app = FastAPI()
    app.include_router(billing.router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def entitlements(db):
    return [row for row in db.rows if isinstance(row, UserEntitlement)]


def webhook_events(db):
    return [row for row in db.rows if isinstance(row, PaymentWebhookEvent)]


def test_signature_canonicalization_sorts_keys_and_normalizes_values():
    assert canonicalize_payos_data({"z": None, "a": 2, "items": [{"b": 1, "a": 2}]}) == (
        'a=2&items=[{"a":2,"b":1}]&z='
    )


def test_webhook_rejects_invalid_signature_without_db_mutation(monkeypatch):
    order = make_order()
    db = FakeDb([order])
    payload = make_payload()
    payload["signature"] = "invalid"

    response = make_client(db, monkeypatch).post("/v1/billing/webhooks/payos", json=payload)

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid webhook signature"}
    assert order.status == "pending"
    assert entitlements(db) == []
    assert webhook_events(db) == []


def test_webhook_missing_checksum_returns_safe_503(monkeypatch):
    order = make_order()
    db = FakeDb([order])

    response = make_client(db, monkeypatch, checksum_key="").post(
        "/v1/billing/webhooks/payos", json=make_payload()
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "billing webhook is not configured"}
    assert order.status == "pending"
    assert entitlements(db) == []


def test_webhook_is_inactive_while_billing_is_disabled(monkeypatch):
    order = make_order()
    db = FakeDb([order])
    monkeypatch.setattr(billing.settings, "ENABLE_BILLING", False)
    monkeypatch.setattr(billing.settings, "PAYOS_CHECKSUM_KEY", TEST_CHECKSUM_KEY)
    app = FastAPI()
    app.include_router(billing.router)
    app.dependency_overrides[get_db] = lambda: db

    response = TestClient(app).post("/v1/billing/webhooks/payos", json=make_payload())

    assert response.status_code == 503
    assert order.status == "pending"
    assert entitlements(db) == []
    assert webhook_events(db) == []


def test_valid_webhook_marks_paid_and_grants_backend_plan_credits(monkeypatch):
    order = make_order()
    db = FakeDb([order])

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=make_payload()
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert order.status == "paid"
    assert order.paid_at is not None
    assert len(entitlements(db)) == 1
    grant = entitlements(db)[0]
    assert grant.source_payment_order_id == order.id
    assert (
        grant.analysis_credits,
        grant.interview_credits,
        grant.cover_letter_credits,
        grant.package_credits,
    ) == (10, 20, 5, 5)
    assert webhook_events(db)[0].status == "applied"


def test_duplicate_payload_does_not_grant_twice(monkeypatch):
    order = make_order()
    db = FakeDb([order])
    client = make_client(db, monkeypatch)
    payload = make_payload()

    assert client.post("/v1/billing/webhooks/payos", json=payload).status_code == 200
    assert client.post("/v1/billing/webhooks/payos", json=payload).status_code == 200

    assert len(entitlements(db)) == 1
    assert len(webhook_events(db)) == 1


def test_already_paid_order_does_not_grant_again(monkeypatch):
    order = make_order(status="paid")
    now = datetime.utcnow()
    existing = UserEntitlement(
        id=uuid.uuid4(), user_id=order.user_id, source_payment_order_id=order.id,
        plan_code=order.plan_code, analysis_credits=10, interview_credits=20,
        cover_letter_credits=5, package_credits=5, starts_at=now,
        created_at=now, updated_at=now,
    )
    db = FakeDb([order, existing])

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=make_payload(reference="TX-RETRY")
    )

    assert response.status_code == 200
    assert len(entitlements(db)) == 1
    assert webhook_events(db)[0].status == "duplicate"


def test_already_paid_order_without_entitlement_is_not_repaired_from_webhook(monkeypatch):
    order = make_order(status="paid")
    db = FakeDb([order])

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=make_payload(reference="TX-INCONSISTENT")
    )

    assert response.status_code == 200
    assert entitlements(db) == []
    assert webhook_events(db)[0].status == "duplicate"


def test_manual_review_order_is_not_automatically_paid(monkeypatch):
    order = make_order(status="manual_review")
    db = FakeDb([order])

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=make_payload(reference="TX-REVIEW")
    )

    assert response.status_code == 200
    assert order.status == "manual_review"
    assert entitlements(db) == []
    assert webhook_events(db)[0].status == "manual_review"


def test_amount_mismatch_routes_to_manual_review_without_credits(monkeypatch):
    order = make_order()
    db = FakeDb([order])

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=make_payload(amount=1)
    )

    assert response.status_code == 200
    assert order.status == "manual_review"
    assert entitlements(db) == []
    assert webhook_events(db)[0].status == "manual_review"


def test_currency_mismatch_routes_to_manual_review_without_credits(monkeypatch):
    order = make_order()
    db = FakeDb([order])

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=make_payload(currency="USD")
    )

    assert response.status_code == 200
    assert order.status == "manual_review"
    assert entitlements(db) == []
    assert webhook_events(db)[0].status == "manual_review"


def test_unknown_order_is_recorded_safely_without_credits(monkeypatch):
    db = FakeDb()

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=make_payload(order_code="999999")
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert entitlements(db) == []
    assert webhook_events(db)[0].status == "manual_review"
    assert webhook_events(db)[0].error_message == "unknown payment order"


def test_webhook_audit_stores_hashes_not_raw_signature_or_payload(monkeypatch):
    order = make_order()
    db = FakeDb([order])
    payload = make_payload()

    response = make_client(db, monkeypatch).post(
        "/v1/billing/webhooks/payos", json=payload
    )

    assert response.status_code == 200
    event = webhook_events(db)[0]
    assert len(event.payload_hash) == 64
    assert len(event.signature_hash) == 64
    assert event.signature_hash != payload["signature"]
    assert payload["signature"] not in str(event.__dict__)
    assert TEST_CHECKSUM_KEY not in response.text
    assert "signature" not in response.text.lower()
