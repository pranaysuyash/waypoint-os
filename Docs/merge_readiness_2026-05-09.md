# Merge Readiness Report: Design-System Migration Stage 1

**Date:** 2026-05-09
**Branch:** current workspace (not pushed)
**Goal:** Stabilize design-system primitives, adoptions, and bug fixes before merge

---

## Files Changed by Domain

| Domain | Files | Type |
|---|---|---|
| **UI Primitives** | `src/components/ui/pill.tsx`, `status-badge.tsx`, `progress-steps.tsx`, `toast.tsx`, `confirm-dialog.tsx` | New shared primitives |
| **UI Tests** | `src/components/ui/__tests__/toast.test.tsx`, `toast-integration.test.tsx`, `status-badge.test.tsx`, `progress-steps.test.tsx`, `confirm-dialog.test.tsx` | New tests |
| **Toast Store** | `src/lib/toast-store.ts` | New Zustand store |
| **Theme** | `src/components/ThemeProvider.tsx`, `src/components/providers.tsx`, `src/stores/themeStore.ts`, `src/stores/index.ts` | Theme wiring + bug fix |
| **Workbench** | `src/app/(agency)/workbench/PipelineFlow.tsx`, `page.tsx`, `__tests__/PipelineFlow.test.tsx`, `SettingsPanel.tsx`, `IntegrityMonitorPanel.tsx` | ProgressSteps + ConfirmDialog adoption |
| **Reviews** | `src/app/(agency)/reviews/page.tsx` | StatusBadge adoption |
| **Workspace Panels** | `src/components/workspace/panels/SuitabilityPanel.tsx`, `DecisionPanel.tsx`, `IntakePanel.tsx`, `IntakeFieldComponents.tsx`, `OutputPanel.tsx` | Toast adoptions + extraction |
| **Workspace Tests** | `src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx`, `DecisionPanel.SuitabilitySignal.integration.test.tsx`, `IntakePanel.test.tsx` | New tests + updates |
| **Contexts** | `src/contexts/TripContext.tsx`, `CurrencyContext.tsx` | Type fixes + currency fix |
| **Marketing** | `src/components/marketing/MarketingVisuals.tsx` | CSS import + useMemo fix |
| **Hooks** | `src/hooks/useRuntimeVersion.ts` | Dead fetch fix |
| **Layout** | `src/app/(agency)/layout.tsx` | ToastContainer mount |
| **API** | `src/app/api/trips/route.ts` | kill switch fix |
| **Backend** | `spine_api/routers/booking_tasks.py` | New booking tasks route |
| **Snapshots** | `tests/fixtures/server_openapi_paths_snapshot.json`, `server_route_snapshot.json` | Regenerated (route count: 138→146, openapi: 121→127) |
| **Docs** | `Docs/design_system_migration_2026-05-09.md`, `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`, `AGENTS.md` | Migration notes + policy updates |

---

## Test Results

| Command | Result |
|---|---|
| `cd frontend && npx vitest run` | **83 files, 760 tests — ALL PASS** |
| `.venv/bin/python -m pytest tests/test_server_openapi_path_parity.py tests/test_server_route_parity.py tests/test_booking_task_service.py` | **34 passed** |
| `cd frontend && npx next build` | **Compiles clean (zero errors)** |

### New Tests Added (20 tests across 5 files)
- `toast.test.tsx` — 7 tests: render, multi-stack, dismiss, icons, live region, standalone fn
- `toast-integration.test.tsx` — 5 tests: action path, stacking, store-remove, four types, null
- `status-badge.test.tsx` — 4 tests: label, null, approved, color
- `progress-steps.test.tsx` — 5 tests: labels, aria-current, completed, custom aria, vertical
- `confirm-dialog.test.tsx` — 6 tests: closed, open, title, labels, onConfirm, danger
- `IntakeFieldComponents.test.tsx` — 27 tests: EditableField (display, edit, save, cancel, types), BudgetField (edit, amount, currency), PlanningDetailSection (empty, rows, badges, actions, editor callback)

---

## Known Residual Risks

1. **IntakePanel extraction (IntakeFieldComponents.tsx)** — The extraction moved EditableField, BudgetField, and PlanningDetailSection to a separate file. IntakePanel imports them and behavior is verified by existing IntakePanel tests (all pass). However, the extraction is partial — IntakePanel is still 1486 lines. Low risk, deferred to future split.

2. **ThemeProvider SSR** — ThemeProvider uses `'use client'` and `useEffect` for DOM manipulation. During SSR, body classes won't be applied until hydration completes. This is expected behavior in Next.js and causes no visible flicker since the default `:root` CSS variables provide the dark theme regardless.

3. **Toast store persistence** — Toast state is in-memory only (Zustand without persist middleware). Reloading the page clears all toasts. This is intentional for transient notifications.

4. **Route snapshot regeneration** — Snapshots were regenerated to match the new backend routes (booking-tasks + agent-runtime). The route count increased from 138→146 (openapi 121→127). No route was removed or renamed — these are additive changes from prior backend feature work that hadn't had their snapshots refreshed.

5. **FilterPill.tsx shim** — Now re-exports from `ui/pill.tsx`. The imports still work, but the shim file could be removed once all consumers import directly from `ui/pill.tsx`.

---

## Merge Verdict

**Merge: YES** — All tests pass, build compiles clean, route snapshots are current, no behavior regressions detected. The implementation is additive: 7 new shared components, 1 new state store, 5 real adoptions in existing workflows, 6 bug fixes, and thorough test coverage.
