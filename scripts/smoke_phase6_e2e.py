#!/usr/bin/env python3
"""
Phase 6 backend E2E smoke test — Target Jobs, Learning, Interview v2, Help
Assistant, Share Links (flag-off check), and Usage / Plans.

Safe for local and deployed use. It registers a synthetic user, exercises a
happy-path across the Phase 6 surfaces, and prints PASS/SKIP/FAIL per step.
It never prints passwords, JWTs, share tokens, raw CV/JD text, or interview
answers, and it never sends real personal data.

Usage:
    python scripts/smoke_phase6_e2e.py [--dry-run]

Environment variables:
    API_BASE_URL / CVFIT_API_BASE_URL   Base URL (default: http://localhost:8000)
    PHASE6_SMOKE_ALLOW_MUTATING         "1" to run mutating steps (creates demo data)
    PHASE6_SMOKE_EXPECT_SHARE_ENABLED   "1" if ENABLE_PHASE6_SHARE_LINKS is on in the
                                        target env (default: expect share links OFF -> 404)

Read-only (health + auth + read endpoints):
    python scripts/smoke_phase6_e2e.py

Full happy path (creates synthetic demo data under a throwaway user):
    set PHASE6_SMOKE_ALLOW_MUTATING=1
    python scripts/smoke_phase6_e2e.py
"""

import argparse
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.request
from typing import Any, Optional


# Fields/keys that must never appear in any response payload.
INTERNAL_FIELDS = frozenset({
    "storage_key", "storage_path", "access_token", "password_hash",
    "report_docx_path", "access_token_hash", "token_hash",
})

# Short, synthetic, non-sensitive demo JD snippet.
DEMO_JD = (
    "We need a backend developer comfortable with Python and REST APIs. "
    "Must-have: Python. Nice-to-have: Docker."
)
DEMO_ANSWER = "I built a small Python service and tested it; first I designed it, then I shipped it."


class SmokeError(RuntimeError):
    pass


def normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    return raw.lower() in ("1", "true", "yes")


def redact_token(token: str) -> str:
    # Never reveal any token bytes (not even the JWT header prefix). Report
    # length only so the caller can confirm a token was received.
    return f"<redacted, len={len(token)}>" if token else "<empty>"


def verify_no_internal_fields(data: Any, path: str = "") -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in INTERNAL_FIELDS:
                raise SmokeError(f"Internal field '{key}' leaked at '{path or '<root>'}'")
            verify_no_internal_fields(value, f"{path}.{key}" if path else key)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            verify_no_internal_fields(item, f"{path}[{i}]")


def request_json(base_url, method, path, body=None, token=None):
    url = f"{base_url}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read()
            return exc.code, (json.loads(raw) if raw else {})
        except Exception:
            return exc.code, {}
    except urllib.error.URLError as exc:
        raise SmokeError(f"connection error: {exc.reason}")


def _pass(msg): print(f"PASS  {msg}")
def _skip(msg): print(f"SKIP  {msg}")
def _fail(msg): print(f"FAIL  {msg}", file=sys.stderr)


