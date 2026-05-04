"""add RLS tenant isolation

Revision ID: f1a2b3c4d5e6
Revises: 10a6e1336ba4
Create Date: 2026-05-04 00:00:00.000000

Enables PostgreSQL Row Level Security on all tenant-scoped tables.
Each table gets two policies:

  waypoint_rls_select  — SELECT restricted to rows where agency_id matches
                          the session-local setting app.current_agency_id.
  waypoint_rls_all     — INSERT/UPDATE/DELETE restricted to same.

The setting is applied per-transaction by get_rls_db() in spine_api/core/rls.py.
Superuser connections (used by Alembic itself and admin tooling) bypass RLS
via BYPASSRLS privilege — they are NOT affected by these policies.

Tables covered:
  - trips                     (primary data; high risk of cross-tenant leak)
  - memberships               (user-agency associations)
  - workspace_codes           (invite codes must not be visible across tenants)
  - booking_collection_tokens (UUID tokens linked to trips; cross-tenant exposure
                               allows accessing another agency's booking flows)

Tables intentionally excluded:
  - agencies        (no agency_id column; the agency IS the tenant)
  - users           (global user table; users exist independently of tenants)
  - audit_logs      (already query-scoped; RLS adds no value and complicates
                     cross-agency audit queries for admin tooling)

down_revision = add_agent_work_leases: all protected tables must exist before
  RLS can reference them. add_agent_work_leases is the chain head at this point.

Performance note:
  Each policy uses current_setting('app.current_agency_id', TRUE).
  The second arg (TRUE) means: return NULL rather than error if the setting
  is not defined. NULL = '' in boolean context → policy returns false → row hidden.
  This is intentional: requests that bypass auth will see nothing, not everything.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "add_agent_work_leases"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables to protect.  Each must have an `agency_id` column.
_RLS_TABLES = ("trips", "memberships", "workspace_codes", "booking_collection_tokens")


def _create_trip_routing_states() -> None:
    """
    Create trip_routing_states and enable RLS on it immediately.

    Bundled here so there is never a window where the table exists but is
    unprotected. The table tracks who owns a trip and the handoff history;
    it must be tenant-isolated from day one.
    """
    op.create_table(
        "trip_routing_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "agency_id",
            sa.String(36),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "primary_assignee_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewer_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "escalation_owner_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="unassigned"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handoff_history", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_routing_trip_id", "trip_routing_states", ["trip_id"])
    op.create_index("ix_routing_agency_id", "trip_routing_states", ["agency_id"])
    op.create_index("ix_routing_assignee", "trip_routing_states", ["primary_assignee_id"])
    op.create_index("ix_routing_status", "trip_routing_states", ["status"])

    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE trip_routing_states ENABLE ROW LEVEL SECURITY"))
    conn.execute(sa.text(
        "CREATE POLICY waypoint_rls_select ON trip_routing_states "
        "FOR SELECT USING (agency_id = current_setting('app.current_agency_id', TRUE))"
    ))
    conn.execute(sa.text(
        "CREATE POLICY waypoint_rls_all ON trip_routing_states "
        "FOR ALL "
        "USING (agency_id = current_setting('app.current_agency_id', TRUE)) "
        "WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE))"
    ))


def upgrade() -> None:
    _create_trip_routing_states()

    conn = op.get_bind()

    for table in _RLS_TABLES:
        # Enable RLS on the table.  FORCE is NOT used — superusers bypass RLS
        # so Alembic migrations and DB admin tools continue to work normally.
        conn.execute(
            __import__("sqlalchemy").text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        )

        # SELECT policy
        conn.execute(
            __import__("sqlalchemy").text(
                f"""
                CREATE POLICY waypoint_rls_select ON {table}
                  FOR SELECT
                  USING (
                    agency_id = current_setting('app.current_agency_id', TRUE)
                  )
                """
            )
        )

        # ALL (INSERT / UPDATE / DELETE) policy — uses WITH CHECK for writes
        conn.execute(
            __import__("sqlalchemy").text(
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
            )
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop routing states first (depends on agencies + users via FK)
    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_all ON trip_routing_states"))
    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_select ON trip_routing_states"))
    op.drop_index("ix_routing_status", table_name="trip_routing_states")
    op.drop_index("ix_routing_assignee", table_name="trip_routing_states")
    op.drop_index("ix_routing_agency_id", table_name="trip_routing_states")
    op.drop_index("ix_routing_trip_id", table_name="trip_routing_states")
    op.drop_table("trip_routing_states")

    for table in reversed(_RLS_TABLES):
        conn.execute(
            __import__("sqlalchemy").text(f"DROP POLICY IF EXISTS waypoint_rls_all ON {table}")
        )
        conn.execute(
            __import__("sqlalchemy").text(f"DROP POLICY IF EXISTS waypoint_rls_select ON {table}")
        )
        conn.execute(
            __import__("sqlalchemy").text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        )
