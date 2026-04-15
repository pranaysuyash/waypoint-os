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

## Log Entry: 2026-04-14 - First-Principles TODO Lock (Parsers -> NER -> OCR -> Gate)

### Context
User requested the immediate implementation order be documented as a strict TODO sequence before next planning discussion.

### Priority TODO Sequence (Locked)
From first principles, implementation should follow this exact order:

1. **Parser-first (deterministic constraints)**
   - Dates, money, pax, locations with strict typed parsers.
   - Locale-aware money/date parsing.
   - Hard rule: date-shaped tokens can never satisfy budget fields.

2. **NER/IE second (semantic fill + disambiguation)**
   - Entity extraction for destination, purpose, preferences, medical/accessibility, group structure.
   - Must output confidence + evidence spans, not just values.

3. **OCR/document ingestion layer**
   - For WhatsApp screenshots, PDFs, passports/visa docs, invoices.
   - OCR output should keep line/box provenance so extraction can cite source.

4. **Schema + confidence gate**
   - Typed validation before decision policy.
   - Low-confidence or conflicting critical fields -> `ASK_FOLLOWUP` / `STOP_NEEDS_REVIEW`.

## Log Entry: 2026-04-14 - Context 2 Ingested (One-Time Link + 5-Core Compression)

### Context
User provided additional second context file from Downloads and requested integration into project documentation.

### Source and Preservation
- Source file: `/Users/pranay/Downloads/travel_agency_context_2.txt`
- Archived in repo: `Archive/context_ingest/travel_agency_context_2_2026-04-14.txt`
- Digest outputs:
  - `Docs/context/TRAVEL_AGENCY_CONTEXT_2_DIGEST_2026-04-14.md`
  - `Docs/context/travel_agency_context_2_digest_2026-04-14.json`

### Decisions/Signals Captured
- Product surface should be **channel-agnostic one-time link workspace**, not chat-only delivery.
- Architecture direction favors **5-core model** over larger specialist-agent mesh for latency/control reasons.
- Canonical packet contract reaffirmed as state backbone.
- Commercial logic highlighted as non-optional (margin floors, partner preference, effort economics).
- Provenance visibility ("source from user message/channel") reinforced as trust feature.

### New Artifact
- `Docs/context/TRAVEL_AGENCY_CONTEXT_2_SYNTHESIS_2026-04-14.md`

### Traceability
- Added to docs navigation:
  - `Docs/INDEX.md`

## Log Entry: 2026-04-15 - Additional Discussion Ingested (Repeat/Ghosting/Window-Shopper/Churn)

### Context
User provided an additional lifecycle-focused discussion and requested explicit treatment of:
- repeat customers
- churn
- ghosting risk
- window-shoppers

### Coverage Review Outcome
- Repeat customer and ghosting ideas existed in docs/scenarios but were fragmented.
- Churn and lifecycle intelligence were mostly implied, not standardized as a first-class contract.
- Existing stack was stronger on trip intelligence than commercial lifecycle intelligence.

### New Artifact Added
- `Docs/LEAD_LIFECYCLE_AND_RETENTION.md`

### What the new artifact formalizes
- lifecycle state machine
- additive canonical packet `lifecycle` schema block
- deterministic v1 heuristic scoring
- commercial decision family
- intervention playbooks
- NB01/NB02/NB03 integration points
- lifecycle metrics

### Traceability
- Added to docs navigation:
  - `Docs/INDEX.md`

## Log Entry: 2026-04-15 - Projects Workflow Compliance (Explicit Lifecycle Record)

### Context
User requested explicit demonstration that the Projects-level workflow structure was discovered and followed (analysis -> document -> plan -> research -> decision log -> implement -> test -> document results), and asked that this also be reflected at project level.

### Actions Taken
- Added explicit compliance artifact:
  - `Docs/context/WORKFLOW_COMPLIANCE_ENTRY_2026-04-15.md`
- Refreshed project-level context pack via:
  - `/Users/pranay/Projects/agent-start --project travel_agency_agent --skip-index`
- Confirmed refreshed files:
  - `.agent/AGENT_KICKOFF_PROMPT.txt`
  - `.agent/SESSION_CONTEXT.md`
  - `.agent/STEP1_ENV.sh`

