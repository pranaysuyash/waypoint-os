# D1–D4 Status Reconciliation + Gemini Review

**Date**: 2026-04-21
**Purpose**: Reconcile what was discussed, what is implemented, what remains open, and how to interpret the external Gemini assessment of D4.

Environment date checked before this documentation update:
- `2026-04-21 23:35:39 IST`

---

## Executive Summary

The cleanest status framing as of 2026-04-21 is:

| Decision | Discussion Status | Code Status | Honest Color |
|---|---|---|---|
| **D1 — Autonomy Gradient** | Core architecture decided | **Partially implemented, but not ADR-complete** | Amber |
| **D2 — Free Engine Persona** | Core architecture decided | **Partial foundation exists** (`audit` mode), consumer surface not built | Amber |
| **D3 — Sourcing Hierarchy** | Contract decided | **Not implemented**; current code is still a stub | Red / Blocked |
| **D4 — Suitability Depth** | Most deeply discussed; addendum closed D4.1–D4.3 | **Tier 1 + Tier 2 implemented**, Tier 3 not built | Amber |

So the short answer to "what's done?" is:

- D1 is **not paper-only**, but the code only has an older autonomy-threshold gate, not the D1 ADR's per-`decision_state` approval model.
- D2 has **runtime foundations** in place for agency audit mode, but not the consumer-facing free engine surface.
- D3 is **still contract-only** and correctly blocked on Gap #01.
- D4 has a **real implemented foundation** (Tier 1 + 2), but the full three-tier ADR target is not complete.

---

## Done vs Open Ledger

### D1 — Autonomy Gradient

**Discussed / decided**
- The architectural decision is locked in `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`.
- The intended model is an agency-level `AgencyAutonomyPolicy` with per-`decision_state` gates (`auto` / `review` / `block`) and mode overrides.

**Actually implemented**
- There is already an `AgencyAutonomyPolicy` dataclass in [src/intake/config/agency_settings.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py) with threshold-style fields such as `min_proceed_confidence` and `min_draft_confidence`.
- That policy is already consumed by [src/intake/gates.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/gates.py) and enforced in [src/intake/orchestration.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py).

**What is still open**
- The implemented policy is **not** the D1 ADR model. It is a simpler confidence-threshold gate, not per-`decision_state` approval control.
- The ADR's `approval_gates`, `mode_overrides`, and "`STOP_NEEDS_REVIEW` always block" invariant are not represented as first-class config in code.
- Override dignity / learning is still only a design connection to D5, not a completed loop.

**What was not yet fully discussed/closed**
- Customer + trip classification for adaptive autonomy is still a deferred deep dive in the D1 ADR.

**Verdict**
- D1 is **partial, not absent**.
- Existing status notes that say "D1 is not in `src/`" are directionally useful but too coarse; the truer statement is: **D1 has an older stub implementation, but not the final ADR shape**.

### D2 — Free Engine Persona

**Discussed / decided**
- The architectural decision is locked in `Docs/ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md`.
- The big call is settled: agency self-audit and the consumer free engine use the same NB01 → NB02 → NB03 pipeline, with different presentation.

