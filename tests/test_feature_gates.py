"""
tests/test_feature_gates — Verify feature gate behavior across the pipeline.

Covers:
  - AiAgentSettings.is_enabled() helper (unit)
  - AgencyTier get_tier_limits() / tier_allows_feature() (unit)
  - run_spine_once: enable_auto_intake, enable_auto_proposal, enable_frontier_orchestration (integration)
  - run_frontier_orchestration: enable_checker_agent, enable_auto_negotiation (integration)
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from src.intake.config.agency_settings import (
    AiAgentSettings,
    AgencySettings,
    AgencyTier,
    get_tier_limits,
    tier_allows_feature,
)
from src.intake.packet_models import SourceEnvelope
from src.intake.orchestration import run_spine_once


# =============================================================================
# SECTION 1: AiAgentSettings.is_enabled() — unit tests
# =============================================================================


class TestAiAgentSettingsIsEnabled:
    """Unit tests for the is_enabled() helper on AiAgentSettings."""

    def test_default_settings_all_gates_true(self):
        ai = AiAgentSettings()
        for gate in (
            "enable_auto_intake",
            "enable_auto_shortlist",
            "enable_auto_proposal",
            "enable_auto_negotiation",
            "enable_frontier_orchestration",
            "enable_checker_agent",
            "enable_call_capture",
            "enable_document_extraction",
        ):
            assert ai.is_enabled(gate) is True, f"{gate} should default to True"

    def test_disabled_gate_returns_false(self):
        ai = AiAgentSettings(enable_checker_agent=False)
        assert ai.is_enabled("enable_checker_agent") is False
        # Other gates still True
        assert ai.is_enabled("enable_auto_intake") is True

    def test_unknown_gate_returns_true(self):
        """Unknown gate names default to True for backward compatibility."""
        ai = AiAgentSettings()
        assert ai.is_enabled("enable_nonexistent_gate") is True

    def test_multiple_disabled_gates(self):
        ai = AiAgentSettings(
            enable_auto_proposal=False,
            enable_checker_agent=False,
            enable_frontier_orchestration=False,
            enable_document_extraction=False,
            enable_call_capture=False,
        )
        assert ai.is_enabled("enable_auto_proposal") is False
        assert ai.is_enabled("enable_checker_agent") is False
        assert ai.is_enabled("enable_frontier_orchestration") is False
        assert ai.is_enabled("enable_document_extraction") is False
        assert ai.is_enabled("enable_call_capture") is False
        # These remain enabled
        assert ai.is_enabled("enable_auto_intake") is True
        assert ai.is_enabled("enable_auto_shortlist") is True


# =============================================================================
# SECTION 2: AgencyTier — unit tests
# =============================================================================


class TestAgencyTierGating:
    """Unit tests for tier-based feature limits."""

    def test_starter_disables_frontier_and_call_capture(self):
        limits = get_tier_limits(AgencyTier.STARTER)
        assert limits["enable_frontier_orchestration"] is False
        assert limits["enable_call_capture"] is False
        assert limits["enable_auto_negotiation"] is False
        assert limits["enable_auto_followup"] is False

    def test_pro_enables_frontier_and_negotiation(self):
        limits = get_tier_limits(AgencyTier.PRO)
        assert limits["enable_frontier_orchestration"] is True
        assert limits["enable_auto_negotiation"] is True
        assert limits["enable_call_capture"] is False  # still disabled at pro

    def test_enterprise_enables_everything(self):
        limits = get_tier_limits(AgencyTier.ENTERPRISE)
        assert limits["enable_call_capture"] is True
        assert limits["enable_frontier_orchestration"] is True
        assert limits["enable_auto_negotiation"] is True
        assert limits["enable_auto_followup"] is True

    def test_tier_allows_feature_true_when_enabled(self):
        assert tier_allows_feature(AgencyTier.ENTERPRISE, "enable_call_capture") is True
        assert tier_allows_feature(AgencyTier.PRO, "enable_frontier_orchestration") is True

    def test_tier_allows_feature_false_when_disabled(self):
        assert tier_allows_feature(AgencyTier.STARTER, "enable_call_capture") is False
        assert tier_allows_feature(AgencyTier.STARTER, "enable_frontier_orchestration") is False

    def test_tier_allows_feature_unknown_defaults_true(self):
        """Features not listed in tier limits default to allowed."""
        assert tier_allows_feature(AgencyTier.STARTER, "enable_auto_intake") is True
        assert tier_allows_feature(AgencyTier.STARTER, "nonexistent_feature") is True

    def test_tier_limits_starter_has_lower_value_threshold(self):
        limits = get_tier_limits(AgencyTier.STARTER)
        assert limits["require_owner_review_above_value"] == 1000.0
        limits_pro = get_tier_limits(AgencyTier.PRO)
        assert limits_pro["require_owner_review_above_value"] == 5000.0

    def test_tier_limits_trip_caps(self):
        assert get_tier_limits(AgencyTier.STARTER)["max_trips_per_month"] == 50
        assert get_tier_limits(AgencyTier.PRO)["max_trips_per_month"] == 500
        assert get_tier_limits(AgencyTier.ENTERPRISE)["max_trips_per_month"] is None  # unlimited


# =============================================================================
# SECTION 3: run_spine_once — feature gate integration tests
# =============================================================================


_RICH_ENVELOPE_TEXT = (
    "We are planning a family leisure trip from Bangalore to Singapore "
    "around 9th to 14th Feb 2026. We are 2 adults with budget around 3L "
    "and do not want a rushed itinerary."
)


def _make_envelope(text: str | None = None) -> list:
    """Build a SourceEnvelope list for spine runs.

    Uses a detailed default text that reliably passes NB01 intake gates.
    """
    return [SourceEnvelope.from_freeform(text or _RICH_ENVELOPE_TEXT)]


def _settings_with(**gate_overrides) -> AgencySettings:
    """Build AgencySettings with specific AiAgentSettings gate overrides."""
    ai = AiAgentSettings(**gate_overrides)
    return AgencySettings(agency_id="test-gate-agency", ai_agent=ai)


class TestSpineAutoIntakeGate:
    """enable_auto_intake gate: when disabled, extraction still runs but metadata flag is set."""

    def test_auto_intake_enabled_by_default(self):
        """Default settings: auto_intake is enabled, no flag in metadata."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(),
        )
        assert result is not None
        assert result.packet is not None
        # No auto_intake_disabled flag by default
        agent_flags = result.packet.metadata.get("agent_flags", {})
        assert "auto_intake_disabled" not in agent_flags

    def test_auto_intake_disabled_sets_metadata_flag(self):
        """When disabled, extraction still runs but metadata flag is set."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(enable_auto_intake=False),
        )
        assert result is not None
        assert result.packet is not None
        # Metadata flag should be set
        agent_flags = result.packet.metadata.get("agent_flags", {})
        assert agent_flags.get("auto_intake_disabled") is True
        # Packet should still be extracted (gate is signaling, not blocking)
        assert len(result.packet.facts) > 0


class TestSpineAutoProposalGate:
    """enable_auto_proposal gate: when disabled, a minimal strategy is returned."""

    def test_auto_proposal_enabled_returns_full_strategy(self):
        """Default: full session strategy with non-empty session_goal."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        assert result.strategy is not None
        # Full strategy should have a meaningful session_goal
        assert result.strategy.session_goal
        assert "Proposal generation disabled" not in result.strategy.session_goal

    def test_auto_proposal_disabled_returns_minimal_strategy(self):
        """When disabled, minimal strategy with disabled message is returned."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(enable_auto_proposal=False),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        assert result.strategy is not None
        # Minimal strategy should have the disabled message
        assert "Proposal generation disabled" in result.strategy.session_goal
        # Priority sequence should be empty
        assert result.strategy.priority_sequence == []
        # Risk flags should be empty
        assert result.strategy.risk_flags == []
        # Next action should mirror the decision state
        assert result.strategy.next_action == result.decision.decision_state

    def test_auto_proposal_disabled_still_produces_valid_result(self):
        """Even with minimal strategy, the full SpineResult should be valid."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(enable_auto_proposal=False),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        # Core fields are still populated
        assert result.packet is not None
        assert result.validation is not None
        assert result.decision is not None
        assert result.sanitized_view is not None
        assert result.leakage_result["is_safe"] is True


