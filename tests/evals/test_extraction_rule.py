"""Tests for src/evals/audit/rules/extraction.py — per-field extraction eval."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.evals.audit.rules.extraction import (
    AggregateMetrics,
    ExtractionEvalReport,
    ExtractionFixture,
    FieldComparison,
    FieldMetrics,
    compare_fixture,
    load_golden_dataset,
    run_extraction_eval,
    values_match,
    _normalise,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixture(
    fixture_id: str = "test_001",
    document_type: str = "passport",
    expected: dict[str, str | None] | None = None,
    difficulty: str = "easy",
) -> ExtractionFixture:
    if expected is None:
        expected = {
            "full_name": "JOHN DOE",
            "date_of_birth": "01/01/1990",
            "passport_number": "AB123456",
            "passport_expiry": "01/01/2030",
            "nationality": "AMERICAN",
        }
    return ExtractionFixture(
        fixture_id=fixture_id,
        document_type=document_type,
        description="test fixture",
        difficulty=difficulty,
        expected_extracted_fields=expected,
        expected_field_count=len(expected),
        tags=["test"],
    )


# ---------------------------------------------------------------------------
# _normalise tests
# ---------------------------------------------------------------------------


class TestNormalise:
    def test_none_returns_none(self) -> None:
        assert _normalise(None) is None

    def test_lowercases(self) -> None:
        assert _normalise("JOHN DOE") == "john doe"

    def test_collapses_whitespace(self) -> None:
        assert _normalise("  JOHN   DOE  ") == "john doe"

    def test_preserves_internal_punctuation(self) -> None:
        assert _normalise("O'BRIEN") == "o'brien"

    def test_empty_string(self) -> None:
        assert _normalise("") == ""


# ---------------------------------------------------------------------------
# values_match tests
# ---------------------------------------------------------------------------


class TestValuesMatch:
    def test_both_none(self) -> None:
        assert values_match(None, None) is True

    def test_expected_none_actual_not(self) -> None:
        assert values_match(None, "hello") is False

    def test_expected_not_actual_none(self) -> None:
        assert values_match("hello", None) is False

    def test_exact_match_case_insensitive(self) -> None:
        assert values_match("JOHN DOE", "john doe") is True

    def test_exact_mismatch(self) -> None:
        assert values_match("JOHN DOE", "JANE DOE") is False

    def test_contains_match_substring(self) -> None:
        assert values_match("DOE", "JOHN DOE SR", mode="contains") is True

    def test_contains_match_reverse(self) -> None:
        assert values_match("JOHN DOE", "DOE", mode="contains") is True

    def test_contains_match_no_match(self) -> None:
        assert values_match("SMITH", "JOHN DOE", mode="contains") is False

    def test_whitespace_normalisation(self) -> None:
        assert values_match("  JOHN   DOE  ", "john doe") is True


# ---------------------------------------------------------------------------
# compare_fixture tests
# ---------------------------------------------------------------------------


class TestCompareFixture:
    def test_perfect_match(self) -> None:
        fixture = _fixture()
        actual = {
            "full_name": "JOHN DOE",
            "date_of_birth": "01/01/1990",
            "passport_number": "AB123456",
            "passport_expiry": "01/01/2030",
            "nationality": "AMERICAN",
        }
        comp = compare_fixture(fixture, actual)
        assert comp.all_fields_match is True
        assert comp.precision == 1.0
        assert comp.recall == 1.0
        assert comp.f1 == 1.0

    def test_missing_field_fn(self) -> None:
        fixture = _fixture()
        actual = {
            "full_name": "JOHN DOE",
            "date_of_birth": "01/01/1990",
            "passport_number": "AB123456",
            "passport_expiry": None,  # missing
            "nationality": "AMERICAN",
        }
        comp = compare_fixture(fixture, actual)
        assert comp.all_fields_match is False
        assert comp.recall < 1.0

        fn_fields = [c for c in comp.field_comparisons if c.match_type == "false_negative"]
        assert len(fn_fields) == 1
        assert fn_fields[0].field_name == "passport_expiry"

    def test_hallucinated_field_fp(self) -> None:
        fixture = _fixture()
        actual = {
            "full_name": "JOHN DOE",
            "date_of_birth": "01/01/1990",
            "passport_number": "AB123456",
            "passport_expiry": "01/01/2030",
            "nationality": "AMERICAN",
            "visa_type": "TOURIST",  # hallucinated
        }
        comp = compare_fixture(fixture, actual)
        fp_fields = [c for c in comp.field_comparisons if c.match_type == "false_positive"]
        assert len(fp_fields) == 1
        assert fp_fields[0].field_name == "visa_type"

    def test_null_match_both_absent(self) -> None:
        fixture = _fixture(expected={
            "full_name": None,
            "passport_number": "AB123456",
        })
        actual = {"full_name": None, "passport_number": "AB123456"}
        comp = compare_fixture(fixture, actual)
        null_matches = [c for c in comp.field_comparisons if c.match_type == "null_match"]
        assert len(null_matches) == 1

    def test_mismatch_wrong_value(self) -> None:
        fixture = _fixture()
        actual = {
            "full_name": "JANE SMITH",
            "date_of_birth": "01/01/1990",
            "passport_number": "AB123456",
            "passport_expiry": "01/01/2030",
            "nationality": "AMERICAN",
        }
        comp = compare_fixture(fixture, actual)
        mismatches = [c for c in comp.field_comparisons if c.match_type == "mismatch"]
        assert len(mismatches) == 1
        assert mismatches[0].field_name == "full_name"

    def test_contains_mode(self) -> None:
        fixture = _fixture(expected={
            "full_name": "BRITISH CITIZEN",
        })
        actual = {"full_name": "BRITISH CITIZEN (UNITED KINGDOM)"}
        comp = compare_fixture(fixture, actual, mode="contains")
        assert comp.all_fields_match is True

    def test_empty_actual_fields(self) -> None:
        fixture = _fixture()
        comp = compare_fixture(fixture, {})
        # All expected fields become false negatives
        fn_fields = [c for c in comp.field_comparisons if c.match_type == "false_negative"]
        assert len(fn_fields) == 5
        assert comp.recall == 0.0

    def test_empty_expected_fields(self) -> None:
        fixture = _fixture(expected={})
        actual = {"full_name": "JOHN DOE"}
        comp = compare_fixture(fixture, actual)
        fp_fields = [c for c in comp.field_comparisons if c.match_type == "false_positive"]
        assert len(fp_fields) == 1
        assert comp.precision == 0.0


# ---------------------------------------------------------------------------
# aggregate_comparisons tests
# ---------------------------------------------------------------------------


class TestAggregateComparisons:
    def test_perfect_aggregate(self) -> None:
        fixture = _fixture()
        actual = {
            "full_name": "JOHN DOE",
            "date_of_birth": "01/01/1990",
            "passport_number": "AB123456",
            "passport_expiry": "01/01/2030",
            "nationality": "AMERICAN",
        }
        comp = compare_fixture(fixture, actual)
        agg = run_extraction_eval([fixture], saved_results={"test_001": actual})
        assert agg.overall.overall_precision == 1.0
        assert agg.overall.overall_recall == 1.0
        assert agg.overall.fixture_accuracy == 1.0

    def test_mixed_fixtures(self) -> None:
        f1 = _fixture(fixture_id="f1")
        f2 = _fixture(fixture_id="f2")
        # f1: perfect, f2: missing nationality
        results = {
            "f1": {
                "full_name": "JOHN DOE",
                "date_of_birth": "01/01/1990",
                "passport_number": "AB123456",
                "passport_expiry": "01/01/2030",
                "nationality": "AMERICAN",
            },
            "f2": {
                "full_name": "JOHN DOE",
                "date_of_birth": "01/01/1990",
                "passport_number": "AB123456",
                "passport_expiry": "01/01/2030",
            },
        }
        report = run_extraction_eval([f1, f2], saved_results=results)
        assert report.total_fixtures == 2
        assert report.overall.overall_precision == 1.0
        assert report.overall.overall_recall < 1.0
        assert report.overall.fixture_accuracy == 0.5  # 1 of 2 perfect

    def test_by_document_type(self) -> None:
        passport = _fixture(fixture_id="p1", document_type="passport")
        visa = _fixture(
            fixture_id="v1",
            document_type="visa",
            expected={"full_name": "JOHN", "nationality": "US", "visa_type": "B1/B2",
                      "visa_number": "V123", "visa_expiry": "01/01/2030", "passport_number": "P123"},
        )
        results = {
            "p1": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456", "passport_expiry": "01/01/2030", "nationality": "AMERICAN",
            },
            "v1": {
                "full_name": "JOHN", "nationality": "US", "visa_type": "B1/B2",
                "visa_number": "V123", "visa_expiry": "01/01/2030", "passport_number": "P123",
            },
        }
        report = run_extraction_eval([passport, visa], saved_results=results)
        assert "passport" in report.by_document_type
        assert "visa" in report.by_document_type
        assert report.by_document_type["passport"].total_fixtures == 1
        assert report.by_document_type["visa"].total_fixtures == 1

    def test_by_difficulty(self) -> None:
        easy = _fixture(fixture_id="e1", difficulty="easy")
        hard = _fixture(fixture_id="h1", difficulty="hard")
        results = {
            "e1": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456", "passport_expiry": "01/01/2030", "nationality": "AMERICAN",
            },
            "h1": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456",
            },
        }
        report = run_extraction_eval([easy, hard], saved_results=results)
        assert "easy" in report.by_difficulty
        assert "hard" in report.by_difficulty
        assert report.by_difficulty["easy"].overall_f1 == 1.0
        assert report.by_difficulty["hard"].overall_f1 < 1.0

    def test_field_metrics_aggregation(self) -> None:
        """Mismatched value is a mismatch, not a false_negative.

        False negative means extractor returned None when a value was expected.
        Mismatch means extractor returned a different non-None value.
        """
        f1 = _fixture(fixture_id="f1")
        f2 = _fixture(fixture_id="f2")
        results = {
            "f1": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456", "passport_expiry": "01/01/2030", "nationality": "AMERICAN",
            },
            "f2": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456", "passport_expiry": "01/01/2030", "nationality": "BRITISH",
            },
        }
        report = run_extraction_eval([f1, f2], saved_results=results)
        nat = report.overall.field_metrics["nationality"]
        # f1: AMERICAN expected = AMERICAN actual → TP
        # f2: AMERICAN expected ≠ BRITISH actual → mismatch (not FN)
        assert nat.true_positives == 1
        assert nat.mismatches == 1
        assert nat.false_negatives == 0

    def test_field_metrics_false_negatives(self) -> None:
        """When extractor returns None for an expected field, that's a false_negative."""
        f1 = _fixture(fixture_id="f1")
        f2 = _fixture(fixture_id="f2")
        results = {
            "f1": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456", "passport_expiry": "01/01/2030", "nationality": "AMERICAN",
            },
            "f2": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456", "passport_expiry": "01/01/2030",
                # nationality missing → false negative
            },
        }
        report = run_extraction_eval([f1, f2], saved_results=results)
        nat = report.overall.field_metrics["nationality"]
        assert nat.true_positives == 1
        assert nat.false_negatives == 1
        assert nat.mismatches == 0


