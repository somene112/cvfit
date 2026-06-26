import uuid
import hashlib
import hmac
import secrets
from pathlib import Path
from typing import Annotated
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_optional_current_user
from app.core.config import settings
from app.db.session import get_db
from app.db.models import AnalysisJob, CVFile, JDDoc, User
from app.schemas.requests import ScoreCreateRequest
from app.schemas.responses import (
    JobCreateResponse,
    JobHistoryItemResponse,
    JobHistoryResponse,
    JobStatusResponse,
    JobResultResponse,
    JobReanalysisResponse,
    JobComparisonResponse,
)
from app.services.comparison import compare_results
from app.services.billing.credit_gating import consume_credit, ensure_credit_available
from app.services.storage import StorageNotFoundError, UploadValidationError, get_storage, save_upload
from app.api.routes.utils import parse_uuid_or_400

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])
SUPPORTED_CV_EXTENSIONS = {".pdf", ".docx"}


def _new_access_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_access_token(access_token: str) -> str:
    return hashlib.sha256(access_token.encode("utf-8")).hexdigest()


def _verify_access_token_or_403(job: AnalysisJob, access_token: str | None) -> None:
    if not access_token or not job.access_token_hash:
        raise HTTPException(status_code=403, detail="invalid access token")
    if not hmac.compare_digest(_hash_access_token(access_token), job.access_token_hash):
        raise HTTPException(status_code=403, detail="invalid access token")


def _access_token_matches(job: AnalysisJob, access_token: str | None) -> bool:
    if not access_token or not job.access_token_hash:
        return False
    return hmac.compare_digest(_hash_access_token(access_token), job.access_token_hash)


def _user_owns_job(job: AnalysisJob, current_user: User | None) -> bool:
    return current_user is not None and job.user_id is not None and job.user_id == current_user.id


def _authorize_job_access_or_403(
    job: AnalysisJob,
    access_token: str | None,
    current_user: User | None,
) -> None:
    if _access_token_matches(job, access_token) or _user_owns_job(job, current_user):
        return
    raise HTTPException(status_code=403, detail="invalid access token")


INTERNAL_RESPONSE_KEYS = {
    "access_token",
    "access_token_hash",
    "Authorization",
    "Bearer",
    "JWT",
    "bucket",
    "cv_text",
    "file_path",
    "local_path",
    "object_key",
    "raw_cv_text",
    "report_docx_path",
    "s3_key",
    "storage_path",
}


def _scrub_internal_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _scrub_internal_fields(item)
            for key, item in value.items()
            if key not in INTERNAL_RESPONSE_KEYS
        }
    if isinstance(value, list):
        return [_scrub_internal_fields(item) for item in value]
    return value


def _extract_fit_score(result: dict) -> float | None:
    if not isinstance(result, dict):
        return None
    scores = result.get("scores", {})
    if isinstance(scores, dict) and scores.get("fit_score") is not None:
        return scores.get("fit_score")
    if result.get("fit_score") is not None:
        return result.get("fit_score")
    overall = result.get("overall", {})
    if isinstance(overall, dict):
        return overall.get("fit_score")
    return None


def _result_contract_fields(result: dict) -> dict:
    skills = result.get("skills", {})
    skill_gap = result.get("skill_gap", {})
    matched = skills.get("matched_must_groups", []) + skills.get("matched_nice_groups", [])
    missing = skill_gap.get("missing_must_have", []) + skill_gap.get("missing_nice_to_have", [])
    overall = result.get("overall", {}) if isinstance(result.get("overall"), dict) else {}

    return {
        "overall_fit_score": _extract_fit_score(result),
        "summary": overall.get("summary") or "Analysis complete.",
        "strengths": matched,
        "missing_skills": missing,
        "recommendations": result.get("improvement_actions")
        or result.get("cv_improvements", []) + skill_gap.get("learn_suggestions", []),
        "evidence": result.get("evidence", []),
    }


def _history_item(job: AnalysisJob) -> JobHistoryItemResponse:
    result_json = job.result_json or {}
    jd_doc = getattr(job, "jd_doc", None)
    return JobHistoryItemResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        overall_fit_score=_extract_fit_score(result_json),
        has_report=bool(job.report_docx_path),
        target_role=getattr(jd_doc, "role", None),
        parent_job_id=str(job.parent_job_id) if getattr(job, "parent_job_id", None) else None,
        analysis_group_id=getattr(job, "analysis_group_id", None),
        revision_number=getattr(job, "revision_number", 1) or 1,
    )


