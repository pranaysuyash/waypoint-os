# Trip Lifecycle Router Extraction

**Date:** 2026-05-12  
**Status:** Complete (route extraction + shared lifecycle service + regression verification)

## Purpose

Continue reducing `spine_api/server.py` into an application shell by extracting trip lifecycle endpoints while keeping the reassessment logic shared with `PATCH /trips/{trip_id}` auto-reassess behavior.

## Scope

Moved from `spine_api/server.py` to `spine_api/routers/trip_lifecycle.py`:

- `POST /trips/{trip_id}/reassess`
- `PATCH /trips/{trip_id}/stage`

Added shared lifecycle helper module:

- `spine_api/services/trip_lifecycle_service.py`

The service owns:

- `VALID_STAGES`
- `REASSESS_EDIT_TRIGGER_FIELDS`
- reassessment request reconstruction from an existing trip
- reassessment queueing/audit emission
- stage-transition state change/audit emission

`PATCH /trips/{trip_id}` remains in `server.py` for now, but now calls the shared lifecycle service for auto-reassessment.

## Files changed

- `spine_api/services/trip_lifecycle_service.py` (new)
- `spine_api/routers/trip_lifecycle.py` (new)
- `spine_api/server.py`
- `Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md` (regenerated)

## Verification

Commands run:

```bash
python -m py_compile spine_api/services/trip_lifecycle_service.py spine_api/routers/trip_lifecycle.py spine_api/server.py
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/test_stage_transitions.py \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_architecture_route_inventory.py \
  tests/test_server_startup_invariants.py \
  tests/test_booking_collection.py -q
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Results:

- Lifecycle/parity/startup/booking regression suite: `72 passed`
- Inventory summary:
  - `backend_route_count=146`
  - `server_py_route_count=27`
  - `router_module_route_count=119`
  - `router_module_count=24`
  - `bff_unmatched_backend_path_count=0`
  - `potential_duplicate_backend_route_count=0`

## Architectural impact

- Keeps reassessment behavior single-sourced instead of copied between `server.py` and a router.
- Moves lifecycle route ownership into a domain router.
- Preserves route parity and BFF map invariants.

## Next recommended slice

The largest remaining shell-owned cluster is documents/extraction plus booking-collection internals. The next safest architectural step is to extract document/extraction routes into a dedicated router only after reviewing document storage/service boundaries and existing tests.
