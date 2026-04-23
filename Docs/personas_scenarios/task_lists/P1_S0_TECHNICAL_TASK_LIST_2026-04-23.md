# P1-S0 Technical Task List (Open)

- Scenario: `P1-S0` Solo Agent Happy Path
- Date: 2026-04-23
- Source evidence:
  - `Docs/reports/P1_SINGLE_AGENT_HAPPY_PATH_OBSERVABILITY_2026-04-23.md`
  - `Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md`

## Open Items

| ID | Priority | Status | Task | Why It Matters | Evidence Anchor |
|---|---|---|---|---|---|
| P1S0-T-01 | P1 | Open | Add explicit integration test for mode selector -> `/api/spine/run` payload (`operating_mode`) | Prevent silent FE->BE mode drift during processing | FE correction targets in observability report |
| P1S0-T-02 | P1 | Open | Tighten NB02 ambiguity handling for destination values like `"A or B"` | Avoid premature proceed behavior on unresolved destination intent | Edge-case matrix ambiguity note |
| P1S0-T-03 | P1 | Open | Clarify and encode last-minute non-emergency soft-blocker behavior | Reduce inconsistent urgency routing outcomes | Edge-case matrix urgency mixed result |
| P1S0-T-04 | P2 | Open | Replace malformed placeholder `frontend/src/components/workspace/panels/__tests__/OverrideModal.test.tsx` with valid TSX/RTL tests | Restore trust in override-path regression coverage | Unknown/gap section in observability report |

## Already Closed in this Scenario

| Item | Status |
|---|---|
| Timeline `details.state` contract mismatch | Closed |
| Inbox -> workspace -> process -> return journey test | Closed |
| Reusable P1 case-study runbook script | Closed |
