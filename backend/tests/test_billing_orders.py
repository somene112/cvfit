"""Ownership and persistence tests for billing orders."""

from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.billing import router
from app.db.models import PaymentOrder, User
from app.db.session import get_db
from app.services.billing.orders import create_checkout_order
from app.services.billing.payos_client import PaymentLinkResult
from app.services.billing.plans import get_billing_plan


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

    def order_by(self, _expression):
        return FakeQuery(sorted(self.rows, key=lambda row: row.created_at, reverse=True))

    def all(self):
        return list(self.rows)

    def first(self):
        return self.rows[0] if self.rows else None


class FakeDb:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.pending = []

    def query(self, model):
        return FakeQuery([row for row in self.rows if isinstance(row, model)])

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


def make_user(email):
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_order(user, created_at, plan_code="starter_pack"):
    return PaymentOrder(
        id=uuid.uuid4(), user_id=user.id, provider="payos",
        provider_order_code=str(uuid.uuid4().int), plan_code=plan_code,
        amount_vnd=20000, currency="VND", status="pending",
        created_at=created_at, updated_at=created_at,
    )


def client_for(db, user):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_order_list_is_current_user_only_and_newest_first():
    user = make_user("owner@example.com")
    other = make_user("other@example.com")
    now = datetime.utcnow()
    old = make_order(user, now - timedelta(minutes=2))
    new = make_order(user, now)
    foreign = make_order(other, now + timedelta(minutes=1))

    response = client_for(FakeDb([old, foreign, new]), user).get("/v1/billing/orders")

    assert response.status_code == 200
    ids = [item["payment_order_id"] for item in response.json()["orders"]]
    assert ids == [str(new.id), str(old.id)]
    assert str(foreign.id) not in response.text


def test_order_detail_returns_owned_order():
    user = make_user("owner@example.com")
    order = make_order(user, datetime.utcnow())

    response = client_for(FakeDb([order]), user).get(f"/v1/billing/orders/{order.id}")

    assert response.status_code == 200
    assert response.json()["payment_order_id"] == str(order.id)
    assert response.json()["credits_granted"] is None


def test_order_detail_hides_another_users_order():
    user = make_user("owner@example.com")
    other = make_user("other@example.com")
    order = make_order(other, datetime.utcnow())

    response = client_for(FakeDb([order]), user).get(f"/v1/billing/orders/{order.id}")

    assert response.status_code == 404


class FakeProvider:
    def create_payment_link(self, **_kwargs):
        return PaymentLinkResult(
            checkout_url="https://pay.example.test/opaque",
            payment_link_id="link-safe-id",
            sanitized_payload={"code": "00", "provider_status": "PENDING"},
        )


def test_order_service_creates_pending_order_without_credit_or_paid_state(monkeypatch):
    from app.services.billing import orders

    user = make_user("owner@example.com")
    db = FakeDb()
    monkeypatch.setattr(orders.settings, "PAYMENT_RETURN_URL", "https://app.example.test/return")
    monkeypatch.setattr(orders.settings, "PAYMENT_CANCEL_URL", "https://app.example.test/cancel")
    order, _result = create_checkout_order(
        db,
        user_id=user.id,
        plan=get_billing_plan("starter_pack"),
        provider_client=FakeProvider(),
    )

    assert order.status == "pending"
    assert order.paid_at is None
    assert order.amount_vnd == 20000
    assert order.checkout_url == "https://pay.example.test/opaque"
    assert not any(row.__class__.__name__ == "UserEntitlement" for row in db.rows)
