"""Executable provenance probes for the N-02/N-03 evaluation lanes.

These tests deliberately describe the current *open* state of the document
and pipeline lanes.  They are not quality scores.  Their purpose is to make
the absence of an independent producer visible and regression-sensitive:
adding an input artifact or a stage producer must update the durable contract
and promotion evidence rather than silently changing a mirror into authority.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.evals.audit.rules.pipeline import load_pipeline_fixtures
from src.evals.audit.snapshot import (
    _collect_live_extraction_results,
    _collect_live_pipeline_results,
    build_gate_snapshot,
)
from src.intake.extractors import ExtractionPipeline
from src.intake.packet_models import SourceEnvelope


ROOT = Path(__file__).resolve().parents[2]
EXTRACTION_FIXTURES = ROOT / "data/fixtures/extraction/golden_dataset.json"
PIPELINE_FIXTURES = ROOT / "data/fixtures/pipeline/pipeline_golden.json"


def _leaf_paths(value: object, prefix: str = "") -> set[str]:
    """Return dotted paths for nested expected-stage fields."""
    if not isinstance(value, dict):
        return {prefix}
    paths: set[str] = set()
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        paths.update(_leaf_paths(child, path))
    return paths


def test_n02_corpus_has_no_retrievable_input_and_collector_stays_empty() -> None:
    """N-02 must remain an explicit shadow gap until artifacts are supplied."""
    rows = json.loads(EXTRACTION_FIXTURES.read_text())

    assert len(rows) == 50
    assert {row["document_type"] for row in rows} == {"passport", "visa", "insurance"}
    assert all(not row.get("raw_input") for row in rows)
    assert all(not row.get("input_ref") for row in rows)
    assert all(not row.get("input_sha256") for row in rows)

    # No source artifact means no independent actuals.  An empty result is
    # the safe signal; expected labels must not be promoted to actuals.
    assert _collect_live_extraction_results(EXTRACTION_FIXTURES) == {}


def test_n03_notes_do_not_masquerade_as_document_stage_inputs() -> None:
    """N-03 note extraction and document extraction remain disjoint stages."""
    fixtures = load_pipeline_fixtures(PIPELINE_FIXTURES)
    assert len(fixtures) == 7

    pipeline = ExtractionPipeline()
    for fixture in fixtures:
        raw_note = fixture.raw_input.get("raw_note")
        assert isinstance(raw_note, str) and raw_note.strip()

        packet = pipeline.extract([
            SourceEnvelope.from_freeform(
                raw_note,
                source="agency_notes",
                actor="eval_probe",
            )
        ])
        emitted_fact_names = set(packet.facts)
        expected_document_paths = _leaf_paths(fixture.expected_extraction)
        expected_document_names = expected_document_paths | {
            path.rsplit(".", 1)[-1] for path in expected_document_paths
        }

        # The note pipeline emits packet facts such as destination/date/budget;
        # it does not produce passport/visa/insurance document fields.  This
        # assertion prevents a future evaluator shortcut based on name overlap.
        assert not emitted_fact_names.intersection(expected_document_names)

    # A partial note result is not an end-to-end actual.  Until document,
    # agent, and decision stage producers are composed, the collector must
    # remain empty and the lane must remain calibration-only.
    assert _collect_live_pipeline_results(PIPELINE_FIXTURES) == {}


def test_n02_n03_mirror_scores_are_not_public_authority() -> None:
    """Perfect expected-vs-expected scores remain explicitly non-authoritative."""
    snapshot = build_gate_snapshot()

    extraction = snapshot["extraction_health"]
    assert extraction["actual_source"] == "expected_fixture_mirror"
    assert extraction["live_grading"] is False
    assert extraction["evidence_tier"] == 0

    pipeline = snapshot["pipeline_health"]
    assert pipeline["actual_source"] == "expected_fixture_mirror"
    assert pipeline["live_grading"] is False
    assert pipeline["evidence_tier"] == 0

    assert snapshot["categories"]["extraction"]["authoritative_for_public_surface"] is False
    assert snapshot["categories"]["pipeline"]["authoritative_for_public_surface"] is False
