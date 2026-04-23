# P1 Single Agent Happy Path - Deep Observability Report

- Date: 2026-04-23
- Scenario source: [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md)
- Mapping sources:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIOS_TO_PIPELINE_MAPPING.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIOS_TO_PIPELINE_MAPPING.md)
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/TEST_IDENTIFICATION_STRATEGY.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/TEST_IDENTIFICATION_STRATEGY.md)
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md)

## Scope Clarification

- Doc selected by user: `P1-S0: Solo Agent Happy Path` (10-step UX flow).
- Canonical pipeline doc maps closest backend behavior under `P1-S1: 11 PM WhatsApp Panic`.
- This report tests both:
  - UX flow capabilities implied by P1-S0.
  - Pipeline/decision edge behavior documented for P1-S1.

## Layman Explanation (User Case Study View)

This case study checks whether a solo travel agent can actually do their real daily job end-to-end in one product flow.

- Expected input:
  - Customer message (often not cleanly written).
  - Agent notes.
  - Chosen mode (normal/audit/emergency/cancellation).
- Expected middle behavior:
  - System extracts facts, flags unclear points, decides whether to continue or ask questions.
  - System tracks progress so the agent can see what happened.
- Expected output:
  - Customer-safe response draft.
  - Internal decision summary and follow-up list.
  - Confidence that the trip can be marked ready and the agent can move to the next inbox item.

What this report adds beyond pass/fail:
- Exactly what was tested and how long it took.
- What dependencies were required.
- Where flow risk existed, what was fixed, and what proof now exists.

## Scenario Steps (P1-S0)

1. Homepage/dashboard
2. Open inbox
3. Select trip
4. Review trip details
5. Add/confirm input
6. Choose mode
7. Process trip
8. Inspect pipeline results
9. Prepare customer output
10. Finish and move on

## Executed Test Evidence

### Backend targeted suite

Command:
```bash
uv run pytest -vv --durations=0 --junitxml Docs/reports/p1_single_agent_backend_pytest_2026-04-23.xml \
  tests/test_e2e_freeze_pack.py::TestScenario1_MessyFamilyDiscovery \
  tests/test_realworld_scenarios_v02.py::TestVagueLead::test_vague_lead_asks_followup_with_missing_blockers \
  tests/test_realworld_scenarios_v02.py::TestWhatsAppDump::test_whatsapp_dump_reveals_ambiguity_gap \
  tests/test_realworld_scenarios_v02.py::TestLastMinuteBooker::test_last_minute_booker_reveals_soft_blocker_gap \
  tests/test_realworld_scenarios_v02.py::TestStageProgressionScenarios::test_shortlist_asks_for_selected_destination \
  tests/test_realworld_scenarios_v02.py::TestStageProgressionScenarios::test_proposal_asks_for_selected_itinerary \
  tests/test_timeline_e2e.py::test_spine_run_emits_audit_events \
  tests/test_timeline_rest_endpoint.py::test_timeline_endpoint_response_structure \
  tests/test_timeline_rest_endpoint.py::test_timeline_endpoint_accepts_stage_filter
```

Result:
- Total: 13
- Passed: 12
- Failed: 1
- Slowest:
  - `0.456s` `TestScenario1_MessyFamilyDiscovery::test_extraction_from_messy_note`
  - `0.411s` `test_spine_run_emits_audit_events` (failed)

Failure (high signal):
- Test: `tests/test_timeline_e2e.py::test_spine_run_emits_audit_events`
- Assertion: expected `details.state` field in timeline event.
- Actual event shape uses `details.pre_state.state` and `details.post_state.state` + `details.description`.
- Impact: timeline contract drift between test expectation and emitted event schema.

Artifact:
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_backend_pytest_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_backend_pytest_2026-04-23.xml)

### Backend edge-mode suite

Command:
```bash
uv run pytest -vv --durations=0 --junitxml Docs/reports/p1_single_agent_edge_modes_pytest_2026-04-23.xml \
  tests/test_nb01_v02.py::TestOperatingModeTopLevel::test_emergency_mode \
  tests/test_nb02_v02.py::TestEmergencyMode::test_emergency_suppresses_soft \
  tests/test_nb02_v02.py::TestOwnerReviewAudit::test_audit_mode_adds_feasibility_contradiction \
  tests/test_nb03_v02.py::TestEmergencyMode::test_emergency_only_crisis_questions \
  tests/test_nb03_v02.py::TestModeSpecificGoals::test_audit_mode_goal_different_from_normal \
  tests/test_e2e_freeze_pack.py::TestScenario3_AuditModeSelfBooked::test_audit_mode_routing \
  tests/test_e2e_freeze_pack.py::TestScenario5_EmergencyCancellation::test_cancellation_mode_detected
```

