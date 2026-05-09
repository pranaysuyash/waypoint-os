# Phase 2 Implementation Task Package — React Doctor Remediation (2026-05-09)

## Executive Summary

**Previous phase (done):** 4 risk-class rules eliminated (hooks-order, nested components, `dangerouslySetInnerHTML`, GET side-effect). Score: 51→59. Evidence in `Docs/RISK_FIX_VERIFICATION_2026-05-09.md`.

**Current state:** 780 findings across 54 rules, score 59/100. This handoff packages the remaining work into 8 atomic, verifiable tasks ordered by risk and dependency.

**Target:** Score ≥95 with zero false-positive findings (documented exceptions only).

---

## Baseline (verified)

```
Date: 2026-05-09
Command: npx react-doctor@latest . --json
Score: 59
Total findings: 780
Framework: Next.js, React 19.2.4, TypeScript, 290 source files
```

### Category Breakdown

| Category | Count | Task |
|----------|-------|------|
| Dead Code | 237 | Task 7 |
| Architecture | 151 | Tasks 3, 5 |
| Accessibility | 110 | Task 1 |
| Performance | 91 | Tasks 3, 6 |
| Correctness | 87 | Tasks 1, 2 |
| Next.js | 44 | Task 5 |
| State & Effects | 41 | Task 3 |
| Server | 17 | Task 5 |
| Bundle Size | 2 | Task 6 |

### Rules Already at Zero (from Phase 1)

- `rules-of-hooks` (was 8) ✅
- `no-nested-component-definition` (was 3) ✅
- `nextjs-no-side-effect-in-get-handler` (was 1) ✅
- `no-danger` (was 2) ✅

### Active Next.js Rules (Task 5 scope)

| Rule | Count | Status |
|------|-------|--------|
| `nextjs-missing-metadata` | 20 | Task 5 |
| `server-fetch-without-revalidate` | 15 | Task 5 |
| `nextjs-no-use-search-params-without-suspense` | 11 | Task 5 |
| `nextjs-no-client-fetch-for-server-data` | 4 | Task 5 |
| `nextjs-no-client-side-redirect` | 4 | Task 5 |
| `nextjs-no-a-element` | 2 | Task 5 |
| `nextjs-no-img-element` | 3 | Task 5 |

---

## Rule-by-Rule File Inventory (current)

All file:line references are under `frontend/`.

```
rendering-hydration-mismatch-time (37):
  src/app/(agency)/audit/page.tsx:79,79,79
  src/app/(agency)/insights/page.tsx:161,161
  src/app/(agency)/trips/[tripId]/layout.tsx:242,242
  src/app/(agency)/workbench/OpsPanel.tsx:782,782,782,782,817,817,817
  src/app/(agency)/workbench/page.tsx:842,842,867,867
  src/components/workspace/ReviewControls.tsx:98,98
  src/components/workspace/panels/ActivityTimeline.tsx:223,223,223,223,223
  src/components/workspace/panels/ChangeHistoryPanel.tsx:108,108,130,130,150,150
  src/components/workspace/panels/FeedbackPanel.tsx:78
  src/components/workspace/panels/MetricDrillDownDrawer.tsx:174,174,174,174
  src/components/workspace/panels/TimelineSummary.tsx:100

no-array-index-as-key (48):
  src/app/(agency)/inbox/page.tsx:460         (skeleton — acceptable)
  src/app/(agency)/insights/page.tsx:277
  src/app/(agency)/overview/page.tsx:402       (skeleton — acceptable)
  src/app/(agency)/settings/components/PeopleTab.tsx:143
  src/app/(agency)/trips/[tripId]/layout.tsx:263
  src/app/(agency)/trips/page.tsx:345
  src/app/(agency)/workbench/DecisionTab.tsx:167,175,190,286,359,369
  src/app/(agency)/workbench/OpsPanel.tsx:553,638,678
  src/app/(agency)/workbench/PacketTab.tsx:84,98,118,247,274,299
  src/app/(agency)/workbench/SafetyTab.tsx:107,121,181,193
  src/app/(agency)/workbench/StrategyTab.tsx:51,64,80
  src/app/(public)/booking-collection/[token]/page.tsx:208
  src/app/(traveler)/itinerary-checker/page.tsx:1043,1119,1688
  src/components/inbox/TripCard.tsx:122
  src/components/visual/PipelineFunnel.tsx:90
  src/components/visual/TeamPerformanceChart.tsx:120
  src/components/workspace/panels/DecisionPanel.tsx:180,197
  src/components/workspace/panels/IntakePanel.tsx:1110
  src/components/workspace/panels/MetricDrillDownDrawer.tsx:79
  src/components/workspace/panels/PacketPanel.tsx:276,299
  src/components/workspace/panels/TimelinePanel.tsx:148
  src/components/workspace/panels/TimelineSummary.tsx:42,52,71,84
  src/components/workspace/panels/BookingExecutionPanel.tsx:152,155,197,200,220,238
  src/components/loading/skeleton.tsx:12,19   (skeleton — acceptable)

label-has-associated-control (39):
  src/app/(agency)/settings/components/AutonomyTab.tsx:212,238,265,291,326
  src/app/(agency)/settings/components/OperationalTab.tsx:58,87,111,144,172,198
  src/app/(agency)/trips/[tripId]/followups/page.tsx:206,240
  src/app/(agency)/workbench/IntakeTab.tsx:117,133,154,176
  src/app/(agency)/workbench/ScenarioLab.tsx:189,241
  src/app/(public)/booking-collection/[token]/page.tsx:212,225,237,250,284,293,302,314
  src/components/workspace/ReviewControls.tsx:114,129
  src/components/workspace/modals/OverrideModal.tsx:136,145,165,190,198,217
  src/components/workspace/panels/IntakePanel.tsx:1199,1215,1238,1260

no-tiny-text (52):
  src/app/(traveler)/itinerary-checker/page.tsx: [50 instances of text-[10px] or text-[11px]]
  src/components/workspace/ReviewControls.tsx:141,190

rendering-hydration-mismatch-time (37):
  [see full listing above — 12 files, 37 instances]

nextjs-no-client-fetch-for-server-data (4):
  src/app/(agency)/trips/[tripId]/suitability/page.tsx:25
  src/app/(auth)/join/[code]/page.tsx:54
  src/app/(agency)/trips/[tripId]/layout.tsx:100
  src/app/(agency)/audit/page.tsx:18

nextjs-missing-metadata (20):

react-compiler-destructure-method (52):
  src/app/(agency)/inbox/page.tsx:133-159,227
  src/app/(agency)/workbench/page.tsx:168-988 (17 instances)
  src/app/(agency)/workbench/IntakeTab.tsx:48,49,54
  src/app/(agency)/settings/page.tsx:40,62
  src/app/(agency)/trips/[tripId]/suitability/page.tsx:75,95
  src/app/(agency)/insights/page.tsx:328
  src/app/(agency)/workbench/ScenarioLab.tsx:67
  src/app/(auth)/join/[code]/page.tsx:123
  src/app/(auth)/login/page.tsx:40,40,40
  src/app/(auth)/signup/page.tsx:45,45,45
  src/app/(auth)/reset-password/page.tsx:10
  src/components/auth/AuthProvider.tsx:41
  src/components/layouts/UserMenu.tsx:54,111
  src/components/workspace/panels/IntakePanel.tsx:195,204,207,443,652,891
  src/components/workspace/panels/PacketPanel.tsx:46

prefer-useReducer (17): [17 files, 17 instances — one per component with 4+ useState calls]
rerender-state-only-in-handlers (17): [17 files, 17 instances]
no-cascading-set-state (10): [10 files, 10 instances]
nextjs-no-use-search-params-without-suspense (11): [7 files, 11 instances]
server-fetch-without-revalidate (15): [15 API route handlers — all src/app/api/]
js-combine-iterations (16): [14 files, 16 instances]
js-batch-dom-css (16): [4 files, 16 instances]
js-tosorted-immutable (7): [5 files, 7 instances]
```

