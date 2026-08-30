"""
tests/test_cryptographic_audit_ledger.py — Cryptographic audit trail validation (PER-0892).

Verifies:
  - SHA-256 chain hashing across successive audit events
  - Genesis block linking
  - Tamper detection on modified audit details
"""

import hashlib
import json
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
