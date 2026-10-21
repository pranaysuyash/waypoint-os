# E15 — Tiered Option Generator: Demand Research (2026-09-18)

**Status:** Researched — original framing rejected; one sharper question survives.
**Origin:** `Docs/FIRST_PRINCIPLES_GAP_ASSESSMENT_2026-04-14.md` P1-2
("multi-option generation: conservative/balanced/premium").
**Depends on:** T-02/T-03 (branch-options serving fix) — see below.

## Question

Is a standalone conservative/balanced/premium option generator worth building?

## Evidence gathered (2026-09-18)

**Demand side — none found:**
- No product/GTM/strategy doc asks for trip-tier option generation. All
  "conservative/balanced/premium" hits are unrelated (pricing-packaging
  modules, growth-scenario modes).
- The only genuine 3-tier signal is `DEEP_PERSONA_AUDIT…` CFT-01
  "3-Tier Counterfactual Generator" — IRROPS disruption rebooking, not trip
  tiering — and it exists only as static mock data
  (`frontend/src/app/(agency)/workbench/IROPSAutoHealerPanel.tsx:73-95`).

**Supply side — the niche is occupied by three mechanisms:**
1. **Route-structure candidates** (TS-06): deterministic, scored, ≥2 options
   end-to-end via `src/decision/route_structures.py` → `decision.branch_options`.
2. **`budget_tier_framing`** (`src/intake/strategy.py:550`): narrative
   within-stated vs stretch framing on budget contradictions.
3. **`BUDGET_BUCKET_RANGES`** (`src/intake/decision.py:605`): per-destination
   component bands driving budget decomposition.

**Sharpest surviving question:** should `branch_options` gain a *second
producer* — budget-tier variants derived by upscaling/downscaling
`BUDGET_BUCKET_RANGES` — reusing the existing scored-candidate contract?
Supporting evidence: `src/intake/plan_candidate.py`'s BRANCH_OPTIONS vocabulary
comment already anticipates "route **or budget** options".

## Verdict

**Not worth building as originally framed** (zero demand, niche occupied).
**Explore-worthy only as pipeline extension** — and only after T-02/T-03 land
and operators actually see route options; any budget-tier work should reuse
the branch-options contract, not create a parallel option system (canonical
routes rule). Revisit trigger: operator feedback asking for tiered choices.

---

## SUPERSEDED-IN-PART 2026-09-30 (T4 Real Quotes)

The council's T4 tranche replaced the fabricated /quotes surface with the real
read model (`spine_api/routers/quotes.py`: persisted modeled cost + MarginPolicy
margin, branches unpriced, "never fabricates prices/tiers" pinned by test). The
fabrication risk this doc worried about is closed. The surviving open question
is only the E15 §Verdict residual: a **budget-tier second producer** on the
branch_options contract, gated on operator demand — tracked as owner DECIDE.
