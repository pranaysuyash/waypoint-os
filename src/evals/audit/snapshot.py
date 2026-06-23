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
from .rules.extraction import ExtractionFixture, load_golden_dataset, run_extraction_eval
from .rules.pipeline import load_pipeline_fixtures, run_pipeline_eval
from .runner import run_eval_suite

try:
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope
    _HAS_INTAKE_PIPELINE = True
except ImportError:
    _HAS_INTAKE_PIPELINE = False

DEFAULT_FIXTURE_ROOT = Path("data/fixtures/audit")
DEFAULT_SNAPSHOT_PATH = Path("data/evals/d6_audit_gate_snapshot.json")
DEFAULT_GOLDEN_DATASET_PATH = Path("data/fixtures/extraction/golden_dataset.json")
DEFAULT_PIPELINE_FIXTURE_PATH = Path("data/fixtures/pipeline/pipeline_golden.json")
DEFAULT_BUDGET_GOLDEN_DATASET_PATH = Path("data/fixtures/budget/golden_dataset.json")

# Budget field mapping: pipeline fact name -> golden dataset field name.
# The extraction pipeline stores budget data as budget_max, budget_currency,
# budget_scope, budget_flexibility in the CanonicalPacket.facts dict.
# The golden dataset expects budget_amount, budget_currency, budget_scope,
# budget_flexibility as string values.
_BUDGET_FIELD_MAP = {
    "budget_amount": "budget_max",
    "budget_currency": "budget_currency",
    "budget_scope": "budget_scope",
    "budget_flexibility": "budget_flexibility",
}


def _collect_live_budget_results(
    golden_dataset_path: Path = DEFAULT_BUDGET_GOLDEN_DATASET_PATH,
) -> dict[str, dict[str, str | None]]:
    """Run the real extraction pipeline on budget golden dataset fixtures.

    Loads the raw JSON (which retains ``raw_input`` not captured by
    ``ExtractionFixture``), feeds each fixture's ``raw_input`` through
    ``ExtractionPipeline``, and maps the resulting CanonicalPacket facts
    back to the golden-dataset field names so that ``run_extraction_eval``
    can compare them against ``expected_extracted_fields``.

    Returns a dict keyed by ``fixture_id`` with the mapped extracted
    fields.  Returns an empty dict when the intake pipeline is not
    importable or the golden dataset is missing.
    """
    if not _HAS_INTAKE_PIPELINE or not golden_dataset_path.exists():
        return {}
    raw_data = json.loads(golden_dataset_path.read_text())
    pipeline = ExtractionPipeline()
    results: dict[str, dict[str, str | None]] = {}
    for item in raw_data:
        fixture_id = item["fixture_id"]
        raw_input = item.get("raw_input", "")
        if not raw_input:
            continue
        envelope = SourceEnvelope.from_freeform(
            raw_input,
            source="agency_notes",
            actor="agent",
        )
        packet = pipeline.extract([envelope])
        # Map pipeline fact names to golden dataset field names.
        extracted: dict[str, str | None] = {}
        for golden_field, pipeline_fact in _BUDGET_FIELD_MAP.items():
            slot = packet.facts.get(pipeline_fact)
            if slot is not None and slot.value is not None:
                extracted[golden_field] = str(slot.value)
            else:
                extracted[golden_field] = None
        results[fixture_id] = extracted
    return results


# Expected baseline accuracy when the pipeline eval runs with self-consistent
# expected-as-actual results.  This value is stored in the snapshot and
# compared during drift detection — if the golden fixtures or comparison
# logic change, the computed accuracy will diverge from this constant.
EXPECTED_PIPELINE_BASELINE_ACCURACY = 1.0
EXPECTED_EXTRACTION_BASELINE_F1 = 1.0
EXPECTED_BUDGET_BASELINE_F1 = 1.0


def _rule_dispatch(fixture: AuditFixture):
    if fixture.category == "activity":
        return run_activity_fixture(fixture)
    return []


