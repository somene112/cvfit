"""Extend applications for Phase 6 Target Jobs.

Adds Target Jobs support on top of the existing ``applications`` table rather
than creating a duplicate table:

* New nullable columns: ``source_url``, ``last_readiness_score``, ``archived_at``.
* New ``application_status`` enum values: ``saved``, ``interviewing``,
  ``rejected``, ``offer``.

All changes are additive and backward compatible. Existing Phase 5
applications and statuses are untouched.

Revision ID: 20260618_0001
Revises: 20260610_0003
Create Date: 2026-06-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260618_0001"
down_revision = "20260610_0003"
branch_labels = None
depends_on = None


NEW_STATUS_VALUES = ("saved", "interviewing", "rejected", "offer")


def upgrade() -> None:
    bind = op.get_bind()

    # Additive nullable columns — safe on every dialect, no table rewrite.
    op.add_column("applications", sa.Column("source_url", sa.String(length=500), nullable=True))
    op.add_column("applications", sa.Column("last_readiness_score", sa.Integer(), nullable=True))
    op.add_column("applications", sa.Column("archived_at", sa.DateTime(), nullable=True))

    # Extend the native enum with Phase 6 statuses. ``ADD VALUE`` runs outside a
    # transaction via autocommit_block so it is safe across PostgreSQL versions.
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            for value in NEW_STATUS_VALUES:
                op.execute(
                    sa.text(f"ALTER TYPE application_status ADD VALUE IF NOT EXISTS '{value}'")
                )


def downgrade() -> None:
    op.drop_column("applications", "archived_at")
    op.drop_column("applications", "last_readiness_score")
    op.drop_column("applications", "source_url")
    # NOTE: PostgreSQL cannot drop enum values. The four Phase 6 statuses are
    # left in place intentionally; they are additive and unused by Phase 5 flows,
    # so leaving them is safe.
