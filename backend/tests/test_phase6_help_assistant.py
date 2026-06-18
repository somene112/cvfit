"""Phase 6 backend tests — Help Assistant / Career Coach v1."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.help_assistant import router
from app.core.security import create_access_token
from app.db.models import AnalysisJob, Application, InterviewSession, LearningTask, User
from app.db.session import get_db


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

    def order_by(self, *a):
        return self

    def all(self):
        return list(self._rows)


def make_user(email="user@example.com") -> User:
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_job(user_id, fit=80.0, missing=True) -> AnalysisJob:
    now = datetime.utcnow()
    result = {
        "overall_fit_score": fit,
        "scores": {"fit_score": fit},
        "missing_skills": [{"skill": "Kubernetes", "requirement_type": "must_have"}] if missing else [],
        "matched_skills": [{"skill": "Python", "requirement_type": "must_have"}],
    }
    return AnalysisJob(
        id=uuid.uuid4(), user_id=user_id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
        status="succeeded", progress=100, result_json=result, created_at=now, updated_at=now,
    )


def make_target_job(user_id, best=None, status="saved") -> Application:
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(), user_id=user_id, job_title="Backend Dev", company_name="Co",
        jd_text="RAW_JD_SECRET", target_role="Backend", status=status,
        best_analysis_job_id=best, created_at=now, updated_at=now,
    )


def client_for(db, user):
    app = FastAPI()
    app.include_router(router)
    create_access_token(str(user.id))
    db.add(user)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def unauthed(db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


class TestAuthAndFlag:
    def test_without_auth_401(self):
        assert unauthed(FakeDb()).post("/v1/help/assistant", json={"intent": "help_product_usage"}).status_code == 401

    def test_flag_disabled_returns_404(self, monkeypatch):
        from app.core import config as cfg
        user = make_user()
        c = client_for(FakeDb(), user)
        monkeypatch.setattr(cfg.settings, "ENABLE_PHASE6_HELP_ASSISTANT", False)
        assert c.get("/v1/help/suggestions").status_code == 404


class TestSuggestions:
    def test_suggestions_lists_supported_intents(self):
        user = make_user()
        c = client_for(FakeDb(), user)
        resp = c.get("/v1/help/suggestions")
        assert resp.status_code == 200
        intents = {s["intent"] for s in resp.json()["suggestions"]}
        assert {"next_best_action", "explain_score", "help_product_usage"} <= intents


class TestIntents:
    def test_next_best_action_with_owned_target_job(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit=80.0)
        tj = make_target_job(user.id, best=job.id)
        db.add(job); db.add(tj)
        c = client_for(db, user)
        resp = c.post("/v1/help/assistant", json={"intent": "next_best_action", "target_job_id": str(tj.id)})
        assert resp.status_code == 200
        body = resp.json()
        assert body["fallback_used"] is False
        assert body["recommended_actions"]
        assert "RAW_JD_SECRET" not in resp.text

    def test_explain_score_with_owned_analysis(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit=72.0)
        tj = make_target_job(user.id, best=job.id)
        db.add(job); db.add(tj)
        c = client_for(db, user)
        resp = c.post("/v1/help/assistant", json={"intent": "explain_score", "target_job_id": str(tj.id)})
        assert resp.status_code == 200
        assert resp.json()["fallback_used"] is False
        assert "72" in resp.json()["answer"]

    def test_explain_gap_returns_derived_gaps(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        tj = make_target_job(user.id, best=job.id)
        db.add(job); db.add(tj)
        c = client_for(db, user)
        resp = c.post("/v1/help/assistant", json={"intent": "explain_gap", "target_job_id": str(tj.id)})
        assert resp.status_code == 200
        assert "Kubernetes" in resp.json()["answer"]

    def test_suggest_learning_references_tasks(self):
        user = make_user()
        db = FakeDb()
        now = datetime.utcnow()
        task = LearningTask(
            id=uuid.uuid4(), user_id=user.id, skill="FastAPI", category="backend",
            priority="high", task_type="project", title="Build FastAPI", description="d",
            evidence_to_add="e", status="todo", created_at=now, updated_at=now,
        )
        db.add(task)
        c = client_for(db, user)
        resp = c.post("/v1/help/assistant", json={"intent": "suggest_learning"})
        assert resp.status_code == 200
        assert "FastAPI" in resp.json()["answer"]
        assert "open_learning" in resp.json()["recommended_actions"]

    def test_suggest_interview_practice_with_session(self):
        user = make_user()
        db = FakeDb()
        now = datetime.utcnow()
        s = InterviewSession(
            id=uuid.uuid4(), user_id=user.id, target_job_id=None, application_id=None,
            analysis_job_id=None, session_type="mixed", difficulty="medium", status="active",
            created_at=now, updated_at=now,
        )
        db.add(s)
        c = client_for(db, user)
        resp = c.post("/v1/help/assistant", json={"intent": "suggest_interview_practice"})
        assert resp.status_code == 200
        assert "start_interview" in resp.json()["recommended_actions"]

    def test_explain_application_status(self):
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id, status="interviewing")
        db.add(tj)
        c = client_for(db, user)
        resp = c.post("/v1/help/assistant", json={"intent": "explain_application_status", "target_job_id": str(tj.id)})
        assert resp.status_code == 200
        assert "interviewing" in resp.json()["answer"]

    def test_help_product_usage_always_answers(self):
        user = make_user()
        c = client_for(FakeDb(), user)
        resp = c.post("/v1/help/assistant", json={"intent": "help_product_usage"})
        assert resp.status_code == 200
        assert resp.json()["fallback_used"] is False

    def test_insufficient_context_returns_fallback(self):
        user = make_user()
        c = client_for(FakeDb(), user)
        resp = c.post("/v1/help/assistant", json={"intent": "explain_score"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["fallback_used"] is True
        assert "cannot determine" in body["answer"].lower()

    def test_unsupported_intent_returns_422(self):
        user = make_user()
        c = client_for(FakeDb(), user)
        assert c.post("/v1/help/assistant", json={"intent": "predict_salary"}).status_code == 422


class TestOwnership:
    def test_cross_user_target_job_returns_404(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        tj_b = make_target_job(ub.id)
        db.add(tj_b)
        c = client_for(db, ua)
        resp = c.post("/v1/help/assistant", json={"intent": "next_best_action", "target_job_id": str(tj_b.id)})
        assert resp.status_code == 404

    def test_cross_user_analysis_returns_404(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        job_b = make_job(ub.id)
        db.add(job_b)
        c = client_for(db, ua)
        resp = c.post("/v1/help/assistant", json={"intent": "explain_score", "analysis_job_id": str(job_b.id)})
        assert resp.status_code == 404

    def test_cross_user_session_returns_404(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        now = datetime.utcnow()
        s_b = InterviewSession(
            id=uuid.uuid4(), user_id=ub.id, target_job_id=None, application_id=None,
            analysis_job_id=None, session_type="mixed", difficulty="medium", status="active",
            created_at=now, updated_at=now,
        )
        db.add(s_b)
        c = client_for(db, ua)
        resp = c.post("/v1/help/assistant", json={"intent": "suggest_interview_practice", "session_id": str(s_b.id)})
        assert resp.status_code == 404
