# Improve Architecture Findings — Waypoint OS

Generated: 2026-04-28
Scope: src/intake/, src/decision/, src/suitability/, src/analytics/, spine_api/
Approach: Module deepening (per "A Philosophy of Software Design" — deep modules have small interfaces hiding large complexity; shallow modules have wide interfaces hiding little)

---

## 1. Intake Orchestration Megamodule

**Module cluster:** `src/intake/orchestration.py` + 12 direct imports from `src/intake/`

**Why they're coupled:**
- `orchestration.py` is the single spine entrypoint but it directly imports and
  sequentially chains: `ExtractionPipeline`, `validate_packet`, `run_gap_and_decision`,
  `build_session_strategy`, `build_internal_bundle`, `build_traveler_safe_bundle`,
  `sanitize_for_traveler`, `check_no_leakage`, `NB01CompletionGate`, `NB02JudgmentGate`,
  `calculate_trip_fees`, `assess_activity_suitability`, `run_frontier_orchestration`.
- `SpineResult` has 12+ fields, each a different type from a different sub-module.
- `run_spine_once()` is a 300-line sequential function that manually stitches
  phases together, including gate-check branching (NB01 ESCALATE/DEGRADE),
  suitability flag injection, autonomy outcome recording, frontier orchestration,
  and fee calculation — all inline.
- Understanding the spine pipeline requires reading orchestration.py end-to-end,
  then bouncing to every imported module to understand each phase's contract.

**What a deepened interface could look like:**
- Each phase (extraction, validation, decision, suitability, strategy, safety, fees, frontier)
  should be a callable `Phase` with a uniform interface: `def run(packet, context) -> PhaseResult`.
- `run_spine_once` becomes a loop over a phase list, with gate checks as composable
  middleware/interceptors rather than inline if/return blocks.
- `SpineResult` becomes a thin wrapper over a `PipelineContext` accumulator — each
  phase writes to the context rather than requiring the orchestrator to manually wire
  12 output variables.
- The pipeline definition becomes declarative (list of phases + gate positions),
  not imperative.

**Test impact:**
- Currently, testing any single phase in isolation requires mocking the entire
  12-import chain or wiring up full `run_spine_once`. With a `Phase` protocol,
  each phase is testable with just a `CanonicalPacket` + `PipelineContext`.
- Gate logic (NB01 ESCALATE/DEGRADE) tests currently require full spine fixture
  setup; they could be tested as standalone interceptors.

---

## 2. CanonicalPacket as a God Object

**Module cluster:** `src/intake/packet_models.py` (CanonicalPacket + 13 dependent dataclasses) → consumed by 15+ files

**Why they're coupled:**
- `CanonicalPacket` contains 15+ top-level fields spanning 5 domains: extraction
  (facts, derived_signals, hypotheses), lifecycle (LifecycleInfo), suitability
  (suitability_flags), audit (events, event_cursor), and commercial (feedback, raw_note).
- Every module in the system depends on `CanonicalPacket` — extractors, validation,
  decision, strategy, safety, suitability, fees, analytics, frontier orchestrator,
  checker agent, negotiation engine.
- `packet_models.py` also defines `AuthorityLevel`, `Slot`, `EvidenceRef`,
  `SourceEnvelope`, `SuitabilityFlag`, `SubGroup`, etc. — effectively the entire
  type system for the application.
- SuitabilityFlag is defined in `packet_models.py` but consumed/created primarily
  in `src/suitability/integration.py` — this cross-domain type ownership creates
  a reverse dependency where the suitability package imports from intake.

**What a deepened interface could look like:**
- Split `packet_models.py` into domain-focused type modules:
  - `intake/types.py` — CanonicalPacket core (facts/signals/hypotheses), Slot, AuthorityLevel
  - `suitability/types.py` — SuitabilityFlag, SuitabilityContext (already exists in models.py)
  - `lifecycle/types.py` — LifecycleInfo
- `CanonicalPacket` should expose accessor methods rather than raw `facts` dict:
  `packet.get_field("destination_candidates")` instead of requiring every consumer
  to know whether a field lives in `facts` or `derived_signals`.