### Test Status
- Re-ran `pytest -q`; same pre-existing notebook import-path errors remain (`ModuleNotFoundError: intake` in two notebook tests).

5. **Fallback strategy**
   - Deterministic parser > NER suggestion > regex fallback (never the reverse for critical fields).

### Immediate Next Priority
- Start parsers + NER + OCR now, with deterministic parsers as the first implementation priority.

## Log Entry: 2026-04-14 - Visa/VOA/Document Requirement Coverage Audit (Discussion Captured)

### Context
User asked whether visa/document-requirement discussions already exist in the codebase and asked that discussion outcomes always be documented automatically.

Environment date checked before update:
- `2026-04-14 10:35:53 IST`

### What Exists Today (Found)
- Code-level partial implementation:
  - `src/intake/extractors.py` contains `_extract_passport_visa(...)` with basic keyword/regex extraction.
  - `src/intake/decision.py` contains booking-stage risk checks for `passport_status` / `visa_status`.
- Documentation-level coverage exists in multiple places:
  - persona scenarios and gap docs (`Docs/personas_scenarios/*`)
  - UX and PM artifacts (`Docs/UX_*`, `Docs/PM_EXECUTION_BLUEPRINT_2026-04-14.md`)
  - contract/gap notes (`Docs/CONTRACT_CHALLENGE_NOTE.md`, `Docs/FIRST_PRINCIPLES_GAP_ASSESSMENT_2026-04-14.md`)

### Gap Summary
- Coverage is present but fragmented; no single canonical execution contract for visa/doc policy.
- Missing deterministic visa/document parser contract for:
  - visa type (`e-visa`, `visa_on_arrival`, embassy visa),
  - transit constraints,
  - processing-time risk by trip date.
- Missing explicit critical-field completeness set for visa decisions:
  - traveler nationality, residency, travel document type, entry count, transit countries, issuing country.
- OCR provenance requirement (line/box citation) is stated conceptually but not wired end-to-end for passport/visa evidence traceability.
- Confidence/evidence-span requirements are not yet fully enforced as a strict visa/doc decision gate.

### Decision
- Treat visa/VOA/document requirements as a P0 implementation stream under the already locked sequence:
  - deterministic parser -> NER/IE -> OCR provenance -> schema/confidence gate -> fallback.
- Track this as an explicit issue in `Docs/issue_review.md` for implementation follow-through.

## Log Entry: 2026-04-14 - Decision Memo Locked + Workflow Source Clarified

### Context
User requested direct execution without additional prompts: document provided strategy inputs, create a concrete decision memo, and clarify "my workflow" location.

### Actions Completed
- Created decision memo with explicit go/no-go gates and scope lock:
  - `Docs/context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md`
- Created internal workflow location and usage mapping (non-user-facing):
  - `Archive/context_ingest/internal_notes_2026-04-14/WORKFLOW_LOCATION_AND_USAGE_2026-04-14.md`

### Key Clarification
- Workspace-level workflow exists on disk at `/Users/pranay/Projects/AGENTS.md`.
- Repo-specific workflow was provided in-session but not persisted as `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`.

### Follow-up
- Optional hardening action: persist repo-specific workflow into local `AGENTS.md` for deterministic future loading.

## Log Entry: 2026-04-14 - SEO + Next.js Playbook Ingested with Execution Filter

### Context
User provided additional strategy and implementation detail from external AI discussion (`Thinking-about-agentic-flow (8).html`) and requested integration into project context.

### Actions Completed
- Archived source file inside repository:
  - `Archive/context_ingest/meta_design_refs_2026-04-14_1816/Thinking-about-agentic-flow (8).html`
- Added synthesis doc with explicit keep/change/defer guidance:
  - `Docs/context/SEO_NEXTJS_GTM_PLAYBOOK_SYNTHESIS_2026-04-14.md`

### Key Decision
- Adopt SEO wedge and component structure for MVP.
- Defer aggressive 50-page programmatic expansion until funnel and precision gates are met.

## Log Entry: 2026-04-15 - Lifecycle/Retention Engine Implemented in Runtime (NB02 Additive Pass)

