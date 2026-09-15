"""
spine_api.models.proposal_tokens — Durable public proposal capability registry (FND-0219).

Backs ``spine_api.services.proposal_token_store.ProposalTokenStore``. One row
per issued public proposal capability token (the traveler-facing
``/api/public/proposals/{token}`` credential).

Security model (first principles: a public token is a capability URL — treat
it as a real credential):

- The raw token material NEVER touches durable storage. Rows are keyed by
  ``token_hash`` (SHA-256 hex of the token); ``lookup_prefix`` carries the
  first 16 hex characters of that hash for operator diagnosis without
  revealing the credential. Lookup is always hash-of-presented-token.
- ``expires_at`` is the credential TTL; ``revoked_at`` is the durable
  revocation timestamp. Both are enforced on every verification.
- ``consented_by`` / ``consented_at`` / ``purpose`` form the consent artifact:
  the authenticated principal who authorized external (traveler) sharing of
  the trip's proposal data, when, and for what purpose.
- ``format_version`` records the token wire-format generation ("v3" opaque
  ``propv3_<urlsafe>`` tokens vs the legacy signed "v2" ``prop_...`` format)
  so replay of an issuance is explicitly versioned rather than implicit.

System-scoped table — intentionally NOT RLS-protected (same precedent as
``idempotency_keys``): the public verification path runs OUTSIDE any
authenticated agency session (travelers do not log in), so agency-scoped RLS
would fail the design closed. Rows are addressed exclusively by the opaque
256-bit credential hash — never by tenant attributes — and ``agency_id`` /
``trip_id`` are recorded as binding and audit metadata. Traveler access is
authorized by possession of the credential plus row-level TTL/revocation
checks, not by a tenant session.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


def _new_row_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProposalAccessToken(Base):
    """One row per issued public proposal capability token (FND-0219)."""

    __tablename__ = "proposal_access_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_row_id
    )
    # SHA-256 hex digest of the raw token. Unique: re-issuing the exact same
    # token material (deterministic legacy v2 minting) resolves to this same
    # row instead of duplicating it (idempotent replay).
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # First 16 chars of token_hash — operator diagnosis aid only; lookups may
    # use it to narrow candidates but MUST confirm the full hash.
    lookup_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    format_version: Mapped[str] = mapped_column(String(8), nullable=False, default="v3")
    agency_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Bound resource: a credential only ever releases data for this trip (and,
    # when known, this proposal) — enforced at verification time.
    trip_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    proposal_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Consent artifact: who authorized external sharing, when, and why.
    consented_by: Mapped[str] = mapped_column(String(255), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    purpose: Mapped[str] = mapped_column(String(255), nullable=False, default="proposal_share")
