# TS-06 — Candidate Route-Structure Generation & Incremental Refinement

**Status:** exploration — gap confirmed, design direction recorded (2026-09-09)
**Source:** training-session register TS-06; tutor's route-design lesson (the owner's weakest-scoring area): route structures have **hard dependencies** (must-visit cities, duration, party) and **soft dependencies** (exact flights, hotels) — generate candidate structures early (Tokyo 4N/Kyoto 3N vs 3N/4N), then refine dramatically when flight data arrives (arrival Tokyo 10:00 / return Osaka 23:00 → open-jaw Tokyo→Kyoto→Osaka instead of backtracking).

---

## 1. Verification result (Observed, 2026-09-09)

The gap is **confirmed**. Nothing in the repo generates candidate route structures:

| Surface | What it does | Route-structure generation? |
|---|---|---|
| `build_plan_candidate` (`src/intake/plan_candidate.py`, Phase 4.6) | Single internal planning snapshot bridging strategy → output bundles | ❌ one plan, not candidates |
| `SessionStrategy` (`src/intake/strategy.py:88`, priority_sequence max-5) | Ordered *action* steps (follow-ups, checks) | ❌ action sequencing, not geography |
| `BRANCH_OPTIONS` decision state (`src/intake/constants.py`) | Vocabulary for offering the customer options | ❌ names the concept; no producer computes route alternatives |
| Route-feasibility matrix (`ROUTE_FEASIBILITY_AND_GEOSPATIAL_AVIATION_PIPELINE_2026-09-02.md` + `constraint_engine.py`) | **Validates** a proposed route (MCT, zigzag, transit visas, overlap — now incl. TS-01 ground-access) | ❌ validates, never generates |
| `AutonomousProposalCompiler` | Compiles one graph (flight→transfer→hotel) | ❌ single structure, sandbox offer |

## 2. Why this matters (Inferred)

The tutor's example is precisely the money case: a 7-day Tokyo+Kyoto+Disney family trip where the open-jaw flight pair (into NRT, out of KIX) changes the optimal structure. A single-structure planner either (a) picks a structure before flights are known and doesn't revise, or (b) waits for flights before structuring — losing the tutor's "refine incrementally, don't wait for every input" principle. The system currently does (a)-ish via the compiler's fixed template.

## 3. Design direction (Proposed)

A deterministic **candidate-structure enumerator** (no LLM in generation — it is combinatorics over hard constraints):

```
inputs (hard deps):  cities[], nights_total, party profile, pace
generator:           enumerate night-splits across cities honoring
                     (min-nights-per-city, travel-time matrix, must-visit)
                     -> 2-4 candidate structures, each a skeleton graph
refinement (soft):   when flight data arrives (arrival airport/time, departure
                     airport/time), score candidates:
                     - open-jaw alignment (arrive city A, depart city B
                       => A-first ordering, no backtrack)
                     - backtracking cost via travel-time matrix
                     - TS-01 constraint engine pre-pass on each candidate
selection:           rank deterministically; LLM may only *narrate* the
                     trade-off, never alter the skeletons (provider-facts rule)
```

- **Canonical home:** a new module beside the constraint engine (`src/decision/route_structures.py`), consumed by the proposal compiler and surfaced through the existing `BRANCH_OPTIONS` decision state — the vocabulary finally gets a producer.
- **Output shape:** candidate skeletons as partial `JourneyDependencyGraph`s (nodes without times), so the existing constraint engine, journey-graph persistence, and disruption-ripple tooling all apply unchanged.
- **Evaluation:** extend the scenario corpus with route-structure cases (hard-split constraints, open-jaw refinement) — the eval lane's failure-becomes-fixture rule.

## 4. Sizing & sequencing (Proposed)

| Step | Size |
|---|---|
| enumerator (night-splits + travel-time matrix + min-nights) | M |
| open-jaw/backtrack scoring + refinement hook on flight arrival | M |
| wire to BRANCH_OPTIONS + operator panel rendering of candidates | M |
| corpus + eval fixtures | S |

**Recommendation:** schedule after TS-01 lands (this doc's scoring reuses the constraint engine) and alongside/near the marketplace proposal work, since multi-option proposals are a marketplace-facing capability. Not urgent for the pilot-of-one Ravi path (single-destination corridor), which is why it stays exploration rather than Wave A.
