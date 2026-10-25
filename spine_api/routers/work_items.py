"""
spine_api.routers.work_items — the operator work queue over classified
incoming work (C1 of the Incoming Work Classification Map, 2026-10-24).

One surface over the canonical work-intake store
(spine_api/services/work_intake.py): urgency-ranked incoming items with
per-class counts, duplicate flags (C3), returning-guest annotations (C2),
and the outcome-state lifecycle (map §14: claim / unclaim / dismiss /
resolve — event-sourced on the same append-only log).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency_id, get_current_user
from spine_api.services import work_intake

logger = logging.getLogger("spine_api.work_items")

router = APIRouter(prefix="/api/v1/work-items", tags=["work-items"])


class WorkItemEntry(BaseModel):
    item_id: str
    received_at: str
    door: str
    origin: str = Field(description="demand | supply | operator | system | world")
    intent: str
    authority: str
    urgency: str
    state: str = Field(default="open", description="open | claimed | resolved | dismissed")
    claimed_by: Optional[str] = None
    channel: Optional[str] = None
    trip_id: Optional[str] = None
    run_id: Optional[str] = None
    draft_id: Optional[str] = None
    actor: Optional[str] = None
    identity_known: bool = False
    # identity_key is exposed to operators (queue tooling), but it is a one-way
    # hash — the raw contact is never recoverable from it.
    identity_key: Optional[str] = None
    returning_customer: bool = False
    memory_entity_id: Optional[str] = None
    memory_fact_count: int = 0
    duplicate_of: Optional[str] = None
    money_touch: bool = False
    pii_present: bool = False
    payload_summary: Dict[str, Any] = Field(default_factory=dict)
    # Read-time display projection (work_intake.display_for): the human
    # sentence an operator acts on, composed from the door vocabulary —
    # never stored on the append-only log. The raw classification axes above
    # remain the tooling/debug surface.
    headline: str = Field(default="", description="Operator-facing row title (door display vocabulary)")
    meta: List[str] = Field(
        default_factory=list,
        description="Human context line: channel / bound-entity label / actor.",
    )
    group_count: int = Field(
        default=1,
        description="N identical entity-bound open items collapsed into this row (1 = uncollapsed).",
    )


class WorkItemQueueResponse(BaseModel):
    ok: bool = True
    items: List[WorkItemEntry]
    total: int
    actionable: int = Field(
        default=0,
        description="Open + claimed items (the ranked list); total stays the log total.",
    )
    duplicates_flagged: int
    returning_customers: int
    counts: Dict[str, Dict[str, int]]
    count_basis: str = Field(
        default="work_item_log_total",
        description="Invariant-3 style basis: totals count the append-only work-item log, not a filtered projection.",
    )


class WorkItemActionRequest(BaseModel):
    action: Literal["claim", "unclaim", "dismiss", "resolve"]
    note: Optional[str] = Field(default=None, max_length=200)


class WorkItemActionResponse(BaseModel):
    ok: bool = True
    item_id: str
    previous_state: str
    state: str
    claimed_by: Optional[str] = None
    at: str


def _trip_display_label(trip: Optional[Dict[str, Any]]) -> Optional[str]:
    """Human label for the bound entity, via the canonical field resolver
    (spine_api/services/inbox_projection.py::resolve_trip_field — the single
    source of truth for trip field resolution). Tombstoned/unknown parts are
    skipped; returns None when nothing human remains (caller falls back to
    keeping the raw id off the prose line). Never raises."""
    if not isinstance(trip, dict):
        return None
    try:
        from spine_api.services.inbox_projection import resolve_trip_field

        parts: List[str] = []
        for field in ("destination", "date_window"):
            value = resolve_trip_field(trip, field)
            text = str(value).strip() if value is not None else ""
            if text and text.lower() not in {"unknown", "tbd"} and text not in parts:
                parts.append(text)
        return " · ".join(parts) or None
    except Exception as exc:  # display label is an annotation, never a blocker
        logger.debug("trip display label skipped: %s", exc)
        return None


async def _resolve_actor_names(user_ids: List[str]) -> Dict[str, str]:
    """User-UUID → display-name lookup (name, falling back to email), one
    primary-key get per distinct actor on the page (bounded by the page
    size). Empty map when nothing resolves — callers degrade to
    ACTOR_DISPLAY/raw. Unknown UUIDs simply resolve to nothing."""
    if not user_ids:
        return {}
    from spine_api.core.database import async_session_maker
    from spine_api.models.tenant import User

    resolved: Dict[str, str] = {}
    async with async_session_maker() as session:
        for uid in user_ids:
            user = await session.get(User, uid)
            if user is not None and (user.name or user.email):
                resolved[uid] = user.name or user.email
    return resolved


def _actor_display_labels(items: List[Dict[str, Any]]) -> Dict[str, str]:
    """One batched user lookup per queue read for every user-UUID actor on
    the page. Best-effort: a failed lookup degrades to ACTOR_DISPLAY/raw,
    never a failed queue read."""
    import asyncio
    import re as _re

    uuid_re = _re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        _re.IGNORECASE,
    )
    user_ids = sorted(
        {
            str(item.get("actor"))
            for item in items
            if item.get("actor") and uuid_re.match(str(item.get("actor")))
        }
    )
    if not user_ids:
        return {}
    try:
        return asyncio.run(_resolve_actor_names(user_ids))
    except Exception as exc:
        logger.debug("actor name lookup skipped: %s", exc)
        return {}


def _annotate_display(
    items: List[Dict[str, Any]], agency_id: str
) -> List[Dict[str, Any]]:
    """Compose headline/meta per item with per-request memoized trip-label
    resolution (at most one TripStore read per distinct bound trip on the
    page) and one batched actor-name lookup per read. Best-effort: a failed
    entity lookup degrades to no label, never a failed queue read."""
    labels: Dict[str, Optional[str]] = {}
    actor_names = _actor_display_labels(items)
    out: List[Dict[str, Any]] = []
    for item in items:
        trip_id = item.get("trip_id")
        trip_label: Optional[str] = None
        if trip_id:
            if trip_id not in labels:
                try:
                    from spine_api.persistence import TripStore

                    labels[trip_id] = _trip_display_label(
                        TripStore.get_trip_for_agency(str(trip_id), agency_id)
                    )
                except Exception as exc:
                    logger.debug("trip label lookup skipped for %s: %s", trip_id, exc)
                    labels[trip_id] = None
            trip_label = labels[trip_id]
        actor_label = actor_names.get(str(item.get("actor"))) if item.get("actor") else None
        annotated = dict(item)
        annotated.update(
            work_intake.display_for(item, trip_label=trip_label, actor_label=actor_label)
        )
        out.append(annotated)
    return out


@router.get("", response_model=WorkItemQueueResponse)
def get_work_item_queue(
    agency_id: str = Depends(get_current_agency_id),
    limit: int = Query(default=50, ge=1, le=200),
    include_done: bool = Query(
        default=False,
        description="History reader: append resolved/dismissed items after the actionable list.",
    ),
) -> WorkItemQueueResponse:
    """Urgency-ranked queue of classified incoming work for this agency.

    Ranking: urgency (high > normal > low), then returning guests, then
    recency. Lifecycle-aware: resolved/dismissed items leave the ranked list;
    counts.by_state and total stay honest log totals (``count_basis``).
    ``include_done=true`` appends done items (state-annotated) after the
    actionable list — the history view over recorded lifecycle events.
    """
    queue = work_intake.ranked_queue(agency_id, limit=limit, include_done=include_done)
    return WorkItemQueueResponse(
        items=[WorkItemEntry.model_validate(i) for i in _annotate_display(queue["items"], agency_id)],
        total=queue["total"],
        actionable=queue["actionable"],
        duplicates_flagged=queue["duplicates_flagged"],
        returning_customers=queue["returning_customers"],
        counts=queue["counts"],
        count_basis=queue["count_basis"],
    )


@router.patch("/{item_id}", response_model=WorkItemActionResponse)
def act_on_work_item(
    item_id: str,
    body: WorkItemActionRequest,
    agency_id: str = Depends(get_current_agency_id),
    user: Any = Depends(get_current_user),
) -> WorkItemActionResponse:
    """Apply one lifecycle transition (claim / unclaim / dismiss / resolve) to
    a work item on THIS agency's queue. Transitions append as lifecycle events
    to the same append-only log (event-sourced; the trail is the audit trail).

    404 — item does not exist on this agency's queue (tenant isolation is
    inherent: each agency reads/writes only its own log).
    409 — transition invalid for the item's current state (resolved/dismissed
    are terminal; see work_intake._VALID_TRANSITIONS).
    """
    actor = getattr(user, "email", None) or getattr(user, "id", None) or "operator"
    try:
        result = work_intake.record_lifecycle(
            agency_id,
            item_id,
            body.action,
            actor=str(actor),
            note=body.note,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Work item not found: {item_id}")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return WorkItemActionResponse.model_validate(result)