Result:
- Total: 7
- Passed: 7
- Failed: 0
- Slowest: `0.422s` emergency mode detection at NB01 extraction layer.

Artifact:
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_edge_modes_pytest_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_edge_modes_pytest_2026-04-23.xml)

### Frontend targeted suite

Command:
```bash
cd frontend
npm test -- --run --reporter=verbose --reporter=json \
  --outputFile=../Docs/reports/p1_single_agent_frontend_vitest_2026-04-23.json \
  src/hooks/__tests__/useTrips.test.ts \
  src/components/workspace/panels/__tests__/IntakePanel.test.tsx \
  src/components/workspace/panels/__tests__/OutputPanel.test.tsx \
  src/components/workspace/panels/__tests__/TimelinePanel.test.tsx \
  'src/app/workspace/[tripId]/__tests__/layout.test.tsx' \
  src/contexts/__tests__/TripContext.test.tsx
```

Result:
- Files: 6
- Tests: 25
- Passed: 25
- Failed: 0
- Total assertion runtime: `0.568s`
- Slowest assertions:
  - `0.122s` workspace layout renders trip header + stage tabs
  - `0.089s` intake panel process/save buttons
  - `0.082s` output panel debug toggle

Artifact:
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_frontend_vitest_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_frontend_vitest_2026-04-23.json)

## P1-S0 Step Coverage Matrix

| Step | Expected Behavior | Evidence | Status | Gap |
|---|---|---|---|---|
| 1 Dashboard | Active work visible | `useTrips` hook API call tests | Partial | No explicit dashboard integration test with real trip cards ordering/SLA rendering |
| 2 Open inbox | Inbox list opens and loads | `useTrips` hook fetch + param/error handling | Partial | No inbox page clickflow test |
| 3 Select trip | Correct trip workspace opens | `workspace/[tripId]/layout` tests with `useParams` and trip load | Partial | No end-to-end click from inbox card to workspace route |
| 4 Review details | Trip details hydrate immediately | `IntakePanel` renders trip metadata and notes | Covered (component) | No backend/frontend hydration latency/SLA assertion |
| 5 Input capture | Customer/agent notes editable, persistent | `IntakePanel` state wiring tests | Covered (component) | No persistence roundtrip assertion to backend store |
| 6 Mode selection | Mode affects pipeline | NB01/NB02/NB03 mode tests + freeze pack audit/cancellation tests | Covered (backend) | Frontend mode selector integration to API payload not tested end-to-end |
| 7 Process trip | Runs analysis and returns output | Freeze pack + realworld + timeline/audit tests | Covered (backend) | No UI integration test for clicking Process and receiving run result payload |
| 8 Inspect results | Packet/decision/strategy/safety visible | `OutputPanel` + `TimelinePanel` tests | Covered (component) | No full-page staged traversal test |
| 9 Customer output | Traveler-safe + internal notes available | Freeze pack leakage tests + OutputPanel tests | Covered | No send/approve action test |
| 10 Finish/move on | Save/ready/back to inbox continuity | Save button presence only | Not covered | No completion-state + navigation handoff test |

## Edge Case Matrix (Doc + Coverage Gaps + Executed)

| Edge Case | Source | Test Evidence | Result | Notes |
|---|---|---|---|---|
| Messy WhatsApp extraction | Mapping P1-S1 | `TestScenario1_MessyFamilyDiscovery` | Pass | Extraction and packet population works |
| Hard blocker ASK_FOLLOWUP for vague lead | Mapping P1-S1 | `TestVagueLead` | Pass | Hard blockers enforced |
| Ambiguous destination string handling | Coverage gaps P0-1 | `TestWhatsAppDump` | Pass (known limitation encoded) | Behavior currently allows proceed with ambiguous value (documented gap) |
| Urgency soft blocker suppression | Coverage gaps P1-S1 | `TestLastMinuteBooker` + `TestEmergencyMode::test_emergency_suppresses_soft` | Mixed | Emergency mode suppresses; last-minute still shows soft-blocker routing tension |
| Stage progression discovery→shortlist→proposal | P1 process continuity | `TestStageProgressionScenarios` (2 tests) | Pass | Correct stage-specific blockers |
| Timeline event contract consistency | P1 process observability | `test_spine_run_emits_audit_events` | Fail | Event schema changed (`state` moved to `post_state.state`) |
| Timeline REST structure/filter | P1 workspace timeline view | `test_timeline_endpoint_response_structure`, `test_timeline_endpoint_accepts_stage_filter` | Pass | Endpoint shape stable at top-level |
| Audit mode routing | P1 mode behavior | NB02/NB03 + freeze pack audit tests | Pass | Audit path operational |
| Cancellation mode detection | P1 mode behavior | `TestScenario5_EmergencyCancellation::test_cancellation_mode_detected` | Pass | Detection allows cancellation or normal_intake |
| Frontend override safety flow tests | Scenario-adjacent risk | `frontend/.../OverrideModal.test.tsx` inspection | Gap | File is Python placeholder content under `.tsx` path; no executable frontend assertions |

