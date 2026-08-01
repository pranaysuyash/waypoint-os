"""add_assigned_to_id_and_is_test

Revision ID: 0cd0399e2c3c
Revises: add_snapshot_attempts
Create Date: 2026-07-31 16:43:02.990788

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0cd0399e2c3c'
down_revision: Union[str, Sequence[str], None] = 'add_snapshot_attempts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    """Check if a column already exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name = :table AND column_name = :column"
    ), {"table": table, "column": column})
    return result.scalar() > 0


def _has_index(index_name: str) -> bool:
    """Check if an index already exists."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE c.relname = :index AND n.nspname = 'public'"
    ), {"index": index_name})
    return result.scalar() > 0


def upgrade() -> None:
    # 1. Add 'is_test' column to agencies
    if not _has_column("agencies", "is_test"):
        op.add_column(
            "agencies",
            sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )

    # 2. Add 'assigned_to_id' column to trips
    if not _has_column("trips", "assigned_to_id"):
        op.add_column(
            "trips",
            sa.Column("assigned_to_id", sa.String(length=36), nullable=True)
        )
        op.create_foreign_key(
            op.f("trips_assigned_to_id_fkey"),
            "trips",
            "users",
            ["assigned_to_id"],
            ["id"],
            ondelete="SET NULL"
        )

    # 3. Add 'destination' column to trips (if missing from older migrations but needed by ORM)
    if not _has_column("trips", "destination"):
        op.add_column(
            "trips",
            sa.Column("destination", sa.String(length=255), nullable=True)
        )

    # 4. Create database indexes on trips for performance
    if not _has_index("ix_trips_user_id"):
        op.create_index("ix_trips_user_id", "trips", ["user_id"], unique=False)
    
    if not _has_index("ix_trips_assigned_to_id"):
        op.create_index("ix_trips_assigned_to_id", "trips", ["assigned_to_id"], unique=False)


def downgrade() -> None:
    # Remove indexes
    if _has_index("ix_trips_assigned_to_id"):
        op.drop_index("ix_trips_assigned_to_id", table_name="trips")

    if _has_index("ix_trips_user_id"):
        op.drop_index("ix_trips_user_id", table_name="trips")

    # Drop columns
    if _has_column("trips", "assigned_to_id"):
        op.drop_constraint("trips_assigned_to_id_fkey", "trips", type_="foreignkey")
        op.drop_column("trips", "assigned_to_id")

    if _has_column("agencies", "is_test"):
        op.drop_column("agencies", "is_test")
