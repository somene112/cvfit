"""Phase 6 backend tests — Target Jobs workspace.

Reuses the in-memory FakeDb pattern from test_phase5_applications_profile.py.
Target Jobs are a product layer over the ``applications`` table, so the same
fake objects apply. No real database is required.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.target_jobs import router as target_jobs_router
from app.core.security import create_access_token
from app.db.models import AnalysisJob, Application, ApplicationArtifact, User
from app.db.session import get_db


# ---------------------------------------------------------------------------
# Fake DB (same shape as the Phase 5 test suite)
# ---------------------------------------------------------------------------

class FakeDb:
    def __init__(self):
        self._store: dict[tuple, Any] = {}
        self._query_results: dict[type, list] = {}

    def _key(self, model, pk):
        return (model.__tablename__, pk)

    def add(self, obj):
        self._store[self._key(type(obj), obj.id)] = obj
        model_type = type(obj)
        self._query_results.setdefault(model_type, [])
        if obj not in self._query_results[model_type]:
            self._query_results[model_type].append(obj)

    def get(self, model, pk):
        return self._store.get(self._key(model, pk))

    def delete(self, obj):
        self._store.pop(self._key(type(obj), obj.id), None)
        lst = self._query_results.get(type(obj), [])
        if obj in lst:
            lst.remove(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        return FakeQuery(self._query_results.get(model, []), model, db=self)


class FakeQuery:
    def __init__(self, rows, model, db=None):
        self._rows = list(rows)
        self._model = model
        self._db = db

    def filter(self, *args):
        new_rows = list(self._rows)
        for expr in args:
            try:
                col_key = expr.left.key
                col_val = expr.right.value
                new_rows = [r for r in new_rows if getattr(r, col_key, None) == col_val]
            except AttributeError:
                pass
        return FakeQuery(new_rows, self._model, db=self._db)

    def order_by(self, *args):
        try:
            col_key = args[0].key
        except Exception:
            return self
        try:
            self._rows = sorted(
                self._rows,
                key=lambda r: getattr(r, col_key, None) or datetime.min,
                reverse=True,
            )
        except Exception:
            pass
        return self

    def all(self):
        return list(self._rows)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email: str = "user@example.com") -> User:
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_target_job(
    user_id: uuid.UUID,
    status: str = "saved",
    best_analysis_job_id: Optional[uuid.UUID] = None,
) -> Application:
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(),
        user_id=user_id,
        job_title="Backend Developer",
        company_name="TestCo",
        jd_text="We need a backend developer with Python and FastAPI skills.",
        target_role="Backend",
        status=status,
        best_analysis_job_id=best_analysis_job_id,
        created_at=now,
        updated_at=now,
    )


def make_job(user_id: uuid.UUID, status: str = "succeeded", fit_score: float = 78.5) -> AnalysisJob:
    now = datetime.utcnow()
    result_json = {"overall_fit_score": fit_score, "scores": {"fit_score": fit_score}}
    return AnalysisJob(
        id=uuid.uuid4(),
        user_id=user_id,
        cv_file_id=uuid.uuid4(),
        jd_id=uuid.uuid4(),
        status=status,
        progress=100 if status == "succeeded" else 0,
        result_json=result_json if status == "succeeded" else None,
        created_at=now,
        updated_at=now,
    )


def build_client(db: FakeDb, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(target_jobs_router)
    token = create_access_token(str(user.id))
    db.add(user)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)
    client._auth_headers = {"Authorization": f"Bearer {token}"}
    return client


def build_unauthed_client(db: FakeDb) -> TestClient:
    app = FastAPI()
    app.include_router(target_jobs_router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestTargetJobAuth:
    def test_create_without_auth_returns_401(self):
        client = build_unauthed_client(FakeDb())
        resp = client.post("/v1/target-jobs", json={"job_title": "Dev", "jd_text": "text"})
        assert resp.status_code == 401

    def test_list_without_auth_returns_401(self):
        client = build_unauthed_client(FakeDb())
        assert client.get("/v1/target-jobs").status_code == 401


# ---------------------------------------------------------------------------
# CRUD + ownership
# ---------------------------------------------------------------------------

class TestTargetJobCRUD:
    def test_create_returns_201_with_saved_status(self):
        user = make_user()
        db = FakeDb()
        client = build_client(db, user)

        resp = client.post("/v1/target-jobs", json={
            "job_title": "Junior Backend Developer",
            "company_name": "Example Company",
            "jd_text": "Job description text for a backend role.",
            "target_role": "Backend Developer",
            "source_url": "https://example.com/jobs/123",
        })

        assert resp.status_code == 201
        payload = resp.json()
        assert payload["job_title"] == "Junior Backend Developer"
        assert payload["status"] == "saved"
        assert payload["source_url"] == "https://example.com/jobs/123"
        assert payload["best_analysis_job_id"] is None
        assert payload["last_readiness_score"] is None
        assert payload["user_id"] == str(user.id)

    def test_create_missing_required_fields_returns_422(self):
        user = make_user()
        client = build_client(FakeDb(), user)
        resp = client.post("/v1/target-jobs", json={"job_title": "Dev"})
        assert resp.status_code == 422

    def test_list_returns_only_current_users_jobs(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_a = make_target_job(user_a.id)
        job_b = make_target_job(user_b.id)
        db.add(job_a)
        db.add(job_b)

        client = build_client(db, user_a)
        resp = client.get("/v1/target-jobs")

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == str(job_a.id)

    def test_list_filters_by_status(self):
        user = make_user()
        db = FakeDb()
        saved = make_target_job(user.id, status="saved")
        applied = make_target_job(user.id, status="applied")
        db.add(saved)
        db.add(applied)
        client = build_client(db, user)

        resp = client.get("/v1/target-jobs?status=applied")

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["status"] == "applied"

    def test_get_own_job_returns_200(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        resp = client.get(f"/v1/target-jobs/{job.id}")

        assert resp.status_code == 200
        assert resp.json()["id"] == str(job.id)

    def test_get_another_users_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_target_job(user_b.id)
        db.add(job_b)
        client = build_client(db, user_a)

        resp = client.get(f"/v1/target-jobs/{job_b.id}")

        assert resp.status_code == 404

    def test_patch_own_job_updates_fields(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        resp = client.patch(f"/v1/target-jobs/{job.id}", json={
            "job_title": "Senior Developer",
            "status": "interviewing",
        })

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["job_title"] == "Senior Developer"
        assert payload["status"] == "interviewing"

    def test_patch_each_phase6_status_is_valid(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        for new_status in (
            "saved", "analyzing", "ready_to_apply", "interviewing",
            "applied", "rejected", "offer", "archived",
        ):
            resp = client.patch(f"/v1/target-jobs/{job.id}", json={"status": new_status})
            assert resp.status_code == 200, new_status
            assert resp.json()["status"] == new_status

    def test_patch_invalid_status_returns_422(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        resp = client.patch(f"/v1/target-jobs/{job.id}", json={"status": "not_a_status"})

        assert resp.status_code == 422

    def test_patch_another_users_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_target_job(user_b.id)
        db.add(job_b)
        client = build_client(db, user_a)

        resp = client.patch(f"/v1/target-jobs/{job_b.id}", json={"status": "applied"})

        assert resp.status_code == 404

    def test_delete_soft_archives_own_job(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        resp = client.delete(f"/v1/target-jobs/{job.id}")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["status"] == "archived"
        assert payload["archived_at"] is not None
        # Soft archive preserves the row.
        assert db.get(Application, job.id) is not None

    def test_delete_another_users_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_target_job(user_b.id)
        db.add(job_b)
        client = build_client(db, user_a)

        resp = client.delete(f"/v1/target-jobs/{job_b.id}")

        assert resp.status_code == 404
        assert db.get(Application, job_b.id) is not None


# ---------------------------------------------------------------------------
# Attach analysis + ownership
# ---------------------------------------------------------------------------

class TestAttachAnalysis:
    def test_attach_own_job_sets_best_analysis_and_readiness_score(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        analysis = make_job(user.id, fit_score=80.0)
        db.add(job)
        db.add(analysis)
        client = build_client(db, user)

        resp = client.post(f"/v1/target-jobs/{job.id}/attach-analysis/{analysis.id}")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["best_analysis_job_id"] == str(analysis.id)
        assert payload["last_readiness_score"] == 80
        assert db.get(Application, job.id).best_analysis_job_id == analysis.id

    def test_attach_another_users_analysis_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_a = make_target_job(user_a.id)
        analysis_b = make_job(user_b.id)
        db.add(job_a)
        db.add(analysis_b)
        db.add(user_b)
        client = build_client(db, user_a)

        resp = client.post(f"/v1/target-jobs/{job_a.id}/attach-analysis/{analysis_b.id}")

        assert resp.status_code == 404
        assert db.get(Application, job_a.id).best_analysis_job_id is None

    def test_attach_nonexistent_analysis_returns_404(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        resp = client.post(f"/v1/target-jobs/{job.id}/attach-analysis/{uuid.uuid4()}")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Readiness (safe empty payload)
# ---------------------------------------------------------------------------

class TestReadiness:
    def test_readiness_without_analysis_returns_not_started(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        resp = client.get(f"/v1/target-jobs/{job.id}/readiness")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["readiness_level"] == "not_started"
        assert payload["fit_score"] is None
        assert payload["disclaimer"]

    def test_readiness_with_high_score_returns_ready(self):
        user = make_user()
        db = FakeDb()
        analysis = make_job(user.id, fit_score=82.0)
        job = make_target_job(user.id, best_analysis_job_id=analysis.id)
        db.add(job)
        db.add(analysis)
        client = build_client(db, user)

        resp = client.get(f"/v1/target-jobs/{job.id}/readiness")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["readiness_level"] == "ready"
        assert payload["fit_score"] == 82.0

    def test_readiness_for_another_users_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_target_job(user_b.id)
        db.add(job_b)
        client = build_client(db, user_a)

        resp = client.get(f"/v1/target-jobs/{job_b.id}/readiness")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Package (safe empty payload)
# ---------------------------------------------------------------------------

class TestPackage:
    def test_package_without_artifact_returns_safe_empty_payload(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        client = build_client(db, user)

        resp = client.get(f"/v1/target-jobs/{job.id}/package")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["has_package"] is False
        assert payload["payload_json"] is None

    def test_package_returns_latest_artifact_when_present(self):
        user = make_user()
        db = FakeDb()
        job = make_target_job(user.id)
        db.add(job)
        artifact = ApplicationArtifact(
            id=uuid.uuid4(),
            user_id=user.id,
            application_id=job.id,
            artifact_type="application_package",
            payload_json={"disclaimer": "draft only", "sections": []},
            created_at=datetime.utcnow(),
        )
        db.add(artifact)
        client = build_client(db, user)

        resp = client.get(f"/v1/target-jobs/{job.id}/package")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["has_package"] is True
        assert payload["artifact_id"] == str(artifact.id)
        assert payload["payload_json"]["disclaimer"] == "draft only"

    def test_package_for_another_users_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_target_job(user_b.id)
        db.add(job_b)
        client = build_client(db, user_a)

        resp = client.get(f"/v1/target-jobs/{job_b.id}/package")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Feature flag
# ---------------------------------------------------------------------------

class TestFeatureFlag:
    def test_disabled_flag_returns_404(self, monkeypatch):
        from app.core import config as config_module

        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        db.add(tj)
        client = build_client(db, user)

        monkeypatch.setattr(config_module.settings, "ENABLE_PHASE6_TARGET_JOBS", False)
        resp = client.get("/v1/target-jobs")
        assert resp.status_code == 404
