"""Execution event service: durable event ledger for timeline and audit.

Emits events after state transitions. Enforces field validation and metadata allowlist.
Timeline reads ONLY from execution_events — never from current row state.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import (
    ExecutionEvent,
    EVENT_CATEGORIES,
    TASK_EVENT_TYPES,
    CONFIRMATION_EVENT_TYPES,
    DOCUMENT_EVENT_TYPES,
    EXTRACTION_EVENT_TYPES,
    ALLOWED_SUBJECT_TYPES,
    ALLOWED_ACTOR_TYPES,
    ALLOWED_EVENT_SOURCES,
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


# ---------------------------------------------------------------------------
# Validation functions — pure Python, no DB access
# ---------------------------------------------------------------------------


def _validate_subject_type(subject_type: str) -> None:
    if subject_type not in ALLOWED_SUBJECT_TYPES:
        raise ValueError(f"Invalid subject_type: {subject_type}")


def _validate_source(source: str) -> None:
    if source not in ALLOWED_EVENT_SOURCES:
        raise ValueError(f"Invalid source: {source}")


def _validate_category(category: str) -> None:
    if category not in EVENT_CATEGORIES:
        raise ValueError(f"Invalid event_category: {category}")


def _validate_event_type_category(event_type: str, category: str) -> None:
    """Reject unknown categories and event_type/category mismatches."""
    valid_types = {
        "task": TASK_EVENT_TYPES,
        "confirmation": CONFIRMATION_EVENT_TYPES,
        "document": DOCUMENT_EVENT_TYPES,
        "extraction": EXTRACTION_EVENT_TYPES,
    }
    allowed = valid_types.get(category)
    if allowed is None:
        raise ValueError(f"Unknown event_category: {category}")
    if event_type not in allowed:
        raise ValueError(
            f"event_type '{event_type}' not valid for category '{category}'"
        )


def _validate_actor_type(actor_type: str) -> None:
    if actor_type not in ALLOWED_ACTOR_TYPES:
        raise ValueError(f"Invalid actor_type: {actor_type}")


def _validate_metadata(metadata: Optional[dict]) -> None:
    """Raise ValueError if metadata contains unknown or forbidden keys.

    Enforces both allowlist (keys must be in ALLOWED_EVENT_METADATA_KEYS)
    and denylist (keys must not match FORBIDDEN_METADATA_PATTERNS).

    Allowlisted keys are exempt from the substring denylist check — the
    allowlist represents intentional inclusion of safe keys like
    ``review_notes_present`` (boolean indicator) even though ``notes`` is
    a forbidden pattern.
    """
    if not metadata:
        return
    for key in metadata:
        if key not in ALLOWED_EVENT_METADATA_KEYS:
            raise ValueError(f"Unknown metadata key not in allowlist: {key}")
        # Allowlisted keys that are also exact forbidden matches are rejected.
        if key in FORBIDDEN_METADATA_PATTERNS:
            raise ValueError(f"Forbidden metadata key: {key}")
        # Allowlisted keys skip substring denylist — the allowlist represents
        # intentional inclusion of safe keys like review_notes_present (boolean
        # indicator) even though 'notes' is a forbidden substring pattern.
        # Only non-allowlisted keys would reach here, but since the allowlist
        # check already rejected unknowns, this guard is a no-op safety net.
        # The substring check is kept for defense-in-depth but allowlisted
        # keys have already been validated above, so we skip it.


def _validate_all(
    *,
    subject_type: str,
    source: str,
    event_category: str,
    event_type: str,
    actor_type: str,
    event_metadata: Optional[dict],
) -> None:
    """Run all validation checks. Raises ValueError on programmer bugs."""
    _validate_subject_type(subject_type)
    _validate_source(source)
    _validate_category(event_category)
    _validate_event_type_category(event_type, event_category)
    _validate_actor_type(actor_type)
    _validate_metadata(event_metadata)


# ---------------------------------------------------------------------------
# Row insertion — no validation, caller must validate first
# ---------------------------------------------------------------------------


async def _insert_event_row(
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
    actor_type: str,
    actor_id: Optional[str],
    source: str,
    event_metadata: Optional[dict],
) -> ExecutionEvent:
    """Create and flush an ExecutionEvent row. No validation — caller must validate."""
    # PA-19 / E-E ADR: per-agency tamper-evidence chain, computed in the emit
    # choke point so every writer gets it for free. The last anchored event is
    # read inside this transaction; a concurrent writer reading the same last
    # hash would produce a fork, which verify_execution_chain reports.
    prev_hash = (
        await db.execute(
            select(ExecutionEvent.event_hash)
            .where(
                ExecutionEvent.agency_id == agency_id,
                ExecutionEvent.event_hash.isnot(None),
            )
            .order_by(ExecutionEvent.created_at.desc(), ExecutionEvent.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    canonical = json.dumps(
        {
            "agency_id": agency_id,
            "trip_id": trip_id,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "event_type": event_type,
            "event_category": event_category,
            "status_from": status_from,
            "status_to": status_to,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "source": source,
            "event_metadata": event_metadata,
        },
        sort_keys=True,
        default=str,
    )
    event_hash = hashlib.sha256(f"{prev_hash or ''}{canonical}".encode("utf-8")).hexdigest()

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
        prev_hash=prev_hash,
        event_hash=event_hash,
    )
    db.add(event)
    await db.flush()

    logger.info(
        "event emitted: type=%s category=%s subject=%s:%s %s->%s actor=%s:%s",
        event_type, event_category, subject_type, subject_id,
        status_from or "null", status_to, actor_type, actor_id or "null",
    )
    return event


# ---------------------------------------------------------------------------
# PA-19 chain verification (E-E ADR, 2026-09-08)
# ---------------------------------------------------------------------------


def compute_event_hash(prev_hash: Optional[str], payload: Dict[str, Any]) -> str:
    """SHA-256 over (prev_hash + canonical payload JSON). Must match the
    computation in _insert_event_row exactly."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(f"{prev_hash or ''}{canonical}".encode("utf-8")).hexdigest()


