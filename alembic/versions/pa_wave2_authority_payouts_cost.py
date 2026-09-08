"""PA wave 2: authority_approvals + advisor_payouts tables, usage_events correlation columns

Revision ID: pa_wave2_authority_payouts_cost
Revises: add_payment_mandates
Create Date: 2026-09-07

PER-0700 remediation wave 2 — closes the open halves of PA-08 and PA-23:

1. ``usage_events`` gains nullable ``run_id`` / ``trip_id`` correlation
   columns (PA-20/A-20: the columns move under alembic custody instead of
   riding inside ``metadata_json``). NOTE: the LLM usage store currently owns
   its own SQLite DDL (``src/llm/usage_store.py``), so in a Postgres-managed
   database where ``usage_events`` does not (yet) exist this step is a
   guarded no-op (inspector-checked); the parallel usage-store change writes
   the same column names.
2. ``authority_approvals`` — the durable dual-control approval ledger backing
   ``spine_api.services.authority_approval_service``. Additive-only.
3. ``advisor_payouts`` — the durable advisor payout ledger backing
   ``spine_api.services.advisor_payout_store``. Additive-only.

Both new tables are tenant-owned (``agency_id``) with the standard RLS
posture (select/all on ``app.current_agency_id``), mirroring
``add_payment_mandates_table`` / ``add_rls_tenant_isolation`` conventions so
the startup RLS validation sees them as covered. DDL is expressed via
alembic ops and static ``sa.text`` statements only — no string formatting of
SQL fragments anywhere in this revision.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "pa_wave2_authority_payouts_cost"
down_revision = "add_payment_mandates"
branch_labels = None
depends_on = None


# Idempotent tenant RLS posture per table (select/all on app.current_agency_id).
# Safe against tables that a service's lazy Base.metadata.create_all created
# before this migration ran: ENABLE RLS is idempotent and policies are only
# created when absent (Postgres has no CREATE POLICY IF NOT EXISTS). Fully
# static SQL — no formatted fragments.
_RLS_STATEMENTS: dict[str, tuple[sa.TextClause, ...]] = {
    "authority_approvals": (
        sa.text("ALTER TABLE authority_approvals ENABLE ROW LEVEL SECURITY"),
        sa.text("ALTER TABLE authority_approvals FORCE ROW LEVEL SECURITY"),
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policy
                    WHERE polrelid = 'authority_approvals'::regclass
                      AND polname = 'waypoint_rls_select'
                ) THEN
                    CREATE POLICY waypoint_rls_select ON authority_approvals
                        FOR SELECT USING (
                            agency_id = current_setting('app.current_agency_id', TRUE)
                        );
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policy
                    WHERE polrelid = 'authority_approvals'::regclass
                      AND polname = 'waypoint_rls_all'
                ) THEN
                    CREATE POLICY waypoint_rls_all ON authority_approvals
                        USING (agency_id = current_setting('app.current_agency_id', TRUE))
                        WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE));
                END IF;
            END $$;
            """
        ),
    ),
    "advisor_payouts": (
        sa.text("ALTER TABLE advisor_payouts ENABLE ROW LEVEL SECURITY"),
        sa.text("ALTER TABLE advisor_payouts FORCE ROW LEVEL SECURITY"),
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policy
                    WHERE polrelid = 'advisor_payouts'::regclass
                      AND polname = 'waypoint_rls_select'
                ) THEN
                    CREATE POLICY waypoint_rls_select ON advisor_payouts
                        FOR SELECT USING (
                            agency_id = current_setting('app.current_agency_id', TRUE)
                        );
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policy
                    WHERE polrelid = 'advisor_payouts'::regclass
                      AND polname = 'waypoint_rls_all'
                ) THEN
                    CREATE POLICY waypoint_rls_all ON advisor_payouts
                        USING (agency_id = current_setting('app.current_agency_id', TRUE))
                        WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE));
                END IF;
            END $$;
            """
        ),
    ),
}


def _apply_rls(conn: sa.engine.Connection, table: str) -> None:
    for statement in _RLS_STATEMENTS[table]:
        conn.execute(statement)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. usage_events run/trip correlation columns (guarded, additive)
    # ------------------------------------------------------------------
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "usage_events" in inspector.get_table_names():
        existing_columns = {c["name"] for c in inspector.get_columns("usage_events")}
        if "run_id" not in existing_columns:
            op.add_column("usage_events", sa.Column("run_id", sa.String(length=64), nullable=True))
        if "trip_id" not in existing_columns:
            op.add_column("usage_events", sa.Column("trip_id", sa.String(length=255), nullable=True))

    # ------------------------------------------------------------------
    # 2. authority_approvals (PA-08 dual-control approval ledger)
    # ------------------------------------------------------------------
    if "authority_approvals" not in inspector.get_table_names():
        # Inspector-guarded: the backing service lazily create_alls the same
        # schema (checkfirst) when SQL mode activates before this migration
        # runs; both orderings must converge on the same posture.
        op.create_table(
            "authority_approvals",
            sa.Column("approval_id", sa.String(length=64), nullable=False),
            sa.Column("agency_id", sa.String(length=64), nullable=False),
            sa.Column("action", sa.String(length=120), nullable=False),
            sa.Column("subject_type", sa.String(length=40), nullable=False),
            sa.Column("subject_id", sa.String(length=255), nullable=False),
            sa.Column("amount_usd", sa.Numeric(14, 2), nullable=True),
            sa.Column("requested_by", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending_second"),
            sa.Column("first_approver_id", sa.String(length=255), nullable=True),
            sa.Column("first_approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("second_approver_id", sa.String(length=255), nullable=True),
            sa.Column("second_approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reason", sa.String(length=500), nullable=True),
            sa.Column("denial_reason", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("approval_id"),
        )
        op.create_index("ix_authority_approvals_agency_id", "authority_approvals", ["agency_id"])
        op.create_index("ix_authority_approvals_subject_id", "authority_approvals", ["subject_id"])
    _apply_rls(conn, "authority_approvals")

    # ------------------------------------------------------------------
    # 3. advisor_payouts (PA-23 durable payout ledger)
    # ------------------------------------------------------------------
    if "advisor_payouts" not in inspector.get_table_names():
        op.create_table(
            "advisor_payouts",
            sa.Column("payout_id", sa.String(length=64), nullable=False),
            sa.Column("agency_id", sa.String(length=64), nullable=False),
            sa.Column("advisor_id", sa.String(length=255), nullable=False),
            sa.Column("amount_usd", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
            sa.Column("trip_id", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="recorded"),
            sa.Column("payout_ref", sa.String(length=64), nullable=False),
            sa.Column("recorded_by", sa.String(length=255), nullable=False),
            sa.Column("method", sa.String(length=40), nullable=False, server_default="DIRECT_DEPOSIT"),
            sa.Column("authority_approval_id", sa.String(length=64), nullable=True),
            sa.Column("note", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("payout_id"),
            sa.UniqueConstraint("payout_ref", name="uq_advisor_payouts_payout_ref"),
        )
        op.create_index("ix_advisor_payouts_agency_id", "advisor_payouts", ["agency_id"])
        op.create_index("ix_advisor_payouts_advisor_id", "advisor_payouts", ["advisor_id"])
        op.create_index("ix_advisor_payouts_trip_id", "advisor_payouts", ["trip_id"])
    _apply_rls(conn, "advisor_payouts")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_all ON advisor_payouts"))
    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_select ON advisor_payouts"))
    op.drop_index("ix_advisor_payouts_trip_id", table_name="advisor_payouts")
    op.drop_index("ix_advisor_payouts_advisor_id", table_name="advisor_payouts")
    op.drop_index("ix_advisor_payouts_agency_id", table_name="advisor_payouts")
    op.drop_table("advisor_payouts")

    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_all ON authority_approvals"))
    conn.execute(sa.text("DROP POLICY IF EXISTS waypoint_rls_select ON authority_approvals"))
    op.drop_index("ix_authority_approvals_subject_id", table_name="authority_approvals")
    op.drop_index("ix_authority_approvals_agency_id", table_name="authority_approvals")
    op.drop_table("authority_approvals")
    # usage_events columns are nullable additions to a table whose DDL is
    # owned by the usage store; they are left in place on downgrade (dropping
    # them would be destructive against a store that may already write them).