# ---------------------------------------------------------------------------
# load_golden_dataset tests
# ---------------------------------------------------------------------------


class TestLoadGoldenDataset:
    def test_loads_valid_json(self, tmp_path: Path) -> None:
        data = [
            {
                "fixture_id": "test_001",
                "document_type": "passport",
                "description": "test",
                "difficulty": "easy",
                "expected_extracted_fields": {"full_name": "JOHN"},
                "expected_field_count": 1,
                "tags": ["test"],
            }
        ]
        path = tmp_path / "golden.json"
        path.write_text(json.dumps(data))
        fixtures = load_golden_dataset(path)
        assert len(fixtures) == 1
        assert fixtures[0].fixture_id == "test_001"
        assert fixtures[0].expected_extracted_fields == {"full_name": "JOHN"}

    def test_loads_real_golden_dataset(self) -> None:
        path = Path("data/fixtures/extraction/golden_dataset.json")
        if path.exists():
            fixtures = load_golden_dataset(path)
            assert len(fixtures) >= 40  # at least 40 fixtures
            doc_types = {f.document_type for f in fixtures}
            assert "passport" in doc_types
            assert "visa" in doc_types
            assert "insurance" in doc_types


# ---------------------------------------------------------------------------
# summary() tests
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_is_json_serialisable(self) -> None:
        f1 = _fixture(fixture_id="f1")
        results = {
            "f1": {
                "full_name": "JOHN DOE", "date_of_birth": "01/01/1990",
                "passport_number": "AB123456", "passport_expiry": "01/01/2030", "nationality": "AMERICAN",
            },
        }
        report = run_extraction_eval([f1], saved_results=results)
        summary = report.summary()
        serialised = json.dumps(summary)
        assert isinstance(serialised, str)
        assert "overall" in summary
        assert "by_document_type" in summary
        assert "by_difficulty" in summary
        assert "field_metrics" in summary


# ---------------------------------------------------------------------------
# Default no-results path
# ---------------------------------------------------------------------------


class TestNoResults:
    def test_all_none_when_no_saved_results(self) -> None:
        f1 = _fixture(fixture_id="f1")
        report = run_extraction_eval([f1])
        assert report.total_fixtures == 1
        assert report.overall.overall_precision == 0.0
        assert report.overall.overall_recall == 0.0
        assert report.overall.fixture_accuracy == 0.0
