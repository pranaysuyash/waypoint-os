# Multi-Agent Backend Operations Runbook (2026-05-04)

## Scope
- Backend-only product-agent runtime operations.
- Canonical for current codebase state (not aspirational architecture).
- Covers recovery supervision loop, agent-event observability, and incident handling.

## Current Agent Runtime (Implemented)
1. Core run pipeline: async accepted run contract (`POST /run` + poll).
2. In-process frontier pass (checker/intelligence/negotiation best-effort enrichment).
3. Autonomous recovery supervision:
   - Agent: `src/agents/recovery_agent.py`
   - Lifecycle: started/stopped in FastAPI lifespan (`spine_api/server.py`)

## Operational Endpoints
- Run lifecycle:
  - `GET /runs`
  - `GET /runs/{run_id}`
  - `GET /runs/{run_id}/events`
- Trip-scoped agent observability:
  - `GET /trips/{trip_id}/agent-events?limit=100`
  - returns canonical `agent_event` records

## Canonical Agent Event Contract
- Event container persisted via `AuditStore.log_event("agent_event", ...)`.
- Typed envelope (`src/agents/events.py`):
  - `agent_name`
  - `event_type` (`agent_decision`, `agent_action`, `agent_failed`, etc.)
  - `trip_id`
  - `run_id` (optional)
  - `correlation_id`
  - `timestamp`
  - `payload`

## RecoveryAgent Policy Ladder
1. Detect stuck trip by stage thresholds.
2. If attempts < `RECOVERY_MAX_REQUEUE`: `re_queue`.
3. Else: `escalate` (`review_status="escalated"`).
4. On requeue failure: emit `agent_failed` (fail-closed, no destructive mutations).

## Config Knobs
- `RECOVERY_STUCK_INTAKE_H` (default 48)
- `RECOVERY_STUCK_DECISION_H` (default 72)
- `RECOVERY_STUCK_REVIEW_H` (default 24)
- `RECOVERY_STUCK_BOOKING_H` (default 336)
- `RECOVERY_MAX_REQUEUE` (default 2)
- `RECOVERY_INTERVAL_S` (default 300)

## SLO Baseline (Initial)
1. `agent_event` visibility SLO:
   - 99% of recovery actions emit a corresponding `agent_event` record.
2. Recovery action latency SLO:
   - p95 recovery pass decision-to-log < 2s (single-worker baseline).
3. Escalation correctness SLO:
   - 100% of trips at/over requeue ceiling transition to escalate action.

## Incident Playbooks

### A) Trip remains stuck after recovery attempts
1. Fetch trip status and stage:
   - `GET /trips/{trip_id}`
2. Inspect recovery events:
   - `GET /trips/{trip_id}/agent-events`
3. Confirm ladder behavior:
   - verify `agent_decision` then `agent_action`/`agent_failed`
4. If repeated `agent_failed` from requeue:
   - move to manual operator handling and root-cause queue/path issue
5. Add an audit note/event for traceability.

### B) Suspected false escalation
1. Inspect trip update timestamps/stage.
2. Inspect `agent_decision` payload (`hours_stuck`, `requeue_attempts`).
3. Verify env thresholds in runtime config.
4. If threshold mismatch confirmed:
   - correct env config
   - re-run one controlled recovery cycle.

### C) Missing agent events
1. Verify trip exists and agency scope is correct.
2. Confirm `RecoveryAgent` is running (startup logs/lifespan).
3. Check audit persistence health:
   - file lock or JSONL write errors in server logs.
4. If ingestion broken:
   - treat as observability incident; do not claim recovery health until restored.

### D) Routing health warning/critical observed
1. Pull operator-relevant alert evidence:
   - `GET /legacy_ops/audit?limit=200&event_type=routing_health_alert` (requires owner/operator auth)
2. Filter returned items for:
   - `item.type == "routing_health_alert"`
   - `item.details.trip_id == <trip_id>`
   - `item.details.status in ["warning", "critical"]`
   - optional narrow-by-trip: `GET /legacy_ops/audit?limit=200&event_type=routing_health_alert&trip_id=<trip_id>`
   - optional narrow-by-severity: `GET /legacy_ops/audit?limit=200&event_type=routing_health_alert&trip_status=<warning|critical>`
