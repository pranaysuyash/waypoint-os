"""
test_passport_gating — Stage-gated passport/visa extraction + readiness signals.

Run: uv run pytest tests/test_passport_gating.py -v
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from intake.extractors import (
    ExtractionPipeline,
    _extract_passport_visa,
    _extract_passport_visa_gated,
    VISA_PASSPORT_CONCERN_TERMS,
)
from intake.packet_models import SourceEnvelope
from intake.readiness import compute_readiness


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_pipeline(text: str, stage: str = "discovery") -> object:
    """Run extraction pipeline on freeform text with the given stage."""
    pipeline = ExtractionPipeline()
    envelope = SourceEnvelope.from_freeform(text)
    return pipeline.extract([envelope], stage=stage)


PASSPORT_TEXT = (
    "We are planning a trip to Thailand. Our passports are valid until March 2029. "
    "We need a visa for Thailand. Family of 4 from Bangalore."
)

NO_PASSPORT_TEXT = (
    "Planning a trip to Goa from Bangalore for 2 adults in May 2026. "
    "Budget around 40000."
)


# ---------------------------------------------------------------------------
# 1. _extract_passport_visa_gated unit tests
# ---------------------------------------------------------------------------

class TestExtractPassportVisaGated:
    def test_proposal_returns_full_extraction(self):
        result = _extract_passport_visa_gated(PASSPORT_TEXT, "proposal")
        assert "passport_status" in result
        assert "visa_status" in result

    def test_booking_returns_full_extraction(self):
        result = _extract_passport_visa_gated(PASSPORT_TEXT, "booking")
        assert "passport_status" in result
        assert "visa_status" in result

    def test_discovery_with_concern_returns_signal(self):
        result = _extract_passport_visa_gated(PASSPORT_TEXT, "discovery")
        assert result == {"visa_concerns_present": True}

    def test_shortlist_with_concern_returns_signal(self):
        result = _extract_passport_visa_gated(PASSPORT_TEXT, "shortlist")
        assert result == {"visa_concerns_present": True}

    def test_discovery_no_concern_returns_empty(self):
        result = _extract_passport_visa_gated(NO_PASSPORT_TEXT, "discovery")
        assert result == {}

    def test_shortlist_no_concern_returns_empty(self):
        result = _extract_passport_visa_gated(NO_PASSPORT_TEXT, "shortlist")
        assert result == {}


# ---------------------------------------------------------------------------
# 2. Pipeline integration: discovery/shortlist → derived_signals
# ---------------------------------------------------------------------------

class TestDiscoveryDerivedSignals:
    def test_discovery_passport_text_signal_in_derived_signals(self):
        packet = _run_pipeline(PASSPORT_TEXT, stage="discovery")
        assert "visa_concerns_present" in packet.derived_signals
        assert packet.derived_signals["visa_concerns_present"].value is True

    def test_discovery_passport_text_not_in_facts(self):
        packet = _run_pipeline(PASSPORT_TEXT, stage="discovery")
        assert "passport_status" not in packet.facts
        assert "visa_status" not in packet.facts

    def test_shortlist_passport_text_signal_in_derived_signals(self):
        packet = _run_pipeline(PASSPORT_TEXT, stage="shortlist")
        assert "visa_concerns_present" in packet.derived_signals
        assert packet.derived_signals["visa_concerns_present"].value is True

    def test_shortlist_passport_text_not_in_facts(self):
        packet = _run_pipeline(PASSPORT_TEXT, stage="shortlist")
        assert "passport_status" not in packet.facts
        assert "visa_status" not in packet.facts

    def test_discovery_no_keywords_signal_absent(self):
        packet = _run_pipeline(NO_PASSPORT_TEXT, stage="discovery")
        assert "visa_concerns_present" not in packet.derived_signals


# ---------------------------------------------------------------------------
# 3. Pipeline integration: proposal/booking → facts
# ---------------------------------------------------------------------------

class TestProposalBookingFullExtraction:
    def test_proposal_passport_in_facts(self):
        packet = _run_pipeline(PASSPORT_TEXT, stage="proposal")
        assert "passport_status" in packet.facts
        assert "visa_status" in packet.facts

    def test_booking_passport_in_facts(self):
        packet = _run_pipeline(PASSPORT_TEXT, stage="booking")
        assert "passport_status" in packet.facts
        assert "visa_status" in packet.facts

    def test_proposal_no_signal_in_derived_signals(self):
        packet = _run_pipeline(PASSPORT_TEXT, stage="proposal")
        assert "visa_concerns_present" not in packet.derived_signals


# ---------------------------------------------------------------------------
# 4. Readiness signals integration
# ---------------------------------------------------------------------------

class TestReadinessSignals:
    def test_readiness_signals_visa_concern_from_derived(self):
        """When visa_concerns_present is in derived_signals, readiness.signals picks it up."""
        packet = _run_pipeline(PASSPORT_TEXT, stage="discovery")
        result = compute_readiness(packet)
        d = result.to_dict()
        assert "signals" in d
        assert d["signals"]["visa_concerns_present"] is True

    def test_readiness_no_signal_when_absent(self):
        """When no visa_concerns_present, signals dict is empty or omitted."""
        packet = _run_pipeline(NO_PASSPORT_TEXT, stage="discovery")
        result = compute_readiness(packet)
        d = result.to_dict()
        # Either no signals key, or empty signals
        signals = d.get("signals", {})
        assert "visa_concerns_present" not in signals

    def test_readiness_no_raw_facts(self):
        """Readiness result never contains raw_facts."""
        packet = _run_pipeline(PASSPORT_TEXT, stage="discovery")
        result = compute_readiness(packet)
        d = result.to_dict()
        assert "raw_facts" not in d


# ---------------------------------------------------------------------------
# 5. Keyword coverage
# ---------------------------------------------------------------------------

class TestKeywordCoverage:
    @pytest.mark.parametrize("term", VISA_PASSPORT_CONCERN_TERMS)
    def test_each_keyword_triggers_signal(self, term):
        text = f"Planning a trip. We need to discuss {term} before we go."
        result = _extract_passport_visa_gated(text, "discovery")
        assert result == {"visa_concerns_present": True}
