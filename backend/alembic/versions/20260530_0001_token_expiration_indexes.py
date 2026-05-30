"""Add access_token_expires_at and performance indexes.

Revision ID: 20260530_0001
Revises: 20260522_0001
Create Date: 2026-05-30

Changes:
  - analysis_jobs.access_token_expires_at (DateTime, nullable)
  - ix_analysis_jobs_cv_file_id       ON analysis_jobs(cv_file_id)
  - ix_analysis_jobs_jd_id           ON analysis_jobs(jd_id)
  - ix_analysis_jobs_status          ON analysis_jobs(status)
  - ix_analysis_jobs_created_at      ON analysis_jobs(created_at)
  - ix_text_embeddings_owner         ON text_embeddings(owner_type, owner_id)
  - ix_text_embeddings_created_at    ON text_embeddings(created_at)
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa   # ← Thêm dòng này nếu chưa có

revision = "20260530_0001"
down_revision = "20260522_0001"
branch_labels = None
depends_on = None





def upgrade() -> None:
    # Thêm cột
    op.add_column(
        "analysis_jobs",
        sa.Column("access_token_expires_at", sa.DateTime(), nullable=True)
    )

    # Các index (phần này có vẻ ổn)
    op.create_index("ix_analysis_jobs_cv_file_id", "analysis_jobs", ["cv_file_id"])
    op.create_index("ix_analysis_jobs_jd_id", "analysis_jobs", ["jd_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])
    op.create_index("ix_analysis_jobs_created_at", "analysis_jobs", ["created_at"])

    op.create_index("ix_text_embeddings_owner", "text_embeddings", ["owner_type", "owner_id"])
    op.create_index("ix_text_embeddings_created_at", "text_embeddings", ["created_at"])


def downgrade() -> None:
    op.drop_column("analysis_jobs", "access_token_expires_at")

    # Drop indexes
    op.drop_index("ix_analysis_jobs_cv_file_id", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_jd_id", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_created_at", table_name="analysis_jobs")

    op.drop_index("ix_text_embeddings_owner", table_name="text_embeddings")
    op.drop_index("ix_text_embeddings_created_at", table_name="text_embeddings")
