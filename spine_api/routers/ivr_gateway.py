"""
spine_api/routers/ivr_gateway.py — Twilio Programmable Voice IVR Gateway API (G-4).

Bridges the simulated DTMF IVR bypass bot to real Twilio Programmable Voice
calls. When Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
TWILIO_FROM_NUMBER) are present, initiates a real outbound call with a TwiML
``<Play digits="...">`` instruction to navigate the carrier IVR tree.

Architecture:
1. POST /api/v1/ivr/calls/initiate — kicks off a real Twilio call or returns
   a preview result when credentials are absent.
2. GET  /api/v1/ivr/calls/{call_sid}/status — polls Twilio call status.
3. POST /api/v1/ivr/webhook/status — receives Twilio status callbacks
   (call-completed, human-agent-detected) for alerting advisors.

Reality boundary: when credentials are absent the endpoint returns a
``reality_tier="deterministic_preview"`` response with a synthetic call SID.
Missing-for-upgrade:
- Bidirectional audio stream (Twilio Media Streams → Whisper/Deepgram STT)
- Human-agent detection NLP → WebRTC advisor softphone bridge
- Call recording compliance and PII scrubbing pipeline
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from spine_api.core.reality_tier import RealityTier

logger = logging.getLogger("spine_api.routers.ivr_gateway")

router = APIRouter(prefix="/api/v1/ivr", tags=["ivr-gateway"])
public_router = APIRouter(prefix="/api/v1/ivr", tags=["ivr-gateway-public"])

_MISSING_FOR_UPGRADE = [
    "TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_FROM_NUMBER environment credentials",
    "Bidirectional audio stream (Twilio Media Streams → Whisper/Deepgram STT for live NLP)",
    "Human-agent detection → WebRTC advisor softphone bridge on answer",
    "Call recording compliance and PII scrubbing pipeline (CCPA/GDPR)",
]

# Known IVR DTMF trees for major carriers — mirrors ivr_bypass_bot.py
_CARRIER_DTMF: Dict[str, str] = {
    "BA":  "1w1w2w2w0",       # British Airways: option 1 → reservations → existing booking → agent
    "DL":  "1w2w1w0",          # Delta: English → existing reservation → agent bypass
    "AF":  "1w1w3w0",          # Air France: English → reservations → existing booking → agent
    "AA":  "1w1w1w0",          # American Airlines: English → reservations → existing → agent
    "UA":  "1w1w0",            # United: English → reservations → agent
    "LH":  "1w2w0",            # Lufthansa: English → existing booking → agent
}

_PREVIEW_DTMF_DEFAULT = "1w1w0"


def _twilio_credentials() -> Optional[tuple[str, str, str]]:
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_num = os.environ.get("TWILIO_FROM_NUMBER", "").strip()
    if sid and token and from_num:
        return sid, token, from_num
    return None


def _preview_call_sid(trip_id: str, carrier_code: str, phone_number: str) -> str:
    return "CA-PREVIEW-" + hashlib.sha256(
        f"{trip_id}:{carrier_code}:{phone_number}".encode()
    ).hexdigest()[:16].upper()


class InitiateCallRequest(BaseModel):
    trip_id: str = Field(..., description="Trip ID this call is for")
    carrier_code: str = Field(..., description="2-letter IATA carrier code (BA, DL, AA, etc.)")
    carrier_phone_number: str = Field(..., description="Target carrier phone number to call (E.164)")
    purpose: str = Field("rebooking", description="Call purpose for audit (rebooking / refund / upgrade)")
    callback_url: Optional[str] = Field(None, description="Optional webhook URL for Twilio status callbacks")


@router.post("/calls/initiate", summary="Initiate a Twilio IVR bypass call to a carrier")
def initiate_ivr_call(payload: InitiateCallRequest) -> Dict[str, Any]:
    """Initiate a real Twilio outbound call to the carrier's IVR and inject
    the pre-programmed DTMF sequence to reach a live agent.

    When Twilio credentials are absent, returns a deterministic preview result.
    """
    creds = _twilio_credentials()
    carrier = payload.carrier_code.upper()
    dtmf_sequence = _CARRIER_DTMF.get(carrier, _PREVIEW_DTMF_DEFAULT)

    if creds is None:
        # Preview mode — no real call
        preview_sid = _preview_call_sid(
            payload.trip_id, carrier, payload.carrier_phone_number
        )
        logger.info(
            "IVR gateway preview: trip=%s carrier=%s (no Twilio creds)",
            payload.trip_id, carrier,
        )
        return {
            "ok": True,
            "call_sid": preview_sid,
            "status": "PREVIEW_ONLY",
            "carrier_code": carrier,
            "dtmf_sequence": dtmf_sequence,
            "trip_id": payload.trip_id,
            "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
            "provider_connected": False,
            "missing_for_upgrade": _MISSING_FOR_UPGRADE,
        }

    account_sid, auth_token, from_number = creds

    # Build TwiML: play the DTMF sequence after the IVR answers.
    # The 'w' character in the DTMF string = 500ms pause between digits.
    twiml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response>'
        f'<Pause length="5"/>'
        f'<Play digits="{dtmf_sequence}"/>'
        f'<Pause length="30"/>'
        f'</Response>'
    )

    try:
        import urllib.request
        import urllib.parse
        import base64
        import json

        status_callback = payload.callback_url or ""
        form_data = urllib.parse.urlencode({
            "To": payload.carrier_phone_number,
            "From": from_number,
            "Twiml": twiml,
            "StatusCallback": status_callback,
            "StatusCallbackMethod": "POST",
        }).encode("utf-8")

        credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
        req = urllib.request.Request(
            url,
            data=form_data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        call_sid = data.get("sid", "")
        call_status = data.get("status", "queued")
        logger.info(
            "IVR gateway live call: trip=%s carrier=%s sid=%s status=%s",
            payload.trip_id, carrier, call_sid, call_status,
        )
        return {
            "ok": True,
            "call_sid": call_sid,
            "status": call_status,
            "carrier_code": carrier,
            "dtmf_sequence": dtmf_sequence,
            "trip_id": payload.trip_id,
            "reality_tier": "live_provider",
            "provider_connected": True,
            "missing_for_upgrade": [
                "Bidirectional audio stream for STT human-agent detection",
                "WebRTC advisor softphone bridge on human-agent answer",
            ],
        }
    except Exception as exc:
        logger.error("IVR gateway Twilio call failed: %s", exc)
        preview_sid = _preview_call_sid(
            payload.trip_id, carrier, payload.carrier_phone_number
        )
        return {
            "ok": False,
            "call_sid": preview_sid,
            "status": "CALL_FAILED",
            "error": str(exc),
            "carrier_code": carrier,
            "dtmf_sequence": dtmf_sequence,
            "trip_id": payload.trip_id,
            "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
            "provider_connected": False,
        }


@router.get("/calls/{call_sid}/status", summary="Poll Twilio call status")
def get_call_status(call_sid: str) -> Dict[str, Any]:
    """Poll the current status of an outbound Twilio IVR call.

    Returns provider_connected=False for preview call SIDs.
    """
    if call_sid.startswith("CA-PREVIEW-"):
        return {
            "call_sid": call_sid,
            "status": "PREVIEW_ONLY",
            "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
            "provider_connected": False,
        }

    creds = _twilio_credentials()
    if creds is None:
        return {
            "call_sid": call_sid,
            "status": "UNKNOWN",
            "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
            "provider_connected": False,
            "reason": "Twilio credentials not configured",
        }

    account_sid, auth_token, _ = creds
    try:
        import urllib.request
        import urllib.parse
        import base64
        import json

        credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Basic {credentials}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "call_sid": call_sid,
            "status": data.get("status", "unknown"),
            "duration": data.get("duration"),
            "direction": data.get("direction"),
            "reality_tier": "live_provider",
            "provider_connected": True,
        }
    except Exception as exc:
        return {
            "call_sid": call_sid,
            "status": "ERROR",
            "error": str(exc),
            "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
            "provider_connected": False,
        }


@public_router.post("/webhook/status", summary="Twilio status callback webhook (public)")
async def twilio_status_webhook(request: Request) -> Dict[str, Any]:
    """Receive Twilio call status callback POSTs.

    In production this would push events to the advisor WebSocket channel
    when the call reaches 'in-progress' (human-agent answered).
    Currently logs and acknowledges — the push channel is missing-for-upgrade.
    """
    form = await request.form()
    call_sid = str(form.get("CallSid", ""))
    call_status = str(form.get("CallStatus", ""))
    logger.info("IVR webhook: sid=%s status=%s", call_sid, call_status)
    # TODO (missing-for-upgrade): push to advisor WebSocket on "in-progress"
    return {"received": True, "call_sid": call_sid, "call_status": call_status}
