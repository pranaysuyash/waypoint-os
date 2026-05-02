"""Add audit_logs table

Revision ID: add_audit_logs
Revises: add_frontier_result_and_fees
Create Date: 2026-05-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'add_audit_logs'
down_revision: Union[str, Sequence[str], None] = 'add_frontier_result_and_fees'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agency_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=36), nullable=True),
        sa.Column('changes', JSONB, nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_agency_created', 'audit_logs', ['agency_id', 'created_at'])
    op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_agency_action', 'audit_logs', ['agency_id', 'action'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_agency_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_agency_created', table_name='audit_logs')
    op.drop_table('audit_logs')