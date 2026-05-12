"""Trip lifecycle helpers shared by server shell and lifecycle routers."""

from __future__ import annotations

import threading
import uuid
from typing import Any, Callable, Dict, Optional

from spine_api.run_ledger import RunLedger

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore
TripStore = persistence.TripStore

VALID_STAGES = {"discovery", "shortlist", "proposal", "booking"}

REASSESS_EDIT_TRIGGER_FIELDS = {
    "origin",
    "destination",
    "budget",
    "party_composition",
    "pace_preference",
    "date_year_confidence",
    "lead_source",
    "activity_provenance",
    "trip_priorities",
    "date_flexibility",
    "follow_up_due_date",
    "owner_note",
    "raw_note",
    "structured_json",
    "itinerary_text",
}


def build_reassessment_request_from_trip(
    trip: Dict[str, Any],
    *,
    stage_override: Optional[str] = None,
    operating_mode_override: Optional[str] = None,
    strict_leakage_override: Optional[bool] = None,
) -> dict[str, Any]:
    raw_input = trip.get("raw_input") if isinstance(trip.get("raw_input"), dict) else {}
    submission = raw_input.get("submission") if isinstance(raw_input.get("submission"), dict) else {}
    extracted = trip.get("extracted") if isinstance(trip.get("extracted"), dict) else {}

    request_dict: dict[str, Any] = {
        "raw_note": submission.get("raw_note"),
        "owner_note": submission.get("owner_note"),
        "structured_json": submission.get("structured_json"),
        "itinerary_text": submission.get("itinerary_text"),
        "retention_consent": bool(raw_input.get("retention_consent", False)),
        "stage": stage_override or trip.get("stage") or raw_input.get("stage") or "discovery",
        "operating_mode": operating_mode_override or raw_input.get("operating_mode") or "normal_intake",
        "strict_leakage": bool(strict_leakage_override if strict_leakage_override is not None else raw_input.get("strict_leakage", False)),
        "scenario_id": raw_input.get("fixture_id"),
        "follow_up_due_date": trip.get("follow_up_due_date"),
        "pace_preference": trip.get("pace_preference"),
        "lead_source": trip.get("lead_source"),
        "activity_provenance": trip.get("activity_provenance"),
        "date_year_confidence": trip.get("date_year_confidence"),
    }

    if not any(request_dict.get(k) for k in ("raw_note", "owner_note", "structured_json", "itinerary_text")):
        request_dict["structured_json"] = {"extracted_snapshot": extracted}

    return request_dict


def queue_trip_reassessment(
    trip: Dict[str, Any],
    *,
    agency_id: str,
    user_id: str,
    request_dict: dict[str, Any],
    trigger: str,
    execute_pipeline_fn: Callable[..., None],
    reason: Optional[str] = None,
) -> str:
    run_id = str(uuid.uuid4())
    RunLedger.create(
        run_id=run_id,
        trip_id=trip.get("id"),
        stage=request_dict.get("stage", trip.get("stage") or "discovery"),
        operating_mode=request_dict.get("operating_mode", "normal_intake"),
        agency_id=agency_id,
        draft_id=None,
    )
    thread = threading.Thread(
        target=execute_pipeline_fn,
        args=(run_id, request_dict, agency_id, user_id, trip.get("id"), "trip_reassessed", trip.get("status")),
        daemon=True,
        name=f"reassess-{run_id[:8]}",
    )
    thread.start()

    AuditStore.log_event(
        "trip_reassess_queued",
        user_id,
        {
            "trip_id": trip.get("id"),
            "run_id": run_id,
            "trigger": trigger,
            "reason": reason,
            "stage": request_dict.get("stage"),
            "operating_mode": request_dict.get("operating_mode"),
        },
    )
    return run_id


def transition_trip_stage(
    trip_id: str,
    *,
    agency_id: str,
    target_stage: str,
    reason: Optional[str] = None,
    expected_current_stage: Optional[str] = None,
) -> dict[str, Any]:
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency_id:
        raise KeyError("Trip not found")

    if target_stage not in VALID_STAGES:
        raise ValueError(f"Invalid target_stage '{target_stage}'. Must be one of {sorted(VALID_STAGES)}")

    current_stage = trip.get("stage", "discovery")
    if expected_current_stage is not None and expected_current_stage != current_stage:
        return {
            "conflict": True,
            "expected": expected_current_stage,
            "actual": current_stage,
        }

    if target_stage == current_stage:
        return {
            "trip_id": trip_id,
            "old_stage": current_stage,
            "new_stage": current_stage,
            "changed": False,
            "readiness": trip.get("validation", {}).get("readiness"),
        }

    TripStore.update_trip(trip_id, {"stage": target_stage})
    AuditStore.log_event("stage_transition", agency_id, {
        "trip_id": trip_id,
        "from": current_stage,
        "to": target_stage,
        "trigger": "manual",
        "reason": reason,
        "actor": "operator",
    })

    return {
        "trip_id": trip_id,
        "old_stage": current_stage,
        "new_stage": target_stage,
        "changed": True,
        "readiness": trip.get("validation", {}).get("readiness"),
    }
