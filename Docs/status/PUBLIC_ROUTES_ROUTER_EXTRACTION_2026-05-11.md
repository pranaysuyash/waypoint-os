# Public Routes Router Extraction

**Date:** 2026-05-11  
**Status:** Complete  
**Parent architecture review:** [Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](../exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)  
**Current inventory:** [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md)

## Purpose

Extract remaining public-facing unscoped routes from `spine_api/server.py` into bounded routers:

- `spine_api/routers/public_checker.py`:
  - `POST /api/public-checker/events`
  - `GET /api/public-checker/{trip_id}`
  - `GET /api/public-checker/{trip_id}/export`
  - `DELETE /api/public-checker/{trip_id}`
- `spine_api/routers/public_collection.py`:
  - `GET /api/public/booking-collection/{token}`
  - `POST /api/public/booking-collection/{token}/submit`
  - `POST /api/public/booking-collection/{token}/documents`

`POST /api/public-checker/run` remains in `server.py` by design for this slice (tested monkeypatch path and API contract unchanged).

## Supersession Analysis

Replacement modules own all route handlers listed above; no route contracts changed.

| Check | Verdict |
| --- | --- |
| Route coverage | Superset of prior server handlers for listed paths/methods |
| Auth behavior | Preserved (`Depends(get_current_agency)` / `Depends(get_current_user)` where applicable) |
| Rate limits | Preserved with same limiter settings and per-route keys |
| Data writes | Preserved `TripStore`/`AuditStore` usage and validation flow |
| API shape | Contracts validated against existing tests and route snapshot parity |

Decision: keep `server.py` run endpoint in place for now, but move all public-checker/package and booking-collection customer endpoints out of `server.py` to dedicated routers.

## Files Updated

- [spine_api/routers/public_checker.py](../../spine_api/routers/public_checker.py) — new public-checker router module.
- [spine_api/routers/public_collection.py](../../spine_api/routers/public_collection.py) — new booking-collection router module.
- [spine_api/server.py](../../spine_api/server.py) — wired new router imports/includes and removed superseded local handlers.
- [tests/test_product_b_events.py](../../tests/test_product_b_events.py) — compatibility path still validated via monkeypatch on `server.ProductBEventStore`.
- [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md) — regenerated after router extraction.

## Verification Evidence

Commands run:

```bash
uv run python -m pytest tests/test_architecture_route_inventory.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_product_b_events.py tests/test_public_checker_agency_config.py tests/test_booking_collection.py tests/test_call_capture_e2e.py tests/test_public_checker_path_safety.py -q
uv run python -m py_compile spine_api/routers/public_checker.py spine_api/routers/public_collection.py spine_api/server.py
uv run python tools/architecture_route_inventory.py --format json
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Observed results:

- 24 tests in initial public-checker/router sweep + 32 tests in booking/public-e2e/contract sweep passed.
- 24/24 in route parity + openapi parity + architecture ownership + product_b_events subset after re-exposing `ProductBEventStore` from `server.py` for legacy monkeypatch compatibility.
- `potential_duplicate_backend_route_count` remains 0 in generated inventory.
