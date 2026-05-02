# ⚠️ ARCHIVED — Superseded by Baseline Audit Index

**Date**: 2026-05-02 | **Status**: ARCHIVED

This document has been split into focused baseline docs. The content below is preserved for history but is no longer the authoritative source.

**→ See `BASELINE_AUDIT_INDEX_2026-05-02.md` for the canonical index of all baseline docs.**

## Replacement Docs

| This doc's section | Now in |
|-------------------|--------|
| Component ratings (Part I) | `BASELINE_AUDIT_CODEBASE_2026-05-02.md` |
| Independent assessment (Part II) | `BASELINE_INDEPENDENT_ASSESSMENT_2026-05-02.md` |
| Feature completeness | `BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` |
| Documentation health (Part III) | `BASELINE_DOCUMENTATION_HEALTH_2026-05-02.md` |
| Action plan (Part IV) | `BASELINE_MASTER_ACTION_PLAN_2026-05-02.md` |

---

*Historical content follows below. Do not reference for current state.*

---

# Architecture Baseline Audit — First-Principles Deep Dive

**Date**: 2026-05-02
**Purpose**: Apply first-principles thinking to every component previously marked "green" in the pipeline breakdown. Verify architectural soundness, scalability, future-readiness, and identify hidden debt.

**Source Documents Applied**:
- `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` (irreducible primitives, build sequence)
- `V02_GOVERNING_PRINCIPLES.md` (layer ownership, deterministic-first, two-axis classification)
- `MASTER_GAP_REGISTER_2026-04-16.md` (17 gap areas)
- `THESIS_TO_IMPLEMENTATION_ALIGNMENT_ANALYSIS_2026-04-16.md`
- `STATUS_ASSESSMENT_2026-04-21.md`
- `D1_D4_D6_WAS_IS_SHOULD_2026-04-21.md`

**Code Inspected**:
| Module | Lines | Previously Rated |
|--------|-------|-----------------|
| `src/intake/packet_models.py` | 483 | ✅ Green |
| `src/intake/gates.py` | 239 | ✅ Green |
| `src/intake/validation.py` | 258 | ✅ Green |
| `src/intake/extractors.py` | 1,808 | ✅ Green |
| `src/intake/decision.py` | 2,240 | ✅ Green |
| `src/intake/strategy.py` | 1,004 | ✅ Green |
| `src/intake/safety.py` | 545 | ✅ Green |
| `src/intake/orchestration.py` | 854 | ✅ Green |
| `src/decision/hybrid_engine.py` | 828 | ✅ Green |
| `src/suitability/scoring.py` | 241 | ✅ Green |
| `src/suitability/context_rules.py` | 166 | ✅ Green |
| `src/suitability/integration.py` | 388 | ✅ Green |
| `src/suitability/catalog.py` | 252 | ✅ Green |
| `src/suitability/models.py` | 116 | ✅ Green |
| `src/intake/config/agency_settings.py` | 291 | ✅ Green |
| `spine_api/server.py` | 3,535 | ✅ Green |
| `frontend/src/types/spine.ts` | 314 | ✅ Green |

**Total core pipeline**: ~7,278 LoC (intake + decision/hybrid)
**Total with spine_api**: ~10,813 LoC
**Test files**: 69 (913 collected tests before env errors)

---

## First-Principles Framework

Every component is evaluated against the 7 irreducible primitives from `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md`:

1. **Intent capture** (explicit + inferred) — does the code capture both?
2. **Constraint model** (hard vs soft) — is the separation clean?
3. **Feasibility engine** — can it explain "why feasible / why not"?
4. **Option space construction** — does it generate ranked alternatives?
5. **Trade-off ranking** — are trade-offs explicit and explainable?
6. **Execution packet** (bookable artifacts) — can a human execute without reconstructing context?
7. **State + provenance** (source envelope, confidence, rationale) — is every decision traceable?

Plus the governing meta-principles:
- **Deterministic-first**: Rules before LLM
- **Layer ownership**: Every concern has a single owning layer (NB01-NB06)
- **Two-axis classification**: `decision_state` × `operating_mode`
- **Safety model**: Traveler-safe output structurally excludes internal data

---

## COMPONENT 1: CanonicalPacket & Slot System (`packet_models.py`)

### Architectural Soundness: STRONG (8/10)

**What's Right**:
- `AuthorityLevel` with ordered ranking and `FACT_LEVELS` frozenset — enforces that only high-authority sources can set facts. This is foundational to provenance integrity.
- `Slot` with `evidence_refs`, `derived_from` (lineage), `maturity` tags — every value carries its origin story.
- Strict separation of `facts` / `derived_signals` / `hypotheses` — three distinct containers with different authority requirements.
- `operating_mode` as top-level field — correct per V02. System routing classification, not traveler truth.
- `SubGroup` as structural type — not a loose dict blob. Correct per V02 Rule 5.
- `OwnerConstraint` with explicit `visibility` semantics — `internal_only` vs `traveler_safe_transformable`. Correct per V02 Rule 6.
- `Ambiguity` as first-class type with 7 ambiguity subtypes — not hidden under unknowns.
- `UnknownField` with explicit reason — "not_present_in_source" vs "extraction_failed" vs "intentionally_unknown" creates useful signal.
- `LifecycleInfo` with 16 status states and engagement tracking — comprehensive for retention/commercial decisions.
- All 39+ dataclasses use `slots=True` — verified memory optimization.
- `set_fact()` with merge policy (never overwrite non-empty with empty, merge lists, keep higher confidence) — prevents silent data loss.
- Every mutation goes through `_emit_event()` for audit trail.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `to_dict()` on `CanonicalPacket` uses `asdict()` which is fragile for complex nested types (ContradictionValue, etc.) | Medium | Serialization bugs in edge cases |
| 2 | `events` list in `CanonicalPacket` is in-memory only — grows unbounded, no persistence, no pruning | HIGH | Memory leak in long-running server; events lost on restart |
| 3 | `add_contradiction()` has legacy backward-compat code path (values_legacy, sources_list) that should be cleaned up | Low | Code clarity, maintenance burden |
| 4 | No immutability — the packet is mutated freely throughout the pipeline with no guardrails | HIGH | Hard to reason about state; no "snapshot at time T" for audit |
| 5 | `feedback` field is `Optional[Dict[str, Any]]` — no structure, no contract for what feedback should contain | Medium | D5 override learning needs structured feedback contracts |
| 6 | `decision_state` is `Optional[str]` — should be a Literal type like operating_mode | Medium | Risk of invalid states, typo bugs |
| 7 | `suitability_flags` uses `field(default_factory=list)` — but `SuitabilityFlag` is imported from this same module, creating circular dependency risk | Low | Already works but fragile |
| 8 | No snapshot/versioning mechanism — can't diff "packet at extraction time" vs "packet after operator edits" | HIGH | Blocks revision comparison UX, D5 learning |

### Future-Readiness: ADEQUATE

The model is rich enough to support future states (multi-party, cancellation, emergency, audit). The gaps are in immutability (snapshot support) and structured feedback contracts.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | Add snapshot/clone method — `packet.snapshot()` returns deep copy for audit diffing | 1 day |
| P0 | Wire events to persistent store (AuditStore/Postgres) — not just in-memory list | 2 days |
| P1 | Make `decision_state` a Literal type matching the 5 canonical states | 0.5 day |
| P1 | Add `FeedbackEvent` dataclass with structured contract for D5 | 1 day |
| P1 | Clean up `add_contradiction()` legacy path — remove values_legacy, sources_list | 0.5 day |
| P2 | Migrate `to_dict()` to explicit serialization (not asdict) for safety | 1 day |

---

## COMPONENT 2: Quality Gates (`gates.py`)

### Architectural Soundness: STRONG (9/10)

**What's Right**:
- `AutonomyOutcome` as first-class separation of policy from judgment — the three-layer model (Judgment → Policy → Human Action) from D1 ADR is correctly implemented.
- `raw_verdict` preserved alongside `effective_action` — downstream consumers get both.
- `safety_invariant_applied`, `mode_override_applied`, `warning_override_applied` — full traceability on why the gate made its decision.
- `rule_source` derivation for D5 telemetry — `safety_invariant` vs `mode_override:X` vs `warning_policy` vs `approval_gates:X`.
- `STOP_NEEDS_REVIEW → block` enforced in code (lines 195-201) — not just a doc statement. This is the hard safety invariant from D1.
- `NB02JudgmentGate.evaluate()` does NOT mutate `decision.decision_state` — correct per architecture comment (line 9).
- Clean dataclass design with computed properties (`is_auto`, `is_review`, `is_blocked`).

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | NB01CompletionGate couples to validation module's specific warning code `QUOTE_READY_INCOMPLETE` — hardcoded string dependency | Low | If warning code changes, gate silently breaks |
| 2 | Data density heuristic `len(packet.facts) / 10.0` is arbitrary — doesn't reflect actual data quality | Low | Cosmetic, score not used for critical decisions |
| 3 | `PipelineGate` Protocol exists but is never used for type checking — dead abstraction | Low | Code clarity |
| 4 | No gate for NB03→output transition — NB02 gate is the last one. Output quality is never gated | Medium | Bad strategy or traveler bundle could proceed unchecked |

### Future-Readiness: STRONG

The three-layer autonomy model is exactly right for future adaptive governance (D5 Phase 2). Just needs a gate between NB03 strategy and output delivery.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Add NB03 output quality gate — checks strategy completeness, bundle coherence before delivery | 2 days |
| P2 | Replace hardcoded warning code check with validation module constant | 0.5 day |
| P2 | Remove or implement PipelineGate Protocol properly | 0.5 day |

---

## COMPONENT 3: Validation (`validation.py`)

### Architectural Soundness: ADEQUATE (7/10)

**What's Right**:
- `PacketValidationReport` with typed `ValidationIssue` (severity, code, message, field).
- `LEGACY_FIELD_NAMES` detection — catches v0.1→v0.2 migration issues.
- `DERIVED_ONLY_FIELDS` guards — prevents facts from containing things that should be derived.
- `INTAKE_MINIMUM` vs `QUOTE_READY` split — clean separation of "can save" vs "can quote".

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `INTAKE_MINIMUM` and `QUOTE_READY` are hardcoded lists — should be configurable per agency | Medium | Different agencies have different minimum requirements |
| 2 | `QUOTE_READY` only has 6 fields — this feels too minimal for real-world quoting | Medium | May allow premature quote generation |
| 3 | `NUMERIC_BUDGET_MODES` is referenced but only checked for audit and coordinator_group — what about booking stage? | Low | Gap in numeric budget enforcement |
| 4 | No runtime schema validation against `specs/canonical_packet.schema.json` — code and spec can drift | Medium | The "single source of truth" claim is only partially true |
| 5 | `DISCOVERY_MVB = QUOTE_READY` backward compat alias — confusing, should be removed | Low | Code clarity |

