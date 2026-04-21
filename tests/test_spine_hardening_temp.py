import pytest
from src.intake.packet_models import CanonicalPacket, Slot, AuthorityLevel
from src.intake.decision import run_gap_and_decision, ConfidenceScorecard
from src.intake.config.agency_settings import AgencySettings

def test_confidence_scorecard_structure():
    packet = CanonicalPacket(packet_id="test_1")
    # Add a high confidence fact
    packet.facts["destination_candidates"] = Slot(
        value=["Paris"], 
        confidence=0.9, 
        authority_level="explicit_user"
    )
    # Add an origin city
    packet.facts["origin_city"] = Slot(
        value="London",
        confidence=1.0,
        authority_level="explicit_user"
    )
    # Add date window
    packet.facts["date_window"] = Slot(
        value="June",
        confidence=1.0,
        authority_level="explicit_user"
    )
    # Add party size
    packet.facts["party_size"] = Slot(
        value=2,
        confidence=1.0,
        authority_level="explicit_user"
    )
    # Add budget
    packet.facts["budget_raw_text"] = Slot(
        value="low",
        confidence=1.0,
        authority_level="explicit_user"
    )
    # Add trip purpose
    packet.facts["trip_purpose"] = Slot(
        value="leisure",
        confidence=1.0,
        authority_level="explicit_user"
    )

    settings = AgencySettings(agency_id="test_agency")
    
    result = run_gap_and_decision(packet, agency_settings=settings)
    
    assert isinstance(result.confidence, ConfidenceScorecard)
    assert result.confidence.data_quality > 0.5
    assert "confidence_scorecard" in result.rationale
    assert result.rationale["confidence_scorecard"]["data"] == result.confidence.data_quality

def test_slot_lineage():
    slot = Slot(value="test", derived_from=["envelope_1", "slot_2"])
    assert "envelope_1" in slot.derived_from
    assert "slot_2" in slot.derived_from
