"""Phase 6 backend tests — Usage / Plan shell (computed, read-only)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.usage import router
from app.core.security import create_access_token
from app.db.models import (
    AnalysisJob,
    Application,
    ApplicationArtifact,
    InterviewSession,
    InterviewSessionAnswer,
    InterviewSessionQuestion,
    LearningTask,
    ShareLink,
    User,
)
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

    def all(self):
        return list(self._rows)


def make_user(email="user@example.com") -> User:
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_job(user_id) -> AnalysisJob:
    now = datetime.utcnow()
    return AnalysisJob(
        id=uuid.uuid4(), user_id=user_id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
        status="succeeded", progress=100, result_json={"overall_fit_score": 70.0}, created_at=now, updated_at=now,
    )


def make_app(user_id) -> Application:
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(), user_id=user_id, job_title="Dev", company_name="Co",
        jd_text="jd", target_role="Backend", status="saved", created_at=now, updated_at=now,
    )


def make_task(user_id) -> LearningTask:
    now = datetime.utcnow()
    return LearningTask(
        id=uuid.uuid4(), user_id=user_id, skill="FastAPI", category="backend",
        priority="high", task_type="project", title="t", description="d",
        evidence_to_add="e", status="todo", created_at=now, updated_at=now,
    )


def make_session(user_id) -> InterviewSession:
    now = datetime.utcnow()
    return InterviewSession(
        id=uuid.uuid4(), user_id=user_id, target_job_id=None, application_id=None,
        analysis_job_id=None, session_type="mixed", difficulty="medium", status="active",
        created_at=now, updated_at=now,
    )


def make_answer(session_id) -> InterviewSessionAnswer:
    now = datetime.utcnow()
    qid = uuid.uuid4()
    return InterviewSessionAnswer(
        id=uuid.uuid4(), session_id=session_id, question_id=qid, answer_text="ans",
        score_json={"relevance": 3}, feedback_json={"strengths": []}, attempt_number=1, created_at=now,
    )


def make_artifact(user_id, atype) -> ApplicationArtifact:
    now = datetime.utcnow()
    return ApplicationArtifact(
        id=uuid.uuid4(), user_id=user_id, application_id=uuid.uuid4(),
        artifact_type=atype, payload_json={"disclaimer": "x"}, created_at=now,
    )


def make_share(user_id) -> ShareLink:
    now = datetime.utcnow()
    return ShareLink(
        id=uuid.uuid4(), user_id=user_id, target_type="target_job", target_id=uuid.uuid4(),
        token_hash="h" * 64, visibility_json={}, expires_at=None, revoked_at=None,
        created_at=now, updated_at=None,
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


class TestPlans:
    def test_plans_returns_free_demo_no_checkout(self):
        user = make_user()
        c = client_for(FakeDb(), user)
        resp = c.get("/v1/plans")
        assert resp.status_code == 200
        body = resp.json()
        assert any(p["id"] == "free_demo" for p in body["plans"])
        assert body["upgrade_available"] is False
        assert "checkout_url" not in resp.text
        assert "stripe" not in resp.text.lower()
        assert "payos" not in resp.text.lower()


class TestUsageAuthAndFlag:
    def test_usage_requires_auth(self):
        assert unauthed(FakeDb()).get("/v1/usage/me").status_code == 401

    def test_flag_disabled_returns_404(self, monkeypatch):
        from app.core import config as cfg
        user = make_user()
        c = client_for(FakeDb(), user)
        monkeypatch.setattr(cfg.settings, "ENABLE_PHASE6_USAGE_SHELL", False)
        assert c.get("/v1/usage/me").status_code == 404
        assert c.get("/v1/plans").status_code == 404


class TestUsageComputation:
    def test_zero_records_is_safe(self):
        user = make_user()
        c = client_for(FakeDb(), user)
        resp = c.get("/v1/usage/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["enforcement_enabled"] is False
        assert all(v == 0 for v in body["usage"].values())
        assert body["plan_id"] == "free_demo"

    def test_counts_only_current_user_records(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        # user A: 1 analysis, 2 apps, 1 task, 1 session+1 answer, 1 cover letter, 1 package, 1 share
        db.add(make_job(ua.id))
        db.add(make_app(ua.id)); db.add(make_app(ua.id))
        db.add(make_task(ua.id))
        sess = make_session(ua.id); db.add(sess); db.add(make_answer(sess.id))
        db.add(make_artifact(ua.id, "cover_letter_draft"))
        db.add(make_artifact(ua.id, "application_package"))
        db.add(make_share(ua.id))
        # user B noise
        db.add(make_job(ub.id)); db.add(make_app(ub.id))
        sess_b = make_session(ub.id); db.add(sess_b); db.add(make_answer(sess_b.id))

        c = client_for(db, ua)
        body = c.get("/v1/usage/me").json()
        u = body["usage"]
        assert u["analyses"] == 1
        assert u["applications"] == 2
        assert u["learning_tasks"] == 1
        assert u["interview_sessions"] == 1
        assert u["interview_answers"] == 1
        assert u["cover_letters"] == 1
        assert u["application_packages"] == 1
        assert u["share_links"] == 1

    def test_no_payment_fields_present(self):
        user = make_user()
        c = client_for(FakeDb(), user)
        resp = c.get("/v1/usage/me")
        body = resp.json()
        text = resp.text.lower()
        # No payment integration fields/URLs (the disclaimer copy may say the word
        # "checkout" to state it is NOT enabled — that is fine).
        for forbidden in ("checkout_url", "credit_card", "stripe", "payos", "price_id"):
            assert forbidden not in text
        assert body["enforcement_enabled"] is False

    def test_warning_appears_near_limit_but_not_enforced(self):
        user = make_user()
        db = FakeDb()
        # 16 applications vs limit 20 -> >= 80% threshold triggers a warning
        for _ in range(16):
            db.add(make_app(user.id))
        c = client_for(db, user)
        body = c.get("/v1/usage/me").json()
        assert body["enforcement_enabled"] is False
        assert any("applications" in w for w in body["warnings"])

    def test_no_raw_text_in_usage_response(self):
        user = make_user()
        db = FakeDb()
        db.add(make_app(user.id))
        c = client_for(db, user)
        text = c.get("/v1/usage/me").text
        # response is counts + static copy only
        assert "token_hash" not in text
        assert "jd_text" not in text
