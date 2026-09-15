# Tools

This directory stores reusable helper utilities for this project.

## Test Inventory Receipt: `test_inventory.py`

Purpose:

- Produce a **reproducible** count receipt for the test suite (FND-0264 /
  ISS-007): collected tests via in-process `pytest --collect-only`, static
  `def test_` count, skip/xfail markers per file, and the CI-excluded file
  list.
- Exists because handoff receipts quoted three different suite totals in
  seven days while the green number was conditional (integration tests
  auto-skip without a dev server; Postgres/LLM tests skip without
  credentials). Quote this receipt instead of a bare total.

**Usage:**

```bash
.venv/bin/python tools/test_inventory.py            # human summary
.venv/bin/python tools/test_inventory.py --json     # machine-readable
.venv/bin/python tools/test_inventory.py --json --out Docs/status/test_inventory_<date>.json
```

**Notes:**

- Read-only: collects, never runs the suite, never mutates the tree.
- Collection runs pytest in-process (no shell, no subprocess).
- A receipt is timestamped; cite the file + `generated_at` when claiming
  counts in handoffs.

## Envelope-Fragment Stripper: `strip_envelope_fragments.py`

Purpose:

- Detect and repair AI tool-call envelope tails (`</content>` followed by
  `<parameter name="filePath">...`) accidentally written into Markdown
  documents by batch agent writes.
- Two auto-fix classes, both provably-safe shapes only:
  1. **Strict EOF tail** — the entire post-`</content>` remainder is exactly
     the single envelope line (leading indent tolerated) running to EOF,
     each marker occurring exactly once.
  2. **Guarded mid-document splice** — the welded tail sits between two
     halves of the document (a later write appended content past it).
     Repairable only when the parameter line's path is **self-referential**
     (names this very file, modulo markdown escaping / stale directories) —
     proving the bytes are write-path artifacts, not authored content. The
     fragment is excised and the halves re-joined with exactly one blank
     line (prevents setext-heading corruption when the following line is
     `---`).
- Anything else is reported for manual review, never guessed.
- Markdown code spans/fences are exempt from detection (docs about this
  defect legitimately quote the markers).
- `--check` and `--dry-run` NEVER write — only plain apply mode mutates
  files (CI runs `--check` on every push and must not repair mid-gate).

Usage:

```bash
python3 tools/strip_envelope_fragments.py --dry-run   # report only, never writes
python3 tools/strip_envelope_fragments.py             # apply strict repair
python3 tools/strip_envelope_fragments.py --check      # detect only, never writes; exit 1 if dirty (CI gate)
```

Notes:

- Defect class introduced at scale in commit c7fa31d (2026-04-23): 108 files
  carried the envelope tail + an absolute local path at EOF.
- Cross-repo sweep 2026-09-10/11: 42 sibling-repo files repaired with this
  tool (EchoPanel 19, learning_for_kids 21, metaextract 1 mid-doc splice,
  caption-art 1) — the sibling corpus revealed the indented and mid-document
  shape variants the original matcher refused.
- Wired into CI (`docs-quality` job runs `--check` on every push/PR).
- Contract tests: tests/test_strip_envelope_fragments.py (10 cases pinning
  write-mode gating, splice join quality, and the self-reference guard).
- Incident record: Docs/travel_agency_process_issue_review_2026-09-10.md.

## Git Classification Ledger Validator: `check_worktree_classification.py`

Purpose:

- Prove that a CSV classification ledger covers every path in an immutable
  commit or the live working tree.
- Reject missing, duplicate, extra, blank, or explicitly unclassified rows.
- Keep provenance/ownership uncertainty explicit without inventing authorship.

Usage:

```bash
python tools/check_worktree_classification.py \
  --commit 2f9a638 \
  --ledger Docs/review/assets/a1_1_commit_2f9a638_classification.csv

python tools/check_worktree_classification.py \
  --worktree \
  --ledger Docs/review/assets/a1_1_live_worktree_2026-09-01_classification.csv

# Create a conservative current snapshot before refining ownership/slices.
python tools/check_worktree_classification.py \
  --scaffold-worktree \
  --ledger Docs/review/assets/a1_1_live_worktree_YYYY-MM-DD_classification.csv
```

Notes:

- `--worktree` expands untracked directories to individual files.
- `--scaffold-worktree` emits explicit preserved-concurrent rows for every
  current path; it is a starting point, not an acceptance decision.
