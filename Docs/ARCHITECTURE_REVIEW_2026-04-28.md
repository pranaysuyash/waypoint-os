# Architecture Review — Waypoint OS (travel_agency_agent)

**Date:** 2026-04-28

## Architecture Overview

Waypoint OS is a B2B operations copilot for boutique travel agencies, implemented as a pipeline-based monolith with a FastAPI backend and Next.js frontend. The core architecture follows a sequential pipeline pattern: `Inquiry -> NB01 Intake (extraction/normalization) -> NB02 Decision (gap detection/confidence scoring) -> NB03 Strategy (output bundle generation)`, with a separate hybrid decision engine (`src/decision/`) layered as cache->rules->LLM fallback. The backend exposes this via a single `POST /run` endpoint that spawns a daemon thread, with a run ledger for polling-based status tracking. Multi-tenancy is achieved through agency-scoped JWT auth with role-based permissions (owner->admin->senior_agent->junior_agent->viewer).

The system uses a dual persistence strategy: JSON file storage for trips/assignments/audit events (via `spine_api/persistence.py`) and SQLAlchemy async ORM for tenant/auth data (via `spine_api/core/database.py`). The frontend is a Next.js App Router application with a BFF proxy (`frontend/src/proxy.ts`), Zustand for state management, and a centralized `ApiClient` class. The project has strong testing discipline with 67 test files covering geography extraction, decision logic, safety leakage detection, E2E flows, and lifecycle management.

The architecture is ambitious and well-documented but has several structural issues that limit scalability and maintainability. At 6,806 lines across just 4 files (server.py, persistence.py, decision.py, orchestration.py), the system has significant god module problems. The dual persistence backend and file-based caching create process-safety risks in multi-worker deployments. Cross-boundary imports (analytics -> spine_api) and name collisions (two `DecisionResult` types) indicate growing pains from rapid iteration.

---

## Strengths

- **Excellent safety model**: `src/intake/safety.py` enforces structural separation between traveler-safe and internal bundles using `SanitizedPacketView` and `FORBIDDEN_TRAVELER_CONCEPTS`, validated by 38+ tests. Data never flows between the two builder paths.

- **Well-defined API contract**: `spine_api/contract.py` is a single source of truth for all Pydantic response schemas. TypeScript types are auto-generated from these models, causing build errors if frontend code is out of sync.

- **Cost-optimized decision engine**: `src/decision/hybrid_engine.py` implements a three-tier cache->rules->LLM fallback with circuit breakers, telemetry, and cost tracking (`cost_inr`). Feature-flagged via `USE_HYBRID_DECISION_ENGINE` env var.

- **Strong test discipline**: 67 test files across geography validation, decision logic, safety leakage, E2E flows, lifecycle retention, and API contracts. Tests validate real schema contracts (not mocked approximations).

- **Multi-tenancy**: Clean agency-scoped auth with `get_current_agency`, `get_current_membership`, and `require_permission` decorators in `spine_api/core/auth.py`. Permission matrix with 5 roles and granular permissions.

- **Run lifecycle tracking**: `RunLedger` (`spine_api/run_ledger.py`) persists per-run metadata and stage outputs with an append-only event log, enabling polling-based status tracking for the async pipeline.

- **Quality gates**: `src/intake/gates.py` defines formal `GateVerdict` (PROCEED/RETRY/ESCALATE/DEGRADE) and `AutonomyOutcome` with a three-layer model (judgment->policy->human action).

- **LLM abstraction**: `src/llm/` provides a clean `BaseLLMClient` interface with Gemini, OpenAI, and local transformers implementations. Open/Closed principle is well-respected -- new providers can be added without modifying existing clients.

---

## Issues Found

### P0 -- Production Blockers

