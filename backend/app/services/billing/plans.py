"""Backend-owned billing plan configuration (Phase 7A).

This module is the single source of truth for credit-pack pricing and the free
monthly allowance. Amounts are integer VND and are **never** taken from client
input — the checkout endpoint (a later PR) resolves the amount from here by
``plan_code`` only.

No provider API calls, no secrets, no DB access.
"""

from __future__ import annotations

from typing import Optional


# Monthly usage windows (free allowance) are computed in this timezone.
BILLING_TIMEZONE = "Asia/Ho_Chi_Minh"

# Currency is fixed to VND for the MVP.
BILLING_CURRENCY = "VND"

# Credit types consumed by gated actions (kept in one place for validation).
CREDIT_TYPES = ("analysis", "interview", "cover_letter", "package")


# Authoritative one-time credit packs. Keyed by ``plan_code``.
_PLANS: dict[str, dict] = {
    "starter_pack": {
        "plan_code": "starter_pack",
        "name": "Starter Pack",
        "price_vnd": 20000,
        "currency": BILLING_CURRENCY,
        "description": "Entry credit pack for trying the paid features.",
        "credits": {
            "analysis": 10,
            "interview": 20,
            "cover_letter": 5,
            "package": 5,
        },
    },
    "pro_demo_pack": {
        "plan_code": "pro_demo_pack",
        "name": "Pro Demo Pack",
        "price_vnd": 49000,
        "currency": BILLING_CURRENCY,
        "description": "Larger credit pack for a full demo run.",
        "credits": {
            "analysis": 30,
            "interview": 60,
            "cover_letter": 15,
            "package": 15,
        },
    },
}


# Free allowance per calendar month (Asia/Ho_Chi_Minh), per credit type.
_FREE_ALLOWANCE: dict[str, int] = {
    "analysis": 3,
    "interview": 10,
    "cover_letter": 2,
    "package": 2,
}


def get_billing_plans() -> list[dict]:
    """Return all plans as a list, in a stable order, as deep-ish copies.

    Copies are returned so callers cannot mutate the authoritative config.
    """
    return [_copy_plan(_PLANS[code]) for code in _PLANS]


def get_billing_plan(plan_code: str) -> Optional[dict]:
    """Return a single plan by ``plan_code``, or ``None`` if unknown."""
    plan = _PLANS.get(plan_code)
    return _copy_plan(plan) if plan is not None else None


def get_free_allowance() -> dict[str, int]:
    """Return the free monthly allowance per credit type (a copy)."""
    return dict(_FREE_ALLOWANCE)


def validate_plan_code(plan_code: str) -> bool:
    """Return True if ``plan_code`` is a known plan."""
    return plan_code in _PLANS


def _copy_plan(plan: dict) -> dict:
    copied = dict(plan)
    copied["credits"] = dict(plan["credits"])
    return copied
