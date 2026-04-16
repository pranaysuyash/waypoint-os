# Deep Dive Discussion: PROJECT_THESIS.md — Four Open Threads

**Date**: 2026-04-16
**Source**: `Docs/PROJECT_THESIS.md`
**Cross-references**: `PRODUCT_VISION_AND_MODEL.md`, `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md`, `Sourcing_And_Decision_Policy.md`, `SINGLE_TENANT_MVP_STRATEGY.md`, `PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md`, `V02_GOVERNING_PRINCIPLES.md`, `DATA_MODEL_AND_TAXONOMY.md`
**Status**: Open for discussion — no code changes

---

## Thread 1: "Copilot, Not Replacement" — Where's the Line?

### The Thesis Position
> "The product is positioned as an Agency Copilot that compresses the workflow... leaving the human to manage the relationship."
> — `Docs/PROJECT_THESIS.md` L4, L14

> "The product must be sold as a Workspace where AI is embedded, not a replacement for the agent."
> — `Docs/PRODUCT_VISION_AND_MODEL.md` L76

### Why This Matters
The framing is strategically correct for adoption — agencies will resist "replacement" framing. But the system already models significant judgment:
- Decision gating (`PROCEED`, `ASK_FOLLOWUP`, `ESCALATE`, `STOP_NEEDS_REVIEW`) — `Docs/V02_GOVERNING_PRINCIPLES.md` L44-50
- Lifecycle scoring (`ghost_risk`, `churn_risk`, commercial decisions) — `Docs/DISCUSSION_LOG.md` L473-479
- Budget feasibility verdicts — `Docs/FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` L89-92
- Per-person suitability flags and wasted spend detection — `Docs/DATA_MODEL_AND_TAXONOMY.md` L62-73

### The Tension
As the system gets better at judgment, the "copilot" framing may become a marketing fiction. Three scenarios to consider:

| Scenario | Risk | Mitigation |
|----------|------|------------|
| System auto-proceeds on `PROCEED_TRAVELER_SAFE` without human review | Agency feels bypassed on quality control | Require explicit "approve and send" gate even for traveler-safe outputs |
| System flags `STOP_NEEDS_REVIEW` on a complex trip the agent was confident about | Agent loses trust: "It doesn't understand my client" | Show evidence (not just verdict), let agent override with logged rationale |
| Junior agent uses system as crutch, never develops planning skill | Agency owner sees tool as replacing training, not augmenting | Build "learning mode" that explains *why* the system made a recommendation |

### Open Questions
1. **Autonomy gradient**: Should the system have configurable autonomy levels (e.g., "show me everything" vs. "flag only problems")? This maps to the `operating_mode` axis but isn't exposed as an agency-level preference yet.
2. **Override dignity**: When an agent overrides the system, does the system "remember" that override for similar future cases? This feeds into the traveler memory / learned preferences loop (`PRODUCT_VISION_AND_MODEL.md` L67-69).
3. **Positioning evolution**: At what scale does "copilot" honestly become "operating system"? The project name already says "AI Ops" — the thesis says "copilot." These may need reconciling as the product matures.

### Current Codebase State
- Human override protocol is specified in architecture (`FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` L118) but not yet implemented as a runtime path.
- `operating_mode` is a top-level packet field (`V02_GOVERNING_PRINCIPLES.md` L73) — could support an `agent_supervised` vs. `agent_autonomous` sublayer.

---

## Thread 2: Intelligence Layer as Lead-Gen — Who Uploads, and What Converts?

### The Thesis Position
> "A free 'Intelligence Layer' (Itinerary Audit) is used as a lead-gen tool. It allows users to upload existing plans... which then converts them into high-quality leads for agency partners."
> — `Docs/PROJECT_THESIS.md` L17-18

> "Consumer Audit → Structured Brief → Agency Execution"
> — `Docs/PRODUCT_VISION_AND_MODEL.md` L91

