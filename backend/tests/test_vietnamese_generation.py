"""Vietnamese-first generated-content tests.

These document and enforce the contract: when ``language="vi"`` the backend
produces Vietnamese app-generated prose for the demo-flow generators, while the
default (no language / "en") keeps the existing English output unchanged. User
content and proper nouns (job titles, company names, skill/tech names) are never
translated.
"""

from __future__ import annotations

import types
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.interview_sessions import router as interview_router
from app.db.models import InterviewSession, InterviewSessionQuestion, User
from app.db.session import get_db
from app.services.application_package import build_package_payload
from app.services.cover_letter import build_cover_letter_payload
from app.services.help import HelpContext, build_assistant_response, build_suggestions
from app.services.i18n import resolve_language
from app.services.interview.sessions_v2 import (
    generate_questions,
    score_answer_v2,
    summarize_answers,
)


def _app(job_title="Backend Engineer", company="Acme Corp"):
    return types.SimpleNamespace(company_name=company, job_title=job_title)


def _job(result: dict):
    return types.SimpleNamespace(result_json=result, id=uuid.uuid4())


_RESULT = {
    "overall_fit_score": 80.0,
    "matched_skills": [{"skill": "Python"}, {"skill": "SQL"}],
    "missing_skills": [{"skill": "Kubernetes"}],
}


def _has_vietnamese(text: str) -> bool:
    """True if the string contains Vietnamese-specific diacritics."""
    return any(ch in text for ch in "ăâđêôơưàảãạáằẳẵặắéèẻẽẹếýỳỵọóợ")


class TestI18nResolver:
    def test_resolves_vietnamese_aliases(self):
        for v in ("vi", "VI", " vi ", "vi-VN", "vietnamese"):
            assert resolve_language(v) == "vi"

    def test_defaults_to_english(self):
        for v in (None, "", "en", "fr", "english"):
            assert resolve_language(v) == "en"


class TestCoverLetterLanguage:
    def test_vietnamese_prose_with_preserved_proper_nouns(self):
        payload = build_cover_letter_payload(_app(), _job(_RESULT), [], language="vi")
        assert _has_vietnamese(payload["opening"])
        assert "Tôi viết thư này" in payload["opening"]
        # Proper nouns are never translated.
        assert "Acme Corp" in payload["opening"]
        assert "Backend Engineer" in payload["opening"]
        assert "Python" in payload["why_role_company"]
        assert "không đảm bảo" in payload["disclaimer"]

    def test_english_is_unchanged_by_default(self):
        payload = build_cover_letter_payload(_app(), _job(_RESULT), [])
        assert payload["opening"].startswith("I am writing to express")
        assert "guarantee" in payload["disclaimer"].lower()
        assert not _has_vietnamese(payload["opening"])


class TestPackageLanguage:
    def test_vietnamese_summary_actions_disclaimer(self):
        payload = build_package_payload(_app(), _job(_RESULT), [], language="vi")
        rs = payload["readiness_summary"]
        assert _has_vietnamese(rs["summary"])
        assert rs["next_actions"] and all(_has_vietnamese(a) for a in rs["next_actions"])
        assert "Không đưa vào" in payload["disclaimer"]
        # Skill names preserved.
        assert "Python" in payload["best_cv_analysis"]["matched_skills"]

    def test_english_default_unchanged(self):
        payload = build_package_payload(_app(), _job(_RESULT), [])
        assert payload["readiness_summary"]["summary"].startswith("Application readiness")
        assert "Do not include skills" in payload["disclaimer"]


