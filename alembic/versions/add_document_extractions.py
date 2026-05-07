"""Add document_extractions table for OCR extraction

Revision ID: add_document_extractions
Revises: add_booking_documents
Create Date: 2026-05-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_document_extractions'
down_revision: Union[str, Sequence[str], None] = 'add_booking_documents'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "document_extractions" not in tables:
        op.create_table(
            "document_extractions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "document_id", sa.String(36),
                sa.ForeignKey("booking_documents.id", ondelete="CASCADE"),
                unique=True, nullable=False,
            ),
            sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
            sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("extracted_fields_encrypted", sa.JSON, nullable=True),
            sa.Column("fields_present", sa.JSON, nullable=True),
            sa.Column("field_count", sa.Integer, server_default="0"),
            sa.Column("confidence_scores", sa.JSON, nullable=True),
            sa.Column("overall_confidence", sa.Float, nullable=True),
            sa.Column("status", sa.String(20), server_default="pending_review"),
            sa.Column("extracted_by", sa.String(20), server_default="noop_extractor"),
            sa.Column("reviewed_by", sa.String(36), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_de_document_id", "document_extractions", ["document_id"], unique=True)
        op.create_index("ix_de_trip_id", "document_extractions", ["trip_id"])
        op.create_index("ix_de_status", "document_extractions", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "document_extractions" in tables:
        op.drop_table("document_extractions")