- This validates inventory/classification completeness, not product behavior.
- Re-run the live check immediately before handoff; any parallel path drift
  fails closed and requires refreshing the ledger.

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
python tools/runtime_smoke_matrix.py --preflight-local-stack
python tools/runtime_smoke_matrix.py --base http://localhost:3000 \
  --email newuser@test.com --password testpass123
```

Standard local gate:

```bash
python tools/runtime_smoke_matrix.py --preflight-local-stack
```

Checks:

- With `--preflight-local-stack`, first verifies:
  - backend health: `http://127.0.0.1:8000/health`
  - frontend health: `http://127.0.0.1:3000/overview`
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

Operational rule:

- Before claiming local frontend/backend runtime stability, run the standard local gate above. It proves both local services are healthy before the authenticated BFF/page matrix starts.

## Performance Benchmark Matrix: `performance_benchmark_matrix.py`

Purpose:

- Run repeatable latency benchmarks across local OTel runtime scenarios.
- Measure endpoint latency distribution (`avg`, `p50`, `p95`, `p99`, `max`) with authenticated requests.
- Emit JSON + Markdown artifacts under `Docs/reports/` for before/after comparison.

Scenarios:

- `otel_off`: tracing disabled.
- `otel_unreachable`: tracing enabled with unreachable collector endpoints (resilience check).
- `otel_configured`: tracing enabled with caller-provided collector endpoints.

Usage:

```bash
python tools/performance_benchmark_matrix.py
python tools/performance_benchmark_matrix.py --iterations 8
python tools/performance_benchmark_matrix.py --scenarios otel_off,otel_unreachable
python tools/performance_benchmark_matrix.py \
  --scenarios otel_configured \
  --iterations 6
```

For `otel_configured`, set both endpoints before running:

```bash
export SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT=http://otel-collector:4317
export OTEL_EXPORTER_OTLP_HTTP_TRACES_ENDPOINT=http://otel-collector:4318/v1/traces
python tools/performance_benchmark_matrix.py --scenarios otel_configured
```

Outputs:

- `Docs/reports/performance_benchmark_matrix_<YYYY-MM-DD>.json`
- `Docs/reports/performance_benchmark_matrix_<YYYY-MM-DD>.md`

Notes:

- The script restarts local backend/frontend for each scenario using `tools/dev_server_manager.py`.
- Keep this as the canonical local benchmark harness for performance regressions.

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

## 4) `feature_scan.py`

Purpose:

- Run the repo-local feature progression scanner against `tools/feature_catalog.json`.
- Emit fresh `scanned_at` metadata instead of the stale external-skill date.
- Require each declared evidence term to be found across all configured file globs before marking a sub-feature done.

Use cases:

- Produce a less manual progression review input after feature work lands.
- Check whether D6, itinerary-option, and per-person utility/waste artifacts are visible to the catalog.
- Debug noisy feature scores by inspecting `matched_terms`, `missing_terms`, and line-level evidence.

Usage:

```bash
cd /Users/pranay/Projects/travel_agency_agent
python3 tools/feature_scan.py . --json
python3 tools/feature_scan.py . --priority P0 --delta
```

Inputs:

- Default catalog: `tools/feature_catalog.json`
- Optional catalog override: `--catalog /path/to/catalog.json`

Outputs:

- Human-readable console report by default.
- JSON report with `--json`, including current scan date, matched terms, missing terms, and evidence snippets.

## 5) D6 Audit Eval Scaffold

Purpose:

- Measure audit-rule quality before findings become authoritative on consumer-facing surfaces.
- Run fixture corpora through category-specific rule runners and compare expected vs actual findings.
- Evaluate manifest thresholds for `planned`, `shadow`, and `gating` categories.

Key modules:

- `src/evals/audit/fixtures.py` — fixture schema and JSON loader.
- `src/evals/audit/runner.py` — eval runner.
- `src/evals/audit/metrics.py` — precision, recall, severity accuracy.
- `src/evals/audit/gates.py` — manifest threshold and public-authority decisions.
- `src/evals/audit/rules/activity.py` — activity utility/waste runner using `ItineraryOption`.

Fixture location:

- `data/fixtures/audit/`

Usage:

```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run pytest -q tests/evals/test_d6_audit_scaffold.py
```

Notes:

- `activity` is currently a shadow category, not a consumer-authoritative gate.
- Promote categories to `gating` only after enough fixtures prove precision/recall.

