"""recoveries ledger table (T10 phase 1)

Revision ID: recoveries_ledger
Revises: force_rls_payment_mandates
Create Date: 2026-10-25

Creates the durable recoveries ledger backing
``spine_api.services.recovery_store`` — the tracking-only record of
entitlements owed to travelers or the agency (price-drop re-locks,
supplier-fault compensation, insurance payouts, manual entries) with their
lifecycle through settlement. Disruption claims are deliberately absent:
their lifecycle is owned by ``claim_disposition`` on the passenger-rights
router (FND-0233).

Tenant-owned (``agency_id``). This migration creates the table and indexes;
the tenant RLS posture (ENABLE/FORCE + select/all policies on
``app.current_agency_id``) is applied by
``RecoveryStore._ensure_table`` (idempotent, mirroring the advisor_payouts
lazy-ensure convention) which the app startup and the test-template
bootstrap both reach. Table DDL only — no raw SQL statements here.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "recoveries_ledger"
down_revision = "force_rls_payment_mandates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recoveries",
        sa.Column("recovery_id", sa.String(length=64), primary_key=True),
        sa.Column("agency_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("trip_id", sa.String(length=255), nullable=True),
        sa.Column("traveler_ref", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("counterparty", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("amount_basis", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="detected"),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recoveries_agency_id", "recoveries", ["agency_id"])
    op.create_index("ix_recoveries_trip_id", "recoveries", ["trip_id"])
    op.create_index("ix_recoveries_status", "recoveries", ["status"])


def downgrade() -> None:
    op.drop_table("recoveries")
