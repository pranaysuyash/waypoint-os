"""force RLS on payment_mandates (tenant-isolation hardening)

Revision ID: force_rls_payment_mandates
Revises: bc_component_identity
Create Date: 2026-10-25

``add_payment_mandates`` enabled RLS and created the standard
``waypoint_rls_select`` / ``waypoint_rls_all`` policies but skipped
``FORCE ROW LEVEL SECURITY`` — so the table owner (the application role)
bypassed the policies entirely and the mandate ledger's DB-level tenant
isolation was inert. Every peer tenant-table migration (add_rls_phase5e_full_coverage,
add_customer_memory_profiles, add_agency_integrations, pa_wave2_authority_payouts_cost)
applies FORCE; this brings payment_mandates to the same posture. Additive-only.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "force_rls_payment_mandates"
down_revision = "bc_component_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE payment_mandates FORCE ROW LEVEL SECURITY"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE payment_mandates NO FORCE ROW LEVEL SECURITY"))
