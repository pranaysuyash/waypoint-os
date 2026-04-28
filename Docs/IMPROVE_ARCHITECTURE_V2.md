# Improve Architecture v2 — Waypoint OS

**Review Date:** 2026-04-28
**Method:** improve-codebase-architecture skill (exploration -> candidate presentation)
**Documents preserved (no overwrite):** ARCHITECT_REVIEW_V2.md, COMPREHENSIVE_REVIEW_V2.md, IMPROVE_ARCHITECTURE_FINDINGS.md, PRODUCTION_AUDIT_FINDINGS.md, ARCHITECT_REVIEW_FINDINGS.md, COMPREHENSIVE_REVIEW_FINDINGS.md, PRODUCTION_AUDIT_FINDINGS.md

---

## Step 1: Exploration Results

### Module Size Distribution
```
src/intake:        19 files,   8,902 lines  (47.9%)
src/decision:     16 files,   3,629 lines  (19.5%)
src/llm:           8 files,   2,340 lines  (12.6%)
src/analytics:     7 files,   1,539 lines  (8.3%)
src/suitability:   7 files,   1,197 lines  (6.4%)
spine_api/models:  4 files,   448 lines     (2.4%)
spine_api/routers: 4 files,   454 lines     (2.4%)
                   ---       -------
        Total:    65 files   18,509 lines
```

### Key Friction Points Identified

**1. CanonicalPacket is imported by 21 files** (across intake, decision, suitability, and their subpackages). This is the single most coupled type in the system. Every change to CanonicalPacket requires verifying 21 consumers.

**2. server.py has 77 function definitions** spanning: health, seeding, pipeline execution, run management, trip CRUD, dashboard aggregate, analytics, reviews, agency settings, override, and timeline. This is 7+ distinct concerns in one file.

**3. Cross-boundary imports identified in 5 locations:**
- src/analytics/metrics.py imports from spine_api.persistence (lazy)
- src/analytics/logger.py imports from spine_api.persistence (conditional)
- src/analytics/review.py imports from spine_api.persistence
- src/services/dashboard_aggregator.py imports from spine_api.persistence
- src/intake/decision.py imports from src/decision/rules

**4. AgencySettings is imported by 6 files** across the pipeline: server.py, agency_settings.py, decision.py, gates.py, orchestration.py, strategy.py. A 30+ field god-config passed through the entire pipeline.

---

## Step 2: Deepening Opportunity Candidates

Below are the candidates for module deepening, ordered by estimated impact.

---

### Candidate A: Intake Orchestration Megamodule

**Cluster:** `src/intake/orchestration.py` + 12 directly imported sub-modules

**Why they're coupled:**
- `run_spine_once()` is a 300-line function that manually wires ExtractionPipeline, validate_packet, run_gap_and_decision, build_session_strategy, build_internal_bundle, build_traveler_safe_bundle, sanitize_for_traveler, check_no_leakage, NB01CompletionGate, NB02JudgmentGate, calculate_trip_fees, assess_activity_suitability, run_frontier_orchestration — all sequentially, inline.
- `SpineResult` has 12+ fields, each from a different sub-module.
- Understanding the pipeline requires reading orchestration.py end-to-end, then bouncing to each imported module.

**Dependency category:** Orchestration (tight call-sequence coupling)

**Test impact:** Currently, testing a phase change (e.g., adding a new gate check) requires either mocking the entire run_spine_once or running the full pipeline. With deepened interfaces, each Phase would be independently testable — and the pipeline itself becomes a testable composition.

---

### Candidate B: CanonicalPacket God Object

**Cluster:** `src/intake/packet_models.py` (483 lines) consumed by 21 files across src/decision/, src/intake/, src/suitability/

**Why they're coupled:**
- packet_models.py defines 20+ dataclasses: CanonicalPacket, Slot, EvidenceRef, Ambiguity, SourceEnvelope, SubGroup, OwnerConstraint, LifecycleInfo, UnknownField, SuitabilityFlag, and more.
- CanonicalPacket has 15+ fields spanning extraction results (facts, slots), lifecycle (lifecycle_info), safety (suitability_flags), and operational metadata (operating_mode).
- Consumers reach into `packet.facts.get("field_name")` — raw string-keyed access without type safety.

