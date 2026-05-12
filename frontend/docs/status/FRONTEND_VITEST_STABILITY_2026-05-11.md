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

## Public Marketing Test Hardening Addendum

Timestamp: Mon May 11 22:10:42 IST 2026

### Fresh Failure Mode

After later parallel-agent work, `src/app/__tests__/public_marketing_pages.test.tsx` became the active full-suite blocker:

- Isolated run: timed out in the public marketing page tests and cleanup hook.
- Full run: `src/app/__tests__/public_marketing_pages.test.tsx` failed and emitted `ReferenceError: requestAnimationFrame is not defined` from real `gsap/ScrollTrigger` runtime code.

Root cause: the GSAP/ScrollTrigger mock lived only in the public marketing test file, while jsdom setup only polyfilled `matchMedia`. Under full-suite module pressure, real animation code could still enter the test runtime. The test environment also lacked a global `requestAnimationFrame`/`cancelAnimationFrame` browser API.

### Change Applied

Updated `frontend/vitest.setup.tsx`:

- Added global `requestAnimationFrame` and `cancelAnimationFrame` jsdom polyfills.
- Added shared Vitest mocks for `gsap` and `gsap/ScrollTrigger`.
- Kept the mock boundary in test setup so production browser behavior still uses real GSAP.

### Verification Evidence

Commands run:

1. `npx vitest run src/app/__tests__/public_marketing_pages.test.tsx`
2. `npx vitest run`
3. `npx next build`
4. `npx tsc --noEmit`

Results:

- Public marketing target: `1 passed`, `9 tests passed`.
- Full frontend suite: `106 passed`, `848 tests passed`.
- `npx next build` was attempted after the fix but was blocked by the active local `next dev` server lock: `Another next build process is already running.`
- `npx tsc --noEmit` was attempted as a non-disruptive compile check but failed because generated Next type files under `.next/types` and `.next/dev/types` were absent while the current `tsconfig.json` includes those paths.

### Residual Risk / Follow-up

- The public marketing target now passes, but it remains heavy compared with normal component tests. The latest isolated run took about 54 seconds, with the itinerary checker render test around 10 seconds.
- Existing React `act(...)` warnings remain non-failing in async UI tests, especially booking collection, trip layout, capture call, followups, and extraction history suites.
- A production build should be rerun after stopping or moving the active local `next dev` server, since Next currently prevents concurrent build/dev use of the same `.next` directory.

## Async UI Warning Cleanup Addendum

Timestamp: Tue May 12 09:08:08 IST 2026

### Fresh Baseline

The warning-hardening slice was rechecked after parallel-agent changes. The targeted baseline command was:

`npx vitest run 'src/app/(public)/booking-collection/__tests__/page.test.tsx' 'src/app/(agency)/trips/[tripId]/__tests__/layout.test.tsx' 'src/components/workspace/panels/__tests__/CaptureCallPanel.test.tsx' 'src/app/(agency)/trips/[tripId]/followups/__tests__/page.test.tsx' 'src/components/workspace/panels/__tests__/ExtractionHistoryPanel.test.tsx'`

Baseline result: all 71 tests passed, but React `act(...)` warnings still appeared in:

- `booking-collection/__tests__/page.test.tsx`
- `trips/[tripId]/__tests__/layout.test.tsx`
- `CaptureCallPanel.test.tsx`
- `followups/__tests__/page.test.tsx`
- `ExtractionHistoryPanel.test.tsx`

### Changes Applied

- `BookingCollectionPage` now cancels the async `params.then(...)` dispatch on unmount.
- `WorkspaceTripLayoutShell` now waits for a loaded trip before fetching timeline rail data.
- Booking collection loading-state test uses a pending params promise so it only asserts the initial loading contract.
- Trip layout tests mock and await the timeline rail fetch where the rail is part of the rendered contract.
- Capture call loading test resolves its controlled request inside `act(...)` and waits for `onSave`.
- Followups sort test uses awaited `userEvent` after initial data load.
- Extraction history test no longer mounts a second component instance only to assert the same text content.

### Verification Evidence

Commands run:

1. `npx vitest run 'src/app/(public)/booking-collection/__tests__/page.test.tsx' 'src/app/(agency)/trips/[tripId]/__tests__/layout.test.tsx' 'src/components/workspace/panels/__tests__/CaptureCallPanel.test.tsx' 'src/app/(agency)/trips/[tripId]/followups/__tests__/page.test.tsx' 'src/components/workspace/panels/__tests__/ExtractionHistoryPanel.test.tsx'`
2. `npx vitest run 'src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx' -t 'payment'`
3. `npx vitest run 'src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx'`
4. `npx vitest run`
5. `npx next build`

Results:

- Targeted warning suites: `5 passed`, `71 tests passed`, with no React `act(...)` warning output.
- Full frontend suite clean rerun: `112 passed`, `869 tests passed`.
- Production build: compiled successfully, TypeScript completed, and all 43 static pages generated.

### Notes

- One first full-suite run exposed two transient `OpsPanel` payment tests, but both payment-targeted and whole-file isolated runs passed, and the subsequent full-suite rerun passed. This was treated as suite-pressure noise, not a deterministic payment-tracking regression.
- The `/api/trips` invalid-JSON route test still logs its intentional `SyntaxError` to stderr while passing. That is not part of the React async warning cleanup.
