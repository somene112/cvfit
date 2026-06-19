"""Phase 6 Usage / Plan shell service layer.

Read-only and deterministic. Usage is computed from existing records; no
usage_events table is introduced. No payment, checkout, or enforcement.
"""

from app.services.usage.counters import (
    DEMO_LIMITS,
    FREE_DEMO_PLAN,
    build_plans,
    compute_usage,
    compute_warnings,
)

__all__ = [
    "compute_usage",
    "compute_warnings",
    "build_plans",
    "DEMO_LIMITS",
    "FREE_DEMO_PLAN",
]