### Future-Readiness: NEEDS WORK

Validation rules should be data-driven and agency-configurable. The current hardcoded approach won't scale to multiple agencies with different requirements.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Load validation thresholds from AgencySettings rather than hardcoding | 2 days |
| P1 | Add schema contract validation step (read specs/ JSON schema, validate packet structure) | 1 day |
| P1 | Expand QUOTE_READY to include date_start, date_end, party_composition, passport_status | 1 day |
| P2 | Remove DISCOVERY_MVB alias | 0.5 day |

---

## COMPONENT 4: Extraction Pipeline (`extractors.py`)

### Architectural Soundness: CONCERNING (5/10)

**What's Right**:
- Geography integration with `is_known_city()`, `is_known_destination()` — correct separation of concerns.
- Stop words, relation words, destination hint verbs — thoughtful noise reduction.
- Month mapping with `@lru_cache` — performance optimization applied.
- `_DESTINATION_RE` with travel-context patterns — avoids false positives.
- Stub signals marked with `maturity="stub"` — honest technical debt marking.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | **1,808 lines in a single file** — this is the most severe architectural problem in the entire codebase | **CRITICAL** | Unmaintainable; every extraction change risks breaking unrelated extraction logic; impossible to test in isolation; onboarding nightmare |
| 2 | All extraction is one monolithic `ExtractionPipeline` — no extraction strategy pattern, no per-domain extractors | **HIGH** | Can't add new extraction domains (WhatsApp formatting, email threads, PDFs) without touching the monolith |
| 3 | No confidence tracking per extraction rule — can't tell which regex produced which extraction or with what confidence | Medium | Can't improve extraction quality systematically |
| 4 | No async support — geography lookups against 590k cities could block | Low | Performance for large inputs |
| 5 | `sourcing_path` stub is dead code — maturity="stub" but still computed on every run | Low | Wasteful, confusing |

### Future-Readiness: **NEEDS MAJOR REFACTOR**

The extraction monolith is the #1 blocker for:
- Adding PDF/URL extraction (audit mode)
- Adding WhatsApp formatting extraction
- Adding voice transcription extraction
- Adding per-language extraction rules (Hindi, Tamil)

**Required Architecture**: Extractors should follow a plugin/registry pattern:
```python
class DateExtractor:
    def extract(self, text: str) -> List[Extraction]:
        ...

class DestinationExtractor:
    def extract(self, text: str) -> List[Extraction]:
        ...

class ExtractionPipeline:
    def __init__(self, extractors: List[BaseExtractor]):
        self.extractors = extractors

    def extract(self, envelopes: List[SourceEnvelope]) -> CanonicalPacket:
        for extractor in self.extractors:
            for envelope in envelopes:
                results = extractor.extract(envelope.content)
                for result in results:
                    packet.set_fact(result.field, result.slot)
```

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | **Split extractors.py into domain-specific modules**: `date_extractor.py`, `destination_extractor.py`, `budget_extractor.py`, `composition_extractor.py`, `preference_extractor.py` | 3-4 days |
| P0 | Define `BaseExtractor` protocol with `extract(text) → List[ExtractionResult]` | 1 day |
| P0 | Add `confidence` field to extraction results from each rule | 1 day |
| P1 | Make extraction pipeline composable (registry of extractors, run in order) | 1 day |
| P1 | Remove dead stub signals from extraction path (sourcing_path) | 0.5 day |

---

## COMPONENT 5: Decision Engine (`decision.py`)

### Architectural Soundness: CONCERNING (4/10)

**What's Right**:
- Hybrid engine integration with feature flag (`USE_HYBRID_DECISION_ENGINE`).
- Risk flag generation covers 4 decision types + budget for booking stage.
- Comprehensive feasibility checks.
- Contradiction detection with structured `ContradictionValue`.
- Follow-up question generation with priority.
- `LifecycleInfo` integration for retention/commercial signals.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | **2,240 lines in a single file** — tied with extractors.py as the most severe architectural problem | **CRITICAL** | Unmaintainable; every decision logic change risks breaking unrelated logic |
| 2 | No clear separation between "gap detection" and "decision making" — these are two separate concerns masquerading as one module | **HIGH** | Can't test gap detection independently from decision logic |
| 3 | Confidence scoring is embedded in decision logic — should be a separate `ConfidenceEngine` | Medium | Can't experiment with different confidence models without touching decision code |
| 4 | Hybrid engine integration is if/else branching — not a strategy pattern | Medium | Hard to add new decision sources (rules, ML models) |
| 5 | `DecisionResult` in `intake/decision.py` is a DIFFERENT CLASS from `DecisionResult` in `decision/hybrid_engine.py` — naming collision across modules | Medium | Confusion, potential import bugs |
| 6 | `_generate_risk_flags_with_hybrid_engine()` does sequential decision_type iteration — no parallelism for independent checks | Low | Performance, especially with LLM calls |
| 7 | Feasibility explainability is weak — "why feasible / why not" with traceable evidence is a Stage 2 exit criterion that's not met | Medium | Blocks operator trust |

