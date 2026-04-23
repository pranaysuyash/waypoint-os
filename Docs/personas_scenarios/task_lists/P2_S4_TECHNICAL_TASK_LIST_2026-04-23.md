# P2-S4 Technical Task List (Open)

- Scenario: `P2-S4` Training Time Problem
- Date: 2026-04-23
- Source evidence:
  - `Docs/reports/P2_TRAINING_TIME_PROBLEM_OBSERVABILITY_2026-04-23.md`
  - `Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md`

## Open Items

| ID | Priority | Status | Task | Why It Matters | Evidence Anchor |
|---|---|---|---|---|---|
| P2S4-T-01 | P0 | Open | Migrate `jest.mock` usage to vitest-compatible mocking in `DecisionPanel.SuitabilitySignal.integration.test.tsx` | Integration suite currently fails before assertions (`jest is not defined`) | Frontend critical setup failure |
| P2S4-T-02 | P0 | Open | Rebaseline `SuitabilitySignal.test.tsx` expectations to current rendered copy/labels | 8 assertion failures hide real regressions | Frontend failure list |
| P2S4-T-03 | P0 | Open | Rebaseline `SuitabilityPanel.test.tsx` acknowledgment/continue flow expectations | 6 assertion failures weaken safe-send gating confidence | Frontend failure list |
| P2S4-T-04 | P1 | Open | Add owner-review onboarding E2E flow (`junior quote -> warnings -> owner decision`) | Current coverage is partial and not true journey-level | Step coverage matrix gap |
| P2S4-T-05 | P1 | Open | Add BE regression test mapping confidence thresholds to owner-facing coaching severity | Lock policy and avoid confidence/UX drift | BE correction hooks |
