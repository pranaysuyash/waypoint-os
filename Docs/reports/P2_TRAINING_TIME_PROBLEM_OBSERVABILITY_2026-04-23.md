# P2 Training Time Problem - Deep Observability Report

- Date: 2026-04-23
- Scenario source: [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md)
- Mapping sources:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIOS_TO_PIPELINE_MAPPING.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIOS_TO_PIPELINE_MAPPING.md)
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/TEST_IDENTIFICATION_STRATEGY.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/TEST_IDENTIFICATION_STRATEGY.md)
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md)

## Layman Explanation (User Case Study View)

This case study checks if a junior agent can be guided by the system in real time, so the owner spends less time on manual training and correction.

- Expected input:
  - Junior agent builds quote with incomplete confidence.
  - Owner expects quality checks and coaching signals.
- Expected middle behavior:
  - System scores confidence and routes safe next action.
  - System explains risk and flags issues before send.
- Expected output:
  - Junior gets clear coaching.
  - Owner sees confidence/risk view and can intervene early.

## Scope Clarification

- Scenario selected: `P2-S4 The Training Time Problem`
- This run validates executable parts of P2-S4 currently implemented in NB02/NB03 and frontend suitability/coaching UI tests.
- It does not claim complete owner dashboard or longitudinal training analytics coverage.

## Scenario I/P -> Intermediate -> O/P

### Input (user side)
- Junior-agent quote-building context with varying confidence.
- Owner review/audit mode context.
- Suitability flags for coaching and risk signaling.

### Intermediate (system side)
- NB02 owner review + audit-mode decision structures.
- NB03 confidence tone mapping (`cautious` vs `direct`) and assumptions behavior.
- Frontend rendering/interaction for SuitabilitySignal and SuitabilityPanel.

### Output (user side)
- Backend decisioning path returns stable confidence/governance behavior.
- Frontend coaching surfaces have significant test-contract drift.
- Training scenario is partially validated; UX layer requires hardening.

## Executed Test Evidence

### Backend targeted suite
Command:
```bash
uv run pytest -vv --durations=0 --junitxml Docs/reports/p2_training_problem_backend_2026-04-23.xml \
  tests/test_nb02_v02.py::TestOwnerReviewAudit::test_owner_review_mode \
  tests/test_nb02_v02.py::TestOwnerReviewAudit::test_audit_mode_adds_feasibility_contradiction \
  tests/test_nb02_v02.py::TestDecisionResultStructure::test_decision_result_has_all_fields \
  tests/test_nb03_v02.py::TestInternalDraftAssumptions::test_soft_blockers_listed_as_assumptions \
  tests/test_nb03_v02.py::TestToneScaling::test_low_confidence_cautious_tone \
  tests/test_nb03_v02.py::TestToneScaling::test_high_confidence_direct_tone
```

Result:
- Total: 6
- Passed: 6
- Failed: 0
- Runtime (pytest): `0.70s`
- Runtime (wall): `1.19s`
- Slowest: `test_owner_review_mode` (`~0.56s`)

Artifacts:
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_timing_2026-04-23.txt](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_timing_2026-04-23.txt)

### Frontend targeted suite
Command:
```bash
cd frontend
npm test -- --run --reporter=verbose --reporter=json \
  --outputFile=../Docs/reports/p2_training_problem_frontend_2026-04-23.json \
  src/components/workspace/panels/__tests__/DecisionPanel.SuitabilitySignal.integration.test.tsx \
  src/components/workspace/panels/__tests__/SuitabilitySignal.test.tsx \
  src/components/workspace/panels/__tests__/SuitabilityPanel.test.tsx
```

Result:
- Files: 3 suites (all failed at suite level)
- Tests: 41 assertions
- Passed: 27
- Failed: 14
- Runtime (vitest): `1.10s`
- Runtime (wall): `1.51s`
- Critical setup failure: `DecisionPanel.SuitabilitySignal.integration.test.tsx` failed with `jest is not defined` (0 assertions executed)

Artifacts:
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_timing_2026-04-23.txt](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_timing_2026-04-23.txt)

