"""Add analysis revision linkage.

Revision ID: 20260606_0001
Revises: 20260531_0001
Create Date: 2026-06-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260606_0001"
down_revision = "20260531_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analysis_jobs",
        sa.Column("parent_job_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("analysis_group_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("revision_number", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_analysis_jobs_parent_job_id", "analysis_jobs", ["parent_job_id"], unique=False)
    op.create_index("ix_analysis_jobs_analysis_group_id", "analysis_jobs", ["analysis_group_id"], unique=False)
    op.create_foreign_key(
        "fk_analysis_jobs_parent_job_id_analysis_jobs",
        "analysis_jobs",
        "analysis_jobs",
        ["parent_job_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_analysis_jobs_parent_job_id_analysis_jobs", "analysis_jobs", type_="foreignkey")
    op.drop_index("ix_analysis_jobs_analysis_group_id", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_parent_job_id", table_name="analysis_jobs")
    op.drop_column("analysis_jobs", "revision_number")
    op.drop_column("analysis_jobs", "analysis_group_id")
    op.drop_column("analysis_jobs", "parent_job_id")