def run_smoke(base_url: str, mutating: bool, expect_share_enabled: bool) -> bool:
    ok = True

    # 1. health
    code, _ = request_json(base_url, "GET", "/health")
    if code == 200:
        _pass("GET /health")
    else:
        _fail(f"GET /health -> {code}")
        return False

    # 2. auth register + login
    ts = int(time.time())
    email = f"cvfit-phase6-smoke-{ts}-{uuid.uuid4().hex[:6]}@example.test"
    password = f"SmokePwd-{uuid.uuid4().hex[:8]}!"
    code, _ = request_json(base_url, "POST", "/v1/auth/register", body={"email": email, "password": password})
    if code not in (200, 201):
        _fail(f"POST /v1/auth/register -> {code}")
        return False
    _pass("POST /v1/auth/register (synthetic user)")
    code, body = request_json(base_url, "POST", "/v1/auth/login", body={"email": email, "password": password})
    token = body.get("access_token") if code == 200 else None
    if not isinstance(token, str):
        _fail(f"POST /v1/auth/login -> {code}")
        return False
    _pass(f"POST /v1/auth/login -> token {redact_token(token)}")

    # Read-only: usage + plans (always available; flag default on)
    code, body = request_json(base_url, "GET", "/v1/plans", token=token)
    if code == 200 and any(p.get("id") == "free_demo" for p in body.get("plans", [])):
        if "checkout_url" in json.dumps(body):
            _fail("GET /v1/plans exposed a checkout_url")
            ok = False
        else:
            _pass("GET /v1/plans (free_demo, no checkout)")
    elif code == 404:
        _skip("GET /v1/plans (usage shell disabled in this env)")
    else:
        _fail(f"GET /v1/plans -> {code}")
        ok = False

    code, body = request_json(base_url, "GET", "/v1/usage/me", token=token)
    if code == 200 and body.get("enforcement_enabled") is False:
        _pass(f"GET /v1/usage/me (enforcement_enabled=false, plan={body.get('plan_id')})")
    elif code == 404:
        _skip("GET /v1/usage/me (usage shell disabled in this env)")
    else:
        _fail(f"GET /v1/usage/me -> {code}: enforcement_enabled={body.get('enforcement_enabled')}")
        ok = False

    # Share links flag check (default OFF -> 404)
    code, _ = request_json(base_url, "GET", "/v1/share-links", token=token)
    if expect_share_enabled:
        if code == 200:
            _pass("GET /v1/share-links (share links enabled as expected)")
        else:
            _fail(f"GET /v1/share-links expected 200 (share enabled) -> {code}")
            ok = False
    else:
        if code == 404:
            _pass("GET /v1/share-links -> 404 (share links flag-off, as expected)")
        else:
            _fail(f"GET /v1/share-links expected 404 (share flag-off) -> {code}")
            ok = False

    if not mutating:
        _skip("Mutating steps skipped (set PHASE6_SMOKE_ALLOW_MUTATING=1 to enable)")
        return ok

    # 3-4. target job create + list
    code, body = request_json(base_url, "POST", "/v1/target-jobs", token=token, body={
        "job_title": "Backend Developer (Phase6 Smoke)", "company_name": "Smoke Co",
        "jd_text": DEMO_JD, "target_role": "Backend",
    })
    target_job_id = body.get("id") if code == 201 else None
    if target_job_id:
        verify_no_internal_fields(body)
        _pass(f"POST /v1/target-jobs -> {target_job_id}")
    else:
        _fail(f"POST /v1/target-jobs -> {code}: {body}")
        return False
    code, body = request_json(base_url, "GET", "/v1/target-jobs", token=token)
    if code == 200 and body.get("total", 0) >= 1:
        _pass("GET /v1/target-jobs")
    else:
        _fail(f"GET /v1/target-jobs -> {code}")
        ok = False

    # 5. learning generation (no analysis attached -> safe limited fallback)
    code, body = request_json(base_url, "POST", f"/v1/target-jobs/{target_job_id}/learning/generate", token=token)
    if code == 201 and "limitations" in body:
        _pass(f"POST .../learning/generate ({body.get('total')} tasks, limited fallback)")
    elif code == 404:
        _skip("learning generation (learning flag disabled in this env)")
    else:
        _fail(f"POST .../learning/generate -> {code}")
        ok = False

    # 6-9. interview session -> questions -> answer -> summary
    code, body = request_json(base_url, "POST", "/v1/interview/sessions", token=token, body={
        "target_job_id": target_job_id, "session_type": "mixed", "difficulty": "medium",
    })
    session_id = body.get("id") if code == 201 else None
    if session_id:
        _pass(f"POST /v1/interview/sessions -> {session_id}")
    elif code == 404:
        _skip("interview v2 (flag disabled in this env)")
    else:
        _fail(f"POST /v1/interview/sessions -> {code}")
        ok = False

    if session_id:
        code, body = request_json(base_url, "POST", f"/v1/interview/sessions/{session_id}/questions/generate",
                                  token=token, body={"count": 3})
        question_id = body["questions"][0]["id"] if code == 201 and body.get("questions") else None
        if question_id:
            _pass(f"POST .../questions/generate ({body.get('total')} questions)")
        else:
            _fail(f"POST .../questions/generate -> {code}")
            ok = False

        if question_id:
            code, body = request_json(base_url, "POST", f"/v1/interview/sessions/{session_id}/answers",
                                      token=token, body={"question_id": question_id, "answer_text": DEMO_ANSWER})
            if code == 201 and "score" in body:
                _pass("POST .../answers (rubric returned)")
            else:
                _fail(f"POST .../answers -> {code}")
                ok = False

        code, body = request_json(base_url, "GET", f"/v1/interview/sessions/{session_id}/summary", token=token)
        if code == 200 and "disclaimer" in body:
            _pass("GET .../summary")
        else:
            _fail(f"GET .../summary -> {code}")
            ok = False

    # 10. help assistant next_best_action
    code, body = request_json(base_url, "POST", "/v1/help/assistant", token=token,
                              body={"intent": "next_best_action", "target_job_id": target_job_id})
    if code == 200 and "answer" in body:
        _pass(f"POST /v1/help/assistant next_best_action (fallback_used={body.get('fallback_used')})")
    elif code == 404:
        _skip("help assistant (flag disabled in this env)")
    else:
        _fail(f"POST /v1/help/assistant -> {code}")
        ok = False

    # Ownership non-leak
    code, _ = request_json(base_url, "GET", f"/v1/target-jobs/{uuid.uuid4()}", token=token)
    if code == 404:
        _pass("GET /v1/target-jobs/<unknown-uuid> -> 404 (non-leak ownership)")
    else:
        _fail(f"Ownership non-leak -> expected 404, got {code}")
        ok = False

    return ok