- SuitabilityFlag should live in src/suitability/ and be imported by packet_models
  (not the other way around), or the packet should just hold `List[Any]` for
  suitability_flags with contract enforced by Protocol.

**Test impact:**
- Currently, creating a test CanonicalPacket requires importing and wiring
  13 dataclasses. Splitting types means test files import only the domain they need.
- Suitability tests could construct SuitabilityFlag without importing the entire
  intake type hierarchy.

---

## 3. DecisionResult Name Collision / Dual Type System

**Module cluster:** `src/intake/decision.py::DecisionResult` vs `src/decision/hybrid_engine.py::DecisionResult`

**Why they're coupled:**
- Two different `DecisionResult` classes exist with completely different shapes:
  - `intake.decision.DecisionResult`: 15+ fields (packet_id, decision_state,
    hard_blockers, soft_blockers, ambiguities, confidence, risk_flags, commercial_decision, etc.)
  - `decision.hybrid_engine.DecisionResult`: 8 fields (decision dict, source,
    confidence, cache_hit, rule_hit, llm_used, cost_inr)
- `intake/decision.py` lazily imports `src/decision/hybrid_engine` and translates
  hybrid engine results into risk_flags on the intake DecisionResult — a manual
  mapping layer inside `_generate_risk_flags_with_hybrid_engine()`.
- Understanding the decision pipeline requires reading both files and understanding
  how the hybrid engine's `DecisionResult` gets mapped into the intake's
  `DecisionResult.risk_flags` list.

**What a deepened interface could look like:**
- Unify into a single `DecisionResult` type or make the mapping explicit via an
  adapter function `hybrid_result_to_risk_flags(HybridDecisionResult) -> List[RiskFlag]`.
- The hybrid engine's `DecisionResult` should be renamed to `HybridEngineResult`
  to eliminate the namespace collision.
- The intake DecisionResult's `risk_flags: List[Dict]` should be typed as
  `List[RiskFlag]` with a proper dataclass rather than raw dicts.

**Test impact:**
- Currently, tests that exercise the decision path must understand both
  DecisionResult shapes. Renaming eliminates confusion.
- The mapping function becomes independently testable without running the
  full pipeline.

---

## 4. Frontier Orchestration Shallow Module Cluster

**Module cluster:** `src/intake/frontier_orchestrator.py` + `checker_agent.py` + `negotiation_engine.py` + `federated_intelligence.py` + `specialty_knowledge.py`

**Why they're coupled:**
- All 5 modules are inside `src/intake/` but represent conceptually separate domains:
  sentiment, redundancy checking, negotiation, threat intelligence, specialty knowledge.
- `frontier_orchestrator.py` is only 127 lines and is a simple linear caller of
  the other 4 services — it's a shallow orchestrator that adds no domain logic.
- `checker_agent.py` (76 lines), `negotiation_engine.py` (102 lines),
  `federated_intelligence.py` (69 lines), `specialty_knowledge.py` (63 lines)
  are each shallow modules with simple interfaces but almost no complexity —
  each is essentially a single function wrapped in a class.
- All 4 services take `(CanonicalPacket, DecisionResult)` and return simple
  result types. They're not deep — the interface is nearly as wide as the
  implementation.

**What a deepened interface could look like:**
- Move to `src/frontier/` as a proper sub-package with a single entry point:
  `run_frontier_analysis(packet, decision, settings) -> FrontierResult`.
- Combine the 5 files into 2-3 files: `frontier/orchestrator.py` (entry point +
  sentiment + checker), `frontier/intelligence.py` (federated + specialty),
  `frontier/negotiation.py` (negotiation engine).
- The internal services don't need to be top-level modules — they can be
  private functions within their files.

**Test impact:**
- Currently, testing frontier features requires importing 5 separate modules.
- With a single `run_frontier_analysis` entry point, integration tests just
  call one function. Unit tests for individual services remain possible via
  the internal functions.

---

## 5. Analytics ↔ Persistence ↔ Review Cross-Layer Coupling

**Module cluster:** `src/analytics/review.py` + `src/analytics/engine.py` + `src/analytics/policy_rules.py` + `src/services/dashboard_aggregator.py` + `spine_api/persistence.py`

