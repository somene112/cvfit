from __future__ import annotations

from typing import Any


TOPIC_MAP = {
    "python": ["Core syntax review", "Data structures", "Backend project practice"],
    "fastapi": ["Routing", "Pydantic models", "Dependency injection", "Error handling"],
    "postgresql": ["SQL joins", "Indexes", "Transactions", "Schema design"],
    "redis": ["Caching basics", "Key expiry", "Cache invalidation"],
    "docker": ["Dockerfile basics", "Compose services", "Image build and run workflow"],
    "kubernetes": ["Pods and deployments", "Services", "Rollouts", "Application logs"],
    "aws": ["IAM basics", "Compute service basics", "Deployment and monitoring overview"],
}


def build_learning_roadmap(result: dict, *, max_items: int = 6) -> list[dict]:
    items: list[dict] = []
    for missing in _missing_skills(result)[:max_items]:
        skill = _safe_label(missing.get("skill") or "this skill")
        priority = "high" if missing.get("requirement_type") == "must_have" else "medium"
        topics = _topics_for(skill)
        items.append(
            {
                "skill": skill,
                "priority": priority,
                "why": f"The JD mentions {skill}, but {skill} evidence was not found in the parsed CV.",
                "topics": topics,
                "mini_project": (
                    f"Build a small project that uses {skill} in a realistic workflow and document what you did."
                ),
                "estimated_effort": "1-2 weeks" if priority == "medium" else "2-4 weeks",
                "cv_evidence_to_add_after_learning": (
                    f"After completing the project, add a truthful CV bullet describing the {skill} task, "
                    "your role, tools used, and actual outcome."
                ),
                "do_not_claim_until_completed": True,
            }
        )
    return items


def _missing_skills(result: dict) -> list[dict]:
    missing = result.get("missing_skills")
    if isinstance(missing, list):
        return [item for item in missing if isinstance(item, dict)]
    return []


def _topics_for(skill: str) -> list[str]:
    key = skill.lower()
    for name, topics in TOPIC_MAP.items():
        if name in key:
            return topics
    return ["Core concepts", "Hands-on practice", "Project documentation", "Interview explanation practice"]


def _safe_label(value: Any) -> str:
    text = str(value or "").strip()
    return text[:120] if text else "this skill"
