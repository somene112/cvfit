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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings
from app.db.models import (
    AnalysisJob,
    Application,
    ApplicationArtifact,
    InterviewSession,
    InterviewSessionAnswer,
    LearningTask,
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


def _distinct_users(rows: list) -> int:
    """Count distinct non-null user_ids across the rows."""
    return len({uid for r in rows if (uid := getattr(r, "user_id", None)) is not None})


def _filter_status(rows: list, statuses: set[str]) -> list:
    return [r for r in rows if getattr(r, "status", None) in statuses]


def _count_artifacts(rows: list, artifact_type: str) -> int:
    return sum(1 for r in rows if getattr(r, "artifact_type", None) == artifact_type)


def _pct(numerator: float, denominator: float) -> Optional[float]:
    """Percentage to 1 decimal, or None when the denominator is zero."""
    if not denominator:
        return None
    return round((numerator / denominator) * 100, 1)


def _avg(numerator: float, denominator: float) -> Optional[float]:
    """Mean to 2 decimals, or None when the denominator is zero."""
    if not denominator:
        return None
    return round(numerator / denominator, 2)


def _created_ats(rows: list) -> list[datetime]:
    """Collect the non-null ``created_at`` datetimes from the rows."""
    out: list[datetime] = []
    for r in rows:
        value = getattr(r, "created_at", None)
        if isinstance(value, datetime):
            out.append(value)
    return out


def _count_since(created_ats: list[datetime], cutoff: datetime) -> int:
    return sum(1 for c in created_ats if c >= cutoff)


def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() + "Z" if isinstance(value, datetime) else None


def _max_or_none(values: list[datetime]) -> Optional[datetime]:
    return max(values) if values else None


def _min_or_none(values: list[datetime]) -> Optional[datetime]:
    return min(values) if values else None


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
    """Assemble the safe aggregate overview payload (Analytics v2).

    Existing v1 sections (users/analysis_jobs/applications/interviews/billing/
    usage/flags) are preserved verbatim for backward compatibility. New v2
    sections (product_funnel/conversion_rates/activity_timeline/analysis_health/
    engagement_depth/billing_readiness) are additive and aggregate-only.
    """
    now = datetime.utcnow()
    cutoff_7 = now - timedelta(days=7)
    cutoff_30 = now - timedelta(days=30)

    users = _rows(db, User)
    jobs = _rows(db, AnalysisJob)
    applications = _rows(db, Application)
    interview_sessions = _rows(db, InterviewSession)
    interview_answers = _rows(db, InterviewSessionAnswer)
    artifacts = _rows(db, ApplicationArtifact)
    learning_tasks = _rows(db, LearningTask)
    orders = _rows(db, PaymentOrder)
    entitlements = _rows(db, UserEntitlement)
    usage_events = _rows(db, UsageEvent)

    target_job_rows = _filter_status(applications, _TARGET_JOB_STATUSES)
    paid_orders = [o for o in orders if getattr(o, "status", None) == "paid"]

    orders_by_status = _count_by(orders, "status")
    jobs_by_status = _count_by(jobs, "status")
    paid_revenue_vnd = sum(int(getattr(o, "amount_vnd", 0) or 0) for o in paid_orders)

    total_users = len(users)
    users_with_analysis = _distinct_users(jobs)
    users_with_application = _distinct_users(applications)
    users_with_interview_session = _distinct_users(interview_sessions)
    users_with_target_job = _distinct_users(target_job_rows)
    users_with_paid_order = _distinct_users(paid_orders)

    analysis_jobs_total = len(jobs)
    applications_total = len(applications)
    cover_letters_total = _count_artifacts(artifacts, "cover_letter_draft")
    packages_total = _count_artifacts(artifacts, "application_package")
    interview_sessions_total = len(interview_sessions)
    interview_answers_total = len(interview_answers)
    learning_tasks_total = len(learning_tasks)

    succeeded = jobs_by_status.get("succeeded", 0)
    failed = jobs_by_status.get("failed", 0)
    pending = jobs_by_status.get("queued", 0)
    running = jobs_by_status.get("running", 0)

    # Created-at series (timeline + recency). Rows without a timestamp are skipped.
    user_dates = _created_ats(users)
    job_dates = _created_ats(jobs)
    application_dates = _created_ats(applications)
    session_dates = _created_ats(interview_sessions)
    target_job_dates = _created_ats(target_job_rows)
    usage_dates = _created_ats(usage_events)

    latest_user = _max_or_none(user_dates)
    latest_analysis = _max_or_none(job_dates)
    latest_application = _max_or_none(application_dates)
    latest_session = _max_or_none(session_dates)
    latest_activity = _max_or_none(
        [d for d in (latest_user, latest_analysis, latest_application, latest_session) if d is not None]
    )

    return {
        # --- v1 sections (unchanged for backward compatibility) ---
        "users": {
            "total_users": total_users,
            "active_users": sum(1 for u in users if getattr(u, "is_active", False)),
            "verified_users": sum(1 for u in users if getattr(u, "email_verified", False)),
        },
        "analysis_jobs": {
            "analysis_jobs_total": analysis_jobs_total,
            "analysis_jobs_by_status": jobs_by_status,
        },
        "applications": {
            "applications_total": applications_total,
            "target_jobs_total": len(target_job_rows),
        },
        "interviews": {
            "interview_sessions_total": interview_sessions_total,
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
        # --- v2 sections (additive) ---
        "product_funnel": {
            "total_users": total_users,
            "users_with_analysis": users_with_analysis,
            "users_with_application": users_with_application,
            "users_with_interview_session": users_with_interview_session,
            "users_with_target_job": users_with_target_job,
            "users_with_paid_order": users_with_paid_order,
            "analysis_jobs_total": analysis_jobs_total,
            "applications_total": applications_total,
            "cover_letters_total": cover_letters_total,
            "packages_total": packages_total,
            "interview_sessions_total": interview_sessions_total,
            "interview_answers_total": interview_answers_total,
            "learning_tasks_total": learning_tasks_total,
        },
        "conversion_rates": {
            "analysis_per_user_rate": _pct(users_with_analysis, total_users),
            "application_per_analysis_user_rate": _pct(users_with_application, users_with_analysis),
            "interview_per_application_user_rate": _pct(users_with_interview_session, users_with_application),
            "application_per_analysis_job_rate": _pct(applications_total, analysis_jobs_total),
        },
        "activity_timeline": {
            "last_7_days": {
                "new_users": _count_since(user_dates, cutoff_7),
                "analysis_jobs_created": _count_since(job_dates, cutoff_7),
                "applications_created": _count_since(application_dates, cutoff_7),
                "interview_sessions_created": _count_since(session_dates, cutoff_7),
                "target_jobs_created": _count_since(target_job_dates, cutoff_7),
                "usage_events_created": _count_since(usage_dates, cutoff_7),
            },
            "last_30_days": {
                "new_users": _count_since(user_dates, cutoff_30),
                "analysis_jobs_created": _count_since(job_dates, cutoff_30),
                "applications_created": _count_since(application_dates, cutoff_30),
                "interview_sessions_created": _count_since(session_dates, cutoff_30),
                "target_jobs_created": _count_since(target_job_dates, cutoff_30),
                "usage_events_created": _count_since(usage_dates, cutoff_30),
            },
            "first_user_created_at": _iso(_min_or_none(user_dates)),
            "latest_user_created_at": _iso(latest_user),
            "first_analysis_created_at": _iso(_min_or_none(job_dates)),
            "latest_analysis_created_at": _iso(latest_analysis),
            "latest_application_created_at": _iso(latest_application),
            "latest_interview_session_created_at": _iso(latest_session),
            "latest_activity_at": _iso(latest_activity),
        },
        "analysis_health": {
            "total": analysis_jobs_total,
            "succeeded": succeeded,
            "failed": failed,
            "pending": pending,
            "running": running,
            "success_rate": _pct(succeeded, analysis_jobs_total),
            "failure_rate": _pct(failed, analysis_jobs_total),
        },
        "engagement_depth": {
            "average_analysis_jobs_per_user": _avg(analysis_jobs_total, total_users),
            "average_analysis_jobs_per_active_analysis_user": _avg(analysis_jobs_total, users_with_analysis),
            "average_applications_per_user": _avg(applications_total, total_users),
            "average_interview_sessions_per_user": _avg(interview_sessions_total, total_users),
            "average_interview_answers_per_session": _avg(interview_answers_total, interview_sessions_total),
        },
        "billing_readiness": {
            "billing_enabled": bool(settings.ENABLE_BILLING),
            "billing_status_label": "Đang bật" if settings.ENABLE_BILLING else "Chưa bật",
            "payment_orders_total": len(orders),
            "paid_orders_total": len(paid_orders),
            "paid_revenue_vnd": paid_revenue_vnd,
            "manual_review_orders_total": orders_by_status.get("manual_review", 0),
            "billing_orders_by_status": orders_by_status,
        },
        "expected_alembic_head": detect_alembic_head(),
        "generated_at": now.isoformat() + "Z",
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
