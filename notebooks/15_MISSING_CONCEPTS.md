# 15 Missing or Under-Modeled Concepts in NB01–NB03

**Method**: Audited actual notebook code against product docs (`MASTER_PRODUCT_SPEC.md`, `PRODUCT_VISION_AND_MODEL.md`, `Sourcing_And_Decision_Policy.md`, `AUDIT_AND_INTELLIGENCE_ENGINE.md`). Cross-referenced with what's structurally present vs what's only discussed in prose.

**Finding**: The spine handles generic trip planning well. What's missing are the concepts that make this a **boutique travel agency OS** rather than a generic itinerary planner.

---

## 1. Sourcing Hierarchy

**What it is**: The agency doesn't search open market first. The sourcing path is: Internal Packages → Preferred Suppliers → Network → Open Market. This is the core differentiator.

**Current state**: Not modeled anywhere. NB02 has no concept of sourcing path. NB03 has no sourcing-aware strategy.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Derived signal → `sourcing_path` (determines which supplier tier to use) | **MVP-now** |
| NB02 | Soft blocker → `sourcing_path_confirmed` (in shortlist stage) | Later |
| NB03 | Strategy item → sourcing-aware question generation (different questions for internal vs open market) | **MVP-now** |

**Why it matters**: A "family of 4, Singapore, 3L" is a very different query if there's an internal package available vs searching Booking.com. The sourcing path determines the agent's entire approach.

---

## 2. Margin / Commercial Logic

**What it is**: Every quote has a margin. The agency needs to know if a trip is worth doing, and at what price point.

**Current state**: Budget is captured as a raw number. No margin model, no profitability check, no commission tracking.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Risk flag → `margin_risk` (budget too tight for viable margin) | Later |
| NB02 | Derived signal → `estimated_cost_range` (to compare against budget for margin calc) | Later |
| NB01 | Fact → `agency_target_margin` (owner-seeded context) | Later |

**Why it matters**: The agency goes out of business if every quote is margin-negative. This is not a blocking concern for v0.1 discovery, but it must be modeled before booking stage.

---

## 3. Preferred Supplier / Partner Fit

**What it is**: The agency has preferred suppliers (hotels, DMCs, transport) who give better rates and reliability. The system should bias toward them.

**Current state**: Not modeled. No supplier database concept, no preferred vs open market distinction.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Derived signal → `preferred_supplier_available` (based on destination + budget tier) | **MVP-now** |
| NB03 | Strategy item → if preferred supplier available, lead with it in proposal | **MVP-now** |

**Why it matters**: This is the "internal packages" concept from the product spec. It's what makes the agency competitive vs OTAs.

---

## 4. Agency-Owner Seeded Context (Tribal Knowledge)

**What it is**: The agency owner knows things no CRM captures: "Don't book Hotel X in Goa — plumbing broke last monsoon." "Family Y always needs ground-floor rooms." This is the agency's moat.

**Current state**: The `explicit_owner` authority level exists but is just another source. No dedicated mechanism for owner knowledge that persists across customers.

| Notebook | Type | Priority |
|----------|------|----------|
| NB01 | Fact → `owner_notes` (freeform agency-owner context, separate from customer data) | **MVP-now** |
| NB01 | Fact → `owner_constraints` (hard rules from owner, e.g., "never use this hotel") | **MVP-now** |
| NB02 | Risk flag → `owner_constraint_violated` (if proposed path conflicts with owner knowledge) | Later |

**Why it matters**: Without this, the system treats the agency owner's hard-won knowledge the same as a random text span. The owner's voice needs higher authority AND persistence.

---

## 5. Repeat-Customer Memory

**What it is**: Past trips, preferences, complaints, budget patterns, document status. The system should recognize returning customers and use history.

**Current state**: The `source_envelope_ids` field exists but there's no `customer_id` or `trip_history` concept. No mechanism to pull prior context.

| Notebook | Type | Priority |
|----------|------|----------|
| NB01 | Fact → `customer_id` (to link to history) | **MVP-now** |
| NB01 | Derived signal → `is_repeat_customer` | **MVP-now** |
| NB01 | Fact → `past_trips` (list of prior trips with key outcomes) | Later |
| NB02 | Derived signal → `preference_consistency` (current request vs past behavior) | Later |

**Why it matters**: A returning customer who told you their preferences last time should not be asked the same questions again. This is a major agent pain point.

---

## 6. Family / Toddler / Elderly Suitability

**What it is**: Not all destinations, hotels, or itineraries work for mixed-age families. The system should flag suitability risks based on traveler composition.

