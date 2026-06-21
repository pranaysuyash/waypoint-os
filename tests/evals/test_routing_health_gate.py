"""Tests for routing health gate integration into D6 snapshot and public authority."""

from __future__ import annotations

import json
from pathlib import Path

from src.evals.audit.public_authority import (
    RoutingHealthAuthority,
    resolve_routing_health_authority,
)


def test_resolve_routing_health_authority_defaults_to_healthy_without_snapshot(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", str(tmp_path / "missing.json"))
    auth = resolve_routing_health_authority()
    assert auth.status == "healthy"
    assert auth.blocks_ci is False
    assert auth.source == "manifest_fallback"
    assert auth.thresholds == {}


def test_resolve_routing_health_authority_reads_from_snapshot(monkeypatch, tmp_path):
    snapshot_path = tmp_path / "d6_gate_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "routing_health": {
                    "status": "warning",
                    "blocks_ci": False,
                    "thresholds": {
                        "fallback_trigger_rate_warning": 0.3,
                        "latency_p95_ms_critical": 30000,
                    },
                },
                "categories": {},
            }
        )
    )
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", str(snapshot_path))
    auth = resolve_routing_health_authority()
    assert auth.status == "warning"
    assert auth.blocks_ci is False
    assert auth.source == "eval_snapshot"
    assert auth.thresholds["fallback_trigger_rate_warning"] == 0.3
    assert auth.thresholds["latency_p95_ms_critical"] == 30000.0


def test_resolve_routing_health_authority_critical_blocks_ci(monkeypatch, tmp_path):
    snapshot_path = tmp_path / "d6_gate_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "routing_health": {
                    "status": "critical",
                    "blocks_ci": True,
                    "thresholds": {},
                },
                "categories": {},
            }
        )
    )
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", str(snapshot_path))
    auth = resolve_routing_health_authority()
    assert auth.status == "critical"
    assert auth.blocks_ci is True
    assert auth.source == "eval_snapshot"


def test_resolve_routing_health_authority_handles_missing_routing_health_key(
    monkeypatch, tmp_path
):
    snapshot_path = tmp_path / "d6_gate_snapshot.json"
    snapshot_path.write_text(json.dumps({"categories": {}}))
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", str(snapshot_path))
    auth = resolve_routing_health_authority()
    assert auth.status == "healthy"
    assert auth.blocks_ci is False
    assert auth.source == "manifest_fallback"


def test_resolve_routing_health_authority_handles_corrupt_json(monkeypatch, tmp_path):
    snapshot_path = tmp_path / "d6_gate_snapshot.json"
    snapshot_path.write_text("{not valid json")
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", str(snapshot_path))
    auth = resolve_routing_health_authority()
    assert auth.status == "healthy"
    assert auth.source == "manifest_fallback"


def test_routing_health_authority_summary_is_json_serialisable(monkeypatch, tmp_path):
    from dataclasses import asdict

    auth = RoutingHealthAuthority(
        status="warning",
        blocks_ci=False,
        source="eval_snapshot",
        thresholds={"fallback_trigger_rate_warning": 0.3},
    )
    dumped = json.dumps(asdict(auth))
    assert "warning" in dumped
