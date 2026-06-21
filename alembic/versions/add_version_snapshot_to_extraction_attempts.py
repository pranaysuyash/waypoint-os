"""Add version_snapshot to document_extraction_attempts.

Revision ID: add_version_snapshot_to_extraction_attempts
Create Date: 2026-06-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "add_version_snapshot_to_extraction_attempts"
down_revision = "add_extraction_attempts_and_pdf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_extraction_attempts",
        sa.Column("version_snapshot", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("document_extraction_attempts", "version_snapshot")
