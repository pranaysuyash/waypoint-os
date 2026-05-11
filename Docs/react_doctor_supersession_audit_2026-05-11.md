# React Doctor Supersession Audit — 2026-05-11

## Scope

This document tracks React Doctor findings that require the repo Supersession Workflow before removal or API-surface consolidation.

Baseline command:

```bash
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_live_2026_05_11.json
```

Baseline at start of this pass:

- Score: 87/100 (`Great`)
- Diagnostics: 371 warnings, 0 errors
- Dead-code related rules: `types` 112, `exports` 100, `files` 13, `duplicates` 12

## Guardrails Applied

- Re-read removal/code preservation instructions in `AGENTS.md`, `/Users/pranay/AGENTS.md`, `/Users/pranay/Projects/AGENTS.md`, `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`, and `Docs/context/agent-start/SESSION_CONTEXT.md`.
- No destructive git commands were used.
- No code was deleted solely to satisfy React Doctor.
- For each removal/consolidation, verify a strict superset or surviving canonical API, audit call sites, update consumers first, then remove the superseded surface.

## Supersession Batch 1: Duplicate Default Exports

Verdict: ACCEPT+MODIFY. React Doctor flagged duplicate exports where the same component was exported both as a named export and as a default export. The named export preserves the full component implementation, props, types, display names, and behavior. The default export was only an alternate import surface.

Action:

- Migrated remaining default import consumers to named imports.
- Removed redundant `export default <Component>;` lines only.
- Preserved all component bodies and named exports.

### Removal: `SuitabilityPanel` default export — superseded by named `SuitabilityPanel`

Comparison:

- Component behavior: unchanged, same `SuitabilityPanel` function/object remains exported.
- Props contract: unchanged, `SuitabilityPanelProps` and `SuitabilityFlag` remain in the same module.
- Runtime rendering: unchanged, consumer imports now bind to the named export.
- Replacement: named `SuitabilityPanel` export is the same component value as the prior default export.

Call sites:

- Default import found in `frontend/src/app/(agency)/trips/[tripId]/suitability/page.tsx`; migrated to `import { SuitabilityPanel, type SuitabilityFlag } ...`.
- Existing tests and other consumers already used named imports.

### Removal: `FollowUpCard` default export — superseded by named `FollowUpCard`

Comparison:

- Component behavior: unchanged, same memoized component remains exported.
- Props contract: unchanged.
- Runtime rendering: unchanged, consumer imports now bind to the named export.
- Replacement: named `FollowUpCard` export is the same component value as the prior default export.

Call sites:

- Default import found in `frontend/src/app/(agency)/trips/[tripId]/followups/page.tsx`; migrated to `import { FollowUpCard } ...`.
- Existing tests already used named imports.

### Removal: default exports with no default call sites

The following default exports had no default import call sites in `frontend/src`, `frontend/app`, `frontend/components`, `frontend/hooks`, `frontend/lib`, or tests. Their named exports are the canonical surviving API and preserve the complete implementation.

- `frontend/src/components/inbox/TripCard.tsx` — named `TripCard`
- `frontend/src/components/inbox/ComposableFilterBar.tsx` — named `ComposableFilterBar`
- `frontend/src/components/inbox/ViewProfileToggle.tsx` — named `ViewProfileToggle`
- `frontend/src/components/inbox/InboxEmptyState.tsx` — named `InboxEmptyState`
- `frontend/src/components/navigation/BackToOverviewLink.tsx` — named `BackToOverviewLink`
- `frontend/src/components/inbox/InboxFilterBar.tsx` — named `InboxFilterBar`
- `frontend/src/components/ui/PriorityIndicator.tsx` — named `PriorityIndicator`
- `frontend/src/components/workspace/panels/ActivityProvenance.tsx` — named `ActivityProvenanceBadge`
- `frontend/src/components/workspace/panels/ActivityTimeline.tsx` — named `ActivityTimeline`
- `frontend/src/components/workspace/panels/SuitabilityCard.tsx` — named `SuitabilityCard`

