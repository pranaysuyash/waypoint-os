# P1-S0: Solo Agent Happy Path

**Persona**: Solo Agent (the one-person travel agency)
**Scenario**: The agent wants to process the next incoming trip request quickly, reliably, and without switching between multiple tools.

---

## Situation

A solo travel agent is working a busy morning.
A new customer request has arrived and the agent wants to move it from inbox to proposal as quickly as possible.
The agent is under time pressure and needs the system to behave like a real assistant, not just a collection of pages.

## Goal

Move one trip from inbound request to review-ready proposal in a single coherent flow.
The agent should feel like they are opening a file, processing it, and getting a useful customer-facing package without reinventing the work.

## User flow

### 1. Homepage / dashboard
- Agent opens the app and lands on the homepage.
- They expect to see a snapshot of active work: urgent trips, current pipeline status, and a clear path to the inbox.
- The agent decides which request to work on next.

### 2. Open the inbox
- The agent clicks `Inbox`.
- The inbox shows trip cards with destination, party size, dates, priority/SLA status, and a quick summary.
- The agent expects to see the next request at the top and the ability to open it immediately.

### 3. Select the trip
- The agent clicks the trip card for the request they want to handle.
- The app opens the trip workspace for that exact request.
- The agent expects the workspace to already show the trip reference, destination, and current status.

### 4. Review trip details
- In the workspace, the agent reviews the loaded trip details.
- The trip should display the customer message, party composition, travel window, budget, and any special notes.
- The agent expects no blank screen and no additional manual loading.

### 5. Add or confirm input
- The agent pastes or types the incoming customer note into the “Customer Message” field.
- They add any internal context in “Agent Notes”.
- The agent expects the system to keep this input visible and editable.

### 6. Choose the right mode
- The agent selects the request type:
  - normal request
  - audit
  - emergency
  - cancellation
- The agent expects the selected mode to affect the analysis and output.

### 7. Process the trip
- The agent clicks `Process Trip` or the equivalent action.
- The agent expects the system to analyze the request and return results quickly.
- The app should show progress and then populate downstream sections.

### 8. Inspect pipeline results
- The agent moves through the workspace sections:
  - Trip details / intake packet
  - Decision recommendation
  - Strategy bundle
  - Safety review / traveler-safe output
- The agent expects each section to show real output from the analysis, not placeholders.

### 9. Prepare customer output
- The agent reviews the proposed customer-facing message and the internal summary.
- They expect the customer message to be clean, safe, and aligned with the customer request.
- They expect the internal notes to capture the decision rationale and any follow-up questions.

### 10. Finish and move on
- The agent saves or marks the trip as ready.
- They expect to return to the inbox and handle the next request without losing the previous work.

## Success criteria

The scenario is successful if:
- The agent can open the next request from the inbox.
- The exact trip loads immediately in the workspace.
- The agent can enter or confirm the customer note and agent notes.
- The selected mode is respected.
- Clicking the process button returns structured results.
- The packet, decision, strategy, and safety sections are populated.
- The agent can review the traveler-facing output.
- The agent does not need to switch out of the app or manually stitch results.

## System behaviors required

- **Trip selection persistence**: Inbox click opens the right trip, not a blank workspace.
- **Trip context loading**: Workspace must hydrate the selected trip immediately.
- **Input capture**: Customer and agent notes must stay editable and connected to the processing action.
- **Mode-aware processing**: Request mode must influence the pipeline.
- **Pipeline execution**: The system must run the analysis and return results.
- **Result visibility**: Downstream sections must render actual output.
- **Review-ready output**: The traveler message and internal notes must be usable.

## Why this matters

This scenario is the closest thing to the product’s core promise:
helping a solo agent move from inbound request to a usable proposal in one flow.
If this narrative breaks, the product feels like a prototype instead of a working tool.

## Layman Explanation (Non-Technical)

Think of this as one full "customer request handling" cycle for a solo travel agent.

- What the agent gives the system:
  - A customer request message (often messy/incomplete).
  - Optional internal notes.
  - A mode like normal, emergency, audit, or cancellation.
- What the system does in the middle:
  - Reads the message and pulls out usable facts.
  - Marks what is unclear or missing.
  - Decides if it should ask follow-up questions or proceed.
  - Builds two outputs: one customer-safe and one internal.
- What the agent gets back:
  - A clear recommendation.
  - A customer-ready response draft.
  - Internal rationale and next actions.

In simple terms: `inbox request -> system organizes + decides -> ready-to-use response package`.

---

## Case Study Execution (2026-04-23)

