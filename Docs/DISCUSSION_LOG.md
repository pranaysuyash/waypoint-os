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

## Log Entry: 2026-04-15 - Coverage Matrix Added as Control Layer

### Context
After the coverage assessment was documented, user requested a second artifact: a **new standalone document** that works as a practical matrix rather than narrative analysis.

### New Artifact Added
- `Docs/COVERAGE_MATRIX_2026-04-15.md`

### What the new artifact does
- separates documented vs scenario-written vs tested vs implemented status
- organizes coverage by risk, stakeholder, scenario family, lifecycle stage, market segment, and commercial logic
- makes the gap between product thinking and runtime closure explicit
- provides a prioritized closure list for P0 / P1 / P2 follow-up
- now also includes execution-oriented planning fields:
  - priority
  - repo area / module
  - acceptance signal
  - blocking dependency

### Traceability
- Added to docs navigation:
  - `Docs/INDEX.md`

## Log Entry: 2026-04-15 - Coverage Closure Queue Added

### Context
After the coverage matrix was upgraded with execution-oriented planning fields, user approved taking the next step if it made sense: convert the highest-priority matrix items into an explicit ordered build queue.

### New Artifact Added
- `Docs/status/COVERAGE_CLOSURE_BUILD_QUEUE_2026-04-15.md`

### What the new artifact does
- translates P0/P1 matrix gaps into a dependency-ordered implementation queue
- aligns work to concrete repo areas such as:
  - `src/intake/decision.py`
  - `src/intake/packet_models.py`
  - `src/intake/extractors.py`
  - `tests/`
- defines acceptance signals for each phase
- separates trust-critical work from later expansion-layer work

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

## Log Entry: 2026-04-15 - Coverage Review Discussion Documented (Risks / Scenarios / Stakeholders / Markets)

### Context
User asked whether the project now has adequate coverage from different angles, including:

- risks
- scenarios
- use cases
- stakeholders
- markets

User then requested that the discussion be documented explicitly, including what is already done, what could be better, and what major coverage gaps remain.

### Findings Captured
- Documentation coverage is now broad across risk categories, personas, scenario families, and core market framing.
- Runtime coverage is still narrower than documentation coverage and remains concentrated around the deterministic golden path.
- The project is no longer primarily missing ideas; it is primarily missing implementation and systematic coverage closure.

### New Artifact Added
- `Docs/COVERAGE_ASSESSMENT_2026-04-15.md`

### What the new artifact summarizes
- what is well covered now
- what improved materially in recent work
- where documentation is ahead of runtime
- which coverage gaps still matter most
- recommended next documentation move: explicit coverage matrix

### Traceability
- Added to docs navigation:
  - `Docs/INDEX.md`

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
  - Converted the legacy issue review pointer filename to a non-model-specific name.
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

## Log Entry: 2026-04-16 - Thesis Deep Dive: Four Open Threads (Updated: No MVP Framing)

### Context
Comprehensive discussion of `PROJECT_THESIS.md` covering all four identified tension points, cross-referenced against 7 existing docs and codebase state. User explicitly corrected framing: **no MVP scoping — full production system phased by dependency order**.

### Artifact Created
- `Docs/DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md`

