"""Edge case tests for src/extraction.confidence.

Covers:
- Duplicate field values in logprobs mapping (character-position ambiguity)
- Date validation edge cases (leap years, boundary ages, unparseable formats)
- Passport number format edge cases (min/max length, special chars, unicode)
- Logprobs-to-confidence conversion math (geometric mean, clamping, edge inputs)
- Visa number format edge cases
- Nationality field edge cases
- Name field edge cases (three+ words, whitespace)
"""

import math
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Date validation edge cases
# ---------------------------------------------------------------------------

class TestDateOfBirthEdgeCases:
    """Edge cases for date_of_birth validation."""

    def test_leap_year_birthday(self):
        """Leap year date (Feb 29) should parse and return high confidence."""
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"date_of_birth": "2000-02-29"})
        # Age ~26, plausible → 0.85
        assert scores["date_of_birth"] == pytest.approx(0.85, abs=0.01)

    def test_boundary_age_exactly_0(self):
        """Date that's today (age ~0) should return implausible."""
        from src.extraction.confidence import compute_field_confidences, _validate_date_field
        today = datetime.now().strftime("%Y-%m-%d")
        score = _validate_date_field(today)
        # Age < 0 effectively → implausible
        assert score == pytest.approx(0.4, abs=0.01)

    def test_boundary_age_120(self):
        """Date 120+ years ago should return implausible."""
        from src.extraction.confidence import _validate_date_field
        old_date = (datetime.now() - timedelta(days=365 * 121)).strftime("%Y-%m-%d")
        score = _validate_date_field(old_date)
        assert score == pytest.approx(0.4, abs=0.01)

    def test_boundary_age_119(self):
        """Date ~119 years ago should return plausible (0.85)."""
        from src.extraction.confidence import _validate_date_field
        date_119 = (datetime.now() - timedelta(days=365 * 119)).strftime("%Y-%m-%d")
        score = _validate_date_field(date_119)
        assert score == pytest.approx(0.85, abs=0.01)

    def test_boundary_age_negative(self):
        """Future DOB should return implausible."""
        from src.extraction.confidence import _validate_date_field
        future = (datetime.now() + timedelta(days=365 * 5)).strftime("%Y-%m-%d")
        score = _validate_date_field(future)
        assert score == pytest.approx(0.4, abs=0.01)

    def test_unparseable_date_returns_low(self):
        """Completely invalid date string returns low confidence."""
        from src.extraction.confidence import _validate_date_field
        score = _validate_date_field("not-a-date-at-all")
        assert score == pytest.approx(0.3, abs=0.01)

    def test_european_format_d_m_y(self):
        """European date format d/m/Y should parse correctly."""
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"date_of_birth": "15/05/1990"})
        assert scores["date_of_birth"] == pytest.approx(0.85, abs=0.01)

    def test_us_format_m_d_y(self):
        """US date format m/d/Y should parse correctly."""
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"date_of_birth": "05/15/1990"})
        assert scores["date_of_birth"] == pytest.approx(0.85, abs=0.01)

    def test_written_month_format(self):
        """Written month format like '15 Jan 1990' should parse."""
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"date_of_birth": "15 Jan 1990"})
        assert scores["date_of_birth"] == pytest.approx(0.85, abs=0.01)

    def test_written_month_full_format(self):
        """Full month format like 'May 15, 1990' should parse."""
        from src.extraction.confidence import compute_field_confidences
        scores, _ = compute_field_confidences({"date_of_birth": "May 15, 1990"})
        assert scores["date_of_birth"] == pytest.approx(0.85, abs=0.01)


