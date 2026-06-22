"""Unit tests for backend-owned transactional credit grants."""

from __future__ import annotations

from datetime import datetime
import uuid

from app.db.models import PaymentOrder, UserEntitlement
import pytest

from app.services.billing.credits import BillingCreditGrantError, grant_order_credits
from app.services.billing.plans import get_billing_plan


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter(self, expression):
        key = expression.left.key
        value = expression.right.value
        return FakeQuery([row for row in self.rows if getattr(row, key) == value])

    def first(self):
        return self.rows[0] if self.rows else None


class FakeDb:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def query(self, model):
        return FakeQuery([row for row in self.rows if isinstance(row, model)])

    def add(self, row):
        self.rows.append(row)


def make_order(*, status="paid"):
    now = datetime.utcnow()
    return PaymentOrder(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider="payos",
        provider_order_code="123456",
        plan_code="starter_pack",
        amount_vnd=20000,
        currency="VND",
        status=status,
        paid_at=now if status == "paid" else None,
        created_at=now,
        updated_at=now,
    )


def test_credit_grant_uses_backend_plan_values():
    order = make_order()
    db = FakeDb()

    entitlement, created = grant_order_credits(
        db,
        order=order,
        plan=get_billing_plan(order.plan_code),
        granted_at=datetime.utcnow(),
    )

    assert created is True
    assert entitlement.user_id == order.user_id
    assert entitlement.source_payment_order_id == order.id
    assert entitlement.analysis_credits == 10
    assert entitlement.interview_credits == 20
    assert entitlement.cover_letter_credits == 5
    assert entitlement.package_credits == 5


def test_credit_grant_is_idempotent_by_payment_order():
    order = make_order()
    now = datetime.utcnow()
    existing = UserEntitlement(
        id=uuid.uuid4(),
        user_id=order.user_id,
        source_payment_order_id=order.id,
        plan_code=order.plan_code,
        analysis_credits=10,
        interview_credits=20,
        cover_letter_credits=5,
        package_credits=5,
        starts_at=now,
        created_at=now,
        updated_at=now,
    )
    db = FakeDb([existing])

    entitlement, created = grant_order_credits(
        db,
        order=order,
        plan=get_billing_plan(order.plan_code),
        granted_at=now,
    )

    assert created is False
    assert entitlement is existing
    assert len([row for row in db.rows if isinstance(row, UserEntitlement)]) == 1


def test_credit_grant_rejects_non_paid_order():
    order = make_order(status="pending")

    with pytest.raises(BillingCreditGrantError, match="require a paid payment order"):
        grant_order_credits(
            FakeDb(),
            order=order,
            plan=get_billing_plan(order.plan_code),
            granted_at=datetime.utcnow(),
        )
