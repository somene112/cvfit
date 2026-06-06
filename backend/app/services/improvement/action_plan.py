from __future__ import annotations

from typing import Any


MISSING_EVIDENCE_WORDING = "was not found in the parsed CV"


def build_improvement_actions(result: dict, *, max_actions: int = 8) -> list[dict]:
    actions: list[dict] = []

    for item in _missing_skills(result)[:max_actions]:
        skill = _safe_label(item.get("skill") or "this skill")
        requirement_type = item.get("requirement_type")
        priority = "high" if requirement_type == "must_have" else "medium"
        jd_requirement = _safe_label(item.get("jd_requirement") or skill)
        evidence_ids = _evidence_ids(item.get("jd_evidence_ids"))
        index = len(actions) + 1
        safe_suggestion = (
            f"If you have actually used {skill}, add a truthful CV bullet with project context, "
            "your specific responsibility, tools used, and a real outcome you can defend. "
            "Only add this if it is true."
        )
        actions.append(
            {
                "id": f"act_v3_missing_{index:03d}",
                "priority": priority,
                "category": "missing_skill",
                "title": f"Address {skill} evidence gap",
                "status": "open",
                "linked_skill": skill,
                "linked_evidence": evidence_ids,
                "reason": f"The JD mentions {jd_requirement}, but {skill} evidence {MISSING_EVIDENCE_WORDING}.",
                "safe_suggestion": safe_suggestion,
                "do_not_fabricate": True,
                # v2/report compatibility aliases.
                "type": "skill_gap",
                "suggestion": safe_suggestion,
                "related_skill": skill,
                "related_evidence_ids": evidence_ids,
                "guardrail": "Only add this if it is true. Do not invent skills or experience.",
            }
        )

    remaining = max_actions - len(actions)
    if remaining > 0:
        actions.extend(_cv_quality_actions(result, limit=remaining, start_index=len(actions) + 1))

    if not actions:
        actions.append(_generic_action())

    return actions[:max_actions]


def _cv_quality_actions(result: dict, *, limit: int, start_index: int) -> list[dict]:
    actions: list[dict] = []
    issues = result.get("cv_improvements")
    for offset, item in enumerate(issues if isinstance(issues, list) else [], start=0):
        if len(actions) >= limit:
            break
        if not isinstance(item, dict):
            continue
        title = _safe_label(item.get("issue") or "Improve CV evidence")
        reason = (
            "The parsed CV could be clearer for this JD, but any added details must come from actual work."
        )
        safe_suggestion = (
            "If this reflects your actual work, rewrite the relevant bullet with clearer scope, tools, "
            "responsibility, and a real outcome. Only add this if it is true."
        )
        action_id = start_index + offset
        actions.append(
            {
                "id": f"act_v3_cv_{action_id:03d}",
                "priority": "medium",
                "category": "weak_evidence",
                "title": title,
                "status": "open",
                "linked_skill": None,
                "linked_evidence": [],
                "reason": reason,
                "safe_suggestion": safe_suggestion,
                "do_not_fabricate": True,
                # v2/report compatibility aliases.
                "type": "cv_rewrite",
                "suggestion": safe_suggestion,
                "related_skill": None,
                "related_evidence_ids": [],
                "guardrail": "Only add this if it is true. Do not invent skills or experience.",
            }
        )
    return actions


def _generic_action() -> dict:
    safe_suggestion = (
        "If the parsed CV missed relevant work you actually did, add a clearer bullet with the real task, "
        "tools used, and outcome. Only add this if it is true."
    )
    return {
        "id": "act_v3_general_001",
        "priority": "low",
        "category": "weak_evidence",
        "title": "Make relevant CV evidence easier to verify",
        "status": "open",
        "linked_skill": None,
        "linked_evidence": [],
        "reason": "The result can be improved by making real CV evidence easier to connect to the JD.",
        "safe_suggestion": safe_suggestion,
        "do_not_fabricate": True,
        "type": "cv_rewrite",
        "suggestion": safe_suggestion,
        "related_skill": None,
        "related_evidence_ids": [],
        "guardrail": "Only add this if it is true. Do not invent skills or experience.",
    }


def _missing_skills(result: dict) -> list[dict]:
    missing = result.get("missing_skills")
    if isinstance(missing, list):
        return [item for item in missing if isinstance(item, dict)]

    gap = result.get("skill_gap") if isinstance(result.get("skill_gap"), dict) else {}
    out = []
    for requirement_type, key in (
        ("must_have", "missing_must_have"),
        ("nice_to_have", "missing_nice_to_have"),
    ):
        for skill in gap.get(key, []) or []:
            out.append(
                {
                    "skill": skill,
                    "requirement_type": requirement_type,
                    "jd_requirement": skill,
                    "jd_evidence_ids": [],
                }
            )
    return out


def _evidence_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _safe_label(value: Any) -> str:
    text = str(value or "").strip()
    return text[:160] if text else "this requirement"