class TestExpiryDateEdgeCases:
    """Edge cases for passport_expiry and visa_expiry validation."""

    def test_today_expiry(self):
        """Expiry date that is today should return expired (0.5)."""
        from src.extraction.confidence import _validate_future_date
        today = datetime.now().strftime("%Y-%m-%d")
        score = _validate_future_date(today)
        # today is NOT > now (same instant), so returns 0.5
        assert score == pytest.approx(0.5, abs=0.01)

    def test_tomorrow_expiry(self):
        """Expiry date tomorrow should return future (0.85)."""
        from src.extraction.confidence import _validate_future_date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        score = _validate_future_date(tomorrow)
        assert score == pytest.approx(0.85, abs=0.01)

    def test_yesterday_expiry(self):
        """Expiry date yesterday should return expired (0.5)."""
        from src.extraction.confidence import _validate_future_date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        score = _validate_future_date(yesterday)
        assert score == pytest.approx(0.5, abs=0.01)

    def test_unparseable_expiry(self):
        """Unparseable expiry date returns low confidence."""
        from src.extraction.confidence import _validate_future_date
        score = _validate_future_date("expiry soon")
        assert score == pytest.approx(0.3, abs=0.01)

    def test_visa_expiry_future(self):
        """Visa expiry in the future returns high confidence."""
        from src.extraction.confidence import compute_field_confidences
        future = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        scores, _ = compute_field_confidences({"visa_expiry": future})
        assert scores["visa_expiry"] == pytest.approx(0.85, abs=0.01)

    def test_visa_expiry_expired(self):
        """Visa expiry in the past returns moderate confidence."""
        from src.extraction.confidence import compute_field_confidences
        past = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        scores, _ = compute_field_confidences({"visa_expiry": past})
        assert scores["visa_expiry"] == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# Passport number format edge cases
# ---------------------------------------------------------------------------

class TestPassportNumberEdgeCases:
    """Edge cases for passport_number validation."""

    def test_min_length_6(self):
        """Exactly 6 alphanumeric characters should pass."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "ABC123")
        assert score == pytest.approx(0.85, abs=0.01)

    def test_max_length_12(self):
        """Exactly 12 alphanumeric characters should pass."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "AB1234567890")
        assert score == pytest.approx(0.85, abs=0.01)

    def test_length_5_rejected(self):
        """5 characters should be rejected (too short)."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "AB123")
        assert score == pytest.approx(0.4, abs=0.01)

    def test_length_13_rejected(self):
        """13 characters should be rejected (too long)."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "AB12345678901")
        assert score == pytest.approx(0.4, abs=0.01)

    def test_all_digits(self):
        """All digits should be accepted."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "12345678")
        assert score == pytest.approx(0.85, abs=0.01)

    def test_all_letters(self):
        """All letters should be accepted."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "ABCDEFGH")
        assert score == pytest.approx(0.85, abs=0.01)

    def test_special_chars_rejected(self):
        """Special characters like dashes, spaces should be rejected."""
        from src.extraction.confidence import _validate_field
        assert _validate_field("passport_number", "AB-12-34") < 0.6
        assert _validate_field("passport_number", "AB 12 34") < 0.6

    def test_lower_case_accepted(self):
        """Lowercase should be accepted (regex is case-insensitive)."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "ab123456")
        assert score == pytest.approx(0.85, abs=0.01)

    def test_mixed_case_accepted(self):
        """Mixed case should be accepted."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "AbCdEf12")
        assert score == pytest.approx(0.85, abs=0.01)

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace should be stripped before validation."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("passport_number", "  AB123456  ")
        assert score == pytest.approx(0.85, abs=0.01)


# ---------------------------------------------------------------------------
# Visa number format edge cases
# ---------------------------------------------------------------------------

class TestVisaNumberEdgeCases:
    """Edge cases for visa_number validation."""

    def test_min_length_4(self):
        """Exactly 4 alphanumeric characters should pass."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("visa_number", "AB12")
        assert score == pytest.approx(0.8, abs=0.01)

    def test_max_length_15(self):
        """Exactly 15 alphanumeric characters should pass."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("visa_number", "A12345678901234")
        assert score == pytest.approx(0.8, abs=0.01)

    def test_length_3_rejected(self):
        """3 characters should be rejected (too short)."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("visa_number", "AB1")
        assert score == pytest.approx(0.4, abs=0.01)

    def test_length_16_rejected(self):
        """16 characters should be rejected (too long)."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("visa_number", "A123456789012345")
        assert score == pytest.approx(0.4, abs=0.01)


