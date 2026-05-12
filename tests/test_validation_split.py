"""
test_validation_split.py — Unit tests for P1.5 validation semantics split.

Tests the stage-aware validate_packet() and NB01CompletionGate
with three-tier verdict system (PROCEED / DEGRADE / ESCALATE).

Run:
    pytest tests/test_validation_split.py -v
"""

import pytest
from src.intake.validation import (
    validate_packet,
    INTAKE_MINIMUM,
    QUOTE_READY,
    DISCOVERY_MVB,
    PacketValidationReport,
    ValidationIssue,
)
from src.intake.gates import NB01CompletionGate, GateVerdict, GateResult
from src.intake.packet_models import CanonicalPacket, Slot, AuthorityLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_packet(facts: dict) -> CanonicalPacket:
    """Create a minimal valid packet with given facts."""
    pkt = CanonicalPacket(packet_id="test-pkt-1")
    for name, (value, confidence) in facts.items():
        pkt.set_fact(name, Slot(
            value=value,
            confidence=confidence,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        ))
    return pkt


FULL_FACTS = {
    "destination_candidates": (["Singapore"], 0.9),
    "origin_city": ("Mumbai", 0.9),
    "date_window": ("9-14 Feb", 0.8),
    "party_size": (4, 0.7),
    "budget_raw_text": ("1.5L INR", 0.6),
    "trip_purpose": ("family leisure", 0.8),
}

INTAKE_ONLY_FACTS = {
    "destination_candidates": (["Singapore"], 0.9),
    "date_window": ("9-14 Feb", 0.8),
}

gate = NB01CompletionGate()


# =============================================================================
# INTAKE_MINIMUM / QUOTE_READY / DISCOVERY_MVB constants
# =============================================================================

class TestConstants:
    def test_intake_minimum_has_two_fields(self):
        assert len(INTAKE_MINIMUM) == 2
        assert "destination_candidates" in INTAKE_MINIMUM
        assert "date_window" in INTAKE_MINIMUM

    def test_quote_ready_has_six_fields(self):
        assert len(QUOTE_READY) == 6
        for f in ["destination_candidates", "origin_city", "date_window",
                  "party_size", "budget_raw_text", "trip_purpose"]:
            assert f in QUOTE_READY, f"Missing {f}"

    def test_discovery_mvb_is_quote_ready_alias(self):
        assert DISCOVERY_MVB is QUOTE_READY
        assert DISCOVERY_MVB == QUOTE_READY


# =============================================================================
# Stage-aware validate_packet
# =============================================================================

class TestValidatePacketStageDiscovery:
    """stage='discovery': intake-minimum errors, quote-ready extras = warnings."""

    def test_all_fields_present(self):
        pkt = _make_packet(FULL_FACTS)
        report = validate_packet(pkt, stage="discovery")
        assert report.is_valid is True
        assert report.error_count == 0
        assert report.warning_count == 0

    def test_intake_only_facts_valid_with_warnings(self):
        pkt = _make_packet(INTAKE_ONLY_FACTS)
        report = validate_packet(pkt, stage="discovery")
        assert report.is_valid is True
        assert report.error_count == 0
        assert report.warning_count == 4
        warning_codes = {w.code for w in report.warnings}
        assert warning_codes == {"QUOTE_READY_INCOMPLETE"}

    def test_missing_destination_is_error(self):
        pkt = _make_packet({"date_window": ("9-14 Feb", 0.8)})
        report = validate_packet(pkt, stage="discovery")
        assert report.is_valid is False
        assert report.error_count == 1
        assert report.errors[0].code == "MVB_MISSING"
        assert report.errors[0].field == "destination_candidates"

    def test_missing_date_window_is_error(self):
        pkt = _make_packet({"destination_candidates": (["Singapore"], 0.9)})
        report = validate_packet(pkt, stage="discovery")
        assert report.is_valid is False
        assert report.error_count == 1
        assert report.errors[0].code == "MVB_MISSING"
        assert report.errors[0].field == "date_window"

    def test_no_facts_both_errors(self):
        pkt = CanonicalPacket(packet_id="empty")
        report = validate_packet(pkt, stage="discovery")
        assert report.is_valid is False
        assert report.error_count == 2
        missing = {e.field for e in report.errors}
        assert missing == {"destination_candidates", "date_window"}


