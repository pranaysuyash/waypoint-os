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
    # Log two distinct events (SQL store — hash payload mirrors
    # core.audit.AuditContext.log: id, agency, user, action, prev, created_at, changes)
    e1 = AuditStore.log_event("trip_created", "usr_agent_1", {"trip_id": "trip_chain_1", "destination": "Tokyo"})
    e2 = AuditStore.log_event("quote_approved", "usr_owner_1", {"trip_id": "trip_chain_1", "quote_cents": 450000})

    assert "previous_hash" in e1
    assert "current_hash" in e1
    assert "previous_hash" in e2
    assert "current_hash" in e2

    # Verify chain link: e2.previous_hash == e1.current_hash
    assert e2["previous_hash"] == e1["current_hash"]

    # Re-verify e2 hash computation under the SQL formula
    hash_payload = (
        f"{e2['id']}:{e2['agency_id']}:{e2['user_id'] or ''}:{e2['event_type']}:"
        f"{e2['previous_hash']}:{e2['created_at']}:{json.dumps(e2['details'], sort_keys=True)}"
    )
    expected_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()
    assert e2["current_hash"] == expected_hash


def test_audit_event_hash_chain_is_contiguous_under_concurrent_writers():
    """Concurrent writers must produce one contiguous chain: each row's
    previous_hash links to the prior row's current_hash (writes serialize on
    the sync/async bridge loop, so the predecessor read cannot race)."""

    def write_event(index: int) -> dict:
        return AuditStore.log_event(
            "concurrent_probe",
            f"worker-{index}",
            {"index": index},
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        returned = list(executor.map(write_event, range(32)))

    assert len({e["id"] for e in returned}) == 32
    # Contiguity in WRITE order: executor.map returns results in submission
    # order, but the 8 worker threads acquire the write lock in arbitrary
    # order — the chain is contiguous by created_at (the serialized timeline).
    ordered = sorted(returned, key=lambda e: e["created_at"])
    for previous, current in zip(ordered, ordered[1:]):
        assert current["previous_hash"] == previous["current_hash"], (
            f"chain break between {previous['id']} and {current['id']}"
        )


def test_audit_chain_verifier_detects_tamper_and_fork(tmp_path, monkeypatch):
    audit_file = tmp_path / "audit" / "events.jsonl"
    monkeypatch.setattr(AuditStore, "AUDIT_FILE", audit_file)
    monkeypatch.setattr(AuditStore, "_write_count", 0)

    first = AuditStore.log_event("probe", "operator", {"step": 1})
    second = AuditStore.log_event("probe", "operator", {"step": 2})
    # Scope to the two events this test wrote: verify_chain() with no
    # arguments verifies the whole canonical store (dev DBs accumulate
    # unrelated history).
    assert AuditStore.verify_chain([first, second])["valid"] is True

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