### Run intent
- Execute this scenario as a user-facing case study, not only as unit coverage.
- Capture expected input, intermediate system behavior, output quality, runtime, dependencies, and known unknowns.
- Produce actionable FE/BE correction targets tied to this scenario flow.

### Scenario I/P → Intermediate → O/P (as tested)

#### Input (user-side)
- Messy inbound travel request (destination alternatives, date window, budget range/flexibility, party constraints).
- Agent context notes.
- Selected processing mode (`normal_intake`, `audit`, `emergency`, `cancellation`).

#### Intermediate (system-side)
- Canonical packet extraction (facts, ambiguities, contradictions, unknowns).
- Decision engine routing (`ASK_FOLLOWUP` / proceed states, blockers, follow-up priorities).
- Strategy and safety generation (traveler-safe + internal bundle).
- Timeline/audit events for run observability.

#### Output (user-side)
- Structured recommendation and follow-up prompts.
- Traveler-safe message for customer.
- Internal notes/rationale for agent.
- Timeline visibility of stage transitions.

### Execution evidence
- Case study report:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/P1_SINGLE_AGENT_HAPPY_PATH_OBSERVABILITY_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/reports/P1_SINGLE_AGENT_HAPPY_PATH_OBSERVABILITY_2026-04-23.md)
- Raw backend evidence:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_backend_pytest_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_backend_pytest_2026-04-23.xml)
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_edge_modes_pytest_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_edge_modes_pytest_2026-04-23.xml)
- Raw frontend evidence:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_frontend_vitest_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_frontend_vitest_2026-04-23.json)
- Compact summary:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_observability_summary_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_observability_summary_2026-04-23.json)

### Key findings from this run
- Backend/Frontend targeted matrix executed for this scenario mapping.
- A high-signal timeline contract mismatch was detected (event `state` field shape drift).
- Core packet/decision/strategy/safety behavior is broadly healthy for this scenario family.
- Full UI journey continuity (inbox click → workspace process → save/return inbox) still needs explicit E2E proof.

### Dependencies and external requirements observed
- Local Python + pytest runtime (`uv`), frontend vitest runtime (`npm`).
- Local audit/timeline persistence path for event retrieval.
- No mandatory external network dependency for the executed case-study runs.
- Optional LLM enrichment can alter risk detail quality if enabled, but core flow runs without it.

### FE/BE correction hooks (scenario-specific)
- FE:
  - Add full user-journey E2E for this exact flow (inbox to completion and return).
  - Validate mode selector → process API payload coupling with integration assertions.
- BE:
  - Resolve timeline event schema mismatch (`state` shape consistency across emitter/tests/consumer).
  - Continue tightening ambiguity treatment for alternative destinations under hard-blocker logic.

### Open task lists (scenario-specific)
- Technical tasks:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_TECHNICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_TECHNICAL_TASK_LIST_2026-04-23.md)
- Logical tasks:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_LOGICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_LOGICAL_TASK_LIST_2026-04-23.md)

### Scenario execution registry
- This scenario’s execution entry is tracked in:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/CASE_STUDY_EXECUTION_LOG.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/CASE_STUDY_EXECUTION_LOG.md)

### Completion update (same-day follow-through)
- Contract mismatch fix completed:
  - Timeline stage events now carry a flat `details.state` while preserving `pre_state`/`post_state`.
  - Timeline API fallback logic supports both flat and nested state reads.
- True journey test completed:
  - Added executable frontend journey coverage for `inbox -> workspace process -> return link`.
  - New test file:
    - [/Users/pranay/Projects/travel_agency_agent/frontend/src/app/__tests__/p1_happy_path_journey.test.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/__tests__/p1_happy_path_journey.test.tsx)
- Reusable runbook script added:
  - [/Users/pranay/Projects/travel_agency_agent/tools/run_p1_happy_path_case_study.sh](/Users/pranay/Projects/travel_agency_agent/tools/run_p1_happy_path_case_study.sh)

### Follow-through evidence (post-fix)
- Backend (contract + scenario checks): all pass
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_backend_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_backend_2026-04-23.xml)
- Backend (mode edges): all pass
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_modes_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_modes_2026-04-23.xml)
- Frontend (journey + panels): all pass
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_frontend_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_frontend_2026-04-23.json)

### Logical Policy Ratification (2026-04-23)

- Ratified policy reference:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/LOGICAL_POLICY_DECISIONS_RATIFIED_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/LOGICAL_POLICY_DECISIONS_RATIFIED_2026-04-23.md)
- Implementation note:
  - Ready-gate policy is enforced through the existing canonical `PATCH /trips/{trip_id}` path (no parallel route).
  - Intake UI now exposes mark-ready flow with explicit ready-gate failure reasons for operators.