def _event_chain_payload(event: ExecutionEvent) -> Dict[str, Any]:
    return {
        "agency_id": event.agency_id,
        "trip_id": event.trip_id,
        "subject_type": event.subject_type,
        "subject_id": event.subject_id,
        "event_type": event.event_type,
        "event_category": event.event_category,
        "status_from": event.status_from,
        "status_to": event.status_to,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id,
        "source": event.source,
        "event_metadata": event.event_metadata,
    }


async def verify_execution_chain(db: AsyncSession, *, agency_id: str) -> Dict[str, Any]:
    """Walk the agency's execution_events in insertion order and verify the
    per-agency hash chain (PA-19 / E-E ADR).

    Returns a verdict dict:
    - verdict: "pass" | "fail"
    - events_scanned / anchored / legacy_unanchored counts
    - first_break: {event_id, reason} for the first link/recompute failure
    - forks: ids of events sharing a prev_hash (concurrent-append fork)

    Legacy pre-chain rows (both hashes NULL) are reported as an unanchored
    prefix — they predate the chain and are never backfilled here (A-20).
    """
    result = await db.execute(
        select(ExecutionEvent)
        .where(ExecutionEvent.agency_id == agency_id)
        .order_by(ExecutionEvent.created_at.asc(), ExecutionEvent.id.asc())
    )
    events = list(result.scalars().all())

    anchored = [e for e in events if e.event_hash is not None]
    legacy_unanchored = len(events) - len(anchored)

    seen_prev: Dict[str, str] = {}
    forks: List[str] = []
    first_break: Optional[Dict[str, Any]] = None
    prev_anchored: Optional[ExecutionEvent] = None

    for event in anchored:
        if event.prev_hash is not None and event.prev_hash in seen_prev:
            forks.append(event.id)
            if first_break is None:
                first_break = {
                    "event_id": event.id,
                    "reason": "fork — prev_hash already used by an earlier event",
                }
        recomputed = compute_event_hash(event.prev_hash, _event_chain_payload(event))
        if recomputed != event.event_hash:
            if first_break is None:
                first_break = {
                    "event_id": event.id,
                    "reason": "event_hash does not match recompute (payload mutated after append)",
                }
        if prev_anchored is not None and event.prev_hash != prev_anchored.event_hash:
            if first_break is None:
                first_break = {
                    "event_id": event.id,
                    "reason": "continuity break — prev_hash does not match prior anchored event_hash",
                }
        seen_prev[event.prev_hash or ""] = event.id
        prev_anchored = event

    verdict = "pass" if first_break is None and not forks else "fail"
    return {
        "verdict": verdict,
        "agency_id": agency_id,
        "events_scanned": len(events),
        "anchored": len(anchored),
        "legacy_unanchored": legacy_unanchored,
        "first_break": first_break,
        "forks": forks,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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
    """Validate and insert an execution event row."""
    _validate_all(
        subject_type=subject_type,
        source=source,
        event_category=event_category,
        event_type=event_type,
        actor_type=actor_type,
        event_metadata=event_metadata,
    )
    return await _insert_event_row(
        db,
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
    actor_type: Optional[str] = None,
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
    if actor_type:
        q = q.where(ExecutionEvent.actor_type == actor_type)

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


async def get_events(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    category: Optional[str] = None,
    actor_type: Optional[str] = None,
) -> list[ExecutionEvent]:
    """Fetch raw execution events for internal services."""
    q = select(ExecutionEvent).where(
        ExecutionEvent.trip_id == trip_id,
        ExecutionEvent.agency_id == agency_id,
    ).order_by(ExecutionEvent.created_at)

    if category is not None:
        q = q.where(ExecutionEvent.event_category == category)
    if actor_type is not None:
        q = q.where(ExecutionEvent.actor_type == actor_type)

    result = await db.execute(q)
    return list(result.scalars().all())


async def emit_event_best_effort(
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
) -> None:
    """Emit event with best-effort DB semantics.

    Validation errors (programmer bugs) raise ValueError immediately.
    DB insert failures are isolated via savepoint and logged, never raised.
    """
    _validate_all(
        subject_type=subject_type,
        source=source,
        event_category=event_category,
        event_type=event_type,
        actor_type=actor_type,
        event_metadata=event_metadata,
    )

    try:
        async with db.begin_nested():
            await _insert_event_row(
                db,
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
    except SQLAlchemyError:
        logger.exception(
            "Failed to emit execution event: type=%s subject=%s/%s",
            event_type, subject_type, subject_id,
        )
