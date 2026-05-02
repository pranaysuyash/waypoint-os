"""Add jurisdiction field to agencies table

Revision ID: add_jurisdiction_to_agencies
Revises: add_audit_logs
Create Date: 2026-05-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_jurisdiction_to_agencies'
down_revision: Union[str, Sequence[str], None] = 'add_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'agencies',
        sa.Column('jurisdiction', sa.String(length=10), nullable=True),
    )
    op.execute("UPDATE agencies SET jurisdiction = 'other' WHERE jurisdiction IS NULL")
    op.alter_column('agencies', 'jurisdiction', nullable=False)


def downgrade() -> None:
    op.drop_column('agencies', 'jurisdiction')