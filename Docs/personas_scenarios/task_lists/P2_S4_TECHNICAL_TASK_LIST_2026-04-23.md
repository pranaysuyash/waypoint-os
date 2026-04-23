# P2-S4 Technical Task List (Open)

- Scenario: `P2-S4` Training Time Problem
- Date: 2026-04-23
- Source evidence:
  - `Docs/reports/P2_TRAINING_TIME_PROBLEM_OBSERVABILITY_2026-04-23.md`
  - `Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md`

## Open Items

| ID | Priority | Status | Task | Why It Matters | Evidence Anchor |
|---|---|---|---|---|---|
| P2S4-T-01 | P0 | Closed (verified 2026-04-23) | Migrate `jest.mock` usage to vitest-compatible mocking in `DecisionPanel.SuitabilitySignal.integration.test.tsx` | Integration suite currently fails before assertions (`jest is not defined`) | `DecisionPanel.SuitabilitySignal.integration.test.tsx` now uses vitest mocks; suite pass |
| P2S4-T-02 | P0 | Closed (verified 2026-04-23) | Rebaseline `SuitabilitySignal.test.tsx` expectations to current rendered copy/labels | 8 assertion failures hide real regressions | `SuitabilitySignal.test.tsx` suite pass (28/28) |
| P2S4-T-03 | P0 | Closed (verified 2026-04-23) | Rebaseline `SuitabilityPanel.test.tsx` acknowledgment/continue flow expectations | 6 assertion failures weaken safe-send gating confidence | `SuitabilityPanel.test.tsx` suite pass (13/13) |
| P2S4-T-04 | P1 | Closed (verified 2026-04-23) | Add owner-review onboarding E2E flow (`junior quote -> warnings -> owner decision`) | Current coverage is partial and not true journey-level | `frontend/src/app/__tests__/p2_owner_onboarding_journey.test.tsx` pass (5/5) |
| P2S4-T-05 | P1 | Closed (verified 2026-04-23) | Add BE regression test mapping confidence thresholds to owner-facing coaching severity | Lock policy and avoid confidence/UX drift | `tests/test_p1_backend_regressions.py::TestConfidenceToCoachingSeverity` pass |

## Verification Snapshot (2026-04-23)

- `cd frontend && npm test -- --run src/components/workspace/panels/__tests__/DecisionPanel.SuitabilitySignal.integration.test.tsx src/components/workspace/panels/__tests__/SuitabilitySignal.test.tsx src/components/workspace/panels/__tests__/SuitabilityPanel.test.tsx` -> `54 passed`
- `cd frontend && npm test -- --run src/app/__tests__/p2_owner_onboarding_journey.test.tsx` -> `5 passed`
- `uv run pytest -q tests/test_p1_backend_regressions.py` -> passed (includes confidence->coaching severity contract tests)