### The Two User Personas for the Free Engine

| Persona | Upload Motivation | Conversion Path | Friction |
|---------|-------------------|-----------------|----------|
| **Agency owner (self-audit)** | Validate own itinerary before sending to client | Adopts full platform | Low — already knows the tool |
| **End traveler (got a plan elsewhere)** | "Is this plan any good?" | Gets handed off to partner agency | High — trust gap, "who are these people?" |

### Why This Distinction Is Critical

The thesis conflates two very different funnels:

**Funnel A: Agency self-audit → platform adoption**
- This is a classic PLG (product-led growth) hook.
- The agency experiences value first, then upgrades to the full workflow tool.
- Aligns with `PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md` Approach A: "Free Beta Tester" (L124-137).
- Lower CAC, higher conversion likelihood.

**Funnel B: Consumer audit → agency referral**
- This is a marketplace/lead-gen play.
- Requires trust transfer: consumer trusts the *audit tool*, but does that trust extend to the *referred agency*?
- Needs: curated agency partner network, quality guarantees, referral tracking, revenue share.
- Higher CAC, needs volume, and exposes to regulatory/liability questions (`Docs/LEGAL_BASICS.md` exists but not reviewed here).

### Recommendation
- **MVP**: Focus exclusively on Funnel A. The single-tenant strategy (`SINGLE_TENANT_MVP_STRATEGY.md` L370-373: "KEEP in scope: Core decision engine") already locks this.
- **Post-validation**: Layer Funnel B as a growth surface once the audit engine has proven accuracy with real agency trips (aligns with `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` Stage 7: "GTM-facing surfaces only when quality floor is met").
- **Open question**: Does the "free engine" need its own quality bar distinct from the full platform? An audit that misses a real risk destroys trust faster than no audit at all.

### Evidence Gap
- No current test coverage or acceptance criteria for audit-mode accuracy. The `operating_mode: audit` exists as a routing concept (`V02_GOVERNING_PRINCIPLES.md` L56) but has no dedicated eval suite.
- `QUESTION_BANK_AND_TAXONOMY.md` L39-40 has audit-specific questions, but no linked fixture set.

---

## Thread 3: Sourcing Hierarchy — Fixed or Configurable?

### The Thesis Position
> "Operational Ease: Prioritizing a sourcing hierarchy: Preferred Network → Network/Consortium → Open Market."
> — `Docs/PROJECT_THESIS.md` L10

> "The system does not search the open web first. It follows a strict hierarchy to preserve agency margins and operational reliability."
> — `Docs/Sourcing_And_Decision_Policy.md` L1-4

### Current Implementation State
The sourcing hierarchy is modeled as a **taxonomy bracket** in `DATA_MODEL_AND_TAXONOMY.md` L28-31:
```
- package_suitable    → Internal Standard Packages
- custom_supplier     → Preferred Supplier Inventory
- network_assisted    → Network/Consortium
- open_market         → Last resort
```

The `PRODUCT_VISION_AND_MODEL.md` L35 locks the decision rule:
> "The system should recommend the 'best acceptable option' within the preferred supply chain, rather than the 'global optimum' from the internet, unless explicitly asked to widen the search."

### The Configurability Question

| Aspect | Fixed (Current) | Configurable (Future) |
|--------|-----------------|----------------------|
| Hierarchy order | Internal → Preferred → Network → Open | Agency defines own priority order |
| Margin thresholds | Not yet implemented | Agency sets minimum margin per tier |
| Supplier blacklist/whitelist | Not modeled | Agency marks specific vendors as preferred/blocked |
| "Widen search" trigger | "Unless explicitly asked" | Agency sets rules: e.g., "always check open market for flights" |

