"""Agentic evaluation service bridge between execution events and reusable eval reducers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from spine_api import persistence
from spine_api.services import execution_event_service
from src.evals.agentic_feedback import aggregate_eval_records


async def get_trip_agentic_eval_summary(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    *,
    workflow: str | None = None,
    min_occurrences: int = 3,
    window_minutes: int = 24 * 60,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Return trip-scoped eval aggregates for the requested workflow."""
    events = await execution_event_service.get_events(
        db,
        trip_id=trip_id,
        agency_id=agency_id,
        category=workflow,
    )
    review_events = persistence.AuditStore.get_events_for_trip(trip_id)
    return aggregate_eval_records(
        events,
        min_occurrences=min_occurrences,
        window_minutes=window_minutes,
        reference_time=reference_time,
        review_events=review_events,
    )
