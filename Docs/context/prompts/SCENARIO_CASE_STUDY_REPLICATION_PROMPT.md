# Prompt: Scenario Case Study Replication

You are executing one scenario as a user-facing case study with full observability.

## Objective

For the selected scenario, produce verifiable evidence of:
- expected input
- intermediate system behavior
- expected and actual output
- dependencies/external requirements
- runtime
- edge cases
- findings and FE/BE correction hooks
- open technical implementation items
- open logical/product items

## Inputs you must receive first

- `SCENARIO_DOC_PATH`: absolute or repo-relative path under `Docs/personas_scenarios/`
- `SCENARIO_ID`: stable scenario id (for example `P1-S0`)
- `RUN_DATE`: ISO date (`YYYY-MM-DD`)

If any input is missing, derive it from the selected scenario file and state assumptions.

## Required execution method

1. Read scenario doc and mapping docs:
   - `Docs/personas_scenarios/SCENARIOS_TO_PIPELINE_MAPPING.md`
   - `Docs/personas_scenarios/TEST_IDENTIFICATION_STRATEGY.md`
   - `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`
2. Build scenario-specific backend + frontend + journey test command set.
3. Execute tests and capture XML/JSON artifacts under `Docs/reports/`.
4. Record pass/fail counts, slowest tests, failure details, timings.
5. Map results to user journey: i/p -> intermediate -> o/p.
6. Identify FE and BE correction hooks.
7. If implementation is in scope, fix high-signal gaps and rerun impacted suites.
8. Update scenario doc + observability report + execution log.
9. Create/update scenario-specific technical and logical task-list docs.

## Required outputs

### A) Scenario doc update
Update the selected scenario doc with:
- Case Study Execution section
- I/P -> Intermediate -> O/P section
- Dependencies and external requirements
- Findings and correction hooks
- Follow-through evidence (if fixes made)
- Layman Explanation section

### B) Observability report
Create or update:
`Docs/reports/<SCENARIO_ID>_OBSERVABILITY_<RUN_DATE>.md`

Must include:
- scope and test inventory
- command list
- pass/fail and runtime details
- step coverage matrix
- edge case matrix
- unknowns and residual risks
- FE/BE correction targets
- layman explanation section

### C) Execution log row
Append row in:
`Docs/personas_scenarios/CASE_STUDY_EXECUTION_LOG.md`

Row must include:
- scenario id
- scenario doc link
- run date
- status
- report link
- code evidence links
- one key finding

### D) Scenario task lists (separate and mandatory)
Create/update both:
- `Docs/personas_scenarios/task_lists/<SCENARIO_ID>_TECHNICAL_TASK_LIST_<RUN_DATE>.md`
- `Docs/personas_scenarios/task_lists/<SCENARIO_ID>_LOGICAL_TASK_LIST_<RUN_DATE>.md`

Each list must include:
- priority
- open/closed status
- concrete action/decision item
- reason (user impact)
- evidence anchor (for technical list)

## Guardrails

- Do not claim coverage without command evidence.
- Do not mark E2E complete unless journey continuity is explicitly tested.
- Keep all artifact paths explicit and clickable.
- Preserve existing docs/history; only append or update relevant sections.
- Keep one canonical route/contract; do not create duplicate API route files.
- Align implementation with ratified policy docs and product vision; do not split logic across parallel paths.

## Definition of done

Done only when all are true:
- scenario doc updated
- observability report updated
- execution log updated
- technical task list updated
- logical task list updated
- test artifacts linked
- layman explanation present
- remaining unknowns clearly listed
