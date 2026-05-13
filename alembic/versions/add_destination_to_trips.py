"""Add destination column to trips table

Revision ID: add_destination_to_trips
Revises: add_booking_confirmations
Create Date: 2026-05-12

"""
from typing import Union, Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_destination_to_trips'
down_revision: Union[str, Sequence[str], None] = 'add_booking_confirmations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add destination column to trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}
    if "destination" not in existing_columns:
        op.add_column('trips', sa.Column('destination', sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove destination column from trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("trips")}
        if "destination" not in existing_columns:
            return
        op.drop_column('trips', 'destination')
