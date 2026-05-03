"""Add booking_data column to trips table

Revision ID: add_booking_data
Revises: add_priorities_flex
Create Date: 2026-05-03 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_booking_data'
down_revision: Union[str, Sequence[str], None] = 'add_priorities_flex'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add booking_data JSON column to trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}
    if "booking_data" not in existing_columns:
        op.add_column('trips', sa.Column('booking_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove booking_data column from trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("trips")}
        if "booking_data" in existing_columns:
            op.drop_column('trips', 'booking_data')
