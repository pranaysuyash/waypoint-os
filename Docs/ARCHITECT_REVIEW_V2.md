# Architecture Review v2 — Waypoint OS

**Review Date:** 2026-04-28
**Method:** architect-review skill (8-step process)
**Scope:** All src/ and spine_api/ modules
**Documents preserved (no overwrite):** ARCHITECT_REVIEW_FINDINGS.md, COMPREHENSIVE_REVIEW_FINDINGS.md, IMPROVE_ARCHITECTURE_FINDINGS.md, PRODUCTION_AUDIT_FINDINGS.md

---

## Step 1: System Context

### What It Does
Waypoint OS is a B2B operations copilot for boutique travel agencies. It ingests natural-language travel inquiries, normalizes them into structured packets, detects ambiguity/gaps, makes booking decisions with confidence scoring, and produces twin output bundles: one for the traveler (sanitized, safe) and one for the internal operator (full data).

### Tech Stack
- **Runtime:** Python 3.13, FastAPI, uvicorn (1+ workers)
- **Database:** PostgreSQL via SQLAlchemy async + asyncpg (pool_size=20, max_overflow=10)
- **Persistence:** Dual — JSON file storage + SQLAlchemy ORM
- **Cache:** Redis (LLM usage guard), JSON file cache (decision cache)
- **LLM:** Gemini (primary), OpenAI (fallback), Local (transformers offline)
- **Frontend:** Next.js (separate directory, not in scope here)

### Module Map (src/)
```
intake/        Pipeline core: packet_models, extractors, validation, decision,
               strategy, safety, geography, orchestration, gates, frontier
decision/      Hybrid engine: cache → rules → LLM fallback, telemetry, health
suitability/   Activity scoring: Tier 1 deterministic, Tier 2 context, catalog
analytics/     Business analytics: scoring, logging, metrics, policy, review
llm/           Client abstraction: base, gemini, openai, local, usage guard
security/      Privacy guard + Fernet encryption
fees/          Fee calculations
pipelines/     EMPTY SHELL
adapters/      EMPTY SHELL
config/        EMPTY SHELL
schemas/       EMPTY SHELL
utils/         EMPTY SHELL
agents/        recovery_agent.py only
```

### Module Map (spine_api/)
```
server.py      App entrypoint + ALL route handlers + multiprocessing (2,644 lines)
contract.py    Pydantic response schemas (449 lines)
persistence.py Dual-backend persistence (1,115 lines)
routers/       auth, frontier, workspace
core/          auth, database, middleware, security, logging_filter
models/        ORM: tenant, frontier, trips
services/      auth_service, membership_service, workspace_service
run_{events, ledger, state}.py  Run lifecycle
watchdog.py    Process health
notifications.py  Email
```

---

## Step 2: Architecture Decisions — Evaluation

### Decision 1: Two-Loop Architecture (Online + Offline)
**Status:** Online loop is fully implemented. Offline loop (eval harness → mutation → score → persist) exists as concept but no concrete implementation was found.

**Risk: LOW.** The offline loop is a long-term vision. The online loop is the product. No active gap.

### Decision 2: Pipeline as Sequential Function Composition
`run_spine_once()` in orchestration.py chains 12+ sub-modules as a 300-line sequential function with inline gate checks, suitability injection, frontier orchestration, and fee calculation.

**Risk: MEDIUM.** The pipeline is tightly coupled — any new phase requires modifying orchestration.py. Individual phases cannot be tested independently without running the full spine.

### Decision 3: Dual Persistence Backend (JSON files + SQLAlchemy)
`spine_api/persistence.py` maintains two storage backends simultaneously. TripStore and AuditStore use JSON files with threading.Lock (not process-safe). SQLAlchemy models in `spine_api/models/` use async sessions.

**Risk: HIGH.** Two async engines exist (one in core/database.py, one in persistence.py). File locks don't synchronize across uvicorn workers. Data consistency between backends is not guaranteed.

### Decision 4: Hybrid Decision Engine (cache → rules → LLM)
`src/decision/` implements a cost-optimized flow with cache hit, rule hit, LLM fallback. Includes circuit breaker and telemetry.

**Risk: LOW.** Well-structured. The cache is file-based (thread lock only) — this breaks under multiple workers. Circuit breaker pattern is a good addition.

