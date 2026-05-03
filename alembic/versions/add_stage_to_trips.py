"""Add stage column to trips table

Revision ID: add_stage_to_trips
Revises: add_jurisdiction_to_agencies
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_stage_to_trips'
down_revision: Union[str, Sequence[str], None] = 'add_jurisdiction_to_agencies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add stage column to trips table with backfill."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}

    if "stage" not in existing_columns:
        op.add_column('trips', sa.Column(
            'stage', sa.String(50), nullable=True, server_default="discovery",
        ))

        if bind.dialect.name == "postgresql":
            # PostgreSQL: use JSON ->>  operator for intelligent backfill
            bind.execute(sa.text("""
                UPDATE trips SET stage = COALESCE(
                    (CASE
                        WHEN raw_input->>'stage' IN ('discovery','shortlist','proposal','booking')
                        THEN raw_input->>'stage'
                        WHEN raw_input->'meta'->>'stage' IN ('discovery','shortlist','proposal','booking')
                        THEN raw_input->'meta'->>'stage'
                        WHEN extracted->>'stage' IN ('discovery','shortlist','proposal','booking')
                        THEN extracted->>'stage'
                        ELSE 'discovery'
                    END),
                    'discovery'
                )
                WHERE stage IS NULL
            """))
        else:
            # SQLite / other dialects: simple default backfill
            bind.execute(sa.text("""
                UPDATE trips SET stage = 'discovery' WHERE stage IS NULL
            """))

        op.alter_column('trips', 'stage', nullable=False)


def downgrade() -> None:
    """Remove stage column from trips table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'trips' not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("trips")}
    if "stage" in existing_columns:
        op.drop_column('trips', 'stage')
