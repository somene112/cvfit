"""Phase 6 Target Jobs service layer.

Target Jobs reuse the Phase 5 ``applications`` table and the existing analysis
result structure. This package holds the small amount of derived logic (readiness
computation) shared between the attach-analysis and readiness endpoints so the
route module stays thin.
"""

from app.services.target_jobs.readiness import compute_readiness

__all__ = ["compute_readiness"]
