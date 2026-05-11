"""D6 manifest gate evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from .manifest import EvalManifest
from .metrics import CategoryMetrics
from .runner import EvalReport


@dataclass(slots=True)
class CategoryGateDecision:
    category: str
    status: str
    metrics: CategoryMetrics | None
    meets_thresholds: bool
    blocks_ci: bool
    authoritative_for_public_surface: bool
    reasons: list[str]


@dataclass(slots=True)
class EvalGateReport:
    categories: dict[str, CategoryGateDecision]


def _meets_thresholds(metrics: CategoryMetrics | None, *, min_precision: float, min_recall: float, min_severity_accuracy: float) -> tuple[bool, list[str]]:
    if metrics is None:
        return False, ["no_metrics_for_category"]
    reasons: list[str] = []
    if metrics.precision < min_precision:
        reasons.append("precision_below_threshold")
    if metrics.recall < min_recall:
        reasons.append("recall_below_threshold")
    if metrics.severity_accuracy < min_severity_accuracy:
        reasons.append("severity_accuracy_below_threshold")
    return not reasons, reasons


def evaluate_report_against_manifest(report: EvalReport, manifest: EvalManifest) -> EvalGateReport:
    """Compare an eval report to manifest thresholds and surface-readiness rules."""

    decisions: dict[str, CategoryGateDecision] = {}
    for category, config in manifest.categories.items():
        metrics = report.category_metrics.get(category)
        meets_thresholds, reasons = _meets_thresholds(
            metrics,
            min_precision=config.min_precision,
            min_recall=config.min_recall,
            min_severity_accuracy=config.min_severity_accuracy,
        )
        blocks_ci = config.status == "gating" and not meets_thresholds
        authoritative = config.status == "gating" and meets_thresholds
        if config.status != "gating":
            reasons = [*reasons, f"category_status_{config.status}"]
        decisions[category] = CategoryGateDecision(
            category=category,
            status=config.status,
            metrics=metrics,
            meets_thresholds=meets_thresholds,
            blocks_ci=blocks_ci,
            authoritative_for_public_surface=authoritative,
            reasons=reasons,
        )
    return EvalGateReport(categories=decisions)
