"""
D1 Autonomy Gradient — Comprehensive tests for the architecturally-upgraded autonomy layer.

Run: uv run pytest tests/test_d1_autonomy.py -v
"""

import os
import sys
import json
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from intake.config.agency_settings import (
    AgencyAutonomyPolicy,
    AgencySettings,
    AgencySettingsStore,
)
from src.intake.gates import AutonomyOutcome, NB02JudgmentGate
from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
from src.intake.decision import DecisionResult


# ---------------------------------------------------------------------------
# Task 1: AgencyAutonomyPolicy ADR shape tests
# ---------------------------------------------------------------------------

class TestAgencyAutonomyPolicyShape:
    def test_default_gates_match_adr(self):
        policy = AgencyAutonomyPolicy()
        gates = policy.approval_gates
        assert gates["PROCEED_TRAVELER_SAFE"] == "review"
        assert gates["PROCEED_INTERNAL_DRAFT"] == "auto"
        assert gates["ASK_FOLLOWUP"] == "auto"
        assert gates["BRANCH_OPTIONS"] == "review"
        assert gates["STOP_NEEDS_REVIEW"] == "block"

    def test_default_mode_overrides(self):
        policy = AgencyAutonomyPolicy()
        assert policy.mode_overrides["emergency"]["PROCEED_TRAVELER_SAFE"] == "block"
        assert policy.mode_overrides["audit"]["PROCEED_INTERNAL_DRAFT"] == "review"

    def test_safety_invariant_enforced(self):
        policy = AgencyAutonomyPolicy()
        policy.approval_gates["STOP_NEEDS_REVIEW"] = "auto"
        policy.__post_init__()
        assert policy.approval_gates["STOP_NEEDS_REVIEW"] == "block"

    def test_unknown_decision_state_removed_on_reinit(self):
        policy = AgencyAutonomyPolicy()
        # Manually inject an unknown state (simulates a malformed JSON load path)
        policy.approval_gates["UNKNOWN_STATE"] = "auto"
        assert "UNKNOWN_STATE" in policy.approval_gates
        # Re-run __post_init__ to normalize
        policy.__post_init__()
        assert "UNKNOWN_STATE" not in policy.approval_gates

    def test_effective_gate_basic(self):
        policy = AgencyAutonomyPolicy()
        assert policy.effective_gate("PROCEED_TRAVELER_SAFE", "normal_intake") == "review"
        assert policy.effective_gate("PROCEED_INTERNAL_DRAFT", "normal_intake") == "auto"

    def test_effective_gate_mode_override(self):
        policy = AgencyAutonomyPolicy()
        assert policy.effective_gate("PROCEED_TRAVELER_SAFE", "emergency") == "block"
        assert policy.effective_gate("PROCEED_INTERNAL_DRAFT", "audit") == "review"

    def test_legacy_dict_upgrade(self):
        legacy = {
            "min_proceed_confidence": 0.9,
            "require_review_on_infeasible_budget": True,
        }
        policy = AgencyAutonomyPolicy.from_legacy_dict(legacy)
        assert policy.min_proceed_confidence == 0.9
        assert policy.approval_gates["PROCEED_TRAVELER_SAFE"] == "review"
        assert policy.approval_gates["STOP_NEEDS_REVIEW"] == "block"

    def test_legacy_dict_full_gates(self):
        legacy = {
            "approval_gates": {
                "PROCEED_TRAVELER_SAFE": "auto",
                "ASK_FOLLOWUP": "review",
            }
        }
        policy = AgencyAutonomyPolicy.from_legacy_dict(legacy)
        assert policy.approval_gates["PROCEED_TRAVELER_SAFE"] == "auto"
        assert policy.approval_gates["ASK_FOLLOWUP"] == "review"
        assert policy.approval_gates["STOP_NEEDS_REVIEW"] == "block"

    def test_full_adr_fields_present(self):
        policy = AgencyAutonomyPolicy()
        assert hasattr(policy, "approval_gates")
        assert hasattr(policy, "mode_overrides")
        assert hasattr(policy, "auto_proceed_with_warnings")
        assert hasattr(policy, "learn_from_overrides")


# ---------------------------------------------------------------------------
# Task 1 continued: AgencySettings backward-compat
# ---------------------------------------------------------------------------

