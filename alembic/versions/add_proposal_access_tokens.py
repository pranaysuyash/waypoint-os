"""add proposal_access_tokens table (FND-0219 durable capability store)

Revision ID: add_proposal_access_tokens
Revises: add_audit_logs_seq
Create Date: 2026-09-14

FND-0219: the public proposal view's capability credentials were tracked in an
unbounded in-process dict and a JSON revocation file keyed by RAW token
material. This migration creates the durable ``proposal_access_tokens`` table
that backs ``spine_api.services.proposal_token_store.ProposalTokenStore``:

- rows are keyed by ``token_hash`` (SHA-256 of the raw token, unique) — raw
  credential material is never stored; ``lookup_prefix`` is a diagnosis aid.
- ``expires_at`` / ``revoked_at`` give every credential a TTL and durable
  revocation.
- ``consented_by`` / ``consented_at`` / ``purpose`` record the consent
  artifact: the authenticated principal who authorized external sharing.
- ``format_version`` explicitly versions the token wire format ("v3" opaque
  vs legacy signed "v2").

The backend also lazily ensures the table via ``Base.metadata.create_all``
(checkfirst) on first use, so this migration exists for alembic-managed
environments and schema review; it is additive-only (create table + indexes,
no truncate/drop) and idempotent with the lazy path.

System-scoped table — intentionally NOT RLS-protected (same precedent as
``idempotency_keys``): the traveler verification path runs OUTSIDE any
authenticated agency session, so agency-scoped RLS would fail the design
closed. Rows are addressed exclusively by the opaque credential hash;
``agency_id``/``trip_id`` are binding/audit metadata, and access is authorized
by possession of the credential plus TTL/revocation checks.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_proposal_access_tokens"
down_revision = "add_audit_logs_seq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "proposal_access_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("lookup_prefix", sa.String(length=16), nullable=False),
        sa.Column("format_version", sa.String(length=8), nullable=False),
        sa.Column("agency_id", sa.String(length=255), nullable=False),
        sa.Column("trip_id", sa.String(length=255), nullable=False),
        sa.Column("proposal_id", sa.String(length=255), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consented_by", sa.String(length=255), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_proposal_access_tokens_token_hash"),
    )
    op.create_index("ix_proposal_access_tokens_lookup_prefix", "proposal_access_tokens", ["lookup_prefix"])
    op.create_index("ix_proposal_access_tokens_agency_id", "proposal_access_tokens", ["agency_id"])
    op.create_index("ix_proposal_access_tokens_trip_id", "proposal_access_tokens", ["trip_id"])
    op.create_index("ix_proposal_access_tokens_expires_at", "proposal_access_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_proposal_access_tokens_expires_at", table_name="proposal_access_tokens")
    op.drop_index("ix_proposal_access_tokens_trip_id", table_name="proposal_access_tokens")
    op.drop_index("ix_proposal_access_tokens_agency_id", table_name="proposal_access_tokens")
    op.drop_index("ix_proposal_access_tokens_lookup_prefix", table_name="proposal_access_tokens")
    op.drop_table("proposal_access_tokens")
