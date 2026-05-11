# Drafts Router Extraction

**Date:** 2026-05-11  
**Status:** Complete  
**Parent architecture review:** [Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](../exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)  
**Current inventory:** [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md)

---

## Purpose

Continue reducing `spine_api/server.py` into an application shell by moving the cohesive draft lifecycle API into a dedicated router. Drafts are a strong modular-monolith boundary because they own an operational lifecycle distinct from trips:

- create and list draft work,
- read/update draft payloads,
- discard and restore drafts,
- inspect draft audit events and linked runs,
- promote a draft to a trip.

This extraction does not create new paths, duplicate routes, or a parallel draft store. It preserves the existing `DraftStore`, `AuditStore`, and `RunLedger` behavior.

---

## Supersession Analysis

Removal candidate: draft handlers and draft request models in `spine_api/server.py`.

Replacement: [spine_api/routers/drafts.py](../../spine_api/routers/drafts.py).

| Dimension checked | Verdict |
| --- | --- |
| Route paths | Superset: all ten method/path pairs moved unchanged. |
| Request models | Superset: `CreateDraftRequest`, `UpdateDraftRequest`, and `PromoteDraftRequest` moved with the same fields/defaults. |
| Persistence dependencies | Preserved: still uses `DraftStore` for draft lifecycle operations. |
| Audit behavior | Preserved: still logs create/save/autosave/discard/restore/promote events through `AuditStore`. |
| Run lookup behavior | Preserved: linked runs still read from `RunLedger` through draft run snapshots. |
| Response shapes | Preserved: list, detail, mutation, events, runs, and promotion responses are copied field-for-field. |
| Auth/tenant checks | Preserved: handlers still depend on current agency/user and check draft agency ownership before returning or mutating data. |
| BFF compatibility | Preserved: existing BFF mappings still target the same backend paths. |

Decision: the old `server.py` draft handlers were fully superseded by the router implementation and were removed to avoid duplicate route registration.

---

## Files Updated

- [spine_api/routers/drafts.py](../../spine_api/routers/drafts.py) — new draft lifecycle route module.
- [spine_api/server.py](../../spine_api/server.py) — imports/includes the draft router and removes superseded local draft handlers/models.
- [tests/test_architecture_route_inventory.py](../../tests/test_architecture_route_inventory.py) — asserts route ownership now includes `drafts`.
- [tests/test_drafts_router_contract.py](../../tests/test_drafts_router_contract.py) — verifies the draft list endpoint still returns the frontend-consumed summary shape.
- [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md) — regenerated after extraction.

---

## Verification Evidence

Commands run:

```bash
uv run python -m pytest tests/test_architecture_route_inventory.py::test_route_inventory_tracks_server_py_and_router_module_ownership -q
python3 -m py_compile spine_api/routers/drafts.py spine_api/routers/settings.py spine_api/server.py
uv run python -m pytest tests/test_drafts_router_contract.py tests/test_settings_router_contract.py tests/test_architecture_route_inventory.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q
uv run python tools/architecture_route_inventory.py --format json
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Observed results:

- Red check before extraction: ownership test failed with `KeyError: 'drafts'`, proving the test detected missing router ownership.
- Syntax check: passed.
- Draft/settings/router/parity/startup targeted suite: `18 passed`.
- Duplicate scan found `/api/drafts` decorators only in `spine_api/routers/drafts.py`.
- Inventory summary after extraction: `backend_route_count=146`, `server_py_route_count=71`, `router_module_route_count=75`, `router_module_count=15`, `bff_route_map_count=71`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.

---

## Next Architecture Slice

The remaining `server.py` ownership is now mostly larger product surfaces. The next candidates need more coupling analysis than settings/drafts:

1. `analytics` routes: high count and BFF-facing, but likely tied to trip projection helpers and response shaping.
2. `inbox` routes: operationally central and likely service-ready because `InboxProjectionService` already exists.
3. document/booking collection routes: strong domain boundary, but higher blast radius because public links, uploads, extraction, and document storage intersect.

Recommended next step: inspect `inbox` first because it already has a projection service and should be lower risk than document/public collection extraction.
