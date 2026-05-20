"""Add agency_integrations table

Revision ID: add_agency_integrations
Revises: add_agent_requeue_jobs
Create Date: 2026-05-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "add_agency_integrations"
down_revision: Union[str, Sequence[str], None] = "add_agent_requeue_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create agency_integrations table with RLS policies matching waypoint conventions."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "agency_integrations" in inspector.get_table_names():
        return

    op.create_table(
        "agency_integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "agency_id",
            sa.String(36),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(30), nullable=False, server_default="disabled"),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("credential_ref", sa.String(200), nullable=True),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(80), nullable=True),
        sa.Column("last_error_message_safe", sa.String(500), nullable=True),
        sa.Column("created_by_user_id", sa.String(36), nullable=True),
        sa.Column("updated_by_user_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('disabled', 'connected', 'degraded', 'auth_expired', 'misconfigured')",
            name="ck_agency_integrations_status",
        ),
    )

    op.create_unique_constraint(
        "uq_agency_integrations_agency_provider",
        "agency_integrations",
        ["agency_id", "provider"],
    )
    op.create_index("ix_ai_agency_id", "agency_integrations", ["agency_id"])
    op.create_index("ix_ai_provider", "agency_integrations", ["provider"])
    op.create_index(
        "ix_ai_agency_provider",
        "agency_integrations",
        ["agency_id", "provider"],
    )

    # Apply RLS using the canonical waypoint policy naming convention
    # (waypoint_rls_select + waypoint_rls_all + FORCE ROW LEVEL SECURITY)
    # consistent with add_rls_tenant_isolation.py and add_rls_phase5e_full_coverage.py.
    if bind.dialect.name == "postgresql":
        bind.execute(sa.text("ALTER TABLE agency_integrations ENABLE ROW LEVEL SECURITY"))
        bind.execute(sa.text("ALTER TABLE agency_integrations FORCE ROW LEVEL SECURITY"))
        bind.execute(sa.text(
            "CREATE POLICY waypoint_rls_select ON agency_integrations "
            "FOR SELECT "
            "USING (agency_id = current_setting('app.current_agency_id', TRUE))"
        ))
        bind.execute(sa.text(
            "CREATE POLICY waypoint_rls_all ON agency_integrations "
            "FOR ALL "
            "USING (agency_id = current_setting('app.current_agency_id', TRUE)) "
            "WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE))"
        ))


def downgrade() -> None:
    """Drop agency_integrations table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "agency_integrations" not in inspector.get_table_names():
        return

    if bind.dialect.name == "postgresql":
        bind.execute(sa.text(
            "DROP POLICY IF EXISTS waypoint_rls_all ON agency_integrations"
        ))
        bind.execute(sa.text(
            "DROP POLICY IF EXISTS waypoint_rls_select ON agency_integrations"
        ))

    op.drop_index("ix_ai_agency_provider", table_name="agency_integrations")
    op.drop_index("ix_ai_provider", table_name="agency_integrations")
    op.drop_index("ix_ai_agency_id", table_name="agency_integrations")
    op.drop_constraint(
        "uq_agency_integrations_agency_provider",
        "agency_integrations",
        type_="unique",
    )
    op.drop_table("agency_integrations")
