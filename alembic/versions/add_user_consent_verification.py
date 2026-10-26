"""Add consent capture and email verification columns to users table.

Revision ID: add_user_consent_verification
Revises: recoveries_ledger
Create Date: 2026-10-26

Adds:
- users.terms_accepted_at: timestamp when user accepted terms of service
  and privacy policy during signup. NULL means consent not yet recorded.
- users.email_verified_at: timestamp when email was verified.
  NULL means email not yet verified.

B-04, B-05: Email verification and consent capture (audit 2026-10-26).
"""

from alembic import op
import sqlalchemy as sa

revision = "add_user_consent_verification"
down_revision = "recoveries_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]
    if "terms_accepted_at" not in columns:
        op.add_column(
            "users",
            sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "email_verified_at" not in columns:
        op.add_column(
            "users",
            sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]
    if "email_verified_at" in columns:
        op.drop_column("users", "email_verified_at")
    if "terms_accepted_at" in columns:
        op.drop_column("users", "terms_accepted_at")
