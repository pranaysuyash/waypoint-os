"""Add frontier_result and fees columns to trips table

Revision ID: add_frontier_result_and_fees
Revises: add_follow_up_due_date
Create Date: 2026-05-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_frontier_result_and_fees'
down_revision: Union[str, Sequence[str], None] = 'add_follow_up_due_date'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add frontier_result and fees columns to trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}
    if "frontier_result" not in existing_columns:
        op.add_column('trips', sa.Column('frontier_result', sa.JSON, nullable=True))
    if "fees" not in existing_columns:
        op.add_column('trips', sa.Column('fees', sa.JSON, nullable=True))


def downgrade() -> None:
    """Remove frontier_result and fees columns from trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}
    if "fees" in existing_columns:
        op.drop_column('trips', 'fees')
    if "frontier_result" in existing_columns:
        op.drop_column('trips', 'frontier_result')
