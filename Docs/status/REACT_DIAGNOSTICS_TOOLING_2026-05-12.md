# React Diagnostics Tooling — 2026-05-12

## Scope

Evaluated Aiden Bai's public GitHub repositories for practical additions to Waypoint OS and implemented the lowest-risk, highest-leverage frontend diagnostics path.

## Sources Checked

- Repo instructions: `/Users/pranay/AGENTS.md`, `/Users/pranay/Projects/AGENTS.md`, `AGENTS.md`, `CLAUDE.md`, `frontend/AGENTS.md`, and `frontend/CLAUDE.md`.
- Project context pack: `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt` and `Docs/context/agent-start/SESSION_CONTEXT.md`.
- Local Next.js 16 docs: `frontend/node_modules/next/dist/docs/01-app/03-api-reference/02-components/script.md`.
- Aiden Bai repos:
  - `https://github.com/aidenybai/react-scan`
  - `https://github.com/aidenybai/react-grab`
  - `https://github.com/aidenybai/element-source`
  - `https://github.com/aidenybai/million`
  - `https://github.com/aidenybai/bippy`
  - `https://github.com/aidenybai/pattycake`
  - `https://github.com/aidenybai/web-interface-guidelines`

## Decision

Adopt `react-scan` and `react-grab` as opt-in development diagnostics loaded through the existing App Router root layout.

Rationale:

- `react-scan` directly targets React render performance problems, which matches the current frontend's dense workbench, trip, inbox, and chart surfaces.
- `react-grab` improves agent/operator feedback loops by copying selected UI element context with component/source information.
- Both packages support the current React line based on npm metadata (`react-scan@0.5.6` supports React 16-19; `react-grab@0.1.33` supports React >=17).
- Next.js local docs specify `beforeInteractive` scripts for App Router should live in the root layout when they need to load before hydration.
- The integration is dev-only and opt-in to avoid adding default local noise, production risk, or a parallel diagnostic shell.

## Implementation

Updated `frontend/src/app/layout.tsx`:

- Added `next/script`.
- Added `enableReactDiagnostics`, gated by:
  - `process.env.NODE_ENV === 'development'`
  - `process.env.NEXT_PUBLIC_ENABLE_REACT_DIAGNOSTICS === '1'`
- Loads pinned script URLs only when enabled:
  - `https://unpkg.com/react-scan@0.5.6/dist/auto.global.js`
  - `https://unpkg.com/react-grab@0.1.33/dist/index.global.js`

Usage:

```bash
cd frontend
NEXT_PUBLIC_ENABLE_REACT_DIAGNOSTICS=1 npm run dev
```

Then open the app normally. React Scan provides render/performance visibility, and React Grab can copy element context for agent handoff/debugging.

## Deferred

- `element-source`: useful only if we build a custom internal source-inspection overlay. React Grab already covers the current workflow.
- `million`: defer until React Scan identifies stable, render-heavy components worth targeted optimization. Do not add a compiler before measurement.
- `bippy`: do not use directly in app code. It intentionally depends on React internals and is too fragile for this project unless wrapped in a separate, explicitly experimental diagnostic tool.
- `pattycake`: no current fit because the frontend does not rely on `ts-pattern`.
- `web-interface-guidelines`: useful as audit material, but should be incorporated selectively into existing frontend QA/design docs rather than copied wholesale.

## Verification Plan

- Run `npm run typecheck` in `frontend/`.
- Run focused layout tests if available.
- Build if typecheck or tests indicate Script/App Router issues.

## Verification Results

Executed:

```bash
cd frontend && npm run typecheck
cd frontend && npx eslint src/app/layout.tsx
cd frontend && npm run build
```

Results:

- TypeScript passed.
- Targeted ESLint for `src/app/layout.tsx` passed.
- Next.js production build passed on Next `16.2.4` with Turbopack.

Additional check:

```bash
cd frontend && npm run lint -- --quiet src/app/layout.tsx
```

Result: failed because the project lint script still linted the full frontend and surfaced 42 pre-existing React Compiler/effect errors in other files. No reported lint error referenced `src/app/layout.tsx`.

Attempted runtime dev HTML check:

```bash
cd frontend && NEXT_PUBLIC_ENABLE_REACT_DIAGNOSTICS=1 npm run dev -- --port 3010
```

Result: blocked by Next's existing dev-server lock for the same frontend project on `http://localhost:3000` (PID `3774`). The running server was not killed or modified.

## Follow-Up

After enabling diagnostics locally, profile these surfaces first:

- `/workbench`
- `/trips`
- `/inbox`
- `/trips/[tripId]/*`
- Traveler itinerary checker

Record findings in a follow-up dated performance note before applying any memoization, virtualization, compiler, or component-splitting changes.
