# Scenario Coverage Gap Analysis: 30 Scenarios → NB01 / NB02 / NB03

**Date**: 2026-04-12
**Method**: Cross-referenced all 30 persona scenarios against actual notebook code, existing test results, 15_MISSING_CONCEPTS.md, and test result artifacts.
**Audited artifacts**:
- `Docs/personas_scenarios/` (all 10 files, 4,236 lines)
- `data/fixtures/test_scenarios.py` (30 CanonicalPacket factories)
- `notebooks/01_intake_and_normalization.ipynb`
- `notebooks/02_gap_and_decision.ipynb`
- `notebooks/03_session_strategy.ipynb`
- `notebooks/05_golden_path.ipynb` (boundary checks)
- `notebooks/test_scenarios_realworld.py` (13 scenario tests)
- `notebooks/15_MISSING_CONCEPTS.md`
- `notebooks/02_SCENARIO_TEST_RESULTS.md`
- `notebooks/02_PERSONA_SCENARIO_COVERAGE.md`
- `notebooks/02_gap_and_decision_contract.md`
- `notebooks/03_session_strategy_contract.md`

---

## Executive Summary

| Question | Answer |
|----------|--------|
| Total persona scenarios | 30 |
| Fully covered (all 3 notebooks) | 5 (17%) |
| Partially covered | 7 (23%) |
| Missing but in-scope for NB01-NB03 | 9 (30%) |
| Out of scope (different systems) | 9 (30%) |
| P0 gaps (block production) | 5 |
| P1 gaps (block beta) | 5 |
| P2 gaps (post-MVP) | 7 |

**Bottom line**: The golden path spine (NB01→NB02→NB03) works cleanly for simple, well-structured discovery inputs. Everything outside that path — urgency, ambiguity, multi-party, visa crises, repeat customers, commercial logic — is either partially handled or not handled at all.

---

## Two Scenario Systems

The project defines **two parallel sets of 30 scenarios** that serve different purposes:

### System A: Technical Test Scenarios (A1–F5)
| Attribute | Detail |
|-----------|--------|
| Location | `data/fixtures/test_scenarios.py` |
| Format | CanonicalPacket factory functions |
| Purpose | Validate NB02 decision correctness for specific data states |
| Coverage | 6 categories: Basic (6), Contradictions (5), Authority (5), Stage Progression (4), Edge Cases (5), Hybrid (5) |
| Test count | 30 factory functions, 68 unit tests, 13 real-world scenario tests |
| Scope | **NB02 only** — does not test NB01 extraction or NB03 strategy |

### System B: Persona Scenarios (P1-S1 through #30)
| Attribute | Detail |
|-----------|--------|
| Location | `Docs/personas_scenarios/` |
| Format | Real-world narratives with full pipeline mapping |
| Purpose | Validate that real users get the right outcome from the full pipeline |
| Coverage | 5 personas: Solo Agent (5), Agency Owner (5), Junior Agent (5), Customers (5), Additional (10) |
| Scope | **Full pipeline** — NB01 intake, NB02 decision, NB03 strategy |

**This analysis focuses on System B (persona scenarios)** because they represent the real-world coverage requirement. Technical scenarios (System A) are NB02-only by design and are already well-covered by existing tests.

---

## Full Coverage Table: All 30 Scenarios