@router.post("/create-score", response_model=JobCreateResponse)
def create_score_job(
    payload: ScoreCreateRequest,
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
):
    if settings.ENABLE_CREDIT_GATING and current_user is None:
        raise HTTPException(status_code=401, detail="authentication required")
    cv_id = parse_uuid_or_400(payload.cv_file_id, "cv_file_id")
    cv = db.get(CVFile, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="cv_file_id not found")

    if current_user is not None:
        ensure_credit_available(db, current_user.id, "analysis")

    jd = JDDoc(id=uuid.uuid4(), jd_text=payload.jd_text, role=payload.options.target_role)
    db.add(jd)
    db.flush()

    access_token = _new_access_token()
    job = AnalysisJob(
        id=uuid.uuid4(),
        cv_file_id=cv.id,
        jd_id=jd.id,
        status="queued",
        progress=0,
        access_token_hash=_hash_access_token(access_token),
        user_id=current_user.id if current_user else None,
    )
    db.add(job)
    if current_user is not None:
        # Async MVP: consume when the job is durably accepted, before enqueue.
        consume_credit(db, current_user.id, "analysis", related_job_id=job.id)
    db.commit()

    # enqueue (pass the requested generation language; options.language defaults to "vi")
    from app.workers.tasks import run_job
    run_job.delay(str(job.id), payload.options.language)
    return JobCreateResponse(job_id=str(job.id), access_token=access_token)


@router.get("/history", response_model=JobHistoryResponse)
def job_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(AnalysisJob)
        .filter_by(user_id=current_user.id)
        .order_by(AnalysisJob.created_at.desc())
        .all()
    )
    return JobHistoryResponse(items=[_history_item(job) for job in jobs])


@router.post("/{job_id}/reanalyze", response_model=JobReanalysisResponse)
def reanalyze_job(
    job_id: str,
    file: UploadFile = File(...),
    jd_text: str | None = Form(default=None),
    access_token: str | None = Form(default=None),
    language: str = Form(default="vi"),
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
):
    if settings.ENABLE_CREDIT_GATING and current_user is None:
        raise HTTPException(status_code=401, detail="authentication required")
    parent_id = parse_uuid_or_400(job_id, "job_id")
    parent = db.get(AnalysisJob, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="job not found")
    _authorize_reanalysis_parent_or_403(parent, access_token, current_user)
    if settings.ENABLE_CREDIT_GATING and parent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="job ownership required")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_CV_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only pdf/docx supported")

    parent_jd = db.get(JDDoc, parent.jd_id)
    if not parent_jd:
        raise HTTPException(status_code=409, detail="parent job is missing JD data")
    child_jd_text = jd_text if jd_text and jd_text.strip() else parent_jd.jd_text

    if current_user is not None:
        ensure_credit_available(db, current_user.id, "analysis")

    try:
        path, digest, mime = save_upload(file)
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    group_id = _ensure_analysis_group(db, parent)
    revision_number = _next_revision_number(db, group_id)

    cv = CVFile(
        id=uuid.uuid4(),
        original_filename=file.filename,
        mime_type=mime,
        storage_path=path,
        sha256=digest,
    )
    jd = JDDoc(id=uuid.uuid4(), jd_text=child_jd_text, role=getattr(parent_jd, "role", None))
    child_access_token = _new_access_token()
    child = AnalysisJob(
        id=uuid.uuid4(),
        cv_file_id=cv.id,
        jd_id=jd.id,
        status="queued",
        progress=0,
        access_token_hash=_hash_access_token(child_access_token),
        user_id=current_user.id if current_user else getattr(parent, "user_id", None),
        parent_job_id=parent.id,
        analysis_group_id=group_id,
        revision_number=revision_number,
    )
    db.add(cv)
    db.add(jd)
    db.add(child)
    if current_user is not None:
        # Reanalysis follows the same accepted-job consumption rule.
        consume_credit(db, current_user.id, "analysis", related_job_id=child.id)
    db.commit()

    from app.workers.tasks import run_job
    run_job.delay(str(child.id), language)

    return JobReanalysisResponse(
        job_id=str(child.id),
        access_token=child_access_token,
        parent_job_id=str(parent.id),
        analysis_group_id=group_id,
        revision_number=revision_number,
    )


@router.get("/{base_job_id}/comparison/{new_job_id}", response_model=JobComparisonResponse)
def job_comparison(
    base_job_id: str,
    new_job_id: str,
    access_token: str | None = None,
    base_access_token: str | None = None,
    new_access_token: str | None = None,
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
):
    base_uuid = parse_uuid_or_400(base_job_id, "base_job_id")
    new_uuid = parse_uuid_or_400(new_job_id, "new_job_id")
    base_job = db.get(AnalysisJob, base_uuid)
    new_job = db.get(AnalysisJob, new_uuid)
    if not base_job or not new_job:
        raise HTTPException(status_code=404, detail="job not found")

    _authorize_comparison_or_403(
        base_job,
        new_job,
        current_user=current_user,
        access_token=access_token,
        base_access_token=base_access_token,
        new_access_token=new_access_token,
    )
    if not _jobs_are_comparable(base_job, new_job):
        raise HTTPException(status_code=409, detail="jobs are not linked or comparable")
    if base_job.status != "succeeded" or new_job.status != "succeeded":
        raise HTTPException(status_code=409, detail="comparison requires completed jobs")
    if not base_job.result_json or not new_job.result_json:
        raise HTTPException(status_code=409, detail="comparison requires result data")

    payload = compare_results(
        _scrub_internal_fields(base_job.result_json),
        _scrub_internal_fields(new_job.result_json),
        base_job_id=str(base_job.id),
        new_job_id=str(new_job.id),
    )
    return JobComparisonResponse(**payload)


