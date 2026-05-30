"""Add access_token_expires_at and performance indexes."""

# revision identifiers, used by Alembic.
revision = "20260530_0001"
down_revision = "20260522_0001"
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # Thêm cột mới
    op.add_column(
        "analysis_jobs",
        sa.Column("access_token_expires_at", sa.DateTime(), nullable=True)
    )

    # Tạo các index performance
    op.create_index(
        "ix_analysis_jobs_cv_file_id", "analysis_jobs", ["cv_file_id"]
    )
    op.create_index(
        "ix_analysis_jobs_jd_id", "analysis_jobs", ["jd_id"]
    )
    op.create_index(
        "ix_analysis_jobs_status", "analysis_jobs", ["status"]
    )
    op.create_index(
        "ix_analysis_jobs_created_at", "analysis_jobs", ["created_at"]
    )

    op.create_index(
        "ix_text_embeddings_owner", 
        "text_embeddings", 
        ["owner_type", "owner_id"]
    )
    op.create_index(
        "ix_text_embeddings_created_at", 
        "text_embeddings", 
        ["created_at"]
    )


def downgrade() -> None:
    # Xóa index
    op.drop_index("ix_analysis_jobs_cv_file_id", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_jd_id", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_created_at", table_name="analysis_jobs")

    op.drop_index("ix_text_embeddings_owner", table_name="text_embeddings")
    op.drop_index("ix_text_embeddings_created_at", table_name="text_embeddings")

    # Xóa cột
    op.drop_column("analysis_jobs", "access_token_expires_at")