**P0-01: Dual persistence backends with no consistency guarantees**
`spine_api/persistence.py` (line 36) creates a second async engine alongside `spine_api/core/database.py` (line 28). Same `DATABASE_URL`, different configurations (NullPool vs. pool_size=20). TripStore/AuditStore use JSON files with `threading.Lock` (line 22), which provides no synchronization across uvicorn workers. Concurrent writes from multiple workers will corrupt trip data.

Recommendation: Adopt SQLAlchemy as the sole backend. Migrate TripStore and AuditStore to database tables. Remove file-based persistence and the second engine. This is a 2-day migration that eliminates an entire class of data-integrity bugs.

**P0-02: server.py is a 2,644-line god module**
`spine_api/server.py` combines: FastAPI app creation, CORS configuration, ALL route handlers (`/run`, `/runs/*`, `/trips/*`, `/assignments`, `/audit`, `/dashboard`, `/override`, `/health`), multiprocessing zombie reaper, background thread orchestration, error handlers, seed scenario loading, schema compatibility checks, and adapter classes. Adding any new endpoint requires modifying this file.

Recommendation: Move route handlers into individual router files under `spine_api/routers/` (runs.py, trips.py, dashboard.py, override.py, health.py). Each router is independently testable and file size drops from 2,644 to ~300 lines.

**P0-03: src/intake/decision.py is a 2,240-line god module**
Single file handles gap detection, confidence scoring, budget feasibility, hybrid engine integration, suitability risk generation, and follow-up question synthesis. The docstring says "NB02 v0.2: Gap and Decision" but contains 5+ distinct responsibilities with no internal decomposition.

Recommendation: Split into focused modules: `gap_detection.py`, `confidence_scoring.py`, `budget_feasibility.py`, `risk_flags.py`. Each drops from 2,240 lines to ~500 and becomes independently testable.

### P1 -- Architecture Hardening

**P1-01: Name collision -- two `DecisionResult` types**
`src/intake/decision.py` defines `DecisionResult` as a dataclass (line 12). `src/decision/hybrid_engine.py` defines a different `DecisionResult` with different fields (line 47). The intake module imports from `src.decision.rules` at line 502. Developers must know which `DecisionResult` is in scope at any given point.

Recommendation: Rename `src/intake/decision.py` to `src/intake/gap_decision.py` and its `DecisionResult` to `GapDecisionResult`. Or rename `src/decision/` to `src/hybrid_decision/`.

**P1-02: Cross-boundary import -- analytics -> spine_api**
`src/analytics/logger.py` (line 10) imports from `spine_api.persistence` using `try/except ModuleNotFoundError` (line 9-13). This violates the layering where `spine_api` should depend on `src`, not the reverse. The `try/except` pattern confirms this is known-fragile.

Recommendation: Extract `AuditStore` interface into a shared `src/ports/` module. `spine_api/persistence.py` implements the port. `src/analytics/` depends on the protocol only.

**P1-03: Thread-based pipeline execution in FastAPI**
`POST /run` (server.py line 1020) spawns a daemon `threading.Thread` to run the spine pipeline. FastAPI/uvicorn uses an async event loop -- running synchronous/blocking code in a daemon thread prevents proper cancellation, error propagation, and backpressure. The zombie reaper (line 643) workaround for leaked child processes confirms this design is fragile.

Recommendation: Use a proper task queue (Celery, ARQ, or Redis-backed job queue) for long-running pipeline execution. Or wrap the synchronous pipeline in `asyncio.to_thread()` for at least basic async compatibility.

**P1-04: File-based decision cache is not process-safe**
`src/decision/cache_storage.py` uses `threading.Lock` (inferred from hybrid_engine.py importing `get_default_storage`). File-based caching with thread locks provides no synchronization across uvicorn workers. Redis is already a project dependency (for LLM usage guard in `src/llm/usage_guard.py`).

Recommendation: Replace file-based cache with Redis-backed cache using the existing Redis dependency. This provides process-safe shared state across workers.

