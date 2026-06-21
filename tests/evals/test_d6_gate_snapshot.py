import json
from pathlib import Path

from src.evals.audit.snapshot import (
    build_gate_snapshot,
    stable_snapshot_view,
    verify_gate_snapshot_file,
    write_gate_snapshot,
)


def test_build_gate_snapshot_includes_activity_gate_and_metrics():
    snapshot = build_gate_snapshot()
    assert snapshot["manifest_version"] == 1
    assert snapshot["total_fixtures"] >= 1
    assert "activity" in snapshot["categories"]
    activity = snapshot["categories"]["activity"]
    assert activity["status"] == "shadow"
    assert activity["authoritative_for_public_surface"] is False
    assert isinstance(activity["metrics"], dict)


def test_build_gate_snapshot_includes_routing_health_gate():
    snapshot = build_gate_snapshot()
    rh = snapshot["routing_health"]
    assert rh["status"] == "healthy"
    assert rh["blocks_ci"] is False
    assert isinstance(rh["thresholds"], dict)
    assert rh["thresholds"]["fallback_trigger_rate_warning"] == 0.3
    assert rh["thresholds"]["latency_p95_ms_critical"] == 30_000
    assert "checked_at" in rh


def test_stable_snapshot_view_strips_volatile_timestamp_from_routing_health():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    rh = stable["routing_health"]
    assert isinstance(rh, dict)
    assert "status" in rh
    assert "blocks_ci" in rh
    assert "thresholds" in rh
    # Volatile timestamp must not be present
    assert "checked_at" not in rh


def test_build_gate_snapshot_routing_health_baseline_healthy():
    """With no live data, routing health should always be healthy."""
    snapshot = build_gate_snapshot()
    rh = snapshot["routing_health"]
    assert rh["status"] == "healthy"
    assert rh["blocks_ci"] is False


