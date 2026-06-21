"""Extraction accuracy rule — per-field precision / recall / F1 for the D6 audit scaffold.

This module evaluates document extraction accuracy against a golden dataset by
comparing expected field values to actual extracted values.  It produces:

- Per-field metrics (precision, recall, F1, accuracy) for every field name that
  appears across the fixture set.
- Per-document-type aggregation (passport / visa / insurance).
- Per-difficulty aggregation (easy / medium / hard).
- An overall aggregate report.

Matching semantics
------------------
Two field values are compared via :func:`_normalise` which lower-cases, strips
collapsible whitespace, and trims leading/trailing spaces.  Callers can choose
between exact-match (strict) and contains-match (lenient) comparison modes.

Null semantics
--------------
Both expected and actual values may be ``None`` (field absent/unreadable).  A
``None`` expected matched by a ``None`` actual is a **true negative** for that
field slot.  A ``None`` expected matched by a non-None actual is a **false
positive** (the extractor hallucinated a value).  A non-None expected matched by
a ``None`` actual is a **false negative** (the extractor failed to read the
field).
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Fixture model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ExtractionFixture:
    """One labelled test case from the golden dataset."""

    fixture_id: str
    document_type: str
    description: str
    difficulty: str
    expected_extracted_fields: dict[str, str | None]
    expected_field_count: int
    tags: list[str]


def load_golden_dataset(path: Path | str) -> list[ExtractionFixture]:
    """Load the golden extraction dataset from a JSON file."""
    raw = json.loads(Path(path).read_text())
    return [
        ExtractionFixture(
            fixture_id=item["fixture_id"],
            document_type=item["document_type"],
            description=item.get("description", ""),
            difficulty=item.get("difficulty", "medium"),
            expected_extracted_fields=item["expected_extracted_fields"],
            expected_field_count=item.get("expected_field_count", 0),
            tags=item.get("tags", []),
        )
        for item in raw
    ]


# ---------------------------------------------------------------------------
# Normalisation & comparison (shared utilities)
# ---------------------------------------------------------------------------

from src.evals.audit.comparison import normalise as _normalise, values_match


# ---------------------------------------------------------------------------
# Per-field comparison result
# ---------------------------------------------------------------------------

MatchType = Literal["exact_match", "contains_match", "null_match", "mismatch", "false_positive", "false_negative"]


@dataclass(slots=True)
class FieldComparison:
    """Outcome of comparing one field across expected vs actual."""

    field_name: str
    expected: str | None
    actual: str | None
    is_match: bool
    match_type: MatchType


@dataclass(slots=True)
class FixtureComparison:
    """All field comparisons for one fixture."""

    fixture: ExtractionFixture
    actual_fields: dict[str, str | None]
    field_comparisons: list[FieldComparison]
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    all_fields_match: bool = False


def compare_fixture(
    fixture: ExtractionFixture,
    actual_fields: dict[str, str | None],
    *,
    mode: Literal["exact", "contains"] = "exact",
) -> FixtureComparison:
    """Compare a single fixture's expected vs actual extracted fields.

    The comparison iterates over the union of expected and actual field names
    so that hallucinated fields (false positives) and missed fields (false
    negatives) are both captured.
    """
    expected = fixture.expected_extracted_fields
    all_field_names = sorted(set(expected) | set(actual_fields))
    comparisons: list[FieldComparison] = []

    for field_name in all_field_names:
        exp_val = expected.get(field_name)
        act_val = actual_fields.get(field_name)
        is_match = values_match(exp_val, act_val, mode=mode)

        # Determine match type
        if exp_val is None and act_val is None:
            match_type: MatchType = "null_match"
        elif exp_val is not None and act_val is not None:
            match_type = "exact_match" if _normalise(exp_val) == _normalise(act_val) else (
                "contains_match" if values_match(exp_val, act_val, mode="contains") else "mismatch"
            )
        elif exp_val is None and act_val is not None:
            match_type = "false_positive"
        else:
            match_type = "false_negative"

        comparisons.append(FieldComparison(
            field_name=field_name,
            expected=exp_val,
            actual=act_val,
            is_match=is_match,
            match_type=match_type,
        ))

    # Per-fixture precision / recall / F1
    # Precision: of the fields the extractor returned (non-None actual), how many are correct?
    # Recall: of the fields that should have been extracted (non-None expected), how many were found correctly?
    tp = sum(1 for c in comparisons if c.expected is not None and c.actual is not None and c.is_match)
    fp = sum(1 for c in comparisons if c.expected is None and c.actual is not None)
    fn = sum(1 for c in comparisons if c.expected is not None and c.actual is None)
    mismatch = sum(1 for c in comparisons if c.expected is not None and c.actual is not None and not c.is_match)

    extracted_count = tp + fp
    expected_count = tp + fn
    precision = tp / extracted_count if extracted_count > 0 else 0.0
    recall = tp / expected_count if expected_count > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return FixtureComparison(
        fixture=fixture,
        actual_fields=actual_fields,
        field_comparisons=comparisons,
        precision=precision,
        recall=recall,
        f1=f1,
        all_fields_match=all(c.is_match for c in comparisons),
    )


# ---------------------------------------------------------------------------
# Aggregate metrics
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class FieldMetrics:
    """Aggregate metrics for a single field name across all fixtures."""

    field_name: str
    total_expected: int = 0
    total_extracted: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    mismatches: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    accuracy: float = 0.0


@dataclass(slots=True)
class AggregateMetrics:
    """Aggregate metrics across a group of fixture comparisons."""

    group_name: str
    total_fixtures: int = 0
    fixtures_all_match: int = 0
    fixture_accuracy: float = 0.0
    field_metrics: dict[str, FieldMetrics] = field(default_factory=dict)
    overall_precision: float = 0.0
    overall_recall: float = 0.0
    overall_f1: float = 0.0


def _ratio(num: int, denom: int) -> float:
    return num / denom if denom > 0 else 0.0


def _compute_field_metrics(
    field_name: str,
    comparisons: list[FieldComparison],
) -> FieldMetrics:
    """Aggregate one field across a list of comparisons."""
    tp = fp = fn = mm = 0
    for c in comparisons:
        if c.field_name != field_name:
            continue
        if c.expected is not None and c.actual is not None:
            if c.is_match:
                tp += 1
            else:
                mm += 1
        elif c.expected is None and c.actual is not None:
            fp += 1
        elif c.expected is not None and c.actual is None:
            fn += 1

    extracted = tp + fp
    expected = tp + fn
    correct = tp
    total = tp + fp + fn + mm
    p = _ratio(tp, extracted)
    r = _ratio(tp, expected)

    return FieldMetrics(
        field_name=field_name,
        total_expected=expected,
        total_extracted=extracted,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        mismatches=mm,
        precision=p,
        recall=r,
        f1=2 * p * r / (p + r) if (p + r) > 0 else 0.0,
        accuracy=_ratio(correct, total),
    )


def aggregate_comparisons(
    comparisons: list[FixtureComparison],
    group_name: str,
) -> AggregateMetrics:
    """Compute aggregate metrics across a list of fixture comparisons."""
    if not comparisons:
        return AggregateMetrics(group_name=group_name)

    # Collect all field names
    all_field_names: set[str] = set()
    for fc in comparisons:
        for c in fc.field_comparisons:
            all_field_names.add(c.field_name)

    # Flatten all FieldComparison objects across fixtures for per-field aggregation
    all_field_comparisons: list[FieldComparison] = []
    for fc in comparisons:
        all_field_comparisons.extend(fc.field_comparisons)

    field_metrics = {
        fname: _compute_field_metrics(fname, all_field_comparisons)
        for fname in sorted(all_field_names)
    }

    # Overall TP/FP/FN across all fields
    total_tp = sum(fm.true_positives for fm in field_metrics.values())
    total_fp = sum(fm.false_positives for fm in field_metrics.values())
    total_fn = sum(fm.false_negatives for fm in field_metrics.values())
    total_extracted = total_tp + total_fp
    total_expected = total_tp + total_fn
    op = _ratio(total_tp, total_extracted)
    or_ = _ratio(total_tp, total_expected)
    overall_f1 = (
        2 * op * or_ / (op + or_)
        if (op + or_) > 0 else 0.0
    )
    overall_precision = op
    overall_recall = or_

    all_match = sum(1 for fc in comparisons if fc.all_fields_match)

    return AggregateMetrics(
        group_name=group_name,
        total_fixtures=len(comparisons),
        fixtures_all_match=all_match,
        fixture_accuracy=_ratio(all_match, len(comparisons)),
        field_metrics=field_metrics,
        overall_precision=overall_precision,
        overall_recall=overall_recall,
        overall_f1=overall_f1,
    )


# ---------------------------------------------------------------------------
# Top-level eval report
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ExtractionEvalReport:
    """Full evaluation report across all fixtures."""

    total_fixtures: int = 0
    fixture_comparisons: list[FixtureComparison] = field(default_factory=list)
    overall: AggregateMetrics = field(default_factory=lambda: AggregateMetrics(group_name="overall"))
    by_document_type: dict[str, AggregateMetrics] = field(default_factory=dict)
    by_difficulty: dict[str, AggregateMetrics] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Return a JSON-serialisable summary of the report."""
        return {
            "total_fixtures": self.total_fixtures,
            "overall": {
                "precision": round(self.overall.overall_precision, 4),
                "recall": round(self.overall.overall_recall, 4),
                "f1": round(self.overall.overall_f1, 4),
                "fixture_accuracy": round(self.overall.fixture_accuracy, 4),
            },
            "by_document_type": {
                name: {
                    "precision": round(m.overall_precision, 4),
                    "recall": round(m.overall_recall, 4),
                    "f1": round(m.overall_f1, 4),
                    "fixture_accuracy": round(m.fixture_accuracy, 4),
                    "total_fixtures": m.total_fixtures,
                }
                for name, m in self.by_document_type.items()
            },
            "by_difficulty": {
                name: {
                    "precision": round(m.overall_precision, 4),
                    "recall": round(m.overall_recall, 4),
                    "f1": round(m.overall_f1, 4),
                    "fixture_accuracy": round(m.fixture_accuracy, 4),
                    "total_fixtures": m.total_fixtures,
                }
                for name, m in self.by_difficulty.items()
            },
            "field_metrics": {
                name: {
                    "precision": round(fm.precision, 4),
                    "recall": round(fm.recall, 4),
                    "f1": round(fm.f1, 4),
                    "accuracy": round(fm.accuracy, 4),
                    "true_positives": fm.true_positives,
                    "false_positives": fm.false_positives,
                    "false_negatives": fm.false_negatives,
                    "mismatches": fm.mismatches,
                }
                for name, fm in self.overall.field_metrics.items()
            },
        }


