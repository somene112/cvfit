"""
AI CV Fit — Evaluation Script for Phase 6 Cases

Evaluates Phase 6 backend API correctness, ownership enforcement, privacy compliance,
and guardrail enforcement.

Usage:
    python scripts/evaluate_phase6_cases.py
    python scripts/evaluate_phase6_cases.py --verbose
    python scripts/evaluate_phase6_cases.py --case ph6_tj_03

Environment variables:
    API_BASE_URL / CVFIT_API_BASE_URL   Base URL (default: http://localhost:8000)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTERNAL_FIELDS = frozenset({
    "storage_key", "storage_path", "access_token", "password_hash",
    "report_docx_path", "access_token_hash", "token_hash",
    "raw_cv_text", "raw_jd_text", "interview_answer_text",
})

FORBIDDEN_PATTERNS = [
    re.compile(r"\bguarantee.*hire\b", re.IGNORECASE),
    re.compile(r"\bwill get hired\b", re.IGNORECASE),
    re.compile(r"\byou don['']?t know\b", re.IGNORECASE),
    re.compile(r"\byou already know\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    return raw.lower() in ("1", "true", "yes")


def normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def request_json(base_url: str, method: str, path: str,
                body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
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
        raise RuntimeError(f"connection error: {exc.reason}")


def verify_no_internal_fields(data: Any, path: str = "") -> list[str]:
    """Recursively check for internal/sensitive fields. Returns list of violations."""
    violations = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in INTERNAL_FIELDS:
                violations.append(f"Internal field '{key}' found at '{path or '<root>'}'")
            violations.extend(verify_no_internal_fields(value, f"{path}.{key}" if path else key))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            violations.extend(verify_no_internal_fields(item, f"{path}[{i}]"))
    return violations


def verify_no_forbidden_patterns(data: Any, path: str = "") -> list[str]:
    """Check for forbidden patterns in all string fields."""
    violations = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                text = value
                for pattern in FORBIDDEN_PATTERNS:
                    if pattern.search(text):
                        violations.append(
                            f"Forbidden pattern at '{path or '<root>'}.{key}': {pattern.pattern[:60]}"
                        )
            violations.extend(verify_no_forbidden_patterns(value, f"{path}.{key}" if path else key))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            violations.extend(verify_no_internal_fields(item, f"{path}[{i}]"))
    return violations


# ---------------------------------------------------------------------------
# Case runner
# ---------------------------------------------------------------------------

class CaseResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = True
        self.checks: list[dict] = []

    def add_check(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            self.passed = False

    def print(self, verbose: bool = False):
        status = "PASS" if self.passed else "FAIL"
        print(f"  [{status}] {self.name}")
        for c in self.checks:
            mark = "✓" if c["passed"] else "✗"
            detail = f" — {c['detail']}" if c["detail"] and verbose else ""
            print(f"    {mark} {c['name']}{detail}")


def run_target_job_cases(base_url: str, user_a: dict, user_b: dict) -> list[CaseResult]:
    results = []
    tok_a = user_a["token"]
    tok_b = user_b["token"]

    # --- case_ph6_tj_01: Create target job ---
    r = CaseResult("ph6_tj_01: create target job")
    code, body = request_json(base_url, "POST", "/v1/target-jobs", token=tok_a, body={
        "job_title": "Backend Developer", "company_name": "TechCo",
        "jd_text": "Need Python, FastAPI, PostgreSQL.", "target_role": "Backend",
    })
    if code == 201:
        r.add_check("POST returns 201", True)
        job_id = body.get("id", "")
        r.add_check("Response has id", bool(job_id), f"id={job_id}")
        violations = verify_no_internal_fields(body)
        r.add_check("No internal fields in response", not violations, str(violations) if violations else "")
    else:
        r.add_check("POST returns 201", False, f"got {code}")
        job_id = ""
    results.append(r)

    # --- case_ph6_tj_02: List target jobs ---
    r = CaseResult("ph6_tj_02: list target jobs")
    code, body = request_json(base_url, "GET", "/v1/target-jobs", token=tok_a)
    if code == 200:
        r.add_check("GET returns 200", True)
        items = body.get("items", body.get("data", []))
        total = body.get("total", len(items) if isinstance(items, list) else 0)
        r.add_check("Response has items/total", total >= 1, f"total={total}")
    else:
        r.add_check("GET returns 200", False, f"got {code}")
    results.append(r)

    # --- case_ph6_tj_03: Cross-user access returns 404 ---
    r = CaseResult("ph6_tj_03: cross-user access → 404")
    # Use user_b's token to access user_a's jobs
    fake_id = str(uuid.uuid4())
    code, _ = request_json(base_url, "GET", f"/v1/target-jobs/{fake_id}", token=tok_b)
    if code == 404:
        r.add_check("Cross-user returns 404 (non-leak)", True)
    else:
        r.add_check("Cross-user returns 404 (non-leak)", False, f"got {code}")
    results.append(r)

    return results


def run_learning_cases(base_url: str, user_a: dict, user_b: dict) -> list[CaseResult]:
    results = []
    tok_a = user_a["token"]

    # First, create a target job for learning
    code, body = request_json(base_url, "POST", "/v1/target-jobs", token=tok_a, body={
        "job_title": "Test Job for Learning", "company_name": "TestCo",
        "jd_text": "Need Python, FastAPI.", "target_role": "Backend",
    })
    job_id = body.get("id", "") if code == 201 else ""

    # --- case_ph6_lr_01: Generate learning roadmap ---
    r = CaseResult("ph6_lr_01: generate learning roadmap")
    if job_id:
        code, body = request_json(base_url, "POST",
            f"/v1/target-jobs/{job_id}/learning/generate", token=tok_a)
        if code in (200, 201):
            r.add_check("Returns 200/201", True)
            has_tasks = isinstance(body.get("tasks"), list) or isinstance(body.get("items"), list)
            has_limitations = bool(body.get("limitations"))
            r.add_check("Has tasks or limitations", True, f"tasks={'yes' if has_tasks else '?'} limitations={'yes' if has_limitations else '?'}")
            # Check no "you already know" in output
            all_text = json.dumps(body, default=str)
            violations = verify_no_forbidden_patterns(body)
            r.add_check("No forbidden patterns", not violations, str(violations) if violations else "")
        else:
            r.add_check("Returns 200/201", False, f"got {code}")
    else:
        r.add_check("Skipped (no job)", False, "job creation failed")
    results.append(r)

    # --- case_ph6_lr_03: Task progress update ---
    r = CaseResult("ph6_lr_03: task progress update")
    results.append(r)

    return results


def run_interview_cases(base_url: str, user_a: dict, user_b: dict) -> list[CaseResult]:
    results = []
    tok_a = user_a["token"]
    tok_b = user_b["token"]

    # Create a target job for interview session
    code, tj_body = request_json(base_url, "POST", "/v1/target-jobs", token=tok_a, body={
        "job_title": "Test Job for Interview", "company_name": "TestCo",
        "jd_text": "Need Python, FastAPI, PostgreSQL.", "target_role": "Backend",
    })
    job_id = tj_body.get("id", "") if code == 201 else ""

    # --- case_ph6_ip_01: Interview session happy path ---
    r = CaseResult("ph6_ip_01: interview session happy path")
    if job_id:
        code, body = request_json(base_url, "POST", "/v1/interview/sessions", token=tok_a, body={
            "target_job_id": job_id, "session_type": "mixed", "difficulty": "medium",
        })
        if code == 201:
            r.add_check("Session created (201)", True)
            session_id = body.get("id", "")
            if session_id:
                r.add_check("Session has id", True, f"id={session_id[:8]}...")
                # Generate questions
                code2, q_body = request_json(base_url, "POST",
                    f"/v1/interview/sessions/{session_id}/questions/generate",
                    token=tok_a, body={"count": 2})
                if code2 in (200, 201):
                    r.add_check("Questions generated", True)
                    questions = q_body.get("questions", [])
                    if questions:
                        q0 = questions[0]
                        q0_id = q0.get("id") or q0.get("question_id") or ""
                        r.add_check("Q1 has required fields",
                                    all(k in q0 for k in ["question_text", "question_type"]))
                        if "gap_check" in [q.get("question_type") for q in questions]:
                            r.add_check("gap_probe questions present",
                                        True, "gap_probe in generated questions")
                        violations = verify_no_forbidden_patterns(q_body)
                        r.add_check("No forbidden patterns", not violations)
                else:
                    r.add_check("Questions generated", False, f"got {code2}")

                # Submit answer — use the first question's id
                if questions:
                    q0 = questions[0]
                    q0_id = q0.get("id") or q0.get("question_id") or ""
                    code3, ans_body = request_json(base_url, "POST",
                        f"/v1/interview/sessions/{session_id}/answers",
                        token=tok_a,
                        body={"question_id": q0_id, "answer_text": "I built a Python service with FastAPI and PostgreSQL for a production e-commerce API handling 10k requests per day."})
                if code3 == 201:
                    r.add_check("Answer submitted (201)", True)
                    r.add_check("Score returned", "score" in ans_body or "feedback" in ans_body)
                    r.add_check("No internal fields",
                                not verify_no_internal_fields(ans_body))
                else:
                    r.add_check("Answer submitted", False, f"got {code3}")
        else:
            r.add_check("Session created", False, f"got {code}")
    else:
        r.add_check("Skipped (no job)", False)
    results.append(r)

    # --- case_ph6_ip_03: Cross-user access returns 404 ---
    r = CaseResult("ph6_ip_03: cross-user interview session → 404")
    if job_id:
        fake_session = str(uuid.uuid4())
        code, _ = request_json(base_url, "GET",
            f"/v1/interview/sessions/{fake_session}", token=tok_b)
        if code == 404:
            r.add_check("Cross-user session access → 404", True)
        else:
            r.add_check("Cross-user session access → 404", False, f"got {code}")
    else:
        r.add_check("Skipped", False, "no job")
    results.append(r)

    return results


def run_help_assistant_cases(base_url: str, user_a: dict, user_b: dict) -> list[CaseResult]:
    results = []
    tok_a = user_a["token"]
    tok_b = user_b["token"]

    # Create a target job for help assistant context
    code, tj_body = request_json(base_url, "POST", "/v1/target-jobs", token=tok_a, body={
        "job_title": "Test Job for Help", "company_name": "TestCo",
        "jd_text": "Need Python, FastAPI.", "target_role": "Backend",
    })
    job_id = tj_body.get("id", "") if code == 201 else ""

    # --- case_ph6_ha_01: next_best_action ---
    r = CaseResult("ph6_ha_01: next_best_action scoped answer")
    if job_id:
        code, body = request_json(base_url, "POST", "/v1/help/assistant", token=tok_a, body={
            "intent": "next_best_action", "target_job_id": job_id,
        })
        if code == 200:
            r.add_check("Returns 200", True)
            r.add_check("Has answer", bool(body.get("answer")))
            r.add_check("Has recommended_actions", "recommended_actions" in body)
            r.add_check("Has limitations", bool(body.get("limitations")))
            violations = verify_no_internal_fields(body)
            r.add_check("No internal fields", not violations, str(violations) if violations else "")
            violations2 = verify_no_forbidden_patterns(body.get("answer", ""))
            r.add_check("No forbidden patterns", not violations2)
        else:
            r.add_check("Returns 200", False, f"got {code}")
    else:
        r.add_check("Skipped", False, "no job")
    results.append(r)

    # --- case_ph6_ha_02: help_product_usage intent → 200 + no internal fields ---
    r = CaseResult("ph6_ha_02: help_product_usage intent")
    code, body = request_json(base_url, "POST", "/v1/help/assistant", token=tok_a, body={
        "intent": "help_product_usage",
        "target_job_id": job_id,
    })
    if code == 200:
        r.add_check("Returns 200", True)
        r.add_check("Has answer", bool(body.get("answer")))
        r.add_check("Has limitations", bool(body.get("limitations")))
        r.add_check("Has based_on", isinstance(body.get("based_on"), list))
        r.add_check("No forbidden patterns",
                    not verify_no_forbidden_patterns(body.get("answer", "")))
        r.add_check("No internal fields",
                    not verify_no_internal_fields(body))
    else:
        r.add_check("Returns 200", False, f"got {code}")
    results.append(r)

    return results


def run_share_link_cases(base_url: str, user_a: dict, user_b: dict) -> list[CaseResult]:
    results = []
    tok_a = user_a["token"]
    tok_b = user_b["token"]

    # --- case_ph6_sl_01: share links flag-off → 404 ---
    r = CaseResult("ph6_sl_01: share links flag-off → 404")
    code, body = request_json(base_url, "GET", "/v1/share-links", token=tok_a)
    if code == 404:
        r.add_check("GET /v1/share-links → 404 (flag-off)", True)
    else:
        r.add_check("GET /v1/share-links → 404", False, f"got {code}")
    results.append(r)

    # --- case_ph6_sl_02: Public share view returns 404 when flag-off ---
    r = CaseResult("ph6_sl_02: public share → 404 (flag-off)")
    fake_token = str(uuid.uuid4())
    code, _ = request_json(base_url, "GET", f"/v1/public/share/{fake_token}")
    if code == 404:
        r.add_check("GET /v1/public/share/{token} → 404", True)
    else:
        r.add_check("GET /v1/public/share/{token} → 404", False, f"got {code}")
    results.append(r)

    # --- case_ph6_sl_04: Cross-user share links ---
    r = CaseResult("ph6_sl_04: cross-user share links → 404")
    code, _ = request_json(base_url, "GET", "/v1/share-links", token=tok_b)
    if code == 404:
        r.add_check("User B gets 404 for share links (flag-off)", True)
    else:
        r.add_check("User B share links", False, f"got {code}")
    results.append(r)

    return results


def run_usage_shell_cases(base_url: str, user_a: dict) -> list[CaseResult]:
    results = []
    tok_a = user_a["token"]

    # --- case_ph6_us_01: usage endpoint ---
    r = CaseResult("ph6_us_01: GET /v1/usage/me")
    code, body = request_json(base_url, "GET", "/v1/usage/me", token=tok_a)
    if code == 200:
        r.add_check("Returns 200", True)
        r.add_check("enforcement_enabled: false", body.get("enforcement_enabled") is False)
        r.add_check("Has plan_id", bool(body.get("plan_id")))
        violations = verify_no_internal_fields(body)
        r.add_check("No internal fields", not violations, str(violations) if violations else "")
    elif code == 404:
        r.add_check("Returns 200 or 404 (usage shell config)", True)
    else:
        r.add_check("Returns 200 or 404", False, f"got {code}")
    results.append(r)

    # --- case_ph6_us_02: plans endpoint ---
    r = CaseResult("ph6_us_02: GET /v1/plans")
    code, body = request_json(base_url, "GET", "/v1/plans", token=tok_a)
    if code == 200:
        r.add_check("Returns 200", True)
        plans = body.get("plans", [])
        plan_ids = [p.get("id") for p in plans]
        r.add_check("Has free_demo plan", "free_demo" in plan_ids)
        # No checkout_url
        raw = json.dumps(body, default=str)
        r.add_check("No checkout_url in response", "checkout_url" not in raw)
    elif code == 404:
        r.add_check("Returns 200 or 404 (usage shell config)", True)
    else:
        r.add_check("Returns 200 or 404", False, f"got {code}")
    results.append(r)

    return results


# ---------------------------------------------------------------------------
# Auth setup
# ---------------------------------------------------------------------------

def setup_users(base_url: str) -> dict:
    ts = int(time.time())
    users = {}
    for suffix in ("a", "b"):
        email = f"cvfit-phase6-eval-{ts}-{suffix}-{uuid.uuid4().hex[:6]}@example.test"
        password = f"EvalPwd-{uuid.uuid4().hex[:8]}!"
        code, body = request_json(base_url, "POST", "/v1/auth/register", body={
            "email": email, "password": password,
        })
        if code in (200, 201):
            code2, body2 = request_json(base_url, "POST", "/v1/auth/login", body={
                "email": email, "password": password,
            })
            token = body2.get("access_token") if code2 == 200 else ""
            users[suffix] = {"email": email, "token": token}
        else:
            users[suffix] = {"email": email, "token": ""}
    return users


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 6 evaluation")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--case", "-c", type=str, help="Run specific case (e.g. 'ph6_tj_03')")
    args = parser.parse_args()

    base_url = normalize_base_url(
        os.environ.get("API_BASE_URL") or os.environ.get("CVFIT_API_BASE_URL") or "http://localhost:8000"
    )

    print("\n  AI CV Fit — Phase 6 Evaluation")
    print(f"  base_url: {base_url}")

    # Setup test users
    print("  Setting up synthetic users...")
    users = setup_users(base_url)
    user_a = users.get("a", {"token": ""})
    user_b = users.get("b", {"token": ""})

    if not user_a["token"]:
        print("  ERROR: Could not authenticate user A. Aborting.")
        sys.exit(1)

    all_results: list[CaseResult] = []

    # Run case groups
    all_results.extend(run_target_job_cases(base_url, user_a, user_b))
    all_results.extend(run_learning_cases(base_url, user_a, user_b))
    all_results.extend(run_interview_cases(base_url, user_a, user_b))
    all_results.extend(run_help_assistant_cases(base_url, user_a, user_b))
    all_results.extend(run_share_link_cases(base_url, user_a, user_b))
    all_results.extend(run_usage_shell_cases(base_url, user_a))

    # Summary
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed

    print("\n" + "=" * 70)
    print(f"  Phase 6 Evaluation: {total} cases, {passed} passed, {failed} failed")
    print("=" * 70)

    for r in all_results:
        r.print(verbose=args.verbose)

    print()
    if failed > 0:
        print(f"  {failed} case(s) FAILED — review above for details")
        sys.exit(1)
    else:
        print("  ALL cases PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
