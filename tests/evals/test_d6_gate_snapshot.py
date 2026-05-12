import json
from pathlib import Path

from src.evals.audit.snapshot import build_gate_snapshot, write_gate_snapshot


def test_build_gate_snapshot_includes_activity_gate_and_metrics():
    snapshot = build_gate_snapshot()
    assert snapshot["manifest_version"] == 1
    assert snapshot["total_fixtures"] >= 1
    assert "activity" in snapshot["categories"]
    activity = snapshot["categories"]["activity"]
    assert activity["status"] == "shadow"
    assert activity["authoritative_for_public_surface"] is False
    assert isinstance(activity["metrics"], dict)


def test_write_gate_snapshot_creates_json_file(tmp_path: Path):
    output = tmp_path / "d6_gate_snapshot.json"
    written = write_gate_snapshot(output_path=output)
    assert written == output
    payload = json.loads(output.read_text())
    assert payload["categories"]["budget"]["status"] == "gating"
    assert "generated_at" in payload

