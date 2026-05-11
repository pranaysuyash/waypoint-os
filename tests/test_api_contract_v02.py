"""
v0.2 API Contract Regression Tests

These tests validate the v0.2 API contract to catch breaking changes early.
If these tests fail after a code change, it means the API contract has changed
and the change should be reviewed for backward compatibility.

Run: uv run python -m pytest tests/test_api_contract_v02.py -v
"""

import os
import sys
import inspect
from typing import get_type_hints

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from dataclasses import is_dataclass, fields

from src.intake.packet_models import (
    Ambiguity,
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
    SourceEnvelope,
    SubGroup,
    UnknownField,
)
from src.intake.decision import (
    DecisionResult,
    LEGACY_ALIASES,
    MVB_BY_STAGE,
    classify_contradiction,
    field_fills_blocker,
    generate_question,
    get_contradiction_action,
    run_gap_and_decision,
)


# ===========================================================================
# CONSTANTS
# ===========================================================================

class TestV02Constants:
    """Validate v0.2 constant values."""

    def test_legacy_aliases_has_expected_mappings(self):
        """LEGACY_ALIASES has all expected v0.1 → v0.2 field mappings."""
        expected_mappings = {
            "destination_city": "destination_candidates",
            "travel_dates": "date_window",
            "budget_range": "budget_min",
            "traveler_count": "party_size",
            "traveler_preferences": "soft_preferences",
            "traveler_details": "passport_status",
        }

        for old_name, new_name in expected_mappings.items():
            assert old_name in LEGACY_ALIASES, \
                f"Legacy alias '{old_name}' missing from LEGACY_ALIASES"
            assert LEGACY_ALIASES[old_name] == new_name, \
                f"Legacy alias '{old_name}' should map to '{new_name}', got '{LEGACY_ALIASES[old_name]}'"

    def test_mvb_by_stage_has_all_stages(self):
        """MVB_BY_STAGE has all expected stages: discovery, shortlist, proposal, booking."""
        expected_stages = {"discovery", "shortlist", "proposal", "booking"}

        actual_stages = set(MVB_BY_STAGE.keys())
        assert actual_stages == expected_stages, \
            f"MVB_BY_STAGE should have stages {expected_stages}, got {actual_stages}"

    def test_mvb_by_stage_has_required_fields(self):
        """Each stage in MVB_BY_STAGE has hard_blockers, soft_blockers."""
        for stage_name, stage_config in MVB_BY_STAGE.items():
            assert "hard_blockers" in stage_config, \
                f"Stage '{stage_name}' missing 'hard_blockers'"
            assert "soft_blockers" in stage_config, \
                f"Stage '{stage_name}' missing 'soft_blockers'"

            # Validate these are lists
            assert isinstance(stage_config["hard_blockers"], list), \
                f"Stage '{stage_name}' hard_blockers should be a list"
            assert isinstance(stage_config["soft_blockers"], list), \
                f"Stage '{stage_name}' soft_blockers should be a list"

    def test_discovery_stage_has_required_hard_blockers(self):
        """Discovery stage has the 4 core hard blockers."""
        discovery_hard = set(MVB_BY_STAGE["discovery"]["hard_blockers"])

        expected_hard = {
            "destination_candidates",
            "origin_city",
            "date_window",
            "party_size",
        }

        assert discovery_hard == expected_hard, \
            f"Discovery hard blockers should be {expected_hard}, got {discovery_hard}"

    def test_booking_stage_has_passport_and_visa(self):
        """Booking stage requires passport_status and visa_status."""
        booking_hard = MVB_BY_STAGE["booking"]["hard_blockers"]

        assert "passport_status" in booking_hard, \
            "Booking stage should require passport_status"
        assert "visa_status" in booking_hard, \
            "Booking stage should require visa_status"


# ===========================================================================
# AUTHORITY LEVEL ENUM
# ===========================================================================

