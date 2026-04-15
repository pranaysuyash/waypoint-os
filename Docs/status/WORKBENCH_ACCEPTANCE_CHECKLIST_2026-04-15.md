# Workbench Acceptance Checklist + Ticket Map

Date: 2026-04-15 08:42:54 IST
Owner: Implementation pass
Status: Ready for execution

Supersession note (2026-04-15 09:50:32 IST):
- Frontend direction changed to full product implementation path (no Streamlit).
- Keep this checklist as historical baseline for feature coverage.
- Re-map tickets into Next.js implementation tracks before execution.

## Ticket WB-001: App Shell + Mode Switch
Scope:
- Create `apps/streamlit_workbench.py`
- Add mode selector: Workbench / Flow Simulation
- Add top-level tabs for 5 screens

Acceptance:
- App boots without runtime errors
- Mode switch updates visible layout
- Tabs load without rerunning spine logic

## Ticket WB-002: Intake Form + Run Action
Scope:
- Intake inputs and selectors
- strict leakage/debug toggles
- Run button

Acceptance:
- Valid inputs execute spine run
- Invalid JSON is blocked with inline error
- Session state stores latest inputs and timestamp

## Ticket WB-003: Spine Orchestration Wiring
Scope:
- One run helper in app calling real shared modules only
- No duplicated business logic

Acceptance:
- Run produces packet, validation, decision, strategy, bundles, leakage status
- Works for manual and fixture inputs

## Ticket WB-004: Packet Screen (NB01)
Scope:
- Human summary cards
- facts/derived/ambiguities/unknowns/contradictions/validation
- Raw JSON toggle

Acceptance:
- Summary-first display is present
- Raw toggle shows complete NB01 object

## Ticket WB-005: Decision Screen (NB02)
Scope:
- Decision badge + rationale
- hard/soft blockers, contradictions, feasibility, risk flags, follow-ups
- Raw JSON toggle

Acceptance:
- Decision state always visible and color-coded
- Rationale is visible without opening raw JSON

## Ticket WB-006: Strategy Screen (NB03)
Scope:
- session goal/opening/priorities/branches/follow-up/tone
- internal vs traveler-safe visual separation

Acceptance:
- Internal and traveler-safe outputs are visibly distinct
- Branch prompts and assumptions are shown

## Ticket WB-007: Safety/Compare Screen
Scope:
- leakage status panel
- stripped-fields summary
- diff view raw vs sanitized
- fixture expected vs actual assertions

Acceptance:
- Leakage status shown for every run
- Strict mode failure visibly flagged
- Compare view shows pass/fail per assertion

## Ticket WB-008: Scenario Fixture Pack (8)
Scope:
- Add 8 scenario fixtures
- stable IDs and expected envelopes

Acceptance:
- Every scenario loads into intake with one click
- All 8 scenarios run end-to-end

## Ticket WB-009: Flow Simulation Paneling
Scope:
- Sequential panel layout A→E
- recommended next action + explanation

Acceptance:
- Panel set shown in Flow Simulation mode only
- Recommended action text changes with decision state

## Ticket WB-010: Minimal UI Tests
Scope:
- Add `tests/test_streamlit_workbench.py`
- Use Streamlit testing utilities

Acceptance:
- app loads
- scenario loads
- run works
- decision state appears
- traveler-safe preview appears/suppresses correctly
- leakage panel appears

## Ticket WB-011: Documentation + Indexing
Scope:
- link new spec/checklist docs in `Docs/INDEX.md`
- add completion/update entry in `Docs/DISCUSSION_LOG.md`

Acceptance:
- Docs index includes both files
- Discussion log contains date-verified entry

## Execution Order
1. WB-001
2. WB-002
3. WB-003
4. WB-004
5. WB-005
6. WB-006
7. WB-007
8. WB-008
9. WB-009
10. WB-010
11. WB-011

## Validation Gate
Before moving to productized frontend phase:
- 8/8 scenarios run successfully
- No leakage in traveler-safe outputs (except explicit test of strict-mode failure path)
- UI tests green
- Full project tests still green
