"""add idempotency_keys table (PT-08 durable idempotency backend)

Revision ID: add_idempotency_keys
Revises: add_frontier_tables
Create Date: 2026-09-02

PT-08 (Docs/review/SPINE_AUDIT_NEW_FINDINGS_2026-09-02.md): the intake
IdempotencyRegistry was in-process only, so multi-worker / multi-replica
deployments silently lost duplicate-intake protection. This migration creates
the durable ``idempotency_keys`` table that backs
``src.agents.idempotency.SqlIdempotencyBackend`` (selected via
``SPINE_API_IDEMPOTENCY_BACKEND=sql``). The backend also lazily ensures the
table via ``Base.metadata.create_all`` on first use, so this migration exists
for alembic-managed environments and schema review; it is additive-only and
idempotent with the lazy path (checkfirst).

System-scoped table — intentionally NOT RLS-protected: rows are keyed by
opaque operation keys and carry no tenant-owned data (``trip_id`` is
informational only, never a tenant lookup path).

``fencing_token`` is regenerated on every acquisition/reclaim and is required
for terminal compare-and-set writes; it prevents stale owners from closing a
new owner's pending row.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_idempotency_keys"
down_revision = "add_frontier_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("fencing_token", sa.String(length=128), nullable=False),
        sa.Column("trip_id", sa.String(length=255), nullable=False),
        sa.Column("action_name", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ttl_seconds", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index("ix_idempotency_keys_trip_id", "idempotency_keys", ["trip_id"])
    op.create_index("ix_idempotency_keys_status", "idempotency_keys", ["status"])


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_status", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_trip_id", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
