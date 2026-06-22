"""Add version_snapshot to document_extraction_attempts.

Revision ID: add_snapshot_attempts
Create Date: 2026-06-20

Rebased onto add_agency_integrations (2026-06-22) to fix dangling branch.
The previous down_revision pointed at add_extraction_attempts, which is
not the current head — this created two alembic heads and prevented
future migrations from running cleanly.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "add_snapshot_attempts"
down_revision = "add_agency_integrations"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    """Check if a column already exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name = :table AND column_name = :column"
    ), {"table": table, "column": column})
    return result.scalar() > 0


def upgrade() -> None:
    if not _has_column("document_extraction_attempts", "version_snapshot"):
        op.add_column(
            "document_extraction_attempts",
            sa.Column("version_snapshot", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("document_extraction_attempts", "version_snapshot"):
        op.drop_column("document_extraction_attempts", "version_snapshot")