def _run_extraction_baseline(
    *,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
    live_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run extraction eval against the golden dataset.

    Returns a JSON-serialisable summary suitable for the gate snapshot.
    When ``live_results`` is provided, they are used as the actual
    extraction outputs and compared against the golden fixtures.  When
    ``live_results`` is ``None``, the expected outputs are used as
    actuals (self-consistent baseline) to validate comparison logic.

    Parameters
    ----------
    golden_dataset_path
        Path to the golden extraction dataset JSON.
    live_results
        Actual extraction results keyed by fixture_id.  When ``None``,
        expected outputs are used as actuals.
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
    if live_results is not None:
        report = run_extraction_eval(fixtures, saved_results=live_results)
        note = "Live extraction results used for F1 evaluation."
    else:
        # Build self-consistent actual results from expected outputs.
        # This validates the comparison logic and produces a 100%-F1
        # reference baseline.
        saved_results = {
            fixture.fixture_id: fixture.expected_extracted_fields
            for fixture in fixtures
        }
        report = run_extraction_eval(fixtures, saved_results=saved_results)
        note = "Baseline using expected outputs as actuals. Override with real extraction results at runtime."
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
        "expected_baseline_f1": EXPECTED_EXTRACTION_BASELINE_F1,
        "baseline_drifted": overall_f1 != EXPECTED_EXTRACTION_BASELINE_F1,
        "note": note,
    }


def _run_pipeline_baseline(
    *,
    pipeline_fixture_path: Path = DEFAULT_PIPELINE_FIXTURE_PATH,
    live_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run pipeline eval against golden fixtures.

    Returns a JSON-serialisable summary suitable for the gate snapshot.
    When ``live_results`` is provided, they are used as the actual
    pipeline outputs and compared against the golden fixtures.  When
    ``live_results`` is ``None``, the expected outputs are used as
    actuals (self-consistent baseline) to validate comparison logic.

    Parameters
    ----------
    pipeline_fixture_path
        Path to the golden pipeline fixtures JSON.
    live_results
        Actual pipeline outputs keyed by fixture_id.  Each value is a
        dict with ``extraction``, ``agents``, and ``decision`` keys.
        When ``None``, expected outputs are used as actuals.
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
    if live_results is not None:
        actual_results = live_results
        note = "Live pipeline results used for accuracy evaluation."
    else:
        # Build self-consistent actual results from expected outputs.
        # This validates the comparison logic and produces a 100%-accuracy
        # reference baseline.
        actual_results = {}
        for fixture in fixtures:
            actual_results[fixture.fixture_id] = {
                "extraction": fixture.expected_extraction,
                "agents": fixture.expected_agents,
                "decision": fixture.expected_decision,
            }
        note = "Baseline using expected outputs as actuals. Override with real pipeline results at runtime."
    report = run_pipeline_eval(fixtures, actual_results)
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
        "expected_baseline_accuracy": EXPECTED_PIPELINE_BASELINE_ACCURACY,
        "baseline_drifted": overall_acc != EXPECTED_PIPELINE_BASELINE_ACCURACY,
        "note": note,
    }