## Input / Intermediate / Output Observability (Representative)

### Flow: messy intake to decision (`TestScenario1_MessyFamilyDiscovery`)
- Input:
  - Freeform note with destination alternatives, fuzzy date window, budget stretch signal, family composition.
- Intermediate:
  - Packet facts include `destination_candidates`, `date_window`, `budget_*`, party details.
  - Ambiguities include unresolved alternatives / vagueness markers.
  - Decision state produced by NB02.
- Output:
  - Traveler-safe bundle passes leakage checks.
  - Internal bundle includes rationale context.
- Runtime:
  - ~0.456s (slowest backend scenario in this run).

### Flow: workspace timeline observability (`test_spine_run_emits_audit_events`)
- Input:
  - Structured trip note (Paris sample) through `run_spine_once`.
- Intermediate:
  - AuditStore emits stage transition events.
- Output:
  - Failure due to event contract mismatch (`details.state` absent).
- Runtime:
  - ~0.411s.

## Dependencies and External Requirements

- Python test runtime (`uv`, pytest, src import path).
- Frontend runtime (`npm`, vitest, jsdom).
- Local persistence/event store for timeline (AuditStore).
- No external network dependencies required for executed tests.

## Unknowns / Uncovered Risk Surface

- No true UI-level E2E from homepage/inbox click to process-trip completion.
- No test asserting exact API payload emitted by frontend mode selector during Process action.
- No continuity test for final handoff (save -> ready -> return to inbox).
- Timeline event schema drift suggests missing contract lock between backend event model and test/API consumers.
- `P1-S0` scenario naming is not directly aligned with pipeline mapping (`P1-S1`); traceability can cause test selection ambiguity.

## FE Correction Targets

1. Add end-to-end workspace flow test: inbox card click -> workspace route -> process trip -> outputs visible -> return to inbox.
2. Add integration test for mode selector wiring (`operating_mode` in `/api/spine/run` request payload).
3. Replace malformed placeholder file:
   - [`frontend/src/components/workspace/panels/__tests__/OverrideModal.test.tsx`](/Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/__tests__/OverrideModal.test.tsx)
   - Currently contains Python + `pass`; should be valid TSX + RTL assertions.

## BE Correction Targets

1. Resolve timeline event schema contract drift:
   - Align tests and consumers on either:
     - `details.state` (flat) OR
     - `details.post_state.state` (nested)
   - Update one canonical schema and enforce through contract tests.
2. Tighten ambiguity handling in NB02 for values like `"Andaman or Sri Lanka"` to avoid false hard-blocker completion.
3. Urgency handling consistency: confirm whether last-minute non-emergency should suppress/selectively downgrade soft blockers.

## Open Task Lists

- Technical:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_TECHNICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_TECHNICAL_TASK_LIST_2026-04-23.md)
- Logical:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_LOGICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P1_S0_LOGICAL_TASK_LIST_2026-04-23.md)

## Artifacts Produced in This Run

- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_backend_pytest_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_backend_pytest_2026-04-23.xml)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_edge_modes_pytest_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_edge_modes_pytest_2026-04-23.xml)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_frontend_vitest_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_single_agent_frontend_vitest_2026-04-23.json)

## Closure Update - Post-Fix Verification (2026-04-23)

Follow-through actions requested after initial report:

1. Timeline contract mismatch fixed:
- `spine_stage_transition` events now include flat `details.state`.
- Timeline API now falls back to `details.post_state.state` when needed.

2. True journey test added:
- Added clickable user-journey integration test:
  - `inbox -> workspace process -> return link`
  - [/Users/pranay/Projects/travel_agency_agent/frontend/src/app/__tests__/p1_happy_path_journey.test.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/__tests__/p1_happy_path_journey.test.tsx)

3. Reusable case-study runbook added:
- [/Users/pranay/Projects/travel_agency_agent/tools/run_p1_happy_path_case_study.sh](/Users/pranay/Projects/travel_agency_agent/tools/run_p1_happy_path_case_study.sh)

Post-fix evidence:
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_backend_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_backend_2026-04-23.xml) (9/9 pass)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_modes_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_modes_2026-04-23.xml) (6/6 pass)
- [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_frontend_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p1_happy_path_frontend_2026-04-23.json) (15/15 pass)
