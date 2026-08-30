# Durable Agent Lease / Heartbeat — Design Exploration

**Date:** 2026-08-29
**Status:** Exploration / design proposal (NOT implemented, NOT verified)
**Canonical path:** `docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md`
**Author:** autonomous exploration agent
**Driving finding:** R-11 in `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md`
(line 129: "No durable lease/heartbeat for agents; zombie tasks on restart",
line 152: "Agent lease/heartbeat — P2 — Inferred — work loss on crash → Durable state machine").

**Doctrine note.** This document applies the operating doctrine's truth taxonomy. Every load-bearing
claim is tagged **Observed** (read directly from the live checkout), **Proposed** (a design, not
yet implemented or checked), or **Inferred** (best explanation supported by evidence, with the
assumption named). The design sections are **Proposed** unless tagged otherwise. Nothing here is
presented as verified runtime truth. See `OPERATING_DOCTRINE.md` §2 (truth taxonomy) and
`ARCHITECTURE_DOCTRINE.md`.

---

## 0. Executive summary

**Observed:** The repo already has a *partial* durable lease implementation. It is not missing a
lease mechanism so much as missing a *liveness* (heartbeat), *conflict* (fencing), and
*reconciliation* (STALE sweep / crash reconcile) layer, plus the agency scoping the R-11 framing
asks for.

Specifically:

- `spine_api/services/agent_work_coordinator.py` — `SQLWorkCoordinator` persists a per-work-item
  lease in the `agent_work_leases` table (Alembic migration
  `alembic/versions/add_agent_work_leases.py`). Columns: `idempotency_key`, `agent_name`,
  `trip_id`, `action`, `owner`, `status`, `attempts`, `leased_until`, `last_reason`, timestamps.
- `spine_api/services/agent_requeue_jobs.py` — `RequeueJobStore` persists durable requeue jobs in
  `agent_requeue_jobs` (migration `add_agent_requeue_jobs.py`), and leases them with
  `FOR UPDATE SKIP LOCKED`.
- `src/agents/runtime.py` — `InMemoryWorkCoordinator` (the **default** backend) keeps leases in
  process memory only, so a restart loses them entirely. `AgentSupervisor.run_once()` is the
  only driver that calls `acquire()`.

What is genuinely absent today:

1. **No heartbeat refresh.** `leased_until` is set once at acquire time to `now + lease_seconds`
   and never extended. A work item whose execution outlives `lease_seconds` (default 60s) has
   its lease expire *while it is still running*. There is no background liveness ping.
2. **No fencing token.** A worker that lost its lease (expired, or reclaimed by another pass)
   keeps writing to the trip with no monotonic generation check, so two workers can operate on
   the same work item concurrently. This is the classic lease-expiry split-brain.
3. **No STALE state / DB-level stale sweep.** The SQL coordinator re-acquires expired leases only
   when the supervisor happens to re-scan that exact work item. If the agent's `scan()` predicate
   no longer yields the work item, the `RUNNING` row is orphaned forever. There is no sweeper that
   transitions expired `RUNNING` → `STALE` and requeues.
4. **No startup reconcile.** `lifespan()` starts the recovery/supervisor/requeue/zombie services but
   does not mark orphaned `RUNNING` rows stale or requeue their work items after a restart.
5. **No agency scoping on the lease tables.** `agent_work_leases` and `agent_requeue_jobs` have no
   `agency_id` column and are deliberately system-wide (documented in
   `Docs/status/AGENT_REQUEUE_SCHEMA_OWNERSHIP_DECISION_2026-05-18.md`). Work is scoped by
   `trip_id`, which itself is agency-scoped, but the lease/queue layer is not tenant-isolated.

**Proposed (this doc):** evolve the existing `agent_work_leases` into a richer
`agent_instance`-style execution table that adds `agent_instance_id`, `heartbeat_at`, `owner_pid`,
a formal `STALE` state, and a fencing token — and then decide deliberately whether to scope it by
`agency_id`/RLS (tension with the existing system-wide design, §6.3).

---

## 1. Problem statement — current state of the agent runtime

### 1.1 What the runtime looks like (Observed)

`spine_api/server.py` `lifespan()` (lines 1020–1144) starts four background services at boot,
and stops them at shutdown:

```python
if not os.environ.get("RUNNING_TESTS"):
    _build_agent_runtime_bundle()      # server.py:1085
    _recovery_agent.start()            # server.py:1086
    _agent_supervisor.start()          # server.py:1087
    _requeue_worker_service.start()    # server.py:1088-1089
    _zombie_reaper_start()             # server.py:1090
```

- `_build_agent_runtime_bundle()` (`agent_runtime_factory.py:299`) constructs the bundle via
  `build_agent_runtime()` → `build_agent_runtime_config()` + `build_agent_runtime_from_config()`.
- `AgentSupervisor` (`src/agents/runtime.py:290`) runs a loop (`_run_loop`, line 330) that calls
  `run_once()` (line 338) on `interval_seconds` cadence (default 300s). `run_once()` scans the
  active-trip repository, `scan()`s each registered agent to produce `WorkItem`s, and for each one
  calls `self.coordinator.acquire(...)` (line 356) before executing.
