# Analytics Router Extraction

**Date:** 2026-05-11  
**Status:** Complete and verified  
**Scope:** Move non-product-B `/analytics/*` routes from `spine_api/server.py` into a canonical analytics router.

## Purpose

Continue the architecture topology plan by reducing `spine_api/server.py` toward an application shell while keeping Waypoint OS a modular monolith. This is a route ownership extraction only: no new API paths, no parallel analytics system, and no product behavior rewrite.

Product-B analytics remains owned by `spine_api/routers/product_b_analytics.py`.

## Routes Moved

The new [spine_api/routers/analytics.py](../../spine_api/routers/analytics.py) owns 14 routes:

- `GET /analytics/summary`
- `GET /analytics/pipeline`
- `GET /analytics/team`
- `GET /analytics/bottlenecks`
- `GET /analytics/revenue`
- `GET /analytics/agent/{agent_id}/drill-down`
- `GET /analytics/alerts`
- `POST /analytics/alerts/{alert_id}/dismiss`
- `GET /analytics/reviews`
- `GET /analytics/reviews/{review_id}`
- `POST /analytics/reviews/bulk-action`
- `GET /analytics/escalations`
- `GET /analytics/funnel`
- `POST /analytics/export`

## Supersession Record

Removal: analytics route handlers in `spine_api/server.py` — superseded by `spine_api/routers/analytics.py`.

Comparison:

- Public method/path contracts preserved exactly.
- Handler names preserved for parity and traceability.
- Response models preserved for summary, pipeline, team, bottlenecks, revenue, alerts, and export endpoints.
- Existing analytics services preserved: `src.analytics.metrics` and `src.analytics.review`.
- Product-B analytics intentionally left in `product_b_analytics.py`.

Call sites:

- Backend app wiring now includes `analytics_router.router`.
- Existing BFF route-map targets still resolve to the same backend paths.
- `tests/test_overview_analytics_hardening.py` now patches/calls the router module directly.

Post-removal verification:

- `python3 -m py_compile spine_api/routers/analytics.py spine_api/server.py`
- `uv run python -m pytest tests/test_analytics_router_contract.py tests/test_overview_analytics_hardening.py tests/test_architecture_route_inventory.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q`
- Result: `21 passed`.
- Broader router extraction regression suite: `uv run python -m pytest tests/test_analytics_router_contract.py tests/test_agent_events_api.py tests/test_inbox_router_contract.py tests/test_drafts_router_contract.py tests/test_settings_router_contract.py tests/test_overview_analytics_hardening.py tests/test_architecture_route_inventory.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q`
- Result: `32 passed`.

## Inventory Impact

Regenerated [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md):

- `backend_route_count=146`
- `server_py_route_count=50`
- `router_module_route_count=96`
- `router_module_count=18`
- `bff_unmatched_backend_path_count=0`
- `potential_duplicate_backend_route_count=0`

## Follow-Up Notes

- `POST /analytics/reviews/bulk-action` and `POST /analytics/export` were moved as-is. They should receive a separate authorization and agency-scoping review before launch, because changing those contracts inside a mechanical extraction would hide behavior changes.
- Analytics remains a read-model/projection concern inside the modular monolith. The long-term target is durable events and SQL-backed projections before considering any separate analytics service.
