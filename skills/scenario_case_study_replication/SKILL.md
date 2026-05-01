# Skill: Scenario Case Study Replication

## Purpose

Run a scenario as a full user-facing case study with deep observability and reproducible evidence.

## Use this when

- user asks to test a scenario in detail
- user asks for i/p, intermediate, o/p documentation
- user asks for edge-case coverage and timing
- user asks for FE/BE correction-ready findings

## Primary references

- Playbook: `Docs/personas_scenarios/SCENARIO_CASE_STUDY_REPLICATION_PLAYBOOK.md`
- Prompt: `.agent/prompts/SCENARIO_CASE_STUDY_REPLICATION_PROMPT.md`
- Template: `Docs/personas_scenarios/templates/SCENARIO_CASE_STUDY_REPORT_TEMPLATE.md`

## Workflow

1. Select one scenario file and lock scenario ID/date.
2. Map scenario steps to executable backend/frontend/journey tests.
3. Run targeted suites and output XML/JSON evidence in `Docs/reports/`.
4. Capture runtime, slowest tests, and failures.
5. Write analysis as i/p -> intermediate -> o/p.
6. Classify findings into FE and BE correction hooks.
7. If in implementation mode, patch issues and rerun impacted tests.
8. Create/update separate scenario task lists (technical + logical).
9. Update scenario doc, report doc, and execution log.

## Mandatory sections in final docs

- Layman explanation
- input/intermediate/output chain
- step coverage
- edge cases
- dependencies/external requirements
- runtime/time taken
- unknowns/residual risk
- evidence artifacts
- open technical task list link
- open logical task list link

## Anti-patterns

- generic summaries with no run evidence
- only code-centric findings without user impact
- no runtime or dependency details
- no layman explanation section
- no execution log update
- no separate technical/logical task lists
- parallel policy implementations across duplicate paths/routes