**Why they're coupled:**
- `analytics/review.py` directly imports `spine_api.persistence.AuditStore` and
  `TripStore` — the analytics domain layer reaches across to the API persistence layer.
- `analytics/engine.py` imports from `analytics/policy_rules.py` and
  `analytics/models.py`, then `dashboard_aggregator.py` imports from
  `spine_api/persistence` — the aggregation layer is entangled with the
  storage layer.
- `analytics/metrics.py` imports from `spine_api.persistence.TripStore` inside
  its `compute_alerts()` function (late import to avoid circular dependencies).
- The review state machine (`process_review_action`) directly writes to `TripStore`
  and `AuditStore`, mixing business logic with I/O.
- Understanding the review flow requires reading: review.py → persistence.py →
  policy_rules.py → engine.py → analytics/models.py.

**What a deepened interface could look like:**
- Introduce a `TripRepository` protocol with `get_trip()`, `update_trip()`,
  `list_trips()` methods. Both `review.py` and `dashboard_aggregator.py` receive
  a repository instance rather than importing the concrete `TripStore`.
- Similarly, introduce an `AuditLogger` protocol instead of direct `AuditStore`
  imports.
- `analytics/engine.py::process_trip_analytics()` should receive a trip dict
  (not access the store); the caller (API router) is responsible for fetching
  and persisting.
- `policy_rules.py` is already pure logic — it's the best deep module in this
  cluster. Keep it as-is.

**Test impact:**
- Currently, testing `process_review_action` requires a live `TripStore` with
  files on disk. With a `TripRepository` protocol, tests inject an in-memory
  dict-based store.
- `compute_alerts()` currently has a side-effect import of `TripStore.update_trip()`
  inside SLA breach detection — this makes it untestable in isolation. The
  side-effect should be lifted to the caller.

---

## 6. Suitability ↔ Packet Bidirectional Dependency

**Module cluster:** `src/suitability/integration.py` + `src/suitability/scoring.py` + `src/intake/packet_models.py` + `src/intake/orchestration.py`

**Why they're coupled:**
- `suitability/integration.py::assess_activity_suitability()` does a late import
  of `SuitabilityFlag` from `src/intake/packet_models.py` — the suitability
  package depends on the intake package for its output type.
- Meanwhile, `orchestration.py` imports `assess_activity_suitability` from the
  suitability package and injects results into `packet.suitability_flags`.
- The suitability module must understand the internal structure of CanonicalPacket
  (especially `packet.facts["party_composition"]`, `packet.facts["child_ages"]`,
  `packet.facts["destination_candidates"]`) to extract participants.
- `integration.py::extract_participants_from_packet()` is 50 lines of conditional
  Slot-value unwrapping — this is intake-domain knowledge that doesn't belong
  in the suitability package.

**What a deepened interface could look like:**
- `assess_activity_suitability()` should accept `List[ParticipantRef]` and
  `SuitabilityContext` (which it mostly already does internally), not a raw
  `CanonicalPacket`. The participant extraction should happen in the intake
  layer, not in the suitability layer.
- `SuitabilityFlag` should move to `src/suitability/models.py` (or the
  analytics models) since it's consumed there. The intake packet can just
  hold `List[Any]` typed as a Protocol.
- This eliminates the bidirectional dependency: suitability no longer imports
  from intake.

**Test impact:**
- Suitability tests currently need to construct full CanonicalPacket objects
  with proper Slot wrapping just to test scoring. With `ParticipantRef` as
  input, tests just create `ParticipantRef(label="elderly")` directly.
- The participant extraction logic can be tested independently in the intake
  layer.

---

## 7. Fee Calculation Defensively Parses Unstructured Dicts

**Module cluster:** `src/fees/calculation.py` + `src/intake/orchestration.py`

**Why they're coupled:**
- `calculate_trip_fees()` accepts `packet: Any` and `decision: Any` — it has
  no type contract and must defensively handle both dict and object inputs
  via `_extract_slot_value()` and `_normalize_risk_list()`.
- The function extracts `party_size` and `duration_nights` from the packet by
  reaching deep into `packet.facts["party_size"].value` — this is intake-domain
  knowledge embedded in the fees module.
- Risk flags come from `decision.risk_flags` which is a `List[Dict]` —
  untyped data that the fee calculator must parse.