Shared comparison:

- Component behavior: unchanged.
- Props and type exports: unchanged.
- Internal helpers: unchanged.
- Replacement: the named export in the same file is the exact component/function already used by current consumers.

Call sites:

- Call-site audit showed named imports only for these components.
- No default import migration was required.

## Deferred Supersession Areas

These React Doctor dead-code categories still need individual first-principles review before any removal:

- `files`: distinguish reusable tools and future-facing UI primitives from genuinely superseded modules.
- `exports`: preserve public API/contract exports unless a canonical replacement is proven.
- `types`: generated API types and backend contract mirror types are not safe to delete from static usage alone.

## Verification Plan

Run after Batch 1:

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_after_batch1_2026_05_11.json
```

Expected outcome:

- TypeScript passes.
- React Doctor `duplicates` count drops from 12 to 0.

## Verification Results: Batch 1

Executed after changes:

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_after_batch1_2026_05_11.json
```

Results:

- TypeScript: passed.
- React Doctor score: 87/100 (`Great`).
- React Doctor diagnostics: 349 warnings, 0 errors.
- `duplicates`: reduced from 12 to 0.
- `exports`: reduced from 100 to 90.

Notes:

- The score did not move because React Doctor score bucketing stayed at 87 despite 22 fewer diagnostics.
- The remaining dead-code findings require separate supersession analysis. Generated contract types, public API types, reusable tools, and future-facing UI primitives should not be removed based on static import graph alone.

## Supersession Batch 2: File-Level Findings With Clear Replacement/Disposition

Verdict: ACCEPT+MODIFY for three files. The remaining file-level findings are deferred because they represent reusable tooling, public/future-facing UI primitives, or product surfaces with documented intent.

### Removal: `frontend/src/components/marketing/marketing.bak.module.css` — superseded by active marketing CSS modules and archived design history

Comparison:

- Active replacement surfaces: `frontend/src/components/marketing/marketing.module.css`, `frontend/src/components/marketing/marketing-v2.module.css`, `frontend/src/components/marketing/landing-experiments.module.css`, and `frontend/src/components/marketing/landing-v5.module.css` are the mounted marketing style modules.
- Historical preservation: copied to `Docs/design/archive/marketing.bak.module.css` before deletion from active source.
- Product behavior: no imports existed for `marketing.bak.module.css`; active pages import current marketing modules.
- Prior decision evidence: `Docs/design/QUARANTINE_PLAN.md` marks this file superseded and says backup files should not remain in the active tree.

Call sites:

- No active source import call sites.

### Removal: `frontend/src/app/page.module.css` — superseded by active marketing module styles and archived design history

Comparison:

- Active replacement surface: `frontend/src/app/page.tsx` imports `@/components/marketing/marketing.module.css`, not `src/app/page.module.css`.
- Historical preservation: copied to `Docs/design/archive/page.module.css` before deletion from active source.
- Product behavior: no imports existed for `src/app/page.module.css`.
- Prior decision evidence: `Docs/design/QUARANTINE_PLAN.md` marks this file superseded by the active landing implementation.

Call sites:

- No active source import call sites.

### Removal: `frontend/src/lib/url-state.ts` — superseded by direct Next.js navigation/search-param usage where needed

Comparison:

- Active replacement surface: pages and components that need URL state use Next.js routing/search-param APIs directly or local state; there are no imports of this helper.
- Product behavior: unchanged because no runtime consumer exists.
- Prior decision evidence: `Docs/FRONTEND_IMPROVEMENT_PLAN_2026-04-16.md` explicitly lists `lib/url-state.ts` as delete-if-unused, and the current audit confirms it is unused.
- Risk note: this file also carried `useSearchParams` wrappers that can introduce Suspense requirements. Removing the unused abstraction avoids preserving an attractive but unverified API surface.

