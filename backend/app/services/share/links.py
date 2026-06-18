"""Share-link token and redacted public-view helpers.

Mirrors the existing access-token pattern in ``app/api/routes/jobs.py``:
``secrets.token_urlsafe`` for generation, SHA-256 hex for the stored hash, and
``hmac.compare_digest`` for constant-time comparison. The raw token is never
stored or logged.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Any, Optional


DEFAULT_VISIBILITY = {
    "summary_only": True,
    "include_score_breakdown": False,
    "include_package": False,
    "include_cover_letter": False,
    "include_learning_roadmap": False,
    "hide_raw_cv": True,
    "hide_raw_jd": True,
}


def generate_share_token() -> str:
    """Return a high-entropy URL-safe raw token (not persisted)."""
    return secrets.token_urlsafe(32)


def hash_share_token(token: str) -> str:
    """Return the SHA-256 hex digest stored in ``share_links.token_hash``."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_match(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_share_token(token), token_hash)


def is_link_active(link: Any, *, now: Optional[datetime] = None) -> bool:
    """A link is active if not revoked and not expired."""
    now = now or datetime.utcnow()
    if getattr(link, "revoked_at", None) is not None:
        return False
    expires_at = getattr(link, "expires_at", None)
    if expires_at is not None and expires_at <= now:
        return False
    return True


def _learning_focus(analysis_job: Any, limit: int = 5) -> list[str]:
    result = getattr(analysis_job, "result_json", None) if analysis_job else None
    if not isinstance(result, dict):
        return []
    out: list[str] = []
    raw = result.get("missing_skills")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("skill"):
                out.append(str(item["skill"]))
            elif isinstance(item, str):
                out.append(item)
    return out[:limit]


def build_public_view(
    link: Any,
    application: Any,
    analysis_job: Any,
    readiness: Any,
) -> dict:
    """Assemble the redacted public payload honoring the link's visibility flags.

    Raw CV/JD text is never included. Score/learning details appear only when the
    corresponding visibility flag is set. ``readiness`` is a ReadinessResult.
    """
    visibility = getattr(link, "visibility_json", None) or DEFAULT_VISIBILITY

    view: dict = {
        "target_type": getattr(link, "target_type", "target_job"),
        "job_title": getattr(application, "job_title", "Shared role"),
        "company_name": getattr(application, "company_name", None),
        "readiness_level": getattr(readiness, "readiness_level", "not_started"),
        "summary": getattr(readiness, "summary", "Readiness summary is not available yet."),
        "fit_score": None,
        "score_breakdown": None,
        "learning_focus": None,
    }

    if visibility.get("include_score_breakdown"):
        fit = getattr(readiness, "fit_score", None)
        if fit is not None:
            view["fit_score"] = int(round(fit))
            view["score_breakdown"] = {
                "fit_score": int(round(fit)),
                "readiness_level": view["readiness_level"],
            }

    if visibility.get("include_learning_roadmap"):
        view["learning_focus"] = _learning_focus(analysis_job)

    return view
