from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings, validate_runtime_config
from app.core.cors import add_cors_middleware, csv_setting


def make_client(monkeypatch, origins="http://localhost:3000", credentials=False):
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", origins)
    monkeypatch.setattr(settings, "CORS_ALLOW_CREDENTIALS", credentials)
    monkeypatch.setattr(settings, "CORS_ALLOWED_METHODS", "GET,POST,OPTIONS")
    monkeypatch.setattr(settings, "CORS_ALLOWED_HEADERS", "Authorization,Content-Type")
    app = FastAPI()
    add_cors_middleware(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return TestClient(app)


def test_csv_setting_strips_empty_items():
    assert csv_setting(" http://localhost:3000, ,https://app.example ") == [
        "http://localhost:3000",
        "https://app.example",
    ]


def test_cors_preflight_allows_configured_next_origin(monkeypatch):
    client = make_client(monkeypatch)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "Authorization" in response.headers["access-control-allow-headers"]
    assert "Content-Type" in response.headers["access-control-allow-headers"]


def test_cors_preflight_does_not_allow_unconfigured_origin(monkeypatch):
    client = make_client(monkeypatch, origins="https://frontend.example")

    response = client.options(
        "/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_cors_validation_rejects_wildcard_with_credentials(monkeypatch):
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", "*")
    monkeypatch.setattr(settings, "CORS_ALLOW_CREDENTIALS", True)

    try:
        validate_runtime_config()
    except RuntimeError as exc:
        assert "CORS_ALLOW_CREDENTIALS" in str(exc)
    else:
        raise AssertionError("expected wildcard credentials config to fail")