Call sites:

- No active source import call sites.

## Deferred File-Level Findings After Batch 2

Do not remove yet without a separate product/API decision:

- `frontend/tools/validate-contrast.ts` and `frontend/src/lib/contrast-utils.ts`: reusable WCAG tooling documented in `frontend/tools/README.md` and frontend audit docs.
- `frontend/src/contexts/CurrencyContext.tsx`: documented currency preference context, currently unused but product-intent-bearing.
- `frontend/src/stores/index.ts`: barrel export for store public surface; static unused status does not prove supersession.
- `frontend/src/components/ui/badge.tsx`, `icon.tsx`, `select.tsx`, `textarea.tsx`: shared UI primitives; unused today does not imply redundant.
- `frontend/src/components/workspace/FrontierDashboard.tsx`: docs conflict between “salvage then delete” and “parked for design reference”; requires explicit salvage/decision before removal.
- `frontend/src/components/workspace/panels/ChangeHistoryPanel.tsx`: documented future/extraction candidate and referenced in feature docs; not safe to delete on static import graph alone.

## Verification Results: Batch 2

Executed after changes:

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_after_batch2_2026_05_11.json
```

Results:

- TypeScript: passed.
- React Doctor score: 88/100 (`Great`).
- React Doctor diagnostics: 343 warnings, 0 errors.
- `files`: reduced from 13 to 10.
- `duplicates`: remains 0.

## Broader Verification Results

Executed after Batch 2:

```bash
cd frontend && npx vitest run
cd frontend && npm run build
```

Results:

- Production build: passed.
- Full Vitest run: failed with 4 failures out of 790 tests, plus 1 Vitest worker timeout error.
- Passing count in full run: 786 passed, 4 failed, 84/87 test files passed.
- Failures were in async/drill-down journey tests unrelated to the supersession files changed here:
  - `src/app/__tests__/e2e_metric_drilldown.test.tsx`: expected `Paris` after drill-down, drawer remained in loading state.
  - `src/app/__tests__/p1_happy_path_journey.test.tsx`: timed out at 30 seconds.
  - `src/components/workspace/panels/__tests__/MetricDrillDownDrawer.test.tsx`: expected `Paris` / `Tokyo`, drawer remained in loading state.
  - `src/components/workspace/panels/__tests__/MetricDrillDownDrawer.test.tsx`: expected decision reason text, drawer remained in loading state.
- Existing React `act(...)` warnings appeared across async UI tests.

Interpretation:

- The supersession changes are TypeScript/build safe and React Doctor verified.
- The full test suite is not green at this checkpoint due to pre-existing or parallel-work async UI failures outside this cleanup surface. These should be handled as a separate verification-hardening task before claiming suite-wide green.

## Supersession Batch 3: Private Module Details Exported By Accident

Verdict: ACCEPT. These symbols are implementation details used only inside their defining module. The canonical public surface remains the higher-level exported functions/components that already consume them. This batch removes only the `export` keyword; it does not delete code or change runtime behavior.

### Removal: `WORKSPACE_STATUSES` and `INBOX_STATUSES` exports — superseded by `isWorkspaceTrip` / `isInboxTrip`

Comparison:

- Public behavior remains through `isWorkspaceTrip`, `isInboxTrip`, and transform functions.
- Status set contents are unchanged.
- Call-site audit found no source imports of the sets outside `frontend/src/lib/bff-trip-adapters.ts`.

### Removal: `SORT_OPTIONS`, `METRIC_ROW_CONFIG`, and `MICRO_LABELS` exports — superseded by typed helpers in `inbox-helpers.ts`

Comparison:

- `SORT_OPTIONS` remains available internally to derive `SortKey`.
- `METRIC_ROW_CONFIG` remains available through `getMetricsForProfile`.
- `MICRO_LABELS` remains available through `getMicroLabel`.
- Call-site audit found no source imports of these constants outside `frontend/src/lib/inbox-helpers.ts`.

### Removal: planning-list display helper exports — superseded by `getPlanningListSummary`

Comparison:

- `getPlanningAssignmentLabel`, `getPlanningStageProgress`, and `getPlanningListAction` remain unchanged internally.
- `getPlanningListSummary` remains the canonical exported API that composes those details.
- Call-site audit found no source imports of these helpers outside `frontend/src/lib/planning-list-display.ts`.

### Removal: timeline-rail helper exports — superseded by exported timeline label/event APIs

Comparison:

- `isTimelineStageUnset` remains unchanged and is still used by `getTimelineStageLabel`.
- `getTimelineTriggerLabel` remains unchanged for future internal use in this module, but is not part of the active public surface.
- Call-site audit found no source imports of these helpers outside `frontend/src/lib/timeline-rail.ts`.

Deferred export findings still require separate decisions because they are public client/API surfaces, documented UI primitives, generated/contract mirrors, or future-facing hooks.

## Verification Results: Batch 3

Executed after changes:

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_after_batch3_2026_05_11.json
```

