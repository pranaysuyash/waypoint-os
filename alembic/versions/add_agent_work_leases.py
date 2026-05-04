"""Add durable agent work leases

Revision ID: add_agent_work_leases
Revises: add_booking_collection
Create Date: 2026-05-04 15:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_agent_work_leases"
down_revision: Union[str, Sequence[str], None] = "add_booking_collection"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if "agent_work_leases" not in tables:
        op.create_table(
            "agent_work_leases",
            sa.Column("idempotency_key", sa.String(500), primary_key=True),
            sa.Column("agent_name", sa.String(120), nullable=False),
            sa.Column("trip_id", sa.String(255), nullable=False),
            sa.Column("action", sa.String(120), nullable=False),
            sa.Column("owner", sa.String(120), nullable=False),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("leased_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_agent_work_leases_agent_name", "agent_work_leases", ["agent_name"])
        op.create_index("ix_agent_work_leases_trip_id", "agent_work_leases", ["trip_id"])
        op.create_index("ix_agent_work_leases_status", "agent_work_leases", ["status"])
        op.create_index("ix_agent_work_leases_leased_until", "agent_work_leases", ["leased_until"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "agent_work_leases" in inspector.get_table_names():
        op.drop_table("agent_work_leases")