### Decision 5: Name Collision — Two `DecisionResult` Types
`src/intake/decision.py` defines its own `DecisionResult` dataclass. `src/decision/hybrid_engine.py` defines a different `DecisionResult` with different fields. The intake module imports from `src.decision.rules` at line 502.

**Risk: MEDIUM.** Two types with the same name but different shapes creates confusion. Developers must know which `DecisionResult` is being referenced.

### Decision 6: Structural Safety (Separate Builder Paths)
`src/intake/safety.py` enforces structural separation between traveler-safe and internal bundles. Internal data is never passed to traveler-facing builders.

**Risk: LOW.** Well-implemented. The FORBIDDEN_TRAVELER_CONCEPTS set and SanitizedPacketView are thorough. 38+ tests validate this.

### Decision 7: Module-Level Globals
Several modules use module-level singleton state:
- `src/security/encryption.py:_fernet` — global Fernet instance
- `src/intake/federated_intelligence.py:intelligence_service` — singleton
- `src/decision/cache_storage.py` — thread-locked file cache
- `spine_api/persistence.py:tripstore_engine` — second async engine

**Risk: MEDIUM.** Module-level state makes testing harder (state leaks between tests) and is not multiprocessing-safe.

### Decision 8: Cross-Boundary Import (analytics → spine_api)
`src/analytics/logger.py` and `src/analytics/review.py` import from `spine_api.persistence`. This violates the intended layering where `spine_api` depends on `src`.

**Risk: MEDIUM.** The `try/except ModuleNotFoundError` in logger.py confirms this is a known fragility.

---

## Step 3: Pattern Compliance Assessment

### Clean Architecture / Layered Architecture

```
IDEAL:    spine_api → src/analytics → src/intake → src/decision → src/llm
                                             ↕
                                      src/suitability
```

**ACTUAL:**
```
spine_api → src/analytics ⇄ spine_api  (cycle risk)
spine_api → src/analytics → src/intake
src/decision → src/intake/packet_models
src/intake → src/decision/rules
src/suitability → src/intake/packet_models
```

**Violations detected:**
1. Analytics imports from spine_api (wrong direction)
2. Two `decision` modules create name collision
3. server.py is a god module that should be decomposed

### SOLID Principles

| Principle | Assessment |
|-----------|------------|
| Single Responsibility | VIOLATED in server.py (2,644 lines), intake/decision.py (2,240 lines), persistence.py (1,115 lines) |
| Open/Closed | LARGELY MET — new LLM providers can be added without modifying base.py |
| Liskov Substitution | MET — LLM clients implement BaseLLMClient interface correctly |
| Interface Segregation | MET — modules expose focused interfaces through __init__.py |
| Dependency Inversion | VIOLATED — analytics depends on persistence concrete class, not protocol |

### DDD Patterns

- `CanonicalPacket` is the Aggregate Root — imported by 15+ files
- `SourceEnvelope`, `Slot`, `EvidenceRef` are Value Objects
- `GateVerdict` and `AutonomyOutcome` are Domain Events
- **Bounded Context:** intake/ has fuzzy boundaries — gates, frontier, and intelligence pool all live inside intake/

---

## Step 4: Architectural Violations & Anti-Patterns

