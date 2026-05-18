"""Add durable agent requeue jobs table

Revision ID: add_agent_requeue_jobs
Revises: add_collection_token_encrypted
Create Date: 2026-05-18 00:00:00.000000

Adds the agent_requeue_jobs table used by RequeueJobStore for durable
SQL-backed recovery requeue.

Parity note
-----------
Schema intentionally matches RequeueJobStore.ensure_schema() in
spine_api/services/agent_requeue_jobs.py column-for-column.  The runtime
ensure_schema() is kept as a belt-and-suspenders guard for local/stale DBs.

Why no RLS
----------
This is a system-internal coordination table, not a tenant-scoped data table.
It has no agency_id column because the recovery worker needs to lease and
process jobs across all agencies.  Adding RLS would require making this a
per-tenant queue, which changes the semantics of the recovery worker.
See Docs/status/AGENT_REQUEUE_SCHEMA_OWNERSHIP_DECISION_2026-05-18.md for
full analysis.

Sibling precedent
-----------------
agent_work_leases follows the same pattern — Alembic migration + runtime
ensure_schema() belt-and-suspenders, no RLS.  add_agent_work_leases.py is
the reference.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_agent_requeue_jobs"
down_revision: Union[str, Sequence[str], None] = "add_collection_token_encrypted"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "agent_requeue_jobs" in inspector.get_table_names():
        # Table already exists (created by runtime ensure_schema()).
        # Ensure all three indexes exist — they are also created idempotently
        # by ensure_schema() so this should normally be a no-op.
        _ensure_indexes(bind)
        return

    op.create_table(
        "agent_requeue_jobs",
        # Primary key
        sa.Column("id", sa.String(36), primary_key=True),
        # Idempotency — unique constraint enforced by uq index below
        sa.Column("idempotency_key", sa.String(500), nullable=False),
        # Trip being requeued
        sa.Column("trip_id", sa.String(255), nullable=False),
        # Job metadata
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("mode", sa.String(40), nullable=False, server_default="sql_queue"),
        # Lifecycle
        sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        # Payload stored as JSON text
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        # Lease tracking
        sa.Column("leased_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(120), nullable=False, server_default=""),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    _ensure_indexes(bind)


def _ensure_indexes(bind: sa.engine.Connection) -> None:
    """Create indexes idempotently.  Safe to call when table already exists."""
    inspector = sa.inspect(bind)
    existing = {idx["name"] for idx in inspector.get_indexes("agent_requeue_jobs")}

    if "ix_agent_requeue_jobs_status" not in existing:
        op.create_index(
            "ix_agent_requeue_jobs_status", "agent_requeue_jobs", ["status"]
        )
    if "ix_agent_requeue_jobs_trip_id" not in existing:
        op.create_index(
            "ix_agent_requeue_jobs_trip_id", "agent_requeue_jobs", ["trip_id"]
        )
    if "uq_agent_requeue_jobs_idempotency" not in existing:
        op.create_index(
            "uq_agent_requeue_jobs_idempotency",
            "agent_requeue_jobs",
            ["idempotency_key"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "agent_requeue_jobs" in inspector.get_table_names():
        op.drop_table("agent_requeue_jobs")
