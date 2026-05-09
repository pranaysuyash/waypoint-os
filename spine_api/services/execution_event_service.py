"""Execution event service: durable event ledger for timeline and audit.

Emits events after state transitions. Enforces metadata allowlist.
Timeline reads ONLY from execution_events — never from current row state.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import (
    ExecutionEvent,
    EVENT_CATEGORIES,
    ALLOWED_EVENT_METADATA_KEYS,
    FORBIDDEN_METADATA_PATTERNS,
)

logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    event_type: str
    event_category: str
    subject_type: str
    subject_id: str
    status_from: Optional[str]
    status_to: str
    actor_type: str
    actor_id: Optional[str]
    source: str
    event_metadata: Optional[dict]
    created_at: object  # datetime


@dataclass
class TimelineResult:
    events: list[TimelineEvent]
    summary: dict[str, int]


def _validate_metadata(metadata: Optional[dict]) -> None:
    """Raise ValueError if metadata contains forbidden keys."""
    if not metadata:
        return
    for key in metadata:
        # Check exact forbidden matches
        if key in FORBIDDEN_METADATA_PATTERNS:
            raise ValueError(f"Forbidden metadata key: {key}")
        # Check substring matches for PII patterns
        key_lower = key.lower()
        for pattern in FORBIDDEN_METADATA_PATTERNS:
            if pattern in key_lower:
                raise ValueError(f"Forbidden metadata key: {key}")


async def emit_event(
    db: AsyncSession,
    *,
    agency_id: str,
    trip_id: str,
    subject_type: str,
    subject_id: str,
    event_type: str,
    event_category: str,
    status_from: Optional[str],
    status_to: str,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
    source: str = "agent_action",
    event_metadata: Optional[dict] = None,
) -> ExecutionEvent:
    """Insert an execution event row. Validates metadata allowlist."""
    _validate_metadata(event_metadata)

    event = ExecutionEvent(
        agency_id=agency_id,
        trip_id=trip_id,
        subject_type=subject_type,
        subject_id=subject_id,
        event_type=event_type,
        event_category=event_category,
        status_from=status_from,
        status_to=status_to,
        actor_type=actor_type,
        actor_id=actor_id,
        source=source,
        event_metadata=event_metadata,
    )
    db.add(event)
    await db.flush()

    logger.info(
        "event emitted: type=%s category=%s subject=%s:%s %s->%s actor=%s:%s",
        event_type, event_category, subject_type, subject_id,
        status_from or "null", status_to, actor_type, actor_id or "null",
    )
    return event


def _event_to_timeline(e: ExecutionEvent) -> TimelineEvent:
    return TimelineEvent(
        event_type=e.event_type,
        event_category=e.event_category,
        subject_type=e.subject_type,
        subject_id=e.subject_id,
        status_from=e.status_from,
        status_to=e.status_to,
        actor_type=e.actor_type,
        actor_id=e.actor_id,
        source=e.source,
        event_metadata=e.event_metadata,
        created_at=e.created_at,
    )


async def get_timeline(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    category: Optional[str] = None,
) -> TimelineResult:
    """Read timeline from execution_events, sorted chronologically."""
    q = (
        select(ExecutionEvent)
        .where(
            ExecutionEvent.trip_id == trip_id,
            ExecutionEvent.agency_id == agency_id,
        )
        .order_by(ExecutionEvent.created_at)
    )
    if category:
        q = q.where(ExecutionEvent.event_category == category)

    result = await db.execute(q)
    rows = list(result.scalars().all())

    summary: dict[str, int] = {c: 0 for c in EVENT_CATEGORIES}
    summary["total"] = len(rows)
    for r in rows:
        summary[r.event_category] = summary.get(r.event_category, 0) + 1

    return TimelineResult(
        events=[_event_to_timeline(e) for e in rows],
        summary=summary,
    )
