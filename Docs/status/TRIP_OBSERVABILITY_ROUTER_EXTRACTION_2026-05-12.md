# Trip Observability Router Extraction

**Date:** 2026-05-12  
**Status:** Complete (route extraction + parity verification)

## Purpose

Continue shrinking `spine_api/server.py` into an application shell by extracting observability-focused trip endpoints into a dedicated router while preserving existing route contracts.

## Scope

Moved from `spine_api/server.py` to `spine_api/routers/trip_observability.py`:

- `GET /trips/{trip_id}/agent-events`
- `GET /api/trips/{trip_id}/timeline`

## Files changed

- `spine_api/routers/trip_observability.py` (new)
- `spine_api/server.py`
- `Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md` (regenerated)

## Verification

Commands run:

```bash
python -m py_compile spine_api/routers/trip_observability.py spine_api/routers/trip_actions.py spine_api/routers/legacy_ops.py spine_api/server.py
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/test_agent_events_api.py -k "get_trip_agent_events" -q
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/test_timeline_rest_endpoint.py \
  tests/test_timeline_e2e_lifecycle.py \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_architecture_route_inventory.py \
  tests/test_server_startup_invariants.py -q
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Results:

- `agent-events` endpoint-focused tests: `2 passed`
- Timeline/parity/inventory/startup suite: `28 passed`
- Inventory summary:
  - `server_py_route_count=29`
  - `router_module_route_count=117`
  - `router_module_count=23`
  - `bff_unmatched_backend_path_count=0`
  - `potential_duplicate_backend_route_count=0`

## Note on unrelated test noise

A broader run that included all tests in `tests/test_agent_events_api.py` showed unrelated failures in runtime monkeypatch tests (`/agents/runtime`), not in `GET /trips/{trip_id}/agent-events`. Endpoint-focused selection was used to verify this extraction slice directly.

## Architectural impact

- Keeps topology as **BFF + modular monolith**.
- Improves route ownership clarity for observability surfaces.
- Preserves API path behavior and route parity invariants.

## Next recommended slice

Extract remaining trip-lifecycle shell handlers (`POST /trips/{trip_id}/reassess`, `PATCH /trips/{trip_id}/stage`) with helper-function decomposition so lifecycle policy logic is reusable and server-shell-free.