def print_dry_run(mutating: bool, expect_share_enabled: bool) -> None:
    print("DRY RUN - no API calls will be made")
    steps = [
        "GET /health",
        "POST /v1/auth/register (synthetic user)",
        "POST /v1/auth/login",
        "GET /v1/plans (free_demo, no checkout)",
        "GET /v1/usage/me (enforcement_enabled=false)",
        f"GET /v1/share-links -> {'200 (share enabled)' if expect_share_enabled else '404 (flag-off)'}",
    ]
    if mutating:
        steps += [
            "POST /v1/target-jobs", "GET /v1/target-jobs",
            "POST /v1/target-jobs/{id}/learning/generate",
            "POST /v1/interview/sessions", "POST .../questions/generate",
            "POST .../answers", "GET .../summary",
            "POST /v1/help/assistant next_best_action",
            "GET /v1/target-jobs/<unknown-uuid> -> 404",
        ]
    else:
        steps.append("SKIP mutating steps (PHASE6_SMOKE_ALLOW_MUTATING not set)")
    for s in steps:
        print(f"  {s}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 6 backend E2E smoke test")
    parser.add_argument("--dry-run", action="store_true", help="Print steps without calling the API")
    args = parser.parse_args()

    base_url = normalize_base_url(
        os.environ.get("API_BASE_URL") or os.environ.get("CVFIT_API_BASE_URL") or "http://localhost:8000"
    )
    mutating = env_flag("PHASE6_SMOKE_ALLOW_MUTATING")
    expect_share_enabled = env_flag("PHASE6_SMOKE_EXPECT_SHARE_ENABLED")

    print("Phase 6 backend E2E smoke")
    print(f"  base_url        : {base_url}")
    print(f"  mutating        : {mutating}")
    print(f"  share_expected  : {'enabled' if expect_share_enabled else 'flag-off (404)'}")
    print()

    if args.dry_run:
        print_dry_run(mutating, expect_share_enabled)
        sys.exit(0)

    try:
        passed = run_smoke(base_url, mutating, expect_share_enabled)
    except SmokeError as exc:
        _fail(str(exc))
        passed = False

    print()
    if passed:
        print("phase6 backend e2e smoke passed")
        sys.exit(0)
    print("phase6 backend e2e smoke FAILED - see FAIL lines above", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
