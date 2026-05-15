"""Phase 5E: Full RLS coverage for all tenant-scoped tables

Revision ID: add_rls_phase5e_full_coverage
Revises: add_destination_to_trips
Create Date: 2026-05-13 00:00:00.000000

Adds agency_id + trip_id to document_extraction_attempts (backfilled from
document_extractions), enables RLS on 6 new tenant tables, creates policies,
and applies FORCE ROW LEVEL SECURITY on all 11 tenant tables.

NOTE: Application startup removes FORCE RLS from memberships and workspace_codes
(RLS_FORCE_EXEMPT_TABLES) because login/join query these tables before agency
context is known. These tables keep ENABLE RLS (protecting non-owner roles) but
the owner bypasses without FORCE. This is enforced by
_ensure_rls_no_force_on_auth_tables() on every startup.

Also creates trip_routing_states if it was never materialized by the original
RLS migration (the DDL ran but the table was later dropped or the migration
was stamped without running).

Migration order (DO NOT reorder):
  1. Create trip_routing_states if missing
  2. Add nullable agency_id/trip_id to document_extraction_attempts
  3. Backfill from document_extractions
  4. Assert no NULLs remain
  5. Set NOT NULL
  6. Add FK constraints + indexes
  7. Enable RLS + create policies on 6 new tables + trip_routing_states
  8. FORCE RLS on all tenant tables that exist

IMPORTANT: After this migration, DML on tenant tables is subject to
app.current_agency_id RLS. Future migrations doing tenant-table DML must
follow the rules in Docs/MIGRATIONS_AND_RLS.md.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_rls_phase5e_full_coverage"
down_revision: Union[str, Sequence[str], None] = "add_destination_to_trips"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables needing RLS enabled for the first time
_NEW_RLS_TABLES = (
    "booking_documents",
    "document_extractions",
    "document_extraction_attempts",
    "booking_tasks",
    "booking_confirmations",
    "execution_events",
)

# Table that should have RLS from original migration but may not exist
_MISSING_TABLE = "trip_routing_states"

# All tenant tables (FORCE RLS applied to all that exist)
_ALL_TENANT_TABLES = (
    "trips",
    "memberships",
    "workspace_codes",
    "booking_collection_tokens",
    "trip_routing_states",
    "booking_documents",
    "document_extractions",
    "document_extraction_attempts",
    "booking_tasks",
    "booking_confirmations",
    "execution_events",
)


def _existing_tables(conn) -> set[str]:
    """Return set of table names that exist in the public schema."""
    rows = conn.execute(sa.text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )).scalars().all()
    return set(rows)


def _create_trip_routing_states_if_missing() -> None:
    """Create trip_routing_states if the original RLS migration never materialized it."""
    conn = op.get_bind()
    existing = _existing_tables(conn)

    if _MISSING_TABLE in existing:
        return

    op.create_table(
        _MISSING_TABLE,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "agency_id", sa.String(36),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "primary_assignee_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewer_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "escalation_owner_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="unassigned"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handoff_history", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_routing_trip_id", _MISSING_TABLE, ["trip_id"])
    op.create_index("ix_routing_agency_id", _MISSING_TABLE, ["agency_id"])
    op.create_index("ix_routing_assignee", _MISSING_TABLE, ["primary_assignee_id"])
    op.create_index("ix_routing_status", _MISSING_TABLE, ["status"])

    # Enable RLS + policies immediately (same as original migration would have done)
    conn.execute(sa.text(f"ALTER TABLE {_MISSING_TABLE} ENABLE ROW LEVEL SECURITY"))
    conn.execute(sa.text(
        f"CREATE POLICY waypoint_rls_select ON {_MISSING_TABLE} "
        f"FOR SELECT USING (agency_id = current_setting('app.current_agency_id', TRUE))"
    ))
    conn.execute(sa.text(
        f"CREATE POLICY waypoint_rls_all ON {_MISSING_TABLE} "
        f"FOR ALL "
        f"USING (agency_id = current_setting('app.current_agency_id', TRUE)) "
        f"WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE))"
    ))


def _add_tenant_columns_to_attempts() -> None:
    """Add agency_id + trip_id to document_extraction_attempts and backfill."""
    conn = op.get_bind()

    # Step 1: Add nullable columns
    op.add_column(
        "document_extraction_attempts",
        sa.Column("agency_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "document_extraction_attempts",
        sa.Column("trip_id", sa.String(36), nullable=True),
    )

    # Step 2: Backfill from parent document_extractions
    conn.execute(sa.text(
        """
        UPDATE document_extraction_attempts dea
        SET agency_id = de.agency_id,
            trip_id = de.trip_id
        FROM document_extractions de
        WHERE dea.extraction_id = de.id
        """
    ))

    # Step 3: Assert no NULLs remain (fail fast if backfill missed rows)
    null_count = conn.execute(sa.text(
        """
        SELECT COUNT(*) FROM document_extraction_attempts
        WHERE agency_id IS NULL OR trip_id IS NULL
        """
    )).scalar()
    if null_count and int(null_count) > 0:
        raise RuntimeError(
            f"Backfill failed: {null_count} document_extraction_attempts rows "
            "have NULL agency_id or trip_id after backfill from document_extractions"
        )

    # Step 4: Set NOT NULL
    op.alter_column("document_extraction_attempts", "agency_id", nullable=False)
    op.alter_column("document_extraction_attempts", "trip_id", nullable=False)

    # Step 5: Add FK constraints + indexes
    op.create_foreign_key(
        "fk_dea_agency", "document_extraction_attempts",
        "agencies", ["agency_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_dea_trip", "document_extraction_attempts",
        "trips", ["trip_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_dea_agency_id", "document_extraction_attempts", ["agency_id"])
    op.create_index("ix_dea_trip_id", "document_extraction_attempts", ["trip_id"])


def _enable_rls_on_new_tables() -> None:
    """Enable RLS and create policies on the 6 new tenant tables."""
    conn = op.get_bind()

    for table in _NEW_RLS_TABLES:
        conn.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))

        conn.execute(sa.text(
            f"""
            CREATE POLICY waypoint_rls_select ON {table}
              FOR SELECT
              USING (
                agency_id = current_setting('app.current_agency_id', TRUE)
              )
            """
        ))

        conn.execute(sa.text(
            f"""
            CREATE POLICY waypoint_rls_all ON {table}
              FOR ALL
              USING (
                agency_id = current_setting('app.current_agency_id', TRUE)
              )
              WITH CHECK (
                agency_id = current_setting('app.current_agency_id', TRUE)
              )
            """
        ))


def _force_rls_on_all_tables() -> None:
    """FORCE ROW LEVEL SECURITY on all tenant tables that exist."""
    conn = op.get_bind()
    existing = _existing_tables(conn)

    for table in _ALL_TENANT_TABLES:
        if table in existing:
            conn.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))


def upgrade() -> None:
    _create_trip_routing_states_if_missing()
    _add_tenant_columns_to_attempts()
    _enable_rls_on_new_tables()
    _force_rls_on_all_tables()


def downgrade() -> None:
    conn = op.get_bind()
    existing = _existing_tables(conn)

    # Remove FORCE RLS from all tables that exist
    for table in _ALL_TENANT_TABLES:
        if table in existing:
            conn.execute(sa.text(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY"))

    # Drop policies and disable RLS on the 6 new tables
    for table in _NEW_RLS_TABLES:
        conn.execute(sa.text(f"DROP POLICY IF EXISTS waypoint_rls_all ON {table}"))
        conn.execute(sa.text(f"DROP POLICY IF EXISTS waypoint_rls_select ON {table}"))
        conn.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    # Remove agency_id + trip_id from document_extraction_attempts
    op.drop_index("ix_dea_trip_id", table_name="document_extraction_attempts")
    op.drop_index("ix_dea_agency_id", table_name="document_extraction_attempts")
    op.drop_constraint("fk_dea_trip", "document_extraction_attempts", type_="foreignkey")
    op.drop_constraint("fk_dea_agency", "document_extraction_attempts", type_="foreignkey")
    op.drop_column("document_extraction_attempts", "trip_id")
    op.drop_column("document_extraction_attempts", "agency_id")

    # Drop trip_routing_states if we created it
    if _MISSING_TABLE in existing:
        conn.execute(sa.text(f"DROP POLICY IF EXISTS waypoint_rls_all ON {_MISSING_TABLE}"))
        conn.execute(sa.text(f"DROP POLICY IF EXISTS waypoint_rls_select ON {_MISSING_TABLE}"))
        op.drop_index("ix_routing_status", table_name=_MISSING_TABLE)
        op.drop_index("ix_routing_assignee", table_name=_MISSING_TABLE)
        op.drop_index("ix_routing_agency_id", table_name=_MISSING_TABLE)
        op.drop_index("ix_routing_trip_id", table_name=_MISSING_TABLE)
        op.drop_table(_MISSING_TABLE)
