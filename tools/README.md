# Tools

This directory stores reusable helper utilities for this project.

## 1) `context_digest.py`

Purpose:
- Convert large exported conversation/context `.txt` files into structured summaries.
- Keep the full source context intact while generating a quick navigation layer.

Use cases:
- Ingest large chat exports from Downloads into project documentation.
- Produce action candidates and theme clustering for planning.
- Generate JSON + Markdown digest artifacts for traceability.

Usage:
```bash
python tools/context_digest.py \
  --input Archive/context_ingest/travelagency_context_2026-04-14.txt \
  --output-md Docs/context/CONTEXT_DIGEST_2026-04-14.md \
  --output-json Docs/context/context_digest_2026-04-14.json
```

Note: `DESIGN.md` has been moved to `Docs/DESIGN.md`.

Outputs:
- Markdown digest (`--output-md`) with sections, themes, top terms, and action candidates.
- JSON digest (`--output-json`) for automation or downstream tooling.

Notes:
- Heuristic summarization only; keep archived source as system-of-record.
- Works offline and has no third-party dependencies.

## 2) `e2e_scenario_runner.py`

Purpose:
- Run repeatable end-to-end intake scenarios through `ExtractionPipeline -> run_gap_and_decision`.
- Support phased runs: first 5 scenarios, remaining existing scenarios, and combined existing+new scenarios.
- Export scenario outcomes to JSON and Markdown for owner tracking.

Use cases:
- Demonstrate 5 E2E scenarios quickly.
- Execute full existing scenario sweep after baseline.
- Re-run all existing + new scenarios after additions.
- Generate artifacts for documentation/review in `Docs/reports/`.

Usage:
```bash
# First 5 existing scenarios
PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set first5 \
  --json-out Docs/reports/e2e_first5_YYYY-MM-DD.json \
  --md-out Docs/reports/e2e_first5_YYYY-MM-DD.md

# Remaining existing scenarios
PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set rest \
  --json-out Docs/reports/e2e_rest_existing_YYYY-MM-DD.json \
  --md-out Docs/reports/e2e_rest_existing_YYYY-MM-DD.md

# Existing + new scenarios
PYTHONPATH=src uv run python tools/e2e_scenario_runner.py --set existing_plus_new \
  --json-out Docs/reports/e2e_existing_plus_new_YYYY-MM-DD.json \
  --md-out Docs/reports/e2e_existing_plus_new_YYYY-MM-DD.md
```

Supported sets:
- `first5`
- `rest`
- `existing`
- `new`
- `existing_plus_new`

Outputs:
- JSON: one object per scenario including decision state, blockers, contradictions, ambiguities, and confidence.
- Markdown: tabular summary for quick review.

Notes:
- This tool is additive and does not replace legacy notebooks/scenario scripts.
- Uses current runtime models from `src/intake/`.

## 3) `eval_runner.py`

Purpose:
- Validate test fixtures against NB02 decision engine.
- Run policy-only (CanonicalPacket → NB02) and end-to-end (Raw → NB02) evaluations.
- Verify decision states, blockers, and follow-up questions match expectations.

Use cases:
- Regression testing after decision engine changes.
- Validate fixture data quality and coverage.
- Debug decision logic behavior with real-world scenarios.

Usage:
```bash
cd /Users/pranay/Projects/travel_agency_agent
python tools/eval_runner.py
```

Outputs:
- Console summary of pass/fail for each fixture.
- Detailed failure breakdown showing check mismatches.
- JSON results file at `data/fixtures/eval_results.json`.

Test coverage:
- Mode 2 (Policy-Only): 19 CanonicalPacket fixtures covering:
  - ASK_FOLLOWUP scenarios (empty, missing fields, contradictions)
  - PROCEED_TRAVELER_SAFE (complete discovery, manual override, derived destination)
  - PROCEED_INTERNAL_DRAFT (soft blockers only, low confidence)
  - BRANCH_OPTIONS (budget/destination ambiguity)
  - STOP_NEEDS_REVIEW (date contradictions, multiple critical issues)

- Mode 1 (End-to-End): 12 raw input fixtures covering:
  - Clean/happy path bookings
  - Messy/under-specified leads
  - Hybrid conflicts (CRM + notes)
  - Contradiction-heavy scenarios
  - Branch-worthy ambiguities

Notes:
- All 31 fixtures currently pass (100%).
- Fixes applied: migrated packet_fixtures.py and raw_fixtures.py to v0.2 API.
- Fixed decision.py to handle string-format party_composition values.

## 4) `singapore_scenario_regression.py`

Purpose:
- Run the canonical Ravi/Singapore messy-call scenario through both live async paths:
  - Frontend proxy: `POST /api/spine/run` -> `GET /api/runs/{run_id}`
  - Backend direct: `POST /run` -> `GET /runs/{run_id}`
- Capture input, intermediate checkpoints, terminal output, run-state transitions, and quality flags.
- Emit durable JSON + Markdown evidence artifacts under `Docs/reports/`.

Usage:
```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run python tools/singapore_scenario_regression.py \
  --frontend-base http://localhost:3000 \
  --backend-base http://localhost:8000
```

Outputs:
- `Docs/reports/singapore_canonical_regression_YYYY-MM-DD.json`
- `Docs/reports/singapore_canonical_regression_YYYY-MM-DD.md`

Notes:
- Scenario fixture source: `data/fixtures/scenarios/SC-901_ravi_singapore_messy_call.json`.
- Ensure backend and frontend dev servers are running before execution.