### Anti-Pattern 1: God Module (server.py) — HIGH
2,644 lines combining: FastAPI app setup, CORS, ALL route handlers (/run, /override, /trips, /dashboard, /health, /run/*), multiprocessing orchestration, background tasks, error handlers, shutdown logic. Adding any new endpoint means modifying this file.

### Anti-Pattern 2: God Module (intake/decision.py) — HIGH
2,240 lines with: gap detection, confidence scoring, budget feasibility, hybrid engine integration, suitability risk generation. The docstring says "NB02 v0.2: Gap and Decision" but the file does 5+ distinct jobs.

### Anti-Pattern 3: God Module (persistence.py) — HIGH
1,115 lines with: JSON file storage, SQLAlchemy engine + session, process monitoring, encryption integration, serialization helpers. Dual async engine creation.

### Anti-Pattern 4: Dual Persistence (spine_api/persistence.py) — HIGH
Two async engines: one in `core/database.py` (pool_size=20, used by FastAPI routes), one in `persistence.py` (NullPool, used by TripStore). Same DATABASE_URL, different configurations. File-based TripStore uses `threading.Lock` which doesn't work across processes.

### Anti-Pattern 5: Empty Shell Packages — MEDIUM
`src/pipelines/`, `src/adapters/`, `src/config/`, `src/schemas/`, `src/utils/`, `src/llm/agents/` are all `__init__.py` only. These signal planned work that hasn't materialized, creating misleading namespace expectations.

### Anti-Pattern 6: Module-Level Global Mutable State — MEDIUM
- `persistence.py:tripstore_engine` — module-level engine
- `federated_intelligence.py:intelligence_service` — singleton with mutable _pool
- `decision.py:_hybrid_engine_instance` — lazy singleton
- `database.py:Base.metadata.clear()` — side effect at import time

### Anti-Pattern 7: Import-Time Side Effects — LOW
- `database.py:52` — `Base.metadata.clear()` executes at module import
- `encryption.py:26` — `_fernet = Fernet(ENCRYPTION_KEY)` executes at module import
- `geography.py` — loads city databases at import
- `privacy_guard.py` — `_load_fixture_ids()` executes at import, with `ast.parse` fallback

---

## Step 5: Recommendations with Refactoring Suggestions

### R1 — HIGH: Decompose server.py into Router Modules
**Move all route handlers out of server.py.** Each set of related endpoints gets its own router file.

**Suggested structure:**
```
spine_api/routers/
├── __init__.py
├── auth.py          # (exists)
├── frontier.py      # (exists)
├── workspace.py     # (exists)
├── runs.py          # /run, /run/{id}/status (moved from server.py)
├── trips.py         # /trips/{id}/* (moved from server.py)
├── dashboard.py     # /dashboard/* (moved from server.py)
├── override.py      # /override/* (moved from server.py)
└── health.py        # /health (new)
```

**server.py shrinks to:** app factory, middleware setup, shutdown logic, router inclusion.

**Tradeoff:** More files. But each router is independently testable, independently modifiable, and the file size drops from 2,644 to ~300 lines.

### R2 — HIGH: Choose One Persistence Backend
**Pick SQLAlchemy as the canonical backend.** Migrate TripStore and AuditStore from JSON files to PostgreSQL.

**Steps:**
1. Add `trips` and `audit_events` tables to spine_api/models/
2. Replace `_make_json_serializable()` with ORM serialization
3. Remove `tripstore_engine` and `tripstore_session_maker` from persistence.py
4. Use the canonical `get_db()` from core/database.py everywhere

**Tradeoff:** Migration effort (~2 days). Benefit: single engine, no file lock issues, consistent data, queryable.

### R3 — HIGH: Decompose intake/decision.py
**Split into focused files:**
```
src/intake/
├── decision.py          # Keep only: orchestrator (run_gap_and_decision)
├── gap_detection.py     # Gap detection logic (moved from decision.py)
├── confidence_scoring.py # Confidence scoring (moved from decision.py)
├── budget_feasibility.py # Budget checks (moved from decision.py)
└── risk_flags.py        # Risk flag generation (moved from decision.py)
```

**Tradeoff:** 5 files instead of 1. But each is independently testable and the file size drops from 2,240 to ~500 each.

### R4 — MEDIUM: Resolve Cross-Boundary Import Direction
**Extract audit/timeline abstractions into a shared module that spine_api depends on.**

**Options:**
1. Move `TimelineEvent`, `TimelineEventMapper`, `TripEventLogger` to `src/analytics/` and have spine_api import from there (correct direction)
2. Create `src/analytics/ports.py` with protocol/interface that persistence.py implements

**Tradeoff:** Option 1 is simpler. Option 2 follows DIP properly.

### R5 — MEDIUM: Process-Safe Decision Cache
**Replace file-based cache with Redis (already a dependency via usage_guard).**

**Tradeoff:** Adding Redis operational dependency for the cache. But it provides process-safe, shared state across workers — required for multi-worker production deployments.

### R6 — MEDIUM: Eliminate Module-Level Mutable State
**Move all singletons and module-level state into dependency injection:**
- `FederatedIntelligenceService` — create once, pass via constructor
- `DecisionCacheStorage` — create in app factory, pass via dependency
- `HybridDecisionEngine` — move `_hybrid_engine_instance` out of module-level

### R7 — MEDIUM: Clean Up Empty Shell Packages
**Either populate or remove:**
- If `src/pipelines/` was for future pipeline abstractions, populate it NOW with the Phase abstraction from the improved pipeline design
- If not, remove them

### R8 — LOW: Rename `src/intake/decision.py` to `src/intake/gap_decision.py`
**Resolve the name collision with `src/decision/`.**

**Tradeoff:** Import changes across the codebase. But eliminates a persistent source of confusion.

---

## Step 6: Scalability Implications

### Current State
- Single-process pipeline (run_spine_once is synchronous and blocking)
- File-based cache not process-safe
- Dual persistence backends with no data consistency guarantee
- Module-level state prevents clean multi-process scaling

### Path to Multi-Worker
1. **Must fix:** Redis-backed cache (R5), eliminate module-level state (R6)
2. **Should fix:** Single persistence backend (R2) — without this, JSON file locks will corrupt under multiple workers
3. **Nice to fix:** Make pipeline phases independently callable so they can be distributed

### Horizontal Scaling Limits
- `run_spine_once` is synchronous — it blocks a worker thread for the duration
- LLM API calls block the async event loop (no asyncio LLM client wrapper)
- Pipeline cannot be partially restarted or checkpointed mid-run

---

## Step 7: Architecture Decision Records

### ADR-2026-01: Pipeline Phase Abstraction

**Status:** Proposed
**Context:** run_spine_once is a 300-line sequential function that manually chains 12 sub-modules.
**Decision:** Introduce a `Phase` protocol:
```python
class Phase(Protocol):
    name: str
    async def run(ctx: PipelineContext) -> PhaseResult
```
Each phase is self-contained with explicit inputs/outputs. A PipelineRunner iterates the phase list and handles gate checks centrally.
**Consequences:**
- + Phases can be tested in isolation
- + New phases added by creating a new Phase class, not modifying orchestration.py
- + Gate checks become composable middleware, not inline if/else
- - More files and indirection
- - Migration of existing orchestration.py logic

### ADR-2026-02: Single Persistence Backend

**Status:** Proposed
**Context:** Two persistence backends (JSON files + SQLAlchemy) with inconsistent usage.
**Decision:** Standardize on SQLAlchemy ORM for all persistent storage. Migrate TripStore and AuditStore to database tables. Remove file-based persistence.
**Consequences:**
- + Single engine, single session factory
- + Process-safe (database transactions, not file locks)
- + Queryable data (can run SQL on trips and audit events)
- - Migration of existing JSON data
- - Schema migration needed for new tables

### ADR-2026-03: Dependency Inversion for Analytics → Persistence

**Status:** Proposed
**Context:** src/analytics imports directly from spine_api.persistence.
**Decision:** Define `AuditLogger` and `TripRepository` protocols in a shared `src/ports/` module. spine_api.persistence implements them. Analytics depends on the protocol, not the concrete class.
**Consequences:**
- + Clean layer direction
- + Testable (analytics can use mock repositories)
- - Protocol definitions add indirection
- - Some interfaces may need iteration

---

## Step 8: Implementation Guidance

### Phase 1 (Fix Production Blockers — 1-2 days)
1. Decompose server.py into router modules (R1)
2. Fix intake/decision.py god file (R3)
3. Move imports for analytics → persistence to correct direction (R4)

### Phase 2 (Architecture Hardening — 3-5 days)
4. Single persistence backend migration (R2)
5. Process-safe decision cache (R5)
6. Eliminate module-level state (R6)

### Phase 3 (Cleanup — 1 day)
7. Resolve module name collision (R8)
8. Clean up or populate empty packages (R7)
9. Introduce Pipeline Phase abstraction (R1)

---

## Appendix: Pattern Compliance Summary

| Pattern | Grade | Notes |
|---------|-------|-------|
| Layered Architecture | C | Cross-boundary imports, god files, circular risk |
| SOLID — SRP | D | 3 files over 1,000 lines with mixed concerns |
| SOLID — OCP | A | LLM client architecture is clean |
| SOLID — DIP | D | Analytics depends on concrete persistence, not protocol |
| DDD — Aggregate | B | CanonicalPacket is good; fuzzy bounded context for intake/ |
| Safety/Security | A | Structural traveler-safe separation is thorough |
| Error Handling | C | print() instead of logging, try/except/ModuleNotFoundError patterns |
| Testability | C | Module-level state and dual persistence make isolated testing hard |
| Scalability | D | File-based cache, module-level state, no process safety |
| Documentation | B | README is strong, ADR proposals exist, some docs stale |
