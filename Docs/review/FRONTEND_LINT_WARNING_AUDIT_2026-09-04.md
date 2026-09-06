# Frontend lint warning audit — 2026-09-04

## Scope and decision

This bounded lane audited the current `frontend` ESLint output and selected
one unowned, behaviorally unambiguous warning for repair. No generated file,
blanket rule suppression, or concurrent lifecycle surface was changed.

## Baseline and implemented fix

Before this lane, the repository-wide command:

```text
pnpm exec eslint . --ext .js,.jsx,.ts,.tsx
```

reported **13 warnings and 0 errors**. The only safe independent candidate was
the missing dependency in
`frontend/src/app/(agency)/overview/useOverviewSummary.ts`:
`actionRequiredItems` uses `inboxCount`, which is the unified-state-derived
source of truth when available, but its dependency list named `inbox.total`.

That mismatch could leave grouped enquiry counts stale after unified state
refreshes while the raw inbox query total remained unchanged. The dependency
was corrected to `inboxCount`.

The regression in
`frontend/src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts`
keeps the raw inbox total at 2, changes unified-state `inbox_lead_count` from
fallback to 9, rerenders the hook, and asserts that the grouped action-required
item changes to `itemCount: 9`.

## Verification

```text
pnpm exec vitest run \
  'src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts'
1 test file passed
8 tests passed
0 failures

Targeted ESLint (overview hook + test): 0 warnings, 0 errors
Frontend TypeScript typecheck: passed
```

The repository-wide lint command now reports **12 warnings and 0 errors**.

## Follow-up: Workbench dependency slice — 2026-09-04

The five Workbench warnings listed below were subsequently audited as one
bounded, behavior-sensitive slice. They were not fixed by adding the complete
Zustand store object to dependency arrays: the store snapshot is mutable and
can change identity on every state update. Instead, each effect now aliases
only the stable action functions it invokes, while retaining explicit value
dependencies. The draft-save callback also removed its unused `replace`
dependency and added the `draft_name` value it reads.

Changed surfaces:

- `frontend/src/app/(agency)/workbench/PageClient.tsx`
- `frontend/src/app/(agency)/workbench/__tests__/page.test.tsx`

The regression test exercises persisted packet, validation, decision,
strategy, internal/traveler bundles, safety, fees, frontier output, and both
traveler/owner notes through the corresponding Workbench store actions. This
guards the hydration contract while allowing ESLint to enforce the actual
closure dependencies.

Verification for this follow-up:

```text
npx eslint 'src/app/(agency)/workbench/PageClient.tsx'
0 warnings, 0 errors

npm test -- --run \
  'src/app/(agency)/workbench/__tests__/page.test.tsx' \
  'src/app/(agency)/workbench/__tests__/page-ops-tab.test.tsx'
2 test files passed
35 tests passed
0 failures

npm run lint
0 errors, 7 warnings remain outside this slice

npm run typecheck
blocked by pre-existing/unrelated test fixture typing in
`src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts:387`
```

This is local source/test evidence (S1/S2); it does not establish browser,
hosted, provider, or production release proof.

## Remaining warning inventory

The following warnings remain intentionally open in this lane:

| Surface | Count | Why not changed here |
| --- | ---: | --- |
| `frontend/src/app/(agency)/audit/PageClient.tsx` | 1 | Mutable audit triage source and memo lifecycle; file is already a concurrent dirty slice and needs behavior-sensitive audit tests before dependency reshaping. |
| `frontend/src/components/workspace/panels/IntakePanel.tsx` | 5 | Trip replacement/refetch and notes-editor callbacks; file is already a concurrent dirty slice and dependency changes can alter repair/deep-link behavior. |
| `frontend/src/types/generated/spine-api.ts` | 1 | Unused generated-file disable directive; fix belongs in the generation template/policy, not a hand edit to generated output. |

## Alignment and next actions

The implemented change is first-principles aligned because the memo now
depends on the actual value it consumes, preserves the unified-state
single-source-of-truth policy, and is protected by a state-transition
regression. It is not a license to clear the remaining warnings mechanically.

Next owners should handle the remaining groups in separate slices:

1. Audit page: memoize the triage fallback or move it into the memo, then test
   refresh/override behavior.
2. Intake panel: establish callback identity and deep-link/focus invariants,
   then add dependencies one callback at a time.
3. Generated types: correct the generator or remove the stale directive through
   the canonical generation workflow and regenerate/check drift.

The repository was lint-clean in the stronger sense of zero errors, but not
warning-free at that historical checkpoint. The remaining groups were then
closed through their canonical owners:

## Final warning-closure refresh — 2026-09-04

- `Audit PageClient.tsx`: the optional triage source is now a stable reference,
  with the empty fallback constructed inside the memo; focused audit coverage
  is **9/9**.
- `IntakePanel.tsx`: callbacks now declare the context/store actions they read
  (`setNotesExpanded`, `replaceTrip`, and `refetchTrip`); focused repair/core/
  mode suites are **38/38**.
- `scripts/generate_types.py`: the generator removes the unused blanket
  `eslint-disable` directive before writing the single canonical generated
  type file; the generated file typechecks and lint-checks cleanly.

Repository verification after this refresh:

```text
npm run lint
0 errors, 0 warnings

npx tsc --noEmit
passed

npm test -- --run
171 test files passed
1,298 tests passed
```

No lint rule was disabled to obtain this result. This is local source/test
evidence; browser/device/hosted behavior and the remaining provider-contract
work are separate release gates.
