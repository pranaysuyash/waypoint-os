"""audit_logs: monotonic seq column for deterministic chain ordering

Revision ID: add_audit_logs_seq
Revises: add_frontier_tables
Create Date: 2026-09-09

A-04 3.4 consolidation: `audit_logs` is now the single canonical audit store.
Both writers (`core.audit.AuditContext.log` and `AuditStore.log_event`) read
the predecessor hash with `ORDER BY created_at DESC, id DESC` — but `id` is a
random UUID, so same-microsecond rows (concurrent writers, serialized batch
writes) reorder arbitrarily between the predecessor read and the verifier.

`seq` (BIGSERIAL) gives new rows the deterministic write order: predecessor
reads and chain verification order by `seq DESC/ASC`. Pre-existing rows keep
NULL `seq` and are ordered by (created_at, id) — their relative order was
already verified contiguous under that ordering. No backfill required.
"""

from alembic import op
import sqlalchemy as sa

revision = "add_audit_logs_seq"
down_revision = "ee_chain_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("seq", sa.BigInteger(), nullable=True))
    op.create_index("ix_audit_logs_seq", "audit_logs", ["seq"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_seq", table_name="audit_logs")
    op.drop_column("audit_logs", "seq")
