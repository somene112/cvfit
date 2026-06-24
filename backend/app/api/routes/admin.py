"""Admin Monitoring MVP routes.

Read-only, aggregate-only operator dashboard mounted under ``/v1/admin``. Every
route requires an authenticated user whose email is in ``ADMIN_EMAILS``
(``require_admin_user``): unauthenticated → 401, authenticated non-admin → 403.

These routes never mutate data and never return raw user content, emails (other
than the caller's own in ``/me``), tokens, secrets, checkout URLs, payment
signatures, or webhook payloads. There are deliberately no admin actions to
delete/edit users, grant credits, mark orders paid, or retry webhooks.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.admin import (
    AdminMeResponse,
    AdminOverviewResponse,
    RecentActivityResponse,
)
from app.services.admin import build_overview, build_recent_activity

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/me", response_model=AdminMeResponse)
def admin_me(
    current_user: Annotated[User, Depends(require_admin_user)],
) -> AdminMeResponse:
    """Confirm the caller is an admin. Non-admins never reach here (403)."""
    return AdminMeResponse(is_admin=True, email=current_user.email)


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(
    _admin: Annotated[User, Depends(require_admin_user)],
    db: Session = Depends(get_db),
) -> AdminOverviewResponse:
    """Safe aggregate system metrics + current feature flags."""
    return AdminOverviewResponse(**build_overview(db))


@router.get("/recent-activity", response_model=RecentActivityResponse)
def admin_recent_activity(
    _admin: Annotated[User, Depends(require_admin_user)],
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> RecentActivityResponse:
    """Recent usage events as masked, content-free metadata."""
    items = build_recent_activity(db, limit=limit)
    return RecentActivityResponse(items=items, total=len(items))