Runtime snapshot generation:

```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run python scripts/generate_d6_gate_snapshot.py
uv run python scripts/verify_d6_gate_snapshot.py
```

- Default output: `data/evals/d6_audit_gate_snapshot.json`
- Runtime authority resolver consumes this via `D6_AUDIT_GATE_SNAPSHOT_PATH` when set.
- If snapshot is missing/invalid, runtime falls back to manifest status.
- `verify_d6_gate_snapshot.py` enforces deterministic drift checks (ignores `generated_at` timestamp noise).

## 6) `singapore_scenario_regression.py`

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

## 7) `generate_dummy_singapore_itinerary_pdf.py`

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

## 8) `run_multi_agent_runtime_scenarios.py`

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

## 9) `build_agent_intelligence_graph.py`

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

## 10) `recovery_guard_report.py`

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

## Status Vocabulary Report: `status_vocabulary_report.py`

Purpose:

- Produce a read-only JSON inventory of `Trip.status` tokens from the file
  store, SQL store, or both.
- Preserve raw values while separately reporting missing keys, explicit nulls,
  blank/invalid values, normalized tokens, and canonical alias coverage.
  Writer provenance is explicitly `not_evaluated`; distribution is not proof
  of which code path wrote a token.

Usage:

```bash
PYTHONPATH=. .venv/bin/python tools/status_vocabulary_report.py --backend file
PYTHONPATH=. .venv/bin/python tools/status_vocabulary_report.py \
  --backend sql --agency-id <agency-uuid>
PYTHONPATH=. .venv/bin/python tools/status_vocabulary_report.py \
  --backend both --agency-id <agency-uuid>
```

Notes:

- The tool never commits, updates, deletes, migrates, or rewrites source data.
- SQL and `both` require `--agency-id`. SQL applies canonical transaction-local
  RLS, verifies its enforcement, retains the agency predicate, and rolls back a
  read-only transaction. `--sql-timeout-seconds` defaults to 30 (maximum 120);
  driver cancellation/cleanup can take additional time.
- File output is **directory-unfiltered**: `--agency-id` applies only to SQL.
  The two sources are not automatically the same population. POSIX/macOS/Linux
  descriptor-relative reads reject symlinks and nonregular files.
- Schema 2 `rows_counted` includes parsed file objects with missing/null/invalid
  statuses; `status_values_counted` counts only actual string values. Do not
  compare schema 1 counts without accounting for that contract change.
- Exit 0 means complete observation, not valid business state. Exit 2 reports
  partial/unavailable observation or invalid CLI usage. Missing roots are not
  empty sources; fixed error codes do not expose exception payloads.
- Raw status strings may contain sensitive data. Inspect and redact before
  sharing reports; file reads are not atomic snapshots of concurrent writes.
- Unknown values are not rewritten and the tool does not define a second
  canonical vocabulary; it imports the backend alias map for comparison.
- Evidence, schema, alternatives, and remaining writer/alias research:
  `Docs/exploration/E12_STATUS_ALIAS_EXPANSION_PLAN_2026-09-02.md`, repair section.

## Live-PostgreSQL Multi-Worker Contention Probe: `live_db_multiworker_probe.py`

Purpose:

- Run the live-PostgreSQL multi-worker contention probe (PER-0700 wave 2) as a
  single command: real OS processes contending on the same durable Postgres
  rows, asserting exactly-one-winner semantics.
- Thin pytest orchestrator only — the single source of truth for the probe
  logic is `tests/test_pa_wave2_live_probe.py`; this tool holds no SQL and no
  business logic.
- Performs preflight (loads `.env`, verifies `DATABASE_URL`, cheap TCP dial of
  the Postgres host), forwards knobs to pytest, propagates pytest's exit code,
  and prints what each check proves.

Usage:

```bash
# All 4 checks, default 4 workers each
.venv/bin/python tools/live_db_multiworker_probe.py

# More contention
.venv/bin/python tools/live_db_multiworker_probe.py --workers 8

# One check (or a comma-separated subset) via pytest -k
.venv/bin/python tools/live_db_multiworker_probe.py --check idempotency
.venv/bin/python tools/live_db_multiworker_probe.py --check lease,token --verbose
```

Example output (abbreviated):