class TestInterviewLanguage:
    def test_vietnamese_fallback_questions_and_rubric(self):
        questions, limitations = generate_questions(None, count=3, language="vi")
        assert questions
        assert "Hãy giới thiệu về bản thân" in questions[0]["question_text"]
        assert _has_vietnamese(questions[0]["rubric_json"]["relevance"])
        assert _has_vietnamese(limitations)

    def test_vietnamese_questions_keep_skill_names(self):
        questions, _ = generate_questions(_job(_RESULT), count=4, language="vi")
        text = " ".join(q["question_text"] for q in questions)
        assert _has_vietnamese(text)
        # Evidence-derived questions wrap the untranslated skill/requirement.
        assert "Python" in text or "Kubernetes" in text or "SQL" in text

    def test_english_fallback_unchanged(self):
        questions, limitations = generate_questions(None, count=3)
        assert questions[0]["question_text"].startswith("Tell me about yourself")
        assert not _has_vietnamese(limitations)

    def test_vietnamese_feedback_prose(self):
        score, feedback = score_answer_v2("Câu hỏi phỏng vấn?", "Tôi đã làm việc này.", None, language="vi")
        for dim in ("relevance", "evidence", "clarity", "structure", "confidence", "risk"):
            assert dim in score
        assert feedback["disclaimer"].startswith("Đây là phản hồi luyện tập")
        assert feedback["improvements"] and all(_has_vietnamese(s) for s in feedback["improvements"])

    def test_vietnamese_risk_flag_for_gap_skill(self):
        score, feedback = score_answer_v2(
            "Kinh nghiệm Kubernetes?",
            "Tôi là chuyên gia Kubernetes và đã triển khai nhiều cụm.",
            _job(_RESULT),
            language="vi",
        )
        assert feedback["risk_flags"]
        assert any("khoảng trống" in f for f in feedback["risk_flags"])

    def test_english_feedback_unchanged(self):
        _, feedback = score_answer_v2("Tell me about a project", "I built a Python service.", None)
        assert "guarantee" in feedback["disclaimer"].lower()
        assert not any(_has_vietnamese(s) for s in feedback["improvements"])

    def test_summary_risk_flags_localized(self):
        scores = [{"relevance": 1, "evidence": 1, "clarity": 1, "structure": 1, "confidence": 1, "risk": 3, "overall": 1.0}]
        agg = summarize_answers(scores, language="vi")
        assert agg["risk_flags"] and all(_has_vietnamese(f) for f in agg["risk_flags"])
        agg_en = summarize_answers(scores)
        assert agg_en["risk_flags"] and not any(_has_vietnamese(f) for f in agg_en["risk_flags"])


class TestHelpAssistantLanguage:
    def test_vietnamese_answer_and_limitations(self):
        result = build_assistant_response("help_product_usage", HelpContext(), language="vi")
        assert _has_vietnamese(result["answer"])
        assert "Quy trình" in result["answer"]
        assert _has_vietnamese(result["limitations"])

    def test_english_default_unchanged(self):
        result = build_assistant_response("help_product_usage", HelpContext())
        assert result["answer"].startswith("Workflow")
        assert not _has_vietnamese(result["limitations"])

    def test_suggestions_labels_localized(self):
        items = build_suggestions(HelpContext(), language="vi")
        assert items and all(_has_vietnamese(i["label"]) for i in items)
        # Machine-readable intents/actions are not translated.
        assert {i["intent"] for i in items}
        assert all(isinstance(i["recommended_actions"], list) for i in items)


# ---------------------------------------------------------------------------
# Route-level: proves the language param threads request → service.
# ---------------------------------------------------------------------------

class _FakeQuery:
    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *args):
        rows = list(self._rows)
        for expr in args:
            try:
                key, val = expr.left.key, expr.right.value
                rows = [r for r in rows if getattr(r, key, None) == val]
            except AttributeError:
                pass
        return _FakeQuery(rows)

    def order_by(self, *args):
        return self

    def all(self):
        return list(self._rows)


class _FakeDb:
    def __init__(self):
        self._store: dict[tuple, Any] = {}
        self._rows: dict[type, list] = {}

    def add(self, obj):
        self._store[(type(obj).__tablename__, obj.id)] = obj
        self._rows.setdefault(type(obj), []).append(obj)

    def get(self, model, pk):
        return self._store.get((model.__tablename__, pk))

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        return _FakeQuery(self._rows.get(model, []))


def test_route_generate_questions_in_vietnamese():
    user = User(id=uuid.uuid4(), email="u@example.com", is_active=True)
    db = _FakeDb()
    now = datetime.utcnow()
    session = InterviewSession(
        id=uuid.uuid4(), user_id=user.id, session_type="mixed", difficulty="medium",
        status="active", created_at=now, updated_at=now,
    )
    db.add(session)

    app = FastAPI()
    app.include_router(interview_router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)

    resp = client.post(
        f"/v1/interview/sessions/{session.id}/questions/generate",
        json={"count": 3, "language": "vi"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["questions"]
    joined = " ".join(q["question_text"] for q in body["questions"])
    assert any(ch in joined for ch in "ăâđêôơưàảãạáệỏ")
