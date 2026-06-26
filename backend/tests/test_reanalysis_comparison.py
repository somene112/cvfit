from __future__ import annotations

import sys
import uuid
from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.routes import jobs as jobs_route
from app.core.security import create_access_token
from app.db.models import AnalysisJob, CVFile, JDDoc, User
from app.db.session import get_db
from app.services.comparison import compare_results


class FakeJobQuery:
    def __init__(self, jobs):
        self.jobs = list(jobs)
        self.filters = {}

    def filter_by(self, **kwargs):
        self.filters.update(kwargs)
        return self

    def order_by(self, *args):
        return self

    def all(self):
        jobs = self.jobs
        for key, value in self.filters.items():
            jobs = [job for job in jobs if getattr(job, key, None) == value]
        return sorted(jobs, key=lambda job: getattr(job, "created_at", datetime.min), reverse=True)


class FakeDb:
    def __init__(self, *, cvs=None, jds=None, jobs=None, users=None):
        self.cvs = {item.id: item for item in cvs or []}
        self.jds = {item.id: item for item in jds or []}
        self.jobs = {item.id: item for item in jobs or []}
        self.users = {item.id: item for item in users or []}
        self.saved_rows = []
        self.commits = 0

    def get(self, model, key):
        if model is CVFile:
            return self.cvs.get(key)
        if model is JDDoc:
            return self.jds.get(key)
        if model is AnalysisJob:
            return self.jobs.get(key)
        if model is User:
            return self.users.get(key)
        return None

    def query(self, model):
        assert model is AnalysisJob
        return FakeJobQuery(self.jobs.values())

    def add(self, row):
        self.saved_rows.append(row)

    def flush(self):
        return None

    def commit(self):
        self.commits += 1
        for row in self.saved_rows:
            if isinstance(row, CVFile):
                self.cvs[row.id] = row
            elif isinstance(row, JDDoc):
                self.jds[row.id] = row
            elif isinstance(row, AnalysisJob):
                self.jobs[row.id] = row


@pytest.fixture
def user_a():
    return User(id=uuid.uuid4(), email="a@example.com", password_hash="hash", is_active=True)


@pytest.fixture
def user_b():
    return User(id=uuid.uuid4(), email="b@example.com", password_hash="hash", is_active=True)


@pytest.fixture
def jobs_app(monkeypatch):
    fake_task_module = SimpleNamespace(run_job=SimpleNamespace(delay=lambda job_id, language="en": None))
    monkeypatch.setitem(sys.modules, "app.workers.tasks", fake_task_module)
    monkeypatch.setattr(
        jobs_route,
        "save_upload",
        lambda file: ("uploads/revised.docx", "a" * 64, file.content_type or "application/octet-stream"),
    )
    app = FastAPI()
    app.include_router(jobs_route.router)
    return app


def client_for(app, db):
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def make_jd(text="Backend JD requiring Python, FastAPI, PostgreSQL, and Kubernetes."):
    return JDDoc(id=uuid.uuid4(), jd_text=text, role="Backend Engineer")


def make_job(
    *,
    owner_id=None,
    token="parent-token",
    jd=None,
    status="succeeded",
    result_json=None,
    group_id=None,
    revision_number=1,
    parent_job_id=None,
):
    jd = jd or make_jd()
    cv_id = uuid.uuid4()
    return SimpleNamespace(
        id=uuid.uuid4(),
        cv_file_id=cv_id,
        jd_id=jd.id,
        user_id=owner_id,
        parent_job_id=parent_job_id,
        analysis_group_id=group_id,
        revision_number=revision_number,
        status=status,
        progress=100 if status == "succeeded" else 20,
        error_message=None,
        result_json=result_json if result_json is not None else result_payload(score=70),
        report_docx_path="reports/test.docx",
        access_token_hash=jobs_route._hash_access_token(token),
        created_at=datetime(2026, 6, 1, 8, revision_number, 0),
        updated_at=datetime(2026, 6, 1, 8, revision_number, 30),
        jd_doc=jd,
    )


def result_payload(*, score, missing=None, matched=None, evidence=None, actions=None):
    return {
        "schema_version": "3.0",
        "fit_score": score,
        "scores": {
            "fit_score": score,
            "skill_match": score - 5,
            "experience_match": score - 10,
        },
        "overall": {"fit_score": score, "summary": "Analysis complete."},
        "score_breakdown": [
            {"key": "skill_match", "score": score - 5},
            {"key": "experience_match", "score": score - 10},
        ],
        "missing_skills": missing or [],
        "matched_skills": matched or [],
        "evidence": evidence or [],
        "improvement_actions": actions or [],
    }


