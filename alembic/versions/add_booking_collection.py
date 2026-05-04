"""Add booking_collection_tokens table and pending columns to trips

Revision ID: add_booking_collection
Revises: add_booking_data
Create Date: 2026-05-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_booking_collection'
down_revision: Union[str, Sequence[str], None] = 'add_booking_data'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create booking_collection_tokens table
    if "booking_collection_tokens" not in tables:
        op.create_table(
            "booking_collection_tokens",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
            sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("status", sa.String(20), server_default="active"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(36), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_bct_token_hash", "booking_collection_tokens", ["token_hash"])
        op.create_index("ix_bct_trip_id", "booking_collection_tokens", ["trip_id"])

    # 2. Add pending_booking_data and booking_data_source to trips
    if "trips" in tables:
        columns = {c["name"] for c in inspector.get_columns("trips")}
        if "pending_booking_data" not in columns:
            op.add_column("trips", sa.Column("pending_booking_data", sa.JSON(), nullable=True))
        if "booking_data_source" not in columns:
            op.add_column("trips", sa.Column("booking_data_source", sa.String(30), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # Remove columns from trips
    if "trips" in tables:
        columns = {c["name"] for c in inspector.get_columns("trips")}
        if "booking_data_source" in columns:
            op.drop_column("trips", "booking_data_source")
        if "pending_booking_data" in columns:
            op.drop_column("trips", "pending_booking_data")

    # Drop table
    if "booking_collection_tokens" in tables:
        op.drop_table("booking_collection_tokens")
