# Design-System Migration: Stage 1

**Date:** 2026-05-09
**Scope:** Shared primitives, initial adoptions, bug fixes
**Status:** Complete — all tests pass, build compiles

## Components Added

| Component | File | Type | Purpose |
|---|---|---|---|
| `Pill` | `src/components/ui/pill.tsx` | Shared primitive | Reusable filter/chip pill with 4 tone variants (neutral, attention, ownership, risk) plus muted mode and role variant |
| `ProgressSteps` | `src/components/ui/progress-steps.tsx` | Shared primitive | Multi-step progress indicator with 3 states (completed/current/pending), horizontal/vertical, responsive label support |
| `StatusBadge` | `src/components/ui/status-badge.tsx` | Shared primitive | Typed status badge accepting a `StatusMap` — per-screen maps define color/icon/label, no global color mapping assumed |
| `Toast` + `ToastContainer` | `src/components/ui/toast.tsx` | Shared system | Stacked transient notifications with 4 types (success/error/info/warning), 5s auto-dismiss, accessible live-region |
| `toast-store` | `src/lib/toast-store.ts` | Zustand store | Toast state management with `add`/`remove` operations and standalone `toast()` convenience function |
| `ConfirmDialog` | `src/components/ui/confirm-dialog.tsx` | Shared primitive | Accessible confirmation modal built on `Modal`, supports danger variant with alert icon, custom labels |
| `ThemeProvider` | `src/components/ThemeProvider.tsx` | Layout provider | Applies `theme-{currentTheme}` CSS class to `document.body` via `useEffect`, decoupled from store DOM manipulation |

## Adoptions

| Primitive | Adopted In | File | What Changed |
|---|---|---|---|
| `ProgressSteps` | `PipelineFlow` | `src/app/(agency)/workbench/PipelineFlow.tsx` | Replaced 107 lines of hand-rolled step indicators (div-based, manual ARIA) with `ProgressSteps` component. Exports `PIPELINE_STAGES`, `PipelineStageId`, `toPipelineStageId` preserved. |
| `StatusBadge` | Reviews page | `src/app/(agency)/reviews/page.tsx` | Replaced 25-line local `StatusBadge` component (memoized, inline color mapping) with shared `StatusBadge` using `REVIEW_STATUS_MAP`. |
| `Toast` | SuitabilityPanel | `src/components/workspace/panels/SuitabilityPanel.tsx` | Replaced inline `toast` state + div-based rendering with `toast()` function from `lib/toast-store.ts`. Removed `toast` state variable and inline notification div. |
| `ToastContainer` | Agency layout | `src/app/(agency)/layout.tsx` | Mounted `ToastContainer` in agency route group layout, making toasts available across all agency pages. |
| `ConfirmDialog` | Workbench Reset | `src/app/(agency)/workbench/page.tsx` | Reset button now opens `ConfirmDialog` (danger variant) instead of firing `handleReset` immediately. State: `isResetDialogOpen`. |
| `ThemeProvider` | Providers | `src/components/providers.tsx` | Wired `ThemeProvider` inside `QueryClientProvider` in `Providers` component. Applies `theme-agency` class on hydration. |

## Behavior Preserved

- `PipelineFlow`: Stage ordering, aria-current on active step, completed/pending states, responsive labels
- `StatusBadge` in reviews: Same colors, icons, labels — only the component source changed
- `SuitabilityPanel`: Override flow unchanged — toast messages appear in the same situations with the same text
- `ConfirmDialog`: Uses existing `Modal` (focus trap, escape, ARIA) — no regression in modal behavior
- `themeStore`: `setTheme` no longer manipulates `document.body` directly — `ThemeProvider` handles it via `useEffect`

## Bug Fixes

| Bug | File | Fix |
|---|---|---|
| `MarketingVisuals.tsx` imported wrong CSS module (classes from `marketing-v2.module.css` but import was `marketing.module.css`) | `src/components/marketing/MarketingVisuals.tsx` | Changed import to `./marketing-v2.module.css` |
| `useMemo` used as `setInterval` in `DataTransformationHero` | `src/components/marketing/MarketingVisuals.tsx` | Replaced `useMemo` with `useEffect` + proper cleanup |
| `CurrencyContext.formatAsPreferred` stub (ignored `fromCurrency`, always formatted as `en-IN`) | `src/contexts/CurrencyContext.tsx` | Now calls real `formatMoney` from `@/lib/currency` |
| `useRuntimeVersion` dead fetch (fetched API but hardcoded label) | `src/hooks/useRuntimeVersion.ts` | Uses `payload.version` when available, falls back to "Operations live" |
| `themeStore.setTheme` DOM manipulation in Zustand action | `src/stores/themeStore.ts` | Removed DOM manipulation — moved to `ThemeProvider` |
| `TripContext.useTripContext` type narrowing for optional mode | `src/contexts/TripContext.tsx` | Added proper TypeScript overloads for `useTripContext()` and `useTripContext({ optional: true })` |

## Test Results

- **Total tests:** 731 (81 test files)
- **New tests added:** 20 across 4 new test files (toast, status-badge, progress-steps, confirm-dialog)
- **Existing tests modified:** 3 (PipelineFlow, FollowUpCard, DecisionPanel integration test)
- **Regressions:** 0 — all 711 pre-existing tests still pass

## Deferred Follow-Ups

- `IntakePanel` split (P1) — high-risk, not in this task scope
- `api-client.ts` split (P2) — broad refactor, deferred
- `DataTable` component (P2) — deferred
- React Query migration for `useAgencySettings`, `useFieldAuditLog`, `useSpineRun` (P2) — deferred
- `tokens.ts` adoption in inline styles (P2) — deferred
- `marketing-v2.module.css` still has hardcoded hex colors instead of CSS custom properties — cosmetic issue, not blocking
- `workbench.module.css` uses `--color-*` naming vs canonical `--accent-*`/`--bg-*`/`--text-*` — deferred
- `FilterPill.tsx` is now a re-export from `ui/pill.tsx` — consider removing the shim file once all imports are updated