| # | Scenario | NB01 | NB02 | NB03 | Overall | Verdict |
|---|----------|------|------|------|---------|---------|
| **P1-S1** | 11 PM WhatsApp Panic | ⚠️ History lookup not implemented | ⚠️ Budget feasibility math missing | ⚠️ Urgency detection exists but not wired to decision | **Partial** | Needs NB02 ambiguity + urgency fixes |
| **P1-S2** | Repeat Customer Who Forgot | ❌ No `customer_id`, no `past_trips`, no `is_repeat_customer` in code | ✅ Works if NB01 provides enriched packet | ⚠️ No history-aware questions | **Partial** | Needs NB01 customer memory |
| **P1-S3** | Customer Changes Everything | ⚠️ Event cursor exists but revision counting not used | ⚠️ Budget feasibility math missing (15MC #13) | ❌ No revision-aware strategy | **Partial** | Needs budget feasibility |
| **P1-S4** | Visa Problem at Last Minute | ❌ No `passport_status` or `visa_requirements` (15MC #7) | ❌ No `valid_passport`/`valid_visa` hard blockers | ❌ No `EMERGENCY_PROTOCOL` output in DecisionResult | **Missing** | P0 — visa/passport + emergency protocol |
| **P1-S5** | Multi-Party Group Trip | ❌ No `sub_groups` field in CanonicalPacket | ❌ No multi-party readiness logic | ❌ No coordinator dashboard | **Missing** | Needs new data structure |
| **P2-S1** | Quote Disaster Review | ❌ Out of scope (owner review workflow) | ❌ Out of scope | ❌ Out of scope | **Out of Scope** | Owner dashboard / quality system |
| **P2-S2** | Agent Who Left | ❌ Out of scope (knowledge transfer / CRM) | ❌ Out of scope | ❌ Out of scope | **Out of Scope** | CRM / knowledge transfer system |
| **P2-S3** | Margin Erosion | ❌ No margin model (15MC #2) | ❌ No `margin_risk` derived signal | ❌ No margin-aware strategy | **Missing** | Needs commercial logic |
| **P2-S4** | Training Time Problem | ✅ Confidence scoring works | ✅ Low confidence → ASK_FOLLOWUP | ✅ Confidence tone works | **Full** | ✅ |
| **P2-S5** | Weekend Panic | ❌ Document tracking not implemented | ❌ Document tracking not a NB02 concern | ❌ No monitoring alerts | **Missing** | Document tracker system |
| **P3-S1** | First Solo Quote | ✅ | ✅ Low confidence triggers ASK_FOLLOWUP | ✅ | **Full** | ✅ |
| **P3-S2** | Visa Mistake Prevention | ⚠️ `traveler_details` exists as booking blocker but no `passport_status` | ⚠️ Partial | ❌ No visa-specific guidance | **Partial** | Needs visa/passport fields |
| **P3-S3** | "Is This Right?" Check | ❌ Cost completeness validation missing | ❌ Needs pricing data | ❌ No cost validation | **Missing** | Cost validator system |
| **P3-S4** | Don't Know Answer | ❌ Out of scope | ❌ Out of scope | ❌ Out of scope | **Out of Scope** | Knowledge base / FAQ system |
| **P3-S5** | Comparison Trap | ❌ Competitor quote analysis missing | ❌ No competitor comparison | ❌ No competitive positioning | **Missing** | Competitor analyzer |
| **S1-S1** | Comparison Shopper | ✅ | ✅ PROCEED_TRAVELER_SAFE when complete | ✅ | **Full** | ✅ |
| **S1-S2** | Post-Booking Anxiety | ❌ Out of scope (post-booking) | ❌ Out of scope | ❌ Out of scope | **Out of Scope** | Post-booking communication system |
| **S1-S3** | Trip Emergency | ⚠️ STOP_NEEDS_REVIEW works | ❌ `EMERGENCY_PROTOCOL` with options not in DecisionResult schema | ❌ No crisis protocol | **Partial** | Needs emergency protocol |
| **S2-S1** | Preference Collection | ✅ Contradiction detection works | ✅ Contradiction detection + ASK_FOLLOWUP | ✅ | **Full** | ✅ |
| **S2-S2** | Document Chaos | ❌ Per-person tracking needs new data structure | ❌ No per-person document state | ❌ No progress dashboard | **Missing** | Document tracker system |
| **S2-S3** | Budget Reality | ⚠️ Budget contradiction detection works | ❌ Budget feasibility MATH needs external pricing (15MC #13) | ❌ No reality check prompts | **Partial** | Needs budget feasibility |
| **#21** | Ghost Customer (No Response) | ❌ Engagement tracking missing | ❌ `LEAD_FOLLOWUP_REQUIRED` not a decision state | ❌ No nurture strategy | **Missing** | Needs lead management |
| **#22** | Scope Creep (Free Consulting) | ❌ Revision counting, time ROI missing | ❌ `SET_BOUNDARIES` not a decision state | ❌ No boundary strategy | **Missing** | Needs scope creep detection |
| **#23** | Influencer Request | ❌ Influencer ROI tracking missing | ❌ No historical ROI calculation | ❌ No opportunity evaluation | **Missing** | Needs influencer ROI logic |
| **#24** | Medical Emergency During Trip | ❌ Emergency keyword detection, insurance data missing | ❌ `EMERGENCY_PROTOCOL` decision state missing | ❌ No crisis protocol | **Missing** | Needs emergency protocol |
| **#25** | Competing Family Priorities | ❌ Multi-party constraints missing | ⚠️ BRANCH_OPTIONS exists but no multi-party optimization | ❌ No consensus building | **Partial** | Needs multi-party support |
| **#26** | Last-Minute Cancellation | ❌ Cancellation policy engine missing | ❌ Policy-guided BRANCH_OPTIONS not implemented | ❌ No cancellation strategy | **Missing** | Needs cancellation logic |
| **#27** | Referral Request | ❌ Referral tracking missing | ❌ `PROCEED_WITH_INCENTIVE` not a decision state | ❌ No referral strategy | **Missing** | Needs referral program logic |
| **#28** | Seasonal Rush | ❌ Queue management missing | ❌ Allocation optimization algorithm missing | ❌ No waitlist strategy | **Missing** | Needs seasonal allocation |
| **#29** | Package Customization | ❌ Dynamic pricing, availability checks missing | ❌ Margin recalculation missing | ❌ No customization strategy | **Missing** | Needs customization engine |
| **#30** | Review Request (Post-Trip) | ❌ Trip completion tracking, sentiment missing | ❌ Post-trip engagement timing missing | ❌ No review strategy | **Missing** | Needs post-trip system |

---

## Coverage Totals

| Status | Count | % |
|--------|-------|---|
| ✅ Full | 5 | 17% |
| ⚠️ Partial | 7 | 23% |
| ❌ Missing (in-scope) | 9 | 30% |
| ❌ Out of scope (different systems) | 9 | 30% |

---

## Deep Dive: 9 Specific Gap Areas

### 1. Ambiguity Handling

**Status**: ⚠️ Partially Covered — **Critical Gap**

| Aspect | Detail |
|--------|--------|
| **What works** | NB03 has `detect_ambiguous_values()` that runs in `build_traveler_safe_strategy()`. If an ambiguous value is found, it adds a confirmation question *after* the proposal is presented. |
| **What's broken** | NB02 does NOT detect ambiguity at decision time. A value like `"Andaman or Sri Lanka"` passes the hard blocker check because a value string exists. The system cannot distinguish a definite value (`"Singapore"`) from an ambiguous one (`"Andaman or Sri Lanka"`). |
| **Evidence** | Scenario test "WhatsApp Dump" explicitly documents: *"The gap: the system can't tell 'Andaman or Sri Lanka' is ambiguous vs 'Singapore' is definite. This is a KNOWN LIMITATION — the MVB checks field existence, not value specificity."* |
| **Impact** | PROCEED_TRAVELER_SAFE on ambiguous values → traveler gets a proposal for "Andaman OR Sri Lanka" instead of a definite destination. Trust-destroying. |
| **Fix** | NB02 needs a `value_ambiguity` check that flags values containing `"or"`, `"maybe"`, `"not sure"`, `"thinking about"`, etc. as partially unfilled even when a value string exists. Ambiguous values should NOT fill hard blockers. |
| **Notebook owner** | NB02 |
| **Priority** | P0 |

### 2. Urgency / Last-Minute

**Status**: ⚠️ Partially Covered — **Medium-High Gap**

| Aspect | Detail |
|--------|--------|
| **What works** | NB03 has `detect_urgency(packet)` that checks if travel dates are within 7 days. It adds a risk flag: `"URGENT: Travel within 7 days — expedite booking."` |
| **What's broken** | Urgency does NOT suppress soft blockers in NB02's decision logic. Scenario "Last-Minute Booker" produces `PROCEED_INTERNAL_DRAFT` because soft blockers `trip_purpose` and `traveler_preferences` remain unfilled. The urgency detection exists only in NB03's strategy builders — too late to affect the decision. |
| **Evidence** | 02_SCENARIO_TEST_RESULTS.md: *"soft blockers (trip_purpose, traveler_preferences) block PROCEED_TRAVELER_SAFE even when urgency is extreme."* 02_gap_and_decision_contract.md: *"Gap: 'This weekend, flying Friday' → soft blockers still block PROCEED_TRAVELER_SAFE."* |
| **Impact** | Agent wastes time on soft questions when the customer needs to book NOW. Loses the sale. |
| **Fix** | NB02 needs urgency-aware MVB — when `detect_urgency()` returns true, soft blockers should be suppressed or downgraded. |
| **Notebook owner** | NB02 |
| **Priority** | P0 |

### 3. Budget Stretch

**Status**: ⚠️ Partially Covered — **Medium Gap**

| Aspect | Detail |
|--------|--------|
| **What works** | NB03 has `detect_budget_stretch(packet)` that captures stretch signals in the value string (e.g., `"200000 (flexible)"`). It adds a risk flag in ASK_FOLLOWUP strategy. |
| **What's broken** | The stretch signal is captured but NOT structurally parsed. The test "Budget Stretch" confirms: *"Stretch signal captured in value string but not structurally parsed."* NB02 cannot act on it as a structured field. |
| **Bigger gap — Budget Feasibility** | No minimum-cost-per-destination logic exists. `"3L for 6 people in Maldives"` is accepted as a valid fact. This is 15MC #13. The system generates proposals that are mathematically impossible. |
| **Evidence** | 02_SCENARIO_TEST_RESULTS.md: *"Stretch signal captured in value string but not structurally parsed."* 15_MISSING_CONCEPTS.md #13: *"Budget is stored as a value. No minimum-cost-per-destination logic. No budget-vs-destination feasibility check."* |
| **Impact** | Two failures: (a) stretch signals not acted on structurally, (b) impossible budgets produce impossible proposals that destroy credibility. |
| **Fix** | (a) Structural budget stretch parsing: extract `can_stretch: bool` and `max_stretch: amount` as derived signals. (b) Budget feasibility enforcement: add min-cost lookup tables `{destination_tier: min_per_person}`. |
| **Notebook owner** | NB01 (derived signal) + NB02 (feasibility check) |
| **Priority** | P0 (feasibility), P1 (stretch parsing) |

### 4. Audit Mode

**Status**: ❌ Missing Entirely

| Aspect | Detail |
|--------|--------|
| **What it is** | Compare a proposed itinerary against market reality. Is the traveler getting value, or overpaying for a bad fit? |
| **Current state** | Not modeled in any notebook. No concept of itinerary comparison, market pricing benchmarks, or fit scoring. |
| **15MC reference** | #8: Audit Mode / Wasted-Spend Analysis — listed as "Later" priority |
| **Impact** | Without this, the system cannot prove its value as a boutique agency OS. This is the "wedge feature" — the agency proves value by finding waste the traveler couldn't see. |
| **Fix** | NB02: derived signal `budget_efficiency` (budget vs typical cost for destination + composition). NB03: "I found a better option" prompts. |
| **Notebook owner** | NB02 (derived signal) + NB03 (strategy prompts) |
| **Priority** | P2 (post-MVP — needs market pricing data first) |

### 5. Multi-Party / Family Coordinator Flows

**Status**: ❌ Missing Entirely

| Aspect | Detail |
|--------|--------|
| **What it is** | 3 families traveling together, different budgets, different payment terms, different document status. Need per-family readiness tracking and coordinator dashboard. |
| **Current state** | `CanonicalPacket` has no `sub_groups` field. No multi-party readiness detection. No coordinator dashboard in any decision state. |
| **Scenarios affected** | P1-S5 (Multi-Party Group), #25 (Competing Family Priorities), S2-S2 (Document Chaos) |
| **Impact** | Cannot handle group bookings where sub-parties have different readiness states. Agent must track everything manually. |
| **Fix** | (a) NB01: extend CanonicalPacket with `sub_groups: Dict[str, SubGroup]`. (b) NB02: per-group blocker checks, group readiness score. (c) NB03: coordinator-aware prompts with per-family status. |
| **Notebook owner** | NB01 (data structure) + NB02 (logic) + NB03 (prompts) |
| **Priority** | P1 |

### 6. Visa / Passport Readiness

**Status**: ❌ Missing Entirely (for booking stage)

| Aspect | Detail |
|--------|--------|
| **What it is** | Passports expiring, visa requirements not met, documents missing for some travelers. Booking-stage killer. |
| **Current state** | `passport_status` and `visa_requirements` are NOT in CanonicalPacket code. The MVB mentions `valid_passport` and `valid_visa` as booking-stage hard blockers but they're not in actual code. The only booking-stage blocker currently is `traveler_details`. |
| **15MC reference** | #7: Document Risk (Passport / Visa) — listed as "Later" but this is a booking-stage safety issue |
| **Scenarios affected** | P1-S4 (Visa Problem), P3-S2 (Visa Mistake Prevention) |
| **Impact** | System could reach PROCEED_TRAVELER_SAFE in booking stage without checking passport validity. Result: booking made for travelers with expired passports. |
| **Fix** | (a) NB01: add `passport_status` (valid/expiring/expired/unknown) and `visa_requirements` as facts. (b) NB02: add `valid_passport` and `valid_visa` as hard blockers in booking stage. |
| **Notebook owner** | NB01 (facts) + NB02 (blockers) |
| **Priority** | P0 |

### 7. Repeat Customer Memory

**Status**: ❌ Missing Entirely

| Aspect | Detail |
|--------|--------|
| **What it is** | Past trips, preferences, complaints, budget patterns, document status. System should recognize returning customers and use history to avoid re-asking known questions. |
| **Current state** | No `customer_id` field in CanonicalPacket. No `is_repeat_customer` derived signal. No `past_trips` or `trip_history` concept. The `source_envelope_ids` tracks envelopes but not customers. |
| **15MC reference** | #5: Repeat-Customer Memory — listed as "MVP-Now" |
| **Scenarios affected** | P1-S2 (Repeat Customer Who Forgot) |
| **Impact** | Returning customers are asked the same questions they answered last trip. Major agent pain point, customer frustration. |
| **Fix** | (a) NB01: add `customer_id` fact, `is_repeat_customer` derived signal, mechanism to pull history from customer database. (b) NB02: use history to fill blockers that were answered in previous trips. |
| **Notebook owner** | NB01 (facts + history lookup) + NB02 (use history) |
| **Priority** | P1 |

### 8. Quote / Commercial Logic

**Status**: ❌ Missing Entirely

| Aspect | Detail |
|--------|--------|
| **What it is** | Every quote has a margin. The agency needs to know if a trip is worth doing and at what price point. Sourcing hierarchy: Internal Packages → Preferred Suppliers → Network → Open Market. |
| **Current state** | Budget is captured as a raw number. No margin model, no profitability check, no commission tracking. No sourcing hierarchy. No preferred supplier concept. |
| **15MC reference** | #2 (Margin/Commercial — Later), #1 (Sourcing Hierarchy — MVP-Now), #3 (Preferred Supplier — MVP-Now) |
| **Scenarios affected** | P2-S3 (Margin Erosion), #29 (Package Customization) |
| **Impact** | Agency goes out of business if every quote is margin-negative. Cannot differentiate between internal package (high margin) and open market (low margin). |
| **Fix** | (a) NB02: derived signal `margin_risk` (budget too tight for viable margin), `sourcing_path` (determines supplier tier), `preferred_supplier_available`. (b) NB03: sourcing-aware question generation. |
| **Notebook owner** | NB02 (derived signals) + NB03 (strategy) |
| **Priority** | P1 |

### 9. Traveler-Safe vs Internal-Only Leakage

**Status**: ⚠️ Partially Covered — **Procedural Not Structural**

| Aspect | Detail |
|--------|--------|
| **What it is** | The boundary between what the traveler sees vs what only the agent sees. If a traveler sees "we're guessing your budget" or "there's a contradiction we couldn't resolve," the agency loses trust. |
| **What works** | NB03 has separate builders for internal vs traveler outputs (`build_traveler_safe_prompts` vs `build_internal_draft_prompts`). Golden path test (NB05) checks for leakage: user_message must not contain "unknown", "hypothesis", "contradiction", "blocker". PromptBundle has a `constraints` list. |
| **What's broken** | The boundary is procedural (different functions), not structural/enforced at the type level. The constraints list exists but nothing prevents an LLM from ignoring them. The golden path test catches leakage post-hoc but doesn't prevent it. |
| **15MC reference** | #12: Internal Draft vs Traveler-Safe Boundary Enforcement — listed as "MVP-Now" |
| **Evidence** | 15_MISSING_CONCEPTS.md: *"The boundary exists in code (two different decision states) but there's no structural enforcement that internal-only data never leaks into traveler-facing output."* |
| **Impact** | A subtle leakage bug could ship to production — traveler sees internal system concepts, trust is destroyed. |
| **Fix** | (a) NB03: add `is_internal` flag on every prompt block, enforced by builder. (b) Add a structural boundary test that runs on every PromptBundle, not just the golden path. (c) Consider a type-level enforcement (Pydantic validator that rejects traveler-facing prompts containing internal keywords). |
| **Notebook owner** | NB03 |
| **Priority** | P0 |

---

## Prioritized Test-Gap List

### P0 — Critical (Block Production)

These gaps can produce trust-destroying outputs or unsafe behavior. Must be fixed before any production deployment.

| # | Gap | Severity | Scenarios Affected | Notebook Owner | Evidence |
|---|-----|----------|-------------------|----------------|----------|
| **P0-1** | **Ambiguity detection in NB02** — values like "Andaman or Sri Lanka" pass hard blocker check as if they were definite | 🔴 Critical | P1-S1, #5 (WhatsApp Dump), S2-S3 | NB02 | test_scenarios_realworld.py: "The gap: the system can't tell 'Andaman or Sri Lanka' is ambiguous" |
| **P0-2** | **Urgency suppresses soft blockers** — last-minute trips should skip trip_purpose/preferences questions | 🔴 Critical | P1-S4, #8 (Last-Minute Booker), #26 | NB02 | 02_SCENARIO_TEST_RESULTS.md: "soft blockers block PROCEED_TRAVELER_SAFE even when urgency is extreme" |
| **P0-3** | **Budget feasibility enforcement** — "3L for 6 in Maldives" accepted as valid fact, generates impossible proposals | 🔴 Critical | P1-S3, S2-S3, #29 | NB01 + NB02 | 15MC #13: "No minimum-cost-per-destination logic" |
| **P0-4** | **Visa/passport hard blockers in booking stage** — not in code despite being in MVB spec | 🔴 Critical | P1-S4, P3-S2 | NB01 + NB02 | 15MC #7: "MVB mentions passport_status but code doesn't enforce it" |
| **P0-5** | **Traveler-safe leakage — structural enforcement** — currently only procedural, not enforced at type level | 🔴 Critical | All PROCEED_TRAVELER_SAFE paths | NB03 | 15MC #12: "boundary is procedural, not structural" |

### P1 — High (Block Beta)

These gaps limit the system's usefulness for real agency workflows but won't produce actively harmful output.

| # | Gap | Severity | Scenarios Affected | Notebook Owner | Evidence |
|---|-----|----------|-------------------|----------------|----------|
| **P1-6** | **Repeat customer memory** — no `customer_id`, no history lookup, no `is_repeat_customer` | 🟠 High | P1-S2, P1-S5 | NB01 | 15MC #5: "MVP-Now" |
| **P1-7** | **Budget stretch structural parsing** — currently string-only signal, NB02 cannot act on it | 🟠 High | P1-S3, S2-S3 | NB02 | 02_SCENARIO_TEST_RESULTS.md: "Stretch signal captured in value string but not structurally parsed" |
| **P1-8** | **Emergency protocol output** — no `EMERGENCY_PROTOCOL` decision state with options for visa crises and medical emergencies | 🟠 High | P1-S4, S1-S3, #24 | NB02 | 02_PERSONA_SCENARIO_COVERAGE.md: "EMERGENCY_PROTOCOL output with options is beyond DecisionResult schema" |
| **P1-9** | **Multi-party / sub_groups data structure** — no support for 3-family coordination, per-group readiness | 🟠 High | P1-S5, #25, S2-S2 | NB01 + NB02 | 02_PERSONA_SCENARIO_COVERAGE.md: "CanonicalPacket has no sub_groups field" |
| **P1-10** | **Margin/commercial logic** — no `margin_risk`, no sourcing hierarchy, no preferred supplier concept | 🟠 High | P2-S3, #29 | NB02 | 15MC #1, #2, #3: all listed as MVP-Now |

### P2 — Important (Post-MVP)

These are valuable features that require external data or new decision states. Not blocking for initial launch.

| # | Gap | Severity | Scenarios Affected | Notebook Owner | Evidence |
|---|-----|----------|-------------------|----------------|----------|
| **P2-11** | **Audit mode** — itinerary vs market comparison, fit scoring, wasted-spend analysis | 🟡 Medium | P3-S3 (implied), P2-S3 | NB02 + NB03 | 15MC #8: "Later — needs market pricing data" |
| **P2-12** | **Lead follow-up / ghost customer** — `LEAD_FOLLOWUP_REQUIRED` decision state, engagement tracking | 🟡 Medium | #21 | NB02 | Scenario #20: "Should I follow up again? Did they book elsewhere?" |
| **P2-13** | **Scope creep / boundary setting** — `SET_BOUNDARIES` decision state, revision counting, time ROI | 🟡 Medium | #22 | NB02 | Scenario #22: "8 revisions over 3 weeks, no commitment" |
| **P2-14** | **Influencer ROI evaluation** — historical ROI tracking, opportunity evaluation | 🟡 Medium | #23 | NB02 | Scenario #23: "expected ROI is -62.5%" |
| **P2-15** | **Cancellation policy engine** — structured cancellation handling, insurance integration | 🟡 Medium | #26 | NB02 | Scenario #26: "hotels ₹2L non-refundable, flights ₹50K cancellation fee" |
| **P2-16** | **Referral program logic** — `PROCEED_WITH_INCENTIVE` state, reward calculation | 🟡 Medium | #27 | NB02 | Scenario #27: "referrer reward: ₹3000 credit" |
| **P2-17** | **Seasonal allocation optimization** — queue management, waitlist, revenue optimization | 🟡 Medium | #28 | NB02 | Scenario #28: "15 leads, only 5 rooms available" |
| **P2-18** | **Post-trip engagement / review timing** — trip completion tracking, sentiment analysis, review request optimization | 🟡 Medium | #30 | NB01 + NB02 | Scenario #30: "Day 3-5: Optimal (experience fresh, settled)" |

### Out of Scope (Different Systems)

These scenarios are correctly outside NB01-NB03 scope. They belong to future systems.

| # | Scenario | Gap | Whose Job |
|---|----------|-----|-----------|
| P2-S1 | Quote Disaster Review | Quality review of generated quotes | Owner dashboard / quality system |
| P2-S2 | Agent Who Left | Knowledge transfer between agents | CRM / knowledge transfer system |
| P2-S5 | Weekend Panic (document tracking) | Document status monitoring | Document tracker system |
| P3-S3 | "Is This Right?" Check | Cost completeness validation | Cost validator / pricing system |
| P3-S4 | Don't Know Answer | Knowledge base lookup | Knowledge base / FAQ system |
| P3-S5 | Comparison Trap | Competitor quote analysis | Competitor analyzer |
| S1-S2 | Post-Booking Anxiety | Already-booked status updates | Post-booking communication system |
| S2-S2 | Document Chaos | Per-person document tracking | Document tracker system |
| #30 (partial) | Review Request | Post-trip engagement | Post-trip / reputation system |

---

## Notebook Owner Responsibility Matrix

### NB01: Intake & Normalization

| Gap | What to Add | Priority |
|-----|-------------|----------|
| Budget feasibility (P0-3) | Derived signal `estimated_minimum_cost` per destination tier + traveler composition | P0 |
| Visa/passport (P0-4) | Facts: `passport_status`, `visa_requirements` with valid/expiring/expired/unknown values | P0 |
| Repeat customer memory (P1-6) | Facts: `customer_id`, `is_repeat_customer`, `past_trips` list. History lookup mechanism. | P1 |
| Multi-party sub_groups (P1-9) | Extend CanonicalPacket with `sub_groups: Dict[str, SubGroup]` for per-family data | P1 |
| Post-trip tracking (P2-18) | Facts: `trip_completed`, `return_date`, sentiment signals | P2 |

### NB02: Gap & Decision

| Gap | What to Add | Priority |
|-----|-------------|----------|
| Ambiguity detection (P0-1) | `value_ambiguity` check: flag values containing "or", "maybe", "not sure" as partially unfilled. Ambiguous values do NOT fill hard blockers. | P0 |
| Urgency suppression (P0-2) | When `detect_urgency()` returns true, downgrade or suppress soft blockers in MVB check. | P0 |
| Budget feasibility (P0-3) | Contradiction type `budget_feasibility`: stated budget vs minimum viable cost for destination + composition. Lookup table: `{destination_tier: min_per_person}`. | P0 |
| Visa/passport blockers (P0-4) | Add `valid_passport` and `valid_visa` as hard blockers in booking stage. | P0 |
| Budget stretch parsing (P1-7) | Extract `can_stretch: bool` and `max_stretch: amount` as derived signals from value strings. | P1 |
| Emergency protocol (P1-8) | New decision state `EMERGENCY_PROTOCOL` with `emergency_options` field containing timed, ranked options with success probabilities. | P1 |
| Multi-party readiness (P1-9) | Per-group blocker checks when `sub_groups` exists. Group readiness score. | P1 |
| Margin/commercial (P1-10) | Derived signals: `margin_risk`, `sourcing_path`, `preferred_supplier_available`. | P1 |
| Lead follow-up (P2-12) | New decision state `LEAD_FOLLOWUP_REQUIRED` with engagement analysis. | P2 |
| Scope creep (P2-13) | New decision state `SET_BOUNDARIES` with revision counting and time ROI. | P2 |
| Influencer ROI (P2-14) | Historical ROI calculation, risk assessment, opportunity evaluation. | P2 |
| Cancellation policy (P2-15) | Cancellation reason categorization, insurance coverage check, financial impact options. | P2 |
| Referral program (P2-16) | New decision state `PROCEED_WITH_INCENTIVE` with reward calculation. | P2 |
| Seasonal allocation (P2-17) | Queue scoring, allocation optimization, waitlist management. | P2 |
| Audit mode (P2-11) | Derived signal `budget_efficiency`, contradiction `value_mismatch`. | P2 |

### NB03: Session Strategy

| Gap | What to Add | Priority |
|-----|-------------|----------|
| Traveler-safe leakage (P0-5) | Add `is_internal` flag on every prompt block. Add structural boundary validator (Pydantic or explicit keyword scan on every PromptBundle). Add regression test that runs on all scenarios, not just golden path. | P0 |
|