"""
Airline IVR Bypass API Router (PER-VOX-AGENT).

Provides endpoints for automated carrier phone tree dialing, DTMF navigation,
hold queue monitoring, and advisor call bridging.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.telephony.ivr_bypass_bot import AirlineIVRBypassBot

router = APIRouter(prefix="/api/v1/ivr-bypass", tags=["ivr-bypass"])


class DispatchCallRequest(BaseModel):
    carrier_code: str = Field("BA", description="Airline IATA code (e.g., BA, DL, AF)")
    pnr_locator: str = Field("6XY7ZQ", description="6-character airline PNR")
    advisor_phone: str = Field("+1-415-555-0144", description="Advisor phone to bridge when agent picks up")


class BridgeCallRequest(BaseModel):
    session_id: str = Field(..., description="Active telephony session ID")
    carrier_agent_name: str = Field("Sarah (BA Trade Desk)", description="Detected agent name")


@router.post("/calls/dispatch")
def dispatch_ivr_call(payload: DispatchCallRequest) -> Dict[str, Any]:
    """Dispatches autonomous outbound telephony bot to navigate carrier IVR menu."""
    session = AirlineIVRBypassBot.dispatch_call(
        carrier_code=payload.carrier_code,
        pnr_locator=payload.pnr_locator,
        advisor_phone=payload.advisor_phone,
    )
    return {
        "status": "success",
        "call_session": session.to_dict(),
    }


@router.post("/calls/bridge")
def bridge_call_to_advisor(payload: BridgeCallRequest) -> Dict[str, Any]:
    """Simulates voice activity detection of carrier agent and bridges advisor phone."""
    session = AirlineIVRBypassBot.bridge_agent_when_connected(
        session_id=payload.session_id,
        carrier_agent_name=payload.carrier_agent_name,
    )
    return {
        "status": "success",
        "call_session": session.to_dict(),
    }


@router.get("/carriers/supported")
def get_supported_carriers() -> Dict[str, Any]:
    """Lists pre-programmed airline trade desk DTMF profiles."""
    carriers = AirlineIVRBypassBot.list_supported_carriers()
    return {
        "status": "success",
        "supported_carriers": carriers,
    }
