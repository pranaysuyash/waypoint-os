# Agent lease local state-machine hardening — R-11 / F-10

**Date:** 2026-09-04\
**Scope:** bounded local hardening of `src/orchestration/agent_lease.py` and its focused tests\
**Status:** locally implemented and verified; durable/runtime integration remains open\
**Owner:** implementation review lane\
**Evidence class:** S2 local deterministic + S2 concurrency regression; not hosted, multi-process, provider, or production evidence

## Decision

The in-memory `DurableAgentLeaseManager` now has a synchronized state machine for the
semantics that are unambiguous without changing the runtime or database contracts:

1. all map and record transitions are serialized by a class-level re-entrant lock;
2. an expired active record is transitioned to inactive before it can be renewed or
   replaced;
3. released, swept, expired, or token-mismatched records cannot be renewed;
4. fencing-token verification fails closed when the lease generation is expired or
   inactive;
5. a new acquisition increments the per-trip fencing counter atomically with installing
   the new record; and
6. metadata is copied at acquisition so later caller mutation does not mutate the
   manager's stored metadata dictionary.

The patch deliberately does **not** add pipeline-version stamps, agency/RLS columns,
SQL persistence, worker heartbeat loops, or fenced trip-write integration. Those are
broader contracts requiring architecture/ownership and deployment evidence; adding
fields or semantics only to this in-memory helper would create a second, misleading
lease model.

## Source observations

- `src/orchestration/agent_lease.py` was a class-dictionary implementation with no
  synchronization. `acquire_lease`, `renew_lease`, `release_lease`, `sweep_stale_leases`,
  and `clear` could interleave across threads.
- `renew_lease` checked `is_active` but did not check the expiry deadline, so a worker
  holding the old token could renew after its lease elapsed.
- `spine_api/services/agent_work_coordinator.py` is the separate SQL-backed work lease
  path. It currently stores `leased_until` but has no pipeline-version or fencing column;
  this dossier does not silently claim that path is fixed.
- `spine_api/routers/agent_lease.py` is present and included by `spine_api/server.py`;
  its HTTP request/response, authentication, status-code, and runtime reachability
  contract does not yet have a dedicated focused test in this slice.
- `src/agents/runtime.py:ExecutionLease.heartbeat` remains a separate primitive and is
  not wired into the supervisor. This local manager change does not claim to wire it.
- `Docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md` marks pipeline compatibility,
  agency scoping, status reconciliation, and multi-worker behavior as design/open
  questions. They remain deferred here.

## Implementation evidence

### Changed files

- `src/orchestration/agent_lease.py`
  - added `RLock` protection around all shared state transitions;
  - added positive-integer TTL validation;
  - added an internal expiry transition helper;
  - rejected renewal of inactive/expired/token-mismatched leases;
  - made expired release return `False` rather than report a successful release;
  - made inspection/sweeping state-aware and synchronized; and
  - copied acquisition metadata.
- `tests/test_durable_agent_lease.py`
  - added expiry renewal/release rejection and replacement fencing coverage;
  - added released-record renewal rejection;
  - added idempotent stale sweeping coverage; and
  - added an eight-worker concurrent-acquisition race regression.
  - added explicit fencing-token rejection coverage after release and expiry.
- `spine_api/routers/agent_lease.py`
  - exposes acquire, renew, release, fencing-verification, and inspection endpoints;
  - is wired into the server route table, but remains contract-unverified here.

### Verification commands and outcomes

Executed from `/Users/pranay/Projects/travel_agency_agent`:

```text
.venv/bin/python -m pytest tests/test_durable_agent_lease.py -q
.......                                                                  [100%]
7 passed in 0.29s

.venv/bin/ruff check src/orchestration/agent_lease.py tests/test_durable_agent_lease.py
All checks passed!

.venv/bin/python -m pytest tests/test_agent_lease_router.py tests/test_durable_agent_lease.py -q
...........                                                              [100%]
11 passed in 0.43s

.venv/bin/ruff check spine_api/routers/agent_lease.py src/orchestration/agent_lease.py \
  tests/test_agent_lease_router.py tests/test_durable_agent_lease.py
All checks passed!

scripts/run_backend_tests.sh
3,754 passed, 10 skipped, 8 known Python 3.13 fork warnings in 248.10s with
the existing :8000 development server present. The runner explicitly marks
this as a server-present/integration-polluted receipt; the earlier clean-port
receipt remains historical evidence.
```

The initial system-Python invocation was not a test result: collection stopped because
the system interpreter lacks `sqlalchemy`. The authoritative run used the repository's
`.venv`, consistent with the project's Python verification rule.

## Invariants now covered

| Invariant | Evidence | Result |
|---|---|---|
| one active winner under concurrent acquisition | `test_concurrent_acquisition_has_one_winner_and_one_fence_generation` | 8 contenders → 1 winner, fencing token 1 |
| active lease cannot be renewed after its deadline | `test_expired_lease_cannot_be_renewed_or_released_and_next_acquire_fences_it` | rejected and marked inactive |
| released lease cannot be renewed | `test_released_lease_cannot_be_renewed` | rejected |
| stale sweep is repeat-safe | `test_sweep_stale_leases_is_idempotent_and_blocks_resurrection` | first sweep 1, second sweep 0 |
| replacement generation fences old token | expiry/replacement test plus existing release test | old token false, new token true |
| existing acquire/contention behavior remains green | state-machine focused tests | 7/7 pass |
| router request/response and status mappings | `test_agent_lease_router.py` | 4 route tests pass; auth and worker-write integration remain open |

## Alignment assessment

- **First principles:** aligned for the local state machine. Ownership, deadline, and
  fencing generation are explicit and transitions are atomic within the process.
- **Long term:** additive and low-blast-radius, but not a durable distributed solution.
  The canonical SQL coordinator must remain the eventual source of truth rather than
  inheriting a parallel in-memory protocol by implication.
- **Doctrine/truth:** the result is labeled local/S2 only. It does not establish
  process-restart recovery, multi-replica mutual exclusion, cross-host liveness,
  database durability, or fenced side effects.

## Deferred work and required stronger evidence

The following remain open under R-11/F-10 and related findings:

- integrate heartbeat renewal into the actual supervisor/coordinator path;
- add SQL-level fencing and conditional owner/token writes;
- decide and implement pipeline/build/schema/policy/capability compatibility stamps,
  including safe resume/checkpoint/defer behavior;
- decide whether lease rows are system-wide or agency-scoped with RLS;
- define stale sweep/startup reconciliation and bounded requeue/poison transitions;
- prove behavior across process restart, multiple workers, and multiple hosts; and
- add independent runtime/browser/hosted evidence before calling the feature release-ready.

### Router-specific follow-up

The four existing `tests/test_agent_lease_router.py` cases cover the isolated
router's envelope/inspection, validation/contention, renewal/release/fencing,
and missing/idempotent paths, as recorded above. The older request to add those
same tests is superseded. Extend them to the actual server's authentication and
agency boundaries, then prove that the supervisor/worker checks a fencing token
atomically with each protected write. Isolated FastAPI route tests do not prove
SQL durability or application auth. Document the single canonical lease owner,
migration and rollback before exposing a replacement to hosted callers.

No claim is made that `spine_api/routers/agent_lease.py` is now backed by durable
PostgreSQL state: it still calls this in-memory manager.
