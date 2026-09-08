"""Build runtime D6 gate snapshots for public-surface authority decisions."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from src.evals.agentic_feedback import (
    DEFAULT_ROUTING_HEALTH_THRESHOLDS,
    build_routing_metrics,
    check_routing_health,
)

from .fixtures import AuditFixture, load_fixtures
from .gates import evaluate_report_against_manifest
from .manifest import load_manifest
from .rules.activity import run_activity_fixture
from .rules.extraction import load_golden_dataset, run_extraction_eval
from .rules.pipeline import load_pipeline_fixtures, run_pipeline_eval
from .rules.scenarios import (
    DEFAULT_SCENARIO_FIXTURES_PATH,
    load_scenario_fixtures,
    run_scenario_eval,
)
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
DEFAULT_COLLOQUIAL_GOLDEN_DATASET_PATH = Path(
    "data/fixtures/extraction/colloquial_golden.json"
)

# Colloquial extraction field mapping: golden field name -> pipeline fact name
# (identity mapping — the colloquial golden dataset speaks packet-fact names
# directly).  Fields outside this whitelist are not gated by the colloquial
# category; the list matches the packet facts exercised by the DEMO-02
# colloquial fixture catalog (destination / party / dates / budget / meals).
_COLLOQUIAL_FIELD_MAP = {
    "destination_candidates": "destination_candidates",
    "destination_status": "destination_status",
    "party_size": "party_size",
    "party_composition": "party_composition",
    "budget_min": "budget_min",
    "budget_max": "budget_max",
    "budget_currency": "budget_currency",
    "budget_scope": "budget_scope",
    "date_window": "date_window",
    "date_confidence": "date_confidence",
    "date_flexibility": "date_flexibility",
    "meal_preferences": "meal_preferences",
}


def _normalise_fact_value(value: Any) -> Any:
    """Collapse empty captures to ``None``.

    An empty list/dict from the pipeline means "field not captured"; treating
    it as ``None`` lets the extraction eval count a regression-to-empty as a
    false negative (recall hit) instead of a silent value mismatch.
    """
    if isinstance(value, (list, dict)) and len(value) == 0:
        return None
    return value

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
        # Map pipeline fact names to golden dataset field names. The golden
        # dataset expresses budget_amount as a composite string — "4000-6000"
        # for a range, "200/day" for a daily scope — composed here from the
        # pipeline's structured min/max/scope facts.
        min_slot = packet.facts.get("budget_min")
        max_slot = packet.facts.get("budget_max")
        scope_slot = packet.facts.get("budget_scope")
        amount_str: str | None = None
        if max_slot is not None and max_slot.value is not None:
            hi = str(max_slot.value)
            lo = str(min_slot.value) if min_slot is not None and min_slot.value is not None else hi
            amount_str = hi if lo == hi else f"{lo}-{hi}"
            if scope_slot is not None and scope_slot.value == "daily":
                amount_str = f"{hi}/day"
        extracted: dict[str, str | None] = {}
        for golden_field, pipeline_fact in _BUDGET_FIELD_MAP.items():
            if golden_field == "budget_amount":
                extracted[golden_field] = amount_str
                continue
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
EXPECTED_COLLOQUIAL_BASELINE_F1 = 1.0
# Mirror baseline for the gap/decision scenario lane: when expectations are
# graded against themselves the composite accuracy is 1.0.  The lane grades
# the real decision engine by default, so an honest run legitimately drifts
# from this constant (same semantics as the live budget lane).
EXPECTED_SCENARIO_BASELINE_ACCURACY = 1.0


def _collect_live_colloquial_results(
    golden_dataset_path: Path = DEFAULT_COLLOQUIAL_GOLDEN_DATASET_PATH,
) -> dict[str, dict[str, Any | None]]:
    """Run the real extraction pipeline on colloquial golden fixtures.

    Mirrors :func:`_collect_live_budget_results` (the F-18 budget gate): the
    raw JSON is loaded directly (which retains ``raw_input`` not captured by
    ``ExtractionFixture``), each fixture's ``raw_input`` is fed through
    ``ExtractionPipeline``, and the resulting CanonicalPacket facts are mapped
    onto the golden-dataset field names via ``_COLLOQUIAL_FIELD_MAP`` so
    ``run_extraction_eval`` can compare them against
    ``expected_extracted_fields``.

    Unlike the budget map (composite amount strings), the colloquial map is an
    identity mapping onto packet facts — list/dict/int values are compared
    structurally through the shared ``normalise`` comparison helpers.

    Returns a dict keyed by ``fixture_id`` with the mapped extracted fields.
    Returns an empty dict when the intake pipeline is not importable or the
    colloquial golden dataset is missing.
    """
    if not _HAS_INTAKE_PIPELINE or not golden_dataset_path.exists():
        return {}
    raw_data = json.loads(golden_dataset_path.read_text())
    pipeline = ExtractionPipeline()
    results: dict[str, dict[str, Any | None]] = {}
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
        extracted: dict[str, Any | None] = {}
        for golden_field, pipeline_fact in _COLLOQUIAL_FIELD_MAP.items():
            slot = packet.facts.get(pipeline_fact)
            if slot is not None and slot.value is not None:
                extracted[golden_field] = _normalise_fact_value(slot.value)
            else:
                extracted[golden_field] = None
        results[fixture_id] = extracted
    return results


def _collect_live_extraction_results(
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
) -> dict[str, dict[str, Any | None]]:
    """Run the real extraction pipeline over extraction golden fixtures.

    Mirrors :func:`_collect_live_colloquial_results`: fixtures that carry a
    ``raw_input`` are run through ``ExtractionPipeline`` and the resulting
    CanonicalPacket facts are mapped onto the golden field names so
    ``run_extraction_eval`` can grade them honestly.

    The current golden dataset (50 passport/visa/insurance fixtures) is a
    *document-vision* target set: it carries no ``raw_input`` at all, and
    the deterministic note pipeline does not emit document fields
    (``full_name``/``passport_number``/``visa_type``/... — those come from
    the LLM vision chain, which is excluded from deterministic CI).  The
    collector therefore returns an empty dict for today's dataset, which
    keeps the extraction lane on the flagged expected-as-actual fallback
    (see :func:`_run_extraction_baseline`) instead of silently pretending
    to grade.  The moment a fixture carries ``raw_input`` (or the pipeline
    grows document facts) it is graded live with no further changes.

    Returns a dict keyed by ``fixture_id`` with the mapped extracted
    fields.  Returns an empty dict when the intake pipeline is not
    importable, the golden dataset is missing, or no fixture yields a
    runnable live actual.
    """
    if not _HAS_INTAKE_PIPELINE or not golden_dataset_path.exists():
        return {}
    raw_data = json.loads(golden_dataset_path.read_text())
    pipeline = ExtractionPipeline()
    results: dict[str, dict[str, Any | None]] = {}
    for item in raw_data:
        fixture_id = item["fixture_id"]
        raw_input = item.get("raw_input", "")
        if not raw_input:
            # Vision-only document fixture: no input text exists to run.
            continue
        envelope = SourceEnvelope.from_freeform(
            raw_input,
            source="agency_notes",
            actor="agent",
        )
        packet = pipeline.extract([envelope])
        extracted: dict[str, Any | None] = {}
        for golden_field in item.get("expected_extracted_fields", {}):
            slot = packet.facts.get(golden_field)
            if slot is not None and slot.value is not None:
                extracted[golden_field] = _normalise_fact_value(slot.value)
            else:
                extracted[golden_field] = None
        results[fixture_id] = extracted
    return results


def _collect_live_pipeline_results(
    pipeline_fixture_path: Path = DEFAULT_PIPELINE_FIXTURE_PATH,
) -> dict[str, dict[str, Any]]:
    """Run the real intake pipeline over the end-to-end pipeline fixtures.

    Mirrors the budget/colloquial collector contract: each fixture that
    carries a ``raw_note`` is run through ``ExtractionPipeline`` and the
    stage actuals the deterministic pipeline genuinely produces are
    returned keyed by ``fixture_id`` (``extraction``/``agents``/
    ``decision``).

    Contract honesty note: today the 7 golden pipeline fixtures expect an
    aspirational end-to-end whose stages have no deterministic in-process
    producer — ``extraction`` expects document-vision fields, ``agents``
    expects trip-agent outputs whose vocabulary (e.g. ``missing_fields``)
    is authored against imagined contracts, and ``decision`` expects a
    ``trip_status``/``stage`` vocabulary the in-process ``DecisionResult``
    does not emit.  Grading note-facts against document expectations would
    be a category error, so this collector emits a fixture result only
    when at least one stage has a genuine actual, and returns an empty
    dict when none do — which routes the lane to the flagged
    expected-as-actual fallback in :func:`_run_pipeline_baseline` instead
    of a false 0.0.  When a deterministic producer for any stage lands,
    this collector grades it live with no further changes.

    Returns an empty dict when the intake pipeline is not importable, the
    fixture file is missing, or no fixture yields a gradable actual.
    """
    if not _HAS_INTAKE_PIPELINE or not pipeline_fixture_path.exists():
        return {}
    fixtures = load_pipeline_fixtures(pipeline_fixture_path)
    pipeline = ExtractionPipeline()
    results: dict[str, dict[str, Any]] = {}
    for fixture in fixtures:
        raw_note = (fixture.raw_input or {}).get("raw_note", "")
        if not raw_note:
            continue
        envelope = SourceEnvelope.from_freeform(
            raw_note,
            source="agency_notes",
            actor="agent",
        )
        packet = pipeline.extract([envelope])
        # Document-extraction stage actual: the packet's document fields.
        # None of the golden document fields are note-facts today, so this
        # mapping is empty until the pipeline emits document facts.
        extraction_actual: dict[str, Any] = {}
        for doc_field in fixture.expected_extraction or {}:
            slot = packet.facts.get(doc_field)
            if slot is not None and slot.value is not None:
                extraction_actual[doc_field] = _normalise_fact_value(slot.value)
        if not extraction_actual:
            # No stage has a genuine deterministic actual yet — emitting an
            # empty per-stage shell would grade as false negatives, so skip
            # the fixture (flagged-fallback contract, see docstring).
            continue
        results[fixture.fixture_id] = {"extraction": extraction_actual}
    return results


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
    live_grading = False
    actual_source = "expected_fixture_mirror"
    if live_results is not None:
        report = run_extraction_eval(fixtures, saved_results=live_results)
        note = "Live extraction results used for F1 evaluation."
        live_grading = True
        actual_source = "caller_supplied_actuals"
    else:
        # Live-first: grade the real pipeline like the budget/colloquial
        # gates do.  The golden dataset is a document-vision target set
        # with no raw_input, so the live collector yields nothing today
        # and the flagged fallback below engages with the honest reason.
        live = _collect_live_extraction_results(golden_dataset_path)
        if live:
            report = run_extraction_eval(fixtures, saved_results=live)
            note = "Live pipeline extraction results used for extraction F1 evaluation."
            live_grading = True
            actual_source = "live_pipeline"
        else:
            saved = {f.fixture_id: f.expected_extracted_fields for f in fixtures}
            report = run_extraction_eval(fixtures, saved_results=saved)
            if _HAS_INTAKE_PIPELINE:
                note = (
                    "Baseline using expected outputs as actuals (golden fixtures "
                    "carry no raw_input; document vision extraction has no "
                    "deterministic producer)."
                )
            else:
                note = (
                    "Baseline using expected outputs as actuals (intake pipeline "
                    "unavailable)."
                )
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
        "live_grading": live_grading,
        "actual_source": actual_source,
        "evidence_tier": 2 if live_grading else 0,
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
    live_grading = False
    actual_source = "expected_fixture_mirror"
    if live_results is not None:
        actual_results = live_results
        note = "Live pipeline results used for accuracy evaluation."
        live_grading = True
        actual_source = "caller_supplied_actuals"
    else:
        # Live-first: grade the real intake pipeline like the budget/
        # colloquial gates do.  The golden fixtures expect document-vision,
        # trip-agent, and trip-status contracts with no deterministic
        # in-process producer, so the live collector yields nothing today
        # and the flagged fallback below engages with the honest reason.
        live = _collect_live_pipeline_results(pipeline_fixture_path)
        if live:
            actual_results = live
            note = "Live pipeline results used for accuracy evaluation (in-process intake pipeline)."
            live_grading = True
            actual_source = "live_pipeline"
        else:
            actual_results = {
                f.fixture_id: {
                    "extraction": f.expected_extraction,
                    "agents": f.expected_agents,
                    "decision": f.expected_decision,
                }
                for f in fixtures
            }
            if _HAS_INTAKE_PIPELINE:
                note = (
                    "Baseline using expected outputs as actuals (pipeline fixtures "
                    "expect document/agent/decision contracts with no deterministic "
                    "in-process producer)."
                )
            else:
                note = (
                    "Baseline using expected outputs as actuals (intake pipeline "
                    "unavailable)."
                )
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
        "live_grading": live_grading,
        "actual_source": actual_source,
        "evidence_tier": 2 if live_grading else 0,
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
    live_grading = False
    actual_source = "expected_fixture_mirror"
    if live_results is not None:
        report = run_extraction_eval(fixtures, saved_results=live_results)
        note = "Live budget results used for F1 evaluation."
        live_grading = True
        actual_source = "caller_supplied_actuals"
    else:
        # Attempt to collect live results from the real extraction pipeline.
        live = _collect_live_budget_results(golden_dataset_path)
        if live:
            report = run_extraction_eval(fixtures, saved_results=live)
            note = "Live pipeline extraction results used for budget F1 evaluation."
            live_grading = True
            actual_source = "live_pipeline"
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
        "live_grading": live_grading,
        "actual_source": actual_source,
        "evidence_tier": 2 if live_grading else 0,
        "note": note,
    }


def _run_colloquial_baseline(
    *,
    golden_dataset_path: Path = DEFAULT_COLLOQUIAL_GOLDEN_DATASET_PATH,
    live_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run colloquial extraction eval against the golden dataset.

    Live-pipeline gate for the DEMO-02 colloquial fixture set (destination
    verb-object/city sets, party group phrasings, season/flexibility dates,
    per-person budget "each", and the full demo note).  Mirrors
    :func:`_run_budget_baseline`: with no ``live_results`` the real pipeline
    is executed via :func:`_collect_live_colloquial_results`; when the intake
    pipeline is not importable the comparison falls back to a self-consistent
    baseline (expected as actuals) so CI without full dependencies still
    validates comparison logic.
    """
    if not golden_dataset_path.exists():
        return {
            "status": "unavailable",
            "reason": "colloquial_golden_dataset_missing",
            "total_fixtures": 0,
            "overall_f1": 0.0,
            "blocks_ci": False,
        }
    fixtures = load_golden_dataset(golden_dataset_path)
    live_grading = False
    actual_source = "expected_fixture_mirror"
    if live_results is not None:
        report = run_extraction_eval(fixtures, saved_results=live_results)
        note = "Live colloquial results used for F1 evaluation."
        live_grading = True
        actual_source = "caller_supplied_actuals"
    else:
        # Attempt to collect live results from the real extraction pipeline.
        live = _collect_live_colloquial_results(golden_dataset_path)
        if live:
            report = run_extraction_eval(fixtures, saved_results=live)
            note = "Live pipeline extraction results used for colloquial F1 evaluation."
            live_grading = True
            actual_source = "live_pipeline"
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
        "expected_baseline_f1": EXPECTED_COLLOQUIAL_BASELINE_F1,
        "baseline_drifted": overall_f1 != EXPECTED_COLLOQUIAL_BASELINE_F1,
        "live_grading": live_grading,
        "actual_source": actual_source,
        "evidence_tier": 2 if live_grading else 0,
        "note": note,
    }


