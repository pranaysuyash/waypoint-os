# Inbox Router Extraction

**Date:** 2026-05-11  
**Status:** Complete  
**Parent architecture review:** [Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](../exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)  
**Current inventory:** [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md)

---

## Purpose

Move the lead inbox API out of `spine_api/server.py` into a dedicated router while preserving the existing BFF/backend contract. Inbox is a good modular-monolith boundary because it is an operator-facing read model over trips and already delegates projection logic to `InboxProjectionService`.

This extraction does not create new paths, duplicate routes, or a parallel inbox system. It preserves the existing `TripStore`, `AssignmentStore`, `build_inbox_response`, and response envelope behavior.

---

## Supersession Analysis

Removal candidate: inbox handlers in `spine_api/server.py`.

Replacement: [spine_api/routers/inbox.py](../../spine_api/routers/inbox.py).

| Dimension checked | Verdict |
| --- | --- |
| Route paths | Superset: all four method/path pairs moved unchanged: `/inbox`, `/inbox/assign`, `/inbox/stats`, `/inbox/bulk`. |
| Response models | Preserved: `InboxResponse`, `AssignInboxResponse`, and `InboxStatsResponse` still come from `spine_api.contract`. |
| Projection ownership | Preserved: inbox collection still uses `build_inbox_response` from `spine_api.services.inbox_projection`. |
| Persistence dependencies | Preserved: still uses `TripStore` and `AssignmentStore`. |
| BFF compatibility | Preserved: existing explicit Next.js BFF routes and route-map entries still target the same backend paths. |
| Test ownership | Updated: the analytics hardening test now calls `spine_api.routers.inbox.get_inbox_stats` directly instead of importing the superseded `server.py` handler. |

Decision: the old `server.py` inbox handlers were fully superseded by the router implementation and were removed to avoid duplicate route registration.

---

## Files Updated

- [spine_api/routers/inbox.py](../../spine_api/routers/inbox.py) — new inbox route module.
- [spine_api/server.py](../../spine_api/server.py) — imports/includes the inbox router and removes superseded local inbox handlers.
- [tests/test_architecture_route_inventory.py](../../tests/test_architecture_route_inventory.py) — asserts route ownership now includes `inbox`.
- [tests/test_inbox_router_contract.py](../../tests/test_inbox_router_contract.py) — verifies the inbox collection and stats response shapes consumed by the frontend.
- [tests/test_overview_analytics_hardening.py](../../tests/test_overview_analytics_hardening.py) — updates the stats hardening test to target the canonical inbox router.
- [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md) — regenerated after extraction.

---

## Verification Evidence

Commands run:

```bash
uv run python -m pytest tests/test_architecture_route_inventory.py::test_route_inventory_tracks_server_py_and_router_module_ownership -q
python3 -m py_compile spine_api/routers/inbox.py spine_api/server.py
uv run python -m pytest tests/test_inbox_router_contract.py tests/test_overview_analytics_hardening.py tests/test_architecture_route_inventory.py -q
uv run python tools/architecture_route_inventory.py --format json
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Observed results:

- Red check before extraction: ownership test failed with `KeyError: 'inbox'`, proving the test detected missing router ownership.
- Syntax check: passed.
- Focused inbox/analytics/inventory tests: `9 passed`.
- Duplicate scan found `/inbox` decorators only in `spine_api/routers/inbox.py`.
- Inventory summary after extraction: `backend_route_count=146`, `server_py_route_count=67`, `router_module_route_count=79`, `router_module_count=16`, `bff_route_map_count=71`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.

---

## Follow-Up Notes

Inbox extraction preserved behavior. A future hardening pass should review assignment authorization at the store boundary: `assign_inbox_trips` currently follows the previous behavior and does not independently filter `tripIds` by `agency_id`, while `bulk_inbox_action` does. That is a separate behavior/security task and should be handled with explicit tests rather than hidden inside a route-move slice.

Next lower-risk modularity candidates:

1. `analytics` routes: high route count but more helper coupling.
2. `agent runtime` routes: small, operationally bounded, but tied to in-process agent supervisor globals.
3. document/booking collection routes: strong boundary, higher blast radius due upload/public-link behavior.
