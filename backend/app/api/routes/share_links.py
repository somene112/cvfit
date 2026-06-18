"""Phase 6 Shareable Readiness routes.

Authenticated owners manage share links under ``/v1/share-links``; an
unauthenticated, redacted public view lives at ``/v1/public/share/{token}``.

Privacy rules enforced here:
* Only the SHA-256 token hash is stored; the raw token is returned once on create
  and never persisted, logged, or echoed afterward.
* ``token_hash`` is never exposed in any response.
* Revoked or expired links resolve to 404 (no existence leak).
* The public view is redacted by default — no raw CV/JD text.

The whole feature is gated behind ``ENABLE_PHASE6_SHARE_LINKS`` (default off until
the privacy review passes); when disabled every route returns 404.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import AnalysisJob, Application, ShareLink, User
from app.db.session import get_db
from app.schemas.share_links import (
    PublicReadinessView,
    ShareLinkCreate,
    ShareLinkCreateResponse,
    ShareLinkListResponse,
    ShareLinkResponse,
    ShareLinkUpdate,
    ShareVisibility,
)
from app.services.share import (
    DEFAULT_VISIBILITY,
    build_public_view,
    generate_share_token,
    hash_share_token,
    is_link_active,
)
from app.services.share.links import tokens_match
from app.services.target_jobs import compute_readiness


def require_share_enabled() -> None:
    if not settings.ENABLE_PHASE6_SHARE_LINKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


router = APIRouter(
    prefix="/v1/share-links",
    tags=["share-links"],
    dependencies=[Depends(require_share_enabled)],
)
# Public, unauthenticated — but still gated by the feature flag.
public_router = APIRouter(
    prefix="/v1/public",
    tags=["share-links-public"],
    dependencies=[Depends(require_share_enabled)],
)


def _owned_application(app_id: uuid.UUID, user: User, db: Session) -> Application:
    app = db.get(Application, app_id)
    if app is None or app.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="target not found")
    return app


def _get_owned_link(link_id: uuid.UUID, user: User, db: Session) -> ShareLink:
    link = db.get(ShareLink, link_id)
    if link is None or link.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="share link not found")
    return link


def _visibility_of(link: ShareLink) -> ShareVisibility:
    return ShareVisibility.model_validate(link.visibility_json or DEFAULT_VISIBILITY)


def _to_response(link: ShareLink) -> ShareLinkResponse:
    return ShareLinkResponse(
        id=str(link.id),
        target_type=link.target_type,
        target_id=str(link.target_id),
        visibility=_visibility_of(link),
        expires_at=link.expires_at,
        revoked_at=link.revoked_at,
        is_active=is_link_active(link),
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ShareLinkCreateResponse)
def create_share_link(
    body: ShareLinkCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ShareLinkCreateResponse:
    try:
        target_id = uuid.UUID(body.target_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="target not found")

    # Both target_type values resolve to an owned Application row.
    _owned_application(target_id, current_user, db)

    visibility = (body.visibility or ShareVisibility()).model_dump()

    raw_token = generate_share_token()
    now = datetime.utcnow()
    link = ShareLink(
        id=uuid.uuid4(),
        user_id=current_user.id,
        target_type=body.target_type,
        target_id=target_id,
        token_hash=hash_share_token(raw_token),
        visibility_json=visibility,
        expires_at=body.expires_at,
        revoked_at=None,
        created_at=now,
        updated_at=None,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    base = _to_response(link)
    return ShareLinkCreateResponse(
        **base.model_dump(),
        share_token=raw_token,
        public_path=f"/v1/public/share/{raw_token}",
    )


@router.get("", response_model=ShareLinkListResponse)
def list_share_links(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ShareLinkListResponse:
    links = (
        db.query(ShareLink)
        .filter(ShareLink.user_id == current_user.id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )
    items = [_to_response(l) for l in links]
    return ShareLinkListResponse(items=items, total=len(items))


@router.get("/{link_id}", response_model=ShareLinkResponse)
def get_share_link(
    link_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ShareLinkResponse:
    return _to_response(_get_owned_link(link_id, current_user, db))


@router.patch("/{link_id}", response_model=ShareLinkResponse)
def patch_share_link(
    link_id: uuid.UUID,
    body: ShareLinkUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ShareLinkResponse:
    link = _get_owned_link(link_id, current_user, db)
    if body.visibility is not None:
        link.visibility_json = body.visibility.model_dump()
    if body.expires_at is not None:
        link.expires_at = body.expires_at
    link.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(link)
    return _to_response(link)


@router.delete("/{link_id}", response_model=ShareLinkResponse)
def revoke_share_link(
    link_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ShareLinkResponse:
    """Soft-revoke (sets ``revoked_at``); the row is preserved for audit."""
    link = _get_owned_link(link_id, current_user, db)
    if link.revoked_at is None:
        link.revoked_at = datetime.utcnow()
        link.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(link)
    return _to_response(link)


@public_router.get("/share/{token}", response_model=PublicReadinessView)
def public_share_view(
    token: str,
    db: Session = Depends(get_db),
) -> PublicReadinessView:
    token_hash = hash_share_token(token)
    matches = db.query(ShareLink).filter(ShareLink.token_hash == token_hash).all()
    # Constant-time confirm + active check; any miss returns an indistinguishable 404.
    link = next((l for l in matches if tokens_match(token, l.token_hash)), None)
    if link is None or not is_link_active(link):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    application = db.get(Application, link.target_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    analysis_job: Optional[AnalysisJob] = None
    if application.best_analysis_job_id is not None:
        analysis_job = db.get(AnalysisJob, application.best_analysis_job_id)

    readiness = compute_readiness(application, analysis_job)
    view = build_public_view(link, application, analysis_job, readiness)
    return PublicReadinessView(**view)
