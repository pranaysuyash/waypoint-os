# Live Intel Execution Checklist — 2026-05-05

## Objective

Implement real-time, cost-effective tool-calling checks through the canonical runtime (no duplicate pipeline), with production-safe fail-closed behavior.

## Current Baseline

- Runtime has pluggable live tools and product agents (`src/agents/live_tools.py`, `src/agents/runtime.py`).
- Scenario coverage improved for:
  - elderly + high flight-leg fatigue
  - toddler + extreme activity mismatch
- Exploration track documented in:
  - `Docs/research/LIVE_INTEL_TOOLCALLING_EXPLORATION_2026-05-05.md`

## Execution Plan (Ordered)

1. Add TinyFish optional provider wrappers in `src/agents/live_tools.py`.
2. Wire optional TinyFish augmentation into existing agents:
   - destination intelligence
   - safety alerts
3. Add stage-aware call-budget guards and TTL tuning.
4. Add provider observability fields to output packets and event logs.
5. Add deterministic fallback behavior tests for provider outage/stale responses.
6. Add integration tests for enriched outputs when TinyFish is enabled.

## Acceptance Criteria

1. No new parallel route or duplicate scenario pipeline.
2. Existing tests pass with provider disabled (default path unchanged).
3. With provider enabled:
   - tool evidence includes source/freshness/confidence/reference.
   - runtime emits `unknown` risk on failure/stale rather than silent pass.
4. Proposal/booking readiness remains backward compatible for existing consumers.
5. Added tests cover:
   - success
   - timeout/error
   - stale evidence
   - idempotent rerun behavior.

## Risks and Controls

- Risk: noisy web evidence causes false positives.
  - Control: confidence threshold + source weighting + advisory severity gating.
- Risk: runaway usage cost.
  - Control: stage budgets, per-trip TTL dedupe, max call caps.
- Risk: fragile parsing from generic search/fetch responses.
  - Control: only map to conservative advisory constraints unless confidence is high.

## Tracking Note

Treat this checklist as active execution guidance for the live-intel stream tied to scenario-handling hardening.