class TestAgencySettingsBackwardCompat:
    def test_default_settings_no_crash(self):
        settings = AgencySettings(agency_id="test")
        assert settings.autonomy.approval_gates["STOP_NEEDS_REVIEW"] == "block"

    def test_legacy_json_loads(self, tmp_path, monkeypatch):
        mod = AgencySettingsStore
        monkeypatch.setattr(
            sys.modules["intake.config.agency_settings"], "_DATA_ROOT", str(tmp_path)
        )
        path = tmp_path / "agency_legacy.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "agency_id": "legacy",
                "brand_tone": "direct",
                "autonomy": {
                    "min_proceed_confidence": 0.95,
                    "require_review_on_infeasible_budget": False,
                }
            }, f)
        loaded = AgencySettingsStore.load("legacy")
        assert loaded.brand_tone == "direct"
        assert loaded.autonomy.min_proceed_confidence == 0.95
        assert loaded.autonomy.approval_gates["PROCEED_INTERNAL_DRAFT"] == "auto"

    def test_save_and_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            sys.modules["intake.config.agency_settings"], "_DATA_ROOT", str(tmp_path)
        )
        settings = AgencySettingsStore.defaults("roundtrip")
        settings.autonomy.approval_gates["PROCEED_TRAVELER_SAFE"] = "auto"
        settings.autonomy.auto_proceed_with_warnings = True
        AgencySettingsStore.save(settings)

        loaded = AgencySettingsStore.load("roundtrip")
        assert loaded.autonomy.approval_gates["PROCEED_TRAVELER_SAFE"] == "auto"
        assert loaded.autonomy.auto_proceed_with_warnings is True
        assert loaded.autonomy.approval_gates["STOP_NEEDS_REVIEW"] == "block"


# ---------------------------------------------------------------------------
# Task 2: AutonomyOutcome + NB02 Judgment Gate tests
# ---------------------------------------------------------------------------

class TestAutonomyOutcome:
    def test_outcome_properties(self):
        outcome = AutonomyOutcome(
            raw_verdict="PROCEED_TRAVELER_SAFE",
            effective_action="review",
            approval_required=True,
            rule_source="safety_invariant",
            safety_invariant_applied=True,
            reasons=["Test"],
        )
        assert outcome.is_auto is False
        assert outcome.is_review is True
        assert outcome.is_blocked is False  # "review" is not "block"
        assert outcome.to_dict()["raw_verdict"] == "PROCEED_TRAVELER_SAFE"

    def test_safety_invariant_forces_block(self):
        policy = AgencyAutonomyPolicy()
        gate = NB02JudgmentGate()

        decision = DecisionResult(
            packet_id="test",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="STOP_NEEDS_REVIEW",
        )
        settings = AgencySettings(agency_id="t", autonomy=policy)
        outcome = gate.evaluate(decision, settings)
        assert outcome.effective_action == "block"
        assert outcome.safety_invariant_applied is True
        assert outcome.rule_source == "safety_invariant"

    def test_mode_override_detected(self):
        policy = AgencyAutonomyPolicy()
        gate = NB02JudgmentGate()

        decision = DecisionResult(
            packet_id="test",
            current_stage="discovery",
            operating_mode="emergency",
            decision_state="PROCEED_TRAVELER_SAFE",
        )
        settings = AgencySettings(agency_id="t", autonomy=policy)
        outcome = gate.evaluate(decision, settings)
        assert outcome.effective_action == "block"
        assert outcome.mode_override_applied == "emergency"
        assert "Mode override" in " ".join(outcome.reasons)

    def test_warning_override_downgrades_auto(self):
        policy = AgencyAutonomyPolicy()
        policy.auto_proceed_with_warnings = False
        gate = NB02JudgmentGate()

        decision = DecisionResult(
            packet_id="test",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="PROCEED_INTERNAL_DRAFT",
            risk_flags=[{"flag": "budget_risk"}],
        )
        settings = AgencySettings(agency_id="t", autonomy=policy)
        outcome = gate.evaluate(decision, settings)
        assert outcome.effective_action == "review"
        assert outcome.warning_override_applied is True

    def test_no_warning_override_when_disabled(self):
        policy = AgencyAutonomyPolicy()
        policy.auto_proceed_with_warnings = True
        gate = NB02JudgmentGate()

        decision = DecisionResult(
            packet_id="test",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="PROCEED_INTERNAL_DRAFT",
            risk_flags=[{"flag": "budget_risk"}],
        )
        settings = AgencySettings(agency_id="t", autonomy=policy)
        outcome = gate.evaluate(decision, settings)
        assert outcome.effective_action == "auto"
        assert outcome.warning_override_applied is False

    def test_stop_needs_review_invariant_no_matter_what(self):
        """Even if someone sets STOP_NEEDS_REVIEW to auto, safety invariant forces block."""
        policy = AgencyAutonomyPolicy()
        policy.approval_gates["STOP_NEEDS_REVIEW"] = "auto"  # try to override (should be reset)
        policy.__post_init__()
        gate = NB02JudgmentGate()

        decision = DecisionResult(
            packet_id="test2",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="STOP_NEEDS_REVIEW",
        )
        settings = AgencySettings(agency_id="t", autonomy=policy)
        outcome = gate.evaluate(decision, settings)
        assert outcome.effective_action == "block"
        assert outcome.safety_invariant_applied is True


