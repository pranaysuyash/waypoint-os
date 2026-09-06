"""Add the acquisition-generation fence to idempotency rows (X-11/N-06).

The initial idempotency table may already exist in a database created from an
earlier checkout. This migration is deliberately introspective so both that
database and a fresh database (where the column is already declared by the
table migration) converge on the same schema without a duplicate-column
failure.
"""

from alembic import op
import sqlalchemy as sa


revision = "add_idempotency_fencing_token"
down_revision = "add_platform_role_to_users"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return column in {item["name"] for item in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "idempotency_keys", "fencing_token"):
        op.add_column(
            "idempotency_keys",
            sa.Column("fencing_token", sa.String(length=128), nullable=True),
        )
        # Existing rows represent an owner that may still be running. Give
        # each one an opaque generation before making the invariant required.
        op.execute(
            sa.text(
                "UPDATE idempotency_keys "
                "SET fencing_token = 'legacy-' || md5(key) "
                "WHERE fencing_token IS NULL"
            )
        )
        op.alter_column(
            "idempotency_keys",
            "fencing_token",
            existing_type=sa.String(length=128),
            nullable=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "idempotency_keys", "fencing_token"):
        op.drop_column("idempotency_keys", "fencing_token")
