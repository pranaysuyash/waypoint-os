# Workbench UX review addendum (2026-06-28)

## Status Note

As of 2026-06-30, the code-side fix documented here is closed, but the live browser proof gap remains open. Keep this addendum active until that runtime check is re-run.

## Issue

The workbench risk review surface was still exposing internal QA language as product copy, and the agency shell/workbench controls were not adapting cleanly on narrower viewports.

## Decision

- Keep leakage detection strict, but stop surfacing raw gate language and field-key jargon in the operator-facing review UI.
- Summarize message-review failures in plain operational language and keep raw leakage details behind diagnostic output only.
- Improve shell/workbench responsiveness by reducing fixed-height/fixed-row pressure and allowing mobile-first navigation/content flow.
- Keep the onboarding welcome card non-blocking and compact on the workbench route.

## Files

- `frontend/src/app/(agency)/workbench/SafetyTab.tsx`
- `frontend/src/components/workspace/panels/SafetyPanel.tsx`
- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/components/onboarding/WelcomeModal.tsx`
- `frontend/src/lib/safety-review-copy.ts`
- `frontend/src/app/(agency)/workbench/__tests__/SafetyTab.test.tsx`
- `frontend/src/components/workspace/panels/__tests__/SafetyPanel.test.tsx`
- `frontend/src/components/onboarding/__tests__/WelcomeModal.test.tsx`

## Verification

- Focused frontend tests passed:
  - `./node_modules/.bin/vitest run src/app/(agency)/workbench/__tests__/SafetyTab.test.tsx src/components/onboarding/__tests__/WelcomeModal.test.tsx src/components/workspace/panels/__tests__/SafetyPanel.test.tsx src/components/layouts/__tests__/Shell.test.tsx`
- Repo-wide frontend typecheck is still failing outside this blast radius in existing tests and fixtures (`overview`, `ops`, `StrategyTab`, `ChangeHistoryPanel`, `strategy-preview`, `trip-picker-label`).

## Remaining runtime gap

- Live browser proof is still pending because the existing local frontend listener on `http://localhost:3000` accepted the port but did not return a response within a 5-second curl window during this pass.
