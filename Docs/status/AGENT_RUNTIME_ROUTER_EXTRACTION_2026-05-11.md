# Agent Runtime Router Extraction

**Date:** 2026-05-11  
**Status:** Complete  
**Parent architecture review:** [Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md](../exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)  
**Current inventory:** [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md)

---

## Purpose

Move the product-agent runtime HTTP surfaces out of `spine_api/server.py` while keeping lifecycle ownership in the FastAPI application shell. This is a small, bounded router extraction for:

- `GET /agents/runtime`
- `POST /agents/runtime/run-once`
- `GET /agents/runtime/events`

The underlying runtime remains the existing in-process `AgentSupervisor` plus `RecoveryAgent`. No queue, worker, plugin runtime, or microservice was introduced.

---

## Supersession Analysis

Removal candidate: agent-runtime handlers in `spine_api/server.py`.

Replacement: [spine_api/routers/agent_runtime.py](../../spine_api/routers/agent_runtime.py).

| Dimension checked | Verdict |
| --- | --- |
| Route paths | Superset: all three method/path pairs moved unchanged. |
| Runtime lifecycle | Preserved: `server.py` still creates, starts, and stops `_agent_supervisor` and `_recovery_agent`. |
| HTTP ownership | Improved: router owns introspection/admin request handling. |
| Runtime dependency injection | Preserved through `configure_runtime(...)`, called by `server.py` after singleton creation and before router inclusion. |
| Event query behavior | Preserved: `/agents/runtime/events` still reads canonical agent events through `AuditStore.get_agent_events`. |
| BFF compatibility | Preserved: route-map entries still target the same backend paths. |
| Tests | Updated: agent runtime API tests patch the app-loaded `routers.agent_runtime` module. |

Decision: the old `server.py` agent-runtime handlers were fully superseded by the router implementation and were removed to avoid duplicate route registration.

---

## Files Updated

- [spine_api/routers/agent_runtime.py](../../spine_api/routers/agent_runtime.py) — new product-agent runtime route module.
- [spine_api/server.py](../../spine_api/server.py) — imports/configures/includes the agent-runtime router and removes superseded local handlers.
- [tests/test_agent_events_api.py](../../tests/test_agent_events_api.py) — updates runtime endpoint monkeypatches to target the app-loaded router module.
- [tests/test_architecture_route_inventory.py](../../tests/test_architecture_route_inventory.py) — asserts route ownership now includes `agent_runtime`.
- [Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md](ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md) — regenerated after extraction.

---

## Verification Evidence

Commands run:

```bash
uv run python -m pytest tests/test_architecture_route_inventory.py::test_route_inventory_tracks_server_py_and_router_module_ownership -q
python3 -m py_compile spine_api/routers/agent_runtime.py spine_api/server.py
uv run python -m pytest tests/test_agent_events_api.py tests/test_architecture_route_inventory.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q
uv run python tools/architecture_route_inventory.py --format json
uv run python tools/architecture_route_inventory.py --format md --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_2026-05-11.md
```

Observed results:

- Red check before extraction: ownership test failed with `KeyError: 'agent_runtime'`, proving the test detected missing router ownership.
- Syntax check: passed.
- Agent-runtime/parity/startup/inventory targeted suite: `19 passed`.
- Duplicate scan found `/agents/runtime` decorators only in `spine_api/routers/agent_runtime.py`.
- Inventory summary after extraction: `backend_route_count=146`, `server_py_route_count=64`, `router_module_route_count=82`, `router_module_count=17`, `bff_route_map_count=71`, `bff_unmatched_backend_path_count=0`, `potential_duplicate_backend_route_count=0`.

---

## Follow-Up Notes

The route move intentionally does not change the agent runtime topology. The future long-term architecture decision remains: keep product-agent execution in-process until a durable Postgres-backed job/worker boundary is explicitly designed and tested.

Next modularity candidates:

1. `analytics` routes: high route count, needs helper/coupling analysis.
2. public-checker routes: cohesive and bounded, but public/export/delete behavior needs contract review.
3. document/booking collection routes: valuable boundary, higher blast radius due uploads and extraction.
