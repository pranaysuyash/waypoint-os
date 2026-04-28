"""Add follow_up_due_date column to trips table

Revision ID: add_follow_up_due_date
Revises: create_trips_table_v1
Create Date: 2026-04-28 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_follow_up_due_date'
down_revision: Union[str, Sequence[str], None] = 'create_trips_table_v1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add follow_up_due_date column to trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}
    if "follow_up_due_date" not in existing_columns:
        op.add_column('trips', sa.Column('follow_up_due_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove follow_up_due_date column from trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("trips")}
        if "follow_up_due_date" not in existing_columns:
            return
        op.drop_column('trips', 'follow_up_due_date')
