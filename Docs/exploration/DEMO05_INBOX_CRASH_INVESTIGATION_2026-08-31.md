# DEMO-05 Investigation — `/inbox` Chrome Renderer Crash ("Aw, Snap! Error code: 5")

*Date: 2026-08-31*
*Source incident: `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` §2 step 11, §4 finding 5.*
*Method: code-level investigation only (renderer crashes are not reproducible headlessly). Read-only; no product code touched.*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## Executive Summary

- During the demo, first navigation to `localhost:3005/inbox` crashed the Chrome tab ("Aw, Snap!", error code 5 = `SBOX_FATAL_MEMORY_EXCEEDED`, a renderer OOM). A reload rendered the page fine.
- **Verdict: dev-environment noise (likely).** No product-code defect was found on the `/inbox` route after a full sweep.
- The route code is clean: server-driven pagination (default 20 rows, UI max 50), TanStack Query with 30s `staleTime`, **no polling intervals, no unbounded fetches, no setState-in-render, no effect loops**.
- The strongest amplifier chain: dev-mode Next.js first-visit compile of `/inbox` took **172.3s / 1199 modules** (`/tmp/waypoint_frontend.log:368-369`) while the long-lived tab sat under a DevTools-protocol client polling accessibility trees (566+ nodes observed on the workbench) — renderer memory grew under sustained AX serialization + unminified dev bundles + auth 401→refresh→retry churn.
- Backend was heavily loaded during the same window (`POST /api/drafts` taking 29–31s, repeated 504 proxy timeouts), indicating a memory/CPU-pressured machine.
- `/inbox`'s 1199 dev modules is in line with other routes (workbench 1203, pricing 1253) — the dev-bundle weight is systemic app weight, not inbox-specific bloat.
- IMP-04 stays conditional per the brief: keep as a watch-item with the manual repro protocol below; **no code change recommended yet**.

## Code Findings

Route under investigation: `frontend/src/app/(agency)/inbox/` (`page.tsx` server wrapper + `PageClient.tsx` client body).

**No infinite re-render candidates found:**

- `frontend/src/app/(agency)/inbox/PageClient.tsx:128-134` — page wrapped in `<Suspense>` for `useSearchParams`; correct pattern.
- `frontend/src/app/(agency)/inbox/PageClient.tsx:142-146` — `sort`/`dir`/`q`/`page`/`limit` derived from URL; `page`/`limit` clamped via `Math.max(1, …)`.
- `frontend/src/app/(agency)/inbox/PageClient.tsx:149-152` — `activeFilters` memoized on `[searchParams]` (stable per navigation).
- `frontend/src/app/(agency)/inbox/PageClient.tsx:250-254` — the only data-adjacent `useEffect`: a one-shot URL correction when an out-of-range `page` param is clamped. It pushes once, the URL updates, `page === currentPage`, effect settles. **Bounded, not a loop.**
- `frontend/src/components/inbox/ComposableFilterBar.tsx:100-104,132-137,352-356,358-366,381-384,569` — all effects are dropdown focus management / outside-click listeners. No data writes.
- `frontend/src/components/inbox/TripCard.tsx:265-279` — same: focus + outside-click handlers only. Cards are `memo`-wrapped.

**No unbounded polling / interval loops:**

- `rg "setInterval|refetchInterval|refetchOnWindowFocus"` across `frontend/src` — no hits in the inbox route or its hooks. The only intervals live in `IntakePanel.tsx:465` (elapsed timer), `insights/PageClient.tsx:102` (1-min clock), `audit/PageClient.tsx:768-770`, `workbench/RunProgressPanel.tsx:98-104` — none mount on `/inbox`.
- `frontend/src/hooks/useGovernance.ts:305-317` — `useInboxTrips` is a plain TanStack Query: `staleTime: 30_000` (line 40), **no `refetchInterval`**, no SSE/WebSocket.
- `frontend/src/components/providers.tsx:9-19` — global QueryClient defaults: `staleTime: 30_000`, `refetchOnWindowFocus: false`, `retry: 1`. No global polling.
- `frontend/src/components/layouts/Shell.tsx:155-177` — sidebar shell mounted on `/inbox` uses only query hooks (`useTrip`, `useRuntimeVersion`, `useUnifiedState`, `useAgencySettings`), all `staleTime`-gated plain queries (`frontend/src/hooks/useUnifiedState.ts:52-60`).

