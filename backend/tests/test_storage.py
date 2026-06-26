import os
import sys
import uuid
from contextlib import contextmanager
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi import UploadFile

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.core.config import settings
from app.services.storage import LocalStorage, S3Storage, StorageError, get_storage
from app.services.storage.factory import get_storage as cached_get_storage


def reset_storage_cache():
    cached_get_storage.cache_clear()


def test_storage_factory_selects_local_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))
    reset_storage_cache()

    storage = get_storage()

    assert isinstance(storage, LocalStorage)


def test_storage_factory_selects_s3(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "cvfit-test")
    monkeypatch.setattr(settings, "S3_REGION", "us-east-1")
    monkeypatch.setattr(settings, "S3_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "S3_PREFIX", "tests")
    monkeypatch.setattr(settings, "AWS_USE_IAM_ROLE", True)
    reset_storage_cache()

    storage = get_storage()

    assert isinstance(storage, S3Storage)
    assert storage.bucket == "cvfit-test"
    assert storage.endpoint_url is None


def test_s3_endpoint_url_is_optional(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "cvfit-test")
    monkeypatch.setattr(settings, "S3_REGION", "us-east-1")
    monkeypatch.setattr(settings, "S3_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "AWS_USE_IAM_ROLE", True)
    reset_storage_cache()

    storage = get_storage()

    assert isinstance(storage, S3Storage)
    assert storage.endpoint_url is None


def test_s3_endpoint_url_is_passed_to_boto3(monkeypatch):
    from app.services.storage.s3 import S3Storage

    calls = []

    class FakeBoto3:
        @staticmethod
        def client(service_name, **kwargs):
            calls.append((service_name, kwargs))
            return SimpleNamespace()

    monkeypatch.setitem(sys.modules, "boto3", FakeBoto3)

    storage = S3Storage(
        bucket="cvfit-test",
        region="us-east-1",
        endpoint_url="https://s3.example.test",
        aws_access_key_id="key",
        aws_secret_access_key="secret",
    )

    assert storage.client is not None
    assert calls == [
        (
            "s3",
            {
                "region_name": "us-east-1",
                "endpoint_url": "https://s3.example.test",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
            },
        )
    ]


def test_invalid_storage_backend_fails_clearly(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "invalid")
    reset_storage_cache()

    with pytest.raises(RuntimeError, match="Invalid STORAGE_BACKEND"):
        get_storage()


def test_s3_storage_requires_bucket(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "")
    monkeypatch.setattr(settings, "S3_REGION", "us-east-1")
    monkeypatch.setattr(settings, "AWS_USE_IAM_ROLE", True)
    reset_storage_cache()

    with pytest.raises(RuntimeError, match="S3_BUCKET is required"):
        get_storage()


def test_s3_storage_requires_region(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "cvfit-test")
    monkeypatch.setattr(settings, "S3_REGION", "")
    monkeypatch.setattr(settings, "AWS_USE_IAM_ROLE", True)
    reset_storage_cache()

    with pytest.raises(RuntimeError, match="S3_REGION is required"):
        get_storage()


def test_s3_storage_requires_credentials_without_iam(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "cvfit-test")
    monkeypatch.setattr(settings, "S3_REGION", "us-east-1")
    monkeypatch.setattr(settings, "AWS_USE_IAM_ROLE", False)
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "")
    reset_storage_cache()

    with pytest.raises(RuntimeError, match="AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"):
        get_storage()


def test_local_storage_can_save_and_read_small_file(tmp_path):
    storage = LocalStorage(str(tmp_path))

    location = storage.save_bytes("uploads/test.txt", b"hello", "text/plain")

    assert storage.read_bytes(location) == b"hello"


def test_report_metadata_does_not_expose_local_path():
    from app.api.routes.jobs import job_report
    from app.api.routes import jobs as jobs_route

    job_id = str(uuid.uuid4())
    token = "correct-token"
    fake_job = SimpleNamespace(
        report_docx_path="./data/reports/test.docx",
        access_token_hash=jobs_route._hash_access_token(token),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)

    response = job_report(job_id, access_token=token, db=fake_db)

    assert response == {
        "job_id": job_id,
        "report_status": "ready",
        "sections": [],
        "format": "docx",
        "download_url": f"/v1/jobs/{job_id}/report/download?access_token={token}",
    }
    assert "local_path" not in response
    assert "./data/reports/test.docx" not in str(response)


def test_create_score_returns_job_id_and_access_token(monkeypatch):
    from app.api.routes import jobs as jobs_route
    from app.schemas.requests import ScoreCreateRequest

    cv_id = uuid.uuid4()
    cv = SimpleNamespace(id=cv_id)
    saved_rows = []
    enqueued_jobs = []

    class FakeDb:
        def get(self, model, key):
            if model.__name__ == "CVFile":
                return cv
            return None

        def add(self, row):
            saved_rows.append(row)

        def flush(self):
            return None

        def commit(self):
            return None

    fake_task_module = SimpleNamespace(
        run_job=SimpleNamespace(delay=lambda job_id, language="en": enqueued_jobs.append(job_id))
    )
    monkeypatch.setitem(sys.modules, "app.workers.tasks", fake_task_module)

    payload = ScoreCreateRequest(cv_file_id=str(cv_id), jd_text="x" * 30)
    response = jobs_route.create_score_job(payload, db=FakeDb())

    jobs = [row for row in saved_rows if row.__class__.__name__ == "AnalysisJob"]
    assert response.job_id
    assert response.access_token
    assert response.status == "queued"
    assert jobs[0].access_token_hash
    assert jobs[0].access_token_hash != response.access_token
    assert jobs[0].access_token_hash == jobs_route._hash_access_token(response.access_token)
    assert enqueued_jobs == [response.job_id]


def test_create_score_accepts_documented_request_aliases(monkeypatch):
    from app.api.routes import jobs as jobs_route
    from app.schemas.requests import ScoreCreateRequest

    cv_id = uuid.uuid4()
    cv = SimpleNamespace(id=cv_id)
    saved_rows = []
    enqueued_jobs = []

    class FakeDb:
        def get(self, model, key):
            if model.__name__ == "CVFile":
                return cv
            return None

        def add(self, row):
            saved_rows.append(row)

        def flush(self):
            return None

        def commit(self):
            return None

    fake_task_module = SimpleNamespace(
        run_job=SimpleNamespace(delay=lambda job_id, language="en": enqueued_jobs.append(job_id))
    )
    monkeypatch.setitem(sys.modules, "app.workers.tasks", fake_task_module)

    payload = ScoreCreateRequest(cv_id=str(cv_id), job_description="x" * 30)
    response = jobs_route.create_score_job(payload, db=FakeDb())

    assert response.job_id
    assert response.access_token
    assert response.status == "queued"
    assert enqueued_jobs == [response.job_id]


def test_result_endpoint_rejects_missing_token():
    from app.api.routes import jobs as jobs_route

    job_id = str(uuid.uuid4())
    fake_job = SimpleNamespace(
        status="succeeded",
        result_json={"scores": {"fit_score": 90}},
        access_token_hash=jobs_route._hash_access_token("correct-token"),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)

    with pytest.raises(HTTPException) as exc:
        jobs_route.job_result(job_id, db=fake_db)

    assert exc.value.status_code == 403


def test_result_endpoint_rejects_wrong_token():
    from app.api.routes import jobs as jobs_route

    job_id = str(uuid.uuid4())
    fake_job = SimpleNamespace(
        status="succeeded",
        result_json={"scores": {"fit_score": 90}},
        access_token_hash=jobs_route._hash_access_token("correct-token"),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)

    with pytest.raises(HTTPException) as exc:
        jobs_route.job_result(job_id, access_token="wrong-token", db=fake_db)

    assert exc.value.status_code == 403


def test_result_endpoint_accepts_correct_token():
    from app.api.routes import jobs as jobs_route

    token = "correct-token"
    job_id = str(uuid.uuid4())
    result_json = {"scores": {"fit_score": 90}}
    fake_job = SimpleNamespace(
        status="succeeded",
        result_json=result_json,
        access_token_hash=jobs_route._hash_access_token(token),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)

    response = jobs_route.job_result(job_id, access_token=token, db=fake_db)

    assert response.job_id == job_id
    assert response.result == result_json
    assert response.overall_fit_score == 90


def test_result_endpoint_scrubs_internal_storage_fields():
    from app.api.routes import jobs as jobs_route

    token = "correct-token"
    job_id = str(uuid.uuid4())
    fake_job = SimpleNamespace(
        status="succeeded",
        result_json={
            "scores": {"fit_score": 90},
            "access_token": "secret-token",
            "access_token_hash": "secret-hash",
            "bucket": "private-bucket",
            "cv_text": "full parsed cv",
            "file_path": "C:/private/file.docx",
            "object_key": "private/object.docx",
            "raw_cv_text": "full raw cv",
            "s3_key": "private/key.docx",
            "storage_path": "uploads/private-cv.pdf",
            "nested": {"local_path": "C:/private/cv.pdf", "safe": "ok"},
            "items": [{"report_docx_path": "reports/private.docx", "safe": True}],
        },
        access_token_hash=jobs_route._hash_access_token(token),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)

    response = jobs_route.job_result(job_id, access_token=token, db=fake_db)

    assert response.result == {"scores": {"fit_score": 90}, "nested": {"safe": "ok"}, "items": [{"safe": True}]}
    response_text = str(response.model_dump())
    assert "secret-token" not in response_text
    assert "secret-hash" not in response_text
    assert "private-bucket" not in response_text
    assert "full parsed cv" not in response_text
    assert "C:/private/file.docx" not in response_text
    assert "private/object.docx" not in response_text
    assert "full raw cv" not in response_text
    assert "private/key.docx" not in response_text
    assert "uploads/private-cv.pdf" not in response_text
    assert "C:/private/cv.pdf" not in response_text
    assert "reports/private.docx" not in response_text


@pytest.mark.parametrize("endpoint", ["job_report", "download_docx"])
@pytest.mark.parametrize("token", [None, "wrong-token"])
def test_report_endpoints_reject_missing_or_wrong_token(monkeypatch, endpoint, token):
    from app.api.routes import jobs as jobs_route

    job_id = str(uuid.uuid4())
    fake_job = SimpleNamespace(
        status="succeeded",
        report_docx_path="reports/test.docx",
        access_token_hash=jobs_route._hash_access_token("correct-token"),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)
    fake_storage = SimpleNamespace(read_bytes=lambda location: b"docx-bytes")
    monkeypatch.setattr(jobs_route, "get_storage", lambda: fake_storage)

    with pytest.raises(HTTPException) as exc:
        getattr(jobs_route, endpoint)(job_id, access_token=token, db=fake_db)

    assert exc.value.status_code == 403


def test_upload_endpoint_response_shape_remains_compatible(monkeypatch):
    from app.api.routes import cv as cv_route

    saved_rows = []
    fake_db = SimpleNamespace(
        add=lambda row: saved_rows.append(row),
        commit=lambda: None,
    )
    upload = UploadFile(filename="cv.pdf", file=BytesIO(b"%PDF-1.4 test"))
    monkeypatch.setattr(
        cv_route,
        "save_upload",
        lambda file: ("uploads/cv.pdf", "a" * 64, "application/pdf"),
    )

    response = cv_route.upload_cv(file=upload, db=fake_db)

    assert isinstance(response.cv_file_id, str)
    assert response.cv_id == response.cv_file_id
    assert response.filename == "cv.pdf"
    assert response.content_type == "application/pdf"
    assert response.size_bytes == 0
    assert saved_rows[0].storage_path == "uploads/cv.pdf"


def test_upload_rejects_invalid_extension():
    from app.api.routes import cv as cv_route

    upload = UploadFile(filename="cv.doc", file=BytesIO(b"test"))

    with pytest.raises(HTTPException) as exc:
        cv_route.upload_cv(file=upload, db=SimpleNamespace())

    assert exc.value.status_code == 400
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail["code"] == "CV_UNSUPPORTED_FILE_TYPE"
    assert "PDF" in detail["message"] or "DOCX" in detail["message"]


def test_upload_rejects_empty_file():
    from app.api.routes import cv as cv_route

    upload = UploadFile(filename="cv.pdf", file=BytesIO(b""))

    with pytest.raises(HTTPException) as exc:
        cv_route.upload_cv(file=upload, db=SimpleNamespace())

    assert exc.value.status_code == 400
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail["code"] == "CV_FILE_EMPTY"
    assert detail["message"]
    # no raw file content or path in error
    assert "storage_path" not in str(detail)
    assert "uploads/" not in str(detail)


def test_upload_rejects_oversized_file(monkeypatch):
    from app.api.routes import cv as cv_route

    monkeypatch.setattr(settings, "CV_MAX_UPLOAD_MB", 1)
    upload = UploadFile(filename="cv.pdf", file=BytesIO(b"x" * (1024 * 1024 + 1)))

    with pytest.raises(HTTPException) as exc:
        cv_route.upload_cv(file=upload, db=SimpleNamespace())

    assert exc.value.status_code == 400
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail["code"] == "CV_FILE_TOO_LARGE"
    assert "1 MB" in detail["message"]
    assert detail["max_size_mb"] == 1
    # no raw file content or path in error
    assert "storage_path" not in str(detail)
    assert "uploads/" not in str(detail)


def test_upload_rejects_file_just_above_10mb(monkeypatch):
    """File just above 10MB must be rejected with structured error citing 10MB."""
    from app.api.routes import cv as cv_route

    monkeypatch.setattr(settings, "CV_MAX_UPLOAD_MB", 10)
    just_over = b"x" * (10 * 1024 * 1024 + 1)
    upload = UploadFile(filename="cv.pdf", file=BytesIO(just_over))

    with pytest.raises(HTTPException) as exc:
        cv_route.upload_cv(file=upload, db=SimpleNamespace())

    assert exc.value.status_code == 400
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail["code"] == "CV_FILE_TOO_LARGE"
    assert "10 MB" in detail["message"]
    assert detail["max_size_mb"] == 10
    assert "storage_path" not in str(detail)
    assert "uploads/" not in str(detail)


def test_upload_accepts_file_at_10mb(monkeypatch):
    """File exactly at the 10MB limit must pass size validation."""
    from app.api.routes import cv as cv_route

    monkeypatch.setattr(settings, "CV_MAX_UPLOAD_MB", 10)
    exactly_10mb = b"x" * (10 * 1024 * 1024)
    upload = UploadFile(filename="cv.pdf", file=BytesIO(exactly_10mb))
    monkeypatch.setattr(
        cv_route,
        "save_upload",
        lambda f: ("uploads/cv.pdf", "a" * 64, "application/pdf"),
    )

    saved_rows = []
    fake_db = SimpleNamespace(add=lambda row: saved_rows.append(row), commit=lambda: None)
    response = cv_route.upload_cv(file=upload, db=fake_db)

    assert isinstance(response.cv_file_id, str)


def test_upload_error_detail_has_no_stack_trace(monkeypatch):
    """Upload error responses must not expose stack traces or internal paths."""
    from app.api.routes import cv as cv_route

    monkeypatch.setattr(settings, "CV_MAX_UPLOAD_MB", 1)
    upload = UploadFile(filename="cv.pdf", file=BytesIO(b"x" * (1024 * 1024 + 1)))

    with pytest.raises(HTTPException) as exc:
        cv_route.upload_cv(file=upload, db=SimpleNamespace())

    detail_str = str(exc.value.detail)
    assert "Traceback" not in detail_str
    assert "File \"" not in detail_str
    assert ".py" not in detail_str


@pytest.mark.parametrize(
    "endpoint,args",
    [
        ("create_score_job", [SimpleNamespace(cv_file_id="bad-id", jd_text="x" * 30, options=SimpleNamespace(target_role=None))]),
        ("job_status", ["bad-id"]),
        ("job_result", ["bad-id"]),
        ("job_report", ["bad-id"]),
        ("download_docx", ["bad-id"]),
    ],
)
def test_job_endpoints_reject_bad_uuid(endpoint, args):
    from app.api.routes import jobs as jobs_route

    with pytest.raises(HTTPException) as exc:
        getattr(jobs_route, endpoint)(*args, db=SimpleNamespace())

    assert exc.value.status_code == 400
    assert "Invalid" in exc.value.detail


def test_report_download_response_shape_remains_compatible(monkeypatch):
    from app.api.routes import jobs as jobs_route

    job_id = str(uuid.uuid4())
    token = "correct-token"
    fake_job = SimpleNamespace(
        status="succeeded",
        report_docx_path="reports/test.docx",
        access_token_hash=jobs_route._hash_access_token(token),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)
    fake_storage = SimpleNamespace(read_bytes=lambda location: b"docx-bytes")
    monkeypatch.setattr(jobs_route, "get_storage", lambda: fake_storage)

    response = jobs_route.download_docx(job_id, access_token=token, db=fake_db)

    assert response.media_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert response.body == b"docx-bytes"
    assert "cvfit_report_" in response.headers["content-disposition"]


def test_report_download_returns_404_when_object_missing(monkeypatch):
    from app.api.routes import jobs as jobs_route
    from app.services.storage import StorageNotFoundError

    job_id = str(uuid.uuid4())
    token = "correct-token"
    fake_job = SimpleNamespace(
        status="succeeded",
        report_docx_path="reports/missing.docx",
        access_token_hash=jobs_route._hash_access_token(token),
    )
    fake_db = SimpleNamespace(get=lambda model, key: fake_job)
    fake_storage = SimpleNamespace(
        read_bytes=lambda location: (_ for _ in ()).throw(StorageNotFoundError("missing"))
    )
    monkeypatch.setattr(jobs_route, "get_storage", lambda: fake_storage)

    with pytest.raises(HTTPException) as exc:
        jobs_route.download_docx(job_id, access_token=token, db=fake_db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "report file not found"


def test_worker_failure_marks_job_failed(monkeypatch):
    import app.workers.tasks as tasks

    updates = []
    job = SimpleNamespace(cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4())
    cv = SimpleNamespace(storage_path="uploads/cv.pdf")
    jd = SimpleNamespace(jd_text="Need Python and FastAPI experience")

    class FakeDb:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, model, key):
            name = model.__name__
            if name == "AnalysisJob":
                return job
            if name == "CVFile":
                return cv
            if name == "JDDoc":
                return jd
            return None

    @contextmanager
    def broken_local_path(location):
        raise RuntimeError("parser failed with private path /tmp/cv.pdf")
        yield

    fake_storage = SimpleNamespace(local_path=broken_local_path)

    monkeypatch.setattr(tasks, "init_db", lambda: None)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: FakeDb())
    monkeypatch.setattr(tasks, "get_storage", lambda: fake_storage)
    monkeypatch.setattr(tasks, "_update_job", lambda job_id, **fields: updates.append(fields))

    with pytest.raises(RuntimeError):
        tasks.run_job.run("job-1")

    assert updates[-1]["status"] == "failed"
    assert updates[-1]["error_message"] == "Analysis failed: RuntimeError"
    assert "/tmp/cv.pdf" not in updates[-1]["error_message"]
