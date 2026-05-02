# Independent Architectural Assessment

**Date**: 2026-05-02 | **Status**: Active Baseline | **Author**: Independent first-principles analysis

**Purpose**: Architectural assessment derived from first-principles reasoning — NOT from reading code or docs. Identifies gaps, risks, and design concerns that code/doc analysis alone may miss.

---

## Philosophy Assessment

The governing philosophy — "deterministic-first, LLM only when necessary" — is correct and rare. Most AI startups default to LLM-first. This got the order right.

**But it's applied inconsistently across layers:**

| Layer | Current | Should |
|-------|---------|--------|
| NB01 Extraction | Regex → LLM fallback ✅ | + structured source adapters (form fields, imports) |
| NB02 Decision | Rules → LLM fallback ✅ | + numeric feasibility models, not just yes/no |
| NB03 Strategy | Switch/case over enums ❌ | Template filling from packet facts → LLM polish |

The gap at NB03 is architectural. When strategy is purely generic ("Based on what you've shared"), it fails the personalization test that makes users feel heard. The entire UX vision ("She actually listened to us") depends on NB03 being data-driven.

---

## Missing Architectural Primitives

### 1. A Numeric Feasibility Model

Current feasibility is boolean (feasible/infeasible). A travel system needs NUMERIC models:
- For destination + dates + party: what does it cost?
- Given budget: what's feasible?
- Given constraints: what's optimal?

The hardcoded table of ~20 destinations doesn't scale. Need: cost estimation backed by updatable destination cost tables → eventually live pricing APIs → gap computation: `estimated_cost - stated_budget`.

### 2. A Structured Constraint Model (Hard vs Soft with Weights)

`CanonicalPacket` tracks constraints as slots in facts. But no constraint classification:
- **Hard**: Cannot violate (visa timeline, min_age, budget ceiling)
- **Soft**: Optimize for (pace, food, hotel style)
- **Weighted trade-offs**: When constraints conflict, which wins?

Example: "Budget ₹4L, want Paris + Switzerland in June." Destination+season is hard. Budget is hard. ₹4L can't do both in peak. Needs explicit trade-off surfacing, not just a "tight" flag.

### 3. A Sourcing Abstraction (Even Without Live Data)

Sourcing hierarchy is architecturally right. But zero abstraction exists — not even a stub that could be filled later.

**Needed now** (without supplier data): `SourcingPolicy` per agency with hierarchy order, margin floors, category overrides. NB02 annotates decisions with `sourcing_tier` even if all resolve to "open_market." Creates the model that supplier data plugs into.

### 4. An Output Rendering Pipeline

Output is `PromptBundle` — text blobs. This is the architecturally weakest link. A travel system outputs:
- **Itinerary options**: Day-by-day with activities, hotels, transport
- **Cost breakdowns**: By category (flights, stay, activities, food, buffer)
- **Suitability badges**: Per activity per person ("Snorkeling ✅ Adults ✅ Kids ❌ Toddlers")
- **Trade-off comparisons**: Option A vs B across cost, comfort, pace, fit

None exists. The system produces text a human must manually convert into a proposal. Defeats "workflow compression."

### 5. A Revision Graph / Diff Model

The UX vision describes "What changed and why" between itinerary versions. Requires:
- **Packet snapshots**: Immutable copies at key points
- **Diff computation**: What fields changed?
- **Rationale attachment**: Why did this change?

`CanonicalPacket.events` captures mutations but not full state at each point. Snapshots + diffs = revision comparison UX.

---

## Design Smells

### 1. The `_obj_to_dict()` Pattern
Tries Pydantic `model_dump` → `asdict` → `vars()` → gives up. Means no unified serialization strategy. Eventually causes silent data loss with new object types.

### 2. Dual Persistence Pattern
JSON files AND PostgreSQL side-by-side. Two consistency models. A trip in JSON referencing a user in Postgres — one out of sync = hard bugs.

### 3. `maturity="stub"` as Honest Debt
Marking unimplemented signals as `stub` is HONEST — one of the best patterns. But honesty without a resolution plan is just documentation of failure. Each stub needs: target date, what data it needs, who owns it.

### 4. "Everything is a Slot" Pattern
Every field carrying provenance is conceptually right. But `party_size: 4` carries same structural weight as `destination_candidates: [Paris, Rome, Barcelona]`. Output/display layer needs to simplify — travelers don't need confidence scores on party size.

### 5. File Size Smell
>500 lines = smell. >1,000 = warning. >2,000 = defect. `server.py` at 3,535L, `decision.py` at 2,240L, `extractors.py` at 1,808L. `routers/` exists but `server.py` defines most routes inline — suggests decomposition was started then abandoned.

---

## Vision vs Code Gaps

### The Two-Screen Model
Vision: Agency screen + traveler screen with live brief. Code: Workbench (agency) only. No traveler live brief. Biggest UX gap.

### The Dynamic Question Router
Vision: Priority-based question selection (P1: blocking → P4: refinements). Code: `QUESTION_PRIORITY_ORDER` exists but no iterative next-question engine. All follow-ups at once.

### "Why This Matters" Annotations
Vision: Every question carries explanation ("affects pricing by 30-40%"). Code: `QuestionWithIntent` has `intent` field — exists structurally, never populated with real explanations.

### The Sourcing Hierarchy
Vision: Rich 4-tier model. Code: `sourcing_path` stub set to "open_market" or "network" by trivial heuristic. Tier concept not even modeled.

---

## Production Readiness Requirements

### 1. Idempotent Pipeline Execution
Same input twice → detect duplicate → return existing or offer re-process. Currently creates new packet regardless.

### 2. Graceful Degradation at Every Tier

| Component | If Fails | Currently |
|-----------|----------|-----------|
| LLM call | Falls to default | ✅ Safe |
| Geography lookup | Should use regex fallback | Unknown |
| DB query | Should use in-memory fallback | Not implemented |

### 3. Tenant Isolation That's Testable
"Can agency A's query ever return agency B's data?" Must be provably "no" through RLS + integration tests. RLS documented, not implemented.

### 4. Operator Override Protocol
- Every override logged: who, when, what, why
- Patterns detectable (D5: "overridden 15x on family trips → suggest policy change")
- No override can silently change hard safety constraints

### 5. Pricing With Uncertainty
Fee calculation produces single numbers. Travel has uncertainty: supplier rate changes, currency fluctuations, seasonal surcharges. Need ranges with confidence bands.

---

## Summary

| Dimension | Verdict | Key Gap |
|-----------|---------|---------|
| Architecture Philosophy | ✅ Strong | Applied inconsistently across layers |
| Data Model | 🟡 Adequate | Missing constraint classification, sourcing abstraction |
| Pipeline | 🟡 Adequate | Missing idempotency, timeout, output rendering |
| Output/UX Pipeline | 🔴 Weak | No structured output, no rendering, no revision graph |
| Production Readiness | 🔴 Not Ready | Missing tenant isolation tests, graceful degradation, pricing uncertainty |
| Documentation Quality | 🔴 Problematic | ~70+ audit docs, many stale/contradictory |

**The system is a decision engine that doesn't produce decisions anyone can see. The spine works. The output doesn't.**

---

*Cross-reference with `BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md` for feature gaps and `BASELINE_AUDIT_CODEBASE_2026-05-02.md` for component ratings.*