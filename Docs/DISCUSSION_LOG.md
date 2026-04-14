# Discussion and Feedback Log

This document serves as the "Decision Audit Trail" for the project. It captures queries, feedback, and pivots derived from consultations with other AI agents (e.g., ChatGPT) and human experts.

## Log Entry: 2026-04-08 - The "Compiler" Pivot

### Context
Initial plan was "Agent-Centric" (Agent understands $\rightarrow$ Agent la-hypothesizes $\rightarrow$ Agent prompts).

### Feedback Received
- **Core Critique**: "Agentic" workflows are brittle. The system should be a "Compiler Pipeline."
- **Key Shift**: Move from `Prompting` $\rightarrow$ `State Integrity`.
- **New Pipeline**: `Normalize` $\rightarrow$ `Validate` $\rightarrow$ `Infer Cautiously` $\rightarrow$ `Decide Action` $\rightarrow$ `Generate Session Plan` $\rightarrow$ `Generate Prompt Bundle`.

### Key Decisions Made:
1. **Separation of Concerns**:
    - **Facts**: Explicitly stated.
    - **Derived Signals**: Direct implications (e.g., toddler $\rightarrow$ nap sensitivity).
    - **Hypotheses**: Soft patterns (e.g., "likely comfort-first").
    - **Unknowns**: Gaps and contradictions.
2. **Decision Policy**: The system must have a "Gating Rule" to decide if it can proceed to planning or must ask follow-ups first.
3. **Prompting Strategy**: Shift from monolithic prompts to "Modular Prompt Blocks" (System Frame + Context + Objective + Response Policy).
4. **Input Model**: Support both freeform and structured intake, normalizing both into a single canonical packet.
5. **Tooling**: Use `uv` with Python 3.13 for strict environment management.

### Action Items for Implementation:
- [ ] Implement `Source Adapters` for heterogeneous input.
- [ ] Define the `Canonical Packet Schema`.
- [ ] Build the `MVB (Minimum Viable Brief)` blocker check.
- [ ] Create a `Prompt Registry` instead of freeform prompt generation.

## Log Entry: 2026-04-13 - Part 1 Continuation Ingested (Agency Ops + Voice Orchestration Nuances)

### Context
The first ChatGPT conversation was continued in this Codex thread and added major constraints beyond the original archive segment.

### What Was Added
- Confirmed agency-first framing with operational sourcing realities:
  - internal packages
  - preferred suppliers
  - network inventory
  - open market as fallback
- Explicit move from "trip generation" to "workflow + optimization" framing.
- Strong requirement for person-level suitability and wasted-spend detection.
- Budget decomposition expansion including shopping allocation.
- Recommendation to support itinerary/package auditing from multiple input types (PDF/text/screenshots/URL).
- Two-screen voice intake direction with adaptive orchestration and live structured brief.
- Validation-side "free engine" accepted only as intelligence/audit layer, not a full B2C offering.

### Preservation Action
- Created `Archive/PART_1_CONTINUATION_2026-04-13.md` to preserve continuation context without overwriting historical raw files.

### Immediate Follow-ups
- Keep ingesting remaining user-provided conversation parts as separate historical artifacts.
- Reconcile full archived raw conversation chain after all parts are received.
- Promote confirmed constraints into implementation contracts only after all context drops are complete.

## Log Entry: 2026-04-13 - Part 2 Ingested (Router/Composer/Verifier + Offline Autoresearch)

### Context
Second conversation focuses on architecture for dynamic question routing and prompt optimization, and where to apply autoresearch safely.

### Key Decisions Reinforced
- Separate **online production path** from **offline optimization path**.
- Use a compiler-like runtime pipeline:
  - context normalizer
  - intake router
  - prompt composer (registry-based)
  - specialist/generalist execution
  - verifier
  - memory/log update
- Keep taxonomy stable and coarse in v1; avoid live taxonomy drift.
- Apply autoresearch offline to:
  - router prompts
  - few-shot packs
  - context packing/truncation
  - confidence/escalation thresholds
- Require eval harness and acceptance gating before deploying prompt/routing changes.

### Preservation Action
- Added archive artifact: `Archive/PART_2_RAW_2026-04-13.md`

### Follow-up for next context drops
- Continue preserving each drop as independent historical artifact.
- After all parts are shared, synthesize into:
  - consolidated decision timeline
  - implementation contract checklist
  - prioritized execution plan mapped to code modules/tests

## Log Entry: 2026-04-13 - Part 2 Re-Shared and Rolling Synthesis Started

### Context
User re-shared the second conversation content in-thread and confirmed additional context drops are coming.

### Preservation Action
- Retained `Archive/PART_2_RAW_2026-04-13.md` as part-specific archive context.
- Added explicit re-share addendum in the archive artifact.

### Synthesis Action
- Created `Docs/ROLLING_CONTEXT_SYNTHESIS.md` as the active rolling document for:
  - stable architecture contracts
  - implementation priorities
  - risk boundaries
  - open intake status

### Operating Rule Confirmed
- Online runtime path remains deterministic.
- Autoresearch-style optimization remains offline and eval-gated.

## Log Entry: 2026-04-14 - First Principles Foundation and Strict Build Order

### Context
User requested that planning be grounded in first-principles reasoning before moving to backlog conversion.

