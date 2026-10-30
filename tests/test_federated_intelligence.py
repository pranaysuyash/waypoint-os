"""Tests for the durable federated-intelligence store (BD framework gap #3).

Covers src/intake/federated_intelligence.py: append-only JSONL persistence
across service instances, freshness-windowed active queries, source
anonymization, audit-chain mirroring, corrupted-line tolerance, and the
labeled demo fixture.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from src.intake.federated_intelligence import (
    ACTIVE_INCIDENT_TTL_SECONDS,
    IntelligenceIncident,
    FederatedIntelligenceService,
)


@pytest.fixture()
def service(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.intake.federated_intelligence.STORE_PATH", tmp_path / "incidents.jsonl"
    )
    return FederatedIntelligenceService(store_path=tmp_path / "incidents.jsonl")


def _incident(inc_type="visa_delay", location="Tokyo", severity=3):
    return IntelligenceIncident(incident_type=inc_type, location=location, severity=severity)


def test_report_incident_persists_across_instances(service, tmp_path):
    service.report_incident("agency-A", _incident())
    # A NEW instance (simulated restart) must see the record — the old
    # in-memory pool lost everything on process death.
    fresh = FederatedIntelligenceService(store_path=tmp_path / "incidents.jsonl")
    hits = fresh.query_risks("Tokyo")
    assert len(hits) == 1
    assert hits[0]["type"] == "visa_delay"
    assert hits[0]["severity"] == 3


def test_source_anonymization_hash_only(service):
    service.report_incident("agency-secret-id", _incident())
    raw = service._resolve_path().read_text()
    record = json.loads(raw.strip())
    assert "agency-secret-id" not in raw
    assert len(record["source_hash"]) == 64


def test_audit_chain_mirror_called(service, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "spine_api.persistence.AuditStore.log_event",
        lambda event_type, user_id, details: calls.append((event_type, user_id, details)),
    )
    service.report_incident("agency-A", _incident())
    assert len(calls) == 1
    event_type, user_id, details = calls[0]
    assert event_type == "federated_intelligence_incident"
    assert user_id == "system"
    assert details["incident_type"] == "visa_delay"
    assert "source_hash" in details and "record_id" in details


def test_audit_mirror_failure_does_not_lose_incident(service, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("db down")

    monkeypatch.setattr("spine_api.persistence.AuditStore.log_event", boom)
    service.report_incident("agency-A", _incident())  # must not raise
    hits = service.query_risks("Tokyo")
    assert len(hits) == 1  # incident retained despite degraded audit


def test_query_filters_stale_incidents(service):
    service.report_incident("agency-A", _incident())  # fresh
    # Inject an aged incident directly (append-only store discipline)
    old = {
        "record_id": "fi_old",
        "type": "weather_disruption",
        "location": "Tokyo",
        "severity": 4,
        "details": {},
        "confidence": 1.0,
        "source_hash": "x" * 64,
        "license_tier": "unknown",
        "timestamp": (
            datetime.now(timezone.utc) - timedelta(seconds=ACTIVE_INCIDENT_TTL_SECONDS + 60)
        ).isoformat(),
    }
    with open(service._resolve_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(old) + "\n")
    hits = service.query_risks("Tokyo")
    assert [h["type"] for h in hits] == ["visa_delay"]  # only the fresh one


def test_undated_record_excluded_from_active(service):
    undated = {
        "record_id": "fi_bad", "type": "scam_zone", "location": "Tokyo",
        "severity": 2, "details": {}, "source_hash": "y" * 64, "timestamp": "",
    }
    with open(service._resolve_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(undated) + "\n")
    assert service.query_risks("Tokyo") == []


def test_corrupted_line_skipped_not_fatal(service):
    service.report_incident("agency-A", _incident())
    with open(service._resolve_path(), "a", encoding="utf-8") as fh:
        fh.write("{corrupted json\n")
    service.report_incident("agency-B", _incident(location="Osaka"))
    assert len(service.query_risks("Tokyo")) == 1
    assert len(service.query_risks("Osaka")) == 1


def test_demo_fixture_labeled_not_fabricated(service):
    hits = service.query_risks("Singapore")
    assert len(hits) == 1
    assert hits[0].get("demo") is True
    assert hits[0]["message"].startswith("DEMO")


def test_demo_fixture_suppressed_by_live_data(service):
    service.report_incident("agency-A", _incident(location="Singapore", inc_type="visa_delay"))
    hits = service.query_risks("Singapore")
    assert all(h.get("demo") is not True for h in hits)


def test_singleton_honors_module_redirect(monkeypatch, tmp_path):
    """The module-level singleton must resolve STORE_PATH lazily so
    test/ops redirects (monkeypatch, env-driven relocation) take effect."""
    import src.intake.federated_intelligence as fi

    redirect = tmp_path / "redirected.jsonl"
    monkeypatch.setattr(fi, "STORE_PATH", redirect)
    fi.intelligence_service.report_incident("agency-Z", _incident())
    assert redirect.exists()
    assert len(fi.intelligence_service.query_risks("Tokyo")) == 1
