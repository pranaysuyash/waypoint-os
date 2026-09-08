"""
Airline IVR Bypass API Router (PER-VOX-AGENT).

Provides endpoints for automated carrier phone tree dialing, DTMF navigation,
hold queue monitoring, and advisor call bridging.

PA-28 (2026-09-06) honesty fix: the IVR bot is a deterministic in-process
simulation — no carrier is dialed, no real DTMF is transmitted, no call is
bridged. The endpoints previously reported ``"status": "success"`` for those
synthesized actions. They now report ``"status": "simulated"`` plus the repo's
canonical preview/reality metadata (modeled on financial_settlement.py /
distribution.py), so API consumers can never mistake a simulated telephony
action for a live one. The response schema change is additive: the
``call_session`` payload shape is unchanged.

Router-level only: src/telephony/ivr_bypass_bot.py (the engine) is a separate
workstream and was not modified here.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from spine_api.core.reality_tier import RealityTier, TierMetadata

from src.telephony.ivr_bypass_bot import AirlineIVRBypassBot

router = APIRouter(prefix="/api/v1/ivr-bypass", tags=["ivr-bypass"])

_IVR_PREVIEW_MISSING = [
    "connected telephony/carrier provider (real dial + DTMF transmission)",
    "live audio stream and voice-activity detection",
    "call recording, consent, and carrier-compliance contract",
]


def _preview_metadata(feature_name: str) -> Dict[str, Any]:
    """Canonical provenance + non-operative flags for a simulated action."""
    metadata = TierMetadata.for_response(
        RealityTier.DETERMINISTIC_PREVIEW,
        feature_name,
        data_sufficient=True,
        computation_method="local deterministic IVR simulation; no telephony provider call",
        missing_for_upgrade=_IVR_PREVIEW_MISSING,
    )
    metadata.update(
        {
            "source": "local_deterministic_simulation",
            "simulation": True,
            "provider_connected": False,
            "external_reference": None,
            "external_action": False,
            "operational_write": False,
            "effects": [],
        }
    )
    return metadata


class DispatchCallRequest(BaseModel):
    carrier_code: str = Field("BA", description="Airline IATA code (e.g., BA, DL, AF)")
    pnr_locator: str = Field("6XY7ZQ", description="6-character airline PNR")
    advisor_phone: str = Field("+1-415-555-0144", description="Advisor phone to bridge when agent picks up")


class BridgeCallRequest(BaseModel):
    session_id: str = Field(..., description="Active telephony session ID")
    carrier_agent_name: str = Field("Sarah (BA Trade Desk)", description="Detected agent name")


@router.post("/calls/dispatch")
def dispatch_ivr_call(payload: DispatchCallRequest) -> Dict[str, Any]:
    """Dispatches the simulated outbound telephony bot (no carrier is dialed)."""
    session = AirlineIVRBypassBot.dispatch_call(
        carrier_code=payload.carrier_code,
        pnr_locator=payload.pnr_locator,
        advisor_phone=payload.advisor_phone,
    )
    return {
        "status": "simulated",
        "call_session": session.to_dict(),
        "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
        "provider_connected": False,
        "effects": [],
        "metadata": _preview_metadata("ivr_call_dispatch"),
    }


@router.post("/calls/bridge")
def bridge_call_to_advisor(payload: BridgeCallRequest) -> Dict[str, Any]:
    """Simulates voice activity detection of carrier agent and advisor bridge (no call placed)."""
    session = AirlineIVRBypassBot.bridge_agent_when_connected(
        session_id=payload.session_id,
        carrier_agent_name=payload.carrier_agent_name,
    )
    return {
        "status": "simulated",
        "call_session": session.to_dict(),
        "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
        "provider_connected": False,
        "effects": [],
        "metadata": _preview_metadata("ivr_call_bridge"),
    }


@router.get("/carriers/supported")
def get_supported_carriers() -> Dict[str, Any]:
    """Lists pre-programmed airline trade desk DTMF profiles (static config)."""
    carriers = AirlineIVRBypassBot.list_supported_carriers()
    return {
        "status": "success",
        "supported_carriers": carriers,
    }
