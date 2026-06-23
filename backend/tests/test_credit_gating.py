"""Core credit balance and consumption tests."""

from __future__ import annotations

from datetime import datetime
import uuid

import pytest

from app.core.config import settings
from app.db.models import UsageEvent, User, UserEntitlement
from app.services.billing.credit_gating import (
    FREE_ALLOWANCE_SOURCE,
    PAID_CREDIT_SOURCE,
    InsufficientCreditsError,
    calculate_credit_balance,
    consume_credit,
    ensure_credit_available,
    get_credit_usage_window,
)


def _expression_value(node):
    return getattr(node, "value", getattr(node, "effective_value", None))


def _matches(row, expression):
    clauses = list(getattr(expression, "clauses", ()))
    if clauses:
        values = [_matches(row, clause) for clause in clauses]
        return any(values) if expression.operator.__name__ == "or_" else all(values)
    key = expression.left.key
    actual = getattr(row, key)
    expected = _expression_value(expression.right)
    operation = expression.operator.__name__
    if operation == "eq":
        return actual == expected
    if operation == "ge":
        return actual >= expected
    if operation == "gt":
        return actual is not None and actual > expected
    if operation == "le":
        return actual <= expected
    if operation == "lt":
        return actual < expected
    if operation == "is_":
        return actual is expected
    return True


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter(self, *expressions):
        return FakeQuery(
            row for row in self.rows if all(_matches(row, expression) for expression in expressions)
        )

    def with_for_update(self):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)


class FakeDb:
    def __init__(self, *rows):
        self.rows = list(rows)

    def query(self, model):
        return FakeQuery(row for row in self.rows if isinstance(row, model))

    def add(self, row):
        self.rows.append(row)


def make_user():
    return User(id=uuid.uuid4(), email=f"{uuid.uuid4()}@example.com", is_active=True)


def make_entitlement(user_id, **credits):
    now = datetime(2026, 6, 1)
    defaults = dict(analysis=0, interview=0, cover_letter=0, package=0)
    defaults.update(credits)
    return UserEntitlement(
        id=uuid.uuid4(),
        user_id=user_id,
        plan_code="test_pack",
        analysis_credits=defaults["analysis"],
        interview_credits=defaults["interview"],
        cover_letter_credits=defaults["cover_letter"],
        package_credits=defaults["package"],
        starts_at=now,
        created_at=now,
        updated_at=now,
    )


def make_usage(user_id, credit_type, quantity, source, created_at):
    return UsageEvent(
        id=uuid.uuid4(),
        user_id=user_id,
        event_type=credit_type,
        quantity=quantity,
        source=source,
        created_at=created_at,
    )


def test_gating_disabled_allows_without_consuming(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_CREDIT_GATING", False)
    user = make_user()
    db = FakeDb(user)

    assert ensure_credit_available(db, user.id, "analysis") is None
    assert consume_credit(db, user.id, "analysis") == []
    assert not any(isinstance(row, UsageEvent) for row in db.rows)


def test_free_allowance_is_consumed_before_paid_credits(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_CREDIT_GATING", True)
    user = make_user()
    db = FakeDb(user, make_entitlement(user.id, analysis=4))

    events = consume_credit(db, user.id, "analysis", now=datetime(2026, 6, 10))

    assert [(event.source, event.quantity) for event in events] == [(FREE_ALLOWANCE_SOURCE, 1)]


def test_paid_credits_are_used_after_free_allowance(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_CREDIT_GATING", True)
    user = make_user()
    free_used = make_usage(
        user.id, "analysis", 3, FREE_ALLOWANCE_SOURCE, datetime(2026, 6, 5)
    )
    db = FakeDb(user, free_used, make_entitlement(user.id, analysis=2))

    events = consume_credit(db, user.id, "analysis", now=datetime(2026, 6, 10))

    assert [(event.source, event.quantity) for event in events] == [(PAID_CREDIT_SOURCE, 1)]


def test_insufficient_credits_raises_safe_error(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_CREDIT_GATING", True)
    user = make_user()
    db = FakeDb(
        user,
        make_usage(user.id, "package", 2, FREE_ALLOWANCE_SOURCE, datetime(2026, 6, 5)),
    )

    with pytest.raises(InsufficientCreditsError) as caught:
        ensure_credit_available(db, user.id, "package", now=datetime(2026, 6, 10))

    assert caught.value.response_body() == {
        "error": "insufficient_credits",
        "message": "You do not have enough credits for this action.",
        "required_credit": "package",
        "pricing_url": "/pricing",
    }


def test_balance_subtracts_monthly_free_and_all_time_paid_usage():
    user = make_user()
    db = FakeDb(
        user,
        make_entitlement(user.id, analysis=4),
        make_entitlement(user.id, analysis=6),
        make_usage(user.id, "analysis", 1, FREE_ALLOWANCE_SOURCE, datetime(2026, 6, 2)),
        make_usage(user.id, "analysis", 2, PAID_CREDIT_SOURCE, datetime(2026, 5, 2)),
        make_usage(user.id, "analysis", 1, PAID_CREDIT_SOURCE, datetime(2026, 6, 3)),
    )

    balance = calculate_credit_balance(db, user.id, datetime(2026, 6, 10))

    assert balance.used_this_month["analysis"] == 2
    assert balance.free_remaining["analysis"] == 2
    assert balance.remaining_credits["analysis"] == 7


def test_usage_event_contains_references_but_no_private_content(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_CREDIT_GATING", True)
    user = make_user()
    job_id = uuid.uuid4()
    app_id = uuid.uuid4()
    db = FakeDb(user)

    event = consume_credit(
        db,
        user.id,
        "interview",
        related_job_id=job_id,
        related_application_id=app_id,
        now=datetime(2026, 6, 10),
    )[0]

    assert event.event_type == "interview"
    assert event.source == FREE_ALLOWANCE_SOURCE
    assert event.quantity == 1
    assert event.related_job_id == job_id
    assert event.related_application_id == app_id
    assert not {"cv_text", "jd_text", "answer_text"}.intersection(vars(event))


def test_month_window_uses_asia_ho_chi_minh_boundary():
    before_local_month = datetime.fromisoformat("2026-05-31T16:59:59+00:00")
    after_local_month = datetime.fromisoformat("2026-05-31T17:00:00+00:00")

    may_start, may_end = get_credit_usage_window(before_local_month)
    june_start, june_end = get_credit_usage_window(after_local_month)

    assert may_start == datetime(2026, 4, 30, 17, 0)
    assert may_end == datetime(2026, 5, 31, 17, 0)
    assert june_start == datetime(2026, 5, 31, 17, 0)
    assert june_end == datetime(2026, 6, 30, 17, 0)