```text
========================================================================
Live-PostgreSQL multi-worker contention probe (PER-0700 wave 2)
========================================================================
  Test module:  tests/test_pa_wave2_live_probe.py
  Workers:      4 (real OS processes, spawn context)
  Checks:       all 4
  DATABASE_URL: found (source: .env)
  Database:     localhost:5432/waypoint_os (credentials redacted)
  Preflight:    Postgres reachable at localhost:5432
...
tests/test_pa_wave2_live_probe.py ....                                    [100%]
Probe PASSED: contention guarantees hold at 4 workers.
```

What each check proves (one line each, also printed by the tool):

- `idempotency` — SQL idempotency registry CAS grants the action to exactly
  1 of N cross-process contenders.
- `lease` — SQLWorkCoordinator work lease is won by exactly 1 process.
- `token` — collection tokens are single-use across processes.
- `usage_events` — usage_events store exposes run correlation columns.

Safety notes:

- **Additive-only by design**: probe rows anchor to the seeded canonical
  agency; each run creates one fresh namespaced probe trip and one fresh
  collection token through the canonical `TripStore` / collection service.
  Nothing pre-existing is mutated or deleted.
- **Skips without `DATABASE_URL`**: the pytest module auto-skips (green) when
  no live PG is configured; this wrapper fails fast with exit code 2 so the
  missing prerequisite is explicit rather than silently proving nothing.
- **CI-safe**: with a Postgres service container providing `DATABASE_URL`,
  the probe runs unattended in CI; exit code is non-zero only on a real
  contention failure or environment error.
- `--workers N` forwards through the `PROBE_WORKERS` env var to the test
  module (`WORKERS = int(os.environ.get("PROBE_WORKERS", "4"))`).

---

## Feature List Generator: `feature_list_generate.py`

**Purpose:** Derive the machine-readable JSON + CSV artifacts of a feature-list
inventory from its markdown source of truth, with validation. Introduced with
`Docs/status/FEATURE_LIST_V3_2026-09-10.md`; the markdown tables are canonical —
never hand-edit the derived `.json`/`.csv`.

**Usage:**

```bash
python3 tools/feature_list_generate.py \
  --md Docs/status/FEATURE_LIST_V3_2026-09-10.md \
  --json Docs/status/FEATURE_LIST_V3_2026-09-10.json \
  --csv Docs/status/FEATURE_LIST_V3_2026-09-10.csv
```

**Notes:**

- Parses `## X) Title` domain sections and 6-column tables
  (`| ID | Feature | Status | Priority | What it does | Evidence |`).
- Validates unique IDs, statuses (`LIVE`, `PARTIAL`, `GATED`, `SIMULATED`,
  `STUB`, `SPEC`, `EXPLORE`), and priorities (`P0`–`P2`); exits non-zero on any
  parse problem, so it doubles as a consistency check for future V4 refreshes.
- Emits `metadata` + `counts` + full `records` in JSON; flat rows in CSV.

## generate_promptfoo_config.py

**Purpose:** port the hybrid risk-flag eval lane (35-record corpus from the
budget/colloquial golden fixtures) to a portable Promptfoo configuration —
per `Docs/exploration/HYBRID_KDD_EXPERIMENT_2026-09-11.md` §7.3/§7.5 (OpenAI
is winding down its Evals product in favor of Promptfoo).

**Usage:**

```bash
python3 tools/generate_promptfoo_config.py
PROMPTFOO_PYTHON="$PWD/.venv/bin/python" \
  npx promptfoo eval -c data/experiments/hybrid_kdd_v1/promptfooconfig.yaml --no-cache
```