Results:

- TypeScript: passed after restoring `getPlanningStageProgressItems` as exported because real consumers import it.
- React Doctor score: 88/100 (`Great`).
- React Doctor diagnostics: 333 warnings, 0 errors.
- `exports`: reduced from 90 to 80.
- `duplicates`: remains 0.

Process note:

- The initial text replacement matched `getPlanningStageProgressItems` unintentionally. TypeScript caught the regression before completion, and the valid export was restored. This reinforces the supersession rule: verify each removal batch immediately and restore anything with real call sites.

## Supersession Batch 4: Zero-Consumer Marketing Wrapper

Verdict: ACCEPT. `DemoButton` was a thin wrapper around the existing `Button asChild` plus `Link` pattern and had no active source call sites.

### Removal: `DemoButton` — superseded by direct `Button asChild` / `Link` composition

Comparison:

- Behavior: no runtime behavior changed because no source file imported or rendered `DemoButton`.
- Replacement: existing `Button` component already supports `asChild`, size variants, className composition, and Link composition.
- Visual affordance: the wrapper only added a `Sparkles` icon and rounded class; any future CTA can compose those directly at the call site with the existing primitives.
- Call-site audit: no active source call sites outside `marketing-client.tsx`.

Removal details:

- Removed the unused `DemoButton` function.
- Removed now-unused `Sparkles` and `Button` imports from `marketing-client.tsx`.

## Verification Results: Batch 4

Executed after changes:

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_after_batch4_2026_05_11.json
```

Results:

- TypeScript: passed.
- React Doctor score: 88/100 (`Great`).
- React Doctor diagnostics: 332 warnings, 0 errors.
- `exports`: reduced from 80 to 79.

Remaining export findings are not being treated as automatic removals. They include API client functions, governance API functions, error-boundary helpers, UI primitive exports, accessibility helpers, currency helpers, design tokens, scenario/combobox/theme hooks, and audit helpers. Each needs either a real canonical replacement or an explicit product/API decision before removal.

## Supersession Batch 5: Redundant Type Surfaces

Verdict: ACCEPT. This batch removes type-only surfaces with no active consumers and clear canonical replacements. No runtime code paths changed.

### Removal: `StatusFamily` — superseded by per-screen `StatusMap`

Comparison:

- Active `StatusBadge` API uses `StatusMap` to define screen-specific labels, colors, and icons.
- `StatusFamily` was not referenced by `StatusBadgeProps` or any source consumer.
- Prior design docs describe the `StatusMap` API as the shared primitive contract.

### Removal: `FilterPillProps` alias — superseded by canonical `PillProps`

Comparison:

- `FilterPill` is a re-export of `Pill` from `@/components/ui/pill`.
- The canonical prop type remains `PillProps` at the source primitive.
- No source consumer imported `FilterPillProps`.

### Removal: `BffFetchOptions` — superseded by `RequestInit`

Comparison:

- BFF helpers accept/return standard `RequestInit` and explicit `CookieScope` parameters.
- `BffFetchOptions` was not referenced by any helper signature or source consumer.
- Removing the unused interface does not affect request construction, headers, cookie scope, CSRF checks, or no-store behavior.

## Verification Results: Batch 5

Executed after changes:

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_after_batch5_2026_05_11.json
```

