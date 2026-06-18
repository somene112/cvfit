"""Add Phase 6 Shareable Readiness ``share_links`` table.

Additive only. Stores the SHA-256 hash of the share token (never the raw token).
``target_id`` references an Application (target job or application) but is left as
a plain UUID column (no FK) so a share link can outlive a hard-deleted target.

Revision ID: 20260620_0001
Revises: 20260619_0001
Create Date: 2026-06-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260620_0001"
down_revision = "20260619_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "share_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("visibility_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_share_links_user_id", "share_links", ["user_id"])
    op.create_index("ix_share_links_target", "share_links", ["target_type", "target_id"])
    op.create_index("ix_share_links_token_hash", "share_links", ["token_hash"], unique=True)
    op.create_index("ix_share_links_revoked_at", "share_links", ["revoked_at"])
    op.create_index("ix_share_links_expires_at", "share_links", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_share_links_expires_at", table_name="share_links")
    op.drop_index("ix_share_links_revoked_at", table_name="share_links")
    op.drop_index("ix_share_links_token_hash", table_name="share_links")
    op.drop_index("ix_share_links_target", table_name="share_links")
    op.drop_index("ix_share_links_user_id", table_name="share_links")
    op.drop_table("share_links")
