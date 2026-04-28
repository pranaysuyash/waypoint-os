# Architecture Review Findings — Waypoint OS (travel_agency_agent)

**Review Date:** 2026-04-28
**Reviewer:** Hermes (architect-review + comprehensive-review-full-review framework)
**Scope:** All src/ and spine_api/ modules (~70 Python source files)
**Rule:** Report only — no code changes, no git commands

---

## A. System Overview

### A.1 Purpose
Waypoint OS is a B2B revenue and operations copilot for boutique travel agencies. It ingests travel inquiries (vague, contradictory natural language), normalizes them into structured packets, detects gaps, makes booking decisions, and generates traveler-safe output bundles for clients plus internal strategy bundles for operators.

### A.2 Two-Loop Architecture
```
Online Loop:  Source -> Normalize -> Validate -> Infer -> Decide -> Execute -> Log
Offline Loop: Eval Harness -> Mutation -> Score -> Persist (if improved)
```

### A.3 Pipeline Stages (NB01-NB03)
```
Inquiry -> NB01 Intake -> NB02 Gap & Decision -> NB03 Strategy & Prompt -> Output
```

### A.4 Deployment Model
- **Backend**: FastAPI (spine_api/server.py) with uvicorn, 1+ workers
- **Frontend**: Next.js (frontend/ directory)
- **Database**: PostgreSQL via SQLAlchemy async (asyncpg)
- **Persistence**: Hybrid — JSON files on disk + SQLAlchemy ORM
- **Cache**: Redis (LLM usage guard) + JSON file cache (decision cache)
- **LLM**: Gemini (primary), OpenAI (fallback), Local (offline)

### A.5 Module Map
```
src/
├── intake/           — Pipeline core (15 files): packet_models, extractors,
│                       validation, decision, strategy, safety, geography,
│                       orchestration, gates, frontier_orchestrator, etc.
├── decision/         — Hybrid decision engine (12 files): hybrid_engine, cache,
│                       rules/, telemetry, health
├── suitability/      — Activity suitability scoring (6 files)
├── analytics/        — Business analytics (7 files): engine, logger, metrics,
│                       models, policy_rules, review
├── llm/              — LLM client abstractions (8 files): base, gemini, openai,
│                       local_llm, usage_guard, usage_store, agents/
├── security/         — Privacy guard + encryption (2 files)
├── agents/           — Agent definitions (recovery_agent.py)
├── fees/             — Fee calculations (calculation.py)
├── pipelines/        — Empty package (__init__.py only)
├── config/           — Empty package
├── adapters/         — Empty package
├── schemas/          — Empty package
└── utils/            — Empty package

spine_api/
├── server.py         — FastAPI app (2644 lines)
├── contract.py       — Response schemas (449 lines)
├── persistence.py    — Hybrid persistence layer (1115 lines)
├── routers/          — API routes: auth, frontier, workspace
├── core/             — auth, database, middleware, security, logging_filter
├── models/           — SQLAlchemy ORM models: tenant, frontier, trips
├── services/         — auth_service, membership_service, workspace_service
├── watchdog.py       — Process health monitoring
├── notifications.py — Email notifications
├── run_events.py     — Run event tracking
├── run_ledger.py     — Run ledger
└── run_state.py      — Run state machine
```

---

## B. Module Analysis

### B.1 src/intake/ — Pipeline Core
**Responsibility:** End-to-end pipeline orchestration for the three stages.

**Public Interface (via src/intake/__init__.py):**
- Models: Ambiguity, AuthorityLevel, CanonicalPacket, EvidenceRef, ExtractionMode, LifecycleInfo, OwnerConstraint, Slot, SourceEnvelope, SubGroup, UnknownField
- Functions: Normalizer, ExtractionPipeline, PacketValidationReport, validate_packet, run_gap_and_decision, build_session_strategy, build_traveler_safe_bundle, build_internal_bundle, run_spine_once, run_frontier_orchestration, is_known_city, is_known_destination, sanitize_for_traveler, enforce_no_leakage, check_no_leakage