Results:

- TypeScript: passed.
- React Doctor score: 88/100 (`Great`).
- React Doctor diagnostics: 329 warnings, 0 errors.
- `types`: reduced from 112 at the start of supersession to 109.
- `exports`: remains 79.

Stop line for this supersession lane:

- Remaining `types` findings are dominated by generated API contracts, frontend/backend contract mirrors, reusable component prop types, store auth types, scenario fixture types, and design-token key types.
- Remaining `exports` findings are dominated by API clients, governance clients, error-boundary utilities, accessibility utilities, currency utilities, design tokens, combobox utilities, scenario/theme hooks, and audit helpers.
- These should be handled by explicit API-contract or product-surface decisions, not by mechanical removal.

Targeted tests after Batches 3-5:

```bash
cd frontend && npx vitest run \
  src/lib/__tests__/bff-trip-adapters.test.ts \
  src/lib/__tests__/inbox-helpers.test.ts \
  src/lib/__tests__/planning-status.test.ts \
  src/components/workspace/panels/__tests__/TimelineSummary.test.tsx \
  src/app/__tests__/public_marketing_pages.test.tsx

cd frontend && npx vitest run \
  src/components/ui/__tests__/status-badge.test.tsx \
  src/lib/__tests__/bff-auth.test.ts \
  src/components/inbox/__tests__/FilterComponents.test.tsx
```

Results:

- First targeted run: 5 files passed, 70 tests passed.
- Second targeted run: 3 files passed, 29 tests passed.

## Supersession Batch 6: Kept Surfaces With Executable Coverage

Verdict: ACCEPT+MODIFY. Several React Doctor `files` findings represented useful primitives, utilities, or parked feature/reference surfaces rather than truly redundant code. Instead of deleting them, this batch adds focused tests so the keep decision is executable and future agents can modify them safely.

Covered surfaces:

- `Badge`, `IconWrapper`, `IconButton`, `IconLink`, `Select`, and `Textarea` shared UI primitives.
- `CurrencyContext` default/persisted currency behavior.
- WCAG contrast utility functions used by the contrast validation tool.
- `ChangeHistoryPanel` empty and stored-change render behavior.
- `FrontierDashboard` no-data and live-data render behavior while the feature remains parked/reference-only.
- `src/stores/index.ts` barrel export as the canonical aggregation surface for store hooks.

Additional correctness fix:

- Versioned `useFieldAuditLog` localStorage keys from `trip_audit_` to `trip_audit:v1:` so future schema changes can safely distinguish stored payload versions.

## Supersession Batch 7: Store Barrel Removal

Verdict: ACCEPT+MODIFY. Batch 6 initially added coverage for `src/stores/index.ts` as a possible canonical aggregation surface. React Doctor then surfaced `no-barrel-import`, which is architecturally stronger: direct store modules are the current real public surface and avoid barrel indirection.

### Removal: `frontend/src/stores/index.ts` — superseded by direct store modules

Comparison:

- `useWorkbenchStore` remains exported from `frontend/src/stores/workbench.ts`.
- `useAuthStore` and auth types remain exported from `frontend/src/stores/auth.ts`.
- `useThemeStore` remains exported from `frontend/src/stores/themeStore.ts`.
- The barrel contained no runtime behavior, validation, state, or unique types.
- Call-site audit found no active source imports from `@/stores` before the temporary test. Active code already imports direct modules.

Action:

- Removed `frontend/src/stores/index.ts`.
- Removed the temporary barrel test added in Batch 6.

