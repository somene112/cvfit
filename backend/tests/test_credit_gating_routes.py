"""Integration checks for credit-gated write routes and public 402 shape."""

from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.exception_handlers import insufficient_credits_handler
from app.api.routes import applications, interview_sessions, jobs
from app.db.models import (
    AnalysisJob,
    Application,
    CVFile,
    InterviewSession,
    InterviewSessionQuestion,
    User,
)
from app.schemas.interview_sessions import AnswerCreateRequest
from app.schemas.phase5 import InterviewAnswerCreate
from app.schemas.requests import ScoreCreateRequest
from app.services.billing.credit_gating import InsufficientCreditsError


class CommitReached(RuntimeError):
    pass


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter(self, *expressions):
        rows = self.rows
        for expression in expressions:
            try:
                key = expression.left.key
                value = expression.right.value
                rows = [row for row in rows if getattr(row, key, None) == value]
            except AttributeError:
                pass
        return FakeQuery(rows)

    def all(self):
        return list(self.rows)


class FakeDb:
    def __init__(self, *rows, stop_on_commit=True):
        self.rows = list(rows)
        self.stop_on_commit = stop_on_commit

    def get(self, model, key):
        return next(
            (row for row in self.rows if isinstance(row, model) and row.id == key),
            None,
        )

    def query(self, model):
        return FakeQuery(row for row in self.rows if isinstance(row, model))

    def add(self, row):
        self.rows.append(row)

    def flush(self):
        pass

    def commit(self):
        if self.stop_on_commit:
            raise CommitReached()

    def refresh(self, row):
        del row


def make_user():
    return User(id=uuid.uuid4(), email="gating@example.com", is_active=True)


def make_job(user_id):
    now = datetime.utcnow()
    return AnalysisJob(
        id=uuid.uuid4(), user_id=user_id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
        status="succeeded", progress=100, result_json={}, created_at=now, updated_at=now,
    )


def make_application(user_id, job_id):
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(), user_id=user_id, job_title="Engineer", company_name="Example",
        jd_text="A sufficiently detailed job description", status="draft",
        best_analysis_job_id=job_id, created_at=now, updated_at=now,
    )


def _raise_insufficient(*args, **kwargs):
    del args, kwargs
    raise InsufficientCreditsError("analysis")


def test_insufficient_credits_handler_returns_machine_readable_402():
    app = FastAPI()
    app.add_exception_handler(InsufficientCreditsError, insufficient_credits_handler)

    @app.get("/gated")
    def gated():
        raise InsufficientCreditsError("analysis")

    response = TestClient(app).get("/gated")

    assert response.status_code == 402
    assert response.json() == {
        "error": "insufficient_credits",
        "message": "You do not have enough credits for this action.",
        "required_credit": "analysis",
        "pricing_url": "/pricing",
    }


def test_cv_analysis_checks_credit_before_creating_job(monkeypatch):
    user = make_user()
    cv = CVFile(
        id=uuid.uuid4(), original_filename="cv.pdf", mime_type="application/pdf",
        storage_path="safe/path", sha256="0" * 64,
    )
    db = FakeDb(cv)
    monkeypatch.setattr(jobs, "ensure_credit_available", _raise_insufficient)

    with pytest.raises(InsufficientCreditsError):
        jobs.create_score_job(
            ScoreCreateRequest(
                cv_file_id=str(cv.id),
                jd_text="Backend engineer role requiring Python and database experience.",
            ),
            db,
            user,
        )

    assert db.rows == [cv]


@pytest.mark.parametrize(
    ("route_module", "route_call"),
    [
        (
            applications,
            lambda module, app, job, user, db: module.generate_package(app.id, user, db),
        ),
        (
            applications,
            lambda module, app, job, user, db: module.generate_cover_letter(app.id, user, db),
        ),
        (
            applications,
            lambda module, app, job, user, db: module.submit_interview_answer(
                app.id,
                InterviewAnswerCreate(
                    question_id="q1", question="Tell me about a project", answer_text="A valid answer",
                ),
                user,
                db,
            ),
        ),
    ],
)
def test_application_generation_routes_block_before_expensive_work(
    monkeypatch, route_module, route_call
):
    user = make_user()
    job = make_job(user.id)
    app = make_application(user.id, job.id)
    db = FakeDb(user, job, app)
    monkeypatch.setattr(route_module, "ensure_credit_available", _raise_insufficient)

    with pytest.raises(InsufficientCreditsError):
        route_call(route_module, app, job, user, db)

    assert db.rows == [user, job, app]