### Future-Readiness: **NEEDS MAJOR REFACTOR**

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | **Split decision.py into**: `gap_detector.py` (what's missing, what conflicts), `feasibility_engine.py` (can this work), `confidence_engine.py` (how sure are we), `decision_router.py` (what do we do) | 3-4 days |
| P1 | Rename hybrid_engine's `DecisionResult` to `HybridDecisionResult` to avoid collision | 0.5 day |
| P1 | Add traceable evidence to feasibility verdicts — "budget of ₹4L is infeasible because: Paris avg hotel ₹12K/night × 10 nights = ₹1.2L, flights ₹80K, activities ₹1.5L... = ₹4.1L minimum" | 2 days |
| P1 | Make hybrid engine integration a proper strategy pattern | 1 day |
| P2 | Add parallel execution for independent risk checks | 1 day |

---

## COMPONENT 6: Hybrid Decision Engine (`hybrid_engine.py`)

### Architectural Soundness: STRONG (8/10)

**What's Right**:
- Clean cache→rules→LLM→default flow — exactly the deterministic-first principle.
- Cost tracking per decision path (₹0 for cache, ₹0 for rules, estimated for LLM).
- Schema templates for each decision type — structured output contracts.
- Default decisions as safe fallbacks — system never returns nothing.
- Telemetry integration for every decision path.
- LLM usage guard integration with cost estimation before calling.
- Health checker integration for LLM failures.
- `register_rule()` with typed signature — extensible rule system.
- `get_metrics()`, `get_cache_stats()`, `get_health_status()`, `get_telemetry_snapshot()` — comprehensive observability surface.
- `create_hybrid_engine()` factory with env var configuration.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | Built-in rules are hardcoded in `_register_builtin_rules()` — 18 rules registered via import-then-register | Medium | Adding a new rule requires code changes, not configuration |
| 2 | LLM prompts are hardcoded strings in `_build_llm_prompt()` — not template files, not versioned separately | Medium | Can't A/B test prompts, can't version prompts independently of code |
| 3 | `_HYBRID_ENGINE_ENABLED` as global module-level check — fragile, not thread-safe | Low | Edge case bugs in multi-worker scenarios |
| 4 | `_hybrid_engine_instance` as module-level global — not thread-safe | Low | Edge case bugs |
| 5 | `DecisionResult` naming collision with `intake/decision.py` (already noted above) | Medium | Confusion |
| 6 | `SCHEMAS` dict only covers 5 decision types — what about new types? | Low | Extensibility |
| 7 | `DEFAULT_DECISIONS` are hardcoded — these should be agency-configurable defaults | Medium | Different agencies have different risk tolerances |
| 8 | `success_rate` threshold (0.7) for cache hits is hardcoded — should be configurable | Low | Fine-tuning |
| 9 | No LLM response validation — if LLM returns a structurally invalid response, it silently falls through to default | Medium | Silent degradation |

### Future-Readiness: STRONG

The cache→rule→LLM→default pattern is exactly right. With plugin system integration and prompt templating, this becomes the self-improving decision engine from the offline autoresearch vision.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | Validate LLM responses against schema before caching — reject invalid responses | 1 day |
| P1 | Move prompts to template files (Jinja2 or simple .txt) — enable A/B testing and versioning | 2 days |
| P1 | Make rule registration data-driven (YAML/JSON config) — plugin system integration point | 2 days |
| P1 | Rename `DecisionResult` → `HybridDecisionResult` | 0.5 day |
| P2 | Make success_rate threshold and default decisions agency-configurable | 1 day |
| P2 | Add thread-safe singleton pattern for engine instance | 0.5 day |

---

## COMPONENT 7: Suitability Engine (`suitability/`)

### Architectural Soundness: ADEQUATE (7/10)

**What's Right**:
- Clean separation: `models.py` (contracts), `scoring.py` (Tier 1), `context_rules.py` (Tier 2), `integration.py` (pipeline wiring), `catalog.py` (activity definitions).
- `ParticipantRef` with kind/ref_id/label/age/metadata — flexible participant model.
- `ActivityDefinition` with tags, intensity, duration, costs, age/weight bounds — rich activity model.
- `TAG_RULES` dictionary — clean declarative rule mapping: `(tag, participant_label) → (tier, reason)`.
- `_pick_most_conservative_tier()` — when multiple rules fire, picks the safest outcome.
- Intensity scoring with per-participant-type modifiers — correct domain logic.
- `compute_confidence()` from field-level confidences — systematic uncertainty tracking.
- `collect_missing_signals()` — identifies what data would improve scoring.
- Pace preference normalization in `integration.py` with clamping to safe default — data-loss prevention pattern correctly applied.
- Vocabulary bridge between capture API (rushed/normal/relaxed) and suitability model (packed/balanced/relaxed) — correctly handled as integration concern.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `STATIC_ACTIVITIES` in `catalog.py` hardcodes 17 activities — this will never scale to real-world use | **HIGH** | Can't add agency-specific activities; can't source activities from external APIs |
| 2 | `TAG_RULES` dict hardcodes all scoring rules — should be data-driven, not code | Medium | Adding a new rule = code change + deploy |
| 3 | `assess_activity_suitability()` in `integration.py` only checks `STATIC_ACTIVITIES[:10]` — arbitrary truncation | **HIGH** | Real itineraries have 20-30 activities; 10 is a toy limit |
| 4 | `evaluate_itinerary_coherence()` only checks 2 specific risks (elderly overload, toddler pacing) — extremely incomplete | Medium | Missing: budget coherence, destination coherence, transport logic, rest-day detection, back-to-back intensity |
| 5 | **No per-person utility percentage computation** — the core thesis concept ("Universal Studios = 20% utility for toddlers") is completely absent | **CRITICAL** | The #1 thesis differentiator is not implemented |
| 6 | No wasted spend calculation — `cost_per_person × (1 - utility)` for each participant | **CRITICAL** | The #2 thesis differentiator (waste flags) is not implemented |
| 7 | `ActivitySuitability.source` is always `"rule"` — Tier 3 LLM path does not exist | Medium | Gaps for ambiguous/world-knowledge cases |
| 8 | `SuitabilityContext` has rich fields (season_month, destination_climate, trip_duration_nights) but they are never populated from actual packet data | Medium | Context is always empty/default — Tier 2 rules can't use real context |
| 9 | No `split_day_recommendation` logic — the thesis concept of "suggest alternative for low-utility members" | Medium | Key UX feature for multi-gen trips |

### Future-Readiness: **NEEDS MAJOR EXTENSION**

The architecture is solid. The catalog is the bottleneck. Need:
1. Agency-specific activity catalogs (loaded from DB/config)
2. Utility percentage computation
3. Wasted spend calculation
4. Richer Tier 2 coherence rules

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | **Implement per-person utility scoring**: `utility = f(activity, participant)` → percentage 0-100% | 2-3 days |
| **P0** | **Implement wasted spend calculation**: `waste = cost_per_person × (1 - utility/max_utility)` summed across participants | 1 day |
| P0 | Remove `[:10]` truncation — score all activities in catalog or provided list | 0.5 day |
| P1 | Populate `SuitabilityContext` from real packet data (season, climate, trip duration) | 1 day |
| P1 | Expand Tier 2 coherence rules: budget coherence, transport logic, rest-day detection, back-to-back intensity | 2 days |
| P1 | Make activity catalog loadable from DB/config (agency-specific) | 2 days |
| P2 | Add split-day recommendation logic | 2 days |
| P2 | Build Tier 3 LLM scorer (behind deterministic tiers, trigger-based) | 3-4 days |

---

## COMPONENT 8: Strategy & Output Bundling (`strategy.py`)

### Architectural Soundness: ADEQUATE (6/10)

**What's Right**:
- `QuestionWithIntent` dataclass — every question carries purpose (`intent`), assumption testing (`tests_assumption`), and `can_infer` flag. Correct from first principles.
- Mode-specific goals and openings for all 8 operating_modes × 5 decision_states — comprehensive coverage.
- Tone scaling by confidence with sentiment override (`anxiety_alert → measured_empathy`, `crisis → direct_crisis_support`).
- `TONAL_GUARDRAILS` dictionary with 6 tone profiles — rich conversational guidance.
- Question priority ordering with `QUESTION_PRIORITY_ORDER` — constraint-first (composition → destination → origin → dates).
- `BranchQualityRules` with conversational approach detection — budget framing vs destination framing.
- `PromptBundle` with separate `system_context` (LLM instructions) vs `user_message` (actual output) vs `internal_notes` (agent-only).
- `to_traveler_dict()` that structurally omits `internal_notes` — intrinsic safety.
- `PromptBlock` with explicit `audience` tagging — internal vs traveler.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | Mode-specific logic is embedded in if/elif chains (`get_mode_specific_goal`, `get_mode_specific_opening`) — not strategy/polymorphism pattern | Medium | Adding a new operating_mode requires touching multiple if/elif chains |
| 2 | `get_mode_specific_goal()` and `get_mode_specific_opening()` duplicate the decision_state×operating_mode matrix — two giant switch statements instead of one data structure | Medium | Inconsistency risk; maintenance burden |
| 3 | Opening messages are hardcoded English strings — no localization, no template system, no agency voice customization | Medium | Indian market needs Hindi/Tamil; agencies want their own voice |
| 4 | `PromptBundle` is text-only — no structured option rendering. The output is a string, not rendered itinerary options with trade-off tables | **CRITICAL** | The "aha moment" from UX journeys (15 min vs 2 days) requires rendered options, not text prompts |
| 5 | `build_session_strategy()` takes optional params (`session_context`, `agent_profile`) that appear to be unused in practice | Low | Dead parameters, confusing API |
| 6 | No dynamic content generation based on actual packet data — everything is switch/case over enums, not template filling from facts | **HIGH** | Strategy is generic, not personalized. "Based on what you've shared" but nothing is actually based on what they shared |
| 7 | `build_internal_bundle()` and `build_traveler_safe_bundle()` are called in orchestration.py but I haven't read their full implementation — need to verify they actually use packet data |
| 8 | No WhatsApp/SMS/email template system — output is always generic text | Medium | Gap #03 communication channels |
| 9 | No presentation_profile (D2) — agency vs consumer presentation distinction | Medium | D2 consumer surface blocked |

### Future-Readiness: **NEEDS MAJOR ENHANCEMENT**

The strategy framework is comprehensive but generic. It needs:
1. Template filling from actual packet data (personalization)
2. Rendered option output (not just text)
3. Multi-channel output formatting

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | **Replace if/elif chains with data-driven mode×state matrix** — single data structure, not duplicated switch statements | 2 days |
| **P0** | **Implement template filling** — opening messages should reference actual packet data ("Based on your interest in {destination} in {month}...") | 2 days |
| **P0** | **Implement rendered option output** — not just text prompts but structured itinerary options with cost comparison tables, day-wise outlines, suitability badges | 5-7 days |
| P1 | Add localization support — message templates in locale files | 3-4 days |
| P1 | Add agency voice customization — templates overridable per agency | 2 days |
| P2 | Add WhatsApp/email output formatters | 3-4 days |
| P2 | Add consumer presentation_profile for D2 | 2 days |

---

## COMPONENT 9: Safety Sanitization (`safety.py`)

### Architectural Soundness: STRONG (9/10)

**What's Right**:
- **Structural sanitization** — internal data is not even passed to the traveler-safe builder (not just hidden from output). This is the correct approach from first principles.
- `SanitizedPacketView` intentionally has NO `hypotheses`, `contradictions`, `unknowns`, `ambiguities` — these are internal-only concepts, correctly excluded.
- `FORBIDDEN_TRAVELER_CONCEPTS` with word-boundary regex — catches "confidence score", "blockers", "hypotheses", "ambiguities" etc.
- `INTERNAL_ONLY_FIELDS` blacklist — strips `agency_notes`, `owner_priority_signals`, `commission_rate`, `net_cost`.
- `TRANSFORM_REQUIRED_FIELDS` — `owner_constraints` and `risk_flags` need transformation, not just stripping.
- `_extract_traveler_safe_constraints()` with visibility filtering — `internal_only` vs `traveler_safe_transformable`.
- `_transform_constraint_text()` for financial language scrubbing — "Owner markup required: 15%" → silently dropped. "Supplier restrictions: no refunds" → "Please review cancellation policies". Correct domain logic.
- Strict mode with `TRAVELER_SAFE_STRICT` env var — can enforce leakage as hard error for testing.
- `check_no_leakage()` with word-boundary regex — avoids false positives like "knowing" matching "unknown".
- Dual-phase leakage check in orchestration.py — checks both traveler bundle text AND sanitized view values.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `FORBIDDEN_TRAVELER_CONCEPTS` is hardcoded — should be data-driven, extensible per agency | Medium | Discovery of new leakage patterns requires code change |
| 2 | `traveler_safe_signals` in `sanitize_for_traveler()` only includes ONE signal: `"domestic_or_international"` — extremely limited | **HIGH** | The comment says trip_duration_days and seasonality were REMOVED because they're "NOT produced by NB01" — but they SHOULD be produced. This is hiding a pipeline gap as a safety feature. |
| 3 | `_transform_constraint_text()` is a simple keyword matcher — fragile for nuanced financial language | Low | Edge cases: "our cost is" vs "the cost is", "we marked up 15%" vs "market price", etc. |
| 4 | `SanitizedPacketView` facts and derived_signals are `Dict[str, Any]` — no structural typing | Medium | Can't catch sanitization bugs at type-check time |
| 5 | No leak detection on structured data (JSON fields, nested objects) — only scans text strings | Medium | Structured output fields could contain internal concepts |

### Future-Readiness: STRONG

The structural approach (data not available, not hidden) is architecturally correct for any future output surface — web, WhatsApp, email, API.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | Implement `trip_duration_days` and `seasonality` as derived signals in NB02 — stop removing them from traveler_safe_signals | 1 day |
| P1 | Expand `traveler_safe_signals` to include: trip_duration_days, seasonality, domestic_or_international, destination_highlights (once NB01 produces them) | 1 day |
| P1 | Make forbidden concepts list data-driven (JSON config) | 0.5 day |
| P2 | Add structured data leakage scanning | 1 day |
| P2 | Add typed SanitizedPacketView (Pydantic/SQLAlchemy model) | 1 day |

---

## COMPONENT 10: Orchestration (`orchestration.py`)

### Architectural Soundness: ADEQUATE (7/10)

**What's Right**:
- Clean sequential pipeline: Extract→Validate→NB01Gate→Decide→Suitability→NB02Gate→Frontier→Strategy→Bundles→Safety→Leakage→Fees→FixtureCompare.
- OpenTelemetry spans on every stage.
- Stage callback pattern for progress reporting.
- `SpineResult` as single return type — all pipeline outputs in one object.
- `_emit_audit_event()` for persistent audit trail.
- Early exit on NB01 ESCALATE/DEGRADE with proper empty/partial results.
- Dual-phase leakage check (traveler bundle + sanitized view).
- Fixture compare framework with 6 assertion types.
- Fee calculation wired in.
- Suitability flags override decision_state for critical issues.
- Frontier orchestration (Ghost Concierge + Sentiment) wired in.
- Autonomy outcome recorded on decision rationale.
- `@lru_cache(maxsize=1)` on forbidden patterns compilation.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `_obj_to_dict()` is a heuristic serialization helper — tries Pydantic model_dump, then dataclass asdict, then vars(), then pass-through. Fragile. | Medium | Serialization inconsistencies across different object types |
| 2 | `_emit_audit_event()` has a `try/except` that silently swallows audit failures — `logger.warning()` but no alerting | Medium | Audit trail gaps go unnoticed |
| 3 | `_emit_audit_event()` sends `pre_state={"state": "previous"}` with a comment "# Placeholder for actual packet delta" — acknowledged tech debt | Medium | Audit events don't capture actual state transitions |
| 4 | `_create_empty_spine_result()` and `_create_partial_intake_result()` duplicate `SpineResult` construction — risk of inconsistency | Low | If SpineResult gains new fields, these helpers silently miss them |
| 5 | `_compare_against_fixture()` lives in orchestration.py — should be in a test/eval module | Low | Production code contains test infrastructure |
| 6 | `_human_block_reason()` with `_BLOCK_COPY` dict — hardcoded English error messages | Low | No localization |
| 7 | No pipeline timeout — a hung LLM call or geography lookup could stall the entire pipeline indefinitely | Medium | Production reliability |

### Future-Readiness: ADEQUATE

The orchestration is correct for the current pipeline. As new stages are added (document extraction, voice intake, booking coordination), the orchestration needs to support configurable pipeline composition rather than hardcoded sequential stages.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Add pipeline timeout (configurable, default 30s) with graceful degradation | 1 day |
| P1 | Fix audit event pre_state to capture actual packet delta | 1 day |
| P1 | Move fixture compare to `tests/` or `src/evals/` | 0.5 day |
| P2 | Make pipeline composition configurable (not hardcoded sequential stages) | 2 days |
| P2 | Extract serialization helper to shared utility | 0.5 day |

---

## COMPONENT 11: Agency Settings (`agency_settings.py`)

### Architectural Soundness: ADEQUATE (7/10)

**What's Right**:
- `AgencyAutonomyPolicy` fully D1-aligned: `approval_gates` with per-decision_state `auto/review/block`, `mode_overrides`, `auto_proceed_with_warnings`, `learn_from_overrides`.
- `__post_init__` enforces `STOP_NEEDS_REVIEW = "block"` and fills missing states from defaults — safety invariant enforced at construction.
- `effective_gate()` method — single lookup point, mode override takes precedence over base gate.
- `from_legacy_dict()` for migration from old threshold-based config.
- `LLMGuardSettings` with budget_mode, thresholds, max_calls.
- `AgencySettings` covers profile, operational (hours, channels, brand_tone, currency, margin), frontier (auto_negotiation, checker agent), autonomy, LLM guard.
- `AgencySettingsStore` with SQLite persistence, legacy JSON migration.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | SQLite for settings persistence — should migrate to PostgreSQL with the rest of the data layer | Medium | Two databases (SQLite + Postgres) = operational complexity |
| 2 | `AgencySettingsStore` is a class with only `@classmethod` methods — should be regular functions or a proper repository pattern | Low | Code style, no real impact |
| 3 | No settings audit trail — who changed what setting when? Documented as Gap #16 but not in code | Medium | Compliance, debugging |
| 4 | `_DATA_ROOT` is module-level mutable — tests can monkeypatch it but this is fragile | Low | Test reliability |
| 5 | Legacy `min_proceed_confidence` and `min_draft_confidence` fields exist for backward compat but confuse the D1 model | Low | Two competing autonomy models in the same object |
| 6 | No per-agency feature flags — what features are enabled for this agency? | Medium | Can't do gradual rollout, A/B testing |
| 7 | `brand_tone` is a simple string — but the strategy module has 6 rich tone profiles. Should AgencySettings reference the tone profiles, not override them | Low | UX inconsistency |

### Future-Readiness: ADEQUATE

Needs migration to PostgreSQL + audit trail + feature flags.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Migrate settings storage from SQLite to PostgreSQL | 2 days |
| P1 | Add settings audit trail — log every settings change with user, timestamp, old/new values | 1 day |
| P2 | Add feature flag system (per-agency enable/disable for: audit_mode, auto_negotiation, checker_agent, suitability_scoring, frontier) | 2 days |
| P2 | Remove legacy threshold fields once D1 upgrade is complete | 0.5 day |

---

## COMPONENT 12: Spine API Server (`spine_api/server.py`)

### Architectural Soundness: **CRITICAL PROBLEM** (3/10)

**What's Right**:
- Comprehensive REST API surface.
- Proper auth dependencies (`get_current_user`, `get_current_agency`).
- Background task support for async pipeline runs.
- Run lifecycle with state machine transitions.
- Timeline endpoint, dashboard stats, follow-up management.
- OpenTelemetry instrumentation.
- Proper error handling with HTTPException.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | **3,535 LINES IN A SINGLE FILE** — this is the single biggest architectural problem in the entire codebase, worse than extractors.py or decision.py | **CRITICAL** | Unmaintainable; impossible to test individual routes; every change risks breaking unrelated endpoints; onboarding nightmare for new developers |
| 2 | `server.py` defines routes directly instead of using the `routers/` directory — `routers/auth.py` and `routers/workspace.py` exist but server.py still defines most routes inline | **CRITICAL** | The router infrastructure exists but is being ignored. Massive code duplication / inconsistency. |
| 3 | Server.py mixes concerns: OTel setup (lines 66-87), auth wiring (lines 93-96), database setup, background task management, route definitions (hundreds of routes), business logic | **CRITICAL** | Violates single responsibility; can't test concerns independently |
| 4 | JSON file persistence (`TripStore`, `AuditStore`) still in active use alongside SQLAlchemy models — dual persistence with no clear migration path in the server code | **HIGH** | Data consistency risk; tech debt |
| 5 | Many routes have inline business logic rather than delegating to service layer — `services/` directory exists but is underutilized | Medium | Can't test business logic without HTTP layer |
| 6 | No API versioning — all routes are `/api/*` with no version prefix | Medium | Breaking changes are all-or-nothing |
| 7 | No request validation beyond Pydantic models — no rate limiting, no request size limits visible | Medium | Production hardening |

### Future-Readiness: **NEEDS COMPLETE REFACTOR**

Before ANY new features are added to the API, server.py must be decomposed. Otherwise every new endpoint adds to the 3,535-line monster.

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | **Decompose server.py into proper routers**: `routers/trips.py`, `routers/runs.py`, `routers/timeline.py`, `routers/dashboard.py`, `routers/suitability.py`, `routers/followups.py`, `routers/analytics.py` | 3-4 days |
| **P0** | **Extract OTel setup to `core/observability.py`** | 0.5 day |
| **P0** | **Extract business logic from routes into service layer** — use existing `services/` directory | 2-3 days |
| P1 | Add API versioning (`/api/v1/...`) | 1 day |
| P1 | Migrate remaining JSON persistence (TripStore, AuditStore) to PostgreSQL via repository pattern | 3-4 days |
| P2 | Add rate limiting, request size limits | 1 day |

---

## COMPONENT 13: Frontend Types (`types/spine.ts`)

### Architectural Soundness: ADEQUATE (6/10)

**What's Right**:
- Re-exports generated types from backend contract — single source of truth for shared types.
- Frontend-only types clearly separated and documented.
- Comprehensive type coverage: `DecisionState`, `PromptBundle`, `ConfidenceScorecard`, `Rationale`, `SuitabilityFlag`, `ValidationReport`, etc.

**What's Wrong / Missing / Concerning**:

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `ValidationReport` has BOTH `is_valid` and `status` fields — this suggests unresolved contract drift between what the backend sends and what the frontend expects | **HIGH** | The `API Contract Verification` section of AGENTS.md explicitly warns about this exact failure mode. The dual-field approach is a band-aid, not a fix. |
| 2 | `SuitabilityFlag` (line 214) and `SuitabilityFlagData` (line 173) are DIFFERENT shapes with confusingly similar names — one is the API response shape, one is the pipeline data shape | Medium | Developer confusion; risk of using wrong type |
| 3 | `PacketContradiction.values` is `unknown[]` — should be typed | Low | Type safety |
| 4 | `SlotValue.value` is `unknown` — generic, no narrowing per field | Low | Type safety |
| 5 | `ValidationReport` includes both `is_valid` (old shape) and `status/gate/reasons` (new shape) — this is the exact contract drift that the API Contract Verification rule is designed to prevent | **HIGH** | Runtime errors when consuming validation data |
| 6 | Some types (`FollowUpQuestion.suggested_values`) use `unknown[]` instead of proper types | Low | Type safety |

### Future-Readiness: NEEDS CLEANUP

### Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | **Resolve ValidationReport contract drift** — pick ONE shape (backend's actual output) and remove the dual-field approach. Verify against real API response. | 1 day |
| P1 | Rename `SuitabilityFlagData` → `PipelineSuitabilityFlag` to distinguish from `SuitabilityFlag` (API response) | 0.5 day |
| P1 | Type `PacketContradiction.values` and `SlotValue.value` properly | 0.5 day |

---

## CROSS-CUTTING ARCHITECTURAL ISSUES

These issues span multiple components and represent systemic architectural debt.

### 1. Monolith File Problem (CRITICAL)

| File | Lines | Should Be |
|------|-------|-----------|
| `spine_api/server.py` | 3,535 | 10+ router files + OTel setup + service layer |
| `src/intake/decision.py` | 2,240 | gap_detector.py + feasibility_engine.py + confidence_engine.py + decision_router.py |
| `src/intake/extractors.py` | 1,808 | date_extractor.py + destination_extractor.py + budget_extractor.py + composition_extractor.py + preference_extractor.py |

**Total**: 7,583 lines in 3 files that should be 20+ files.

**First-Principles Violation**: The "dependency-ordered build sequence" from `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` requires testable, independently verifiable modules. Monolithic files prevent this.

### 2. Dual Persistence Problem (HIGH)

The system has TWO persistence layers actively in use:
- **PostgreSQL + SQLAlchemy 2.0**: `agencies`, `users`, `memberships`, `workspace_codes` (tenant data)
- **JSON files**: `TripStore.get_trip()`, `AuditStore.log_event()`, `AssignmentStore` (operational data)

These are used side-by-side in `server.py` with no clear migration path in the code. Phase 8 of the onboarding roadmap addresses this but it's not started.

### 3. Naming Collision (Medium)

`DecisionResult` exists in BOTH:
- `src/intake/decision.py` — the NB02 pipeline output
- `src/decision/hybrid_engine.py` — the hybrid engine output

These are different types with different fields. This is a time bomb for import confusion.

### 4. Dead/Stub Code (Medium)

- `sourcing_path` signal — `maturity="stub"`, computed but never used
- `preferred_supplier_available` — in validation schema but never computed
- `PipelineGate` Protocol in `gates.py` — defined but never used for type checking
- `session_context` and `agent_profile` params in `build_session_strategy()` — accepted but unused
- Empty directories: `src/agents/`, `src/config/`, `src/adapters/`, `src/pipelines/`, `src/schemas/`, `src/utils/`, `frontend/src/components/shell/`

### 5. No Output Quality Gate (Medium)

NB01→NB02 has a gate. NB02→NB03 has a gate. NB03→Output has NO gate. A bad strategy or incoherent traveler bundle would proceed unchecked.

### 6. Hardcoded vs Data-Driven (Medium)

Across the codebase, critical configuration is hardcoded:
- Validation thresholds (`QUOTE_READY`, `INTAKE_MINIMUM`)
- Suitability rules (`TAG_RULES`)
- Activity catalog (`STATIC_ACTIVITIES`)
- Forbidden terms (`FORBIDDEN_TRAVELER_CONCEPTS`)
- Strategy openings (`get_mode_specific_opening`)
- LLM prompts (`_build_llm_prompt`)

None of these are agency-configurable. This blocks per-agency customization — one of the thesis's core value props.

---

## CONSOLIDATED ACTION PLAN (Dependency-Ordered)

This is the implementation order if the goal is to fix architectural debt before adding new features.

### Phase A: Critical Refactors (Must Do Before Any New Features)

| # | Action | Files | Effort | Blocks |
|---|--------|-------|--------|--------|
| A1 | **Decompose server.py** into routers + extract OTel to core/ | `spine_api/server.py` → 10+ router files | 3-4 days | Every new API endpoint |
| A2 | **Split extractors.py** into domain-specific modules | `src/intake/extractors.py` → 5+ files | 3-4 days | PDF extraction, voice intake, audit mode extraction |
| A3 | **Split decision.py** into gap/feasibility/confidence/router modules | `src/intake/decision.py` → 4+ files | 3-4 days | Feasibility explainability, new decision types |
| A4 | **Resolve ValidationReport contract drift** in frontend types | `frontend/src/types/spine.ts` | 0.5 day | Frontend consuming validation data |
| A5 | **Rename DecisionResult collision** | `src/decision/hybrid_engine.py` + all imports | 0.5 day | Confusion |

**Total Phase A**: ~10-12 days

### Phase B: Missing Primitives (Thesis-Critical Features)

| # | Action | Effort | Blocks |
|---|--------|--------|--------|
| B1 | Implement per-person utility scoring (suitability) | 2-3 days | Wasted spend, thesis differentiator |
| B2 | Implement wasted spend calculation | 1 day | Thesis differentiator |
| B3 | Make activity catalog loadable from DB/config | 2 days | Per-agency activities |
| B4 | Implement template filling in strategy (personalization) | 2 days | "Aha moment" quality |
| B5 | Add NB03 output quality gate | 2 days | Output safety |

**Total Phase B**: ~9-10 days

### Phase C: Hardening & Production Readiness

| # | Action | Effort |
|---|--------|--------|
| C1 | Add snapshot/clone to CanonicalPacket (immutability) | 1 day |
| C2 | Wire events to persistent store (not in-memory) | 2 days |
| C3 | Add pipeline timeout | 1 day |
| C4 | Make validation thresholds agency-configurable | 2 days |
| C5 | Move LLM prompts to template files | 2 days |
| C6 | Add LLM response validation | 1 day |
| C7 | Add structured data leakage scanning | 1 day |
| C8 | Migrate settings from SQLite to PostgreSQL | 2 days |
| C9 | Add settings audit trail | 1 day |
| C10 | Add feature flag system | 2 days |

**Total Phase C**: ~15 days

### Phase D: Features on Clean Foundation

| # | Action | Effort |
|---|--------|--------|
| D1 | PDF/URL document extraction (audit mode) | 4-5 days |
| D2 | Rendered itinerary option output | 5-7 days |
| D3 | Dynamic question router | 3-4 days |
| D4 | Mode-specific NB03 builders | 4-5 days |
| D5 | WhatsApp/email output formatters | 3-4 days |
| D6 | Consumer presentation_profile (D2) | 2 days |
| D7 | D5 override feedback bus | 4-5 days |
| D8 | D4 Tier 3 LLM suitability scorer | 3-4 days |
| D9 | Eval harness scaffold (D6) | 3-4 days |

**Total Phase D**: ~31-43 days

---

## VERDICT: What "Green" Actually Means

| Component | Previous Rating | Actual Rating | Key Finding |
|-----------|----------------|---------------|-------------|
| packet_models.py | ✅ Green | 🟡 Adequate (8/10) | Strong model, missing immutability & persistent events |
| gates.py | ✅ Green | ✅ Strong (9/10) | Correct D1 implementation, missing NB03 gate |
| validation.py | ✅ Green | 🟡 Adequate (7/10) | Hardcoded thresholds, no schema contract validation |
| extractors.py | ✅ Green | 🔴 Concerning (5/10) | **1,808-line monolith — critical refactor needed** |
| decision.py | ✅ Green | 🔴 Concerning (4/10) | **2,240-line monolith — critical refactor needed** |
| hybrid_engine.py | ✅ Green | ✅ Strong (8/10) | Good pattern, needs prompt templating + response validation |
| suitability/ | ✅ Green | 🟡 Adequate (7/10) | Good architecture, missing utility scoring & catalog scalability |
| strategy.py | ✅ Green | 🟡 Adequate (6/10) | Good framework, needs template filling + rendered output |
| safety.py | ✅ Green | ✅ Strong (9/10) | Correct structural approach, needs broader signal coverage |
| orchestration.py | ✅ Green | 🟡 Adequate (7/10) | Correct sequencing, missing timeout + persistent events |
| agency_settings.py | ✅ Green | 🟡 Adequate (7/10) | D1-aligned, needs Postgres migration + audit trail |
| spine_api/server.py | ✅ Green | 🔴 **CRITICAL (3/10)** | **3,535-line monolith — worst architectural problem** |
| frontend types | ✅ Green | 🟡 Adequate (6/10) | Contract drift on ValidationReport, naming confusion |

**Summary**: Of 13 components rated "green" in the previous breakdown, applying first-principles scrutiny reveals:
- **2 are truly Strong** (gates.py, safety.py)
- **7 are Adequate but need work** (packet_models, validation, hybrid_engine, suitability, strategy, orchestration, agency_settings)
- **3 are Concerning and NEED major refactoring** (extractors, decision, frontend types)
- **1 is CRITICAL and needs complete decomposition** (server.py)

**The spine concept is correct. The implementation has grown a monolith problem that must be solved before meaningful new features can be added.**

---

# PART II: INDEPENDENT ARCHITECTURAL ASSESSMENT

**Note: This section represents independent architectural judgment — not derived from reading code or docs, but from first-principles reasoning about what a system of this type requires. It identifies gaps, risks, and design concerns that the code/doc analysis alone may miss.**

---

## Architectural Philosophy Assessment

The system's governing philosophy — "deterministic-first, LLM only when necessary" — is correct and rare. Most AI startups default to LLM-first and then scramble to add rules. This team got the order right.

However, the philosophy is applied inconsistently. The extraction pipeline treats LLM as a fallback for regex failures. The hybrid engine treats rules as a tier before LLM. But the strategy layer (NB03) makes no such distinction — openings and goals are purely switch/case with no deterministic "what does this packet actually say" before the generic template. The philosophy needs to be applied to ALL layers uniformly.

### What "Deterministic-First" Should Mean at Each Layer

| Layer | Current | Should |
|-------|---------|--------|
| NB01 Extraction | Regex → LLM fallback ✅ | + structured source adapters (form fields, import formats) |
| NB02 Decision | Rules → LLM fallback ✅ | + numeric feasibility models, not just yes/no |
| NB03 Strategy | Switch/case over enums ❌ | Template filling from packet facts → LLM polish |

The gap at NB03 is architectural, not cosmetic. When strategy is purely generic ("Based on what you've shared"), it fails the personalization test that makes users feel heard. The entire UX vision (Journeys doc: "She actually listened to us") depends on NB03 being data-driven, not generic.

---

## Missing Architectural Primitives

These are things the system doesn't have that it should, based on what it aims to do:

### 1. A Numeric Feasibility Model

The current feasibility checks are boolean — feasible/infeasible. A travel agency system needs a NUMERIC model:
- For a given destination + dates + party size: what does it cost?
- Given a budget: what's feasible?
- Given constraints: what's optimal?

Without this, "feasibility" is heuristic guesswork. The budget_feasibility rule just checks a hardcoded table of ~20 destinations. This doesn't scale to 200+ destinations with seasonal price variation.

**What's needed**: A cost estimation model backed by (a) static destination cost tables that can be updated without code changes, (b) eventually live pricing data from supplier APIs, (c) a gap computation: estimated_cost - stated_budget.

### 2. A Structured Constraint Model (Hard vs Soft with Weights)

The `CanonicalPacket` tracks constraints as slots in facts. But there's no constraint classification:
- **Hard constraints**: Cannot be violated (visa timeline, min_age for activity, budget ceiling)
- **Soft constraints**: Should optimize for (pace preference, food type, hotel style)
- **Weighted trade-offs**: When constraints conflict, which wins?

Example: A traveler says "budget ₹4L, but want Paris and Switzerland in June." The system needs to know that destination+season is a hard constraint, budget is also hard, and the conflict (₹4L can't do both in peak season) requires explicit trade-off surfacing, not just a "tight" flag.

### 3. A Sourcing Abstraction (Even Without Live Data)

The sourcing hierarchy (Internal → Preferred → Network → Open Market) is architecturally the right model. But the system has NO sourcing abstraction at all — not even a stub that could be filled later. 

**What's needed now** (even without supplier data): A `SourcingPolicy` object per agency that defines the hierarchy order, margin floors, and category overrides. The NB02 decision layer can use this to annotate decisions with `sourcing_tier: "open_market (no internal or preferred match)"` even if all tiers resolve to open_market today. This creates the data model that supplier data will eventually plug into.

### 4. An Output Rendering Pipeline

The current output is `PromptBundle` — text blobs. This is the architecturally weakest link. A travel agency system outputs:
- **Itinerary options**: Day-by-day with activities, hotels, transport
- **Cost breakdowns**: By category (flights, stay, activities, food, buffer)
- **Suitability badges**: Per activity per person ("Snorkeling ✅ Adults ✅ Kids ❌ Toddlers")
- **Trade-off comparisons**: Option A vs B across cost, comfort, pace, fit

None of this rendering exists. The system produces text that a human would need to manually convert into a proposal. This defeats the "workflow compression" thesis.

**What's needed**: A structured output model (`ItineraryOption` with days, activities, costs, suitability) that can be rendered into multiple formats (web proposal, WhatsApp message, email, PDF).

### 5. A Revision Graph / Diff Model

The UX vision describes "What changed and why" comparison between itinerary versions. This requires:
- **Packet snapshots**: Immutable copies at key points (intake complete, after edits, after decisions)
- **Diff computation**: What fields changed between snapshots?
- **Rationale attachment**: Why did this change? (operator override, traveler feedback, pricing update)

The current `CanonicalPacket.events` list captures mutations but not the full state at each point. Snapshots + diffs = the revision comparison UX.

---

## Design Smells I've Noticed

These aren't bugs. They're patterns that indicate architectural stress that will compound:

### 1. The `_obj_to_dict()` Pattern

When a codebase has a `_obj_to_dict()` function that tries Pydantic `model_dump`, then `asdict`, then `vars()`, then gives up — that's a smell. It means the system has multiple serialization contracts and no unified approach. This is a symptom of organic growth without a serialization strategy. Eventually it will cause silent data loss when a new object type appears that none of the heuristics handle correctly.

### 2. The Dual Persistence Pattern

JSON files AND PostgreSQL used side-by-side for different entities. This isn't just "not migrated yet" — it means the system has two different consistency models (JSON files are eventually-consistent-by-accident, PostgreSQL is ACID). Different entities have different reliability guarantees. This is invisible to users but will cause hard-to-debug issues when a trip in JSON references a user in Postgres and one is out of sync.

### 3. The `maturity="stub"` Pattern as Honest Debt

Marking unimplemented signals as `maturity="stub"` is architecturally HONEST. It's one of the best patterns in the codebase. But honesty without a plan to resolve is just documentation of failure. Each `stub` signal needs:
- A target maturity date/sprint
- What data or integration it needs to graduate to `heuristic` or `verified`
- Who owns it

### 4. The "Everything is a Slot" Pattern

Making every packet field a `Slot` with provenance, confidence, authority is conceptually right. But it also means that simple things ("party_size: 4") carry the same structural weight as complex things ("destination_candidates: [Paris, Rome, Barcelona]"). This is fine for the internal model, but the output/display layer needs to simplify — travelers don't need to see confidence scores on party size.

### 5. The File Size Smell

Any file over 500 lines in a Python project is a smell. Over 1,000 is a warning. Over 2,000 is an architectural defect. `server.py` at 3,535 lines, `decision.py` at 2,240, `extractors.py` at 1,808 — these aren't just "big files," they're structural evidence that the system wasn't decomposed when it should have been. The fact that `routers/` exists but `server.py` defines most routes inline suggests the decomposition was started and then abandoned.

---

## Things the Vision Docs Got Right That the Code Forgot

### 1. The Two-Screen Model

The vision describes an agency screen AND a traveler screen with a live brief. The code has a workbench (agency screen) but no traveler-facing live brief surface. This is the biggest gap between vision UX and current reality. The two-screen model is the "aha moment" from the user journeys doc.

### 2. The Dynamic Question Router

The vision describes a priority-based question selection engine (P1: blocking unknowns → P4: refinements). The code has `QUESTION_PRIORITY_ORDER` with field weights and `sort_questions_by_priority()`, but no router that dynamically selects the NEXT question based on current packet state. The existing code assumes all follow-ups are generated at once, not iteratively.

### 3. The "Why This Matters" Annotations

The vision says every follow-up question should carry an explanation: "Ask about dates (affects pricing by 30-40%)." The `QuestionWithIntent` dataclass has `intent` and `tests_assumption` fields — the model exists. But the actual question generation never populates these fields with real explanations. The fields are structural but unused.

### 4. The Sourcing Hierarchy

This is the thesis's margin optimization lever. The code has a `sourcing_path` stub marked `maturity="stub"`. The vision has a rich 4-tier model. This gap isn't just "not implemented" — it's that the architecture has NO place for sourcing logic. It doesn't need supplier data yet, but it needs the abstraction that supplier data will eventually plug into. Currently `sourcing_path` is set to `"open_market"` or `"network"` based on a trivial heuristic — the tier concept isn't even modeled.

---

## What Would Make This System Production-Ready

Beyond the specific refactors identified in Part I, here's what a production-grade travel agency system needs architecturally:

### 1. Idempotent Pipeline Execution

If the same input is submitted twice, the system should:
- Detect that it's a duplicate (same traveler, same trip parameters, same timeframe)
- NOT create two separate trips
- Either return the existing result or offer to re-process

Currently, every `run_spine_once()` call creates a new packet regardless.

### 2. Graceful Degradation at Every Tier

| Component | If Fails | Should |
|-----------|----------|--------|
| LLM call | Falls to default (safe) ✅ | Already correct |
| Geography lookup | Should use regex fallback | Currently unknown |
| DB query | Should use in-memory fallback | Not implemented |
| External API | Should cache last successful result | Not applicable yet |

### 3. Tenant Isolation That's Testable

The system has multi-tenant models. The test for tenant isolation should be: "Can a query from agency A ever return agency B's data?" The answer should be provably "no" through RLS + integration tests. Currently RLS is documented but not implemented.

### 4. An Operator Override Protocol With Audit Trail

The vision describes operator overrides for AI decisions. The current override API exists (P1-02) but the protocol should ensure:
- Every override is logged with: who, when, what was overridden, why
- Override patterns are detectable (D5: "intake_extractor overridden 15x on family trips → suggest policy change")
- No override can silently change a hard safety constraint (STOP_NEEDS_REVIEW)

### 5. Pricing That Accounts For Uncertainty

The fee calculation currently produces a single number. But travel pricing has uncertainty:
- Supplier rates may change between quote and booking
- Currency fluctuations for international trips
- Seasonal surcharges that kick in at different dates

The pricing model should produce ranges with confidence bands, not single numbers.

---

## Summary: Independent Assessment

| Dimension | Verdict | Key Gap |
|-----------|---------|---------|
| Architecture Philosophy | ✅ Strong | Applied inconsistently across layers |
| Data Model | 🟡 Adequate | Missing constraint classification, sourcing abstraction |
| Pipeline | 🟡 Adequate | Missing idempotency, timeout, output rendering |
| Output/UX Pipeline | 🔴 Weak | No structured output, no rendering, no revision graph |
| Production Readiness | 🔴 Not Ready | Missing tenant isolation tests, graceful degradation, pricing uncertainty |
| Documentation Quality | 🔴 Problematic | ~70+ audit docs, many stale/contradictory, see Part III |

**Bottom line**: The system is architecturally coherent at the pipeline level but incomplete at the output/presentation level. The "aha moment" from the UX journeys — 15 minutes from WhatsApp to personalized options — depends on NB03 output rendering that doesn't exist. The monolith problem (Part I) is real and blocks progress. The documentation problem (Part III) is creating false confidence about what's implemented vs what's planned.

---

# PART III: DOCUMENTATION COMPLETENESS AUDIT

**421+ documents in Docs/. 69 audit/review/findings documents alone. Here is what's wrong.**

---

## Audit Process

Three parallel agents audited:
1. Core policy/spec/GTM docs (~20 files)
2. Discussion docs, status docs, roadmap docs (~15 files)
3. Wave/planning/audit/exploration docs (~25 files)

Total docs read: ~60 key files across all categories.

---

## Findings: By Severity

### CRITICAL (5 findings)

| # | File(s) | Issue |
|---|---------|-------|
| C1 | `FROZEN_SPINE_STATUS.md:142` | **Test count: "127+ tests passing."** Actual: 1,104 test functions. 9x understatement. This doc is treated as frozen spine authority but metrics are wildly stale (from April 15). |
| C2 | `AUDIT_AND_INTELLIGENCE_ENGINE.md` | **Reads as a working feature spec.** Describes "Wasted Spend Detection," "Fit-Score Framework," "Market Flywheel," "Audit Output Report" as if operational. Has NO date, NO status markers, NO indication that anything is implemented. Could mislead contributors into thinking these features exist. Reality: P2, not implemented. |
| C3 | `IMPLEMENTATION_BACKLOG_PRIORITIZATION.md:14` | **"P0-01 - Suitability Audit" still listed as P0.** Suitability was implemented (Tier 1+2, 7 files in `src/suitability/`, 23 tests) by April 18. Backlog doc from April 22 never updated. Top priority is already done. |
| C4 | `PHASE_3456_COMPLETION_HANDOFF.md:6,124` | **"960 tests passed" — suspicious math.** Doc claims 960 total (251 new + 42 baseline). 251+42 = 293, not 960. Pre-existing test count inflated or misattributed. With 40 pre-existing failures + 13 skipped = 53 non-passing, "Launch Ready: Yes" verdict is not credible. |
| C5 | `dashboard_homepage_ui_2026-04-29.md:462` | **References non-existent file**: `Docs/discussions/calendar_availability_2026-04-29.md`. This file doesn't exist. Same error in `itinerary_builder`. |

### HIGH (9 findings)

| # | File(s) | Issue |
|---|---------|-------|
| H1 | `FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`, `DISCUSSION_LOG.md` | **"No Streamlit implementation path."** But `app.py` (575 lines) is still in repo root. Streamlit is in `pyproject.toml`. Contradiction persists for 17+ days. |
| H2 | `Sourcing_And_Decision_Policy.md:19` | **Uses `PRESENT_BRANCHES` as decision state.** Actual frozen spine defines `BRANCH_OPTIONS`. Direct contradiction between policy docs. |
| H3 | Multiple April 28 audits | **Line counts stale.** All April 28 docs claim `server.py` = 2,644 lines. Actual: 3,535 (+34%). `persistence.py` claimed 1,115 lines. Actual: 1,407 (+26%). Audits were already stale when written. |
| H4 | Multiple April 27-28 audits | **Test file count inconsistent.** `agentic_pipeline_audit`: 53 files. `ARCHITECT_REVIEW_V2`: 63. `COMPREHENSIVE_REVIEW_V2`: 64. `ARCHITECTURE_REVIEW_2026-04-28`: 67. `CONSOLIDATED_AUDIT`: 67. Actual: 71. Spread of 53→71 in 1 day across docs. |
| H5 | `FRONTEND_WORKFLOW_IMPLEMENTATION_CHECKLIST_2026-04-16.md` | **All 23 tasks unchecked, status "Planned."** Frontend is live at localhost:3000 with dashboard, inbox, workbench. Checklist predates Next.js work and was never updated. |
| H6 | `AGENTIC_PIPELINE_CODE_AUDIT_2026-04-27.md:131-138` | **Line number references stale.** Claims `server.py:560` has hardcoded `agency_id`. File has grown 900+ lines since. Code has moved. Auditors made production-blocking recommendations based on wrong line numbers. |
| H7 | `agentic_pipeline_audit_2026-04-27.md`, `AGENTIC_PIPELINE_CODE_AUDIT` | **Both claim `src/agents/` is empty.** Actual: `src/agents/recovery_agent.py` exists. False claim that all agent infrastructure is missing. |
| H8 | `IMPLEMENTATION_PLAN_D001_D003_2026-04-23.md` | **Should have been deleted.** Handoff doc explicitly says: "Delete `IMPLEMENTATION_PLAN_D001_D003_2026-04-23.md` (superseded by this handoff)." File still exists. |
| H9 | `PHASE2_CALL_CAPTURE_IMPLEMENTATION.md:214,278` | **(a) Misclassification**: `frontend/src/app/api/trips/route.ts` listed under "Backend" — it's a frontend BFF route. **(b) Contradiction**: "No database schema changes needed (JSON storage)." But `alembic/versions/add_follow_up_due_date_to_trips.py` migration exists. |

### MEDIUM (16 findings)

| # | File(s) | Issue |
|---|---------|-------|
| M1 | `WAVES_1_11_FIRST_PRINCIPLES_ANALYSIS.md:80` | **Self-identified component naming mismatch**: `RecoveryHeader.tsx` in docs vs `FeedbackPanel.tsx`/`CriticalAlertBanner` in code. Identified but never resolved. |
| M2 | `dashboard_homepage_ui_2026-04-29.md:403-404` | **Claims `human_agent_model` was "SKIPED."** That doc was actually written (380 lines, substantive). |
| M3 | `MASTER_PHASE_ROADMAP.md:15,32-33` | **Phase 2 status "Active."** From April 22. Later handoffs show significant work completed since. Status never updated. |
| M4 | `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md` | **No phase status markers used.** Doc references `planned/active/partially shipped/complete` vocabulary but no phase in doc body actually uses it. |
| M5 | `DESIGN_REVIEW_FRONTEND_2026-04-23.md:46,330,344` | **(a) Stale routes**: References `/workspace/[tripId]/intake` — actual routes use `/(agency)/trips/[tripId]/`. **(b) D-003/D-006 references**: `CardAccent` (already removed) and table view toggle (may not be at expected path). |
| M6 | `system_architecture_plan_2026-04-29.md:228-269` | **Proposes API routes that don't exist.** `/api/enquiries`, `/api/customers`, `/api/bookings`, etc. — none in `spine_api/routers/`. Plan presented as architecture spec without implementation status. |
| M7 | `IMPLEMENTATION_HANDOFF_D001_D003_2026-04-23.md:65` | **Type-check failure reference stale.** References `api/inbox/route.ts:251` — file may no longer exist or issue may be fixed. |
| M8 | `FRONTEND_AUDIT_2026-04-28.md:43` | **`dangerouslySetInnerHTML` at `page.tsx:279-280`.** Flagged as P0 critical in April 28 audit. Grep confirms 2 occurrences still present. Unfixed. |
| M9 | `DASHBOARD_GOVERNANCE_WIRING_PLAN_2026-04-20.md:41-59` | **Proposes `src/analytics/calculations.py`.** 12 days later, file doesn't exist. Never implemented. |
| M10 | `ARCHITECT_REVIEW_V2.md`, `IMPROVE_ARCHITECTURE_FINDINGS.md` | **Both propose `src/ports/` module.** Does not exist. Cross-boundary import problem identified but fix never executed. |
| M11 | `IMPROVE_ARCHITECTURE_FINDINGS.md:136-143` | **Proposes `src/frontier/` package.** Does not exist. Frontier code still lives in `src/intake/`. |
| M12 | `SPINE_HARDENING_PLAN_STAGE_2_2026-04-15.md:159` | **Mandated creating `Docs/PHASE_B_MERGE_CONTRACT.md`.** 17 days later, doc doesn't exist. Multiple docs reference it — all pointing at void. |
| M13 | `UNIFIED_COMMUNICATION_AND_CHANNEL_STRATEGY.md` | **Pure vision doc — zero implementation.** Describes `CommunicationThread`, WhatsApp WATI integration, `shareToken`, `Client Portal`, Ghost Concierge — none exist. Sits alongside operational docs with no "VISION" marker. |
| M14 | `SYSTEM_INTEGRITY_PLAN.md:10-21,27` | **References gap of 1,054** between dashboard vs inbox. May no longer exist after Wave 7-10 URL-state fixes. Proposes `ScenarioProvider`, `GET /api/system/audit/orphans` — never built. |
| M15 | Multiple docs April 22-28 | **Severity inconsistency**: Dockerfile rated CRITICAL/HIGH/P0-01 across docs. April 22 docs don't mention it (predates finding). Reader of older docs has zero awareness. In reality, Dockerfile is a deployment option only — local dev uses `uv run uvicorn`, no Docker dependency. 15-min fix when needed for Render/Fly. |
| M16 | `INDEX.md:27` | **Links to SUPERSEDED doc**: `FRONTEND_SUITABILITY_DISPLAY_SPEC.md` (declares itself superseded on line 3). Replacement 2026-04-22 docs not in INDEX. D6 architecture decision exists but is hidden under D4 grouping. |

### LOW (14 findings)

| # | File(s) | Issue |
|---|---------|-------|
| L1 | `HYBRID_DECISION_ARCHITECTURE_2026-04-16.md:832-843` | **Quick start checklist items unchecked.** `hybrid_engine.py`, rules, cache_schema all exist. Checklist was planning doc, never updated. |
| L2 | `GTM_AND_DATA_NETWORK_EFFECTS.md`, `PRICING_AND_CUSTOMER_ACQUISITION.md` | **Reference imaginary URLs**: `audit.agency-os.com`, `agency-os.com/check`. Normal for pre-launch but should be annotated. |
| L3 | `QUESTION_BANK_AND_TAXONOMY.md` | **No date, version, or status.** Some taxonomies ARE in code (`suitability/catalog.py`), others aren't. Impossible to tell what's real. |
| L4 | `ROUTING_STRATEGY.md` | **No date, no status markers.** Describes two-loop system including offline autoresearch — offline loop not started. Reads as spec, not status. |
| L5 | `DATA_ARCHITECTURE.md:98-101` | **Path calculation bug in code example.** `.parent.parent` resolves to `src/`, not repo root. Code copied from docs would break. |
| L6 | `INDEX.md` | **Missing major docs**: D6 architecture decision (exists but hidden under D4). Multiple 2026-04-22 replacement docs not surfaced. |
| L7 | `INDUSTRY_PROCESS_GAP_ANALYSIS_2026-04-16.md:365` | **"2 of 15 working" score stale.** From April 16. Suitability, analytics, decision rules all implemented since. |
| L8 | `agentic_pipeline_audit_2026-04-27.md:277` | **Flags `page.bak.tsx` as "backup file."** File no longer exists. Stale finding. |
| L9 | `COMPREHENSIVE_REVIEW_FINDINGS.md:172-173` | **Flags `streamlit` and `rich` as potentially unused.** Never verified. If actually unused, dead deps. |
| L10 | `.agent/SESSION_CONTEXT.md` | **All retrieval sections skipped.** Generated 2026-05-02 but provides zero context. Skip-index = intentional startup behavior, but doc is valueless as-is. |
| L11 | `DESIGN.md:104-105` | **Font loading comments** say "(loaded via next/font)" — predates/coincides with Next.js decision. May not reflect reality. |
| L12 | `dependency_management_2026-04-29.md:92-93,105` | **(a) Next.js 14 claimed** — actual: Next.js 16. **(b) Version typo**: `^7.0.0.0` (8 segments, should be 4). |
| L13 | `WAVES_1_11_FIRST_PRINCIPLES_ANALYSIS.md:33` | **Claims `BUDGET_FEASIBILITY_TABLE` is in `src/intake/decision.py`.** Actually in `src/decision/rules/`. Partially extracted, doc stale on location. |
| L14 | `WAVE_1_TO_10_SUMMARY_2026-04-22.md:185` | **Lists itself as an artifact to attach.** Self-referential. Copy-paste error. |

---

## Documentation Health Summary

| Metric | Count |
|--------|-------|
| Total docs in Docs/ | 421+ |
| Docs audited in detail | ~60 |
| Critical findings | 6 |
| High findings | 9 |
| Medium findings | 16 |
| Low findings | 14 |
| **Total issues found** | **45** |

### By Category

| Category | Count | Key Pattern |
|----------|-------|-------------|
| Stale line/file references | 8 | Audits cite wrong line numbers, files that moved/grew |
| Claim-vs-reality (features claimed but absent) | 7 | Audit mode, communication channels, analytics calculations |
| Status not updated (done marked as undone) | 6 | Test counts, phase completion, backlog items |
| Missing documents (referenced but not created) | 4 | PHASE_B_MERGE_CONTRACT, calendar_availability, ports/, calculations.py |
| Contradictions between docs | 4 | Decision state names, test counts, Streamlit, product names |
| Stale routes/paths | 3 | Frontend routes changed from `/workspace/` to `/(agency)/` |
| Dead code/docs not cleaned up | 3 | Implementation plan not deleted as instructed, page.bak.tsx flagged but gone, CardAccent removed but docs reference it |
| Vision docs without status | 3 | AUDIT_AND_INTELLIGENCE_ENGINE, COMMUNICATION_STRATEGY, QUESTION_BANK |
| Version/Dep issues | 2 | Next 14 claimed vs 16 actual; Dockerfile has hyphen-vs-underscore naming issue (deployment only — local dev uses uv run uvicorn, no Docker dependency) |
| Other (typos, self-refs, severity inconsistency) | 5 | Various minor issues |

### Root Causes

1. **Audit Parallelism without Synchronization**: The 7 April 28 audits were written simultaneously against code that was simultaneously growing. They cross-referenced each other but measured different HEAD states.

2. **Docs-as-Plans Never Graduated**: Multiple docs (`HYBRID_DECISION_ARCHITECTURE`, `FRONTEND_WORKFLOW_CHECKLIST`, `PHASE_B_MERGE_CONTRACT`) were written as planning docs with action items. Implementation happened but the plans were never updated to reflect completion.

3. **Streamlit Zombie**: The Streamlit→Next.js migration was decided April 15. `app.py` still exists May 2. Multiple docs claim "no Streamlit" while the app remains present. This half-migration creates confusion.

4. **No Documentation Owner**: No single doc is canonical for "what's implemented." `FROZEN_SPINE_STATUS.md`, `STATUS_ASSESSMENT_2026-04-21.md`, `MASTER_GAP_REGISTER_2026-04-16.md`, `COVERAGE_MATRIX_2026-04-15.md` all attempt to cover implementation status but all are stale by days to weeks.

5. **Test Count as Vanity Metric**: Test count is cited as evidence of quality in 6+ docs, but no two docs agree on what the count is (range: 53→71 for test files, 127→1,104 for test functions). If test count is used as a quality signal, it needs to be a single source of truth.

---

## Recommended Documentation Actions

### Immediate (P0)

| # | Action | Effort |
|---|--------|--------|
| 1 | Fix Dockerfile (underscores, not hyphens) | 15 min |
| 2 | Update `FROZEN_SPINE_STATUS.md` test count to actual | 5 min |
| 3 | Add status header to `AUDIT_AND_INTELLIGENCE_ENGINE.md`: "⚠️ PLANNING — Not yet implemented. Expected: Phase D" | 5 min |
| 4 | Remove `IMPLEMENTATION_PLAN_D001_D003_2026-04-23.md` (as handoff instructed) | 5 min |
| 5 | Update `IMPLEMENTATION_BACKLOG_PRIORITIZATION.md` — mark P0-01 as done | 5 min |

### Short-term (P1)

| # | Action | Effort |
|---|--------|--------|
| 6 | Run `rg "streamlit" --include "*.py"` to verify usage. If unused, remove from deps. If used (app.py), either delete app.py or update docs to acknowledge its existence. | 30 min |
| 7 | Add `presentation_profile` field (even as stub) to packet model — placeholder for D2 consumer surface | 30 min |
| 8 | Mark vision-only docs with standardized header: "📋 PLANNING/VISION — Not yet implemented" | 30 min |
| 9 | Update `INDEX.md` to link replacement docs, not superseded ones | 30 min |
| 10 | Create `Docs/PHASE_B_MERGE_CONTRACT.md` or mark task as DEFERRED in hardening plan | 30 min |

### Medium-term (P2)

| # | Action | Effort |
|---|--------|--------|
| 11 | Establish single source of truth for test counts (this doc, updated per sprint) | 1 day |
| 12 | Archive or delete clearly obsolete docs into `Docs/archives/` with pointer files: `STATUS_MATRIX.md`, `COVERAGE_MATRIX_2026-04-15.md`, `DESIGN_REVIEW_FRONTEND_2026-04-23.md` | 1 day |
| 13 | Create `Docs/README.md` as doc map — what to read for what purpose | 1 day |
| 14 | Standardize doc header format: Date, Status (Planning/Active/Complete/Stale), Owner, Last Verified Against Code At | 0.5 day |

---

# PART IV: CONSOLIDATED MASTER ACTION PLAN

This combines ALL action items from Parts I, II, and III into a single dependency-ordered plan.

## Phase A: Immediate Fixes (Do Now — Zero Dependencies)

| # | Source | Action | Effort |
|---|--------|--------|--------|
| A1 | Part III C1 | Fix Dockerfile (underscores not hyphens) | 15 min |
| A2 | Part III C2 | Update FROZEN_SPINE_STATUS test count | 5 min |
| A3 | Part III C3 | Add status header to AUDIT_AND_INTELLIGENCE_ENGINE.md | 5 min |
| A4 | Part III H8 | Delete IMPLEMENTATION_PLAN_D001_D003_2026-04-23.md | 5 min |
| A5 | Part III C4 | Update backlog — mark P0-01 done | 5 min |
| A6 | Part III H1 | Resolve Streamlit: delete app.py or update docs | 30 min |

**Total Phase A**: ~1 hour

## Phase B: Documentation Cleanup (This Week)

| # | Source | Action | Effort |
|---|--------|--------|--------|
| B1 | Part III P1 | Add status headers to vision-only docs | 30 min |
| B2 | Part III M16 | Update INDEX.md — fix superseded links, add D6 entry | 30 min |
| B3 | Part III M12 | Resolve PHASE_B_MERGE_CONTRACT — create or defer | 30 min |
| B4 | Part III P2 | Standardize doc headers (Date, Status, Owner, Verified At) | 1 day |
| B5 | Part III P2 | Create Docs/README.md as doc map | 1 day |
| B6 | Part III P2 | Archive obsolete docs to archives/ | 1 day |
| B7 | Part III L9 | Verify streamlit/rich usage, remove dead deps | 30 min |

**Total Phase B**: ~4 days

## Phase C: Critical Code Refactors (Next 2 Weeks)

| # | Source | Action | Effort |
|---|--------|--------|--------|
| C1 | Part I A1 | Decompose server.py into routers + extract OTel | 3-4 days |
| C2 | Part I A2 | Split extractors.py into domain modules | 3-4 days |
| C3 | Part I A3 | Split decision.py into gap/feasibility/confidence/router | 3-4 days |
| C4 | Part I A4 | Resolve ValidationReport contract drift | 0.5 day |
| C5 | Part I A5 | Rename DecisionResult collision (hybrid_engine) | 0.5 day |
| C6 | Part I P0 | Add snapshot/clone to CanonicalPacket | 1 day |
| C7 | Part I P0 | Wire events to persistent store (not in-memory) | 2 days |
| C8 | Part I C3 | Add pipeline timeout | 1 day |
| C9 | Part I C6 | Validate LLM responses against schema | 1 day |

**Total Phase C**: ~16-18 days

## Phase D: Missing Primitives (Weeks 3-4)

| # | Source | Action | Effort |
|---|--------|--------|--------|
| D1 | Part I B1 | Implement per-person utility scoring | 2-3 days |
| D2 | Part I B2 | Implement wasted spend calculation | 1 day |
| D3 | Part I P0 | Implement rendered itinerary option output | 5-7 days |
| D4 | Part I P0 | Implement template filling in strategy | 2 days |
| D5 | Part I B5 | Add NB03 output quality gate | 2 days |
| D6 | Part I D1 | Make activity catalog loadable from DB | 2 days |
| D7 | Part I D1 | Make validation thresholds agency-configurable | 2 days |
| D8 | Part II.1 | Build numeric feasibility model (replace hardcoded table) | 3-4 days |
| D9 | Part II.4 | Build structured output model (ItineraryOption) | 2 days |

**Total Phase D**: ~21-25 days

## Phase E: Hardening (Weeks 5-6)

| # | Source | Action | Effort |
|---|--------|--------|--------|
| E1 | Part I C8 | Migrate settings from SQLite to PostgreSQL | 2 days |
| E2 | Part I C9 | Add settings audit trail | 1 day |
| E3 | Part I C10 | Add feature flag system | 2 days |
| E4 | Part I C1 | Move LLM prompts to template files | 2 days |
| E5 | Part I C7 | Add structured data leakage scanning | 1 day |
| E6 | Part II.3 | Add SourcingPolicy abstraction (even without data) | 2 days |
| E7 | Part II.1 | Add constraint classification (hard/soft/weighted) | 2 days |
| E8 | Part I P0 | Make pipeline composition configurable | 2 days |
| E9 | Part II.1 | Implement idempotent pipeline execution | 2 days |

**Total Phase E**: ~16 days

## Phase F: Features on Clean Foundation (Weeks 7-10)

| # | Source | Action | Effort |
|---|--------|--------|--------|
| F1 | Vision | PDF/URL document extraction (audit mode) | 4-5 days |
| F2 | Vision | Dynamic question router | 3-4 days |
| F3 | Vision | Mode-specific NB03 builders | 4-5 days |
| F4 | Vision | WhatsApp/email output formatters | 3-4 days |
| F5 | Vision | Consumer presentation_profile (D2) | 2 days |
| F6 | Vision | D5 override feedback bus | 4-5 days |
| F7 | Vision | D4 Tier 3 LLM suitability scorer | 3-4 days |
| F8 | Vision | Eval harness scaffold (D6) | 3-4 days |
| F9 | Vision | Revision graph / diff model | 3-4 days |
| F10 | Vision | Operator override protocol with full audit trail | 3-4 days |

**Total Phase F**: ~32-43 days

---

# GRAND TOTAL

| Phase | Work | Calendar Time |
|-------|------|---------------|
| A: Immediate Fixes | 6 items | ~1 hour |
| B: Doc Cleanup | 7 items | ~4 days |
| C: Critical Refactors | 9 items | ~16-18 days |
| D: Missing Primitives | 9 items | ~21-25 days |
| E: Hardening | 9 items | ~16 days |
| F: Features | 10 items | ~32-43 days |
| **Total** | **50 action items** | **~89-106 calendar days** |

**This is ~3-4 months of focused engineering work to go from "spine works, output doesn't" to "production-ready agency OS with structured output, audit mode, per-person suitability, and multi-channel delivery."**

---

*This document — ARCHITECTURE_BASELINE_AUDIT_2026-05-02.md — is now the single authoritative source for:*
- *Component-by-component architectural ratings (Part I)*
- *Independent first-principles assessment (Part II)*
- *Documentation completeness and contradictions (Part III)*
- *Consolidated dependency-ordered action plan (Part IV)*

*All subsequent implementation work should reference this document. All future docs should include standardized headers (Date, Status, Verified Against Code At).*