3. Confirm payload has evidence fields:
   - `checked_at`
   - `alerts`
   - `metrics_snapshot`
   - `authority` (`blocks_ci`, `source`, `thresholds`)
4. Record operator action for tracked alerts (required for auditability):
   - `POST /legacy_ops/audit/<event_id>/triage`
   - body: `{ "action": "acknowledge|close|escalate", "note": "optional" }`
   - response: `routing_health_alert_triage` event containing `target_event_id`, `action`, and `note`.
   - escalate action includes operator note before posting.
4. For `critical`:
   - route as immediate handling and check `authority.blocks_ci` for CI ownership.
5. For repeated warning without closure:
   - within the configured backend dedupe window, duplicate events for the same normalized alert state are suppressed by logger logic.
   - this prevents repeated operator noise from polling-only calls.
6. For sustained warning/critical repetition:
   - logger emits `routing_health_paging_alert` when the same trip context crosses sustained thresholds.
   - event payload contains `occurrence_index`, `sustained_window_seconds`, and `paging_cooldown_seconds`.
   - if paging was emitted within cooldown, duplicates are suppressed.
7. If repeated warning persists outside the sustained paging policy:
   - file a triage note and tag the recurring window.
8. If trip status continues to oscillate across requests:
   - avoid clearing incident state until trip review outcomes close the loop.
9. For operator visibility:
   - check `/(agency)/audit` for consolidated operator views:
     - trip audit stream,
     - routing health alerts,
     - and routing health paging alerts (trip-level sustained recurrence).

### E) Routing health paging controls
1. Env knobs:
   - `ROUTING_HEALTH_ALERT_SUSTAINED_WARNING_THRESHOLD` (default `3`)
   - `ROUTING_HEALTH_ALERT_SUSTAINED_WINDOW_SECONDS` (default `3600`)
   - `ROUTING_HEALTH_ALERT_PAGING_COOLDOWN_SECONDS` (default `3600`)
   - `ROUTING_HEALTH_ALERT_DEDUPE_WINDOW_SECONDS` (existing; warning/critical duplicate suppression)
2. Runbook queries:
   - `GET /legacy_ops/audit?event_type=routing_health_paging_alert`
   - optional narrow-by-trip: `GET /legacy_ops/audit?event_type=routing_health_paging_alert&trip_id=<trip_id>`

## Public Checker SQL Startup Preflight (Required)

If `TRIPSTORE_BACKEND=sql`, startup now assumes the configured `PUBLIC_CHECKER_AGENCY_ID` exists in `agencies.id`.

1. Confirm config value:
   - `echo $PUBLIC_CHECKER_AGENCY_ID`
2. Run SQL preflight before app start:
   - `SELECT id, slug, name FROM agencies WHERE id = '<PUBLIC_CHECKER_AGENCY_ID>';`
3. If missing, run bootstrap seed:
   - `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/bootstrap_public_checker_agency.py`
4. If `agencies` table missing, run migrations first:
   - `uv run alembic upgrade head`

Expected behavior:
- SQL mode + missing agency row -> startup fail-fast with actionable error.
- SQL mode + seeded row -> startup succeeds.

## Verification Checklist (Before Claiming Healthy)
1. `RecoveryAgent` lifecycle initialized on startup logs.
2. `GET /trips/{trip_id}/agent-events` returns records for synthetic or live recovery run.
3. Scenario tests pass:
   - `tests/test_recovery_agent.py`
   - run lifecycle + scenario suites.
4. No auth scope violations on trip agent-event endpoint.
5. Public-checker SQL preflight passes for `PUBLIC_CHECKER_AGENCY_ID`.

## Known Limits
1. Recovery runner currently depends on in-process callback wiring.
2. Multi-worker ownership semantics for recovery loop require explicit deployment constraints.
3. Frontier subsystem remains mostly heuristic and best-effort, not independently supervised workers.