class TestAuthorityLevelEnum:
    """Validate AuthorityLevel structure."""

    def test_has_all_authority_levels(self):
        """AuthorityLevel has all 7 expected levels."""
        expected_levels = {
            "MANUAL_OVERRIDE",
            "EXPLICIT_USER",
            "IMPORTED_STRUCTURED",
            "EXPLICIT_OWNER",
            "DERIVED_SIGNAL",
            "SOFT_HYPOTHESIS",
            "UNKNOWN",
        }

        actual_levels = {x for x in dir(AuthorityLevel) if x.isupper() and not x.startswith('_')}
        actual_levels.discard("FACT_LEVELS")  # Not a level, but a frozenset
        actual_levels.discard("RANK")  # Not a level, but a dict

        assert actual_levels == expected_levels, \
            f"AuthorityLevel should have {expected_levels}, got {actual_levels}"

    def test_rank_method_exists(self):
        """AuthorityLevel.RANK dict exists and returns correct ordering."""
        # AuthorityLevel uses a RANK dict instead of enum values
        assert hasattr(AuthorityLevel, "RANK"), \
            "AuthorityLevel should have RANK dict"

        # MANUAL_OVERRIDE should have highest rank (1)
        assert AuthorityLevel.RANK[AuthorityLevel.MANUAL_OVERRIDE] == 1

        # UNKNOWN should have lowest rank (7)
        assert AuthorityLevel.RANK[AuthorityLevel.UNKNOWN] == 7

        # Ordering should be correct
        assert AuthorityLevel.RANK[AuthorityLevel.MANUAL_OVERRIDE] < \
               AuthorityLevel.RANK[AuthorityLevel.EXPLICIT_USER]
        assert AuthorityLevel.RANK[AuthorityLevel.EXPLICIT_USER] < \
               AuthorityLevel.RANK[AuthorityLevel.IMPORTED_STRUCTURED]
        assert AuthorityLevel.RANK[AuthorityLevel.IMPORTED_STRUCTURED] < \
               AuthorityLevel.RANK[AuthorityLevel.EXPLICIT_OWNER]
        assert AuthorityLevel.RANK[AuthorityLevel.EXPLICIT_OWNER] < \
               AuthorityLevel.RANK[AuthorityLevel.DERIVED_SIGNAL]
        assert AuthorityLevel.RANK[AuthorityLevel.DERIVED_SIGNAL] < \
               AuthorityLevel.RANK[AuthorityLevel.SOFT_HYPOTHESIS]
        assert AuthorityLevel.RANK[AuthorityLevel.SOFT_HYPOTHESIS] < \
               AuthorityLevel.RANK[AuthorityLevel.UNKNOWN]

    def test_is_fact_method_exists(self):
        """AuthorityLevel.is_fact() method exists and correctly identifies fact levels."""
        # Fact levels should return True
        assert AuthorityLevel.is_fact(AuthorityLevel.MANUAL_OVERRIDE)
        assert AuthorityLevel.is_fact(AuthorityLevel.EXPLICIT_USER)
        assert AuthorityLevel.is_fact(AuthorityLevel.IMPORTED_STRUCTURED)
        assert AuthorityLevel.is_fact(AuthorityLevel.EXPLICIT_OWNER)

        # Non-fact levels should return False
        assert not AuthorityLevel.is_fact(AuthorityLevel.DERIVED_SIGNAL)
        assert not AuthorityLevel.is_fact(AuthorityLevel.SOFT_HYPOTHESIS)
        assert not AuthorityLevel.is_fact(AuthorityLevel.UNKNOWN)

    def test_fact_levels_frozenset_exists(self):
        """AuthorityLevel.FACT_LEVELS contains all fact levels."""
        expected_fact_levels = {
            AuthorityLevel.MANUAL_OVERRIDE,
            AuthorityLevel.IMPORTED_STRUCTURED,
            AuthorityLevel.EXPLICIT_USER,
            AuthorityLevel.EXPLICIT_OWNER,
        }

        assert AuthorityLevel.FACT_LEVELS == expected_fact_levels, \
            f"FACT_LEVELS should contain {expected_fact_levels}"


# ===========================================================================
# FUNCTION SIGNATURES
# ===========================================================================

class TestFunctionSignatures:
    """Validate function signatures haven't changed unexpectedly."""

    def test_run_gap_and_decision_signature(self):
        """run_gap_and_decision() has expected signature."""
        sig = inspect.signature(run_gap_and_decision)

        params = list(sig.parameters.keys())

        # Expected parameters (v0.2)
        expected_params = ["packet", "feasibility_table", "_cached_feasibility"]

        for param in expected_params:
            assert param in params, \
                f"run_gap_and_decision() should have parameter '{param}', got {params}"

    def test_field_fills_blocker_signature(self):
        """field_fills_blocker() has expected signature."""
        sig = inspect.signature(field_fills_blocker)

        params = list(sig.parameters.keys())

        # Expected parameters (v0.2)
        expected_params = ["slot", "ambiguities", "field_name"]

        for param in expected_params:
            assert param in params, \
                f"field_fills_blocker() should have parameter '{param}', got {params}"

    def test_generate_question_signature(self):
        """generate_question() has expected signature."""
        sig = inspect.signature(generate_question)

        params = list(sig.parameters.keys())

        # Expected parameters (v0.2 - may vary)
        # Just check that field_name is present
        assert "field_name" in params, \
            f"generate_question() should have parameter 'field_name', got {params}"


# ===========================================================================
# DATACLASS STRUCTURES
# ===========================================================================

