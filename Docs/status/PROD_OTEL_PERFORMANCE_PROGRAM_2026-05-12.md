# Production OTel Performance Program — 2026-05-12

## Context

User requested a production-grade performance strategy with OpenTelemetry enabled, plus measured evidence rather than patch-style tuning.

## Ground-Truth Checks Completed

- Instruction stack validated:
  - `/Users/pranay/AGENTS.md`
  - `/Users/pranay/Projects/AGENTS.md`
  - `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
  - `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`
  - `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
  - `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`
- Parallel-drift status check completed (`git status --short` + recent commit scan).
- Relevant skills confirmed and loaded from curated project store:
  - `search-first`
  - `systematic-debugging`
  - `verification-before-completion`

## What Was Built

1. Reproducible benchmark harness:
   - `tools/performance_benchmark_matrix.py`
   - Scenario matrix support:
     - `otel_off`
     - `otel_unreachable`
     - `otel_configured` (requires endpoint env vars)
   - Measures per endpoint:
     - `avg_ms`, `p50_ms`, `p95_ms`, `p99_ms`, `max_ms`, `min_ms`
   - Authenticated request path through frontend for user-visible truth.
   - Deterministic lifecycle via `tools/dev_server_manager.py`.
   - Artifacts:
     - `Docs/reports/performance_benchmark_matrix_2026-05-12.json`
     - `Docs/reports/performance_benchmark_matrix_2026-05-12.md`

2. Tooling resilience hardening:
   - `tools/runtime_smoke_matrix.py` now handles transient `RemoteDisconnected` failures during startup/restart races.
   - Benchmark harness includes command timeouts + smoke retries to avoid hangs.

3. Tool docs updated:
   - `tools/README.md` now documents the benchmark matrix workflow and required env vars.

## Measured Evidence

Run:
```bash
python -u tools/performance_benchmark_matrix.py --scenarios otel_off,otel_unreachable --iterations 2
```

Results captured in:
- `Docs/reports/performance_benchmark_matrix_2026-05-12.md`
- `Docs/reports/performance_benchmark_matrix_2026-05-12.json`

Important interpretation note:
- `iterations=2` is a quick validation pass for harness correctness, not a statistically strong production benchmark.
- Production gating should use at least `iterations>=20` (preferably fixed-duration load windows with concurrency).

## Verification

- Smoke matrix:
  - `python tools/runtime_smoke_matrix.py --preflight-local-stack` ✅
- Runtime smoke tests:
  - `uv run pytest tests/test_runtime_smoke_matrix.py -q` → `2 passed` ✅
- Stack status:
  - backend/frontend healthy via `tools/dev_server_manager.py status --service all` ✅

## Production-Grade Rollout Path (First Principles)

1. OTel configuration contracts:
   - Keep separate backend/frontend endpoint env vars to avoid protocol/format conflicts.
   - Keep explicit BSP controls for queue size, batch size, schedule delay, and export timeout.

2. Benchmark policy:
   - Baseline profile:
     - `otel_off`
     - `otel_configured` (real collector)
     - `otel_unreachable` (collector failure mode)
   - Run with fixed dataset, fixed user/account, fixed endpoint set, fixed iteration count.
   - Publish JSON artifacts per run for trend diffing.

3. SLO gate example:
   - `p95 /api/inbox <= 350ms`
   - `p95 /api/pipeline <= 300ms`
   - `otel_unreachable` must not exceed agreed degradation budget (for example, +20% p95 on critical reads).

4. Next technical depth:
   - Add concurrency mode to benchmark harness (`N workers`) to reflect real user overlap.
   - Add endpoint-level request count and failure budget scoring.
   - Attach SQL timing and app-level span correlation IDs in benchmark report.

## Open Questions

1. What production SLO thresholds should be enforced for each key endpoint?
2. What collector topology is planned (single collector vs gateway + tail sampling)?
3. Should `otel_unreachable` be a required CI gate or an on-demand release check?
