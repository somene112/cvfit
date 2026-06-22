"""Tests for POST /v1/auth/google.

Google ID-token verification is always mocked — these tests never touch the
network or require the ``google-auth`` package to be installed.
"""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_module
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.services.google_auth import GoogleAuthError


class FakeQuery:
    def __init__(self, db):
        self.db = db
        self.field = None
        self.value = None

    def filter_by(self, **kwargs):
        # Single-field lookups are all the route needs (email / google_sub).
        (self.field, self.value), = kwargs.items()
        return self

    def first(self):
        if self.value is None:
            return None
        for user in self.db.users:
            if getattr(user, self.field, None) == self.value:
                return user
        return None


class FakeDb:
    def __init__(self):
        self.users = []
        self.pending = []

    def query(self, model):
        assert model is User
        return FakeQuery(self)

    def get(self, model, key):
        assert model is User
        for user in self.users:
            if user.id == key:
                return user
        return None

    def add(self, user):
        self.pending.append(user)

    def commit(self):
        self.users.extend(self.pending)
        self.pending = []

    def rollback(self):
        self.pending = []

    def refresh(self, user):
        return None


@pytest.fixture
def google_client(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "ENABLE_GOOGLE_AUTH", True)

    db = FakeDb()
    app = FastAPI()
    app.include_router(auth_module.router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app), db


def _mock_verifier(monkeypatch, claims):
    monkeypatch.setattr(auth_module, "verify_google_id_token", lambda credential: dict(claims))


def _claims(**overrides):
    base = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-123",
        "email": "person@example.com",
        "email_verified": True,
        "name": "Test Person",
        "picture": "https://example.com/p.png",
    }
    base.update(overrides)
    return base


def _make_password_user(db, email="person@example.com"):
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed-secret",
        full_name="Existing User",
        is_active=True,
    )
    db.users.append(user)
    return user


def test_google_login_unconfigured_returns_503(google_client, monkeypatch):
    client, _db = google_client
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")

    response = client.post("/v1/auth/google", json={"credential": "any.token.value"})

    assert response.status_code == 503
    assert "client" not in response.json()["detail"].lower()


def test_google_login_disabled_returns_503(google_client, monkeypatch):
    client, _db = google_client
    monkeypatch.setattr(settings, "ENABLE_GOOGLE_AUTH", False)

    response = client.post("/v1/auth/google", json={"credential": "any.token.value"})

    assert response.status_code == 503


def test_google_login_invalid_token_returns_401(google_client, monkeypatch):
    client, _db = google_client

    def _raise(credential):
        raise GoogleAuthError("invalid google credential")

    monkeypatch.setattr(auth_module, "verify_google_id_token", _raise)

    response = client.post("/v1/auth/google", json={"credential": "bad.token.value"})

    assert response.status_code == 401


def test_google_login_unverified_email_returns_403(google_client, monkeypatch):
    client, _db = google_client
    _mock_verifier(monkeypatch, _claims(email_verified=False))

    response = client.post("/v1/auth/google", json={"credential": "tok.tok.tok"})

    assert response.status_code == 403


def test_google_login_creates_new_verified_user(google_client, monkeypatch):
    client, db = google_client
    _mock_verifier(monkeypatch, _claims())

    response = client.post("/v1/auth/google", json={"credential": "tok.tok.tok"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "person@example.com"
    assert len(db.users) == 1
    created = db.users[0]
    assert created.google_sub == "google-sub-123"
    assert created.auth_provider == "google"
    assert created.password_hash is None


def test_google_login_links_existing_email_user(google_client, monkeypatch):
    client, db = google_client
    existing = _make_password_user(db)
    _mock_verifier(monkeypatch, _claims())

    response = client.post("/v1/auth/google", json={"credential": "tok.tok.tok"})

    assert response.status_code == 200
    assert response.json()["user"]["id"] == str(existing.id)
    assert len(db.users) == 1
    # Linking must not overwrite the existing password.
    assert existing.password_hash == "hashed-secret"
    assert existing.google_sub == "google-sub-123"


def test_google_login_existing_google_sub_logs_in(google_client, monkeypatch):
    client, db = google_client
    user = User(
        id=uuid.uuid4(),
        email="person@example.com",
        password_hash=None,
        full_name="Test Person",
        google_sub="google-sub-123",
        auth_provider="google",
        email_verified=True,
        is_active=True,
    )
    db.users.append(user)
    _mock_verifier(monkeypatch, _claims())

    response = client.post("/v1/auth/google", json={"credential": "tok.tok.tok"})

    assert response.status_code == 200
    assert response.json()["user"]["id"] == str(user.id)
    assert len(db.users) == 1


def test_google_login_repeated_does_not_duplicate_user(google_client, monkeypatch):
    client, db = google_client
    _mock_verifier(monkeypatch, _claims())

    first = client.post("/v1/auth/google", json={"credential": "tok.tok.tok"})
    second = client.post("/v1/auth/google", json={"credential": "tok.tok.tok"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["user"]["id"] == second.json()["user"]["id"]
    assert len(db.users) == 1


def test_google_login_response_has_no_raw_token_or_sub(google_client, monkeypatch):
    client, _db = google_client
    credential = "header.payload.signature"
    _mock_verifier(monkeypatch, _claims())

    response = client.post("/v1/auth/google", json={"credential": credential})

    body = response.text
    assert credential not in body
    assert "google-sub-123" not in body


def test_google_login_inactive_user_returns_403(google_client, monkeypatch):
    client, db = google_client
    existing = _make_password_user(db)
    existing.is_active = False
    _mock_verifier(monkeypatch, _claims())

    response = client.post("/v1/auth/google", json={"credential": "tok.tok.tok"})

    assert response.status_code == 403
