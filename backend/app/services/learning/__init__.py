"""Phase 6 Learning Roadmap service layer.

Generates learning tasks deterministically from a user's own analysis result.
Reuses the Phase 5 ``build_learning_roadmap`` deriver and normalizes its output
into persistable task rows. No external/course-marketplace data, no paid APIs,
and no raw CV/JD text is stored — only derived skills, titles, and descriptions.
"""

from app.services.learning.generator import (
    LIMITATION_LIMITED_CONTEXT,
    LIMITATION_NO_CONTEXT,
    generate_learning_tasks,
)

__all__ = [
    "generate_learning_tasks",
    "LIMITATION_LIMITED_CONTEXT",
    "LIMITATION_NO_CONTEXT",
]
