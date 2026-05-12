# Trip Actions Router Extraction

**Date:** 2026-05-12  
**Status:** Complete (route extraction + contract-shadowing fix + regression verification)

## Purpose

Continue modular monolith decomposition by moving trip action endpoints out of `spine_api/server.py` while preserving route contracts and avoiding duplicate ownership.

## Scope

Moved from `spine_api/server.py` to `spine_api/routers/trip_actions.py`:

- `POST /trips/{trip_id}/review/action`
- `GET /trips/{trip_id}/activities/provenance`

Also fixed a request-model shadowing defect in `server.py`:

- Local class `ReviewActionRequest` (single `reason` field for pending-booking flows) previously shadowed the canonical contract model imported from `spine_api.contract`.
- Renamed local model to `PendingBookingReviewActionRequest`.
- Updated pending booking endpoints to use the renamed model:
  - `POST /trips/{trip_id}/pending-booking-data/accept`
  - `POST /trips/{trip_id}/pending-booking-data/reject`

This preserves the canonical `ReviewActionRequest` for `/trips/{trip_id}/review/action`.

## Files changed

- `spine_api/routers/trip_actions.py` (new)
- `spine_api/server.py`
- `Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md` (regenerated)

## Verification

Commands run:

```bash
python -m py_compile spine_api/routers/trip_actions.py spine_api/routers/legacy_ops.py spine_api/server.py
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_architecture_route_inventory.py \
  tests/test_server_startup_invariants.py \
  tests/test_override_api.py \
  tests/test_override_e2e.py \
  tests/test_call_capture_phase6_backend.py \
  tests/test_booking_collection.py -q
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Results:

- Regression suite: `86 passed`
- Inventory summary:
  - `backend_route_count=146`
  - `server_py_route_count=31`
  - `router_module_route_count=115`
  - `router_module_count=22`
  - `bff_unmatched_backend_path_count=0`
  - `potential_duplicate_backend_route_count=0`

## Architectural impact

- Further reduces `server.py` to application shell responsibilities.
- Maintains route parity and no duplicate method/path ownership.
- Removes a model-shadowing risk that could silently break `review/action` request parsing.

## Next recommended slice

Extract the remaining `trip lifecycle` shell endpoints (`reassess`, `stage`, `agent-events`, plus timeline if coupling permits) into a dedicated lifecycle router, then rerun parity snapshots and startup invariants.
