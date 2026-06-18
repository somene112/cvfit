"""Deterministic Interview Practice v2 generation and scoring.

Pure functions only — no DB, no LLM, no network. Produces the six-dimension
rubric (relevance, evidence, clarity, structure, confidence, risk) and honest,
guardrail-aware feedback. Never claims a guaranteed interview/hiring outcome and
never sends raw answer text anywhere outside the returned product payload.
"""

from __future__ import annotations

from typing import Any, Optional

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


def _result_of(job: Any) -> dict:
    result = getattr(job, "result_json", None) if job is not None else None
    return result if isinstance(result, dict) else {}


def generate_questions(
    job: Optional[Any],
    *,
    requested_type: Optional[str] = None,
    difficulty: str = "medium",
    count: int = 5,
) -> tuple[list[dict], str]:
    """Return ``(question_dicts, limitations)``.

    Each dict: question_type, difficulty, question_text, related_evidence_json,
    rubric_json. Honors an optional ``requested_type`` filter and falls back to
    generic questions when analysis context is missing.
    """
    result = _result_of(job)
    questions: list[dict] = []

    if result:
        for prep in build_interview_prep(result, max_questions=count * 2):
            qtype = _TYPE_MAP.get(str(prep.get("type")), "behavioral")
            if requested_type and qtype != requested_type:
                continue
            questions.append(
                {
                    "question_type": qtype,
                    "difficulty": difficulty,
                    "question_text": str(prep.get("question") or "").strip(),
                    "related_evidence_json": {
                        "related_jd_requirement": prep.get("related_jd_requirement"),
                        "related_cv_evidence": prep.get("related_cv_evidence", []),
                    },
                    "rubric_json": dict(RUBRIC_TEMPLATE),
                }
            )
            if len(questions) >= count:
                break

    limitations = LIMITATION_LIMITED if questions else LIMITATION_FALLBACK

    if not questions:
        for qtype, text in _FALLBACK_QUESTIONS:
            if requested_type and qtype != requested_type:
                continue
            questions.append(
                {
                    "question_type": qtype,
                    "difficulty": difficulty,
                    "question_text": text,
                    "related_evidence_json": None,
                    "rubric_json": dict(RUBRIC_TEMPLATE),
                }
            )
            if len(questions) >= count:
                break

    # If a requested_type filtered everything out, still return at least one
    # generic question of that type so the session is usable.
    if not questions and requested_type:
        questions.append(
            {
                "question_type": requested_type,
                "difficulty": difficulty,
                "question_text": (
                    f"Share a {requested_type} example from your real experience relevant to this role."
                ),
                "related_evidence_json": None,
                "rubric_json": dict(RUBRIC_TEMPLATE),
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


def score_answer_v2(question_text: str, answer_text: str, job: Optional[Any]) -> tuple[dict, dict]:
    """Return ``(score_json, feedback_json)`` using the six-dimension rubric."""
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
                f"Answer references '{s}', which the analysis flagged as a gap — be ready to back this up honestly."
            )
            break
    if any(oc in lower for oc in _OVERCLAIM_WORDS):
        risk += 1
        risk_flags.append("Answer uses strong claim language; ensure every claim is supported by real evidence.")
    if any(v in lower for v in _VAGUE_PHRASES):
        risk += 1
    if n_words < 8:
        risk += 1
        risk_flags.append("Answer is very short; add a concrete example.")
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
    if relevance >= 3:
        strengths.append("Directly addresses the question.")
    if evidence >= 3:
        strengths.append("Grounded in concrete evidence/outcomes.")
    if structure >= 2:
        strengths.append("Shows a logical structure.")
    if not strengths:
        strengths.append("A starting answer is in place — build on it with specifics.")

    improvements: list[str] = []
    if evidence < 3:
        improvements.append("Anchor the answer in a specific real project or measurable outcome.")
    if structure < 2:
        improvements.append("Use a STAR structure: Situation, Task, Action, Result.")
    if confidence < 3:
        improvements.append("Add concrete details (numbers, tools, scope) and avoid vague phrasing.")
    if not improvements:
        improvements.append("Tighten the answer and rehearse it so it stays specific under pressure.")

    feedback_json = {
        "strengths": strengths,
        "improvements": improvements,
        "risk_flags": risk_flags,
        "disclaimer": (
            "This is practice feedback based on your answer and available evidence. "
            "It does not guarantee interview or hiring outcomes."
        ),
    }
    return score_json, feedback_json


def summarize_answers(scores: list[dict]) -> dict:
    """Aggregate a list of ``score_json`` dicts into summary metrics."""
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