### Recommendation
- **MVP (single-tenant)**: Fixed hierarchy is correct. The one partner agency's preferences are hardcoded in config (`SINGLE_TENANT_MVP_STRATEGY.md` L172-176 — `Config` class with hardcoded agency details). Sourcing hierarchy is part of that config.
- **Multi-tenant**: Must become per-agency configurable. This is a first-class differentiator — "the system plans the way YOUR agency plans."
- **Implementation path**: The `planning_route` bracket assignment in the taxonomy (`DATA_MODEL_AND_TAXONOMY.md` L28-31) should be driven by an agency-level `SourcingPolicy` config object, not hardcoded logic.

### Immediate Gap
- No `SourcingPolicy` model exists in `src/intake/packet_models.py`.
- No test validates that sourcing hierarchy actually influences option ranking (Stage 3 in `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` is not yet implemented).
- The hierarchy is currently a classification label, not a decision driver.

---

## Thread 4: Per-Person Suitability — Data Source and Depth

### The Thesis Position
> "Client Fit: Moving from group-level planning to per-person suitability (e.g., toddler/elderly suitability for specific activities)."
> — `Docs/PROJECT_THESIS.md` L8

> "The system must evaluate activity utility at a per-person level, not a group level."
> — `Docs/Sourcing_And_Decision_Policy.md` L30

### Current Implementation State (from codebase audit)

**What exists:**
- `SubGroup` model in `src/intake/packet_models.py` (L170-180) — captures per-group size, budget share, constraints
- `composition_risk` and `coordination_risk` as derived signals in `src/intake/decision.py` (L1110-1130)
- Ambiguity detection for vague age/composition ("big family") in `src/intake/normalizer.py` (L86-89)
- Traveler classification brackets in taxonomy: `family_with_toddler`, `family_with_elderly`, `mixed_group` — `DATA_MODEL_AND_TAXONOMY.md` L10-12

**What's missing:**
- `activity_matcher.py` — referenced in architecture docs (`Docs/architecture/SCENARIO_HANDLING_ARCHITECTURE.md` L172-180) but **not yet implemented**
- Per-person utility scoring (`adult_usability`, `elderly_usability`, `toddler_usability`) — defined in taxonomy (`DATA_MODEL_AND_TAXONOMY.md` L68-72) but **no runtime code**
- Wasted spend calculation — formula defined (`DATA_MODEL_AND_TAXONOMY.md` L65, L72) but **no implementation**

### Data Source Question

Where does person-level context come from?

| Source | Reliability | Coverage | Implementation |
|--------|-------------|----------|----------------|
| **Explicit intake questions** | High | Partial — depends on what agent asks | `QUESTION_BANK_AND_TAXONOMY.md` L34-36 has suitability questions |
| **Inferred from group composition** | Medium | Good for hard constraints (age → mobility) | `normalizer.py` derives signals from age bands |
| **Traveler memory (repeat clients)** | High | Only for returning travelers | Architected (`PRODUCT_VISION_AND_MODEL.md` L67-69) but not built |
| **Agency-supplied notes** | High | Spotty — depends on agency discipline | `OwnerConstraint` model captures this (`packet_models.py` L162-167) |
| **OCR from documents** | Medium | Narrow — passport → nationality/age | Stage 1 TODO: OCR layer (`DISCUSSION_LOG.md` L237-239) |

### Depth Question: How Granular Should Suitability Be?

| Level | Example | Complexity | Value |
|-------|---------|------------|-------|
| **L1: Binary flags** | "toddler_friendly: yes/no" | Low | Catches obvious mismatches |
| **L2: Scored compatibility** | "elderly_usability: 0.3 (steep stairs, 2km walk)" | Medium | Enables trade-off ranking |
| **L3: Per-person scheduling** | "Grandma stays at hotel during theme park, rejoins for dinner" | High | Enables split-day alternatives |

### Full Production Target (Phased by Dependency)
All three levels are part of the production system. They phase by dependency, not by ambition:

| Phase | Level | Depends On | Unlocks |
|-------|-------|------------|---------|
| **Phase 1** (Stage 2: Feasibility) | L1: Binary flags | Intake compiler, composition extraction | Feasibility verdicts, blocker detection, basic risk flags |
| **Phase 2** (Stage 3: Option Generation) | L2: Scored compatibility | L1 flags + activity/destination data model | Wasted spend detection, trade-off ranking, per-person utility |
| **Phase 3** (Stage 4+: LLM + Execution) | L3: Per-person scheduling | L2 scores + option space + itinerary structure | Split-day alternatives, personalized pacing, family-aware day plans |

- **Data strategy**: Explicit intake + inferred signals are the foundation. Traveler memory and OCR are additive layers that compound over time — they don't gate any phase.

### Implementation Priority (from First Principles Build Sequence)
Per `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md`:
- Stage 2 (Feasibility) → L1 binary flags ← **current build target**
- Stage 3 (Option Generation) → L2 scored compatibility ← **requires `activity_matcher.py` + activity data model**
- Stage 4 (LLM Augmentation) → L3 natural language scheduling suggestions ← **requires working option space**

---

## Cross-Thread Synthesis

These four threads are not independent — they form a coherent product tension:

```
         Thread 1 (Copilot line)
              ↕
    How much judgment does
    the system exercise?
              ↕
Thread 3 (Sourcing) ←→ Thread 4 (Suitability)
    What options does          How deep does
    it consider?               fit-checking go?
              ↕
    How does the system
    prove its value?
              ↕
         Thread 2 (Lead-gen)
```

**The unifying insight**: The system's credibility as a "copilot" depends on Threads 3 and 4 being excellent. If sourcing is smart and suitability is accurate, the agent trusts the system → the system earns more autonomy (Thread 1) → the audit engine can credibly generate leads (Thread 2).

**Build order implication**: Threads 3 and 4 are foundational. Thread 1 is a configuration/UX question. Thread 2 is a GTM question that should not drive architecture.

---

## Open Decisions for Discussion

