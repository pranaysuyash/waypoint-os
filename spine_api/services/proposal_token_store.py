"""
spine_api.services.proposal_token_store — Durable capability-token store for
the public proposal view (FND-0219).

A public proposal token is a capability URL: whoever holds it can read the
bound trip's proposal data without logging in. It is therefore a real
credential and gets real credential lifecycle semantics:

- Generation uses ``secrets.token_urlsafe(32)`` (256-bit opaque material).
  Durable storage keeps ONLY ``sha256(token)`` plus a short ``lookup_prefix``
  — never the raw token as a plaintext key.
- Every row records the bound resource (agency_id / trip_id / proposal_id),
  the TTL (``expires_at``), durable revocation (``revoked_at``), and the
  consent artifact for external sharing (``consented_by`` / ``consented_at``
  / ``purpose``).
- Verification is ordered: hash match -> TTL not elapsed -> not revoked ->
  resource binding (the caller may only project data for the row's
  ``trip_id``). Failure modes are uniform honest errors; callers must not
  distinguish "revoked" from "expired" from "unknown" toward the public.

Backends (modeled on ``src/agents/idempotency.py``):
- ``memory`` (default when constructed directly / in tests): in-process,
  correct for single-worker deployments and tests.
- ``sql``: durable ``proposal_access_tokens`` table
  (spine_api/models/proposal_tokens.py) on the app's async engine via the
  canonical sync->async bridge (``spine_api.persistence._run_async_blocking``).
  Cross-worker/cross-replica durable; issue is idempotent on ``token_hash``
  (concurrent INSERTs race one PK-unique conflict, loser replays).
- ``auto``: ``sql`` when DATABASE_URL is set, else ``memory``.

Selection via ``SPINE_API_PROPOSAL_TOKEN_BACKEND=memory|sql|auto``. Production
/ multi-worker deployments MUST run with ``sql`` (or ``auto`` with a database).
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Tuple

logger = logging.getLogger("spine_api.services.proposal_token_store")

PROPOSAL_TOKEN_BACKEND_ENV = "SPINE_API_PROPOSAL_TOKEN_BACKEND"

# FND-0219 documented default TTL: 30 days. Traveler proposal review cycles
# commonly span 1-3 weeks; 30 days bounds the credential's life while not
# expiring mid-negotiation. Overridable per issuance; the environment variable
# provides an ops lever without code change.
DEFAULT_ISSUANCE_TTL_HOURS = 720  # 30 days
PROPOSAL_TOKEN_TTL_HOURS_ENV = "PROPOSAL_TOKEN_TTL_HOURS"

# v3 opaque wire prefix. The legacy signed v2 format uses "prop_" (kept for
# backward compatibility in the router); old pre-hardening 16-hex tokens fail
# closed through the existing demo-allowlist/verifier path — no silent
# upgrade, honest errors.
V3_TOKEN_PREFIX = "propv3_"

_LOOKUP_PREFIX_CHARS = 16


class TokenStatus(str, Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"  # no row for the presented token hash


@dataclass(slots=True)
class ProposalTokenRecord:
    """Stored lifecycle record for one capability token."""

    token_hash: str
    lookup_prefix: str
    format_version: str
    agency_id: str
    trip_id: str
    proposal_id: Optional[str]
    issued_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]
    consented_by: str
    consented_at: datetime
    purpose: str


def hash_token(token: str) -> Tuple[str, str]:
    """Return ``(sha256_hex, lookup_prefix)`` for a raw token.

    The prefix is the first 16 hex characters of the digest: enough for an
    operator to correlate logs/rows, far short of the 256-bit credential.
    """
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return digest, digest[:_LOOKUP_PREFIX_CHARS]


def default_ttl_hours() -> int:
    """Resolve the configured default issuance TTL (documented: 30 days)."""
    raw = (os.getenv(PROPOSAL_TOKEN_TTL_HOURS_ENV) or "").strip()
    if raw:
        try:
            value = int(raw)
        except ValueError:
            logger.warning("Invalid %s=%r; using %sh", PROPOSAL_TOKEN_TTL_HOURS_ENV, raw, DEFAULT_ISSUANCE_TTL_HOURS)
        else:
            if value > 0:
                return value
            logger.warning("%s must be positive; using %sh", PROPOSAL_TOKEN_TTL_HOURS_ENV, DEFAULT_ISSUANCE_TTL_HOURS)
    return DEFAULT_ISSUANCE_TTL_HOURS


def new_token_material() -> str:
    """Mint fresh v3 opaque token material: 256-bit, URL-safe, stateless."""
    return f"{V3_TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


class MemoryProposalTokenBackend:
    """In-process backend: hash-keyed, thread-safe. Tests and single-worker."""

    def __init__(self) -> None:
        self._rows: dict[str, ProposalTokenRecord] = {}
        self._lock = threading.Lock()

    def issue(
        self,
        *,
        token_hash: str,
        lookup_prefix: str,
        format_version: str,
        agency_id: str,
        trip_id: str,
        proposal_id: Optional[str],
        issued_at: datetime,
        expires_at: datetime,
        consented_by: str,
        consented_at: datetime,
        purpose: str,
    ) -> Tuple[bool, ProposalTokenRecord]:
        record = ProposalTokenRecord(
            token_hash=token_hash,
            lookup_prefix=lookup_prefix,
            format_version=format_version,
            agency_id=agency_id,
            trip_id=trip_id,
            proposal_id=proposal_id,
            issued_at=issued_at,
            expires_at=expires_at,
            revoked_at=None,
            consented_by=consented_by,
            consented_at=consented_at,
            purpose=purpose,
        )
        with self._lock:
            existing = self._rows.get(token_hash)
            if existing is not None:
                # Idempotent replay: the credential already exists; return the
                # stored row (do not refresh TTL or overwrite the consent
                # artifact — replay must not extend a credential's life).
                return False, existing
            self._rows[token_hash] = record
            return True, record

    def lookup(self, token_hash: str) -> Optional[ProposalTokenRecord]:
        with self._lock:
            return self._rows.get(token_hash)

    def revoke(self, token_hash: str, revoked_at: datetime) -> bool:
        with self._lock:
            record = self._rows.get(token_hash)
            if record is None:
                return False
            if record.revoked_at is None:
                record.revoked_at = revoked_at
            return True

    def count(self) -> int:
        with self._lock:
            return len(self._rows)


class SqlProposalTokenBackend:
    """Durable SQL backend (``proposal_access_tokens`` table).

    Presents the same synchronous interface as the memory backend; async
    SQLAlchemy runs on the repo's canonical sync->async bridge
    (``spine_api.persistence._run_async_blocking``), exactly like
    ``SqlIdempotencyBackend``. All engine/model imports are lazy so importing
    this module (or running with the memory backend) never requires
    DATABASE_URL.
    """

    def __init__(self, engine=None, session_maker=None):
        self._engine = engine
        self._session_maker = session_maker
        self._table_ready = False

    def _get_engine(self):
        if self._engine is None:
            from spine_api.core.database import engine as app_engine

            self._engine = app_engine
        return self._engine

    def _get_session_maker(self):
        if self._session_maker is None:
            from spine_api.core.database import async_session_maker

            self._session_maker = async_session_maker
        return self._session_maker

    def _run(self, coro):
        from spine_api.persistence import _run_async_blocking

        return _run_async_blocking(coro)

    async def _ensure_table(self) -> None:
        if self._table_ready:
            return
        from spine_api.core.database import Base
        from spine_api.models.proposal_tokens import ProposalAccessToken

        # Additive-only safety net for environments that have not run the
        # alembic migration yet (mirrors SqlIdempotencyBackend); the alembic
        # migration remains the canonical schema path. checkfirst keeps this
        # idempotent — never drops or rewrites existing data.
        async with self._get_engine().begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn, tables=[ProposalAccessToken.__table__], checkfirst=True
                )
            )
        self._table_ready = True

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @staticmethod
    def _record_from_row(row) -> ProposalTokenRecord:
        return ProposalTokenRecord(
            token_hash=row.token_hash,
            lookup_prefix=row.lookup_prefix,
            format_version=row.format_version,
            agency_id=row.agency_id,
            trip_id=row.trip_id,
            proposal_id=row.proposal_id,
            issued_at=SqlProposalTokenBackend._as_utc(row.issued_at),
            expires_at=SqlProposalTokenBackend._as_utc(row.expires_at),
            revoked_at=(
                SqlProposalTokenBackend._as_utc(row.revoked_at)
                if row.revoked_at is not None
                else None
            ),
            consented_by=row.consented_by,
            consented_at=SqlProposalTokenBackend._as_utc(row.consented_at),
            purpose=row.purpose,
        )

    # ------------------------------------------------------------------
    # Synchronous interface (mirrors MemoryProposalTokenBackend)
    # ------------------------------------------------------------------

    def issue(
        self,
        *,
        token_hash: str,
        lookup_prefix: str,
        format_version: str,
        agency_id: str,
        trip_id: str,
        proposal_id: Optional[str],
        issued_at: datetime,
        expires_at: datetime,
        consented_by: str,
        consented_at: datetime,
        purpose: str,
    ) -> Tuple[bool, ProposalTokenRecord]:
        return self._run(
            self._issue_async(
                token_hash=token_hash,
                lookup_prefix=lookup_prefix,
                format_version=format_version,
                agency_id=agency_id,
                trip_id=trip_id,
                proposal_id=proposal_id,
                issued_at=issued_at,
                expires_at=expires_at,
                consented_by=consented_by,
                consented_at=consented_at,
                purpose=purpose,
            )
        )

    async def _issue_async(self, **kwargs) -> Tuple[bool, ProposalTokenRecord]:
        from sqlalchemy.exc import IntegrityError, OperationalError

        from spine_api.models.proposal_tokens import ProposalAccessToken

        await self._ensure_table()
        session_maker = self._get_session_maker()
        # ON CONFLICT DO NOTHING semantics via unique-PK race: concurrent
        # issuers INSERT the same token_hash and exactly one wins; the loser
        # replays the stored row (never truncates or overwrites data).
        async with session_maker() as session:
            session.add(ProposalAccessToken(**kwargs))
            try:
                await session.commit()
                return True, _record_from_kwargs(kwargs)
            except (IntegrityError, OperationalError):
                await session.rollback()
            row = (
                await session.execute(
                    select_proposal_token_by_hash(kwargs["token_hash"])
                )
            ).scalar_one_or_none()
            if row is None:
                raise RuntimeError(
                    f"Proposal token row for hash prefix {kwargs['lookup_prefix']!r} "
                    "vanished while issuing"
                )
            return False, self._record_from_row(row)

    def lookup(self, token_hash: str) -> Optional[ProposalTokenRecord]:
        return self._run(self._lookup_async(token_hash))

    async def _lookup_async(self, token_hash: str):
        await self._ensure_table()
        session_maker = self._get_session_maker()
        async with session_maker() as session:
            row = (
                await session.execute(select_proposal_token_by_hash(token_hash))
            ).scalar_one_or_none()
            return self._record_from_row(row) if row is not None else None

    def revoke(self, token_hash: str, revoked_at: datetime) -> bool:
        return self._run(self._revoke_async(token_hash, revoked_at))

    async def _revoke_async(self, token_hash: str, revoked_at: datetime) -> bool:
        from sqlalchemy import update

        from spine_api.models.proposal_tokens import ProposalAccessToken

        await self._ensure_table()
        session_maker = self._get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                update(ProposalAccessToken)
                .where(ProposalAccessToken.token_hash == token_hash)
                .where(ProposalAccessToken.revoked_at.is_(None))
                .values(revoked_at=revoked_at)
            )
            await session.commit()
            return result.rowcount == 1


def _record_from_kwargs(kwargs) -> ProposalTokenRecord:  # pragma: no cover - trivial mapping
    return ProposalTokenRecord(
        token_hash=kwargs["token_hash"],
        lookup_prefix=kwargs["lookup_prefix"],
        format_version=kwargs["format_version"],
        agency_id=kwargs["agency_id"],
        trip_id=kwargs["trip_id"],
        proposal_id=kwargs.get("proposal_id"),
        issued_at=kwargs["issued_at"],
        expires_at=kwargs["expires_at"],
        revoked_at=None,
        consented_by=kwargs["consented_by"],
        consented_at=kwargs["consented_at"],
        purpose=kwargs["purpose"],
    )


def select_proposal_token_by_hash(token_hash: str):
    """Late-bound select so the SQL layer owns its model import path."""
    from sqlalchemy import select

    from spine_api.models.proposal_tokens import ProposalAccessToken

    return select(ProposalAccessToken).where(ProposalAccessToken.token_hash == token_hash)


class ProposalTokenStore:
    """Facade with pluggable backend for public proposal capability tokens."""

    _instance: Optional["ProposalTokenStore"] = None
    _instance_lock = threading.Lock()

    def __init__(self, backend=None):
        self._backend = backend
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ProposalTokenStore":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    backend_name = (
                        os.getenv(PROPOSAL_TOKEN_BACKEND_ENV, "memory").strip().lower()
                    )
                    if backend_name == "sql":
                        cls._instance = cls(backend=SqlProposalTokenBackend())
                    elif backend_name == "auto":
                        database_url = os.getenv("DATABASE_URL", "").strip()
                        cls._instance = cls(
                            backend=SqlProposalTokenBackend() if database_url else None
                        )
                    else:
                        cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Test hook: drop the process singleton so backend selection reruns."""
        with cls._instance_lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # Issue
    # ------------------------------------------------------------------

    def issue(
        self,
        *,
        token: str,
        format_version: str,
        agency_id: str,
        trip_id: str,
        proposal_id: Optional[str] = None,
        ttl_hours: Optional[int] = None,
        consented_by: str,
        purpose: str = "proposal_share",
        issued_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        consented_at: Optional[datetime] = None,
    ) -> Tuple[bool, ProposalTokenRecord]:
        """Register an issued credential. Idempotent on the token hash.

        Re-issuing the exact same token material (deterministic legacy minting)
        replays the stored row — TTL and consent artifact are NOT refreshed, so
        replay cannot silently extend a credential's life. Fresh v3 material
        mints a new row each time (explicitly versioned via ``format_version``).
        """
        if not trip_id:
            raise ValueError("trip_id must be a non-empty string")
        if not agency_id:
            raise ValueError("agency_id must be a non-empty string")
        if not consented_by:
            raise ValueError("consented_by is required: a consent artifact must name the authorizing principal")

        token_hash, lookup_prefix = hash_token(token)
        now = issued_at or datetime.now(timezone.utc)
        resolved_expiry = expires_at or (
            now + timedelta(hours=ttl_hours if ttl_hours is not None else default_ttl_hours())
        )
        return self._backend.issue(
            token_hash=token_hash,
            lookup_prefix=lookup_prefix,
            format_version=format_version,
            agency_id=agency_id,
            trip_id=trip_id,
            proposal_id=proposal_id,
            issued_at=now,
            expires_at=resolved_expiry,
            consented_by=consented_by,
            consented_at=consented_at or now,
            purpose=purpose,
        )

    # ------------------------------------------------------------------
    # Verify / revoke
    # ------------------------------------------------------------------

    def verify(self, token: str) -> Tuple[TokenStatus, Optional[ProposalTokenRecord]]:
        """Ordered credential check: hash match -> TTL -> revocation.

        Returns ``(status, record)``; ``record`` is present only for VALID so
        callers cannot project data for an unusable credential.
        """
        token_hash, _prefix = hash_token(token)
        record = self._backend.lookup(token_hash)
        if record is None:
            return TokenStatus.UNKNOWN, None
        now = datetime.now(timezone.utc)
        if self._as_utc(record.expires_at) <= now:
            return TokenStatus.EXPIRED, None
        if record.revoked_at is not None:
            return TokenStatus.REVOKED, None
        return TokenStatus.VALID, record

    def revoke(self, token: str) -> bool:
        """Durably revoke by hash. Idempotent; False when nothing to revoke."""
        token_hash, _prefix = hash_token(token)
        return self._backend.revoke(token_hash, datetime.now(timezone.utc))

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
