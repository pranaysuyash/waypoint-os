import pytest
import uuid
from spine_api.contract import SpineRunRequest
from spine_api.server import build_envelopes
from src.intake.orchestration import run_spine_once
from src.intake.packet_models import CanonicalPacket

def test_intake_pipeline_hardening_new_fields():
    """
    Verify that the intake pipeline correctly extracts and persists
    the new fields from SpineRunRequest into the CanonicalPacket.
    """
    # 1. Setup Request with new fields
    request = SpineRunRequest(
        raw_note="Family trip to Japan",
        follow_up_due_date="2026-05-01T10:00:00",
        pace_preference="relaxed",
        lead_source="referral",
        activity_provenance="direct_call",
        date_year_confidence="high",
        stage="discovery",
        operating_mode="normal_intake"
    )
    
    # 2. Build Envelopes (logic from server.py)
    # Using model_dump() for Pydantic v2
    envelopes = build_envelopes(request.model_dump())
    
    # 3. Run Pipeline
    result = run_spine_once(
        envelopes=envelopes,
        stage=request.stage,
        operating_mode=request.operating_mode
    )
    
    # 4. Verify Packet
    packet = result.packet
    assert packet is not None
    assert isinstance(packet, CanonicalPacket)
    
    # Check fields in facts
    facts = packet.facts
    
    # Verify new fields are extracted correctly
    # They should be in facts because we added them to the field_mappings in extractors.py
    
    assert facts.get("follow_up_due_date").value == "2026-05-01T10:00:00"
    assert facts.get("pace_preference").value == "relaxed"
    assert facts.get("lead_source").value == "referral"
    assert facts.get("activity_provenance").value == "direct_call"
    assert facts.get("date_year_confidence").value == "high"

    print("Intake pipeline hardening test passed!")

if __name__ == "__main__":
    test_intake_pipeline_hardening_new_fields()
