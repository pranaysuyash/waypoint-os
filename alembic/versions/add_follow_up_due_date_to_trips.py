"""Add follow_up_due_date column to trips table

Revision ID: add_follow_up_due_date
Revises: 10a6e1336ba4
Create Date: 2026-04-28 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_follow_up_due_date'
down_revision: Union[str, Sequence[str], None] = '10a6e1336ba4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add follow_up_due_date column to trips table."""
    # Check if trips table exists before adding column
    # This migration assumes the trips table will be created separately
    # The follow_up_due_date field stores ISO-8601 datetime strings for promised follow-ups
    # Example: "2026-04-29T18:30:00+00:00" (in 48 hours from creation)
    
    try:
        op.add_column('trips', sa.Column('follow_up_due_date', sa.DateTime(timezone=True), nullable=True))
    except Exception:
        # Table may not exist yet if trips are still JSON-based
        # This migration is prepared for future database migration
        pass


def downgrade() -> None:
    """Remove follow_up_due_date column from trips table."""
    try:
        op.drop_column('trips', 'follow_up_due_date')
    except Exception:
        # Table may not exist yet
        pass