**What a deepened interface could look like:**
- `calculate_trip_fees()` should accept a typed `FeeInput` dataclass with:
  `party_size: int`, `duration_nights: int`, `risks: List[RiskFlag]`.
- The orchestration layer extracts and constructs `FeeInput` from the packet
  and decision — the fees module never touches `CanonicalPacket` or
  `DecisionResult` directly.
- `RiskFlag` becomes a proper dataclass (not a raw dict) with `flag`, `severity`,
  `message` fields.

**Test impact:**
- Currently, fee tests must construct either dicts or full object graphs with
  Slot wrappers. With `FeeInput`, tests just pass `FeeInput(party_size=4,
  duration_nights=5, risks=[RiskFlag(flag="x", severity="high", message="y")])`.
- No more `_extract_slot_value` or `_normalize_risk_list` in production —
  those become unnecessary.

---

## 8. Analytics Engine Dict-Oriented Processing vs. Typed Models

**Module cluster:** `src/analytics/engine.py` + `src/analytics/metrics.py`

**Why they're coupled:**
- `process_trip_analytics()` in `engine.py` accepts a raw `trip: dict` and digs
  through it with `.get("extracted", {}).get("budget", {}).get("value", 0)` —
  deep dict chains with no type safety.
- The same "extracted/packet/budget/value" path is duplicated in `metrics.py`'s
  `compute_revenue_metrics()` and `compute_team_metrics()`.
- `analytics/engine.py` computes `quality_score`, `margin_pct`,
  `requires_review`, etc. — these are already modeled in `AnalyticsPayload`,
  but the engine produces them from unstructured dicts, then constructs the
  Pydantic model at the end.
- The output type (`AnalyticsPayload`) is well-defined, but the input contract
  is implicit: callers must provide a dict with specific nested keys.

**What a deepened interface could look like:**
- Define a `TripAnalyticsInput` dataclass/Pydantic model that formalizes the
  expected dict shape: `extracted: Optional[dict]`, `decision: Optional[dict]`,
  `safety: Optional[dict]`, `analytics: Optional[dict]`.
- Alternatively, `process_trip_analytics()` should accept the typed
  `SpineResult` or `CanonicalPacket` + `DecisionResult` objects directly
  instead of raw dicts.
- Extract the repeated `.get("extracted", {}).get("budget", {}).get("value", 0)`
  patterns into a shared `TripDataAccess` helper.

**Test impact:**
- Currently, analytics tests must construct carefully-shaped dicts matching
  the implicit contract. A typed input model makes the contract explicit and
  catches mismatches at construction time.
- Revenue/margin calculation becomes testable without the trip dict nesting.

---

## 9. Agency Settings as Cross-Cutting Cross-Package Dependency

**Module cluster:** `src/intake/config/agency_settings.py` → consumed by `orchestration.py`, `decision.py`, `gates.py`, `strategy.py`, and frontier orchestrator

**Why they're coupled:**
- `AgencySettings` is a large dataclass (30+ fields) spanning profile, operational,
  autonomy, and LLM settings — it's passed through the entire pipeline.
- However, most phases only use a small slice: gates.py uses `autonomy` only;
  strategy.py uses `brand_tone` and `autonomy`; frontier uses `autonomy.checker_audit_threshold`;
  decision.py uses nothing directly (it receives it from orchestration.py).
- The `AgencySettingsStore` uses direct SQLite access (`sqlite3.connect`) with
  no repository abstraction — it's not injectable or mockable.
- The settings module lives in `src/intake/config/` but is consumed by `src/decision/`
  and `src/suitability/` — creating a dependency from decision/suitability back
  into intake.

**What a deepened interface could look like:**
- Split `AgencySettings` into focused protocols/traits:
  - `AutonomyPolicy` (used by gates + strategy) — already partially
    extracted as `AgencyAutonomyPolicy`
  - `BrandConfig` (used by strategy)
  - `OperationalConfig` (used by fees, analytics)
- Each phase declares which config trait it needs via its function signature,
  not the monolithic `AgencySettings`.
- `AgencySettingsStore` should implement a `SettingsRepository` protocol
  for injectability.

