"""Regression tests for cover-letter "Save Changes".

Editing an already-generated cover-letter draft must:
* persist the edited fields (and preserve the disclaimer),
* be free — never call consume_credit, never invoke credit gating,
* work even when ENABLE_CREDIT_GATING is true (editing an existing artifact is free),
* be owner-scoped (a non-owner gets 404, not another user's artifact),
* update the latest draft in place (no extra artifact created),
* reject malformed payloads safely.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes import applications as applications_module
from app.api.routes.applications import router
from app.core import config as config_module
from app.db.models import Application, ApplicationArtifact, User
from app.db.session import get_db


class FakeQuery:
    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, *args):
        rows = list(self._rows)
        for expr in args:
            try:
                key, val = expr.left.key, expr.right.value
                rows = [r for r in rows if getattr(r, key, None) == val]
            except AttributeError:
                pass
        return FakeQuery(rows)

    def order_by(self, *args):
        return self

    def all(self):
        return list(self._rows)


class FakeDb:
    def __init__(self):
        self._store: dict[tuple, Any] = {}
        self._rows: dict[type, list] = {}
        self.commits = 0

    def add(self, obj):
        self._store[(type(obj).__tablename__, obj.id)] = obj
        self._rows.setdefault(type(obj), []).append(obj)

    def get(self, model, pk):
        return self._store.get((model.__tablename__, pk))

    def query(self, model):
        return FakeQuery(self._rows.get(model, []))

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        pass


def _seed():
    user = User(id=uuid.uuid4(), email="owner@example.com", is_active=True)
    other = User(id=uuid.uuid4(), email="intruder@example.com", is_active=True)
    app = Application(
        id=uuid.uuid4(), user_id=user.id, job_title="Dev", jd_text="JD", status="draft",
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    artifact = ApplicationArtifact(
        id=uuid.uuid4(), user_id=user.id, application_id=app.id, artifact_type="cover_letter_draft",
        payload_json={"opening": "Old opening", "closing": "Old closing", "disclaimer": "keep me"},
        created_at=datetime.utcnow(),
    )
    db = FakeDb()
    for obj in (user, other, app, artifact):
        db.add(obj)
    return db, user, other, app, artifact


def _client(db, user):
    fa = FastAPI()
    fa.include_router(router)
    fa.dependency_overrides[get_db] = lambda: db
    if user is not None:
        fa.dependency_overrides[get_current_user] = lambda: user
    return TestClient(fa, raise_server_exceptions=False)


def test_owner_can_save_edits_and_they_persist():
    db, user, _other, app, artifact = _seed()
    resp = _client(db, user).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": "Bản mở đầu mới"})
    assert resp.status_code == 200
    assert resp.json()["payload_json"]["opening"] == "Bản mở đầu mới"
    # The stored artifact (what the next GET reads) is updated in place.
    assert artifact.payload_json["opening"] == "Bản mở đầu mới"
    assert artifact.payload_json["closing"] == "Old closing"   # untouched field preserved
    assert artifact.payload_json["disclaimer"] == "keep me"    # disclaimer always preserved
    assert db.commits == 1


def test_non_owner_cannot_save():
    db, _user, other, app, artifact = _seed()
    resp = _client(db, other).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": "hack"})
    assert resp.status_code == 404
    assert artifact.payload_json["opening"] == "Old opening"   # unchanged


def test_save_updates_in_place_without_extra_artifact():
    db, user, _other, app, _artifact = _seed()
    before = len(db._rows[ApplicationArtifact])
    _client(db, user).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": "x"})
    assert len(db._rows[ApplicationArtifact]) == before


def test_save_does_not_consume_credit(monkeypatch):
    db, user, _other, app, _artifact = _seed()
    calls = {"n": 0}
    monkeypatch.setattr(applications_module, "consume_credit", lambda *a, **k: calls.__setitem__("n", calls["n"] + 1))
    resp = _client(db, user).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": "x"})
    assert resp.status_code == 200
    assert calls["n"] == 0


def test_save_is_free_even_when_credit_gating_enabled(monkeypatch):
    db, user, _other, app, artifact = _seed()
    monkeypatch.setattr(config_module.settings, "ENABLE_CREDIT_GATING", True)
    resp = _client(db, user).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": "free edit"})
    assert resp.status_code == 200
    assert artifact.payload_json["opening"] == "free edit"


def test_missing_draft_returns_404():
    db, user, _other, app, artifact = _seed()
    db._rows[ApplicationArtifact] = []
    db._store.pop((ApplicationArtifact.__tablename__, artifact.id), None)
    resp = _client(db, user).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": "x"})
    assert resp.status_code == 404


def test_invalid_payload_is_rejected():
    db, user, _other, app, _artifact = _seed()
    # A dict where a string is expected → schema validation rejects before the handler.
    resp = _client(db, user).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": {"k": "v"}})
    assert resp.status_code == 422


def test_save_nfc_normalizes_vietnamese_diacritics():
    import unicodedata
    db, user, _other, app, artifact = _seed()
    nfc = "Tiếng Việt chào bạn"
    nfd = unicodedata.normalize("NFD", nfc)
    assert nfd != nfc  # sanity: the input is decomposed (broken-diacritic risk)
    resp = _client(db, user).patch(f"/v1/applications/{app.id}/cover-letter", json={"opening": nfd})
    assert resp.status_code == 200
    stored = artifact.payload_json["opening"]
    assert stored == nfc
    assert unicodedata.is_normalized("NFC", stored)