def test_analysis_job_revision_fields_exist_and_default_to_one():
    job = AnalysisJob(cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4())

    assert hasattr(job, "parent_job_id")
    assert hasattr(job, "analysis_group_id")
    assert hasattr(job, "revision_number")
    assert job.parent_job_id is None
    assert job.analysis_group_id is None
    column = AnalysisJob.__table__.columns["revision_number"]
    assert column.default.arg == 1
    assert column.server_default.arg == "1"


def test_logged_in_owner_can_reanalyze_own_job(jobs_app, user_a):
    jd = make_jd()
    parent = make_job(owner_id=user_a.id, jd=jd, group_id=None, revision_number=1)
    original_result = dict(parent.result_json)
    db = FakeDb(jds=[jd], jobs=[parent], users=[user_a])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.post(
        f"/v1/jobs/{parent.id}/reanalyze",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("revised.docx", b"docx-bytes", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parent_job_id"] == str(parent.id)
    assert payload["analysis_group_id"] == parent.analysis_group_id
    assert payload["revision_number"] == 2
    assert payload["status"] == "queued"
    child = db.jobs[uuid.UUID(payload["job_id"])]
    assert child.parent_job_id == parent.id
    assert child.analysis_group_id == parent.analysis_group_id
    assert child.revision_number == 2
    assert child.user_id == user_a.id
    assert parent.revision_number == 1
    assert parent.result_json == original_result
    assert db.commits == 1


def test_wrong_logged_in_user_cannot_reanalyze(jobs_app, user_a, user_b):
    jd = make_jd()
    parent = make_job(owner_id=user_a.id, jd=jd)
    db = FakeDb(jds=[jd], jobs=[parent], users=[user_a, user_b])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_b.id))

    response = client.post(
        f"/v1/jobs/{parent.id}/reanalyze",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("revised.docx", b"docx-bytes", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 403


def test_guest_with_valid_parent_token_can_reanalyze(jobs_app):
    jd = make_jd()
    parent = make_job(jd=jd, token="parent-token")
    db = FakeDb(jds=[jd], jobs=[parent])
    client = client_for(jobs_app, db)

    response = client.post(
        f"/v1/jobs/{parent.id}/reanalyze",
        data={"access_token": "parent-token"},
        files={"file": ("revised.pdf", b"%PDF test", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    child = db.jobs[uuid.UUID(payload["job_id"])]
    assert payload["access_token"]
    assert child.access_token_hash == jobs_route._hash_access_token(payload["access_token"])
    assert child.parent_job_id == parent.id
    assert child.analysis_group_id == parent.analysis_group_id
    assert child.revision_number == 2
    assert child.user_id is None


@pytest.mark.parametrize("token", [None, "wrong-token"])
def test_guest_reanalysis_requires_valid_parent_token(jobs_app, token):
    jd = make_jd()
    parent = make_job(jd=jd, token="parent-token")
    db = FakeDb(jds=[jd], jobs=[parent])
    client = client_for(jobs_app, db)
    data = {"access_token": token} if token else {}

    response = client.post(
        f"/v1/jobs/{parent.id}/reanalyze",
        data=data,
        files={"file": ("revised.pdf", b"%PDF test", "application/pdf")},
    )

    assert response.status_code == 403


def test_comparison_service_resolves_only_evidenced_missing_skill():
    base = result_payload(
        score=63.5,
        missing=[{"skill": "Kubernetes", "reason": "Kubernetes evidence was not found in the parsed CV."}],
        matched=[{"skill": "FastAPI", "cv_evidence_ids": ["ev_cv_fastapi"]}],
        evidence=[{"id": "ev_cv_fastapi", "source": "cv", "text": "Built FastAPI APIs."}],
    )
    new = result_payload(
        score=75.9,
        missing=[],
        matched=[
            {"skill": "FastAPI", "cv_evidence_ids": ["ev_cv_fastapi"]},
            {"skill": "Kubernetes", "cv_evidence_ids": ["ev_cv_k8s"]},
        ],
        evidence=[
            {"id": "ev_cv_fastapi", "source": "cv", "text": "Built FastAPI APIs."},
            {"id": "ev_cv_k8s", "source": "cv", "text": "Deployed a service to Kubernetes."},
        ],
    )

    comparison = compare_results(base, new, base_job_id="base", new_job_id="new")

    assert comparison["base_score"] == 63.5
    assert comparison["new_score"] == 75.9
    assert comparison["score_delta"] == 12.4
    assert comparison["breakdown_delta"]["skill_match"] == 12.4
    assert comparison["resolved_missing_skills"][0]["skill"] == "Kubernetes"
    assert comparison["newly_matched_skills"][0]["skill"] == "Kubernetes"
    assert comparison["new_evidence"][0]["id"] == "ev_cv_k8s"


def test_comparison_service_warns_for_unsupported_keyword_match_and_scrubs_sensitive_fields():
    base = result_payload(
        score=60,
        missing=[{"skill": "Kubernetes", "reason": "Kubernetes evidence was not found in the parsed CV."}],
    )
    new = result_payload(
        score=70,
        missing=[],
        matched=[{"skill": "Kubernetes", "cv_evidence_ids": []}],
        evidence=[{"id": "ev_cv_skills", "source": "cv", "text": "Skills: Python, Kubernetes, Docker"}],
        actions=[{"title": "safe", "access_token": "secret-token"}],
    )
    new["storage_path"] = "uploads/private.docx"

    comparison = compare_results(base, new, base_job_id="base", new_job_id="new")

    assert comparison["resolved_missing_skills"] == []
    assert comparison["still_missing_skills"][0]["skill"] == "Kubernetes"
    assert comparison["keyword_stuffing_warnings"]
    text = str(comparison)
    assert "secret-token" not in text
    assert "uploads/private.docx" not in text
    assert "lying" not in text.lower()


def test_owner_can_compare_own_linked_jobs(jobs_app, user_a):
    group_id = "grp_test"
    base = make_job(owner_id=user_a.id, group_id=group_id, revision_number=1, result_json=result_payload(score=63))
    new = make_job(owner_id=user_a.id, group_id=group_id, revision_number=2, parent_job_id=base.id, result_json=result_payload(score=75))
    db = FakeDb(jobs=[base, new], users=[user_a])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.get(
        f"/v1/jobs/{base.id}/comparison/{new.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["score_delta"] == 12.0


def test_wrong_user_cannot_compare(jobs_app, user_a, user_b):
    group_id = "grp_test"
    base = make_job(owner_id=user_a.id, group_id=group_id, revision_number=1)
    new = make_job(owner_id=user_a.id, group_id=group_id, revision_number=2, parent_job_id=base.id)
    db = FakeDb(jobs=[base, new], users=[user_a, user_b])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_b.id))

    response = client.get(
        f"/v1/jobs/{base.id}/comparison/{new.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_guest_can_compare_linked_jobs_with_new_job_token(jobs_app):
    group_id = "grp_test"
    base = make_job(group_id=group_id, revision_number=1, token="base-token")
    new = make_job(group_id=group_id, revision_number=2, parent_job_id=base.id, token="new-token")
    db = FakeDb(jobs=[base, new])
    client = client_for(jobs_app, db)

    response = client.get(f"/v1/jobs/{base.id}/comparison/{new.id}?access_token=new-token")

    assert response.status_code == 200
    assert response.json()["base_job_id"] == str(base.id)
    assert "access_token" not in str(response.json())


def test_comparison_incomplete_jobs_return_409(jobs_app, user_a):
    group_id = "grp_test"
    base = make_job(owner_id=user_a.id, group_id=group_id, revision_number=1)
    new = make_job(owner_id=user_a.id, group_id=group_id, revision_number=2, parent_job_id=base.id, status="running")
    db = FakeDb(jobs=[base, new], users=[user_a])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.get(
        f"/v1/jobs/{base.id}/comparison/{new.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409


def test_unlinked_jobs_return_409(jobs_app, user_a):
    base = make_job(owner_id=user_a.id, group_id="grp_a")
    new = make_job(owner_id=user_a.id, group_id="grp_b")
    db = FakeDb(jobs=[base, new], users=[user_a])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.get(
        f"/v1/jobs/{base.id}/comparison/{new.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409


def test_history_includes_revision_fields(jobs_app, user_a):
    job = make_job(owner_id=user_a.id, group_id="grp_test", revision_number=2, parent_job_id=uuid.uuid4())
    db = FakeDb(jobs=[job], users=[user_a])
    client = client_for(jobs_app, db)
    token = create_access_token(str(user_a.id))

    response = client.get("/v1/jobs/history", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["parent_job_id"] == str(job.parent_job_id)
    assert item["analysis_group_id"] == "grp_test"
    assert item["revision_number"] == 2
