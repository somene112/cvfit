"""Phase 6 backend tests — Interview Practice v2 (sessions/questions/answers)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.interview_sessions import router
from app.core.security import create_access_token
from app.db.models import (
    AnalysisJob,
    Application,
    InterviewSession,
    InterviewSessionAnswer,
    InterviewSessionQuestion,
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

    def order_by(self, *args):
        try:
            key = args[0].key
            self._rows = sorted(self._rows, key=lambda r: getattr(r, key, None) or datetime.min, reverse=True)
        except Exception:
            pass
        return self

    def all(self):
        return list(self._rows)


def make_user(email="user@example.com") -> User:
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_job(user_id: uuid.UUID) -> AnalysisJob:
    now = datetime.utcnow()
    result = {
        "overall_fit_score": 60.0,
        "missing_skills": [{"skill": "Kubernetes", "requirement_type": "must_have"}],
        "matched_skills": [{"skill": "Python", "requirement_type": "must_have"}],
    }
    return AnalysisJob(
        id=uuid.uuid4(), user_id=user_id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
        status="succeeded", progress=100, result_json=result, created_at=now, updated_at=now,
    )


def make_session(user_id, analysis_job_id=None, **kw) -> InterviewSession:
    now = datetime.utcnow()
    defaults = dict(
        id=uuid.uuid4(), user_id=user_id, target_job_id=None, application_id=None,
        analysis_job_id=analysis_job_id, session_type="mixed", difficulty="medium",
        status="active", created_at=now, updated_at=now,
    )
    defaults.update(kw)
    return InterviewSession(**defaults)


def make_question(session_id, **kw) -> InterviewSessionQuestion:
    now = datetime.utcnow()
    defaults = dict(
        id=uuid.uuid4(), session_id=session_id, question_type="behavioral", difficulty="medium",
        question_text="Tell me about a project using Python.", related_evidence_json=None,
        rubric_json={}, created_at=now,
    )
    defaults.update(kw)
    return InterviewSessionQuestion(**defaults)


def client_for(db: FakeDb, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    create_access_token(str(user.id))
    db.add(user)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def unauthed(db: FakeDb) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


class TestSessionAuth:
    def test_create_without_auth_returns_401(self):
        assert unauthed(FakeDb()).post("/v1/interview/sessions", json={}).status_code == 401


class TestSessionCRUD:
    def test_create_session(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        db.add(job)
        c = client_for(db, user)

        resp = c.post("/v1/interview/sessions", json={
            "analysis_job_id": str(job.id), "session_type": "technical", "difficulty": "hard",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["session_type"] == "technical"
        assert body["difficulty"] == "hard"
        assert body["status"] == "active"
        assert body["analysis_job_id"] == str(job.id)

    def test_create_session_invalid_difficulty_returns_422(self):
        user = make_user()
        db = FakeDb()
        c = client_for(db, user)
        assert c.post("/v1/interview/sessions", json={"difficulty": "impossible"}).status_code == 422

    def test_list_returns_only_own_sessions(self):
        ua, ub = make_user("a@example.com"), make_user("b@example.com")
        db = FakeDb()
        sa, sb = make_session(ua.id), make_session(ub.id)
        db.add(sa); db.add(sb)
        c = client_for(db, ua)

        resp = c.get("/v1/interview/sessions")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1 and items[0]["id"] == str(sa.id)

    def test_get_own_session(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        db.add(s)
        c = client_for(db, user)
        resp = c.get(f"/v1/interview/sessions/{s.id}")
        assert resp.status_code == 200
        assert resp.json()["session"]["id"] == str(s.id)

    def test_get_cross_user_session_returns_404(self):
        ua, ub = make_user("a@example.com"), make_user("b@example.com")
        db = FakeDb()
        sb = make_session(ub.id)
        db.add(sb)
        c = client_for(db, ua)
        assert c.get(f"/v1/interview/sessions/{sb.id}").status_code == 404


class TestQuestionGeneration:
    def test_generate_questions_for_own_session(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        s = make_session(user.id, analysis_job_id=job.id)
        db.add(job); db.add(s)
        c = client_for(db, user)

        resp = c.post(f"/v1/interview/sessions/{s.id}/questions/generate", json={"count": 3})
        assert resp.status_code == 201
        body = resp.json()
        assert 1 <= body["total"] <= 3
        assert body["limitations"]
        for q in body["questions"]:
            assert q["question_text"]
            assert q["rubric"] is not None

    def test_generate_respects_question_type_and_difficulty(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        db.add(s)
        c = client_for(db, user)

        resp = c.post(f"/v1/interview/sessions/{s.id}/questions/generate", json={
            "question_type": "behavioral", "difficulty": "hard", "count": 2,
        })
        assert resp.status_code == 201
        for q in resp.json()["questions"]:
            assert q["question_type"] == "behavioral"
            assert q["difficulty"] == "hard"

    def test_generate_invalid_question_type_returns_422(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        db.add(s)
        c = client_for(db, user)
        resp = c.post(f"/v1/interview/sessions/{s.id}/questions/generate", json={"question_type": "trivia"})
        assert resp.status_code == 422

    def test_generate_cross_user_session_returns_404(self):
        ua, ub = make_user("a@example.com"), make_user("b@example.com")
        db = FakeDb()
        sb = make_session(ub.id)
        db.add(sb)
        c = client_for(db, ua)
        assert c.post(f"/v1/interview/sessions/{sb.id}/questions/generate", json={}).status_code == 404


class TestAnswers:
    def test_submit_answer_returns_rubric(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        q = make_question(s.id)
        db.add(s); db.add(q)
        c = client_for(db, user)

        resp = c.post(f"/v1/interview/sessions/{s.id}/answers", json={
            "question_id": str(q.id),
            "answer_text": "I built a Python service that reduced latency by 30% using caching and async I/O.",
        })
        assert resp.status_code == 201
        body = resp.json()
        for dim in ("relevance", "evidence", "clarity", "structure", "confidence", "risk"):
            assert dim in body["score"]
        assert body["attempt_number"] == 1

    def test_attempt_number_increments(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        q = make_question(s.id)
        db.add(s); db.add(q)
        c = client_for(db, user)

        first = c.post(f"/v1/interview/sessions/{s.id}/answers", json={"question_id": str(q.id), "answer_text": "First attempt answer."})
        second = c.post(f"/v1/interview/sessions/{s.id}/answers", json={"question_id": str(q.id), "answer_text": "Second, more detailed attempt with specifics."})
        assert first.json()["attempt_number"] == 1
        assert second.json()["attempt_number"] == 2

    def test_answer_unsupported_skill_claim_raises_risk_flag(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)  # missing skill: Kubernetes
        s = make_session(user.id, analysis_job_id=job.id)
        q = make_question(s.id, question_text="How would you handle Kubernetes in production?")
        db.add(job); db.add(s); db.add(q)
        c = client_for(db, user)

        resp = c.post(f"/v1/interview/sessions/{s.id}/answers", json={
            "question_id": str(q.id),
            "answer_text": "I am an expert in Kubernetes and have deployed many clusters.",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["score"]["risk"] >= 1
        assert body["feedback"]["risk_flags"]

    def test_submit_answer_cross_user_session_returns_404(self):
        ua, ub = make_user("a@example.com"), make_user("b@example.com")
        db = FakeDb()
        sb = make_session(ub.id)
        qb = make_question(sb.id)
        db.add(sb); db.add(qb)
        c = client_for(db, ua)
        resp = c.post(f"/v1/interview/sessions/{sb.id}/answers", json={"question_id": str(qb.id), "answer_text": "x"})
        assert resp.status_code == 404

    def test_list_answers_returns_only_session_answers(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        q = make_question(s.id)
        db.add(s); db.add(q)
        c = client_for(db, user)
        c.post(f"/v1/interview/sessions/{s.id}/answers", json={"question_id": str(q.id), "answer_text": "An answer with detail."})

        resp = c.get(f"/v1/interview/sessions/{s.id}/answers")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestSummary:
    def test_summary_returns_aggregate_metrics(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        q = make_question(s.id)
        db.add(s); db.add(q)
        c = client_for(db, user)
        c.post(f"/v1/interview/sessions/{s.id}/answers", json={
            "question_id": str(q.id),
            "answer_text": "I built a Python data pipeline that improved throughput; first I designed it, then I implemented and tested it.",
        })

        resp = c.get(f"/v1/interview/sessions/{s.id}/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_answers"] == 1
        assert body["average_score"] is not None
        assert body["best_dimension"]
        assert body["weakest_dimension"]
        assert "guarantee" in body["disclaimer"].lower()

    def test_summary_empty_session_is_safe(self):
        user = make_user()
        db = FakeDb()
        s = make_session(user.id)
        db.add(s)
        c = client_for(db, user)
        resp = c.get(f"/v1/interview/sessions/{s.id}/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_answers"] == 0
        assert body["average_score"] is None


class TestFeatureFlag:
    def test_disabled_flag_returns_404(self, monkeypatch):
        from app.core import config as config_module
        user = make_user()
        db = FakeDb()
        c = client_for(db, user)
        monkeypatch.setattr(config_module.settings, "ENABLE_PHASE6_INTERVIEW_V2", False)
        assert c.get("/v1/interview/sessions").status_code == 404
