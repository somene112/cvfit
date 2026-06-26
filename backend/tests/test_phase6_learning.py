"""Phase 6 backend tests — Learning Roadmap.

Uses the in-memory FakeDb pattern from the Phase 5/6 suites. No real DB.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.learning import router, target_job_router
from app.core.security import create_access_token
from app.db.models import AnalysisJob, Application, LearningTask, User
from app.db.session import get_db


# ---------------------------------------------------------------------------
# Fake DB
# ---------------------------------------------------------------------------

class FakeDb:
    def __init__(self):
        self._store: dict[tuple, Any] = {}
        self._rows: dict[type, list] = {}

    def _key(self, model, pk):
        return (model.__tablename__, pk)

    def add(self, obj):
        self._store[self._key(type(obj), obj.id)] = obj
        self._rows.setdefault(type(obj), [])
        if obj not in self._rows[type(obj)]:
            self._rows[type(obj)].append(obj)

    def get(self, model, pk):
        return self._store.get(self._key(model, pk))

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        return FakeQuery(self._rows.get(model, []), model)


class FakeQuery:
    def __init__(self, rows, model):
        self._rows = list(rows)
        self._model = model

    def filter(self, *args):
        rows = list(self._rows)
        for expr in args:
            try:
                key = expr.left.key
                val = expr.right.value
                rows = [r for r in rows if getattr(r, key, None) == val]
            except AttributeError:
                pass
        return FakeQuery(rows, self._model)

    def order_by(self, *args):
        try:
            key = args[0].key
            self._rows = sorted(self._rows, key=lambda r: getattr(r, key, None) or datetime.min, reverse=True)
        except Exception:
            pass
        return self

    def all(self):
        return list(self._rows)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RAW_JD_SENTINEL = "RAW_JD_SECRET_TEXT_should_never_leak_into_tasks"


def make_user(email="user@example.com") -> User:
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_job(user_id: uuid.UUID, with_skills=True) -> AnalysisJob:
    now = datetime.utcnow()
    result = {
        "overall_fit_score": 60.0,
        "missing_skills": [
            {"skill": "FastAPI", "requirement_type": "must_have"},
            {"skill": "PostgreSQL", "requirement_type": "nice_to_have"},
        ] if with_skills else [],
        "matched_skills": [{"skill": "Python", "requirement_type": "must_have"}] if with_skills else [],
    }
    return AnalysisJob(
        id=uuid.uuid4(), user_id=user_id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
        status="succeeded", progress=100, result_json=result, created_at=now, updated_at=now,
    )


def make_target_job(user_id, best_analysis_job_id=None) -> Application:
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(), user_id=user_id, job_title="Backend Dev", company_name="Co",
        jd_text=RAW_JD_SENTINEL, target_role="Backend", status="saved",
        best_analysis_job_id=best_analysis_job_id, created_at=now, updated_at=now,
    )


def make_task(user_id, **kw) -> LearningTask:
    now = datetime.utcnow()
    defaults = dict(
        id=uuid.uuid4(), user_id=user_id, skill="FastAPI", category="backend",
        priority="high", task_type="project", title="Build evidence for FastAPI",
        description="desc", evidence_to_add="ev", status="todo", created_at=now, updated_at=now,
    )
    defaults.update(kw)
    return LearningTask(**defaults)


def client_for(db: FakeDb, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.include_router(target_job_router)
    create_access_token(str(user.id))
    db.add(user)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def unauthed(db: FakeDb) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.include_router(target_job_router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLearningAuth:
    def test_generate_without_auth_returns_401(self):
        assert unauthed(FakeDb()).post("/v1/learning/roadmaps/generate", json={}).status_code == 401

    def test_list_without_auth_returns_401(self):
        assert unauthed(FakeDb()).get("/v1/learning/tasks").status_code == 401


class TestGenerate:
    def test_generate_from_owned_target_job_with_analysis(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        tj = make_target_job(user.id, best_analysis_job_id=job.id)
        db.add(job); db.add(tj)
        c = client_for(db, user)

        resp = c.post(f"/v1/target-jobs/{tj.id}/learning/generate")
        assert resp.status_code == 201
        body = resp.json()
        assert body["total"] >= 1
        assert body["limitations"]
        # tasks linked to the target job + analysis
        for t in body["tasks"]:
            assert t["target_job_id"] == str(tj.id)
            assert t["analysis_job_id"] == str(job.id)
            assert t["status"] == "todo"

    def test_generate_from_owned_analysis_directly(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        db.add(job)
        c = client_for(db, user)

        resp = c.post("/v1/learning/roadmaps/generate", json={"analysis_job_id": str(job.id)})
        assert resp.status_code == 201
        assert resp.json()["total"] >= 1

    def test_generate_does_not_include_raw_jd_text(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        tj = make_target_job(user.id, best_analysis_job_id=job.id)
        db.add(job); db.add(tj)
        c = client_for(db, user)

        resp = c.post(f"/v1/target-jobs/{tj.id}/learning/generate")
        assert resp.status_code == 201
        blob = resp.text
        assert RAW_JD_SENTINEL not in blob

    def test_generate_with_no_context_returns_limited_fallback(self):
        user = make_user()
        db = FakeDb()
        c = client_for(db, user)

        resp = c.post("/v1/learning/roadmaps/generate", json={})
        assert resp.status_code == 201
        body = resp.json()
        assert "current analysis only" in body["limitations"].lower()
        assert body["total"] >= 1  # safe fallback profile tasks

    def test_generate_cross_user_target_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        tj_b = make_target_job(user_b.id)
        db.add(tj_b)
        c = client_for(db, user_a)

        resp = c.post(f"/v1/target-jobs/{tj_b.id}/learning/generate")
        assert resp.status_code == 404

    def test_generate_cross_user_analysis_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_job(user_b.id)
        db.add(job_b); db.add(user_b)
        c = client_for(db, user_a)

        resp = c.post("/v1/learning/roadmaps/generate", json={"analysis_job_id": str(job_b.id)})
        assert resp.status_code == 404


class TestTaskCRUD:
    def test_list_returns_only_own_tasks(self):
        ua, ub = make_user("a@example.com"), make_user("b@example.com")
        db = FakeDb()
        ta, tb = make_task(ua.id), make_task(ub.id)
        db.add(ta); db.add(tb)
        c = client_for(db, ua)

        resp = c.get("/v1/learning/tasks")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1 and items[0]["id"] == str(ta.id)

    def test_list_filters_by_status(self):
        user = make_user()
        db = FakeDb()
        db.add(make_task(user.id, status="todo"))
        db.add(make_task(user.id, status="done"))
        c = client_for(db, user)

        resp = c.get("/v1/learning/tasks?status=done")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1 and items[0]["status"] == "done"

    def test_get_own_task(self):
        user = make_user()
        db = FakeDb()
        t = make_task(user.id)
        db.add(t)
        c = client_for(db, user)
        assert c.get(f"/v1/learning/tasks/{t.id}").status_code == 200

    def test_get_cross_user_task_returns_404(self):
        ua, ub = make_user("a@example.com"), make_user("b@example.com")
        db = FakeDb()
        tb = make_task(ub.id)
        db.add(tb)
        c = client_for(db, ua)
        assert c.get(f"/v1/learning/tasks/{tb.id}").status_code == 404

    def test_patch_status_progression(self):
        user = make_user()
        db = FakeDb()
        t = make_task(user.id, status="todo")
        db.add(t)
        c = client_for(db, user)

        for s in ("in_progress", "done"):
            resp = c.patch(f"/v1/learning/tasks/{t.id}", json={"status": s})
            assert resp.status_code == 200
            assert resp.json()["status"] == s

    def test_patch_status_persists_for_subsequent_get(self):
        # Phase 7A regression: the detail-page optimistic update must round-trip
        # through the API. If PATCH returned success but GET still showed the
        # old status, the UI would flash the new value and revert on refresh.
        user = make_user()
        db = FakeDb()
        t = make_task(user.id, status="todo")
        db.add(t)
        c = client_for(db, user)

        patch_resp = c.patch(f"/v1/learning/tasks/{t.id}", json={"status": "in_progress"})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "in_progress"

        get_resp = c.get(f"/v1/learning/tasks/{t.id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "in_progress"
        assert get_resp.json()["id"] == str(t.id)

    def test_patch_status_unknown_task_returns_404(self):
        # The frontend treats 404 the same as any other failure (rolls back the
        # optimistic update). Confirm we never leak existence to other users.
        user = make_user()
        db = FakeDb()
        c = client_for(db, user)
        missing_id = uuid.uuid4()
        resp = c.patch(f"/v1/learning/tasks/{missing_id}", json={"status": "done"})
        assert resp.status_code == 404

    def test_patch_invalid_status_returns_422(self):
        user = make_user()
        db = FakeDb()
        t = make_task(user.id)
        db.add(t)
        c = client_for(db, user)
        assert c.patch(f"/v1/learning/tasks/{t.id}", json={"status": "nope"}).status_code == 422

    def test_patch_invalid_priority_returns_422(self):
        user = make_user()
        db = FakeDb()
        t = make_task(user.id)
        db.add(t)
        c = client_for(db, user)
        assert c.patch(f"/v1/learning/tasks/{t.id}", json={"priority": "urgent"}).status_code == 422

    def test_patch_cross_user_task_returns_404(self):
        ua, ub = make_user("a@example.com"), make_user("b@example.com")
        db = FakeDb()
        tb = make_task(ub.id)
        db.add(tb)
        c = client_for(db, ua)
        assert c.patch(f"/v1/learning/tasks/{tb.id}", json={"status": "done"}).status_code == 404


class TestFeatureFlag:
    def test_disabled_flag_returns_404(self, monkeypatch):
        from app.core import config as config_module
        user = make_user()
        db = FakeDb()
        c = client_for(db, user)
        monkeypatch.setattr(config_module.settings, "ENABLE_PHASE6_LEARNING", False)
        assert c.get("/v1/learning/tasks").status_code == 404
