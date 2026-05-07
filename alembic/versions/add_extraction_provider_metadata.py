"""Add provider metadata columns to document_extractions

Revision ID: add_extraction_provider_metadata
Revises: add_document_extractions
Create Date: 2026-05-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_extraction_provider_metadata'
down_revision: Union[str, Sequence[str], None] = 'add_document_extractions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "document_extractions" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("document_extractions")}

    if "provider_name" not in columns:
        op.add_column("document_extractions",
                       sa.Column("provider_name", sa.String(30), server_default="noop_extractor"))
    if "model_name" not in columns:
        op.add_column("document_extractions",
                       sa.Column("model_name", sa.String(50), nullable=True))
    if "latency_ms" not in columns:
        op.add_column("document_extractions",
                       sa.Column("latency_ms", sa.Integer, nullable=True))
    if "prompt_tokens" not in columns:
        op.add_column("document_extractions",
                       sa.Column("prompt_tokens", sa.Integer, nullable=True))
    if "completion_tokens" not in columns:
        op.add_column("document_extractions",
                       sa.Column("completion_tokens", sa.Integer, nullable=True))
    if "total_tokens" not in columns:
        op.add_column("document_extractions",
                       sa.Column("total_tokens", sa.Integer, nullable=True))
    if "cost_estimate_usd" not in columns:
        op.add_column("document_extractions",
                       sa.Column("cost_estimate_usd", sa.Float, nullable=True))
    if "error_code" not in columns:
        op.add_column("document_extractions",
                       sa.Column("error_code", sa.String(50), nullable=True))
    if "error_summary" not in columns:
        op.add_column("document_extractions",
                       sa.Column("error_summary", sa.String(200), nullable=True))
    if "confidence_method" not in columns:
        op.add_column("document_extractions",
                       sa.Column("confidence_method", sa.String(30), server_default="model"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "document_extractions" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("document_extractions")}
    for col in ("confidence_method", "error_summary", "error_code",
                "cost_estimate_usd", "total_tokens", "completion_tokens",
                "prompt_tokens", "latency_ms", "model_name", "provider_name"):
        if col in columns:
            op.drop_column("document_extractions", col)
