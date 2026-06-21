"""D6 audit evaluation scaffold."""

from .comparison import normalise, values_match
from .fixtures import AuditFixture, ExpectedAbsentFinding, ExpectedFinding, load_fixtures
from .gates import CategoryGateDecision, EvalGateReport, evaluate_report_against_manifest
from .manifest import EvalCategoryConfig, EvalManifest, load_manifest
from .metrics import CategoryMetrics, compute_category_metrics
from .rules.extraction import (
    AggregateMetrics,
    ExtractionEvalReport,
    ExtractionFixture,
    FieldComparison,
    FieldMetrics,
    compare_fixture,
    load_golden_dataset,
    run_extraction_eval,
)
from .runner import EvalReport, FixtureEvalResult, run_eval_suite

__all__ = [
    "AuditFixture",
    "AggregateMetrics",
    "CategoryMetrics",
    "CategoryGateDecision",
    "EvalCategoryConfig",
    "EvalManifest",
    "EvalGateReport",
    "EvalReport",
    "ExpectedAbsentFinding",
    "ExpectedFinding",
    "ExtractionEvalReport",
    "ExtractionFixture",
    "FieldComparison",
    "FieldMetrics",
    "FixtureEvalResult",
    "compare_fixture",
    "compute_category_metrics",
    "evaluate_report_against_manifest",
    "load_fixtures",
    "load_golden_dataset",
    "load_manifest",
    "normalise",
    "run_eval_suite",
    "run_extraction_eval",
    "values_match",
]
