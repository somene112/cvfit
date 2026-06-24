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
    InterviewSession,
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


def _seed() -> FakeDb:
    now = datetime.utcnow()
    admin = User(id=uuid.uuid4(), email="admin@example.com", is_active=True, email_verified=True)
    member = User(id=uuid.uuid4(), email="member@example.com", is_active=True, email_verified=False)
    inactive = User(id=uuid.uuid4(), email="ghost@example.com", is_active=False, email_verified=False)

    jobs = [
        AnalysisJob(id=uuid.uuid4(), cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
                    status="succeeded", result_json={"cv_text": SECRET_CV, "jd_text": SECRET_JD}),
        AnalysisJob(id=uuid.uuid4(), cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(), status="failed"),
    ]
    applications = [
        Application(id=uuid.uuid4(), user_id=member.id, job_title="Dev", jd_text=SECRET_JD, status="draft"),
        Application(id=uuid.uuid4(), user_id=member.id, job_title="ML", jd_text=SECRET_JD, status="saved"),
        Application(id=uuid.uuid4(), user_id=member.id, job_title="BE", jd_text=SECRET_JD, status="offer"),
    ]
    sessions = [InterviewSession(id=uuid.uuid4(), user_id=member.id, status="active")]
    orders = [
        PaymentOrder(id=uuid.uuid4(), user_id=member.id, provider_order_code="oc1", plan_code="p1",
                     amount_vnd=50000, status="paid", checkout_url=SECRET_CHECKOUT,
                     raw_provider_payload_json=SECRET_PAYLOAD),
        PaymentOrder(id=uuid.uuid4(), user_id=member.id, provider_order_code="oc2", plan_code="p1",
                     amount_vnd=30000, status="paid", checkout_url=SECRET_CHECKOUT),
        PaymentOrder(id=uuid.uuid4(), user_id=member.id, provider_order_code="oc3", plan_code="p2",
                     amount_vnd=99000, status="manual_review", checkout_url=SECRET_CHECKOUT),
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
            SECRET_CHECKOUT, SECRET_CV, SECRET_JD, "checkout_url", "raw_provider_payload",
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
