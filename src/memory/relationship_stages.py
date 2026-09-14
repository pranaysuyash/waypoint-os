"""
src/memory/relationship_stages.py — Customer Relationship-Axis Lifecycle.

Ratified under the Extraction-Realignment Blueprint Addendum 8 ("Ratified
answer to 'how many'") with the PER-0369 Customer Success Architect seat
ruling: the relationship lifecycle is a SEPARATE machine from the 12-state
trip-execution lifecycle and carries exactly 6 coarse stages:

    PROSPECT -> BOOKED_ACTIVE -> POST_TRIP -> REPEAT_CLIENT / DORMANT / LOST

Design rulings encoded here:

- **Hybrid persistence**: persist the coarse stage + ``stage_entered_at``;
  derived signals are computed, never persisted as stages (GHOST_RISK,
  churn_risk, window_shopper etc. are scores, NOT stages).
- **Trip-machine event hooks drive transitions**: commit -> BOOKED_ACTIVE,
  trip completion -> POST_TRIP, repeat commit -> REPEAT_CLIENT.
- **Time decay drives POST_TRIP -> DORMANT** via a configurable decay
  function — this is deliberately NOT a strict adjacency machine: stages are
  re-enterable and time-driven, so transitions are guarded by invariants,
  not an adjacency table.
- **DORMANT never auto-churns** — churn (LOST) is signal-based, not
  clock-based.
- **LOST is terminal at trip level, soft/re-enterable at relationship
  level**: ``win_back`` revives LOST/DORMANT records to PROSPECT.
- BOOKED_ACTIVE / REPEAT_CLIENT carry state invariants (validated, not
  implied by path): REPEAT_CLIENT requires ``repeat_trip_count >= 1``;
  BOOKED_ACTIVE requires >= 1 non-terminal trip when trip context is
  provided.

Integration wiring (trip-gate event hooks, decay job, stage persistence) is a
LATER slice per the blueprint. This module is self-contained and stdlib-only
by design: relationship state is a memory/customer-side concern and must not
depend on ``spine_api``.

Every mutating call returns ``(record, audit)`` where ``record`` is a NEW
``RelationshipRecord`` (inputs are never mutated) and ``audit`` is
``None`` when nothing changed, or a dict ``{"from", "to", "at", "trigger"}``
with JSON-serializable values when the record mutated.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "DEFAULT_DORMANT_DAYS",
    "DEFAULT_RETENTION_WINDOW_DAYS",
    "RelationshipStage",
    "TripEvent",
    "RelationshipRecord",
    "validate_relationship_record",
    "apply_trip_event",
    "apply_decay",
    "derived_signal",
]

DEFAULT_DORMANT_DAYS = 90
DEFAULT_RETENTION_WINDOW_DAYS = 90


def _utcnow() -> datetime:
    """Current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC (naive input assumed UTC)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class RelationshipStage(str, enum.Enum):
    """The 6 ratified relationship stages (PER-0369, Addendum 8)."""

    PROSPECT = "prospect"
    BOOKED_ACTIVE = "booked_active"
    POST_TRIP = "post_trip"
    REPEAT_CLIENT = "repeat_client"
    DORMANT = "dormant"
    LOST = "lost"


class TripEvent(str, enum.Enum):
    """Trip-machine events that drive relationship-stage transitions."""

    TRIP_COMMITTED = "trip_committed"
    TRIP_COMPLETED = "trip_completed"
    DEAL_LOST = "deal_lost"
    WIN_BACK = "win_back"


@dataclass(slots=True)
class RelationshipRecord:
    """Persisted coarse relationship state for one customer.

    ``stage_entered_at`` records when the current stage was entered (audit +
    decay anchoring for stages entered by events). ``last_trip_completed_at``
    anchors time-driven decay and the retention-window derived signal.
    """

    customer_id: str
    stage: RelationshipStage = RelationshipStage.PROSPECT
    stage_entered_at: datetime = field(default_factory=_utcnow)
    repeat_trip_count: int = 0
    last_trip_completed_at: Optional[datetime] = None
    loss_reason: Optional[str] = None


def validate_relationship_record(
    record: RelationshipRecord,
    active_trips: Optional[int] = None,
) -> None:
    """Validate state invariants; raise ``ValueError`` on violation.

    Invariants (validated, NOT implied by transition path):

    - ``repeat_trip_count`` may never be negative.
    - REPEAT_CLIENT requires ``repeat_trip_count >= 1``.
    - BOOKED_ACTIVE requires at least 1 non-terminal trip — enforced only
      when trip context is provided via ``active_trips`` (the relationship
      record does not own trip state; callers with trip-machine context may
      assert it).
    """
    if not isinstance(record.stage, RelationshipStage):
        raise ValueError(
            f"record.stage must be a RelationshipStage, got {record.stage!r}"
        )
    if record.repeat_trip_count < 0:
        raise ValueError(
            f"repeat_trip_count must be >= 0, got {record.repeat_trip_count}"
        )
    if record.stage is RelationshipStage.REPEAT_CLIENT and record.repeat_trip_count < 1:
        raise ValueError(
            "Invariant violation: REPEAT_CLIENT requires repeat_trip_count >= 1 "
            f"(customer {record.customer_id} has {record.repeat_trip_count})"
        )
    if (
        active_trips is not None
        and record.stage is RelationshipStage.BOOKED_ACTIVE
        and active_trips < 1
    ):
        raise ValueError(
            "Invariant violation: BOOKED_ACTIVE requires at least 1 non-terminal "
            f"trip (customer {record.customer_id} has {active_trips})"
        )


