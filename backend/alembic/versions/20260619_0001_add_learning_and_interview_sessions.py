"""Add Phase 6 Learning Roadmap and Interview v2 session tables.

Adds four additive tables:

* ``learning_tasks``
* ``interview_sessions``
* ``interview_session_questions``
* ``interview_session_answers``

Constrained fields (priority / task_type / status / difficulty / question_type)
are plain strings validated at the Pydantic schema layer — no native enum types
are introduced. The Phase 5 ``interview_answers`` table is untouched.

Revision ID: 20260619_0001
Revises: 20260618_0001
Create Date: 2026-06-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260619_0001"
down_revision = "20260618_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("skill", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("task_type", sa.String(length=30), nullable=False, server_default="practice"),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_to_add", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="todo"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_job_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["analysis_job_id"], ["analysis_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_learning_tasks_user_id", "learning_tasks", ["user_id"])
    op.create_index("ix_learning_tasks_target_job_id", "learning_tasks", ["target_job_id"])
    op.create_index("ix_learning_tasks_application_id", "learning_tasks", ["application_id"])
    op.create_index("ix_learning_tasks_analysis_job_id", "learning_tasks", ["analysis_job_id"])
    op.create_index("ix_learning_tasks_status", "learning_tasks", ["status"])

    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_type", sa.String(length=30), nullable=False, server_default="mixed"),
        sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_job_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["analysis_job_id"], ["analysis_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])
    op.create_index("ix_interview_sessions_target_job_id", "interview_sessions", ["target_job_id"])
    op.create_index("ix_interview_sessions_application_id", "interview_sessions", ["application_id"])
    op.create_index("ix_interview_sessions_analysis_job_id", "interview_sessions", ["analysis_job_id"])
    op.create_index("ix_interview_sessions_status", "interview_sessions", ["status"])

    op.create_table(
        "interview_session_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_type", sa.String(length=30), nullable=False, server_default="behavioral"),
        sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("related_evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rubric_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_session_questions_session_id", "interview_session_questions", ["session_id"])

    op.create_table(
        "interview_session_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("score_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("feedback_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["interview_session_questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_session_answers_session_id", "interview_session_answers", ["session_id"])
    op.create_index("ix_interview_session_answers_question_id", "interview_session_answers", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_interview_session_answers_question_id", table_name="interview_session_answers")
    op.drop_index("ix_interview_session_answers_session_id", table_name="interview_session_answers")
    op.drop_table("interview_session_answers")

    op.drop_index("ix_interview_session_questions_session_id", table_name="interview_session_questions")
    op.drop_table("interview_session_questions")

    op.drop_index("ix_interview_sessions_status", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_analysis_job_id", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_application_id", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_target_job_id", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")

    op.drop_index("ix_learning_tasks_status", table_name="learning_tasks")
    op.drop_index("ix_learning_tasks_analysis_job_id", table_name="learning_tasks")
    op.drop_index("ix_learning_tasks_application_id", table_name="learning_tasks")
    op.drop_index("ix_learning_tasks_target_job_id", table_name="learning_tasks")
    op.drop_index("ix_learning_tasks_user_id", table_name="learning_tasks")
    op.drop_table("learning_tasks")
