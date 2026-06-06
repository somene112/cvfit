from __future__ import annotations

from typing import Any

from app.services.comparison.keyword_stuffing import detect_keyword_stuffing


SENSITIVE_KEYS = {
    "access_token",
    "access_token_hash",
    "authorization",
    "bearer",
    "jwt",
    "password",
    "password_hash",
    "raw_cv_text",
    "cv_text",
    "storage_path",
    "report_docx_path",
    "local_path",
    "file_path",
    "s3_key",
    "object_key",
    "bucket",
    "secret",
}


def compare_results(
    base_result: dict,
    new_result: dict,
    *,
    base_job_id: str,
    new_job_id: str,
) -> dict:
    base = _scrub(base_result or {})
    new = _scrub(new_result or {})
    base_score = _extract_score(base)
    new_score = _extract_score(new)
    warnings = detect_keyword_stuffing(base, new)

    comparison = {
        "base_job_id": base_job_id,
        "new_job_id": new_job_id,
        "base_score": base_score,
        "new_score": new_score,
        "score_delta": _delta(base_score, new_score),
        "breakdown_delta": _breakdown_delta(base, new),
        "resolved_missing_skills": _resolved_missing_skills(base, new),
        "still_missing_skills": _still_missing_skills(base, new),
        "newly_matched_skills": _newly_matched_skills(base, new),
        "new_evidence": _new_evidence(base, new),
        "keyword_stuffing_warnings": warnings,
        "improvement_summary": _summary(base_score, new_score, warnings),
        "next_actions": _next_actions(new),
    }
    return _scrub(comparison)


def _extract_score(result: dict) -> float | None:
    overall = result.get("overall") if isinstance(result.get("overall"), dict) else {}
    for value in (overall.get("fit_score"), result.get("fit_score")):
        if value is not None:
            return _coerce_float(value)
    scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
    return _coerce_float(scores.get("fit_score")) if scores.get("fit_score") is not None else None


def _coerce_float(value: Any) -> float | None:
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def _delta(base_score: float | None, new_score: float | None) -> float | None:
    if base_score is None or new_score is None:
        return None
    return round(new_score - base_score, 1)


def _breakdown_delta(base: dict, new: dict) -> dict[str, float]:
    base_scores = _component_scores(base)
    new_scores = _component_scores(new)
    out = {}
    for key in sorted(set(base_scores) & set(new_scores)):
        out[key] = round(new_scores[key] - base_scores[key], 1)
    return out


def _component_scores(result: dict) -> dict[str, float]:
    out = {}
    breakdown = result.get("score_breakdown")
    if isinstance(breakdown, list):
        for item in breakdown:
            if not isinstance(item, dict) or not item.get("key"):
                continue
            score = _coerce_float(item.get("score"))
            if score is not None:
                out[str(item["key"])] = score
    scores = result.get("scores")
    if isinstance(scores, dict):
        for key, value in scores.items():
            if key == "fit_score":
                continue
            score = _coerce_float(value)
            if score is not None:
                out.setdefault(str(key), score)
    return out


def _resolved_missing_skills(base: dict, new: dict) -> list[dict]:
    base_missing = _missing_skill_map(base)
    new_matched = _matched_skill_map(new)
    out = []
    for skill, missing_item in base_missing.items():
        matched_item = new_matched.get(skill)
        if not matched_item or not _has_meaningful_cv_evidence(matched_item, new):
            continue
        out.append(
            {
                "skill": matched_item.get("skill") or missing_item.get("skill") or skill,
                "base_reason": missing_item.get("reason"),
                "new_evidence_ids": _ids(matched_item.get("cv_evidence_ids")),
            }
        )
    return out


