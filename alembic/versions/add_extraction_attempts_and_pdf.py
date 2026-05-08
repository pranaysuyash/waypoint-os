"""Add extraction attempts table and Phase 4E columns.

Creates document_extraction_attempts table and adds attempt tracking columns
to document_extractions.

Revision ID: add_extraction_attempts
Revises: add_priorities_flex
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_extraction_attempts'
down_revision: Union[str, Sequence[str], None] = 'add_extraction_provider_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    """Check if a column already exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name = :table AND column_name = :column"
    ), {"table": table, "column": column})
    return result.scalar() > 0


def _has_table(table: str) -> bool:
    """Check if a table already exists."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_name = :table"
    ), {"table": table})
    return result.scalar() > 0


def upgrade() -> None:
    # 1. Create document_extraction_attempts table
    if not _has_table("document_extraction_attempts"):
        op.create_table(
            "document_extraction_attempts",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("extraction_id", sa.String(36), sa.ForeignKey("document_extractions.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("run_number", sa.Integer, nullable=False),
            sa.Column("attempt_number", sa.Integer, nullable=False),
            sa.Column("fallback_rank", sa.Integer, nullable=True),
            sa.Column("provider_name", sa.String(30), nullable=False),
            sa.Column("model_name", sa.String(50), nullable=True),
            sa.Column("latency_ms", sa.Integer, nullable=True),
            sa.Column("prompt_tokens", sa.Integer, nullable=True),
            sa.Column("completion_tokens", sa.Integer, nullable=True),
            sa.Column("total_tokens", sa.Integer, nullable=True),
            sa.Column("cost_estimate_usd", sa.Float, nullable=True),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("error_code", sa.String(50), nullable=True),
            sa.Column("error_summary", sa.String(200), nullable=True),
            sa.Column("extracted_fields_encrypted", sa.JSON, nullable=True),
            sa.Column("fields_present", sa.JSON, nullable=True),
            sa.Column("field_count", sa.Integer, server_default="0"),
            sa.Column("confidence_scores", sa.JSON, nullable=True),
            sa.Column("overall_confidence", sa.Float, nullable=True),
            sa.Column("confidence_method", sa.String(30), server_default="model"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    # 2. Add new columns to document_extractions
    if not _has_column("document_extractions", "current_attempt_id"):
        op.add_column("document_extractions",
            sa.Column("current_attempt_id", sa.String(36), nullable=True))
        op.create_index("ix_de_current_attempt_id", "document_extractions", ["current_attempt_id"])

    if not _has_column("document_extractions", "attempt_count"):
        op.add_column("document_extractions",
            sa.Column("attempt_count", sa.Integer, server_default="0"))

    if not _has_column("document_extractions", "run_count"):
        op.add_column("document_extractions",
            sa.Column("run_count", sa.Integer, server_default="0"))

    if not _has_column("document_extractions", "page_count"):
        op.add_column("document_extractions",
            sa.Column("page_count", sa.Integer, nullable=True))

    # 3. Backfill: create attempt rows for existing extractions
    conn = op.get_bind()

    # Backfill successful extractions
    conn.execute(sa.text("""
        INSERT INTO document_extraction_attempts (
            id, extraction_id, run_number, attempt_number, fallback_rank,
            provider_name, model_name, latency_ms, prompt_tokens, completion_tokens,
            total_tokens, cost_estimate_usd, status, error_code, error_summary,
            extracted_fields_encrypted, fields_present, field_count,
            confidence_scores, overall_confidence, confidence_method, created_at
        )
        SELECT
            gen_random_uuid()::text,
            e.id, 1, 1, 0,
            COALESCE(e.provider_name, e.extracted_by, 'noop_extractor'),
            e.model_name, e.latency_ms, e.prompt_tokens, e.completion_tokens,
            e.total_tokens, e.cost_estimate_usd,
            'success', NULL, NULL,
            e.extracted_fields_encrypted, e.fields_present, e.field_count,
            e.confidence_scores, e.overall_confidence,
            COALESCE(e.confidence_method, 'model'),
            COALESCE(e.created_at, NOW())
        FROM document_extractions e
        WHERE e.status IN ('pending_review', 'applied', 'rejected')
          AND NOT EXISTS (
              SELECT 1 FROM document_extraction_attempts a WHERE a.extraction_id = e.id
          )
    """))

    # Backfill failed extractions
    conn.execute(sa.text("""
        INSERT INTO document_extraction_attempts (
            id, extraction_id, run_number, attempt_number, fallback_rank,
            provider_name, model_name, latency_ms, status, error_code, error_summary,
            field_count, confidence_method, created_at
        )
        SELECT
            gen_random_uuid()::text,
            e.id, 1, 1, 0,
            COALESCE(e.provider_name, e.extracted_by, 'unknown'),
            e.model_name, e.latency_ms,
            'failed', e.error_code, e.error_summary,
            0, 'model',
            COALESCE(e.created_at, NOW())
        FROM document_extractions e
        WHERE e.status = 'failed'
          AND NOT EXISTS (
              SELECT 1 FROM document_extraction_attempts a WHERE a.extraction_id = e.id
          )
    """))

    # Set attempt_count, run_count, and current_attempt_id for existing extractions
    conn.execute(sa.text("""
        UPDATE document_extractions e SET
            attempt_count = 1,
            run_count = 1,
            current_attempt_id = (
                SELECT a.id FROM document_extraction_attempts a
                WHERE a.extraction_id = e.id AND a.status = 'success'
                ORDER BY a.created_at DESC LIMIT 1
            )
        WHERE e.attempt_count = 0
          AND EXISTS (SELECT 1 FROM document_extraction_attempts a WHERE a.extraction_id = e.id)
    """))

    # Failed extractions: attempt_count=1 but current_attempt_id stays NULL
    conn.execute(sa.text("""
        UPDATE document_extractions e SET
            attempt_count = 1,
            run_count = 1
        WHERE e.status = 'failed'
          AND e.attempt_count = 0
          AND EXISTS (SELECT 1 FROM document_extraction_attempts a WHERE a.extraction_id = e.id)
    """))


def downgrade() -> None:
    # Remove backfilled columns from document_extractions
    for col in ("page_count", "run_count", "attempt_count", "current_attempt_id"):
        if _has_column("document_extractions", col):
            op.drop_column("document_extractions", col)

    if _has_column("document_extractions", "current_attempt_id"):
        op.drop_index("ix_de_current_attempt_id", "document_extractions")

    # Drop attempts table
    if _has_table("document_extraction_attempts"):
        op.drop_table("document_extraction_attempts")
