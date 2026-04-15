# Frozen Spine Status (Pre-UI)

Date: 2026-04-14

This document records what is real, heuristic, stubbed, and intentionally postponed
in the NB01/NB02/NB03 intake spine as of the pre-UI freeze.

## HONEST ASSESSMENT: What "Frozen" Means

**The spine is frozen enough for UI/workbench work.**
**The semantic extraction problem is NOT solved.**

The extraction layer remains fundamentally regex/pattern-based. This is an honest
temporary baseline, not the final intelligence layer. The architecture supports
future hybrid extraction (regex + NER/LLM) without breaking changes.

---

## REAL (verified, tested, production-quality)

### Data Model & Contracts
- CanonicalPacket v0.2 data model with fact/derived/hypothesis separation
- AuthorityLevel hierarchy and Slot provenance tracking
- DecisionResult with 5 decision states, MVB-by-stage, operating mode routing
- Schema validation (LEGACY_FIELD_NAMES, DERIVED_ONLY_FIELDS, maturity tags)

### Safety & Boundary (Structurally Enforced)
- Structural traveler-safe sanitization (SanitizedPacketView)
- OwnerConstraint visibility semantics (internal_only vs traveler_safe_transformable)
- Leakage detection with plural/variant support (FORBIDDEN_TRAVELER_CONCEPTS)
- Strict leakage enforcement mode (enforce_no_leakage raises ValueError on leakage)
- Separate builder paths enforced at function signature level:
  - `build_traveler_safe_bundle(strategy, decision)` — NO packet access
  - `build_internal_bundle(strategy, decision, packet)` — packet required
- Leakage detection runs automatically in the build path

### Decision Engine (NB02)
- Stage-gated blocker evaluation (discovery/shortlist/proposal/booking)
- Budget feasibility check with conservative multi-candidate handling
- Operating mode routing:
  - Follow-up mode: demotes soft blockers (re-engagement, not re-collection)
  - Cancellation mode: clears soft blockers, adds cancellation_policy contradiction
  - Emergency mode: suppresses non-critical soft blockers
  - Audit mode: adds budget_feasibility contradiction (both infeasible + tight)
- Feasibility caching (computed once, reused in risk flags)
- Urgency computation from date_end (verified maturity)
- Confidence scoring: authority-weighted average with unknown penalties

### Strategy & Output (NB03)
- SessionStrategy and PromptBundle generation
- Tone scaling based on confidence (cautious → measured → confident → direct)
- Question ordering (constraint-first)
- Legacy alias deprecation warnings

### Extraction Hardening (Regex-Based)
- **Pattern-based (not LLM) extraction** — honest temporary baseline
- Freeform text extraction for 30+ fields using regex patterns
- Past-trip destination filtering (prevents contamination of current intent)
- Origin extraction bounding (max 3 words, destination guard, origin-pattern guard)
- Ambiguity detection on source text spans (not just extracted values)
- Date extraction with fuzzy phrase support ("sometime in May", "around March")
- Budget parsing with scope detection (per_person, per_night, total)
- Party composition extraction (adults/children/elderly with ages)

---

## HEURISTIC (works, but based on estimated/keyword data, not verified market data)

- Budget feasibility table (BUDGET_FEASIBILITY_TABLE): estimated min_per_person costs
- domestic_or_international classification: based on static destination sets
- is_repeat_customer detection: keyword-based ("past customer", "repeat", etc.)
- Sub-group extraction: regex-based pattern matching
- Operating mode classification: keyword-based routing
- Budget scope detection: keyword-based
- Trip purpose/style extraction: keyword pattern matching

---

## STUB (placeholder, not real logic)

- sourcing_path derived signal: always "open_market" or "network", no real supplier data
- cancellation_policy contradiction: placeholder "pending_policy_lookup"
- LLM prompt execution: PromptBundle is generated but never sent to an LLM
- Internal bundle: system_context and user_message are built but never rendered
- Normalizer city normalization: basic matching, not comprehensive

---

## INTENTIONALLY POSTPONED (not in scope for pre-UI freeze)

- UI/workbench implementation
- FastAPI/Flask/HTTP layer
- Database/auth/infrastructure
- Provider/model abstraction (LLM backend)
- Recommendation engine
- Full agent orchestration loop
- Real supplier/package data integration
- Document verification (passport/visa API calls)
- Payment processing integration
- trip_duration_days and seasonality derived signals (removed from traveler-safe list until implemented)
- Full cancellation policy engine (currently detects mode but does not resolve policy)
- Post-trip mode: skips blocker logic (intentional, not a stub)
- Owner review mode: financial data handling (currently adds contradiction, not full audit)
- **Semantic extraction quality upgrades (NER/span layer, LLM-backed extraction)**

---

## What the UI may assume

1. CanonicalPacket v0.2 schema is stable — no breaking field name changes
2. DecisionResult has exactly 5 decision states — no new ones without versioning
3. build_traveler_safe_bundle(strategy, decision) is the sole traveler-facing entry point
4. build_internal_bundle(strategy, decision, packet) is the sole internal entry point
5. The traveler builder NEVER receives the raw packet — enforced at function signature level
6. Leakage detection runs automatically in the build path (strict mode optional)
7. All derived signals have maturity tags (stub/heuristic/verified)
8. Operating mode affects routing behavior, not just labeling
9. Past-trip destinations do not contaminate current destination intent
10. Origin cities are filtered from destination candidates (not perfect, but guarded)

---

## What the UI should NOT assume

1. Extraction is semantic/LLM-based — it is regex-pattern based
2. Extraction handles all edge cases gracefully — it is a baseline
3. All origin cities are known — only major Indian cities + destination list
4. All destinations are known — only static list of ~40 destinations
5. Budget feasibility is based on real market data — it is heuristic estimates

---

## Test Coverage

- 116 tests passing (85 original + 31 e2e freeze-pack)
- 5 realistic scenarios: messy family discovery, past customer, audit mode, coordinator group, emergency/cancellation
- Edge cases: fuzzy dates, origin bounding, past-trip filtering, ambiguity detection, strict leakage enforcement

---

## Post-Freeze Rules

### Phase A (Now): UI/Workbench
- Treat spine as read-mostly
- Only patch for real surfaced bugs
- Build flow simulation on deterministic baseline

### Phase B (Later): Hybrid Extraction Track
- Keep regex as baseline/fallback
- Add NER/span layer
- Add schema-constrained LLM extraction
- Merge + validate
- Compare against deterministic baseline in eval mode

**Frozen does not mean "done." Frozen means "stable enough to build on top of."**
