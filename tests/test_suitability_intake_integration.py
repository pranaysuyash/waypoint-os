"""
tests/test_suitability_intake_integration.py

Tests for P0-01: Suitability Audit at Intake integration.
Tests that suitability flags are properly integrated into the intake orchestration.
"""

import pytest
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal

from src.intake.packet_models import (
    CanonicalPacket,
    SourceEnvelope,
    Slot,
    SuitabilityFlag,
    AuthorityLevel,
)
from src.suitability.integration import assess_activity_suitability
from src.suitability.models import ParticipantRef, ActivityDefinition


@pytest.fixture
def packet_elderly_with_intense_activity():
    """Create a packet with elderly traveler and intense activities."""
    packet = CanonicalPacket(packet_id="test_elderly_intense_001")
    
    # Add party composition with elderly
    packet.facts["party_composition"] = Slot(
        value={"adults": 0, "elderly": 1, "children": 0},
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    
    # Add destination
    packet.facts["destination_candidates"] = Slot(
        value=["maldives"],
        confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    
    return packet


@pytest.fixture
def packet_toddler_with_activities():
    """Create a packet with toddler."""
    packet = CanonicalPacket(packet_id="test_toddler_001")
    
    # Add party composition with toddler
    packet.facts["party_composition"] = Slot(
        value={"adults": 1, "elderly": 0, "children": 1},
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    
    # Add child ages
    packet.facts["child_ages"] = Slot(
        value=[3],
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    
    return packet


@pytest.fixture
def packet_elderly_and_toddler():
    """Create a packet with both elderly and toddler."""
    packet = CanonicalPacket(packet_id="test_mixed_001")
    
    # Add party composition
    packet.facts["party_composition"] = Slot(
        value={"adults": 1, "elderly": 1, "children": 1},
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    
    # Add child ages
    packet.facts["child_ages"] = Slot(
        value=[2],
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    
    return packet


@pytest.fixture
def packet_suitable():
    """Create a packet with no suitability concerns."""
    packet = CanonicalPacket(packet_id="test_suitable_001")
    
    # Add party composition with only adults
    packet.facts["party_composition"] = Slot(
        value={"adults": 2, "elderly": 0, "children": 0},
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    
    return packet


class TestSuitabilityIntegration:
    """Test suitability integration at intake end."""

    def test_assess_activity_suitability_elderly_intense(self, packet_elderly_with_intense_activity):
        """Test that elderly + intense activities generate CRITICAL flags."""
        flags = assess_activity_suitability(packet_elderly_with_intense_activity)
        
        # Should have some flags for intense activities (high intensity with elderly)
        assert len(flags) > 0
        
        # Some flags should be critical or high
        critical_high = [f for f in flags if f.severity in ["critical", "high"]]
        assert len(critical_high) > 0, "Expected critical/high flags for elderly + intense activities"

    def test_assess_activity_suitability_toddler(self, packet_toddler_with_activities):
        """Test that toddler generates appropriate flags."""
        flags = assess_activity_suitability(packet_toddler_with_activities)
        
        # Should have flags for water-based activities with toddler
        water_flags = [f for f in flags if "water" in str(f.details).lower()]
        if water_flags:
            # Water-based activities should be critical for toddlers
            assert water_flags[0].severity in ["critical", "high"]

    def test_assess_activity_suitability_no_participants(self):
        """Test that no participants returns no flags."""
        packet = CanonicalPacket(packet_id="test_no_participants")
        # Don't add party composition
        
        flags = assess_activity_suitability(packet)
        assert len(flags) == 0

    def test_assess_activity_suitability_suitable(self, packet_suitable):
        """Test that suitable trips have minimal flags."""
        flags = assess_activity_suitability(packet_suitable)
        
        # Adults with no specific constraints should have no critical flags
        critical_flags = [f for f in flags if f.severity == "critical"]
        assert len(critical_flags) == 0, "Adults should not have critical suitability flags"

    def test_suitability_flag_structure(self, packet_elderly_with_intense_activity):
        """Test that flags have correct structure."""
        flags = assess_activity_suitability(packet_elderly_with_intense_activity)
        
        for flag in flags:
            assert isinstance(flag, SuitabilityFlag)
            assert hasattr(flag, "flag_type")
            assert hasattr(flag, "severity")
            assert hasattr(flag, "reason")
            assert hasattr(flag, "confidence")
            assert flag.severity in ["low", "medium", "high", "critical"]
            assert 0.0 <= flag.confidence <= 1.0

    def test_suitability_flags_confidence(self, packet_elderly_with_intense_activity):
        """Test that confidence scores are reasonable."""
        flags = assess_activity_suitability(packet_elderly_with_intense_activity)
        
        for flag in flags:
            # Confidence should be between 0 and 1
            assert 0.0 <= flag.confidence <= 1.0


class TestSuitabilityOrchestration:
    """Test suitability integration in orchestration."""
    
    def test_critical_flags_set_decision_state(self, packet_elderly_with_intense_activity):
        """Test that critical flags set decision_state to STOP_NEEDS_REVIEW."""
        from src.intake.orchestration import run_spine_once
        from src.intake.packet_models import SourceEnvelope
        
        # Create a simple envelope with elderly traveler
        envelope = SourceEnvelope(
            envelope_id="test_env_1",
            source_system="traveler_form",
            actor_type="traveler",
            received_at=datetime.now().isoformat(),
            content={
                "party_composition": {"adults": 0, "elderly": 1},
                "destination": "maldives",
            },
            content_type="structured_json",
        )
        
        # Run spine
        result = run_spine_once([envelope], stage="discovery")
        
        # Check if suitability_flags are populated
        assert hasattr(result.packet, "suitability_flags")
        
        # If there are critical flags, decision_state should be STOP_NEEDS_REVIEW
        critical_flags = [f for f in result.packet.suitability_flags if f.severity == "critical"]
        if critical_flags:
            assert result.packet.decision_state == "STOP_NEEDS_REVIEW"
            assert "suitability_critical_flags_present" in result.decision.hard_blockers
            assert any(
                r.get("flag") == "suitability_critical_flags_present"
                for r in result.decision.risk_flags
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