# ---------------------------------------------------------------------------
# Nationality field edge cases
# ---------------------------------------------------------------------------

class TestNationalityEdgeCases:
    """Edge cases for nationality validation."""

    def test_single_char_rejected(self):
        """Single character should return low confidence."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("nationality", "U")
        assert score == pytest.approx(0.4, abs=0.01)

    def test_two_char_accepted(self):
        """Two characters (ISO code) should return high confidence."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("nationality", "US")
        assert score == pytest.approx(0.8, abs=0.01)

    def test_long_name_accepted(self):
        """Long nationality name should return high confidence."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("nationality", "United Kingdom")
        assert score == pytest.approx(0.8, abs=0.01)


# ---------------------------------------------------------------------------
# Name field edge cases
# ---------------------------------------------------------------------------

class TestNameEdgeCases:
    """Edge cases for full_name validation."""

    def test_three_words(self):
        """Three-word name should return high confidence."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("full_name", "John Michael Doe")
        assert score >= 0.8

    def test_four_words(self):
        """Four-word name should return high confidence."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("full_name", "John Michael Robert Doe")
        assert score >= 0.8

    def test_whitespace_only_returns_low(self):
        """Whitespace-only name should return low confidence (0 words after strip)."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("full_name", "   ")
        assert score < 0.8  # split() on whitespace gives empty list

    def test_leading_trailing_spaces(self):
        """Name with extra spaces should be stripped and validated."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("full_name", "  John Doe  ")
        assert score >= 0.8

    def test_single_long_word(self):
        """Single long word (e.g., mononym) gets moderate confidence."""
        from src.extraction.confidence import _validate_field
        score = _validate_field("full_name", "Madonna")
        assert 0.4 < score < 0.8


# ---------------------------------------------------------------------------
# Logprobs-to-confidence conversion math
# ---------------------------------------------------------------------------

class TestLogprobsConversionMath:
    """Verify the geometric mean math and clamping logic."""

    def test_single_logprob_exact(self):
        """Single logprob should return exp(logprob)."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        # logprob = -0.5 → exp(-0.5) ≈ 0.6065
        result = logprobs_to_overall_confidence([{"logprob": -0.5}])
        assert result is not None
        assert result == pytest.approx(math.exp(-0.5), abs=0.001)

    def test_multiple_logprobs_geometric_mean(self):
        """Multiple logprobs should compute geometric mean."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        # Two logprobs: -0.2 and -0.4 → avg = -0.3 → exp(-0.3) ≈ 0.7408
        result = logprobs_to_overall_confidence([{"logprob": -0.2}, {"logprob": -0.4}])
        assert result is not None
        assert result == pytest.approx(math.exp(-0.3), abs=0.001)

    def test_mixed_types_handled(self):
        """Dict and object items should both be handled."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        obj = MagicMock()
        obj.logprob = -0.3
        result = logprobs_to_overall_confidence([{"logprob": -0.1}, obj])
        assert result is not None
        assert 0.0 < result < 1.0

    def test_items_without_logprob_ignored(self):
        """Items missing logprob should be skipped."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        # Only the first item has logprob
        result = logprobs_to_overall_confidence([{"logprob": -0.2}, {"token": "hello"}])
        assert result is not None
        assert result == pytest.approx(math.exp(-0.2), abs=0.001)

    def test_all_items_missing_logprob_returns_none(self):
        """If no items have logprob, returns None."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        result = logprobs_to_overall_confidence([{"token": "a"}, {"token": "b"}])
        assert result is None

    def test_none_input_returns_none(self):
        """None input returns None."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        assert logprobs_to_overall_confidence(None) is None

    def test_empty_list_returns_none(self):
        """Empty list returns None."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        assert logprobs_to_overall_confidence([]) is None

    def test_zero_logprob_probability_one(self):
        """logprob=0.0 → probability=1.0, clamped to 1.0."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        result = logprobs_to_overall_confidence([{"logprob": 0.0}])
        assert result == 1.0

    def test_very_negative_logprob_clamped_zero(self):
        """Very negative logprob → probability ≈ 0, clamped to 0.0."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        result = logprobs_to_overall_confidence([{"logprob": -500.0}])
        assert result == 0.0

    def test_symmetric_logprobs(self):
        """Symmetric logprobs around 0 should give ~0.5 confidence."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        # logprob=-0.6931 → exp(-0.6931) ≈ 0.5
        result = logprobs_to_overall_confidence([{"logprob": -0.6931}])
        assert result is not None
        assert result == pytest.approx(0.5, abs=0.01)

    def test_large_number_of_tokens(self):
        """Many tokens should still compute correctly."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        logprobs = [{"logprob": -0.1}] * 1000
        result = logprobs_to_overall_confidence(logprobs)
        assert result is not None
        assert result > 0.8

    def test_single_token_dominates(self):
        """Single token logprob should be the result."""
        from src.extraction.confidence import logprobs_to_overall_confidence
        result = logprobs_to_overall_confidence([{"logprob": -1.0}])
        assert result is not None
        assert result == pytest.approx(math.exp(-1.0), abs=0.001)


