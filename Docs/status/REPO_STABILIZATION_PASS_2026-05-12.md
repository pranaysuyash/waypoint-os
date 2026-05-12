# Repo Stabilization Pass

Date: 2026-05-12
Scope: Current dirty tree stabilization after parallel-agent frontend/backend/docs changes.

## Baseline

Fresh read-only status showed substantial parallel-agent drift across frontend, backend, specs, evals, and docs.
This pass avoided git write operations and did not revert unrelated work.

## Findings

1. Frontend typecheck had regressed from the prior documented green state.
2. Focused backend D6/public-checker/router tests were still green.
3. Frontend lint remains the active stabilization track. The remaining findings are React hook-rule issues concentrated in behavior-heavy components, not a low-risk text cleanup batch.

## Changes Applied

1. Restored frontend typecheck:
   - `frontend/src/components/workspace/panels/__tests__/ExtractionHistoryPanel.test.tsx`
     - Removed stale `container` destructuring and used `document.body.textContent` for the no-emoji assertion.
   - `frontend/src/components/workspace/panels/PacketPanel.tsx`
     - Parallel drift had already aligned packet ambiguity/contradiction rendering with canonical `Ambiguity.raw_value` and `PacketContradiction.values` / `sources` before final verification.
2. Reduced low-risk lint warnings:
   - `frontend/src/app/(agency)/overview/PageClient.tsx`
     - Memoized `safeData` so `stageTotal` dependencies are stable.
   - `frontend/src/components/ui/tabs.tsx`
     - Wrapped `getTabLabel` in `useCallback`.
   - `frontend/src/app/(public)/booking-collection/[token]/PageClient.tsx`
     - Added `fields.travelers` as the real dependency for generated traveler keys.
3. Fixed a real behavior bug found during lint review:
   - `frontend/src/app/(agency)/inbox/PageClient.tsx`
     - `handleBulkAssign` previously computed selected trip IDs and cleared selection without calling `assignTrips`.
     - It now calls the canonical assignment mutation when the selection is non-empty.

## Verification

Commands run:

```bash
cd frontend && npm run typecheck
# PASS

cd frontend && npm test -- "src/lib/__tests__/nav-modules.test.ts" \
  "src/components/workspace/panels/__tests__/ExtractionHistoryPanel.test.tsx" --reporter=dot
# 2 files passed, 11 tests passed

.venv/bin/python -m pytest \
  tests/test_validation_split.py \
  tests/test_public_checker_contract_authority.py \
  tests/test_live_checker_service.py \
  tests/test_legacy_ops_router_behavior.py \
  tests/evals/test_public_authority.py \
  tests/evals/test_d6_gate_snapshot.py -q
# 39 passed

set -a; source .env; set +a; .venv/bin/python tools/dev_server_manager.py restart --service backend
# backend: healthy

curl -sS -o /dev/null -w 'backend %{http_code}\n' http://localhost:8000/health
# backend 200

curl -sS -o /dev/null -w 'frontend %{http_code}\n' http://localhost:3000
# frontend 200
```

Lint snapshot:

```text
Before this small slice: 60 total, 45 errors, 15 warnings
After this small slice:  53 total, 42 errors, 11 warnings
```

Remaining categories:

```text
26 react-hooks/preserve-manual-memoization
13 react-hooks/set-state-in-effect
11 react-hooks/exhaustive-deps
3  react-hooks/immutability
```

## Remaining Work

Next safe unit is not a broad mechanical cleanup. It should be handled component-by-component with focused tests:

1. `frontend/src/app/(agency)/workbench/OpsPanel.tsx`
   - 18 lint errors.
   - Needs memoization/dependency review around trip identity, document fetches, pending booking flows, link actions, and save handlers.
2. `frontend/src/components/workspace/panels/IntakePanel.tsx`
   - 8 errors, 6 warnings.
   - Includes immutability findings and planning-editor callback dependency issues; requires behavior-aware refactor.
3. `frontend/src/app/(agency)/workbench/PageClient.tsx`
   - 6 errors, 4 warnings.
   - Store dependency and memoization issues should be reviewed against Zustand/store usage.
4. Single-error async effect panels:
   - `BookingExecutionPanel.tsx`
   - `ConfirmationPanel.tsx`
   - `ExecutionTimelinePanel.tsx`
   - `ExtractionHistoryPanel.tsx`
   - `TimelinePanel.tsx`
   - `useFieldAuditLog.ts`

Each batch should run:

```bash
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm test -- <focused tests> --reporter=dot
```

## Decision

Do not silence the remaining lint rules with blanket disables. The remaining errors are mostly behavior-level React hook contracts, so the long-term fix is reducer/query-state or effect-boundary refactoring with focused regression tests.
