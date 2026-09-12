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


def test_n02_corpus_carries_raw_input_but_collector_stays_empty_until_producer() -> None:
    """N-02 (2026-09-11): corpus is runnable, but no producer emits doc facts.

    Every golden fixture now carries an authored ``raw_input`` text layer
    (simulated OCR/confirmation text matching its expected fields), so the
    lane is runnable for provider/producer enablement.  The deterministic
    note pipeline emits no document facts, so the collector must still
    return an empty dict — an all-None shell would grade as false negatives
    (category error) — and expected labels must not be promoted to actuals.
    """
    rows = json.loads(EXTRACTION_FIXTURES.read_text())

    assert len(rows) == 50
    assert {row["document_type"] for row in rows} == {"passport", "visa", "insurance"}
    assert all(isinstance(row.get("raw_input"), str) and row["raw_input"].strip() for row in rows)
    # The authored text must actually carry each fixture's non-null expected
    # field values so a future deterministic text producer can be graded
    # against it without re-authoring.
    for row in rows:
        for field_name, expected in row["expected_extracted_fields"].items():
            if expected is not None:
                assert expected in row["raw_input"], (
                    f"{row['fixture_id']}: expected {field_name}={expected!r} "
                    "missing from authored raw_input"
                )
    assert all(not row.get("input_ref") for row in rows)
    assert all(not row.get("input_sha256") for row in rows)

    # No deterministic producer emits document facts yet.  An empty result
    # is the safe signal; the lane stays on the flagged calibration
    # fallback (evidence tier 0) and flips live automatically once a
    # text-path document producer emits packet facts.
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
