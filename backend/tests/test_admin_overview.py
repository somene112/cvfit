"""Admin Monitoring MVP tests — authorization, aggregates, and privacy.

Verifies that:
* unauthenticated → 401, authenticated non-admin → 403, admin (email in
  ADMIN_EMAILS) → 200;
* the overview returns safe aggregate metrics with correct counts/sums;
* responses never leak raw CV/JD/answer text, checkout URLs, provider payloads,
  signatures, tokens, or emails (other than the admin's own in ``/me``);
* the routes do not mutate data.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.admin import router
from app.core import config as config_module
from app.db.models import (
    AnalysisJob,
    Application,
    ApplicationArtifact,
    InterviewSession,
    InterviewSessionAnswer,
    LearningTask,
    PaymentOrder,
    UsageEvent,
    User,
    UserEntitlement,
)
from app.db.session import get_db


class FakeQuery:
    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return list(self._rows)


class FakeDb:
    """Minimal read store keyed by model. Tracks writes to prove no mutation."""

    def __init__(self, rows: dict[type, list] | None = None):
        self._rows = rows or {}
        self.write_calls = 0

    def query(self, model):
        return FakeQuery(self._rows.get(model, []))

    # Any of these being called would indicate a mutation attempt.
    def add(self, obj):  # pragma: no cover - must never happen
        self.write_calls += 1

    def delete(self, obj):  # pragma: no cover - must never happen
        self.write_calls += 1

    def commit(self):  # pragma: no cover - must never happen
        self.write_calls += 1


SECRET_CHECKOUT = "https://pay.example/checkout/secret-link"
SECRET_PAYLOAD = {"signature": "deadbeef", "raw": "should-never-appear"}
SECRET_CV = "RAW CV TEXT name phone secret"
SECRET_JD = "RAW JD TEXT confidential"
SECRET_COVER = "RAW COVER LETTER body should-never-appear"
SECRET_ANSWER = "RAW INTERVIEW ANSWER should-never-appear"


def _seed() -> FakeDb:
    now = datetime.utcnow()
    admin = User(id=uuid.uuid4(), email="admin@example.com", is_active=True, email_verified=True, created_at=now)
    member = User(id=uuid.uuid4(), email="member@example.com", is_active=True, email_verified=False, created_at=now)
    inactive = User(id=uuid.uuid4(), email="ghost@example.com", is_active=False, email_verified=False, created_at=now)

    jobs = [
        AnalysisJob(id=uuid.uuid4(), user_id=member.id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
                    status="succeeded", result_json={"cv_text": SECRET_CV, "jd_text": SECRET_JD}, created_at=now),
        AnalysisJob(id=uuid.uuid4(), user_id=member.id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
                    status="failed", created_at=now),
    ]
    applications = [
        Application(id=uuid.uuid4(), user_id=member.id, job_title="Dev", jd_text=SECRET_JD, status="draft", created_at=now),
        Application(id=uuid.uuid4(), user_id=member.id, job_title="ML", jd_text=SECRET_JD, status="saved", created_at=now),
        Application(id=uuid.uuid4(), user_id=member.id, job_title="BE", jd_text=SECRET_JD, status="offer", created_at=now),
    ]
    sessions = [InterviewSession(id=uuid.uuid4(), user_id=member.id, status="active", created_at=now)]
    answers = [
        InterviewSessionAnswer(id=uuid.uuid4(), session_id=sessions[0].id, question_id=uuid.uuid4(),
                               answer_text=SECRET_ANSWER, score_json={}, feedback_json={}, created_at=now),
        InterviewSessionAnswer(id=uuid.uuid4(), session_id=sessions[0].id, question_id=uuid.uuid4(),
                               answer_text=SECRET_ANSWER, score_json={}, feedback_json={}, created_at=now),
    ]
    artifacts = [
        ApplicationArtifact(id=uuid.uuid4(), user_id=member.id, application_id=applications[0].id,
                            artifact_type="cover_letter_draft", payload_json={"opening": SECRET_COVER}, created_at=now),
        ApplicationArtifact(id=uuid.uuid4(), user_id=member.id, application_id=applications[0].id,
                            artifact_type="application_package", payload_json={"disclaimer": "x"}, created_at=now),
    ]
    learning_tasks = [
        LearningTask(id=uuid.uuid4(), user_id=member.id, skill="Python", title="Học Python", status="todo", created_at=now),
        LearningTask(id=uuid.uuid4(), user_id=member.id, skill="SQL", title="Học SQL", status="done", created_at=now),
    ]
    orders = [
        PaymentOrder(id=uuid.uuid4(), user_id=member.id, provider_order_code="oc1", plan_code="p1",
                     amount_vnd=50000, status="paid", checkout_url=SECRET_CHECKOUT,
                     raw_provider_payload_json=SECRET_PAYLOAD, created_at=now),
        PaymentOrder(id=uuid.uuid4(), user_id=member.id, provider_order_code="oc2", plan_code="p1",
                     amount_vnd=30000, status="paid", checkout_url=SECRET_CHECKOUT, created_at=now),
        PaymentOrder(id=uuid.uuid4(), user_id=member.id, provider_order_code="oc3", plan_code="p2",
                     amount_vnd=99000, status="manual_review", checkout_url=SECRET_CHECKOUT, created_at=now),
    ]
    entitlements = [UserEntitlement(id=uuid.uuid4(), user_id=member.id, plan_code="p1")]
    usage_events = [
        UsageEvent(id=uuid.uuid4(), user_id=member.id, event_type="analysis", source="free_allowance", created_at=now),
        UsageEvent(id=uuid.uuid4(), user_id=member.id, event_type="interview", source="paid_credit", created_at=now),
        UsageEvent(id=uuid.uuid4(), user_id=member.id, event_type="analysis", source="paid_credit", created_at=now),
    ]
    return FakeDb({
        User: [admin, member, inactive],
        AnalysisJob: jobs,
        Application: applications,
        InterviewSession: sessions,
        InterviewSessionAnswer: answers,
        ApplicationArtifact: artifacts,
        LearningTask: learning_tasks,
        PaymentOrder: orders,
        UserEntitlement: entitlements,
        UsageEvent: usage_events,
    })


def _client(db: FakeDb, user: User | None) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def _admin_user(db: FakeDb) -> User:
    return db._rows[User][0]


def _member_user(db: FakeDb) -> User:
    return db._rows[User][1]


def _set_admins(monkeypatch, value: str) -> None:
    monkeypatch.setattr(config_module.settings, "ADMIN_EMAILS", value)


class TestAdminAuthorization:
    def test_unauthenticated_returns_401(self):
        db = _seed()
        # No get_current_user override → real auth dependency runs → 401.
        assert _client(db, None).get("/v1/admin/overview").status_code == 401

    def test_authenticated_non_admin_returns_403(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        resp = _client(db, _member_user(db)).get("/v1/admin/overview")
        assert resp.status_code == 403

    def test_empty_admin_list_means_nobody_is_admin(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "")
        assert _client(db, _admin_user(db)).get("/v1/admin/overview").status_code == 403

    def test_admin_email_is_case_insensitive(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "  ADMIN@EXAMPLE.COM ,other@x.com")
        assert _client(db, _admin_user(db)).get("/v1/admin/me").status_code == 200

    def test_admin_me_returns_identity(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        resp = _client(db, _admin_user(db)).get("/v1/admin/me")
        assert resp.status_code == 200
        assert resp.json() == {"is_admin": True, "email": "admin@example.com"}


class TestAdminOverview:
    def test_overview_aggregate_counts(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        resp = _client(db, _admin_user(db)).get("/v1/admin/overview")
        assert resp.status_code == 200
        body = resp.json()

        assert body["users"]["total_users"] == 3
        assert body["users"]["active_users"] == 2
        assert body["users"]["verified_users"] == 1
        assert body["analysis_jobs"]["analysis_jobs_total"] == 2
        assert body["analysis_jobs"]["analysis_jobs_by_status"] == {"succeeded": 1, "failed": 1}
        assert body["applications"]["applications_total"] == 3
        # "saved" + "offer" are target-job statuses; "draft" is not.
        assert body["applications"]["target_jobs_total"] == 2
        assert body["interviews"]["interview_sessions_total"] == 1
        assert body["billing"]["billing_orders_total"] == 3
        assert body["billing"]["paid_orders_total"] == 2
        assert body["billing"]["paid_revenue_vnd"] == 80000
        assert body["billing"]["manual_review_orders_total"] == 1
        assert body["billing"]["user_entitlements_total"] == 1
        assert body["usage"]["usage_events_total"] == 3
        assert body["usage"]["usage_events_by_type"] == {"analysis": 2, "interview": 1}

    def test_overview_reports_default_false_flags(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        body = _client(db, _admin_user(db)).get("/v1/admin/overview").json()
        # Hard requirement: payment/share flags stay OFF by default.
        assert body["flags"]["ENABLE_BILLING"] is False
        assert body["flags"]["ENABLE_CREDIT_GATING"] is False
        assert body["flags"]["ENABLE_PHASE6_SHARE_LINKS"] is False
        assert "generated_at" in body

    def test_overview_does_not_leak_private_content(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        raw = _client(db, _admin_user(db)).get("/v1/admin/overview").text
        for forbidden in (
            SECRET_CHECKOUT, SECRET_CV, SECRET_JD, SECRET_COVER, SECRET_ANSWER,
            "should-never-appear", "checkout_url", "raw_provider_payload",
            "signature", "deadbeef", "cv_text", "jd_text", "answer_text",
            "member@example.com", "ghost@example.com",
        ):
            assert forbidden not in raw, f"leaked: {forbidden}"

    def test_overview_does_not_mutate(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        before = {model: len(rows) for model, rows in db._rows.items()}
        _client(db, _admin_user(db)).get("/v1/admin/overview")
        after = {model: len(rows) for model, rows in db._rows.items()}
        assert before == after
        assert db.write_calls == 0


class TestRecentActivity:
    def test_recent_activity_is_masked_and_content_free(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        resp = _client(db, _admin_user(db)).get("/v1/admin/recent-activity")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == len(body["items"]) <= 20
        member_id = str(_member_user(db).id)
        for item in body["items"]:
            assert set(item.keys()) == {"type", "status", "user_ref", "created_at"}
            assert item["user_ref"].endswith("…")
            assert member_id not in item["user_ref"]
            assert "@" not in item["user_ref"]

    def test_recent_activity_requires_admin(self, monkeypatch):
        db = _seed()
        _set_admins(monkeypatch, "admin@example.com")
        assert _client(db, _member_user(db)).get("/v1/admin/recent-activity").status_code == 403


def _overview(monkeypatch, db) -> dict:
    _set_admins(monkeypatch, "admin@example.com")
    resp = _client(db, _admin_user(db)).get("/v1/admin/overview")
    assert resp.status_code == 200
    return resp.json()


class TestAnalyticsV2:
    def test_v1_sections_still_present(self, monkeypatch):
        body = _overview(monkeypatch, _seed())
        for key in ("users", "analysis_jobs", "applications", "interviews", "billing", "usage", "flags"):
            assert key in body, f"backward-compat: missing {key}"

    def test_product_funnel(self, monkeypatch):
        f = _overview(monkeypatch, _seed())["product_funnel"]
        assert f["total_users"] == 3
        assert f["users_with_analysis"] == 1
        assert f["users_with_application"] == 1
        assert f["users_with_interview_session"] == 1
        assert f["users_with_target_job"] == 1
        assert f["users_with_paid_order"] == 1
        assert f["analysis_jobs_total"] == 2
        assert f["applications_total"] == 3
        assert f["cover_letters_total"] == 1
        assert f["packages_total"] == 1
        assert f["interview_sessions_total"] == 1
        assert f["interview_answers_total"] == 2
        assert f["learning_tasks_total"] == 2

    def test_conversion_rates(self, monkeypatch):
        c = _overview(monkeypatch, _seed())["conversion_rates"]
        assert c["analysis_per_user_rate"] == 33.3
        assert c["application_per_analysis_user_rate"] == 100.0
        assert c["interview_per_application_user_rate"] == 100.0
        assert c["application_per_analysis_job_rate"] == 150.0

    def test_activity_timeline(self, monkeypatch):
        t = _overview(monkeypatch, _seed())["activity_timeline"]
        w7 = t["last_7_days"]
        assert w7["new_users"] == 3
        assert w7["analysis_jobs_created"] == 2
        assert w7["applications_created"] == 3
        assert w7["interview_sessions_created"] == 1
        assert w7["target_jobs_created"] == 2
        assert w7["usage_events_created"] == 3
        assert t["last_30_days"]["new_users"] == 3
        assert t["first_user_created_at"] is not None
        assert t["latest_activity_at"] is not None

    def test_analysis_health(self, monkeypatch):
        h = _overview(monkeypatch, _seed())["analysis_health"]
        assert h["total"] == 2
        assert h["succeeded"] == 1
        assert h["failed"] == 1
        assert h["pending"] == 0
        assert h["running"] == 0
        assert h["success_rate"] == 50.0
        assert h["failure_rate"] == 50.0

    def test_engagement_depth(self, monkeypatch):
        e = _overview(monkeypatch, _seed())["engagement_depth"]
        assert e["average_analysis_jobs_per_user"] == 0.67
        assert e["average_analysis_jobs_per_active_analysis_user"] == 2.0
        assert e["average_applications_per_user"] == 1.0
        assert e["average_interview_sessions_per_user"] == 0.33
        assert e["average_interview_answers_per_session"] == 2.0

    def test_billing_readiness_disabled_by_default(self, monkeypatch):
        b = _overview(monkeypatch, _seed())["billing_readiness"]
        assert b["billing_enabled"] is False
        assert b["billing_status_label"] == "Chưa bật"
        assert b["payment_orders_total"] == 3
        assert b["paid_orders_total"] == 2
        assert b["paid_revenue_vnd"] == 80000
        assert b["manual_review_orders_total"] == 1

    def test_billing_readiness_label_when_enabled(self, monkeypatch):
        monkeypatch.setattr(config_module.settings, "ENABLE_BILLING", True)
        b = _overview(monkeypatch, _seed())["billing_readiness"]
        assert b["billing_enabled"] is True
        assert b["billing_status_label"] == "Đang bật"
        # Flag is reported, but no production rollout is triggered by reading it.
        assert _overview(monkeypatch, _seed())["flags"]["ENABLE_BILLING"] is True


class TestAnalyticsV2ZeroData:
    """Zero denominators must be safe (None), never a ZeroDivisionError."""

    def test_empty_db_rates_and_averages_are_null(self, monkeypatch):
        _set_admins(monkeypatch, "admin@example.com")
        admin = User(id=uuid.uuid4(), email="admin@example.com", is_active=True)
        resp = _client(FakeDb({}), admin).get("/v1/admin/overview")
        assert resp.status_code == 200
        body = resp.json()
        assert body["product_funnel"]["total_users"] == 0
        for v in body["conversion_rates"].values():
            assert v is None
        for v in body["engagement_depth"].values():
            assert v is None
        assert body["analysis_health"]["total"] == 0
        assert body["analysis_health"]["success_rate"] is None
        assert body["analysis_health"]["failure_rate"] is None
        assert body["activity_timeline"]["latest_activity_at"] is None
        assert body["activity_timeline"]["first_user_created_at"] is None
        assert body["activity_timeline"]["last_7_days"]["new_users"] == 0
