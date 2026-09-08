"""add payment_mandates table (F-04 payment authorization mandate ledger)

Revision ID: add_payment_mandates
Revises: add_idempotency_fencing_token
Create Date: 2026-09-07

F-04: split deposits and ACH/split movements had no durable consent artifact —
money moved without a mandate ledger answering "who consented, to how much,
and is that consent still in force?". This migration creates the durable
``payment_mandates`` table backing
``spine_api.services.payment_mandate_service.PaymentMandateLedger``. The
service also lazily ensures the table via ``Base.metadata.create_all``
(checkfirst) on first SQL use, so this migration exists for alembic-managed
environments and schema review; additive-only.

Tenant-owned table (``agency_id``): RLS-enabled with the standard
``app.current_agency_id`` select/all policies, matching
``add_rls_tenant_isolation`` conventions. The raw consent text is never
stored — only its SHA-256 digest plus a reference to the durable consent
artifact (audit event / acceptance token) that carries the full text.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_payment_mandates"
down_revision = "add_idempotency_fencing_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_mandates",
        sa.Column("mandate_id", sa.String(length=64), nullable=False),
        sa.Column("agency_id", sa.String(length=64), nullable=False),
        sa.Column("trip_id", sa.String(length=255), nullable=False),
        sa.Column("customer_id", sa.String(length=255), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("customer_email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("max_authorized_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("consent_text_sha256", sa.String(length=64), nullable=False),
        sa.Column("consent_artifact_ref", sa.String(length=255), nullable=False),
        sa.Column("client_ip_address", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("consumed_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revocation_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mandate_metadata", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("mandate_id"),
    )
    op.create_index("ix_payment_mandates_agency_id", "payment_mandates", ["agency_id"])
    op.create_index("ix_payment_mandates_trip_id", "payment_mandates", ["trip_id"])

    # Tenant-owned table: standard RLS posture (select/all on agency_id),
    # mirroring add_rls_tenant_isolation.py so the startup RLS validation
    # sees the table as covered.
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE payment_mandates ENABLE ROW LEVEL SECURITY"))
    conn.execute(
        sa.text(
            "CREATE POLICY waypoint_rls_select ON payment_mandates "
            "FOR SELECT USING (agency_id = current_setting('app.current_agency_id', TRUE))"
        )
    )
    conn.execute(
        sa.text(
            "CREATE POLICY waypoint_rls_all ON payment_mandates "
            "USING (agency_id = current_setting('app.current_agency_id', TRUE)) "
            "WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE))"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_all ON payment_mandates"))
    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_select ON payment_mandates"))
    op.drop_index("ix_payment_mandates_trip_id", table_name="payment_mandates")
    op.drop_index("ix_payment_mandates_agency_id", table_name="payment_mandates")
    op.drop_table("payment_mandates")
