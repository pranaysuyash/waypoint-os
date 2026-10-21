"""SQL audit hash contract tests; no persistent database access."""

from datetime import datetime, timedelta, timezone
import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from spine_api.services.audit_chain_hash import (
    GENESIS_BLOCK_HASH,
    compute_audit_entry_hash,
    verify_audit_entries,
)


def entry(identifier="first", predecessor=GENESIS_BLOCK_HASH, agency="agency-one"):
    row = SimpleNamespace(
        id=identifier, agency_id=agency, user_id=None, action="update",
        previous_hash=predecessor,
        created_at=datetime(2026, 10, 4, 12, tzinfo=timezone.utc),
        changes={"after": 2, "before": 1},
    )
    row.current_hash = compute_audit_entry_hash(
        row.id, row.agency_id, row.user_id, row.action, predecessor,
        row.created_at.isoformat(), row.changes,
    )
    return row


def test_global_chain_crosses_agencies():
    first = entry()
    second = entry("second", first.current_hash, "agency-two")
    assert verify_audit_entries([first, second])["verdict"] == "pass"
    assert verify_audit_entries([second])["verdict"] == "fail"


def test_hash_preserves_historical_writer_bytes():
    # Independent oracle: sharing a helper alone would let both consumers
    # silently agree on an incompatible change to already-persisted hashes.
    payload = (
        'first:agency-one:None:update:GENESIS_BLOCK_HASH:'
        '2026-10-04T12:00:00+00:00:{"after": 2, "before": 1}'
    )
    assert entry().current_hash == hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_reordering_and_missing_genesis_fail():
    first = entry()
    second = entry("second", first.current_hash)
    assert verify_audit_entries([second, first])["verdict"] == "fail"
    second.previous_hash = None
    assert verify_audit_entries([second])["verdict"] == "fail"


@pytest.mark.parametrize("field,value", [
    ("changes", {"after": 999}), ("agency_id", "forged"),
    ("user_id", "forged"), ("action", "delete"), ("id", "forged"),
])
def test_covered_payload_tampering_fails(field, value):
    row = entry()
    setattr(row, field, value)
    assert verify_audit_entries([row])["verdict"] == "fail"


def test_partial_hash_and_unhashed_tail_fail():
    first = entry()
    second = entry("second", first.current_hash)
    second.current_hash = None
    assert verify_audit_entries([first, second])["verdict"] == "fail"
    second.previous_hash = None
    assert verify_audit_entries([first, second])["verdict"] == "fail"
    assert verify_audit_entries([second, first])["legacy_unanchored"] == 1


def test_second_genesis_and_fork_fail():
    first = entry()
    second = entry("second")
    assert verify_audit_entries([first, second])["forks"] == ["second"]
    child = entry("child", first.current_hash)
    sibling = entry("sibling", first.current_hash)
    assert verify_audit_entries([first, child, sibling])["forks"] == ["sibling"]


def test_datetime_storage_representation_does_not_change_hash():
    row = entry()
    row.created_at = row.created_at.replace(tzinfo=None)
    assert verify_audit_entries([row])["verdict"] == "pass"
    row.created_at = row.created_at.replace(tzinfo=timezone.utc).astimezone(
        timezone(timedelta(hours=5, minutes=30))
    )
    assert verify_audit_entries([row])["verdict"] == "pass"
    row.created_at += timedelta(seconds=1)
    assert verify_audit_entries([row])["verdict"] == "fail"


def test_empty_snapshot_is_not_an_external_anchor():
    result = verify_audit_entries([])
    assert result["verdict"] == "pass"
    assert result["anchored"] == 0


@pytest.mark.asyncio
async def test_actual_writer_agrees_with_verifier():
    from spine_api.core.audit import AuditContext

    rows = []
    db = SimpleNamespace(flush=AsyncMock(), scalars=AsyncMock(return_value=[]))

    def add(row):
        row.id = "writer-entry"
        rows.append(row)

    db.add = add
    context = AuditContext(db, "agency-one", None, None, None)
    row = await context.log("update", changes={"before": 1, "after": 2})
    assert row is rows[0]
    assert verify_audit_entries(rows)["verdict"] == "pass"
    assert db.flush.await_count == 2
