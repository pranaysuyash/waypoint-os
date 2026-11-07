"""agency_api_keys table (R2-A) — align schema with runtime ensure-table.

The API-key auth core (spine_api/core/api_key_auth.py) creates this table at
runtime via CREATE TABLE IF NOT EXISTS; that is invisible to backup/restore
and rollback drills (FND-0388/0394 invariants — a restored database must
carry every table the running code expects). This migration makes the table
a first-class schema citizen. Runtime ensure-table remains as a no-op
fallback for pre-migration environments.

Match the runtime column shape exactly so the migration is a no-op on
databases where the runtime table already exists.

Revision ID: agency_api_keys_r2a
Revises: add_revoked_tokens
Create Date: 2026-11-06
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "agency_api_keys_r2a"
down_revision = "add_revoked_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agency_api_keys",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("agency_id", sa.String(length=36), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("revoked_at", sa.String(length=40), nullable=True),
    )
    op.create_index(
        "ix_agency_api_keys_agency_id", "agency_api_keys", ["agency_id"]
    )
    op.create_index(
        "ix_agency_api_keys_key_hash", "agency_api_keys", ["key_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_agency_api_keys_key_hash", table_name="agency_api_keys")
    op.drop_index("ix_agency_api_keys_agency_id", table_name="agency_api_keys")
    op.drop_table("agency_api_keys")
