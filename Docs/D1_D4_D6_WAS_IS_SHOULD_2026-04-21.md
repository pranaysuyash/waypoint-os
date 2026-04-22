# D1–D4 + D6 — What Was, What Is, What Should Happen Next

**Date**: 2026-04-21
**Purpose**: Provide a detailed past / present / next-state view across D1–D4, with D6 included where it is the gating dependency for D2 and D4 progression.

Environment date checked before this documentation update:
- `2026-04-21 23:41:31 IST`

---

## Why This Doc Exists

There were two different kinds of status language floating around:

- architecture-language: "D1, D2, D3, D4 are decided"
- implementation-language: "some of this exists, some is still paper-only"

That split is real. This document makes it explicit using three lenses:

- **What was**: what the discussions and ADRs locked in
- **What is**: what is actually in the repo today
- **What should**: what should happen next, in dependency order

---

## One-Page Reality Map

| Area | What Was | What Is | What Should |
|---|---|---|---|
| **D1** Autonomy | Agency-level autonomy gradient, per-`decision_state` approval gates | Older threshold-based autonomy gate exists, but not ADR-complete | Upgrade existing gate to ADR shape, don't rebuild from zero |
| **D2** Free Engine Persona | Shared pipeline, agency audit first, consumer surface later | `audit` mode exists; consumer presentation layer does not | Keep agency audit as the active surface; gate consumer surface on D6 |
| **D3** Sourcing | Per-agency `SourcingPolicy` contract | Runtime still uses a sourcing stub | Defer real implementation until Gap #01 lands |
| **D4** Suitability | Three-tier engine: deterministic → context → LLM | Tier 1 + Tier 2 are live; Tier 3 is absent | Build Tier 3 only after trigger/eval/plugin decisions are tightened |
| **D6** Audit Eval | Manifest-driven quality gate for audit surfaces | Still missing as runtime/eval framework | Scaffold before public D2 expansion and before calling D4 “green” |

---

## D1 — Autonomy Gradient

### What Was

The D1 ADR in `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md` defined autonomy as:

- agency-owned policy, not per-agent preference
- explicit per-`decision_state` gates
- `auto`, `review`, `block` semantics
- hard safety invariant: `STOP_NEEDS_REVIEW` always blocks
- future adaptive autonomy layered on customer + trip classification

The important historical point is that D1 was never just "confidence thresholds." The thesis discussion framed it as a trust-boundary model between NB02 judgment and NB03 action.

### What Is

The repo already has a meaningful D1 precursor:

- [src/intake/config/agency_settings.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py) defines `AgencyAutonomyPolicy`
- [src/intake/gates.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/gates.py) evaluates confidence against that policy
- [src/intake/orchestration.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py) enforces degrade/escalate outcomes

So D1 is not missing. But it is not complete either.

Current shape:

- threshold-driven (`min_proceed_confidence`, `min_draft_confidence`)
- confidence-led degrade/escalate behavior
- no explicit `decision_state -> gate` map
- no explicit mode-specific override table
- no D1-native concept of traveler-safe outputs being review-gated by policy

### What Should

D1 should be treated as an **upgrade path**, not a greenfield feature.

Recommended implementation order:

1. Preserve the current threshold-based policy as an internal fallback, because it already works.
2. Add ADR-native fields to `AgencyAutonomyPolicy`:
   - `approval_gates`
   - `mode_overrides`
   - `auto_proceed_with_warnings`
   - `learn_from_overrides`
3. Update [src/intake/gates.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/gates.py) so it evaluates both:
   - confidence floor
   - decision-state approval requirement
4. Make `STOP_NEEDS_REVIEW -> block` a hard invariant in code, not just a doc statement.
5. Defer adaptive customer+trip classification until pilot override data exists.

**What should not happen**:
- Do not jump to adaptive autonomy first.
- Do not throw away the existing threshold gate just because it is not the final ADR shape.

---

## D2 — Free Engine Persona

### What Was

The D2 ADR in `Docs/ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md` locked in a strategic sequencing call:

