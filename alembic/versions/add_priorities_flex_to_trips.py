"""Add trip_priorities and date_flexibility columns to trips table

Revision ID: add_trip_priorities_date_flexibility
Revises: add_stage_to_trips
Create Date: 2026-05-03 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_priorities_flex'
down_revision: Union[str, Sequence[str], None] = 'add_stage_to_trips'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trip_priorities and date_flexibility columns to trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}
    if "trip_priorities" not in existing_columns:
        op.add_column('trips', sa.Column('trip_priorities', sa.Text(), nullable=True))
    if "date_flexibility" not in existing_columns:
        op.add_column('trips', sa.Column('date_flexibility', sa.String(50), nullable=True))


def downgrade() -> None:
    """Remove trip_priorities and date_flexibility columns from trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("trips")}
        if "trip_priorities" in existing_columns:
            op.drop_column('trips', 'trip_priorities')
        if "date_flexibility" in existing_columns:
            op.drop_column('trips', 'date_flexibility')