**Dependency category:** Data coupling (shared type with too many responsibilities)

**Test impact:** 21 files need updating if CanonicalPacket changes. Tests for any consumer require constructing a full CanonicalPacket even when they only need 2-3 fields.

---

### Candidate C: DecisionResult Dual Type System

**Cluster:** `src/intake/decision.py:DecisionResult` + `src/decision/hybrid_engine.py:DecisionResult`

**Why they're coupled:**
- Two different DecisionResult dataclasses with different fields but the same name.
- `src/intake/decision.py` imports from `src/decision/rules` at line 502.
- The intake DecisionResult has fields like decision_state, commercial_decision, confidence. The hybrid engine DecisionResult has decision, source, confidence, cache_hit, cost_inr.

**Dependency category:** Name collision with shared semantics

**Test impact:** When testing src/decision/hybrid_engine.py, you get the hybrid engine's DecisionResult. When testing src/intake/decision.py, you get the intake's DecisionResult. Developers and tests must constantly disambiguate which type they're working with.

---

### Candidate D: Server.py Megamodule

**Cluster:** `spine_api/server.py` (2,644 lines) — all route handlers, pipeline orchestration, seeding, background tasks

**Why they're coupled:**
- 77 function definitions across 7+ distinct concerns: health, seeding, pipeline execution, run management, trip CRUD, dashboard, analytics, reviews, settings, override, timeline.
- 13 unused imports at the top of the file (F401 violations).
- 28 import-order violations (E402) where imports are scattered through the file after code.

**Dependency category:** Blast radius coupling (everything touches everything)

**Test impact:** Testing any single route handler requires understanding the entire file. Route handlers can't be tested independently without running the full server.

---

### Candidate E: Analytics Cross-Layer Coupling

**Cluster:** `src/analytics/logger.py`, `src/analytics/review.py`, `src/analytics/metrics.py` + `spine_api/persistence.py`

**Why they're coupled:**
- 5 imports from spine_api.persistence into src/ modules (wrong direction).
- `logger.py` wraps the import in `try/except ModuleNotFoundError` — explicit recognition of fragility.
- `metrics.py` uses lazy imports at line 369 and 376 for TripStore.

**Dependency category:** Cross-boundary dependency (violates layer direction)

**Test impact:** Testing analytics logic requires either a running persistence layer or mocking AuditStore/TripStore at the import site. With a protocol/interface, tests can inject mock repositories.

---

### Candidate F: AgencySettings God-Config

**Cluster:** AgencySettings (30+ fields) passed through 6 files across the pipeline

**Why they're coupled:**
- `src/intake/config/agency_settings.py` defines AgencySettings with fields across: branding, operational settings, autonomy policy, margin configuration, and more.
- Imported by: server.py, decision.py, gates.py, orchestration.py, strategy.py.
- Each consumer only needs a subset of the fields but receives everything.

**Dependency category:** Config coupling (everything depends on everything)

**Test impact:** Tests for any consumer must construct a full AgencySettings object even when they only need 2-3 fields.

---

### Candidate G: Parser/Searcher Shallow Cluster

**Cluster:** `src/intake/`, 19 files but 8,902 lines — dominated by decision.py (2,240)

**Why they're coupled:**
- 4 empty packages (pipelines, adapters, config, schemas, utils) suggest planned separation that never materialized.
- The frontier/ features (orchestrator, checker, intelligence, negotiation) are 5 files totaling 327 lines — each so thin they're shallow on their own.

**Dependency category:** Boundary fragmentation (too many thin files for one concept)

**Test impact:** Understanding how frontier orchestration works requires reading 5 files. Each is ~65 lines average — the interface IS the implementation.

---

**Which of these candidates would you like me to explore further?**
