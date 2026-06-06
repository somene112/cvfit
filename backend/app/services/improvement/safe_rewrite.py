from __future__ import annotations

from typing import Any


WARNING = "Only use details that are true and can be defended in an interview."


def build_safe_rewrite_suggestions(result: dict, *, max_suggestions: int = 4) -> list[dict]:
    evidence_items = _cv_evidence(result)
    suggestions: list[dict] = []

    for item in evidence_items[:max_suggestions]:
        source = item.get("id") or item.get("text") or item.get("best_cv_bullet")
        suggestions.append(
            {
                "source_evidence": [source] if source else [],
                "suggested_structure": (
                    "Built [actual feature or workflow] using [actual framework] and [actual database] "
                    "to support [actual user or business need], resulting in [real metric or actual outcome]."
                ),
                "warning": WARNING,
                "missing_context_to_confirm": [
                    "actual feature or workflow",
                    "actual framework",
                    "actual database",
                    "real metric or actual outcome",
                ],
                "do_not_fabricate": True,
            }
        )

    if suggestions:
        return suggestions

    return [
        {
            "source_evidence": [],
            "suggested_structure": (
                "Rewrite one real CV bullet as: [action verb] [actual task] using [actual tools] "
                "for [actual context], with [real result] if you can verify it."
            ),
            "warning": WARNING,
            "missing_context_to_confirm": [
                "actual task",
                "actual tools",
                "actual context",
                "real result",
            ],
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
