"""Deterministic Interview Practice v2 generation and scoring.

Pure functions only — no DB, no LLM, no network. Produces the six-dimension
rubric (relevance, evidence, clarity, structure, confidence, risk) and honest,
guardrail-aware feedback. Never claims a guaranteed interview/hiring outcome and
never sends raw answer text anywhere outside the returned product payload.

Localized: when ``language="vi"`` the generated question prose, rubric labels,
and feedback are Vietnamese. Skill/tech names and the user's own answer text are
never translated. The numeric scoring heuristics are language-agnostic keyword
signals tuned for English; Vietnamese answers are scored on the same structural
signals, with the *feedback prose* localized.
"""

from __future__ import annotations

from typing import Any, Optional

from app.services.i18n import resolve_language
from app.services.interview.interview_prep import build_interview_prep


RUBRIC_DIMENSIONS = ("relevance", "evidence", "clarity", "structure", "confidence", "risk")

# Risk is inverse: higher = more interview risk (worse). The other five are
# positive (higher = better).
RUBRIC_TEMPLATE = {
    "relevance": "Does the answer address the question? (0-5, higher better)",
    "evidence": "Is the answer grounded in real CV/profile evidence? (0-5, higher better)",
    "clarity": "Is the answer clear and easy to follow? (0-5, higher better)",
    "structure": "Does the answer follow a logical/STAR structure? (0-5, higher better)",
    "confidence": "Is the answer specific and assured without vagueness? (0-5, higher better)",
    "risk": "Interview risk from gaps or unsupported claims (0-5, lower better)",
}
RUBRIC_TEMPLATE_VI = {
    "relevance": "Câu trả lời có giải quyết đúng câu hỏi không? (0-5, cao hơn là tốt hơn)",
    "evidence": "Câu trả lời có dựa trên bằng chứng thực tế từ CV/hồ sơ không? (0-5, cao hơn là tốt hơn)",
    "clarity": "Câu trả lời có rõ ràng, dễ hiểu không? (0-5, cao hơn là tốt hơn)",
    "structure": "Câu trả lời có cấu trúc logic/STAR không? (0-5, cao hơn là tốt hơn)",
    "confidence": "Câu trả lời có cụ thể và chắc chắn, không mơ hồ không? (0-5, cao hơn là tốt hơn)",
    "risk": "Rủi ro phỏng vấn từ khoảng trống hoặc tuyên bố thiếu căn cứ (0-5, thấp hơn là tốt hơn)",
}

QUESTIONS_DISCLAIMER = (
    "Questions are generated from your analysis result and profile evidence. "
    "They are practice aids only — real interviewers may ask different questions."
)
LIMITATION_LIMITED = (
    "Generated from the attached analysis only. Based on current analysis only."
)
LIMITATION_FALLBACK = (
    "No completed analysis was available, so generic career questions were used. "
    "Attach a completed analysis for evidence-specific questions. "
    "Based on current analysis only."
)
LIMITATION_LIMITED_VI = (
    "Được tạo chỉ từ phân tích đã đính kèm. Dựa trên phân tích hiện tại."
)
LIMITATION_FALLBACK_VI = (
    "Không có phân tích hoàn chỉnh nào khả dụng, nên các câu hỏi nghề nghiệp tổng quát đã được sử dụng. "
    "Hãy đính kèm một phân tích hoàn chỉnh để có câu hỏi theo bằng chứng cụ thể. "
    "Dựa trên phân tích hiện tại."
)

# Map the Phase 5 prep "type" to a Phase 6 question_type.
_TYPE_MAP = {
    "project_deep_dive": "project",
    "gap_probe": "gap_check",
    "technical": "technical",
    "behavioral": "behavioral",
}

_FALLBACK_QUESTIONS = [
    ("behavioral", "Tell me about yourself and why you are interested in this role."),
    ("behavioral", "Describe a challenging project you worked on. What was your role and what did you learn?"),
    ("HR", "What are your key strengths, and how do they fit this position?"),
    ("project", "Walk me through a project you are proud of, including the tools you used and the outcome."),
    ("gap_check", "Which skill from the job description would you most need to develop, and how would you approach it?"),
]
_FALLBACK_QUESTIONS_VI = [
    ("behavioral", "Hãy giới thiệu về bản thân và lý do bạn quan tâm đến vị trí này."),
    ("behavioral", "Mô tả một dự án thử thách mà bạn đã thực hiện. Vai trò của bạn là gì và bạn học được điều gì?"),
    ("HR", "Điểm mạnh chính của bạn là gì, và chúng phù hợp với vị trí này như thế nào?"),
    ("project", "Hãy trình bày một dự án bạn tự hào, bao gồm các công cụ bạn đã dùng và kết quả đạt được."),
    ("gap_check", "Kỹ năng nào trong mô tả công việc mà bạn cần phát triển nhất, và bạn sẽ tiếp cận nó ra sao?"),
]


