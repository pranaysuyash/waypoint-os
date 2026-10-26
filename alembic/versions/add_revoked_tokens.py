"""Add revoked_tokens table for session revocation.

Revision ID: add_revoked_tokens
Revises: add_email_verification_tokens
Create Date: 2026-10-26

B-03: Session revocation (audit 2026-10-26).
"""

from alembic import op
import sqlalchemy as sa

revision = "add_revoked_tokens"
down_revision = "add_email_verification_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "revoked_tokens" in inspector.get_table_names():
        return

    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("jti", sa.String(length=64), unique=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_revoked_tokens_jti", "revoked_tokens", ["jti"])
    op.create_index("ix_revoked_tokens_user_id", "revoked_tokens", ["user_id"])
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "revoked_tokens" in inspector.get_table_names():
        op.drop_table("revoked_tokens")
