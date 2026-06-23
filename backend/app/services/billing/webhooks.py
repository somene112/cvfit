"""payOS webhook verification, audit, and transactional payment application."""

from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import json
from typing import Any
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import PaymentOrder, PaymentWebhookEvent
from app.services.billing.credits import get_entitlement_for_order, grant_order_credits
from app.services.billing.plans import BILLING_CURRENCY, get_billing_plan


class BillingWebhookError(RuntimeError):
    """Safe base error for webhook handling."""


class BillingWebhookPayloadError(BillingWebhookError):
    """Raised when the webhook envelope cannot be safely interpreted."""


class BillingWebhookSignatureError(BillingWebhookError):
    """Raised when the payOS signature is absent or invalid."""


def _sorted_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sorted_json_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted_json_value(item) for item in value]
    return value


def _payos_value_to_string(value: Any) -> str:
    if value is None or value in ("null", "NULL"):
        return ""
    if isinstance(value, list):
        return json.dumps(
            [_sorted_json_value(item) for item in value],
            ensure_ascii=False,
            separators=(",", ":"),
        )
    if isinstance(value, dict):
        return json.dumps(
            _sorted_json_value(value),
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return str(value)


def canonicalize_payos_data(data: dict[str, Any]) -> str:
    """Serialize payOS payment-request data using the provider's signing rules."""
    return "&".join(
        f"{key}={_payos_value_to_string(data[key])}"
        for key in sorted(data)
    )


def create_payos_data_signature(data: dict[str, Any], checksum_key: str) -> str:
    canonical_data = canonicalize_payos_data(data)
    return hmac.new(
        checksum_key.encode("utf-8"),
        canonical_data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_payos_webhook_signature(
    payload: dict[str, Any],
    checksum_key: str,
) -> tuple[dict[str, Any], str, str]:
    data = payload.get("data")
    signature = payload.get("signature")
    if not isinstance(data, dict) or not isinstance(signature, str) or not signature:
        raise BillingWebhookPayloadError("invalid webhook payload")

    canonical_data = canonicalize_payos_data(data)
    expected = hmac.new(
        checksum_key.encode("utf-8"),
        canonical_data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected.lower(), signature.lower()):
        raise BillingWebhookSignatureError("invalid webhook signature")
    return data, signature, canonical_data


def _safe_string(value: Any, *, max_length: int = 255) -> str | None:
    if value is None or isinstance(value, (dict, list)):
        return None
    result = str(value)
    return result[:max_length] if result else None


def _finish_event(
    db: Session,
    event: PaymentWebhookEvent,
    *,
    status: str,
    processed_at: datetime,
    error_message: str | None = None,
) -> None:
    event.status = status
    event.processed_at = processed_at
    event.error_message = error_message
    db.commit()


def _mark_manual_review(
    db: Session,
    event: PaymentWebhookEvent,
    order: PaymentOrder | None,
    *,
    processed_at: datetime,
    reason: str,
) -> None:
    if order is not None and order.status == "pending":
        order.status = "manual_review"
        order.updated_at = processed_at
    _finish_event(
        db,
        event,
        status="manual_review",
        processed_at=processed_at,
        error_message=reason,
    )


def process_payos_webhook(
    db: Session,
    *,
    payload: dict[str, Any],
    checksum_key: str,
) -> None:
    """Verify and apply one payOS webhook, committing all effects atomically."""
    data, signature, canonical_data = verify_payos_webhook_signature(payload, checksum_key)
    payload_hash = hashlib.sha256(canonical_data.encode("utf-8")).hexdigest()
    signature_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()

    existing_event = (
        db.query(PaymentWebhookEvent)
        .filter(PaymentWebhookEvent.payload_hash == payload_hash)
        .first()
    )
    if existing_event is not None:
        return

    now = datetime.utcnow()
    provider_order_code = _safe_string(data.get("orderCode"))
    event = PaymentWebhookEvent(
        id=uuid.uuid4(),
        provider="payos",
        provider_event_id=_safe_string(data.get("reference")),
        provider_order_code=provider_order_code,
        payload_hash=payload_hash,
        signature_hash=signature_hash,
        status="received",
        received_at=now,
    )
    db.add(event)

    try:
        db.flush()
    except IntegrityError:
        # A concurrent delivery inserted the same payload hash first.
        db.rollback()
        return

    try:
        # Only fields inside ``data`` are covered by the payOS signature. Do not
        # make payment decisions from unsigned envelope fields.
        if data.get("code") != "00":
            _finish_event(
                db,
                event,
                status="rejected",
                processed_at=now,
                error_message="provider did not report a successful payment",
            )
            return

        if provider_order_code is None:
            _mark_manual_review(
                db,
                event,
                None,
                processed_at=now,
                reason="missing provider order code",
            )
            return

        order_query = db.query(PaymentOrder).filter(
            PaymentOrder.provider == "payos",
            PaymentOrder.provider_order_code == provider_order_code,
        )
        if hasattr(order_query, "with_for_update"):
            order_query = order_query.with_for_update()
        order = order_query.first()
        if order is None:
            _mark_manual_review(
                db,
                event,
                None,
                processed_at=now,
                reason="unknown payment order",
            )
            return

        plan = get_billing_plan(order.plan_code)
        if (
            plan is None
            or order.amount_vnd != plan["price_vnd"]
            or order.currency != BILLING_CURRENCY
            or plan["currency"] != BILLING_CURRENCY
        ):
            _mark_manual_review(
                db,
                event,
                order,
                processed_at=now,
                reason="payment order configuration mismatch",
            )
            return

        amount = data.get("amount")
        currency = data.get("currency")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount != order.amount_vnd:
            _mark_manual_review(
                db,
                event,
                order,
                processed_at=now,
                reason="payment amount mismatch",
            )
            return
        if currency != BILLING_CURRENCY:
            _mark_manual_review(
                db,
                event,
                order,
                processed_at=now,
                reason="payment currency mismatch",
            )
            return

        payment_link_id = _safe_string(data.get("paymentLinkId"))
        if (
            order.provider_payment_link_id
            and payment_link_id != order.provider_payment_link_id
        ):
            _mark_manual_review(
                db,
                event,
                order,
                processed_at=now,
                reason="payment link mismatch",
            )
            return

        if order.status == "paid":
            _finish_event(db, event, status="duplicate", processed_at=now)
            return
        if order.status != "pending":
            _mark_manual_review(
                db,
                event,
                order,
                processed_at=now,
                reason="payment order is not payable",
            )
            return

        if get_entitlement_for_order(db, order.id) is not None:
            _mark_manual_review(
                db,
                event,
                order,
                processed_at=now,
                reason="payment order already has a credit grant",
            )
            return

        order.status = "paid"
        order.paid_at = now
        order.updated_at = now
        _entitlement, granted = grant_order_credits(
            db,
            order=order,
            plan=plan,
            granted_at=now,
        )
        if not granted:
            raise RuntimeError("credit grant conflict")
        event.status = "applied"
        event.processed_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise
