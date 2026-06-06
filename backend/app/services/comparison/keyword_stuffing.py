from __future__ import annotations

from typing import Any


WARNING_MESSAGE = (
    "The revised CV mentions {skill}, but project or responsibility evidence was not found. "
    "Add truthful context if you have it; otherwise keep it as a learning goal."
)


def detect_keyword_stuffing(base_result: dict, new_result: dict) -> list[dict]:
    warnings: list[dict] = []
    new_matched = _matched_skill_map(new_result)
    missing_skills = set(_skill_key(item.get("skill")) for item in _missing_skills(new_result))

    unsupported_matches = []
    for skill_key, item in new_matched.items():
        if _has_cv_evidence(item, new_result):
            continue
        unsupported_matches.append(item)
        warnings.append(_warning(item.get("skill") or skill_key))

    for skill in missing_skills:
        if not skill:
            continue
        if skill in new_matched:
            continue
        if _weak_keyword_mention(skill, new_result):
            warnings.append(_warning(skill))

    if len(unsupported_matches) >= 3:
        warnings.append(
            {
                "skill": "multiple_skills",
                "severity": "medium",
                "message": (
                    "Several newly matched skills do not include related CV evidence. Treat this as an "
                    "evidence quality risk and add truthful project context where available."
                ),
            }
        )

    return _dedupe_warnings(warnings)


def _warning(skill: Any) -> dict:
    label = str(skill or "this skill").strip() or "this skill"
    return {
        "skill": label,
        "severity": "medium",
        "message": WARNING_MESSAGE.format(skill=label),
    }


def _matched_skill_map(result: dict) -> dict[str, dict]:
    out = {}
    matched = result.get("matched_skills")
    for item in matched if isinstance(matched, list) else []:
        if not isinstance(item, dict):
            continue
        key = _skill_key(item.get("skill"))
        if key:
            out[key] = item
    return out


def _missing_skills(result: dict) -> list[dict]:
    missing = result.get("missing_skills")
    return [item for item in missing if isinstance(item, dict)] if isinstance(missing, list) else []


def _has_cv_evidence(matched_item: dict, result: dict) -> bool:
    ids = matched_item.get("cv_evidence_ids")
    if not isinstance(ids, list) or not ids:
        return False
    evidence_by_id = {
        str(item.get("id")): item
        for item in result.get("evidence", [])
        if isinstance(item, dict) and item.get("id")
    }
    for evidence_id in ids:
        item = evidence_by_id.get(str(evidence_id))
        if item and item.get("source") == "cv" and (item.get("text") or item.get("best_cv_bullet")):
            return True
    return False


def _weak_keyword_mention(skill: str, result: dict) -> bool:
    skill_l = skill.lower()
    for item in result.get("evidence", []) if isinstance(result.get("evidence"), list) else []:
        if not isinstance(item, dict) or item.get("source") != "cv":
            continue
        text = str(item.get("text") or item.get("best_cv_bullet") or "").lower()
        if skill_l not in text:
            continue
        if any(word in text for word in ("built", "implemented", "deployed", "designed", "optimized", "owned")):
            return False
        if "," in text or "skills" in text:
            return True
    return False


def _skill_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _dedupe_warnings(warnings: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for item in warnings:
        key = (item.get("skill"), item.get("message"))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
