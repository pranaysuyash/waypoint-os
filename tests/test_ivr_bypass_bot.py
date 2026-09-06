"""
Airline IVR Bypass & Telephony Dispatcher Tests (PER-VOX-AGENT).
"""

from src.telephony.ivr_bypass_bot import AirlineIVRBypassBot
from src.telephony.models import CallSessionStatus


def test_ivr_call_dispatch():
    session = AirlineIVRBypassBot.dispatch_call(
        carrier_code="BA",
        pnr_locator="6XY7ZQ",
        advisor_phone="+1-415-555-0144",
    )

    assert session.carrier_code == "BA"
    assert session.pnr_locator == "6XY7ZQ"
    assert session.status == CallSessionStatus.ON_HOLD_LISTENING
    assert len(session.dtmf_tones_sent) == 3
    assert "British Airways Trade Support" in session.live_audio_transcript or "In Hold Queue" in session.live_audio_transcript


def test_ivr_call_agent_bridging():
    session = AirlineIVRBypassBot.bridge_agent_when_connected(
        session_id="CALL-TEST-001",
        carrier_agent_name="Sarah (BA Trade Support Lead)",
    )

    assert session.session_id == "CALL-TEST-001"
    assert session.status == CallSessionStatus.BRIDGED_TO_ADVISOR
    assert session.carrier_agent_name == "Sarah (BA Trade Support Lead)"
    assert "bridged to advisor" in session.live_audio_transcript.lower()


def test_supported_carriers_list():
    carriers = AirlineIVRBypassBot.list_supported_carriers()
    assert len(carriers) >= 3
    codes = [c["code"] for c in carriers]
    assert "BA" in codes
    assert "DL" in codes
    assert "AF" in codes
