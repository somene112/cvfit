from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


REQUEST_TIMEOUT_SECONDS = 30


class SmokeError(RuntimeError):
    pass


def normalize_base_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise SmokeError("API_BASE_URL is required, for example https://your-render-api.onrender.com")
    if not cleaned.startswith(("http://", "https://")):
        raise SmokeError("API_BASE_URL must start with http:// or https://")
    return cleaned.rstrip("/")


def env_flag_enabled(name: str) -> bool:
    return os.environ.get(name, "").strip() == "1"


def synthetic_email() -> str:
    return f"cvfit-auth-smoke-{int(time.time())}@example.test"


def build_url(base_url: str, path: str) -> str:
    return urljoin(f"{base_url}/", path.lstrip("/"))


def redact_token(value: str) -> str:
    if not value:
        return value
    if len(value) <= 12:
        return "<hidden>"
    return f"{value[:6]}...<hidden>"


def request_json(
    base_url: str,
    method: str,
    path: str,
    body: dict | None = None,
    token: str | None = None,
) -> dict:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(build_url(base_url, path), data=data, headers=headers, method=method)
    with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def run_auth_smoke(base_url: str) -> int:
    email = synthetic_email()
    password = f"synthetic-password-{int(time.time())}"

    health = request_json(base_url, "GET", "/health")
    if health != {"status": "ok"}:
        raise SmokeError(f"unexpected health response: {health}")
    print("health ok")

    registered = request_json(
        base_url,
        "POST",
        "/v1/auth/register",
        {"email": email, "password": password, "full_name": "CVFit Auth Smoke"},
    )
    register_token = registered.get("access_token")
    user = registered.get("user") or {}
    if not register_token or user.get("email") != email:
        raise SmokeError("register response missing token or expected synthetic user")
    print(f"register ok email={email} token={redact_token(register_token)}")

    logged_in = request_json(
        base_url,
        "POST",
        "/v1/auth/login",
        {"email": email, "password": password},
    )
    login_token = logged_in.get("access_token")
    if not login_token:
        raise SmokeError("login response missing access token")
    print(f"login ok token={redact_token(login_token)}")

    me = request_json(base_url, "GET", "/v1/auth/me", token=login_token)
    if me.get("email") != email:
        raise SmokeError("me response did not return the synthetic user")
    print("me ok")

    logout = request_json(base_url, "POST", "/v1/auth/logout", token=login_token)
    if logout != {"ok": True}:
        raise SmokeError(f"unexpected logout response: {logout}")
    print("logout ok")
    print("auth smoke created one synthetic account; no account cleanup endpoint is available")
    print("auth smoke passed")
    return 0


def main() -> int:
    try:
        base_url = normalize_base_url(os.environ.get("API_BASE_URL", ""))
        if not env_flag_enabled("AUTH_SMOKE_ALLOW_MUTATING"):
            raise SmokeError("refusing auth smoke; set AUTH_SMOKE_ALLOW_MUTATING=1 to create one synthetic account")
        return run_auth_smoke(base_url)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}", file=sys.stderr)
        return 1
    except (SmokeError, URLError, TimeoutError) as exc:
        print(f"auth smoke failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
