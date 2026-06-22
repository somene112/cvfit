"""Authenticated Phase 7A billing checkout API foundation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any
import uuid
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import PaymentOrder, UsageEvent, User, UserEntitlement
from app.db.session import get_db
from app.schemas.billing import (
    BillingCredits,
    BillingPlan,
    BillingPlansResponse,
    BillingUsageResponse,
    BillingWebhookResponse,
    CheckoutRequest,
    CheckoutResponse,
    PaymentOrderDetail,
    PaymentOrdersResponse,
    PaymentOrderSummary,
)
from app.services.billing.orders import create_checkout_order, get_owned_order, list_orders
from app.services.billing.payos_client import (
    BillingProviderConfigError,
    BillingProviderError,
    PayOSClient,
)
from app.services.billing.plans import (
    BILLING_TIMEZONE,
    get_billing_plan,
    get_billing_plans,
    get_free_allowance,
)
from app.services.billing.webhooks import (
    BillingWebhookPayloadError,
    BillingWebhookSignatureError,
    process_payos_webhook,
)


router = APIRouter(prefix="/v1/billing", tags=["billing"])


def get_payos_client() -> PayOSClient:
    return PayOSClient.from_settings()


def _credits(values: dict[str, int]) -> BillingCredits:
    return BillingCredits(**values)


def _plan_response(plan: dict) -> BillingPlan:
    return BillingPlan(
        plan_code=plan["plan_code"],
        name=plan["name"],
        amount=plan["price_vnd"],
        currency=plan["currency"],
        description=plan.get("description"),
        credits=_credits(plan["credits"]),
    )


def _order_summary(order: PaymentOrder) -> PaymentOrderSummary:
    return PaymentOrderSummary(
        payment_order_id=str(order.id),
        plan_code=order.plan_code,
        amount=order.amount_vnd,
        currency=order.currency,
        status=order.status,
        created_at=order.created_at,
        paid_at=order.paid_at,
    )


@router.get("/plans", response_model=BillingPlansResponse)
def billing_plans(
    current_user: Annotated[User, Depends(get_current_user)],
) -> BillingPlansResponse:
    del current_user
    plans = [_plan_response(plan) for plan in get_billing_plans()]
    return BillingPlansResponse(plans=plans)


@router.get("/usage", response_model=BillingUsageResponse)
def billing_usage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> BillingUsageResponse:
    now_ict = datetime.now(ZoneInfo(BILLING_TIMEZONE))
    month_start_ict = now_ict.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_utc = month_start_ict.astimezone(timezone.utc).replace(tzinfo=None)

    events = (
        db.query(UsageEvent)
        .filter(
            UsageEvent.user_id == current_user.id,
            UsageEvent.created_at >= month_start_utc,
        )
        .all()
    )
    allowance = get_free_allowance()
    used = {key: 0 for key in allowance}
    for event in events:
        if event.event_type in used:
            used[event.event_type] += max(0, event.quantity)

    free_remaining = {
        key: max(0, allowance[key] - used[key])
        for key in allowance
    }

    entitlements = (
        db.query(UserEntitlement)
        .filter(UserEntitlement.user_id == current_user.id)
        .all()
    )
    remaining = {key: 0 for key in allowance}
    for entitlement in entitlements:
        remaining["analysis"] += max(0, entitlement.analysis_credits)
        remaining["interview"] += max(0, entitlement.interview_credits)
        remaining["cover_letter"] += max(0, entitlement.cover_letter_credits)
        remaining["package"] += max(0, entitlement.package_credits)

    return BillingUsageResponse(
        month=now_ict.strftime("%Y-%m"),
        timezone=BILLING_TIMEZONE,
        free_allowance=_credits(allowance),
        used_this_month=_credits(used),
        free_remaining=_credits(free_remaining),
        remaining_credits=_credits(remaining),
    )


@router.get("/orders", response_model=PaymentOrdersResponse)
def billing_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PaymentOrdersResponse:
    return PaymentOrdersResponse(
        orders=[_order_summary(order) for order in list_orders(db, current_user.id)]
    )


@router.get("/orders/{payment_order_id}", response_model=PaymentOrderDetail)
def billing_order_detail(
    payment_order_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PaymentOrderDetail:
    order = get_owned_order(
        db,
        user_id=current_user.id,
        payment_order_id=payment_order_id,
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    summary = _order_summary(order)
    return PaymentOrderDetail(**summary.model_dump(), credits_granted=None)


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
)
def billing_checkout(
    body: CheckoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    if not settings.ENABLE_BILLING:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="billing is not available",
        )

    plan = get_billing_plan(body.plan_code)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unknown plan code")

    if settings.PAYMENT_PROVIDER != "payos":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="billing provider is not available",
        )

    try:
        provider_client = get_payos_client()
        order, result = create_checkout_order(
            db,
            user_id=current_user.id,
            plan=plan,
            provider_client=provider_client,
        )
    except BillingProviderConfigError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="billing provider is not configured",
        )
    except BillingProviderError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="billing provider request failed",
        )

    return CheckoutResponse(
        payment_order_id=str(order.id),
        provider=order.provider,
        plan_code=order.plan_code,
        amount=order.amount_vnd,
        currency=order.currency,
        status=order.status,
        checkout_url=result.checkout_url,
        expires_at=order.expired_at,
    )


@router.post("/webhooks/payos", response_model=BillingWebhookResponse)
def payos_webhook(
    payload: Annotated[dict[str, Any], Body()],
    db: Session = Depends(get_db),
) -> BillingWebhookResponse:
    """Apply a verified payOS payment notification without app authentication."""
    if not settings.ENABLE_BILLING:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="billing is not available",
        )
    if not settings.PAYOS_CHECKSUM_KEY.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="billing webhook is not configured",
        )

    try:
        process_payos_webhook(
            db,
            payload=payload,
            checksum_key=settings.PAYOS_CHECKSUM_KEY,
        )
    except BillingWebhookSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid webhook signature",
        )
    except BillingWebhookPayloadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid webhook payload",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="webhook processing failed",
        )

    return BillingWebhookResponse()
