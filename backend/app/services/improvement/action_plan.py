from __future__ import annotations

from typing import Any

from app.services.i18n import resolve_language


MISSING_EVIDENCE_WORDING = "was not found in the parsed CV"

# Deterministic CV-quality issue strings (from the scorer) → Vietnamese titles.
_VI_ISSUE_MAP = {
    "CV text too short or parser quality may be low": "Văn bản CV quá ngắn hoặc chất lượng phân tích có thể thấp",
    "Contact/email not clearly visible": "Thông tin liên hệ/email chưa hiển thị rõ ràng",
    "Low number of measurable achievements": "Ít thành tựu có thể đo lường được",
    "Bullets are not strongly action-oriented": "Gạch đầu dòng chưa đủ định hướng hành động",
    "Improve CV evidence": "Cải thiện bằng chứng trong CV",
}

_GUARDRAIL_EN = "Only add this if it is true. Do not invent skills or experience."
_GUARDRAIL_VI = "Chỉ thêm nếu điều đó là sự thật. Không bịa đặt kỹ năng hay kinh nghiệm."


def build_improvement_actions(result: dict, *, max_actions: int = 8, language: str = "en") -> list[dict]:
    lang = resolve_language(language)
    actions: list[dict] = []

    for item in _missing_skills(result)[:max_actions]:
        skill = _safe_label(item.get("skill") or ("kỹ năng này" if lang == "vi" else "this skill"))
        requirement_type = item.get("requirement_type")
        priority = "high" if requirement_type == "must_have" else "medium"
        jd_requirement = _safe_label(item.get("jd_requirement") or skill)
        evidence_ids = _evidence_ids(item.get("jd_evidence_ids"))
        index = len(actions) + 1
        if lang == "vi":
            safe_suggestion = (
                f"Nếu bạn thực sự đã sử dụng {skill}, hãy thêm một gạch đầu dòng CV trung thực với bối cảnh "
                "dự án, trách nhiệm cụ thể của bạn, công cụ đã dùng và một kết quả thực tế mà bạn có thể bảo vệ. "
                "Chỉ thêm nếu điều đó là sự thật."
            )
            title = f"Khắc phục thiếu bằng chứng về {skill}"
            reason = f"Mô tả công việc có đề cập đến {jd_requirement}, nhưng không tìm thấy bằng chứng về {skill} trong CV đã phân tích."
        else:
            safe_suggestion = (
                f"If you have actually used {skill}, add a truthful CV bullet with project context, "
                "your specific responsibility, tools used, and a real outcome you can defend. "
                "Only add this if it is true."
            )
            title = f"Address {skill} evidence gap"
            reason = f"The JD mentions {jd_requirement}, but {skill} evidence {MISSING_EVIDENCE_WORDING}."
        actions.append(
            {
                "id": f"act_v3_missing_{index:03d}",
                "priority": priority,
                "category": "missing_skill",
                "title": title,
                "status": "open",
                "linked_skill": skill,
                "linked_evidence": evidence_ids,
                "reason": reason,
                "safe_suggestion": safe_suggestion,
                "do_not_fabricate": True,
                # v2/report compatibility aliases.
                "type": "skill_gap",
                "suggestion": safe_suggestion,
                "related_skill": skill,
                "related_evidence_ids": evidence_ids,
                "guardrail": _GUARDRAIL_VI if lang == "vi" else _GUARDRAIL_EN,
            }
        )

    remaining = max_actions - len(actions)
    if remaining > 0:
        actions.extend(_cv_quality_actions(result, limit=remaining, start_index=len(actions) + 1, lang=lang))

    if not actions:
        actions.append(_generic_action(lang))

    return actions[:max_actions]


def _cv_quality_actions(result: dict, *, limit: int, start_index: int, lang: str = "en") -> list[dict]:
    actions: list[dict] = []
    issues = result.get("cv_improvements")
    for offset, item in enumerate(issues if isinstance(issues, list) else [], start=0):
        if len(actions) >= limit:
            break
        if not isinstance(item, dict):
            continue
        raw_title = _safe_label(item.get("issue") or "Improve CV evidence")
        if lang == "vi":
            title = _VI_ISSUE_MAP.get(raw_title, raw_title)
            reason = (
                "CV đã phân tích có thể rõ ràng hơn cho vị trí này, nhưng mọi chi tiết bổ sung phải đến từ "
                "công việc thực tế."
            )
            safe_suggestion = (
                "Nếu điều này phản ánh công việc thực tế của bạn, hãy viết lại gạch đầu dòng liên quan với "
                "phạm vi, công cụ, trách nhiệm và kết quả thực tế rõ ràng hơn. Chỉ thêm nếu điều đó là sự thật."
            )
        else:
            title = raw_title
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
                "guardrail": _GUARDRAIL_VI if lang == "vi" else _GUARDRAIL_EN,
            }
        )
    return actions


def _generic_action(lang: str = "en") -> dict:
    if lang == "vi":
        title = "Làm cho bằng chứng CV liên quan dễ kiểm chứng hơn"
        reason = "Kết quả có thể cải thiện bằng cách làm cho bằng chứng CV thật dễ kết nối với mô tả công việc hơn."
        safe_suggestion = (
            "Nếu CV đã phân tích bỏ sót công việc liên quan mà bạn thực sự đã làm, hãy thêm một gạch đầu dòng "
            "rõ ràng hơn với nhiệm vụ thực tế, công cụ đã dùng và kết quả. Chỉ thêm nếu điều đó là sự thật."
        )
    else:
        title = "Make relevant CV evidence easier to verify"
        reason = "The result can be improved by making real CV evidence easier to connect to the JD."
        safe_suggestion = (
            "If the parsed CV missed relevant work you actually did, add a clearer bullet with the real task, "
            "tools used, and outcome. Only add this if it is true."
        )
    return {
        "id": "act_v3_general_001",
        "priority": "low",
        "category": "weak_evidence",
        "title": title,
        "status": "open",
        "linked_skill": None,
        "linked_evidence": [],
        "reason": reason,
        "safe_suggestion": safe_suggestion,
        "do_not_fabricate": True,
        "type": "cv_rewrite",
        "suggestion": safe_suggestion,
        "related_skill": None,
        "related_evidence_ids": [],
        "guardrail": _GUARDRAIL_VI if lang == "vi" else _GUARDRAIL_EN,
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
