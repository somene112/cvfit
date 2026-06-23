"""Phase 7A billing schemas.

Response/request shapes for the Billing & Credits API, matching
``docs/billing_api_contract.md``. Status/credit vocabularies are ``Literal`` types
validated at the schema layer (consistent with the Phase 6 convention).

No provider secrets or raw payloads are represented here. Amounts are integer VND.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# Order lifecycle vocabulary (mirrors PAYMENT_ORDER_STATUS in db.models).
PaymentOrderStatus = Literal[
    "created",
    "pending",
    "paid",
    "cancelled",
    "expired",
    "failed",
    "manual_review",
    "refunded",
]

# Credit type vocabulary (mirrors CREDIT_TYPES in services.billing.plans).
CreditType = Literal["analysis", "interview", "cover_letter", "package"]


class BillingCredits(BaseModel):
    analysis: int = 0
    interview: int = 0
    cover_letter: int = 0
    package: int = 0


class BillingPlan(BaseModel):
    plan_code: str
    name: str
    amount: int  # VND, backend-owned; the frontend must not override it
    currency: str = "VND"
    description: Optional[str] = None
    credits: BillingCredits


class BillingPlansResponse(BaseModel):
    currency: str = "VND"
    plans: List[BillingPlan]


class BillingUsageResponse(BaseModel):
    month: str  # e.g. "2026-06" in Asia/Ho_Chi_Minh
    timezone: str = "Asia/Ho_Chi_Minh"
    free_allowance: BillingCredits
    used_this_month: BillingCredits
    free_remaining: BillingCredits
    remaining_credits: BillingCredits


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Only the plan code is accepted — the amount is resolved server-side.
    plan_code: str = Field(min_length=1, max_length=50)


class CheckoutResponse(BaseModel):
    payment_order_id: str
    provider: str
    plan_code: str
    amount: int
    currency: str = "VND"
    status: PaymentOrderStatus
    checkout_url: str
    expires_at: Optional[datetime] = None


class PaymentOrderSummary(BaseModel):
    payment_order_id: str
    plan_code: str
    amount: int
    currency: str = "VND"
    status: PaymentOrderStatus
    created_at: datetime
    paid_at: Optional[datetime] = None


class PaymentOrderDetail(PaymentOrderSummary):
    credits_granted: Optional[BillingCredits] = None


class PaymentOrdersResponse(BaseModel):
    orders: List[PaymentOrderSummary]


class BillingWebhookResponse(BaseModel):
    ok: Literal[True] = True


class InsufficientCreditsError(BaseModel):
    error: Literal["insufficient_credits"] = "insufficient_credits"
    message: str
    required_credit: CreditType
    pricing_url: str = "/pricing"
