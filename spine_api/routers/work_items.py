"""
spine_api.routers.work_items — the operator work queue over classified
incoming work (C1 of the Incoming Work Classification Map, 2026-10-24).

One read surface over the canonical work-intake store
(spine_api/services/work_intake.py): urgency-ranked incoming items with
per-class counts, duplicate flags (C3), and returning-guest annotations (C2).
This is the seed of the unified operator queue (map §5 E3): W4 system-generated
work and further doors join the same store as they get wired.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency_id
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
    duplicates_flagged: int
    returning_customers: int
    counts: Dict[str, Dict[str, int]]
    count_basis: str = Field(
        default="work_item_log_total",
        description="Invariant-3 style basis: totals count the append-only work-item log, not a filtered projection.",
    )


@router.get("", response_model=WorkItemQueueResponse)
def get_work_item_queue(
    agency_id: str = Depends(get_current_agency_id),
    limit: int = Query(default=50, ge=1, le=200),
) -> WorkItemQueueResponse:
    """Urgency-ranked queue of classified incoming work for this agency.

    Ranking: urgency (high > normal > low), then returning guests, then
    recency. Counts are honest log totals (``count_basis`` carries the basis).
    """
    queue = work_intake.ranked_queue(agency_id, limit=limit)
    return WorkItemQueueResponse(
        items=[WorkItemEntry.model_validate(i) for i in queue["items"]],
        total=queue["total"],
        duplicates_flagged=queue["duplicates_flagged"],
        returning_customers=queue["returning_customers"],
        counts=queue["counts"],
        count_basis=queue["count_basis"],
    )
