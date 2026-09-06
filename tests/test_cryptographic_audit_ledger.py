"""
tests/test_cryptographic_audit_ledger.py — Cryptographic audit trail validation (PER-0892).

Verifies:
  - SHA-256 chain hashing across successive audit events
  - Genesis block linking
  - Tamper detection on modified audit details
"""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

from spine_api.persistence import AuditStore


def test_audit_event_hash_chain():
    # Log two distinct events
    e1 = AuditStore.log_event("trip_created", "usr_agent_1", {"trip_id": "trip_chain_1", "destination": "Tokyo"})
    e2 = AuditStore.log_event("quote_approved", "usr_owner_1", {"trip_id": "trip_chain_1", "quote_cents": 450000})

    assert "previous_hash" in e1
    assert "current_hash" in e1
    assert "previous_hash" in e2
    assert "current_hash" in e2

    # Verify chain link: e2.previous_hash == e1.current_hash
    assert e2["previous_hash"] == e1["current_hash"]

    # Re-verify e2 hash computation
    hash_payload = f"{e2["id"]}:{e2["event_type"]}:{e2["user_id"]}:{e2["previous_hash"]}:{e2["timestamp"]}:{json.dumps(e2["details"], sort_keys=True)}"
    expected_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()
    assert e2["current_hash"] == expected_hash


def test_audit_event_hash_chain_is_contiguous_under_concurrent_writers(tmp_path, monkeypatch):
    """The predecessor read and append must be one cross-process critical section."""
    audit_file = tmp_path / "audit" / "events.jsonl"
    monkeypatch.setattr(AuditStore, "AUDIT_FILE", audit_file)
    monkeypatch.setattr(AuditStore, "_write_count", 0)

    def write_event(index: int) -> dict:
        return AuditStore.log_event(
            "concurrent_probe",
            f"worker-{index}",
            {"index": index},
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        returned = list(executor.map(write_event, range(32)))

    persisted = AuditStore._read_events()
    assert len(persisted) == 32
    assert {event["id"] for event in persisted} == {event["id"] for event in returned}
    for previous, current in zip(persisted, persisted[1:]):
        assert current["previous_hash"] == previous["current_hash"]


def test_audit_chain_verifier_detects_tamper_and_fork(tmp_path, monkeypatch):
    audit_file = tmp_path / "audit" / "events.jsonl"
    monkeypatch.setattr(AuditStore, "AUDIT_FILE", audit_file)
    monkeypatch.setattr(AuditStore, "_write_count", 0)

    first = AuditStore.log_event("probe", "operator", {"step": 1})
    second = AuditStore.log_event("probe", "operator", {"step": 2})
    assert AuditStore.verify_chain()["valid"] is True

    tampered = [dict(first), dict(second)]
    tampered[0]["details"] = {"step": "altered"}
    result = AuditStore.verify_chain(tampered)
    assert result["valid"] is False
    assert any("hash mismatch" in error for error in result["errors"])

    forked = [dict(first), dict(second)]
    forked[1]["previous_hash"] = "forked-predecessor"
    result = AuditStore.verify_chain(forked)
    assert result["valid"] is False
    assert any("predecessor mismatch" in error for error in result["errors"])