**Current state**: Traveler composition is captured as a value ("2 adults, 2 kids") but there's no suitability analysis. The `traveler_type` classification exists in NB01's code but isn't wired into NB02's decision logic or NB03's strategy.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Risk flag → `composition_risk` (elderly + international, toddler + packed itinerary, etc.) | **MVP-now** |
| NB02 | Risk flag → `destination_suitability` (destination known to be unsuitable for this composition) | Later |
| NB03 | Strategy item → suitablity-aware question generation (ask about mobility aids if elderly detected) | **MVP-now** |

**Why it matters**: Sending an elderly family to a destination with no medical facilities or a toddler to a hotel with no crib isn't just a bad trip — it's a refund and a lost customer.

---

## 7. Document Risk (Passport / Visa)

**What it is**: Passports expiring, visa requirements not met, documents missing for some travelers. This is a booking-stage killer.

**Current state**: `traveler_details` is a hard blocker in booking stage but there's no `passport_status`, `visa_status`, or `document_expiry` concept. The MVB mentions `passport_status` as a booking blocker but it's not in the actual code.

| Notebook | Type | Priority |
|----------|------|----------|
| NB01 | Fact → `passport_status` (valid / expiring / expired / unknown) | Later |
| NB01 | Fact → `visa_requirements` (destination-specific, traveler-specific) | Later |
| NB02 | Hard blocker → `valid_passport` (in booking stage) | Later |
| NB02 | Hard blocker → `valid_visa` (in booking stage) | Later |

**Why it matters**: This is the visa crisis scenario (P1-S4). The MVB mentions it but the code doesn't enforce it. Must be modeled before booking stage.

---

## 8. Audit Mode / Wasted-Spend Analysis

**What it is**: Compare a proposed itinerary against market reality. Is the traveler getting value, or overpaying for a bad fit?

**Current state**: Not modeled. No concept of itinerary comparison, market pricing benchmarks, or fit scoring.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Derived signal → `budget_efficiency` (budget vs typical cost for this destination + composition) | Later |
| NB02 | Contradiction → `value_mismatch` (premium budget for budget destination, or vice versa) | Later |
| NB03 | Strategy item → "I found a better option" prompts | Later |

**Why it matters**: This is the wedge feature — the agency proves its value by finding waste the traveler couldn't see. Not MVP-now, but the data model needs to support it.

---

## 9. Booking Readiness Gate

**What it is**: Not just "all fields filled." The system should verify that a booking is actually executable: documents ready, payment confirmed, supplier availability checked.

**Current state**: The booking stage MVB has `traveler_details` and `payment_method` as hard blockers. But there's no `booking_readiness_score` or `execution_risk` concept.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Derived signal → `booking_readiness` (composite of document status, payment readiness, supplier confirmation) | Later |
| NB02 | Risk flag → `execution_blocker` (supplier sold out, visa timeline impossible, etc.) | Later |

**Why it matters**: A "complete" packet can still be unbookable. The system needs to distinguish between "all fields filled" and "actually executable."

---

## 10. Operational Ease

**What it is**: How hard will this trip be to execute? Multi-destination with 3 stopovers is harder than a direct package. Some destinations require more hand-holding.

**Current state**: `trip_complexity` exists in NB01's classifier but isn't wired into NB02 decisions or NB03 strategy.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Derived signal → `operational_complexity` (used to route to appropriate sourcing path) | Later |
| NB03 | Strategy item → complexity-aware session planning (complex trips need more questions) | Later |

**Why it matters**: High-complexity trips need more agent attention, more customer communication, and different sourcing. The system should flag them.

---

## 11. Network Supplier vs Open Market Distinction

**What it is**: Between preferred suppliers and open market, there's a "network" tier — suppliers the agency has worked with but aren't preferred. Different trust level, different pricing.

**Current state**: Not modeled. The sourcing hierarchy in the product docs is 4-tier but the code has no supplier tier concept.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Derived signal → `sourcing_tier` (internal / preferred / network / open) | Later |

**Why it matters**: This affects margin, reliability, and the questions the agent asks. Not MVP-now but should be in the data model before the sourcing engine is built.

---

## 12. Internal Draft vs Traveler-Safe Boundary Enforcement

**What it is**: The boundary exists in code (two different decision states) but there's no structural enforcement that internal-only data never leaks into traveler-facing output.

**Current state**: NB03 has separate builders for internal vs traveler outputs. The boundary is procedural (different functions), not structural. The golden path test checks for leakage but it's not enforced at the type level.

