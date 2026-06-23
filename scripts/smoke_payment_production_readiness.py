#!/usr/bin/env python3
"""This script does not perform real payment and does not verify webhook delivery."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: Any


def parse_bool(value: str | None) -> bool:
    return (value or "false").strip().lower() in {"1", "true", "yes", "on"}


def normalize_base_url(name: str, value: str | None) -> str:
    candidate = (value or "").strip().rstrip("/")
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be a valid http(s) base URL")
    return candidate


def request_json(
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> HttpResult:
    headers = {"Accept": "application/json", "User-Agent": "cvfit-payment-readiness/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(
        urljoin(f"{base_url}/", path.lstrip("/")),
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(256_000)
            return HttpResult(response.status, _decode_json(raw))
    except HTTPError as exc:
        return HttpResult(exc.code, _decode_json(exc.read(256_000)))
    except URLError as exc:
        raise RuntimeError(f"request failed for {path}: {exc.reason}") from exc


def request_page(base_url: str, path: str, timeout: float) -> int:
    request = Request(
        urljoin(f"{base_url}/", path.lstrip("/")),
        headers={"User-Agent": "cvfit-payment-readiness/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read(1)
            return response.status
    except HTTPError as exc:
        return exc.code
    except URLError as exc:
        raise RuntimeError(f"frontend request failed for {path}: {exc.reason}") from exc


def _decode_json(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def validate_checkout(body: Any) -> list[str]:
    if not isinstance(body, dict):
        return ["checkout response is not a JSON object"]
    required = ("payment_order_id", "provider", "status", "checkout_url")
    failures = [f"checkout response missing {key}" for key in required if not body.get(key)]
    if body.get("provider") != "payos":
        failures.append("checkout provider is not payos")
    if body.get("status") != "pending":
        failures.append("checkout order is not pending")
    return failures


def run(args: argparse.Namespace) -> int:
    try:
        api_base = normalize_base_url("API_BASE_URL", os.getenv("API_BASE_URL"))
        frontend_base = normalize_base_url(
            "FRONTEND_BASE_URL", os.getenv("FRONTEND_BASE_URL")
        )
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    token = os.getenv("AUTH_TOKEN") or None
    expect_enabled = parse_bool(os.getenv("EXPECT_BILLING_ENABLED"))
    failures: list[str] = []

    health = request_json(api_base, "/health", timeout=args.timeout)
    if health.status != 200 or not isinstance(health.body, dict):
        failures.append(f"backend health failed with HTTP {health.status}")
    else:
        print("PASS backend /health")

    acceptable_frontend = {200, 301, 302, 303, 307, 308, 401, 403}
    for path in ("/pricing", "/billing", "/billing/success", "/billing/cancel"):
        status = request_page(frontend_base, path, args.timeout)
        if status not in acceptable_frontend:
            failures.append(f"frontend {path} returned HTTP {status}")
        else:
            print(f"PASS frontend {path} HTTP {status} (render or auth response accepted)")

    if not token:
        print("SKIP authenticated billing checks: set AUTH_TOKEN for a controlled test user")
    else:
        for path in ("/v1/billing/plans", "/v1/billing/usage", "/v1/billing/orders"):
            result = request_json(api_base, path, token=token, timeout=args.timeout)
            if result.status != 200 or not isinstance(result.body, dict):
                failures.append(f"authenticated {path} failed with HTTP {result.status}")
            else:
                print(f"PASS authenticated {path}")

        checkout = request_json(
            api_base,
            "/v1/billing/checkout",
            token=token,
            method="POST",
            payload={"plan_code": "starter_pack"},
            timeout=args.timeout,
        )
        if expect_enabled:
            if checkout.status not in {200, 201}:
                failures.append(f"enabled checkout failed with HTTP {checkout.status}")
            else:
                failures.extend(validate_checkout(checkout.body))
                if isinstance(checkout.body, dict):
                    print(
                        "PASS checkout",
                        f"payment_order_id={checkout.body.get('payment_order_id')}",
                        f"provider={checkout.body.get('provider')}",
                        f"status={checkout.body.get('status')}",
                        f"checkout_url_present={bool(checkout.body.get('checkout_url'))}",
                    )
        elif checkout.status != 503:
            failures.append(
                f"disabled checkout expected HTTP 503 but received HTTP {checkout.status}"
            )
        else:
            print("PASS disabled checkout returned safe HTTP 503")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("PASS payment readiness smoke (no real payment or webhook verification performed)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check deployed CVFit billing/frontend readiness without contacting payOS "
            "or performing a real payment. Configuration comes from API_BASE_URL, "
            "FRONTEND_BASE_URL, optional AUTH_TOKEN, and optional "
            "EXPECT_BILLING_ENABLED (default false)."
        )
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="request timeout in seconds")
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
