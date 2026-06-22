"""Transactional credit grants for verified paid billing orders."""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.db.models import PaymentOrder, UserEntitlement


class BillingCreditGrantError(RuntimeError):
    """Raised when a credit grant is attempted from a non-paid order."""


def get_entitlement_for_order(
    db: Session,
    payment_order_id: uuid.UUID,
) -> UserEntitlement | None:
    return (
        db.query(UserEntitlement)
        .filter(UserEntitlement.source_payment_order_id == payment_order_id)
        .first()
    )


def grant_order_credits(
    db: Session,
    *,
    order: PaymentOrder,
    plan: dict,
    granted_at: datetime,
) -> tuple[UserEntitlement, bool]:
    """Stage one backend-owned entitlement grant for an order.

    The caller owns the transaction and must lock the payment order before
    calling this function. Returning ``False`` means a grant already exists.
    """
    if order.status != "paid" or order.paid_at is None:
        raise BillingCreditGrantError("credits require a paid payment order")

    existing = get_entitlement_for_order(db, order.id)
    if existing is not None:
        return existing, False

    credits = plan["credits"]
    entitlement = UserEntitlement(
        id=uuid.uuid4(),
        user_id=order.user_id,
        source_payment_order_id=order.id,
        plan_code=plan["plan_code"],
        analysis_credits=credits["analysis"],
        interview_credits=credits["interview"],
        cover_letter_credits=credits["cover_letter"],
        package_credits=credits["package"],
        starts_at=granted_at,
        created_at=granted_at,
        updated_at=granted_at,
    )
    db.add(entitlement)
    return entitlement, True
