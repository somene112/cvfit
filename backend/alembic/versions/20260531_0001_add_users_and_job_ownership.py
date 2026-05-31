"""Add users and job ownership.

Revision ID: 20260531_0001
Revises: 20260522_0001
Create Date: 2026-05-31
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260531_0001"
down_revision = "20260522_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column(
        "analysis_jobs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_analysis_jobs_user_id", "analysis_jobs", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_analysis_jobs_user_id_users",
        "analysis_jobs",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_analysis_jobs_user_id_users", "analysis_jobs", type_="foreignkey")
    op.drop_index("ix_analysis_jobs_user_id", table_name="analysis_jobs")
    op.drop_column("analysis_jobs", "user_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