def test_write_gate_snapshot_creates_json_file(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    written = write_gate_snapshot(output_path=output)
    assert written == output
    payload = json.loads(output.read_text())
    assert payload["categories"]["budget"]["status"] == "gating"
    assert "generated_at" in payload
    assert "routing_health" in payload


def test_write_gate_snapshot_routing_health_in_json(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    payload = json.loads(output.read_text())
    rh = payload["routing_health"]
    assert rh["status"] == "healthy"
    assert isinstance(rh["thresholds"], dict)
    assert len(rh["thresholds"]) >= 6


def test_verify_gate_snapshot_file_detects_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is True

    payload = json.loads(output.read_text())
    payload["categories"]["activity"]["status"] = "gating"
    output.write_text(json.dumps(payload, indent=2))

    ok, expected, actual = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False
    assert expected["categories"]["activity"]["status"] == "shadow"
    assert actual["categories"]["activity"]["status"] == "gating"


def test_verify_gate_snapshot_detects_routing_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is True

    # Tamper with routing_health thresholds
    payload = json.loads(output.read_text())
    payload["routing_health"]["thresholds"]["fallback_trigger_rate_warning"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, expected, actual = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False
    assert expected["routing_health"]["thresholds"]["fallback_trigger_rate_warning"] == 0.3
    assert actual["routing_health"]["thresholds"]["fallback_trigger_rate_warning"] == 0.99


def test_verify_gate_snapshot_detects_routing_health_status_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["routing_health"]["status"] = "critical"
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


# --- extraction_health gate tests ---


def test_build_gate_snapshot_includes_extraction_health():
    snapshot = build_gate_snapshot()
    eh = snapshot["extraction_health"]
    assert isinstance(eh, dict)
    assert "status" in eh
    assert "overall_f1" in eh
    assert "overall_precision" in eh
    assert "overall_recall" in eh
    assert "total_fixtures" in eh
    assert eh["total_fixtures"] == 50
    assert "by_document_type" in eh
    assert "by_difficulty" in eh
    # Baseline with no live results: all expected fields become false negatives
    assert eh["status"] == "failing"
    assert eh["overall_f1"] == 0.0
    assert eh["blocks_ci"] is True


def test_stable_snapshot_view_strips_extraction_health_volatile_fields():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    eh = stable["extraction_health"]
    assert isinstance(eh, dict)
    assert "status" in eh
    assert "overall_f1" in eh
    assert "blocks_ci" in eh
    # Volatile note field must not be present
    assert "note" not in eh


def test_write_gate_snapshot_includes_extraction_health(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    payload = json.loads(output.read_text())
    assert "extraction_health" in payload
    eh = payload["extraction_health"]
    assert eh["total_fixtures"] == 50


def test_verify_gate_snapshot_detects_extraction_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["extraction_health"]["overall_f1"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


def test_extraction_health_baseline_has_all_document_types():
    snapshot = build_gate_snapshot()
    eh = snapshot["extraction_health"]
    by_type = eh["by_document_type"]
    assert "passport" in by_type
    assert "visa" in by_type
    assert "insurance" in by_type


def test_extraction_health_manifest_category_present():
    snapshot = build_gate_snapshot()
    assert "extraction" in snapshot["categories"]
    extraction_cat = snapshot["categories"]["extraction"]
    assert extraction_cat["status"] == "shadow"
    assert extraction_cat["blocks_ci"] is False


def test_extraction_manifest_category_evaluated_with_accuracy():
    """Extraction category should receive overall_f1 from extraction_health."""
    snapshot = build_gate_snapshot()
    extraction_cat = snapshot["categories"]["extraction"]
    eh = snapshot["extraction_health"]
    # Baseline with no live results: f1=0.0, below min_accuracy=0.85
    assert extraction_cat["status"] == "shadow"
    # Shadow status means blocks_ci is always False regardless of accuracy
    assert extraction_cat["blocks_ci"] is False
    # The accuracy_below_threshold reason should be present (f1=0.0 < 0.85)
    assert "accuracy_below_threshold" in extraction_cat["reasons"]


def test_extraction_manifest_category_min_accuracy_threshold():
    """Verify the extraction category uses min_accuracy from manifest.yaml."""
    from src.evals.audit.manifest import load_manifest
    manifest = load_manifest()
    extraction_config = manifest.categories["extraction"]
    assert extraction_config.min_accuracy == 0.85
    assert extraction_config.status == "shadow"


# --- pipeline_health gate tests ---


def test_build_gate_snapshot_includes_pipeline_health():
    snapshot = build_gate_snapshot()
    ph = snapshot["pipeline_health"]
    assert isinstance(ph, dict)
    assert "status" in ph
    assert "overall_accuracy" in ph
    assert "total_fixtures" in ph
    assert "fixtures_passing" in ph
    assert "fixtures_failing" in ph
    assert "stage_accuracies" in ph
    assert ph["total_fixtures"] == 7
    # Self-consistent baseline: expected outputs used as actuals → 100% accuracy
    assert ph["status"] == "passing"
    assert ph["overall_accuracy"] == 1.0
    assert ph["blocks_ci"] is False


def test_stable_snapshot_view_strips_pipeline_health_volatile_fields():
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    ph = stable["pipeline_health"]
    assert isinstance(ph, dict)
    assert "status" in ph
    assert "overall_accuracy" in ph
    assert "total_fixtures" in ph
    assert "blocks_ci" in ph
    # Volatile note and stage_accuracies must not be present
    assert "note" not in ph
    assert "stage_accuracies" not in ph


def test_write_gate_snapshot_includes_pipeline_health(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)
    payload = json.loads(output.read_text())
    assert "pipeline_health" in payload
    ph = payload["pipeline_health"]
    assert ph["total_fixtures"] == 7
    assert isinstance(ph["stage_accuracies"], dict)


def test_verify_gate_snapshot_detects_pipeline_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["pipeline_health"]["overall_accuracy"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


# --- pipeline manifest category tests ---


def test_pipeline_manifest_category_present():
    snapshot = build_gate_snapshot()
    assert "pipeline" in snapshot["categories"]
    pipeline_cat = snapshot["categories"]["pipeline"]
    assert pipeline_cat["status"] == "gating"
    assert pipeline_cat["blocks_ci"] is False


def test_pipeline_manifest_category_evaluated_with_accuracy():
    """Pipeline category should receive overall_accuracy from pipeline_health."""
    snapshot = build_gate_snapshot()
    pipeline_cat = snapshot["categories"]["pipeline"]
    ph = snapshot["pipeline_health"]
    # Self-consistent baseline: expected outputs as actuals → 100% accuracy
    # Pipeline category is gating, and accuracy meets the 0.80 threshold
    assert pipeline_cat["status"] == "gating"
    assert pipeline_cat["meets_thresholds"] is True
    assert pipeline_cat["blocks_ci"] is False


def test_pipeline_manifest_category_min_accuracy_threshold():
    """Verify the pipeline category uses min_accuracy from manifest.yaml."""
    from src.evals.audit.manifest import load_manifest
    manifest = load_manifest()
    pipeline_config = manifest.categories["pipeline"]
    assert pipeline_config.min_accuracy == 0.80
    assert pipeline_config.status == "gating"


def test_pipeline_category_blocks_ci_when_accuracy_below_threshold():
    """Gating status means blocks_ci is True when accuracy is below threshold."""
    from src.evals.audit.gates import _meets_thresholds
    # Simulate low accuracy (below 0.80 threshold)
    meets, reasons = _meets_thresholds(
        None, min_precision=0.0, min_recall=0.0, min_severity_accuracy=0.0,
        min_accuracy=0.80, accuracy=0.50,
    )
    assert meets is False
    assert "accuracy_below_threshold" in reasons


def test_pipeline_category_passes_when_accuracy_above_threshold():
    """Gating status with accuracy above threshold should not block CI."""
    from src.evals.audit.gates import _meets_thresholds
    meets, reasons = _meets_thresholds(
        None, min_precision=0.0, min_recall=0.0, min_severity_accuracy=0.0,
        min_accuracy=0.80, accuracy=0.90,
    )
    assert meets is True
    assert "accuracy_below_threshold" not in reasons


# --- live pipeline results tests ---


def test_build_gate_snapshot_with_live_pipeline_results():
    """Live pipeline results should override the self-consistent baseline."""
    snapshot = build_gate_snapshot()
    baseline_acc = snapshot["pipeline_health"]["overall_accuracy"]
    # Baseline is 1.0 (self-consistent)
    assert baseline_acc == 1.0

    # Now provide partial live results (only one fixture matches perfectly)
    from src.evals.audit.rules.pipeline import load_pipeline_fixtures
    fixtures = load_pipeline_fixtures(Path("data/fixtures/pipeline/pipeline_golden.json"))
    live_results = {
        fixtures[0].fixture_id: {
            "extraction": fixtures[0].expected_extraction,
            "agents": fixtures[0].expected_agents,
            "decision": fixtures[0].expected_decision,
        },
    }
    degraded = build_gate_snapshot(pipeline_live_results=live_results)
    degraded_acc = degraded["pipeline_health"]["overall_accuracy"]
    # Accuracy should drop because only 1 of 7 fixtures has actual results
    assert degraded_acc < baseline_acc
    assert degraded_acc > 0.0


def test_pipeline_live_results_accuracy_degrades_to_warning():
    """Partial live results should produce warning status (0.50-0.80)."""
    from src.evals.audit.rules.pipeline import load_pipeline_fixtures
    fixtures = load_pipeline_fixtures(Path("data/fixtures/pipeline/pipeline_golden.json"))
    # Provide results for 2 of 7 fixtures
    live_results = {
        fixtures[0].fixture_id: {
            "extraction": fixtures[0].expected_extraction,
            "agents": fixtures[0].expected_agents,
            "decision": fixtures[0].expected_decision,
        },
        fixtures[1].fixture_id: {
            "extraction": fixtures[1].expected_extraction,
            "agents": fixtures[1].expected_agents,
            "decision": fixtures[1].expected_decision,
        },
    }
    snapshot = build_gate_snapshot(pipeline_live_results=live_results)
    ph = snapshot["pipeline_health"]
    # 2/7 fixtures with perfect results → accuracy ~0.28
    assert ph["overall_accuracy"] < 0.80
    assert ph["status"] in ("failing", "warning")


def test_pipeline_live_results_empty_degrades_to_failing():
    """Empty live results should produce failing status."""
    snapshot = build_gate_snapshot(pipeline_live_results={})
    ph = snapshot["pipeline_health"]
    assert ph["overall_accuracy"] < 0.50
    assert ph["status"] == "failing"
    assert ph["blocks_ci"] is True


def test_pipeline_live_results_blocks_ci_when_below_threshold():
    """Low accuracy with gating status should block CI via manifest category."""
    snapshot = build_gate_snapshot(pipeline_live_results={})
    pipeline_cat = snapshot["categories"]["pipeline"]
    assert pipeline_cat["status"] == "gating"
    assert pipeline_cat["meets_thresholds"] is False
    assert pipeline_cat["blocks_ci"] is True


def test_write_gate_snapshot_with_live_results(tmp_path: Path):
    """write_gate_snapshot should accept pipeline_live_results."""
    from src.evals.audit.rules.pipeline import load_pipeline_fixtures
    fixtures = load_pipeline_fixtures(Path("data/fixtures/pipeline/pipeline_golden.json"))
    live_results = {
        fixtures[0].fixture_id: {
            "extraction": fixtures[0].expected_extraction,
            "agents": fixtures[0].expected_agents,
            "decision": fixtures[0].expected_decision,
        },
    }
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output, pipeline_live_results=live_results)
    payload = json.loads(output.read_text())
    ph = payload["pipeline_health"]
    assert ph["overall_accuracy"] < 1.0
    assert ph["overall_accuracy"] > 0.0


# --- pipeline baseline drift detection tests ---


def test_pipeline_baseline_drift_fields_present():
    """Pipeline health should include expected_baseline_accuracy and baseline_drifted."""
    snapshot = build_gate_snapshot()
    ph = snapshot["pipeline_health"]
    assert "expected_baseline_accuracy" in ph
    assert "baseline_drifted" in ph
    assert ph["expected_baseline_accuracy"] == 1.0


def test_pipeline_baseline_no_drift_by_default():
    """Self-consistent baseline should produce no drift."""
    snapshot = build_gate_snapshot()
    ph = snapshot["pipeline_health"]
    assert ph["baseline_drifted"] is False
    assert ph["overall_accuracy"] == ph["expected_baseline_accuracy"]


def test_pipeline_baseline_drift_detected_with_live_results():
    """Live results that diverge from expected should trigger drift."""
    snapshot = build_gate_snapshot(pipeline_live_results={})
    ph = snapshot["pipeline_health"]
    assert ph["baseline_drifted"] is True
    assert ph["overall_accuracy"] < ph["expected_baseline_accuracy"]


def test_pipeline_baseline_drift_in_stable_view():
    """Drift fields should appear in stable snapshot view for drift detection."""
    snapshot = build_gate_snapshot()
    stable = stable_snapshot_view(snapshot)
    ph = stable["pipeline_health"]
    assert "expected_baseline_accuracy" in ph
    assert "baseline_drifted" in ph
    # Volatile note and stage_accuracies must not be present
    assert "note" not in ph
    assert "stage_accuracies" not in ph


def test_pipeline_baseline_drift_detected_by_verify(tmp_path: Path):
    """Tampering with pipeline accuracy should be detected as drift."""
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["pipeline_health"]["overall_accuracy"] = 0.50
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False


def test_pipeline_baseline_accuracy_constant_matches():
    """EXPECTED_PIPELINE_BASELINE_ACCURACY should equal 1.0."""
    from src.evals.audit.snapshot import EXPECTED_PIPELINE_BASELINE_ACCURACY
    assert EXPECTED_PIPELINE_BASELINE_ACCURACY == 1.0