## Step Coverage Matrix

| Step | Expected Behavior | Evidence | Status | Gap |
|---|---|---|---|---|
| 1 Guided workflows | Junior gets structured step support | NB02 owner-review + decision structure tests pass | Partial | No full clickflow onboarding E2E |
| 2 Just-in-time coaching | Risky choices flagged before send | Suitability panel/signal suites executed | Partial (failing) | 14 frontend assertions failing on text/interaction contracts |
| 3 Decision support | Confidence-based next action and rationale | NB03 tone + assumptions tests pass | Covered (backend) | FE projection of these signals unstable |
| 4 Performance feedback | Confidence visible and actionable to owner | Suitability/decision panel tests targeted | Partial | Integration suite setup broken (`jest` in vitest) |

## Edge Case Matrix

| Edge Case | Source | Evidence | Result | Notes |
|---|---|---|---|---|
| Owner review mode structure | P2-S4 mapping + NB02 | `TestOwnerReviewAudit::test_owner_review_mode` | Pass | Stable owner-review decision behavior |
| Audit contradiction handling | P2-S4/owner quality review | `test_audit_mode_adds_feasibility_contradiction` | Pass | Audit branch active |
| Low-confidence cautious tone | Training/coaching behavior | `TestToneScaling::test_low_confidence_cautious_tone` | Pass | Confidence->tone policy works |
| High-confidence direct tone | Training/coaching behavior | `TestToneScaling::test_high_confidence_direct_tone` | Pass | High-confidence messaging tone works |
| Soft blocker assumptions | Junior guidance uncertainty | `TestInternalDraftAssumptions::test_soft_blockers_listed_as_assumptions` | Pass | Assumptions path present |
| FE integration framework compatibility | UI coaching integration | `DecisionPanel.SuitabilitySignal.integration.test.tsx` | Fail | `jest is not defined` under vitest |
| FE copy/label contracts | User-visible warnings and counts | `SuitabilitySignal.test.tsx` failing assertions | Fail | Rendered text differs from test expectations |
| FE acknowledgment/continue flow | Safe-send gating for juniors | `SuitabilityPanel.test.tsx` failing assertions | Fail | Behavior/text contract drift in continue flow tests |

## Dependencies and External Requirements

- Python + `uv` + pytest for backend coverage.
- Node/npm + vitest + RTL for frontend coaching/suitability coverage.
- Local repo test fixtures and component contracts.
- No mandatory external network dependency for this run.
- Agents used: none.

## Timing Summary

- Backend targeted suite wall runtime: `1.19s`
- Frontend targeted suite wall runtime: `1.51s`
- Total measured wall runtime: `2.70s`

## Findings

### FE correction hooks
1. Replace `jest.mock` usage in `vitest` test path for `DecisionPanel.SuitabilitySignal.integration.test.tsx` (`vi.mock` migration).
2. Rebaseline `SuitabilitySignal.test.tsx` assertions to current rendered copy/phrasing.
3. Rebaseline `SuitabilityPanel.test.tsx` acknowledge/continue expectations to current component semantics.
4. Add one owner-review onboarding E2E flow to prove junior guidance continuity in UI.

### BE correction hooks
1. No blocker in sampled training-path backend behavior.
2. Add one explicit regression tying confidence score thresholds to owner-visible coaching severity levels.

## Open Task Lists

- Technical:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_TECHNICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_TECHNICAL_TASK_LIST_2026-04-23.md)
- Logical:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_LOGICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_LOGICAL_TASK_LIST_2026-04-23.md)

## Unknowns and Residual Risk

- No real end-to-end owner dashboard flow executed in browser for this scenario.
- Current frontend failures may represent either intended UX copy changes or regressions; the suite cannot currently distinguish reliably.
- Integration suite setup break (`jest`/`vitest`) masks potential deeper UI integration defects.

## Artifacts Produced

- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_timing_2026-04-23.txt](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_timing_2026-04-23.txt)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_timing_2026-04-23.txt](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_timing_2026-04-23.txt)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_observability_summary_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_observability_summary_2026-04-23.json)
