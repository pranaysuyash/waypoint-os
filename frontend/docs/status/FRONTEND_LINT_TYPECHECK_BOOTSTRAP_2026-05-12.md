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
