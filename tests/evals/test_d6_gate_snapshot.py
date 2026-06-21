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
    assert ph["total_fixtures"] == 5
    # Baseline with no live results: low accuracy expected
    assert ph["status"] in ("failing", "warning")
    assert ph["overall_accuracy"] < 0.2
    assert ph["blocks_ci"] is True


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
    assert ph["total_fixtures"] == 5
    assert isinstance(ph["stage_accuracies"], dict)


def test_verify_gate_snapshot_detects_pipeline_health_drift(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    write_gate_snapshot(output_path=output)

    payload = json.loads(output.read_text())
    payload["pipeline_health"]["overall_accuracy"] = 0.99
    output.write_text(json.dumps(payload, indent=2))

    ok, _, _ = verify_gate_snapshot_file(snapshot_path=output)
    assert ok is False
