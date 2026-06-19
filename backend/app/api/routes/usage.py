"""Phase 6 Usage / Plan / Credits Shell routes.

Read-only and informational. Usage is computed from the authenticated user's own
records; no payment, checkout, or paid-plan enforcement exists. Responses contain
integer counts and static copy only — never raw CV/JD/answer text or tokens.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.usage import PlanItem, PlansResponse, UsageResponse
from app.services.usage import (
    DEMO_LIMITS,
    FREE_DEMO_PLAN,
    build_plans,
    compute_usage,
    compute_warnings,
)


def require_usage_enabled() -> None:
    if not settings.ENABLE_PHASE6_USAGE_SHELL:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


router = APIRouter(
    prefix="/v1",
    tags=["usage"],
    dependencies=[Depends(require_usage_enabled)],
)

USAGE_LIMITATIONS = [
    "Usage is informational only. No payment or checkout is enabled.",
    "Counts are cumulative across your account for this demo (no billing period reset).",
]

PLAN_LIMITATIONS = [
    "This is a demo plan list. No real payment, checkout, or paid subscription is available.",
]


@router.get("/usage/me", response_model=UsageResponse)
def get_my_usage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> UsageResponse:
    usage = compute_usage(db, current_user.id)
    warnings = compute_warnings(usage, DEMO_LIMITS)
    return UsageResponse(
        plan_id=FREE_DEMO_PLAN["id"],
        plan_name=FREE_DEMO_PLAN["name"],
        period="all_time",
        usage=usage,
        limits=dict(DEMO_LIMITS),
        warnings=warnings,
        limitations=USAGE_LIMITATIONS,
        reset_at=None,
        enforcement_enabled=False,
    )


@router.get("/plans", response_model=PlansResponse)
def get_plans(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PlansResponse:
    plans = [PlanItem(**p) for p in build_plans()]
    return PlansResponse(
        plans=plans,
        upgrade_available=False,
        upgrade_teaser_disabled=True,
        limitations=PLAN_LIMITATIONS,
    )