def _result_of(job: Any) -> dict:
    result = getattr(job, "result_json", None) if job is not None else None
    return result if isinstance(result, dict) else {}


def _vi_question_from_prep(prep: dict) -> str:
    """Build a Vietnamese question around the (untranslated) skill/requirement."""
    skill = str(prep.get("related_jd_requirement") or "kỹ năng này").strip() or "kỹ năng này"
    prep_type = str(prep.get("type") or "")
    if prep_type == "gap_probe":
        return (
            f"Mô tả công việc có đề cập đến {skill}. Mức độ hiện tại của bạn với kỹ năng này ra sao, "
            "và bạn sẽ làm gì để thu hẹp khoảng cách?"
        )
    if prep_type == "project_deep_dive":
        return (
            f"Bạn có thể trình bày một dự án hoặc nhiệm vụ thực tế mà bạn đã sử dụng {skill}, "
            "bao gồm vai trò, các lựa chọn triển khai và kết quả không?"
        )
    return (
        f"Hãy chia sẻ một ví dụ thực tế liên quan đến {skill}, "
        "mô tả bối cảnh, hành động của bạn và kết quả đạt được."
    )


def generate_questions(
    job: Optional[Any],
    *,
    requested_type: Optional[str] = None,
    difficulty: str = "medium",
    count: int = 5,
    language: str = "en",
) -> tuple[list[dict], str]:
    """Return ``(question_dicts, limitations)``.

    Each dict: question_type, difficulty, question_text, related_evidence_json,
    rubric_json. Honors an optional ``requested_type`` filter and falls back to
    generic questions when analysis context is missing. When ``language="vi"``
    the question prose, rubric labels, and limitations are Vietnamese.
    """
    lang = resolve_language(language)
    rubric = RUBRIC_TEMPLATE_VI if lang == "vi" else RUBRIC_TEMPLATE
    fallback_questions = _FALLBACK_QUESTIONS_VI if lang == "vi" else _FALLBACK_QUESTIONS

    result = _result_of(job)
    questions: list[dict] = []

    if result:
        for prep in build_interview_prep(result, max_questions=count * 2):
            qtype = _TYPE_MAP.get(str(prep.get("type")), "behavioral")
            if requested_type and qtype != requested_type:
                continue
            question_text = (
                _vi_question_from_prep(prep)
                if lang == "vi"
                else str(prep.get("question") or "").strip()
            )
            questions.append(
                {
                    "question_type": qtype,
                    "difficulty": difficulty,
                    "question_text": question_text,
                    "related_evidence_json": {
                        "related_jd_requirement": prep.get("related_jd_requirement"),
                        "related_cv_evidence": prep.get("related_cv_evidence", []),
                    },
                    "rubric_json": dict(rubric),
                }
            )
            if len(questions) >= count:
                break

    if lang == "vi":
        limitations = LIMITATION_LIMITED_VI if questions else LIMITATION_FALLBACK_VI
    else:
        limitations = LIMITATION_LIMITED if questions else LIMITATION_FALLBACK

    if not questions:
        for qtype, text in fallback_questions:
            if requested_type and qtype != requested_type:
                continue
            questions.append(
                {
                    "question_type": qtype,
                    "difficulty": difficulty,
                    "question_text": text,
                    "related_evidence_json": None,
                    "rubric_json": dict(rubric),
                }
            )
            if len(questions) >= count:
                break

    # If a requested_type filtered everything out, still return at least one
    # generic question of that type so the session is usable.
    if not questions and requested_type:
        if lang == "vi":
            generic = (
                f"Hãy chia sẻ một ví dụ thuộc loại '{requested_type}' từ kinh nghiệm thực tế "
                "của bạn liên quan đến vị trí này."
            )
        else:
            generic = (
                f"Share a {requested_type} example from your real experience relevant to this role."
            )
        questions.append(
            {
                "question_type": requested_type,
                "difficulty": difficulty,
                "question_text": generic,
                "related_evidence_json": None,
                "rubric_json": dict(rubric),
            }
        )

    return questions[:count], limitations


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

