"""Precision/recall metrics for D6 audit evals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.suitability.models import StructuredRisk

from .fixtures import ExpectedFinding


@dataclass(slots=True)
class CategoryMetrics:
    category: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    severity_matches: int
    severity_total: int
    severity_accuracy: float


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def compute_category_metrics(
    category: str,
    expected_findings: Iterable[ExpectedFinding],
    actual_findings: Iterable[StructuredRisk],
) -> CategoryMetrics:
    expected = [finding for finding in expected_findings if finding.category == category]
    actual = [finding for finding in actual_findings if finding.category == category]
    expected_by_flag = {finding.flag: finding for finding in expected}
    actual_by_flag = {finding.flag: finding for finding in actual}

    expected_flags = set(expected_by_flag)
    actual_flags = set(actual_by_flag)
    true_positive_flags = expected_flags & actual_flags
    false_positive_flags = actual_flags - expected_flags
    false_negative_flags = expected_flags - actual_flags
    severity_matches = sum(
        1
        for flag in true_positive_flags
        if actual_by_flag[flag].severity == expected_by_flag[flag].severity
    )
    severity_total = len(true_positive_flags)

    return CategoryMetrics(
        category=category,
        true_positives=len(true_positive_flags),
        false_positives=len(false_positive_flags),
        false_negatives=len(false_negative_flags),
        precision=_ratio(len(true_positive_flags), len(true_positive_flags) + len(false_positive_flags)),
        recall=_ratio(len(true_positive_flags), len(true_positive_flags) + len(false_negative_flags)),
        severity_matches=severity_matches,
        severity_total=severity_total,
        severity_accuracy=_ratio(severity_matches, severity_total),
    )