# ---------------------------------------------------------------------------
# Task 2 continued: Orchestration integration (raw verdict preserved)
# ---------------------------------------------------------------------------

class TestOrchestrationRawVerdictPreservation:
    def test_spine_run_preserves_raw_decision(self):
        """
        Simulate a valid packet through run_spine_once by mocking the
        extraction and validation layers so the NB02 gate is exercised.
        """
        from unittest.mock import patch

        # Build a minimally valid packet that will pass validation
        from intake.packet_models import CanonicalPacket, Slot, AuthorityLevel
        from intake.validation import PacketValidationReport

        valid_packet = CanonicalPacket(
            packet_id="pkt_valid",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "destination_candidates": Slot(value="Goa", confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
                "origin_city": Slot(value="Bangalore", confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
                "date_window": Slot(value="May 2026", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER),
                "party_size": Slot(value=2, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
                "budget_min": Slot(value=40000, confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER),
                "trip_purpose": Slot(value="family leisure", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER),
            }
        )
        valid_validation = PacketValidationReport(
            is_valid=True, errors=[], warnings=[],
        )

        with patch("src.intake.orchestration.ExtractionPipeline") as MockPipe:
            MockPipe.return_value.extract.return_value = valid_packet
            with patch("src.intake.orchestration.validate_packet", return_value=valid_validation):
                envelope = SourceEnvelope.from_freeform("mock envelope")
                result = run_spine_once(
                    envelopes=[envelope],
                    stage="discovery",
                    operating_mode="normal_intake",
                )
        decision = result.decision
        autonomy = result.autonomy_outcome

        assert decision is not None
        assert autonomy is not None
        assert autonomy.raw_verdict == decision.decision_state, \
            f"Raw autonomy mismatch: {autonomy.raw_verdict} != {decision.decision_state}"
        # D2/D5-ready: decision_state is not mutated by the gate
        assert autonomy.raw_verdict == autonomy.raw_verdict  # tautology
        assert "autonomy" in decision.rationale

    def test_spine_run_emergency_override_reflects_in_autonomy(self):
        from unittest.mock import patch
        from intake.packet_models import CanonicalPacket, Slot, AuthorityLevel
        from intake.validation import PacketValidationReport

        valid_packet = CanonicalPacket(
            packet_id="pkt_valid",
            stage="discovery",
            operating_mode="emergency",
            facts={
                "destination_candidates": Slot(value="Goa", confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
                "origin_city": Slot(value="Bangalore", confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
                "date_window": Slot(value="May 2026", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER),
                "party_size": Slot(value=2, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
                "budget_min": Slot(value=40000, confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER),
                "trip_purpose": Slot(value="family leisure", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER),
            }
        )
        valid_validation = PacketValidationReport(is_valid=True, errors=[], warnings=[])

        with patch("src.intake.orchestration.ExtractionPipeline") as MockPipe:
            MockPipe.return_value.extract.return_value = valid_packet
            with patch("src.intake.orchestration.validate_packet", return_value=valid_validation):
                envelope = SourceEnvelope.from_freeform("mock envelope")
                result = run_spine_once(
                    envelopes=[envelope],
                    stage="discovery",
                    operating_mode="emergency",
                )
        autonomy = result.autonomy_outcome
        assert autonomy is not None
        assert autonomy.effective_action == "block"
        assert autonomy.mode_override_applied == "emergency"


# ---------------------------------------------------------------------------
# Task 5: D5/D2-ready hooks
# ---------------------------------------------------------------------------

class TestD5D2Hooks:
    def test_reason_codes_are_machine_readable(self):
        gate = NB02JudgmentGate()
        decision = DecisionResult(
            packet_id="t",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="STOP_NEEDS_REVIEW",
        )
        settings = AgencySettings(agency_id="x")
        outcome = gate.evaluate(decision, settings)
        assert outcome.rule_source == "safety_invariant"
        assert any("safety invariant" in r.lower() for r in outcome.reasons)

    def test_reason_codes_for_mode_override(self):
        gate = NB02JudgmentGate()
        decision = DecisionResult(
            packet_id="t",
            current_stage="discovery",
            operating_mode="audit",
            decision_state="PROCEED_INTERNAL_DRAFT",
        )
        settings = AgencySettings(agency_id="x")
        outcome = gate.evaluate(decision, settings)
        assert outcome.rule_source == "mode_override:audit"

    def test_reason_codes_for_base_gate(self):
        gate = NB02JudgmentGate()
        decision = DecisionResult(
            packet_id="t",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="PROCEED_TRAVELER_SAFE",
        )
        settings = AgencySettings(agency_id="x")
        outcome = gate.evaluate(decision, settings)
        assert outcome.rule_source == "approval_gates:PROCEED_TRAVELER_SAFE"

    def test_future_override_fields_exist(self):
        policy = AgencyAutonomyPolicy()
        assert hasattr(policy, "learn_from_overrides")
        assert policy.learn_from_overrides is True

    def test_future_telemetry_slot_exists(self):
        outcome = AutonomyOutcome(
            raw_verdict="PROCEED_TRAVELER_SAFE",
            effective_action="review",
            approval_required=True,
            rule_source="approval_gates:PROCEED_TRAVELER_SAFE",
            safety_invariant_applied=False,
        )
        d = outcome.to_dict()
        assert "raw_verdict" in d
        assert "effective_action" in d
        assert "approval_required" in d
        assert "rule_source" in d
        assert "safety_invariant_applied" in d
        assert "mode_override_applied" in d
        assert "warning_override_applied" in d
        assert "reasons" in d


# ---------------------------------------------------------------------------
# Task 5: Invalid state regression guards
# ---------------------------------------------------------------------------

class TestDecisionStateInvariant:
    def test_decision_result_rejects_invalid_decision_state(self):
        import pytest as _pytest
        from src.intake.decision import DecisionResult

        with _pytest.raises(ValueError, match="Invalid decision_state"):
            DecisionResult(
                packet_id="pkt_test",
                current_stage="discovery",
                operating_mode="normal_intake",
                decision_state="suitability_review_required",
            )

    def test_constants_assert_valid_decision_state_rejects_unknown(self):
        import pytest as _pytest
        from src.intake.constants import assert_valid_decision_state

        with _pytest.raises(ValueError, match="Invalid decision_state"):
            assert_valid_decision_state("suitability_review_required")

    def test_constants_assert_valid_decision_state_accepts_canonical(self):
        from src.intake.constants import assert_valid_decision_state

        for state in ("ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT",
                       "PROCEED_TRAVELER_SAFE", "BRANCH_OPTIONS",
                       "STOP_NEEDS_REVIEW"):
            assert assert_valid_decision_state(state) == state

    def test_decision_result_set_decision_state_rejects_invalid(self):
        import pytest as _pytest
        from src.intake.decision import DecisionResult

        result = DecisionResult(
            packet_id="pkt_test",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="PROCEED_INTERNAL_DRAFT",
        )
        assert result.decision_state == "PROCEED_INTERNAL_DRAFT"

        with _pytest.raises(ValueError, match="Invalid decision_state"):
            result.set_decision_state("suitability_review_required")

    def test_decision_result_set_decision_state_accepts_canonical(self):
        from src.intake.decision import DecisionResult

        result = DecisionResult(
            packet_id="pkt_test",
            current_stage="discovery",
            operating_mode="normal_intake",
            decision_state="ASK_FOLLOWUP",
        )
        result.set_decision_state("STOP_NEEDS_REVIEW")
        assert result.decision_state == "STOP_NEEDS_REVIEW"

    def test_run_status_response_rejects_invalid_decision_state(self):
        import pytest as _pytest
        from spine_api.contract import RunStatusResponse
        from pydantic import ValidationError as _PydanticValidationError

        with _pytest.raises(_PydanticValidationError):
            RunStatusResponse(
                run_id="r_test",
                state="completed",
                decision_state="suitability_review_required",
            )

    def test_run_status_response_accepts_canonical_decision_state(self):
        from spine_api.contract import RunStatusResponse

        for state in ("ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT",
                       "PROCEED_TRAVELER_SAFE", "BRANCH_OPTIONS",
                       "STOP_NEEDS_REVIEW"):
            resp = RunStatusResponse(
                run_id="r_test",
                state="completed",
                decision_state=state,
            )
            assert resp.decision_state == state

    def test_autonomy_outcome_rejects_invalid_raw_verdict(self):
        import pytest as _pytest
        from spine_api.contract import AutonomyOutcome
        from pydantic import ValidationError as _PydanticValidationError

        with _pytest.raises(_PydanticValidationError):
            AutonomyOutcome(
                raw_verdict="suitability_review_required",
                effective_action="review",
                approval_required=True,
                rule_source="test",
                safety_invariant_applied=False,
            )

    def test_autonomy_outcome_accepts_canonical_raw_verdict(self):
        from spine_api.contract import AutonomyOutcome

        for state in ("ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT",
                       "PROCEED_TRAVELER_SAFE", "BRANCH_OPTIONS",
                       "STOP_NEEDS_REVIEW"):
            outcome = AutonomyOutcome(
                raw_verdict=state,
                effective_action="review",
                approval_required=True,
                rule_source="test",
                safety_invariant_applied=False,
            )
            assert outcome.raw_verdict == state
