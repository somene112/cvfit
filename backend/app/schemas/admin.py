"""Admin Monitoring MVP schemas — aggregate, privacy-safe responses only.

None of these models carry raw user content, emails (other than the admin's own
in ``/me``), tokens, secrets, checkout URLs, signatures, or webhook payloads.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class AdminMeResponse(BaseModel):
    is_admin: bool
    email: str


class UsersMetrics(BaseModel):
    total_users: int
    active_users: int
    verified_users: int


class AnalysisJobsMetrics(BaseModel):
    analysis_jobs_total: int
    analysis_jobs_by_status: Dict[str, int]


class ApplicationsMetrics(BaseModel):
    applications_total: int
    target_jobs_total: int


class InterviewsMetrics(BaseModel):
    interview_sessions_total: int


class BillingMetrics(BaseModel):
    billing_orders_total: int
    billing_orders_by_status: Dict[str, int]
    paid_orders_total: int
    paid_revenue_vnd: int
    manual_review_orders_total: int
    user_entitlements_total: int


class UsageMetrics(BaseModel):
    usage_events_total: int
    usage_events_by_type: Dict[str, int]


class FeatureFlags(BaseModel):
    ENABLE_BILLING: bool
    ENABLE_CREDIT_GATING: bool
    ENABLE_PHASE6_SHARE_LINKS: bool


class AdminOverviewResponse(BaseModel):
    users: UsersMetrics
    analysis_jobs: AnalysisJobsMetrics
    applications: ApplicationsMetrics
    interviews: InterviewsMetrics
    billing: BillingMetrics
    usage: UsageMetrics
    flags: FeatureFlags
    expected_alembic_head: Optional[str] = None
    generated_at: str


class RecentActivityItem(BaseModel):
    type: str
    status: str
    user_ref: str
    created_at: Optional[str] = None


class RecentActivityResponse(BaseModel):
    items: List[RecentActivityItem]
    total: int
