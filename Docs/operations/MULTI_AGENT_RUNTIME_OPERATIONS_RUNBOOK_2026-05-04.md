# Multi-Agent Runtime Operations Runbook (Backend) — 2026-05-04

## Scope
Backend product-agent runtime operations for `travel_agency_agent`.

## Canonical Runtime Surfaces
- Registry + supervisor implementation: `src/agents/runtime.py`
- Recovery loop: `src/agents/recovery_agent.py`
- Event envelope: `src/agents/events.py`
- Runtime APIs: `spine_api/server.py`
  - `GET /agents/runtime`
  - `POST /agents/runtime/run-once`
  - `GET /agents/runtime/events`
  - `GET /trips/{trip_id}/agent-events`

## Registered Product Agents (Current)
- `front_door_agent`
- `sales_activation_agent`
- `document_readiness_agent`
- `destination_intelligence_agent`
- `weather_pivot_agent`
- `constraint_feasibility_agent`
- `proposal_readiness_agent`
- `booking_readiness_agent`
- `flight_status_agent`
- `ticket_price_watch_agent`
- `safety_alert_agent`
- `gds_schema_bridge_agent`
- `pnr_shadow_agent`
- `supplier_intelligence_agent`
- `follow_up_agent`
- `quality_escalation_agent`
- separate lifecycle loop: `recovery_agent`

## Operator Checks
1. Runtime health:
   - `GET /agents/runtime`
   - Confirm `supervisor.running == true`
   - Confirm expected agent names in `supervisor.registered_agents`
2. Event stream:
   - `GET /agents/runtime/events?limit=100`
   - Filter by `agent_name` and `correlation_id` as needed
3. Trip-specific trace:
   - `GET /trips/{trip_id}/agent-events`
4. Trip packet surface:
   - Open `/trips/{trip_id}/packet`
   - Confirm the Agent Operations panel shows any attached document, destination, weather, feasibility, proposal, booking, flight, price, safety, supplier, GDS, and PNR packets.
   - Use `Refresh Agent Checks` to trigger the canonical `POST /agents/runtime/run-once` backend pass through the existing `/api/[...path]` proxy route map.

## Event Semantics
- `agent_started` / `agent_stopped`: supervisor lifecycle
- `agent_decision`: execution decision or skip reason
- `agent_action`: successful action completion
- `agent_retry`: transient failure/retry or ownership conflict skip
- `agent_escalated`: terminal failure / poisoned work item
- `agent_failed`: scan/runtime failure in an agent loop

## Manual Runtime Drill
- Trigger one pass for all agents:
  - `POST /agents/runtime/run-once`
- Trigger one pass for a specific agent:
  - `POST /agents/runtime/run-once?agent_name=follow_up_agent`
- Expected response contains:
  - `results[]`
  - `total`
  - updated supervisor health snapshot

## Failure Drills (Validated)
1. Transient update failure:
   - expected: first pass `retry_pending`, second pass success
2. Retry budget exhaustion:
   - expected: status transitions to `poisoned`, event `agent_escalated`
3. Ownership collision/idempotent re-entry:
   - expected: secondary acquire denied, completed work not re-executed

## Work Coordination
- Local/drill fallback: `InMemoryWorkCoordinator` in `src/agents/runtime.py`.
- Production SQL path: `SQLWorkCoordinator` in `spine_api/services/agent_work_coordinator.py`.
- Schema:
  - SQLAlchemy model: `spine_api/models/agent_work.py`
  - Alembic migration: `alembic/versions/add_agent_work_leases.py`
- Enable SQL coordination with either:
  - `TRIPSTORE_BACKEND=sql` (default production/test trip store setting), or
  - `AGENT_WORK_COORDINATOR=sql`
- Apply the migration before enabling multi-worker runtime. The SQL coordinator stores durable terminal idempotency states (`completed`, `poisoned`) and row-locked leases for `running` work.
- Local verification on 2026-05-04 applied `uv run alembic upgrade head`, which created `agent_work_leases` and also applied the already-pending RLS migration in the local database.

