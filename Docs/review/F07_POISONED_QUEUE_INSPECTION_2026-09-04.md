# F-07 Poisoned Queue Inspection — 2026-09-04

## Finding

The canonical durable recovery queue in
`spine_api/services/agent_requeue_jobs.py` already records poisoned jobs, but
operators could inspect only aggregate status counts and per-trip statistics.
The alternate `src/agents/dlq_inspector.py` is an in-memory prototype whose
`REPLAYED_SUCCESSFULLY` result does not invoke a worker, persist state, enforce
tenant scope, or emit the claimed audit event. It is therefore not promoted as
the source of truth.

## Implemented bounded slice

`RequeueJobStore.list_poisoned()` now provides a durable, deterministic,
read-only inspection projection:

- filters to `status = poisoned` only;
- supports a trip-id filter and offset pagination;
- orders by `updated_at DESC, id DESC` for repeatable results;
- validates `1 <= limit <= 100` and non-negative offsets;
- returns job ID, trip ID, reason, attempt counts, bounded error text, and
  created/updated timestamps;
- omits the stored payload entirely;
- caps `last_error` at 2,048 characters;
- remains service-level only because `agent_requeue_jobs` has no `agency_id`.

No replay, purge, mutation, or global HTTP route was added.

## Verification

- `PYTHONPATH=src .venv/bin/pytest -q tests/test_agent_requeue_jobs.py` →
  **34 passed**.
- The inspection tests prove poisoned-only filtering, payload omission,
  bounded error projection, trip filtering, pagination, and argument limits.
- Full backend verification is required after this slice; hosted/multi-worker,
  tenant-authorization, and operator/audit evidence remain open.
- Post-slice isolated backend runner (no `:8000` server detected):
  `scripts/run_backend_tests.sh` → **3,733 passed, 44 skipped, 0 failed** in
  382.49s, with 8 known Python 3.13 fork deprecation warnings. The increased
  skip count means server-dependent integration paths were not exercised; the
  earlier server-present 3,760/10 receipt remains the broader but non-hermetic
  checkpoint.

## Follow-up required before an API route or replay

1. Add an agency ownership contract to the queue (or a canonical join to
   tenant-scoped trips) before exposing inspection through authenticated HTTP.
2. Add operator authorization, audit events, pagination cursors, and hosted
   multi-replica evidence.
3. Replace the shadow inspector's replay status with `REPLAY_REQUESTED` or
   `REPLAY_QUEUED` until a durable worker execution and terminal result are
   observed.
4. Implement replay only with an injected executor, idempotency key,
   authorization identity, audit event, compensating action, and rollback/
   unknown-outcome semantics.
5. Implement purge only with legal-retention/hold checks and durable audit
   evidence.

**Disposition:** F-07 inspection visibility **ACCEPT+MODIFY — local durable
service complete**; tenant-facing route, replay, purge, authorization, and
hosted evidence **OPEN**.
