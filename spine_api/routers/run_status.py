"""
Run status router — async pipeline status/read endpoints.

This module extracts read-only /runs* routes from server.py while preserving:
- exact route paths
- exact handler names
- endpoint-level agency scoping via Depends(get_current_agency)
- response models and error semantics
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from spine_api.contract import RunStatusResponse
from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.run_events import get_run_events
from spine_api.run_ledger import RunLedger

router = APIRouter()


@router.get("/runs")
def list_runs(
    trip_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50,
    agency: Agency = Depends(get_current_agency),
):
    """
    List run records, newest first.
    Optionally filter by trip_id and/or state (queued|running|completed|failed|blocked).
    """
    runs = RunLedger.list_runs(trip_id=trip_id, state=state, limit=500)
    agency_runs = [r for r in runs if r.get("agency_id") == agency.id][:limit]
    return {"items": agency_runs, "total": len(agency_runs)}


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
def get_run_status(
    run_id: str,
    agency: Agency = Depends(get_current_agency),
) -> RunStatusResponse:
    """
    Full run status including metadata and latest checkpointed steps.
    Returns 404 if the run_id is not found in the ledger.
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    if meta.get("state") in ("queued", "running"):
        RunLedger.timeout_stale_runs(max_age_seconds=300)

    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    steps = RunLedger.get_all_steps(run_id)
    events = get_run_events(run_id)

    decision_data = None
    blocked_result_data = None
    if "decision" in steps:
        decision_data = steps["decision"].get("data")
    elif "blocked_result" in steps:
        blocked_result_data = steps["blocked_result"].get("data") or {}
        decision_data = blocked_result_data.get("decision")

    decision_state = None
    follow_up_questions: list[dict[str, Any]] = []
    hard_blockers: list[str] = []
    soft_blockers: list[str] = []
    if isinstance(decision_data, dict):
        decision_state = decision_data.get("decision_state")
        follow_up_questions = decision_data.get("follow_up_questions") or []
        hard_blockers = decision_data.get("hard_blockers") or []
        soft_blockers = decision_data.get("soft_blockers") or []

    # Extract validation and packet from blocked_result or individual steps
    validation_data = None
    packet_data = None
    if blocked_result_data:
        validation_data = blocked_result_data.get("validation")
        packet_data = blocked_result_data.get("packet")
    if not validation_data and "validation" in steps:
        validation_data = steps["validation"].get("data")
    if not packet_data and "packet" in steps:
        packet_data = steps["packet"].get("data")

    return RunStatusResponse(
        **meta,
        steps_completed=list(steps.keys()),
        events=events,
        decision_state=decision_state,
        follow_up_questions=follow_up_questions,
        hard_blockers=hard_blockers,
        soft_blockers=soft_blockers,
        validation=validation_data,
        packet=packet_data,
    )


@router.get("/runs/{run_id}/steps/{step_name}")
def get_run_step(
    run_id: str,
    step_name: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Return the full checkpointed output for a single pipeline step.
    Returns 404 if the step has not been checkpointed yet.
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    step = RunLedger.get_step(run_id, step_name)
    if step is None:
        raise HTTPException(
            status_code=404,
            detail=f"Step '{step_name}' not yet checkpointed for run {run_id}",
        )
    return step


@router.get("/runs/{run_id}/events")
def get_run_event_stream(
    run_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Return the append-only event log for a run in chronological order.
    Returns empty list if the run_id is unknown (no events written yet).
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    events = get_run_events(run_id)
    return {"run_id": run_id, "events": events, "total": len(events)}
