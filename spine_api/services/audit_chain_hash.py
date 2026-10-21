"""
spine_api.services.audit_chain_hash — canonical RULE_015 entry hash.

Mirrors the writer payload in spine_api.core.audit.AuditContext.log exactly:
sha256 over "id:agency:user:action:previous_hash:created_at:changes-json"
(sorted-keys JSON). tests/test_audit_log_chain_verify.py pins
writer/verifier agreement so the two can never silently drift.

Deliberately dependency-free (no DB imports) — pure hashing.
"""

import hashlib
import json
from datetime import datetime, timezone
from collections.abc import Sequence
from typing import Protocol
from typing import Optional

GENESIS_BLOCK_HASH = "GENESIS_BLOCK_HASH"


class AuditHashEntry(Protocol):
    """Fields covered by the existing SQL writer's hash contract."""

    id: str
    agency_id: str
    user_id: Optional[str]
    action: str
    previous_hash: Optional[str]
    current_hash: Optional[str]
    created_at: datetime
    changes: Optional[dict]


def compute_audit_entry_hash(
    entry_id: str,
    agency_id: str,
    user_id: Optional[str],
    action: str,
    previous_hash: Optional[str],
    created_at_iso: str,
    changes: Optional[dict],
) -> str:
    parts = [
        str(entry_id),
        str(agency_id),
        str(user_id),
        str(action),
        str(previous_hash),
        str(created_at_iso),
        json.dumps(changes or {}, sort_keys=True),
    ]
    joined = chr(58).join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def verify_audit_entries(entries: Sequence[AuditHashEntry]) -> dict:
    """Verify a complete global snapshot supplied in writer order.

    Do not pass an agency-filtered or paginated slice: AuditContext writes one
    global chain. This pure function neither reads a database nor re-anchors
    records. An intact snapshot cannot prove that a tail or entire chain was
    not deleted without an independently trusted checkpoint. Resource and
    network metadata are not covered by the historical writer hash.
    """
    anchored = 0
    legacy_unanchored = 0
    previous = GENESIS_BLOCK_HASH
    seen_predecessors: set[str] = set()
    first_break = None
    forks = []

    def fail(entry: AuditHashEntry, reason: str) -> None:
        nonlocal first_break
        if first_break is None:
            first_break = {"id": entry.id, "reason": reason}

    for entry in entries:
        if entry.current_hash is None:
            if entry.previous_hash is not None:
                fail(entry, "missing current_hash on linked entry")
            elif anchored:
                fail(entry, "unhashed entry after chain start")
            else:
                legacy_unanchored += 1
            continue

        anchored += 1
        predecessor = entry.previous_hash
        if predecessor in seen_predecessors:
            forks.append(entry.id)
            fail(entry, "multiple entries share a predecessor")
        if predecessor is not None:
            seen_predecessors.add(predecessor)
        if predecessor != previous:
            fail(entry, "missing predecessor or continuity break")

        # The writer always hashes UTC-aware timestamps. SQLite round trips
        # discard tzinfo; PostgreSQL can return the same instant in another
        # session timezone. Restore the writer representation, not local time.
        created_at = entry.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = created_at.astimezone(timezone.utc)
        expected = compute_audit_entry_hash(
            entry.id, entry.agency_id, entry.user_id, entry.action,
            predecessor, created_at.isoformat(), entry.changes,
        )
        if entry.current_hash != expected:
            fail(entry, "current_hash does not match covered payload")
        previous = entry.current_hash

    return {
        "verdict": "fail" if first_break else "pass",
        "events_scanned": len(entries),
        "anchored": anchored,
        "legacy_unanchored": legacy_unanchored,
        "first_break": first_break,
        "forks": forks,
    }