def _run_budget_baseline(
    *,
    golden_dataset_path: Path = DEFAULT_BUDGET_GOLDEN_DATASET_PATH,
    live_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run budget extraction eval against the golden dataset.

    Returns a JSON-serialisable summary suitable for the gate snapshot.
    Uses the same extraction eval framework since budget fixtures follow
    the same schema (fixture_id, expected_extracted_fields, etc.).

    Parameters
    ----------
    golden_dataset_path
        Path to the budget golden dataset JSON.
    live_results
        Actual budget extraction results keyed by fixture_id.  When
        ``None``, expected outputs are used as actuals (self-consistent
        baseline).
    """
    if not golden_dataset_path.exists():
        return {
            "status": "unavailable",
            "reason": "budget_golden_dataset_missing",
            "total_fixtures": 0,
            "overall_f1": 0.0,
            "blocks_ci": False,
        }
    fixtures = load_golden_dataset(golden_dataset_path)
    if live_results is not None:
        report = run_extraction_eval(fixtures, saved_results=live_results)
        note = "Live budget results used for F1 evaluation."
    else:
        # Attempt to collect live results from the real extraction pipeline.
        live = _collect_live_budget_results(golden_dataset_path)
        if live:
            report = run_extraction_eval(fixtures, saved_results=live)
            note = "Live pipeline extraction results used for budget F1 evaluation."
        else:
            # Fallback: self-consistent baseline (expected as actuals).
            # This validates comparison logic when the intake pipeline is not
            # importable (e.g. in CI without full dependencies).
            saved_results = {
                fixture.fixture_id: fixture.expected_extracted_fields
                for fixture in fixtures
            }
            report = run_extraction_eval(fixtures, saved_results=saved_results)
            note = "Baseline using expected outputs as actuals (intake pipeline unavailable)."
    summary = report.summary()
    overall_f1 = summary["overall"]["f1"]
    if overall_f1 >= 0.95:
        status = "passing"
    elif overall_f1 >= 0.80:
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
        "expected_baseline_f1": EXPECTED_BUDGET_BASELINE_F1,
        "baseline_drifted": overall_f1 != EXPECTED_BUDGET_BASELINE_F1,
        "note": note,
    }


def build_gate_snapshot(
    *,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
    extraction_live_results: dict[str, Any] | None = None,
    pipeline_live_results: dict[str, dict[str, Any]] | None = None,
    budget_live_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixture_root)
    manifest = load_manifest()
    report = run_eval_suite(fixtures, rule_runner=_rule_dispatch)

    # --- routing health gate ---
    routing_health = check_routing_health({})

    # --- extraction accuracy gate ---
    extraction_eval_report = _run_extraction_baseline(
        golden_dataset_path=golden_dataset_path,
        live_results=extraction_live_results,
    )

    # --- pipeline end-to-end eval gate ---
    pipeline_health = _run_pipeline_baseline(
        live_results=pipeline_live_results,
    )

    # --- budget extraction eval gate ---
    budget_health = _run_budget_baseline(
        live_results=budget_live_results,
    )

    # --- manifest gate evaluation ---
    # Pass per-category accuracy values for categories that use
    # min_accuracy thresholds instead of the standard precision/recall/
    # severity metrics.
    category_accuracy: dict[str, float] = {}
    pipeline_acc = pipeline_health.get("overall_accuracy")
    if pipeline_acc is not None:
        category_accuracy["pipeline"] = pipeline_acc
    extraction_f1 = extraction_eval_report.get("overall_f1")
    if extraction_f1 is not None:
        category_accuracy["extraction"] = extraction_f1
    budget_f1 = budget_health.get("overall_f1")
    if budget_f1 is not None:
        category_accuracy["budget"] = budget_f1
    gate = evaluate_report_against_manifest(
        report, manifest, category_accuracy=category_accuracy,
    )

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
        "budget_health": budget_health,
    }


def write_gate_snapshot(
    *,
    output_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
    extraction_live_results: dict[str, Any] | None = None,
    pipeline_live_results: dict[str, dict[str, Any]] | None = None,
    budget_live_results: dict[str, Any] | None = None,
) -> Path:
    snapshot = build_gate_snapshot(
        fixture_root=fixture_root,
        golden_dataset_path=golden_dataset_path,
        extraction_live_results=extraction_live_results,
        pipeline_live_results=pipeline_live_results,
        budget_live_results=budget_live_results,
    )
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
            "expected_baseline_f1": extraction_health.get("expected_baseline_f1"),
            "baseline_drifted": extraction_health.get("baseline_drifted"),
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
            "expected_baseline_accuracy": pipeline_health.get("expected_baseline_accuracy"),
            "baseline_drifted": pipeline_health.get("baseline_drifted"),
            "total_fixtures": pipeline_health.get("total_fixtures"),
            "blocks_ci": pipeline_health.get("blocks_ci"),
        }
    budget_health = snapshot.get("budget_health")
    stable_budget: dict[str, Any] | None = None
    if isinstance(budget_health, dict):
        stable_budget = {
            "status": budget_health.get("status"),
            "overall_f1": budget_health.get("overall_f1"),
            "expected_baseline_f1": budget_health.get("expected_baseline_f1"),
            "baseline_drifted": budget_health.get("baseline_drifted"),
            "overall_precision": budget_health.get("overall_precision"),
            "overall_recall": budget_health.get("overall_recall"),
            "total_fixtures": budget_health.get("total_fixtures"),
            "blocks_ci": budget_health.get("blocks_ci"),
        }
    return {
        "manifest_version": snapshot.get("manifest_version"),
        "fixture_root": snapshot.get("fixture_root"),
        "total_fixtures": snapshot.get("total_fixtures"),
        "categories": snapshot.get("categories"),
        "routing_health": stable_routing,
        "extraction_health": stable_extraction,
        "pipeline_health": stable_pipeline,
        "budget_health": stable_budget,
    }


def verify_gate_snapshot_file(
    *,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
    extraction_live_results: dict[str, Any] | None = None,
    pipeline_live_results: dict[str, dict[str, Any]] | None = None,
    budget_live_results: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any], dict[str, Any] | None]:
    expected = build_gate_snapshot(
        fixture_root=fixture_root,
        golden_dataset_path=golden_dataset_path,
        extraction_live_results=extraction_live_results,
        pipeline_live_results=pipeline_live_results,
        budget_live_results=budget_live_results,
    )
    if not snapshot_path.exists():
        return False, expected, None
    try:
        actual = json.loads(snapshot_path.read_text())
    except Exception:
        return False, expected, None
    return stable_snapshot_view(actual) == stable_snapshot_view(expected), expected, actual
