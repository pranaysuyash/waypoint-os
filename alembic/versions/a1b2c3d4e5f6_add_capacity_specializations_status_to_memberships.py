"""add capacity specializations status to memberships

Revision ID: a1b2c3d4e5f6
Revises: 10a6e1336ba4
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "10a6e1336ba4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "memberships",
        sa.Column("capacity", sa.Integer(), nullable=True, server_default="5"),
    )
    op.add_column(
        "memberships",
        sa.Column("specializations", sa.JSON(), nullable=True),
    )
    op.add_column(
        "memberships",
        sa.Column("status", sa.String(50), nullable=True, server_default="active"),
    )
    op.add_column(
        "memberships",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        "UPDATE memberships SET capacity = 5, status = 'active' WHERE capacity IS NULL"
    )

    op.alter_column("memberships", "capacity", nullable=False)
    op.alter_column("memberships", "status", nullable=False)


def downgrade() -> None:
    op.drop_column("memberships", "updated_at")
    op.drop_column("memberships", "status")
    op.drop_column("memberships", "specializations")
    op.drop_column("memberships", "capacity")
