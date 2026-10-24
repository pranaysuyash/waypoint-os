"""Preserve replay protection per real booking component.

Revision ID: bc_component_identity
Revises: add_customer_memory_profiles
Create Date: 2026-10-23

Legacy rows and writers retain primary. No confirmation is deleted or voided.
Supersession evidence: Docs/review/AUDIT_IMPLEMENTATION_2026-10-23.md.
"""

from alembic import op
import sqlalchemy as sa

revision = "bc_component_identity"
down_revision = "add_customer_memory_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "component_key" not in {c["name"] for c in inspector.get_columns("booking_confirmations")}:
        op.add_column("booking_confirmations", sa.Column(
            "component_key", sa.String(96), nullable=False, server_default="primary",
        ))
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("booking_confirmations")}
    if "uq_bc_component_active" not in indexes:
        # Install the stronger identity before retiring the superseded index.
        op.create_index(
            "uq_bc_component_active", "booking_confirmations",
            ["agency_id", "trip_id", "confirmation_type", "component_key"], unique=True,
            postgresql_where=sa.text("confirmation_status != 'voided'"),
            sqlite_where=sa.text("confirmation_status != 'voided'"),
        )
    if "uq_bc_trip_type_active" in indexes:
        op.drop_index("uq_bc_trip_type_active", table_name="booking_confirmations")


def downgrade() -> None:
    connection = op.get_bind()
    # Reversal must not erase the identity of even a historical voided row.
    non_primary = connection.execute(sa.text(
        "SELECT COUNT(*) FROM booking_confirmations WHERE component_key != 'primary'"
    )).scalar_one()
    old_identity_conflict = connection.execute(sa.text(
        "SELECT COUNT(*) FROM (SELECT trip_id, confirmation_type FROM booking_confirmations "
        "WHERE confirmation_status != 'voided' GROUP BY trip_id, confirmation_type "
        "HAVING COUNT(*) > 1) AS conflicts"
    )).scalar_one()
    if non_primary or old_identity_conflict:
        raise RuntimeError("Cannot downgrade: preserve booking component identities before reverting schema")
    op.create_index(
        "uq_bc_trip_type_active", "booking_confirmations", ["trip_id", "confirmation_type"],
        unique=True, postgresql_where=sa.text("confirmation_status != 'voided'"),
        sqlite_where=sa.text("confirmation_status != 'voided'"),
    )
    op.drop_index("uq_bc_component_active", table_name="booking_confirmations")
    op.drop_column("booking_confirmations", "component_key")