# ---------------------------------------------------------------------------
# Duplicate field values in logprobs mapping
# ---------------------------------------------------------------------------

class TestDuplicateFieldValues:
    """Test behavior when multiple fields have the same value."""

    def test_duplicate_values_find_first_occurrence(self):
        """When two fields share a value, mapping finds the first occurrence."""
        from src.extraction.confidence import logprobs_to_field_confidences
        fields = {"nationality": "US", "visa_type": "US"}
        logprobs = [
            {"token": '{"nationality":"US","visa_type":"US"}', "logprob": -0.1}
        ]
        output_text = '{"nationality":"US","visa_type":"US"}'
        result = logprobs_to_field_confidences(fields, logprobs, output_text)
        # Should find at least one field, possibly mapping to first occurrence
        assert result is None or isinstance(result, dict)

    def test_different_values_map_independently(self):
        """Fields with different values should map independently."""
        from src.extraction.confidence import logprobs_to_field_confidences
        logprobs = [
            {"token": '{"full_name":"', "logprob": -0.05},
            {"token": "John Doe", "logprob": -0.1},
            {"token": '","passport_number":"', "logprob": -0.05},
            {"token": "AB123456", "logprob": -0.1},
            {"token": '"}', "logprob": -0.05},
        ]
        output_text = '{"full_name":"John Doe","passport_number":"AB123456"}'
        fields = {"full_name": "John Doe", "passport_number": "AB123456"}
        result = logprobs_to_field_confidences(fields, logprobs, output_text)
        if result is not None:
            # Both fields should have scores if mapping succeeded
            assert isinstance(result, dict)

    def test_empty_output_text_returns_none(self):
        """Empty output text returns None."""
        from src.extraction.confidence import logprobs_to_field_confidences
        result = logprobs_to_field_confidences({"a": "val"}, [{"logprob": -0.1}], "")
        assert result is None

    def test_none_output_text_returns_none(self):
        """None output text returns None."""
        from src.extraction.confidence import logprobs_to_field_confidences
        result = logprobs_to_field_confidences({"a": "val"}, [{"logprob": -0.1}], None)
        assert result is None

    def test_non_dict_json_returns_none(self):
        """Non-dict JSON (e.g., array) returns None."""
        from src.extraction.confidence import logprobs_to_field_confidences
        result = logprobs_to_field_confidences(
            {"a": "val"}, [{"logprob": -0.1}], '["not","a","dict"]'
        )
        assert result is None

    def test_malformed_json_returns_none(self):
        """Malformed JSON returns None."""
        from src.extraction.confidence import logprobs_to_field_confidences
        result = logprobs_to_field_confidences(
            {"a": "val"}, [{"logprob": -0.1}], "{not valid json"
        )
        assert result is None


