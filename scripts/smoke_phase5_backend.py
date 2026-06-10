#!/usr/bin/env python3
"""
Phase 5 backend smoke test — Application Workspace, Career Profile, Interview Practice.

Usage:
    python scripts/smoke_phase5_backend.py [--dry-run]

Environment variables:
    API_BASE_URL                  Base URL (default: http://localhost:8000)
    PHASE5_SMOKE_ALLOW_MUTATING   Set to "1" to run mutating steps (creates real data)
    PHASE5_SMOKE_JOB_ID           UUID of an owned succeeded AnalysisJob to attach for
                                  package/cover-letter/analysis-backed question tests
    PHASE5_SMOKE_CLEANUP          Set to "0" to skip cleanup (default: cleanup enabled)

Read-only smoke (no env vars needed beyond API_BASE_URL):
    python scripts/smoke_phase5_backend.py

Mutating smoke with analysis attachment:
    set PHASE5_SMOKE_ALLOW_MUTATING=1
    set PHASE5_SMOKE_JOB_ID=<uuid-of-succeeded-job>
    python scripts/smoke_phase5_backend.py
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


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SmokeError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Fields that must never appear in any API response
# ---------------------------------------------------------------------------

INTERNAL_FIELDS = frozenset({
    "storage_key",
    "storage_path",
    "access_token",
    "password_hash",
    "report_docx_path",
    "access_token_hash",
})


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def env_flag_enabled(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    return raw.lower() in ("1", "true", "yes")


def redact_token(token: str) -> str:
    return (token[:12] + "...") if len(token) > 12 else "***"


def verify_no_internal_fields(data: Any, path: str = "") -> None:
    """Raise SmokeError if any forbidden internal field appears in response data."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in INTERNAL_FIELDS:
                raise SmokeError(
                    f"Internal field '{key}' leaked in API response at '{path or '<root>'}'"
                )
            verify_no_internal_fields(value, path=f"{path}.{key}" if path else key)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            verify_no_internal_fields(item, path=f"{path}[{i}]")


def request_json(
    base_url: str,
    method: str,
    path: str,
    body: Optional[dict] = None,
    token: Optional[str] = None,
) -> tuple[int, Any]:
    url = f"{base_url}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers: dict[str, str] = {"Accept": "application/json"}
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


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _pass(msg: str) -> None:
    print(f"PASS  {msg}")


def _skip(msg: str) -> None:
    print(f"SKIP  {msg}")


