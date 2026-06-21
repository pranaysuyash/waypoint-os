"""Build runtime D6 gate snapshots for public-surface authority decisions."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.evals.agentic_feedback import (
    DEFAULT_ROUTING_HEALTH_THRESHOLDS,
    check_routing_health,
)

from .fixtures import AuditFixture, load_fixtures
from .gates import evaluate_report_against_manifest
from .manifest import load_manifest
from .rules.activity import run_activity_fixture
from .rules.extraction import load_golden_dataset, run_extraction_eval
from .rules.pipeline import load_pipeline_fixtures, run_pipeline_eval
from .runner import run_eval_suite

DEFAULT_FIXTURE_ROOT = Path("data/fixtures/audit")
DEFAULT_SNAPSHOT_PATH = Path("data/evals/d6_audit_gate_snapshot.json")
DEFAULT_GOLDEN_DATASET_PATH = Path("data/fixtures/extraction/golden_dataset.json")
DEFAULT_PIPELINE_FIXTURE_PATH = Path("data/fixtures/pipeline/pipeline_golden.json")


def _rule_dispatch(fixture: AuditFixture):
    if fixture.category == "activity":
        return run_activity_fixture(fixture)
    return []


def _run_extraction_baseline(
    *,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
) -> dict[str, Any]:
    """Run extraction eval against the golden dataset with no live results.

    Returns a JSON-serialisable summary suitable for the gate snapshot.
    When no extraction results are available, all non-null expected fields
    become false negatives — the worst-case baseline.
    """
    if not golden_dataset_path.exists():
        return {
            "status": "unavailable",
            "reason": "golden_dataset_missing",
            "total_fixtures": 0,
            "overall_f1": 0.0,
            "blocks_ci": False,
        }
    fixtures = load_golden_dataset(golden_dataset_path)
    report = run_extraction_eval(fixtures)
    summary = report.summary()
    # Determine gate status from overall F1
    overall_f1 = summary["overall"]["f1"]
    if overall_f1 >= 0.85:
        status = "passing"
    elif overall_f1 >= 0.70:
        status = "warning"
    else:
        status = "failing"
    return {
        "status": status,
        "overall_f1": overall_f1,
        "overall_precision": summary["overall"]["precision"],
        "overall_recall": summary["overall"]["recall"],
        "total_fixtures": summary["total_fixtures"],
        "fixture_accuracy": summary["overall"]["fixture_accuracy"],
        "by_document_type": summary["by_document_type"],
        "by_difficulty": summary["by_difficulty"],
        "blocks_ci": status == "failing",
        "note": "Baseline with no live extraction results. Override with actual results at runtime.",
    }


def _run_pipeline_baseline(
    *,
    pipeline_fixture_path: Path = DEFAULT_PIPELINE_FIXTURE_PATH,
) -> dict[str, Any]:
    """Run pipeline eval against golden fixtures with no live results.

    Returns a JSON-serialisable summary suitable for the gate snapshot.
    When no actual pipeline results are available, all expected fields
    become false negatives — the worst-case baseline.
    """
    if not pipeline_fixture_path.exists():
        return {
            "status": "unavailable",
            "reason": "pipeline_fixture_missing",
            "total_fixtures": 0,
            "overall_accuracy": 0.0,
            "blocks_ci": False,
        }
    fixtures = load_pipeline_fixtures(pipeline_fixture_path)
    report = run_pipeline_eval(fixtures)
    summary = report.summary()
    overall_acc = summary["overall_accuracy"]
    if overall_acc >= 0.80:
        status = "passing"
    elif overall_acc >= 0.50:
        status = "warning"
    else:
        status = "failing"
    return {
        "status": status,
        "overall_accuracy": overall_acc,
        "total_fixtures": summary["total_fixtures"],
        "fixtures_passing": summary["fixtures_passing"],
        "fixtures_failing": summary["fixtures_failing"],
        "stage_accuracies": summary["stage_accuracies"],
        "blocks_ci": status == "failing",
        "note": "Baseline with no live pipeline results. Override with actual results at runtime.",
    }


def build_gate_snapshot(
    *,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixture_root)
    manifest = load_manifest()
    report = run_eval_suite(fixtures, rule_runner=_rule_dispatch)
    gate = evaluate_report_against_manifest(report, manifest)

    categories: dict[str, Any] = {}
    for name, decision in gate.categories.items():
        categories[name] = {
            "status": decision.status,
            "meets_thresholds": decision.meets_thresholds,
            "blocks_ci": decision.blocks_ci,
            "authoritative_for_public_surface": decision.authoritative_for_public_surface,
            "reasons": list(decision.reasons),
            "metrics": asdict(decision.metrics) if decision.metrics is not None else None,
        }

    # --- routing health gate ---
    # Evaluate routing health against default thresholds using empty metrics
    # (no live data at snapshot generation time).  This establishes a
    # baseline "healthy" state that can be overridden at runtime when
    # actual routing metrics are available.
    routing_health = check_routing_health({})

    # --- extraction accuracy gate ---
    # Run the extraction eval against the golden dataset with no live
    # extraction results (baseline: all fields are None → all non-null
    # expected fields are false negatives).  This establishes baseline
    # metrics that will be overridden when actual extraction results
    # are available at runtime.
    extraction_eval_report = _run_extraction_baseline(
        golden_dataset_path=golden_dataset_path,
    )

    # --- pipeline end-to-end eval gate ---
    # Run pipeline eval against golden fixtures with no live results.
    # Baseline: all expected fields are false negatives.
    pipeline_health = _run_pipeline_baseline()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest.version,
        "fixture_root": str(fixture_root),
        "total_fixtures": report.total_fixtures,
        "categories": categories,
        "routing_health": {
            "status": routing_health.status,
            "blocks_ci": routing_health.status == "critical",
            "thresholds": dict(DEFAULT_ROUTING_HEALTH_THRESHOLDS),
            "checked_at": routing_health.checked_at.isoformat(),
        },
        "extraction_health": extraction_eval_report,
        "pipeline_health": pipeline_health,
    }


def write_gate_snapshot(
    *,
    output_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
) -> Path:
    snapshot = build_gate_snapshot(fixture_root=fixture_root, golden_dataset_path=golden_dataset_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))
    return output_path


def stable_snapshot_view(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic comparable view (ignores volatile timestamp)."""
    routing_health = snapshot.get("routing_health")
    stable_routing: dict[str, Any] | None = None
    if isinstance(routing_health, dict):
        stable_routing = {
            "status": routing_health.get("status"),
            "blocks_ci": routing_health.get("blocks_ci"),
            "thresholds": routing_health.get("thresholds"),
        }
    extraction_health = snapshot.get("extraction_health")
    stable_extraction: dict[str, Any] | None = None
    if isinstance(extraction_health, dict):
        stable_extraction = {
            "status": extraction_health.get("status"),
            "overall_f1": extraction_health.get("overall_f1"),
            "overall_precision": extraction_health.get("overall_precision"),
            "overall_recall": extraction_health.get("overall_recall"),
            "total_fixtures": extraction_health.get("total_fixtures"),
            "blocks_ci": extraction_health.get("blocks_ci"),
            "by_document_type": extraction_health.get("by_document_type"),
            "by_difficulty": extraction_health.get("by_difficulty"),
        }
    pipeline_health = snapshot.get("pipeline_health")
    stable_pipeline: dict[str, Any] | None = None
    if isinstance(pipeline_health, dict):
        stable_pipeline = {
            "status": pipeline_health.get("status"),
            "overall_accuracy": pipeline_health.get("overall_accuracy"),
            "total_fixtures": pipeline_health.get("total_fixtures"),
            "blocks_ci": pipeline_health.get("blocks_ci"),
        }
    return {
        "manifest_version": snapshot.get("manifest_version"),
        "fixture_root": snapshot.get("fixture_root"),
        "total_fixtures": snapshot.get("total_fixtures"),
        "categories": snapshot.get("categories"),
        "routing_health": stable_routing,
        "extraction_health": stable_extraction,
        "pipeline_health": stable_pipeline,
    }


def verify_gate_snapshot_file(
    *,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
) -> tuple[bool, dict[str, Any], dict[str, Any] | None]:
    expected = build_gate_snapshot(fixture_root=fixture_root, golden_dataset_path=golden_dataset_path)
    if not snapshot_path.exists():
        return False, expected, None
    try:
        actual = json.loads(snapshot_path.read_text())
    except Exception:
        return False, expected, None
    return stable_snapshot_view(actual) == stable_snapshot_view(expected), expected, actual