@router.get("/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str, db: Session = Depends(get_db)):
    job_uuid = parse_uuid_or_400(job_id, "job_id")
    job = db.get(AnalysisJob, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(
        job_id=job_id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        error=job.error_message,
    )


def _authorize_reanalysis_parent_or_403(
    parent: AnalysisJob,
    access_token: str | None,
    current_user: User | None,
) -> None:
    if current_user is not None:
        if _user_owns_job(parent, current_user):
            return
        raise HTTPException(status_code=403, detail="invalid access token")
    _verify_access_token_or_403(parent, access_token)


def _ensure_analysis_group(db: Session, parent: AnalysisJob) -> str:
    group_id = getattr(parent, "analysis_group_id", None)
    if not group_id:
        group_id = f"grp_{uuid.uuid4().hex}"
        parent.analysis_group_id = group_id
    if not getattr(parent, "revision_number", None):
        parent.revision_number = 1
    db.flush()
    return group_id


def _next_revision_number(db: Session, group_id: str) -> int:
    try:
        jobs = db.query(AnalysisJob).filter_by(analysis_group_id=group_id).all()
    except AttributeError:
        jobs = []
    revisions = [getattr(job, "revision_number", 1) or 1 for job in jobs]
    return max(revisions or [1]) + 1


def _authorize_comparison_or_403(
    base_job: AnalysisJob,
    new_job: AnalysisJob,
    *,
    current_user: User | None,
    access_token: str | None,
    base_access_token: str | None,
    new_access_token: str | None,
) -> None:
    if current_user is not None:
        if _user_owns_job(base_job, current_user) and _user_owns_job(new_job, current_user):
            return
        raise HTTPException(status_code=403, detail="invalid access token")

    if base_access_token is not None or new_access_token is not None:
        if _access_token_matches(base_job, base_access_token) and _access_token_matches(new_job, new_access_token):
            return
        raise HTTPException(status_code=403, detail="invalid access token")

    if _same_analysis_group(base_job, new_job) and _access_token_matches(new_job, access_token):
        return
    raise HTTPException(status_code=403, detail="invalid access token")


def _jobs_are_comparable(base_job: AnalysisJob, new_job: AnalysisJob) -> bool:
    if _same_analysis_group(base_job, new_job):
        return True
    return getattr(new_job, "parent_job_id", None) == getattr(base_job, "id", None)


def _same_analysis_group(base_job: AnalysisJob, new_job: AnalysisJob) -> bool:
    base_group = getattr(base_job, "analysis_group_id", None)
    new_group = getattr(new_job, "analysis_group_id", None)
    return bool(base_group and new_group and base_group == new_group)

@router.get("/{job_id}/result", response_model=JobResultResponse)
def job_result(
    job_id: str,
    access_token: str | None = None,
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
):
    job_uuid = parse_uuid_or_400(job_id, "job_id")
    job = db.get(AnalysisJob, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    _authorize_job_access_or_403(job, access_token, current_user)
    if job.status != "succeeded" or not job.result_json:
        raise HTTPException(status_code=409, detail=f"job not ready: {job.status}")
    result = _scrub_internal_fields(job.result_json)
    return JobResultResponse(job_id=job_id, result=result, **_result_contract_fields(result))

@router.get("/{job_id}/report")
def job_report(
    job_id: str,
    access_token: str | None = None,
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
):
    job_uuid = parse_uuid_or_400(job_id, "job_id")
    job = db.get(AnalysisJob, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    _authorize_job_access_or_403(job, access_token, current_user)
    if not job.report_docx_path:
        raise HTTPException(status_code=409, detail="report not ready")
    download_url = f"/v1/jobs/{job_id}/report/download"
    if access_token:
        token_param = quote(access_token, safe="")
        download_url = f"{download_url}?access_token={token_param}"
    return {
        "job_id": job_id,
        "report_status": "ready",
        "sections": [],
        "format": "docx",
        "download_url": download_url,
    }

@router.get("/{job_id}/report/download")
def download_docx(
    job_id: str,
    access_token: str | None = None,
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
):
    job_uuid = parse_uuid_or_400(job_id, "job_id")
    job = db.get(AnalysisJob, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    _authorize_job_access_or_403(job, access_token, current_user)
    if job.status != "succeeded" or not job.report_docx_path:
        raise HTTPException(status_code=409, detail="report not ready")

    try:
        content = get_storage().read_bytes(job.report_docx_path)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="report file not found")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="cvfit_report_{job_id}.docx"'},
    )
