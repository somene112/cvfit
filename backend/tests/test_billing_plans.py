"""Tests for backend-owned billing plan config (Phase 7A).

Pure config — no DB, no network, no provider SDK.
"""

from app.services.billing import plans as billing_plans


def test_exactly_two_plans():
    result = billing_plans.get_billing_plans()
    codes = {p["plan_code"] for p in result}
    assert len(result) == 2
    assert codes == {"starter_pack", "pro_demo_pack"}


def test_starter_pack_amount_and_credits():
    plan = billing_plans.get_billing_plan("starter_pack")
    assert plan["price_vnd"] == 20000
    assert plan["currency"] == "VND"
    assert plan["credits"] == {
        "analysis": 10,
        "interview": 20,
        "cover_letter": 5,
        "package": 5,
    }


def test_pro_demo_pack_amount_and_credits():
    plan = billing_plans.get_billing_plan("pro_demo_pack")
    assert plan["price_vnd"] == 49000
    assert plan["currency"] == "VND"
    assert plan["credits"] == {
        "analysis": 30,
        "interview": 60,
        "cover_letter": 15,
        "package": 15,
    }


def test_unknown_plan_returns_none():
    assert billing_plans.get_billing_plan("does_not_exist") is None


def test_validate_plan_code():
    assert billing_plans.validate_plan_code("starter_pack") is True
    assert billing_plans.validate_plan_code("pro_demo_pack") is True
    assert billing_plans.validate_plan_code("free") is False
    assert billing_plans.validate_plan_code("") is False


def test_free_allowance_matches_contract():
    allowance = billing_plans.get_free_allowance()
    assert allowance == {
        "analysis": 3,
        "interview": 10,
        "cover_letter": 2,
        "package": 2,
    }


def test_timezone_and_currency_constants():
    assert billing_plans.BILLING_TIMEZONE == "Asia/Ho_Chi_Minh"
    assert billing_plans.BILLING_CURRENCY == "VND"
    assert set(billing_plans.CREDIT_TYPES) == {
        "analysis",
        "interview",
        "cover_letter",
        "package",
    }


def test_returned_config_is_a_copy_and_cannot_mutate_source():
    plan = billing_plans.get_billing_plan("starter_pack")
    plan["price_vnd"] = 1
    plan["credits"]["analysis"] = 999
    # The authoritative config must be unchanged.
    fresh = billing_plans.get_billing_plan("starter_pack")
    assert fresh["price_vnd"] == 20000
    assert fresh["credits"]["analysis"] == 10

    allowance = billing_plans.get_free_allowance()
    allowance["analysis"] = 999
    assert billing_plans.get_free_allowance()["analysis"] == 3
