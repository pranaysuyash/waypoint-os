# Settings Router Extraction

**Date:** 2026-05-11  
**Status:** Complete  
**Parent architecture review:** [Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](../exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)  
**Current inventory:** [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md)

---

## Purpose

Continue the architecture path toward a BFF + backend modular monolith by moving a cohesive route family out of `spine_api/server.py` into a dedicated router module. Settings is a good extraction candidate because its API surface is already grouped in the BFF route map and its handlers share a clear ownership boundary:

- agency profile and operational settings,
- agency autonomy policy,
- pipeline stage configuration,
- approval threshold configuration.

This is not a new settings system and does not create duplicate API routes. The same backend paths and handler behavior are preserved under `spine_api/routers/settings.py`.

---

## Supersession Analysis

Removal candidate: settings handlers in `spine_api/server.py`.

Replacement: [spine_api/routers/settings.py](../../spine_api/routers/settings.py).

| Dimension checked | Verdict |
| --- | --- |
| Route paths | Superset: all eight method/path pairs moved unchanged. |
| Request models | Superset: uses canonical `UpdateOperationalSettings`, `UpdateAutonomyPolicy`, `PipelineStageConfig`, and `ApprovalThresholdConfig` from `spine_api.contract`. |
| Persistence dependencies | Superset: uses the same `AgencySettingsStore` and `ConfigStore` persistence backends. |
| Safety invariant | Preserved: `STOP_NEEDS_REVIEW` still rejects any action other than `block`. |
| Response shapes | Preserved: copied field-for-field from the original handlers. |
| Auth/permissions | Preserved: route-level `settings:read` / `settings:write` dependencies remain, and the router is also included behind the existing `_auth_or_skip` wrapper. |
| Call sites | Preserved: frontend BFF mappings still target the same backend paths. |

Decision: the old `server.py` handlers were fully superseded by the router implementation and were removed to avoid duplicate route registration.

---

## Files Updated

- [spine_api/routers/settings.py](../../spine_api/routers/settings.py) — new settings route module.
- [spine_api/server.py](../../spine_api/server.py) — imports/includes the settings router and removes superseded local settings handlers.
- [tests/test_architecture_route_inventory.py](../../tests/test_architecture_route_inventory.py) — asserts route ownership now includes `settings`.
- [tests/test_settings_router_contract.py](../../tests/test_settings_router_contract.py) — verifies the moved settings endpoints still return the frontend-consumed response shapes.
- [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md) — regenerated after extraction.

---

## Verification Evidence

Commands run:

```bash
uv run python -m pytest tests/test_architecture_route_inventory.py::test_route_inventory_tracks_server_py_and_router_module_ownership -q
python3 -m py_compile spine_api/routers/settings.py spine_api/server.py
uv run python -m pytest tests/test_settings_router_contract.py -q
uv run python -m pytest tests/test_architecture_route_inventory.py -q
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q
uv run python tools/architecture_route_inventory.py --format json
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Observed results:

- Red check before extraction: ownership test failed with `KeyError: 'settings'`, proving the test detected missing router ownership.
- Syntax check: passed.
- Settings router contract tests: `3 passed`.
- Focused architecture inventory tests: `5 passed`.
- Route parity, OpenAPI path parity, and startup invariants: `9 passed`.
- Inventory summary after extraction: `backend_route_count=146`, `server_py_route_count=81`, `router_module_route_count=65`, `router_module_count=14`, `bff_route_map_count=71`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.

---

## Next Architecture Slice

The next extraction should be chosen by coupling, not by file size alone. Good candidates to inspect next:

1. `analytics` routes in `server.py`: many routes but likely more shared helper coupling.
2. `drafts` routes in `server.py`: cohesive lifecycle boundary, but needs store/service inspection.
3. document/booking collection routes: valuable bounded subsystem, higher blast radius because public routes, upload handling, and document services intersect.

Do not extract another route family until route inventory and parity tests are green at the start of that slice.
