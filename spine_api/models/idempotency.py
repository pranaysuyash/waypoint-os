"""
spine_api/models/idempotency.py — Durable idempotency key registry model (PT-08).

Backs ``src.agents.idempotency.IdempotencyRegistry`` when
``SPINE_API_IDEMPOTENCY_BACKEND=sql``. A single row per idempotency key:

- Primary key on ``key`` makes cross-worker/cross-replica duplicate acquisition
  impossible: two processes INSERT the same key and exactly one wins; the loser
  gets an integrity violation and replays the holder's state instead.
- Rows are reclaimed (re-INSERTed as PENDING) after ``ttl_seconds`` so FAILED
  retries and stale PENDING locks recover exactly like the in-memory backend.
- Every acquisition has a fresh opaque ``fencing_token``. Terminal writes are
  compare-and-set operations on that token, preventing a slow owner from
  completing a row reclaimed by a newer owner.

Additive-only table; intentionally NOT RLS-protected (idempotency keys are
system-scoped, keyed by opaque operation keys — no tenant data is stored; the
``trip_id`` column is informational for operators, never a lookup path).
"""

from datetime import datetime, timezone
import secrets
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


class IdempotencyKey(Base):
    """One row per reserved idempotency key (PT-08 durable backend)."""

    __tablename__ = "idempotency_keys"

    # "idem:{trip_id}:{action_name}:{payload_hash16}" — see
    # IdempotencyRegistry.generate_key for the canonical format.
    key: Mapped[str] = mapped_column(String(512), primary_key=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="PENDING", index=True
    )
    # One opaque generation per acquisition. It is the compare-and-set fence
    # used by mark_completed/mark_failed; reclaim always replaces it.
    fencing_token: Mapped[str] = mapped_column(
        String(128), nullable=False, default=lambda: secrets.token_urlsafe(32)
    )
    trip_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    response_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=86400)
