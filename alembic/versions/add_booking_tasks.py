"""add booking_tasks table

Revision ID: add_booking_tasks
Revises: add_extraction_attempts
Create Date: 2026-05-09
"""

from typing import Union, Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'add_booking_tasks'
down_revision: Union[str, Sequence[str], None] = 'add_extraction_attempts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return bind.dialect.has_table(bind, name)


def upgrade() -> None:
    if not _has_table("booking_tasks"):
        op.create_table(
            "booking_tasks",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("trip_id", sa.String(36), nullable=False),
            sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("task_type", sa.String(40), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.String(500), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
            sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
            sa.Column("owner_id", sa.String(36), nullable=True),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("blocker_code", sa.String(40), nullable=True),
            sa.Column("blocker_refs", sa.JSON, nullable=True),
            sa.Column("source", sa.String(30), nullable=False, server_default="agent_created"),
            sa.Column("generation_hash", sa.String(64), nullable=True),
            sa.Column("created_by", sa.String(36), nullable=False),
            sa.Column("completed_by", sa.String(36), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_bt_trip_id", "booking_tasks", ["trip_id"])
        op.create_index("ix_bt_agency_id", "booking_tasks", ["agency_id"])
        op.create_index("ix_bt_status", "booking_tasks", ["status"])
        op.create_index("ix_bt_task_type", "booking_tasks", ["task_type"])
        op.create_index("ix_bt_trip_status", "booking_tasks", ["trip_id", "status"])
        op.create_index("ix_bt_generation_hash", "booking_tasks", ["generation_hash"])


def downgrade() -> None:
    if _has_table("booking_tasks"):
        op.drop_index("ix_bt_generation_hash", table_name="booking_tasks")
        op.drop_index("ix_bt_trip_status", table_name="booking_tasks")
        op.drop_index("ix_bt_task_type", table_name="booking_tasks")
        op.drop_index("ix_bt_status", table_name="booking_tasks")
        op.drop_index("ix_bt_agency_id", table_name="booking_tasks")
        op.drop_index("ix_bt_trip_id", table_name="booking_tasks")
        op.drop_table("booking_tasks")
