# Test Gap Analysis: 30 Scenarios → NB01 / NB02 / NB03 Coverage

**Date**: 2026-04-12
**Method**: Cross-referenced all 30 persona scenarios (`Docs/personas_scenarios/`) + 30 technical scenarios (`data/fixtures/`) against actual NB01/NB02/NB03 notebook code, `15_MISSING_CONCEPTS.md`, and test results.
**Sources**: `Docs/personas_scenarios/`, `data/fixtures/test_scenarios.py`, `notebooks/02_PERSONA_SCENARIO_COVERAGE.md`, `notebooks/15_MISSING_CONCEPTS.md`, `notebooks/02_SCENARIO_TEST_RESULTS.md`, actual notebook code.

---

## Two Parallel Scenario Systems

This project has **two independent sets of 30 scenarios** that must be understood separately:

| System | Location | What It Tests | Run Command |
|--------|----------|---------------|-------------|
| **Technical Scenarios (A1–F5)** | `data/fixtures/test_scenarios.py` | CanonicalPacket factories → NB02 decision correctness | `uv run python data/fixtures/run_all_tests.py` |
| **Persona Scenarios (P1-S1 through #30)** | `Docs/personas_scenarios/` | Real-world narratives → full pipeline behavior | Documentation only (no runner yet) |

The **technical scenarios** test NB02's internal logic (authority levels, contradictions, stage progression). They all pass.

The **persona scenarios** test real-world user situations. Only **5 of 30 are fully covered** by existing tests.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total persona scenarios | 30 |
| ✅ Fully covered | 5 (17%) |
| ⚠️ Partially covered | 7 (23%) |
| ❌ Missing (in-scope) | 9 (30%) |
| ❌ Out of scope (different systems) | 9 (30%) |
| P0 gaps (block production) | 5 |
| P1 gaps (block beta) | 5 |
| P2 gaps (post-MVP) | 8 |

**The spine works**: NB01→NB02→NB03 golden path is clean and proven (NB05). But it covers only the happy path — messy, real-world inputs expose significant gaps.

---

## Coverage Map: All 30 Persona Scenarios

### Legend
| Symbol | Meaning |
|--------|---------|
| ✅ | Fully covered — existing code + tests validate this |
| ⚠️ | Partially covered — some pieces work, critical pieces missing |
| ❌ | Missing entirely — no code, no test |
| ⬜ | Out of scope — belongs to a different system |

### P1: Solo Agent (Scenarios 1–5)

| # | Scenario | NB01 | NB02 | NB03 | Overall | Key Gap |
|---|----------|------|------|------|---------|---------|
| 1 | 11 PM WhatsApp Panic | ⚠️ History lookup not implemented | ⚠️ Budget feasibility math missing | ⚠️ Urgency detection exists but not wired to decision | **⚠️ Partial** | Can't flag "4-5L for 5 in Europe" as unrealistic |
| 2 | Repeat Customer Who Forgot | ❌ No `customer_id`, `past_trips`, `is_repeat_customer` | ✅ Works IF NB01 provides enriched packet | ⚠️ No history-aware questions | **⚠️ Partial** | Asks returning customer the same questions |
| 3 | Customer Changes Everything | ⚠️ `event_cursor` exists but no revision counting | ⚠️ Budget feasibility math missing (15MC #13) | ❌ Missing | **⚠️ Partial** | Accepts impossible budgets after revisions |
| 4 | Visa Problem at Last Minute | ❌ No `passport_status`, `visa_requirements` | ❌ No `valid_passport`/`valid_visa` hard blockers | ❌ `EMERGENCY_PROTOCOL` not in schema | **❌ Missing** | Could book without valid passport |
| 5 | Multi-Party Group Trip | ❌ No `sub_groups` field | ❌ No multi-party readiness logic | ❌ No coordinator dashboard | **❌ Missing** | Can't track 3 families independently |

### P2: Agency Owner (Scenarios 6–10)

| # | Scenario | NB01 | NB02 | NB03 | Overall | Key Gap |
|---|----------|------|------|------|---------|---------|
| 6 | Quote Disaster Review | ⬜ Owner review workflow | ⬜ Out of scope | ⬜ Out of scope | **⬜ Out of Scope** | Needs owner dashboard |
| 7 | Agent Who Left | ⬜ Knowledge transfer / CRM | ⬜ Out of scope | ⬜ Out of scope | **⬜ Out of Scope** | Needs knowledge base |
| 8 | Margin Erosion | ❌ No margin model (15MC #2) | ❌ No `margin_risk` derived signal | ❌ Missing | **❌ Missing** | Unprofitable quotes undetected |
| 9 | Training Time Problem | ✅ Confidence scoring | ✅ Confidence scoring works | ✅ Covered | **✅ Full** | — |
| 10 | Weekend Panic | ❌ Document tracking not implemented | ❌ Missing | ❌ Missing | **❌ Missing** | Needs document tracker |

### P3: Junior Agent (Scenarios 11–15)

| # | Scenario | NB01 | NB02 | NB03 | Overall | Key Gap |
|---|----------|------|------|------|---------|---------|
| 11 | First Solo Quote | ✅ | ✅ Low confidence → ASK_FOLLOWUP | ✅ | **✅ Full** | — |
| 12 | Visa Mistake Prevention | ⚠️ `traveler_details` is booking blocker but no `passport_status` | ⚠️ Partial | ❌ Missing | **⚠️ Partial** | Visa-specific checks missing |
| 13 | "Is This Right?" Check | ❌ Cost completeness validation | ❌ Needs pricing data | ❌ Missing | **❌ Missing** | Can't verify all costs included |
| 14 | Don't Know Answer | ⬜ Knowledge base lookup | ⬜ Out of scope | ⬜ Out of scope | **⬜ Out of Scope** | Needs KB / FAQ system |
| 15 | Comparison Trap | ❌ Competitor quote analysis | ❌ Missing | ❌ Missing | **❌ Missing** | Can't compare vs competitors |

### S1/S2: Customers (Scenarios 16–20)

| # | Scenario | NB01 | NB02 | NB03 | Overall | Key Gap |
|---|----------|------|------|------|---------|---------|
| 16 | Comparison Shopper | ✅ | ✅ PROCEED_TRAVELER_SAFE when complete | ✅ | **✅ Full** | — |
| 17 | Post-Booking Anxiety | ⬜ Post-booking system | ⬜ Out of scope | ⬜ Out of scope | **⬜ Out of Scope** | Needs post-booking comms |
| 18 | Trip Emergency | ⚠️ STOP_NEEDS_REVIEW works | ❌ `EMERGENCY_PROTOCOL` with options not in DecisionResult | ❌ Missing | **⚠️ Partial** | No emergency options output |
| 19 | Preference Collection Nightmare | ✅ Contradiction detection | ✅ Works | ✅ | **✅ Full** | — |
| 20 | Document Chaos | ❌ Per-person doc tracking | ❌ Missing | ❌ Missing | **❌ Missing** | Needs new data structure |

### Additional Scenarios (21–30)

| # | Scenario | NB01 | NB02 | NB03 | Overall | Key Gap |
|---|----------|------|------|------|---------|---------|
| 21 | Ghost Customer (No Response) | ❌ No engagement tracking | ❌ `LEAD_FOLLOWUP_REQUIRED` not a decision state | ❌ Missing | **❌ Missing** | No lead nurturing logic |
| 22 | Scope Creep (Free Consulting) | ❌ No revision counting / time ROI | ❌ `SET_BOUNDARIES` not a decision state | ❌ Missing | **❌ Missing** | No agent protection |
| 23 | Influencer Request | ❌ No influencer ROI tracking | ❌ No historical ROI calculation | ❌ Missing | **❌ Missing** | Accepts bad deals |
| 24 | Medical Emergency During Trip | ❌ No emergency keyword detection / insurance data | ❌ `EMERGENCY_PROTOCOL` decision state missing | ❌ Crisis protocol missing | **❌ Missing** | No crisis automation |
| 25 | Competing Family Priorities | ❌ No multi-party constraints | ⚠️ BRANCH_OPTIONS exists but no multi-party optimization | ❌ Consensus building missing | **⚠️ Partial** | Can't optimize across families |
| 26 | Last-Minute Cancellation | ❌ No cancellation policy engine | ❌ Policy-guided BRANCH_OPTIONS not implemented | ❌ Missing | **❌ Missing** | No structured cancellation |
| 27 | Referral Request | ❌ No referral tracking | ❌ `PROCEED_WITH_INCENTIVE` not a decision state | ❌ Missing | **❌ Missing** | No referral program |
| 28 | Seasonal Rush | ❌ No queue management | ❌ No allocation optimization | ❌ Missing | **❌ Missing** | FCFS instead of value-based |
| 29 | Package Customization | ❌ No dynamic pricing / availability checks | ❌ No margin recalculation | ❌ Missing | **❌ Missing** | Manual recalculation needed |
| 30 | Review Request (Post-Trip) | ❌ No trip completion tracking / sentiment | ❌ No post-trip engagement timing | ❌ Missing | **❌ Missing** | Random review timing |

---

## Deep Dive: 9 Specific Gap Areas

### 1. Ambiguity Handling

**Status**: ⚠️ Partially covered — **Critical Gap**

**What works**:
- NB03 has `detect_ambiguous_values(packet)` in `build_traveler_safe_strategy()` — adds confirmation questions even when NB02 says PROCEED_TRAVELER_SAFE
- NB05 golden path test checks for leakage (user_message must not contain "unknown", "hypothesis", etc.)

**What's missing**:
- NB02 does NOT detect ambiguity. A value like `"Andaman or Sri Lanka"` satisfies the hard blocker check because a value string exists
- The system cannot distinguish a definite value (`"Singapore"`) from an ambiguous one (`"maybe Europe"`, `"not sure yet"`)
- Test evidence: Scenario "WhatsApp Dump" (`test_scenarios_realworld.py`) explicitly documents: *"The system can't tell 'Andaman or Sri Lanka' is ambiguous vs 'Singapore' is definite. This is a KNOWN LIMITATION."*

**Where to fix**:
- **NB02**: Add `value_ambiguity` check that flags values containing `"or"`, `"maybe"`, `"not sure"`, `"thinking about"`, `"could be"` as partially unfilled
- **NB01**: Extract ambiguity signals during normalization (extraction_mode = `"ambiguous"`)
- **NB03**: Already handles the mitigation — adds confirmation questions. Just needs NB02 to detect the ambiguity first

**Scenarios affected**: P1-S1, #5 (WhatsApp Dump), S2-S3, F2 (normalized values test)

---

### 2. Urgency / Last-Minute

**Status**: ⚠️ Partially covered — **Medium Gap**

**What works**:
- NB03 has `detect_urgency(packet)` that checks if travel dates are within 7 days
- Adds risk flag: `"URGENT: Travel within 7 days — prioritize speed."` in session strategy
- Urgency adds "expedite booking" to risk flags

**What's missing**:
- Urgency detection is ONLY in NB03's strategy builders — NOT in NB02's decision logic
- Soft blockers (`trip_purpose`, `traveler_preferences`) still block PROCEED_TRAVELER_SAFE even for last-minute trips
- Test evidence: Scenario "Last-Minute Booker" returns `PROCEED_INTERNAL_DRAFT` instead of `PROCEED_TRAVELER_SAFE` because soft blockers remain
- 15MC gap analysis: *"This weekend, flying Friday → soft blockers still block PROCEED_TRAVELER_SAFE"*

**Where to fix**:
- **NB02**: When `detect_urgency()` returns true, downgrade soft blockers to advisory or suppress them entirely
- **NB03**: Already has urgency-aware strategy (skips soft blocker questions). Just needs NB02 to route correctly

**Scenarios affected**: P1-S4, #8 (Last-Minute Booker), #26 (Last-Minute Cancellation)

---

### 3. Budget Stretch

**Status**: ⚠️ Partially covered — **Medium Gap**

**What works**:
- NB03 has `detect_budget_stretch(packet)` that looks for stretch signals in value strings (e.g., `"200000 (flexible)"`, `"can stretch if it's good"`)
- Captures the signal and adds it to risk flags in session strategy

**What's missing**:
- The stretch signal is captured but NOT structurally parsed — it's just a string annotation
- **Budget Feasibility** (the bigger gap): No minimum-cost-per-destination logic at all
  - "3L for 6 people in Maldives" = ₹50K/person — physically impossible
  - Minimum realistic Maldives cost: ~₹80K/person
  - The system accepts this as a valid fact without flagging
  - 15MC #13: "Budget Feasibility Enforcement" — listed as MVP-now

**Where to fix**:
- **NB01**: Add derived signal `estimated_minimum_cost` (per person, per destination tier)
- **NB02**: Add `budget_feasibility` contradiction type — compare stated budget vs minimum viable cost for destination + composition
- **NB03**: Already surfaces stretch in risk flags. Just needs NB02 to flag feasibility violations

**Scenarios affected**: P1-S3, S2-S3, #3 (The Dreamer)

---

### 4. Audit Mode

**Status**: ❌ Missing entirely

**What it is**: Compare a proposed itinerary against market reality. Is the traveler getting value, or overpaying for a bad fit? This is the agency's wedge feature — proving value by finding waste the traveler couldn't see.

**What's missing**:
- No concept of itinerary comparison
- No market pricing benchmarks
- No fit scoring
- No `budget_efficiency` derived signal
- No `value_mismatch` contradiction (premium budget for budget destination, or vice versa)
- 15MC #8: Listed as "Later" priority — needs market pricing data first

**Where to fix**:
- **NB02**: Add derived signal `budget_efficiency` (budget vs typical cost for destination + composition)
- **NB02**: Add contradiction `value_mismatch`
- **NB03**: Add "I found a better option" strategy prompts

**Scenarios affected**: P3-S3, implied in audit-related scenarios

---

### 5. Multi-Party / Family Coordinator Flows

**Status**: ❌ Missing entirely

**What it is**: 3 families with different budgets, payment terms, and document statuses coordinating one trip. The system needs to track each sub-group independently and report collective readiness.

**What's missing**:
- `CanonicalPacket` has no `sub_groups` field
- No multi-party readiness detection in NB02
- No coordinator dashboard in any decision state or session strategy
- No per-group blocker checking
- Affects P1-S5 (3 families, different payments), #25 (competing family priorities), S2-S2 (document chaos per person)

**Where to fix**:
- **NB01**: Extend CanonicalPacket with `sub_groups: Dict[str, SubGroup]` where each sub-group has its own facts, budget, payment status, document status
- **NB02**: Add multi-group readiness check — iterate each sub-group, check blockers per group, compute collective readiness
- **NB03**: Add coordinator-aware prompts — generate per-group follow-up messages + group summary

**Scenarios affected**: P1-S5, #25, S2-S2

---

### 6. Visa / Passport Readiness

**Status**: ❌ Missing entirely (for booking stage)

**What it is**: Before booking international travel, verify all travelers have valid passports with sufficient expiry buffer, and visa requirements are understood and achievable within the timeline.

**What's missing**:
- `passport_status` is NOT a field in CanonicalPacket code
- `visa_requirements` is NOT a field in CanonicalPacket code
- The MVB (Minimum Viable Blocker) list mentions `valid_passport` and `valid_visa` as booking-stage hard blockers — but they're NOT in the actual code
- Only `traveler_details` is a booking-stage blocker currently
- 15MC #7: "Document Risk (Passport / Visa)" — listed as "Later" but is P0 for production

**Where to fix**:
- **NB01**: Add facts `passport_status` (valid / expiring_soon / expired / unknown per traveler) and `visa_requirements` (required / not_required / evisa / embassy, per destination)
- **NB02**: Add booking-stage hard blockers `valid_passport` and `valid_visa`
- **NB03**: Add document-aware session strategy (flag expiring passports, suggest visa timeline)

**Scenarios affected**: P1-S4, P3-S2, #24 (Medical Emergency — also needs insurance docs)

---

### 7. Repeat Customer Memory

**Status**: ❌ Missing entirely

**What it is**: Recognize returning customers by phone number / email, pull their history (past trips, preferences, complaints, budget patterns, document status), and avoid re-asking known questions.

**What's missing**:
- No `customer_id` field in CanonicalPacket
- No `is_repeat_customer` derived signal
- No `past_trips` or `trip_history` concept
- `source_envelope_ids` tracks envelopes but not customers
- The agency's biggest advantage — knowing the customer — is completely absent

**Where to fix**:
- **NB01**: Add fact `customer_id` (matched from phone/email), derived signal `is_repeat_customer`, fact `past_trips` (list of prior trips with key outcomes)
- **NB01**: Add `owner_notes` and `owner_constraints` for persistent agency knowledge (15MC #4)
- **NB02**: Use history to fill soft blockers (e.g., if customer previously said "vegetarian", don't ask again)
- **NB03**: Generate history-aware questions ("Last time you loved Atlantis — want something similar?")

**Scenarios affected**: P1-S2, P1-S5

---

### 8. Quote / Commercial Logic

**Status**: ❌ Missing entirely

**What it is**: Every quote has a margin. The agency needs to know if a trip is worth doing, what sourcing path to use (Internal Packages → Preferred Suppliers → Network → Open Market), and whether preferred suppliers are available.

**What's missing**:
- No margin model (15MC #2)
- No `margin_risk` derived signal
- No `estimated_cost_range`
- No sourcing hierarchy (15MC #1) — this is the agency's CORE DIFFERENTIATOR
- No preferred supplier concept (15MC #3)
- No `sourcing_path` derived signal
- No `agency_target_margin`

**Where to fix**:
- **NB02**: Add derived signal `sourcing_path` (internal / preferred / network / open), derived signal `margin_risk` (budget too tight for viable margin), derived signal `preferred_supplier_available`
- **NB01**: Add fact `agency_target_margin` (owner-seeded context)
- **NB03**: Add sourcing-aware strategy (different questions/approach for internal vs open market)

**Scenarios affected**: P2-S3 (Margin Erosion), #29 (Package Customization), #23 (Influencer ROI)

---

### 9. Traveler-Safe vs Internal-Only Leakage

**Status**: ⚠️ Partially covered — **Critical Gap**

**What works**:
- NB03 has separate builders for internal vs traveler outputs (`build_traveler_safe_prompts()` vs `build_internal_draft_prompts()`)
- NB05 golden path test checks for leakage:
  - User message must NOT contain "unknown", "hypothesis", "contradiction", "blocker"
  - System context has constraints list ("Do not mention unknowns, hypotheses, or contradictions")
  - Internal notes exist for agent-only context

**What's missing**:
- The boundary is **procedural** (different functions call different builders), NOT **structural** (enforced at type level)
- Nothing prevents an LLM from ignoring the constraints list
- No `is_internal` flag on every prompt block
- 15MC #12: "Internal Draft vs Traveler-Safe Boundary Enforcement" — listed as MVP-now
- Test evidence: Only the golden path test checks for leakage — no dedicated unit test exists

**Where to fix**:
- **NB03**: Add `is_internal` flag on every PromptBlock, enforced by builder
- **NB02**: Add risk flag `internal_data_present` — if hypotheses or unresolved contradictions exist, force internal draft
- **Add**: Dedicated unit test that attempts to leak internal concepts into traveler-facing output

**Scenarios affected**: ALL PROCEED_TRAVELER_SAFE paths — any time the system generates traveler-facing content

---

## Prioritized Test-Gap List

### P0 — Critical (Fix Before Production)

These gaps produce **trust-destroying outputs**: impossible proposals, leaked internal concepts to travelers, or bookings without valid documents.

| # | Gap | Severity | Scenarios Affected | Notebook Owner | Effort |
|---|-----|----------|-------------------|----------------|--------|
| 1 | **Ambiguity detection in NB02** — values like "Andaman or Sri Lanka" pass hard blocker check as if definite | 🔴 Critical | P1-S1, #5, S2-S3 | NB02 | Medium |
| 2 | **Urgency suppresses soft blockers** — last-minute trips should skip trip_purpose/preferences questions | 🔴 Critical | P1-S4, #8, #26 | NB02 | Small |
| 3 | **Budget feasibility enforcement** — "3L for 6 in Maldives" accepted as valid fact | 🔴 Critical | P1-S3, S2-S3, #3 | NB01 + NB02 | Medium |
| 4 | **Visa/passport hard blockers in booking stage** — not in code, only in MVB prose | 🔴 Critical | P1-S4, P3-S2 | NB01 + NB02 | Medium |
| 5 | **Traveler-safe leakage — structural enforcement** — currently only procedural, not enforced | 🔴 Critical | All PROCEED_TRAVELER_SAFE paths | NB03 | Small |

### P1 — High (Fix Before Beta)

These gaps cause **suboptimal but not dangerous** behavior: re-asking known questions, missing margin risks, unable to handle group trips.

| # | Gap | Severity | Scenarios Affected | Notebook Owner | Effort |
|---|-----|----------|-------------------|----------------|--------|
| 6 | **Repeat customer memory** — no `customer_id`, history lookup, `is_repeat_customer` | 🟠 High | P1-S2, P1-S5 | NB01 | Medium |
| 7 | **Budget stretch structural parsing** — currently string-only signal, not actionable | 🟠 High | P1-S3, S2-S3 | NB02 | Small |
| 8 | **Emergency protocol output** — `EMERGENCY_PROTOCOL` decision state with structured options | 🟠 High | P1-S4, S1-S3, #24 | NB02 | Medium |
| 9 | **Multi-party / sub_groups data structure** — no support for 3-family coordination | 🟠 High | P1-S5, #25, S2-S2 | NB01 + NB02 | Large |
| 10 | **Margin/commercial logic** — no `margin_risk`, no sourcing hierarchy | 🟠 High | P2-S3, #29 | NB02 | Medium |

### P2 — Important (Post-MVP)

These are **nice-to-have** capabilities that differentiate the product but aren't required for basic operation.

| # | Gap | Severity | Scenarios Affected | Notebook Owner | Effort |
|---|-----|----------|-------------------|----------------|--------|
| 11 | **Audit mode** — itinerary vs market comparison, fit scoring | 🟡 Medium | P3-S3, audit scenarios | NB02 + NB03 | Large |
| 12 | **Lead follow-up / ghost customer** — `LEAD_FOLLOWUP_REQUIRED` decision state | 🟡 Medium | #21 | NB02 | Small |
| 13 | **Scope creep / boundary setting** — `SET_BOUNDARIES` decision state | 🟡 Medium | #22 | NB02 | Small |
| 14 | **Influencer ROI evaluation** — historical ROI tracking | 🟡 Medium | #23 | NB02 | Medium |
| 15 | **Cancellation policy engine** — structured cancellation handling | 🟡 Medium | #26 | NB02 | Medium |
| 16 | **Referral program logic** — `PROCEED_WITH_INCENTIVE` decision state | 🟡 Medium | #27 | NB02 | Small |
| 17 | **Seasonal allocation optimization** — queue management, value-based ranking | 🟡 Medium | #28 | NB02 | Large |
| 18 | **Post-trip engagement / review timing** — sentiment-aware review requests | 🟡 Medium | #30 | NB01 + NB02 | Small |

### Out of Scope (Different Systems Entirely)

These scenarios are documented for completeness but belong to systems that don't exist yet and aren't part of NB01-NB03's mandate.

| # | Scenario | Current Status | Whose Job |
|---|----------|---------------|-----------|
| P2-S1 | Quote Disaster Review | ⬜ Not started | Owner dashboard / quality system |
| P2-S2 | Agent Who Left | ⬜ Not started | CRM / knowledge transfer system |
| P3-S4 | Don't Know Answer | ⬜ Not started | Knowledge base / FAQ system |
| S1-S2 | Post-Booking Anxiety | ⬜ Not started | Post-booking communication system |
| P2-S5 | Weekend Panic (document tracking) | ⬜ Not started | Document tracker system |

---

## Notebook Owner Responsibility Matrix

### NB01: Intake & Normalization

| Gap | What to Add | Priority |
|-----|-------------|----------|
| #3 Budget feasibility | Derived signal `estimated_minimum_cost` (per person, per destination tier) | P0 |
| #4 Visa/passport | Facts `passport_status`, `visa_requirements` | P0 |
| #6 Repeat customer | Fact `customer_id`, derived signal `is_repeat_customer`, fact `past_trips` | P1 |
| #9 Multi-party | Extend CanonicalPacket with `sub_groups` field | P1 |
| #10 Margin/commercial | Fact `agency_target_margin` (owner-seeded) | P1 |
| #18 Post-trip | Trip completion tracking, sentiment capture | P2 |

### NB02: Gap & Decision

| Gap | What to Add | Priority |
|-----|-------------|----------|
| #1 Ambiguity detection | `value_ambiguity` check — flag vague values as partially unfilled | P0 |
| #2 Urgency handling | Urgency-aware MVB — suppress soft blockers when travel < 7 days | P0 |
| #3 Budget feasibility | `budget_feasibility` contradiction — stated budget vs minimum viable cost | P0 |
| #4 Visa/passport | Booking-stage hard blockers `valid_passport`, `valid_visa` | P0 |
| #7 Budget stretch | Structural parsing of stretch signals (not just string annotation) | P1 |
| #8 Emergency protocol | New `EMERGENCY_PROTOCOL` decision state with structured options | P1 |
| #9 Multi-party | Per-group readiness check, collective readiness computation | P1 |
| #10 Margin/commercial | Derived signals `sourcing_path`, `margin_risk`, `preferred_supplier_available` | P1 |
| #12 Lead follow-up | New `LEAD_FOLLOWUP_REQUIRED` decision state | P2 |
| #13 Scope creep | New `SET_BOUNDARIES` decision state | P2 |
| #14 Influencer ROI | Historical ROI tracking, risk assessment | P2 |
| #15 Cancellation | Cancellation policy engine, option generation | P2 |
| #16 Referral | New `PROCEED_WITH_INCENTIVE` decision state | P2 |
| #17 Seasonal | Allocation optimization algorithm | P2 |
| #11 Audit mode | Derived signal `budget_efficiency`, contradiction `value_mismatch` | P2 |

### NB03: Session Strategy

| Gap | What to Add | Priority |
|-----|-------------|----------|
| #5 Leakage enforcement | `is_internal` flag on every PromptBlock, structural enforcement | P0 |
| #8 Emergency protocol | Crisis-aware prompts with step-by-step guidance | P1 |
| #9 Multi-party | Coordinator-aware prompt generation (per-group messages + summary) | P1 |
| #11 Audit mode | "I found a better option" strategy prompts | P2 |
| #18 Post-trip | Engagement timing optimization, review request generation | P2 |

---

## Technical Scenarios (A1–F5) Coverage

The 30 technical scenarios in `data/fixtures/test_scenarios.py` are **NB02-only** and all pass. They test:

| Category | Scenarios | What They Test | Coverage |
|----------|-----------|---------------|----------|
| A: Basic Flows | A1–A6 | Empty, complete, hypothesis-only, derived, soft-only, minimal-safe | ✅ Full |
| B: Contradictions | B1–B5 | Date, budget, destination, count, origin conflicts | ✅ Full |
| C: Authority | C1–C5 | Manual override, owner vs imported, derived vs hypothesis, unknown rejection | ✅ Full |
| D: Stage Progression | D1–D4 | Discovery → shortlist → proposal → booking transitions | ✅ Full |
| E: Edge Cases | E1–E5 | Nulls, empty strings, zero confidence, duplicates, unknown stage | ✅ Full |
| F: Complex Hybrid | F1–F5 | Multi-source, normalization, cross-layer, boundary conditions, all layers | ✅ Full |

**Gap**: These 30 scenarios test NB02's internal logic thoroughly but don't test the full pipeline (raw input → NB01 → NB02 → NB03 → PromptBundle). The persona scenarios fill that gap — but only 5 are currently executable as tests.

---

## Relationship to 15 Missing Concepts

This gap analysis is the **test coverage view** of the same problem that `15_MISSING_CONCEPTS.md` documents from a **data model perspective**. Cross-reference:

| 15MC # | Concept | Test Gap # | Priority Alignment |
|--------|---------|-----------|-------------------|
| 1 | Sourcing Hierarchy | #10 | Both: P1 |
| 2 | Margin / Commercial Logic | #10 | Both: P1 |
| 3 | Preferred Supplier | #10 | Both: P1 |
| 4 | Owner Seeded Context | #6 | Both: P1 |
| 5 | Repeat-Customer Memory | #6 | Both: P1 |
| 6 | Family/Elderly Suitability | — | 15MC: P1, Tests: implied in P1-S1 |
| 7 | Document Risk (Passport/Visa) | #4 | Both: P0 for production |
| 8 | Audit Mode | #11 | Both: P2 / Later |
| 9 | Booking Readiness Gate | — | 15MC: Later, Tests: implied in #4 |
| 10 | Operational Ease | — | 15MC: Later, Tests: not yet identified |
| 11 | Network Supplier Tier | #10 | Both: P2 / Later |
| 12 | Internal/External Boundary | #5 | Both: P0 / MVP-now |
| 13 | Budget Feasibility | #3 | Both: P0 / MVP-now |
| 14 | Question Quality by Context | — | 15MC: P1, Tests: implied in #1 |
| 15 | Confidence vs Decision-State | — | 15MC: P1, Tests: already correct in code |

---

## Recommended Next Steps

### Immediate (This Week)
1. **Add ambiguity detection to NB02** — Gap #1, ~2 hours. Lowest effort, highest impact.
2. **Add urgency suppression of soft blockers** — Gap #2, ~1 hour.
3. **Add structural leakage enforcement to NB03** — Gap #5, ~2 hours.
4. **Add dedicated leakage unit test** — ~1 hour.

### Short-term (This Sprint)
5. **Add budget feasibility enforcement** — Gap #3, ~4 hours. Needs destination tier pricing table.
6. **Add visa/passport booking blockers** — Gap #4, ~3 hours.
7. **Add budget stretch structural parsing** — Gap #7, ~1 hour.

### Next Sprint
8. **Add repeat customer memory** — Gap #6, ~6 hours. Needs customer_id matching.
9. **Add emergency protocol output** — Gap #8, ~4 hours.
10. **Add margin/commercial logic** — Gap #10, ~6 hours.

### Post-MVP
11. Multi-party support (Gap #9) — ~2 days
12. Audit mode (Gap #11) — ~3 days
13. Remaining P2 gaps — ~4 days total

---

*Analysis date: 2026-04-12. Based on code state as of this date. Re-run after any significant NB01/NB02/NB03 changes.*
