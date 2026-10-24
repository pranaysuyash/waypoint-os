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


@router.get("", response_model=WorkItemQueueResponse)
def get_work_item_queue(
    agency_id: str = Depends(get_current_agency_id),
    limit: int = Query(default=50, ge=1, le=200),
) -> WorkItemQueueResponse:
    """Urgency-ranked queue of classified incoming work for this agency.

    Ranking: urgency (high > normal > low), then returning guests, then
    recency. Lifecycle-aware: resolved/dismissed items leave the ranked list;
    counts.by_state and total stay honest log totals (``count_basis``).
    """
    queue = work_intake.ranked_queue(agency_id, limit=limit)
    return WorkItemQueueResponse(
        items=[WorkItemEntry.model_validate(i) for i in queue["items"]],
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
