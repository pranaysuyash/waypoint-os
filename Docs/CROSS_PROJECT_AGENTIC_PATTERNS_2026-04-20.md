# Cross-Project Agentic Pattern Exchange — WaypointOS ↔ AdShot

**Date**: 2026-04-20
**Status**: Living document — updated as both projects evolve
**Projects**:
- **WaypointOS** (`travel_agency_agent`) — Travel agency operating system. Freeform trip request → structured planning decisions.
- **AdShot** (`opencode_buidathon`) — Ad creative generation pipeline. Phone photo → marketplace-ready creatives.
**Mirror doc**: `docs/discussions/2026-04-20-013-cross-project-agentic-patterns.md` in `opencode_buidathon`

---

## Why This Document Exists

Both projects are building agentic pipelines with the same core philosophy: **compiler pipeline, not agentic swarm**. Both use deterministic rules first, LLM only when semantic judgment is needed. Both structure specialist roles with typed contracts and quality gates. Both face the same scaling challenges (multi-tenant config, feedback loops, eval suites).

This document captures patterns that transfer between projects — what one project solved that the other should adopt, and shared architectural DNA that validates the approach.

---

## Shared Architectural DNA

| Pattern | WaypointOS | AdShot |
|---|---|---|
| Compiler pipeline, not agentic swarm | NB01→NB02→NB03 deterministic pipeline | Detect→Cutout→Hero→Copy→Quality linear pipeline |
| State machine for workflow | `decision_state` × `operating_mode` axes | State machine orchestrator with `proceed/retry/degrade/escalate` |
| Specialist roles, not generic agents | NB01/NB02/NB03 layer ownership per `V02_GOVERNING_PRINCIPLES.md` | Agency role model (Photographer, Retoucher, Copywriter, etc.) |
| Structured output contracts | `CanonicalPacket`, `DecisionResult`, `Slot`, `SuitabilityBundle` | `ImageAnalysis`, `CutoutResult`, `CopyResult`, `HeroResult` |
| Human-in-the-loop at ambiguity | `ASK_FOLLOWUP`, `STOP_NEEDS_REVIEW` decision states | `needs_clarification` for multi-object detection |
| V1 as fallback, not deprecated | Existing pipeline preserved during all refactors | V1 pipeline is runtime fallback for V2 stages |
| Deterministic-first, LLM-second | Three-tier suitability: deterministic rules → tour-context rules → LLM only when borderline | ADR: CV/rules for measurable checks, agents only for semantics |

---

## Patterns FROM AdShot → Adopt in WaypointOS

### 1. Quality Gates at Every Pipeline Stage

**What it is**: AdShot ADR-002 puts an explicit quality gate between every stage with a typed contract: `GateVerdict = 'proceed' | 'retry' | 'escalate' | 'degrade'` and score-based decision tree.

**Why WaypointOS needs it**: NB01→NB02→NB03 pipeline has implicit boundaries but no explicit gate contract between notebooks. The MVB (Minimum Viable Brief) check between NB01→NB02 exists as logic but isn't formalized as a gate.

**Where it applies**:
- Formalize `NB01CompletionGate` — structured quality check on NB01 output before NB02 runs
- Add `NB02JudgmentGate` — verify NB02 output meets minimum standards before NB03 builds session
- Each gate has `proceed/retry/escalate` semantics matching the existing `decision_state` axis

**Cross-ref**: `docs/decisions/2026-04-20-agent-orchestration-v2.md` ADR-002 in AdShot

**Status**: ⬜ Not yet adopted — design with plugin system architecture

### 2. 3-Layer Evaluation Scorecard

**What it is**: AdShot's external architecture review pushed splitting a single quality score into Technical / Creative / Business evaluation layers. Each layer has its own checks and scores.

**Why WaypointOS needs it**: `DecisionResult` (`src/intake/decision.py` L212-231) has `confidence_score` as a single float. When confidence is low, you can't tell if it's because data is incomplete (technical), suitability analysis is uncertain (judgment), or margin viability is unclear (commercial).

**Where it applies**:
- Replace single `confidence_score` with structured confidence:
  - **Data quality**: completeness, consistency, ambiguity level
  - **Judgment confidence**: feasibility, suitability, risk assessment certainty
  - **Commercial confidence**: margin viability, sourcing path clarity
- Feeds into D1 autonomy gates (`ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`) — auto-proceed only when ALL confidence layers are above threshold

**Cross-ref**: `docs/architecture/GAP-ANALYSIS-V2-VS-PDF.md` §5 in AdShot

**Status**: ⬜ Not yet adopted

### 3. Artifact Lineage

**What it is**: AdShot tracks `asset_id → parent_asset_id → generation_metadata` for every artifact. Every output traces back to its inputs.

**Why WaypointOS needs it**: Derived signals in `CanonicalPacket` don't trace back to which facts produced them. When an agent overrides a system verdict (D5, `ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md`), you can't show "here's the evidence chain that led to this verdict."

**Where it applies**:
- Add `derived_from: List[str]` to `Slot` model (`src/intake/packet_models.py`) — list of slot keys that produced this derived signal
- Enables "evidence display" in override UX — agent sees why the system reached its verdict
- Compounds with D5 override learning — override quality depends on understanding the original evidence

**Cross-ref**: `docs/architecture/GAP-ANALYSIS-V2-VS-PDF.md` §6 in AdShot

**Status**: ⬜ Not yet adopted

### 4. Deterministic-First as Explicit Governing Principle

