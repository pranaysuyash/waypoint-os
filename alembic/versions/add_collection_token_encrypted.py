"""Add plain_token_encrypted to booking_collection_tokens

Revision ID: add_collection_token_encrypted
Revises: add_rls_phase5e_full_coverage
Create Date: 2026-05-18

Stores the plain collection token (Fernet-encrypted) alongside the existing
token_hash. This allows authenticated agency operators to re-view/copy an
active collection link after page reload or in a different session, without
revoking and regenerating the link.

token_hash remains the public lookup identity (unchanged).
plain_token_encrypted stores encrypt_field(plain_token) for authenticated re-display.

Nullable — no backfill needed for pre-existing rows. Those rows will return
collection_url=null from GET until the token is revoked and regenerated.
"""

from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "add_collection_token_encrypted"
down_revision: Union[str, Sequence[str], None] = "add_rls_phase5e_full_coverage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get current table names to guard against re-runs
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columns = {c["name"] for c in inspector.get_columns("booking_collection_tokens")}

    if "plain_token_encrypted" not in columns:
        op.add_column(
            "booking_collection_tokens",
            sa.Column("plain_token_encrypted", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("booking_collection_tokens", "plain_token_encrypted")
