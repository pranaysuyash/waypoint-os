"""Add booking_documents table for secure document upload

Revision ID: add_booking_documents
Revises: f1a2b3c4d5e6
Create Date: 2026-05-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_booking_documents'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "booking_documents" not in tables:
        op.create_table(
            "booking_documents",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
            sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("traveler_id", sa.String(36), nullable=True),
            sa.Column("uploaded_by_type", sa.String(20), nullable=False),
            sa.Column("uploaded_by_id", sa.String(36), nullable=True),
            sa.Column(
                "collection_token_id", sa.String(36),
                sa.ForeignKey("booking_collection_tokens.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("filename_hash", sa.String(64), nullable=False),
            sa.Column("filename_ext", sa.String(10), nullable=False),
            sa.Column("storage_key", sa.String(512), nullable=False),
            sa.Column("mime_type", sa.String(100), nullable=False),
            sa.Column("size_bytes", sa.Integer, nullable=False),
            sa.Column("sha256", sa.String(64), nullable=False),
            sa.Column("document_type", sa.String(30), nullable=False),
            sa.Column("status", sa.String(20), server_default="pending_review"),
            sa.Column("scan_status", sa.String(20), server_default="skipped"),
            sa.Column("review_notes_present", sa.Boolean, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
            sa.Column("storage_delete_status", sa.String(20), nullable=True),
        )
        op.create_index("ix_bd_trip_id", "booking_documents", ["trip_id"])
        op.create_index("ix_bd_agency_id", "booking_documents", ["agency_id"])
        op.create_index("ix_bd_status", "booking_documents", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "booking_documents" in tables:
        op.drop_table("booking_documents")
