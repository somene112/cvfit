"""Computed usage counters and the static free-demo plan.

All counts are derived from existing per-user records. Counting never reads or
returns raw CV/JD/answer text — only integer counts.
"""

from __future__ import annotations

import uuid
from typing import Any


# Informational demo limits only. enforcement_enabled is always False.
DEMO_LIMITS = {
    "analyses": 5,
    "applications": 20,
    "learning_tasks": 100,
    "interview_sessions": 10,
    "interview_answers": 50,
    "cover_letters": 10,
    "application_packages": 10,
    "share_links": 10,
}

FREE_DEMO_PLAN = {
    "id": "free_demo",
    "name": "Free Demo",
    "price": "Free (demo)",
    "features": [
        "Target Jobs workspace",
        "Learning roadmap generation",
        "Interview practice v2",
        "Guided help assistant",
        "Readiness summaries",
    ],
}

WARNING_THRESHOLD = 0.8


def _count(db: Any, model: Any, user_id: uuid.UUID, **extra_eq: Any) -> int:
    query = db.query(model).filter(model.user_id == user_id)
    for attr, value in extra_eq.items():
        query = query.filter(getattr(model, attr) == value)
    return len(query.all())


def compute_usage(db: Any, user_id: uuid.UUID) -> dict[str, int]:
    """Return integer usage counts for the user across Phase 5/6 records."""
    # Imported here to avoid any import cycle at module load.
    from app.db.models import (
        AnalysisJob,
        Application,
        ApplicationArtifact,
        InterviewSession,
        InterviewSessionAnswer,
        LearningTask,
        ShareLink,
    )

    sessions = db.query(InterviewSession).filter(InterviewSession.user_id == user_id).all()
    session_ids = {s.id for s in sessions}
    all_answers = db.query(InterviewSessionAnswer).all()
    interview_answers = sum(1 for a in all_answers if a.session_id in session_ids)

    return {
        "analyses": _count(db, AnalysisJob, user_id),
        "applications": _count(db, Application, user_id),
        "learning_tasks": _count(db, LearningTask, user_id),
        "interview_sessions": len(sessions),
        "interview_answers": interview_answers,
        "cover_letters": _count(db, ApplicationArtifact, user_id, artifact_type="cover_letter_draft"),
        "application_packages": _count(db, ApplicationArtifact, user_id, artifact_type="application_package"),
        "share_links": _count(db, ShareLink, user_id),
    }


def compute_warnings(usage: dict[str, int], limits: dict[str, int]) -> list[str]:
    """Informational soft warnings only — nothing is enforced or blocked."""
    warnings: list[str] = []
    for key, used in usage.items():
        limit = limits.get(key)
        if limit and used >= limit * WARNING_THRESHOLD:
            warnings.append(
                f"You have used {used} of {limit} {key.replace('_', ' ')} on the free demo (informational only)."
            )
    return warnings


def build_plans() -> list[dict]:
    """Return the plan list — free demo only, marked current. No checkout."""
    return [
        {
            "id": FREE_DEMO_PLAN["id"],
            "name": FREE_DEMO_PLAN["name"],
            "price": FREE_DEMO_PLAN["price"],
            "features": list(FREE_DEMO_PLAN["features"]),
            "current": True,
        }
    ]
