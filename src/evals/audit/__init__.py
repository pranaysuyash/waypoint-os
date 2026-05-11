"""D6 audit evaluation scaffold."""

from .fixtures import AuditFixture, ExpectedAbsentFinding, ExpectedFinding, load_fixtures
from .manifest import EvalCategoryConfig, EvalManifest, load_manifest
from .metrics import CategoryMetrics, compute_category_metrics
from .runner import EvalReport, FixtureEvalResult, run_eval_suite

__all__ = [
    "AuditFixture",
    "CategoryMetrics",
    "EvalCategoryConfig",
    "EvalManifest",
    "EvalReport",
    "ExpectedAbsentFinding",
    "ExpectedFinding",
    "FixtureEvalResult",
    "compute_category_metrics",
    "load_fixtures",
    "load_manifest",
    "run_eval_suite",
]
