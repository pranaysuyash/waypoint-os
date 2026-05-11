# React Doctor Progress - 2026-05-10

## Scope

Continued React Doctor remediation from the prior Phase 2 work. This pass focused on bounded, low-deletion risk findings:

- Accessibility labels and interactive semantics
- Stable React keys
- Hydration-safe render paths
- React 19 deprecated API warnings in context/shared UI primitives
- Default Tailwind palette leftovers
- Small React Compiler destructuring issues in auth/settings pages
- Follow-up navigation/search-param destructuring cleanup
- Bounded accessibility, image, bundle-size, and stale-closure fixes

## Instruction And Workflow Notes

- Loaded repo instructions from `AGENTS.md`, `CLAUDE.md`, `frontend/AGENTS.md`, and `frontend/CLAUDE.md`.
- Loaded project context pack from `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt` and `Docs/context/agent-start/SESSION_CONTEXT.md`.
- Relevant skills consulted: `react-best-practices`, `react-effect-discipline`, `verification-before-completion`, and `search-first`.
- No destructive git commands were used.
- No dead-code/type-export removals were attempted in this pass because repo instructions require call-site and supersession analysis before removal.

## Baseline For This Pass

Command:

```bash
cd frontend
npx -y react-doctor@latest . --json
```

Starting scan:

- Score: 65
- Findings: 555
- Errors: 0
- Warnings: 555

## Current Verified Scan

Command:

```bash
cd frontend
npx -y react-doctor@latest . --json
```

Current scan after follow-up remediation on 2026-05-11:

- Score: 87
- Findings: 371
- Errors: 0
- Warnings: 371

## Rules Cleared In This Pass

| Rule | Before | After | Notes |
| --- | ---: | ---: | --- |
| `label-has-associated-control` | 7 | 0 | Added explicit screen-reader labels to custom checkbox/radio label wrappers. |
| `no-array-index-as-key` | 6 | 0 | Replaced skeleton/star/traveler keys with stable non-index keys. |
| `rendering-hydration-mismatch-time` | 4 | 0 | Removed render-time `Math.random()` and `new Date()` usage from flagged JSX paths. |
| `no-static-element-interactions` | 6 | 0 | Added explicit roles/keyboard semantics where elements already behaved as controls. |
| `no-react19-deprecated-apis` | 15 | 0 | Replaced context reads with React 19 `use()` and removed `forwardRef` wrappers from shared UI primitives. |
| `design-no-default-tailwind-palette` | 6 | 0 | Replaced default gray placeholder classes with design-token placeholder color. |
| `react-compiler-destructure-method` | 40 | 0 | Bound `URLSearchParams.get` helpers and destructured router methods without losing native method context. |
| `no-autofocus` | 5 | 0 | Removed forced focus from signup and inline editors. |
| `no-outline-none` | 2 | 0 | Restored keyboard-visible browser focus outlines in the itinerary checker. |
| `nextjs-no-img-element` | 3 | 0 | Replaced local marketing art with `next/image`, used accessible background preview for arbitrary agency logo URLs, and updated the test mock. |
| `prefer-dynamic-import` | 2 | 0 | Converted eager Recharts imports in visual charts to dynamic imports. |
| `js-hoist-intl` | 1 | 0 | Hoisted currency number formatters to module-level singletons. |
| `js-set-map-lookups` | 1 | 0 | Replaced repeated currency-code scan with a precompiled code matcher. |
| `rerender-functional-setstate` | 3 | 0 | Converted stale-closure-prone array/object updates to functional state updates. |
| `no-generic-handler-names` | 3 | 0 | Renamed generic test handler mocks to intent-specific names. |
| `no-large-animated-blur` | 1 | 0 | Reduced oversized itinerary checker header blur from 12px to 8px. |
| `server-hoist-static-io` | 1 | 0 | Hoisted static scenario fixture loading out of the GET handler while preserving 500 behavior on load failure. |
| `server-sequential-independent-await` | 1 | 0 | Parallelized independent dynamic imports in the metric drilldown test. |
| `design-no-bold-heading` | 14 | 0 | Replaced over-heavy heading weights with semibold equivalents. |
| `design-no-redundant-padding-axes` | 3 | 0 | Collapsed redundant same-axis padding classes to shorthand. |
| `advanced-event-handler-refs` | 2 | 0 | Registered drawer/modal keydown listeners inside open-state effects while reading latest close handlers from refs. |
| `rerender-functional-setstate` | 1 | 0 | Converted the remaining stale closure update to functional state. |
| `js-combine-iterations` | 1 | 0 | Combined extraction field filtering and mapping into one pass. |
| `no-side-tab-border` | 2 | 0 | Replaced thick one-sided error accents with subtler inset shadows. |
| `rendering-hydration-no-flicker` | 1 | 0 | Replaced client date mount-effect formatting with `useSyncExternalStore` snapshots. |

## Rules Reduced In This Pass

