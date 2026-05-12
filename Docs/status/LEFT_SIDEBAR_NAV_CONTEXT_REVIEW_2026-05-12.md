# Left Sidebar Navigation and Context Review

Date: 2026-05-12  
Scope: Global left sidebar navigation, trip contextual UI placement, and next-step recommendations.

## Instruction and Status Baseline

- Loaded instruction stack:
  - `/Users/pranay/AGENTS.md`
  - `/Users/pranay/Projects/AGENTS.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `frontend/AGENTS.md`
  - `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
  - `Docs/context/agent-start/SESSION_CONTEXT.md`
- Ran read-only status check with `git status --short --branch`.
- Current tree has active parallel-agent drift, including modified `frontend/src/lib/nav-modules.ts`, `frontend/src/components/layouts/Shell.tsx` dependencies, and newly added `/documents` files.
- Backend and frontend servers were already live:
  - `curl http://localhost:8000/health` returned `200`.
  - `curl http://localhost:3000` returned `200`.

## Current Implementation Evidence

### Global Left Sidebar

Canonical source:

- `frontend/src/lib/nav-modules.ts`
- Rendered by `frontend/src/components/layouts/Shell.tsx`

Current sections:

| Section | Items | Status |
| --- | --- | --- |
| COMMAND | Overview, Lead Inbox, Quote Review | Enabled |
| PLANNING | Trips in Planning | Enabled |
| PLANNING | Quotes, Bookings | Planned/disabled |
| OPERATIONS | Documents | Route exists, nav still disabled by rollout gate |
| OPERATIONS | Payments, Suppliers | Planned/disabled |
| INTELLIGENCE | Insights, Audit | Enabled |
| INTELLIGENCE | Knowledge Base | Planned/disabled |
| ADMIN | Settings | Enabled |

Live Chrome inspection confirmed the sidebar renders these sections and disabled items show as `Planned` buttons with toast affordance.

### Documents Module Gate

`/documents` now has a route shell:

- `frontend/src/app/(agency)/documents/page.tsx`
- `frontend/src/app/(agency)/documents/PageClient.tsx`

Follow-up drift check on 2026-05-12 08:28 IST found the final `contract-regression-suite`
gate is now complete:

- `frontend/docs/status/CONTRACT_REGRESSION_SUITE_GATE_2026-05-12.md`
- `frontend/src/lib/nav-modules.ts`
- `frontend/src/lib/__tests__/nav-modules.test.ts`

`isDocumentsModuleEnabled()` now returns `true`, so Documents is enabled by gate rather
than by a manual sidebar exception.

### Trip Contextual UI

Contextual colors and next-step guidance are implemented mainly in:

- `frontend/src/app/(agency)/trips/[tripId]/layout.tsx`
- `frontend/src/lib/planning-status.ts`
- `frontend/src/lib/planning-list-display.ts`

Current behavior observed live on `/trips/trip_5c1389d95a21/intake`:

- Main trip header uses state accent color and status badge.
- Stage progress line shows current stage and locked next stages.
- Locked stage tabs explain required details.
- Main body shows:
  - Missing customer details
  - Suggested next move
  - Watch/blocker state
- Optional right rail contains:
  - Next Suggestions
  - Blocker/next action
  - Timeline summary

## Findings

### 1. Nav Coverage Is Broad Enough for the Current Product Map

The sidebar already covers the meaningful agency operating map: command center, lead intake, quote review, trip planning, operations, intelligence, and admin.

Do not add more global nav items just to reflect every research document. That would create a crowded enterprise shell before the modules are real.

### 2. Some Planned Modules Are Real Product Gaps, Not Missing Nav

The missing work is mostly module readiness, not sidebar discovery:

- Quotes needs a durable proposal/versioning surface.
- Bookings needs confirmed operational records and booking lifecycle.
- Payments needs collection milestones and risk state.
- Suppliers needs preferred supplier/rate/reliability workflows.
- Knowledge Base needs agency memory/playbooks surfaced into work.
- Documents needs final contract regression evidence before nav enablement.

### 3. Contextual UI Exists, But Not In The Left Sidebar

The remembered contextual UI is largely present in the trip workspace, but it lives in the trip header/body/right rail. This is the right default architecture:

- Left sidebar: "Where am I in the product?"
- Trip header/body: "What is this trip's state?"
- Right rail: "Why this state, what changed, what should I do next?"

Putting too much trip context into the global left nav would make the nav unstable and noisy.

### 4. A Small Contextual Left-Side Summary Is Now Implemented

The left sidebar can carry a compact context strip under the navigation or above the status footer, but it should not become a second trip panel.

Implemented in:

- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/components/layouts/__tests__/Shell.test.tsx`

Content:

- Current trip short label.
- State badge/tone.
- One next action line.
- One primary route link such as "Open missing details" or "Review quote".

Implementation rules applied:

- Show only inside `/trips/[tripId]/*`.
- Hide or compress on the 72px collapsed rail.
- Reuse `planning-status.ts` and `planning-list-display.ts`.
- Use tokenized semantic colors, not new hardcoded color maps.
- Do not fetch new data in `Shell`; derive from the existing `useTrip(shellTripId)` already present there.

### 5. Docs Have Some Drift

Relevant drift:

- `frontend/docs/status/RUNTIME_TRUTH_MATRIX_2026-05-11.md` says `/documents` is disabled and research complete only. Current code now has a route shell, but nav remains disabled due to pending contract regression.
- `Docs/FRONTEND_SIDEPANEL_AND_RAIL_INVENTORY.md` describes the right rail as Wave 2 placeholder, while current trip layout has a functioning toggle, next suggestions, blocker summary, and timeline summary.

These docs should be reconciled after the current parallel-agent work settles.

## Recommendation

Do not expand the left sidebar with more top-level navs right now.

Proceed in this order:

1. Keep `/documents` enabled only through rollout gates and regression tests.
2. Keep the lightweight `SidebarTripContext` block powered by existing planning helpers.
3. Create readiness contracts for Quotes, Bookings, Payments, Suppliers, and Knowledge Base before enabling any of them.
4. Reconcile stale docs around Documents and the right rail.

## Verification Run

Commands run during this review:

```bash
curl -s -o /dev/null -w 'backend:%{http_code}\n' http://localhost:8000/health
curl -s -o /dev/null -w 'frontend:%{http_code}\n' http://localhost:3000
cd frontend && npm test -- "src/lib/__tests__/nav-modules.test.ts" --reporter=dot
```

Result:

- Backend health: `200`
- Frontend root: `200`
- `nav-modules.test.ts`: 1 file passed, 2 tests passed

Additional verification:

```bash
cd frontend && npm test -- "src/app/(agency)/trips/[tripId]/__tests__/layout.test.tsx" --reporter=dot
cd frontend && npm test -- "src/app/(agency)/documents/__tests__/page.test.tsx" --reporter=dot
cd frontend && npx tsc --noEmit
```

Result:

- Trip layout test: 1 file passed, 8 tests passed. Existing React `act(...)` warnings were printed by the test.
- Documents page test: 1 file passed, 1 test passed.
- TypeScript: `npx tsc --noEmit` exited `0`.

## 2026-05-12 Follow-Up Implementation

Implemented `SidebarTripContext` in the global shell:

- Shows current trip context only when `Shell` already has a `shellTrip`.
- Reuses `getPlanningListSummary()` so sidebar copy, status, next action, and route target stay aligned with Trips in Planning.
- Adds no new backend/API route, no new fetch path, and no parallel planning state model.
- Keeps the block hidden on the collapsed mobile/sidebar rail using existing responsive shell behavior.

Fresh verification:

```bash
cd frontend && npm test -- "src/components/layouts/__tests__/Shell.test.tsx" --reporter=dot
cd frontend && npm test -- "src/app/(agency)/documents/__tests__/page.test.tsx" --reporter=dot
cd frontend && npm test -- "src/lib/__tests__/nav-modules.test.ts" --reporter=dot
cd frontend && npx tsc --noEmit
```

Result:

- Shell sidebar trip-context test: 1 file passed, 2 tests passed.
- Documents page test: 1 file passed, 1 test passed.
- Nav modules test: 1 file passed, 2 tests passed.
- TypeScript: `npx tsc --noEmit` exited `0`.

## Authenticated Browser Verification

Timestamp: 2026-05-12 09:14:08 IST.

Account used: `newuser@test.com`.

Route checked: `http://localhost:3000/trips/trip_5c1389d95a21/intake`.

Observed in the live browser:

- The left navigation includes Overview, Lead Inbox, Quote Review, Trips in Planning, Documents, Insights, Audit, and Settings as enabled links.
- Quotes, Bookings, Payments, Suppliers, and Knowledge Base remain disabled with planned/coming-soon semantics.
- Documents is enabled as a real link after the contract-regression gate completion.
- The new `Current trip` sidebar context block renders in the left rail for the trip route.
- The context block shows the trip status `Need Customer Details`, the current trip label `leisure`, party/date summary `1 pax · TBD`, the next-step copy, and the `Open missing details` link back to the intake route.
- The implementation is confirmed against an authenticated runtime session and is not only unit-test coverage.

Runtime note:

- DevTools showed one `GET /api/trips/trip_5c1389d95a21` `500` during initial load, but the authenticated trip page recovered and rendered the trip workspace and sidebar context. This should be investigated separately if it repeats; it did not block the sidebar/nav verification.
