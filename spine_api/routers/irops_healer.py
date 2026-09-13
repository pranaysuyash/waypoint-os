"""
Deterministic IROPS recovery-plan preview API (PER-IROPS-SIM).

The local engine can calculate a disruption ripple and candidate next steps, but
no carrier, lodging, payment, legal-claims, or supplier-message provider is
connected. The router therefore exposes analysis as preview-only and strips
effect-bearing artifacts before returning them to API consumers.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from spine_api.core.reality_tier import RealityTier, TierMetadata
from src.orchestration.irops_healer import IROPSAutoHealerEngine

router = APIRouter(prefix="/api/v1/irops-healer", tags=["irops-healer"])

_IROPS_PREVIEW_MISSING = [
    "authenticated carrier disruption and availability feed",
    "fresh rebooking/hold provider confirmation",
    "authorized lodging/payment provider",
    "jurisdiction-specific legal review and claim evidence",
    "supplier waiver submission and delivery receipt",
]


def _preview_metadata(feature_name: str) -> Dict[str, Any]:
    """Return the canonical non-operative metadata for an IROPS preview."""
    metadata = TierMetadata.for_response(
        RealityTier.DETERMINISTIC_PREVIEW,
        feature_name,
        computation_method="local deterministic journey graph and rule preview; no provider call or operational write",
        missing_for_upgrade=_IROPS_PREVIEW_MISSING,
    )
    metadata.update(
        {
            "source": "local_deterministic_preview",
            "simulation": True,
            "provider_connected": False,
            "external_reference": None,
            "external_action": False,
            "operational_write": False,
            "effects": [],
        }
    )
    return metadata


def _preview_incident_id(trip_id: str, delayed_node_id: str, delay_minutes: int) -> str:
    """Create a stable, visibly non-operational preview identifier."""
    digest = hashlib.sha256(
        f"{trip_id}|{delayed_node_id}|{delay_minutes}".encode("utf-8")
    ).hexdigest()[:10].upper()
    return f"PREVIEW-IROPS-{digest}"


def _sanitize_healing_plan(plan: Any, payload: HealDisruptionRequest) -> Dict[str, Any]:
    """Keep candidate analysis while removing claims of external completion."""
    plan_data = plan.to_dict()
    plan_data["incident_id"] = _preview_incident_id(
        payload.trip_id,
        payload.delayed_node_id,
        payload.delay_minutes,
    )
    plan_data["resolved_at"] = None
    plan_data["evidence_status"] = "UNVERIFIED_LOCAL_INPUT"
    plan_data["analysis_status"] = "PREVIEW_ONLY"
    plan_data["operator_next_step"] = (
        "Review candidate options with an authorized operator; no rebooking, payment, "
        "compensation claim, VCC issuance, or supplier message was executed."
    )

    compensation = dict(plan_data.get("statutory_compensation") or {})
    compensation["estimated_amount_eur"] = compensation.get("amount_eur")
    compensation["amount_eur"] = None
    compensation["status"] = "UNVERIFIED_LEGAL_ESTIMATE"
    compensation["evidence_status"] = "NO_JURISDICTION_OR_CARRIER_EVIDENCE"
    plan_data["statutory_compensation"] = compensation

    preview_options: List[Dict[str, Any]] = []
    for option in plan_data.get("counterfactual_options") or []:
        candidate = dict(option)
        candidate["status"] = "PREVIEW_ONLY"
        candidate["provider_connected"] = False
        candidate["external_reference"] = None
        candidate["effects"] = []
        candidate["action"] = "REVIEW_ONLY — provider confirmation required"
        preview_options.append(candidate)
    plan_data["counterfactual_options"] = preview_options

    # The lower engine returns a generated card object for its historical unit
    # contract. It is not a real payment instrument and must never cross the
    # API boundary as one.
    plan_data["emergency_lodging_vcc"] = None
    plan_data["lodging_payment_status"] = "NOT_ISSUED"
    plan_data["waiver_status"] = "DRAFT_NOT_SENT"
    plan_data["waiver_external_reference"] = None
    return plan_data


class HealDisruptionRequest(BaseModel):
    trip_id: str = Field(..., description="Identifier of the disrupted trip")
    delayed_node_id: str = Field(..., description="ID of the delayed/cancelled node")
    delay_minutes: int = Field(180, description="Delay duration in minutes")


@router.post("/heal")
def heal_disrupted_journey(payload: HealDisruptionRequest) -> Dict[str, Any]:
    """Calculate a local recovery-plan preview without executing any action."""
    preview_envelope = {
        "status": "PREVIEW_ONLY",
        "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
        "simulation": True,
        "provider_connected": False,
        "external_action": False,
        "operational_write": False,
        "effects": [],
        "metadata": _preview_metadata("irops_recovery_plan"),
    }
    try:
        plan = IROPSAutoHealerEngine.execute_healing_protocol(
            trip_id=payload.trip_id,
            delayed_node_id=payload.delayed_node_id,
            delay_minutes=payload.delay_minutes,
        )
    except ValueError as exc:
        digest = _preview_incident_id(
            payload.trip_id, payload.delayed_node_id, payload.delay_minutes
        )
        preview_envelope["healing_plan"] = {
            "incident_id": f"PREVIEW-IROPS-{digest}",
            "trip_id": payload.trip_id,
            "analysis_status": "ABSTAIN_NO_STORED_GRAPH",
            "evidence_status": "NO_STORED_JOURNEY_GRAPH",
            "resolved_at": None,
            "counterfactual_options": [],
            "emergency_lodging_vcc": None,
            "lodging_payment_status": "NOT_ISSUED",
            "waiver_status": "DRAFT_NOT_SENT",
            "statutory_compensation": {
                "amount_eur": None,
                "estimated_amount_eur": None,
                "status": "NOT_EVALUATED",
            },
            "operator_next_step": (
                "No stored journey graph for this trip; IROPS analysis abstains. "
                f"{exc}"
            ),
        }
        return preview_envelope

    plan_data = _sanitize_healing_plan(plan, payload)
    preview_envelope["healing_plan"] = plan_data
    return preview_envelope


# ---------------------------------------------------------------------------
# G-1: Watch service management endpoints
# ---------------------------------------------------------------------------

@router.post("/watch/start", summary="Start the 24/7 IROPS auto-heal watch loop")
async def start_irops_watch() -> Dict[str, Any]:
    """Start the background watch loop that continuously monitors active trips
    for disrupted JDG nodes and runs the healing protocol automatically.

    Reality boundary: disruption detection uses ``metadata.disrupted`` flags
    on stored JDG nodes. Missing-for-upgrade: live flight-status API."""
    from src.orchestration.irops_watch_service import start_watch_service, watch_service_status

    start_watch_service()
    return {"ok": True, "action": "started", **watch_service_status()}


@router.post("/watch/stop", summary="Stop the IROPS auto-heal watch loop")
async def stop_irops_watch() -> Dict[str, Any]:
    """Cancel the background watch loop. Safe to call when the loop is not running."""
    from src.orchestration.irops_watch_service import stop_watch_service, watch_service_status

    stop_watch_service()
    return {"ok": True, "action": "stopped", **watch_service_status()}


@router.get("/watch/status", summary="IROPS watch loop status and incident registry")
async def irops_watch_status() -> Dict[str, Any]:
    """Return the current watch loop status, poll interval, and list of processed incidents."""
    from src.orchestration.irops_watch_service import watch_service_status

    return watch_service_status()
