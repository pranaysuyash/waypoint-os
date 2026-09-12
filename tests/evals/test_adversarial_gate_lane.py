"""E-08 — adversarial-input D6 gate lane (adversarial_health) snapshot tests.

The lane grades the promoted gating_candidate records
(``data/fixtures/adversarial/adversarial_golden.json``) live through the
in-process intake pipeline by property contract and feeds the manifest
category ``adversarial`` (gating, min_accuracy 1.0 — regression ratchet).
"""

from __future__ import annotations

import json
from pathlib import Path

from src.evals.audit.snapshot import (
    EXPECTED_ADVERSARIAL_BASELINE_ACCURACY,
    build_gate_snapshot,
    stable_snapshot_view,
    verify_gate_snapshot_file,
    write_gate_snapshot,
)


def test_adversarial_baseline_accuracy_constant_matches():
    """The adversarial baseline constant is the honest live baseline (1.0)."""
    assert EXPECTED_ADVERSARIAL_BASELINE_ACCURACY == 1.0


def test_build_gate_snapshot_includes_adversarial_health():
    """The lane is live-by-default and grades the promoted records at 1.0."""
    snapshot = build_gate_snapshot()
    ah = snapshot["adversarial_health"]
    assert isinstance(ah, dict)
    assert ah["total_fixtures"] == 21
    assert ah["actual_source"] == "live_extraction_pipeline"
    assert ah["live_grading"] is True
    assert ah["evidence_tier"] == 2
    assert ah["overall_accuracy"] == 1.0
    assert ah["property_accuracy"] == 1.0
    assert ah["fixtures_passing"] == 21
    assert ah["fixtures_failing"] == 0
    assert ah["status"] == "passing"
    assert ah["baseline_drifted"] is False
    assert ah["blocks_ci"] is False


def test_adversarial_manifest_category_present_and_gating():
    snapshot = build_gate_snapshot()
    assert "adversarial" in snapshot["categories"]
    cat = snapshot["categories"]["adversarial"]
    assert cat["status"] == "gating"
    assert cat["meets_thresholds"] is True
    assert cat["blocks_ci"] is False
    # Live-graded with an independent actual producer: authority applies.
    assert cat["authoritative_for_public_surface"] is True
    assert "actual_source_not_independent" not in cat["reasons"]


def test_adversarial_manifest_category_min_accuracy_threshold():
    from src.evals.audit.manifest import load_manifest

    config = load_manifest().categories["adversarial"]
    assert config.min_accuracy == 1.0
    assert config.status == "gating"


def test_adversarial_single_property_regression_blocks_ci():
    """One violated property on one record must trip drift AND block CI.

    Simulated via pre-computed grades (the lane's degraded-run input path),
    mirroring how the colloquial lane's drift tests inject degraded results.
    """
    snapshot = build_gate_snapshot(
        adversarial_live_results={"adv_bound_004": ["adv_bound_004: banned value leaked"]}
    )
    ah = snapshot["adversarial_health"]
    assert ah["overall_accuracy"] < 1.0
    assert ah["baseline_drifted"] is True
    # 20/21 records passing = 0.9524 → lane status still "passing", but the
    # gating category blocks because min_accuracy is 1.0 (ratchet).
    assert ah["status"] == "passing"
    assert ah["blocks_ci"] is True
    cat = snapshot["categories"]["adversarial"]
    assert cat["meets_thresholds"] is False
    assert "accuracy_below_threshold" in cat["reasons"]
    assert cat["blocks_ci"] is True


def test_adversarial_stable_view_carries_lane_and_strips_note():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    ah = stable["adversarial_health"]
    assert isinstance(ah, dict)
    assert "status" in ah
    assert "overall_accuracy" in ah
    assert "property_accuracy" in ah
    assert "baseline_drifted" in ah
    assert "blocks_ci" in ah
    # Volatile note field must not be part of the comparable view.
    assert "note" not in ah


def test_verify_detects_adversarial_accuracy_tampering(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["adversarial_health"]["overall_accuracy"] = 0.9
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


def test_verify_detects_adversarial_category_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["categories"]["adversarial"]["status"] = "shadow"
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False
