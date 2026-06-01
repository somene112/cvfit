import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import smoke_test_auth_api


def test_auth_smoke_requires_api_base_url(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)

    assert smoke_test_auth_api.main() == 1


def test_auth_smoke_refuses_without_explicit_mutating_flag(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://cvfit.example.test")
    monkeypatch.delenv("AUTH_SMOKE_ALLOW_MUTATING", raising=False)

    assert smoke_test_auth_api.main() == 1


def test_redact_token_hides_full_token():
    redacted = smoke_test_auth_api.redact_token("abcdef1234567890")

    assert redacted == "abcdef...<hidden>"
    assert "1234567890" not in redacted


def test_auth_smoke_calls_auth_flow_without_printing_tokens(monkeypatch, capsys):
    calls = []

    def fake_request_json(base_url, method, path, body=None, token=None):
        calls.append((method, path, token))
        if path == "/health":
            return {"status": "ok"}
        if path == "/v1/auth/register":
            return {
                "access_token": "register-secret-token",
                "token_type": "bearer",
                "user": {"email": body["email"]},
            }
        if path == "/v1/auth/login":
            return {
                "access_token": "login-secret-token",
                "token_type": "bearer",
                "user": {"email": body["email"]},
            }
        if path == "/v1/auth/me":
            return {"email": "cvfit-auth-smoke-1@example.test"}
        if path == "/v1/auth/logout":
            return {"ok": True}
        raise AssertionError(f"unexpected request {method} {path}")

    monkeypatch.setattr(smoke_test_auth_api, "synthetic_email", lambda: "cvfit-auth-smoke-1@example.test")
    monkeypatch.setattr(smoke_test_auth_api, "request_json", fake_request_json)

    assert smoke_test_auth_api.run_auth_smoke("https://cvfit.example.test") == 0
    output = capsys.readouterr().out
    assert "register-secret-token" not in output
    assert "login-secret-token" not in output
    assert ("GET", "/v1/auth/me", "login-secret-token") in calls
    assert ("POST", "/v1/auth/logout", "login-secret-token") in calls
