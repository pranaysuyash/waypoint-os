# BFF Route-Map Drift Cleanup

**Date:** 2026-05-11  
**Status:** Complete  
**Parent architecture review:** [Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](../exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)  
**Inventory baseline:** [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md)

---

## Purpose

Phase 0 architecture instrumentation found that the Next.js BFF catch-all route registry contained backend mappings that did not correspond to any current FastAPI route. This cleanup removes those stale aliases instead of adding new backend routes, because there was no current frontend call-site evidence that those aliases are product requirements.

The architectural principle is deny-by-default: the BFF route map should expose only backend-backed routes or explicitly intentional aliases. It should not preserve stale paths as implicit future contracts.

---

## Status Check Before Cleanup

Instruction and context sources were refreshed before editing:

- `/Users/pranay/AGENTS.md`
- `/Users/pranay/Projects/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/CLAUDE.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`

Working tree status was checked with read-only git commands. Parallel-agent changes existed in unrelated frontend pages, docs, runtime files, and tests; this cleanup only touched the BFF route registry, its focused test, the architecture inventory test, and architecture status documents.

---

## Decisions

| Route-map key removed | Backend target removed | Decision | Evidence |
| --- | --- | --- | --- |
| `items` | `items` | Remove stale alias. | No current backend route path `/items`; no frontend runtime call site found for `/api/items`. |
| `overrides` | `overrides` | Remove stale collection alias. | Current backend exposes `/trips/{trip_id}/overrides` for collection reads and `/overrides/{override_id}` for item reads, not `/overrides`. |
| `team/members/{id}/workload` | `api/team/members/{id}/workload` | Remove stale member workload alias. | Current backend exposes aggregate `/api/team/workload`; no backend member-specific workload route exists. |

Canonical mappings retained and tested:

- `trips/{id}/overrides` -> `trips/{id}/overrides`
- `overrides/{id}` -> `overrides/{id}`
- `team/workload` -> `api/team/workload`
- `team/members/{id}` -> `api/team/members/{id}`

---

## Files Updated

- [frontend/src/lib/route-map.ts](../../frontend/src/lib/route-map.ts) — removed the three stale BFF catch-all mappings.
- [frontend/src/lib/__tests__/route-map.test.ts](../../frontend/src/lib/__tests__/route-map.test.ts) — added regression coverage that stale aliases resolve to `null` and canonical related routes still resolve.
- [tests/test_architecture_route_inventory.py](../../tests/test_architecture_route_inventory.py) — updated the inventory invariant to require zero BFF backend paths without a runtime backend route.
- [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md) — regenerated after cleanup.
- [Docs/status/ARCHITECTURE_TOPOLOGY_PHASE0_EXECUTION_2026-05-11.md](ARCHITECTURE_TOPOLOGY_PHASE0_EXECUTION_2026-05-11.md) — annotated the original Phase 0 finding with the follow-up resolution.

---

## Verification Evidence

Commands run:

```bash
uv run python tools/architecture_route_inventory.py --format json
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
uv run python -m pytest tests/test_architecture_route_inventory.py -q
cd frontend && npm test -- --run src/lib/__tests__/route-map.test.ts
```

Observed results:

- Inventory summary: `backend_route_count=146`, `server_py_route_count=89`, `router_module_route_count=57`, `bff_route_map_count=71`, `bff_backend_path_count=70`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.
- Focused architecture inventory tests: `5 passed`.
- Focused BFF route-map tests: `12 passed`.

---

## Follow-Up Architecture Notes

This cleanup improves the current BFF + backend modular monolith without creating a parallel route system. The route map remains the correct central place for catch-all BFF forwarding policy.

Next architecture slices should use the inventory output before moving routes:

1. Refresh backend route ownership candidates still in `spine_api/server.py`.
2. Move one cohesive route family at a time only after coupling analysis.
3. Keep API route parity tests and BFF route-map tests green after each slice.
4. Do not add collection aliases such as `/api/overrides` unless the backend contract is intentionally created and documented.
