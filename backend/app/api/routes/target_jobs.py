"""Phase 6 Target Jobs backend routes.

Target Jobs are a product layer over the Phase 5 ``applications`` table — no new
table is introduced. All routes require an authenticated user and are scoped by
``user_id``; cross-user access returns 404 (never reveals existence), matching
the Phase 5 applications convention.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import AnalysisJob, Application, ApplicationArtifact, User
from app.db.session import get_db
from app.schemas.target_jobs import (
    AttachAnalysisResponse,
    TargetJobCreate,
    TargetJobListResponse,
    TargetJobPackageResponse,
    TargetJobReadinessResponse,
    TargetJobResponse,
    TargetJobStatus,
    TargetJobUpdate,
)
from app.services.target_jobs import compute_readiness


def require_target_jobs_enabled() -> None:
    """Route-level feature flag. Returns 404 when Target Jobs is disabled."""
    if not settings.ENABLE_PHASE6_TARGET_JOBS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


router = APIRouter(
    prefix="/v1/target-jobs",
    tags=["target-jobs"],
    dependencies=[Depends(require_target_jobs_enabled)],
)


def _to_response(app: Application) -> TargetJobResponse:
    return TargetJobResponse(
        id=str(app.id),
        user_id=str(app.user_id),
        job_title=app.job_title,
        company_name=app.company_name,
        jd_text=app.jd_text,
        target_role=app.target_role,
        source_url=getattr(app, "source_url", None),
        status=app.status,
        best_analysis_job_id=str(app.best_analysis_job_id) if app.best_analysis_job_id else None,
        last_readiness_score=getattr(app, "last_readiness_score", None),
        archived_at=getattr(app, "archived_at", None),
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


def _get_owned_target_job(job_id: uuid.UUID, current_user: User, db: Session) -> Application:
    app = db.get(Application, job_id)
    if app is None or app.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="target job not found")
    return app


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TargetJobResponse)
def create_target_job(
    body: TargetJobCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TargetJobResponse:
    now = datetime.utcnow()
    app = Application(
        id=uuid.uuid4(),
        user_id=current_user.id,
        job_title=body.job_title,
        company_name=body.company_name,
        jd_text=body.jd_text,
        target_role=body.target_role,
        source_url=body.source_url,
        status=body.status or "saved",
        created_at=now,
        updated_at=now,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _to_response(app)


@router.get("", response_model=TargetJobListResponse)
def list_target_jobs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    status_filter: Optional[TargetJobStatus] = Query(default=None, alias="status"),
) -> TargetJobListResponse:
    query = db.query(Application).filter(Application.user_id == current_user.id)
    if status_filter is not None:
        query = query.filter(Application.status == status_filter)
    apps = query.order_by(Application.created_at.desc()).all()
    items = [_to_response(a) for a in apps]
    return TargetJobListResponse(items=items, total=len(items))


@router.get("/{job_id}", response_model=TargetJobResponse)
def get_target_job(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TargetJobResponse:
    return _to_response(_get_owned_target_job(job_id, current_user, db))


@router.patch("/{job_id}", response_model=TargetJobResponse)
def patch_target_job(
    job_id: uuid.UUID,
    body: TargetJobUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TargetJobResponse:
    app = _get_owned_target_job(job_id, current_user, db)

    if body.job_title is not None:
        app.job_title = body.job_title
    if body.company_name is not None:
        app.company_name = body.company_name
    if body.jd_text is not None:
        app.jd_text = body.jd_text
    if body.target_role is not None:
        app.target_role = body.target_role
    if body.source_url is not None:
        app.source_url = body.source_url
    if body.status is not None:
        app.status = body.status
        # Keep archived_at consistent with explicit status changes.
        if body.status == "archived" and app.archived_at is None:
            app.archived_at = datetime.utcnow()
        elif body.status != "archived":
            app.archived_at = None
    app.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(app)
    return _to_response(app)


@router.delete("/{job_id}", response_model=TargetJobResponse)
def archive_target_job(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TargetJobResponse:
    """Soft-archive a target job (preserves data and attached analysis)."""
    app = _get_owned_target_job(job_id, current_user, db)
    app.status = "archived"
    app.archived_at = datetime.utcnow()
    app.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app)
    return _to_response(app)


@router.post("/{job_id}/attach-analysis/{analysis_job_id}", response_model=AttachAnalysisResponse)
def attach_analysis(
    job_id: uuid.UUID,
    analysis_job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AttachAnalysisResponse:
    app = _get_owned_target_job(job_id, current_user, db)

    job = db.get(AnalysisJob, analysis_job_id)
    # 404 for missing or cross-user jobs — never reveal existence.
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis job not found")

    app.best_analysis_job_id = job.id
    readiness = compute_readiness(app, job)
    app.last_readiness_score = int(round(readiness.fit_score)) if readiness.fit_score is not None else None
    app.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app)

    return AttachAnalysisResponse(
        target_job_id=str(app.id),
        best_analysis_job_id=str(app.best_analysis_job_id),
        last_readiness_score=app.last_readiness_score,
    )


@router.get("/{job_id}/readiness", response_model=TargetJobReadinessResponse)
def get_readiness(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TargetJobReadinessResponse:
    app = _get_owned_target_job(job_id, current_user, db)

    job: Optional[AnalysisJob] = None
    if app.best_analysis_job_id is not None:
        candidate = db.get(AnalysisJob, app.best_analysis_job_id)
        # Non-leak: 404 if the attached job belongs to another user.
        if candidate is not None and candidate.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis job not found")
        job = candidate

    readiness = compute_readiness(app, job)
    return TargetJobReadinessResponse(
        target_job_id=str(app.id),
        status=app.status,
        best_analysis_job_id=str(app.best_analysis_job_id) if app.best_analysis_job_id else None,
        fit_score=readiness.fit_score,
        readiness_level=readiness.readiness_level,
        summary=readiness.summary,
        next_actions=readiness.next_actions,
    )


@router.get("/{job_id}/package", response_model=TargetJobPackageResponse)
def get_package(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TargetJobPackageResponse:
    app = _get_owned_target_job(job_id, current_user, db)

    artifacts = (
        db.query(ApplicationArtifact)
        .filter(
            ApplicationArtifact.application_id == app.id,
            ApplicationArtifact.user_id == current_user.id,
            ApplicationArtifact.artifact_type == "application_package",
        )
        .order_by(ApplicationArtifact.created_at.desc())
        .all()
    )
    if not artifacts:
        # Safe empty payload rather than 404 — the workspace UI can show an
        # explicit "no package yet" state without handling an error.
        return TargetJobPackageResponse(target_job_id=str(app.id), has_package=False)

    artifact = artifacts[0]
    return TargetJobPackageResponse(
        target_job_id=str(app.id),
        has_package=True,
        artifact_id=str(artifact.id),
        artifact_type=artifact.artifact_type,
        payload_json=artifact.payload_json,
        created_at=artifact.created_at,
    )
