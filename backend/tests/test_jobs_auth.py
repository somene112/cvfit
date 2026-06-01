import sys
import uuid
from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.routes import jobs as jobs_route
from app.core.security import create_access_token
from app.db.models import AnalysisJob, CVFile, User
from app.db.session import get_db


class FakeJobQuery:
    def __init__(self, jobs):
        self.jobs = list(jobs)
        self.user_id = None

    def filter_by(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        return self

    def order_by(self, *args):
        return self

    def all(self):
        jobs = self.jobs
        if self.user_id is not None:
            jobs = [job for job in jobs if job.user_id == self.user_id]
        return sorted(jobs, key=lambda job: job.created_at, reverse=True)


class FakeDb:
    def __init__(self, cv=None, users=None, jobs=None):
        self.cv = cv
        self.users = {user.id: user for user in users or []}
        self.jobs = {job.id: job for job in jobs or []}
        self.saved_rows = []
        self.committed = False

    def get(self, model, key):
        if model is CVFile:
            return self.cv if self.cv and self.cv.id == key else None
        if model is User:
            return self.users.get(key)
        if model is AnalysisJob:
            return self.jobs.get(key)
        return None

    def query(self, model):
        assert model is AnalysisJob
        return FakeJobQuery(self.jobs.values())

    def add(self, row):
        self.saved_rows.append(row)

    def flush(self):
        return None

    def commit(self):
        self.committed = True
        for row in self.saved_rows:
            if isinstance(row, AnalysisJob):
                self.jobs[row.id] = row


@pytest.fixture
def user_a():
    return User(
        id=uuid.uuid4(),
        email="a@example.com",
        password_hash="hash",
        is_active=True,
    )


@pytest.fixture
def user_b():
    return User(
        id=uuid.uuid4(),
        email="b@example.com",
        password_hash="hash",
        is_active=True,
    )


@pytest.fixture
def cv_file():
    return SimpleNamespace(id=uuid.uuid4())


@pytest.fixture
def jobs_app(monkeypatch):
    fake_task_module = SimpleNamespace(run_job=SimpleNamespace(delay=lambda job_id: None))
    monkeypatch.setitem(sys.modules, "app.workers.tasks", fake_task_module)
    app = FastAPI()
    app.include_router(jobs_route.router)
    return app


def make_job(owner_id=None, token="correct-token", status="succeeded", score=88, report=True):
    job_id = uuid.uuid4()
    return SimpleNamespace(
        id=job_id,
        user_id=owner_id,
        status=status,
        progress=100 if status == "succeeded" else 0,
        error_message=None,
        result_json={"scores": {"fit_score": score}, "evidence": []},
        report_docx_path=f"reports/{job_id}.docx" if report else None,
        access_token_hash=jobs_route._hash_access_token(token),
        created_at=datetime(2026, 6, 1, 8, 0, 0),
        updated_at=datetime(2026, 6, 1, 8, 1, 0),
        jd_doc=SimpleNamespace(role="Backend Engineer"),
    )


def client_for(app, db):
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def create_score_payload(cv_id):
    return {
        "cv_file_id": str(cv_id),
        "jd_text": "Backend Engineer requiring Python, FastAPI, PostgreSQL, Redis, and Docker.",
    }


def test_create_score_without_authorization_remains_guest_and_returns_access_token(jobs_app, cv_file):
    db = FakeDb(cv=cv_file)
    client = client_for(jobs_app, db)

    response = client.post("/v1/jobs/create-score", json=create_score_payload(cv_file.id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["access_token"]
    jobs = [row for row in db.saved_rows if isinstance(row, AnalysisJob)]
    assert jobs[0].user_id is None


def test_create_score_with_valid_jwt_attaches_user_id(jobs_app, cv_file, user_a):
    db = FakeDb(cv=cv_file, users=[user_a])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.post(
        "/v1/jobs/create-score",
        json=create_score_payload(cv_file.id),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    jobs = [row for row in db.saved_rows if isinstance(row, AnalysisJob)]
    assert jobs[0].user_id == user_a.id


def test_create_score_with_invalid_authorization_returns_401_and_creates_no_job(jobs_app, cv_file):
    db = FakeDb(cv=cv_file)
    client = client_for(jobs_app, db)

    response = client.post(
        "/v1/jobs/create-score",
        json=create_score_payload(cv_file.id),
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
    assert not [row for row in db.saved_rows if isinstance(row, AnalysisJob)]


def test_history_without_token_returns_401(jobs_app):
    db = FakeDb()
    client = client_for(jobs_app, db)

    response = client.get("/v1/jobs/history")

    assert response.status_code == 401


def test_history_with_valid_jwt_returns_only_current_users_jobs(jobs_app, user_a, user_b):
    job_a = make_job(owner_id=user_a.id, score=88)
    job_b = make_job(owner_id=user_b.id, score=55)
    guest_job = make_job(owner_id=None, score=99)
    db = FakeDb(users=[user_a, user_b], jobs=[job_a, job_b, guest_job])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.get("/v1/jobs/history", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["job_id"] for item in payload["items"]] == [str(job_a.id)]
    item = payload["items"][0]
    assert item["overall_fit_score"] == 88
    assert item["has_report"] is True
    assert item["target_role"] == "Backend Engineer"
    assert "access_token" not in str(payload)
    assert "access_token_hash" not in str(payload)
    assert "report_docx_path" not in str(payload)


def test_user_a_history_does_not_include_user_b_jobs(jobs_app, user_a, user_b):
    job_a = make_job(owner_id=user_a.id, score=88)
    job_b = make_job(owner_id=user_b.id, score=55)
    db = FakeDb(users=[user_a, user_b], jobs=[job_a, job_b])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_b.id))

    response = client.get("/v1/jobs/history", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert [item["job_id"] for item in response.json()["items"]] == [str(job_b.id)]


def test_result_endpoint_remains_accessible_with_valid_guest_access_token(jobs_app):
    job = make_job(token="guest-token")
    db = FakeDb(jobs=[job])
    client = client_for(jobs_app, db)

    response = client.get(f"/v1/jobs/{job.id}/result?access_token=guest-token")

    assert response.status_code == 200
    assert response.json()["overall_fit_score"] == 88


def test_result_endpoint_accessible_with_owner_jwt_without_query_access_token(jobs_app, user_a):
    job = make_job(owner_id=user_a.id)
    db = FakeDb(users=[user_a], jobs=[job])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.get(
        f"/v1/jobs/{job.id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["overall_fit_score"] == 88


def test_result_endpoint_rejects_non_owner_jwt(jobs_app, user_a, user_b):
    job = make_job(owner_id=user_a.id)
    db = FakeDb(users=[user_a, user_b], jobs=[job])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_b.id))

    response = client.get(
        f"/v1/jobs/{job.id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_report_metadata_endpoint_accessible_with_owner_jwt(jobs_app, user_a):
    job = make_job(owner_id=user_a.id)
    db = FakeDb(users=[user_a], jobs=[job])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.get(
        f"/v1/jobs/{job.id}/report",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["download_url"] == f"/v1/jobs/{job.id}/report/download"


def test_report_download_endpoint_accessible_with_owner_jwt(monkeypatch, jobs_app, user_a):
    job = make_job(owner_id=user_a.id)
    db = FakeDb(users=[user_a], jobs=[job])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))
    monkeypatch.setattr(jobs_route, "get_storage", lambda: SimpleNamespace(read_bytes=lambda path: b"docx-bytes"))

    response = client.get(
        f"/v1/jobs/{job.id}/report/download",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.content == b"docx-bytes"


def test_wrong_access_token_still_returns_403(jobs_app):
    job = make_job(token="correct-token")
    db = FakeDb(jobs=[job])
    client = client_for(jobs_app, db)

    response = client.get(f"/v1/jobs/{job.id}/result?access_token=wrong-token")

    assert response.status_code == 403