_VAGUE_PHRASES = ("i don't know", "not sure", "no idea", "maybe", "i guess", "kind of", "sort of")
_OUTCOME_WORDS = ("result", "outcome", "improved", "reduced", "increased", "delivered", "achieved", "shipped", "built", "led")
_STRUCTURE_WORDS = ("first", "then", "next", "finally", "because", "therefore", "situation", "task", "action", "result")
_OVERCLAIM_WORDS = ("expert", "mastered", "fluent", "years of experience", "extensive experience")


def _skill_names(result: dict, key: str) -> list[str]:
    raw = result.get(key)
    out: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                name = item.get("skill") or item.get("name")
                if name:
                    out.append(str(name).lower())
            elif isinstance(item, str):
                out.append(item.lower())
    return out


def score_answer_v2(
    question_text: str,
    answer_text: str,
    job: Optional[Any],
    *,
    language: str = "en",
) -> tuple[dict, dict]:
    """Return ``(score_json, feedback_json)`` using the six-dimension rubric.

    When ``language="vi"`` the feedback prose is Vietnamese. The numeric scoring
    is unchanged (language-agnostic structural signals).
    """
    lang = resolve_language(language)
    result = _result_of(job)
    matched = _skill_names(result, "matched_skills")
    missing = _skill_names(result, "missing_skills")

    text = answer_text.strip()
    lower = text.lower()
    words = text.split()
    n_words = len(words)

    # relevance: keyword overlap with the question + non-trivial length
    q_keywords = [w.strip("?.,'\"").lower() for w in question_text.split() if len(w) > 4]
    hits = sum(1 for kw in set(q_keywords) if kw in lower)
    relevance = min(5, hits + (1 if n_words >= 12 else 0))

    # evidence: references matched skills / concrete nouns
    ev_hits = sum(1 for s in matched if s in lower)
    evidence = min(5, ev_hits + (1 if any(w in lower for w in _OUTCOME_WORDS) else 0))

    # clarity: sentence count + not too short, penalize vagueness
    sentences = [s for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    clarity = 0
    if n_words >= 8:
        clarity += 2
    if len(sentences) >= 2:
        clarity += 1
    if n_words >= 30:
        clarity += 1
    if not any(v in lower for v in _VAGUE_PHRASES):
        clarity += 1
    clarity = min(5, clarity)

    # structure: STAR/connective markers
    structure = min(5, sum(1 for w in _STRUCTURE_WORDS if w in lower))

    # confidence: specificity (numbers, outcomes) minus vagueness
    confidence = 0
    if any(c.isdigit() for c in text):
        confidence += 1
    if any(w in lower for w in _OUTCOME_WORDS):
        confidence += 2
    if n_words >= 25:
        confidence += 1
    if any(v in lower for v in _VAGUE_PHRASES):
        confidence -= 1
    confidence = max(0, min(5, confidence + 1))

    # risk (inverse): gaps, overclaiming, vagueness, very short answers
    risk = 0
    risk_flags: list[str] = []
    for s in missing:
        if s in lower:
            risk += 2
            risk_flags.append(
                f"Câu trả lời có nhắc đến '{s}', vốn được phân tích đánh dấu là khoảng trống — "
                "hãy chuẩn bị chứng minh điều này một cách trung thực."
                if lang == "vi"
                else f"Answer references '{s}', which the analysis flagged as a gap — be ready to back this up honestly."
            )
            break
    if any(oc in lower for oc in _OVERCLAIM_WORDS):
        risk += 1
        risk_flags.append(
            "Câu trả lời dùng ngôn từ khẳng định mạnh; hãy đảm bảo mọi tuyên bố đều có bằng chứng thực tế."
            if lang == "vi"
            else "Answer uses strong claim language; ensure every claim is supported by real evidence."
        )
    if any(v in lower for v in _VAGUE_PHRASES):
        risk += 1
    if n_words < 8:
        risk += 1
        risk_flags.append(
            "Câu trả lời quá ngắn; hãy bổ sung một ví dụ cụ thể."
            if lang == "vi"
            else "Answer is very short; add a concrete example."
        )
    risk = min(5, risk)

    score_json = {
        "relevance": relevance,
        "evidence": evidence,
        "clarity": clarity,
        "structure": structure,
        "confidence": confidence,
        "risk": risk,
    }

    positives = [relevance, evidence, clarity, structure, confidence]
    overall = round(sum(positives) / len(positives), 2)
    score_json["overall"] = overall

    strengths: list[str] = []
    improvements: list[str] = []
    if lang == "vi":
        if relevance >= 3:
            strengths.append("Trả lời trực tiếp vào câu hỏi.")
        if evidence >= 3:
            strengths.append("Có bằng chứng/kết quả cụ thể.")
        if structure >= 2:
            strengths.append("Thể hiện cấu trúc logic.")
        if not strengths:
            strengths.append("Đã có câu trả lời khởi đầu — hãy phát triển thêm với các chi tiết cụ thể.")

        if evidence < 3:
            improvements.append("Gắn câu trả lời với một dự án thực tế cụ thể hoặc kết quả đo lường được.")
        if structure < 2:
            improvements.append("Sử dụng cấu trúc STAR: Tình huống, Nhiệm vụ, Hành động, Kết quả.")
        if confidence < 3:
            improvements.append("Thêm chi tiết cụ thể (con số, công cụ, phạm vi) và tránh diễn đạt mơ hồ.")
        if not improvements:
            improvements.append("Tinh chỉnh câu trả lời và luyện tập để giữ được sự cụ thể khi áp lực.")

        disclaimer = (
            "Đây là phản hồi luyện tập dựa trên câu trả lời và bằng chứng hiện có của bạn. "
            "Nó không đảm bảo kết quả phỏng vấn hay tuyển dụng."
        )
    else:
        if relevance >= 3:
            strengths.append("Directly addresses the question.")
        if evidence >= 3:
            strengths.append("Grounded in concrete evidence/outcomes.")
        if structure >= 2:
            strengths.append("Shows a logical structure.")
        if not strengths:
            strengths.append("A starting answer is in place — build on it with specifics.")

        if evidence < 3:
            improvements.append("Anchor the answer in a specific real project or measurable outcome.")
        if structure < 2:
            improvements.append("Use a STAR structure: Situation, Task, Action, Result.")
        if confidence < 3:
            improvements.append("Add concrete details (numbers, tools, scope) and avoid vague phrasing.")
        if not improvements:
            improvements.append("Tighten the answer and rehearse it so it stays specific under pressure.")

        disclaimer = (
            "This is practice feedback based on your answer and available evidence. "
            "It does not guarantee interview or hiring outcomes."
        )

    feedback_json = {
        "strengths": strengths,
        "improvements": improvements,
        "risk_flags": risk_flags,
        "disclaimer": disclaimer,
    }
    return score_json, feedback_json


def summarize_answers(scores: list[dict], *, language: str = "en") -> dict:
    """Aggregate a list of ``score_json`` dicts into summary metrics."""
    lang = resolve_language(language)
    positive_dims = ("relevance", "evidence", "clarity", "structure", "confidence")
    if not scores:
        return {
            "average_score": None,
            "best_dimension": None,
            "weakest_dimension": None,
            "risk_flags": [],
        }

    overalls = [s.get("overall", 0) for s in scores]
    average_score = round(sum(overalls) / len(overalls), 2)

    dim_avgs = {
        dim: round(sum(s.get(dim, 0) for s in scores) / len(scores), 2)
        for dim in positive_dims
    }
    best_dimension = max(dim_avgs, key=dim_avgs.get)
    weakest_dimension = min(dim_avgs, key=dim_avgs.get)

    avg_risk = sum(s.get("risk", 0) for s in scores) / len(scores)
    risk_flags: list[str] = []
    if lang == "vi":
        if avg_risk >= 2:
            risk_flags.append("Một số câu trả lời tiềm ẩn rủi ro phỏng vấn từ khoảng trống hoặc tuyên bố thiếu căn cứ.")
        if dim_avgs["evidence"] < 2:
            risk_flags.append("Các câu trả lời còn ít bằng chứng cụ thể; hãy bổ sung ví dụ thực tế.")
    else:
        if avg_risk >= 2:
            risk_flags.append("Several answers carry interview risk from gaps or unsupported claims.")
        if dim_avgs["evidence"] < 2:
            risk_flags.append("Answers are light on concrete evidence; add real examples.")

    return {
        "average_score": average_score,
        "best_dimension": best_dimension,
        "weakest_dimension": weakest_dimension,
        "risk_flags": risk_flags,
    }