- The coordinator is chosen by env `AGENT_WORK_COORDINATOR`. **Default is `"memory"`**
  (`agent_runtime_factory.py:132`), which yields `coordinator=None` and the supervisor defaulting
  to `InMemoryWorkCoordinator()` (line 303). `"sql"` yields `SQLWorkCoordinator` (line 206).
- `_recovery_agent` (`src/agents/recovery_agent.py`) detects trips *stuck in a stage* (by
  `updated_at` age vs a stage threshold, `_detect_stuck_trips:184`) and requeues or escalates.
  It is **not** a per-work-item lease recovery mechanism — it works at the *trip/stage* granularity.
- `_zombie_reaper` (`server.py:1511–1549`) is an OS-level reaper: `os.waitpid(-1, WNOHANG)`.
  It reaps **already-dead child processes** so they don't become zombies in the process table.
  It knows nothing about DB rows or agent work items.

### 1.2 Why restarts lose work or create zombies (Inferred, with named assumptions)

**Assumption A1: execution is synchronous inside a single supervisor pass.** `run_once()` calls
`agent.execute(item, trip_repo)` inline (line 389). There is no separate persistent worker process
per work item, and no durable record of "this work item is being executed by pid X" beyond the
octet of columns in the lease table. So "zombie task" means: *a lease row stuck in `RUNNING` whose
owner no longer exists*, or *in-memory lease state lost on restart*.

**Assumption A2: the supervisor executes on a daemon thread in the same process as the API.** The
threads are `threading.Thread(..., daemon=True)`. If the process is killed (deploy, OOM, crash),
all daemon threads die with it. In-memory coordinator state (`InMemoryWorkCoordinator._leases`)
is irrecoverable.

Consequences:

1. **Default (in-memory) mode loses all in-flight work on restart.** `InMemoryWorkCoordinator`
   (`runtime.py:188`) keeps `_leases`, `_completed`, `_poisoned` in a process dictionary. A restart
   empties them. Any work item that was `RUNNING` is restarted from scratch on the next scan (the
   agent's `scan()` will re-yield it if the underlying trip is still in an eligible state), which can
   duplicate a partially-applied side effect (e.g. a `trip_repo.update_trip(...)` that already
   wrote a `front_door_assessment`). The agent's *idempotency contract* (per-agent
   `AgentDefinition.idempotency_contract`) is a best-effort mitigation, not a hard guarantee.
2. **SQL mode keeps the row but not the liveness.** `SQLWorkCoordinator` persists `RUNNING` with
   `leased_until = now + lease_seconds` (default 60s) and never refreshes it. On restart the rows
   survive, but (a) nothing marks them stale, and (b) they are only re-acquired if the supervisor
   re-scans that exact work item. If the trip has since left the agent's eligible state, the row is
   orphaned `RUNNING` forever.
3. **Two workers on one work item (no fencing).** Because `leased_until` is a fixed TTL and there is
   no fencing token, a slow worker whose lease expired can be re-acquired by a second pass while the
   first is still executing. Both then write the trip. `_acquire` re-claims by *incrementing
   `attempts`*, so the second worker consumes retry budget on a the-live-first-worker's behalf.
4. **The OS zombie reaper does not address any of this.** It reaps child processes only. It has no
   DB access and cannot detect a stale lease or requeue a work item. This is the gap the R-11 finding
   names as "zombie tasks on restart."

**Observed counterbalance.** The *requeue* path is already durable and lease-protected:
`RequeueJobStore._lease_pending_async` uses `WHERE ... FOR UPDATE SKIP LOCKED` and `leased_until`
(`agent_requeue_jobs.py:160-207`). So the system is not uniformly fragile — the requeue *job* layer
is sound; the *work* lease layer is the weak point.

---

## 2. Source-of-truth state model (Proposed)

### 2.1 The durable agent-execution table

Treat the Postgres table as the **source of truth** for in-flight and terminal agent work. Proposed
columns (this deliberately generalizes the existing `agent_work_leases`):

| Column | Type | Semantics | Relationship to existing |
|---|---|---|---|
| `agent_instance_id` | `uuid` **PK** | One row per *execution attempt* of a work item. Grows on every lease re-acquire / retry. | **new** — today the PK is `idempotency_key` |
| `work_item_id` | `varchar` | Stable identity of the work unit (today = `WorkItem.idempotency_key`). Indexed; unique together with status. | = `agent_work_leases.idempotency_key` |
| `agency_id` | `varchar` FK → `agencies.id` | Tenant scoping. **Optional per §6.3** — existing table has none. | new (decision required) |
| `agent_name` | `varchar` | Which product agent owns the work. | = `agent_work_leases.agent_name` |
| `trip_id` | `varchar` | The trip the work item targets. | = `agent_work_leases.trip_id` |
| `action` | `varchar` | The action being taken. | = `agent_work_leases.action` |
| `status` | `enum` | `PENDING / RUNNING / COMPLETED / FAILED / STALE` (see 2.2). | superset of `agent_work_leases.status` |
| `lease_expires_at` | `timestamptz` | Absolute deadline a lease holder must refresh. | = `agent_work_leases.leased_until` |
| `heartbeat_at` | `timestamptz` | Last liveness ping. Drives STALE detection when `lease_expires_at` is not the only signal. | **new** |
| `owner_pid` | `int` | OS pid (and optional worker/host id) holding the lease. Fencing/ownership diagnostics. | **new** (existing `owner` is a *name*, not a pid) |
| `fence_token` | `bigint` | Monotonic generation incremented on each acquire. Prevents a stale worker from writing after losing its lease. | **new** |
| `attempt_count` | `int` | Retry counter; bounds retries. | = `agent_work_leases.attempts` |
| `idempotency_key` | `varchar` **unique** | Dedup boundary so the same *logical* work item is never committed twice. Today it is also the PK. | = `agent_work_leases.idempotency_key` |
| `payload` / `last_reason` / `error` | `jsonb`/`text` | Execution context and terminal diagnostic. | `last_reason` exists; `payload` on the requeue table |
| `created_at` / `updated_at` | `timestamptz` | Audit. | exists |

