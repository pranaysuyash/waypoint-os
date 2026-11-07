"""Agency-facing API-key auth (R2-A tranche, 2026-11-04).

External consumers (agency MCP/agent integrations) authenticate with a
per-agency API key over ``X-API-Key``. Keys are stored HASHED (sha256) — the
plaintext is shown exactly once at creation and never recoverable.

Security posture (recorded for the security review):
- Lookup is by key hash only; no tenant context exists before the key
  resolves, so the ``agency_api_keys`` table is deliberately NOT under FORCE
  RLS (FORCE RLS would need a tenant GUC that does not exist pre-auth). The
  key hash is the capability credential; possession IS the authorization to
  resolve the owning agency.
- Key format ``wpt_live_<32 hex>``; constant-time hash comparison; revoked
  keys fail closed.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base, async_session_maker, engine

_API_KEY_PREFIX = "wpt_live_"


class AgencyApiKey(Base):
    """Hashed agency API key (R2-A). See module docstring for the RLS posture."""

    __tablename__ = "agency_api_keys"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True)
    agency_id: Mapped[str] = mapped_column(VARCHAR(36), index=True, nullable=False)
    key_hash: Mapped[str] = mapped_column(VARCHAR(64), unique=True, index=True, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(VARCHAR(120), nullable=True)
    created_at: Mapped[str] = mapped_column(VARCHAR(40), nullable=False)
    revoked_at: Mapped[Optional[str]] = mapped_column(VARCHAR(40), nullable=True)


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256((raw_key or "").strip().encode("utf-8")).hexdigest()


def generate_agency_api_key() -> tuple[str, str, str]:
    """Create a new key. Returns (raw_plaintext, key_hash, key_id).

    The plaintext is returned exactly once — it is never stored."""
    raw = _API_KEY_PREFIX + secrets.token_hex(16)
    key_id = secrets.token_hex(12)
    return raw, hash_api_key(raw), key_id


_ensure_attempted = False


async def _ensure_api_keys_table() -> None:
    """Create the key table on first use (house ensure-table pattern)."""
    global _ensure_attempted
    if _ensure_attempted:
        return
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS agency_api_keys (
                id VARCHAR(36) PRIMARY KEY,
                agency_id VARCHAR(36) NOT NULL,
                key_hash VARCHAR(64) NOT NULL UNIQUE,
                label VARCHAR(120),
                created_at VARCHAR(40) NOT NULL,
                revoked_at VARCHAR(40)
            )
            """
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_agency_api_keys_agency_id ON agency_api_keys (agency_id)"
        ))
    _ensure_attempted = True


async def resolve_agency_for_key(raw_key: str) -> Optional[str]:
    """Resolve the owning agency_id for a presented key, or None."""
    if not raw_key:
        return None
    await _ensure_api_keys_table()
    key_hash = hash_api_key(raw_key)
    async with async_session_maker() as session:
        row = (
            await session.execute(
                select(AgencyApiKey).where(
                    AgencyApiKey.key_hash == key_hash,
                    AgencyApiKey.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return str(row.agency_id)


async def get_agency_api_key(request: Request) -> str:
    """FastAPI dependency: X-API-Key header → agency_id (fail-closed 401)."""
    raw = request.headers.get("X-API-Key", "").strip()
    if not raw:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    agency_id = await resolve_agency_for_key(raw)
    if not agency_id:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    return agency_id


async def issue_agency_api_key(agency_id: str, label: str = "") -> dict:
    """Mint a key for an agency (JWT-authenticated operator action)."""
    await _ensure_api_keys_table()
    raw, key_hash, key_id = generate_agency_api_key()
    async with async_session_maker() as session:
        session.add(
            AgencyApiKey(
                id=key_id,
                agency_id=agency_id,
                key_hash=key_hash,
                label=(label or "")[:120],
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        await session.commit()
    return {"key_id": key_id, "api_key": raw}


async def revoke_agency_api_key(agency_id: str, key_id: str) -> bool:
    await _ensure_api_keys_table()
    async with async_session_maker() as session:
        row = (
            await session.execute(
                select(AgencyApiKey).where(
                    AgencyApiKey.id == key_id,
                    AgencyApiKey.agency_id == agency_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return False
        row.revoked_at = datetime.now(timezone.utc).isoformat()
        await session.commit()
        return True
