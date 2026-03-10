from celery import chain
from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal, engine
from app.db.models import Base, AnalysisJob, CVFile, JDDoc
from app.services.parsing.cv_parser import parse_cv_to_text
from app.services.parsing.jd_parser import parse_jd
from app.services.scoring.scorer import score
from app.services.storage import report_path
from app.services.reporting.report_docx import build_docx_report

# create tables for dev (replace with Alembic later)
Base.metadata.create_all(bind=engine)

def _update_job(job_id, **fields):
    with SessionLocal() as db:
        job = db.get(AnalysisJob, job_id)
        for k, v in fields.items():
            setattr(job, k, v)
        db.commit()

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def run_job(self, job_id: str):
    _update_job(job_id, status="running", progress=5, error_message=None)

    with SessionLocal() as db:
        job = db.get(AnalysisJob, job_id)
        cv = db.get(CVFile, job.cv_file_id)
        jd = db.get(JDDoc, job.jd_id)

    _update_job(job_id, progress=20)
    cv_parsed = parse_cv_to_text(cv.storage_path)

    _update_job(job_id, progress=40)
    jd_struct = parse_jd(jd.jd_text)

    _update_job(job_id, progress=70)
    result = score(cv_parsed["text"], jd_struct)
    # add metadata
    result_full = {
        "job_id": job_id,
        "cv": {"file_name": cv.original_filename, "parsed_confidence": cv_parsed["confidence"]},
        "jd": jd_struct,
        **result
    }

    out_docx = report_path(job_id)
    build_docx_report(result_full, out_docx)

    _update_job(job_id, progress=95, result_json=result_full, report_docx_path=out_docx)
    _update_job(job_id, status="succeeded", progress=100)

    return {"job_id": job_id, "status": "succeeded"}