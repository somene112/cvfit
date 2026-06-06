from __future__ import annotations

from typing import Any


def build_interview_prep(result: dict, *, max_questions: int = 6) -> list[dict]:
    questions: list[dict] = []

    for item in _matched_skills(result):
        if len(questions) >= max_questions:
            break
        skill = _safe_label(item.get("skill") or "this skill")
        cv_ids = _ids(item.get("cv_evidence_ids"))
        questions.append(
            {
                "question": (
                    f"Can you walk through a real project or task where you used {skill}, including your role, "
                    "the implementation choices, and the outcome?"
                ),
                "type": "project_deep_dive",
                "why_this_question": (
                    f"The JD appears to value {skill}, and the parsed CV contains related evidence."
                ),
                "related_jd_requirement": _safe_label(item.get("jd_requirement") or skill),
                "related_cv_evidence": cv_ids,
                "suggested_answer_outline": [
                    "State the real project or task context.",
                    "Explain your specific responsibility.",
                    "Describe the actual tools and implementation choices.",
                    "Share a real outcome or lesson learned if you can verify it.",
                ],
                "risk_if_user_cannot_answer": (
                    f"If you cannot explain the {skill} evidence, the match may appear shallow in interview."
                ),
            }
        )

    for item in _missing_skills(result):
        if len(questions) >= max_questions:
            break
        skill = _safe_label(item.get("skill") or "this skill")
        questions.append(
            {
                "question": f"The JD mentions {skill}. What is your current level with it, and how would you close the gap?",
                "type": "gap_probe",
                "why_this_question": (
                    f"{skill} evidence was not found in the parsed CV, so an interviewer may probe this gap."
                ),
                "related_jd_requirement": _safe_label(item.get("jd_requirement") or skill),
                "related_cv_evidence": [],
                "suggested_answer_outline": [
                    "Be honest about whether you have used the skill.",
                    "If you have used it, describe only the real context.",
                    "If you have not used it, explain the learning plan or related foundation.",
                    "Avoid claiming experience you cannot support.",
                ],
                "risk_if_user_cannot_answer": (
                    "If this is a must-have requirement, weak preparation may reduce interview readiness."
                ),
            }
        )

    return questions[:max_questions]


def _matched_skills(result: dict) -> list[dict]:
    matched = result.get("matched_skills")
    if isinstance(matched, list):
        return [item for item in matched if isinstance(item, dict)]
    return []


def _missing_skills(result: dict) -> list[dict]:
    missing = result.get("missing_skills")
    if isinstance(missing, list):
        return [item for item in missing if isinstance(item, dict)]
    return []


def _ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _safe_label(value: Any) -> str:
    text = str(value or "").strip()
    return text[:220] if text else "this requirement"
