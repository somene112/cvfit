from __future__ import annotations

from typing import Any

from app.services.i18n import resolve_language


WARNING = "Only use details that are true and can be defended in an interview."
WARNING_VI = "Chỉ sử dụng các chi tiết có thật và bạn có thể bảo vệ khi phỏng vấn."


def build_safe_rewrite_suggestions(result: dict, *, max_suggestions: int = 4, language: str = "en") -> list[dict]:
    lang = resolve_language(language)
    evidence_items = _cv_evidence(result)
    suggestions: list[dict] = []

    if lang == "vi":
        structure = (
            "Đã xây dựng [tính năng hoặc quy trình thực tế] bằng [framework thực tế] và [cơ sở dữ liệu thực tế] "
            "để hỗ trợ [nhu cầu người dùng hoặc nghiệp vụ thực tế], mang lại [chỉ số hoặc kết quả thực tế]."
        )
        missing_context = [
            "tính năng hoặc quy trình thực tế",
            "framework thực tế",
            "cơ sở dữ liệu thực tế",
            "chỉ số hoặc kết quả thực tế",
        ]
        warning = WARNING_VI
    else:
        structure = (
            "Built [actual feature or workflow] using [actual framework] and [actual database] "
            "to support [actual user or business need], resulting in [real metric or actual outcome]."
        )
        missing_context = [
            "actual feature or workflow",
            "actual framework",
            "actual database",
            "real metric or actual outcome",
        ]
        warning = WARNING

    for item in evidence_items[:max_suggestions]:
        source = item.get("id") or item.get("text") or item.get("best_cv_bullet")
        suggestions.append(
            {
                "source_evidence": [source] if source else [],
                "suggested_structure": structure,
                "warning": warning,
                "missing_context_to_confirm": list(missing_context),
                "do_not_fabricate": True,
            }
        )

    if suggestions:
        return suggestions

    if lang == "vi":
        fallback_structure = (
            "Viết lại một gạch đầu dòng CV thật theo cấu trúc: [động từ hành động] [nhiệm vụ thực tế] "
            "bằng [công cụ thực tế] cho [bối cảnh thực tế], với [kết quả thực tế] nếu bạn có thể kiểm chứng."
        )
        fallback_context = ["nhiệm vụ thực tế", "công cụ thực tế", "bối cảnh thực tế", "kết quả thực tế"]
    else:
        fallback_structure = (
            "Rewrite one real CV bullet as: [action verb] [actual task] using [actual tools] "
            "for [actual context], with [real result] if you can verify it."
        )
        fallback_context = ["actual task", "actual tools", "actual context", "real result"]

    return [
        {
            "source_evidence": [],
            "suggested_structure": fallback_structure,
            "warning": warning,
            "missing_context_to_confirm": fallback_context,
            "do_not_fabricate": True,
        }
    ]


def _cv_evidence(result: dict) -> list[dict]:
    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        return []
    out = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        if item.get("source") != "cv":
            continue
        text = item.get("best_cv_bullet") or item.get("text")
        if text:
            out.append(item)
    return out