| # | Decision | Options | Recommendation | Blocking? |
|---|----------|---------|----------------|-----------|
| D1 | Autonomy gradient for copilot | Fixed "always review" vs. configurable per-agency | Configurable with "always review" as default; agency can loosen | No — UX layer, phased after core |
| D2 | Free engine target persona | Agency self-audit vs. consumer audit vs. both | Both are production targets; agency self-audit ships first (Stage 2), consumer audit ships with GTM surface (Stage 7) | No — sequenced by dependency |
| D3 | Sourcing hierarchy configurability | Fixed vs. per-agency | Per-agency `SourcingPolicy` config object — design contract now, implement with vendor/supplier models | No — design now, implement with Gap #01 |
| D4 | Suitability depth phasing | What scope for `activity_matcher.py` and when | All three levels (L1→L2→L3) are production targets. See detailed breakdown below. | **Yes** — determines Phase 2 data model scope |
| D5 | Override learning | Overrides are logged vs. overrides influence future behavior | Log + influence; override patterns feed traveler memory and agency-level learned preferences | No — additive, layers on customer lifecycle (Gap #06) |
| D6 | Audit-mode eval suite | None (current) vs. dedicated accuracy benchmarks | Dedicated eval suite required — audit is a production surface, not a demo. See detailed breakdown below. | **Yes** — quality gate for audit surface |

---

## D4 Detailed: Suitability Depth — What `activity_matcher.py` Actually Needs to Do

### The Problem in Plain Terms
A family of 5 (2 adults, 1 elderly parent with knee trouble, 1 child age 8, 1 toddler age 2) is going to Singapore. The agency puts Universal Studios on Day 2. The system needs to know:

- The toddler can't ride most attractions — that's a wasted ticket (~₹5,000)
- The elderly parent will struggle with 6+ hours of walking — that's a comfort risk
- The child is fine for *most* rides but not roller coasters — partial fit
- The adults are fine — full fit

**Without suitability scoring**, the system treats "Universal Studios for 5 people" as one line item. **With it**, the system can flag: "3 of 5 people get full value from this ₹25,000 spend. Consider: adults + child do USS, grandparent + toddler do Gardens by the Bay (₹2,000)."

That's the wasted spend detection the thesis promises.

### What Exists Today (Runtime Code)

| Component | Status | Location |
|-----------|--------|----------|
| Party composition extraction (adults/children/toddlers/elderly) | ✅ Working | `src/intake/decision.py` L804-830 |
| Composition-aware budget modifiers (toddler surcharge 0.30, elderly 0.05) | ✅ Working | `src/intake/decision.py` L696-702 |
| `SubGroup` model for multi-party trips | ✅ Working | `src/intake/packet_models.py` L170-181 |
| Coordination risk (budget spread across subgroups) | ✅ Working | `src/intake/decision.py` L1110-1129 |
| Group composition brackets (`family_with_toddler`, `mixed_group`, etc.) | ✅ Documented | `DATA_MODEL_AND_TAXONOMY.md` L7-12 |
| `ActivitySuitability` dataclass (architecture spec) | 📐 Designed | `Docs/architecture/SCENARIO_HANDLING_ARCHITECTURE.md` L172-180 |
| `activity_matcher.py` module | ❌ Not implemented | Referenced but does not exist in `src/intake/` |
| Per-person utility scoring (adult/elderly/toddler usability) | ❌ Not implemented | Defined in `DATA_MODEL_AND_TAXONOMY.md` L67-72, no runtime code |
| Wasted spend formula | ❌ Not implemented | Formula in `DATA_MODEL_AND_TAXONOMY.md` L65,72 and `Sourcing_And_Decision_Policy.md` L30-33, no runtime code |

### What Needs to Be Built (Full Production Scope)

**Phase 1 — L1 Binary Flags** (unlocks: basic feasibility + blocker detection)
```
Depends on: Stage 2 intake compiler (✅ exists)
```
- Activity type taxonomy: `physical_intense`, `walking_heavy`, `water_based`, `height_required`, `seated_show`, `nature_walk`, `shopping`, `dining`
- Per-type binary suitability matrix:
  ```
  {activity_type} × {traveler_type} → suitable: bool
  e.g., "roller_coaster" × "toddler" → false
       "botanical_garden" × "elderly" → true
  ```
- Risk flag generation: if activity is unsuitable for any group member → add `StructuredRisk` with `category: "activity"`, `affected_travelers: ["toddler_1"]`
- This is a **static lookup table** — no LLM needed, no external data needed

**Phase 2 — L2 Scored Compatibility** (unlocks: wasted spend detection + trade-off ranking)
```
Depends on: L1 flags + activity cost data + option generation skeleton (Stage 3)
```
- Replace binary suitable/not with a 0.0-1.0 score per person per activity:
  ```python
  @dataclass
  class PersonActivityScore:
      traveler_id: str          # "adult_1", "elderly_1", "toddler_1"
      activity_type: str
      usability_score: float    # 0.0 (cannot participate) to 1.0 (full value)
      limiting_factors: List[str]  # ["steep_stairs", "2km_walking", "height_requirement"]
      warnings: List[str]
  ```
- Wasted spend calculation (per `Sourcing_And_Decision_Policy.md` L30-33):
  ```
  high_utility_users = count(score > 0.7 for each person)
  total_tickets = party_size
  if total_tickets > high_utility_users:
      wasted_spend_ratio = (total_tickets - high_utility_users) / total_tickets
      wasted_amount = activity_cost * wasted_spend_ratio
      → flag as "high_wasted_spend_risk" with suggested alternative
  ```
- This requires an **activity data model** — at minimum, a catalog of activity types with their physical demands, cost ranges, and age suitability profiles
- Alternative activity suggestion: for each flagged activity, system suggests a parallel option for excluded travelers

**Phase 3 — L3 Per-Person Scheduling** (unlocks: split-day planning, family-aware itineraries)
```
Depends on: L2 scores + working itinerary structure + option space (Stage 3-4)
```
- Day-level split planning: given a day's activities and the L2 scores, propose split schedules:
  ```
  Day 2 Morning:
    Group A (adults + child): Universal Studios
    Group B (grandparent + toddler): Gardens by the Bay + lunch at Satay by the Bay
  Day 2 Evening:
    Rejoin: Dinner at Clarke Quay
  ```
- Requires: time-of-day activity data, transport logistics between split venues, reunion point planning
- This is where LLM augmentation adds real value — generating natural-language day plans with scheduling rationale
- Also requires itinerary structure (not just options) — this is a Stage 4+ capability

### The Blocking Decision
The question is **not** "should we build L1 or L2" — both are production targets. The blocking question is:

> **What data model do we design NOW that supports all three levels without rework?**

Specifically:
1. Does the activity taxonomy live in `src/intake/` or in a separate `src/planning/` module? (Layer ownership per `V02_GOVERNING_PRINCIPLES.md`)
2. Does the `ActivitySuitability` dataclass (already spec'd in architecture docs) need additional fields for L2/L3 now, or can it be extended later without breaking contracts?
3. Where does the activity catalog data come from? Hardcoded table? Agency-configurable? External API?

---

## D6 Detailed: Audit-Mode Eval Suite — What "Quality Gate" Actually Means

### The Problem in Plain Terms
The audit surface ("Upload your itinerary, we'll tell you what's wrong") is a **production feature**, not a demo. If someone uploads a real Singapore itinerary and the system:

- Misses that the hotel is 45 minutes from the activities → credibility destroyed
- Flags a "wasted spend" that isn't actually wasted (e.g., toddler actually loves that activity) → false positive annoyance
- Says "budget is feasible" when it's clearly ₹50K short → liability risk
- Doesn't catch a visa requirement for a transit country → serious operational failure

The audit engine's mistakes are **visible to end users** (either the agency or, in Funnel B, the consumer). Unlike internal decision gating where the agent can catch errors, audit output is the product's face.

### What Exists Today

| Audit Capability | Test Coverage | Location |
|-----------------|---------------|----------|
| Audit mode routing (detects "audit" in input, sets `operating_mode: audit`) | ✅ Tested | `tests/test_nb02_v02.py` L199-216, `tests/test_e2e_freeze_pack.py` L213-237 |
| Audit-specific goal text (different from normal_intake) | ✅ Tested | `tests/test_nb03_v02.py` L654-661 |
| Internal data audit (counts hypotheses, contradictions) | ✅ Tested | `tests/test_nb03_v02.py` L708-721 |
| Budget feasibility in audit mode | ✅ Partial | Checks feasibility and adds contradiction — but no accuracy benchmark |
| Wasted spend detection in audit mode | ❌ None | `activity_matcher.py` doesn't exist — can't detect wasted spend |
| Pacing/logistics audit | ❌ None | No module checks if Day 1 has 6 activities across 3 areas of the city |
| Hotel-activity distance audit | ❌ None | No geographic proximity check |
| Visa/document risk in audit mode | ❌ None | Visa parser referenced but not implemented for audit surface |
| False positive rate measurement | ❌ None | No fixture set that tests "this itinerary is actually fine, don't flag it" |
| False negative rate measurement | ❌ None | No fixture set that tests "this itinerary has a real problem, catch it" |

### What a Production Eval Suite Requires

**Layer 1: Fixture Set (the "exam paper")**

A curated set of real-world-representative itineraries with known issues and known non-issues:

| Fixture Category | Count Needed | Example |
|-----------------|--------------|---------|
| **Clean itineraries** (no issues — tests false positive rate) | 10-15 | Well-paced Singapore family trip, correct budget, appropriate activities |
| **Budget-broken itineraries** | 5-8 | ₹1.5L budget for 5 people × 6 nights in Singapore (infeasible) |
| **Suitability-broken itineraries** | 5-8 | Theme park day with elderly + toddler, no alternatives |
| **Pacing-broken itineraries** | 5-8 | 6 activities on Day 1, nothing on Day 4 |
| **Logistics-broken itineraries** | 3-5 | Hotel in Sentosa, all activities in Orchard/Marina Bay |
| **Document-risk itineraries** | 3-5 | Indian passport, Schengen transit without visa mention |
| **Multi-issue itineraries** | 5-8 | Combinations of above — tests if system catches ALL issues |
| **Edge cases** | 3-5 | Solo traveler (no group dynamics), 15-person group (coordination chaos) |
| **Total** | ~40-60 fixtures | |

Each fixture needs:
- Input: the itinerary (structured or freeform — test both)
- Expected issues: what the audit should flag (with severity)
- Expected non-issues: what the audit should NOT flag
- Acceptable tolerance: how many expected issues can be missed before the test fails

**Layer 2: Accuracy Metrics (the "grading rubric")**

| Metric | Definition | Target |
|--------|------------|--------|
| **Recall** (sensitivity) | % of real issues that the system catches | ≥ 85% for critical issues, ≥ 70% for medium |
| **Precision** | % of flagged issues that are actually real | ≥ 80% (≤ 20% false positive rate) |
| **Severity accuracy** | When it catches an issue, does it rate severity correctly? | ≥ 75% exact match |
| **Coverage** | Does the audit check all declared categories? | 100% — if we claim to check budget, we must check budget |

**Layer 3: Regression Gate (the "CI check")**

- Every PR touching `src/intake/` runs the audit fixture suite
- Accuracy metrics must not regress below thresholds
- New fixture categories added as new audit capabilities ship
- Historical trend tracking: are we getting better or worse over time?

### What This Depends On

The eval suite can be **designed and fixture-authored now**, but full accuracy measurement requires:

| Capability | Needed For | Status |
|------------|------------|--------|
| Budget feasibility | Budget-broken fixtures | ✅ Working (`check_budget_feasibility`) |
| Activity suitability (D4) | Suitability-broken fixtures | ❌ Blocked on `activity_matcher.py` |
| Pacing analysis | Pacing-broken fixtures | ❌ Not implemented |
| Geographic proximity | Logistics-broken fixtures | ❌ Not implemented |
| Visa/document risk | Document-risk fixtures | ❌ Parser referenced, not implemented |

### The Blocking Decision
The question is:

> **Do we build the eval framework and author fixtures NOW (even before all audit capabilities exist), or wait until the capabilities are ready?**

Recommendation: **Build now, gate incrementally.**
- Author the full fixture set (~40-60 cases) as the ground truth for what audit must eventually catch
- Implement the eval runner framework that measures recall/precision/severity accuracy
- Start with budget-only accuracy (the one capability that works today) — this establishes the pattern
- As each new audit capability ships (suitability, pacing, logistics, visa), add it to the eval suite and enforce its accuracy gate
- This means the eval suite is both a **quality gate** and a **roadmap** — it shows exactly what audit can and can't do at any point

### Relationship to D4
D4 and D6 are coupled:
- D4 (suitability depth) determines whether the audit can catch suitability issues
- D6 (eval suite) determines whether we can *prove* the audit catches them correctly
- If D4 delivers `activity_matcher.py` without D6 having suitability fixtures, we can't measure if it works
- If D6 has suitability fixtures without D4 being implemented, the tests correctly show 0% recall — which is useful as a progress tracker

Build both in parallel. They reinforce each other.

---

*This document is a discussion artifact. Decisions made here should be promoted into implementation contracts via the standard workflow: document → plan → implement → verify → document outcomes.*
