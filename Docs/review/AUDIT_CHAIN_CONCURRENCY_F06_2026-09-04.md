# Audit Chain Concurrency Hardening — F-06 — 2026-09-04

## Finding and root cause

`AuditStore.log_event` read the last JSONL event before acquiring the
cross-process lock, then acquired the lock only while appending. Concurrent
writers could therefore compute different blocks from different predecessors,
creating a chain discontinuity even though every individual line was valid.

The full backend gate reproduced this in
`tests/test_cryptographic_audit_ledger.py`:

```text
AssertionError: e2["previous_hash"] != e1["current_hash"]
```

## Implemented correction

- `AuditStore._append_event` now supports a `lock_held` path and flushes plus
  fsyncs each appended JSONL line.
- `AuditStore.log_event` holds one cross-process file lock across migration,
  predecessor read, hash computation, and append.
- The old append-only API and event schema remain compatible.
- A new isolated regression launches 32 concurrent writers and verifies that
  all 32 persisted events form one contiguous `previous_hash` → `current_hash`
  chain.
- `AuditStore.verify_chain()` now provides a read-only verifier that checks the
  genesis/predecessor link and recomputes every event hash. An isolated
  regression proves that modified details produce a hash-mismatch finding and
  a changed predecessor produces a fork/predecessor finding.

## Verification

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_cryptographic_audit_ledger.py
3 passed in 0.61s
```

```text
scripts/run_backend_tests.sh
3,657 passed, 44 skipped, 0 failed in 112.72s
```

```text
.venv/bin/ruff check spine_api/persistence.py \
  tests/test_cryptographic_audit_ledger.py
All checks passed!
```

## Status and remaining boundary

**F-06 is partial, not closed.** Local concurrent chain continuity,
per-event fsync, and read-only tamper/fork detection are now verified.
Remaining work is:

- external or database anchoring of the chain head;
- gap/replay detection, operator surfacing, and integration of the verifier
  into a scheduled/ release gate;
- shared multi-replica audit storage and retention;
- backup/restore and operator recovery evidence;
- a decision on whether run-ledger events belong in the same canonical chain.

Local test evidence does not establish hosted, legal, production, or
cryptographic external-anchor guarantees.
