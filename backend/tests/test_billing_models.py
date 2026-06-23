"""Tests for Phase 7A billing DB models, schemas, and migration wiring.

Model assertions inspect SQLAlchemy metadata (no live DB / no PG required).
Migration assertions inspect the revision file text and EXPECTED_ALEMBIC_HEAD.
"""

import os
from pathlib import Path

# Settings requires these before importing app modules.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.db import models  # noqa: E402
from app.db import init_db  # noqa: E402
from app.schemas import billing as billing_schemas  # noqa: E402


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = BACKEND_ROOT / "alembic" / "versions" / "20260623_0001_add_billing_models.py"


def _column_names(model):
    return {c.name for c in model.__table__.columns}


def _unique_columns(model):
    """Columns covered by a single-column UNIQUE index (how SQLAlchemy renders
    ``unique=True`` on a column)."""
    unique = set()
    for index in model.__table__.indexes:
        if index.unique and len(index.columns) == 1:
            unique.update(c.name for c in index.columns)
    return unique


def _fk_targets(model):
    return {
        f"{fk.column.table.name}.{fk.column.name}"
        for col in model.__table__.columns
        for fk in col.foreign_keys
    }


# ---------------------------------------------------------------------------
# Tables registered
# ---------------------------------------------------------------------------

def test_billing_tables_registered():
    tables = set(models.Base.metadata.tables)
    assert {
        "payment_orders",
        "user_entitlements",
        "usage_events",
        "payment_webhook_events",
    }.issubset(tables)


# ---------------------------------------------------------------------------
# payment_orders
# ---------------------------------------------------------------------------

def test_payment_orders_columns_and_constraints():
    cols = _column_names(models.PaymentOrder)
    expected = {
        "id", "user_id", "provider", "provider_order_code", "provider_payment_link_id",
        "plan_code", "amount_vnd", "currency", "status", "checkout_url", "return_url",
        "cancel_url", "raw_provider_payload_json", "created_at", "updated_at",
        "paid_at", "cancelled_at", "expired_at",
    }
    assert expected.issubset(cols)
    assert "provider_order_code" in _unique_columns(models.PaymentOrder)
    assert "users.id" in _fk_targets(models.PaymentOrder)


# ---------------------------------------------------------------------------
# user_entitlements
# ---------------------------------------------------------------------------

def test_user_entitlements_columns_and_fk():
    cols = _column_names(models.UserEntitlement)
    expected = {
        "id", "user_id", "source_payment_order_id", "plan_code",
        "analysis_credits", "interview_credits", "cover_letter_credits",
        "package_credits", "starts_at", "expires_at", "created_at", "updated_at",
    }
    assert expected.issubset(cols)
    targets = _fk_targets(models.UserEntitlement)
    assert "users.id" in targets
    assert "payment_orders.id" in targets


# ---------------------------------------------------------------------------
# usage_events
# ---------------------------------------------------------------------------

def test_usage_events_columns_and_fk():
    cols = _column_names(models.UsageEvent)
    expected = {
        "id", "user_id", "event_type", "quantity", "source", "related_job_id",
        "related_application_id", "related_order_id", "created_at",
    }
    assert expected.issubset(cols)
    assert "payment_orders.id" in _fk_targets(models.UsageEvent)


# ---------------------------------------------------------------------------
# payment_webhook_events
# ---------------------------------------------------------------------------

def test_payment_webhook_events_columns_and_unique_payload_hash():
    cols = _column_names(models.PaymentWebhookEvent)
    expected = {
        "id", "provider", "provider_event_id", "provider_order_code",
        "payload_hash", "signature_hash", "status", "received_at",
        "processed_at", "error_message",
    }
    assert expected.issubset(cols)
    assert "payload_hash" in _unique_columns(models.PaymentWebhookEvent)


def test_webhook_model_stores_no_raw_secret_columns():
    # Audit-safe by design: signature/payload are stored only as hashes.
    cols = _column_names(models.PaymentWebhookEvent)
    assert "signature" not in cols
    assert "raw_payload" not in cols
    assert "payload" not in cols


# ---------------------------------------------------------------------------
# Status / vocabulary constants
# ---------------------------------------------------------------------------

def test_status_vocabularies():
    assert models.PAYMENT_ORDER_STATUS == (
        "created", "pending", "paid", "cancelled", "expired", "failed",
        "manual_review", "refunded",
    )
    assert set(models.USAGE_EVENT_TYPE) == {
        "analysis", "interview", "cover_letter", "package",
    }


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

def test_plans_response_schema_shape():
    resp = billing_schemas.BillingPlansResponse(
        currency="VND",
        plans=[
            billing_schemas.BillingPlan(
                plan_code="starter_pack",
                name="Starter Pack",
                amount=20000,
                currency="VND",
                description="x",
                credits=billing_schemas.BillingCredits(
                    analysis=10, interview=20, cover_letter=5, package=5
                ),
            )
        ],
    )
    dumped = resp.model_dump()
    assert dumped["plans"][0]["amount"] == 20000
    assert dumped["plans"][0]["credits"]["analysis"] == 10


def test_checkout_request_only_accepts_plan_code():
    req = billing_schemas.CheckoutRequest(plan_code="starter_pack")
    assert req.plan_code == "starter_pack"
    # No amount field exists on the request — the client cannot supply one.
    assert "amount" not in billing_schemas.CheckoutRequest.model_fields


def test_insufficient_credits_error_shape():
    err = billing_schemas.InsufficientCreditsError(
        message="no credits", required_credit="analysis"
    )
    dumped = err.model_dump()
    assert dumped["error"] == "insufficient_credits"
    assert dumped["required_credit"] == "analysis"
    assert dumped["pricing_url"] == "/pricing"


# ---------------------------------------------------------------------------
# Migration wiring
# ---------------------------------------------------------------------------

def test_expected_alembic_head_advanced():
    assert init_db.EXPECTED_ALEMBIC_HEAD == "20260623_0001"


def test_migration_file_revision_chain_and_tables():
    text = MIGRATION.read_text(encoding="utf-8")
    assert 'revision = "20260623_0001"' in text
    assert 'down_revision = "20260622_0001"' in text
    for table in (
        '"payment_orders"',
        '"user_entitlements"',
        '"usage_events"',
        '"payment_webhook_events"',
    ):
        assert table in text
    # Unique constraints + composite usage index.
    assert "ix_payment_orders_provider_order_code" in text
    assert "ix_payment_webhook_events_payload_hash" in text
    assert "ix_usage_events_user_id_created_at" in text
    assert '["user_id", "created_at"]' in text
