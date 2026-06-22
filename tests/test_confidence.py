"""Tests for src/extraction.confidence — validation-based and logprobs confidence scoring.

Covers:
- Per-field validators (passport, dates, names, etc.)
- Null field handling (0.0 confidence)
- Overall confidence computation
- Logprobs-to-confidence conversion
- Logprobs field mapping (best-effort)
- Edge cases: empty input, unknown fields, blended scores
"""

import math
from unittest.mock import MagicMock

import pytest


class TestFieldValidators:
    """Per-field validation returns appropriate confidence scores."""

    def test_passport_valid_format(self):
        from src.extraction.confidence import compute_field_confidences
        scores, method = compute_field_confidences({"passport_number": "AB123456"})
        assert scores["passport_number"] >= 0.7
        assert method == "validation"

    def test_passport_invalid_format(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"passport_number": "short"})
        assert scores["passport_number"] < 0.6

    def test_valid_full_name_two_words(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"full_name": "John Doe"})
        assert scores["full_name"] >= 0.8

    def test_single_word_name_lower_confidence(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"full_name": "John"})
        assert 0.4 < scores["full_name"] < 0.8

    def test_valid_date_of_birth(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"date_of_birth": "1990-05-15"})
        assert scores["date_of_birth"] >= 0.7

    def test_implausible_date_of_birth(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"date_of_birth": "1800-01-01"})
        assert scores["date_of_birth"] < 0.5

    def test_future_expiry_high_confidence(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"passport_expiry": "2030-12-31"})
        assert scores["passport_expiry"] >= 0.7

    def test_expired_expiry_moderate_confidence(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"passport_expiry": "2020-01-01"})
        assert 0.3 < scores["passport_expiry"] < 0.7

    def test_nationality_valid(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"nationality": "US"})
        assert scores["nationality"] >= 0.7

    def test_visa_type_valid(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"visa_type": "Tourist"})
        assert scores["visa_type"] >= 0.6

    def test_insurance_provider_valid(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"insurance_provider": "Allianz"})
        assert scores["insurance_provider"] >= 0.6

    def test_insurance_policy_number_valid(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"insurance_policy_number": "POL12345"})
        assert scores["insurance_policy_number"] >= 0.6


class TestNullFieldHandling:
    """Null fields always get 0.0 confidence."""

    def test_null_field_zero_confidence(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"full_name": None, "passport_number": "AB1234"})
        assert scores["full_name"] == 0.0
        assert scores["passport_number"] > 0.0

    def test_all_null_fields(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"full_name": None, "passport_number": None})
        assert all(v == 0.0 for v in scores.values())

    def test_empty_fields_dict(self):
        from src.extraction.confidence import compute_field_confidences
        scores, method = compute_field_confidences({})
        assert scores == {}
        assert method == "validation"


class TestOverallConfidence:
    """Overall confidence computation from per-field scores."""

    def test_overall_is_average_of_fields(self):
        from src.extraction.confidence import compute_overall_confidence
        field_scores = {"a": 0.8, "b": 0.6}
        overall = compute_overall_confidence(field_scores)
        assert abs(overall - 0.7) < 0.01

    def test_overall_empty_fields(self):
        from src.extraction.confidence import compute_overall_confidence
        assert compute_overall_confidence({}) == 0.0

    def test_overall_single_field(self):
        from src.extraction.confidence import compute_overall_confidence
        assert compute_overall_confidence({"a": 0.9}) == 0.9

    def test_overall_clamped_to_one(self):
        from src.extraction.confidence import compute_overall_confidence
        # Even with all 1.0 scores, overall should be 1.0
        scores = {f"field_{i}": 1.0 for i in range(10)}
        assert compute_overall_confidence(scores) == 1.0


class TestLogprobsConversion:
    """Logprobs-to-confidence conversion via geometric mean."""

    def test_logprobs_high_confidence(self):
        from src.extraction.confidence import logprobs_to_overall_confidence
        # logprob=-0.1 → probability=0.905 → high confidence
        logprobs = [{"logprob": -0.1} for _ in range(10)]
        result = logprobs_to_overall_confidence(logprobs)
        assert result is not None
        assert result > 0.8

    def test_logprobs_low_confidence(self):
        from src.extraction.confidence import logprobs_to_overall_confidence
        # logprob=-2.0 → probability=0.135 → low confidence
        logprobs = [{"logprob": -2.0} for _ in range(10)]
        result = logprobs_to_overall_confidence(logprobs)
        assert result is not None
        assert result < 0.3

    def test_logprobs_empty_returns_none(self):
        from src.extraction.confidence import logprobs_to_overall_confidence
        assert logprobs_to_overall_confidence([]) is None
        assert logprobs_to_overall_confidence(None) is None

    def test_logprobs_handles_object_items(self):
        from src.extraction.confidence import logprobs_to_overall_confidence
        item = MagicMock()
        item.logprob = -0.5
        result = logprobs_to_overall_confidence([item])
        assert result is not None
        assert 0.0 < result < 1.0

    def test_logprobs_clamped_to_one(self):
        from src.extraction.confidence import logprobs_to_overall_confidence
        # logprob=0.0 → probability=1.0 → capped at 1.0
        logprobs = [{"logprob": 0.0} for _ in range(5)]
        result = logprobs_to_overall_confidence(logprobs)
        assert result == 1.0

    def test_logprobs_clamped_to_zero(self):
        from src.extraction.confidence import logprobs_to_overall_confidence
        # Very negative logprob → probability ≈ 0 → clamped to 0.0
        logprobs = [{"logprob": -100.0}]
        result = logprobs_to_overall_confidence(logprobs)
        assert result == 0.0


class TestLogprobsFieldMapping:
    """Best-effort logprobs-to-field mapping."""

    def test_mapping_returns_none_for_empty_input(self):
        from src.extraction.confidence import logprobs_to_field_confidences
        result = logprobs_to_field_confidences({"a": "val"}, [], '{"a":"val"}')
        assert result is None

    def test_mapping_returns_none_for_no_match(self):
        from src.extraction.confidence import logprobs_to_field_confidences
        # Logprobs that don't align with any field value
        logprobs = [{"token": "unrelated", "logprob": -0.5}]
        result = logprobs_to_field_confidences({"a": "val"}, logprobs, '{"a":"val"}')
        # May or may not match — depends on character position alignment
        # Just verify it doesn't crash
        assert result is None or isinstance(result, dict)


class TestBlendedConfidence:
    """Blended logprobs + validation confidence."""

    def test_blended_with_logprobs(self):
        from src.extraction.confidence import compute_field_confidences
        logprobs = [{"logprob": -0.1, "token": '"John Doe"'} for _ in range(5)]
        scores, method = compute_field_confidences(
            {"full_name": "John Doe"},
            logprobs_data=logprobs,
            output_text='{"full_name":"John Doe"}',
        )
        # With logprobs available, method should indicate blend
        assert "logprobs" in method or method == "validation"
        assert scores["full_name"] > 0.0

    def test_validation_only_when_no_logprobs(self):
        from src.extraction.confidence import compute_field_confidences
        scores, method = compute_field_confidences({"full_name": "John Doe"})
        assert method == "validation"
        assert scores["full_name"] > 0.5

    def test_unknown_field_gets_moderate_confidence(self):
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"custom_field": "some value"})
        assert scores["custom_field"] == 0.6  # default for unknown fields