**Internal Structure:**
- `packet_models.py` (483 lines) — CanonicalPacket + all supporting dataclasses. Single source of truth for packet shape.
- `extractors.py` — ExtractionPipeline with pattern-based extraction from natural language.
- `normalizer.py` — Text normalization with ambiguity detection.
- `validation.py` — Packet validation rules.
- `decision.py` — NB02 v0.2 gap and decision engine (2240 lines). LARGE FILE.
- `strategy.py` — NB03 session strategy and bundle builders.
- `safety.py` — Structural traveler-safe sanitization and leakage detection.
- `orchestration.py` — Single spine entrypoint (807 lines). Chains all modules.
- `gates.py` — NB01CompletionGate, NB02JudgmentGate, Autonomy gates.
- `frontier_orchestrator.py` — Ghost Concierge, emotional monitoring, intelligence pool.
- `federated_intelligence.py` — Intelligence pool service (risk data sharing).
- `negotiation_engine.py` — Supplier negotiation logic.
- `checker_agent.py` — Redundancy checker for autonomous decisions.
- `geography.py` — GeoNames + world cities database (494 lines).
- `telemetry.py` — Ambiguity synthesis emissions.
- `config/agency_settings.py` — Agency configuration.

**Cohesion Assessment:**
- HIGH cohesion — all files in the package serve the pipeline
- However, `decision.py` at 2240 lines is a god file candidate
- Mixed concerns: gates, telegraph, and intelligence pool all live here
- `packet_models.py` is imported by almost every other module — high centrality

### B.2 src/decision/ — Hybrid Decision Engine
**Responsibility:** Cost-optimized decision flow: cache -> rules -> LLM fallback.

**Public Interface:**
- HybridDecisionEngine, DecisionResult, EngineMetrics, CachedDecision, DecisionCacheStorage, DecisionTelemetry, HybridEngineHealth

**Internal Structure:**
- `hybrid_engine.py` (828 lines) — Main orchestrator
- `cache_key.py` — Cache key generation from packet content
- `cache_schema.py` — Cache entry data model
- `cache_storage.py` — JSON file-based cache persistence
- `telemetry.py` — Metrics tracking
- `health.py` — Health checks + circuit breaker
- `rules/` — 6 rule files (mobility, toddler, budget, visa, composition, not_applicable)
- `whatsapp_formatter.py` — WhatsApp-specific output formatting

**Cohesion Assessment:**
- HIGH cohesion — the module is self-contained with clear concerns separated into files
- Exports are well-documented in __init__.py
- The `rules/` subpackage follows a clean register pattern for rule registration
- Dependency on `src.intake.packet_models` is appropriate (needs CanonicalPacket)

### B.3 src/suitability/ — Activity Suitability Scoring
**Responsibility:** Three-tier scoring system for travel activity recommendations.

**Public Interface:**
- ActivityDefinition, ParticipantRef, StructuredRisk, SuitabilityContext
- evaluate_activity, apply_tour_context_rules, compute_confidence, collect_missing_signals
- extract_participants_from_packet, generate_suitability_risks, assess_activity_suitability

**Internal Structure:**
- `models.py` (116 lines) — Typed contracts
- `scoring.py` — Tier 1 deterministic scoring
- `context_rules.py` — Tier 2 day/trip coherence rules
- `confidence.py` — Confidence calculation
- `catalog.py` — Static activity definitions
- `integration.py` (314 lines) — Decision pipeline integration

**Cohesion Assessment:**
- HIGH cohesion — clean separation of tiers and concerns
- Integration point is well-defined through `integration.py`
- Clean dependency: packet -> suitability (one-directional)

### B.4 src/analytics/ — Business Analytics
**Responsibility:** Trip analytics, dashboard aggregation, review logic.

**Internal Structure:**
- `engine.py` — Scoring functions (completeness, feasibility, risk, margin)
- `logger.py` — TripEventLogger + TimelineEventMapper
- `metrics.py` — Revenue metrics
- `models.py` — Pydantic models
- `policy_rules.py` — Owner escalation and send policies
- `review.py` — Review logic using persistence layer
- `dashboard_aggregator.py` (in services/) — Dashboard state aggregation

**Cohesion Assessment:**
- MODERATE cohesion — engine.py and logger.py have overlapping concerns
- Dependency on `spine_api.persistence.AuditStore` creates a cross-boundary import pattern (src -> spine_api)
- `logger.py` has a conditional import for AuditStore with try/except ModuleNotFoundError — sign of unresolved layering

### B.5 src/llm/ — LLM Client Abstractions
**Responsibility:** Unified LLM interface with multiple backends.

**Public Interface:**
- BaseLLMClient, GeminiClient, LocalLLMClient, create_gemini_client, create_local_llm_client
- LLMError, LLMUnavailableError, LLMResponseError
- UsageGuard, UsageStore

**Internal Structure:**
- `base.py` — Abstract base class
- `gemini_client.py` — Google Gemini implementation
- `openai_client.py` — OpenAI implementation
- `local_llm.py` — Local inference via transformers
- `usage_guard.py` — Usage quotas and limits
- `usage_store.py` — Usage data persistence

