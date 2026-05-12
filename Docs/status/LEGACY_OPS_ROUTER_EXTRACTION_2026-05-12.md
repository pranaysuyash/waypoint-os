# Legacy Ops Router Extraction

**Date:** 2026-05-12  
**Status:** Complete (route ownership extraction, parity preserved)

## Purpose

Reduce `spine_api/server.py` shell size without changing API contracts by extracting remaining assignment/audit/override action endpoints into a dedicated router module.

## Scope

Moved from `spine_api/server.py` to `spine_api/routers/legacy_ops.py`:

- `POST /trips/{trip_id}/assign`
- `POST /trips/{trip_id}/unassign`
- `POST /trips/{trip_id}/snooze`
- `POST /trips/{trip_id}/suitability/acknowledge`
- `GET /assignments`
- `GET /audit`
- `POST /trips/{trip_id}/override`
- `GET /trips/{trip_id}/overrides`
- `GET /overrides/{override_id}`
- `POST /trips/{trip_id}/reassign`

Out of scope in this slice:

- `POST /trips/{trip_id}/review/action` (left in `server.py` intentionally to avoid mixing request-model concerns in the same extraction)

## Files changed

- `spine_api/routers/legacy_ops.py` (new)
- `spine_api/server.py` (router import/include + handler removal)
- `Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md` (regenerated)

## Verification

Commands run:

```bash
python -m py_compile spine_api/routers/legacy_ops.py spine_api/server.py
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/test_override_api.py \
  tests/test_override_e2e.py \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_architecture_route_inventory.py \
  tests/test_server_startup_invariants.py -q
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Results:

- Focused regression suite: `36 passed`
- Route inventory summary:
  - `backend_route_count=146`
  - `server_py_route_count=33`
  - `router_module_route_count=113`
  - `router_module_count=21`
  - `bff_unmatched_backend_path_count=0`
  - `potential_duplicate_backend_route_count=0`

## Architectural impact

- Keeps topology as **BFF + modular monolith**.
- Further shrinks server shell and increases explicit route ownership.
- Avoids duplicate endpoints and preserves existing public/internal route contracts.

## Additional Contract Hardening (Same-Day)

To protect extraction parity from future drift, explicit router-behavior tests were added:

- `tests/test_legacy_ops_router_behavior.py`
  - reassign handler dependency profile + route registration parity check
  - `GET /assignments` agency-scope filtering assertion
  - `POST /trips/{trip_id}/override` stale-severity conflict (`409`) assertion

Verification refresh:

```bash
uv run pytest -q \
  tests/test_legacy_ops_router_behavior.py \
  tests/test_product_b_events.py \
  tests/test_product_b_analytics_router_behavior.py \
  tests/test_public_checker_agency_config.py \
  tests/test_public_checker_path_safety.py
# 30 passed in 7.86s
```

## Next recommended slice

Extract `POST /trips/{trip_id}/review/action` and adjacent trip-lifecycle actions into a dedicated `trip_actions` router after request-model harmonization to prevent contract ambiguity.