**No unbounded list fetches:**

- Pagination is server-driven: `frontend/src/app/(agency)/inbox/PageClient.tsx:179-194` passes `page` + `limit` to `useInboxTrips`; the Rows selector offers 10/20/30/50 only (`PageClient.tsx:431-434`); the grid renders exactly the returned page (`PageClient.tsx:484-505`). Backend confirms paged requests: `GET /api/inbox?page=1&limit=20&sort=priority&dir=desc` (`/tmp/waypoint_frontend.log:376,393`).

**No very large one-off imports specific to inbox:** compile module counts are systemic — `/inbox` 1199 modules, `/workbench` 1203 (`log:60`), `/pricing` 1253 (`log:400`). Inbox is not an outlier.

**Minor, unrelated-to-crash observations:**

- During the crash window the first `/api/inbox`, `/api/settings`, `/api/system/unified-state` calls returned **401** (access token expired during the 172s compile wait), then auth-refresh recovered and retries returned 200 (`log:376-394`). This adds re-render churn on first load but is a correctable transient, not a leak.

## Log Evidence

`/tmp/waypoint_frontend.log` (Next.js 14.2.35 dev server, the demo session):

- `log:368-369` — `○ Compiling /inbox ...` → `✓ Compiled /inbox in 172.3s (1199 modules)` — the first `/inbox` visit triggered an extreme dev-mode on-demand compile. This is the crash window.
- `log:370` — `GET /inbox 200 in 963ms` — page served only after the compile finished; the tab sat waiting through the entire 172s.
- `log:376-384` — `GET /api/inbox… 401`, `/api/system/unified-state 401`, `/api/settings 401` — auth token expired while the tab waited; three parallel 401s fired.
- `log:385-388` — `/api/auth/refresh` compiled and returned 200; `log:390-394` — retries returned 200. Page recovered to "0 leads total" state.
- `log:61-62, 73-75, 98-121, 279-285` — `POST /api/drafts` repeatedly taking **26–31s** with numerous 504 proxy timeouts — the machine and backend were under heavy load for the whole session.
- `log:399-400` — `/pricing` then compiled in 20.3s (1253 modules): heavy dev compiles are systemic to this app; `/inbox`'s 172s was extreme due to concurrent load, not route size.
- No React dev-overlay errors, hydration errors, or renderer warnings appear anywhere in the log around `/inbox`. No "Aw, Snap" originates server-side (renderer crashes are client-side by definition).

## Verdict

**dev-environment noise (likely)** — with the caveat that only a human repro can fully close it.

Reasoning:

1. The route code has none of the classic renderer-OOM signatures (no render loops, no polling, no unbounded data, no mega-imports).
2. The crash occurred exactly at the first `/inbox` visit, which coincides with a 172-second dev compile while a CDP client was actively polling AX trees/screenshots against a tab that had been alive through the entire demo session (landing → signup → overview → workbench runs).
3. Chrome error code 5 (`SBOX_FATAL_MEMORY_EXCEEDED`) is a renderer memory cap. Plausible mechanism: sustained AX-tree serialization (each `Accessibility.getFullAXTree` materializes a full tree in the renderer; 566+ nodes per capture on the workbench, and the harness polled repeatedly) + unminified dev bundles + source maps + dev overlay, on a memory-pressured machine (29–31s backend calls, repeated 504s), pushed the renderer over its cap.
4. The instant, clean recovery on reload with identical code is characteristic of environmental memory pressure, not a deterministic app defect.

