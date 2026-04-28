"""create trips table

Revision ID: create_trips_table_v1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'create_trips_table_v1'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if trips table already exists (unlikely in this flow, but safe)
    # op.get_bind().engine.has_table('trips') is old way.
    # We'll just try to create it.
    
    op.create_table('trips',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('agency_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='unknown'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='new'),
        sa.Column('follow_up_due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('party_composition', sa.String(length=255), nullable=True),
        sa.Column('pace_preference', sa.String(length=50), nullable=True),
        sa.Column('date_year_confidence', sa.String(length=50), nullable=True),
        sa.Column('lead_source', sa.String(length=100), nullable=True),
        sa.Column('activity_provenance', sa.Text(), nullable=True),
        sa.Column('extracted', sa.JSON(), nullable=False),
        sa.Column('validation', sa.JSON(), nullable=False),
        sa.Column('decision', sa.JSON(), nullable=False),
        sa.Column('strategy', sa.JSON(), nullable=True),
        sa.Column('traveler_bundle', sa.JSON(), nullable=True),
        sa.Column('internal_bundle', sa.JSON(), nullable=True),
        sa.Column('safety', sa.JSON(), nullable=False),
        sa.Column('raw_input', sa.JSON(), nullable=False),
        sa.Column('analytics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trips_agency_id', 'trips', ['agency_id'], unique=False)
    op.create_index('ix_trips_status', 'trips', ['status'], unique=False)
    op.create_index('ix_trips_created_at', 'trips', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_trips_created_at', table_name='trips')
    op.drop_index('ix_trips_status', table_name='trips')
    op.drop_index('ix_trips_agency_id', table_name='trips')
    op.drop_table('trips')
