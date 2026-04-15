# Operator Workbench + Agency Flow Simulator

Date: 2026-04-15 08:42:54 IST
Scope: Internal app only (Phase A), additive to frozen spine, no scope reduction.

Supersession note (2026-04-15 09:50:32 IST):
- The product direction now requires proper full frontend implementation (no Streamlit path).
- Treat this file as historical planning context for component decomposition.
- Current execution authority is:
  - `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`

## 1) Purpose
Build a single internal Streamlit app with two modes:
- Workbench (deep inspectability for NB01/NB02/NB03/safety)
- Flow Simulation (operator-facing realism with traveler-safe boundary visibility)

This is a validation layer on top of the frozen spine, not a replacement frontend.

## 2) Non-Goals
- No auth/user accounts
- No DB/new persistence service
- No FastAPI/Flask backend work
- No live message sending
- No supplier/booking integration
- No business-logic duplication in UI

## 3) App Entry + Modules
Create:
- `apps/streamlit_workbench.py`

Use only existing shared runtime modules:
- `ExtractionPipeline`
- `validate_packet`
- `run_gap_and_decision`
- `build_session_strategy_and_bundle`
- `build_traveler_safe_bundle`
- `build_internal_bundle`
- `safety/leakage checks`

## 4) Page Information Architecture
Single Streamlit app with:
- Top controls: mode, stage, operating mode, scenario, debug toggles
- Main navigation tabs/screens:
  1. Intake
  2. Packet
  3. Decision
  4. Strategy
  5. Safety/Compare

## 5) Shared State Contract (UI Session)
Session state keys:
- `input_raw_note`
- `input_owner_note`
- `input_structured_json`
- `input_itinerary_text`
- `operating_mode`
- `stage`
- `scenario_id`
- `strict_leakage`
- `debug_raw_json`
- `result_packet`
- `result_validation`
- `result_decision`
- `result_strategy`
- `result_internal_bundle`
- `result_traveler_bundle`
- `result_leakage`
- `result_assertions`
- `result_run_ts`

Computed keys are read-only in UI.

## 6) Screen-by-Screen Component Spec

### Screen 1: Intake
Primary objective: collect or load context and run spine once.

Components:
- Scenario preset selector
- Input editors:
  - raw agency note
  - owner note
  - structured JSON (optional)
  - itinerary/audit text (optional)
- Selectors:
  - operating mode
  - stage
- Toggles:
  - strict leakage
  - show raw JSON globally
- Actions:
  - `Run Spine`
  - `Save Fixture`
  - `Compare Fixture`

Behavior:
- `Run Spine` executes deterministic orchestration pipeline and stores outputs to session state.
- Input validation happens before run; malformed JSON returns explicit inline error.

### Screen 2: Packet
Primary objective: human-readable NB01 packet inspection first, raw second.

Components:
- Summary cards:
  - trip type
  - destination/date/budget/party confidence snapshots
- Structured sections:
  - facts
  - derived signals (+ maturity)
  - ambiguities
  - unknowns
  - contradictions
  - validation report
  - source/evidence preview
- Raw JSON accordion/toggle

Behavior:
- Summary cards always shown before object dumps.

### Screen 3: Decision
Primary objective: explain NB02 state and reasoning.

Components:
- Decision state badge (clear color semantics)
- Panels:
  - hard blockers
  - soft blockers
  - contradictions
  - feasibility
  - urgency/risk flags
  - rationale
  - follow-up questions
- Raw JSON accordion/toggle

Behavior:
- “Why this state” explanation is mandatory and visually prominent.

### Screen 4: Strategy
Primary objective: expose NB03 sequencing and communication boundaries.

Components:
- Session goal
- Suggested opening
- Priority sequence
- Tone and follow-up sequence
- Branch prompts
- Internal notes
- Constraints/assumptions
- Side-by-side visual split:
  - internal path
  - traveler-safe path
- Raw JSON accordion/toggle

### Screen 5: Safety/Compare
Primary objective: make boundary enforcement first-class.

Components:
- Traveler-safe bundle render
- Leakage check result/status
- Stripped internal fields list
- Diff view:
  - raw packet vs sanitized traveler bundle
- Fixture compare:
  - expected vs actual
  - assertion pass/fail panel

Behavior:
- Leakage failures must be impossible to miss.
- In strict mode, hard failure status is shown with exact leakage reasons.

## 7) Flow Simulation Mode Contract
Layout: 5 sequential panels that mimic real operator workflow.

Panels:
- A. Incoming context
- B. System understanding summary
- C. Recommended next action (+ reason)
- D. Internal agent view (assumptions, contradictions, constraints)
- E. Traveler-safe preview

Decision-state color meanings:
- Green: traveler-safe proceed
- Amber: internal draft/branch
- Red: stop/review/escalate
- Blue/neutral: ask follow-up

## 8) Scenario Wiring (Initial 8)
Backed by fixture files under `data/fixtures/`:
1. clean family discovery
2. semi-open destination discovery
3. past customer with old-trip mention
4. audit mode with self-booked plan
5. coordinator group
6. cancellation
7. emergency
8. owner-review/internal-only case

Each scenario must include:
- stable `scenario_id`
- input payload
- expected decision-state envelope
- expected traveler-safe visibility expectations

## 9) Orchestration Call Graph (Single Run)
1. normalize/extract into packet (`ExtractionPipeline`)
2. validate packet (`validate_packet`)
3. decisioning (`run_gap_and_decision`)
4. strategy + bundles (`build_session_strategy_and_bundle`)
5. safety/leakage checks (`check_no_leakage`/strict enforcement)
6. assertions + fixture comparison (if selected)

UI must call this graph through one local orchestration helper function in app.

## 10) Error Handling Contract
- Malformed JSON input: block run, show inline error.
- Spine exception: show traceback in debug panel + user-facing summarized failure card.
- Leakage strict-mode violation: explicit failure panel with leaked fields and terms.
- Missing scenario fixture: non-fatal warning, fallback to manual input only.

## 11) Performance + UX Constraints
- Single-run path target: under 2s for fixture-size inputs on local machine.
- No blocking re-renders on tab switches; reuse session state.
- No silent mutation of computed outputs.

## 12) Deliverables for Phase A
- `apps/streamlit_workbench.py`
- scenario fixtures for 8 flows
- UI tests (basic interaction + visibility checks)
- docs updates in index/discussion log
