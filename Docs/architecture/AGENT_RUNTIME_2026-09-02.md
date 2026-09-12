# Agent Runtime — Production Map

**Date**: 2026-09-02 · **Status**: Documentation of what IS (all `file:line` evidence verified against the working tree on this date)
**Origin**: shadow-audit R-05; agent inventory from `Docs/exploration/AGENTIC_FLOW_DEEP_MAP_2026-08-31.md` (19 registered agents). Companion design research: `Docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md` (note: its "no durable lease exists" premise was partially wrong at birth — leases existed in `src/agents/runtime.py`; the SQL backends and fencing are the later hardening).

---

## 1. Shape of the system

A **deterministic, code-registered agent runtime** — no LLM in the serving loop. Agents are
classes implementing a `scan()`/`execute()` protocol (`src/agents/runtime.py:239-251`,
`ProductAgent`), registered by code in `build_default_registry()` (`runtime.py:3371-3398`,
19 agents), and driven by a single `AgentSupervisor` loop (`runtime.py:374`) that scans the
trip store, acquires single-owner leases on work items, executes, and emits events.

Assembly is centralized in `spine_api/services/agent_runtime_factory.py`:
`build_agent_runtime()` (`:253-266`) reads env → `build_agent_runtime_config()` (`:119-152`)
→ `build_agent_runtime_from_config()` (`:175-251`) → `AgentRuntimeBundle` (`:75-96`,
config + coordinator + recovery agent + supervisor + requeue worker). The single server call
site is `spine_api/server.py:286-310` (`_build_agent_runtime_bundle`).

**Config env vars** (`agent_runtime_factory.py:29-42`):

| Env var | Values (default) | Meaning |
|---|---|---|
| `DEPLOYMENT_MODE` | local/test/dogfood/beta/production (`local`) | `:32`, validated `:41` |
| `AGENT_WORK_COORDINATOR` | memory/sql (`memory`) | lease coordinator backend; `sql` → `SQLWorkCoordinator`, `memory` → supervisor-default in-memory (`factory:210-214`) |
| `AGENT_WORK_LEASE_SECONDS` | int (60) | lease TTL |
| `AGENT_SUPERVISOR_INTERVAL_S` | int (300) | scan interval |
| `AGENT_RECOVERY_REQUEUE_MODE` | disabled/inline/sql_queue (`disabled`) | recovery requeue port (`factory:216-241`) |
| `RECOVERY_INTERVAL_S` | int (300) | recovery scan interval |

## 2. Agent inventory (19 registered, `build_default_registry` `runtime.py:3378-3398`)

| # | Agent | Class location | Domain |
|---|---|---|---|
| 1 | FrontDoorAgent | `runtime.py:638` | intake triage |
| 2 | SalesActivationAgent | `runtime.py:760` | quote/proposal activation nudges |
| 3 | DocumentReadinessAgent | `runtime.py:974` | visa/passport document readiness |
| 4 | DestinationIntelligenceAgent | `runtime.py:1180` | destination intel flags |
| 5 | WeatherPivotAgent | `runtime.py:1382` | weather-driven itinerary pivots |
| 6 | ConstraintFeasibilityAgent | `runtime.py:1585` | constraint/feasibility checks |
| 7 | ProposalReadinessAgent | `runtime.py:2315` | proposal completeness |
| 8 | BookingReadinessAgent | `runtime.py:2473` | booking prerequisites |
| 9 | FlightStatusAgent | `runtime.py:2641` | flight status watch |
| 10 | TicketPriceWatchAgent | `runtime.py:2907` | price-drop watch |
| 11 | SafetyAlertAgent | `runtime.py:3013` | safety alerts |
| 12 | GDSSchemaBridgeAgent | `runtime.py:3144` | GDS schema bridging |
| 13 | PNRShadowAgent | `runtime.py:3215` | PNR shadow reconciliation |
| 14 | SupplierIntelligenceAgent | `runtime.py:3269` | supplier signals |
| 15 | FollowUpAgent | `runtime.py:843` | customer follow-ups |
| 16 | QualityEscalationAgent | `runtime.py:898` | quality escalation |
| 17 | ClosedLoopLearningAgent | `src/agents/closed_loop_learning.py` | override/outcome learning loop |
| 18 | CommunicatorAgent | `src/agents/communicator_agent.py` | outbound communication |
| 19 | OperatorRefinementAgent | `src/agents/operator_refinement_agent.py` | operator refinement cues |

