"""
Telephony & IVR Voice Bot Models (PER-VOX-AGENT).

Defines typed schemas for automated carrier phone tree navigation,
DTMF tone sequencing, hold queue detection, and advisor bridging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class CallSessionStatus(str, Enum):
    INITIATING = "initiating"
    NAVIGATING_IVR = "navigating_ivr"
    ON_HOLD_LISTENING = "on_hold_listening"
    HUMAN_AGENT_CONNECTED = "human_agent_connected"
    BRIDGED_TO_ADVISOR = "bridged_to_advisor"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class CarrierIVRProfile:
    """Configured DTMF menu navigation rules for specific airline."""
    carrier_code: str
    carrier_name: str
    trade_phone_number: str
    dtmf_tree_sequence: List[str]  # e.g., ["1", "3", "9"]
    voice_prompt_keywords: List[str]  # e.g., ["schedule change", "agent", "travel agency"]
    average_hold_minutes: int


@dataclass(slots=True)
class IVRCallSession:
    """Active or historical telephony bypass session."""
    session_id: str
    carrier_code: str
    pnr_locator: str
    advisor_phone: str
    status: CallSessionStatus
    hold_duration_seconds: int
    dtmf_tones_sent: List[str]
    live_audio_transcript: str
    carrier_agent_name: str = "Pending Connection"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "carrier_code": self.carrier_code,
            "pnr_locator": self.pnr_locator,
            "advisor_phone": self.advisor_phone,
            "status": self.status.value,
            "hold_duration_seconds": self.hold_duration_seconds,
            "dtmf_tones_sent": self.dtmf_tones_sent,
            "live_audio_transcript": self.live_audio_transcript,
            "carrier_agent_name": self.carrier_agent_name,
            "created_at": self.created_at,
        }
