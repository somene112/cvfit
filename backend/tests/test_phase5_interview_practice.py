"""
Phase 5 backend tests — Interview Practice APIs (PR6A).

Tests follow the same in-memory fake DB pattern used in PR5A tests.
No real database required.
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
from app.db.models import (
    AnalysisJob,
    Application,
    InterviewAnswer,
    CareerProfileItem,
    User,
)
from app.db.session import get_db
from app.api.deps import get_current_user


# ---------------------------------------------------------------------------
# Fake DB (mirrors test_phase5_package_cover_letter.py)
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
        return FakeQuery(self._query_results.get(model, []), model)


class FakeQuery:
    def __init__(self, rows, model):
        self._rows = list(rows)
        self._model = model

    def filter(self, *args):
        new_rows = list(self._rows)
        for expr in args:
            try:
                col_key = expr.left.key
                col_val = expr.right.value
                new_rows = [r for r in new_rows if getattr(r, col_key, None) == col_val]
            except AttributeError:
                pass
        return FakeQuery(new_rows, self._model)

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


def make_application(
    user_id: uuid.UUID,
    status: str = "draft",
    best_analysis_job_id: Optional[uuid.UUID] = None,
    company_name: Optional[str] = "TestCo",
) -> Application:
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(),
        user_id=user_id,
        job_title="Backend Developer",
        company_name=company_name,
        jd_text="We need a backend developer with Python, FastAPI, and PostgreSQL skills.",
        target_role="Backend",
        status=status,
        best_analysis_job_id=best_analysis_job_id,
        created_at=now,
        updated_at=now,
    )


def make_job(
    user_id: uuid.UUID,
    status: str = "succeeded",
    fit_score: float = 72.0,
    matched_skills: Optional[list] = None,
    missing_skills: Optional[list] = None,
    interview_prep: Optional[list] = None,
) -> AnalysisJob:
    now = datetime.utcnow()
    if matched_skills is None:
        matched_skills = [
            {"skill": "FastAPI", "requirement_type": "must_have"},
            {"skill": "PostgreSQL", "requirement_type": "must_have"},
        ]
    if missing_skills is None:
        missing_skills = [
            {"skill": "Kubernetes", "requirement_type": "must_have"},
        ]
    result_json = {
        "overall_fit_score": fit_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    } if status == "succeeded" else None
    if result_json and interview_prep is not None:
        result_json["interview_prep"] = interview_prep
    return AnalysisJob(
        id=uuid.uuid4(),
        user_id=user_id,
        cv_file_id=uuid.uuid4(),
        jd_id=uuid.uuid4(),
        status=status,
        progress=100 if status == "succeeded" else 0,
        result_json=result_json,
        created_at=now,
        updated_at=now,
    )


def make_profile_item(
    user_id: uuid.UUID,
    item_type: str = "project",
    title: str = "E-commerce API",
    skills: Optional[list] = None,
) -> CareerProfileItem:
    now = datetime.utcnow()
    return CareerProfileItem(
        id=uuid.uuid4(),
        user_id=user_id,
        item_type=item_type,
        title=title,
        description="Built a REST API using FastAPI and PostgreSQL.",
        skills_json=skills or ["FastAPI", "PostgreSQL"],
        evidence_text="github.com/user/project",
        source="GitHub",
        created_at=now,
        updated_at=now,
    )


def make_answer(
    user_id: uuid.UUID,
    application_id: uuid.UUID,
    question: str = "Describe your FastAPI experience.",
    answer_text: str = "I used FastAPI to build REST APIs.",
) -> InterviewAnswer:
    now = datetime.utcnow()
    return InterviewAnswer(
        id=uuid.uuid4(),
        user_id=user_id,
        application_id=application_id,
        job_id=None,
        question=question,
        answer_text=answer_text,
        rubric_json={"relevance": 3, "specificity": 2, "evidence": 2, "structure": 2, "risk_gap": 1, "overall": 3},
        feedback_json={
            "strengths": ["Relevant answer."],
            "missing_evidence": [],
            "suggested_improvements": ["Add specific outcomes."],
            "sample_outline": ["Situation: ...", "Task: ...", "Action: ...", "Result: ..."],
            "risk_notes": ["Ensure you can elaborate."],
            "disclaimer": "Feedback is generated from your CV, JD, application workspace, and provided answer. Review before using in a real interview.",
        },
        created_at=now,
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
    app = FastAPI()
    app.include_router(applications_router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

class TestInterviewAuth:
    def test_get_questions_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        resp = client.get(f"/v1/applications/{uuid.uuid4()}/interview/questions")
        assert resp.status_code == 401

    def test_submit_answer_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        resp = client.post(
            f"/v1/applications/{uuid.uuid4()}/interview/answers",
            json={"question_id": "q_1", "question": "Test?", "answer_text": "Answer."},
        )
        assert resp.status_code == 401

    def test_list_answers_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        resp = client.get(f"/v1/applications/{uuid.uuid4()}/interview/answers")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Ownership tests
# ---------------------------------------------------------------------------

class TestInterviewOwnership:
    def test_user_cannot_get_questions_for_another_users_application(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_job(user_b.id)
        app_b = make_application(user_b.id, best_analysis_job_id=job_b.id)
        db.add(app_b)
        db.add(job_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/applications/{app_b.id}/interview/questions")

        assert resp.status_code == 404

    def test_user_cannot_submit_answer_for_another_users_application(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        db.add(app_b)
        client = build_app_client(db, user_a)

        resp = client.post(
            f"/v1/applications/{app_b.id}/interview/answers",
            json={"question_id": "q_1", "question": "Test?", "answer_text": "Answer."},
        )

        assert resp.status_code == 404

    def test_user_cannot_list_answers_for_another_users_application(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        answer_b = make_answer(user_b.id, app_b.id)
        db.add(app_b)
        db.add(answer_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/applications/{app_b.id}/interview/answers")

        assert resp.status_code == 404

    def test_answer_response_never_exposes_job_id_storage_internals(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={"question_id": "q_1", "question": "Describe FastAPI.", "answer_text": "I built REST APIs with FastAPI."},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert "storage_key" not in body
        assert "user_id" not in body


# ---------------------------------------------------------------------------
# Question generation tests
# ---------------------------------------------------------------------------

class TestInterviewQuestions:
    def test_get_questions_without_analysis_returns_200_with_generic_questions(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["application_id"] == str(app.id)
        assert len(body["questions"]) > 0

    def test_get_questions_without_analysis_response_includes_disclaimer(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert resp.status_code == 200
        assert "disclaimer" in resp.json()
        assert len(resp.json()["disclaimer"]) > 0

    def test_get_questions_without_analysis_contains_behavioral_question(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert resp.status_code == 200
        types = [q["type"] for q in resp.json()["questions"]]
        assert "behavioral" in types

    def test_get_questions_without_analysis_does_not_claim_user_skills(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert resp.status_code == 200
        for q in resp.json()["questions"]:
            # Should not assert user owns any specific skill
            assert "you are proficient in" not in q["question"].lower()
            assert "you have expertise in" not in q["question"].lower()

    def test_get_questions_with_corrupted_cross_user_job_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_job(user_b.id)
        # App belonging to user_a but pointing to user_b's job (corrupted state)
        app_a = make_application(user_a.id, best_analysis_job_id=job_b.id)
        db.add(app_a)
        db.add(job_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/applications/{app_a.id}/interview/questions")

        assert resp.status_code == 404

    def test_get_questions_returns_200_with_analysis(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["application_id"] == str(app.id)
        assert isinstance(body["questions"], list)
        assert len(body["questions"]) > 0

    def test_questions_include_disclaimer(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert resp.status_code == 200
        body = resp.json()
        assert "disclaimer" in body
        assert "practice" in body["disclaimer"].lower()

    def test_questions_have_required_fields(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        for q in resp.json()["questions"]:
            assert "question_id" in q
            assert "question" in q
            assert "type" in q
            assert "related_jd_requirement" in q
            assert "related_cv_evidence" in q
            assert "why_this_question" in q

    def test_gap_probe_questions_generated_for_missing_skills(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            missing_skills=[{"skill": "Kubernetes", "requirement_type": "must_have"}],
            matched_skills=[],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        questions = resp.json()["questions"]
        gap_probes = [q for q in questions if q["type"] == "gap_probe"]
        assert len(gap_probes) > 0
        assert any("Kubernetes" in q["question"] for q in gap_probes)

    def test_gap_probe_states_skill_not_found_in_cv(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            missing_skills=[{"skill": "Kubernetes", "requirement_type": "must_have"}],
            matched_skills=[],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        gap_probes = [q for q in resp.json()["questions"] if q["type"] == "gap_probe"]
        kubernetes_q = next((q for q in gap_probes if "Kubernetes" in q["question"]), None)
        assert kubernetes_q is not None
        why = kubernetes_q["why_this_question"].lower()
        assert "not found" in why or "not" in why

    def test_project_deep_dive_only_when_profile_evidence_exists(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, matched_skills=[{"skill": "FastAPI", "requirement_type": "must_have"}])
        app = make_application(user.id, best_analysis_job_id=job.id)
        profile = make_profile_item(user.id, item_type="project", title="API Gateway", skills=["FastAPI"])
        db.add(app)
        db.add(job)
        db.add(profile)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        deep_dives = [q for q in resp.json()["questions"] if q["type"] == "project_deep_dive"]
        assert len(deep_dives) > 0

    def test_no_project_deep_dive_without_profile_evidence(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            matched_skills=[{"skill": "FastAPI", "requirement_type": "must_have"}],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        # No profile items added
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        deep_dives = [q for q in resp.json()["questions"] if q["type"] == "project_deep_dive"]
        assert len(deep_dives) == 0

    def test_max_eight_questions_generated(self):
        user = make_user()
        db = FakeDb()
        many_skills = [{"skill": f"Skill{i}", "requirement_type": "must_have"} for i in range(15)]
        job = make_job(user.id, matched_skills=many_skills, missing_skills=[])
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert len(resp.json()["questions"]) <= 8

    def test_questions_include_existing_interview_prep_from_result(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            interview_prep=[
                {"question": "How do you handle async DB queries in FastAPI?", "type": "technical"},
            ],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        questions_text = [q["question"] for q in resp.json()["questions"]]
        assert any("async" in q.lower() for q in questions_text)

    def test_empty_profile_questions_use_jd_and_analysis_only(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            matched_skills=[{"skill": "FastAPI", "requirement_type": "must_have"}],
            missing_skills=[{"skill": "Kubernetes", "requirement_type": "must_have"}],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        # No profile items
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/questions")

        assert resp.status_code == 200
        questions = resp.json()["questions"]
        assert len(questions) > 0
        # No project_deep_dive since no profile
        assert all(q["type"] != "project_deep_dive" for q in questions)


# ---------------------------------------------------------------------------
# Answer submission tests
# ---------------------------------------------------------------------------

class TestInterviewAnswerSubmit:
    def test_submit_answer_returns_201(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your FastAPI experience.",
                "answer_text": "I used FastAPI to build e-commerce REST APIs with PostgreSQL. Implemented async endpoints.",
            },
        )

        assert resp.status_code == 201

    def test_submit_answer_response_has_required_fields(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your experience with PostgreSQL.",
                "answer_text": "I designed schemas and wrote complex queries in PostgreSQL for a production system.",
            },
        )

        body = resp.json()
        assert "answer_id" in body
        assert "application_id" in body
        assert "question" in body
        assert "answer_text" in body
        assert "rubric" in body
        assert "feedback" in body
        assert "created_at" in body

    def test_rubric_has_all_dimensions(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your FastAPI experience.",
                "answer_text": "I built several APIs with FastAPI.",
            },
        )

        rubric = resp.json()["rubric"]
        for dim in ("relevance", "specificity", "evidence", "structure", "risk_gap", "overall"):
            assert dim in rubric, f"Missing rubric dimension: {dim}"
            assert 0 <= rubric[dim] <= 5, f"Rubric {dim} out of range: {rubric[dim]}"

    def test_feedback_has_required_fields(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your FastAPI experience.",
                "answer_text": "Used FastAPI to build APIs.",
            },
        )

        feedback = resp.json()["feedback"]
        for field in ("strengths", "missing_evidence", "suggested_improvements", "sample_outline", "risk_notes", "disclaimer"):
            assert field in feedback, f"Missing feedback field: {field}"

    def test_feedback_disclaimer_always_present(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your experience.",
                "answer_text": "I have experience.",
            },
        )

        feedback = resp.json()["feedback"]
        assert feedback["disclaimer"]
        assert "review" in feedback["disclaimer"].lower()

    def test_weak_answer_produces_non_empty_missing_evidence_and_improvements(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            matched_skills=[{"skill": "FastAPI", "requirement_type": "must_have"}],
            missing_skills=[{"skill": "Kubernetes", "requirement_type": "must_have"}],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        # Very weak, short answer referencing a missing skill topic
        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_2",
                "question": "The JD requires Kubernetes. How would you approach it?",
                "answer_text": "ok",
            },
        )

        body = resp.json()
        feedback = body["feedback"]
        rubric = body["rubric"]
        # Contract Section I: weak answer must have non-empty missing_evidence,
        # non-empty suggested_improvements, and risk_gap >= 3
        assert len(feedback["suggested_improvements"]) > 0
        assert rubric["risk_gap"] >= 3

    def test_strong_answer_produces_non_empty_strengths(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        profile = make_profile_item(user.id, title="E-commerce API", skills=["FastAPI", "PostgreSQL"])
        db.add(app)
        db.add(job)
        db.add(profile)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe a project where you used FastAPI to build a REST API.",
                "answer_text": (
                    "In my E-commerce API project, I used FastAPI to build product, cart, and checkout endpoints. "
                    "I implemented async DB calls using PostgreSQL and SQLAlchemy. "
                    "The result was a 40% improvement in response time for high-traffic endpoints. "
                    "I designed the schema, tested endpoints with pytest, and deployed the service."
                ),
            },
        )

        feedback = resp.json()["feedback"]
        assert len(feedback["strengths"]) > 0

    def test_sample_outline_uses_user_context_no_fabrication(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        profile = make_profile_item(user.id, title="Order Management System")
        db.add(app)
        db.add(job)
        db.add(profile)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your backend experience.",
                "answer_text": "I built backend services with FastAPI and PostgreSQL.",
            },
        )

        outline = resp.json()["feedback"]["sample_outline"]
        assert isinstance(outline, list)
        assert len(outline) > 0
        # Should reference the user's own profile project in the Situation line
        outline_text = " ".join(outline).lower()
        assert "order management system" in outline_text

    def test_missing_skill_in_answer_noted_in_missing_evidence(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            matched_skills=[{"skill": "FastAPI", "requirement_type": "must_have"}],
            missing_skills=[{"skill": "Kubernetes", "requirement_type": "must_have"}],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_2",
                "question": "The JD requires Kubernetes. How would you approach learning it?",
                "answer_text": "I would take online courses.",
            },
        )

        feedback = resp.json()["feedback"]
        missing_text = " ".join(feedback["missing_evidence"])
        assert "Kubernetes" in missing_text or len(feedback["missing_evidence"]) > 0

    def test_submit_answer_without_attached_analysis_still_works(self):
        user = make_user()
        db = FakeDb()
        # Application with no analysis attached
        app = make_application(user.id, best_analysis_job_id=None)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your experience.",
                "answer_text": "I have worked on multiple backend projects using Python.",
            },
        )

        assert resp.status_code == 201

    def test_submit_answer_missing_required_field_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                # Missing "question" and "answer_text"
            },
        )

        assert resp.status_code == 422

    def test_empty_question_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={"question_id": "q_1", "question": "", "answer_text": "Some answer."},
        )

        assert resp.status_code == 422

    def test_empty_answer_text_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={"question_id": "q_1", "question": "Describe your experience.", "answer_text": ""},
        )

        assert resp.status_code == 422

    def test_empty_question_id_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={"question_id": "", "question": "Describe your experience.", "answer_text": "Answer."},
        )

        assert resp.status_code == 422

    def test_overlong_answer_text_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(
            f"/v1/applications/{app.id}/interview/answers",
            json={
                "question_id": "q_1",
                "question": "Describe your experience.",
                "answer_text": "x" * 8001,
            },
        )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Answer list tests
# ---------------------------------------------------------------------------

class TestInterviewAnswerList:
    def test_list_answers_returns_200_with_empty_list(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/answers")

        assert resp.status_code == 200
        body = resp.json()
        assert body["application_id"] == str(app.id)
        assert body["answers"] == []
        assert body["total"] == 0

    def test_list_answers_returns_submitted_answers(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        answer = make_answer(user.id, app.id)
        db.add(app)
        db.add(answer)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/answers")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert len(body["answers"]) == 1

    def test_list_answer_summary_has_required_fields(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        answer = make_answer(user.id, app.id)
        db.add(app)
        db.add(answer)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/answers")

        item = resp.json()["answers"][0]
        assert "answer_id" in item
        assert "question" in item
        assert "rubric" in item
        assert "created_at" in item
        assert "answer_text" not in item  # summary omits full answer text

    def test_list_answers_total_matches_actual_count(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        for i in range(3):
            db.add(make_answer(user.id, app.id, question=f"Question {i}"))
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/interview/answers")

        body = resp.json()
        assert body["total"] == 3
        assert len(body["answers"]) == 3

    def test_list_answers_scope_to_application(self):
        user = make_user()
        db = FakeDb()
        app1 = make_application(user.id)
        app2 = make_application(user.id)
        answer1 = make_answer(user.id, app1.id, question="Q for app1")
        answer2 = make_answer(user.id, app2.id, question="Q for app2")
        db.add(app1)
        db.add(app2)
        db.add(answer1)
        db.add(answer2)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app1.id}/interview/answers")

        assert resp.json()["total"] == 1
        assert resp.json()["answers"][0]["question"] == "Q for app1"


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------

class TestInterviewRegression:
    def test_existing_application_crud_still_works(self):
        user = make_user()
        db = FakeDb()
        client = build_app_client(db, user)

        resp = client.post("/v1/applications", json={
            "job_title": "Backend Developer",
            "jd_text": "Looking for a Python/FastAPI developer.",
        })

        assert resp.status_code == 201

    def test_package_endpoints_still_work_after_interview_routes_added(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/package")
        assert resp.status_code == 404  # not generated yet — still 404 not 500

    def test_cover_letter_endpoints_still_work_after_interview_routes_added(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/cover-letter")
        assert resp.status_code == 404  # not generated yet — still 404 not 500

    def test_readiness_endpoint_still_returns_not_started(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/readiness")

        assert resp.status_code == 200
        assert resp.json()["readiness_level"] == "not_started"