- agency self-audit and consumer free engine are both real targets
- both use the same core pipeline
- agency audit ships first
- consumer surface ships only after D6 proves accuracy
- consumer framing is empowerment, not agency replacement

This matters because D2 was never supposed to become a public funnel immediately. The quality gate was part of the decision, not an afterthought.

### What Is

Agency-audit foundation already exists:

- `audit` is an operating mode in [src/intake/packet_models.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py)
- audit-mode routing exists in [src/intake/decision.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/decision.py)
- audit-mode tests exist in [tests/test_nb02_v02.py](file:///Users/pranay/Projects/travel_agency_agent/tests/test_nb02_v02.py) and [tests/test_nb03_v02.py](file:///Users/pranay/Projects/travel_agency_agent/tests/test_nb03_v02.py)
- frontend mode selectors expose audit mode in [frontend/src/components/workspace/panels/IntakePanel.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/IntakePanel.tsx) and [frontend/src/app/workbench/IntakeTab.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/IntakeTab.tsx)

What does not exist:

- `presentation_profile`
- consumer-specific NB03 builder
- public itinerary-checker UI
- D6-driven gating-only finding filter

### What Should

D2 should remain sequenced exactly the way the ADR intended:

1. Keep agency audit as the only active D2 surface for now.
2. Build D6 before any consumer release logic.
3. Add `presentation_profile` only when there is a real second builder to route to.
4. Treat consumer surface as a presentation/output problem sitting on top of a proven audit core.

**What should not happen**:
- Do not ship a public consumer checker just because `audit` mode exists.
- Do not equate "audit mode works internally" with "consumer surface is ready."

---

## D3 — Sourcing Hierarchy

### What Was

The D3 ADR in `Docs/ARCHITECTURE_DECISION_D3_SOURCING_HIERARCHY_2026-04-18.md` locked the business logic target:

- per-agency `SourcingPolicy`
- agency-owned hierarchy order
- margin floors
- category-specific overrides
- supplier preferences and blocks
- widen-search behavior connected to D1 approval semantics

D3 was explicitly framed as a major differentiator, but also explicitly tied to the missing supplier/cost layer.

### What Is

Runtime sourcing is still a stub in [src/intake/extractors.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/extractors.py).

That means:

- no real supplier inventory model
- no package margin reasoning
- no actual tier resolution logic
- no `SourcingPolicy` runtime object in the core path

### What Should

D3 should stay blocked until Gap #01 lands. That is not procrastination; it is architectural honesty.

Recommended next-state handling:

1. Keep D3 as a contract-only area in short-term status reporting.
2. When Gap #01 begins, use D3 as the control-plane contract for the implementation.
3. Resolve D3 open questions only when actual supplier data models exist.

**What should not happen**:
- Do not simulate D3 with more elaborate hardcoded heuristics and call it "implemented."
- Do not build `SourcingPolicy` wiring without the data layer it governs.

---

## D4 — Suitability Depth

### What Was

The original D4/D6 architecture defined suitability as an analyzer and audit as measurement over analyzer outputs.

The key evolution happened in `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md`:

- D4 stopped being just per-activity fit
- D4 became a three-tier engine
- Tier 2 introduced day/trip coherence
- Tier 3 was intentionally reserved for ambiguous, world-knowledge-heavy cases

This is the biggest conceptual shift in the D1–D4 series.

### What Is

The repo now has real D4 substance:

- Tier 1 in [src/suitability/scoring.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/scoring.py)
- Tier 2 in [src/suitability/context_rules.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/context_rules.py)
- expanded context model in [src/suitability/models.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/models.py)
- decision-pipeline wiring in [src/suitability/integration.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/integration.py)

This means D4 is already more than a spec. It is a running deterministic suitability foundation.

What remains absent:

- Tier 3 LLM contextual scorer
- scorer registry/plugin system
- suitability-specific cache orchestration
- Tier 3 edge-case eval fixtures

### What Should

D4 should progress in a disciplined order:

1. Do not call D4 "fully green" yet.
2. Formalize the plugin/registry direction enough to avoid building a one-off Tier 3 path that will be thrown away.
3. Define Tier 3 triggers using observed ambiguity classes, not just imagined ones.
4. Implement Tier 3 behind deterministic tiers, never instead of them.
5. Measure Tier 3 with fixtures before broadening its use.

**What should not happen**:
- Do not reduce D4 status to "not done"; Tier 1 + 2 are real.
- Do not reduce D4 completion to "add one LLM scorer file."

---

## D6 — Audit Eval Suite

### What Was

D6 was defined from the start as the quality gate that makes audit-mode output trustworthy, especially for D2.

The design target in `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` is clear:

- manifest-driven categories
- `planned -> shadow -> gating`
- eval fixtures as both roadmap and accuracy gate
- no public consumer audit without passing gates

### What Is

D6 is still missing in implementation terms:

- no `src/evals/` framework
- no manifest runner
- no category promotion machinery
- no gating status used by presentation logic

### What Should

D6 should move ahead of major D2 expansion and ahead of claiming D4 completion.

Recommended order:

1. Create the eval scaffold.
2. Seed first audit categories and fixtures.
3. Make D6 the gate for consumer-surface findings.
4. Extend D6 to Tier 3 suitability edge cases once Tier 3 exists.

**What should not happen**:
- Do not leave D6 as documentation while building outward-facing audit experiences.

---

## Detailed Execution Order

This is the recommended implementation sequence if the goal is maximum truthfulness with minimum architectural thrash.

### Phase 1 — Correct the Baseline Reality Map

Goal: stop stale docs from distorting planning.

- Update status docs so D1, D2, quality gates, scorecard, and lineage are described accurately.
- Keep the wording precise: "partial / upgrade path" where appropriate.

### Phase 2 — Finish D1 as an Upgrade, Not a Rewrite

Goal: align the current autonomy gate with the D1 ADR.

- Extend `AgencyAutonomyPolicy`
- preserve threshold gating
- add decision-state approval gating
- enforce `STOP_NEEDS_REVIEW -> block`

Why second:
- D1 already has code to build on
- low blocker count
- improves governance before more automation

### Phase 3 — Build D6 Scaffold

Goal: create the measurement layer before broader surface expansion.

- scaffold `src/evals/`
- add manifest shape
- add first budget/audit fixtures
- create category status model

Why third:
- D2 depends on it
- D4 Tier 3 should be measured through it

### Phase 4 — Resolve Plugin / Registry Direction for D4 Tier 3

Goal: avoid hardcoding a dead-end LLM scorer path.

- formalize scorer registration and activation model
- decide relationship to hybrid engine and cache system
- decide whether suitability scorer selection is global or policy-driven

Why before coding Tier 3:
- prevents throwaway architecture
- keeps D4 aligned with the broader plugin discussion already in docs

### Phase 5 — Implement D4 Tier 3 Conservatively

Goal: add semantic/world-knowledge depth only where deterministic tiers are insufficient.

- define trigger conditions
- build cache key with day/trip context
- implement scorer behind deterministic layers
- add targeted eval fixtures

Why here:
- by this point D1 governance and D6 measurement both exist

### Phase 6 — Expand D2 to Consumer Surface

Goal: only after audit quality is measurable.

- add `presentation_profile`
- build consumer NB03 builder
- filter findings via D6 gating status
- then consider public itinerary-checker surface

### Phase 7 — Revisit D3 with Gap #01

Goal: implement sourcing only when supplier/cost primitives are real.

- start with vendor/cost data models
- then wire `SourcingPolicy`
- then connect D3 audit/commercial rules

---

## Bottom-Line Guidance

If someone asks "what was, what is, what should be next," the honest answer is:

- **What was**: D1–D4 were meaningfully discussed and mostly architecturally decided; D4 evolved the most.
- **What is**: D1 and D2 have partial real foundations, D3 is still blocked/contract-only, D4 deterministic tiers are live, D6 is still missing.
- **What should**: finish D1 as an upgrade, build D6 as the audit truth gate, then do D4 Tier 3 carefully, and only after that expand D2 to consumer-facing territory.

That sequence preserves architectural intent and avoids pretending public trust surfaces are ready before the measurement layer exists.