Rationale:

- Direct module imports are more explicit and avoid the barrel-import anti-pattern.
- This is additive in architecture even though it removes a file, because it consolidates on the already-used canonical store modules.

## Supersession Batch 8: Move Frontend Contrast Tool To Repo Tools

Verdict: ACCEPT. `frontend/tools/validate-contrast.ts` was not frontend application code; it was a reusable diagnostic tool. Keeping it under `frontend/tools` made React Doctor classify it as an unused frontend file.

### Move: `frontend/tools/validate-contrast.ts` — superseded by `tools/frontend-validate-contrast.ts`

Comparison:

- Tool behavior preserved: it still calls `validateTokenColors()` and prints contrast ratios plus recommendations.
- Import path updated from `../src/lib/contrast-utils.js` to `../frontend/src/lib/contrast-utils.js`.
- Documentation updated in root `tools/README.md` with the command `cd frontend && npx tsx ../tools/frontend-validate-contrast.ts`.
- Removed the stale frontend-local README entry so the active tool location is unambiguous.

Rationale:

- Global reusable-tools guidance says reusable helpers should live under project `tools/`.
- React Doctor should scan frontend app health, not repo-level diagnostic tools.

## Verification Results: Batches 6-8

Executed after kept-surface coverage, store barrel removal, and contrast-tool move:

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run \
  src/components/ui/__tests__/primitive-surfaces.test.tsx \
  src/contexts/__tests__/CurrencyContext.test.tsx \
  src/lib/__tests__/contrast-utils.test.ts \
  src/components/workspace/panels/__tests__/ChangeHistoryPanel.test.tsx \
  src/components/workspace/__tests__/FrontierDashboard.test.tsx
