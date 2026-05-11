"""D6 audit eval runner scaffold."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Iterable

from src.suitability.models import StructuredRisk

from .fixtures import AuditFixture
from .metrics import CategoryMetrics, compute_category_metrics

AuditRuleRunner = Callable[[AuditFixture], list[StructuredRisk]]


@dataclass(slots=True)
class FixtureEvalResult:
    fixture_id: str
    category: str
    expected_flags: list[str]
    actual_flags: list[str]
    passed: bool


@dataclass(slots=True)
class EvalReport:
    total_fixtures: int
    fixture_results: list[FixtureEvalResult] = field(default_factory=list)
    category_metrics: dict[str, CategoryMetrics] = field(default_factory=dict)


def run_eval_suite(
    fixtures: Iterable[AuditFixture],
    rule_runner: AuditRuleRunner,
) -> EvalReport:
    fixture_list = list(fixtures)
    expected_by_category = defaultdict(list)
    actual_by_category = defaultdict(list)
    fixture_results: list[FixtureEvalResult] = []

    for fixture in fixture_list:
        actual = rule_runner(fixture)
        expected_by_category[fixture.category].extend(fixture.expected_findings)
        actual_by_category[fixture.category].extend(actual)
        expected_flags = [finding.flag for finding in fixture.expected_findings]
        actual_flags = [finding.flag for finding in actual]
        fixture_results.append(
            FixtureEvalResult(
                fixture_id=fixture.fixture_id,
                category=fixture.category,
                expected_flags=expected_flags,
                actual_flags=actual_flags,
                passed=set(expected_flags) == set(actual_flags),
            )
        )

    categories = set(expected_by_category) | set(actual_by_category)
    category_metrics = {
        category: compute_category_metrics(
            category,
            expected_by_category[category],
            actual_by_category[category],
        )
        for category in categories
    }
    return EvalReport(
        total_fixtures=len(fixture_list),
        fixture_results=fixture_results,
        category_metrics=category_metrics,
    )