class TestSpineFrontierGate:
    """enable_frontier_orchestration gate: when disabled, frontier is skipped entirely."""

    def test_frontier_enabled_populates_result(self):
        """Default: frontier_result is populated."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        assert result.frontier_result is not None
        # sentiment_score should be a real value (0.0–1.0)
        assert 0.0 <= result.frontier_result.sentiment_score <= 1.0

    def test_frontier_disabled_returns_empty_result(self):
        """When disabled, frontier_result is a default empty result."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(enable_frontier_orchestration=False),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        assert result.frontier_result is not None
        # Empty result: no ghost triggered, default sentiment
        assert result.frontier_result.ghost_triggered is False
        assert result.frontier_result.ghost_workflow_id is None
        assert result.frontier_result.intelligence_hits == []
        assert result.frontier_result.negotiation_active is False

    def test_frontier_disabled_skips_subsystems(self):
        """When frontier is disabled, checker and negotiation should not run."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(enable_frontier_orchestration=False),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        # No manual audit since frontier was skipped
        assert result.frontier_result.requires_manual_audit is False
        assert result.frontier_result.negotiation_active is False

    def test_frontier_disabled_records_skip_in_decision_rationale(self):
        """Decision rationale should record that frontier was skipped."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(enable_frontier_orchestration=False),
        )
        frontier_rationale = result.decision.rationale.get("frontier", {})
        assert frontier_rationale.get("skipped") is True
        assert "disabled" in frontier_rationale.get("reason", "").lower()


