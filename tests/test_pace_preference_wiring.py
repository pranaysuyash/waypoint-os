"""
test_pace_preference_wiring — Asserts pace_preference flows from
packet.facts into SuitabilityContext at both integration construction sites.

Background
----------
Before this fix, the capture UI accepted pace_preference and the spine
extractor wrote it to packet.facts["pace_preference"], but the two
SuitabilityContext() constructions in src/suitability/integration.py
never read it. The field was dead-letter at the pipeline-consumption layer.

This test pins the wiring end-to-end and locks in the vocabulary
normalization (capture {rushed, normal, relaxed} → suitability
{packed, balanced, relaxed}) per
Docs/research/DATA_CAPTURE_PACKET_NAMESPACING_DISCOVERY_2026-04-29.md.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pytest

from src.suitability import integration as integ
from src.suitability.integration import (
    _extract_pace_preference_from_packet,
    _normalize_pace_preference,
)


# ---------------------------------------------------------------------------
# Lightweight packet/fact stubs.
#
# We intentionally do not import CanonicalPacket because the wiring under test
# only depends on packet.facts being a Mapping[str, slot_with_.value]. Using
# the smallest possible stub keeps the test focused on the wiring contract,
# not on incidental packet construction details.
# ---------------------------------------------------------------------------


@dataclass
class _Slot:
    value: Any


class _StubPacket:
    """Minimal stand-in for CanonicalPacket exposing .facts as a dict."""

    def __init__(self, facts: dict[str, _Slot]):
        self.facts = facts


def _make_packet(**facts: Any) -> _StubPacket:
    return _StubPacket({k: _Slot(value=v) for k, v in facts.items()})


# ---------------------------------------------------------------------------
# Normalizer unit tests
# ---------------------------------------------------------------------------


class TestNormalizePacePreference:
    """Pure unit tests on the vocabulary normalizer."""

    def test_returns_none_for_none_input(self):
        assert _normalize_pace_preference(None) is None

    def test_returns_none_for_empty_string(self):
        assert _normalize_pace_preference("") is None
        assert _normalize_pace_preference("   ") is None

    def test_capture_vocabulary_rushed_maps_to_packed(self):
        assert _normalize_pace_preference("rushed") == "packed"

    def test_capture_vocabulary_normal_maps_to_balanced(self):
        assert _normalize_pace_preference("normal") == "balanced"

    def test_capture_vocabulary_relaxed_maps_to_relaxed(self):
        assert _normalize_pace_preference("relaxed") == "relaxed"

    def test_suitability_vocabulary_passes_through(self):
        # Suitability-native vocabulary should also be accepted unchanged so
        # that fixtures or future code paths that already use the model
        # vocabulary keep working.
        assert _normalize_pace_preference("balanced") == "balanced"
        assert _normalize_pace_preference("packed") == "packed"

    def test_case_and_whitespace_insensitive(self):
        assert _normalize_pace_preference("  RUSHED  ") == "packed"
        assert _normalize_pace_preference("Relaxed") == "relaxed"

    def test_unknown_value_clamps_to_balanced_and_logs(self, caplog):
        with caplog.at_level(logging.WARNING, logger="src.suitability.integration"):
            result = _normalize_pace_preference("hyperdrive")
        assert result == "balanced", (
            "Unknown values must clamp to the natural midpoint, not be dropped; "
            "see AGENTS.md Data Loss Prevention Pattern."
        )
        assert any(
            "unrecognized pace_preference" in record.message
            for record in caplog.records
        ), "Unknown values must emit a WARNING log for observability."

    def test_non_string_input_is_coerced_then_normalized(self):
        # Defensive: if a fact ever arrives as a non-string (e.g. an enum), the
        # normalizer should not crash.
        assert _normalize_pace_preference(123) == "balanced"


# ---------------------------------------------------------------------------
# Packet → context extractor tests
# ---------------------------------------------------------------------------


class TestExtractPacePreferenceFromPacket:
    def test_returns_none_when_fact_absent(self):
        packet = _make_packet()
        assert _extract_pace_preference_from_packet(packet) is None

    def test_returns_none_when_packet_lacks_facts(self):
        # Defensive against partial packets in early pipeline stages.
        class _BareObject:
            pass

        assert _extract_pace_preference_from_packet(_BareObject()) is None

    def test_returns_normalized_value_when_present(self):
        packet = _make_packet(pace_preference="rushed")
        assert _extract_pace_preference_from_packet(packet) == "packed"

    def test_already_normalized_value_passes_through(self):
        packet = _make_packet(pace_preference="balanced")
        assert _extract_pace_preference_from_packet(packet) == "balanced"


# ---------------------------------------------------------------------------
# End-to-end wiring tests against the real integration entry points
# ---------------------------------------------------------------------------


class TestSuitabilityContextWiring:
    """
    These tests prove that BOTH SuitabilityContext construction sites in
    src/suitability/integration.py read pace_preference from the packet.

    They use monkey-patching to capture the constructed context without
    rebuilding the entire spine pipeline.
    """

    def _packet_with_party_and_pace(self, pace_value: str) -> _StubPacket:
        # generate_suitability_risks() and assess_activity_suitability() both
        # short-circuit when there are no participants, so we must include
        # party_composition for the constructions under test to fire.
        return _StubPacket(
            facts={
                "party_composition": _Slot(value={"adults": 2}),
                "pace_preference": _Slot(value=pace_value),
            }
        )

    def _capture_constructed_context(self, monkeypatch):
        captured: list[Any] = []
        original_ctor = integ.SuitabilityContext

        def _spy(*args, **kwargs):
            ctx = original_ctor(*args, **kwargs)
            captured.append(ctx)
            return ctx

        monkeypatch.setattr(integ, "SuitabilityContext", _spy)
        return captured

    def test_generate_suitability_risks_passes_pace_to_context(self, monkeypatch):
        captured = self._capture_constructed_context(monkeypatch)
        packet = self._packet_with_party_and_pace("rushed")

        integ.generate_suitability_risks(packet)

        assert captured, "generate_suitability_risks should construct SuitabilityContext"
        ctx = captured[0]
        assert ctx.pace_preference == "packed", (
            "pace_preference='rushed' from capture vocabulary must reach "
            "SuitabilityContext as 'packed' (suitability vocabulary)."
        )

    def test_assess_activity_suitability_passes_pace_to_context(self, monkeypatch):
        captured = self._capture_constructed_context(monkeypatch)
        packet = self._packet_with_party_and_pace("relaxed")

        integ.assess_activity_suitability(packet)

        assert captured, "assess_activity_suitability should construct SuitabilityContext"
        ctx = captured[0]
        assert ctx.pace_preference == "relaxed", (
            "pace_preference='relaxed' must pass through to SuitabilityContext."
        )

    def test_missing_pace_preference_yields_none_not_error(self, monkeypatch):
        captured = self._capture_constructed_context(monkeypatch)
        # Same packet shape but no pace_preference fact at all.
        packet = _StubPacket(facts={"party_composition": _Slot(value={"adults": 2})})

        integ.generate_suitability_risks(packet)

        assert captured
        assert captured[0].pace_preference is None, (
            "Missing pace_preference must result in None on the context, "
            "preserving the existing behavior of contexts without the field."
        )

    def test_unknown_pace_value_is_clamped_in_context(self, monkeypatch, caplog):
        captured = self._capture_constructed_context(monkeypatch)
        packet = self._packet_with_party_and_pace("hyperdrive")

        with caplog.at_level(logging.WARNING, logger="src.suitability.integration"):
            integ.assess_activity_suitability(packet)

        assert captured
        assert captured[0].pace_preference == "balanced", (
            "Unknown pace values must be clamped to 'balanced', never dropped, "
            "per the data-loss-prevention pattern."
        )
        assert any(
            "unrecognized pace_preference" in record.message
            for record in caplog.records
        )


# ---------------------------------------------------------------------------
# Regression guard: end-to-end through the real intake extractor.
#
# This locks in the contract that a structured-import envelope carrying
# pace_preference produces a packet whose pace_preference fact, when read
# through our extractor, normalizes correctly. If the extractor ever stops
# writing pace_preference into packet.facts, this test fails loudly and
# signals that the discovery doc's Slice N1 namespace migration changed the
# storage location.
# ---------------------------------------------------------------------------


class TestExtractorIntegrationGuard:
    """
    Mirrors the call shape of tests/test_intake_pipeline_hardening.py to lock
    the wiring at the same boundary that production uses (SpineRunRequest →
    build_envelopes → run_spine_once → packet.facts).
    """

    def test_capture_request_pace_preference_reaches_normalized_context_value(self):
        from spine_api.contract import SpineRunRequest
        from spine_api.server import build_envelopes
        from src.intake.orchestration import run_spine_once

        request = SpineRunRequest(
            raw_note="Family trip to Singapore around Feb 2025",
            pace_preference="rushed",  # capture vocabulary
            stage="discovery",
            operating_mode="normal_intake",
        )
        envelopes = build_envelopes(request.model_dump(exclude_none=True))
        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
        )

        packet = result.packet
        assert packet is not None
        assert "pace_preference" in packet.facts, (
            "Extractor must continue to write pace_preference into "
            "packet.facts. If this fails, the namespace migration "
            "(Slice N1 in DATA_CAPTURE_PACKET_NAMESPACING_DISCOVERY_2026-04-29) "
            "may have moved the field — update the integration helper to read "
            "from the new home."
        )
        # Extractor stores the raw capture-vocabulary value verbatim.
        assert packet.facts["pace_preference"].value == "rushed"

        # The integration layer normalizes capture vocabulary → suitability
        # vocabulary on the way into SuitabilityContext.
        normalized = _extract_pace_preference_from_packet(packet)
        assert normalized == "packed"