def _transition(
    record: RelationshipRecord,
    to_stage: RelationshipStage,
    at: datetime,
    trigger: str,
    **mutations: Any,
) -> Tuple[RelationshipRecord, Dict[str, Any]]:
    """Build the post-transition record and its audit dict."""
    new_record = replace(
        record, stage=to_stage, stage_entered_at=at, **mutations
    )
    audit = {
        "from": record.stage.value,
        "to": to_stage.value,
        "at": at.isoformat(),
        "trigger": trigger,
    }
    return new_record, audit


def apply_trip_event(
    record: RelationshipRecord,
    event: "TripEvent | str",
    **context: Any,
) -> Tuple[RelationshipRecord, Optional[Dict[str, Any]]]:
    """Apply a trip-machine event to a relationship record.

    Events (per ratified semantics):

    - ``trip_committed`` -> BOOKED_ACTIVE; if the record shows a prior
      completed trip -> REPEAT_CLIENT and ``repeat_trip_count`` increments.
      Clear any stale ``loss_reason`` (a commit implies engagement).
    - ``trip_completed`` -> POST_TRIP; sets ``last_trip_completed_at``.
    - ``deal_lost`` -> LOST with ``loss_reason``; only legal from PROSPECT
      (deal loss is a prospect-stage event; LOST is soft at the relationship
      level and re-enterable via ``win_back``).
    - ``win_back`` -> PROSPECT; only legal from LOST/DORMANT; clears
      ``loss_reason``. History (``last_trip_completed_at``,
      ``repeat_trip_count``) is preserved — a revived customer who rebooks is
      a repeat client, which is correct real-world behavior.

    Context keys: ``at`` (event datetime, default now), ``loss_reason``,
    ``active_trips`` (optional non-terminal trip count for invariant
    validation when trip context is available).

    Returns ``(record, audit)``; ``audit`` is ``None`` when the event
    produced no mutation (no-op / duplicate / illegal source stage).
    """
    evt = event if isinstance(event, TripEvent) else TripEvent(str(event))
    at = _as_utc(context.get("at") or _utcnow())
    active_trips = context.get("active_trips")

    if evt is TripEvent.TRIP_COMMITTED:
        is_repeat = (
            record.last_trip_completed_at is not None
            or record.repeat_trip_count >= 1
        )
        if is_repeat:
            target = RelationshipStage.REPEAT_CLIENT
            new_count = record.repeat_trip_count + 1
        else:
            target = RelationshipStage.BOOKED_ACTIVE
            new_count = record.repeat_trip_count
        if record.stage is target and record.repeat_trip_count == new_count:
            return record, None
        new_record, audit = _transition(
            record,
            target,
            at,
            evt.value,
            repeat_trip_count=new_count,
            loss_reason=None,
        )
    elif evt is TripEvent.TRIP_COMPLETED:
        if record.stage is RelationshipStage.POST_TRIP and (
            record.last_trip_completed_at == at
        ):
            return record, None
        new_record, audit = _transition(
            record,
            RelationshipStage.POST_TRIP,
            at,
            evt.value,
            last_trip_completed_at=at,
        )
    elif evt is TripEvent.DEAL_LOST:
        if record.stage is not RelationshipStage.PROSPECT:
            return record, None
        new_record, audit = _transition(
            record,
            RelationshipStage.LOST,
            at,
            evt.value,
            loss_reason=context.get("loss_reason"),
        )
    elif evt is TripEvent.WIN_BACK:
        if record.stage not in (
            RelationshipStage.LOST,
            RelationshipStage.DORMANT,
        ):
            return record, None
        new_record, audit = _transition(
            record,
            RelationshipStage.PROSPECT,
            at,
            evt.value,
            loss_reason=None,
        )
    else:  # pragma: no cover - enum exhaustiveness guard
        raise ValueError(f"Unsupported trip event: {event!r}")

    validate_relationship_record(new_record, active_trips=active_trips)
    return new_record, audit


def apply_decay(
    record: RelationshipRecord,
    now: datetime,
    dormant_days: int = DEFAULT_DORMANT_DAYS,
) -> Tuple[RelationshipRecord, Optional[Dict[str, Any]]]:
    """Time-driven decay: POST_TRIP -> DORMANT after ``dormant_days``.

    Decay anchors on ``last_trip_completed_at`` with no subsequent trip (a
    subsequent commit would have already moved the record out of POST_TRIP).
    DORMANT stays DORMANT forever — churn (LOST) is signal-based, not
    clock-based, and is never applied here.

    Returns ``(record, audit)``; ``audit`` is ``None`` when the record is
    unchanged (non-POST_TRIP stage, inside the window, or missing anchor).
    """
    now_dt = _as_utc(now)
    if record.stage is not RelationshipStage.POST_TRIP:
        return record, None
    if record.last_trip_completed_at is None:
        return record, None
    elapsed_days = (
        now_dt - _as_utc(record.last_trip_completed_at)
    ).total_seconds() / 86400.0
    if elapsed_days < dormant_days:
        return record, None
    return _transition(record, RelationshipStage.DORMANT, now_dt, "time_decay")


def derived_signal(
    record: RelationshipRecord,
    now: Optional[datetime] = None,
    retention_window_days: int = DEFAULT_RETENTION_WINDOW_DAYS,
) -> Dict[str, bool]:
    """Compute derived signals from the record. Signals are NOT stages.

    ``retention_window_active`` is True while the customer sits inside the
    post-trip retention window (``last_trip_completed_at`` + window days),
    the standard post-trip outreach window. A customer with no completed
    trip has no active retention window.
    """
    now_dt = _as_utc(now or _utcnow())
    if record.last_trip_completed_at is None:
        return {"retention_window_active": False}
    elapsed_days = (
        now_dt - _as_utc(record.last_trip_completed_at)
    ).total_seconds() / 86400.0
    return {
        "retention_window_active": elapsed_days <= retention_window_days
    }