Each carries an `AgentDefinition` (`runtime.py:176-188`) with a `RetryPolicy`
(`runtime.py:170-173`: `max_attempts=3`, `backoff_seconds=(0, 1, 5)` by default).

## 3. Lease / lifecycle model

**Three lease layers exist (deliberately distinct):**

1. **In-process work coordination** — `ExecutionLease` (`runtime.py:53-88`, fields include
   `owner_worker_id`, `last_heartbeat_at`) held by `InMemoryWorkCoordinator`
   (`runtime.py:273-…`, thread-safe single-owner acquire `:282-…`; retry-exhaustion gating
   `:295-304`) and its SQL twin `SQLWorkCoordinator`
   (`spine_api/services/agent_work_coordinator.py:15-…`; `acquire :52`, `complete :115`,
   `fail :118`, row-locked updates `:161-…`). `ZombieLeaseSweeper` reaps expired leases
   (`runtime.py:132-…`).
   ⚠️ **`ExecutionLease.heartbeat()` (`runtime.py:68`) has zero callers** — `rg "\.heartbeat\("`
   across `src/`+`spine_api/` → no matches (re-verified 2026-09-02; shadow-audit R-11 still
   holds). Leases are protected by TTL expiry, not renewal.
2. **Durable distributed leases** — `src/orchestration/agent_lease.py`: `MemoryAgentLeaseBackend`
   (`:59-172`) and `SqlAgentLeaseBackend` (`:174-…`, selected via `SPINE_API_AGENT_LEASE_BACKEND`,
   `:27`) with acquire/renew/release, `verify_fencing_token` (`:143`), and `sweep_stale_leases`
   (`:158`). SQL persistence table: `agent_leases` (`spine_api/models/agent_lease.py:18-21`).
3. **Run-level idempotency locks** — see §4; these fence *pipeline runs*, not agent work items.

**Supervisor lifecycle** (`runtime.py:374-530`): `start()` spawns a daemon thread emitting
`AGENT_STARTED` (`:400-407`); `_run_loop` runs `run_once()` every `interval_seconds`
(`:419-427`); `run_once(agent_name=None)` scans → acquires (via coordinator) → executes →
on failure marks retry vs terminal at `max_attempts` (`:491-…`); `health()` (`:508`) reports
registry/coordinator state. The supervisor wraps the trip repo with
`NextActionAwareTripRepo` (`:386`, from `src/orchestration/travel_next_action.py`).

## 4. Idempotency (SQL backend + fencing tokens)

`src/agents/idempotency.py` (746 lines):

- `IdempotencyStatus` enum (`:44`) — includes `UNKNOWN` (crash-ambiguity state, resolvable
  via `mark_unknown`/`resolve_unknown` `:397-…`).
- `SqlIdempotencyBackend` (`:76-…`): CAS acquisition (`try_acquire :167`, async `:179`),
  `mark_completed` (`:357`), `mark_failed` (`:380`), `mark_unknown` (`:397`),
  `resolve_unknown` (`:419`). Table: `idempotency_keys`
  (`spine_api/models/idempotency.py:35`), auto-created on first use
  (`idempotency.py:116-130`).
- **Fencing tokens**: every acquire mints `fencing_token = secrets.token_urlsafe(32)`
  (`idempotency.py:68,198,259,318`); a stale token's `mark_completed/mark_failed` is
  rejected (module docstring `:19`). `IdempotencyRegistry` (`:518-…`) is the process-wide
  singleton; backend selected by `SPINE_API_IDEMPOTENCY_BACKEND=memory|sql` (`:41`,
  `:542-547` — `sql` requires `DATABASE_URL`).
