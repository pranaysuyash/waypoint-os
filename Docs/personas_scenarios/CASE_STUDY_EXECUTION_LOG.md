# Scenario Case Study Execution Log

Purpose: scenario-wise reference log that links each scenario doc to its latest user-facing case-study output and code-backed execution evidence.

Method reference for future agents:
- Scenario replication playbook:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIO_CASE_STUDY_REPLICATION_PLAYBOOK.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIO_CASE_STUDY_REPLICATION_PLAYBOOK.md)
- Agent prompt:
  - [/Users/pranay/Projects/travel_agency_agent/.agent/prompts/SCENARIO_CASE_STUDY_REPLICATION_PROMPT.md](/Users/pranay/Projects/travel_agency_agent/.agent/prompts/SCENARIO_CASE_STUDY_REPLICATION_PROMPT.md)
- Skill instruction:
  - [/Users/pranay/Projects/travel_agency_agent/.agent/skills/scenario_case_study_replication/SKILL.md](/Users/pranay/Projects/travel_agency_agent/.agent/skills/scenario_case_study_replication/SKILL.md)
- Report template:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/templates/SCENARIO_CASE_STUDY_REPORT_TEMPLATE.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/templates/SCENARIO_CASE_STUDY_REPORT_TEMPLATE.md)

| Scenario ID | Scenario Doc | Last Run Date | Status | User-Facing Case Study | Code Evidence | Open Task Lists | Key Finding |
|---|---|---|---|---|---|---|---|
| P1-S0 | [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md) | 2026-04-23 | Completed (fix + rerun) | [/Users/pranay/Projects/travel_agency_agent/Docs/reports/P1_SINGLE_AGENT_HAPPY_PATH_OBSERVABILITY_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/reports/P1_SINGLE_AGENT_HAPPY_PATH_OBSERVABILITY_2026-04-23.md) | [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_backend_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_backend_2026-04-23.xml), [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_modes_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_modes_2026-04-23.xml), [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_frontend_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_frontend_2026-04-23.json) | [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_TECHNICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_TECHNICAL_TASK_LIST_2026-04-23.md), [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_LOGICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_LOGICAL_TASK_LIST_2026-04-23.md) | Timeline state contract fixed; journey test added and passing |
| P2-S4 | [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md) | 2026-04-23 | Completed (evidence run; FE gaps found) | [/Users/pranay/Projects/travel_agency_agent/Docs/reports/P2_TRAINING_TIME_PROBLEM_OBSERVABILITY_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/reports/P2_TRAINING_TIME_PROBLEM_OBSERVABILITY_2026-04-23.md) | [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml), [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json), [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_observability_summary_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_observability_summary_2026-04-23.json) | [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_TECHNICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_TECHNICAL_TASK_LIST_2026-04-23.md), [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_LOGICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_LOGICAL_TASK_LIST_2026-04-23.md) | Backend confidence path is stable; frontend coaching tests are failing with copy drift and `jest`/`vitest` mismatch |

## Update Protocol (for future scenario runs)

1. Append one row per scenario execution date.
2. Keep both links:
- user-facing case-study markdown report
- code evidence JSON/XML summary
3. Add links to both scenario task lists:
- technical task list
- logical task list
4. Record one crisp key finding that drives FE/BE change.