> **Note on PK.** The existing table keys on `idempotency_key`, which means one row per logical work
> item and the lease/attempt state is *overwritten in place*. The proposed `agent_instance_id` PK
> keeps an **append-only execution history** (one row per attempt) while `idempotency_key` remains
> the unique dedup boundary. This is what makes "how many times did we try" and "which attempt is
> live" separately answerable.

### 2.2 Status model

The existing enum (`src/agents/runtime.py:41`) is:
`PENDING, RUNNING, COMPLETED, RETRY_PENDING, POISONED, ESCALATED, INTERRUPTED_RECOVERABLE`.

The proposed execution-table statuses are intentionally a **different, DB-faithful** set, with a
mapping (this is a **Proposed** mapping; the runtime enum would be reconciled):

| Proposed (DB) | Runtime analog | Meaning |
|---|---|---|
| `PENDING` | `PENDING` | Not yet leased; eligible for a worker. |
| `RUNNING` | `RUNNING` | A worker holds a live lease and is executing. |
| `COMPLETED` | `COMPLETED` | Finished successfully; terminal; honored by idempotency. |
| `FAILED` | `RETRY_PENDING` / `POISONED` | Terminal or retry-exhausted. `attempt_count` vs `max_attempts` distinguishes retryable vs poison. |
| `STALE` | (none — **new**) | Lease expired without heartbeat; the prior owner is presumed dead; eligible for requeue. |

`STALE` is the key addition: it is the *discovered* state between RUNNING and a retry decision,
produced by a sweeper (not by a worker). It exists so that (a) an operator can see the work was
interrupted rather than merely re-running, and (b) the requeue decision is bounded by `attempt_count`.

---

## 3. Lease / heartbeat protocol (Proposed)

### 3.1 Acquire

A worker acquires a work item with a single atomic statement that both:

- selects a row that is either `PENDING` or `RUNNING` **with an expired lease**, and
- claims it.

Two mechanisms are viable. **PostgreSQL row lock** is preferred for correctness and reuses existing
patterns; **advisory lock** is an alternative.

**Row-lock acquire** (compare with the existing `WHERE ... FOR UPDATE SKIP LOCKED` used by
`RequeueJobStore._lease_pending_async:160-207`):

```sql
-- Claim one eligible work item for this worker; only one worker ever wins.
UPDATE agent_instances
SET    status = 'RUNNING',
       owner_pid = :pid,
       lease_expires_at = :now + (:lease_seconds * interval '1 second'),
       heartbeat_at      = :now,
       fence_token       = fence_token + 1,
       attempt_count     = attempt_count + 1,
       updated_at        = :now
WHERE  id = (
    SELECT id
    FROM   agent_instances
    WHERE  agency_id IS NOT DISTINCT FROM :agency_id      -- if scoped (see §6.3)
      AND  ( status = 'PENDING'
             OR (status = 'RUNNING' AND lease_expires_at < :now)
             OR (status = 'STALE'  AND attempt_count < :max_attempts) )
      AND  attempt_count < :max_attempts
    ORDER  BY updated_at ASC
    LIMIT  1
    FOR    UPDATE SKIP LOCKED            -- skip rows another worker is already claiming
)
RETURNING id, work_item_id, fence_token, attempt_count, owner_pid;
```

Key properties:
- `FOR UPDATE SKIP LOCKED` lets many workers race without blocking, and without claiming the same
  row. This is `Observed` to already be the established pattern in `agent_requeue_jobs.py`.
- The `WHERE` clause is deliberately **not** a "compare-and-set" on a single row; it is a
  claim-eligible-row set that the `UPDATE` locks and updates in one statement, so two workers can
  never get the same row.
- `fence_token + 1` makes the token **monotonically increasing per attempt**. A worker that holds
  token N can be invalidated the moment a reclaim increments the row to N+1.

**Alternative — dedicated advisory lock.** `SELECT pg_try_advisory_lock(xact_id)`. This avoids
writing to the row during acquire and is useful when the *set* of eligible rows is computed
separately. Tradeoffs in §8.3. The advisory lock must be held for the whole execution and released
after; it does not naturally yield the fencing-token on write (fencing still needs a column).

**Fencing token enforcement on every write.** Every trip/state mutation performed *by the worker*
must be conditional on the fence token it was handed at acquire:

