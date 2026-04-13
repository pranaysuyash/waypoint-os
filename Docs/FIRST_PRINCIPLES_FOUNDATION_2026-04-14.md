# First Principles Foundation (2026-04-14)

## Why this exists
This document captures first-principles reasoning for the Travel Agency Agent system and translates it into a strict build sequence.

---

## Part A: First-Principles Framing (Captured Discussion)

### 1) What are we building?
A **decision system for custom travel agencies** that converts messy traveler intent into **bookable, defensible plans** with less dependence on senior planners.

Not:
- a generic AI itinerary generator
- a shallow chatbot that only asks destination/date/budget

### 2) Ground truths (non-negotiable)
1. Custom trip planning is a **constraint satisfaction problem under uncertainty**.
2. Agency value is **judgment + trust + execution reliability**, not information retrieval.
3. Most failures come from **missed constraints**, not missing attractions.
4. Profit and scalability come from **repeatable process**, not one-off creativity.
5. Without provenance and state integrity, accountability collapses.

### 3) Objective function
Maximize:
- traveler-fit quality
- operational reliability
- agency margin
- planning speed

Minimize:
- rework loops
- contradictions
- in-trip failure risk
- concentration risk in one planner

### 4) Irreducible primitives
1. **Intent capture** (explicit + inferred)
2. **Constraint model** (hard vs soft)
3. **Feasibility engine**
4. **Option space construction**
5. **Trade-off ranking**
6. **Execution packet** (bookable artifacts)
7. **State + provenance** (source envelope, confidence, rationale)

### 5) Architecture implication
Start with a **deterministic backbone**, then layer selective LLM specialization.

- Deterministic: normalization, schema checks, blockers, contradiction detection, gate decisions
- LLM: ambiguity handling, nuanced follow-ups, personalization, rationale language

### 6) Things to avoid early
- premature multi-agent complexity without packet/state integrity
- GTM expansion before reliable planning output quality
- full automation without human override and audit trail

### 7) MVP success definition
Given messy context, system consistently produces:
- normalized hard/soft constraints
- contradiction + blocker flags
- feasibility verdict
- 2–3 ranked options with rationale
- clear bookable next actions

---

## Part B: First-Principles Build Sequence (Strict Order)

The following order is intentionally dependency-driven: each layer unlocks the next.

### Stage 0: Invariants and contracts
- Freeze canonical packet and source envelope contracts.
- Define hard/soft constraint taxonomy and blocker classes.
- Define decision-state contract (`PROCEED`, `ASK_FOLLOWUP`, `ESCALATE`, `STOP_NEEDS_REVIEW`).
- Define non-negotiable logging fields (who decided what, why, from which source).

**Exit criteria**
- Schemas and decision contracts are versioned and testable.

### Stage 1: Deterministic intake compiler (no orchestration complexity)
- Build/strengthen normalization and extraction adapters for freeform + structured inputs.
- Implement contradiction and missing-critical-field detectors.
- Implement MVB (Minimum Viable Brief) gate per stage.

**Exit criteria**
- Same input always yields deterministic packet + deterministic gate result.

### Stage 2: Feasibility and budget realism engine
- Add feasibility checks (season, trip length realism, transfer burden, traveler profile compatibility).
- Add budget decomposition and realism checks against destination/date profile assumptions.

**Exit criteria**
- Engine can explicitly explain “why feasible / why not feasible” with traceable evidence.

### Stage 3: Option generation skeleton
- Build deterministic option-space scaffold (2–3 canonical option archetypes).
- Add ranking model with explicit weighted trade-offs (cost, comfort, pace, logistics risk, profile fit).

**Exit criteria**
- Option ranking is explainable and reproducible.

### Stage 4: Selective LLM augmentation
- Use LLM only where deterministic logic is insufficient:
  - ambiguity compression
  - intelligent follow-up question drafting
  - rationale narrative and traveler-facing phrasing
- Keep packet truth and gate decisions deterministic.

**Exit criteria**
- LLM output cannot override hard constraints or gates without explicit human override.

### Stage 5: Execution packet and handoff
- Convert winning option into a bookable execution packet:
  - assumptions
  - dependencies
  - unresolved blockers
  - action checklist
- Add operator override protocol and provenance log.

**Exit criteria**
- Human planner can execute packet without reconstructing context manually.

### Stage 6: Evaluation and break-testing harness
- Expand fixture suite across clean/messy/contradictory/edge cases.
- Add regression checks for:
  - schema integrity
  - gate correctness
  - contradiction handling
  - option-rank stability
- Add scenario-level failure-mode test sets.

**Exit criteria**
- Full evaluation suite produces stable metrics and catches regressions.

### Stage 7: Controlled productionization
- Introduce orchestration modularity only after core reliability.
- Add offline optimization loop (prompt packs, routing tuning, threshold tuning) behind eval gates.
- Introduce GTM-facing surfaces only when quality floor is met.

**Exit criteria**
- System meets quality thresholds for repeatability and operational trust.

---

## Part C: Immediate priorities from this sequence
1. Confirm Stage 0 contracts are complete and aligned across `specs/` + `src/` + tests.
2. Audit Stage 1/2 implementation gaps from existing notebooks and code modules.
3. Convert open architecture threads into testable acceptance checks.
4. Keep all optimization loops offline and eval-gated until Stage 6 stability.

---

## Date validation
Environment date used: `2026-04-14 00:25:45 IST +0530`.
