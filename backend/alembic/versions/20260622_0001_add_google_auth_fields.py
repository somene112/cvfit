"""Add Google Sign-In fields to ``users``.

Additive and reversible. Adds nullable federated-identity columns and relaxes
``password_hash`` to NULLABLE so Google-only accounts can exist without a local
password. No data is dropped and existing password users are untouched.

Revision ID: 20260622_0001
Revises: 20260620_0001
Create Date: 2026-06-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260622_0001"
down_revision = "20260620_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("auth_provider", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("picture_url", sa.String(length=500), nullable=True))
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    # Relax password_hash so federated accounts need no local password.
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    # Restore NOT NULL only if no NULL password hashes exist; backfill a sentinel
    # is intentionally avoided to prevent creating usable-looking empty hashes.
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=False)
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_column("users", "picture_url")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "google_sub")
