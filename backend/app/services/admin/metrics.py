"""Aggregate, privacy-safe metrics for the Admin Monitoring MVP.

Design constraints (all enforced here, verified by tests):

* Read-only. No function mutates any row.
* Aggregate-only. We return counts, sums, and status/type breakdowns — never
  raw CV/JD text, interview answers, generated documents, emails, tokens,
  checkout URLs, payment signatures, or webhook payloads.
* MVP-scale. Counts are computed in Python over ``query(...).all()`` so the
  same code path works against the production Session and the lightweight
  in-memory fake used by the unit tests. At demo scale this is fine; if the
  data set grows, swap these for SQL ``func.count``/``func.sum`` aggregates.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings
from app.db.models import (
    AnalysisJob,
    Application,
    InterviewSession,
    PaymentOrder,
    User,
    UsageEvent,
    UserEntitlement,
)

# Application rows whose status belongs to the Phase 6 "target job" workflow.
# Applications and target jobs share one table, so this is a best-effort split
# for the monitoring view, not an authoritative classification.
_TARGET_JOB_STATUSES = {"saved", "interviewing", "rejected", "offer"}


def _rows(db: Any, model: Any) -> list:
    """Return all rows for ``model`` or an empty list on any query error.

    A monitoring endpoint should degrade gracefully rather than 500 if one
    table is unavailable.
    """
    try:
        return list(db.query(model).all())
    except Exception:  # pragma: no cover - defensive; never leak the error body
        return []


def _count_by(rows: list, attr: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        key = getattr(row, attr, None)
        key = str(key) if key is not None else "unknown"
        out[key] = out.get(key, 0) + 1
    return out


def mask_user_id(value: Any) -> str:
    """Mask a user id to a short, non-reversible-looking prefix.

    Never returns an email or the full id — just enough to eyeball distinct
    actors in a recent-activity list without exposing identity.
    """
    text = str(value or "")
    if not text:
        return "unknown"
    return f"{text[:8]}…"


def build_overview(db: Any) -> dict:
    """Assemble the safe aggregate overview payload."""
    users = _rows(db, User)
    jobs = _rows(db, AnalysisJob)
    applications = _rows(db, Application)
    interview_sessions = _rows(db, InterviewSession)
    orders = _rows(db, PaymentOrder)
    entitlements = _rows(db, UserEntitlement)
    usage_events = _rows(db, UsageEvent)

    orders_by_status = _count_by(orders, "status")
    paid_orders = [o for o in orders if getattr(o, "status", None) == "paid"]
    paid_revenue_vnd = sum(int(getattr(o, "amount_vnd", 0) or 0) for o in paid_orders)

    return {
        "users": {
            "total_users": len(users),
            "active_users": sum(1 for u in users if getattr(u, "is_active", False)),
            "verified_users": sum(1 for u in users if getattr(u, "email_verified", False)),
        },
        "analysis_jobs": {
            "analysis_jobs_total": len(jobs),
            "analysis_jobs_by_status": _count_by(jobs, "status"),
        },
        "applications": {
            "applications_total": len(applications),
            "target_jobs_total": sum(
                1 for a in applications if getattr(a, "status", None) in _TARGET_JOB_STATUSES
            ),
        },
        "interviews": {
            "interview_sessions_total": len(interview_sessions),
        },
        "billing": {
            "billing_orders_total": len(orders),
            "billing_orders_by_status": orders_by_status,
            "paid_orders_total": len(paid_orders),
            "paid_revenue_vnd": paid_revenue_vnd,
            "manual_review_orders_total": orders_by_status.get("manual_review", 0),
            "user_entitlements_total": len(entitlements),
        },
        "usage": {
            "usage_events_total": len(usage_events),
            "usage_events_by_type": _count_by(usage_events, "event_type"),
        },
        "flags": {
            "ENABLE_BILLING": bool(settings.ENABLE_BILLING),
            "ENABLE_CREDIT_GATING": bool(settings.ENABLE_CREDIT_GATING),
            "ENABLE_PHASE6_SHARE_LINKS": bool(settings.ENABLE_PHASE6_SHARE_LINKS),
        },
        "expected_alembic_head": detect_alembic_head(),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def build_recent_activity(db: Any, limit: int = 20) -> list[dict]:
    """Recent usage events as safe metadata only.

    Usage events structurally cannot contain raw CV/JD/answer text — they hold
    an event type, a spend source, timestamps, and ids. We still mask the user
    id and omit related object ids to avoid correlation.
    """
    events = _rows(db, UsageEvent)
    try:
        events = sorted(
            events,
            key=lambda e: getattr(e, "created_at", None) or datetime.min,
            reverse=True,
        )
    except Exception:  # pragma: no cover - defensive
        pass

    items: list[dict] = []
    for event in events[: max(0, int(limit))]:
        created = getattr(event, "created_at", None)
        items.append(
            {
                "type": str(getattr(event, "event_type", "") or "unknown"),
                "status": str(getattr(event, "source", "") or "n/a"),
                "user_ref": mask_user_id(getattr(event, "user_id", None)),
                "created_at": created.isoformat() if isinstance(created, datetime) else None,
            }
        )
    return items


_REVISION_RE = re.compile(r"""^revision\s*=\s*["']([^"']+)["']""", re.MULTILINE)
_DOWN_REVISION_RE = re.compile(r"""^down_revision\s*=\s*["']([^"']+)["']""", re.MULTILINE)


def detect_alembic_head() -> Optional[str]:
    """Best-effort: the single migration revision that nothing revises from.

    Parsed from the alembic versions directory in the repo. Returns ``None`` if
    the directory is missing or the head is ambiguous, so the endpoint never
    fails just because migration files cannot be read.
    """
    try:
        versions_dir = Path(__file__).resolve().parents[3] / "alembic" / "versions"
        if not versions_dir.is_dir():
            return None
        revisions: set[str] = set()
        down_revisions: set[str] = set()
        for path in versions_dir.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            rev = _REVISION_RE.search(text)
            if rev:
                revisions.add(rev.group(1))
            down = _DOWN_REVISION_RE.search(text)
            if down:
                down_revisions.add(down.group(1))
        heads = revisions - down_revisions
        if len(heads) == 1:
            return next(iter(heads))
        return None
    except Exception:  # pragma: no cover - defensive
        return None