**Actually implemented**
- `audit` is already a first-class operating mode in [src/intake/packet_models.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py).
- Audit-mode routing logic already exists in [src/intake/decision.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/decision.py).
- Audit-mode behavior is covered by tests in [tests/test_nb02_v02.py](file:///Users/pranay/Projects/travel_agency_agent/tests/test_nb02_v02.py) and [tests/test_nb03_v02.py](file:///Users/pranay/Projects/travel_agency_agent/tests/test_nb03_v02.py).
- The frontend already exposes `audit` mode in [frontend/src/components/workspace/panels/IntakePanel.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/IntakePanel.tsx) and [frontend/src/app/workbench/IntakeTab.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/IntakeTab.tsx).

**What is still open**
- The D2 ADR's `presentation_profile: "agency" | "consumer"` is not wired in code.
- There is no consumer-specific NB03 report builder.
- There is no public itinerary-checker funnel implemented.
- The D6 gating-only rule filter that protects the consumer surface does not exist yet.

**What was not yet fully discussed/closed**
- The architectural direction is closed, but the concrete public-surface implementation path remains dependent on D6 eval infrastructure and related product execution work.

**Verdict**
- D2 is **partially operational for agency audit mode**, but **not shipped as the full dual-surface architecture** described in the ADR.

### D3 — Sourcing Hierarchy

**Discussed / decided**
- The architectural decision is locked in `Docs/ARCHITECTURE_DECISION_D3_SOURCING_HIERARCHY_2026-04-18.md`.
- The `SourcingPolicy` contract is settled at the design level: tier priority, margin floors, category overrides, supplier preferences, widen-search behavior.

**Actually implemented**
- Current runtime behavior is still a stub in [src/intake/extractors.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/extractors.py), where `sourcing_path` defaults to `open_market` or `network` with explicit "Stub" notes.

**What is still open**
- No vendor/supplier model.
- No margin decomposition.
- No policy-driven sourcing resolution.
- No D3 rule/audit linkage in running code.

**What was not yet fully discussed/closed**
- The ADR itself leaves future refinements open: per-category margin floors and scoped supplier preferences.

**Verdict**
- D3 is **decided but not implemented**.
- This is the clearest true blocker among D1–D4 because the ADR explicitly depends on Gap #01.

### D4 — Suitability Depth

**Discussed / decided**
- The parent architecture is in `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md`.
- The decisive refinement is in `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md`, which upgrades D4 from isolated activity scoring to a three-tier model:
  - Tier 1 deterministic per-activity rules
  - Tier 2 deterministic tour-context rules
  - Tier 3 LLM contextual scoring

**Actually implemented**
- [src/suitability/scoring.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/scoring.py) implements Tier 1 deterministic scoring.
- [src/suitability/context_rules.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/context_rules.py) implements Tier 2 day/trip coherence rules.
- [src/suitability/models.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/models.py) includes the expanded `SuitabilityContext` with `day_activities`, `trip_activities`, `day_index`, `season_month`, and `destination_climate`.
- [src/suitability/integration.py](file:///Users/pranay/Projects/travel_agency_agent/src/suitability/integration.py) wires suitability output into the decision pipeline as heuristic risk flags.
- `Docs/SUITABILITY_IMPLEMENTATION_SUMMARY_2026-04-18.md` correctly records Tier 1 + Tier 2 as complete and Tier 3 as future work.

**What is still open**
- No Tier 3 scorer exists in `src/`.
- No suitability-side LLM cache orchestration exists.
- No plugin/registry implementation exists for swappable scorers.
- No trip-sequence Tier C eval fixtures exist for the Tier 3 edge cases described in the addendum.

**What was not yet fully discussed/closed**
- The D4 addendum explicitly deferred Tier 3 trigger calibration and prompt specifics until Tier 1 + 2 are running on real inputs.
- So Tier 3 is not just "unimplemented"; parts of its implementation detail were intentionally left open to avoid premature design lock.

**Verdict**
- D4 is **real and useful today**, because Tiers 1 + 2 are live.
- D4 is **not fully green against the full ADR target**, because Tier 3 remains paper-only.

---

## Gemini Assessment Review

This section applies the repo's external-review evaluation workflow to the Gemini claim.

### Source Assessment

- Source type: external model review, not an authoritative project artifact.
- Freshness risk: medium. The review is broadly aligned with current code, but it missed one nuance in D1 (older autonomy stub already exists in code).
- Ownership: cannot be iterated directly; needs repo-side validation against current files.

### Recommendation Ledger

**Recommendation**: "D4 is Tier 1 + 2 ready, but not green because Tier 3 is still paper-only."
- **Decision**: ACCEPT
- **Why**: This matches the D4 addendum and the implementation summary. The codebase has deterministic tiers, not the LLM tier.

**Recommendation**: "There is no `src/suitability/scorers/llm_scorer.py` or equivalent implementation."
- **Decision**: ACCEPT
- **Why**: Repo search confirms no Tier 3 scorer implementation exists.

**Recommendation**: "The pluggable scorer / registry pattern remains paper-only; current structure is still flat files."
- **Decision**: ACCEPT
- **Why**: The ADRs discuss swappable protocols, but runtime code is still a flat `src/suitability/` package without scorer registry infrastructure.

**Recommendation**: "To reach green, implement the Tier 3 scorer and wire it into suitability integration."
- **Decision**: ACCEPT+MODIFY
- **Why**: This is directionally correct, but incomplete as a next-step prescription. A genuinely ADR-aligned Tier 3 implementation also needs:
  - trigger-threshold calibration,
  - cache-key and hybrid-engine integration,
  - a decision on plugin/registry shape,
  - and eval fixtures for the new ambiguity cases.
- **Modification**: "Green" should mean **ADR-complete D4**, not merely "a new file exists." A thin `llm_scorer.py` without calibrated triggers and eval coverage would still be only partially complete.

### Net Verdict on Gemini

Gemini is substantially right on D4.

The one important repo-level refinement is:
- D4 should be described as **Amber: Tier 1 + 2 production foundation complete; Tier 3 intentionally deferred and not yet implemented**.
- That is stronger than "paper-only fantasy," but weaker than full-green completion.

---

## Answer To "What's Done, Open, Not Yet Discussed?"

### Done

- D1 core autonomy direction was discussed and a partial threshold-based autonomy gate already exists in code.
- D2 core architecture was discussed and audit mode exists in the runtime and frontend.
- D3 contract design was discussed and closed at ADR level.
- D4 Tier 1 + Tier 2 were discussed, implemented, and documented.

### Open

- D1 ADR-conformant autonomy policy shape is still not implemented.
- D2 consumer-facing free engine surface is not built.
- D3 runtime sourcing engine is blocked on Gap #01.
- D4 Tier 3 LLM contextual scoring is not built.

### Not Yet Fully Discussed / Closed

- D1 customer + trip classification for adaptive autonomy.
- D3 finer-grained policy questions like per-category margin floors and scoped supplier preferences.
- D4 Tier 3 trigger calibration, real ambiguity patterns, and final plugin/registry design.

---

## Recommended Status Language Going Forward

Use this wording to avoid future confusion:

- **D1**: "Partially implemented, ADR not complete."
- **D2**: "Foundation present for agency audit mode; consumer surface pending D6."
- **D3**: "Contract decided, implementation blocked on Gap #01."
- **D4**: "Tier 1 + 2 complete; Tier 3 deferred/unimplemented."

That phrasing matches the actual repo state more accurately than either "all done" or "all paper-only."
