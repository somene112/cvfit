from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.services.i18n import resolve_language


SCHEMA_VERSION = "2.0"
GUARDRAIL_NOTICE = (
    "This analysis estimates CV-to-JD fit only and does not guarantee any hiring outcome."
)
GUARDRAIL_NOTICE_VI = (
    "Phân tích này chỉ ước lượng mức độ phù hợp giữa CV và JD và không đảm bảo bất kỳ kết quả tuyển dụng nào."
)
MISSING_EVIDENCE_WORDING = "not found in the parsed CV"
MISSING_EVIDENCE_WORDING_VI = "không tìm thấy trong CV đã phân tích"

_SCORE_LABELS_VI = {
    "skill_match": "Mức độ khớp kỹ năng",
    "responsibility_match": "Mức độ khớp trách nhiệm",
    "experience_level": "Mức kinh nghiệm",
    "project_relevance": "Mức độ liên quan dự án",
    "cv_quality": "Chất lượng CV",
}
_SCORE_EXPLANATIONS_VI = {
    "skill_match": "Mức độ bao phủ các nhóm kỹ năng bắt buộc và ưu tiên của JD được tìm thấy trong CV đã phân tích.",
    "responsibility_match": "Mức độ tương đồng giữa các gạch đầu dòng trong CV và phần trách nhiệm trong JD.",
    "experience_level": "Ước lượng mức độ phù hợp về thâm niên từ các tín hiệu thời gian trong CV đã phân tích.",
    "project_relevance": "Mức độ liên quan và mật độ của các gạch đầu dòng về dự án hoặc kinh nghiệm.",
    "cv_quality": "Chất lượng phân tích, thông tin liên hệ, số liệu và các gạch đầu dòng theo hướng hành động.",
}
_FIT_LEVEL_VI = {
    "excellent": "Phù hợp xuất sắc",
    "good": "Phù hợp tốt",
    "partial": "Phù hợp một phần",
    "weak": "Phù hợp yếu",
}

SENSITIVE_KEYS = {
    "access_token",
    "access_token_hash",
    "bucket",
    "cv_text",
    "file_path",
    "local_path",
    "object_key",
    "raw_cv_text",
    "report_docx_path",
    "s3_key",
    "secret",
    "storage_path",
}

SCORE_COMPONENTS = [
    ("skill_match", "Skill match", 0.35),
    ("responsibility_match", "Responsibility match", 0.30),
    ("experience_level", "Experience level", 0.15),
    ("project_relevance", "Project relevance", 0.10),
    ("cv_quality", "CV quality", 0.10),
]


def build_result_v2(
    legacy_result: dict,
    *,
    cv_parsed: dict | None = None,
    jd_struct: dict | None = None,
    job_id: str | None = None,
    language: str = "en",
) -> dict:
    lang = resolve_language(language)
    result = _scrub_sensitive(deepcopy(legacy_result or {}))
    scores = _ensure_scores(result)
    fit_score = _coerce_score(_first_present_score(scores, result))
    scores["fit_score"] = fit_score

    result["schema_version"] = SCHEMA_VERSION
    if job_id:
        result["job_id"] = job_id
    result["fit_score"] = fit_score
    result["scores"] = scores

    jd_context = _build_jd_context(jd_struct or result.get("jd", {}))
    evidence = _build_evidence(result, jd_context)
    matched_skills = _build_matched_skills(result, evidence, jd_context)
    missing_skills = _build_missing_skills(result, jd_context, lang)
    improvement_actions = _build_improvement_actions(result, missing_skills)

    result["evidence"] = evidence
    result["matched_skills"] = matched_skills
    result["missing_skills"] = missing_skills
    result["improvement_actions"] = improvement_actions
    result["limitations"] = _build_limitations(cv_parsed, lang)
    result["score_breakdown"] = _build_score_breakdown(scores, lang)
    result["overall"] = {
        "fit_score": fit_score,
        "fit_level": fit_level(fit_score),
        "summary": _build_summary(fit_score, matched_skills, missing_skills, lang),
        "confidence": _analysis_confidence(result, cv_parsed),
        "guardrail_notice": GUARDRAIL_NOTICE_VI if lang == "vi" else GUARDRAIL_NOTICE,
    }
    result["metadata"] = _build_metadata(result, cv_parsed, jd_struct, job_id)

    result.setdefault("strengths", _legacy_strengths(matched_skills))
    result.setdefault("recommendations", improvement_actions)
    return _scrub_sensitive(result)


def fit_level(fit_score: float | int | None) -> str:
    score = _coerce_score(fit_score)
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 50:
        return "partial"
    return "weak"


