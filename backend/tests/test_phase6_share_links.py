"""Phase 6 backend tests — Shareable Readiness / share links."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.share_links import router, public_router
from app.core.security import create_access_token
from app.db.models import AnalysisJob, Application, ShareLink, User
from app.db.session import get_db
from app.services.share.links import hash_share_token


class FakeDb:
    def __init__(self):
        self._store: dict[tuple, Any] = {}
        self._rows: dict[type, list] = {}

    def _key(self, model, pk):
        return (model.__tablename__, pk)

    def add(self, obj):
        self._store[self._key(type(obj), obj.id)] = obj
        self._rows.setdefault(type(obj), [])
        if obj not in self._rows[type(obj)]:
            self._rows[type(obj)].append(obj)

    def get(self, model, pk):
        return self._store.get(self._key(model, pk))

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        return FakeQuery(self._rows.get(model, []), model)


class FakeQuery:
    def __init__(self, rows, model):
        self._rows = list(rows)
        self._model = model

    def filter(self, *args):
        rows = list(self._rows)
        for expr in args:
            try:
                key = expr.left.key
                val = expr.right.value
                rows = [r for r in rows if getattr(r, key, None) == val]
            except AttributeError:
                pass
        return FakeQuery(rows, self._model)

    def order_by(self, *a):
        return self

    def all(self):
        return list(self._rows)


@pytest.fixture(autouse=True)
def enable_share(monkeypatch):
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "ENABLE_PHASE6_SHARE_LINKS", True)
    yield


def make_user(email="user@example.com") -> User:
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_job(user_id, fit=80.0) -> AnalysisJob:
    now = datetime.utcnow()
    result = {
        "overall_fit_score": fit, "scores": {"fit_score": fit},
        "missing_skills": [{"skill": "Kubernetes", "requirement_type": "must_have"}],
        "matched_skills": [{"skill": "Python"}],
    }
    return AnalysisJob(
        id=uuid.uuid4(), user_id=user_id, cv_file_id=uuid.uuid4(), jd_id=uuid.uuid4(),
        status="succeeded", progress=100, result_json=result, created_at=now, updated_at=now,
    )


RAW_CV_SENTINEL = "RAW_CV_SECRET_TEXT"
RAW_JD_SENTINEL = "RAW_JD_SECRET_TEXT"


def make_target_job(user_id, best=None) -> Application:
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(), user_id=user_id, job_title="Backend Dev", company_name="Co",
        jd_text=RAW_JD_SENTINEL, target_role="Backend", status="saved",
        best_analysis_job_id=best, created_at=now, updated_at=now,
    )


def make_link(user_id, target_id, token, **kw) -> ShareLink:
    now = datetime.utcnow()
    defaults = dict(
        id=uuid.uuid4(), user_id=user_id, target_type="target_job", target_id=target_id,
        token_hash=hash_share_token(token),
        visibility_json={
            "summary_only": True, "include_score_breakdown": False, "include_package": False,
            "include_cover_letter": False, "include_learning_roadmap": False,
            "hide_raw_cv": True, "hide_raw_jd": True,
        },
        expires_at=None, revoked_at=None, created_at=now, updated_at=None,
    )
    defaults.update(kw)
    return ShareLink(**defaults)


def client_for(db, user):
    app = FastAPI()
    app.include_router(router)
    app.include_router(public_router)
    create_access_token(str(user.id))
    db.add(user)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Create / token hashing
# ---------------------------------------------------------------------------

class TestCreate:
    def test_create_returns_raw_token_once_and_stores_hash(self):
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        db.add(tj)
        c = client_for(db, user)

        resp = c.post("/v1/share-links", json={"target_type": "target_job", "target_id": str(tj.id)})
        assert resp.status_code == 201
        body = resp.json()
        token = body["share_token"]
        assert token and len(token) >= 20
        assert body["public_path"].endswith(token)
        # token_hash never exposed
        assert "token_hash" not in body
        # stored object holds the hash, not the raw token
        stored = db.query(ShareLink).all()[0]
        assert stored.token_hash == hash_share_token(token)
        assert getattr(stored, "raw_token", None) is None
        assert token != stored.token_hash

    def test_create_cross_user_target_returns_404(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        tj_b = make_target_job(ub.id)
        db.add(tj_b)
        c = client_for(db, ua)
        resp = c.post("/v1/share-links", json={"target_type": "target_job", "target_id": str(tj_b.id)})
        assert resp.status_code == 404

    def test_create_disabled_flag_returns_404(self, monkeypatch):
        from app.core import config as cfg
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        db.add(tj)
        c = client_for(db, user)
        monkeypatch.setattr(cfg.settings, "ENABLE_PHASE6_SHARE_LINKS", False)
        resp = c.post("/v1/share-links", json={"target_type": "target_job", "target_id": str(tj.id)})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Owner management
# ---------------------------------------------------------------------------

class TestManage:
    def test_list_returns_only_own_links_without_hash(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        tja = make_target_job(ua.id)
        db.add(tja)
        db.add(make_link(ua.id, tja.id, "tok-a"))
        db.add(make_link(ub.id, uuid.uuid4(), "tok-b"))
        c = client_for(db, ua)

        resp = c.get("/v1/share-links")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert "token_hash" not in resp.text
        assert "tok-a" not in resp.text  # raw token never present

    def test_get_own_link_no_hash(self):
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        link = make_link(user.id, tj.id, "tok")
        db.add(tj); db.add(link)
        c = client_for(db, user)
        resp = c.get(f"/v1/share-links/{link.id}")
        assert resp.status_code == 200
        assert "token_hash" not in resp.text

    def test_get_cross_user_link_404(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        link_b = make_link(ub.id, uuid.uuid4(), "tok")
        db.add(link_b)
        c = client_for(db, ua)
        assert c.get(f"/v1/share-links/{link_b.id}").status_code == 404

    def test_patch_visibility_and_expiry(self):
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        link = make_link(user.id, tj.id, "tok")
        db.add(tj); db.add(link)
        c = client_for(db, user)
        resp = c.patch(f"/v1/share-links/{link.id}", json={
            "visibility": {"summary_only": True, "include_score_breakdown": True,
                           "include_package": False, "include_cover_letter": False,
                           "include_learning_roadmap": True, "hide_raw_cv": True, "hide_raw_jd": True},
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        })
        assert resp.status_code == 200
        assert resp.json()["visibility"]["include_score_breakdown"] is True

    def test_patch_cross_user_404(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        link_b = make_link(ub.id, uuid.uuid4(), "tok")
        db.add(link_b)
        c = client_for(db, ua)
        assert c.patch(f"/v1/share-links/{link_b.id}", json={"expires_at": datetime.utcnow().isoformat()}).status_code == 404

    def test_delete_revokes_without_hard_delete(self):
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        link = make_link(user.id, tj.id, "tok")
        db.add(tj); db.add(link)
        c = client_for(db, user)
        resp = c.delete(f"/v1/share-links/{link.id}")
        assert resp.status_code == 200
        assert resp.json()["revoked_at"] is not None
        assert resp.json()["is_active"] is False
        assert db.get(ShareLink, link.id) is not None  # preserved

    def test_delete_cross_user_404(self):
        ua, ub = make_user("a@e.com"), make_user("b@e.com")
        db = FakeDb()
        link_b = make_link(ub.id, uuid.uuid4(), "tok")
        db.add(link_b)
        c = client_for(db, ua)
        assert c.delete(f"/v1/share-links/{link_b.id}").status_code == 404


# ---------------------------------------------------------------------------
# Public redacted view
# ---------------------------------------------------------------------------

class TestPublicView:
    def test_public_valid_token_returns_redacted_summary(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit=82.0)
        tj = make_target_job(user.id, best=job.id)
        link = make_link(user.id, tj.id, "valid-token")
        db.add(job); db.add(tj); db.add(link)
        c = client_for(db, user)

        resp = c.get("/v1/public/share/valid-token")
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_title"] == "Backend Dev"
        assert body["readiness_level"]
        assert body["disclaimer"]
        # redacted by default: no raw CV/JD, no score breakdown
        assert RAW_JD_SENTINEL not in resp.text
        assert RAW_CV_SENTINEL not in resp.text
        assert body["fit_score"] is None
        assert body["learning_focus"] is None

    def test_public_score_breakdown_only_when_enabled(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit=82.0)
        tj = make_target_job(user.id, best=job.id)
        vis = {
            "summary_only": True, "include_score_breakdown": True, "include_package": False,
            "include_cover_letter": False, "include_learning_roadmap": True,
            "hide_raw_cv": True, "hide_raw_jd": True,
        }
        link = make_link(user.id, tj.id, "tok2", visibility_json=vis)
        db.add(job); db.add(tj); db.add(link)
        c = client_for(db, user)
        resp = c.get("/v1/public/share/tok2")
        assert resp.status_code == 200
        body = resp.json()
        assert body["fit_score"] == 82
        assert body["learning_focus"] is not None

    def test_public_invalid_token_404(self):
        user = make_user()
        db = FakeDb()
        c = client_for(db, user)
        assert c.get("/v1/public/share/nope-not-a-token").status_code == 404

    def test_public_revoked_token_404(self):
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        link = make_link(user.id, tj.id, "revoked-tok", revoked_at=datetime.utcnow())
        db.add(tj); db.add(link)
        c = client_for(db, user)
        assert c.get("/v1/public/share/revoked-tok").status_code == 404

    def test_public_expired_token_404(self):
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        link = make_link(user.id, tj.id, "expired-tok", expires_at=datetime.utcnow() - timedelta(days=1))
        db.add(tj); db.add(link)
        c = client_for(db, user)
        assert c.get("/v1/public/share/expired-tok").status_code == 404

    def test_public_disabled_flag_404(self, monkeypatch):
        from app.core import config as cfg
        user = make_user()
        db = FakeDb()
        tj = make_target_job(user.id)
        link = make_link(user.id, tj.id, "tok-x")
        db.add(tj); db.add(link)
        c = client_for(db, user)
        monkeypatch.setattr(cfg.settings, "ENABLE_PHASE6_SHARE_LINKS", False)
        assert c.get("/v1/public/share/tok-x").status_code == 404