### Context
User asked to run the workflow end-to-end against current project state and implement missing lifecycle/churn parts only where they materially improve the existing system.

Environment date checked before this documentation update:
- `2026-04-15 08:12:13 IST`

### Implementation Completed
- Added canonical lifecycle block support in packet model:
  - `src/intake/packet_models.py` (`LifecycleInfo`, optional `CanonicalPacket.lifecycle`, serialization)
- Exported lifecycle model:
  - `src/intake/__init__.py`
- Added deterministic lifecycle scoring and commercial policy in NB02:
  - `src/intake/decision.py`
  - New scores: `ghost_risk`, `window_shopper_risk`, `repeat_likelihood`, `churn_risk`
  - New outputs on `DecisionResult`: `commercial_decision`, `intent_scores`, `next_best_action`
- Added tests for lifecycle/commercial behavior:
  - `tests/test_lifecycle_retention.py`

### Verification
- Focused suite passed:
  - `uv run pytest -q tests/test_lifecycle_retention.py tests/test_decision_policy_conformance.py tests/test_nb02_v02.py`
  - Result: `29 passed`
- Full suite status unchanged from prior baseline:
  - `uv run pytest -q`
  - Existing notebook collection errors remain (`ModuleNotFoundError: intake` in notebook tests).

### Outcome
- Lifecycle/churn logic moved from doc-only guidance to executable runtime behavior.
- Change is additive and backward-compatible with current trip decision flow.

## Log Entry: 2026-04-15 - Comprehensive Orchestration Alignment (No Scope Shrink)

### Context
User provided another discussion set and explicitly locked direction:
- do not reduce or delete prior comprehensive work
- keep additive improvement approach
- go big with proper multi-agent orchestration
- add this motto at Projects-level instructions

Environment date checked before this documentation update:
- `2026-04-15 08:17:30 IST`

### Actions Completed
- Added Projects-level execution motto in:
  - `/Users/pranay/Projects/AGENTS.md`
  - Motto: **additive, better, comprehensive** with explicit multi-agent orchestration preference.
- Added repo control docs:
  - `Docs/status/STATUS_MATRIX.md`
  - `Docs/status/PHASE_1_BUILD_QUEUE.md`
- Updated index links:
  - `Docs/INDEX.md`

### Decision
- Preserve full capability map and all historical documentation as product ontology.
- Use explicit status layering:
  - Knowledge Asset
  - Build Now
  - Design Contract
  - Orchestration Expansion
- Treat current phase work as foundation for larger orchestration, not MVP downscoping.

## Log Entry: 2026-04-15 - Follow-up Mode Bug Fix + Notebook Import Path Hardening

### Context
User requested immediate implementation of:
1. notebook import-path failure fix
2. `follow_up` mode bug flagged in issue review
3. clarification and correction of model-specific issue-review naming

Environment date checked before this documentation update:
- `2026-04-15 08:22:32 IST`

### Actions Completed
- Fixed runtime bug in `src/intake/decision.py`:
  - `apply_operating_mode(...)` now receives `hard_blockers` explicitly.
  - Updated call site in `run_gap_and_decision(...)`.
- Added regression coverage:
  - `tests/test_follow_up_mode.py`
- Hardened notebook scripts so `src` import path is injected before notebook cell execution:
  - `notebooks/test_02_comprehensive.py`
  - `notebooks/test_scenarios_realworld.py`
- Prevented notebook script harnesses from being collected as pytest modules:
  - `pyproject.toml` -> `[tool.pytest.ini_options] testpaths = ["tests"]`
- Addressed naming convention drift:
  - Added canonical project-neutral review file:
    - `Docs/process_issue_review_2026-04-15.md`
  - Converted `Docs/gemini issue review.md` to legacy pointer.
  - Updated `Docs/INDEX.md` link to project-neutral file.
- Stabilized unrelated flaky geography test using unique runtime-generated fake city names:
  - `tests/test_geography.py`

### Verification
- Targeted decision/path tests:
  - `uv run pytest -q tests/test_follow_up_mode.py tests/test_decision_policy_conformance.py tests/test_nb02_v02.py`
  - Result: `25 passed`
- Full suite:
  - `uv run pytest -q`
  - Result: `132 passed`
