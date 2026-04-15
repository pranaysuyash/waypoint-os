"""
Tests for Block 2 of Spine Hardening Plan:
- Stage-aware ambiguity severity
- Budget-stretch question generation
- NB02 telemetry for ambiguity synthesis

Run: uv run python -m pytest tests/test_block2_spine_hardening.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from intake.packet_models import (
    Ambiguity,
    CanonicalPacket,
    Slot,
    AuthorityLevel,
)
from intake.decision import (
    classify_ambiguity_severity,
    generate_budget_question,
    _synthesize_destination_ambiguity,
    AmbiguityRef,
)


class TestStageAwareAmbiguitySeverity:
    """Tests for stage-aware destination vagueness severity."""

    def test_value_vague_at_discovery_is_advisory(self):
        """At discovery, value_vague on destination is advisory (exploratory)."""
        severity = classify_ambiguity_severity(
            "destination_candidates",
            "value_vague",
            stage="discovery"
        )
        assert severity == "advisory", f"Expected advisory at discovery, got {severity}"

    def test_value_vague_at_shortlist_is_blocking(self):
        """At shortlist, value_vague on destination is blocking."""
        severity = classify_ambiguity_severity(
            "destination_candidates",
            "value_vague",
            stage="shortlist"
        )
        assert severity == "blocking", f"Expected blocking at shortlist, got {severity}"

    def test_value_vague_at_proposal_is_blocking(self):
        """At proposal, value_vague on destination is blocking."""
        severity = classify_ambiguity_severity(
            "destination_candidates",
            "value_vague",
            stage="proposal"
        )
        assert severity == "blocking"

    def test_value_vague_at_booking_is_blocking(self):
        """At booking, value_vague on destination is blocking."""
        severity = classify_ambiguity_severity(
            "destination_candidates",
            "value_vague",
            stage="booking"
        )
        assert severity == "blocking"

    def test_unresolved_alternatives_still_blocking(self):
        """unresolved_alternatives remains blocking regardless of stage."""
        for stage in ["discovery", "shortlist", "proposal", "booking"]:
            severity = classify_ambiguity_severity(
                "destination_candidates",
                "unresolved_alternatives",
                stage=stage
            )
            assert severity == "blocking", f"Expected blocking at {stage}, got {severity}"

    def test_non_destination_fields_unchanged(self):
        """Stage-awareness only affects destination_candidates."""
        for stage in ["discovery", "shortlist"]:
            severity = classify_ambiguity_severity(
                "budget_min",
                "value_vague",
                stage=stage
            )
            # Should return default (advisory) not affected by stage
            assert severity == "advisory"


class TestBudgetStretchQuestions:
    """Tests for budget-stretch question generation."""

    def test_no_stretch_generic_question(self):
        """When no stretch ambiguity, returns generic budget question."""
        pkt = CanonicalPacket(packet_id="test_no_stretch")
        # No ambiguities added
        
        question = generate_budget_question(pkt, budget_min=200000)
        assert "budget" in question.lower() or "confirm" in question.lower()

    def test_case_a_stretch_without_max(self):
        """Case A: '2L, can stretch' → asks for absolute upper limit."""
        pkt = CanonicalPacket(packet_id="test_case_a")
        pkt.add_ambiguity(Ambiguity(
            field_name="budget_min",
            ambiguity_type="budget_stretch_present",
            raw_value="2L, can stretch if needed",
        ))
        
        question = generate_budget_question(pkt, budget_min="2L")
        
        assert "absolute upper limit" in question.lower() or "upper limit" in question.lower()
        assert "2L" in question or "budget" in question

    def test_case_b_stretch_with_explicit_max(self):
        """Case B: '2L, can stretch to 2.5L' → confirms the stretch amount."""
        pkt = CanonicalPacket(packet_id="test_case_b")
        pkt.add_ambiguity(Ambiguity(
            field_name="budget_min",
            ambiguity_type="budget_stretch_present",
            raw_value="2L, can stretch to 2.5L",
        ))
        
        question = generate_budget_question(pkt, budget_min="2L")
        
        # Should mention the upper bound
        assert "2.5" in question or "2.5L" in question
        assert "hard limit" in question.lower() or "wiggle room" in question.lower()

    def test_case_b_with_unit_parsing(self):
        """Case B with unit: '200000, can go up to 250000'."""
        pkt = CanonicalPacket(packet_id="test_unit")
        pkt.add_ambiguity(Ambiguity(
            field_name="budget_min",
            ambiguity_type="budget_stretch_present",
            raw_value="200000, can go up to 250000",
        ))
        
        question = generate_budget_question(pkt, budget_min=200000)
        
        assert "250000" in question or "250k" in question.lower()


class TestTelemetryEmission:
    """Tests for NB02 telemetry emission."""

    def test_telemetry_file_created(self, tmp_path, monkeypatch):
        """Ambiguity synthesis emits telemetry to JSONL file."""
        import os
        from pathlib import Path
        
        # Mock telemetry directory
        mock_telemetry_dir = tmp_path / "telemetry"
        monkeypatch.setenv("SPINE_TELEMETRY_DIR", str(mock_telemetry_dir))
        
        pkt = CanonicalPacket(
            packet_id="test_telemetry",
            stage="discovery",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Andaman", "Sri Lanka"],
            confidence=0.7,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        
        # No ambiguity yet, synthesis should trigger
        ambiguities = []
        _synthesize_destination_ambiguity(pkt, ambiguities)
        
        # Check telemetry was written
        import glob
        telemetry_files = list(mock_telemetry_dir.glob("*.jsonl"))
        assert len(telemetry_files) > 0, "Telemetry file should be created"
        
        # Verify content
        with open(telemetry_files[0]) as f:
            event = f.readline()
            data = __import__('json').loads(event)
            assert data["event_type"] == "nb02.ambiguity_synthesis"
            assert data["data"]["field"] == "destination_candidates"
            assert data["data"]["candidates"] == ["Andaman", "Sri Lanka"]

    def test_no_telemetry_when_already_has_ambiguity(self, tmp_path, monkeypatch):
        """No telemetry when ambiguity already exists."""
        import os
        from pathlib import Path
        
        mock_telemetry_dir = tmp_path / "telemetry"
        monkeypatch.setenv("SPINE_TELEMETRY_DIR", str(mock_telemetry_dir))
        
        pkt = CanonicalPacket(
            packet_id="test_no_telemetry",
            stage="discovery",
        )
        
        # Already has ambiguity
        ambiguities = [
            AmbiguityRef(
                field_name="destination_candidates",
                ambiguity_type="unresolved_alternatives",
                raw_value="Andaman or Sri Lanka",
                severity="blocking",
            )
        ]
        
        _synthesize_destination_ambiguity(pkt, ambiguities)
        
        # Should NOT create telemetry (no synthesis needed)
        import glob
        telemetry_files = list(mock_telemetry_dir.glob("*.jsonl"))
        assert len(telemetry_files) == 0, "No telemetry when ambiguity already exists"


class TestIntegrationStageAwareQuestions:
    """Integration: Stage-aware severity affects decision flow."""

    def test_discovery_allows_branch_options_with_vague_destination(self):
        """At discovery, vague destination can allow BRANCH_OPTIONS."""
        from intake.decision import run_gap_and_decision
        
        pkt = CanonicalPacket(
            packet_id="test_discovery_vague",
            stage="discovery",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Singapore"],  # Single but vague (maybe Singapore)
            confidence=0.5,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.add_ambiguity(Ambiguity(
            field_name="destination_candidates",
            ambiguity_type="value_vague",
            raw_value="maybe Singapore",
        ))
        # Fill other blockers
        pkt.facts["origin_city"] = Slot(value="Bangalore", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER)
        pkt.facts["date_window"] = Slot(value="March 2026", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER)
        pkt.facts["party_size"] = Slot(value=4, confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER)
        
        decision = run_gap_and_decision(pkt)
        
        # At discovery, value_vague is advisory, so should not block to STOP
        assert decision.decision_state != "STOP_NEEDS_REVIEW"
        # Could be ASK_FOLLOWUP or BRANCH_OPTIONS or PROCEED_INTERNAL_DRAFT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])