class TestValidatePacketStageShortlist:
    """stage='shortlist': full QUOTE_READY is required as errors."""

    def test_all_fields_present(self):
        pkt = _make_packet(FULL_FACTS)
        report = validate_packet(pkt, stage="shortlist")
        assert report.is_valid is True
        assert report.error_count == 0

    def test_intake_only_has_errors(self):
        pkt = _make_packet(INTAKE_ONLY_FACTS)
        report = validate_packet(pkt, stage="shortlist")
        assert report.is_valid is False
        assert report.error_count == 4  # origin_city, party_size, budget_raw_text, trip_purpose
        error_codes = {e.code for e in report.errors}
        assert error_codes == {"MVB_MISSING"}
        # No QUOTE_READY_INCOMPLETE warnings at shortlist stage
        warning_codes = {w.code for w in report.warnings}
        assert "QUOTE_READY_INCOMPLETE" not in warning_codes


class TestValidatePacketStageProposal:
    """stage='proposal': same as shortlist — full QUOTE_READY required."""

    def test_intake_only_fails(self):
        pkt = _make_packet(INTAKE_ONLY_FACTS)
        report = validate_packet(pkt, stage="proposal")
        assert report.is_valid is False
        assert report.error_count == 4


# =============================================================================
# NB01CompletionGate — three verdicts
# =============================================================================

class TestNB01Gate:
    """NB01 gate returns PROCEED / DEGRADE / ESCALATE."""

    def test_all_fields_proceed(self):
        pkt = _make_packet(FULL_FACTS)
        report = validate_packet(pkt, stage="discovery")
        gr = gate.evaluate(pkt, report)
        assert gr.verdict == GateVerdict.PROCEED
        assert gr.score > 0.5

    def test_intake_only_degrade(self):
        pkt = _make_packet(INTAKE_ONLY_FACTS)
        report = validate_packet(pkt, stage="discovery")
        gr = gate.evaluate(pkt, report)
        assert gr.verdict == GateVerdict.DEGRADE
        assert "Intake minimum met" in " ".join(gr.reasons)
        assert "Quote-ready fields are incomplete" in " ".join(gr.reasons)

    def test_missing_destination_escalate(self):
        pkt = _make_packet({"date_window": ("9-14 Feb", 0.8)})
        report = validate_packet(pkt, stage="discovery")
        gr = gate.evaluate(pkt, report)
        assert gr.verdict == GateVerdict.ESCALATE
        assert gr.score == 0.0
        assert gr.reasons == ["Structural validation failed (1 error)"]

    def test_empty_packet_escalate(self):
        pkt = CanonicalPacket(packet_id="empty")
        report = validate_packet(pkt, stage="discovery")
        gr = gate.evaluate(pkt, report)
        assert gr.verdict == GateVerdict.ESCALATE
        assert gr.reasons == ["Structural validation failed (2 errors)"]

    def test_shortlist_stage_intake_only_escalate(self):
        pkt = _make_packet(INTAKE_ONLY_FACTS)
        report = validate_packet(pkt, stage="shortlist")
        gr = gate.evaluate(pkt, report)
        assert gr.verdict == GateVerdict.ESCALATE


# =============================================================================
# GateVerdict enum values
# =============================================================================

class TestGateVerdict:
    def test_enum_values(self):
        assert GateVerdict.PROCEED.value == "proceed"
        assert GateVerdict.RETRY.value == "retry"
        assert GateVerdict.ESCALATE.value == "escalate"
        assert GateVerdict.DEGRADE.value == "degrade"

    def test_all_verdicts_distinct(self):
        values = [v.value for v in GateVerdict]
        assert len(values) == len(set(values))


# =============================================================================
# PacketValidationReport properties
# =============================================================================

class TestValidationReport:
    def test_error_and_warning_count(self):
        pkt = _make_packet(INTAKE_ONLY_FACTS)
        report = validate_packet(pkt, stage="discovery")
        assert report.error_count == 0
        assert report.warning_count == 4

    def test_is_valid_false_with_errors(self):
        pkt = _make_packet({"date_window": ("Jan", 0.8)})
        report = validate_packet(pkt, stage="discovery")
        assert report.is_valid is False
        assert report.error_count == 1

    def test_to_dict_like(self):
        pkt = _make_packet(FULL_FACTS)
        report = validate_packet(pkt, stage="discovery")
        d = {
            "is_valid": report.is_valid,
            "errors": report.errors,
            "warnings": report.warnings,
            "ambiguity_report": report.ambiguity_report,
            "evidence_coverage": report.evidence_coverage,
        }
        assert d["is_valid"] is True
        assert len(d["errors"]) == 0

    def test_repr(self):
        pkt = _make_packet(FULL_FACTS)
        report = validate_packet(pkt, stage="discovery")
        r = repr(report)
        assert "PacketValidationReport" in r