- **Wired into the pipeline**: `spine_api/services/pipeline_execution_service.py`
  acquires `(lock_key, fencing_token)` at submission (`:356-373`) and stashes the token in
  run meta; completion/failure paths replay it via `registry.mark_completed(..., fencing_token=fencing)`
  (`:103-117`). Key generation: `IdempotencyRegistry.generate_key(trip_id, action_name, payload)`
  (`idempotency.py:556`).
- **Checkpoints**: `src/agents/checkpoints.py` — `ExecutionCheckpoint` (`:20`) +
  singleton `CheckpointStore` (`:41-…`, save `:55`, latest `:81`) for run resumption state.

## 5. Dead-letter queue (DLQ)

`src/agents/dlq_inspector.py` — `DLQInspector` (`:39-123`): `record_poisoned_job` (`:47`),
`list_poisoned_jobs` (`:70`), `get_job` (`:77`), `replay_job` (`:81`), `purge_job` (`:104`),
payload sanitization (`:113`).
⚠️ **Storage is in-process class state** (`_POISON_STORE: Dict` at `:43`) — DLQ records do
**not** survive a restart. The *requeue* path (below) is SQL-durable; the DLQ inspection
layer is not (yet). The SQL requeue store's `fail(..., poison=True)` flag
(`spine_api/services/agent_requeue_jobs.py:281`) is the durable poison signal.

## 6. Recovery & requeue

- `src/agents/recovery_agent.py` (`RecoveryAgent`, 455 lines): monitors trips for
  stuck/anomalous states (module docstring `:4`) and dispatches through a `RequeuePort`
  (`src/agents/requeue.py`): `DisabledSpineRequeuePort` (`:47`), `_RawCallableRequeuePort`
  (`:64`), `InlineSpineRequeuePort` (`:96`), selected by `build_requeue_port` per
  `AGENT_RECOVERY_REQUEUE_MODE`.
- `sql_queue` mode (`factory:216-231`): durable `RequeueJobStore`
  (`spine_api/services/agent_requeue_jobs.py:67-…`) — `agent_requeue_jobs` table created
  via `CREATE TABLE IF NOT EXISTS` (`:84`), lease-based job claiming (`lease_pending :174`),
  `complete`/`fail(poison)` (`:278-281`), drained by a `RequeueWorker` +
  `RequeueWorkerService` bundled by the factory (`factory:219-231`).

## 7. Observability

- **Events**: `src/agents/events.py` — `AgentEventType` (`:16-23`: started/stopped/decision/
  action/failed/retry/escalated) and `AgentEvent` (`:27-33`, `correlation_id` default
  `agt_<uuid12>`); emitted by the supervisor (`runtime.py:403,417`) and execution paths.
- **HTTP surface**: `spine_api/routers/agent_runtime.py` — `GET /agents/runtime`
  (registry + supervisor health, `:59-…`), `POST /agents/runtime/run-once` (`:92-…`),
  `GET /agents/runtime/events` (`:112-…`). Runtime is configured into the app at
  `spine_api/server.py:299-310`.
- **Audit sink**: supervisor takes an `AgentAuditSink`; production adapter is
  `AuditStoreAdapter` (`spine_api/services/agent_runtime_factory.py:191-193`, adapters in
  `spine_api/services/agent_runtime_adapters.py`).
- ⚠️ Gaps carried from the audit record: OTel spans exist but have no dashboard/CI consumer
  (`Docs/exploration/OTEL_TRACE_CORRELATION_GAP_2026-08-29.md`), and the heartbeat gap in
  §3 means long executions are protected only by TTL sweeps.

## 8. Related orchestration modules (`src/orchestration/`)

`agent_lease.py` (durable leases, §3.2), `irops_healer.py` (EU261 deterministic
compensation, `:87-89`), `duty_of_care_radar.py`, `proposal_compiler.py`,
`booking_fulfillment.py`, `model_router.py`, `travel_next_action.py` (next-action
projection, consumed via `NextActionAwareTripRepo`). These are the agents' domain engines;
the runtime in `src/agents/` is the supervision layer above them.