- Notebook script import-path check:
  - Executed both notebook scripts and verified no `ModuleNotFoundError: intake` surfaced.

## Log Entry: 2026-04-15 - Operator Workbench Component Spec + Ticketed Acceptance Checklist

### Context
User requested explicit conversion of UI direction into execution-grade specification and acceptance gates.

Environment date checked before this documentation update:
- `2026-04-15 08:42:54 IST`

### Actions Completed
- Added component specification:
  - `Docs/status/OPERATOR_WORKBENCH_COMPONENT_SPEC_2026-04-15.md`
- Added ticketed acceptance checklist:
  - `Docs/status/WORKBENCH_ACCEPTANCE_CHECKLIST_2026-04-15.md`
- Updated index links:
  - `Docs/INDEX.md`

### Decision
- Proceed with one internal Streamlit app in Phase A.
- Implement two real modes (Workbench + Flow Simulation) over frozen spine modules.
- Keep logic centralized in shared intake modules; UI remains orchestration and presentation layer only.

## Log Entry: 2026-04-15 - Frontend Direction Override (No Streamlit, Proper Full Frontend)

### Context
User explicitly requested a proper full frontend path and rejected Streamlit for implementation.

Environment date checked before this documentation update:
- `2026-04-15 09:50:32 IST`

### Actions Completed
- Added full-scope frontend specification:
  - `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`
- Preserved previous draft as historical baseline:
  - `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15_STREAMLIT_BASELINE.md`
- Marked Streamlit-oriented workbench docs as superseded/historical context:
  - `Docs/status/OPERATOR_WORKBENCH_COMPONENT_SPEC_2026-04-15.md`
  - `Docs/status/WORKBENCH_ACCEPTANCE_CHECKLIST_2026-04-15.md`
- Updated docs index:
  - `Docs/INDEX.md`

### Decision
- Frontend implementation path is now locked to productized web app architecture (Next.js + TypeScript), including internal workbench routes inside the same shell.
- No Streamlit implementation path for frontend delivery.

## Log Entry: 2026-04-15 - Next.js Frontend Implementation Track Defined

### Context
User requested conversion of full frontend spec into execution-ready implementation tracks with routes, ownership, and API contracts.

Environment date checked before this documentation update:
- `2026-04-15 09:57:42 IST`

### Actions Completed
- Added Next.js implementation track:
  - `Docs/status/NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md`
- Included:
  - route-by-route build track
  - component ownership map
  - BFF API contracts (`/api/spine/run`, scenario, fixture compare)
  - phased FE ticket sequence (P0/P1/P2/P3)
  - test plan and program-level done criteria
- Updated docs index:
  - `Docs/INDEX.md`

### Decision
- Frontend execution is now explicitly organized as Next.js product tracks with no Streamlit dependency.

## Log Entry: 2026-04-15 - Plan Correction Applied (Contract + Phase Ordering)

### Context
User provided blocking feedback: resolve Streamlit vs Next.js conflict, keep workbench as internal validation route inside product shell, and fix BFF enum contract mismatch with frozen spine before implementation proceeds.

Environment date checked before this documentation update:
- `2026-04-15 10:03:53 IST`

### Actions Completed
- Corrected implementation track file:
  - `Docs/status/NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md`
- Added explicit truth-source section:
  - Next.js as only active implementation path
  - full frontend spec as product truth
  - workbench docs treated as screen-level behavior/acceptance references only
- Corrected `/api/spine/run` request contract to spine-native enums:
  - `stage`: `discovery | shortlist | proposal | booking`
  - `operating_mode`: `normal_intake | audit | emergency | follow_up | cancellation | post_trip | coordinator_group | owner_review`
- Tightened runtime rules:
  - shared orchestrator entrypoint under `src/intake/`
  - strict leakage hard-fail behavior
  - no reruns on tab switch
- Reordered execution phases:
  - P0 foundation first
  - P1 internal product core (`/app/workbench` + `/app/workspace/[tripId]/*`)
  - P2 inbox + owner + traveler
  - P3 public growth surface

### Decision
- Contract drift between frontend/BFF and frozen spine is now removed at plan level.
- Implementation sequencing now reflects foundation -> workspace core -> additional surfaces.