```sql
UPDATE trips
SET    front_door_assessment = :payload,
       updated_at = :now
WHERE  id = :trip_id
  AND  EXISTS (
        SELECT 1 FROM agent_instances
        WHERE work_item_id = :work_item_id
          AND fence_token = :my_fence_token
          AND status = 'RUNNING'
  );
```

If this updates 0 rows, the worker lost its lease and must stop immediately (abort, no further
side effects, do not emit `COMPLETED`). This is the concrete mechanism that prevents the
split-brain where a stale worker and a fresh worker both write.

### 3.2 Heartbeat

While executing, the worker refreshes the lease on a fixed interval (`heartbeat_interval <
lease_seconds`, e.g. every 15s for a 60s lease, or a fraction like 1/4 of the TTL):

```sql
UPDATE agent_instances
SET    lease_expires_at = :now + (:lease_seconds * interval '1 second'),
       heartbeat_at      = :now
WHERE  work_item_id = :work_item_id
  AND  owner_pid = :pid
  AND  fence_token = :my_fence_token
  AND  status = 'RUNNING';
```

- The heartbeat **re-asserts ownership** via `owner_pid` + `fence_token`, so a worker that has
  effectively been replaced gets a 0-row update and can notice and abort.
- `heartbeat_at` is the *liveness* signal. `lease_expires_at` is the *deadline*. STALE detection can
  use either (deadline is primary), which matters for the disagreement case in §3.3.
- A worker that finishes is expected to release by calling `complete()`; the heartbeat loop must be
  cancelled on completion so it cannot resurrect a `COMPLETED` row back to `RUNNING`.

**Observed note.** The existing `ExecutionLease` dataclass in `src/agents/runtime.py:52` has an
in-memory `heartbeat()` method that extends `lease_expires_at` in place. It is **not** wired into
`AgentSupervisor` or `SQLWorkCoordinator` (grep shows no call site outside the dataclass itself).
So the heartbeat *concept* exists but is dead code — there is no loop that calls it, and no persisted
`heartbeat_at` column. This doc's proposal is effectively "make the dead heartbeat real, in SQL."

### 3.3 Lease expiry / STALE detection

Two signals compete:

1. **Deadline (`lease_expires_at < now`).** A worker failed to heartbeat in time. Primary signal.
2. **Liveness staleness (`heartbeat_at` too old).** `heartbeat_at < now - stale_grace`. Configured
   `stale_grace > lease_seconds` to absorb GC pauses and clock skew.

A sweeper (see §4) transitions rows into `STALE` when either condition holds **and** the owner pid
is no longer alive. Owner-aliveness is checked cheaply:

- same-process workers: `os.kill(pid, 0)` / `psutil.pid_exists` → `False` ⇒ dead;
- remote/multi-host workers: rely on the heartbeat only (no shared pid namespace), which is why
  `stale_grace` must exceed `lease_seconds` and why `owner_pid` alone is not sufficient cross-host
  (see §9 open question OQ-1).

The stale row's `attempt_count` is then contrasted with `max_attempts` to decide requeue vs poison.

---

## 4. Zombie-task detection & recovery (Proposed)

The word "zombie" is used for two distinct things; both must be handled and they are **different
mechanisms**:

| Zombie kind | Detector | Recovery |
|---|---|---|
| **OS zombie** (child process exited, parent hasn't `wait()`ed) | `_zombie_reaper` (`server.py:1511-1549`) — `os.waitpid(-1, WNOHANG)` every 5s | `waitpid` reaps it. **Keep as-is.** |
| **DB zombie** (lease row `RUNNING`, owner gone, lease expired) | **new** `agent_instance_stale_sweeper` | Transition to `STALE`, then requeue / poison per `attempt_count`. |

### 4.1 The existing `_zombie_reaper`

**Observed.** It is correct for what it does and should remain. It has no notion of DB state and
cannot requeue work. Do not "fix" it into a DB sweeper — add a **separate** DB sweeper.

### 4.2 New DB-level STALE sweep

A dedicated background task (lifecycle like the others in `lifespan()`; a thread or an
`asyncio` task) that runs periodically (default 15–30s, independent of the supervisor's 300s pass):

```sql
-- 1. Mark expired leases STALE (idempotent: only touches RUNNING rows).
UPDATE agent_instances
SET    status = 'STALE',
       updated_at = :now
WHERE  status = 'RUNNING'
  AND  ( lease_expires_at < :now
         OR heartbeat_at < :now - (:stale_grace * interval '1 second') )
  AND  owner_pid IS NOT DISTINCT FROM :own_pid /* same-process optimization; cross-host uses heartbeat */
  AND  attempt_count < :max_attempts;   -- if budget exhausted, leave as RUNNING→ flagged for poison
```

```sql
-- 2. Requeue: reactivate STALE rows as PENDING (bounded by attempt_count).
UPDATE agent_instances
SET    status = 'PENDING',
       lease_expires_at = NULL,
       heartbeat_at = :now,
       updated_at = :now
WHERE  status = 'STALE'
  AND  attempt_count < :max_attempts;
```

```sql
-- 3. Poison: rows that exhausted the retry budget become FAILED (or an explicit POISONED marker).
UPDATE agent_instances
SET    status = 'FAILED',
       last_reason = 'retry_policy_exhausted',
       updated_at = :now
WHERE  status = 'STALE'
  AND  attempt_count >= :max_attempts;
```

Idempotency and ordering: the sweep is safe to run repeatedly; `STALE` is a self-describing state,
and step 2 re-arms only rows under budget. The sweeper must be **single-writer** (one process at a
time), otherwise two sweepers race. A Postgres advisory lock on a fixed key
(`pg_try_advisory_lock('agent_instance_stale_sweeper')`) or a "last sweep time" doc row guards this.

**Observed precedent for the sweepers-vs-workers ownership split.** `src/agents/recovery_agent.py`
is already the *trip/stage* level recovery loop; `spine_api/services/agent_requeue_jobs.py`
`RequeueWorker` is the durable *requeue job* executor. This proposal generalizes the same
"detect → mark → requeue" ladder down to the *work-item/lease* level. The recovery agent's
requeue decision (attempts < max → re_queue, else escalate) is reused as the `attempt_count`
gate.

### 4.3 Idempotent resume semantics (Proposed)

Re-walking a work item after a crash must be **safe to repeat**:

1. **The side effect must be keyed by `idempotency_key`.** On re-execution, the agent re-runs its
   `scan()`/`execute()`; the side effect (a `trip_repo.update_trip(...)`) is guarded by the fence
   token (only the live worker's write lands) and by the agent's own idempotency contract. The
   result is *at-most-once* for the mutation, not exactly-once — if the trip update already landed
   before the crash, the requeued run re-computes the same value (idempotent contract) and the DB
   converges to the same state. This is the honest guarantee to state in behavior docs: **at-least
   once execution, at-most-once commit per idempotency key.**
2. **Do not reset `attempt_count` to 0 on resume.** The whole point of `attempt_count` is to bound
   retries across crashes. Only the requeue decision (and possibly a manual operator reset) clears it.
3. **Terminal rows (`COMPLETED`) are never re-armed.** `acquire()`'s WHERE clause excludes
   `COMPLETED`, and idempotency re-entry short-circuits. This prevents re-running a finished work item
   merely because a stale replica re-scanned the trip.

---

## 5. Crash-recovery (Proposed)

On server restart, `lifespan()` must run a **one-shot reconcile** before (or immediately after) the
background services start. Today it does **not** (`Observed` — see §1.2). Proposed steps:

1. **Mark orphaned `RUNNING` rows as `STALE`.**
   `UPDATE agent_instances SET status='STALE', updated_at=now() WHERE status='RUNNING' AND owner_pid
   NOT IN (SELECT pid FROM pg_stat_activity)` — or, equivalently, rely on the sweeper. During a
   boot where the old pids are gone, every surviving `RUNNING` row is orphaned by definition, so a
   simpler boot-time statement is valid: transition all `RUNNING` → `STALE` once at start.
2. **Requeue the now-stale work items** back to `PENDING` (bounded by `attempt_count`), so the
   supervisor re-yields them on its next pass. Alternatively enqueue durable requeue jobs via the
   existing `RequeueJobStore`, which reuses the already-sound durable requeue path (§3/§4 of
   `agent_requeue_jobs.py`).
3. **Do not clear `attempt_count`.** Crash counts as a retry.
4. **Guard against boot-time double-processing.** The reconcile must be **single-run** and not race
   the supervisor's first pass. Do the reconcile *before* `_agent_supervisor.start()` in lifespan,
   or use an advisory lock so that exactly one node/process reconciles in a multi-node deploy.
5. **Idempotency.** The reconcile is idempotent (re-running it lines up already-`STALE` rows with
   the requeue predicate and moves nothing twice).

### 5.1 The shutdown side

`lifespan()` already stops services on shutdown (`_zombie_reaper_stop()`, `_requeue_worker_service.stop()`,
`_agent_supervisor.stop()`, `_recovery_agent.stop()`, `server.py:1137-1143`). Graceful shutdown should
**release** held leases (transition live `RUNNING` rows to `PENDING` or set `lease_expires_at=now()`)
so they are immediately re-claimable rather than waiting out the TTL. This is a **Proposed** addition;
today a graceful stop simply abandons the row (in SQL mode it waits out `lease_seconds`).

---

## 6. Integration points

### 6.1 How `src/agents/runtime.py` returns map to the state machine

`AgentExecutionResult` (`runtime.py:118`) carries `status: WorkStatus`, `success`, `reason`, `output`,
`attempt`. The supervisor's `run_once` (lines 388–418) currently branches on `result.success`:

- success → `coordinator.complete(item, result.reason)` (line 402)
- failure → `terminal = attempt >= retry_policy.max_attempts`; `coordinator.fail(item, POISONED if
  terminal else RETRY_PENDING)` (lines 405-407)

**Proposed mapping to the durable table:**

- `acquire()` returns `(True, reason, fence_token, attempt)`; the row becomes `RUNNING`.
- `complete()` → `UPDATE ... SET status='COMPLETED', lease_expires_at=NULL`.
- `fail(...)` with `RETRY_PENDING` → leave the row `RUNNING`-expired (or set a retryable `FAILED`
  with a backoff lease) so the sweeper/requeue path re-arms it; only set `FAILED` (poison) when
  `attempt_count >= max_attempts`.
- Add an explicit `STALE` transition that is **only ever written by the sweeper or boot reconcile**,
  never by a worker — so the runtime enum's `INTERRUPTED_RECOVERABLE` maps to `STALE`.

Because `run_once` is synchronous and single-threaded per agent, in the *current* design the
fence token is trivially held for the duration of one `execute()`. The wrap-around to **no** concern is
when two supervisor processes run concurrently (e.g. `uvicorn --workers N`). Note `SPINE_API_WORKERS`
defaults to 1 (`server.py:595`), so today a single process is the norm — but the durable design must
assume >1 worker (see §9 OQ-4).

### 6.2 How the supervisor uses the lease

`AgentSupervisor` will call `coordinator.acquire(...)` exactly as it does today, but the
`WorkCoordinator` protocol (`runtime.py:165`) must be extended to return the fence token and to add
`heartbeat(work_item, fence_token, owner)`. The supervisor:

- acquires → gets `(fence_token, attempt)`;
- starts a heartbeat thread/task for that work item (cancelled on completion);
- runs `execute()`, passing the *guard* into every `trip_repo.update_trip(...)` call so writes are
  fenced (this is the big integration change — the agent `execute()` methods currently call
  `trip_repo.update_trip(trip_id, updates)` with no guard). Two options: (a) thread a fence-guard
  context through `execute()`; (b) make `TripStoreAdapter.update_trip` take an optional
  `fence_check` callable. Option (b) is less invasive to the 17 agents.

**Observed:** 17 agents are registered (`build_default_registry`, `runtime.py:3150`), each with its
own `idempotency_contract` and `retry_policy`. The fence token is additive — it does not change the
agents' scan/execute contracts, only the *write path*.

### 6.3 How dequeuing is scoped by `agency_id` (RLS)

This is the single biggest **design tension** and it is worth stating plainly.

**Observed.** `agent_work_leases` and `agent_requeue_jobs` are **system-wide coordination tables with
no `agency_id` column and no RLS**. The rationale is documented in
`Docs/status/AGENT_REQUEUE_SCHEMA_OWNERSHIP_DECISION_2026-05-18.md` §3/§5:

> "These are system coordination tables … RLS as implemented requires `agency_id` to be present —
> it would not apply without a schema change … Adding `agency_id` and RLS would change semantics
> (system queue → per-tenant queue), which is not the intent."

`spine_api/core/rls.py` `RLS_TENANT_TABLES` (line 46) enumerates 11 tenant tables (`trips`,
`memberships`, `workspace_codes`, `booking_collection_tokens`, `trip_routing_states`,
`booking_documents`, `document_extractions`, `document_extraction_attempts`, `booking_tasks`,
`booking_confirmations`, `execution_events`) — neither lease table is in it.

**The tension.** The task asks for "dequeuing scoped by `agency_id` (RLS)." That directly conflicts
with the observed, deliberate system-wide design. Two coherent resolutions:

**Option 1 — per-tenant lease table (RLS-scoped).** Add `agency_id` to `agent_instances`, add it to
`RLS_TENANT_TABLES`, and enable `waypoint_rls_select`/`waypoint_rls_all` policies keyed on
`app.current_agency_id`. Dequeuing then runs inside a transaction where `app.current_agency_id` is
set per-agency. **Cost:** the worker must know which agency it is serving, changing the current
coordinator (which leases across all agencies in one query) into a per-agency loop, OR the worker
serves a single agency. This mirrors the observed *trip* data path, where
`SQLTripStore.update_trip_for_agency` and `_rls_session_for_agency` set `app.current_agency_id`
explicitly (`persistence.py:781, 1207`).

**Option 2 — keep the table system-wide, scope by `trip_id`.** Keep no `agency_id`; rely on
`trip_id` (which is agency-owned) as the tenant key, and enforce isolation only at the trip-write
path (already RLS'd via `trips`). This is the status quo and is defensible because the lease table
holds **no tenant data** beyond a foreign `trip_id`.

**Recommendation (Proposed):** For the *execution* table, follow **Option 1** but only if you
accept the per-agency dequeuing semantic. If you want to preserve the "one worker serves all
agencies" optimization, choose **Option 2** and accept that the lease table is not RLS-isolated
(the isolation guarantee is inherited via the `trips` write path). This must be decided explicitly —
it is a cross-cutting ownership decision, not an implementation detail. See §9 OQ-3. The existing
decision doc (Option C) already flagged this as "not the right move now," which suggests the project
has implicitly chosen Option 2 — but the R-11 task framing asks for RLS scoping, so the conflict
should be surfaced rather than silently resolved.

**Observed nuance for the background supervisor.** The supervisor scans trips via
`TripStoreAdapter.list_active()` → `SQLTripStore.list_trips()` → `_rls_session()` (`persistence.py:948,
772`), which reads `app.current_agency_id` from a `ContextVar` (`get_rls_agency()`). In a background
**daemon thread**, that ContextVar is typically **None** (it is set per-request by
`get_current_membership`). So an agent supervisor scan runs with **no agency context**, and depending
on the runtime role it either sees all trips (owner role, ENABLE RLS only) or none (non-owner role,
FORCE RLS). This is a real correctness gap independent of the lease table, and should be addressed by
making background agent scans explicitly iterate agencies and set `app.current_agency_id` per agency
(via `_rls_session_for_agency`), not by relying on the request ContextVar. Flagging as it directly
affects "how dequeuing is scoped by agency_id."

---

## 7. First-principles decomposition (Proposed)

Strip the domain nouns and name the primitives the durable-agent-execution design is built from:

| Primitive | Definition | Existing | Gap |
|---|---|---|---|
| **Lease** | Exclusive right to execute a work item for a bounded window. | `agent_work_leases` / `SQLWorkCoordinator` | TTL only; no liveness refresh |
| **Heartbeat** | Periodic extension of the lease to prove the owner is alive. | `ExecutionLease.heartbeat()` (dead code) | Not wired; not persisted |
| **Fencing token** | Monotonic generation that invalidates a stale owner's writes. | — | **Missing** — the split-brain cause |
| **Idempotency** | Guarantee a logical work item commits at most once. | `idempotency_key` per work item; per-agent `idempotency_contract` | Best-effort at runtime; needs DB enforcement |
| **Requeue** | Re-arm an interrupted work item for a fresh attempt, bounded. | `RequeueJobStore` + `RequeueWorker` (durable, `SKIP LOCKED`) | Works for requeue *jobs*, not for *work leases* directly |
| **Dead-letter** | Terminal isolation of permanently failing work for operator review. | `POISONED` / `ESCAPED` / `review_status=escalated` | No single durable DLQ marker at work-item level |
| **Agency scoping** | Tenant isolation of the work-queue state. | `trips`-level RLS only | Lease tables are system-wide (deliberate) |

Composition: `acquire` = `lease` + `fence token` allocation; `heartbeat` = `lease` renewal;
`sweeper` = `lease` expiry + `requeue`/`dead-letter`; boot reconcile = `requeue` after restore.
These seven primitives are orthogonal; the design cleanly maps each to one mechanism. This matches
the `ARCHITECTURE_DOCTRINE` preference for explicit boundaries and single owners.

---

## 8. Alternative approaches rejected

### 8.1 In-memory only (status quo default)

**Rejected.** `InMemoryWorkCoordinator` is the default (`agent_runtime_factory.py:132`). It is fast
and adequate for a single-process demo, but it is **not durable**: an `AgentSupervisor` restart
empties `_leases`/`_completed`/`_poisoned`, losing in-flight and health. It also has no cross-process
guarantee — `uvicorn --workers N` would each have a private coordinator (see §9 OQ-4). Given R-11
explicitly names "zombie tasks on restart," in-memory is the exact failure mode being fixed.

### 8.2 Celery / RQ / full task queue

**Rejected as overkill, and as a composition mismatch.** The system already has (a) a Postgres
coordination layer, (b) a durable requeue job store, and (c) 17 in-process agents with their own
scan/execute contracts. Introducing Celery/RQ would add a broker, a new serialization boundary, a new
worker deployment, and a second source of truth for leases/status — fighting the doctrine's "one
canonical source per route/schema." The existing `SQLWorkCoordinator` + a **heartbeat/fencing/stale
sweeper** extension achieves durable work-lease semantics inside the Postgres the project already owns,
with no new infrastructure. Celery's value (distributed task graph, retries, routing) is not what
R-11 is asking for (that is *lease liveness and crash recovery*), so it would be architectural
theater.

### 8.3 Optimistic-lock only (e.g. `version`/`updated_at` compare-and-set on the trip)

**Rejected as insufficient.** Optimistic locking on the *trip* row (the `expected_updated_at` param
already used by `update_trip_for_agency`, `persistence.py:1196-1203`) can prevent a lost update on the
trip itself, but it does **not** prevent two workers from claiming the *same work item* in the first
place, nor does it track lease expiry / heartbeat / owner liveness. Without a lease you still get
double-execution of a long task and double side effects; with optimistic locking alone, the second
worker merely fails its CAS *after* doing the work. The fencing-token-over-a-lease design subsumes
optimistic locking while additionally solving mutual-exclusion, liveness, and crash recovery.

### 8.4 Pure advisory locks, no lease row

**Partially rejected.** `pg_try_advisory_lock` is a good mutual-exclusion primitive and avoids a
"lease metadata" table. But it does not persist *status* or *history* (`attempt_count`, terminal
states, idempotency dedup) that operators need to inspect, and it does not give a durable record that
survives a crash for *reconciliation* — after a crash the lock is gone (Postgres releases it) but you
have no record of which work items were in flight. Advisory locks are retained as the *sweeper
single-writer* guard and as an *optional acquire* alternative, but not as the sole source of truth.
The row-based lease is the durable state; advisory lock is a concurrency guard.

---

## 9. Open questions and stopping rules

**Open questions (blocking / high value):**

- **OQ-1 — Cross-host ownership.** Is the runtime single-node (one `uvicorn`, `SPINE_API_WORKERS=1`)
  or multi-host? If multi-host, `owner_pid` is not a reliable liveness signal across the cluster and
  STALE detection must rely purely on `heartbeat_at`/`lease_expires_at`, with `stale_grace > lease`.
  This sets whether we also need a host id in the lease row. *Check: current deployment model and
  `SPINE_API_WORKERS` value in prod.*
- **OQ-2 — Fencing enforcement scope.** Do we enforce the fence token on *every* agent trip write
  (option b in §6.2 — thread through `TripStoreAdapter.update_trip`), or only on the *terminal*
  `complete()`/`fail()`? Enforcing everywhere is safer but touches all 17 agents' write paths.
- **OQ-3 — `agency_id` + RLS on the lease table.** Adopt Option 1 (per-tenant, RLS-scoped, worker
  serves one agency) or Option 2 (system-wide, scope by `trip_id`, no RLS)? This is the explicit
  conflict between the R-11 framing and the existing `AGENT_REQUEUE_SCHEMA_OWNERSHIP_DECISION`. Must
  be decided by the architecture owner before implementation.
- **OQ-4 — Multiple worker processes.** Does the durable lease need to support >1 concurrent supervisor
  (e.g. multi-worker uvicorn, or a future worker fleet)? The `FOR UPDATE SKIP LOCKED` claim already
  handles it, but the *background agent scan agency-context gap* (§6.3) becomes a hard bug under
  multi-worker.
- **OQ-5 — Status enum reconciliation.** Should `src/agents/runtime.py` `WorkStatus` gain `FAILED`
  and `STALE`, or should the DB enum be a separate, richer model with a mapping (as proposed in §2.2)?
  Keeping two enums risks drift; merging them couples the runtime to DB states.
- **OQ-6 — `agent_work_leases` vs `agent_instances`.** Do we evolve the existing
  `agent_work_leases` table (add columns in place, keep `idempotency_key` PK) or introduce a new
  `agent_instances` table with an `agent_instance_id` PK and migrate/backfill? The in-place evolution
  is lower-risk but loses append-only attempt history; a new table is cleaner but needs a migration
  and a decision on what happens to live rows.

**Stopping rules:**

1. **Stop design when the seven primitives (§7) have a single owner each and no two mechanisms
   overlap.** If a mechanism needs to be both a lease and a queue, that is scope creep.
2. **Stop before implementing.** This is an exploration/design artifact. It hands implementation
   tasks to the architecture and testing doctrines; it does **not** grant permission to write code.
3. **Stop on unverifiable claims.** Any claim about multi-host behavior, prod `SPINE_API_WORKERS`,
   or the real backfilled state of `agent_work_leases`/`agent_requeue_jobs` must be resolved by
   reading the live DB before it becomes a design input (see OQ-1, OQ-4).
4. **Stop and escalate on the RLS conflict (OQ-3).** Do not silently choose; the two options are
   materially different semantics. The architecture owner must decide.

---

## 10. Sources / evidence index

**Code (Observed):**

- `spine_api/server.py` — `lifespan` 1020–1144; agent runtime start 1084–1090; `_zombie_reaper` /
  `_reap_zombies` 1511–1549.
- `src/agents/runtime.py` — `WorkStatus` 41; `ExecutionLease` 52; `WorkCoordinator` protocol 165;
  `InMemoryWorkCoordinator` 188; `AgentSupervisor` 290; `run_once` 338–420; `build_default_registry`
  3150.
- `spine_api/services/agent_work_coordinator.py` — `SQLWorkCoordinator` 15; `ensure_schema` 21;
  `_acquire` 55; `_locked_row`/`FOR UPDATE` 161; `snapshot` 129.
- `spine_api/services/agent_requeue_jobs.py` — `RequeueJobStore` 48; `_lease_pending_async`
  `FOR UPDATE SKIP LOCKED` 160–207; `RequeueWorker` 365; `RequeueWorkerService` 431.
- `spine_api/services/agent_runtime_factory.py` — config defaults 49–66, 119–153; `coordinator`
  wiring 204–208.
- `src/agents/recovery_agent.py` — `RecoveryAgent` 89; `_recovery_pass` 159; `_detect_stuck_trips` 184;
  requeue action 286.
- `spine_api/persistence.py` — `tripstore_session_maker` 55; `_run_async_blocking` 1344;
  `SQLTripStore._rls_session` 772/`_rls_session_for_agency` 781; `list_trips` 948;
  `update_trip_for_agency` 1196–1213.
- `spine_api/models/tenant.py` — `Agency` 38; tenant models, membership agency scoping.
- `spine_api/core/rls.py` — `RLS_TENANT_TABLES` 46; `set_rls_agency` 132; `get_rls_db` 214;
  `rls_session` 250.
- `spine_api/routers/agent_runtime.py` — `configure_runtime` 32; `get_agent_runtime` 59;
  `run_agent_runtime_once` 92.

**Migrations (Observed):** `alembic/versions/add_agent_work_leases.py`;
`alembic/versions/add_agent_requeue_jobs.py`; `add_rls_tenant_isolation.py`.

**Decision / findings (Observed):** `Docs/status/AGENT_REQUEUE_SCHEMA_OWNERSHIP_DECISION_2026-05-18.md`;
`Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md` (R-11, lines 129/152).
