"""
Booking collection token service — generate, validate, revoke.

Follows the PasswordResetToken pattern from auth_service.py:
- Plain token via secrets.token_urlsafe(32)
- SHA-256 hash stored in DB, plain token never persisted
- Single-use: marked as used after customer submission
- Revocable by agent at any time
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import BookingCollectionToken
from spine_api.services.private_fields import encrypt_field

logger = logging.getLogger(__name__)

DEFAULT_TTL_HOURS = int(os.getenv("BOOKING_COLLECTION_TOKEN_TTL_HOURS", "168"))


async def generate_token(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    created_by: str,
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> tuple[str, BookingCollectionToken]:
    """Generate a new collection token. Returns (plain_token, token_record).

    Revokes any existing active tokens for the same trip first.
    """
    # Revoke existing active tokens for this trip
    await db.execute(
        BookingCollectionToken.__table__.update()
        .where(
            BookingCollectionToken.trip_id == trip_id,
            BookingCollectionToken.status == "active",
        )
        .values(status="revoked", revoked_at=datetime.now(timezone.utc))
    )

    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()

    record = BookingCollectionToken(
        trip_id=trip_id,
        agency_id=agency_id,
        token_hash=token_hash,
        plain_token_encrypted=encrypt_field(plain_token),
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        created_by=created_by,
    )
    db.add(record)
    # Refresh BEFORE commit: commit ends the transaction and releases the
    # connection, and a re-checkout (NullPool, pool recycle, overflow churn)
    # arrives without the RLS session context — under FORCE RLS the refresh
    # then finds nothing and raises InvalidRequestError.
    await db.flush()
    await db.refresh(record)
    await db.commit()

    logger.info("Collection token generated: trip=%s token_id=%s", trip_id, record.id)
    return plain_token, record


async def validate_token(
    db: AsyncSession,
    plain_token: str,
) -> Optional[BookingCollectionToken]:
    """Look up a token by plain value. Returns None if invalid/expired/revoked/used.

    Returns the record only if active and not expired. Marks expired tokens.
    """
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()

    result = await db.execute(
        select(BookingCollectionToken).where(
            BookingCollectionToken.token_hash == token_hash,
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        return None

    if record.status != "active":
        return None

    if record.expires_at < datetime.now(timezone.utc):
        record.status = "expired"
        await db.commit()
        return None

    return record


async def get_active_token_for_trip(
    db: AsyncSession,
    trip_id: str,
) -> Optional[BookingCollectionToken]:
    """Get the active token for a trip, if any."""
    result = await db.execute(
        select(BookingCollectionToken).where(
            BookingCollectionToken.trip_id == trip_id,
            BookingCollectionToken.status == "active",
        )
    )
    record = result.scalar_one_or_none()

    if record and record.expires_at < datetime.now(timezone.utc):
        record.status = "expired"
        await db.commit()
        return None

    return record


async def revoke_token(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
) -> bool:
    """Revoke the active token for a trip. Returns True if revoked."""
    result = await db.execute(
        select(BookingCollectionToken).where(
            BookingCollectionToken.trip_id == trip_id,
            BookingCollectionToken.agency_id == agency_id,
            BookingCollectionToken.status == "active",
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        return False

    record.status = "revoked"
    record.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("Collection token revoked: trip=%s token_id=%s", trip_id, record.id)
    return True


async def mark_token_used(
    db: AsyncSession,
    token_id: str,
) -> bool:
    """Mark a token as used after customer submission — atomically (PA-16).

    The previous implementation was SELECT-then-write: two concurrent
    submissions could both read ``status='active'`` and both record usage
    (TOCTOU). Consumption is now a single conditional UPDATE whose WHERE
    clause re-checks ``status='active'`` at write time, so exactly one
    concurrent consumer can win (rowcount decides).

    Returns True when this call consumed the token. Raises HTTPException(410,
    "invalid") when rowcount is 0 — the same rejection the validate path
    produces for an already-used/invalid token, so the public submit endpoint
    rejects a lost concurrent race exactly like an invalid token.

    S2 note: the double-consume race is evidenced with a sequential
    double-call in tests/test_collection_token_cas.py (second call hits the
    CAS guard and raises); true simultaneous execution is decided by the same
    rowcount predicate in the database.
    """
    from fastapi import HTTPException  # local import keeps service-layer deps lazy

    result = await db.execute(
        BookingCollectionToken.__table__.update()
        .where(
            BookingCollectionToken.id == token_id,
            BookingCollectionToken.status == "active",
        )
        .values(status="used", used_at=datetime.now(timezone.utc))
    )
    await db.commit()

    if result.rowcount == 0:
        logger.warning(
            "Collection token consume lost CAS race (already used/revoked/expired): "
            "token_id=%s",
            token_id,
        )
        raise HTTPException(status_code=410, detail="invalid")

    logger.info("Collection token used: token_id=%s", token_id)
    return True
