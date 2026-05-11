# Architecture Topology Phase 0 Execution

**Date:** 2026-05-11  
**Status:** Complete for Phase 0 instrumentation; BFF drift, settings-router, and drafts-router follow-ups completed  
**Source exploration:** [Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](../exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)

---

## Purpose

The topology review recommended keeping Waypoint OS as a **BFF + backend modular monolith** and making route ownership explicit before more route/service decomposition. This Phase 0 execution adds a reusable architecture inventory tool so future agents can inspect current route ownership and BFF mapping drift before moving routes.

This is intentionally not a microservice extraction, not a new routing system, and not a duplicate API path. It is a read-only architecture aid.

---

## Current-State Findings

Fresh inventory from `tools/architecture_route_inventory.py`:

| Metric | Value |
| --- | ---: |
| Backend route decorators / registered routes | 146 |
| OpenAPI paths | 127 |
| Routes still owned by `spine_api/server.py` | 71 |
| Routes owned by router modules | 75 |
| Router modules with routes | 15 |
| BFF route-map entries | 71 |
| Unique BFF backend paths | 70 |
| Exact backend method/path duplicates | 0 |
| BFF backend paths without a current backend match | 0 |

The existing runtime snapshot now agrees with the static inventory: `scripts/snapshot_server_routes.py` reports `route_count=146` and `openapi_path_count=127`.

---

## BFF Route-Map Drift Found

The new inventory normalizes backend path parameters (`{id}` vs `{trip_id}`) before comparing BFF route-map entries to backend paths. It originally found three route-map entries that did not match a backend route:

| Frontend route-map key | Backend target | Finding |
| --- | --- | --- |
| `items` | `items` | No current backend route path `/items`. |
| `overrides` | `overrides` | No current backend route path `/overrides`; only `/overrides/{override_id}` and `/trips/{trip_id}/overrides` exist. |
| `team/members/{id}/workload` | `api/team/members/{id}/workload` | No current backend route path `/api/team/members/{member_id}/workload`; only `/api/team/workload` exists. |

Follow-up resolution: [Docs/status/BFF_ROUTE_MAP_DRIFT_CLEANUP_2026-05-11.md](BFF_ROUTE_MAP_DRIFT_CLEANUP_2026-05-11.md) removed these stale aliases after call-site review and added route-map regression tests. The regenerated inventory now reports `bff_unmatched_backend_path_count=0`.

---

## Files Added Or Updated

- [tools/architecture_route_inventory.py](../../tools/architecture_route_inventory.py) — static route ownership and BFF route-map inventory tool.
- [tests/test_architecture_route_inventory.py](../../tests/test_architecture_route_inventory.py) — focused regression tests for the inventory tool and drift detector.
- [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md) — generated current route inventory.
- [Docs/status/BFF_ROUTE_MAP_DRIFT_CLEANUP_2026-05-11.md](BFF_ROUTE_MAP_DRIFT_CLEANUP_2026-05-11.md) — follow-up cleanup decision record for the stale BFF aliases.
- [Docs/status/SETTINGS_ROUTER_EXTRACTION_2026-05-11.md](SETTINGS_ROUTER_EXTRACTION_2026-05-11.md) — follow-up settings route extraction and supersession record.
- [Docs/status/DRAFTS_ROUTER_EXTRACTION_2026-05-11.md](DRAFTS_ROUTER_EXTRACTION_2026-05-11.md) — follow-up draft route extraction and supersession record.
- [tools/README.md](../../tools/README.md) — usage documentation for the new tool.

---

## Verification Evidence

Commands run:

```bash
uv run python tools/architecture_route_inventory.py --format json
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/snapshot_server_routes.py
uv run python -m pytest tests/test_architecture_route_inventory.py -q
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py tests/test_architecture_route_inventory.py -q
```

Observed results:

- Original inventory summary before BFF cleanup: `backend_route_count=146`, `server_py_route_count=89`, `router_module_route_count=57`, `bff_route_map_count=74`, `bff_unmatched_backend_path_count=3`, `potential_duplicate_backend_route_count=0`.
- Regenerated inventory summary after BFF cleanup: `backend_route_count=146`, `server_py_route_count=89`, `router_module_route_count=57`, `bff_route_map_count=71`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.
- Regenerated inventory summary after settings router extraction: `backend_route_count=146`, `server_py_route_count=81`, `router_module_route_count=65`, `router_module_count=14`, `bff_route_map_count=71`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.
- Regenerated inventory summary after drafts router extraction: `backend_route_count=146`, `server_py_route_count=71`, `router_module_route_count=75`, `router_module_count=15`, `bff_route_map_count=71`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.
- Runtime snapshot: `route_count=146`, `openapi_path_count=127`.
- Focused inventory tests: `5 passed`.
- Route parity/startup/inventory regression suite: `13 passed`.

---

## Sequencing Decision

The next safest architecture step is **not** a broad `server.py` route move. The codebase has already advanced since older plans:

- `run_status` is already in `spine_api/routers/run_status.py`.
- `team` is already in `spine_api/routers/team.py`.
- Route parity fixtures now reflect `146` registered routes, not the older `129` count referenced in earlier planning docs.

Recommended next slices:

1. **Backend router decomposition candidate refresh**: use the new inventory to choose the next route family still owned by `server.py`. Likely candidates are inbox, analytics, or document/booking collection, but each needs coupling analysis before movement.
2. **Worker-boundary design note**: define the minimum same-repo worker contract for long-running pipeline/extraction work, without implementing a queue until route/persistence ownership is clearer.
3. **Persistence convergence plan**: remove the long-term dual-store risk by planning the path to PostgreSQL as the sole trip persistence layer.

---

## Long-Term Guardrail

Before any future router extraction or BFF route-map cleanup, run:

```bash
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_YYYY-MM-DD.md
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/snapshot_server_routes.py
```

Then preserve route parity with:

```bash
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_server_startup_invariants.py
```