**What it is**: AdShot's external review: "Use CV/rules where the answer is measurable. Use an agent only when semantics or taste matter."

**Why WaypointOS should codify it**: The three-tier suitability scoring (D4 addendum, `ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md`) already implements this principle for suitability. But it's not stated as a governing principle that applies to ALL pipeline stages.

**Where it applies**:
- Add to `V02_GOVERNING_PRINCIPLES.md`: "Deterministic rules first. LLM only when the answer requires world knowledge or semantic judgment."
- This validates the existing `HybridDecisionEngine` pattern (`src/decision/hybrid_engine.py`: rules → cache → LLM) as the standard for all decision points

**Cross-ref**: `docs/architecture/GAP-ANALYSIS-V2-VS-PDF.md` §4 in AdShot

**Status**: ⬜ Not yet codified — principle is practiced but not documented as governing rule

---

## Patterns FROM WaypointOS → Contributed to AdShot

### 1. Cache → Rule Graduation (HybridDecisionEngine)

**What it is**: `src/decision/hybrid_engine.py` runs cache → rule → LLM → cache-result with `success_rate` tracking. When cached LLM verdicts hit `use_count > 20 + success_rate > 0.95`, they become candidates for promotion to deterministic rules via `PromotionCandidate`.

**Where AdShot should use it**: Quality gates that use LLM agents (tone alignment, brand fit) make the same judgments repeatedly. Cache verdicts keyed by `(category × platform × tone)`, graduate consistent verdicts to deterministic rules.

**Cross-ref**: `src/decision/hybrid_engine.py`, `ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md`

**Status in AdShot**: ⬜ Not yet adopted

### 2. Override Learning / Feedback Bus (D5)

**What it is**: `ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md` — three override categories (decision/suitability/sourcing), each feeding different learning destinations. `OverrideEvent` contract with required rationale and structured tags. Two-phase learning: frequency-based → outcome-based.

**Where AdShot should use it**: User behavior IS the override signal. Regeneration = rejection. Download = approval. Track `user_verdict` events, aggregate by generation parameters, feed into ARES as production-signal complement to benchmark-signal.

**Cross-ref**: `ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md`

**Status in AdShot**: ⬜ Not yet adopted

### 3. Manifest-Driven Eval Categories (D6)

**What it is**: D6 eval suite uses `planned → shadow → gating` progression per audit category. New capabilities measured in shadow mode before surfaced to users.

**Where AdShot should use it**: New quality gate checks start in `shadow` (scored but don't affect `GateVerdict`). Graduate to `active` when false positive rate < threshold on production data.

**Cross-ref**: `ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` Part 5

**Status in AdShot**: ⬜ Not yet adopted

### 4. Per-Tenant Policy Config (D1/D3)

**What it is**: `AgencyAutonomyPolicy` (D1), `SourcingPolicy` (D3), `AgencySuitabilityPolicy` (D4) — per-agency config objects that drive pipeline behavior without code branches.

**Where AdShot should use it (future)**: Extract model routing matrix into `BrandCreativePolicy` config when going multi-tenant. Per-brand quality thresholds, tone defaults, forbidden content rules.

**Cross-ref**: `ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`, `ARCHITECTURE_DECISION_D3_SOURCING_HIERARCHY_2026-04-18.md`

**Status in AdShot**: ⬜ Not yet needed (single-tenant)

---

## Lessons Learned (Updated as Projects Progress)

*This section captures insights from building both pipelines. Add entries as patterns prove or fail in practice.*

| Date | Project | Lesson | Impact on Other Project |
|---|---|---|---|
| 2026-04-20 | Both | Compiler pipeline > agentic swarm. Both projects independently converged on "normalize → judge → act" over "let agents figure it out." | Validates the approach for agentic platforms generally |
| 2026-04-20 | WaypointOS | Cache → rule graduation compounds. LLM decisions that repeat become free deterministic rules over time. | AdShot should adopt for quality gate verdicts |
| 2026-04-20 | AdShot | Separating cleanup from cutout (different failure modes) prevents cascading quality issues. | WaypointOS should consider: separating fact extraction from signal derivation failures in NB01 |
| 2026-04-20 | AdShot | Single quality score is un-debuggable. Split into layers. | WaypointOS `confidence_score` should become multi-dimensional |

---

## Meta-Pattern: What Makes an Agentic Pipeline Work

Distilled from building both systems:

1. **Compiler, not swarm.** Normalize → Judge → Act. Every stage has typed input/output contracts.
2. **Deterministic first.** Rules and arithmetic before LLM. LLM only for world knowledge or taste.
3. **Gates, not hopes.** Explicit quality gate between every stage. `proceed/retry/escalate/degrade` — not "pass it along and see."
4. **Layered confidence.** Never one number. Separate technical/judgment/commercial (or technical/creative/business) so you can debug.
5. **Policy as config, not code branches.** Per-tenant behavior driven by data objects, not if/else chains.
6. **Cache → graduate.** Every LLM call that repeats is a rule candidate. Compound improvement over time.
7. **Override = learning signal.** Human corrections are the most valuable data. Log them, aggregate them, suggest policy changes.
8. **Shadow before enforce.** New capabilities measured in shadow mode before they affect production decisions.
9. **Lineage everything.** Every output traces to its inputs. Every decision traces to its evidence.
10. **V1 is the fallback, not the enemy.** Wrap, don't rewrite. Degrade gracefully to proven paths.

---

*This is a living document. Update it when patterns transfer successfully, when a pattern from one project fails in the other, or when new shared insights emerge from building both agentic platforms.*
