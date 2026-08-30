# Server Decomposition Plan — spine_api (R-10)

**Status:** Proposed design (not yet implemented)
**Date:** 2026-08-29
**Owner:** Backend architecture
**Associated finding:** R-10 (monolithic `spine_api/server.py` — 3,719 lines, 44 routers, two divergent audit systems)

## Problem

`spine_api/server.py` is a 3,719-line monolith that imports and mounts 44 routers, builds middleware, runs startup assertions, configures OpenTelemetry, and houses the application lifespan (agent runtime bundle, recovery agent, supervisor, requeue worker, zombie reaper). This produces:

- **High change amplification** — any shared change touches one very large file.
- **Scattered responsibilities** — there is no single owner for server assembly vs. router registration vs. runtime lifecycle.
- **Regression risk** — the route-inventory tests (`route_count=226`) make the assembled surface a contract; broad edits risk drift.

## Decomposition target

This is a **modularization**, not a microservices split. The doctrine's Refactor Decision Architect explicitly rejects microservices here (no evidence of a scaling bottleneck; splitting adds coordination cost). The target is **clean APIRouter decomposition with a shared assembly module**, preserving the single-process FastAPI app.

Proposed structure:

```
spine_api/
  app.py                # create_app() factory: builds FastAPI, mounts middleware,
                        #   applies startup assertions, wraps routers
  server.py             # (kept as thin entrypoint) -> calls create_app() for uvicorn
  routers/              # existing 44 routers (already single-responsibility)
  middleware.py         # existing middleware, unchanged
  runtime/              # NEW: extract lifecycle (agent bundle, supervisor, requeue, reaper)
    lifecycle.py
    supervisor.py
    requeue_worker.py
    zombie_reaper.py
  core/
    startup_assertions.py  # unchanged
    reality_tier.py        # unchanged
    feature_gates.py       # unchanged
```

### Reasons for this boundary

1. **Routers are already single-responsibility** — each API domain has its own module. Splitting `server.py` into `app.py` (assembly) + `runtime/` (lifecycle) is the smallest coherent intervention.
2. **The only genuinely monolithic concern is assembly + lifecycle.** Extract the agent-runtime lifecycle into `runtime/` so the server file stops owning process-level concerns.
3. **Single source of truth for the route contract** — keep the route-inventory test as the guard that the assembly produces the same surface.

## Migration path (safe, incremental)

1. **Extract `create_app()` factory** into `spine_api/app.py`. `server.py` becomes a thin `app = create_app()` entrypoint. Run the route-inventory test (`test_server_openapi_path_parity.py`) — assert `route_count` unchanged (226).
2. **Extract agent-runtime lifecycle** into `spine_api/runtime/lifecycle.py` (moves `_build_agent_runtime_bundle`, `_recovery_agent`, `_agent_supervisor`, `_requeue_worker_service`, `_zombie_reaper_start`). `server.py` lifespan calls into it.
3. **Verify** — run the full backend test suite + route-inventory + import smoke test after each step.

## Unify audit stores (done)

The two audit systems are now unified on the RULE_015 SHA-256 chain:
- `spine_api/models/audit.py` `AuditLog` now has `previous_hash`/`current_hash` columns (backward-compatible nullable) — migration `add_audit_chain_hash`.
- `spine_api/core/audit.py` `AuditContext.log()` computes the chain, mirroring the file-based `AuditStore` semantics.
- The file-based `AuditStore` remains for legacy/back-compat but the DB path is the production-grade record.

## Acceptance criteria

- The route-inventory test still reports `route_count=226` (no surface drift).
- `create_app()` is importable and produces an equivalent FastAPI app.
- No change to the 44 router modules' public endpoints.
- The DB audit log entries carry a valid `current_hash`; consecutive entries form a linked chain.

## Risks / open questions

- The route-inventory snapshot must be regenerated if `create_app()` changes any path (it should not).
- The lifespan reordering must preserve the startup-assertion fail-closed behavior (R-03 relies on it).
- Whether `runtime/` should be framework-agnostic or FastAPI-coupled — deferring that decision until extraction reveals the real coupling.