class TestDataclassStructures:
    """Validate dataclass structures haven't changed unexpectedly."""

    def test_canonical_packet_is_dataclass(self):
        """CanonicalPacket is a dataclass."""
        assert is_dataclass(CanonicalPacket), \
            "CanonicalPacket should be a dataclass"

    def test_canonical_packet_has_required_fields(self):
        """CanonicalPacket has all expected fields."""
        packet_fields = {f.name for f in fields(CanonicalPacket)}

        expected_fields = {
            "packet_id",
            "schema_version",
            "stage",
            "operating_mode",
            "decision_state",
            "facts",
            "derived_signals",
            "hypotheses",
            "ambiguities",
            "unknowns",
            "contradictions",
            "source_envelope_ids",
            "revision_count",
            "event_cursor",
            "events",
        }

        # Check all expected fields are present
        for field in expected_fields:
            assert field in packet_fields, \
                f"CanonicalPacket should have field '{field}', got {packet_fields}"

    def test_decision_result_is_dataclass(self):
        """DecisionResult is a dataclass."""
        assert is_dataclass(DecisionResult), \
            "DecisionResult should be a dataclass"

    def test_decision_result_has_required_fields(self):
        """DecisionResult has all expected fields."""
        result_fields = {f.name for f in fields(DecisionResult)}

        expected_fields = {
            "packet_id",
            "current_stage",
            "operating_mode",
            "decision_state",
            "hard_blockers",
            "soft_blockers",
            "ambiguities",
            "contradictions",
            "follow_up_questions",
            "branch_options",
            "rationale",
            "confidence",
            "risk_flags",
            "commercial_decision",
            "intent_scores",
            "next_best_action",
            "budget_breakdown",
        }

        # Check all expected fields are present
        for field in expected_fields:
            assert field in result_fields, \
                f"DecisionResult should have field '{field}', got {result_fields}"

    def test_slot_is_dataclass(self):
        """Slot is a dataclass."""
        assert is_dataclass(Slot), \
            "Slot should be a dataclass"

    def test_slot_has_required_fields(self):
        """Slot has all expected fields."""
        slot_fields = {f.name for f in fields(Slot)}

        expected_fields = {
            "value",
            "confidence",
            "authority_level",
            "extraction_mode",
            "evidence_refs",
            "updated_at",
            "notes",
            "maturity",
            "derived_from",
        }

        # Check all expected fields are present
        for field in expected_fields:
            assert field in slot_fields, \
                f"Slot should have field '{field}', got {slot_fields}"

    def test_slot_to_dict_preserves_lineage(self):
        """Slot serialization preserves provenance lineage."""
        slot = Slot(
            value="high urgency",
            confidence=0.8,
            authority_level=AuthorityLevel.DERIVED_SIGNAL,
            extraction_mode="derived",
            derived_from=["date_end", "envelope_1"],
        )

        assert slot.to_dict()["derived_from"] == ["date_end", "envelope_1"]

    def test_packet_to_dict_preserves_slot_lineage(self):
        """Packet serialization must not drop fact/derived/hypothesis lineage."""
        pkt = CanonicalPacket(packet_id="lineage_contract")
        pkt.facts["destination_candidates"] = Slot(
            value=["Paris"],
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            derived_from=["envelope_1"],
        )
        pkt.derived_signals["urgency"] = Slot(
            value="medium",
            confidence=0.7,
            authority_level=AuthorityLevel.DERIVED_SIGNAL,
            extraction_mode="derived",
            derived_from=["date_window"],
        )

        data = pkt.to_dict()

        assert data["facts"]["destination_candidates"]["derived_from"] == ["envelope_1"]
        assert data["derived_signals"]["urgency"]["derived_from"] == ["date_window"]

    def test_ambiguity_is_dataclass(self):
        """Ambiguity is a dataclass."""
        assert is_dataclass(Ambiguity), \
            "Ambiguity should be a dataclass"


# ===========================================================================
# BACKWARD COMPATIBILITY
# ===========================================================================

class TestBackwardCompatibility:
    """Test backward compatibility with v0.1 field names."""

    def test_legacy_alias_resolution_works(self):
        """Legacy field names can be resolved through LEGACY_ALIASES."""
        # Create a packet with legacy field name in facts
        pkt = CanonicalPacket(packet_id="legacy_test", stage="discovery")

        # Use legacy field name
        pkt.facts["destination_city"] = Slot(
            value="Singapore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )

        # This should not raise an error
        # The decision engine should handle the legacy field name
        r = run_gap_and_decision(pkt)

        # The legacy field should fill the corresponding blocker
        # (Note: This tests that the system doesn't crash with legacy field names)
        # In v0.2, reverse alias lookup only works in facts layer, not derived_signals
        assert r is not None

    def test_canonical_field_names_work(self):
        """Canonical v0.2 field names work correctly."""
        pkt = CanonicalPacket(packet_id="canonical_test", stage="discovery")

        # Use canonical field names
        pkt.facts["destination_candidates"] = Slot(
            value=["Singapore"],
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["party_size"] = Slot(
            value=3,
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )

        r = run_gap_and_decision(pkt)

        # Should have no hard blockers with all canonical fields filled
        assert len(r.hard_blockers) == 0, \
            f"Canonical field names should fill blockers, got {r.hard_blockers}"