class _ScenarioActualsShim:
    """Adapt pre-computed per-scenario actuals to the decision-result shape.

    Used when ``scenario_live_results`` is passed explicitly to
    :func:`build_gate_snapshot` (degraded-run simulations, mirroring how the
    other lanes accept explicit live results).  Each value is a dict with
    ``decision_state`` (str), ``hard_blockers`` (int) and ``contradictions``
    (bool).
    """

    def __init__(self, actuals: dict[str, dict[str, Any]]):
        self._actuals = actuals

    def __call__(self, packet: Any) -> Any:
        actual = self._actuals.get(packet.packet_id)
        if actual is None:
            raise KeyError(packet.packet_id)
        return _ScenarioDecisionView(actual)


class _ScenarioDecisionView:
    """Duck-typed DecisionResult view over a plain actuals dict."""

    def __init__(self, actual: dict[str, Any]):
        self.decision_state = actual.get("decision_state")
        self.hard_blockers = list(range(actual.get("hard_blockers", 0)))
        self.contradictions = [{}] if actual.get("contradictions") else []


def _collect_live_scenario_results(
    fixtures_path: Path = DEFAULT_SCENARIO_FIXTURES_PATH,
) -> dict[str, dict[str, Any]]:
    """Run the 30-scenario gap/decision corpus through the real engine.

    The corpus (``data/fixtures/test_scenarios.py``) covers five failure-mode
    families — basic flows, contradictions, authority precedence, stage
    progression, edge/hybrid cases — and was wired into nothing before this
    lane existed (EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT 2026-08-31 §1.2).
    Each scenario packet is converted to production packet models and run
    through ``run_gap_and_decision``; grading happens in
    :func:`_run_scenario_baseline`.

    Returns a dict keyed by packet_id with the actual decision outcome,
    or an empty dict when the decision engine is not importable or the
    corpus file is missing.
    """
    if not _HAS_INTAKE_PIPELINE or not fixtures_path.exists():
        return {}
    scenario_fixtures = load_scenario_fixtures(fixtures_path)
    # The graded axes (decision_state / hard_blockers / contradictions) are
    # produced by the deterministic rule machine; the flag-gated hybrid risk
    # engine only enriches risk flags. Preserve the caller's configured mode
    # so D6 exercises the same mode as the serving path. CI supplies
    # USE_HYBRID_DECISION_ENGINE=1 explicitly. If this helper is called
    # locally without a value, set the serving default explicitly for the
    # duration of the run. The scenario corpus does not authorize provider
    # calls; absent provider credentials leave only deterministic rules and
    # the engine's safe fallback executable.
    from src.intake import decision as _decision

    saved_flag = os.environ.get("USE_HYBRID_DECISION_ENGINE")
    if saved_flag is None:
        os.environ["USE_HYBRID_DECISION_ENGINE"] = "1"
    try:
        _decision._reset_hybrid_engine()
        report = run_scenario_eval(scenario_fixtures)
    finally:
        if saved_flag is None:
            os.environ.pop("USE_HYBRID_DECISION_ENGINE", None)
        else:
            os.environ["USE_HYBRID_DECISION_ENGINE"] = saved_flag
        _decision._reset_hybrid_engine()
    actuals: dict[str, dict[str, Any]] = {}
    for fixture, result in zip(scenario_fixtures, report.results):
        if result.error is not None:
            continue
        actuals[fixture.packet.packet_id] = {
            "decision_state": result.actual_decision_state,
            "hard_blockers": result.actual_hard_blockers,
            "contradictions": result.actual_contradictions,
        }
    return actuals


