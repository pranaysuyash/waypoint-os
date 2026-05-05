# Multi-Agent Runtime Current State Handoff — 2026-05-04

## Purpose

This handoff records the current state of the travel-agency multi-agent runtime after the expanded implementation pass. It is intended for any follow-on agent so they can continue without re-auditing from scratch or mistaking the work for an MVP.

## Working Goal

The original thread direction started as a request to inspect more repo, docs, and online context and plan the travel-agency agent accordingly. The goal then changed after user feedback:

- Do not stop at audit/planning.
- Do not frame the work as an MVP unless explicitly requested.
- Build the travel-agency agent system as a full-fledged, extensible, production-grade foundation.
- Include stage-specific agents, live tool callers, document/visa readiness, weather/flight/price/safety/provider checks, durable Postgres coordination, operator UI visibility, and verified behavior against the real codebase.
- Leave `/Users/pranay/Projects/agent-start` alone; it is a helper and not important for this app.

## State Before This Pass

The runtime was too narrow for the product context. It primarily had follow-up and quality/escalation style behavior and did not yet cover the wider travel agency operating model described in repo docs:

- live destination intelligence;
- weather pivots;
- document/visa/passport readiness;
- feasibility and proposal/booking readiness gates;
- flight delay/status monitoring;
- quote/ticket price drift checks;
- safety alerts;
- GDS/provider normalization;
- PNR mismatch checks;
- supplier intelligence;
- durable multi-worker work coordination;
- operator-facing visibility for the new packets.

The user explicitly challenged the audit-only state and asked why the goal would be considered achieved if only an audit had been done.

## Current Implementation State

### Backend Runtime

`src/agents/runtime.py` now has an expanded product-agent registry with these agents:

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

The recovery loop remains separate as `recovery_agent`.

### Tool Contract And Live Tools

Added/expanded:

- `src/agents/tool_contracts.py`
- `src/agents/live_tools.py`

The shared tool result contract includes source, fetched timestamp, expiry, confidence, raw/reference metadata, and freshness checks. Agents consume normalized `ToolResult` objects instead of raw provider payloads.

Implemented adapters:

- deterministic mock weather;
- keyless Open-Meteo weather when `TRAVEL_AGENT_ENABLE_LIVE_TOOLS=1`;
- deterministic mock flight status;
- deterministic mock quote/price watch;
- deterministic mock safety alerts;
- configurable HTTP JSON flight-status adapter;
- configurable HTTP JSON price-watch adapter;
- configurable HTTP JSON safety-alert adapter;
- U.S. State Department travel advisory adapter gated by `TRAVEL_AGENT_SAFETY_PROVIDER=state_dept`.

Provider URL templates support fields such as `{carrier}`, `{flight_number}`, `{origin}`, `{destination}`, `{date}`, and `{quote_id}`. Query-string secret-looking keys are redacted in evidence references.

### Durable Work Coordination

Added durable SQL work coordination:

- `spine_api/models/agent_work.py`
- `spine_api/services/agent_work_coordinator.py`
- `alembic/versions/add_agent_work_leases.py`

`spine_api/server.py` wires `SQLWorkCoordinator` when `TRIPSTORE_BACKEND=sql` or `AGENT_WORK_COORDINATOR=sql`.

Local DB migration was applied:

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run alembic upgrade head
```

This created `agent_work_leases` and also applied the already-pending RLS migration in the local database.

### Postgres / Async Boundary Hardening

Postgres is installed and active. Earlier failures were not because Postgres was skipped; they were due to sandbox restrictions and then missing `agent_work_leases`.

Additional hardening was added in `spine_api/persistence.py`:

- synchronous TripStore SQL facade no longer creates a fresh event loop per call;
- sync SQL calls go through a serialized background bridge;
- TripStore SQL engines/sessionmakers are loop-local so FastAPI lifespan work and runtime bridge work do not share asyncpg loop-bound state;
- stale ownerless audit lock directories are reclaimed by `file_lock()`.

This addressed the prior asyncpg/SQLAlchemy error:

```text
RuntimeError: <asyncio.locks.Lock ...> is bound to a different event loop
```

### Frontend / Operator UI

The frontend now preserves and renders product-agent operation packets:

- `frontend/src/lib/api-client.ts` adds `AgentOperationsMetadata`.
- `frontend/src/lib/bff-trip-adapters.ts` maps backend runtime packet fields into `trip.agentOperations`.
- `frontend/src/components/workspace/panels/PacketPanel.tsx` shows an Agent Operations panel.
- `frontend/src/lib/route-map.ts` maps canonical runtime/event backend routes through the existing catch-all proxy.

The packet page now exposes:

- document readiness;
- destination intelligence;
- weather pivot;
- constraint feasibility;
- proposal readiness;
- booking readiness;
- flight status;
- price watch;
- safety alerts;
- supplier intelligence;
- GDS/PNR status.

It also includes `Refresh Agent Checks`, which calls the canonical backend runtime pass through:

```text
POST /api/agents/runtime/run-once
```

No duplicate Next API route was added for this.

### Restored Compatibility

`frontend/src/lib/bff-trip-adapters.ts` had removed these exports in the dirty worktree:

- `transformSpineTripToInboxTrip`
- `transformSpineTripsResponseToInboxTrips`

They were restored because current tests and compatibility still depend on them.

## Verification Evidence

Focused backend/runtime verification:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s \
  tests/test_persistence_runtime_boundaries.py \
  tests/test_live_tools.py \
  tests/test_agent_runtime.py \
  tests/test_recovery_agent.py \
  tests/test_agent_tripstore_adapter.py -q
```

