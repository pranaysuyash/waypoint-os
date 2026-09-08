"""Booking confirmations: one active confirmation per (trip, confirmation_type)

Revision ID: bc_active_type_uniqueness
Revises: pa_wave2_authority_payouts_cost
Create Date: 2026-09-07

Part-J #3 (codex follow-up review, 2026-09-07): fulfillment replay-repair can
record the same booking confirmation twice when a crash lands between the SQL
record and the trip-blob update. The durable backstop is a partial unique
index: at most one NON-voided confirmation per (trip_id, confirmation_type).
Voided rows are excluded so a legitimate re-issue after a void stays legal.

Upgrade is guarded: any duplicate active rows are voided first (newest kept,
older rows voided via parameterized statements — history preserved, nothing
deleted), then the unique index is created. DDL is expressed via alembic ops
and static ``sa.text`` statements with bound parameters only — no string
formatting of SQL fragments anywhere in this revision. The matching
model-level index lives in ``spine_api/models/tenant.py`` so the lazy
``create_all`` path converges on the same posture.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "bc_active_type_uniqueness"
down_revision = "pa_wave2_authority_payouts_cost"
branch_labels = None
depends_on = None

_INDEX_NAME = "uq_bc_trip_type_active"

# ids of duplicate active confirmations (newest per trip+type kept)
_SELECT_DUPLICATE_IDS = sa.text(
    """
    SELECT id FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY trip_id, confirmation_type
                   ORDER BY created_at DESC, id DESC
               ) AS rn
        FROM booking_confirmations
        WHERE confirmation_status != 'voided'
    ) ranked
    WHERE ranked.rn > 1
    """
)

# parameterized void of one duplicate row
_VOID_ONE = sa.text(
    """
    UPDATE booking_confirmations
    SET confirmation_status = 'voided',
        voided_by = :voided_by,
        voided_at = NOW()
    WHERE id = :confirmation_id
    """
)


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "booking_confirmations" not in inspector.get_table_names():
        return

    existing_indexes = {ix["name"] for ix in inspector.get_indexes("booking_confirmations")}
    if _INDEX_NAME not in existing_indexes:
        duplicate_ids = conn.execute(_SELECT_DUPLICATE_IDS).scalars().all()
        for confirmation_id in duplicate_ids:
            conn.execute(
                _VOID_ONE,
                {
                    "voided_by": "migration_bc_active_type_uniqueness",
                    "confirmation_id": confirmation_id,
                },
            )
        op.create_index(
            _INDEX_NAME,
            "booking_confirmations",
            ["trip_id", "confirmation_type"],
            unique=True,
            postgresql_where=sa.text("confirmation_status != 'voided'"),
            sqlite_where=sa.text("confirmation_status != 'voided'"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "booking_confirmations" not in inspector.get_table_names():
        return
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("booking_confirmations")}
    if _INDEX_NAME in existing_indexes:
        op.drop_index(_INDEX_NAME, table_name="booking_confirmations")
