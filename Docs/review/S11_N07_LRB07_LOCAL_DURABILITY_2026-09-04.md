# S-11 / N-07 / LR-B07 — Local Run-Ledger Durability Addendum

**Date:** 2026-09-04\
**Scope:** bounded local hardening of the file-backed run ledger and event
stream\
**Owner:** idempotency/durability lane\
**Evidence class:** Tier 2 focused verification, with Tier 1 deployment
configuration analysis\
**Sensitivity:** S1 focused passes, including simulated interruption and
contention checks; no pre-fix run or mutation score is claimed (not a hosted or
multi-replica gate)

## Decision

Keep the current file-backed ledger as the canonical development/single-host
implementation, but make its local safety properties explicit and enforceable:

1. `WAYPOINT_RUNS_DIR` is the one configuration seam for placing run metadata,
   stage checkpoints, and event logs on a mounted durable path.
2. Every `meta.json` and stage checkpoint is written through a per-file lock,
   temporary sibling, `fsync`, atomic `os.replace`, and best-effort directory
   `fsync`.
3. Every `events.jsonl` append and read is serialized by a per-stream lock;
   appends flush and `fsync` before releasing the lock.
4. Lifecycle methods re-read metadata while holding the lock before validating
   and publishing a transition. A concurrent transition therefore has one
   winner rather than two workers publishing from the same stale snapshot.

This is the smallest safe local improvement that removes torn artifacts and
local-worker write races without introducing a speculative provider or a
second persistence system.

## Prior state and failure mode

`spine_api/run_ledger.py` previously wrote `meta.json` and `steps/*.json`
directly with `open("w")` and `json.dump`. `spine_api/run_events.py` appended
to `events.jsonl` without a lock. The state-machine guard prevented invalid
logical transitions, but it did not serialize the read/validate/write sequence
or guarantee that readers never saw a partial file after an interrupted write.

The larger LR-B07 finding remains: the records are still filesystem state. A
machine restart or deployment without a durable mount can lose them, and
separate replicas cannot converge by sharing process-local or ephemeral disk.
The existing proposal revocation path is similarly documented as single-host
atomic JSON persistence; it is not silently reclassified as a shared database.

## Implementation

### Run metadata and checkpoints

`spine_api/run_ledger.py` now resolves `RUNS_DIR` from
`WAYPOINT_RUNS_DIR` when present, retaining the repository-local `data/runs`
default for development and test isolation. `_file_lock()` uses a sibling lock
file and `fcntl.flock` on supported deployment targets. `_atomic_write_json()`
flushes and fsyncs a temporary sibling before atomically replacing the target;
it also flushes the containing directory where supported.

`create`, `set_state`, `save_step`, `complete`, `fail`, `block`, and
`update_meta` now use the lock/write path. Lifecycle transitions re-read the
latest metadata inside the lock, preserving the state-machine contract under
contention.

### Run events

`spine_api/run_events.py` uses the same `WAYPOINT_RUNS_DIR` seam. Event stream
reads and appends use a sibling lock; appends flush and fsync before release.
The event stream remains append-only JSONL and keeps its existing event shape.

## Verification

Focused command:

```bash
.venv/bin/pytest -q tests/test_run_ledger_durability.py
```

Observed result:

```text
4 passed in 0.45s
```

The checks cover:

- simulated failure before `os.replace`: the last published `meta.json`
  remains valid and no temporary artifact remains;
- 80 concurrent thread appends and eight separate worker-process appends:
  complete, independently parseable JSON lines are retained;
- eight concurrent `queued → running` attempts: exactly one transition wins
  and the final state is `running`.

Existing related coverage also remains green:

```bash
.venv/bin/pytest -q \
  tests/test_run_ledger_durability.py \
  tests/test_run_state_unit.py \
  tests/test_journey_smoke.py
```

```text
51 passed in 2.21s
```

Static checks:

```bash
.venv/bin/ruff check \
  spine_api/run_ledger.py \
  spine_api/run_events.py \
  tests/test_run_ledger_durability.py
```

```text
All checks passed!
```

`git diff --check` for the lane also passed.

The configuration seam was independently checked with:

```bash
WAYPOINT_RUNS_DIR=/var/lib/waypoint/runs \
  .venv/bin/python -c 'from spine_api import run_ledger, run_events; assert run_ledger.RUNS_DIR == run_events.RUNS_DIR; print(run_ledger.RUNS_DIR)'
```

Observed result:

```text
/var/lib/waypoint/runs
```

## Why this is aligned

| Dimension | Assessment |
|---|---|
| First principles | The ledger's first obligation is to preserve a truthful lifecycle record. Atomic publication and serialized transitions protect that invariant at the storage boundary. |
| Long term | `WAYPOINT_RUNS_DIR` gives the existing canonical path a deployment seam without inventing `run-ledger-v2` or coupling application logic to one hosting provider. |
| Doctrine | Unknown and unsupported deployment guarantees remain explicit. Local tests are not called production proof, and the provider/replica gate remains open. |
| Operational value | A crash cannot normally publish a half-written JSON artifact; local workers cannot both commit a lifecycle transition from the same stale snapshot; event records remain parseable. |
| Reversibility | The public API and file layout remain unchanged. Removing the optional environment variable returns to the development default. |

## Deliberate non-claims and remaining work

This addendum does **not** prove:

- that Fly/Render has provisioned a volume;
- that the volume survives deploy, replacement, or region failure;
- that multiple replicas share one filesystem with correct locking semantics;
- backup, restore, retention, encryption, or disaster-recovery objectives;
- that proposal issuance/revocation converges across independent machines;
- that the ledger is covered by the SQL audit hash chain;
- production, hosted, browser, provider, or real-user behavior.

The next architecture decision remains one of:

1. promote proposal revocations and run-ledger state to PostgreSQL (preferred
   for replica-wide security and operational truth); or
2. ratify a single-host topology and provision a durable mounted volume,
   explicitly accepting its RPO/RTO and failover limits.

Before either claim is closed, run a deployment-specific restart/replacement
probe, a cross-process or cross-replica convergence test, and a documented
backup/restore drill. Until then, LR-B07 is locally hardened but not launch
closed.

## Files

- `spine_api/run_ledger.py`
- `spine_api/run_events.py`
- `tests/test_run_ledger_durability.py`

No Git mutation was performed. Existing concurrent modifications were
preserved.