def _run_scenario_baseline(
    *,
    fixtures_path: Path = DEFAULT_SCENARIO_FIXTURES_PATH,
    scenario_live_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the gap/decision scenario lane against the real decision engine.

    This lane is live-by-default: unlike the extraction/pipeline lanes it
    has a fully deterministic producer (the corpus packets + the rule-based
    decision engine), so honest composite accuracy is graded on every run.
    When the decision engine is not importable the comparison falls back to
    a self-consistent baseline (expected as actuals) so CI without full
    dependencies still validates grading logic.

    The manifest category ``gap_decision`` is currently ``shadow``: the
    honest composite accuracy (0.57 at introduction — the corpus was authored
    against earlier NB02 semantics) does not meet the 0.95 gating bar, so it
    is reported and hash-tracked without blocking CI.  Flip it to ``gating``
    once triaged.
    """
    if not fixtures_path.exists():
        return {
            "status": "unavailable",
            "reason": "scenario_fixtures_missing",
            "total_fixtures": 0,
            "overall_accuracy": 0.0,
            "blocks_ci": False,
        }
    scenario_fixtures = load_scenario_fixtures(fixtures_path)
    configured_hybrid_flag = os.environ.get("USE_HYBRID_DECISION_ENGINE")
    # Record the canonical effective value rather than raw environment
    # provenance.  This keeps a local run with the serving default (unset)
    # comparable to CI/deployments that explicitly declare the same value.
    # PA-03 (2026-09-06): the serving default flipped to OFF — determinism is
    # architectural, not credential-accidental — so an unset variable now
    # records "0", keeping the snapshot able to catch CI/serving divergence.
    effective_hybrid_value = (
        configured_hybrid_flag
        if configured_hybrid_flag is not None
        else "0"
    )
    hybrid_config = {
        "environment_variable": "USE_HYBRID_DECISION_ENGINE",
        "configured_value": effective_hybrid_value,
        "effective_enabled": effective_hybrid_value == "1",
        "default_enabled": False,
        "evaluation_contract": "deterministic_authority_axes",
        "provider_calls_authorized": False,
    }
    mirror = False
    live_grading = False
    actual_source = "expected_fixture_mirror"
    if scenario_live_results is not None:
        decision_fn: Any = _ScenarioActualsShim(scenario_live_results)
        note = "Pre-computed scenario actuals used for accuracy evaluation."
        live_grading = True
        actual_source = "caller_supplied_actuals"
    else:
        live = _collect_live_scenario_results(fixtures_path)
        if live:
            # Grade from the collector's captured engine outcomes so the
            # engine runs exactly once per snapshot build.
            decision_fn = _ScenarioActualsShim(live)
            note = "Live gap/decision engine results used for accuracy evaluation."
            live_grading = True
            actual_source = "live_decision_engine"
        else:
            # Decision engine unavailable: grade expectations against
            # themselves (self-consistent baseline, mirroring the other
            # lanes' import-failure fallback semantics).
            mirror = True
            note = (
                "Baseline using expected outputs as actuals (decision engine "
                "unavailable)."
            )

    if mirror:
        def mirror_decision_fn(fixture: Any) -> Any:
            return _ScenarioDecisionView({
                "decision_state": fixture.expected_decision_state,
                "hard_blockers": fixture.expected_hard_blockers or 0,
                "contradictions": fixture.expected_contradictions,
            })

        report = run_scenario_eval(scenario_fixtures, decision_fn=mirror_decision_fn)
    else:
        report = run_scenario_eval(scenario_fixtures, decision_fn=decision_fn)
    summary = report.summary()
    overall_acc = summary["fixture_accuracy"]
    if overall_acc >= 0.95:
        status = "passing"
    elif overall_acc >= 0.80:
        status = "warning"
    else:
        status = "failing"
    return {
        "status": status,
        "overall_accuracy": overall_acc,
        "decision_state_accuracy": summary["decision_state_accuracy"],
        "hard_blocker_accuracy": summary["hard_blocker_accuracy"],
        "contradiction_accuracy": summary["contradiction_accuracy"],
        "total_fixtures": summary["total_fixtures"],
        "fixtures_passing": summary["fixtures_passing"],
        "fixtures_failing": summary["fixtures_failing"],
        "blocks_ci": status == "failing",
        "expected_baseline_accuracy": EXPECTED_SCENARIO_BASELINE_ACCURACY,
        "baseline_drifted": overall_acc != EXPECTED_SCENARIO_BASELINE_ACCURACY,
        "live_grading": live_grading,
        "actual_source": actual_source,
        "evidence_tier": 2 if live_grading else 0,
        "note": note,
        "hybrid_config": hybrid_config,
    }


def build_gate_snapshot(
    *,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
    extraction_live_results: dict[str, Any] | None = None,
    pipeline_live_results: dict[str, dict[str, Any]] | None = None,
    budget_live_results: dict[str, Any] | None = None,
    colloquial_live_results: dict[str, Any] | None = None,
    scenario_live_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixture_root)
    manifest = load_manifest()
    report = run_eval_suite(fixtures, rule_runner=_rule_dispatch)

    # --- routing health gate ---
    routing_metrics = build_routing_metrics([])
    routing_health = check_routing_health(routing_metrics)

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

    # --- colloquial extraction eval gate (DEMO-02 / IMP-07) ---
    colloquial_health = _run_colloquial_baseline(
        live_results=colloquial_live_results,
    )

    # --- gap/decision scenario gate (30-scenario corpus, live engine) ---
    scenario_health = _run_scenario_baseline(
        scenario_live_results=scenario_live_results,
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
    colloquial_f1 = colloquial_health.get("overall_f1")
    if colloquial_f1 is not None:
        category_accuracy["colloquial"] = colloquial_f1
    scenario_acc = scenario_health.get("overall_accuracy")
    if scenario_acc is not None:
        category_accuracy["gap_decision"] = scenario_acc
    # Public authority requires an independent actual producer.  Mirror
    # baselines are intentionally retained for evaluator calibration, but a
    # perfect expected-vs-expected score must never authorize a product
    # surface or hide that the producer is absent.
    category_authority = {
        "extraction": extraction_eval_report.get("actual_source") != "expected_fixture_mirror",
        "pipeline": pipeline_health.get("actual_source") != "expected_fixture_mirror",
        "budget": budget_health.get("actual_source") != "expected_fixture_mirror",
        "colloquial": colloquial_health.get("actual_source") != "expected_fixture_mirror",
        "gap_decision": scenario_health.get("actual_source") != "expected_fixture_mirror",
    }
    gate = evaluate_report_against_manifest(
        report,
        manifest,
        category_accuracy=category_accuracy,
        category_authority=category_authority,
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

    # The scenario health dict must reflect actual CI impact: the lane is
    # shadow, so a failing honest score is reported but does not block.
    gap_category = categories.get("gap_decision")
    if isinstance(gap_category, dict):
        scenario_health["blocks_ci"] = bool(gap_category.get("blocks_ci"))

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
            "alerts": [asdict(a) for a in routing_health.alerts],
            "metrics_snapshot": routing_health.metrics_snapshot,
            "checked_at": routing_health.checked_at.isoformat(),
        },
        "extraction_health": extraction_eval_report,
        "pipeline_health": pipeline_health,
        "budget_health": budget_health,
        "colloquial_health": colloquial_health,
        "scenario_health": scenario_health,
    }


def write_gate_snapshot(
    *,
    output_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
    extraction_live_results: dict[str, Any] | None = None,
    pipeline_live_results: dict[str, dict[str, Any]] | None = None,
    budget_live_results: dict[str, Any] | None = None,
    colloquial_live_results: dict[str, Any] | None = None,
    scenario_live_results: dict[str, dict[str, Any]] | None = None,
) -> Path:
    snapshot = build_gate_snapshot(
        fixture_root=fixture_root,
        golden_dataset_path=golden_dataset_path,
        extraction_live_results=extraction_live_results,
        pipeline_live_results=pipeline_live_results,
        budget_live_results=budget_live_results,
        colloquial_live_results=colloquial_live_results,
        scenario_live_results=scenario_live_results,
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
            "alerts": routing_health.get("alerts"),
            "metrics_snapshot": routing_health.get("metrics_snapshot"),
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
            "live_grading": extraction_health.get("live_grading"),
            "actual_source": extraction_health.get("actual_source"),
            "evidence_tier": extraction_health.get("evidence_tier"),
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
            "live_grading": pipeline_health.get("live_grading"),
            "actual_source": pipeline_health.get("actual_source"),
            "evidence_tier": pipeline_health.get("evidence_tier"),
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
            "live_grading": budget_health.get("live_grading"),
            "actual_source": budget_health.get("actual_source"),
            "evidence_tier": budget_health.get("evidence_tier"),
        }
    colloquial_health = snapshot.get("colloquial_health")
    stable_colloquial: dict[str, Any] | None = None
    if isinstance(colloquial_health, dict):
        stable_colloquial = {
            "status": colloquial_health.get("status"),
            "overall_f1": colloquial_health.get("overall_f1"),
            "expected_baseline_f1": colloquial_health.get("expected_baseline_f1"),
            "baseline_drifted": colloquial_health.get("baseline_drifted"),
            "overall_precision": colloquial_health.get("overall_precision"),
            "overall_recall": colloquial_health.get("overall_recall"),
            "total_fixtures": colloquial_health.get("total_fixtures"),
            "blocks_ci": colloquial_health.get("blocks_ci"),
            # by_document_type / by_difficulty carry fixture_accuracy; a pure
            # value mismatch (expected X, actual Y) moves fixture accuracy
            # without moving precision/recall, so it must be part of the
            # comparable view for drift detection to catch it.
            "by_document_type": colloquial_health.get("by_document_type"),
            "by_difficulty": colloquial_health.get("by_difficulty"),
            "live_grading": colloquial_health.get("live_grading"),
            "actual_source": colloquial_health.get("actual_source"),
            "evidence_tier": colloquial_health.get("evidence_tier"),
        }
    scenario_health = snapshot.get("scenario_health")
    stable_scenario: dict[str, Any] | None = None
    if isinstance(scenario_health, dict):
        stable_scenario = {
            "status": scenario_health.get("status"),
            "overall_accuracy": scenario_health.get("overall_accuracy"),
            "decision_state_accuracy": scenario_health.get("decision_state_accuracy"),
            "hard_blocker_accuracy": scenario_health.get("hard_blocker_accuracy"),
            "expected_baseline_accuracy": scenario_health.get("expected_baseline_accuracy"),
            "baseline_drifted": scenario_health.get("baseline_drifted"),
            "total_fixtures": scenario_health.get("total_fixtures"),
            "blocks_ci": scenario_health.get("blocks_ci"),
            "live_grading": scenario_health.get("live_grading"),
            "actual_source": scenario_health.get("actual_source"),
            "evidence_tier": scenario_health.get("evidence_tier"),
            "hybrid_config": scenario_health.get("hybrid_config"),
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
        "colloquial_health": stable_colloquial,
        "scenario_health": stable_scenario,
    }


def verify_gate_snapshot_file(
    *,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    golden_dataset_path: Path = DEFAULT_GOLDEN_DATASET_PATH,
    extraction_live_results: dict[str, Any] | None = None,
    pipeline_live_results: dict[str, dict[str, Any]] | None = None,
    budget_live_results: dict[str, Any] | None = None,
    colloquial_live_results: dict[str, Any] | None = None,
    scenario_live_results: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool, dict[str, Any], dict[str, Any] | None]:
    expected = build_gate_snapshot(
        fixture_root=fixture_root,
        golden_dataset_path=golden_dataset_path,
        extraction_live_results=extraction_live_results,
        pipeline_live_results=pipeline_live_results,
        budget_live_results=budget_live_results,
        colloquial_live_results=colloquial_live_results,
        scenario_live_results=scenario_live_results,
    )
    if not snapshot_path.exists():
        return False, expected, None
    try:
        actual = json.loads(snapshot_path.read_text())
    except Exception:
        return False, expected, None
    return stable_snapshot_view(actual) == stable_snapshot_view(expected), expected, actual
