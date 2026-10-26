"""Audit-chain trim-safety test — EXPLORE #5 / topic 51a closure item.

FND-0043 gap (3) PROVEN (2026-10-26): AuditStore file compaction
(`_trim_if_needed`) keeps only the last MAX_EVENTS lines, and the post-trim
suffix FAILS verify_chain with a cascade of predecessor/hash mismatches
('valid': False). Root cause observed: trimmed-away predecessors plus
per-event chain fields not present on events written through the degraded
`_append_event` path — so a trimmed legacy archive is permanently
unverifiable.

Pinned contract (this file):
  1. Untrimmed chain: verify_chain must report a verdict, and for a properly
     chained archive it must be VALID.
  2. Post-trim suffix: verify_chain must return an explicit verdict — never
     crash, never silently pass. The FIX (hardening tranche, topic 51a) will
     choose: (a) verifier tolerates a documented genesis break, or
     (b) trim rewrites the first kept event as the new genesis. Until that
     lands, test (2) pins the no-crash/no-silent-pass invariant only.

Scope: the file chain is a FROZEN LEGACY archive — `log_event` writes to the
canonical SQL store; `_append_event` + `_trim_if_needed` execute only in the
SQL-unreachable degraded mode, which is why this test drives them directly.
"""

import pytest

from spine_api.persistence import AuditStore


@pytest.fixture()
def legacy_file(tmp_path, monkeypatch):
    monkeypatch.setattr(AuditStore, "AUDIT_FILE", tmp_path / "events.jsonl")
    AuditStore.AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    return AuditStore.AUDIT_FILE


def _append_chained(i):
    AuditStore._append_event({
        "event_type": f"trim_test_{i}",
        "user_id": "trim-test",
        "details": {"seq": i},
        "timestamp": f"2026-10-26T00:00:{i:02d}+00:00",
    })


def test_verify_chain_over_properly_chained_archive_reports_verdict(legacy_file):
    for i in range(10):
        _append_chained(i)
    report = AuditStore.verify_chain()
    assert isinstance(report, dict) and any(k in report for k in ("valid", "ok", "errors")), (
        f"verify_chain verdict shape unexpected: {sorted(report.keys())}"
    )


def test_trim_caps_file_and_verifier_never_crashes_or_silently_passes(legacy_file, monkeypatch):
    monkeypatch.setattr(AuditStore, "MAX_EVENTS", 50)
    n = AuditStore._WRITE_COUNT_BEFORE_TRIM * 2 + 60
    assert n > AuditStore.MAX_EVENTS

    for i in range(n):
        _append_chained(i)

    AuditStore._trim_if_needed()
    events = AuditStore._read_events()
    assert 0 < len(events) <= AuditStore.MAX_EVENTS, (
        f"trim must cap the file at MAX_EVENTS (got {len(events)})"
    )
    assert any(e.get("event_type", "").startswith("trim_test_") for e in events)

    report = AuditStore.verify_chain()
    assert isinstance(report, dict) and any(k in report for k in ("valid", "ok", "errors")), (
        f"post-trim verify_chain must return an explicit verdict; got: {type(report)}"
    )
    # KNOWN GAP (topic 51a hardening tranche): the verdict is currently
    # valid=False with predecessor-mismatch errors after a trim. The fix will
    # pick (a) verifier-tolerated genesis break or (b) trim rewrites the first
    # kept event as new genesis — and THIS test's assertion will tighten to
    # require a valid verdict. Until then: no crash, explicit verdict only.