**P1-05: Module-level global mutable state**
Multiple modules use module-level singletons:
- `spine_api/persistence.py:36` -- `tripstore_engine` (second async engine)
- `src/intake/federated_intelligence.py` -- `intelligence_service` singleton
- `src/intake/decision.py:33` -- `_hybrid_engine_instance` lazy singleton
- `src/security/encryption.py:26` -- global `_fernet` instance

This makes testing harder (state leaks between tests) and prevents clean multiprocess scaling.

Recommendation: Move all singletons into dependency injection. Create instances at app startup and pass them via constructor or FastAPI `Depends()`.

### P2 -- Quality of Life

**P2-01: Import-time side effects**
- `spine_api/core/database.py:52` -- `Base.metadata.clear()` executes at module import
- `src/security/encryption.py:26` -- `_fernet = Fernet(ENCRYPTION_KEY)` at import
- `src/intake/geography.py` -- loads city databases at module import
- `src/security/privacy_guard.py` -- `_load_fixture_ids()` at import with `ast.parse` fallback

These cause slow startup, hidden failures, and make imports order-dependent.

Recommendation: Use lazy initialization or explicit `init()` functions for all expensive/side-effect-heavy operations.

**P2-02: Empty shell packages creating misleading namespace expectations**
Five packages under `src/` contain only `__init__.py`: `pipelines/`, `adapters/`, `config/`, `schemas/`, `utils/`. These signal planned work that hasn't materialized but creates namespace confusion.

Recommendation: Either populate them with actual content or remove them to avoid confusing future developers.

**P2-03: `docker-compose.yml`, `fly.toml`, `Procfile`, `render.yaml` -- four deployment configs**
The project has deployment configurations for Docker Compose, Fly.io, Render, and a Procfile. This fragmentation means each requires separate maintenance and no single path is canonical.

Recommendation: Choose one deployment target and consolidate. Remove the other configs or archive them.

**P2-04: `package.json` at root is empty**
`/package.json` (line 1): `{}`. This suggests an abandoned monorepo attempt or a stray file.

Recommendation: Either remove it or use it for workspace-level scripts if a monorepo setup is intended.

**P2-05: No explicit monitoring or observability configuration**
Despite having health endpoints, run events, and audit logging, there is no structured observability framework (OpenTelemetry, structured logging, metrics export). The `logs/` directory exists but no rotation or aggregation strategy is visible.

Recommendation: Add structured JSON logging, OpenTelemetry instrumentation for FastAPI, and configure log rotation.

---

## Architecture Assessment Score

| Dimension | Score | Key Issue |
|-----------|-------|-----------|
| Architecture Pattern | 6/10 | Two-loop concept is clean; sequential function composition is not |
| Module Boundaries | 4/10 | God modules (server.py, decision.py, persistence.py) violate SRP |
| Data Flow | 7/10 | SourceEnvelope->CanonicalPacket is clear; dual persistence muddies it |
| API Design | 7/10 | Well-defined contracts; all-in-one server.py hurts discoverability |
| Dependency Management | 5/10 | Cross-boundary imports, try/except fallbacks, empty shell packages |
| Scalability | 4/10 | File-based cache, module-level state, thread-based async, no process safety |
| Maintainability | 5/10 | God modules, name collisions, dual backends, fragmentation |
| Test Coverage | 8/10 | 67 test files, real schema contracts, good coverage breadth |
| Safety/Security | 8/10 | Excellent traveler-safe separation, auth, role-based permissions |
| Documentation | 7/10 | Strong README, ADR proposals exist, some architectural docs stale |

**Overall: 6.3 / 10**

The architecture has a solid foundation -- the pipeline concept, safety model, and API contracts are well-designed. The critical issues are structural: three god modules (6,800 lines total), dual persistence backends that will corrupt data under concurrent access, and process-unsafe caching that prevents horizontal scaling. These are fixable with targeted refactoring -- Phase 1 (server.py decomposition + persistence unification) is ~3 days work and would raise the score to ~7.5.