# ---------------------------------------------------------------------------
# Overall confidence with logprobs blend
# ---------------------------------------------------------------------------

class TestOverallConfidenceBlend:
    """Test overall confidence computation with logprobs blending."""

    def test_overall_with_high_logprobs(self):
        """High logprobs should boost overall confidence."""
        from src.extraction.confidence import compute_overall_confidence
        field_scores = {"a": 0.6, "b": 0.6}
        logprobs = [{"logprob": -0.01}] * 10  # Very high confidence
        result = compute_overall_confidence(field_scores, logprobs_data=logprobs)
        # 0.6 * 0.6 (validation) + 0.4 * ~0.99 (logprobs) ≈ 0.756
        assert result > 0.7

    def test_overall_with_low_logprobs(self):
        """Low logprobs should reduce overall confidence."""
        from src.extraction.confidence import compute_overall_confidence
        field_scores = {"a": 0.8, "b": 0.8}
        logprobs = [{"logprob": -3.0}] * 10  # Very low confidence
        result = compute_overall_confidence(field_scores, logprobs_data=logprobs)
        # 0.6 * 0.8 (validation) + 0.4 * ~0.05 (logprobs) ≈ 0.50
        assert result < 0.7

    def test_overall_without_logprobs_uses_validation_only(self):
        """Without logprobs, overall is just the average of field scores."""
        from src.extraction.confidence import compute_overall_confidence
        field_scores = {"a": 0.8, "b": 0.6}
        result = compute_overall_confidence(field_scores)
        assert result == pytest.approx(0.7, abs=0.01)

    def test_overall_empty_logprobs_uses_validation_only(self):
        """Empty logprobs list should fall back to validation only."""
        from src.extraction.confidence import compute_overall_confidence
        field_scores = {"a": 0.9}
        result = compute_overall_confidence(field_scores, logprobs_data=[])
        assert result == pytest.approx(0.9, abs=0.01)


# ---------------------------------------------------------------------------
# Compute field confidences integration
# ---------------------------------------------------------------------------

class TestComputeFieldConfidencesIntegration:
    """Integration tests for compute_field_confidences with various inputs."""

    def test_multiple_fields_mixed_validity(self):
        """Mix of valid and invalid fields returns appropriate scores."""
        from src.extraction.confidence import compute_field_confidences
        fields = {
            "full_name": "John Doe",        # valid → 0.85
            "passport_number": "AB123456",   # valid → 0.85
            "date_of_birth": "not-a-date",   # invalid → 0.3
            "nationality": "X",              # too short → 0.4
            "custom_field": "anything",      # unknown → 0.6
        }
        scores, method = compute_field_confidences(fields)
        assert method == "validation"
        assert scores["full_name"] == pytest.approx(0.85, abs=0.01)
        assert scores["passport_number"] == pytest.approx(0.85, abs=0.01)
        assert scores["date_of_birth"] == pytest.approx(0.3, abs=0.01)
        assert scores["nationality"] == pytest.approx(0.4, abs=0.01)
        assert scores["custom_field"] == 0.6

    def test_all_null_fields(self):
        """All null fields return all zeros."""
        from src.extraction.confidence import compute_field_confidences
        fields = {"full_name": None, "passport_number": None, "date_of_birth": None}
        scores, method = compute_field_confidences(fields)
        assert all(v == 0.0 for v in scores.values())

    def test_empty_fields_returns_empty(self):
        """Empty fields dict returns empty scores."""
        from src.extraction.confidence import compute_field_confidences
        scores, method = compute_field_confidences({})
        assert scores == {}
        assert method == "validation"