**Assessment:**
- Well-structured abstract base class pattern
- Clean extension point for new backends
- `agents/` subpackage exists but is empty

### B.6 src/security/ — Privacy and Encryption
**Responsibility:** PII guardrails and encryption.

**Internal Structure:**
- `encryption.py` (44 lines) — Fernet-based encryption wrapper
- `privacy_guard.py` (333 lines) — PII detection and blocking

**Assessment:**
- Encryption is a thin Fernet wrapper — adequate for current stage
- `encryption.py` has a hardcoded development key as fallback (documented)
- `privacy_guard.py` is more substantial with fixture ID detection
- Privacy guard has a `try/except/ast.parse` fallback path for fixture detection — fragile but functional

### B.7 spine_api/ — FastAPI Backend
**Responsibility:** HTTP API surface, database models, persistence, auth.

**Key Files:**
- `server.py` (2644 lines) — LARGE. App creation, all route registrations, all endpoint handlers, background tasks, error handlers, multiprocessing setup.
- `contract.py` (449 lines) — Pydantic response schemas
- `persistence.py` (1115 lines) — Hybrid JSON file + SQLAlchemy persistence
- `run_events.py` / `run_ledger.py` / `run_state.py` — Run lifecycle management

**Assessment:**
- `server.py` at 2644 lines is a critical architectural concern — it combines app setup, ALL route handlers, background tasks, multiprocessing orchestration, and error handling in one file
- Routes are partially extracted into routers/ (auth.py, frontier.py, workspace.py) but the main /run, /override, /trips, /dashboard etc. all live in server.py
- `persistence.py` has dual storage backends (JSON files + SQLAlchemy) that are inconsistently used

---

## C. Dependency Analysis

### C.1 Dependency Direction (Canonical)
```
                    spine_api/
                       |
                       v
     src/analytics/ --> src/intake/ <-- src/decision/
          |                 |           /
          |                 v          /
          |        src/suitability/   /
          |                          /
          +----< src/security/ <----+
                       |
                       v
                  src/llm/
```

### C.2 Cross-Boundary Imports (Concerns)

1. **src/analytics -> spine_api** (INCORRECT direction):
   - `src/analytics/logger.py` does `from spine_api.persistence import AuditStore` inside a try/except ModuleNotFoundError
   - `src/analytics/review.py` imports directly from `spine_api.persistence`
   - This violates the intended layering. spine_api should depend on src, not vice versa.

2. **src/analytics -> src/intake**: 
   - `src/analytics/engine.py` operates on `Dict[str, Any]` (loose dicts), not typed packet objects — weak contract

3. **spine_api -> src/security**:
   - `spine_api/persistence.py` imports `encrypt`/`decrypt` from `src.security.encryption`
   - Correct direction, but encrypt/decrypt at the persistence layer means all stored data is encrypted — good

4. **spine_api -> src/analytics**:
   - `spine_api/persistence.py` imports `process_trip_analytics` from `src.analytics.engine`
   - Correct direction

### C.3 Circular Dependency Risk
- None detected from import analysis — the dependency graph is acyclic
- However, the cross-boundary imports (analytics -> spine_api) create a logical cycle risk if not careful

