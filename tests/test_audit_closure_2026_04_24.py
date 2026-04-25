"""
test_audit_closure_2026_04_24.py — Regression tests for audit closure fixes.

Covers:
- P1-3: internal_notes leakage via serialization
- P2-5: BUDGET_FEASIBILITY_TABLE canonical import
"""

import pytest
from intake.strategy import PromptBundle, build_traveler_safe_bundle
from src.intake.decision import BUDGET_FEASIBILITY_TABLE, _build_suitability_profile
from src.decision.rules import BUDGET_FEASIBILITY_TABLE as RULES_TABLE


class TestSerializationSafety:
    """P1-3: Traveler-safe serialization must never include internal_notes."""

    def test_prompt_bundle_to_traveler_dict_excludes_internal_notes(self):
        bundle = PromptBundle(
            system_context="sys",
            user_message="user",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes="SECRET",
            constraints=[],
            audience="traveler",
        )
        serialized = bundle.to_traveler_dict()
        assert "internal_notes" not in serialized
        assert serialized["audience"] == "traveler"

    def test_serialize_bundle_prefers_to_traveler_dict(self):
        from spine_api.server import serialize_bundle

        bundle = PromptBundle(
            system_context="sys",
            user_message="user",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes="SECRET",
            constraints=[],
            audience="traveler",
        )
        result = serialize_bundle(bundle, traveler_safe=True)
        assert "internal_notes" not in result

    def test_serialize_bundle_non_traveler_uses_to_dict(self):
        from spine_api.server import serialize_bundle

        bundle = PromptBundle(
            system_context="sys",
            user_message="user",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes="SECRET",
            constraints=[],
            audience="internal",
        )
        # Non-traveler serialization uses to_dict() which includes internal_notes
        result = serialize_bundle(bundle, traveler_safe=False)
        assert "internal_notes" in result


class TestBudgetTableDeduplication:
    """P2-5: BUDGET_FEASIBILITY_TABLE must have a single canonical source."""

    def test_tables_are_identical(self):
        """Ensure imported table matches the rules module table exactly."""
        assert BUDGET_FEASIBILITY_TABLE is RULES_TABLE, (
            "intake.decision and decision.rules budget tables must be the same object"
        )

    def test_table_has_expected_destinations(self):
        expected = [
            "Singapore",
            "Japan",
            "Dubai",
            "Thailand",
            "Maldives",
            "Europe",
            "Sri Lanka",
            "Andaman",
            "Andamans",
            "Goa",
            "Kerala",
            "Kashmir",
            "Bangkok",
            "Bali",
            "Vietnam",
            "Nepal",
            "Bhutan",
            "Mauritius",
            "Seychelles",
            "Turkey",
            "Istanbul",
            "Paris",
            "London",
            "Tokyo",
            "Osaka",
            "New York",
            "__default_domestic__",
            "__default_international__",
        ]
        for dest in expected:
            assert dest in BUDGET_FEASIBILITY_TABLE, f"Missing destination: {dest}"
            assert "min_per_person" in BUDGET_FEASIBILITY_TABLE[dest]
    
    def test_table_is_mutable_in_one_place(self):
        """Mutating one reference must affect the other (single source)."""
        original = BUDGET_FEASIBILITY_TABLE["Singapore"]["min_per_person"]
        BUDGET_FEASIBILITY_TABLE["Singapore"]["min_per_person"] = 99999
        assert RULES_TABLE["Singapore"]["min_per_person"] == 99999
        # Restore
        BUDGET_FEASIBILITY_TABLE["Singapore"]["min_per_person"] = original


class TestSuitabilityProfile:
    """Backend contract: _build_suitability_profile maps risk_flags to structured profile."""

    def test_empty_risk_flags_returns_none(self):
        assert _build_suitability_profile([]) is None

    def test_non_suitability_flags_are_ignored(self):
        flags = [{
            "flag": "budget_feasibility",
            "severity": "high",
            "message": "Budget too low",
        }]
        assert _build_suitability_profile(flags) is None

    def test_suitability_exclude_produces_profile(self):
        flags = [{
            "flag": "suitability_exclude_scuba",
            "severity": "critical",
            "message": "Child under 5 cannot scuba dive",
            "confidence": 0.95,
            "details": {"activity_id": "scuba", "participant_ref": "child_1"},
        }]
        profile = _build_suitability_profile(flags)
        assert profile is not None
        assert profile["summary"]["status"] == "unsuitable"
        assert profile["summary"]["overallScore"] == 95.0
        assert len(profile["dimensions"]) == 1
        assert profile["dimensions"][0]["type"] == "intensity"
        assert profile["dimensions"][0]["severity"] == "high"

    def test_suitability_discourage_produces_caution(self):
        flags = [{
            "flag": "suitability_discourage_trekking",
            "severity": "medium",
            "message": "Elderly traveler may find trekking strenuous",
            "confidence": 0.72,
        }]
        profile = _build_suitability_profile(flags)
        assert profile is not None
        assert profile["summary"]["status"] == "caution"
        assert profile["dimensions"][0]["type"] == "mobility"
        assert profile["dimensions"][0]["score"] == 72.0

    def test_multiple_flags_aggregate(self):
        flags = [
            {
                "flag": "suitability_exclude_scuba",
                "severity": "critical",
                "message": "Too young",
                "confidence": 0.95,
            },
            {
                "flag": "suitability_discourage_trekking",
                "severity": "medium",
                "message": "Elderly fatigue risk",
                "confidence": 0.60,
            },
        ]
        profile = _build_suitability_profile(flags)
        assert profile is not None
        # Max severity is critical (mapped to high) -> unsuitable
        assert profile["summary"]["status"] == "unsuitable"
        # Average score = (95 + 60) / 2 = 77.5
        assert profile["summary"]["overallScore"] == 77.5
        assert len(profile["dimensions"]) == 2
        assert profile["overrides"] == []

    def test_suitability_coherence_flag(self):
        flags = [{
            "flag": "suitability_coherence",
            "severity": "high",
            "message": "Activity overload detected",
            "confidence": 0.80,
        }]
        profile = _build_suitability_profile(flags)
        assert profile is not None
        assert profile["dimensions"][0]["type"] == "other"
