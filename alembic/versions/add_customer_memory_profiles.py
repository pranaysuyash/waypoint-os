"""add customer_memory_profiles — durable, agency-scoped customer memory (FND-0060 residual)

Revision ID: add_customer_memory_profiles
Revises: add_proposal_access_tokens
Create Date: 2026-09-15

Creates ``customer_memory_profiles``: the durable identity/preference profile
for the customer-memory surface, replacing the legacy process-local dict that
FND-0060 flagged (profiles were lost on every restart).

Follows the canonical tenant-table pattern:
- agency_id FK -> agencies.id ON DELETE CASCADE
- RLS enabled + FORCE with the house waypoint_rls_all policy keyed on the
  app.current_agency_id session GUC, matching add_rls_phase5e_full_coverage.
- Unique (agency_id, customer_id) upsert key; identity lookup indexes.

Deliberately NOT included: passport_country / passport_expiry columns.
Passport data carries a 30-day post-trip retention SLA
(RetentionCategory.PASSPORT_MRZ); durable passport storage would violate it
by design. See Docs/exploration/
CUSTOMER_MEMORY_DURABLE_STORE_EXPLORATION_2026-09-15.md.

Note: all DDL statements are complete hardcoded literals — migrations run
offline against a fixed schema and take no input, so there is nothing to
parameterize.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "add_customer_memory_profiles"
down_revision: Union[str, Sequence[str], None] = "add_proposal_access_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_memory_profiles",
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column(
            "agency_id",
            sa.String(length=36),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("customer_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("normalized_email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("normalized_phone", sa.String(length=40), nullable=True),
        sa.Column("dietary_requirements", sa.String(length=500), nullable=True),
        sa.Column("room_preference", sa.String(length=200), nullable=True),
        sa.Column("seating_preference", sa.String(length=200), nullable=True),
        sa.Column("source_trip_ids", sa.JSON(), nullable=True),
        sa.Column("last_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "agency_id", "customer_id", name="uq_cmp_agency_customer"
        ),
    )
    op.create_index("ix_cmp_agency_id", "customer_memory_profiles", ["agency_id"])
    op.create_index(
        "ix_cmp_agency_email", "customer_memory_profiles", ["agency_id", "normalized_email"]
    )
    op.create_index(
        "ix_cmp_agency_phone", "customer_memory_profiles", ["agency_id", "normalized_phone"]
    )

    # RLS tenant isolation — house convention: waypoint_rls_select for reads
    # plus combined waypoint_rls_all (INSERT/UPDATE/DELETE via WITH CHECK +
    # USING) and FORCE RLS.
    op.execute("ALTER TABLE customer_memory_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY waypoint_rls_select ON customer_memory_profiles FOR SELECT USING (agency_id = current_setting('app.current_agency_id', TRUE))")
    op.execute("CREATE POLICY waypoint_rls_all ON customer_memory_profiles FOR ALL USING (agency_id = current_setting('app.current_agency_id', TRUE)) WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE))")
    op.execute("ALTER TABLE customer_memory_profiles FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS waypoint_rls_all ON customer_memory_profiles")
    op.execute("ALTER TABLE customer_memory_profiles DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_cmp_agency_phone", table_name="customer_memory_profiles")
    op.drop_index("ix_cmp_agency_email", table_name="customer_memory_profiles")
    op.drop_index("ix_cmp_agency_id", table_name="customer_memory_profiles")
    op.drop_table("customer_memory_profiles")
