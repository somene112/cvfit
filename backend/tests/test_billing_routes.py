"""Route tests for billing plans and usage."""

from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.billing import router
from app.db.models import UsageEvent, User, UserEntitlement
from app.db.session import get_db


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter(self, *expressions):
        rows = self.rows
        for expression in expressions:
            key = expression.left.key
            value = expression.right.value
            if expression.operator.__name__ == "eq":
                rows = [row for row in rows if getattr(row, key) == value]
            elif expression.operator.__name__ == "ge":
                rows = [row for row in rows if getattr(row, key) >= value]
        return FakeQuery(rows)

    def all(self):
        return list(self.rows)


class FakeDb:
    def __init__(self, rows=None):
        self.rows = rows or []

    def query(self, model):
        return FakeQuery([row for row in self.rows if isinstance(row, model)])

    def get(self, model, key):
        return next(
            (row for row in self.rows if isinstance(row, model) and row.id == key),
            None,
        )


def make_user(email="billing@example.com"):
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_client(db, user=None):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_billing_endpoints_require_auth():
    client = make_client(FakeDb())
    for method, path in (
        ("get", "/v1/billing/plans"),
        ("get", "/v1/billing/usage"),
        ("get", "/v1/billing/orders"),
        ("get", f"/v1/billing/orders/{uuid.uuid4()}"),
        ("post", "/v1/billing/checkout"),
    ):
        response = client.request(
            method.upper(),
            path,
            json={"plan_code": "starter_pack"} if method == "post" else None,
        )
        assert response.status_code == 401


def test_plans_returns_starter_and_pro_demo_from_backend_config():
    user = make_user()
    response = make_client(FakeDb(), user).get("/v1/billing/plans")

    assert response.status_code == 200
    payload = response.json()
    assert payload["currency"] == "VND"
    assert [plan["plan_code"] for plan in payload["plans"]] == [
        "starter_pack",
        "pro_demo_pack",
    ]
    assert [plan["amount"] for plan in payload["plans"]] == [20000, 49000]


def test_usage_returns_allowance_and_safe_zero_defaults():
    user = make_user()
    response = make_client(FakeDb(), user).get("/v1/billing/usage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["timezone"] == "Asia/Ho_Chi_Minh"
    assert payload["free_allowance"] == {
        "analysis": 3,
        "interview": 10,
        "cover_letter": 2,
        "package": 2,
    }
    assert all(value == 0 for value in payload["used_this_month"].values())
    assert all(value == 0 for value in payload["remaining_credits"].values())


def test_usage_counts_current_user_events_and_entitlements_only():
    user = make_user()
    other = make_user("other@example.com")
    now = datetime.utcnow()
    rows = [
        UsageEvent(id=uuid.uuid4(), user_id=user.id, event_type="analysis", quantity=1, created_at=now),
        UsageEvent(id=uuid.uuid4(), user_id=other.id, event_type="analysis", quantity=9, created_at=now),
        UserEntitlement(
            id=uuid.uuid4(), user_id=user.id, plan_code="starter_pack",
            analysis_credits=10, interview_credits=20, cover_letter_credits=5,
            package_credits=5, created_at=now, updated_at=now, starts_at=now,
        ),
    ]
    payload = make_client(FakeDb(rows), user).get("/v1/billing/usage").json()

    assert payload["used_this_month"]["analysis"] == 1
    assert payload["free_remaining"]["analysis"] == 2
    assert payload["remaining_credits"]["analysis"] == 10
