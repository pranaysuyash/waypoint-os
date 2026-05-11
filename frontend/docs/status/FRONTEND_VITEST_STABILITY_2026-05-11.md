# Frontend Vitest Stability Report

Date: 2026-05-11
Scope: `frontend` test reliability (Priority-1 execution)

## Context

During full-suite runs, tests were often green but the process could fail with:

- `Unhandled Error: [vitest-worker]: Timeout calling "onTaskUpdate"`

This made CI signal unreliable even when assertions passed.

## Baseline Findings

1. Initial full run showed heavy React `act(...)` warnings and one unstable worker timeout path.
2. Reproduction with dot reporter surfaced intermittent suite-level instability and occasional flaky failures under high concurrency pressure.
3. Isolated test runs for suspect files passed consistently, indicating orchestration/runtime pressure more than deterministic logic defects.

## Change Applied

Updated `vitest.config.ts`:

- `testTimeout: 30000 -> 60000`
- Added `hookTimeout: 30000`
- Added `teardownTimeout: 30000`
- Added `pool: 'forks'`
- Added `maxWorkers: 4`

Rationale: reduce worker RPC back-pressure and prevent false negatives from orchestration timeouts in a large jsdom + React 19 suite.

## Verification Evidence

Commands run:

1. `npm test -- 'src/components/workspace/panels/__tests__/MetricDrillDownDrawer.test.tsx' 'src/app/(agency)/trips/[tripId]/__tests__/packet-page.test.tsx'`
2. `npm test`

Final result:

- `Test Files  87 passed (87)`
- `Tests  790 passed (790)`
- No `onTaskUpdate` unhandled worker timeout

## Residual Risk / Follow-up

- React `act(...)` warnings still exist across several UI tests.
- These are not currently failing assertions, but they remain a reliability smell and should be cleaned up incrementally.

Suggested next hardening unit:

- Normalize async test patterns (`findBy*`, explicit user-event awaits, deterministic mock timing) in top warning-heavy files:
  - `src/components/workspace/panels/__tests__/CaptureCallPanel.test.tsx`
  - `src/app/(agency)/trips/[tripId]/__tests__/layout.test.tsx`
  - `src/components/workspace/panels/__tests__/MetricDrillDownDrawer.test.tsx`

