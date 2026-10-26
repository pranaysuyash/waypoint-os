"""Add email_verification_tokens table.

Revision ID: add_email_verification_tokens
Revises: add_user_consent_verification
Create Date: 2026-10-26

B-04: Email verification (audit 2026-10-26).
"""

from alembic import op
import sqlalchemy as sa

revision = "add_email_verification_tokens"
down_revision = "add_user_consent_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "email_verification_tokens" in inspector.get_table_names():
        return

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_email_verification_tokens_user_id", "email_verification_tokens", ["user_id"])
    op.create_index("ix_email_verification_tokens_expires_at", "email_verification_tokens", ["expires_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "email_verification_tokens" in inspector.get_table_names():
        op.drop_table("email_verification_tokens")
