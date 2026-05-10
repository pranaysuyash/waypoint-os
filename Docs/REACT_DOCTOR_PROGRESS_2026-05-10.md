# React Doctor Progress - 2026-05-10

## Scope

Continued React Doctor remediation from the prior Phase 2 work. This pass focused on bounded, low-deletion risk findings:

- Accessibility labels and interactive semantics
- Stable React keys
- Hydration-safe render paths
- React 19 deprecated API warnings in context/shared UI primitives
- Default Tailwind palette leftovers
- Small React Compiler destructuring issues in auth/settings pages

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

Current scan after this pass:

- Score: 69
- Findings: 502
- Errors: 0
- Warnings: 502

## Rules Cleared In This Pass

| Rule | Before | After | Notes |
| --- | ---: | ---: | --- |
| `label-has-associated-control` | 7 | 0 | Added explicit screen-reader labels to custom checkbox/radio label wrappers. |
| `no-array-index-as-key` | 6 | 0 | Replaced skeleton/star/traveler keys with stable non-index keys. |
| `rendering-hydration-mismatch-time` | 4 | 0 | Removed render-time `Math.random()` and `new Date()` usage from flagged JSX paths. |
| `no-static-element-interactions` | 6 | 0 | Added explicit roles/keyboard semantics where elements already behaved as controls. |
| `no-react19-deprecated-apis` | 15 | 0 | Replaced context reads with React 19 `use()` and removed `forwardRef` wrappers from shared UI primitives. |
| `design-no-default-tailwind-palette` | 6 | 0 | Replaced default gray placeholder classes with design-token placeholder color. |

## Rules Reduced In This Pass

| Rule | Before | After | Notes |
| --- | ---: | ---: | --- |
| `react-compiler-destructure-method` | 49 | 40 | Small auth/settings pass only. URLSearchParams-heavy hooks left for a focused follow-up because method binding semantics need care. |

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

Result: 87 files passed, 790 tests passed. The run still prints existing React `act(...)` warnings in several tests and a Recharts container-size warning, but exits successfully.

Production build:

```bash
cd frontend
npm run build
```

Result: build completed successfully with Next.js 16.2.4.

## Remaining Largest Buckets

| Rule | Count | Recommended Next Move |
| --- | ---: | --- |
| `types` | 112 | Audit generated/public contract surfaces before removing anything. Many are likely intentional API types. |
| `exports` | 100 | Same as above; apply supersession workflow before removal. |
| `react-compiler-destructure-method` | 40 | Continue file-by-file, especially `workbench/page.tsx`, `inbox/page.tsx`, `IntakePanel.tsx`; avoid unsafe unbound URLSearchParams method extraction. |
| `no-inline-exhaustive-style` | 40 | Concentrated in `itinerary-checker/page.tsx`; extract stable style objects/CSS module classes thoughtfully. |
| `prefer-useReducer` | 19 | Use reducer only where state is genuinely coupled; do not convert unrelated local booleans mechanically. |
| `nextjs-missing-metadata` | 18 | Many flagged pages are client components; resolve with server wrapper/client component split or validated layout-level metadata strategy. |
| `js-batch-dom-css` | 16 | Batch imperative style writes into classes or CSS text where behavior is unchanged. |
| `rerender-state-only-in-handlers` | 16 | Convert event-only mutable values to refs where they do not affect rendering. |

## Decision Notes

- Dead-code cleanup was deliberately deferred. React Doctor reports useful candidates, but repo rules require preserving product intent, public contracts, generated types, and future-facing utility code unless a call-site audit proves removal is safe.
- Metadata cleanup was also deferred. A correct long-term fix likely requires splitting client pages into server metadata wrappers plus client implementation components. That is safer than trying to force metadata exports into client files.
- The `react-compiler-destructure-method` URLSearchParams cases need care because native-style method extraction can lose `this` binding. Use bound helpers or server/client splits where appropriate rather than blindly destructuring.
