"""
Phase 5 backend tests — Application Workspace and Career Profile APIs.

Tests use in-memory fake DB objects following the established pattern in
test_auth_routes.py and test_jobs_auth.py. No real database is required.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.routes.applications import router as applications_router
from app.api.routes.profile import router as profile_router
from app.core.security import create_access_token
from app.db.models import AnalysisJob, Application, ApplicationArtifact, CareerProfileItem, InterviewAnswer, User
from app.db.session import get_db
from app.api.deps import get_current_user


# ---------------------------------------------------------------------------
# Fake DB
# ---------------------------------------------------------------------------

class FakeDb:
    def __init__(self):
        self._store: dict[tuple, Any] = {}
        self._query_results: dict[type, list] = {}

    def _key(self, model, pk):
        return (model.__tablename__, pk)

    def add(self, obj):
        pk = obj.id
        self._store[self._key(type(obj), pk)] = obj
        model_type = type(obj)
        if model_type not in self._query_results:
            self._query_results[model_type] = []
        if obj not in self._query_results[model_type]:
            self._query_results[model_type].append(obj)

    def get(self, model, pk):
        return self._store.get(self._key(model, pk))

    def delete(self, obj):
        key = self._key(type(obj), obj.id)
        self._store.pop(key, None)
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
        # Apply simple equality filters by inspecting SQLAlchemy BinaryExpression
        new_rows = list(self._rows)
        for expr in args:
            try:
                col_key = expr.left.key
                col_val = expr.right.value
                new_rows = [r for r in new_rows if getattr(r, col_key, None) == col_val]
            except AttributeError:
                pass
        q = FakeQuery(new_rows, self._model, db=self._db)
        return q

    def delete(self):
        for row in list(self._rows):
            if self._db is not None:
                self._db.delete(row)
        return len(self._rows)

    def order_by(self, *args):
        try:
            col_key = args[0].key
            desc = hasattr(args[0], "modifier") or str(args[0]).endswith("DESC")
        except Exception:
            return self
        try:
            self._rows = sorted(self._rows, key=lambda r: getattr(r, col_key, None) or datetime.min, reverse=True)
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


def make_application(
    user_id: uuid.UUID,
    status: str = "draft",
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


def make_profile_item(
    user_id: uuid.UUID,
    item_type: str = "project",
) -> CareerProfileItem:
    now = datetime.utcnow()
    return CareerProfileItem(
        id=uuid.uuid4(),
        user_id=user_id,
        item_type=item_type,
        title="E-commerce API",
        description="Built a REST API using FastAPI.",
        skills_json=["FastAPI", "PostgreSQL"],
        evidence_text="github.com/user/project",
        source="GitHub",
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


def build_app_client(db: FakeDb, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(applications_router)
    app.include_router(profile_router)
    token = create_access_token(str(user.id))
    db.add(user)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)
    client._auth_headers = {"Authorization": f"Bearer {token}"}
    return client


def build_unauthed_client(db: FakeDb) -> TestClient:
    """Client with no auth override — tests that get_current_user returns 401."""
    app = FastAPI()
    app.include_router(applications_router)
    app.include_router(profile_router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Application Workspace tests
# ---------------------------------------------------------------------------

class TestApplicationAuth:
    def test_create_application_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        resp = client.post("/v1/applications", json={
            "job_title": "Dev", "jd_text": "some text"
        })
        assert resp.status_code == 401

    def test_list_applications_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        assert client.get("/v1/applications").status_code == 401

    def test_get_application_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        assert client.get(f"/v1/applications/{uuid.uuid4()}").status_code == 401


class TestApplicationCRUD:
    def test_create_application_returns_201_with_draft_status(self):
        user = make_user()
        db = FakeDb()
        client = build_app_client(db, user)

        resp = client.post("/v1/applications", json={
            "job_title": "Junior Backend Developer",
            "company_name": "Example Company",
            "jd_text": "Job description text for a backend role.",
            "target_role": "Backend Developer",
        })

        assert resp.status_code == 201
        payload = resp.json()
        assert payload["job_title"] == "Junior Backend Developer"
        assert payload["status"] == "draft"
        assert payload["best_analysis_job_id"] is None
        assert payload["user_id"] == str(user.id)

    def test_list_returns_only_current_users_applications(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_a = make_application(user_a.id)
        app_b = make_application(user_b.id)
        db.add(app_a)
        db.add(app_b)

        client = build_app_client(db, user_a)
        resp = client.get("/v1/applications")

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == str(app_a.id)

    def test_get_own_application_returns_200(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}")

        assert resp.status_code == 200
        assert resp.json()["id"] == str(app.id)

    def test_get_another_users_application_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        db.add(app_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/applications/{app_b.id}")

        assert resp.status_code == 404

    def test_patch_own_application_updates_fields(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/applications/{app.id}", json={
            "job_title": "Senior Developer",
            "status": "improving_cv",
        })

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["job_title"] == "Senior Developer"
        assert payload["status"] == "improving_cv"

    def test_patch_invalid_status_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/applications/{app.id}", json={"status": "invalid_status"})

        assert resp.status_code == 422

    def test_delete_own_application_returns_204(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.delete(f"/v1/applications/{app.id}")

        assert resp.status_code == 204
        assert db.get(Application, app.id) is None

    def test_delete_another_users_application_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        db.add(app_b)
        client = build_app_client(db, user_a)

        resp = client.delete(f"/v1/applications/{app_b.id}")

        assert resp.status_code == 404

    def test_delete_application_with_interview_answer_returns_204(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        answer = InterviewAnswer(
            id=uuid.uuid4(),
            user_id=user.id,
            application_id=app.id,
            job_id=None,
            question="Tell me about yourself.",
            answer_text="I am a developer.",
            rubric_json={"overall": 2},
            feedback_json={"strengths": []},
            created_at=datetime.utcnow(),
        )
        db.add(answer)
        client = build_app_client(db, user)

        resp = client.delete(f"/v1/applications/{app.id}")

        assert resp.status_code == 204
        assert db.get(Application, app.id) is None
        assert db.get(InterviewAnswer, answer.id) is None

    def test_create_application_missing_required_fields_returns_422(self):
        user = make_user()
        db = FakeDb()
        client = build_app_client(db, user)

        resp = client.post("/v1/applications", json={"job_title": "Dev"})

        assert resp.status_code == 422


class TestAttachAnalysis:
    def test_attach_own_job_sets_best_analysis_job_id(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        job = make_job(user.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(f"/v1/applications/{app.id}/attach-analysis/{job.id}")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["best_analysis_job_id"] == str(job.id)
        assert db.get(Application, app.id).best_analysis_job_id == job.id

    def test_attach_another_users_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_a = make_application(user_a.id)
        job_b = make_job(user_b.id)
        db.add(app_a)
        db.add(job_b)
        db.add(user_b)
        client = build_app_client(db, user_a)

        resp = client.post(f"/v1/applications/{app_a.id}/attach-analysis/{job_b.id}")

        assert resp.status_code == 404

    def test_attach_nonexistent_job_returns_404(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(f"/v1/applications/{app.id}/attach-analysis/{uuid.uuid4()}")

        assert resp.status_code == 404


class TestReadiness:
    def test_readiness_without_analysis_returns_not_started(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/readiness")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["readiness_level"] == "not_started"
        assert payload["fit_score"] is None
        assert payload["disclaimer"]

    def test_readiness_with_high_score_returns_ready(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit_score=80.0)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/readiness")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["readiness_level"] == "ready"
        assert payload["fit_score"] == 80.0

    def test_readiness_with_mid_score_returns_almost_ready(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit_score=60.0)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/readiness")

        assert resp.status_code == 200
        assert resp.json()["readiness_level"] == "almost_ready"

    def test_readiness_with_low_score_returns_needs_work(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit_score=40.0)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/readiness")

        assert resp.status_code == 200
        assert resp.json()["readiness_level"] == "needs_work"

    def test_readiness_for_another_users_application_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        db.add(app_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/applications/{app_b.id}/readiness")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Career Profile tests
# ---------------------------------------------------------------------------

class TestProfileAuth:
    def test_create_profile_item_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        resp = client.post("/v1/profile/items", json={
            "item_type": "project", "title": "My Project"
        })
        assert resp.status_code == 401

    def test_list_profile_items_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        assert client.get("/v1/profile/items").status_code == 401


class TestProfileCRUD:
    def test_create_profile_item_returns_201(self):
        user = make_user()
        db = FakeDb()
        client = build_app_client(db, user)

        resp = client.post("/v1/profile/items", json={
            "item_type": "project",
            "title": "CV Fit App",
            "description": "Built a CV/JD analysis app.",
            "skills_json": ["FastAPI", "PostgreSQL", "Celery"],
            "evidence_text": "Implemented backend APIs.",
            "source": "user_entered",
        })

        assert resp.status_code == 201
        payload = resp.json()
        assert payload["title"] == "CV Fit App"
        assert payload["item_type"] == "project"
        assert payload["user_id"] == str(user.id)

    def test_list_returns_only_current_users_profile_items(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        item_a = make_profile_item(user_a.id)
        item_b = make_profile_item(user_b.id)
        db.add(item_a)
        db.add(item_b)

        client = build_app_client(db, user_a)
        resp = client.get("/v1/profile/items")

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == str(item_a.id)

    def test_get_own_profile_item_returns_200(self):
        user = make_user()
        db = FakeDb()
        item = make_profile_item(user.id)
        db.add(item)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/profile/items/{item.id}")

        assert resp.status_code == 200
        assert resp.json()["id"] == str(item.id)

    def test_get_another_users_profile_item_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        item_b = make_profile_item(user_b.id)
        db.add(item_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/profile/items/{item_b.id}")

        assert resp.status_code == 404

    def test_patch_own_profile_item_updates_fields(self):
        user = make_user()
        db = FakeDb()
        item = make_profile_item(user.id)
        db.add(item)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/profile/items/{item.id}", json={
            "title": "Updated Project Title",
            "skills_json": ["FastAPI", "PostgreSQL", "Docker"],
        })

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["title"] == "Updated Project Title"
        assert "Docker" in payload["skills_json"]

    def test_patch_invalid_item_type_returns_422(self):
        user = make_user()
        db = FakeDb()
        item = make_profile_item(user.id)
        db.add(item)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/profile/items/{item.id}", json={"item_type": "invalid_type"})

        assert resp.status_code == 422

    def test_delete_own_profile_item_returns_204(self):
        user = make_user()
        db = FakeDb()
        item = make_profile_item(user.id)
        db.add(item)
        client = build_app_client(db, user)

        resp = client.delete(f"/v1/profile/items/{item.id}")

        assert resp.status_code == 204
        assert db.get(CareerProfileItem, item.id) is None

    def test_delete_another_users_profile_item_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        item_b = make_profile_item(user_b.id)
        db.add(item_b)
        client = build_app_client(db, user_a)

        resp = client.delete(f"/v1/profile/items/{item_b.id}")

        assert resp.status_code == 404

    def test_create_item_missing_required_fields_returns_422(self):
        user = make_user()
        db = FakeDb()
        client = build_app_client(db, user)

        resp = client.post("/v1/profile/items", json={"item_type": "project"})

        assert resp.status_code == 422

    def test_list_filters_by_item_type(self):
        user = make_user()
        db = FakeDb()
        project_item = make_profile_item(user.id, item_type="project")
        skill_item = make_profile_item(user.id, item_type="skill")
        skill_item.id = uuid.uuid4()
        skill_item.title = "Python skill"
        db.add(project_item)
        db.add(skill_item)
        client = build_app_client(db, user)

        resp = client.get("/v1/profile/items?item_type=project")

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["item_type"] == "project" for i in items)