**Test impact:**
- Currently, testing the NB02 gate requires constructing the full `AgencySettings`
  even though only `autonomy` is used. With `AutonomyPolicy` as a Protocol,
  tests just provide the 5-field autonomy dict.
- Settings persistence tests are coupled to SQLite file paths; a repository
  protocol enables in-memory testing.

---

## 10. Spine API Persistence Layer Dual-Backend Complexity

**Module cluster:** `spine_api/persistence.py` (TripStore + AuditStore + FileTripStore + SQLTripStore + file_lock) → consumed by analytics/review.py, analytics/metrics.py, services/dashboard_aggregator.py, analytics/logger.py

**Why they're coupled:**
- `persistence.py` is 1115 lines containing: `FileTripStore`, `SQLTripStore`,
  `TripStore` (facade), `AuditStore`, plus file locking, JSON serialization,
  PII encryption, and cross-process lock utilities.
- The `TripStore` facade switches between file and SQL backends at runtime
  via `TRIPSTORE_BACKEND` env var — but the two backends have different
  async/sync contracts (`SQLTripStore` is async, `FileTripStore` is sync),
  requiring the `_run_async_blocking()` bridge that raises `RuntimeError`
  if called from an event loop.
- Consumers (review.py, metrics.py, dashboard_aggregator.py) use the sync
  `TripStore.get_trip()` / `TripStore.update_trip()` directly, which breaks
  under async contexts.
- The file-locking mechanism (directory-based, with PID staleness detection)
  is 70 lines of complexity that's irrelevant to the SQL backend.
- Analytics metrics reaches into `spine_api.persistence.TripStore` for
  SLA breach side-effects — a layering violation.

**What a deepened interface could look like:**
- Split into 3 files:
  - `persistence/trip_store.py` — the `TripRepository` Protocol + `TripStore`
    facade (choose backend)
  - `persistence/file_store.py` — `FileTripStore` + file locking
  - `persistence/sql_store.py` — `SQLTripStore` + encryption
  - `persistence/audit_store.py` — `AuditStore` + `AuditLogger` protocol
- Define a `TripRepository` Protocol (async) that both backends implement.
  The sync `TripStore` becomes a thin async wrapper, not a synchronous shim
  that crashes in event loops.
- Analytics and review modules receive a `TripRepository` injection, not
  import the concrete `TripStore` class.

**Test impact:**
- Currently, integration tests are forced to use `disable_audit_logging`
  fixture because `AuditStore.log_event()` writes to disk and causes file
  lock contention. With an `AuditLogger` protocol, tests inject a no-op logger.
- SQL store tests currently require a real PostgreSQL; with the Protocol,
  an in-memory store can be used.
- File lock timeout tests become isolated in `file_store.py` instead of
  affecting the entire persistence layer.

---

## Summary: Priority Order

| # | Cluster | Impact | Effort |
|---|---------|--------|--------|
| 6 | Suitability ↔ Packet bidirectional dependency | High: eliminates circular import, simplifies testing | Low: move SuitabilityFlag, change one function signature |
| 3 | DecisionResult dual type system | High: eliminates name collision, clarifies mapping | Low: rename one class, extract adapter function |
| 7 | Fee calculation untyped inputs | Medium: makes fee logic independently testable | Low: introduce FeeInput dataclass |
| 2 | CanonicalPacket god object | High: reduces import burden, simplifies test setup | Medium: split type modules, add accessors |
| 5 | Analytics ↔ Persistence cross-layer coupling | High: enables pure-logic testing of review/policy | Medium: define Repository+Logger protocols, inject |
| 1 | Intake orchestration megamodule | High: makes each phase independently testable | High: refactor to Phase protocol + PipelineContext |
| 9 | AgencySettings cross-cutting dependency | Medium: simplifies test setup for gates/strategy | Medium: extract focused protocols |
| 10 | Persistence dual-backend complexity | Medium: eliminates sync/async bridge crashes | High: split files, define async Protocol |
| 4 | Frontier orchestration shallow cluster | Low: 5 files → 2-3, minor cohesion win | Low: move and merge files |
| 8 | Analytics dict-oriented processing | Low: improves type safety, catches bugs earlier | Medium: define typed input model |