def _first_present_score(scores: dict, result: dict) -> Any:
    if scores.get("fit_score") is not None:
        return scores.get("fit_score")
    if result.get("fit_score") is not None:
        return result.get("fit_score")
    overall = result.get("overall", {})
    if isinstance(overall, dict) and overall.get("fit_score") is not None:
        return overall.get("fit_score")
    return None


def _ensure_scores(result: dict) -> dict:
    scores = result.get("scores")
    if not isinstance(scores, dict):
        scores = {}
    return scores


def _coerce_score(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return round(max(0.0, min(100.0, numeric)), 1)


def _scrub_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _scrub_sensitive(item)
            for key, item in value.items()
            if key not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [_scrub_sensitive(item) for item in value]
    return value


def _build_score_breakdown(scores: dict, lang: str = "en") -> list[dict]:
    explanations = {
        "skill_match": "Coverage of required and preferred JD skill groups found in the parsed CV.",
        "responsibility_match": "Similarity between parsed CV bullets and JD responsibilities.",
        "experience_level": "Estimated seniority alignment from parsed CV timeline signals.",
        "project_relevance": "Relevance and density of project or experience bullets.",
        "cv_quality": "Parse quality, contact visibility, metrics, and action-oriented bullet checks.",
    }
    breakdown = []
    for key, label, weight in SCORE_COMPONENTS:
        if key not in scores:
            continue
        breakdown.append(
            {
                "key": key,
                "label": _SCORE_LABELS_VI.get(key, label) if lang == "vi" else label,
                "score": _coerce_score(scores.get(key)),
                "weight": weight,
                "explanation": _SCORE_EXPLANATIONS_VI.get(key, explanations[key]) if lang == "vi" else explanations[key],
            }
        )
    return breakdown


def _build_evidence(result: dict, jd_context: dict) -> list[dict]:
    evidence = []
    skill_count = 0
    resp_count = 0
    legacy_evidence = result.get("evidence", [])

    for item in legacy_evidence if isinstance(legacy_evidence, list) else []:
        if not isinstance(item, dict):
            continue
        entry = _scrub_sensitive(deepcopy(item))
        evidence_type = entry.get("type", "")
        source = "cv"
        kind = "responsibility" if evidence_type == "responsibility_match" else "skill"
        if kind == "responsibility":
            resp_count += 1
            entry["id"] = entry.get("id") or f"ev_cv_resp_{resp_count:03d}"
            if entry.get("text"):
                entry.setdefault("best_cv_bullet", entry["text"])
            entry.setdefault("jd_evidence_ids", _jd_responsibility_ids(jd_context, entry.get("jd_requirement")))
        else:
            skill_count += 1
            entry["id"] = entry.get("id") or f"ev_cv_skill_{skill_count:03d}"
        entry.setdefault("source", source)
        entry.setdefault("kind", kind)
        entry.setdefault("confidence", _evidence_confidence(entry))
        if evidence_type == "skill_match" and "matched_skill" in entry:
            entry.setdefault("normalized_skill", entry["matched_skill"])
        evidence.append(entry)

    seen_responsibilities = {
        (item.get("jd_requirement"), item.get("best_cv_bullet") or item.get("text"))
        for item in evidence
        if item.get("kind") == "responsibility"
    }
    responsibility_details = result.get("responsibility_match", {}).get("details", [])
    for detail in responsibility_details if isinstance(responsibility_details, list) else []:
        if not isinstance(detail, dict):
            continue
        jd_requirement = detail.get("jd_requirement")
        best_cv_bullet = detail.get("best_cv_bullet")
        if not jd_requirement or not best_cv_bullet:
            continue
        key = (jd_requirement, best_cv_bullet)
        if key in seen_responsibilities:
            continue
        resp_count += 1
        evidence.append(
            {
                "id": f"ev_cv_resp_{resp_count:03d}",
                "type": "responsibility_match",
                "source": "cv",
                "kind": "responsibility",
                "text": best_cv_bullet,
                "best_cv_bullet": best_cv_bullet,
                "jd_requirement": jd_requirement,
                "similarity": detail.get("similarity"),
                "confidence": _evidence_confidence(detail),
                "jd_evidence_ids": _jd_responsibility_ids(jd_context, jd_requirement),
            }
        )
        seen_responsibilities.add(key)

    evidence.extend(jd_context["evidence"])
    return evidence


def _evidence_confidence(entry: dict) -> float:
    if isinstance(entry.get("similarity"), (int, float)):
        return round(max(0.0, min(1.0, float(entry["similarity"]))), 2)
    if entry.get("text"):
        return 0.85
    return 0.5


def _build_matched_skills(result: dict, evidence: list[dict], jd_context: dict) -> list[dict]:
    skills = result.get("skills", {}) if isinstance(result.get("skills"), dict) else {}
    matched = []
    evidence_by_skill = {}
    for ev in evidence:
        if ev.get("source") != "cv" or ev.get("kind") != "skill":
            continue
        skill = ev.get("matched_skill") or ev.get("normalized_skill")
        if skill:
            evidence_by_skill.setdefault(str(skill).lower(), []).append(ev["id"])
        for item in ev.get("skill_group", []) if isinstance(ev.get("skill_group"), list) else []:
            evidence_by_skill.setdefault(str(item).lower(), []).append(ev["id"])
        if isinstance(ev.get("skill_group"), list):
            evidence_by_skill.setdefault(_group_key(ev["skill_group"]), []).append(ev["id"])

    for requirement_type, groups_key in (
        ("must_have", "matched_must_groups"),
        ("nice_to_have", "matched_nice_groups"),
    ):
        for item in skills.get(groups_key, []) or []:
            if not isinstance(item, dict):
                continue
            skill = item.get("matched_by")
            group = item.get("group") or []
            if not skill:
                continue
            cv_evidence_ids = _dedupe(
                evidence_by_skill.get(str(skill).lower(), [])
                + evidence_by_skill.get(_group_key(group), [])
            )
            jd_requirement, jd_evidence_ids = _jd_requirement_for_group(
                jd_context,
                group,
                fallback=" / ".join(group) if isinstance(group, list) else str(group),
            )
            matched.append(
                {
                    "skill": skill,
                    "requirement_type": requirement_type,
                    "jd_requirement": jd_requirement,
                    "match_type": "alias_or_group" if isinstance(group, list) and len(group) > 1 else "direct",
                    "confidence": 0.9,
                    "cv_evidence_ids": cv_evidence_ids,
                    "jd_evidence_ids": jd_evidence_ids,
                    "notes": "Matched from parsed CV evidence." if cv_evidence_ids else f"CV evidence {MISSING_EVIDENCE_WORDING}.",
                }
            )
    return matched


def _build_missing_skills(result: dict, jd_context: dict, lang: str = "en") -> list[dict]:
    skill_gap = result.get("skill_gap", {}) if isinstance(result.get("skill_gap"), dict) else {}
    missing = []
    for requirement_type, key, severity in (
        ("must_have", "missing_must_have", "high"),
        ("nice_to_have", "missing_nice_to_have", "medium"),
    ):
        for skill in skill_gap.get(key, []) or []:
            jd_requirement, jd_evidence_ids = _jd_requirement_for_skill(jd_context, skill)
            if lang == "vi":
                requirement_label = "yêu cầu" if requirement_type == "must_have" else "liệt kê"
                reason = f"Mô tả công việc {requirement_label} {skill}, nhưng bằng chứng về {skill} {MISSING_EVIDENCE_WORDING_VI}."
                suggestion = (
                    f"Nếu bạn thực sự đã sử dụng {skill}, hãy thêm một gạch đầu dòng CV trung thực với bối cảnh "
                    "dự án, công cụ đã dùng và kết quả đo lường được. Chỉ thêm nếu điều đó là sự thật."
                )
            else:
                requirement_label = "requires" if requirement_type == "must_have" else "lists"
                reason = f"JD {requirement_label} {skill}, but {skill} evidence was {MISSING_EVIDENCE_WORDING}."
                suggestion = (
                    f"If you have actually used {skill}, add a truthful CV bullet with project context, "
                    "tools used, and measurable outcome. Only add this if it is true."
                )
            missing.append(
                {
                    "skill": skill,
                    "requirement_type": requirement_type,
                    "jd_requirement": jd_requirement or skill,
                    "severity": severity,
                    "reason": reason,
                    "jd_evidence_ids": jd_evidence_ids,
                    "suggestion": suggestion,
                }
            )
    return missing


def _build_jd_context(jd_struct: dict | None) -> dict:
    context = {
        "evidence": [],
        "skill_requirements": {},
        "responsibility_requirements": {},
    }
    if not isinstance(jd_struct, dict):
        return context

    skill_items = _jd_skill_items(jd_struct)
    must_count = 0
    nice_count = 0
    for item in skill_items:
        if not isinstance(item, dict):
            continue
        group = item.get("group") or []
        requirement_type = "nice_to_have" if item.get("type") == "preferred" else "must_have"
        if requirement_type == "must_have":
            must_count += 1
            evidence_id = f"ev_jd_skill_must_{must_count:03d}"
        else:
            nice_count += 1
            evidence_id = f"ev_jd_skill_nice_{nice_count:03d}"
        label = _group_label(group)
        text = item.get("source_line") or f"JD {requirement_type.replace('_', ' ')} skill requirement: {label}"
        entry = {
            "id": evidence_id,
            "source": "jd",
            "kind": "requirement",
            "text": text,
            "skill_group": group,
            "requirement_type": requirement_type,
            "confidence": 0.9 if item.get("source_line") else 0.7,
        }
        context["evidence"].append(entry)
        for key in _skill_lookup_keys(group):
            context["skill_requirements"].setdefault(key, {"text": text, "ids": []})
            context["skill_requirements"][key]["ids"].append(evidence_id)

    for index, responsibility in enumerate(jd_struct.get("responsibilities", []) or [], start=1):
        if not responsibility:
            continue
        evidence_id = f"ev_jd_resp_{index:03d}"
        context["evidence"].append(
            {
                "id": evidence_id,
                "source": "jd",
                "kind": "responsibility",
                "text": responsibility,
                "jd_requirement": responsibility,
                "confidence": 0.85,
            }
        )
        context["responsibility_requirements"].setdefault(str(responsibility).strip().lower(), []).append(evidence_id)
    return context


def _jd_skill_items(jd_struct: dict) -> list[dict]:
    details = jd_struct.get("skill_group_details")
    if isinstance(details, list) and details:
        return details
    items = []
    for group in jd_struct.get("must_have_skill_groups", []) or []:
        items.append({"group": group, "type": "required", "source_line": None})
    for group in jd_struct.get("nice_to_have_skill_groups", []) or []:
        items.append({"group": group, "type": "preferred", "source_line": None})
    return items


def _build_improvement_actions(result: dict, missing_skills: list[dict]) -> list[dict]:
    actions = []
    for index, item in enumerate(missing_skills[:6], start=1):
        skill = item["skill"]
        action_prefix = "must" if item["requirement_type"] == "must_have" else "nice"
        actions.append(
            {
                "id": f"act_missing_{action_prefix}_{index:03d}",
                "type": "skill_gap",
                "priority": "high" if item["requirement_type"] == "must_have" else "medium",
                "title": f"Address {skill} evidence gap",
                "suggestion": (
                    f"If you have actually used {skill}, add a project or experience bullet "
                    f"that responds to this JD requirement: {item['jd_requirement']}. "
                    "Describe what you built, the tools used, and the measurable outcome. "
                    "Only add this if it is true."
                ),
                "related_skill": skill,
                "related_evidence_ids": item.get("jd_evidence_ids", []),
                "guardrail": "Only add this if it is true. Do not invent skills or experience.",
            }
        )

    cv_improvements = result.get("cv_improvements", [])
    for index, issue in enumerate(cv_improvements[:4], start=1):
        if not isinstance(issue, dict):
            continue
        actions.append(
            {
                "id": f"act_cv_{index:03d}",
                "type": "cv_rewrite",
                "priority": "medium",
                "title": issue.get("issue", "Improve CV evidence"),
                "suggestion": (
                    f"If this reflects your actual work, {issue.get('fix', 'add clearer CV evidence')}. "
                    "Only add this if it is true."
                ),
                "related_skill": None,
                "related_evidence_ids": [],
                "guardrail": "Do not invent skills or experience.",
            }
        )
    return actions


def _build_limitations(cv_parsed: dict | None, lang: str = "en") -> list[str]:
    if lang == "vi":
        limitations = [
            "Phân tích này chỉ ước lượng mức độ phù hợp giữa CV và JD và không đảm bảo bất kỳ kết quả tuyển dụng nào.",
            "Thiếu bằng chứng nghĩa là không tìm thấy hỗ trợ trong CV đã phân tích, chứ không phải ứng viên chắc chắn thiếu kỹ năng đó.",
            "Không bịa đặt kỹ năng, kinh nghiệm, dự án, nhà tuyển dụng, ngày tháng, chứng chỉ hay số liệu dựa trên các gợi ý này.",
        ]
        if cv_parsed and cv_parsed.get("confidence") is not None:
            limitations.append(
                "Độ tin cậy của bộ phân tích dựa trên chất lượng văn bản trích xuất và có thể bỏ sót nội dung từ file scan hoặc nhiều hình ảnh."
            )
        return limitations
    limitations = [
        "This analysis estimates CV-to-JD fit only and does not guarantee any hiring outcome.",
        "Missing evidence means support was not found in the parsed CV, not that the candidate definitely lacks the skill.",
        "Do not invent skills, experience, projects, metrics, or responsibilities based on these suggestions.",
    ]
    if cv_parsed and cv_parsed.get("confidence") is not None:
        limitations.append(
            "Parser confidence is based on extracted text quality and may miss content from scanned or image-heavy files."
        )
    return limitations


def _build_summary(fit_score: float, matched_skills: list[dict], missing_skills: list[dict], lang: str = "en") -> str:
    level = fit_level(fit_score)
    matched_count = len(matched_skills)
    missing_count = len(missing_skills)
    if lang == "vi":
        level_vi = _FIT_LEVEL_VI.get(level, level)
        if missing_count:
            return (
                f"{level_vi} với {matched_count} nhóm kỹ năng đáp ứng và {missing_count} yêu cầu JD "
                f"chưa có bằng chứng ({MISSING_EVIDENCE_WORDING_VI})."
            )
        return f"{level_vi} với {matched_count} nhóm kỹ năng đáp ứng và không có thiếu sót bằng chứng kỹ năng đáng kể."
    if missing_count:
        return (
            f"{level.title()} fit with {matched_count} matched skill groups and "
            f"{missing_count} JD requirements where evidence was {MISSING_EVIDENCE_WORDING}."
        )
    return f"{level.title()} fit with {matched_count} matched skill groups and no major missing skill evidence found."


def _jd_requirement_for_group(jd_context: dict, group: Any, fallback: str) -> tuple[str, list[str]]:
    for key in _skill_lookup_keys(group):
        item = jd_context["skill_requirements"].get(key)
        if item:
            return item["text"], _dedupe(item["ids"])
    return fallback, []


def _jd_requirement_for_skill(jd_context: dict, skill: str) -> tuple[str | None, list[str]]:
    item = jd_context["skill_requirements"].get(str(skill).lower())
    if item:
        return item["text"], _dedupe(item["ids"])
    return None, []


def _jd_responsibility_ids(jd_context: dict, jd_requirement: Any) -> list[str]:
    if not jd_requirement:
        return []
    return _dedupe(jd_context["responsibility_requirements"].get(str(jd_requirement).strip().lower(), []))


def _skill_lookup_keys(group: Any) -> list[str]:
    if isinstance(group, list):
        return _dedupe([_group_key(group)] + [str(item).lower() for item in group])
    value = str(group).lower()
    return [value]


def _group_label(group: Any) -> str:
    if isinstance(group, list):
        return " / ".join(str(item) for item in group)
    return str(group)


def _group_key(group: Any) -> str:
    if isinstance(group, list):
        return " / ".join(str(item).lower() for item in group)
    return str(group).lower()


def _dedupe(values: list[Any]) -> list[Any]:
    seen = set()
    out = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _analysis_confidence(result: dict, cv_parsed: dict | None) -> float:
    confidence = None
    if cv_parsed:
        confidence = cv_parsed.get("confidence")
    if confidence is None:
        confidence = result.get("cv", {}).get("parsed_confidence") if isinstance(result.get("cv"), dict) else None
    try:
        return round(max(0.0, min(1.0, float(confidence))), 2)
    except (TypeError, ValueError):
        return 0.75


def _build_metadata(
    result: dict,
    cv_parsed: dict | None,
    jd_struct: dict | None,
    job_id: str | None,
) -> dict:
    cv_meta = result.get("cv", {}) if isinstance(result.get("cv"), dict) else {}
    jd_meta = jd_struct or (result.get("jd", {}) if isinstance(result.get("jd"), dict) else {})
    metadata = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scorer_version": "phase3.result_json_v2",
        "job_id": job_id or result.get("job_id"),
        "cv": {
            "file_name": cv_meta.get("file_name"),
            "parsed_confidence": (
                cv_parsed.get("confidence") if cv_parsed else cv_meta.get("parsed_confidence")
            ),
            "skills_detected": cv_meta.get("skills_detected")
            or (cv_parsed.get("skills_detected", []) if cv_parsed else []),
        },
        "jd": {
            "role": jd_meta.get("role"),
            "must_have_skill_groups": jd_meta.get("must_have_skill_groups", []),
            "nice_to_have_skill_groups": jd_meta.get("nice_to_have_skill_groups", []),
            "responsibility_count": len(jd_meta.get("responsibilities", []) or []),
        },
    }
    return _scrub_sensitive(metadata)


def _legacy_strengths(matched_skills: list[dict]) -> list[str]:
    return [item["skill"] for item in matched_skills if item.get("skill")]
