# E2E Scenario Execution Report

- Date: 2026-04-14 (IST)
- Scope: Intake extraction + decision routing (`ExtractionPipeline -> run_gap_and_decision`)
- Runner: `tools/e2e_scenario_runner.py`

## Requested Flow
1. Show 5 scenarios E2E
2. Plan and execute the remaining existing scenarios
3. Repeat with existing + new scenarios

## Plan Used
1. Build reusable scenario tool in `tools/` for repeatable set-based runs
2. Run `first5` set and capture baseline outputs
3. Run `rest` set for the remaining existing scenarios
4. Add and run `existing_plus_new` set for repeat coverage
5. Store outputs in both JSON and Markdown under `Docs/reports/`

## Run 1 — First 5 (Existing)
- Command:
  - `PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set first5 --json-out Docs/reports/e2e_first5_2026-04-14.json --md-out Docs/reports/e2e_first5_2026-04-14.md`
- Key outcomes:
  - S01 Vague Lead -> ASK_FOLLOWUP
  - S02 Confused Couple -> STOP_NEEDS_REVIEW
  - S03 Dreamer Luxury vs Budget -> ASK_FOLLOWUP
  - S04 Ready to Buy -> ASK_FOLLOWUP
  - S05 WhatsApp Dump -> ASK_FOLLOWUP

## Run 2 — Remaining Existing Scenarios
- Command:
  - `PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set rest --json-out Docs/reports/e2e_rest_existing_2026-04-14.json --md-out Docs/reports/e2e_rest_existing_2026-04-14.md`
- Key outcomes:
  - S06-S13 all evaluated successfully
  - S08 marked `emergency` operating mode
  - S09/S10 stage-specific scenarios run without API errors in reusable runner

## Run 3 — Existing + New Scenarios
- Command:
  - `PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set existing_plus_new --json-out Docs/reports/e2e_existing_plus_new_2026-04-14.json --md-out Docs/reports/e2e_existing_plus_new_2026-04-14.md`
- New scenarios added:
  - N01 Emergency Medical Routing
  - N02 Hard Date Conflict
  - N03 Booking Stage Fully Ready
  - N04 Budget Branching Candidate
  - N05 Coordinator Group Lead
- Key outcomes:
  - N02 correctly routed to STOP_NEEDS_REVIEW
  - N01 correctly routed with emergency operating mode
  - N03/N04/N05 routed through current decision policy and surfaced current blocker behavior

## Owner Tracking View
- Artifacts generated:
  - `Docs/reports/e2e_first5_2026-04-14.{json,md}`
  - `Docs/reports/e2e_rest_existing_2026-04-14.{json,md}`
  - `Docs/reports/e2e_existing_plus_new_2026-04-14.{json,md}`
- Reusable tool delivered:
  - `tools/e2e_scenario_runner.py`
  - `tools/README.md` updated with usage and examples

## What Remains
1. Scenario expectation alignment:
   - Some legacy expectations assume `PROCEED_*` where current policy still keeps `ASK_FOLLOWUP` due blockers/ambiguities.
2. Policy tuning decisions:
   - Decide whether to relax blocking criteria for specific business-ready paths (for example booking-ready synthetic scenario).
3. Legacy notebook script harmonization:
   - Keep `notebooks/test_scenarios_realworld.py` as historical artifact, but converge it to current field/stage policy if desired.

## Validation
- Regression tests after tool addition:
  - `PYTHONPATH=src uv run pytest -q tests/test_nb02_v02.py tests/test_decision_policy_conformance.py`
  - Result: 24 passed
