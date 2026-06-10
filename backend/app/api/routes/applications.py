from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import AnalysisJob, Application, ApplicationArtifact, CareerProfileItem, User
from app.db.session import get_db
from app.schemas.phase5 import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationUpdate,
    ArtifactGeneratedResponse,
    ArtifactResponse,
    AttachAnalysisResponse,
    CoverLetterPatch,
    ReadinessResponse,
)
from app.services.application_package import build_package_payload
from app.services.cover_letter import build_cover_letter_payload

router = APIRouter(prefix="/v1/applications", tags=["applications"])


def _app_to_response(app: Application) -> ApplicationResponse:
    return ApplicationResponse(
        id=str(app.id),
        user_id=str(app.user_id),
        job_title=app.job_title,
        company_name=app.company_name,
        jd_text=app.jd_text,
        target_role=app.target_role,
        status=app.status,
        best_analysis_job_id=str(app.best_analysis_job_id) if app.best_analysis_job_id else None,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


def _get_owned_application(
    application_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Application:
    app = db.get(Application, application_id)
    if app is None or app.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="application not found")
    return app


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApplicationResponse)
def create_application(
    body: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = Application(
        id=uuid.uuid4(),
        user_id=current_user.id,
        job_title=body.job_title,
        company_name=body.company_name,
        jd_text=body.jd_text,
        target_role=body.target_role,
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _app_to_response(app)


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    apps = (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    items = [_app_to_response(a) for a in apps]
    return ApplicationListResponse(items=items, total=len(items))


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = _get_owned_application(application_id, current_user, db)
    return _app_to_response(app)


@router.patch("/{application_id}", response_model=ApplicationResponse)
def patch_application(
    application_id: uuid.UUID,
    body: ApplicationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = _get_owned_application(application_id, current_user, db)

    if body.job_title is not None:
        app.job_title = body.job_title
    if body.company_name is not None:
        app.company_name = body.company_name
    if body.jd_text is not None:
        app.jd_text = body.jd_text
    if body.target_role is not None:
        app.target_role = body.target_role
    if body.status is not None:
        app.status = body.status
    app.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(app)
    return _app_to_response(app)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_application(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> None:
    app = _get_owned_application(application_id, current_user, db)
    db.delete(app)
    db.commit()


@router.post("/{application_id}/attach-analysis/{job_id}", response_model=AttachAnalysisResponse)
def attach_analysis(
    application_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AttachAnalysisResponse:
    app = _get_owned_application(application_id, current_user, db)

    job = db.get(AnalysisJob, job_id)
    # Return 404 for missing or cross-user jobs to avoid revealing existence
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis job not found")

    app.best_analysis_job_id = job.id
    app.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app)
    return AttachAnalysisResponse(
        application_id=str(app.id),
        best_analysis_job_id=str(app.best_analysis_job_id),
    )


def _artifact_to_response(artifact: ApplicationArtifact) -> ArtifactResponse:
    return ArtifactResponse(
        id=str(artifact.id),
        application_id=str(artifact.application_id),
        artifact_type=artifact.artifact_type,
        payload_json=artifact.payload_json,
        created_at=artifact.created_at,
    )


def _get_latest_artifact(
    db: Session,
    application_id: uuid.UUID,
    user_id: uuid.UUID,
    artifact_type: str,
) -> Optional[ApplicationArtifact]:
    results = (
        db.query(ApplicationArtifact)
        .filter(
            ApplicationArtifact.application_id == application_id,
            ApplicationArtifact.user_id == user_id,
            ApplicationArtifact.artifact_type == artifact_type,
        )
        .order_by(ApplicationArtifact.created_at.desc())
        .all()
    )
    return results[0] if results else None


def _get_profile_items(db: Session, user_id: uuid.UUID) -> list:
    return (
        db.query(CareerProfileItem)
        .filter(CareerProfileItem.user_id == user_id)
        .all()
    )


@router.get("/{application_id}/readiness", response_model=ReadinessResponse)
def get_readiness(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ReadinessResponse:
    app = _get_owned_application(application_id, current_user, db)

    if app.best_analysis_job_id is None:
        return ReadinessResponse(
            application_id=str(app.id),
            status=app.status,
            best_analysis_job_id=None,
            fit_score=None,
            readiness_level="not_started",
            summary="No analysis job is attached to this application yet.",
            next_actions=[
                "Upload a CV and run an analysis for this job description.",
                "Attach the analysis result to this application using the attach-analysis endpoint.",
            ],
        )

    job = db.get(AnalysisJob, app.best_analysis_job_id)
    if job is None or job.status != "succeeded" or job.result_json is None:
        return ReadinessResponse(
            application_id=str(app.id),
            status=app.status,
            best_analysis_job_id=str(app.best_analysis_job_id),
            fit_score=None,
            readiness_level="not_started",
            summary="The attached analysis job has not completed yet.",
            next_actions=["Wait for the analysis job to complete, then check readiness again."],
        )

    result = job.result_json
    # Use explicit is-not-None checks so a score of 0.0 is not skipped.
    fit_score: Optional[float] = None
    for candidate in (
        result.get("overall_fit_score"),
        (result.get("result") or {}).get("fit_score"),
        (result.get("scores") or {}).get("fit_score"),
    ):
        if candidate is not None:
            try:
                fit_score = float(candidate)
            except (TypeError, ValueError):
                pass
            break

    if fit_score is None:
        readiness_level = "not_started"
        next_actions = ["Attach a completed analysis job to this application."]
    elif fit_score >= 75:
        readiness_level = "ready"
        next_actions = [
            "Review missing skills and add evidence to your career profile.",
            "Generate an application package to prepare your cover letter and interview practice.",
        ]
    elif fit_score >= 55:
        readiness_level = "almost_ready"
        next_actions = [
            "Address the top missing skills from the analysis.",
            "Add project evidence for matched skills to your career profile.",
        ]
    else:
        readiness_level = "needs_work"
        next_actions = [
            "Review missing skills from the latest analysis.",
            "Add project evidence to your career profile.",
            "Consider revising your CV to address high-priority JD requirements.",
        ]

    return ReadinessResponse(
        application_id=str(app.id),
        status=app.status,
        best_analysis_job_id=str(app.best_analysis_job_id),
        fit_score=fit_score,
        readiness_level=readiness_level,
        summary="Application readiness is based on the attached analysis result.",
        next_actions=next_actions,
    )


# ---------------------------------------------------------------------------
# Package endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{application_id}/package/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=ArtifactGeneratedResponse,
)
def generate_package(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ArtifactGeneratedResponse:
    app = _get_owned_application(application_id, current_user, db)

    if app.best_analysis_job_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="attach an analysis job before generating a package",
        )

    job = db.get(AnalysisJob, app.best_analysis_job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis job not found")

    profile_items = _get_profile_items(db, current_user.id)
    payload = build_package_payload(app, job, profile_items)

    artifact = ApplicationArtifact(
        id=uuid.uuid4(),
        user_id=current_user.id,
        application_id=app.id,
        artifact_type="application_package",
        payload_json=payload,
        created_at=datetime.utcnow(),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return ArtifactGeneratedResponse(
        application_id=str(app.id),
        artifact_id=str(artifact.id),
        status="generated",
        artifact_type="application_package",
    )


@router.get("/{application_id}/package/download")
def download_package(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> JSONResponse:
    app = _get_owned_application(application_id, current_user, db)
    artifact = _get_latest_artifact(db, app.id, current_user.id, "application_package")
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no package generated yet")
    return JSONResponse(
        content={
            "download_format": "json",
            "application_id": str(app.id),
            "artifact_id": str(artifact.id),
            "artifact_type": "application_package",
            "payload_json": artifact.payload_json,
        },
        headers={"Content-Disposition": "attachment; filename=application_package.json"},
    )


@router.get("/{application_id}/package", response_model=ArtifactResponse)
def get_package(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ArtifactResponse:
    app = _get_owned_application(application_id, current_user, db)
    artifact = _get_latest_artifact(db, app.id, current_user.id, "application_package")
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no package generated yet")
    return _artifact_to_response(artifact)


# ---------------------------------------------------------------------------
# Cover letter endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{application_id}/cover-letter/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=ArtifactGeneratedResponse,
)
def generate_cover_letter(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ArtifactGeneratedResponse:
    app = _get_owned_application(application_id, current_user, db)

    if app.best_analysis_job_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="attach an analysis job before generating a cover letter",
        )

    job = db.get(AnalysisJob, app.best_analysis_job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis job not found")

    profile_items = _get_profile_items(db, current_user.id)
    payload = build_cover_letter_payload(app, job, profile_items)

    artifact = ApplicationArtifact(
        id=uuid.uuid4(),
        user_id=current_user.id,
        application_id=app.id,
        artifact_type="cover_letter_draft",
        payload_json=payload,
        created_at=datetime.utcnow(),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return ArtifactGeneratedResponse(
        application_id=str(app.id),
        artifact_id=str(artifact.id),
        status="generated",
        artifact_type="cover_letter_draft",
    )


@router.get("/{application_id}/cover-letter", response_model=ArtifactResponse)
def get_cover_letter(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ArtifactResponse:
    app = _get_owned_application(application_id, current_user, db)
    artifact = _get_latest_artifact(db, app.id, current_user.id, "cover_letter_draft")
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no cover letter draft generated yet")
    return _artifact_to_response(artifact)


@router.patch("/{application_id}/cover-letter", response_model=ArtifactResponse)
def patch_cover_letter(
    application_id: uuid.UUID,
    body: CoverLetterPatch,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ArtifactResponse:
    app = _get_owned_application(application_id, current_user, db)
    artifact = _get_latest_artifact(db, app.id, current_user.id, "cover_letter_draft")
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no cover letter draft generated yet")

    payload = dict(artifact.payload_json)
    if body.opening is not None:
        payload["opening"] = body.opening
    if body.why_role_company is not None:
        payload["why_role_company"] = body.why_role_company
    if body.relevant_evidence is not None:
        payload["relevant_evidence"] = body.relevant_evidence
    if body.contribution_fit is not None:
        payload["contribution_fit"] = body.contribution_fit
    if body.closing is not None:
        payload["closing"] = body.closing
    if body.review_notes is not None:
        payload["review_notes"] = body.review_notes
    # Always preserve disclaimer — not patchable.
    payload["disclaimer"] = artifact.payload_json.get("disclaimer", "")

    artifact.payload_json = payload
    db.commit()
    db.refresh(artifact)

    return _artifact_to_response(artifact)