Result:

```text
41 passed
```

Focused frontend verification:

```bash
npm test -- src/lib/__tests__/bff-trip-adapters.test.ts src/lib/__tests__/route-map.test.ts --run
```

Result:

```text
20 passed
```

Frontend production build:

```bash
npm run build
```

Result:

```text
success
```

Scenario runner:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/run_multi_agent_runtime_scenarios.py
```

Result:

```text
Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md
```

Temporary backend verification with Postgres enabled:

```bash
cd /Users/pranay/Projects/travel_agency_agent && \
UV_CACHE_DIR=/private/tmp/uv-cache uv run uvicorn spine_api.server:app --port 8010
```

Observed:

- startup completed;
- `GET /health` returned `status: ok`;
- `GET /agents/runtime` returned `{"detail":"Not authenticated"}`, confirming route reachability and auth protection;
- the earlier asyncpg cross-loop crash did not recur after the serialized bridge / loop-local engine fix.

## Known Issues And Warnings

### Dirty Worktree

The worktree is very dirty and includes many unrelated modified and untracked files. Do not assume every changed file belongs to this pass. Relevant files from this pass include:

- `src/agents/runtime.py`
- `src/agents/tool_contracts.py`
- `src/agents/live_tools.py`
- `tests/test_agent_runtime.py`
- `tests/test_live_tools.py`
- `tests/test_agent_tripstore_adapter.py`
- `tests/test_persistence_runtime_boundaries.py`
- `tools/run_multi_agent_runtime_scenarios.py`
- `spine_api/server.py`
- `spine_api/persistence.py`
- `spine_api/models/agent_work.py`
- `spine_api/services/agent_work_coordinator.py`
- `alembic/versions/add_agent_work_leases.py`
- `frontend/src/lib/api-client.ts`
- `frontend/src/lib/bff-trip-adapters.ts`
- `frontend/src/lib/route-map.ts`
- `frontend/src/lib/__tests__/bff-trip-adapters.test.ts`
- `frontend/src/lib/__tests__/route-map.test.ts`
- `frontend/src/components/workspace/panels/PacketPanel.tsx`
- docs under `Docs/status/` and `Docs/operations/` for multi-agent runtime evidence/runbook/status.

Before committing, isolate the diff carefully and do not include unrelated auth/RLS/inbox/overview/workbench changes unless explicitly intended.

### Sandbox DB Test Limitation

Sandboxed TestClient runs still cannot open the local Postgres socket:

```text
PermissionError: [Errno 1] Operation not permitted
```

This is a sandbox permission issue. Direct local server verification with elevated local access succeeded.

### Decryption Noise

Backend startup logs repeatedly print:

```text
Decryption failed:
```

This appears to come from existing encrypted rows that cannot be decrypted with the current local key. It is separate from Postgres availability and separate from the runtime work coordination implementation. It should be handled as local data/key hygiene.

### LLM Health

`/health` reports the LLM component as unavailable. This is separate from Postgres and the agent runtime plumbing. The user mentioned an OpenAI key in `frontend/.env.local`; do not print or copy secret values.

## Pending Work

### Production Provider Wiring

Choose and configure production providers for:

- flight status;
- fare/quote price watch;
- safety/security alerts;
- supplier feeds;
- GDS/NDC/PNR integrations.

Use the configured HTTP adapters or add provider-specific adapters that still return `ToolResult`.

### Authenticated E2E Runtime UI QA

Run browser QA as an authenticated user:

1. Open frontend on `:3000`.
2. Navigate to a trip packet page.
3. Confirm Agent Operations renders real backend packet fields.
4. Click `Refresh Agent Checks`.
5. Confirm the BFF proxy calls `POST /api/agents/runtime/run-once`.
6. Confirm the packet page refreshes and agent event surfaces remain auth-protected.

### Operator Action Workflows

The UI currently surfaces packet status and refresh. It does not yet implement dedicated operator workflows for:

- acknowledging safety/document/booking blockers;
- creating internal tasks from agent packets;
- refreshing one specific agent/tool only;
- approving quote revalidation;
- marking document checks verified;
- triggering human booking handoff.

These should use canonical backend routes, not duplicate route files.

### Data / Key Hygiene

Investigate existing encrypted trip rows producing `Decryption failed` logs. Do not delete or reset data. Preserve `TRIPSTORE_BACKEND=sql`.

### Full DB-Backed Test Run

Run DB-backed API tests with local Postgres access outside the sandbox or with an approved pytest escalation:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s \
  tests/test_agent_events_api.py \
  tests/test_agent_tripstore_adapter.py -q
```

Sandboxed execution is expected to fail on local Postgres socket permissions.

### Worktree Cleanup

Before any commit:

- review `git status --short --ignored=matching`;
- separate unrelated user/other-agent work from this pass;
- avoid reverting unknown changes;
- do not commit or push without explicit approval.

## Current Verdict

The project is no longer in audit-only state. The multi-agent runtime has a broad, extensible foundation with backend agents, live-tool contracts/adapters, durable Postgres coordination, operator packet visibility, and focused verification.

It is not launch-complete yet. The remaining work is production provider wiring, authenticated browser QA, operator action workflows, data/key hygiene, and careful worktree segmentation.
