"""Billing order queries and checkout-order creation."""

from __future__ import annotations

from datetime import datetime, timezone
import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PaymentOrder
from app.services.billing.payos_client import PayOSClient, PaymentLinkResult


def generate_provider_order_code() -> int:
    """Return a positive numeric code accepted by payOS."""
    timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return timestamp_ms * 1000 + secrets.randbelow(1000)


def list_orders(db: Session, user_id: uuid.UUID) -> list[PaymentOrder]:
    return (
        db.query(PaymentOrder)
        .filter(PaymentOrder.user_id == user_id)
        .order_by(PaymentOrder.created_at.desc())
        .all()
    )


def get_owned_order(
    db: Session,
    *,
    user_id: uuid.UUID,
    payment_order_id: uuid.UUID,
) -> PaymentOrder | None:
    return (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.id == payment_order_id,
            PaymentOrder.user_id == user_id,
        )
        .first()
    )


def create_checkout_order(
    db: Session,
    *,
    user_id: uuid.UUID,
    plan: dict,
    provider_client: PayOSClient,
) -> tuple[PaymentOrder, PaymentLinkResult]:
    order_code = generate_provider_order_code()
    order = PaymentOrder(
        id=uuid.uuid4(),
        user_id=user_id,
        provider=settings.PAYMENT_PROVIDER,
        provider_order_code=str(order_code),
        plan_code=plan["plan_code"],
        amount_vnd=plan["price_vnd"],
        currency=plan["currency"],
        status="pending",
        return_url=settings.PAYMENT_RETURN_URL,
        cancel_url=settings.PAYMENT_CANCEL_URL,
    )
    db.add(order)

    try:
        result = provider_client.create_payment_link(
            order_code=order_code,
            amount_vnd=plan["price_vnd"],
            description=f"CVFIT{order_code % 10000:04d}",
        )
        order.checkout_url = result.checkout_url
        order.provider_payment_link_id = result.payment_link_id
        order.raw_provider_payload_json = result.sanitized_payload
        db.commit()
        db.refresh(order)
    except Exception:
        db.rollback()
        raise

    return order, result
