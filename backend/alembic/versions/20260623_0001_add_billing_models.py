"""Add Phase 7A billing tables (payOS / VietQR credit packs).

Additive only. Creates four tables:

* ``payment_orders``        — one row per checkout attempt; source of truth for
                              amount and paid state.
* ``user_entitlements``     — purchased credit balances per user.
* ``usage_events``          — append-only ledger of credit-consuming actions.
* ``payment_webhook_events``— audit + idempotency for provider webhooks.

Constrained fields (status / event_type) are plain strings validated at the
schema/service layer (no native enum types). No provider secrets, raw signatures,
or raw webhook payloads are stored. No existing rows are touched. Amounts are
integer VND.

Revision ID: 20260623_0001
Revises: 20260622_0001
Create Date: 2026-06-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260623_0001"
down_revision = "20260622_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False, server_default="payos"),
        sa.Column("provider_order_code", sa.String(length=255), nullable=False),
        sa.Column("provider_payment_link_id", sa.String(length=255), nullable=True),
        sa.Column("plan_code", sa.String(length=50), nullable=False),
        sa.Column("amount_vnd", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="VND"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="created"),
        sa.Column("checkout_url", sa.Text(), nullable=True),
        sa.Column("return_url", sa.String(length=500), nullable=True),
        sa.Column("cancel_url", sa.String(length=500), nullable=True),
        sa.Column("raw_provider_payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("expired_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_orders_user_id", "payment_orders", ["user_id"])
    op.create_index(
        "ix_payment_orders_provider_order_code",
        "payment_orders",
        ["provider_order_code"],
        unique=True,
    )
    op.create_index("ix_payment_orders_plan_code", "payment_orders", ["plan_code"])
    op.create_index("ix_payment_orders_status", "payment_orders", ["status"])

    op.create_table(
        "user_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_payment_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plan_code", sa.String(length=50), nullable=False),
        sa.Column("analysis_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("interview_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cover_letter_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("package_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_payment_order_id"], ["payment_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_entitlements_user_id", "user_entitlements", ["user_id"])
    op.create_index(
        "ix_user_entitlements_source_payment_order_id",
        "user_entitlements",
        ["source_payment_order_id"],
    )

    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.Column("related_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_order_id"], ["payment_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_events_user_id", "usage_events", ["user_id"])
    op.create_index("ix_usage_events_event_type", "usage_events", ["event_type"])
    op.create_index("ix_usage_events_created_at", "usage_events", ["created_at"])
    # Composite index powers the Asia/Ho_Chi_Minh monthly usage window queries.
    op.create_index(
        "ix_usage_events_user_id_created_at",
        "usage_events",
        ["user_id", "created_at"],
    )

    op.create_table(
        "payment_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("provider_order_code", sa.String(length=255), nullable=True),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("signature_hash", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("received_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_webhook_events_provider", "payment_webhook_events", ["provider"])
    op.create_index(
        "ix_payment_webhook_events_provider_order_code",
        "payment_webhook_events",
        ["provider_order_code"],
    )
    op.create_index(
        "ix_payment_webhook_events_payload_hash",
        "payment_webhook_events",
        ["payload_hash"],
        unique=True,
    )
    op.create_index("ix_payment_webhook_events_status", "payment_webhook_events", ["status"])


def downgrade() -> None:
    op.drop_index("ix_payment_webhook_events_status", table_name="payment_webhook_events")
    op.drop_index("ix_payment_webhook_events_payload_hash", table_name="payment_webhook_events")
    op.drop_index("ix_payment_webhook_events_provider_order_code", table_name="payment_webhook_events")
    op.drop_index("ix_payment_webhook_events_provider", table_name="payment_webhook_events")
    op.drop_table("payment_webhook_events")

    op.drop_index("ix_usage_events_user_id_created_at", table_name="usage_events")
    op.drop_index("ix_usage_events_created_at", table_name="usage_events")
    op.drop_index("ix_usage_events_event_type", table_name="usage_events")
    op.drop_index("ix_usage_events_user_id", table_name="usage_events")
    op.drop_table("usage_events")

    op.drop_index("ix_user_entitlements_source_payment_order_id", table_name="user_entitlements")
    op.drop_index("ix_user_entitlements_user_id", table_name="user_entitlements")
    op.drop_table("user_entitlements")

    op.drop_index("ix_payment_orders_status", table_name="payment_orders")
    op.drop_index("ix_payment_orders_plan_code", table_name="payment_orders")
    op.drop_index("ix_payment_orders_provider_order_code", table_name="payment_orders")
    op.drop_index("ix_payment_orders_user_id", table_name="payment_orders")
    op.drop_table("payment_orders")
