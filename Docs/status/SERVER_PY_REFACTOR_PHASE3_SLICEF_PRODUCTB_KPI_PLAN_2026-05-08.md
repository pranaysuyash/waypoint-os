# Server.py Refactor Phase 3 — Slice F Product-B KPI Plan (Plan Only)

Date: 2026-05-08
Status: Plan-only (implementation not started)

## Scope Guardrails (Hard)
- Plan only. No implementation.
- No route movement yet.
- No code edits outside this plan doc.
- No snapshot updates.
- No mutating git commands.
- `/run` and `/runs` are out of scope.
- No public checker movement, no agent runtime movement, no settings movement.
- No startup/lifespan/app-factory/middleware changes.
- No cleanup or hardening mixed with extraction.

## 1) Exact route inventory
Target route to move (only this route):
1. GET `/analytics/product-b/kpis` (current location: `spine_api/server.py` line 1042; handler starts line 1043)

## 2) Current behavior contract (must preserve exactly)
- Path: `/analytics/product-b/kpis`
- Function name: `get_product_b_kpis`
- Query params:
  - `window_days: int = Query(default=30, ge=1, le=365)`
  - `qualified_only: bool = Query(default=False)`
- Dependency:
  - `agency: Agency = Depends(get_current_agency)`
- Handler behavior:
  - `_ = agency`
  - `return ProductBEventStore.compute_kpis(window_days=window_days, qualified_only=qualified_only)`
- No `response_model`
- No permission dependency
- No rate-limit decorator
- No persistence writes

## 3) Dependency/auth/rate-limit profile
- Auth/dependency: `Depends(get_current_agency)` only.
- Permissions: none (`require_permission(...)` not used).
- Rate limiting: none (`@limiter.limit(...)` absent).
- Side effects: none expected in handler; read-only compute call.

## 4) Required imports in planned router module
Planned file: `spine_api/routers/product_b_analytics.py`
Required imports:
- `APIRouter`, `Depends`, `Query`
- `get_current_agency`
- `Agency`
- `ProductBEventStore`

Planned router shape:
- `router = APIRouter()`
- no prefix
- no tags
- no router-level dependencies

## 5) server.py wiring plan after approval (implementation phase only)
1. Add normal import path entry for product-b analytics router.
2. Add fallback importlib path entry for product-b analytics router.
3. Add `app.include_router(product_b_analytics_router.router)` in router include section.
4. Remove only the in-file `get_product_b_kpis` handler from `server.py`.
5. Do not touch any other route/group.

## 6) Tests to add (implementation phase only)
New test file:
- `tests/test_product_b_analytics_router_behavior.py`

Required test coverage:
1. Verifies `ProductBEventStore.compute_kpis` is called with `window_days` and `qualified_only`.
2. Verifies `get_current_agency` dependency remains present on the route.
3. Verifies no permission dependency is added.

## 7) Verification matrix (post-implementation)
Run all:
- `tests/test_server_route_parity.py`
- `tests/test_server_openapi_path_parity.py`
- `tests/test_server_startup_invariants.py`
- `tests/test_product_b_events.py`
- `tests/test_product_b_analytics_router_behavior.py`

## 8) Snapshot expectations
- Route/OpenAPI counts remain unchanged from current fixture baseline at implementation time.
- No new/removed paths expected for a pure route move.

## 9) Forbidden import check (post-implementation)
Command:
- `grep -n "from spine_api.server\|import server" spine_api/routers/product_b_analytics.py`
Expected:
- no matches

## 10) Non-goals
- no public checker movement
- no agent runtime movement
- no settings movement
- no `/run` or `/runs` movement
- no startup/lifespan/app-factory/middleware changes
- no cleanup or hardening

## Stop Rule
Stop after writing this plan. Await approval before implementation.
