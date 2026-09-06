"""Add explicit platform-admin role to user identities.

Revision ID: add_platform_role_to_users
Revises: add_idempotency_keys
Create Date: 2026-09-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_platform_role_to_users"
down_revision: Union[str, Sequence[str], None] = "add_idempotency_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    if "platform_role" not in existing_columns:
        op.add_column(
            "users",
            sa.Column(
                "platform_role",
                sa.String(length=50),
                nullable=False,
                server_default="none",
            ),
        )
    op.execute("UPDATE users SET platform_role = 'none' WHERE platform_role IS NULL")
    op.alter_column("users", "platform_role", server_default=None, nullable=False)


def downgrade() -> None:
    op.drop_column("users", "platform_role")
