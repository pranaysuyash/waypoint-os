"""add frontier feature tables (ghost_workflows, emotional_state_logs, intelligence_pool, legacy_aspirations)

Revision ID: add_frontier_tables
Revises: add_audit_chain_hash
Create Date: 2026-08-30

A-20 remediation (partial): the four models in spine_api/models/frontier.py had
no migration files, so the tables did not exist in any migrated database and
every frontier endpoint touching them failed at runtime (confirmed 2026-08-30
via the cross-tenant router probe: `relation "ghost_workflows" does not exist`).

Additive only — creates the four tables exactly as defined by the models.
These tables carry agency_id and are intentionally NOT RLS-protected yet;
they are listed in RLS_EXCLUDED_AGENCY_TABLES with rationale, and their
router read paths are agency-filtered at the application layer (RQ-03
verdict, see Docs/review/A19_RLS_COVERAGE_RESOLUTION_2026-08-30.md).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_frontier_tables"
down_revision = "add_audit_chain_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ghost_workflows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agency_id", sa.String(length=36), nullable=False),
        sa.Column("trip_id", sa.String(length=36), nullable=False),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("action_payload", sa.JSON(), nullable=True),
        sa.Column("autonomic_level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'executing', 'completed', 'failed', 'escalated')",
            name="ck_ghost_workflows_status",
        ),
        sa.CheckConstraint(
            "autonomic_level BETWEEN 0 AND 4",
            name="ck_ghost_workflows_autonomic_level",
        ),
    )
    op.create_index("ix_ghost_workflows_agency_id", "ghost_workflows", ["agency_id"])
    op.create_index("ix_ghost_workflows_trip_id", "ghost_workflows", ["trip_id"])
    op.create_index("ix_ghost_workflows_status", "ghost_workflows", ["status"])

    op.create_table(
        "emotional_state_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agency_id", sa.String(length=36), nullable=False),
        sa.Column("traveler_id", sa.String(length=36), nullable=False),
        sa.Column("trip_id", sa.String(length=36), nullable=False),
        sa.Column("sentiment_score", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("anxiety_trigger", sa.String(length=255), nullable=True),
        sa.Column("mitigation_action_id", sa.String(length=36), nullable=True),
        sa.Column("recovery_time_ms", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "sentiment_score >= 0 AND sentiment_score <= 1",
            name="ck_emotional_state_logs_sentiment_score",
        ),
    )
    op.create_index("ix_emotional_state_logs_agency_id", "emotional_state_logs", ["agency_id"])
    op.create_index("ix_emotional_state_logs_trip_id", "emotional_state_logs", ["trip_id"])
    op.create_index("ix_emotional_state_logs_traveler_id", "emotional_state_logs", ["traveler_id"])

    op.create_table(
        "intelligence_pool",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("incident_type", sa.String(length=100), nullable=False),
        sa.Column("anonymized_data", sa.JSON(), nullable=True),
        sa.Column("severity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("source_agency_hash", sa.String(length=64), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "severity BETWEEN 1 AND 5",
            name="ck_intelligence_pool_severity",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_intelligence_pool_confidence",
        ),
    )
    op.create_index("ix_intelligence_pool_incident_type", "intelligence_pool", ["incident_type"])
    op.create_index("ix_intelligence_pool_severity", "intelligence_pool", ["severity"])

    op.create_table(
        "legacy_aspirations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("traveler_id", sa.String(length=36), nullable=False),
        sa.Column("agency_id", sa.String(length=36), nullable=False),
        sa.Column("goal_title", sa.String(length=255), nullable=False),
        sa.Column("target_year", sa.Integer(), nullable=False),
        sa.Column("fitness_window_age", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="aspirational", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('aspirational', 'planning', 'executed', 'cancelled')",
            name="ck_legacy_aspirations_status",
        ),
    )
    op.create_index("ix_legacy_aspirations_traveler_id", "legacy_aspirations", ["traveler_id"])
    op.create_index("ix_legacy_aspirations_agency_id", "legacy_aspirations", ["agency_id"])


def downgrade() -> None:
    op.drop_table("legacy_aspirations")
    op.drop_table("intelligence_pool")
    op.drop_table("emotional_state_logs")
    op.drop_table("ghost_workflows")