| Rule | Before | After | Notes |
| --- | ---: | ---: | --- |
| `react-compiler-destructure-method` | 49 | 0 | Completed across auth, settings, workbench, inbox, insights, suitability, layout/auth, and workspace panels. |

## Verification

TypeScript:

```bash
cd frontend
npx tsc --noEmit
```

Result: exit code 0.

Targeted tests:

```bash
cd frontend
npx vitest run \
  src/components/ui/__tests__/confirm-dialog.test.tsx \
  src/components/ui/__tests__/progress-steps.test.tsx \
  src/components/ui/__tests__/status-badge.test.tsx \
  src/components/ui/__tests__/toast.test.tsx \
  src/contexts/__tests__/TripContext.test.tsx
```

Result: 5 files passed, 24 tests passed.

Full frontend test suite:

```bash
cd frontend
npx vitest run
```

Result: 87 files passed, 790 tests passed on the clean rerun. A prior full-suite run executed concurrently with `npm run build` and hit one booking-collection timeout plus a Vitest worker timeout; the isolated booking-collection suite then passed 9/9, and the subsequent clean full-suite rerun passed. The test run still prints existing React `act(...)` warnings in several suites and an intentional invalid-JSON route-test console error, but exits successfully.

Production build:

```bash
cd frontend
npm run build
```

Result: build completed successfully with Next.js 16.2.4.

2026-05-11 follow-up verification:

```bash
cd frontend
npx tsc --noEmit
npx vitest run
npm run build
```

Result:

```text
npx tsc --noEmit: exit code 0
npx vitest run: 87 files passed, 790 tests passed
npm run build: exit code 0, Next.js 16.2.4 production build completed
```

Targeted regression tests added in the follow-up:

```bash
cd frontend
npx vitest run \
  src/components/ui/__tests__/input.test.tsx \
  src/components/ui/__tests__/button.test.tsx \
  src/components/visual/__tests__/RevenueChart.test.tsx \
  src/components/visual/__tests__/PipelineFunnel.test.tsx
```

Result: 4 files passed, 36 tests passed.

## Remaining Largest Buckets

| Rule | Count | Recommended Next Move |
| --- | ---: | --- |
| `types` | 112 | Audit generated/public contract surfaces before removing anything. Many are likely intentional API types. |
| `exports` | 100 | Same as above; apply supersession workflow before removal. |
| `no-inline-exhaustive-style` | 40 | Concentrated in `itinerary-checker/page.tsx`; extract stable style objects/CSS module classes thoughtfully. |
| `prefer-useReducer` | 15 | Use reducer only where state is genuinely coupled; do not convert unrelated local booleans mechanically. |
| `nextjs-missing-metadata` | 18 | Many flagged pages are client components; resolve with server wrapper/client component split or validated layout-level metadata strategy. |
| `rerender-state-only-in-handlers` | 12 | Inspect before changing; many remaining items are used in early returns or conditional JSX and are likely false positives. |

## Decision Notes

- Dead-code cleanup was deliberately deferred. React Doctor reports useful candidates, but repo rules require preserving product intent, public contracts, generated types, and future-facing utility code unless a call-site audit proves removal is safe.
- Metadata cleanup was also deferred. A correct long-term fix likely requires splitting client pages into server metadata wrappers plus client implementation components. That is safer than trying to force metadata exports into client files.
- The `react-compiler-destructure-method` URLSearchParams cases were resolved with bound helpers because native-style method extraction can lose `this` binding.
- Some remaining `no-derived-useState`/`no-mirror-prop-effect` findings are not automatically safe. For example, `SmartCombobox` keeps an editable input draft distinct from the selected value; flattening that state mechanically would change UX.
- The route and chart changes are intentionally additive: static fixture loading preserves the route's 500 response behavior on load failure, and chart imports now split Recharts without changing chart props or tests.
- The `async-await-in-loop` findings currently point at sequential polling/retry code (`useSpineRun`, `api-client`) and were intentionally left unchanged because parallelizing them would break the control flow.

## Next Task Order

1. Extract `itinerary-checker/page.tsx` inline visual system into a CSS module or stable style primitives. This can clear `no-inline-exhaustive-style`, reduce giant component pressure, and improve long-term maintainability, but it should be done as a dedicated visual refactor with screenshot/browser QA.
2. Add metadata through server wrappers/layout-level exports. Do not try to export metadata from client components; split page shells from client implementations where needed.
3. Audit `types` and `exports` with the Supersession Workflow before removal. Treat generated types, public API contracts, and future-facing helpers as preserved until call-site and replacement analysis proves redundancy.
4. Review `prefer-useReducer`, `no-cascading-set-state`, and `rerender-state-only-in-handlers` by behavior cluster. Convert only genuinely coupled state machines; do not introduce reducers as lint theater.
5. Move remaining page-level `fetch` in effects to server components or TanStack Query/SWR where it matches data ownership, starting with trip layout/suitability/audit/join.
