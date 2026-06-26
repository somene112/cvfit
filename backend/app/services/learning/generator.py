"""Deterministic learning-task generation from an analysis result.

Pure functions only — no DB access, no LLM, no network. The route layer is
responsible for ownership checks and persistence.
"""

from __future__ import annotations

from typing import Any, Optional

from app.services.i18n import resolve_language
from app.services.roadmap.learning_roadmap import build_learning_roadmap


LIMITATION_NO_CONTEXT = (
    "No completed analysis is available, so generic profile-building tasks were "
    "produced. Attach a completed analysis for skill-specific tasks. "
    "Based on current analysis only."
)
LIMITATION_LIMITED_CONTEXT = (
    "Tasks were generated from the attached analysis only. They reflect detected "
    "skill gaps and matched evidence — not a guarantee of interview outcomes. "
    "Based on current analysis only."
)
LIMITATION_NO_CONTEXT_VI = (
    "Chưa có phân tích hoàn chỉnh nào, nên các nhiệm vụ xây dựng hồ sơ tổng quát đã "
    "được tạo. Hãy đính kèm một phân tích hoàn chỉnh để có nhiệm vụ theo kỹ năng cụ thể. "
    "Dựa trên phân tích hiện tại."
)
LIMITATION_LIMITED_CONTEXT_VI = (
    "Các nhiệm vụ được tạo chỉ từ phân tích đã đính kèm. Chúng phản ánh các khoảng trống "
    "kỹ năng và bằng chứng đã phát hiện — không đảm bảo kết quả phỏng vấn. "
    "Dựa trên phân tích hiện tại."
)

# Map a derived skill to a coarse category for grouping in the UI. Best-effort
# only; unknown skills fall back to "general".
_CATEGORY_HINTS = {
    "python": "programming",
    "java": "programming",
    "javascript": "programming",
    "typescript": "programming",
    "fastapi": "backend",
    "django": "backend",
    "node": "backend",
    "sql": "database",
    "postgresql": "database",
    "mysql": "database",
    "redis": "database",
    "docker": "devops",
    "kubernetes": "devops",
    "aws": "cloud",
    "gcp": "cloud",
    "azure": "cloud",
    "react": "frontend",
    "vue": "frontend",
}


def _category_for(skill: str) -> str:
    key = (skill or "").lower()
    for name, category in _CATEGORY_HINTS.items():
        if name in key:
            return category
    return "general"


def _result_of(job: Any) -> dict:
    result = getattr(job, "result_json", None) if job is not None else None
    return result if isinstance(result, dict) else {}


def generate_learning_tasks(
    job: Optional[Any],
    *,
    max_tasks: int = 8,
    language: str = "en",
) -> tuple[list[dict], str]:
    """Return ``(task_dicts, limitations)`` derived from the analysis job.

    Each task dict carries only derived fields (skill, category, priority,
    task_type, title, description, evidence_to_add) — never raw CV/JD text.
    A safe fallback set is returned when no usable analysis context exists.

    When ``language="vi"`` the task title/description/evidence prose is
    Vietnamese; skill/tech names (proper nouns) are never translated. Default is
    English for backward compatibility.
    """
    lang = resolve_language(language)
    result = _result_of(job)
    roadmap_items = build_learning_roadmap(result, max_items=max_tasks) if result else []

    tasks: list[dict] = []
    for item in roadmap_items:
        default_skill = "kỹ năng này" if lang == "vi" else "this skill"
        skill = str(item.get("skill") or default_skill)
        priority = item.get("priority") if item.get("priority") in ("high", "medium", "low") else "medium"
        topics = item.get("topics") or []
        if lang == "vi":
            topic_hint = f" Trọng tâm: {', '.join(str(t) for t in topics[:4])}." if topics else ""
            title = f"Xây dựng bằng chứng cho {skill}"
            description = (
                f"Thực hành {skill} trong một dự án thực tế và ghi lại vai trò, "
                f"công cụ và kết quả đo lường được.{topic_hint}"
            )
            evidence_to_add = (
                "Một gạch đầu dòng ngắn, có thật mô tả dự án, vai trò của bạn và kết quả."
            )
        else:
            topic_hint = f" Focus areas: {', '.join(str(t) for t in topics[:4])}." if topics else ""
            title = f"Build evidence for {skill}"
            description = (
                f"{item.get('mini_project', f'Practice {skill} in a realistic task.')}"
                f"{topic_hint}"
            )
            evidence_to_add = item.get("cv_evidence_to_add_after_learning")
        tasks.append(
            {
                "skill": skill,
                "category": _category_for(skill),
                "priority": priority,
                "task_type": "project",
                "title": title,
                "description": description,
                "evidence_to_add": evidence_to_add,
            }
        )

    if not tasks:
        # No usable analysis context — safe, honest fallback tasks.
        if lang == "vi":
            fallback_skills = ["kể chuyện phỏng vấn", "bằng chứng hồ sơ năng lực"]
            for skill in fallback_skills[:max_tasks]:
                tasks.append(
                    {
                        "skill": skill,
                        "category": "general",
                        "priority": "medium",
                        "task_type": "profile_evidence",
                        "title": f"Củng cố {skill}",
                        "description": (
                            "Thêm một ví dụ cụ thể, có thật từ kinh nghiệm của bạn vào hồ sơ năng lực "
                            "để các phân tích sau có bằng chứng mạnh hơn để làm việc."
                        ),
                        "evidence_to_add": (
                            "Một gạch đầu dòng ngắn, kiểm chứng được mô tả dự án thật, vai trò và kết quả."
                        ),
                    }
                )
            return tasks, LIMITATION_NO_CONTEXT_VI

        fallback_skills = ["interview storytelling", "career profile evidence"]
        for skill in fallback_skills[:max_tasks]:
            tasks.append(
                {
                    "skill": skill,
                    "category": "general",
                    "priority": "medium",
                    "task_type": "profile_evidence",
                    "title": f"Strengthen {skill}",
                    "description": (
                        "Add a concrete, truthful example from your real experience to your "
                        "career profile so future analyses have stronger evidence to work with."
                    ),
                    "evidence_to_add": (
                        "A short, verifiable bullet describing a real project, your role, and the outcome."
                    ),
                }
            )
        return tasks, LIMITATION_NO_CONTEXT

    return tasks, LIMITATION_LIMITED_CONTEXT_VI if lang == "vi" else LIMITATION_LIMITED_CONTEXT
