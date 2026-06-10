"""Add application_artifacts table.

Revision ID: 20260610_0002
Revises: 20260610_0001
Create Date: 2026-06-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260610_0002"
down_revision = "20260610_0001"
branch_labels = None
depends_on = None

_ARTIFACT_TYPE_VALUES = (
    "application_package",
    "cover_letter_draft",
    "interview_practice_result",
    "readiness_summary",
)


def upgrade() -> None:
    artifact_type = postgresql.ENUM(
        *_ARTIFACT_TYPE_VALUES,
        name="application_artifact_type",
        create_type=False,
    )
    postgresql.ENUM(*_ARTIFACT_TYPE_VALUES, name="application_artifact_type").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "application_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artifact_type", artifact_type, nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_application_artifacts_user_id", "application_artifacts", ["user_id"], unique=False)
    op.create_index("ix_application_artifacts_application_id", "application_artifacts", ["application_id"], unique=False)
    op.create_index("ix_application_artifacts_artifact_type", "application_artifacts", ["artifact_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_application_artifacts_artifact_type", table_name="application_artifacts")
    op.drop_index("ix_application_artifacts_application_id", table_name="application_artifacts")
    op.drop_index("ix_application_artifacts_user_id", table_name="application_artifacts")
    op.drop_table("application_artifacts")
    sa.Enum(name="application_artifact_type").drop(op.get_bind(), checkfirst=True)
