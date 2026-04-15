"""
Tests for Block 3 of Spine Hardening Plan:
- Budget stretch parsing with explicit max extraction
- Geography false positives audit

Run: uv run python -m pytest tests/test_block3_extraction.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from intake.extractors import (
    _extract_budget_stretch_max,
    _extract_destination_candidates,
)
from intake.geography import is_known_destination


class TestBudgetStretchMaxExtraction:
    """Tests for explicit budget stretch max extraction."""

    def test_stretch_to_lakh(self):
        """"2L, can stretch to 2.5L" → 250000"""
        result = _extract_budget_stretch_max("Budget is 2L, can stretch to 2.5L")
        assert result == 250000, f"Expected 250000, got {result}"

    def test_stretch_up_to_amount(self):
        """"can go up to 3L" → 300000"""
        result = _extract_budget_stretch_max("We can go up to 3L if needed")
        assert result == 300000

    def test_stretch_until_amount(self):
        """"flexible until 250000" → 250000"""
        result = _extract_budget_stretch_max("Budget is flexible until 250000")
        assert result == 250000

    def test_stretch_with_k_suffix(self):
        """"can stretch to 50k" → 50000"""
        result = _extract_budget_stretch_max("Can stretch to 50k")
        assert result == 50000

    def test_no_explicit_max_returns_none(self):
        """"can stretch" without explicit max → None"""
        result = _extract_budget_stretch_max("Budget is 2L, can stretch if needed")
        assert result is None

    def test_flexible_without_amount(self):
        """"flexible budget" without max → None"""
        result = _extract_budget_stretch_max("We have a flexible budget")
        assert result is None

    def test_plain_number_large(self):
        """Large number without unit treated as base units"""
        result = _extract_budget_stretch_max("Can stretch to 300000")
        assert result == 300000


class TestGeographyFalsePositives:
    """Tests for geography false positive filtering."""

    def test_pronoun_we_rejected(self):
        """"We" should NOT be a valid destination."""
        assert not is_known_destination("We")

    def test_pronoun_i_rejected(self):
        """"I" should NOT be a valid destination."""
        assert not is_known_destination("I")

    def test_pronoun_my_rejected(self):
        """"My" should NOT be a valid destination."""
        assert not is_known_destination("My")

    def test_pronoun_our_rejected(self):
        """"Our" should NOT be a valid destination."""
        assert not is_known_destination("Our")

    def test_article_the_rejected(self):
        """"The" should NOT be a valid destination."""
        assert not is_known_destination("The")

    def test_valid_destination_still_accepted(self):
        """Valid destinations should still work."""
        assert is_known_destination("Singapore")
        assert is_known_destination("Japan")
        assert is_known_destination("Bangalore")

    def test_month_names_rejected(self):
        """Month names should be rejected."""
        assert not is_known_destination("March")
        assert not is_known_destination("May")

    def test_destination_extraction_filters_pronouns(self):
        """Extraction should filter pronoun false positives."""
        text = "We want to go somewhere nice from Bangalore"
        candidates, status, raw = _extract_destination_candidates(text)
        
        # Should not extract "We" as destination
        assert "We" not in candidates if candidates else True


class TestBudgetSoftCeilingFact:
    """Integration: budget_soft_ceiling fact is set when stretch max extracted."""

    def test_soft_ceiling_set_via_extraction(self):
        """Extraction pipeline sets budget_soft_ceiling when explicit max found."""
        from intake.extractors import ExtractionPipeline
        from intake.packet_models import SourceEnvelope
        
        text = "Looking for a trip to Singapore. Budget around 2L, can stretch to 2.5L. 4 people."
        env = SourceEnvelope.from_freeform(text, "test")
        packet = ExtractionPipeline().extract([env])
        
        # Should have budget_min
        assert "budget_min" in packet.facts
        
        # Should have budget_soft_ceiling
        assert "budget_soft_ceiling" in packet.facts
        assert packet.facts["budget_soft_ceiling"].value == 250000

    def test_no_soft_ceiling_without_explicit_max(self):
        """No budget_soft_ceiling when stretch has no explicit max."""
        from intake.extractors import ExtractionPipeline
        from intake.packet_models import SourceEnvelope
        
        text = "Looking for a trip to Singapore. Budget around 2L, can stretch. 4 people."
        env = SourceEnvelope.from_freeform(text, "test")
        packet = ExtractionPipeline().extract([env])
        
        # Should have budget_min
        assert "budget_min" in packet.facts
        
        # Should NOT have budget_soft_ceiling (no explicit max)
        assert "budget_soft_ceiling" not in packet.facts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])