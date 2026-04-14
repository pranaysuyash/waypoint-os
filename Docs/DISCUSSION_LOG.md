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