### Four Threads Analyzed
1. **Copilot vs. Replacement line** — System already models significant judgment (decision gating, lifecycle scoring, feasibility). Need autonomy gradient + override dignity pattern.
2. **Intelligence Layer lead-gen** — Two distinct funnels (agency self-audit vs. consumer audit). Both are production targets. Agency self-audit ships first (Stage 2), consumer audit ships with GTM surface (Stage 7).
3. **Sourcing hierarchy configurability** — Currently a taxonomy label, not a decision driver. Per-agency `SourcingPolicy` config object needed — design contract now, implement with vendor/supplier models (Gap #01).
4. **Per-person suitability depth** — `activity_matcher.py` is referenced in architecture but not implemented. Three depth levels (L1 binary → L2 scored → L3 scheduling) — ALL are production targets, phased by dependency.

### D4 and D6 Detailed Breakdowns Added
- **D4**: Full production scope for `activity_matcher.py` across three phases. Blocking question: what data model supports all three levels without rework? Three sub-decisions: layer ownership, dataclass extensibility, activity catalog data source.
- **D6**: Full audit-mode eval suite spec: ~40-60 fixture set, recall/precision/severity metrics, CI regression gate. Recommendation: build framework and author fixtures now, gate incrementally as capabilities ship. D4 and D6 are coupled — build in parallel.

### Key Gaps Identified
- No `SourcingPolicy` model in packet models
- No `activity_matcher.py` runtime implementation
- No audit-mode eval suite / accuracy benchmarks
- Human override protocol specified but not implemented as runtime path

### Open Decisions (6)
- D1: Autonomy gradient — configurable with "always review" default
- D2: Free engine persona — both funnels, sequenced by dependency
- D3: Sourcing configurability — per-agency, design now, implement with Gap #01
- D4: Suitability depth phasing — all three levels, **blocking: data model design** (detailed)
- D5: Override learning — log + influence via traveler memory
- D6: Audit-mode eval suite — **blocking: quality gate for audit surface** (detailed)

### Cross-Thread Synthesis
Threads 3 (sourcing) and 4 (suitability) are foundational — they determine system credibility. Thread 1 (autonomy) is a UX/config question. Thread 2 (lead-gen) is GTM and should not drive architecture.

## Log Entry: 2026-04-16 - LLM Output Caching + NB05/NB06 Architecture

### Context
User raised two critical gaps in the D4/D6 architecture:
1. Every LLM call must extract and cache its output so similar future calls reuse cached results instead of calling the LLM again.
2. NB05 (golden-path demos) and NB06 (shadow-mode replay) are defined in V02 but not addressed in D4/D6.

### Artifact Created
- `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md`

### Key Discovery
`src/decision/hybrid_engine.py` already implements the cache → rule → LLM → cache-result pattern with feedback-based success rate tracking (`CachedDecision.record_feedback()`). This is a strong foundation — needs extension to all LLM touchpoints, not replacement.

### Decisions

**LLM Caching Strategy:**
- `LLMCacheable` protocol generalizes the existing hybrid engine pattern to all LLM touchpoints (extraction, question generation, suitability scoring, audit explanation, proposal generation, tone adaptation)
- Every LLM call logs to `LLMCallLog` (namespace, cost, latency, cache hit/miss)
- Cache lifecycle: call → cache → feedback → eviction or promotion
- **Cache → Rule promotion**: When a cached decision has `use_count > 20`, `success_rate > 0.95`, `feedback_count > 5`, it's a candidate for promotion to a deterministic rule. System gets cheaper over time.

**NB05 (Golden-Path Demos):**
- NOT a runtime pipeline stage — a demonstration and validation system
- Curated `GoldenPathScenario` dataclass with expected outcomes at every pipeline stage
- Leakage assertions (internal data never in traveler output)
- Cache-warming function: golden paths pre-populate LLM cache with known-good results
- Lives in `src/evals/golden_path/`

**NB06 (Shadow-Mode Replay):**
- Replays real production inputs through experimental pipeline, compares outputs
- `ShadowDiff` structured comparison (decision state, risk flags, costs, latency)
- Primary feedback loop for cache freshness validation
- Used to test new scorers, audit rules, and policy changes before deployment
- Lives in `src/evals/shadow/`

### The Evolution Flywheel
Day 1: Heuristics + LLM for edge cases → cache results
Week 2: Cache hit rate climbs, costs drop
Month 1: High-success cached decisions promoted to rules
Month 3: New capabilities start LLM-assisted → graduate to rules
Ongoing: Every LLM call is a compounding investment that reduces future costs.

## Log Entry: 2026-04-16 - Architecture Decision: D4+D6 Suitability Engine + Audit Eval Suite

### Context
User requested architecturally sound decisions where everything evolves and improves — no throwaway contracts, no MVP scoping.

### Artifact Created
- `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md`

### Core Architectural Decisions
1. **Analyzers vs. Routers split**: D4 (suitability) is an analyzer that computes typed artifacts. D6 (audit) is a measurement system over those same artifacts. They share contracts but never duplicate logic.
2. **Protocol-based plugin pattern**: Three swappable interfaces for suitability (`ActivityCatalogProvider`, `SuitabilityScorer`, `ScheduleAllocator`) and one for audit (`AuditRule`). Simple Python protocols + registries — no framework dependency.
3. **Stable contracts across all phases**: `ActivitySuitability` uses same shape for binary flags (Phase 1), scored compatibility (Phase 2), and per-person scheduling (Phase 3). `ParticipantRef` evolves from `cohort` → `person` without downstream contract changes.
4. **Manifest-driven eval suite**: Categories progress `planned` → `shadow` → `gating`. Eval suite serves as both quality gate AND roadmap.
5. **`StructuredRisk` as common finding contract**: Replaces current `List[Dict]` risk flags. Same type used by runtime decision engine, audit rules, and eval fixtures.
6. **`AuditDerivedState` as shared cache**: D4 suitability bundles feed directly into D6 audit rules — the activity audit rule reads suitability results, never re-scores.

### Module Layout Specified
- `src/intake/suitability/` (contracts, registry, service, catalogs, scorers, scheduling)
- `src/intake/audit/` (contracts, registry, engine, rules per category)
- `src/evals/audit/` (manifest, fixtures, metrics, gates, runner)
- 5-step migration path from current `decision.py` monolith

### Guardrails Locked
- Agency customization via policy objects, never code branches
- ML scoring cannot bypass hard exclusions
- External data normalizes to `ActivityDefinition` before scoring
- Eval gates per-category, not just aggregate
- Traveler memory is explicit input, not hidden side effect

### Open Sub-Decisions (5)
- D4.1: Initial activity catalog scope (destination-scoped vs. activity-type-only)
- D4.2: Suitability matrix granularity (~100 cells vs. tag-based)
- D4.3: Layer ownership — `src/intake/` vs. `src/planning/`
- D6.1: Fixture authoring source (manual vs. real agency scenarios)
- D6.2: Fixture format (Python dataclasses vs. JSON/YAML)

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

## Log Entry: 2026-04-16 - Activity Suitability Matrix Web Findings Documented

### Context
User requested that web research findings be documented directly and consistently.

### Actions Completed
- Created dedicated research artifact:
  - `Docs/ACTIVITY_SUITABILITY_MATRIX_WEB_FINDINGS_2026-04-16.md`
- Captured evidence for:
  - API/provider landscape for age suitability signals
  - OTA activity-data structuring patterns
  - family and elderly/accessibility resource overlays
- Included confidence levels, caveats, normalized schema proposal, and source appendix URLs.

### Key Outcome
- Research is now preserved as a reusable implementation input for Product B / GTM activity suitability matrix work.
- Documentation explicitly records that direct provider-level age suitability scores were not verified; suitability must be derived from structured constraints and overlays.

## Log Entry: 2026-04-16 - Activity Suitability Implementation Handoff Added

### Context
User approved creation of an execution-grade handoff document derived from web findings.

### Actions Completed
- Added implementation handoff artifact:
  - `Docs/status/ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md`
- Included deterministic delivery content:
  - provider onboarding priority order
  - canonical suitability schema
  - provider-level field mapping matrix
  - scoring pseudocode with confidence adjustment
  - phased implementation sequence and acceptance criteria
  - risk and drift mitigation notes
- Added index discoverability entry:
  - `Docs/INDEX.md`

### Key Outcome
- Downstream implementation can now proceed without additional research interpretation.
- Handoff is aligned to deterministic-first execution and includes explicit confidence/provenance expectations.

## Log Entry: 2026-04-16 - Pricing Angle + Map/Globe + Real-Time Flight Tracking Exploration

### Context
User asked to explore product and GTM opportunities around:
- pricing strategy/packaging
- map or globe component
- real-time flight tracking

### What Was Reviewed
- Existing pricing strategy and GTM guidance in:
  - `Docs/GTM_AND_DATA_NETWORK_EFFECTS.md`
  - `Docs/PRODUCT_VISION_AND_MODEL.md`
- Frontend readiness and product-surface gaps in:
  - `Docs/FRONTEND_COMPREHENSIVE_AUDIT_2026-04-16.md`
- Codebase scan confirmed map/globe and live flight tracking are not currently implemented as product modules.

### Strategic Outcome (Documented Direction)
1. **Pricing**
   - Keep core subscription simple.
   - Introduce attachable premium value layers:
     - Price Intelligence add-on
     - Live Ops (flight disruption) add-on
     - Traveler map/share experience module (mid/high tiers)

2. **Map/Globe Productization Sequence**
   - Phase 1: 2D operational route map (itinerary legs, transfer/risk overlays).
   - Phase 2: Traveler-safe branded share surface.
   - Phase 3: Optional 3D globe only if conversion/demo ROI is proven.

3. **Real-Time Flight Tracking Productization Sequence**
   - Start with delay/cancellation/gate-change operational alerts.
   - Attach action playbooks (notify traveler, adjust transfer, reflow itinerary).
   - Monetize by active trip segment / ops usage rather than broad flat inclusion.

### GTM/Execution Recommendation
- 90-day rollout framing:
  1. Price intelligence lite + 2D map baseline
  2. Flight disruption alerts + ops action cards
  3. Premium traveler map experience + usage-linked monetization

### Key Constraint Recorded
- Feature roadmap should remain dependency-ordered and deterministic-first.
- Visual sophistication (globe) should follow measurable operational/commercial impact, not precede it.

## Log Entry: 2026-04-17 - Baseline Packaging Proposal (₹6k Core + Team Packs + Add-ons)

### Context
User proposed a commercially simpler baseline aligned with prior direction:
- one default plan around ₹6,000/month
- includes 1 owner/admin + 4 team members
- additional team member packs can be added
- add-on components (including live modules) should remain separate

### Decision Signal Captured
- Keep pricing architecture simple at the entry point (single strong default).
- Preserve modular monetization through optional add-ons rather than feature bloat in base tier.
- Use team expansion packs as the scaling mechanism before introducing multi-tier complexity.

### Recommended Implementation Interpretation
1. **Core Default Plan**
  - `Core_6000`: owner/admin + 4 team seats.
2. **Team Expansion**
  - add seat packs (e.g., +3 or +5 users) as attachable increments.
3. **Optional Add-ons**
  - Price Intelligence module
  - Live Ops / Flight disruption module
  - Traveler map/share premium module

### Why This Matters
- Reduces decision fatigue in early sales conversations.
- Keeps packaging aligned with demonstrated agency team structures.
- Maintains clear path to ARPU growth via expansion + add-ons.

## Log Entry: 2026-04-17 - Next Exploration Direction: Plugin System (Draft)

### Context
User asked what to explore next and suggested plugin system as the next strategic thread.

### Actions Completed
- Created draft exploration artifact:
  - `Docs/PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md`
- Documented:
  - candidate plugin domains (suitability, audit rules, data sources, ops/live)
  - core design questions (registration, contract strictness, execution, safety, precedence)
  - recommended v1 architecture (explicit registry + execution guardrails)
  - phased execution order and non-goals

### Traceability
- Added index link:
  - `Docs/INDEX.md`

## Log Entry: 2026-04-17 - Pricing Packaging Draft Documented (Proper Naming)

### Context
User requested the discussion to be documented with a clear and proper name while keeping status as non-final.

### Actions Completed
- Created dedicated draft artifact:
  - `Docs/PRICING_PACKAGING_DISCUSSION_DRAFT_2026-04-17.md`
- Captured current working direction:
  - ₹6,000 default plan
  - 1 owner/admin + 4 team members included
  - team expansion packs
  - modular add-ons (live ops, price intelligence, traveler map/share)
- Explicitly marked document status as **Draft / Not Final** with open questions.

### Traceability
- Added to docs navigation:
  - `Docs/INDEX.md`

## Log Entry: 2026-04-17 - Trip Workspace Fix (Blank Page + Mock Data + Wiring)

### Context
User reported two issues: (1) clicking recent trips from dashboard/inbox opened a blank workspace instead of showing trip data, and (2) UI still said "workbench" everywhere despite previous claims of wording fixes. Further investigation revealed that all 5 tabs showed empty states because no pipeline data was populated, the IntakeTab had a hardcoded dropdown of fake trips, and the Process Trip button was dead (no onClick).

### Root Cause
- Workbench page read `?tab=` URL param but never read `?trip=` param. The `useTrip(id)` hook existed but wasn't used.
- IntakeTab had 4 hardcoded fake trip IDs (`sgp-family`, `dubai-corp`) unrelated to real trip data.
- Trip detail API only had 2 of 7 trips with basic fields (no packet/decision/strategy/safety data).
- Process Trip button rendered but had no onClick handler.
- "Workbench" wording in 305+ references across source files.

### Actions Completed
1. **Trip detail API enrichment** (`api/trips/[id]/route.ts`): Expanded from 2 trips to all 7 trips with full pipeline mock data — packet (facts, derived signals, ambiguities), validation, decision (state, blockers, rationale, budget breakdown), strategy (goal, priority sequence, tonal guardrails, suggested opening), safety (leakage check), internal_bundle, traveler_bundle, customerMessage, agentNotes.
2. **Workbench store hydration** (`workbench/page.tsx`): Added `useHydrateStoreFromTrip()` hook that reads `?trip=` param, fetches trip data, and pushes all pipeline results into Zustand store so all 5 tabs render populated.
3. **IntakeTab rewrite** (`workbench/IntakeTab.tsx`): Removed hardcoded dropdown, added trip detail card (destination, party, dates, budget), connected textareas to Zustand store for pre-filled customer message and agent notes.
4. **Process Trip button wiring**: Connected to `useSpineRun` hook, sends intake inputs to `POST /api/spine/run`, populates store with results on success, shows error banner on failure.
5. **Reset button**: Clears all store state (inputs + results).
6. **Wording cleanup**: "Open workbench" → "Open Trip Workspace", sidebar descriptions updated.

### Key Decisions
- Route paths (`/workbench`) kept as-is to avoid breaking navigation — only user-facing labels changed.
- Store hydration uses `useRef` guard to prevent double-hydration in React strict mode.
- Process Trip button disabled when both inputs are empty (nothing to process).
- Mock data designed to cover all decision states: PROCEED_SAFE, ASK_FOLLOWUP, BRANCH_OPTIONS, STOP_NEEDS_REVIEW.

### Verification
- `npx next build` passes clean.
- All 7 trips in list API have matching detail entries.
- Full session writeup: `Docs/SESSION_WRITEUP_TRIP_WORKSPACE_FIX_2026-04-17.md`

### Deferred to Real API Stage
- Database-backed trip storage (replace all mock data)
- Input persistence (PUT/PATCH endpoints)
- Python spine API deployment for live Process Trip functionality
- Local caching / offline support

## Log Entry: 2026-04-18 - D4/D6 Sub-Decisions Resolved (D4.1–D4.3, D6.1–D6.2)

### Context
Five sub-decisions from `ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md` Part 8 were discussed. During D4.1 discussion, the owner identified a critical gap: suitability was being evaluated per-activity in isolation, which would break coherence within the same tour (e.g., temple walk after 3-hour hike in tropical heat for elderly ≠ temple walk on a rest day).

### Evolution Trigger
Owner challenge: "Shouldn't we also look at a hybrid LLM-based strategy for D4.1? I don't want later that the logic breaks within the same tour." This exposed that the `SuitabilityContext` had no awareness of other activities in the trip — scorer evaluated each activity independently.

### Decisions Made

**D4.1 — Activity Catalog + Scoring Architecture**: Hybrid three-tier scoring:
- Tier 1: Per-activity deterministic tag rules (~40-60 rules), safety floor, ₹0
- Tier 2: Tour-context deterministic sequence rules (~15-20 rules) evaluating cumulative intensity, back-to-back strain, rest-day gaps, climate×intensity, ₹0
- Tier 3: LLM contextual scoring via existing `HybridDecisionEngine` for borderline/ambiguous cases. Cached, graduating to rules.
- Catalog itself: activity-type tables (destination-agnostic), destination context enters through `SuitabilityContext` not catalog.

**D4.2 — Suitability Matrix Granularity**: Tag-based matching with two rule sections:
- Section A: per-activity rules (~40-60), feeds Tier 1
- Section B: sequence rules (~15-20), feeds Tier 2

**D4.3 — Module Placement**: `src/intake/suitability/` (NB02 judgment layer). Unchanged — tour-context scoring reinforces this is judgment, not planning.

**D6.1 — Fixture Authoring**: Manual curation with three fixture tiers:
- Tier A: isolated activity fixtures (~15-20)
- Tier B: day-sequence fixtures (~15-20)
- Tier C: trip-sequence fixtures (~10-15, adapted from existing `Docs/context/` scenarios)
- Total: ~50-65 fixtures. Real-world fixtures added post-pilot via NB06 shadow collector.

**D6.2 — Fixture Format**: YAML for data, Python dataclasses for schema/loading. Tour-context fixtures include `day_plan` section with per-day activity sequences.

### Key Contract Changes
- `SuitabilityContext`: extended with `day_activities`, `trip_activities`, `day_index`, `season_month`, `destination_climate`
- `AuditSubject`: extended with `day_plan` for tour-context fixtures
- All other parent document contracts (`ActivitySuitability`, `SuitabilityBundle`, `StructuredRisk`, `ParticipantRef`, `ActivityDefinition`): unchanged

### Artifacts
- Created: `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md`
- Parent: `Docs/ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md`

### Traceability
- Added to `Docs/INDEX.md`

## Log Entry: 2026-04-18 - D1 Autonomy Gradient Decision + Adaptive Autonomy Thread

### Context
Continued thesis deep dive sub-decisions. D1 (autonomy gradient) from `DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` Thread 1 discussed.

### Core Decision
Agency-level `AgencyAutonomyPolicy` config with per-`decision_state` approval gates (`auto`/`review`/`block`). Default: `"review"` for all traveler-facing outputs. Safety invariant: `STOP_NEEDS_REVIEW` is always `"block"`, no override.

### Evolution Thread: Adaptive Autonomy
Owner proposed: "We can fine-tune or give more autonomy based on learning — start looking at the customer+trip classification problem and switch on/off controls later." This reframes autonomy from static config → learned adaptive policy. System observes override patterns per trip classification, suggests loosening/tightening controls. Owner approves changes.

### Customer+Trip Classification Problem (Pending Deep Dive)
Identified as prerequisite for adaptive autonomy. Candidate dimensions: trip complexity, destination familiarity, budget sensitivity, customer type, suitability risk, composition complexity, time pressure. Five sub-questions (D1.1–D1.5) deferred until pilot data available.

### Remaining Open Items
- D2 (free engine persona), D3 (sourcing configurability), D5 (override learning) — open for discussion
- Plugin system — draft exists, decision needed
- D4/D6 implementation — migration Steps 1-5 pending

### Artifacts
- Created: `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`

### Traceability
- Added to `Docs/INDEX.md`

## Log Entry: 2026-04-18 - D2 Free Engine Persona Decision

### Context
Continued thesis deep dive. D2 (free engine target persona) from `DISCUSSION_THESIS_DEEP_DIVE_2026-04-16.md` Thread 2 discussed.

### Key Consolidation
Funnel B (thesis deep dive) and Itinerary Checker GTM Wedge (`Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md`) are the same initiative described at two altitudes. Documented as such to prevent future confusion.

### Positioning Decision (Owner-Directed)
Owner corrected the framing: the free engine is NOT "your plan is bad, we'll fix it." It IS "here are things worth discussing with your planner before you finalize." The tool empowers consumers to ask better questions, not to replace their agency. Lead-gen conversion happens organically when the consumer's agency can't answer well — not through adversarial redirect.

### Architecture Decision
Shared pipeline (`operating_mode: "audit"` for both surfaces), different NB03 presentation layer. New field: `presentation_profile: Literal["agency", "consumer"]` controls NB03 builder selection, finding visibility, and language register. Consumer surface only shows `gating`-status rules from D6 eval manifest (stricter quality bar — no agent to catch false positives, and false positives undermine consumer-agency relationships under the empowerment framing).

### Sequencing
Agency self-audit (Funnel A) ships with Stage 2. Consumer free engine (Funnel B = itinerary checker) ships after D6 eval gating categories pass precision thresholds. Paid fix tier + lead routing after 30-day go/no-go gates from decision memo.

### Artifacts
- Created: `Docs/ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md`

### Traceability
- Added to `Docs/INDEX.md`

## Log Entry: 2026-04-18 - Cloudflare vs Postgres Clarification (Ease of Deployment + Cost)

### Context
Owner clarified original intent: **not anti-PostgreSQL**, but optimizing for **ease of deployment, lower operational cost, and simpler ops**. Request was to revisit Option B vs Option C in that framing.

### Original Ask (as clarified)
- "Not no PostgreSQL" 
- Prioritize: easy deploy, lower recurring cost, less ops burden
- Keep documenting findings and rationale in decision trail

### What Was Found
1. Project docs currently converge on: **FastAPI + PostgreSQL + managed hosting + R2 for files**.
  - `Docs/TECHNICAL_INFRASTRUCTURE.md`
  - `Docs/research/DATA_STRATEGY.md`
  - `Docs/DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md`
2. Cloudflare appears in existing architecture as:
  - **R2 for object/document storage**
  - edge/webhook infra options (Workers discussed, not adopted as primary system of record)
3. Current codebase has:
  - no DB deps yet (`pyproject.toml`)
  - no DB service in compose (`docker-compose.yml`)
  - JSON-file persistence (`spine-api/persistence.py`)
  - mock-heavy API routes in frontend BFF

### Option B vs Option C (deployment/cost lens)

#### Option B — Hybrid (Recommended in this phase)
**Shape**:
- FastAPI app remains core runtime
- PostgreSQL as system of record
- Cloudflare R2 for file/document storage
- Optional Cloudflare edge/CDN in front of app

**Pros**:
- Keeps architecture aligned with existing docs/specs
- Minimal migration friction from current Python/FastAPI code
- Strong long-term fit for analytics, RBAC, tenant scoping
- Cost remains controlled via managed Postgres + R2

**Cons**:
- Two-vendor stack (compute + data/storage split)
- Slightly more setup than all-in-one platform patterns

#### Option C — Current trajectory (Render/Railway + Postgres + R2)
**Shape**:
- Managed app hosting (Render/Railway)
- Managed PostgreSQL
- R2/S3 for documents

**Pros**:
- Fastest path to production with lowest change risk
- Operationally straightforward for solo/team-small stage
- Matches all existing persistence/auth planning artifacts

**Cons**:
- Less edge-native than full Cloudflare approach
- Still pays managed DB baseline costs (but predictable)

### Recommendation (for this project stage)
Use **Option C as default execution path**, while adopting **Option B elements incrementally** where they improve cost/ops:
- Keep PostgreSQL as source of truth
- Use Cloudflare R2 for documents from day one
- Add Cloudflare edge only when traffic/perf pressure justifies it

This satisfies owner's clarified constraint (easy deployment + lower cost) without forcing a high-risk platform pivot.

### Decision Status
- **No hard pivot away from PostgreSQL**
- **Cost/ease-optimized path accepted**: Postgres + managed deploy + R2
- Revisit full Cloudflare runtime only after persistence/auth/analytics backbone is live and measured

## Log Entry: 2026-04-18 - Cost-Floor Deployment Plan (Option B/C Execution)

### Context
Owner confirmed priority order:
1. ease of deployment,
2. lower recurring cost,
3. architecture upgrades later when cost viability/revenue is proven.

### Original Ask (captured)
- Keep documenting decision trail while moving forward
- Do not optimize for maximum architecture complexity before commercial validation
- Keep PostgreSQL in scope (not rejected), but avoid expensive/complex ops now

### What Was Found in Current Repo State
- Deploy assets already present for managed hosting (`render.yaml`, `fly.toml`).
- Runtime is Python/FastAPI-first (`README.md`, `spine-api/server.py`).
- Persistence is still JSON-file based (`spine-api/persistence.py`) and not yet DB-backed.
- No DB dependencies/config yet in runtime (`pyproject.toml`, `docker-compose.yml`).

### Cost-Floor Strategy (Practical)

#### Phase 1 — Revenue-Validation Baseline (now)
**Primary stance**: Option C default + Option B storage component
- App hosting: managed web service (Render/Fly/Railway) with minimum viable plan.
- DB: PostgreSQL as source of truth (single primary, no replicas).
- File storage: Cloudflare R2 from day one for docs/uploads.
- Observability: basic logs + health checks; defer heavy tooling.

**Explicit defer list (to keep costs down)**:
- No read replicas
- No queue cluster (use simple background tasks first)
- No multi-region active-active
- No full edge rewrite to Workers/D1/DO
- No premium observability stack until error volume justifies it

#### Phase 2 — Early Revenue / Stability Upgrade
Trigger: recurring revenue covers infra by comfortable margin or sustained reliability pain
- Add alerting and error budget dashboards
- Add migration-safe background job mechanism
- Add DB backup automation verification cadence

#### Phase 3 — Architecture Lift (only after viability)
Trigger: measurable limits in cost-per-trip, latency, or ops toil
- Introduce edge acceleration/CDN where evidence supports it
- Evaluate deeper Option B expansion (Cloudflare edge/webhook routing)
- Consider advanced tenancy and analytics scaling patterns

### Option B vs C Operating Rule (Locked)
- **Now**: Run Option C (fastest, lowest execution risk)
- **Incremental**: Pull in Option B components only when they reduce cost/toil without forcing platform rewrite
- **Later**: pursue broader architecture improvements when revenue and usage justify complexity

### Cost Viability Checkpoints (Decision Gates)
- Infra spend % of monthly revenue
- Cost per active trip / per completed booking
- On-call/ops hours per week
- P95 API latency and error rate trend

If checkpoints remain healthy, do not introduce architecture complexity.
If checkpoints degrade beyond agreed thresholds, escalate to architecture uplift planning.

### Decision Status
- Cost-first execution confirmed.
- Architecture evolution is explicitly staged behind viability checkpoints.
- Documentation-first discipline maintained for all tradeoff decisions.