# ---------------------------------------------------------------------------
# Main eval runner
# ---------------------------------------------------------------------------

def run_extraction_eval(
    fixtures: list[ExtractionFixture],
    actual_extractor: Any | None = None,
    extraction_fn: Any | None = None,
    *,
    mode: Literal["exact", "contains"] = "exact",
    saved_results: dict[str, dict[str, str | None]] | None = None,
) -> ExtractionEvalReport:
    """Run the extraction eval suite over a set of fixtures.

    Parameters
    ----------
    fixtures
        Golden dataset fixtures with expected field values.
    actual_extractor
        Optional extractor object with an ``extract(file_data, mime_type, doc_type)``
        async method.  Not used when ``saved_results`` is provided.
    extraction_fn
        Optional async callable ``(fixture) -> dict[str, str | None]`` that
        returns actual extracted fields for a fixture.
    mode
        Comparison mode: ``"exact"`` for strict equality, ``"contains"`` for
        substring/fuzzy matching.
    saved_results
        Pre-computed extraction results keyed by fixture_id.  When provided,
        the runner skips extraction and uses these values directly.  This is
        the primary path for offline eval against recorded results.

    Returns
    -------
    ExtractionEvalReport
        Full report with per-field, per-document-type, and per-difficulty metrics.
    """
    comparisons: list[FixtureComparison] = []

    for fixture in fixtures:
        if saved_results is not None:
            actual = saved_results.get(fixture.fixture_id, {})
        elif extraction_fn is not None:
            # extraction_fn is expected to be a sync callable or already awaited
            actual = extraction_fn(fixture)  # type: ignore[assignment]
        else:
            # No actual data — all fields are None (false negatives for non-null expected)
            actual = {field_name: None for field_name in fixture.expected_extracted_fields}

        comp = compare_fixture(fixture, actual, mode=mode)
        comparisons.append(comp)

    # Overall aggregation
    overall = aggregate_comparisons(comparisons, group_name="overall")

    # By document type
    by_type: dict[str, list[FixtureComparison]] = defaultdict(list)
    for comp in comparisons:
        by_type[comp.fixture.document_type].append(comp)
    by_document_type = {
        dt: aggregate_comparisons(comps, group_name=dt)
        for dt, comps in sorted(by_type.items())
    }

    # By difficulty
    by_diff: dict[str, list[FixtureComparison]] = defaultdict(list)
    for comp in comparisons:
        by_diff[comp.fixture.difficulty].append(comp)
    by_difficulty = {
        diff: aggregate_comparisons(comps, group_name=diff)
        for diff, comps in sorted(by_diff.items())
    }

    return ExtractionEvalReport(
        total_fixtures=len(fixtures),
        fixture_comparisons=comparisons,
        overall=overall,
        by_document_type=by_document_type,
        by_difficulty=by_difficulty,
    )
