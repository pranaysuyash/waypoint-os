"""Trip lifecycle router extracted from server shell."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from spine_api.contract import ExplicitReassessRequest
from spine_api.core.auth import get_current_agency, get_current_user
from spine_api.models.tenant import Agency, User
from spine_api.services import trip_lifecycle_service
from src.intake.config.agency_settings import AgencySettingsStore

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

TripStore = persistence.TripStore

router = APIRouter()

_execute_pipeline = None


def configure(*, execute_pipeline_fn) -> None:
    global _execute_pipeline
    _execute_pipeline = execute_pipeline_fn


class StageTransitionRequest(BaseModel):
    target_stage: str
    reason: Optional[str] = None
    expected_current_stage: Optional[str] = None


@router.post("/trips/{trip_id}/reassess")
def reassess_trip(
    trip_id: str,
    request: ExplicitReassessRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    if _execute_pipeline is None:
        raise HTTPException(status_code=500, detail="Reassessment executor is not configured")

    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    settings = AgencySettingsStore.load(agency.id)
    policy = settings.autonomy
    if not policy.allow_explicit_reassess:
        raise HTTPException(status_code=403, detail="Explicit reassessment is disabled by policy")

    if request.stage and request.stage not in trip_lifecycle_service.VALID_STAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid stage '{request.stage}'. Must be one of {sorted(trip_lifecycle_service.VALID_STAGES)}",
        )

    request_dict = trip_lifecycle_service.build_reassessment_request_from_trip(
        trip,
        stage_override=request.stage,
        operating_mode_override=request.operating_mode,
        strict_leakage_override=request.strict_leakage,
    )
    run_id = trip_lifecycle_service.queue_trip_reassessment(
        trip,
        agency_id=agency.id,
        user_id=user.id,
        request_dict=request_dict,
        trigger="explicit",
        reason=request.reason,
        execute_pipeline_fn=_execute_pipeline,
    )
    return {
        "ok": True,
        "trip_id": trip_id,
        "run_id": run_id,
        "state": "queued",
        "trigger": "explicit",
    }


@router.patch("/trips/{trip_id}/stage")
def transition_trip_stage(
    trip_id: str,
    request: StageTransitionRequest,
    agency: Agency = Depends(get_current_agency),
):
    try:
        result = trip_lifecycle_service.transition_trip_stage(
            trip_id,
            agency_id=agency.id,
            target_stage=request.target_stage,
            reason=request.reason,
            expected_current_stage=request.expected_current_stage,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Trip not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if result.get("conflict"):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Stage conflict",
                "expected": result["expected"],
                "actual": result["actual"],
            },
        )
    return result