def _still_missing_skills(base: dict, new: dict) -> list[dict]:
    base_missing = _missing_skill_map(base)
    new_missing = _missing_skill_map(new)
    new_matched = _matched_skill_map(new)
    out = []
    for skill, item in {**base_missing, **new_missing}.items():
        matched_item = new_matched.get(skill)
        if matched_item and _has_meaningful_cv_evidence(matched_item, new):
            continue
        out.append(
            {
                "skill": item.get("skill") or skill,
                "reason": item.get("reason") or "Evidence remains weak or was not found in the parsed CV.",
            }
        )
    return out


def _newly_matched_skills(base: dict, new: dict) -> list[dict]:
    base_matched = _matched_skill_map(base)
    out = []
    for skill, item in _matched_skill_map(new).items():
        if skill in base_matched:
            continue
        out.append(
            {
                "skill": item.get("skill") or skill,
                "cv_evidence_ids": _ids(item.get("cv_evidence_ids")),
                "jd_requirement": item.get("jd_requirement"),
            }
        )
    return out


def _new_evidence(base: dict, new: dict, *, limit: int = 8) -> list[dict]:
    base_ids = {
        str(item.get("id"))
        for item in base.get("evidence", [])
        if isinstance(item, dict) and item.get("id")
    }
    out = []
    for item in new.get("evidence", []) if isinstance(new.get("evidence"), list) else []:
        if not isinstance(item, dict):
            continue
        evidence_id = str(item.get("id") or "")
        text = item.get("best_cv_bullet") or item.get("text")
        if evidence_id and evidence_id in base_ids:
            continue
        if item.get("source") != "cv" or not text:
            continue
        out.append(
            {
                "id": evidence_id or None,
                "kind": item.get("kind") or item.get("type"),
                "text": _truncate(str(text), 220),
                "related_skill": item.get("normalized_skill") or item.get("matched_skill"),
            }
        )
        if len(out) >= limit:
            break
    return out


def _next_actions(new: dict, *, limit: int = 5) -> list[dict]:
    actions = new.get("improvement_actions")
    if not isinstance(actions, list):
        return []
    return [_scrub(item) for item in actions if isinstance(item, dict)][:limit]


def _summary(base_score: float | None, new_score: float | None, warnings: list[dict]) -> str:
    score_delta = _delta(base_score, new_score)
    if score_delta is None:
        base = "Comparison is available, but one or both scores were missing."
    elif score_delta > 0:
        base = f"The revised CV score improved by {score_delta} points, but evidence quality still matters."
    elif score_delta < 0:
        base = f"The revised CV score decreased by {abs(score_delta)} points; review remaining gaps and evidence quality."
    else:
        base = "The revised CV score did not change; review evidence quality and next actions."
    if warnings:
        return base + " Keyword-stuffing warnings indicate some matches may need stronger project context."
    return base


def _missing_skill_map(result: dict) -> dict[str, dict]:
    out = {}
    for item in result.get("missing_skills", []) if isinstance(result.get("missing_skills"), list) else []:
        if not isinstance(item, dict):
            continue
        key = _skill_key(item.get("skill"))
        if key:
            out[key] = item
    return out


def _matched_skill_map(result: dict) -> dict[str, dict]:
    out = {}
    for item in result.get("matched_skills", []) if isinstance(result.get("matched_skills"), list) else []:
        if not isinstance(item, dict):
            continue
        key = _skill_key(item.get("skill"))
        if key:
            out[key] = item
    return out


def _has_meaningful_cv_evidence(matched_item: dict, result: dict) -> bool:
    evidence_by_id = {
        str(item.get("id")): item
        for item in result.get("evidence", [])
        if isinstance(item, dict) and item.get("id")
    }
    for evidence_id in _ids(matched_item.get("cv_evidence_ids")):
        item = evidence_by_id.get(str(evidence_id))
        if item and item.get("source") == "cv" and (item.get("text") or item.get("best_cv_bullet")):
            return True
    return False


def _ids(value: Any) -> list[str]:
    return [str(item) for item in value if item] if isinstance(value, list) else []


def _skill_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _truncate(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _scrub(item)
            for key, item in value.items()
            if str(key).lower() not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value
