"""Security-focused checkout and payOS boundary tests."""

from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.deps import get_current_user
from app.api.routes import billing
from app.db.models import PaymentOrder, User, UserEntitlement
from app.db.session import get_db
from app.services.billing.payos_client import (
    BillingProviderConfigError,
    BillingProviderRequestError,
    PaymentLinkResult,
    PayOSClient,
)


class FakeDb:
    def __init__(self):
        self.rows = []
        self.pending = []

    def add(self, row):
        if getattr(row, "created_at", None) is None:
            row.created_at = datetime.utcnow()
            row.updated_at = row.created_at
        self.rows.append(row)
        self.pending.append(row)

    def commit(self):
        self.pending.clear()

    def rollback(self):
        for row in self.pending:
            self.rows.remove(row)
        self.pending.clear()

    def refresh(self, _row):
        pass


class FakeProvider:
    def __init__(self):
        self.calls = []

    def create_payment_link(self, **kwargs):
        self.calls.append(kwargs)
        return PaymentLinkResult(
            checkout_url="https://pay.example.test/opaque",
            payment_link_id="safe-link-id",
            sanitized_payload={
                "code": "00",
                "description": "success",
                "provider_status": "PENDING",
            },
        )


def make_user():
    return User(
        id=uuid.uuid4(),
        email="checkout@example.com",
        password_hash="hash",
        is_active=True,
    )


def make_client(db, user):
    app = FastAPI()
    app.include_router(billing.router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def enable_billing(monkeypatch):
    monkeypatch.setattr(billing.settings, "ENABLE_BILLING", True)
    monkeypatch.setattr(billing.settings, "PAYMENT_PROVIDER", "payos")
    monkeypatch.setattr(billing.settings, "PAYMENT_RETURN_URL", "https://app.example.test/return")
    monkeypatch.setattr(billing.settings, "PAYMENT_CANCEL_URL", "https://app.example.test/cancel")


def test_checkout_disabled_returns_safe_503_without_calling_provider(monkeypatch):
    monkeypatch.setattr(billing.settings, "ENABLE_BILLING", False)
    monkeypatch.setattr(
        billing,
        "get_payos_client",
        lambda: pytest.fail("provider must not be constructed when billing is disabled"),
    )

    response = make_client(FakeDb(), make_user()).post(
        "/v1/billing/checkout", json={"plan_code": "starter_pack"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "billing is not available"}


def test_checkout_rejects_unknown_plan_without_calling_provider(monkeypatch):
    enable_billing(monkeypatch)
    monkeypatch.setattr(
        billing,
        "get_payos_client",
        lambda: pytest.fail("provider must not be constructed for an invalid plan"),
    )

    response = make_client(FakeDb(), make_user()).post(
        "/v1/billing/checkout", json={"plan_code": "not-a-plan"}
    )

    assert response.status_code == 422


@pytest.mark.parametrize("extra_field, value", [
    ("amount", 1),
    ("currency", "USD"),
    ("status", "paid"),
    ("user_id", "attacker"),
])
def test_checkout_rejects_frontend_owned_payment_fields(monkeypatch, extra_field, value):
    enable_billing(monkeypatch)
    monkeypatch.setattr(
        billing,
        "get_payos_client",
        lambda: pytest.fail("provider must not be called for an invalid request"),
    )
    body = {"plan_code": "starter_pack", extra_field: value}

    response = make_client(FakeDb(), make_user()).post("/v1/billing/checkout", json=body)

    assert response.status_code == 422


def test_checkout_uses_backend_amount_and_creates_pending_order(monkeypatch):
    enable_billing(monkeypatch)
    provider = FakeProvider()
    monkeypatch.setattr(billing, "get_payos_client", lambda: provider)
    db = FakeDb()

    response = make_client(db, make_user()).post(
        "/v1/billing/checkout", json={"plan_code": "starter_pack"}
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["provider"] == "payos"
    assert payload["checkout_url"] == "https://pay.example.test/opaque"
    assert payload["status"] == "pending"
    assert payload["amount"] == 20000
    assert payload["currency"] == "VND"
    assert payload["payment_order_id"]
    assert provider.calls[0]["amount_vnd"] == 20000

    orders = [row for row in db.rows if isinstance(row, PaymentOrder)]
    assert len(orders) == 1
    assert orders[0].status == "pending"
    assert orders[0].paid_at is None
    assert not any(isinstance(row, UserEntitlement) for row in db.rows)

    response_text = response.text.lower()
    for forbidden in (
        "checksum",
        "api_key",
        "client_id",
        "signature",
        "webhook",
        "raw_provider_payload",
    ):
        assert forbidden not in response_text


def test_checkout_missing_provider_config_returns_safe_503(monkeypatch):
    enable_billing(monkeypatch)
    monkeypatch.setattr(billing.settings, "PAYOS_CLIENT_ID", "")
    monkeypatch.setattr(billing.settings, "PAYOS_API_KEY", "")
    monkeypatch.setattr(billing.settings, "PAYOS_CHECKSUM_KEY", "")

    response = make_client(FakeDb(), make_user()).post(
        "/v1/billing/checkout", json={"plan_code": "starter_pack"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "billing provider is not configured"}


def test_checkout_provider_failure_rolls_back_and_returns_safe_502(monkeypatch):
    enable_billing(monkeypatch)

    class FailingProvider:
        def create_payment_link(self, **_kwargs):
            raise BillingProviderRequestError("internal provider detail")

    monkeypatch.setattr(billing, "get_payos_client", lambda: FailingProvider())
    db = FakeDb()

    response = make_client(db, make_user()).post(
        "/v1/billing/checkout", json={"plan_code": "starter_pack"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "billing provider request failed"}
    assert not any(isinstance(row, PaymentOrder) for row in db.rows)


def test_payos_client_requires_all_backend_configuration():
    with pytest.raises(BillingProviderConfigError, match="provider is not configured"):
        PayOSClient(
            client_id="",
            api_key="",
            checksum_key="",
            return_url="",
            cancel_url="",
        )


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "code": "00",
            "desc": "success",
            "data": {
                "orderCode": 123,
                "status": "PENDING",
                "paymentLinkId": "safe-link-id",
                "checkoutUrl": "https://pay.example.test/opaque",
                "qrCode": "sensitive-qr-data",
            },
            "signature": "provider-response-signature",
        }


class FakeHttpClient:
    def __init__(self):
        self.request = None

    def post(self, url, **kwargs):
        self.request = (url, kwargs)
        return FakeResponse()


def test_payos_client_returns_only_sanitized_provider_data():
    transport = FakeHttpClient()
    client = PayOSClient(
        client_id="unit-client-id",
        api_key="unit-api-key",
        checksum_key="unit-checksum-key",
        return_url="https://app.example.test/return",
        cancel_url="https://app.example.test/cancel",
        http_client=transport,
    )

    result = client.create_payment_link(
        order_code=123,
        amount_vnd=20000,
        description="CVFIT0123",
    )

    assert result.payment_link_id == "safe-link-id"
    assert result.sanitized_payload == {
        "code": "00",
        "description": "success",
        "provider_status": "PENDING",
        "provider_order_code": 123,
    }
    assert "signature" not in str(result.sanitized_payload).lower()
    assert "qrcode" not in str(result.sanitized_payload).lower()
    assert transport.request[1]["timeout"] == 10.0
