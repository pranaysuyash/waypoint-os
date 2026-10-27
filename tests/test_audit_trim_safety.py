"""Audit-chain trim-safety test — EXPLORE #5 / topic 51a closure item.

FND-0043 gap (3) PROVEN (2026-10-26, commit 5c367b35) and FIXED (2026-10-27):
the degraded file-chain primitive ``_append_event`` could emit archive lines
without RULE_015 chain fields, so any archive built through it — including
every post-trim suffix — failed ``verify_chain`` permanently.

Fix design (the (b)-lite variant of the two options pre-registered here):
  - ``_append_event`` chains events off the current file head when they arrive
    without chain fields (defense-in-depth; ``log_event`` still pre-chains),
  - the verifier's SUBCHAIN anchor (first event's recorded predecessor is the
    trusted anchor) already tolerates the trimmed-away front BY DESIGN,
  - trim therefore needs no hash rewriting: the head event is untouched, so a
    head-hash witness stays valid across trims,
  - writer and verifier share ``compute_file_entry_hash``
    (spine_api.services.audit_chain_hash) so the file formula cannot drift.

Pinned contract (this file):
  1. A chain written through ``_append_event`` verifies VALID end-to-end.
  2. Post-trim: the file is capped at MAX_EVENTS, the head event is unchanged
     across the trim, and the kept suffix still verifies VALID.
  3. Pre-hardening archives (hand-written lines without chain fields) still
     produce an explicit invalid verdict — honest failure, never a silent
     pass.

Scope: the file chain is the SQL-unreachable degraded mode — ``log_event``
writes to the canonical SQL store; ``_append_event`` + ``_trim_if_needed``
execute only when SQL is down. All assertions use the explicit-events form of
``verify_chain`` so this file tests the FILE chain without coupling to SQL
test-database state.
"""

import json

import pytest

from spine_api.persistence import AuditStore


@pytest.fixture()
def legacy_file(tmp_path, monkeypatch):
    monkeypatch.setattr(AuditStore, "AUDIT_FILE", tmp_path / "events.jsonl")
    monkeypatch.setattr(AuditStore, "_write_count", 0)
    AuditStore.AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    return AuditStore.AUDIT_FILE


def _append_chained(i):
    AuditStore._append_event({
        "event_type": f"trim_test_{i}",
        "user_id": "trim-test",
        "details": {"seq": i},
        "timestamp": f"2026-10-26T00:00:{i:02d}+00:00",
    })


def test_verify_chain_over_properly_chained_archive_is_valid(legacy_file):
    for i in range(10):
        _append_chained(i)
    events = AuditStore._read_events()
    for e in events:
        assert e.get("previous_hash") and e.get("current_hash"), (
            f"_append_event must emit chained lines; got keys {sorted(e.keys())}"
        )
    report = AuditStore.verify_chain(events)
    assert report["valid"], f"chained file archive must verify: {report['errors']}"
    assert report["head_hash"] == events[-1]["current_hash"]


def test_trim_caps_file_and_post_trim_suffix_verifies(legacy_file, monkeypatch):
    monkeypatch.setattr(AuditStore, "MAX_EVENTS", 50)
    n = AuditStore._WRITE_COUNT_BEFORE_TRIM * 2 + 60
    assert n > AuditStore.MAX_EVENTS

    for i in range(n):
        _append_chained(i)

    head_before = AuditStore._read_events()[-1]["current_hash"]
    AuditStore._trim_if_needed()

    events = AuditStore._read_events()
    assert 0 < len(events) <= AuditStore.MAX_EVENTS, (
        f"trim must cap the file at MAX_EVENTS (got {len(events)})"
    )
    assert events[-1]["current_hash"] == head_before, (
        "trim drops the front only — the head event (and its hash) must be unchanged"
    )
    assert any(e.get("event_type", "").startswith("trim_test_") for e in events)

    report = AuditStore.verify_chain(events)
    assert report["valid"], (
        f"post-trim suffix must verify via the subchain anchor: {report['errors']}"
    )


def test_pre_hardening_unchained_archive_reports_invalid_honestly(legacy_file):
    for i in range(5):
        with open(AuditStore.AUDIT_FILE, "a") as f:
            f.write(json.dumps({
                "id": f"legacy_{i}",
                "event_type": "pre_hardening",
                "user_id": "legacy-writer",
                "timestamp": f"2026-01-01T00:00:0{i}+00:00",
                "details": {"seq": i},
            }) + "\n")

    events = AuditStore._read_events()
    report = AuditStore.verify_chain(events)
    assert report["valid"] is False, "pre-hardening unchained archives must never silently pass"
    assert report["errors"], "an invalid verdict must carry explicit error reasons"
    assert any("predecessor mismatch" in e or "hash mismatch" in e for e in report["errors"])
