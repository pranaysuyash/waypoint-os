# Frontend Lint/Typecheck Bootstrap (2026-05-12)

## Scope

Enable package-level static scripts and validate current behavior in `frontend`.

## Changes Applied

1. Added package scripts in `frontend/package.json`:
   - `lint`: `eslint . --ext .js,.jsx,.ts,.tsx`
   - `typecheck`: `tsc -p tsconfig.json --noEmit`
2. Added ESLint flat config for ESLint v9 compatibility:
   - `frontend/eslint.config.mjs`
   - Uses `eslint-config-next/core-web-vitals` with standard build ignores.
3. Added lint dependencies:
   - `eslint`
   - `eslint-config-next`
4. Updated `PlanningDetailSection` test contract usage to match current component props:
   - `frontend/src/components/workspace/panels/__tests__/IntakeFieldComponents.test.tsx`
   - Migrated from `renderEditor` callback style to `activeEditorId` + `editorContent`.

## Verification

Commands run:

```bash
cd frontend
npm run typecheck
npm run lint
```

Results:

- `typecheck`: PASS
- `lint`: FAIL (runs successfully, reports existing lint debt)

Observed lint summary:

- Total: `101` problems
- Errors: `82`
- Warnings: `19`

Primary error buckets from current output:

1. `react-hooks/purity` (e.g. `Date.now()` in render paths)
2. `react-hooks/set-state-in-effect`
3. `react-hooks/preserve-manual-memoization`
4. `react/no-unescaped-entities`

Representative files with current lint errors:

- `src/app/(agency)/reviews/PageClient.tsx`
- `src/app/(agency)/settings/page.tsx`
- `src/app/(agency)/trips/[tripId]/layout.tsx`
- `src/app/(agency)/workbench/OpsPanel.tsx`
- `src/components/workspace/panels/IntakePanel.tsx`
- `src/components/workspace/panels/TimelinePanel.tsx`
- `src/hooks/useFieldAuditLog.ts`

## Interpretation

Script enablement is complete and future-proof for Next.js + ESLint v9.
Current lint failure is due to pre-existing repo-wide code issues, not script misconfiguration.

## Recommended Next Safe Unit

Lint debt reduction in focused batches:

1. Batch A: `react/no-unescaped-entities` and unused disable directives (low risk).
2. Batch B: `react-hooks/purity` and `set-state-in-effect` in isolated components.
3. Batch C: `preserve-manual-memoization` with targeted hook dependency reviews.

Keep each batch independently verifiable with:

```bash
npm run lint
npm run typecheck
```

## Batch A Execution Update (2026-05-12)

### Objective

Close only low-risk lint categories:

1. `react/no-unescaped-entities`
2. `Unused eslint-disable directive`

### Files Updated

- `src/app/(agency)/audit/PageClient.tsx`
- `src/app/(agency)/reviews/PageClient.tsx`
- `src/app/(agency)/trips/[tripId]/layout.tsx`
- `src/app/(agency)/trips/[tripId]/suitability/PageClient.tsx`
- `src/app/(agency)/workbench/DecisionTab.tsx`
- `src/app/(agency)/workbench/PacketTab.tsx`
- `src/app/(agency)/workbench/SafetyTab.tsx`
- `src/app/(agency)/workbench/StrategyTab.tsx`
- `src/app/(auth)/forgot-password/page.tsx`
- `src/app/(auth)/join/[code]/page.tsx`
- `src/components/marketing/MarketingVisuals.tsx`
- `src/components/ui/SmartCombobox.tsx`
- `src/components/workspace/ReviewControls.tsx`
- `src/components/workspace/panels/CaptureCallPanel.tsx`
- `src/components/workspace/panels/FeedbackPanel.tsx`
- `src/components/workspace/panels/StrategyPanel.tsx`
- `src/components/workspace/panels/TimelineSummary.tsx`
- `src/hooks/useRuntimeVersion.ts`
- `src/types/generated/spine-api.ts`

