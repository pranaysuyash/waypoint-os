"""
tests/test_concierge_and_audio.py — Tests for Concierge Messaging & Spoken Voice Intake.
"""

from src.concierge.messaging_router import TravelerConciergeRouter
from src.intake.audio_intake import VoiceBriefingIntakeEngine


def test_concierge_flight_alert_and_inbound_routing():
    """Verify proactive notification creation and traveler inbound intent routing."""
    notif = TravelerConciergeRouter.create_flight_disruption_alert(
        traveler_name="Sarah Connor",
        phone="+12025550199",
        flight_number="LH400",
        delay_minutes=150,
        alternate_flight="LH404",
        channel="whatsapp",
    )
    assert "Sarah Connor" in notif.content
    assert "LH404" in notif.content
    assert notif.channel == "whatsapp"

    # Inbound escalation
    agent_res = TravelerConciergeRouter.route_incoming_traveler_message("+12025550199", "I need to talk to an agent please")
    assert agent_res["action"] == "ESCALATE_TO_HUMAN_AGENT"

    confirm_res = TravelerConciergeRouter.route_incoming_traveler_message("+12025550199", "YES confirm that alternate flight")
    assert confirm_res["action"] == "AUTO_CONFIRM_REBOOKING"


def test_voice_briefing_audio_intake():
    """Verify speech artifact cleaning and canonical entity extraction from voice memos."""
    raw_speech = "Um, like, we want to plan a family vacation to Rome, you know, for 2 adults and 2 kids with flights included."
    res = VoiceBriefingIntakeEngine.process_voice_memo(
        audio_file_name="briefing_01.m4a",
        simulated_transcript=raw_speech,
    )

    assert "um" not in res.raw_transcript.lower()
    assert "you know" not in res.raw_transcript.lower()
    assert res.extracted_fields["flight_inclusiveness"] == "INCLUDE_FLIGHTS"
    assert res.source_envelope["source_system"] == "agency_notes"