| Notebook | Type | Priority |
|----------|------|----------|
| NB03 | Strategy item → `is_internal` flag on every prompt block, enforced by builder | **MVP-now** |
| NB02 | Risk flag → `internal_data_present` (if hypotheses or unresolved contradictions exist, force internal draft) | **MVP-now** |

**Why it matters**: If a traveler sees "we're guessing your budget" or "there's a contradiction we couldn't resolve," the agency loses trust. The boundary is the most important safety mechanism.

---

## 13. Budget Feasibility Enforcement

**What it is**: "3L for 6 people in Maldives" is physically impossible. The system should flag this as a contradiction, not just accept it as a fact.

**Current state**: Budget is stored as a value. No minimum-cost-per-destination logic. No budget-vs-destination feasibility check. The `budget_conflict` contradiction type exists but only detects conflicts between two budget values, not budget vs reality.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Contradiction → `budget_feasibility` (stated budget vs minimum viable cost for destination + composition) | **MVP-now** |
| NB01 | Derived signal → `estimated_minimum_cost` (per person, per destination tier) | **MVP-now** |

**Why it matters**: This is the dreamer scenario and the revision-loop scenario. Without it, the system generates proposals that are mathematically impossible, which destroys credibility.

---

## 14. Question Quality by Decision Context

**What it is**: Not all questions are equally useful. "Where would you like to go?" is fine for a vague lead but useless for a customer who said "Andaman or Sri Lanka." The system should generate decision-driving questions, not form-fill questions.

**Current state**: Questions are templated strings from `_generate_question()`. They're context-free — same question regardless of what's already known. No intelligence about what question would actually move the needle.

| Notebook | Type | Priority |
|----------|------|----------|
| NB03 | Strategy item → `question_intent` (for each question: what decision does this unlock?) | **MVP-now** |
| NB03 | Strategy item → contextual question generation (use hypotheses to frame questions, not generic templates) | **MVP-now** |

**Why it matters**: This is the difference between an agent who feels supported vs an agent who's filling out a form. The current question templates are correct but dumb.

---

## 15. Confidence vs Decision-State Precedence

**What it is**: Confidence is currently a scoring mechanism. But the decision state should always win — even high confidence shouldn't override a hard blocker, and low confidence shouldn't prevent PROCEED_TRAVELER_SAFE if all blockers are actually filled.

**Current state**: Confidence feeds into the decision state machine but the precedence isn't explicit. The tone scaling (cautious → direct) could be misinterpreted as permission to skip uncertainty handling.

| Notebook | Type | Priority |
|----------|------|----------|
| NB02 | Invariant → decision_state always determined by blockers/contradictions, never by confidence alone | **MVP-now** |
| NB03 | Strategy item → confidence adjusts tone but never changes decision_state or suppresses required questions | **MVP-now** |

**Why it matters**: If someone later tweaks confidence thresholds to make the system "more decisive," they could create a pipeline that proceeds with missing blockers. The decision state is the boss.

---

## Summary by Priority

### MVP-Now (10 concepts)
| # | Concept | Notebook(s) | Impact |
|---|---------|-------------|--------|
| 1 | Sourcing Hierarchy | NB02, NB03 | Core differentiator — determines entire approach |
| 3 | Preferred Supplier | NB02, NB03 | Competitive advantage vs OTAs |
| 4 | Owner Seeded Context | NB01, NB02 | Agency's tribal knowledge as first-class data |
| 5 | Repeat-Customer Memory | NB01 | Don't re-ask known questions |
| 6 | Family/Elderly Suitability | NB02, NB03 | Prevent bad-fit trips |
| 12 | Internal/External Boundary | NB02, NB03 | Safety mechanism — prevent trust-destroying leaks |
| 13 | Budget Feasibility | NB01, NB02 | Prevent impossible proposals |
| 14 | Question Quality | NB03 | Agent usefulness |
| 15 | Confidence vs Decision Precedence | NB02, NB03 | Invariant safety |

### Later (5 concepts)
| # | Concept | Notebook(s) | Reason for deferral |
|---|---------|-------------|---------------------|
| 2 | Margin/Commercial | NB02 | Needs pricing data first |
| 7 | Document Risk | NB01, NB02 | Booking-stage concern, not discovery |
| 8 | Audit Mode | NB02 | Needs market pricing data |
| 9 | Booking Readiness | NB02 | Booking-stage concern |
| 10 | Operational Ease | NB02, NB03 | Optimization, not blocker |
| 11 | Network Supplier Tier | NB02 | Sourcing engine not built yet |
