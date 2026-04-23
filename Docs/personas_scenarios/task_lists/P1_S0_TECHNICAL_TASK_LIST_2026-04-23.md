# P1-S0 Technical Task List (Open)

- Scenario: `P1-S0` Solo Agent Happy Path
- Date: 2026-04-23
- Source evidence:
  - `Docs/reports/P1_SINGLE_AGENT_HAPPY_PATH_OBSERVABILITY_2026-04-23.md`
  - `Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md`

## Open Items

| ID | Priority | Status | Task | Why It Matters | Evidence Anchor |
|---|---|---|---|---|---|
| P1S0-T-01 | P1 | Closed (verified 2026-04-23) | Add explicit integration test for mode selector -> `/api/spine/run` payload (`operating_mode`) | Prevent silent FE->BE mode drift during processing | `frontend/src/app/__tests__/mode_selector_spine_payload.test.tsx` (10/10 pass) |
| P1S0-T-02 | P1 | Closed (verified 2026-04-23) | Tighten NB02 ambiguity handling for destination values like `"A or B"` | Avoid premature proceed behavior on unresolved destination intent | `tests/test_p1_backend_regressions.py::TestDestinationAmbiguityTightening` (7/7 pass) |
| P1S0-T-03 | P1 | Closed (verified 2026-04-23) | Clarify and encode last-minute non-emergency soft-blocker behavior | Reduce inconsistent urgency routing outcomes | `tests/test_p1_backend_regressions.py::TestLastMinuteSoftBlockerBehavior` (7/7 pass) |
| P1S0-T-04 | P2 | Closed (verified 2026-04-23) | Replace malformed placeholder `frontend/src/components/workspace/panels/__tests__/OverrideModal.test.tsx` with valid TSX/RTL tests | Restore trust in override-path regression coverage | `cd frontend && npm test -- --run src/components/workspace/panels/__tests__/OverrideModal.test.tsx` (5/5 pass) |

## Already Closed in this Scenario

| Item | Status |
|---|---|
| Timeline `details.state` contract mismatch | Closed |
| Inbox -> workspace -> process -> return journey test | Closed |
| Reusable P1 case-study runbook script | Closed |

## Verification Snapshot (2026-04-23)

- `uv run pytest -q tests/test_timeline_e2e.py::test_spine_run_emits_audit_events tests/test_p1_backend_regressions.py` -> `25 passed`
- `cd frontend && npm test -- --run src/app/__tests__/p1_happy_path_journey.test.tsx src/app/__tests__/mode_selector_spine_payload.test.tsx` -> passed
- `cd frontend && npm test -- --run src/components/workspace/panels/__tests__/IntakePanel.test.tsx` -> `4 passed` (includes ready-gate error surfacing UX)
- `bash tools/run_p1_happy_path_case_study.sh` -> passed (backend + frontend case-study suites)

## Completion Note

Remaining open technical item (`P1S0-T-04`) has been implemented and verified:
- `cd frontend && npm test -- --run src/components/workspace/panels/__tests__/OverrideModal.test.tsx` -> `5 passed`


## Current Open Technical Items

- None.
