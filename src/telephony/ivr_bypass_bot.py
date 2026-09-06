"""
Automated Airline IVR Bypass & Telephony Dispatcher (PER-VOX-AGENT).

Simulates dialing airline trade support desks, navigating multi-level DTMF voice prompts,
waiting through hold queues with music/speech detection, and alerting human advisors when connected.
"""

from __future__ import annotations

import uuid
from typing import Dict, List

from src.telephony.models import (
    CallSessionStatus,
    CarrierIVRProfile,
    IVRCallSession,
)

CARRIER_PROFILES: Dict[str, CarrierIVRProfile] = {
    "BA": CarrierIVRProfile(
        carrier_code="BA",
        carrier_name="British Airways Trade Support",
        trade_phone_number="+1-800-452-1201",
        dtmf_tree_sequence=["1", "2", "4"],
        voice_prompt_keywords=["travel agent", "ticket revalidation", "schedule disruption"],
        average_hold_minutes=18,
    ),
    "DL": CarrierIVRProfile(
        carrier_code="DL",
        carrier_name="Delta Air Lines Global Sales Support",
        trade_phone_number="+1-800-847-0578",
        dtmf_tree_sequence=["2", "1", "9"],
        voice_prompt_keywords=["agency desk", "irregular operations", "waiver code"],
        average_hold_minutes=12,
    ),
    "AF": CarrierIVRProfile(
        carrier_code="AF",
        carrier_name="Air France Agency Direct Line",
        trade_phone_number="+1-800-667-2747",
        dtmf_tree_sequence=["1", "3", "0"],
        voice_prompt_keywords=["b2b trade", "amadeus sync", "re-issue"],
        average_hold_minutes=15,
    ),
}


class AirlineIVRBypassBot:
    """Automates outbound telephony navigation through carrier voice menus."""

    @classmethod
    def dispatch_call(
        cls,
        carrier_code: str,
        pnr_locator: str,
        advisor_phone: str = "+1-415-555-0144",
    ) -> IVRCallSession:
        carrier = carrier_code.upper()
        profile = CARRIER_PROFILES.get(carrier, CARRIER_PROFILES["BA"])
        session_id = f"CALL-{uuid.uuid4().hex[:6].upper()}"

        # Synthesize simulated DTMF navigation sequence
        return IVRCallSession(
            session_id=session_id,
            carrier_code=carrier,
            pnr_locator=pnr_locator,
            advisor_phone=advisor_phone,
            status=CallSessionStatus.ON_HOLD_LISTENING,
            hold_duration_seconds=145,
            dtmf_tones_sent=profile.dtmf_tree_sequence,
            live_audio_transcript=f"Dialed {profile.trade_phone_number} -> DTMF Sequence {' -> '.join(profile.dtmf_tree_sequence)} -> In Hold Queue (Est. wait {profile.average_hold_minutes}m)",
            carrier_agent_name="Waiting in Queue",
        )

    @classmethod
    def bridge_agent_when_connected(
        cls,
        session_id: str,
        carrier_agent_name: str = "Sarah (BA Trade Support Lead)",
    ) -> IVRCallSession:
        """Simulates carrier human agent pickup and advisor audio bridge."""
        return IVRCallSession(
            session_id=session_id,
            carrier_code="BA",
            pnr_locator="6XY7ZQ",
            advisor_phone="+1-415-555-0144",
            status=CallSessionStatus.BRIDGED_TO_ADVISOR,
            hold_duration_seconds=420,
            dtmf_tones_sent=["1", "2", "4"],
            live_audio_transcript="Carrier human agent answered: 'British Airways Trade Desk, Sarah speaking.' -> Audio bridged to advisor +1-415-555-0144.",
            carrier_agent_name=carrier_agent_name,
        )

    @classmethod
    def list_supported_carriers(cls) -> List[Dict[str, str]]:
        return [
            {"code": p.carrier_code, "name": p.carrier_name, "phone": p.trade_phone_number, "avg_hold": f"{p.average_hold_minutes}m"}
            for p in CARRIER_PROFILES.values()
        ]
