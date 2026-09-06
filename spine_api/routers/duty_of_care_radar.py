"""Deterministic duty-of-care cockpit preview API.

The local engine supplies fixture threat, beacon, STEP, dispatch, and SOS
shapes for workflow review. No live threat feed, trusted beacon source,
consular submission, dispatch provider, or message transport is connected.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field

from spine_api.core.reality_tier import RealityTier, TierMetadata
from src.orchestration.duty_of_care_radar import DutyOfCareRadarEngine

router = APIRouter(prefix="/api/v1/duty-of-care-radar", tags=["duty-of-care-radar"])


class CockpitSummaryRequest(BaseModel):
    agency_id: str = Field("AGENCY-ENTERPRISE-001", description="Agency account identifier")


def _preview_metadata() -> Dict[str, Any]:
    return {
        **TierMetadata.for_response(
            RealityTier.DETERMINISTIC_PREVIEW,
            "duty_of_care_cockpit_preview",
            computation_method="local deterministic fixture engine; no live feed or outbound action",
            missing_for_upgrade=[
                "trusted threat-feed provenance and freshness",
                "authenticated traveler/device beacon evidence",
                "authorized STEP/consular submission receipt",
                "dispatch provider assignment and delivery receipt",
                "operator approval, idempotency, and audit reference",
            ],
        ),
        "source": "local_deterministic_preview",
        "simulation": True,
        "provider_connected": False,
        "external_reference": None,
        "external_action": False,
        "operational_write": False,
        "effects": [],
    }


@router.post("/cockpit/summary")
def get_duty_of_care_summary(payload: CockpitSummaryRequest) -> Dict[str, Any]:
    """Return a non-operative cockpit preview; no emergency action is sent."""
    summary = DutyOfCareRadarEngine.compile_live_cockpit(agency_id=payload.agency_id)
    cockpit = summary.to_dict()
    cockpit["evidence_status"] = "UNVERIFIED_LOCAL_FIXTURES"
    cockpit["operator_next_step"] = (
        "Review sample threat, beacon, STEP, dispatch, and SOS records with an authorized operator; "
        "nothing was verified, transmitted, dispatched, or persisted by this route."
    )
    cockpit["traveler_metrics"]["accounted_for_status"] = "SUBMITTED_SAMPLE_STATUS_NOT_VERIFIED"
    cockpit["step_consular_manifests_status"] = "DRAFT_NOT_SUBMITTED"
    cockpit["ground_dispatch_status"] = "FIXTURE_NOT_DISPATCHED"
    cockpit["sos_broadcast_status"] = "PAYLOAD_PREVIEW_NOT_SENT"
    return {
        "status": "PREVIEW_ONLY",
        "reality": _preview_metadata(),
        "cockpit": cockpit,
    }
