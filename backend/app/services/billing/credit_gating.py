"""Credit balance calculation and consumption for gated AI actions.

This module never commits. Route handlers stage usage events in the same
transaction as the accepted/generated product record so failed requests do not
consume credits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import UsageEvent, User, UserEntitlement
from app.services.billing.plans import BILLING_TIMEZONE, CREDIT_TYPES, get_free_allowance


FREE_ALLOWANCE_SOURCE = "free_allowance"
PAID_CREDIT_SOURCE = "paid_credit"
_CREDIT_COLUMNS = {
    "analysis": "analysis_credits",
    "interview": "interview_credits",
    "cover_letter": "cover_letter_credits",
    "package": "package_credits",
}


class InsufficientCreditsError(RuntimeError):
    """Safe, user-scoped insufficient-credit error."""

    def __init__(self, required_credit: str) -> None:
        self.required_credit = required_credit
        super().__init__("You do not have enough credits for this action.")

    def response_body(self) -> dict[str, str]:
        return {
            "error": "insufficient_credits",
            "message": str(self),
            "required_credit": self.required_credit,
            "pricing_url": "/pricing",
        }


@dataclass(frozen=True)
class CreditBalance:
    free_allowance: dict[str, int]
    used_this_month: dict[str, int]
    free_remaining: dict[str, int]
    remaining_credits: dict[str, int]


@dataclass(frozen=True)
class CreditAllocation:
    credit_type: str
    free_quantity: int
    paid_quantity: int


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def get_credit_usage_window(
    now: datetime,
    timezone_name: str = BILLING_TIMEZONE,
) -> tuple[datetime, datetime]:
    """Return the current local calendar month as naive UTC boundaries."""
    zone = ZoneInfo(timezone_name)
    aware_utc = (
        now.replace(tzinfo=timezone.utc)
        if now.tzinfo is None
        else now.astimezone(timezone.utc)
    )
    local_now = aware_utc.astimezone(zone)
    start_local = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start_local.month == 12:
        end_local = start_local.replace(year=start_local.year + 1, month=1)
    else:
        end_local = start_local.replace(month=start_local.month + 1)
    return _utc_naive(start_local), _utc_naive(end_local)


def _validate_request(credit_type: str, quantity: int) -> None:
    if credit_type not in CREDIT_TYPES:
        raise ValueError("unknown credit type")
    if quantity < 1:
        raise ValueError("quantity must be positive")


def calculate_credit_balance(
    db: Session,
    user_id: uuid.UUID,
    now: datetime | None = None,
) -> CreditBalance:
    now = now or datetime.utcnow()
    now_utc = _utc_naive(now)
    window_start, window_end = get_credit_usage_window(now)

    monthly_events = (
        db.query(UsageEvent)
        .filter(
            UsageEvent.user_id == user_id,
            UsageEvent.created_at >= window_start,
            UsageEvent.created_at < window_end,
        )
        .all()
    )
    paid_events = (
        db.query(UsageEvent)
        .filter(UsageEvent.user_id == user_id)
        .all()
    )
    entitlements = (
        db.query(UserEntitlement)
        .filter(UserEntitlement.user_id == user_id)
        .all()
    )
    entitlements = [
        entitlement
        for entitlement in entitlements
        if entitlement.starts_at <= now_utc
        and (entitlement.expires_at is None or entitlement.expires_at > now_utc)
    ]

    allowance = get_free_allowance()
    used = {credit_type: 0 for credit_type in CREDIT_TYPES}
    free_used = {credit_type: 0 for credit_type in CREDIT_TYPES}
    paid_used = {credit_type: 0 for credit_type in CREDIT_TYPES}
    for event in monthly_events:
        if event.event_type not in used:
            continue
        quantity = max(0, event.quantity)
        used[event.event_type] += quantity
        # Source was nullable before gating; preserve those historical events as
        # free usage rather than silently restoring allowance.
        if event.source in (None, FREE_ALLOWANCE_SOURCE, "free"):
            free_used[event.event_type] += quantity
    for event in paid_events:
        if event.event_type in paid_used and event.source in (PAID_CREDIT_SOURCE, "paid"):
            paid_used[event.event_type] += max(0, event.quantity)

    granted = {credit_type: 0 for credit_type in CREDIT_TYPES}
    for entitlement in entitlements:
        for credit_type, column in _CREDIT_COLUMNS.items():
            granted[credit_type] += max(0, getattr(entitlement, column))

    free_remaining = {
        credit_type: max(0, allowance[credit_type] - free_used[credit_type])
        for credit_type in CREDIT_TYPES
    }
    remaining = {
        credit_type: max(0, granted[credit_type] - paid_used[credit_type])
        for credit_type in CREDIT_TYPES
    }
    return CreditBalance(
        free_allowance=allowance,
        used_this_month=used,
        free_remaining=free_remaining,
        remaining_credits=remaining,
    )


def _lock_user(db: Session, user_id: uuid.UUID) -> None:
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if user is None:
        raise ValueError("user not found")


def ensure_credit_available(
    db: Session,
    user_id: uuid.UUID,
    credit_type: str,
    quantity: int = 1,
    *,
    now: datetime | None = None,
) -> CreditAllocation | None:
    _validate_request(credit_type, quantity)
    if not settings.ENABLE_CREDIT_GATING:
        return None

    _lock_user(db, user_id)
    balance = calculate_credit_balance(db, user_id, now)
    free_quantity = min(quantity, balance.free_remaining[credit_type])
    paid_quantity = quantity - free_quantity
    if paid_quantity > balance.remaining_credits[credit_type]:
        raise InsufficientCreditsError(credit_type)
    return CreditAllocation(credit_type, free_quantity, paid_quantity)


def consume_credit(
    db: Session,
    user_id: uuid.UUID,
    credit_type: str,
    quantity: int = 1,
    *,
    related_job_id: uuid.UUID | None = None,
    related_application_id: uuid.UUID | None = None,
    related_order_id: uuid.UUID | None = None,
    now: datetime | None = None,
) -> list[UsageEvent]:
    """Stage free-first usage events; the caller owns commit/rollback."""
    _validate_request(credit_type, quantity)
    if not settings.ENABLE_CREDIT_GATING:
        return []

    created_at = _utc_naive(now or datetime.utcnow())
    allocation = ensure_credit_available(db, user_id, credit_type, quantity, now=created_at)
    assert allocation is not None
    events: list[UsageEvent] = []
    for source, allocated in (
        (FREE_ALLOWANCE_SOURCE, allocation.free_quantity),
        (PAID_CREDIT_SOURCE, allocation.paid_quantity),
    ):
        if allocated == 0:
            continue
        event = UsageEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=credit_type,
            quantity=allocated,
            source=source,
            related_job_id=related_job_id,
            related_application_id=related_application_id,
            related_order_id=related_order_id,
            created_at=created_at,
        )
        db.add(event)
        events.append(event)
    return events
