"""PA-19 / E-E ADR (2026-09-08): tamper-evidence chain on execution_events.

Adds per-agency hash-chain columns (prev_hash, event_hash) to the
``execution_events`` table:

- ``prev_hash`` — the previous anchored event's ``event_hash`` for this
  agency (NULL = genesis or legacy pre-chain row; legacy rows are treated as
  an unanchored prefix by the verifier, never backfilled here — backfill is
  an offline, owner-gated operation per A-20 custody).
- ``event_hash`` — SHA-256 over (prev_hash + canonical event field JSON).

Additive and nullable: no data migration, no backfill in this revision. The
chain is computed going forward by the emit choke point
(``execution_event_service._insert_event_row``). Concurrent writers can in
principle fork the chain (both read the same last hash); the verifier
detects duplicate ``prev_hash`` links as forks.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ee_chain_columns"
down_revision = "bc_active_type_uniqueness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "execution_events" not in inspector.get_table_names():
        return

    existing_columns = {c["name"] for c in inspector.get_columns("execution_events")}
    if "prev_hash" not in existing_columns:
        op.add_column("execution_events", sa.Column("prev_hash", sa.String(length=64), nullable=True))
    if "event_hash" not in existing_columns:
        op.add_column("execution_events", sa.Column("event_hash", sa.String(length=64), nullable=True))

    existing_indexes = {ix["name"] for ix in inspector.get_indexes("execution_events")}
    if "ix_ee_agency_created" not in existing_indexes:
        # Chain walk + last-anchored lookup ordering: (agency_id, created_at)
        op.create_index("ix_ee_agency_created", "execution_events", ["agency_id", "created_at"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "execution_events" not in inspector.get_table_names():
        return
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("execution_events")}
    if "ix_ee_agency_created" in existing_indexes:
        op.drop_index("ix_ee_agency_created", table_name="execution_events")
    existing_columns = {c["name"] for c in inspector.get_columns("execution_events")}
    for col in ("event_hash", "prev_hash"):
        if col in existing_columns:
            op.drop_column("execution_events", col)