# =============================================================================
# SECTION 4: run_frontier_orchestration — subsystem gate integration tests
# =============================================================================


def _make_frontier_test_packet(
    text: str = "Emergency trip, something went very wrong",
):
    """Build a minimal CanonicalPacket for frontier orchestration tests."""
    from src.intake.packet_models import CanonicalPacket, Slot

    packet = CanonicalPacket(packet_id="test-packet-001")
    packet.raw_note = text
    packet.facts["resolved_destination"] = Slot(value="Bali", authority_level="imported_structured", confidence=0.9)
    packet.facts["trip_purpose"] = Slot(value="emergency", authority_level="imported_structured", confidence=0.8)
    packet.operating_mode = "emergency"
    return packet


def _make_frontier_test_decision():
    """Build a minimal DecisionResult that triggers Ghost Concierge.

    Ghost Concierge triggers on operating_mode == 'emergency' (set on packet),
    so we use a valid decision_state here.
    """
    from src.intake.decision import DecisionResult

    return DecisionResult(
        packet_id="test-packet-001",
        current_stage="discovery",
        operating_mode="emergency",
        decision_state="STOP_NEEDS_REVIEW",
    )


class TestFrontierCheckerAgentGate:
    """enable_checker_agent gate: when disabled, checker audit is skipped."""

    def test_checker_agent_enabled_calls_audit(self):
        """When enabled, checker_agent.audit should be called during Ghost Concierge."""
        with patch("src.intake.frontier_orchestrator.checker_agent") as mock_checker:
            mock_checker.audit.return_value = MagicMock(
                requires_manual=False, reason="OK"
            )
            packet = _make_frontier_test_packet()
            decision = _make_frontier_test_decision()
            settings = _settings_with(enable_checker_agent=True)

            from src.intake.frontier_orchestrator import run_frontier_orchestration

            result = run_frontier_orchestration(packet, decision, agency_settings=settings)

            assert result.ghost_triggered is True
            mock_checker.audit.assert_called_once()

    def test_checker_agent_disabled_skips_audit(self):
        """When disabled, checker_agent.audit should NOT be called."""
        with patch("src.intake.frontier_orchestrator.checker_agent") as mock_checker:
            packet = _make_frontier_test_packet()
            decision = _make_frontier_test_decision()
            settings = _settings_with(enable_checker_agent=False)

            from src.intake.frontier_orchestrator import run_frontier_orchestration

            result = run_frontier_orchestration(packet, decision, agency_settings=settings)

            # Ghost Concierge should still trigger (it's not gated by checker)
            assert result.ghost_triggered is True
            # But checker audit was NOT called
            mock_checker.audit.assert_not_called()
            # No manual audit since checker was skipped
            assert result.requires_manual_audit is False

    def test_checker_agent_default_enabled(self):
        """By default, checker_agent is enabled."""
        with patch("src.intake.frontier_orchestrator.checker_agent") as mock_checker:
            mock_checker.audit.return_value = MagicMock(
                requires_manual=True, reason="Suspicious pattern"
            )
            packet = _make_frontier_test_packet()
            decision = _make_frontier_test_decision()
            settings = _settings_with()  # all defaults

            from src.intake.frontier_orchestrator import run_frontier_orchestration

            result = run_frontier_orchestration(packet, decision, agency_settings=settings)

            assert result.ghost_triggered is True
            mock_checker.audit.assert_called_once()
            assert result.requires_manual_audit is True
            assert result.audit_reason == "Suspicious pattern"