**What it emits:** `data/experiments/hybrid_kdd_v1/promptfooconfig.yaml`
(35 test cases + assertions) and `promptfoo_provider.py` (python provider
wrapping the repo's real extraction + hybrid decision pipeline).

**Assertions:** output is JSON with a `risks` array, plus the no-spurious-visa
invariant (`visa_timeline_risk` only when destination facts exist — KDD §7.4
Q8). Not per-record ground truth; that belongs to the E-07 judge lane.

**Notes:**

- `PROMPTFOO_PYTHON` must point at the repo venv (provider imports need repo
  dependencies; promptfoo's default worker python lacks them).
- Without provider credentials the pipeline degrades deterministically
  (safe-default decisions are not emitted as flags), so the lane is CI-safe
  and free; with credentials set it exercises the real LLM escalation path.
- Re-run the generator after fixture changes; do not hand-edit the generated
  config/provider.

## grade_kdd_flags.py

**Purpose:** grade KDD experiment risk-flag arms against the curated
ground-truth labels — completes KDD §7.5 item 2 (precision/recall/F1 per arm).

**Usage:**

```bash
python3 tools/grade_kdd_flags.py                    # grade every records*.jsonl run
python3 tools/grade_kdd_flags.py records_final_single.jsonl   # grade one run
```

**Labels:** `data/fixtures/risk_flags/ground_truth_labels.json` — note-level
business reality (a flag is expected when an advisor reading the raw note would
raise it), rubric fixed before any arm was scored. Matching is flag-name level;
severity agreement reported as `severity_exact`.
`traveler_safe_leakage_risk` (pipeline-integrity family) is excluded — see the
labels file's `_meta.excluded_flags`.

**Output:** per-arm P/R/F1 table + `data/experiments/hybrid_kdd_v1/grading_receipt.json`.

**Caveats:** author-curated labels (documented bias mitigations in `_meta`);
`budget_hard_001` labeled domestic-unknown; visa judgments assume
Indian-passport travelers (corpus default).

## build_model_comparison.py

**Purpose:** regenerate the full model-comparison sheet — every model ever
tested in the hybrid risk-flag lane (kept, deleted, failed, partial, blocked)
— from the per-run JSONLs + a curated manifest. Nothing is lost when models
are pruned from the local ollama store.

**Usage:** `python3 tools/build_model_comparison.py`

**Outputs:** `data/experiments/hybrid_kdd_v1/comparison_sheet.csv` and the
table block in `Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md`
(includes the failure/ops log and one-command re-pull recipes).

**Notes:** add new runs to the `MANIFEST` list in the script (id, tier, size,
cost, status, run file, arm, notes), then regenerate. Grades are computed
live via `grade_kdd_flags.py` logic against the ground-truth labels.

## sim2_acceptance_probe.py

**Purpose:** Reusable fresh-acceptance gate for the Sim #2 (Family Summit)
defect classes plus the extraction-realignment wave's new contracts, run
against the real in-process pipeline. Origin-fabrication, budget-scope
overwrite, D-02 misfire, per-traveler attribution, anniversary survival,
group-chat-dump attribution, direction intent ("X side"), VFR promotion,
and past-trip memory/history-informed asks.

**Usage:**
```bash
.venv/bin/python tools/sim2_acceptance_probe.py
```

**Output:** per-check PASS/FAIL lines with evidence, exit 0 only when all
checks pass. Run after any change to `src/intake/extractors.py`,
`src/intake/attribution.py`, or `src/intake/decision.py`.

**Source of truth:** `Docs/sims/SIM2_FAMILY_SUMMIT_RESULTS_2026-09-12.md`
(defect classes) and `Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md`
(new contracts). Note the verbatim persona scripts are embedded as constants
so the probe stays deterministic and self-contained.

**Example:**
```
== Sim #2 fresh acceptance probe ==
  [PASS] 1. origin fabrication dead: origin_city=None
  ...
9/9 checks passed
ALL GREEN
```

---

## Memory Slot Shadow Review: `python -m src.memory.slot_review`

Purpose:

- Turn `memory_slot_promotion` audit events into the E-D slot-1
  shadow-window verdict (ADR-008 §7 row 4): `INSUFFICIENT_DATA`,
  `GUARDRAIL_VIOLATION` (reopen signal), or `REVIEW_READY` (owner decides
  the `MEMORY_SLOT_READ_MODE=active` flip). Pre-registered criteria live in
  the module docstring and `Docs/architecture/MEMORY_SLOT_WIRING_2026-09-15.md`
  §"Shadow-window review contract".

**Usage:**

```bash
.venv/bin/python -m src.memory.slot_review                        # human summary
.venv/bin/python -m src.memory.slot_review --json                 # machine-readable
.venv/bin/python -m src.memory.slot_review --agency <id> --since 2026-09-15
```

**Exit codes:** 0 review-ready/clean, 2 insufficient data (<30 asks),
3 guardrail violation (G1 invariant, G2 trust floor, G3 single-memory
degeneracy, G4 noise bound).

**Notes:**

- Canonical home is the package module (`src/memory/slot_review.py`); this
  README entry is the pointer, not a parallel implementation.
- Read-only over `data/audit/events.jsonl`; never flips the mode itself.