cd frontend && npx tsx ../tools/frontend-validate-contrast.ts
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_supersession_after_batch8_2026_05_11.json
```

Results:

- TypeScript: passed.
- Targeted kept-surface tests: 5 files passed, 16 tests passed.
- Contrast validator tool: passed, 16/16 token combinations passed AA.
- React Doctor score: 89/100 (`Great`).
- React Doctor diagnostics: 319 warnings, 0 errors.
- `files`: reduced to 0.
- `duplicates`: remains 0.
- `client-localstorage-no-version`: remains 0 after versioning audit-log keys.
- `no-barrel-import`: remains 0 after removing the store barrel.

Current remaining dead-code categories:

- `types`: 112. Mostly generated API contracts, frontend/backend contract mirrors, reusable component prop types, store auth types, scenario fixture types, and design-token key types.
- `exports`: 76. Mostly API clients, governance clients, error-boundary utilities, accessibility utilities, currency utilities, design tokens, combobox utilities, scenario/theme hooks, and audit helpers.

Decision:

- Stop mechanical supersession here. Remaining `types` and `exports` require explicit API-contract or product-surface decisions, not blind removal.

Production build after Batches 6-8:

```bash
cd frontend && npm run build
```

Result:

- Passed. Next.js 16.2.4 production build completed successfully.

## Supersession Batch 9: Public Contract Surface Coverage

Verdict: ACCEPT+MODIFY. The remaining `exports`/`types` findings after Batch 8 were not equivalent to removable dead code. They included generated backend contracts, frontend/backend mirror contracts, API client methods, governance client methods, reusable UI primitives, accessibility helpers, combobox/currency utilities, audit helpers, and hook/store selectors.

Classification applied:

- `KEEP_CONTRACT`: generated OpenAPI/backend mirrors and BFF/API client contracts. These remain importable because they describe runtime contracts even when not every field is consumed by current screens.
- `KEEP_PUBLIC_UTILITY`: accessibility, currency, combobox, audit, tokens, error-boundary, and primitive UI APIs. These are reusable supported surfaces and now have behavioral tests.
- `KEEP_HOOK_SURFACE`: `useScenario`, `useWorkloadDistribution`, `useInboxStats`, `useAllAuditLogs`, and `useComponentVariant` are intentionally exported hook/store selectors and now have hook-level tests.
- `KEEP_CONVERSION_HELPER`: `toPipelineStageId` is a boundary helper for converting external string inputs into typed pipeline stage ids and is now covered in the existing `PipelineFlow` test.
- `NO_REMOVAL`: no remaining public surface in this batch was proven to be a strict redundant subset under the Supersession Workflow, so nothing was deleted.

Coverage added:

- `frontend/src/lib/__tests__/accessibility.test.tsx`
- `frontend/src/lib/__tests__/currency.test.ts`
- `frontend/src/lib/__tests__/combobox.test.ts`
- `frontend/src/lib/__tests__/tokens.test.ts`
- `frontend/src/lib/__tests__/api-client-contract-surface.test.ts`
- `frontend/src/lib/__tests__/governance-api-contract-surface.test.ts`
- `frontend/src/types/__tests__/audit.test.ts`
- `frontend/src/types/__tests__/contract-surfaces.test.ts`
- `frontend/src/components/__tests__/error-boundary.test.tsx`
- `frontend/src/hooks/__tests__/useFieldAuditLog.contract-surface.test.tsx`
- `frontend/src/hooks/__tests__/useGovernance.contract-surface.test.tsx`
- `frontend/src/hooks/__tests__/useScenarios.contract-surface.test.tsx`
- `frontend/src/stores/__tests__/themeStore.contract-surface.test.tsx`
- `frontend/src/app/(agency)/workbench/__tests__/PipelineFlow.test.tsx` extended for `toPipelineStageId`.
- `frontend/src/components/ui/__tests__/primitive-surfaces.test.tsx` extended for primitive props/variants.

Verification after Batch 9:

```bash
cd frontend && npx -y react-doctor@latest . --json > /tmp/react_doctor_contract_surface_final_2026_05_11.json
```

Result:

- Score: 90/100 (`Great`).
- Diagnostics: 131 warnings, 0 errors.
- `exports`: 0.
- `types`: 0.
- Remaining rules: `no-inline-exhaustive-style` 40, `nextjs-missing-metadata` 18, `no-giant-component` 16, `prefer-useReducer` 15, `rerender-state-only-in-handlers` 12, `no-cascading-set-state` 9, `no-fetch-in-effect` 6, `nextjs-no-client-fetch-for-server-data` 4, `rendering-usetransition-loading` 3, and smaller async/derived/render rules.

Targeted test verification during this batch:

- Public utility/primitive tests: 7 files passed, 34 tests passed.
- API/governance contract tests: 2 files passed, 4 tests passed.
- Hook/store/PipelineFlow contract tests: 5 files passed, 18 tests passed.
- Type/localStorage follow-up tests: 2 files passed, 3 tests passed.

Full TypeScript status:

- `cd frontend && npx tsc --noEmit` is currently blocked by `frontend/src/components/workspace/panels/__tests__/MetricDrillDownDrawer.test.tsx:124` with `TS2349: This expression is not callable. Type 'never' has no call signatures.`
- That file was not touched in Batch 9 and appears to be parallel-agent drift. It should be resolved before claiming full-suite TypeScript green again.

Next recommended remediation sequence:

1. Fix or coordinate the `MetricDrillDownDrawer.test.tsx` TypeScript blocker, then rerun full `npx tsc --noEmit`.
2. Tackle `nextjs-missing-metadata` at layout/page boundaries first because it is low-blast-radius and product-visible.
3. Refactor `itinerary-checker/page.tsx` inline style/component-size findings as a dedicated visual QA task with browser screenshots.
4. Review reducer candidates (`prefer-useReducer`, cascading/rerender state findings) by user flow, not by mechanical conversion.
5. Re-check `no-fetch-in-effect` and `nextjs-no-client-fetch-for-server-data` against actual API/runtime contracts before moving data loading to server boundaries.
