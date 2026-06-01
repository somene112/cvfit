import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.routes.auth import router as auth_router
from app.db.models import User
from app.db.session import get_db


class FakeQuery:
    def __init__(self, db):
        self.db = db
        self.email = None

    def filter_by(self, **kwargs):
        self.email = kwargs.get("email")
        return self

    def first(self):
        if self.email is None:
            return None
        return self.db.users_by_email.get(self.email)


class FakeDb:
    def __init__(self):
        self.users_by_email = {}
        self.users_by_id = {}
        self.pending = []

    def query(self, model):
        assert model is User
        return FakeQuery(self)

    def get(self, model, key):
        assert model is User
        return self.users_by_id.get(key)

    def add(self, user):
        self.pending.append(user)

    def commit(self):
        for user in self.pending:
            self.users_by_email[user.email] = user
            self.users_by_id[user.id] = user
        self.pending = []

    def rollback(self):
        self.pending = []

    def refresh(self, user):
        return None


@pytest.fixture
def auth_client():
    db = FakeDb()
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app), db


def register(client, email="student@example.com", password="strong-password", full_name="Student"):
    return client.post(
        "/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def test_register_success_returns_user_and_bearer_token(auth_client):
    client, db = auth_client

    response = register(client)

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "student@example.com"
    assert payload["user"]["full_name"] == "Student"
    assert "password_hash" not in str(payload)
    assert db.users_by_email["student@example.com"].password_hash != "strong-password"


def test_register_normalizes_lowercase_email(auth_client):
    client, db = auth_client

    response = register(client, email="  Student@Example.COM  ")

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "student@example.com"
    assert "student@example.com" in db.users_by_email


def test_register_duplicate_email_returns_409(auth_client):
    client, _db = auth_client

    assert register(client, email="Student@Example.COM").status_code == 200
    response = register(client, email=" student@example.com ")

    assert response.status_code == 409


def test_login_success_returns_user_and_bearer_token(auth_client):
    client, _db = auth_client
    assert register(client, email="student@example.com", password="correct-password").status_code == 200

    response = client.post(
        "/v1/auth/login",
        json={"email": " STUDENT@example.com ", "password": "correct-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "student@example.com"
    assert "password_hash" not in str(payload)


def test_login_wrong_password_returns_401(auth_client):
    client, _db = auth_client
    assert register(client, password="correct-password").status_code == 200

    response = client.post(
        "/v1/auth/login",
        json={"email": "student@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid credentials"


def test_login_inactive_user_returns_403(auth_client):
    client, db = auth_client
    assert register(client, password="correct-password").status_code == 200
    db.users_by_email["student@example.com"].is_active = False

    response = client.post(
        "/v1/auth/login",
        json={"email": "student@example.com", "password": "correct-password"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive user"


def test_auth_me_without_token_returns_401(auth_client):
    client, _db = auth_client

    response = client.get("/v1/auth/me")

    assert response.status_code == 401


def test_auth_me_with_valid_token_returns_safe_user(auth_client):
    client, _db = auth_client
    token = register(client).json()["access_token"]

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "student@example.com"
    assert "password_hash" not in str(payload)


def test_auth_logout_with_valid_token_returns_ok(auth_client):
    client, _db = auth_client
    token = register(client).json()["access_token"]

    response = client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_auth_me_with_token_for_missing_user_returns_401(auth_client):
    from app.core.security import create_access_token

    client, _db = auth_client
    token = create_access_token(str(uuid.uuid4()))

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