class TestFrontierNegotiationGate:
    """enable_auto_negotiation gate: when disabled, negotiation engine is skipped."""

    def test_negotiation_enabled_calls_service(self):
        """When enabled, negotiation_service.analyze_and_trigger should be called."""
        with patch("src.intake.frontier_orchestrator.negotiation_service") as mock_neg:
            mock_neg.analyze_and_trigger.return_value = [
                {"action": "haggle", "reason": "margin opportunity"}
            ]
            packet = _make_frontier_test_packet()
            decision = _make_frontier_test_decision()
            settings = _settings_with(enable_auto_negotiation=True)

            from src.intake.frontier_orchestrator import run_frontier_orchestration

            result = run_frontier_orchestration(packet, decision, agency_settings=settings)

            mock_neg.analyze_and_trigger.assert_called_once()
            assert result.negotiation_active is True
            assert len(result.negotiation_logs) == 1

    def test_negotiation_disabled_skips_service(self):
        """When disabled, negotiation_service should NOT be called."""
        with patch("src.intake.frontier_orchestrator.negotiation_service") as mock_neg:
            packet = _make_frontier_test_packet()
            decision = _make_frontier_test_decision()
            settings = _settings_with(enable_auto_negotiation=False)

            from src.intake.frontier_orchestrator import run_frontier_orchestration

            result = run_frontier_orchestration(packet, decision, agency_settings=settings)

            mock_neg.analyze_and_trigger.assert_not_called()
            assert result.negotiation_active is False
            assert result.negotiation_logs == []

    def test_negotiation_disabled_does_not_affect_other_subsystems(self):
        """Disabling negotiation should not prevent intelligence or specialty lookup."""
        with (
            patch("src.intake.frontier_orchestrator.negotiation_service") as mock_neg,
            patch("src.intake.frontier_orchestrator.intelligence_service") as mock_intel,
            patch("src.intake.frontier_orchestrator.SpecialtyKnowledgeService") as mock_spec,
            patch("src.intake.frontier_orchestrator._extract_destination", return_value="Bali"),
        ):
            mock_neg.analyze_and_trigger.return_value = []
            mock_intel.query_risks.return_value = [{"risk": "flood"}]
            mock_spec.identify_niche.return_value = []

            packet = _make_frontier_test_packet()
            decision = _make_frontier_test_decision()
            settings = _settings_with(enable_auto_negotiation=False)

            from src.intake.frontier_orchestrator import run_frontier_orchestration

            result = run_frontier_orchestration(packet, decision, agency_settings=settings)

            # Negotiation skipped
            mock_neg.analyze_and_trigger.assert_not_called()
            assert result.negotiation_active is False
            # Intelligence and specialty still ran
            mock_intel.query_risks.assert_called_once()
            assert len(result.intelligence_hits) == 1


# =============================================================================
# SECTION 5: Combined gate interaction tests
# =============================================================================


class TestCombinedGates:
    """Tests that multiple gates interact correctly when combined."""

    def test_all_disabled_produces_valid_minimal_result(self):
        """Disabling all major gates should still produce a valid SpineResult."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(
                enable_auto_intake=False,
                enable_auto_proposal=False,
                enable_frontier_orchestration=False,
            ),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        assert result is not None
        assert result.packet is not None
        assert result.validation is not None
        assert result.decision is not None
        # Metadata flag
        assert result.packet.metadata.get("agent_flags", {}).get("auto_intake_disabled") is True
        # Minimal strategy
        assert "Proposal generation disabled" in result.strategy.session_goal
        # Empty frontier
        assert result.frontier_result.ghost_triggered is False
        # Still safe
        assert result.leakage_result["is_safe"] is True

    def test_only_proposal_disabled_others_enabled(self):
        """Disabling only auto_proposal: extraction + frontier run normally."""
        result = run_spine_once(
            envelopes=_make_envelope(),
            stage="discovery",
            agency_settings=_settings_with(enable_auto_proposal=False),
        )
        assert not result.early_exit, f"NB01 gate escalated: {result.early_exit_reason}"
        # Extraction ran normally (no flag)
        agent_flags = result.packet.metadata.get("agent_flags", {})
        assert "auto_intake_disabled" not in agent_flags
        # Frontier ran (sentiment computed)
        assert result.frontier_result is not None
        assert 0.0 <= result.frontier_result.sentiment_score <= 1.0
        # But strategy is minimal
        assert "Proposal generation disabled" in result.strategy.session_goal