### Decisions Captured
- Reframed product as a **decision system for agencies**, not a generic trip planner.
- Locked core truths: constraint satisfaction, state integrity, repeatable operations, provenance.
- Established deterministic-first architecture with selective LLM usage.
- Defined MVP output quality as: normalized constraints, blocker/contradiction handling, feasibility verdict, ranked options, and bookable next actions.

### New Artifact
- `Docs/FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md`
  - contains captured first-principles discussion
  - contains strict dependency-ordered build sequence (Stage 0 -> Stage 7)

### Immediate Execution Implication
- Next planning and implementation should be evaluated against Stage 0/1/2 readiness first, before orchestration or GTM expansion work.

## Log Entry: 2026-04-14 - First Principles Gap Assessment (Have vs Should vs Next)

### Context
User requested explicit first-principles checkpointing: what exists today, what should exist for MVP correctness, and what to execute next.

### Action Taken
- Added `Docs/FIRST_PRINCIPLES_GAP_ASSESSMENT_2026-04-14.md` with:
  - current-state inventory from code
  - MVP-required state from first principles
  - prioritized P0/P1/P2 gaps
  - strict next execution order and acceptance criteria

### Key Execution Constraint Reinforced
- Continue deterministic-first progression: contract -> deterministic compiler hardening -> realism -> optioning/ranking -> orchestration.

## Log Entry: 2026-04-14 - Multi-Agent Execution (NB02 Contract + Notebook Test Compatibility)

### Context
User requested execution using multiple agents with workflow compliance (plan -> implement -> verify -> document).

### Multi-Agent Work Completed
1. Notebook loader hardening:
   - `notebooks/test_02_comprehensive.py`
   - `notebooks/test_scenarios_realworld.py`
   - normalized notebook code-cell source before `exec` (`list[str]` -> joined `str`)
2. Decision-policy contract alignment:
   - updated `specs/decision_policy.md` to runtime v0.2 behavior
   - added `tests/test_decision_policy_conformance.py`

### Verification Performed
- `uv run python -m pytest tests/test_decision_policy_conformance.py -q` -> `5 passed`
- `uv run python -m pytest tests/test_nb02_v02.py -q` -> `19 passed`
- `uv run python -m pytest tests -q` -> `46 passed`
- Notebook scenario scripts executed with `PYTHONPATH=src`:
  - `notebooks/test_02_comprehensive.py` runs but reports multiple legacy expectation mismatches
  - `notebooks/test_scenarios_realworld.py` runs but reports multiple legacy expectation mismatches

### Notes
- Core `tests/` suite is green and aligned with current runtime contract.
- Notebook scripts contain legacy assumptions from pre-v0.2 interfaces and now act as migration gap indicators rather than strict release gates.

### Pending
- Decide whether notebook scripts should be:
  1. migrated fully to v0.2 contracts, or
  2. archived/reframed as legacy exploratory harnesses (non-gating).
- If retained, remove deprecated expectations (`current_stage`, `mvb_config`, old field names/aliases) and align assertions with v0.2 decisions.

## Log Entry: 2026-04-14 - Policy Tuning for Business-Ready Progression + PM/UX Artifact Expansion

### Context
User requested policy adjustment so practical, business-ready scenarios do not over-trigger follow-up questions. User also requested deeper PM-oriented coverage: detailed role flows, JTBD, aha moments, synthetic data, and explicit "what still needs work."

### Product/Policy Change Implemented
- Updated `src/intake/decision.py`:
  - `budget_feasibility` contradiction priority: `critical` -> `high`.
  - Stage-aware handling for infeasible budget:
    - `proposal`/`booking`: remains hard blocker.
    - `discovery`/`shortlist`: becomes soft blocker (allow internal draft progression).

### Validation Performed
- `PYTHONPATH=src uv run pytest -q tests/test_nb02_v02.py tests/test_decision_policy_conformance.py`
- Result: all tests passed (`24 passed`).
- E2E scenario pack executed and documented:
  - `Docs/reports/e2e_existing_plus_new_2026-04-14.md`
  - `Docs/reports/e2e_existing_plus_new_2026-04-14.json`
- Notable outcome: previously over-blocked business-ready scenarios now progress via `PROCEED_INTERNAL_DRAFT` where expected.

### New PM/UX Artifacts
- `Docs/PM_EXECUTION_BLUEPRINT_2026-04-14.md`
  - what makes the product tick
  - role outcomes (agency owner / senior / junior / traveler)
  - end-to-end execution flows
  - prioritized P0/P1/P2 backlog
- `data/fixtures/product_persona_flows_synthetic_v1.json`
  - persona JTBD (functional/emotional/social)
  - role-specific aha moments + metric proxies
  - persona journey flows and instrumentation fields

### Documentation Integrity Updates
- Indexed new PM blueprint in `Docs/INDEX.md`.
- Added fixture cross-reference section in `Docs/SYNTHETIC_DATA_AND_FIXTURES.md`.

### Remaining Open Items
- Decide release gate policy for notebook-based scenario scripts vs core pytest suite.
- Add traveler-safe quality rubric as explicit acceptance criteria in tests/docs.
- E2E expected-decision drift was resolved by aligning stale S03 legacy expectation in `tools/e2e_scenario_runner.py`; current run is `4/4` for expected checks.
