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


# --- Analytics v2 (additive) ---


class ProductFunnel(BaseModel):
    total_users: int
    users_with_analysis: int
    users_with_application: int
    users_with_interview_session: int
    users_with_target_job: int
    users_with_paid_order: int
    analysis_jobs_total: int
    applications_total: int
    cover_letters_total: int
    packages_total: int
    interview_sessions_total: int
    interview_answers_total: int
    learning_tasks_total: int


class ConversionRates(BaseModel):
    # Percentages (0-100, 1 decimal). None when the denominator is zero.
    analysis_per_user_rate: Optional[float] = None
    application_per_analysis_user_rate: Optional[float] = None
    interview_per_application_user_rate: Optional[float] = None
    application_per_analysis_job_rate: Optional[float] = None


class ActivityWindow(BaseModel):
    new_users: int
    analysis_jobs_created: int
    applications_created: int
    interview_sessions_created: int
    target_jobs_created: int
    usage_events_created: int


class ActivityTimeline(BaseModel):
    last_7_days: ActivityWindow
    last_30_days: ActivityWindow
    first_user_created_at: Optional[str] = None
    latest_user_created_at: Optional[str] = None
    first_analysis_created_at: Optional[str] = None
    latest_analysis_created_at: Optional[str] = None
    latest_application_created_at: Optional[str] = None
    latest_interview_session_created_at: Optional[str] = None
    latest_activity_at: Optional[str] = None


class AnalysisHealth(BaseModel):
    total: int
    succeeded: int
    failed: int
    pending: int
    running: int
    success_rate: Optional[float] = None
    failure_rate: Optional[float] = None


class EngagementDepth(BaseModel):
    average_analysis_jobs_per_user: Optional[float] = None
    average_analysis_jobs_per_active_analysis_user: Optional[float] = None
    average_applications_per_user: Optional[float] = None
    average_interview_sessions_per_user: Optional[float] = None
    average_interview_answers_per_session: Optional[float] = None


class BillingReadiness(BaseModel):
    billing_enabled: bool
    billing_status_label: str
    payment_orders_total: int
    paid_orders_total: int
    paid_revenue_vnd: int
    manual_review_orders_total: int
    billing_orders_by_status: Dict[str, int]


class AdminOverviewResponse(BaseModel):
    users: UsersMetrics
    analysis_jobs: AnalysisJobsMetrics
    applications: ApplicationsMetrics
    interviews: InterviewsMetrics
    billing: BillingMetrics
    usage: UsageMetrics
    flags: FeatureFlags
    # Analytics v2 sections (additive).
    product_funnel: ProductFunnel
    conversion_rates: ConversionRates
    activity_timeline: ActivityTimeline
    analysis_health: AnalysisHealth
    engagement_depth: EngagementDepth
    billing_readiness: BillingReadiness
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