def _fail(msg: str) -> None:
    print(f"FAIL  {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Smoke runner
# ---------------------------------------------------------------------------

def run_smoke(
    base_url: str,
    mutating: bool,
    job_id_env: Optional[str],
    cleanup: bool,
) -> bool:
    ok = True
    token: Optional[str] = None
    application_id: Optional[str] = None
    profile_item_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------
    code, body = request_json(base_url, "GET", "/health")
    if code == 200:
        _pass("GET /health")
    else:
        _fail(f"GET /health -> {code}")
        ok = False

    # ------------------------------------------------------------------
    # Auth — register + login synthetic user (always required for JWT)
    # ------------------------------------------------------------------
    ts = int(time.time())
    synthetic_email = f"cvfit-phase5-smoke-{ts}@example.test"
    synthetic_password = f"SmokePwd-{uuid.uuid4().hex[:8]}!"

    code, body = request_json(base_url, "POST", "/v1/auth/register", body={
        "email": synthetic_email,
        "password": synthetic_password,
    })
    if code in (200, 201):
        _pass(f"POST /v1/auth/register -> {synthetic_email}")
    else:
        _fail(f"POST /v1/auth/register -> {code}: {body}")
        print("Cannot continue without auth.", file=sys.stderr)
        return False

    code, body = request_json(base_url, "POST", "/v1/auth/login", body={
        "email": synthetic_email,
        "password": synthetic_password,
    })
    if code == 200 and isinstance(body.get("access_token"), str):
        token = body["access_token"]
        _pass(f"POST /v1/auth/login -> token {redact_token(token)}")
    else:
        _fail(f"POST /v1/auth/login -> {code}: {body}")
        print("Cannot continue without JWT token.", file=sys.stderr)
        return False

    # ------------------------------------------------------------------
    # Read-only: list empty profile items
    # ------------------------------------------------------------------
    code, body = request_json(base_url, "GET", "/v1/profile/items", token=token)
    if code == 200 and isinstance(body.get("items"), list):
        try:
            verify_no_internal_fields(body)
        except SmokeError as exc:
            _fail(str(exc))
            ok = False
        else:
            _pass(f"GET /v1/profile/items (empty list, read-only)")
    else:
        _fail(f"GET /v1/profile/items -> {code}: {body}")
        ok = False

    # Read-only: list empty applications
    code, body = request_json(base_url, "GET", "/v1/applications", token=token)
    if code == 200 and isinstance(body.get("items"), list):
        try:
            verify_no_internal_fields(body)
        except SmokeError as exc:
            _fail(str(exc))
            ok = False
        else:
            _pass(f"GET /v1/applications (empty list, read-only)")
    else:
        _fail(f"GET /v1/applications -> {code}: {body}")
        ok = False

    # ------------------------------------------------------------------
    # Guard: remaining steps are mutating
    # ------------------------------------------------------------------
    if not mutating:
        _skip("Mutating steps skipped (set PHASE5_SMOKE_ALLOW_MUTATING=1 to enable)")
        return ok

    # ==================================================================
    # Mutating steps
    # ==================================================================

    # ------------------------------------------------------------------
    # Career Profile — create
    # ------------------------------------------------------------------
    code, body = request_json(base_url, "POST", "/v1/profile/items", token=token, body={
        "item_type": "project",
        "title": "Smoke Test Project",
        "description": "Automated smoke test project entry.",
        "evidence_text": "Built a smoke test runner in Python with pytest.",
    })
    if code == 201 and body.get("id"):
        profile_item_id = body["id"]
        try:
            verify_no_internal_fields(body)
        except SmokeError as exc:
            _fail(str(exc))
            ok = False
        else:
            _pass(f"POST /v1/profile/items -> {profile_item_id}")
    else:
        _fail(f"POST /v1/profile/items -> {code}: {body}")
        ok = False

    if profile_item_id:
        # Career Profile — get by id
        code, body = request_json(base_url, "GET", f"/v1/profile/items/{profile_item_id}", token=token)
        if code == 200 and body.get("id") == profile_item_id:
            try:
                verify_no_internal_fields(body)
            except SmokeError as exc:
                _fail(str(exc))
                ok = False
            else:
                _pass(f"GET /v1/profile/items/{profile_item_id}")
        else:
            _fail(f"GET /v1/profile/items/{profile_item_id} -> {code}: {body}")
            ok = False

        # Career Profile — patch
        code, body = request_json(
            base_url, "PATCH", f"/v1/profile/items/{profile_item_id}", token=token,
            body={"title": "Smoke Test Project (updated)"},
        )
        if code == 200 and body.get("title") == "Smoke Test Project (updated)":
            _pass(f"PATCH /v1/profile/items/{profile_item_id}")
        else:
            _fail(f"PATCH /v1/profile/items/{profile_item_id} -> {code}: {body}")
            ok = False

        # Career Profile — list with item_type filter
        code, body = request_json(base_url, "GET", "/v1/profile/items?item_type=project", token=token)
        if code == 200 and body.get("total", 0) >= 1:
            _pass("GET /v1/profile/items?item_type=project (filter works)")
        else:
            _fail(f"GET /v1/profile/items?item_type=project -> {code}: {body}")
            ok = False

    # ------------------------------------------------------------------
    # Applications — create
    # ------------------------------------------------------------------
    code, body = request_json(base_url, "POST", "/v1/applications", token=token, body={
        "job_title": "Backend Software Engineer (Smoke Test)",
        "company_name": "Smoke Test Co",
        "jd_text": (
            "We need a Python developer with FastAPI, PostgreSQL, and REST API experience. "
            "Must-have: Python, PostgreSQL. Nice-to-have: Docker, Kubernetes."
        ),
        "target_role": "Backend Engineer",
    })
    if code == 201 and body.get("id"):
        application_id = body["id"]
        try:
            verify_no_internal_fields(body)
        except SmokeError as exc:
            _fail(str(exc))
            ok = False
        else:
            _pass(f"POST /v1/applications -> {application_id}")
    else:
        _fail(f"POST /v1/applications -> {code}: {body}")
        ok = False

    if application_id:
        # Applications — get by id
        code, body = request_json(base_url, "GET", f"/v1/applications/{application_id}", token=token)
        if code == 200 and body.get("id") == application_id:
            try:
                verify_no_internal_fields(body)
            except SmokeError as exc:
                _fail(str(exc))
                ok = False
            else:
                _pass(f"GET /v1/applications/{application_id}")
        else:
            _fail(f"GET /v1/applications/{application_id} -> {code}: {body}")
            ok = False

        # Applications — patch status
        code, body = request_json(
            base_url, "PATCH", f"/v1/applications/{application_id}", token=token,
            body={"status": "interview_prep"},
        )
        if code == 200 and body.get("status") == "interview_prep":
            _pass(f"PATCH /v1/applications/{application_id} -> status=interview_prep")
        else:
            _fail(f"PATCH /v1/applications/{application_id} -> {code}: {body}")
            ok = False

        # Readiness — no analysis attached
        code, body = request_json(base_url, "GET", f"/v1/applications/{application_id}/readiness", token=token)
        if code == 200 and body.get("readiness_level") == "not_started":
            try:
                verify_no_internal_fields(body)
            except SmokeError as exc:
                _fail(str(exc))
                ok = False
            else:
                _pass(f"GET .../readiness (no analysis -> readiness_level=not_started)")
        else:
            _fail(f"GET .../readiness -> {code}: {body}")
            ok = False

        # Interview questions — no analysis (generic behavioral fallback, must be 200)
        code, body = request_json(
            base_url, "GET", f"/v1/applications/{application_id}/interview/questions", token=token,
        )
        if code == 200 and isinstance(body.get("questions"), list) and len(body["questions"]) > 0:
            first_q = body["questions"][0]
            missing_keys = [k for k in ("question_id", "question", "type", "why_this_question") if k not in first_q]
            missing_top = [k for k in ("disclaimer",) if k not in body]
            if missing_keys or missing_top:
                _fail(f"GET .../interview/questions: missing keys {missing_keys + missing_top}")
                ok = False
            else:
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass(
                        f"GET .../interview/questions (no analysis, {len(body['questions'])} behavioral fallback)"
                    )
        else:
            _fail(f"GET .../interview/questions -> {code}: {body}")
            ok = False

        # Interview — submit answer
        code, body = request_json(
            base_url, "POST", f"/v1/applications/{application_id}/interview/answers",
            token=token,
            body={
                "question_id": "q_1",
                "question": "Tell me about your experience with Python and REST APIs.",
                "answer_text": (
                    "I have built REST APIs using FastAPI and PostgreSQL in several projects. "
                    "In one project I designed user authentication and product catalog endpoints. "
                    "I used SQLAlchemy for the ORM, Alembic for migrations, and deployed to Render. "
                    "I applied async route handlers and dependency injection for clean separation."
                ),
            },
        )
        if code == 201 and body.get("answer_id"):
            rubric = body.get("rubric", {})
            feedback = body.get("feedback", {})
            rubric_keys = ("relevance", "specificity", "evidence", "structure", "risk_gap", "overall")
            feedback_keys = ("strengths", "missing_evidence", "suggested_improvements", "sample_outline", "risk_notes", "disclaimer")
            rubric_missing = [k for k in rubric_keys if k not in rubric]
            feedback_missing = [k for k in feedback_keys if k not in feedback]
            if rubric_missing or feedback_missing:
                _fail(
                    f"POST .../interview/answers: rubric missing {rubric_missing}, "
                    f"feedback missing {feedback_missing}"
                )
                ok = False
            elif not feedback.get("disclaimer"):
                _fail("POST .../interview/answers: feedback.disclaimer is empty")
                ok = False
            else:
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass(f"POST .../interview/answers -> {body['answer_id']} (rubric={rubric})")
        else:
            _fail(f"POST .../interview/answers -> {code}: {body}")
            ok = False

        # Interview — list answers
        code, body = request_json(
            base_url, "GET", f"/v1/applications/{application_id}/interview/answers", token=token,
        )
        if code == 200 and body.get("total", 0) >= 1:
            try:
                verify_no_internal_fields(body)
            except SmokeError as exc:
                _fail(str(exc))
                ok = False
            else:
                _pass(f"GET .../interview/answers -> {body['total']} answer(s)")
        else:
            _fail(f"GET .../interview/answers -> {code}: {body}")
            ok = False

        # --------------------------------------------------------------
        # Attach analysis + package / cover-letter / analysis questions
        # (requires PHASE5_SMOKE_JOB_ID)
        # --------------------------------------------------------------
        if job_id_env:
            code, body = request_json(
                base_url, "POST",
                f"/v1/applications/{application_id}/attach-analysis/{job_id_env}",
                token=token,
            )
            if code == 200 and body.get("best_analysis_job_id") == job_id_env:
                _pass(f"POST .../attach-analysis/{job_id_env[:8]}...")
            else:
                _fail(f"POST .../attach-analysis -> {code}: {body}")
                ok = False

            # Readiness with analysis attached
            code, body = request_json(
                base_url, "GET", f"/v1/applications/{application_id}/readiness", token=token,
            )
            valid_levels = ("not_started", "needs_work", "almost_ready", "ready")
            if code == 200 and body.get("readiness_level") in valid_levels:
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass(
                        f"GET .../readiness (with analysis) -> "
                        f"level={body['readiness_level']}, fit_score={body.get('fit_score')}"
                    )
            else:
                _fail(f"GET .../readiness (with analysis) -> {code}: {body}")
                ok = False

            # Package — generate
            code, body = request_json(
                base_url, "POST", f"/v1/applications/{application_id}/package/generate", token=token,
            )
            if code == 201 and body.get("artifact_id"):
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass(f"POST .../package/generate -> {body['artifact_id']}")
            else:
                _fail(f"POST .../package/generate -> {code}: {body}")
                ok = False

            # Package — get
            code, body = request_json(
                base_url, "GET", f"/v1/applications/{application_id}/package", token=token,
            )
            if code == 200 and body.get("artifact_type") == "application_package":
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass("GET .../package")
            else:
                _fail(f"GET .../package -> {code}: {body}")
                ok = False

            # Package — download (JSON stub)
            code, body = request_json(
                base_url, "GET", f"/v1/applications/{application_id}/package/download", token=token,
            )
            if code == 200 and body.get("download_format") == "json":
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass("GET .../package/download")
            else:
                _fail(f"GET .../package/download -> {code}: {body}")
                ok = False

            # Cover letter — generate
            code, body = request_json(
                base_url, "POST", f"/v1/applications/{application_id}/cover-letter/generate", token=token,
            )
            if code == 201 and body.get("artifact_id"):
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass(f"POST .../cover-letter/generate -> {body['artifact_id']}")
            else:
                _fail(f"POST .../cover-letter/generate -> {code}: {body}")
                ok = False

            # Cover letter — get (verify disclaimer in payload_json)
            code, body = request_json(
                base_url, "GET", f"/v1/applications/{application_id}/cover-letter", token=token,
            )
            if code == 200 and body.get("artifact_type") == "cover_letter_draft":
                payload = body.get("payload_json", {})
                if not payload.get("disclaimer"):
                    _fail("GET .../cover-letter: disclaimer missing from payload_json")
                    ok = False
                else:
                    try:
                        verify_no_internal_fields(body)
                    except SmokeError as exc:
                        _fail(str(exc))
                        ok = False
                    else:
                        _pass("GET .../cover-letter (disclaimer present)")
            else:
                _fail(f"GET .../cover-letter -> {code}: {body}")
                ok = False

            # Cover letter — patch (disclaimer must survive)
            code, body = request_json(
                base_url, "PATCH", f"/v1/applications/{application_id}/cover-letter",
                token=token,
                body={"opening": "Smoke-patched opening paragraph."},
            )
            if code == 200:
                payload = body.get("payload_json", {})
                if payload.get("opening") != "Smoke-patched opening paragraph.":
                    _fail(f"PATCH .../cover-letter: opening not updated, got {payload.get('opening')!r}")
                    ok = False
                elif not payload.get("disclaimer"):
                    _fail("PATCH .../cover-letter: disclaimer was removed after patch")
                    ok = False
                else:
                    _pass("PATCH .../cover-letter (opening updated, disclaimer preserved)")
            else:
                _fail(f"PATCH .../cover-letter -> {code}: {body}")
                ok = False

            # Interview questions — analysis-backed
            code, body = request_json(
                base_url, "GET", f"/v1/applications/{application_id}/interview/questions", token=token,
            )
            if code == 200 and isinstance(body.get("questions"), list) and len(body["questions"]) > 0:
                try:
                    verify_no_internal_fields(body)
                except SmokeError as exc:
                    _fail(str(exc))
                    ok = False
                else:
                    _pass(
                        f"GET .../interview/questions (with analysis, {len(body['questions'])} questions)"
                    )
            else:
                _fail(f"GET .../interview/questions (with analysis) -> {code}: {body}")
                ok = False

        else:
            _skip(
                "attach-analysis / package / cover-letter / analysis-backed questions "
                "(set PHASE5_SMOKE_JOB_ID to enable)"
            )

        # --------------------------------------------------------------
        # Ownership / non-leak: random UUID must return 404
        # --------------------------------------------------------------
        fake_id = str(uuid.uuid4())
        code, _ = request_json(base_url, "GET", f"/v1/applications/{fake_id}", token=token)
        if code == 404:
            _pass(f"GET /v1/applications/<unknown-uuid> -> 404 (non-leak ownership)")
        else:
            _fail(f"Ownership non-leak check -> expected 404, got {code}")
            ok = False

        fake_item_id = str(uuid.uuid4())
        code, _ = request_json(base_url, "GET", f"/v1/profile/items/{fake_item_id}", token=token)
        if code == 404:
            _pass(f"GET /v1/profile/items/<unknown-uuid> -> 404 (non-leak ownership)")
        else:
            _fail(f"Profile ownership non-leak check -> expected 404, got {code}")
            ok = False

        # --------------------------------------------------------------
        # Cleanup
        # --------------------------------------------------------------
        if cleanup:
            code, _ = request_json(base_url, "DELETE", f"/v1/applications/{application_id}", token=token)
            if code == 204:
                _pass(f"DELETE /v1/applications/{application_id} (cleanup)")
            else:
                _fail(f"DELETE /v1/applications/{application_id} -> {code}")
                ok = False
        else:
            _skip(f"Application cleanup skipped (PHASE5_SMOKE_CLEANUP=0), id={application_id}")

    if profile_item_id:
        if cleanup:
            code, _ = request_json(base_url, "DELETE", f"/v1/profile/items/{profile_item_id}", token=token)
            if code == 204:
                _pass(f"DELETE /v1/profile/items/{profile_item_id} (cleanup)")
            else:
                _fail(f"DELETE /v1/profile/items/{profile_item_id} -> {code}")
                ok = False
        else:
            _skip(f"Profile item cleanup skipped (PHASE5_SMOKE_CLEANUP=0), id={profile_item_id}")

    return ok


# ---------------------------------------------------------------------------
# Dry-run output
# ---------------------------------------------------------------------------

def print_dry_run_steps(mutating: bool, job_id_env: Optional[str], cleanup: bool) -> None:
    print("DRY RUN — no API calls will be made")
    print()
    print("Steps that would run:")
    print("  PASS  GET /health")
    print("  PASS  POST /v1/auth/register (synthetic user)")
    print("  PASS  POST /v1/auth/login")
    print("  PASS  GET /v1/profile/items (read-only)")
    print("  PASS  GET /v1/applications (read-only)")
    if not mutating:
        print("  SKIP  Mutating steps (PHASE5_SMOKE_ALLOW_MUTATING not set)")
        return
    print("  PASS  POST /v1/profile/items")
    print("  PASS  GET /v1/profile/items/{id}")
    print("  PASS  PATCH /v1/profile/items/{id}")
    print("  PASS  GET /v1/profile/items?item_type=project")
    print("  PASS  POST /v1/applications")
    print("  PASS  GET /v1/applications/{id}")
    print("  PASS  PATCH /v1/applications/{id}")
    print("  PASS  GET /v1/applications/{id}/readiness (no analysis)")
    print("  PASS  GET /v1/applications/{id}/interview/questions (generic fallback)")
    print("  PASS  POST /v1/applications/{id}/interview/answers")
    print("  PASS  GET /v1/applications/{id}/interview/answers")
    if job_id_env:
        print(f"  PASS  POST /v1/applications/{{id}}/attach-analysis/{job_id_env}")
        print("  PASS  GET /v1/applications/{id}/readiness (with analysis)")
        print("  PASS  POST /v1/applications/{id}/package/generate")
        print("  PASS  GET /v1/applications/{id}/package")
        print("  PASS  GET /v1/applications/{id}/package/download")
        print("  PASS  POST /v1/applications/{id}/cover-letter/generate")
        print("  PASS  GET /v1/applications/{id}/cover-letter")
        print("  PASS  PATCH /v1/applications/{id}/cover-letter")
        print("  PASS  GET /v1/applications/{id}/interview/questions (with analysis)")
    else:
        print("  SKIP  attach-analysis / package / cover-letter (PHASE5_SMOKE_JOB_ID not set)")
    print("  PASS  GET /v1/applications/<unknown-uuid> -> 404 (non-leak)")
    print("  PASS  GET /v1/profile/items/<unknown-uuid> -> 404 (non-leak)")
    if cleanup:
        print("  PASS  DELETE /v1/applications/{id} (cleanup)")
        print("  PASS  DELETE /v1/profile/items/{id} (cleanup)")
    else:
        print("  SKIP  Cleanup (PHASE5_SMOKE_CLEANUP=0)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5 backend smoke test")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and print expected steps without making API calls",
    )
    args = parser.parse_args()

    base_url = normalize_base_url(os.environ.get("API_BASE_URL", "http://localhost:8000"))
    mutating = env_flag_enabled("PHASE5_SMOKE_ALLOW_MUTATING")
    job_id_env = os.environ.get("PHASE5_SMOKE_JOB_ID") or None
    cleanup = env_flag_enabled("PHASE5_SMOKE_CLEANUP", default=True)

    print("Phase 5 backend smoke")
    print(f"  base_url : {base_url}")
    print(f"  mutating : {mutating}")
    print(f"  job_id   : {job_id_env or '(not set)'}")
    print(f"  cleanup  : {cleanup}")
    print()

    if args.dry_run:
        print_dry_run_steps(mutating, job_id_env, cleanup)
        sys.exit(0)

    passed = run_smoke(base_url, mutating, job_id_env, cleanup)
    print()
    if passed:
        print("phase5 backend smoke passed")
        sys.exit(0)
    else:
        print("phase5 backend smoke FAILED — see FAIL lines above", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
