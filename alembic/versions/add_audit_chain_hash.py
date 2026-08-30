"""Add RULE_015 hash-chain columns to audit_logs

Revision ID: add_audit_chain_hash
Revises: 0cd0399e2c3c
Create Date: 2026-08-29

Unifies the database-backed AuditLog with the file-based AuditStore by adding
the SHA-256 tamper-evident chain (previous_hash -> current_hash), matching the
RULE_015 semantics already implemented in persistence.py AuditStore.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_audit_chain_hash'
down_revision: Union[str, Sequence[str], None] = '0cd0399e2c3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('previous_hash', sa.String(length=64), nullable=True))
    op.add_column('audit_logs', sa.Column('current_hash', sa.String(length=64), nullable=True))
    op.create_index('ix_audit_logs_current_hash', 'audit_logs', ['current_hash'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_current_hash', table_name='audit_logs')
    op.drop_column('audit_logs', 'current_hash')
    op.drop_column('audit_logs', 'previous_hash')
