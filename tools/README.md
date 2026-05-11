# Tools

This directory stores reusable helper utilities for this project.

## Dev Server Manager: `dev_server_manager.py`

Purpose:
- Manage backend/frontend dev servers as detached processes for stable local QA loops.
- Avoid fragile per-terminal sessions by keeping mutable PID and log state in ignored `.runtime/local/`.
- Provide explicit `start/stop/restart/status/check/logs` commands with health validation.

Usage:
```bash
python tools/dev_server_manager.py start --service all
python tools/dev_server_manager.py status --service all
python tools/dev_server_manager.py check --service all
python tools/dev_server_manager.py logs --service backend --lines 80
python tools/dev_server_manager.py restart --service all
python tools/dev_server_manager.py stop --service all
```

Notes:
- Backend health target: `http://127.0.0.1:8000/health`
- Frontend health target: `http://127.0.0.1:3000/overview`
- Runtime files:
  - `.runtime/local/backend.pid`
  - `.runtime/local/frontend.pid`
  - `.runtime/local/backend.log`
  - `.runtime/local/frontend.log`
- If PID files drift, status recovers by discovering the process bound to the service port.

## Runtime Smoke Matrix: `runtime_smoke_matrix.py`

Purpose:
- Run a real authenticated smoke pass against key frontend pages and BFF routes.
- Catch runtime regressions (401/500/drift) with one command before/after major edits.

Usage:
```bash
python tools/runtime_smoke_matrix.py
python tools/runtime_smoke_matrix.py --base http://localhost:3000 \
  --email newuser@test.com --password testpass123
```

Checks:
- `/api/auth/me`
- `/overview`
- `/workbench?draft=new&tab=safety`
- `/api/inbox?page=1&limit=1`
- `/api/trips?view=workspace&limit=5`
- `/api/reviews?status=pending`
- `/api/inbox/stats`
- `/api/pipeline`

Exit behavior:
- Returns `0` when all checks match expected status.
- Returns `1` and prints failing status/body snippets when any check fails.

## Architecture Route Inventory: `architecture_route_inventory.py`

Purpose:
- Inventory FastAPI route ownership across `spine_api/server.py` and `spine_api/routers/`.
- Inventory the frontend BFF route registry in `frontend/src/lib/route-map.ts`.
- Flag exact backend method/path duplicates before router decomposition work.
- Flag BFF route-map entries whose `backendPath` does not match a current backend path after path-parameter normalization.
- Produce Markdown/JSON evidence for architecture planning without importing the FastAPI app.

Usage:
```bash
uv run python tools/architecture_route_inventory.py --format md \
  --output Docs/status/ARCHITECTURE_ROUTE_INVENTORY_YYYY-MM-DD.md

uv run python tools/architecture_route_inventory.py --format json
```

Notes:
- This is a static architecture aid. Runtime route/OpenAPI parity is still covered by `scripts/snapshot_server_routes.py` and the server route parity tests.
- Keep using it before moving route families out of `spine_api/server.py` so decomposition choices are based on current code, not stale line references.


## Frontend Contrast Validator: `frontend-validate-contrast.ts`

Purpose:
- Validate frontend design token text/background contrast combinations using `frontend/src/lib/contrast-utils.ts`.
- Keep contrast diagnostics as a reusable repo-level tool instead of frontend runtime code.

Usage:
```bash
cd frontend
npx tsx ../tools/frontend-validate-contrast.ts
```

Notes:
- The script is read-only and prints PASS/FAIL contrast ratios plus suggested token adjustments.
- It intentionally lives in the repo-level `tools/` directory so React Doctor does not classify it as unused frontend application code.

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

## 5) `generate_dummy_singapore_itinerary_pdf.py`

Purpose:
- Generate a realistic sample Singapore family itinerary PDF for checker upload testing.
- Produce a stable, visually polished PDF under `output/pdf/`.

Use cases:
- Create a dummy upload file for itinerary checker QA.
- Test OCR, PDF text extraction, and live destination checks with a family-heavy travel plan.

Usage:
```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run python tools/generate_dummy_singapore_itinerary_pdf.py
```

Output:
- `output/pdf/pranay_family_singapore_may_dummy_itinerary.pdf`

Notes:
- The file is a sample only and does not represent a real booking.
- Uses `reportlab` and the existing project venv / uv environment.

## 6) `run_multi_agent_runtime_scenarios.py`

Purpose:
- Run deterministic backend multi-agent runtime drills without touching the
  production/test database.
- Verify happy path orchestration, retry after transient dependency failure,
  terminal failure escalation, and idempotent re-entry behavior.
- Write durable Markdown evidence for implementation handoff and audit review.

Usage:
```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run python tools/run_multi_agent_runtime_scenarios.py
```

Output:
- `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`

Notes:
- Uses an in-memory trip repository and audit sink.
- Does not require backend or frontend servers.

## 7) `build_agent_intelligence_graph.py`

Purpose:
- Turn the repo's autoresearch, feedback-loop, graph-memory, and live-intelligence docs into a living navigation graph.
- Produce a durable Markdown + JSON artifact that agents can read before planning changes.

Use cases:
- Seed a canonical "where to look next" graph from the docs that already define learning, memory, and graph behavior.
- Surface cross-links between autoresearch, feedback loops, taste graphs, governance, and live intelligence.
- Keep the repo's improvement system additive instead of relying on a single index file.

Usage:
```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run python tools/build_agent_intelligence_graph.py
```

Outputs:
- `Docs/context/AGENT_INTELLIGENCE_GRAPH.md`
- `Docs/context/agent_intelligence_graph.json`

Notes:
- Heuristic and additive, not a source-of-truth database.
- Uses only the repository's existing docs and standard library.

## 8) `recovery_guard_report.py`

Purpose:
- Provide a read-only starting point when an agent suspects unsafe stash/reset/worktree activity.
- Surface current branch/worktree/stash state without replaying anything.
- Point agents to the repo's safe selective-recovery workflow instead of destructive shortcuts.

Usage:
```bash
cd /Users/pranay/Projects/travel_agency_agent
.venv/bin/python tools/recovery_guard_report.py
```

Outputs:
- Console report covering:
  - `git status --short --branch`
  - `git worktree list --porcelain`
  - visible stash entries
  - stash-log presence
  - tracked `.claude/worktrees` artifacts
  - the safe recovery checklist

Related note:
- `Docs/SAFE_STASH_RESET_RECOVERY_PROTOCOL_2026-05-05.md`

Notes:
- Read-only by design.
- Use this before any stash/worktree recovery decision.