If the manual repro in a clean environment crashes `/inbox`, upgrade the verdict to "plausible product bug" and revisit; nothing found so far points at a specific suspect line.

## Manual Repro Protocol (human-executable)

**Environment variables to control:** browser profile, DevTools-protocol clients, build mode, tenant data volume, machine load.

**Step 0 — Baseline.**
- Fresh Chrome instance with a scratch profile and **no** CDP/computer-use client attached:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --user-data-dir=/tmp/waypoint-crash-repro --window-position=80,40`
- Start backend + frontend: `spine_api` on `:8000`, `cd frontend && npm run dev -- -p 3005`. Wait for "Ready".
- Note machine memory pressure first (Activity Monitor → Memory tab; expect Memory Pressure green).

**Step 1 — Dev build, human hands, fresh tenant.**
- Sign up a brand-new tenant → process a note in the workbench → click **Lead Inbox** (first visit triggers the dev compile).
- *Success criteria:* page renders header "Lead Inbox" + "0 leads total" (or the real count); **no** "Aw, Snap". Watch the Chrome **Renderer** process in Activity Monitor during and ~2 min after first load: flag if private memory exceeds ~1.5 GB or climbs monotonically without plateau.

**Step 2 — Dev build + CDP harness attached (amplifier test).**
- Relaunch Chrome with a fresh scratch profile; attach the computer-use/DevTools client and poll the AX tree the way the demo session did; navigate to `/inbox` first-visit again.
- *Success criteria:* no crash, and renderer memory materially higher than Step 1 while polling is active → confirms harness amplification; crash here but not in Step 1 → harness-attributed, file no product bug.

**Step 3 — Production build.**
- `cd frontend && npm run build && npm start` (prod on its configured port); repeat Step 1 with the same fresh tenant flow.
- *Success criteria:* no crash; renderer memory noticeably lower than dev-mode Step 1 (prod strips unminified bundles/source maps/overlay). If prod still crashes → escalate to "plausible product bug", capture `chrome://tracing` + a heap snapshot at crash.

**Step 4 — Data-volume stress (optional, only if Steps 1–3 are clean).**
- Seed a scratch tenant with ~200 leads (additive inserts only — **never** touch the `waypoint_os` test DB), page through with Rows=50.
- *Success criteria:* memory plateaus per page; paging Prev/Next does not grow renderer memory across 10+ page turns.

Record for every step: crash yes/no, renderer private memory at 30s/2min/5min, Chrome version, and whether the tab had prior navigation history.

## Recommended Follow-up

1. **Keep IMP-04 conditional / watch-item** (per `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md` §3 IMP-04). No code change until a human repro lands.
2. For future demo sessions, run the crash-prone flow against `npm run build && npm start` (prod) or pre-warm `/inbox` once before recording — first-visit dev compiles (172s here) are the dominant anomaly in the window.
3. Optional hardening (not crash-related): investigate why `/inbox`'s dev compile took 172s vs the app-typical ~2–20s — likely concurrent backend load starvation rather than route complexity; a `NEXT_CPU_COUNT` cap or warm-up route list could stabilize demo-day first visits.
4. If Step 3 (prod) ever crashes, add `@next/bundle-analyzer` for the inbox route and profile with a renderer heap snapshot before touching code.

## Open Questions

- Exact Chrome version and system free-RAM at the moment of the demo crash (not recorded in the demo log).
- Did the CDP harness retain references to prior AX snapshots across polls (client-side retention would compound renderer pressure)? Unknown — harness implementation detail.
- Was the tab's renderer already near its cap from the workbench session before navigating to `/inbox`? A pre-navigation memory reading would settle this in any future repro.
- The 401-storm during the compile wait (`log:376-384`) is a UX papercut independent of the crash; should token refresh be proactively triggered before long in-flight navigations? (Minor; separate from DEMO-05.)
