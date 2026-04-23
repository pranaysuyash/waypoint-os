# Scenario Case Study Replication Playbook

Purpose: give any agent a repeatable method to run a scenario end-to-end, capture full observability, and produce user-facing documentation that drives FE/BE corrections.

## When to use this

Use this playbook when asked to:
- test a scenario deeply
- run a scenario as a case study
- document i/p, intermediate states, and o/p
- capture dependencies, external requirements, runtime, edge cases, and unknowns

## Non-negotiable outputs per scenario

For each scenario run, produce all five artifacts:
1. Scenario doc update in `Docs/personas_scenarios/<SCENARIO_FILE>.md`
2. Observability report in `Docs/reports/<SCENARIO_ID>_OBSERVABILITY_<DATE>.md`
3. Execution-log row in `Docs/personas_scenarios/CASE_STUDY_EXECUTION_LOG.md`
4. Scenario technical task list in `Docs/personas_scenarios/task_lists/<SCENARIO_ID>_TECHNICAL_TASK_LIST_<DATE>.md`
5. Scenario logical task list in `Docs/personas_scenarios/task_lists/<SCENARIO_ID>_LOGICAL_TASK_LIST_<DATE>.md`

Also generate machine evidence artifacts (XML/JSON) and link them from docs.

## Required sections in docs

Every scenario doc and report must include:
- Scenario i/p -> intermediate -> o/p
- Test inventory (what was tested)
- Edge case matrix (pass/fail + risk)
- Dependencies and external requirements
- Runtime/time taken
- Findings and correction hooks (FE and BE)
- Unknowns and uncovered risks
- Layman explanation (non-technical user story)
- Evidence links (commands + output artifacts)
- Open technical implementation items (scenario-specific)
- Open logical/product items (scenario-specific)

## Standard method (replicable steps)

### Step 1: Lock scope and source
- Pick one scenario doc from `Docs/personas_scenarios/`.
- Confirm scenario ID and exact path.
- Capture test date in ISO format (for example `2026-04-23`).

### Step 2: Map scenario to executable surfaces
Map scenario steps to concrete test surfaces:
- Backend pipeline tests under `tests/`
- Frontend component/integration tests under `frontend/src/**/__tests__/`
- Existing E2E journey tests if present
- API contracts and timeline/audit checks

Use these references for mapping:
- `Docs/personas_scenarios/SCENARIOS_TO_PIPELINE_MAPPING.md`
- `Docs/personas_scenarios/TEST_IDENTIFICATION_STRATEGY.md`
- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`

### Step 3: Build scenario-specific command set
Prepare explicit commands per layer:
- Backend targeted suite
- Backend edge/mode suite
- Frontend targeted suite
- Journey/E2E suite (if available)

Rules:
- Avoid broad test runs when scenario-targeted runs exist.
- Prefer deterministic test subsets linked to scenario behavior.
- Emit XML/JSON artifacts into `Docs/reports/`.

### Step 4: Execute and collect observability
For each command, capture:
- command string
- pass/fail counts
- slowest tests
- key failure messages
- generated artifact paths

Capture timing:
- per suite runtime
- notable slow test durations
- total scenario validation runtime

### Step 5: Analyze with user-journey lens
Extract findings across this chain:
- input capture
- intermediate transformation/decision
- output readiness
- completion continuity (save/return)

Flag clearly:
- contract mismatches
- missing E2E continuity proof
- frontend/backend coupling gaps
- any user-visible regression risk

### Step 6: Fix critical blockers when in implementation mode
If user expects execution (not just planning):
- implement high-signal fixes found in Step 5
- add missing journey tests where feasible
- rerun impacted suites
- replace stale evidence with post-fix artifacts

### Step 7: Document case study outputs
Update scenario doc with:
- execution summary
- i/p -> intermediate -> o/p
- dependencies/external requirements
- FE/BE correction hooks
- links to scenario-specific technical and logical task lists
- layman explanation
- post-fix follow-through evidence

Create/update observability report with:
- detailed step coverage matrix
- edge-case matrix
- runtime table
- commands and artifact links

Append execution log row with:
- scenario ID, date, status
- user-facing report link
- code evidence links
- task-list links (technical + logical)
- one crisp key finding

### Step 8: Verify documentation quality
Before closing, verify docs answer these user-level questions:
- What did we test exactly?
- What was expected input/output?
- What happened in the middle?
- What failed and why?
- What was fixed and re-tested?
- What still remains unknown?
- Can a non-technical stakeholder understand this?

## Execution checklist

- [ ] Scenario path and ID confirmed
- [ ] Scenario-to-test mapping completed
- [ ] Backend targeted suite executed
- [ ] Backend edge suite executed
- [ ] Frontend targeted suite executed
- [ ] Journey/E2E coverage executed or explicitly marked missing
- [ ] Artifacts generated under `Docs/reports/`
- [ ] Runtime and slow tests captured
- [ ] Findings classified by FE/BE
- [ ] Critical blockers fixed (if implementation mode)
- [ ] Post-fix rerun evidence captured
- [ ] Scenario doc updated
- [ ] Observability report updated
- [ ] Execution log updated
- [ ] Layman explanation present in docs
- [ ] Technical task list created/updated for this scenario
- [ ] Logical task list created/updated for this scenario

## Naming and file conventions

Use these conventions:
- Report: `Docs/reports/<SCENARIO_ID>_OBSERVABILITY_<YYYY-MM-DD>.md`
- Backend XML: `Docs/reports/<scenario_key>_backend_<YYYY-MM-DD>.xml`
- Modes XML: `Docs/reports/<scenario_key>_modes_<YYYY-MM-DD>.xml`
- Frontend JSON: `Docs/reports/<scenario_key>_frontend_<YYYY-MM-DD>.json`

Where `<scenario_key>` is lowercase snake case.

## Agent handoff prompt pointer

Use this ready prompt:
- `.agent/prompts/SCENARIO_CASE_STUDY_REPLICATION_PROMPT.md`

Use this skill instruction bundle:
- `.agent/skills/scenario_case_study_replication/SKILL.md`

Use this report template:
- `Docs/personas_scenarios/templates/SCENARIO_CASE_STUDY_REPORT_TEMPLATE.md`
