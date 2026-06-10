"""Deterministic application package builder — no LLM, evidence-only."""

from __future__ import annotations

from typing import Any, Optional


PACKAGE_DISCLAIMER = (
    "This package is generated from your uploaded CV, JD and extracted evidence. "
    "Do not include skills or experience that are not true."
)


def build_package_payload(
    application: Any,
    job: Optional[Any],
    profile_items: list,
) -> dict:
    result: dict = job.result_json if (job and job.result_json) else {}

    fit_score = _extract_fit_score(result)
    readiness_level = _compute_readiness_level(fit_score)
    next_actions = _compute_next_actions(readiness_level)
    matched_skills = _extract_skill_list(result.get("matched_skills"))
    missing_skills = _extract_skill_list(result.get("missing_skills"))

    return {
        "readiness_summary": {
            "readiness_level": readiness_level,
            "fit_score": fit_score,
            "summary": "Application readiness is based on the attached analysis result.",
            "next_actions": next_actions,
        },
        "best_cv_analysis": {
            "job_id": str(job.id) if job else None,
            "fit_score": fit_score,
            "matched_skills": matched_skills[:10],
            "missing_skills": missing_skills[:10],
            "strengths": _extract_strengths(result),
            "improvement_actions": _extract_improvement_actions(result),
        },
        "cover_letter_draft": None,
        "interview_prep_pack": {
            "questions": _extract_interview_questions(result),
        },
        "learning_roadmap": _safe_list(result.get("learning_roadmap"))[:8],
        "evidence_checklist": _build_evidence_checklist(profile_items, matched_skills),
        "disclaimer": PACKAGE_DISCLAIMER,
    }


def _extract_fit_score(result: dict) -> Optional[float]:
    for candidate in (
        result.get("overall_fit_score"),
        (result.get("scores") or {}).get("fit_score"),
        result.get("fit_score"),
        (result.get("overall") or {}).get("fit_score"),
    ):
        if candidate is not None:
            try:
                return float(candidate)
            except (TypeError, ValueError):
                pass
    return None


def _compute_readiness_level(fit_score: Optional[float]) -> str:
    if fit_score is None:
        return "not_started"
    if fit_score >= 75:
        return "ready"
    if fit_score >= 55:
        return "almost_ready"
    return "needs_work"


def _compute_next_actions(readiness_level: str) -> list[str]:
    if readiness_level == "not_started":
        return ["Attach a completed analysis job to this application."]
    if readiness_level == "ready":
        return [
            "Review missing skills and add evidence to your career profile.",
            "Finalize your cover letter and apply.",
        ]
    if readiness_level == "almost_ready":
        return [
            "Address the top missing skills from the analysis.",
            "Add project evidence for matched skills to your career profile.",
        ]
    return [
        "Review missing skills from the latest analysis.",
        "Add project evidence to your career profile.",
        "Consider revising your CV to address high-priority JD requirements.",
    ]


def _extract_skill_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            skill = item.get("skill") or item.get("name") or item.get("title")
            if skill:
                out.append(str(skill))
    return out


def _extract_strengths(result: dict) -> list[str]:
    raw = result.get("strengths")
    if isinstance(raw, list):
        return [str(s) for s in raw if s][:5]
    return []


def _extract_improvement_actions(result: dict) -> list[dict]:
    raw = result.get("improvement_actions")
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw[:5]:
        if isinstance(item, dict):
            out.append({
                "title": str(item.get("title") or ""),
                "safe_suggestion": str(item.get("safe_suggestion") or item.get("suggestion") or ""),
                "priority": str(item.get("priority") or "medium"),
            })
    return out


def _extract_interview_questions(result: dict) -> list[str]:
    prep = result.get("interview_prep")
    items = prep if isinstance(prep, list) else []
    out = []
    for q in items[:5]:
        if isinstance(q, str):
            out.append(q)
        elif isinstance(q, dict):
            text = q.get("question") or q.get("text") or q.get("title")
            if text:
                out.append(str(text))
    return out


def _build_evidence_checklist(profile_items: list, matched_skills: list[str]) -> list[dict]:
    checklist = []
    for skill in matched_skills[:8]:
        skill_lower = skill.lower()
        has_evidence = False
        for item in profile_items:
            skills_json = getattr(item, "skills_json") or []
            if isinstance(skills_json, list) and any(skill_lower in str(s).lower() for s in skills_json):
                has_evidence = True
                break
            title = str(getattr(item, "title") or "").lower()
            desc = str(getattr(item, "description") or "").lower()
            if skill_lower in title or skill_lower in desc:
                has_evidence = True
                break
        checklist.append({
            "skill": skill,
            "has_profile_evidence": has_evidence,
            "note": (
                "Found in career profile."
                if has_evidence
                else "No profile evidence found — add a project or skill item."
            ),
        })
    return checklist


def _safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []
