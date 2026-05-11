from pathlib import Path

import pytest

from src.evals.audit.fixtures import AuditFixture, ExpectedFinding, load_fixtures
from src.evals.audit.manifest import load_manifest
from src.evals.audit.metrics import compute_category_metrics
from src.evals.audit.runner import run_eval_suite
from src.suitability.models import StructuredRisk


def test_d6_manifest_loads_category_progression():
    manifest = load_manifest()

    assert manifest.categories["activity"].status == "shadow"
    assert manifest.categories["budget"].status == "gating"
    assert manifest.categories["activity"].min_precision > 0


def test_d6_fixture_schema_validates_expected_findings():
    fixture = AuditFixture(
        fixture_id="activity_toddler_low_utility",
        category="activity",
        subject={
            "subject_id": "subject_1",
            "subject_type": "itinerary",
            "destination_keys": ["singapore"],
            "party_composition": {"adults": 2, "toddlers": 1},
            "activities": [{"activity_id": "universal_studios"}],
        },
        expected_findings=[
            ExpectedFinding(
                category="activity",
                flag="low_utility_activity",
                severity="high",
                affected_refs=["toddler_1"],
            )
        ],
    )

    assert fixture.primary_expected_flags == {"low_utility_activity"}


def test_d6_metrics_compute_precision_recall_and_severity_accuracy():
    expected = [
        ExpectedFinding(category="activity", flag="low_utility_activity", severity="high"),
        ExpectedFinding(category="activity", flag="wasted_spend", severity="medium"),
    ]
    actual = [
        StructuredRisk(flag="low_utility_activity", severity="high", category="activity", message=""),
        StructuredRisk(flag="extra_flag", severity="low", category="activity", message=""),
    ]

    metrics = compute_category_metrics("activity", expected, actual)

    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == pytest.approx(0.5)
    assert metrics.recall == pytest.approx(0.5)
    assert metrics.severity_accuracy == pytest.approx(1.0)


def test_d6_runner_can_execute_fixture_directory(tmp_path: Path):
    fixture_path = tmp_path / "activity_low_utility.json"
    fixture_path.write_text(
        """
{
  "fixture_id": "activity_low_utility",
  "category": "activity",
  "subject": {
    "subject_id": "subject_1",
    "subject_type": "itinerary",
    "destination_keys": ["singapore"],
    "party_composition": {"adults": 1},
    "activities": []
  },
  "expected_findings": []
}
""".strip()
    )

    fixtures = load_fixtures(tmp_path)
    report = run_eval_suite(fixtures, rule_runner=lambda fixture: [])

    assert report.total_fixtures == 1
    assert report.category_metrics["activity"].precision == 1.0
    assert report.category_metrics["activity"].recall == 1.0


def test_d6_seed_fixture_corpus_loads():
    fixture_root = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "audit"

    fixtures = load_fixtures(fixture_root)

    assert {fixture.fixture_id for fixture in fixtures} >= {"activity_toddler_low_utility"}
    assert fixtures[0].expected_findings
