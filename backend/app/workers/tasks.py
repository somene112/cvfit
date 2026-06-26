import os
import tempfile

from app.workers.celery_app import celery_app
from app.core.config import validate_runtime_config
from app.db.session import SessionLocal
from app.db.models import AnalysisJob, CVFile, JDDoc
from app.db.init_db import init_db
from app.services.parsing.cv_parser import parse_cv_to_text
from app.services.parsing.jd_parser import parse_jd
from app.services.scoring.result_v2 import build_result_v2
from app.services.scoring.result_v3 import build_result_v3
from app.services.scoring.scorer import score
from app.services.storage import get_storage, save_report_file
from app.services.reporting.report_docx import build_docx_report

validate_runtime_config()


def _update_job(job_id, **fields):
    with SessionLocal() as db:
        job = db.get(AnalysisJob, job_id)
        if not job:
            return
        for k, v in fields.items():
            setattr(job, k, v)
        db.commit()


def _safe_error_message(exc: Exception) -> str:
    return f"Analysis failed: {exc.__class__.__name__}"


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def run_job(self, job_id: str, language: str = "en"):
    try:
        init_db()
        _update_job(job_id, status="running", progress=5, error_message=None)

        with SessionLocal() as db:
            job = db.get(AnalysisJob, job_id)
            cv = db.get(CVFile, job.cv_file_id)
            jd = db.get(JDDoc, job.jd_id)

        _update_job(job_id, progress=20)
        with get_storage().local_path(cv.storage_path) as cv_path:
            cv_parsed = parse_cv_to_text(cv_path)

        _update_job(job_id, progress=40)
        jd_struct = parse_jd(jd.jd_text)

        _update_job(job_id, progress=75)
        scored = score(cv_parsed, jd_struct)

        result_full = {
            "job_id": job_id,
            "cv": {
                "file_name": cv.original_filename,
                "parsed_confidence": cv_parsed["confidence"],
                "skills_detected": cv_parsed.get("skills_detected", []),
            },
            "jd": jd_struct,
            **scored
        }
        result_full = build_result_v2(
            result_full,
            cv_parsed=cv_parsed,
            jd_struct=jd_struct,
            job_id=job_id,
            language=language,
        )
        result_full = build_result_v3(result_full, language=language)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            out_docx = tmp.name
        try:
            build_docx_report(result_full, out_docx)
            report_location = save_report_file(job_id, out_docx)
        finally:
            try:
                os.remove(out_docx)
            except FileNotFoundError:
                pass

        _update_job(
            job_id,
            progress=95,
            result_json=result_full,
            report_docx_path=report_location
        )
        _update_job(job_id, status="succeeded", progress=100)

        return {"job_id": job_id, "status": "succeeded"}
    except Exception as exc:
        _update_job(job_id, status="failed", error_message=_safe_error_message(exc))
        raise