### C.4 Packet Model Centrality
- `src/intake/packet_models.py` is imported by nearly every module:
  - All rules in src/decision/rules/
  - src/decision/hybrid_engine.py, cache_key.py
  - src/suitability/integration.py
  - src/intake/* (all submodules)
  - spine_api/routers/frontier.py
- This makes packet_models a high-risk change surface — any change here ripples everywhere

---

## D. Architectural Concerns

### D.1 CRITICAL: server.py God File (2644 lines)
`spine_api/server.py` contains:
- FastAPI app creation
- All CORS/config setup
- All route handlers (run, override, trips, dashboard, health, etc.)
- Multiprocessing run orchestration
- Background task handling
- Error handlers
- Shutdown logic

**Impact:** Maintainability risk. Adding one endpoint means modifying this file. Testing individual handlers is harder. Route handlers should be extracted into routers/ with clear separation.

### D.2 HIGH: persistence.py Dual Backend (1115 lines)
`spine_api/persistence.py` has:
- JSON file storage (TripStore, AuditStore)
- SQLAlchemy async engine + session
- Process health monitoring
- Encryption integration

**Impact:** Two persistence strategies exist simultaneously without clear separation. Some data goes to JSON files (data/trips/, data/audit/), some goes to PostgreSQL via SQLAlchemy models. This adds cognitive load and risks inconsistent data.

### D.3 MEDIUM: src/intake/decision.py God File (2240 lines)
Contains gap detection, confidence scoring, inference, budget feasibility, risk flags, AND the hybrid engine integration. Multiple concerns in one file.

**Impact:** Hard to test individual concerns. File is already difficult to navigate (requires scrolling through 2000+ lines).

### D.4 MEDIUM: Empty Shell Packages
Several packages exist as empty shells:
- `src/pipelines/` (__init__.py only)
- `src/adapters/` (__init__.py only)
- `src/config/` (__init__.py only)
- `src/schemas/` (__init__.py only)
- `src/utils/` (__init__.py only)
- `src/llm/agents/` (__init__.py only)

**Impact:** These represent planned or aspirational architecture that hasn't materialized. They create namespace confusion (is something supposed to be in pipelines or orchestration?).

### D.5 LOW: Cross-Boundary Import Pattern
`src/analytics/logger.py` and `src/analytics/review.py` import from `spine_api.persistence`. This violates a clean layered architecture where spine_api should depend on src, not the reverse.

**Impact:** Creates a fragile import that relies on module availability at runtime (the try/except pattern confirms this is known fragility).

### D.6 LOW: Module Name Collision
There are TWO `decision` modules:
- `src/intake/decision.py` — NB02 gap and decision (legacy)
- `src/decision/` — Hybrid decision engine (newer)

The `src/intake/decision.py` imports from `src.decision.rules` at line 502. This works but creates confusion about which decision module does what.

---

## E. Scalability

### E.1 State Management
- Pipeline state is ephemeral within `run_spine_once()` — no persistent state between runs
- Run state machine (run_state.py) tracks run lifecycle
- Decision cache is JSON-file-based (src/decision/cache_storage.py) with thread lock, not process-safe
- No distributed state management

**Risk:** The thread-locked file cache will corrupt under multiple uvicorn workers. Each worker process has its own in-memory cache and file lock that doesn't synchronize across processes.

### E.2 Caching
- Decision cache (src/decision/) reduces LLM costs
- No query-level or response-level HTTP caching
- No CDN or edge caching

### E.3 Single Points of Failure
- Pipeline runs are synchronous (run_spine_once blocks)
- Database dependency on single PostgreSQL instance
- LLM API calls are synchronous (blocks the event loop during API calls)
- The `spine_api/persistence.py` has `tripstore_engine` as a module-level global

### E.4 Concurrency Model
- uvicorn with 1+ workers
- SQLAlchemy async with asyncpg
- Persistence uses threading.Lock for file access (not multiprocessing-safe)
- LLM usage guard is Redis-backed (good for multi-worker)

---

## F. Security Architecture

### F.1 Authentication
- JWT-based with Bearer token + cookie fallback
- AuthMiddleware catches all routes except PUBLIC_PATHS and PUBLIC_PREFIXES
- get_current_user / get_current_membership / get_current_agency dependencies

**Strengths:**
- Two-layer auth (middleware + per-route dependency)
- Cookie + Bearer token support
- SQLAlchemy-based user lookup

**Weaknesses:**
- No rate limiting on auth endpoints
- No MFA
- Session revocation not implemented (JWT until expiry)
- No refresh token rotation

### F.2 Data Privacy
- PrivacyGuard blocks real PII from persisting in dogfood mode
- Encryption available via Fernet (symmetric)
- Hardcoded dev key documented as non-production

**Weaknesses:**
- Encryption is used selectively (persistence layer) but not universally
- Privacy guard relies on fixture ID matching — heuristic, not absolute
- The try/except/ast.parse fallback for fixture detection is fragile

### F.3 Data Flow Security
- Traveler-safe output structurally excludes raw packet data
- Leakage detection (safety.py) enforced by 38+ tests
- Internal bundle has full access (for operators only)

---

## G. Data Flow (End-to-End)

```
1. HTTP POST /run (from Next.js BFF)
       |
2. run_spine_once() begins
       |
3. NB01: SourceEnvelope -> Normalizer -> ExtractionPipeline
       |     Extracts: destinations, dates, party, budget, purpose
       |     Output: CanonicalPacket with Slot values + EvidenceRef provenance
       |
4. Validate packet (validate_packet)
       |     Checks: required fields, structural validity
       |     Output: PacketValidationReport
       |
5. NB02: run_gap_and_decision
       |     Detects: ambiguity, gaps, missing info
       |     Scores: confidence (0-100)
       |     Uses: hybrid engine (cache -> rules -> LLM fallback)
       |     Output: DecisionResult + AutonomyOutcome
       |
6. Suitability assessment
       |     Extracts participants from packet
       |     Runs Tier 1 + Tier 2 scoring
       |     Output: risk flags
       |
7. Fee calculation
       |     Calculates trip fees based on packet data
       |
8. NB03: Strategy + Prompt build
       |     Traveler-safe bundle (sanitized)
       |     Internal bundle (full data)
       |
9. Frontier orchestration
       |     Ghost Concierge, emotional monitoring, intelligence pool
       |
10. Safety check (leakage detection)
        |
11. HTTP response (SpineRunResponse)
```

---

## H. Recommendations

### H.1 HIGH: Extract route handlers from server.py
**Problem:** server.py is 2644 lines with all endpoint handlers inline.
**Recommendation:** Move /run, /override, /trips, /dashboard, /health handlers into separate router modules under spine_api/routers/. Keep only app setup, middleware, and lifecycle in server.py.
**Tradeoff:** More files, but each handler is independently testable and navigable.

### H.2 HIGH: Single persistence backend decision
**Problem:** Two persistence backends (JSON files + SQLAlchemy) without clear separation.
**Recommendation:** Pick one. If SQLAlchemy is the future path, migrate TripStore and AuditStore from JSON files to PostgreSQL. De-duplicate the engine creation (there are TWO async engines: one in core/database.py, one in persistence.py).
**Tradeoff:** Migration effort upfront, but eliminates a known inconsistency and the process-unsafe file locking.

### H.3 MEDIUM: Decompose src/intake/decision.py
**Problem:** 2240 lines with gap detection, confidence scoring, inference, budget, and hybrid engine integration.
**Recommendation:** Split into focused modules: gap_detection.py, confidence_scoring.py, budget_feasibility.py, and keep the orchestration in decision.py.
**Tradeoff:** More files, but each is independently testable and the hybrid engine integration (which has its own cache + rules + LLM flow) is cleanly separated.

### H.4 MEDIUM: Fix cross-boundary import direction
**Problem:** src/analytics imports from spine_api.persistence.
**Recommendation:** Extract the audit/timeline abstractions into src/ (either src/analytics or a new shared module) so spine_api imports from src, not the reverse.
**Tradeoff:** Requires extracting interfaces, but removes the fragile try/except import pattern.

### H.5 MEDIUM: Process-safe decision cache
**Problem:** Current cache uses threading.Lock — not safe under multiple uvicorn workers.
**Recommendation:** Either use Redis (already a dependency via usage_guard) or a database-backed cache. Avoid file-based caching in multi-process deployments.
**Tradeoff:** Redis adds operational overhead but is already a dependency.

### H.6 MEDIUM: Clean up empty shell packages
**Problem:** 6 packages exist as empty shells (pipelines, adapters, config, schemas, utils, llm/agents).
**Recommendation:** Either populate them with actual content or remove them. Empty packages create misleading assumptions about the architecture.
**Tradeoff:** Removing is easier, but some may represent planned work.

### H.7 LOW: Resolve module name collision
**Problem:** Two `decision` modules (src/intake/decision.py and src/decision/).
**Recommendation:** Rename src/intake/decision.py to src/intake/gap_decision.py or similar, or make src/intake/decision.py delegate entirely to src/decision/ and deprecate the inline logic.
**Tradeoff:** Refactoring cost vs. ongoing developer confusion.

### H.8 LOW: Hardcoded encryption key
**Problem:** encryption.py has a static Fernet key as fallback.
**Recommendation:** For beta/production, ensure DATA_PRIVACY_MODE enforces ENCRYPTION_KEY requirement (it already does for production mode, but beta mode should also warn).
**Tradeoff:** Slightly stricter startup requirements for a documented edge case.

---

## I. Summary Statistics

| Metric | Value |
|--------|-------|
| Python source files | ~70 |
| Lines of code (src/) | ~12,000 (estimated) |
| Lines of code (spine_api/) | ~6,500 (estimated) |
| Test files | 63 |
| Empty shell packages | 6 |
| God files (>1000 lines) | 3 (server.py: 2644, persistence.py: 1115, intake/decision.py: 2240) |
| Cross-boundary violations | 2 (analytics -> spine_api) |
| Persistence backends | 2 (JSON files + SQLAlchemy) |
| LLM backends | 3 (Gemini, OpenAI, Local) |
| Run lifecycle files | 3 (run_events, run_ledger, run_state) |