## Live Tool Configuration
- Weather:
  - Default: deterministic `MockWeatherTool`
  - Live keyless option: `TRAVEL_AGENT_ENABLE_LIVE_TOOLS=1` uses Open-Meteo
- Flight status:
  - Default: deterministic `MockFlightStatusTool`
  - Provider option: set `TRAVEL_AGENT_FLIGHT_STATUS_URL_TEMPLATE`
  - Optional provider label: `TRAVEL_AGENT_FLIGHT_STATUS_PROVIDER`
  - Optional headers: `TRAVEL_AGENT_FLIGHT_STATUS_HEADER_<HEADER_NAME>`
- Quote / price watch:
  - Default: deterministic `MockPriceWatchTool`
  - Provider option: set `TRAVEL_AGENT_PRICE_WATCH_URL_TEMPLATE`
  - Optional provider label: `TRAVEL_AGENT_PRICE_WATCH_PROVIDER`
  - Optional headers: `TRAVEL_AGENT_PRICE_WATCH_HEADER_<HEADER_NAME>`
- Safety alerts:
  - Default: deterministic `MockSafetyAlertTool`
  - Provider option: set `TRAVEL_AGENT_SAFETY_ALERT_URL_TEMPLATE`
  - Optional provider label: `TRAVEL_AGENT_SAFETY_ALERT_PROVIDER`
  - Optional headers: `TRAVEL_AGENT_SAFETY_ALERT_HEADER_<HEADER_NAME>`
  - State Department option: `TRAVEL_AGENT_SAFETY_PROVIDER=state_dept`

URL templates may reference fields such as `{carrier}`, `{flight_number}`, `{origin}`, `{destination}`, `{date}`, and `{quote_id}`. Query-string secrets named like key/token/secret/password/auth are redacted from tool evidence references.

## SLO Starter Set
1. Runtime availability: `/agents/runtime` success >= 99.5%
2. Event write reliability: `agent_action`/`agent_retry`/`agent_escalated` events present for agent outcomes >= 99%
3. Decision-to-event latency: p95 < 2s in single-worker baseline
4. Poison rate: track proportion of `agent_escalated` over total executed actions

## Guardrails
- Do not create duplicate API routes for runtime operations.
- Keep runtime on canonical pipeline; no parallel orchestration path.
- Keep changes additive and evidence-tested.
- Keep trip access agency-scoped on all event surfaces.

## Known Operational Limits
1. SQL work coordination is implemented but requires the Alembic migration before production use.
2. Recovery re-queue path depends on runner wiring availability.
3. Tool-backed destination intelligence, weather pivots, and feasibility assessments use freshness-aware adapters. Weather has a keyless live path; flight, price, and external safety feeds require configured provider endpoints or the State Department advisory adapter. Authoritative source verification remains operator responsibility.
4. FastAPI TestClient verification emitted async TripStore/list supervisor warnings; track a separate hardening task so runtime scans never leak unawaited SQL coroutines.
   - Update: `_TripStoreAdapter` now resolves accidental coroutine results before handing data to synchronous agent scans. Regression coverage: `tests/test_agent_tripstore_adapter.py`.
   - Update: the synchronous SQL facade now uses a serialized background bridge plus loop-local TripStore SQL engines, avoiding asyncpg/SQLAlchemy lock reuse across runtime scans and FastAPI lifespan work.
5. File-backed audit events can leave ownerless lock directories after interrupted processes.
   - Update: `file_lock()` now removes ownerless stale lock directories after the configured timeout window. Regression coverage: `tests/test_persistence_runtime_boundaries.py`.
6. The packet page exposes agent-operation metadata read-only. Operator task actions, acknowledgments, and provider refresh controls still need dedicated workflow endpoints before launch-grade autonomous operations.

## Escalation Path
- If recurring `agent_escalated` spikes:
  1. Query `/agents/runtime/events?agent_name=<name>&limit=200`
  2. Pivot on `reason`, `status`, `idempotency_key`
  3. Trigger targeted `run-once` after remediation
  4. If unresolved, switch affected trips to manual handling and open backend hardening task with evidence bundle