---

## Pre-Implementation Research Notes

### server-fetch-without-revalidate — False Negative Risk
All 15 instances are in `src/app/api/` route handlers, NOT page/server components. These are BFF proxy routes that fetch from the backend. However, Next.js route handlers DO cache `fetch` calls by default — if these routes are deployed as serverless functions, the `fetch` calls could return stale data. **Fix:** Add `cache: 'no-store'` or `next: { revalidate: 0 }` to each `fetch()` call in API route handlers. This is a real issue.

### nextjs-missing-metadata — Per-Page Resolution Required
- 20 pages flagged. Some are server components that can take `export const metadata` directly (`app/page.tsx`, `app/v2/page.tsx`).
- Most are `'use client'` pages under route groups (`(agency)/`, `(public)/`, `(traveler)/`). These cannot export static metadata themselves.
- **Resolution strategy:** Resolve case-by-case. For server pages, add page-level `metadata`. For client pages, check whether the route group layout is a server component — if so, add layout-level metadata. Currently `(auth)/layout.tsx` and root `layout.tsx` have it. Missing: `(agency)/layout.tsx`, `(public)/layout.tsx`, `(traveler)/layout.tsx`, `app/page.tsx`, `app/v2/page.tsx`. Do not assume layouts-only; evaluate each flagged file.
- `Metadata` from `next` can also be exported from `generateMetadata` async functions, which work even alongside `'use client'` if the data-fetching is extracted to a server data layer.

### nextjs-no-client-fetch-for-server-data (4)
These 4 pages use `useEffect` + `fetch` for data that should be fetched server-side. Fix: move data fetching to the parent layout server component (or convert page to RSC where possible), and pass data as props or via context. Exact files:
- `src/app/(agency)/trips/[tripId]/suitability/page.tsx:25`
- `src/app/(auth)/join/[code]/page.tsx:54`
- `src/app/(agency)/trips/[tripId]/layout.tsx:100`
- `src/app/(agency)/audit/page.tsx:18`

### no-array-index-as-key — Skeletons Are Acceptable
- 3 files use `[1,2,3].map((i) => ...)` for skeleton loaders with static, identical children. These are acceptable uses of index keys. Document as exception.
- All remaining ~45 instances are on dynamic data (travelers, line items, cards) and must be fixed.

### rendering-hydration-mismatch-time — Correct Fix Pattern
The root cause is always the same pattern: `new Date(x).toLocaleDateString()` or `new Date().toISOString()` executed during render. Server and client produce different output (timezone, locale availability). The standard fix:
1. Create a `useHydrationValue` hook or use `useSyncExternalStore` for client-only values.
2. Or suppress hydration via `suppressHydrationWarning` on specific elements (last resort).
3. Best practice: render nothing on server, populate on client via `useEffect` / `useSyncExternalStore`.

### Dead Code — React Doctor Already Reports It
React Doctor's dead-code detection (237 findings across `types`, `exports`, `duplicates`, `files`) is the primary data source. The implementer should rely on this first, using `knip` as a secondary confidence layer if desired, but it is **not a prerequisite**. Proceed with call-site audits before any removal — dead-code sweeps must never break public contracts.

See `Docs/RISK_FIX_VERIFICATION_2026-05-09.md` for Phase 1 methods.

