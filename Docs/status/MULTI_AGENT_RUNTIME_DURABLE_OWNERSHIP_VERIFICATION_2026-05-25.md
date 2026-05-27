# Multi-Agent Runtime Durable Ownership Verification

- Date: 2026-05-25
- Baseline references:
  - `Docs/status/MULTI_AGENT_RUNTIME_BASELINE_AUDIT_2026-05-04.md`
  - `Docs/status/MULTI_AGENT_RUNTIME_CURRENT_STATE_HANDOFF_2026-05-04.md`

## Verified Now

1. Canonical durable ownership path is wired end-to-end with no parallel stack:
   - Product-agent work ownership/idempotency/retry/poison: `spine_api/services/agent_work_coordinator.py` (`SQLWorkCoordinator`) via `AgentSupervisor` coordinator injection.
   - Recovery requeue path: `RecoveryAgent` -> `SQLSpineJobQueueRequeuePort` -> `agent_requeue_jobs` durable table -> `RequeueWorkerService` lifecycle runner.
   - Server lifecycle ownership now includes requeue worker startup/shutdown in `spine_api/server.py`.

2. Recovery requeue decisions are durable-aware:
   - Recovery no longer relies only on in-memory counters when sql_queue is enabled.
   - Durable attempts/poison state are read from SQL queue stats (`trip_stats`) through the requeue port.
   - Duplicate enqueue is treated as accepted durable ownership, not a false negative.

3. Runtime introspection now exposes requeue worker health:
   - `GET /agents/runtime` includes `requeue_worker` health when configured.

4. Verification evidence (executed 2026-05-25):
   - `tests/test_agent_runtime.py tests/test_recovery_agent.py tests/test_agent_requeue.py tests/test_agent_runtime_factory.py tests/test_agent_tripstore_adapter.py` -> **86 passed**.
   - `tests/test_agent_requeue_jobs.py tests/test_agent_work_coordinator.py` -> **50 passed**.
   - `tools/run_multi_agent_runtime_scenarios.py` -> regenerated `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`.

## Still Not Verified

1. Full multi-process/multi-host contention under real concurrent uvicorn workers against the same DB lease rows was not load-tested in this pass (unit/integration tests cover logic and SQL locking semantics, not production traffic profile).
2. End-to-end auth-validated live API runtime drill for `/agents/runtime/run-once` + SQL queue execution in a long-running deployed process was not captured as artifact evidence in this pass.
3. Recovery queue observability is currently runtime-health plus DB status counts; no dedicated operator UI for per-job timelines/triage has been added.
