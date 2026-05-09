"""add booking_confirmations + execution_events tables

Revision ID: add_booking_confirmations
Revises: add_booking_tasks
Create Date: 2026-05-09
"""

from typing import Union, Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'add_booking_confirmations'
down_revision: Union[str, Sequence[str], None] = 'add_booking_tasks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return bind.dialect.has_table(bind, name)


def upgrade() -> None:
    if not _has_table("booking_confirmations"):
        op.create_table(
            "booking_confirmations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("trip_id", sa.String(36), nullable=False),
            sa.Column("task_id", sa.String(36), sa.ForeignKey("booking_tasks.id", ondelete="SET NULL"), nullable=True),
            sa.Column("confirmation_type", sa.String(20), nullable=False),
            sa.Column("confirmation_status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("supplier_name_encrypted", sa.JSON, nullable=True),
            sa.Column("confirmation_number_encrypted", sa.JSON, nullable=True),
            sa.Column("notes_encrypted", sa.JSON, nullable=True),
            sa.Column("external_ref_encrypted", sa.JSON, nullable=True),
            sa.Column("has_supplier", sa.Boolean, default=False, server_default="0"),
            sa.Column("has_confirmation_number", sa.Boolean, default=False, server_default="0"),
            sa.Column("notes_present", sa.Boolean, default=False, server_default="0"),
            sa.Column("external_ref_present", sa.Boolean, default=False, server_default="0"),
            sa.Column("evidence_refs", sa.JSON, nullable=True),
            sa.Column("recorded_by", sa.String(36), nullable=True),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_by", sa.String(36), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("voided_by", sa.String(36), nullable=True),
            sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(36), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_bc_trip_id", "booking_confirmations", ["trip_id"])
        op.create_index("ix_bc_agency_id", "booking_confirmations", ["agency_id"])
        op.create_index("ix_bc_task_id", "booking_confirmations", ["task_id"])
        op.create_index("ix_bc_status", "booking_confirmations", ["confirmation_status"])
        op.create_index("ix_bc_type", "booking_confirmations", ["confirmation_type"])
        op.create_index("ix_bc_trip_status", "booking_confirmations", ["trip_id", "confirmation_status"])

    if not _has_table("execution_events"):
        op.create_table(
            "execution_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("trip_id", sa.String(36), nullable=False),
            sa.Column("subject_type", sa.String(30), nullable=False),
            sa.Column("subject_id", sa.String(36), nullable=False),
            sa.Column("event_type", sa.String(40), nullable=False),
            sa.Column("event_category", sa.String(20), nullable=False),
            sa.Column("status_from", sa.String(20), nullable=True),
            sa.Column("status_to", sa.String(20), nullable=False),
            sa.Column("actor_type", sa.String(20), nullable=False, server_default="system"),
            sa.Column("actor_id", sa.String(36), nullable=True),
            sa.Column("source", sa.String(30), nullable=False, server_default="agent_action"),
            sa.Column("event_metadata", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_ee_trip_id", "execution_events", ["trip_id"])
        op.create_index("ix_ee_agency_id", "execution_events", ["agency_id"])
        op.create_index("ix_ee_subject", "execution_events", ["subject_type", "subject_id"])
        op.create_index("ix_ee_category", "execution_events", ["event_category"])
        op.create_index("ix_ee_trip_created", "execution_events", ["trip_id", "created_at"])


def downgrade() -> None:
    if _has_table("execution_events"):
        op.drop_index("ix_ee_trip_created", table_name="execution_events")
        op.drop_index("ix_ee_category", table_name="execution_events")
        op.drop_index("ix_ee_subject", table_name="execution_events")
        op.drop_index("ix_ee_agency_id", table_name="execution_events")
        op.drop_index("ix_ee_trip_id", table_name="execution_events")
        op.drop_table("execution_events")

    if _has_table("booking_confirmations"):
        op.drop_index("ix_bc_trip_status", table_name="booking_confirmations")
        op.drop_index("ix_bc_type", table_name="booking_confirmations")
        op.drop_index("ix_bc_status", table_name="booking_confirmations")
        op.drop_index("ix_bc_task_id", table_name="booking_confirmations")
        op.drop_index("ix_bc_agency_id", table_name="booking_confirmations")
        op.drop_index("ix_bc_trip_id", table_name="booking_confirmations")
        op.drop_table("booking_confirmations")