### Verification

Commands run:

```bash
cd frontend
npm run typecheck
npm run lint
```

Results after Batch A:

- `typecheck`: PASS
- `lint`: FAIL (remaining non-Batch-A categories)
- Lint problem count improved from `101` (`82` errors, `19` warnings) to `63` (`49` errors, `14` warnings)
- Re-check for Batch A categories returns no hits:
  - `react/no-unescaped-entities`
  - `Unused eslint-disable directive`

### Remaining Lint Debt (Next Unit)

Primary remaining categories:

1. `react-hooks/set-state-in-effect`
2. `react-hooks/purity`
3. `react-hooks/preserve-manual-memoization`
4. `react-hooks/exhaustive-deps`

These require behavior-aware refactoring and should be handled as Batch B, component-by-component.

## Batch B Slice 1 Execution Update (2026-05-12)

### Objective

Close the lowest-risk hook-rule violations in isolated page components:

1. `react-hooks/purity` in the owner reviews page.
2. `react-hooks/set-state-in-effect` in the agency settings page.
3. `react-hooks/set-state-in-effect` in the documents route shell.
4. `react-hooks/refs` render-time ref writes in shared drawer/modal primitives.

### Files Updated

- `src/app/(agency)/reviews/PageClient.tsx`
- `src/app/(agency)/settings/page.tsx`
- `src/app/(agency)/documents/PageClient.tsx`
- `src/components/ui/drawer.tsx`
- `src/components/ui/modal.tsx`

### Implementation Notes

- Reviews now captures one stable `referenceNow` value per page mount and passes it into review cards/sorting. This removes `Date.now()` from render-time calculations while preserving stable urgency ordering during a page session.
- Settings now derives a cloned base draft from loaded settings and keeps local draft state only after user edits or reset. This removes the synchronous state sync effect and keeps reset/save behavior explicit.
- Documents now derives the effective selected trip from the fetched trip list instead of syncing the first trip into state with an effect.
- Drawer and modal now depend on `onClose` directly in their effects instead of assigning callback refs during render.

### Verification

Commands run:

```bash
cd frontend
npm run typecheck
npm run lint
npm run lint -- --format stylish 2>&1 | rg "reviews/PageClient|settings/page|✖|problems"
npx eslint 'src/app/(agency)/documents/PageClient.tsx' 'src/app/(agency)/reviews/PageClient.tsx' 'src/app/(agency)/settings/page.tsx' 'src/components/ui/drawer.tsx' 'src/components/ui/modal.tsx'
```

Results after Batch B Slice 1:

- `typecheck`: PASS
- `lint`: FAIL (remaining lint debt is outside the two files changed in this slice)
- First full lint after this slice reported `59` problems (`45` errors, `14` warnings)
- A follow-up filtered lint summary reported `61` problems (`46` errors, `15` warnings), consistent with the currently active dirty tree changing while parallel work is ongoing.
- Re-check for this slice returned no `reviews/PageClient` or `settings/page` lint hits.
- Targeted ESLint for the five files touched in this slice: PASS.
- Latest full lint after documents/drawer/modal cleanup: FAIL with `56` problems (`42` errors, `14` warnings).

### Remaining Lint Debt (Next Unit)

Continue Batch B in small behavior-aware slices. Current highest-signal remaining areas:

1. `src/app/(agency)/trips/[tripId]/layout.tsx` - trip/stage rail reset state.
2. `src/app/(agency)/trips/[tripId]/followups/PageClient.tsx` - fetch state owned by effect callback.
3. `src/app/(agency)/workbench/OpsPanel.tsx` - several fetch/action callbacks need dependency and effect ownership review.
4. `src/app/(agency)/workbench/PageClient.tsx` - store/effect dependency and manual memoization review.
5. `src/components/workspace/panels/IntakePanel.tsx`, `TimelinePanel.tsx`, and `src/hooks/useFieldAuditLog.ts` - larger hook/state ownership cleanup.
