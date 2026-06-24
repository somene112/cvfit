"""Admin Monitoring MVP services.

Read-only, aggregate-only system metrics for an operator dashboard. These
helpers never read or return raw user content (CV/JD/answer text), provider
secrets, tokens, checkout URLs, signatures, or webhook payloads — only counts,
sums, status breakdowns, feature flags, and masked identifiers.
"""

from app.services.admin.metrics import (
    build_overview,
    build_recent_activity,
    detect_alembic_head,
    mask_user_id,
)

__all__ = [
    "build_overview",
    "build_recent_activity",
    "detect_alembic_head",
    "mask_user_id",
]
