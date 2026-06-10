"""add interview_answers table

Revision ID: 20260610_0003
Revises: 20260610_0002
Create Date: 2026-06-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260610_0003"
down_revision = "20260610_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_jobs.id"), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("rubric_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("feedback_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_interview_answers_user_id", "interview_answers", ["user_id"])
    op.create_index("ix_interview_answers_application_id", "interview_answers", ["application_id"])
    op.create_index("ix_interview_answers_job_id", "interview_answers", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_interview_answers_job_id", table_name="interview_answers")
    op.drop_index("ix_interview_answers_application_id", table_name="interview_answers")
    op.drop_index("ix_interview_answers_user_id", table_name="interview_answers")
    op.drop_table("interview_answers")