def test_interview_v2_feedback_blocks_before_scoring(monkeypatch):
    user = make_user()
    session = InterviewSession(
        id=uuid.uuid4(), user_id=user.id, status="active", session_type="mixed",
        difficulty="medium", created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    question = InterviewSessionQuestion(
        id=uuid.uuid4(), session_id=session.id, question_type="behavioral",
        difficulty="medium", question_text="Tell me about a project", created_at=datetime.utcnow(),
    )
    db = FakeDb(user, session, question)
    monkeypatch.setattr(interview_sessions, "ensure_credit_available", _raise_insufficient)

    with pytest.raises(InsufficientCreditsError):
        interview_sessions.submit_answer(
            session.id,
            AnswerCreateRequest(question_id=str(question.id), answer_text="A valid answer"),
            user,
            db,
        )

    assert db.rows == [user, session, question]


def test_interview_v2_target_job_is_not_recorded_as_application(monkeypatch):
    user = make_user()
    target_job_id = uuid.uuid4()
    session = InterviewSession(
        id=uuid.uuid4(), user_id=user.id, status="active", session_type="mixed",
        difficulty="medium", target_job_id=target_job_id, application_id=None,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    question = InterviewSessionQuestion(
        id=uuid.uuid4(), session_id=session.id, question_type="behavioral",
        difficulty="medium", question_text="Tell me about a project", created_at=datetime.utcnow(),
    )
    captured = {}
    monkeypatch.setattr(
        interview_sessions,
        "ensure_credit_available",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(interview_sessions, "score_answer_v2", lambda *args, **kwargs: ({}, {}))

    def capture_consume(*args, **kwargs):
        del args
        captured.update(kwargs)

    monkeypatch.setattr(interview_sessions, "consume_credit", capture_consume)

    with pytest.raises(CommitReached):
        interview_sessions.submit_answer(
            session.id,
            AnswerCreateRequest(question_id=str(question.id), answer_text="A valid answer"),
            user,
            FakeDb(user, session, question),
        )

    assert captured["related_application_id"] is None
    assert target_job_id not in captured.values()


def test_all_expensive_action_families_stage_usage_before_commit(monkeypatch):
    user = make_user()
    job = make_job(user.id)
    app = make_application(user.id, job.id)
    consumed: list[tuple[str, dict]] = []

    def allow(*args, **kwargs):
        del args, kwargs

    def consume(db, user_id, credit_type, **kwargs):
        del db
        assert user_id == user.id
        consumed.append((credit_type, kwargs))

    for module in (jobs, applications, interview_sessions):
        monkeypatch.setattr(module, "ensure_credit_available", allow)
        monkeypatch.setattr(module, "consume_credit", consume)
    monkeypatch.setattr(applications, "build_package_payload", lambda *args, **kwargs: {})
    monkeypatch.setattr(applications, "build_cover_letter_payload", lambda *args, **kwargs: {})
    monkeypatch.setattr(applications, "score_answer", lambda *args, **kwargs: ({}, {}))
    monkeypatch.setattr(interview_sessions, "score_answer_v2", lambda *args, **kwargs: ({}, {}))

    cv = CVFile(
        id=uuid.uuid4(), original_filename="cv.pdf", mime_type="application/pdf",
        storage_path="safe/path", sha256="0" * 64,
    )
    with pytest.raises(CommitReached):
        jobs.create_score_job(
            ScoreCreateRequest(
                cv_file_id=str(cv.id),
                jd_text="Backend engineer role requiring Python and database experience.",
            ),
            FakeDb(cv),
            user,
        )

    with pytest.raises(CommitReached):
        applications.generate_package(app.id, user, FakeDb(user, job, app))
    with pytest.raises(CommitReached):
        applications.generate_cover_letter(app.id, user, FakeDb(user, job, app))
    with pytest.raises(CommitReached):
        applications.submit_interview_answer(
            app.id,
            InterviewAnswerCreate(
                question_id="q1", question="Tell me about a project", answer_text="A valid answer",
            ),
            user,
            FakeDb(user, job, app),
        )

    session = InterviewSession(
        id=uuid.uuid4(), user_id=user.id, status="active", session_type="mixed",
        difficulty="medium", analysis_job_id=job.id, application_id=app.id,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    question = InterviewSessionQuestion(
        id=uuid.uuid4(), session_id=session.id, question_type="behavioral",
        difficulty="medium", question_text="Tell me about a project", created_at=datetime.utcnow(),
    )
    with pytest.raises(CommitReached):
        interview_sessions.submit_answer(
            session.id,
            AnswerCreateRequest(question_id=str(question.id), answer_text="A valid answer"),
            user,
            FakeDb(user, job, app, session, question),
        )

    assert [credit_type for credit_type, _ in consumed] == [
        "analysis", "package", "cover_letter", "interview", "interview"
    ]
    assert all("related_job_id" in details for _, details in consumed)
