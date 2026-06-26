from __future__ import annotations

from typing import Any

from app.services.i18n import resolve_language


# Per-skill topic hints. Keep framework/tool terms unchanged; only the generic
# fallback topics are localized (the skill-specific lists are technical terms).
TOPIC_MAP = {
    "python": ["Core syntax review", "Data structures", "Backend project practice"],
    "fastapi": ["Routing", "Pydantic models", "Dependency injection", "Error handling"],
    "postgresql": ["SQL joins", "Indexes", "Transactions", "Schema design"],
    "redis": ["Caching basics", "Key expiry", "Cache invalidation"],
    "docker": ["Dockerfile basics", "Compose services", "Image build and run workflow"],
    "kubernetes": ["Pods and deployments", "Services", "Rollouts", "Application logs"],
    "aws": ["IAM basics", "Compute service basics", "Deployment and monitoring overview"],
}

_DEFAULT_TOPICS_EN = ["Core concepts", "Hands-on practice", "Project documentation", "Interview explanation practice"]
_DEFAULT_TOPICS_VI = ["Khái niệm cốt lõi", "Thực hành trực tiếp", "Tài liệu dự án", "Luyện giải thích khi phỏng vấn"]


def build_learning_roadmap(result: dict, *, max_items: int = 6, language: str = "en") -> list[dict]:
    lang = resolve_language(language)
    items: list[dict] = []
    for missing in _missing_skills(result)[:max_items]:
        skill = _safe_label(missing.get("skill") or ("kỹ năng này" if lang == "vi" else "this skill"))
        priority = "high" if missing.get("requirement_type") == "must_have" else "medium"
        topics = _topics_for(skill, lang)
        if lang == "vi":
            why = f"Mô tả công việc có đề cập đến {skill}, nhưng không tìm thấy bằng chứng về {skill} trong CV đã phân tích."
            mini_project = (
                f"Xây dựng một dự án nhỏ sử dụng {skill} trong quy trình thực tế và ghi lại những gì bạn đã làm."
            )
            estimated_effort = "1-2 tuần" if priority == "medium" else "2-4 tuần"
            cv_evidence = (
                f"Sau khi hoàn thành dự án, thêm một gạch đầu dòng CV trung thực mô tả nhiệm vụ {skill}, "
                "vai trò của bạn, công cụ đã dùng và kết quả thực tế."
            )
        else:
            why = f"The JD mentions {skill}, but {skill} evidence was not found in the parsed CV."
            mini_project = (
                f"Build a small project that uses {skill} in a realistic workflow and document what you did."
            )
            estimated_effort = "1-2 weeks" if priority == "medium" else "2-4 weeks"
            cv_evidence = (
                f"After completing the project, add a truthful CV bullet describing the {skill} task, "
                "your role, tools used, and actual outcome."
            )
        items.append(
            {
                "skill": skill,
                "priority": priority,
                "why": why,
                "topics": topics,
                "mini_project": mini_project,
                "estimated_effort": estimated_effort,
                "cv_evidence_to_add_after_learning": cv_evidence,
                "do_not_claim_until_completed": True,
            }
        )
    return items


def _missing_skills(result: dict) -> list[dict]:
    missing = result.get("missing_skills")
    if isinstance(missing, list):
        return [item for item in missing if isinstance(item, dict)]
    return []


def _topics_for(skill: str, lang: str = "en") -> list[str]:
    key = skill.lower()
    for name, topics in TOPIC_MAP.items():
        if name in key:
            return topics
    return list(_DEFAULT_TOPICS_VI if lang == "vi" else _DEFAULT_TOPICS_EN)


def _safe_label(value: Any) -> str:
    text = str(value or "").strip()
    return text[:120] if text else "this skill"
