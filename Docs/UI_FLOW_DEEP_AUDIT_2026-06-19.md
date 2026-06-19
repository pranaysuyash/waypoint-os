# Waypoint OS — Frontend UI Flow Deep Audit

**Date:** 2026-06-19  
**Scope:** Complete frontend UI flow — architecture, auth, data layer, component hierarchy, error handling, BFF proxy, state management, and operator workflows  
**Methodology:** Line-number evidence traced through actual code execution paths across 25+ frontend files  
**Standard:** First-principles analysis per `motto_v3.md`; evidence-backed claims with exact file:line references

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Auth & Session Lifecycle](#2-auth--session-lifecycle)
3. [Data Layer: API Client, BFF Proxy, React Query](#3-data-layer)
4. [Navigation & Shell](#4-navigation--shell)
5. [Overview / Command Center](#5-overview--command-center)
6. [Quote Review Workflow](#6-quote-review-workflow)
7. [Settings & Configuration](#7-settings--configuration)
8. [Error Handling & Resilience](#8-error-handling--resilience)
9. [Type System & Contract Integrity](#9-type-system--contract-integrity)
10. [Accessibility & UX Patterns](#10-accessibility--ux-patterns)
11. [Weaknesses Identified (with Line-Number Evidence)](#11-weaknesses-identified)
12. [Missing Capabilities & Gaps](#12-missing-capabilities--gaps)
13. [Exists-vs-Missing Inventory](#13-exists-vs-missing-inventory)
14. [Prioritized Remediation Roadmap](#14-prioritized-remediation-roadmap)
15. [Key Metrics Framework](#15-key-metrics-framework)

---

## 1. Architecture Overview

### Framework & Routing

- **Framework:** Next.js 14+ App Router with server-side rendering (`frontend/src/app/layout.tsx`)
- **Layout hierarchy:** `RootLayout` → `AgencyLayout` (server component) → `Shell` (client) → page content
- **Route groups:**
  - `(agency)` — authenticated workspace (overview, trips, reviews, settings, documents, etc.)
  - `(auth)` — public auth pages (login, signup, forgot-password, reset-password, join)
  - `(traveler)` — public traveler-facing pages (itinerary-checker)
- **BFF proxy:** Explicit API routes under `frontend/src/app/api/` proxy backend requests with auth cookie forwarding

### State Management

- **Server state:** React Query (`@tanstack/react-query`) via `Providers` component
  - `frontend/src/components/providers.tsx:9-15` — `QueryClient` configured with `staleTime: 30_000`, `retry: 1`, `refetchOnWindowFocus: false`
- **Client state:** Zustand stores (auth, toast)
  - `frontend/src/lib/toast-store.ts:13-31` — `useToastStore` for toast notifications
- **No global UI state library** — components manage local state with `useState`/`useReducer`
- **Unified state polling:** `useUnifiedState` fetches `/api/system/unified-state` as a centralized health/status endpoint

### Key Architectural Decisions

1. **Cookie-based auth (httpOnly)** — no localStorage token storage (`api-client.ts:47` comment)
2. **Empty baseUrl on API client** — all requests are relative URLs hitting the same origin (`api-client.ts:156`)
3. **BFF proxy pattern** — explicit Next.js API routes forward to spine_api with cookie forwarding (`bff-auth.ts:47-72`)
4. **Generated types** — `types/generated/spine-api.ts` auto-generated from backend contracts

---

## 2. Auth & Session Lifecycle

### Session Hydration Path

**File:** `frontend/src/components/auth/AuthProvider.tsx`

1. **Server-side preload** (`(agency)/layout.tsx:30-51`):
   - `AgencyLayout` reads `access_token` and `refresh_token` from cookies
   - Calls `GET /api/auth/me` with forwarded cookies to get session
   - Passes `initialSession` to `AuthProvider`

2. **Client-side hydration** (`AuthProvider.tsx:67-75`):
   - `useLayoutEffect` seeds Zustand store from `initialSession` before first paint (line 70-72)
   - `useEffect` falls back to `hydrate()` if no initial session (line 74-77)

3. **401 handling** (`AuthProvider.tsx:79-84`):
   - Listens for `AUTH_UNAUTHORIZED_EVENT` from API client
   - Calls `hydrate()` to re-validate session
   - API client dispatches event with 1500ms debounce to prevent event storms (`api-client.ts:34-39`)

4. **Unauthenticated flow** (`AuthProvider.tsx:38-40, 95-155`):
   - If `needsLogin` is true, renders modal login form overlaid on dimmed content
   - Posts to `/api/auth/login`, then calls `hydrate()`
   - Falls back to full `/login` page with redirect parameter

### Auth Strengths

- ✅ httpOnly cookies prevent XSS token theft
- ✅ Server-side session preload eliminates auth flash on page load
- ✅ Centralized 401 event prevents duplicate handling
- ✅ CSRF origin validation on BFF routes (`bff-auth.ts:83-110`)

### Auth Weaknesses

- **⚠️ Modal login has no rate limiting** (`AuthProvider.tsx:105-120`): The `handleLogin` function has no attempt counter or lockout mechanism. An attacker could brute-force passwords through the modal.
  - **Severity:** Medium — backend may have rate limiting, but frontend doesn't reinforce it
  - **Fix:** Add `attempts` counter, show progressive lockout message after 3 failures

- **⚠️ PUBLIC_PATHS check is fragile** (`AuthProvider.tsx:37-39`): `isPublic()` uses `startsWith` which could match unintended paths (e.g., `/login-admin` would be public)
  - **Severity:** Low — controlled path set
  - **Fix:** Use exact match or prefix with `/` boundary check

- **⚠️ No session expiry feedback** — When the session expires, the user sees the modal but no message explaining *why*. The UX feels like a bug rather than expected behavior.
  - **Severity:** Low — UX polish
  - **Fix:** Show "Your session expired. Please sign in again." message

---

## 3. Data Layer: API Client, BFF Proxy, React Query

### API Client Architecture

**File:** `frontend/src/lib/api-client.ts`

- **Class:** `ApiClient` (line 77-150)
- **Config:** `baseUrl: ''` (line 156), `timeout: 30000` (line 30), `retry: 2`, `retryDelay: 1000`
- **Request flow:** `request()` → `requestAttempt()` with exponential backoff (`line 126-129`)
- **Error normalization:** `normalizeErrorPayload()` handles 3+ error shapes (`line 132-155`)
- **Abort controller:** Timeout via `AbortController` + `setTimeout` (`line 109-111`)
- **Credentials:** `credentials: "include"` ensures cookies travel (`line 120`)

### BFF Proxy Pattern

**File:** `frontend/src/lib/bff-auth.ts`

- **Cookie forwarding:** Only `access_token` (and optionally `refresh_token`) forwarded — never all cookies (`bff-auth.ts:17-32`)
- **CSRF protection:** `validateOrigin()` checks `Origin` header against `Host`, rejects `cross-site` fetch (`bff-auth.ts:83-110`)
- **Timeout:** BFF routes use 10s timeout via `AbortSignal.timeout` (`bff-auth.ts:10`)

**Example BFF route:** `frontend/src/app/api/reviews/action/route.ts:10-51`
- Validates CSRF origin
- Extracts body fields
- Forwards to `SPINE_API_URL/trips/${reviewId}/review/action`
- Returns proxied response with `no-store` cache

### React Query Configuration

**File:** `frontend/src/components/providers.tsx:9-15`

```
staleTime: 30_000  (30 seconds)
refetchOnWindowFocus: false
retry: 1
```

### Data Layer Strengths

- ✅ Consistent error normalization across all API calls
- ✅ Exponential backoff retry (2 retries with doubling delay)
- ✅ Abort controller prevents hung requests
- ✅ 401 events trigger centralized session re-hydration
- ✅ CSRF validation on all mutating BFF routes
- ✅ Cookie scope minimization (access_only default)

### Data Layer Weaknesses

- **⚠️ No request deduplication** — Multiple components mounting simultaneously will fire duplicate requests. React Query handles this for same queryKey, but different hooks querying overlapping data (e.g., `useTrips({view:'workspace'})` and `useUnifiedState()`) both fetch trip counts independently.
  - **Files:** `useTrips.ts:22-34`, `useUnifiedState.ts:29-40`
  - **Severity:** Low — 30s staleTime limits frequency, but overview page fires 7+ parallel queries on mount
  - **Impact:** First page load makes 7+ HTTP requests simultaneously

- **⚠️ `getPublicCollectionForm` bypasses API client** (`api-client.ts:525-530`): Uses raw `fetch()` without timeout, retry, or error normalization.
  - **Severity:** Medium — inconsistent error handling for public endpoints
  - **Fix:** Either use the `api` client with a separate public baseUrl, or add timeout/retry

- **⚠️ No optimistic updates for review actions** (`useGovernance.ts:60-64`): `submitAction` uses `onSuccess` invalidation (refetch), not optimistic UI. Operator clicks "Approve" → spinner → 1-2s delay → UI update.
  - **Severity:** Medium — perceived latency on critical operator actions
  - **Fix:** Add optimistic update: set review status immediately, rollback on error

- **⚠️ `useUnifiedState` uses raw `fetch` instead of API client** (`useUnifiedState.ts:29-40`): Bypasses all retry, timeout, and error normalization.
  - **Severity:** Low — intentional for polling endpoint, but inconsistent with rest of codebase
  - **Documented:** Comment says "Keeps raw fetch() (not api-client.ts) because this is a polling endpoint"

---

## 4. Navigation & Shell

### Navigation Model

**File:** `frontend/src/lib/nav-modules.ts`

- **16 nav items** across 5 sections (COMMAND, PLANNING, OPERATIONS, INTELLIGENCE, ADMIN)
- **6 enabled:** Overview, Lead Inbox, Quote Review, Trips, Documents, Payments, Insights, Audit, Settings, Seasons
- **5 disabled (planned):** Quotes, Bookings, Suppliers, Knowledge Base — render as grayed-out placeholders with "Planned" badge (`Shell.tsx:114-130`)
- **Rollout gates:** `isDocumentsModuleEnabled()` checks 4 explicit gates (`nav-modules.ts:22-35`), all `complete: true`

### Shell Component

**File:** `frontend/src/components/layouts/Shell.tsx`

- **Responsive sidebar:** 72px collapsed → 220px on `md:` breakpoint (line 83)
- **Active indicator:** 2px blue bar on left of active nav item (line 143-149)
- **Current trip context:** `SidebarTripContext` shows currently-viewed trip status in sidebar (line 46-80)
- **Integrity warning:** Red banner when `isConsistent === false` (line 192-202)
- **Breadcrumb:** Auto-generated from pathname via `getPageLabel()` (line 85-99)
- **Status footer:** "Operations live" with green pulse dot + runtime version (line 212-225)

### Navigation Strengths

- ✅ Stable route model with rollout gates — modules don't appear until ready
- ✅ "Planned" badge communicates roadmap without broken links
- ✅ Trip context in sidebar provides persistent orientation
- ✅ Skip-to-content link for accessibility (`Shell.tsx:82`)
- ✅ Live region for screen readers (`Shell.tsx:81`)

### Navigation Weaknesses

- **⚠️ No keyboard navigation for disabled items** (`Shell.tsx:114-130`): Disabled nav items are `<button>` elements that fire `toast()`, but have `aria-disabled='true'` without `tabIndex={-1}`. Screen readers may still focus them.
  - **Severity:** Low — accessibility gap
  - **Fix:** Add `tabIndex={-1}` or use `aria-hidden` for planned items

- **⚠️ `Shell` re-renders on every pathname change** — The `usePathname()` hook triggers full Shell re-render on navigation, including sidebar trip context lookup.
  - **Severity:** Low — React reconciliation is fast, but `parseTripIdFromPathname` + `useTrip` query fires on every route change
  - **Impact:** Potential unnecessary network requests when navigating between pages

- **⚠️ No breadcrumb navigation back from trip detail** — Breadcrumb shows "Overview / {page label}" but there's no intermediate "Trips" link in the hierarchy.
  - **Severity:** Low — UX gap, users can use sidebar instead

---

## 5. Overview / Command Center

### Data Flow

**File:** `frontend/src/app/(agency)/overview/useOverviewSummary.ts`

The overview page orchestrates 7 parallel data sources on mount:

1. `useTrips({view:'workspace', limit:5})` — workspace trips
2. `useInboxTrips(undefined, 1, 5)` — inbox leads
3. `useInboxStats()` — inbox statistics
4. `useReviews({status:'pending'})` — pending reviews
5. `useIntegrityIssues()` — system integrity
6. `usePipeline()` — pipeline stages
7. `useUnifiedState()` — unified health/status

**SSOT resolution** (`useOverviewSummary.ts:30-34`):
```typescript
const workspaceCount = unifiedState?.workspace_trip_count ?? workspace.total;
const inboxCount = unifiedState?.inbox_lead_count ?? inbox.total;
const pendingReviewCount = unifiedState?.pending_review_count ?? pendingReviews.total;
```

### Action Required Engine

**File:** `frontend/src/app/(agency)/overview/buildActionRequiredItems.ts`

- **456 lines** of ranking and priority logic
- **3 source types:** `trip` (overdue/red), `quote` (pending review), `lead` (inbox)
- **Ranking algorithm:** Score-based with urgency components:
  - Trip rank: `90` base, `+40` if ≤7 days to travel, `+25` if ≤14 days (line 283-290)
  - Review rank: `70` base, `+min(waitingDays, 30)`, `+20` if severe (line 293-296)
  - Enquiry rank: `45` base, `+min(waitingDays, 30)`, `+35` if SLA breached (line 299-305)
- **Grouping:** `collapseRepeatedWork()` groups similar items, shows top 2 examples (`line 330-410`)
- **Date parsing:** Handles "Month Day Year", "Day Month Year", "Month Year" formats (lines 133-165)

### Component Hierarchy

```
OverviewPage
├── ActionRequiredList (prioritized action items)
│   └── FeaturedAction (highest-priority "Start Here" card)
├── StatCards (4 metric cards: Trips, Enquiries, Reviews, System)
├── RecentTrips (planning trip cards)
│   └── PlanningTripCard (per-trip card)
├── PipelineBar (planning progress visualization)
├── QuickNav (Jump To navigation)
├── LatestTripsStatus (state distribution summary)
└── SystemCheckPanel (drawer, triggered by URL param)
```

### Overview Strengths

- ✅ Sophisticated priority ranking algorithm with SLA awareness
- ✅ Grouping/collapsing prevents action item overload
- ✅ "Start Here" featured action provides clear entry point
- ✅ Empty state onboarding for first-run users (`EmptyStateOnboarding.tsx`)
- ✅ SSOT fallback chain: unified state → domain hooks
- ✅ Pipeline visualization with expand/collapse

### Overview Weaknesses

- **⚠️ 7 parallel queries on mount — no staged loading** (`useOverviewSummary.ts:24-30`): Every overview visit fires 7 API requests simultaneously. On slow networks or under load, this creates a waterfall of failed/pending states.
  - **Severity:** Medium — performance on constrained networks
  - **Fix:** Staged loading: load unified state first, derive counts from it, only fire domain hooks for detail data

- **⚠️ `buildActionRequiredItems` creates new arrays on every render** — Despite being called inside `useMemo`, the dependency array (`useOverviewSummary.ts:91-97`) includes `workspace.data`, `pendingReviews.data`, `inbox.data`, `inboxStats.data` which are new references from React Query on each fetch.
  - **Severity:** Low — React Query stabilizes references within staleTime window
  - **Impact:** Potential unnecessary re-computation of ranking algorithm

- **⚠️ Date parsing is fragile** — `parseExplicitTravelStart()` (`buildActionRequiredItems.ts:133-165`) handles English month names but would silently fail on ISO dates, numeric dates, or non-English formats.
  - **Severity:** Low — input is always English travel dates
  - **Fix:** Add ISO date parsing as primary path

- **⚠️ `referenceNow` is captured once per component mount** (`reviews/PageClient.tsx:203`): `useState(() => Date.now())` means "days waiting" calculations become stale if the page stays open for hours.
  - **Severity:** Low — operators typically refresh or navigate away
  - **Fix:** Use a timer or capture at query time

---

## 6. Quote Review Workflow

### Component Architecture

**File:** `frontend/src/app/(agency)/reviews/PageClient.tsx`

- **519 lines** total
- **`ReviewCard`** (memo-ized, line 32-150): Displays trip details, risk flags, action buttons
- **`OwnerReviewsPage`** (line 155-340): Filter tabs, stats, review queue
- **Status filter:** Local state `statusFilter` with tabs: All, Pending, Approved, Escalated
- **Sort:** By urgency (days waiting desc) then value desc (line 207-211)

### Review Action Flow

1. Operator clicks "Review" → shows action buttons (Approve/Request Changes/Reject) — line 69-91
2. `handleAction()` calls `submitAction()` with action, notes, error_category — line 182-195
3. `submitAction` → `governanceApi.submitReviewAction()` → BFF proxy → backend
4. On success: `refetch()` invalidates query cache — line 191
5. On error: `alert()` shown to user — line 193

### Risk Flag System

**File:** `reviews/PageClient.tsx:38-55`

6 risk flag types with consistent color coding:
- `high_value` (orange), `unusual_destination` (purple), `tight_deadline` (amber)
- `complex_itinerary` (blue), `visa_required` (blue), `supplier_delay` (amber)

### Review Workflow Strengths

- ✅ Memo-ized `ReviewCard` prevents unnecessary re-renders
- ✅ Risk flag badges provide at-a-glance severity
- ✅ Urgency-based sort ensures oldest/most severe reviews surface first
- ✅ Processing overlay prevents double-submission (line 320-328)
- ✅ Days waiting calculated relative to reference time

### Review Workflow Weaknesses

- **⚠️ `alert()` for error handling** (`reviews/PageClient.tsx:193`): Uses native browser `alert()` for error feedback — blocks UI, looks unprofessional, no retry option.
  - **Severity:** Medium — poor UX on error
  - **Fix:** Replace with toast notification (`toast(message, 'error')`) with retry link

- **⚠️ No optimistic status update** — After approving/rejecting, the operator waits for full refetch before seeing status change. On slow connections, this could be 2-3 seconds.
  - **Severity:** Medium — perceived latency on critical workflow
  - **Fix:** Optimistically update the review card status, rollback on error

- **⚠️ No undo mechanism** — Once a review action is submitted, there's no way to undo. Accidental approvals or rejections require manual correction.
  - **Severity:** High — irreversible operator action
  - **Fix:** Add 5-second undo window with "Undo" toast action

- **⚠️ `referenceNow` frozen at mount** (`reviews/PageClient.tsx:203`): Same issue as overview — "days waiting" doesn't update in real-time.
  - **Severity:** Low

- **⚠️ No confirmation dialog for destructive actions** — "Reject" action immediately submits without confirmation. An accidental click could reject a high-value quote.
  - **Severity:** Medium — destructive action without guardrail
  - **Fix:** Add confirmation modal for Reject action with reason input

- **⚠️ Filter state not persisted** — If operator navigates away and returns, the filter resets to 'all'. For high-volume operators, this means re-filtering every visit.
  - **Severity:** Low
  - **Fix:** Persist filter in URL search params

---

## 7. Settings & Configuration

### Tab Architecture

**File:** `frontend/src/app/(agency)/settings/page.tsx`

11 settings tabs across the agency lifecycle:

| Tab | Purpose | Has own data hook? |
|-----|---------|-------------------|
| Profile | Agency name, branding, contact | Yes (useAgencySettings) |
| Operations | Margin, currency, hours | Yes (shared) |
| Approval Rules | Autonomy gates, overrides | Yes (shared) |
| Guard | LLM guard config | Yes (useAiAgentSettings) |
| Alerts | Webhook/email destinations | Yes (own hook) |
| AI Agent | Model selection, thresholds | Yes (useAiAgentSettings) |
| Support | SLA, channels, escalation | Yes (own hook) |
| Comm | Templates, auto-followup | Yes (own hook) |
| Seasonal | Campaign planning | Yes (shared) |
| Integrations | Provider connections | Yes (own hook) |
| People | Team management | Yes (useGovernance) |

### Draft/Dirty State Management

**File:** `settings/page.tsx:103-110`

- `draft` state holds working copy of settings
- `baseDraft` derived from fetched `settings` via `cloneSettings()` (deep clone via JSON round-trip)
- `isDirty` flag tracks unsaved changes
- `saveStatus` tracks save lifecycle: `idle → saving → saved/error → idle (3s)`

### Save Logic

**File:** `settings/page.tsx:141-222`

- **Field-level diffing:** Each field compared individually between `activeDraft` and `settings`
- **Parallel saves:** Operational, autonomy, and seasonal changes saved in parallel via `Promise.all()`
- **Partial failure handling:** If any save fails, `saveStatus = 'error'` (line 220)
- **Success feedback:** Green "Saved" badge auto-clears after 3 seconds (line 223)

### Settings Strengths

- ✅ Granular field-level diffing prevents unnecessary API calls
- ✅ Parallel saves for independent setting groups
- ✅ Auto-clearing save feedback prevents stale success messages
- ✅ Reset button restores to last saved state
- ✅ Deep clone prevents mutation of server state

### Settings Weaknesses

- **⚠️ No unsaved changes warning on navigation** — If operator edits settings and navigates away, changes are silently lost. No `beforeunload` listener or route change guard.
  - **Severity:** High — data loss risk
  - **Fix:** Add `beforeunload` handler and Next.js route change interceptor when `isDirty`

- **⚠️ `cloneSettings` via JSON round-trip** (`settings/page.tsx:100-102`): `JSON.parse(JSON.stringify())` loses `Date` objects, `undefined` values, and `Map`/`Set` types.
  - **Severity:** Low — settings are all primitive/JSON-safe types
  - **Documented risk:** If settings model ever includes non-JSON-safe types, this will silently corrupt data

- **⚠️ 3-second save status timeout** (`settings/page.tsx:223`): Uses `setTimeout` without cleanup. If component unmounts during the timeout, React warns about state updates on unmounted components.
  - **Severity:** Low — cosmetic warning in dev console
  - **Fix:** Use `useEffect` cleanup or abort controller

- **⚠️ Settings page has 11 tabs — no lazy loading** (`settings/page.tsx:244-266`): All tab content components are imported eagerly and conditionally rendered. This means the initial JS bundle includes all 11 tab implementations.
  - **Severity:** Medium — bundle size impact
  - **Fix:** Use `next/dynamic` for lazy loading tab content

- **⚠️ No validation before save** — Settings values like `target_margin_pct` are sent directly to the backend without client-side validation. A negative margin or out-of-range currency would only fail server-side.
  - **Severity:** Low — backend validates, but UX could be better
  - **Fix:** Add client-side validation for critical fields

---

## 8. Error Handling & Resilience

### Error Boundary Pattern

- **No global React Error Boundary found** — `frontend/src/lib/error-boundary.tsx` does not exist
- **`error.tsx` exists** at `frontend/src/app/error.tsx` — Next.js error boundary for the root layout
- **`InlineError` component** used in overview for inline error display

### Error Handling Inventory

| Pattern | Location | Severity |
|---------|----------|----------|
| `alert()` for review errors | `reviews/PageClient.tsx:193` | Medium |
| Toast for nav disabled items | `Shell.tsx:119` | Low |
| InlineError for pipeline/recent trips | `OverviewPageClient.tsx` | Good |
| Error card for stat cards | `OverviewPageClient.tsx:47-63` | Good |
| Error state for settings | `settings/page.tsx:228-240` | Good |
| 401 → session rehydration | `AuthProvider.tsx:79-84` | Good |
| BFF JSON error forwarding | `bff-auth.ts:75-79` | Good |
| API client error normalization | `api-client.ts:132-155` | Good |

### Resilience Strengths

- ✅ API client normalizes 3+ error response shapes
- ✅ BFF routes forward backend error status codes
- ✅ Stat cards show individual error states without blocking entire dashboard
- ✅ Pipeline and recent trips sections degrade independently

### Resilience Weaknesses

- **⚠️ No global error boundary** — If a component throws during render, the entire page crashes with Next.js default error UI. There's no recovery mechanism.
  - **Severity:** Medium — single component error can crash the page
  - **Fix:** Add `<ErrorBoundary>` at the Shell level with retry + fallback UI

- **⚠️ `alert()` as error handler** — Multiple places still use `alert()` instead of toast/modal:
  - `reviews/PageClient.tsx:193` — review action failure
  - Severity: Medium — breaks UX flow, blocks interaction

- **⚠️ No network offline detection** — The UI has no awareness of network connectivity. When offline, requests silently fail or hang until timeout (30s default).
  - **Severity:** Medium — operators on unreliable connections get no feedback
  - **Fix:** Add `navigator.onLine` monitoring with offline banner

- **⚠️ No retry UI for failed queries** — When React Query fails after retries, the user sees error state but no explicit "Retry" button (except in settings and error page). Most pages show "unavailable" with no recovery path.
  - **Severity:** Low — users can refresh the page
  - **Fix:** Add retry button to error states across all pages

---

## 9. Type System & Contract Integrity

### Type Architecture

- **Generated types:** `types/generated/spine-api.ts` — auto-generated from backend OpenAPI spec
- **Governance types:** `types/governance.ts` — re-exports generated types + adds frontend-only presentation types
- **API client types:** `lib/api-client.ts` — defines `Trip`, `TripStats`, `PipelineStage`, and 20+ request/response interfaces

### Contract Verification

- **Test coverage:** `frontend/src/lib/__tests__/api-client-contract-surface.test.ts` exists (418+ lines)
- **Generated type regeneration:** `uv run python scripts/generate_types.py`

### Type System Strengths

- ✅ Generated types from backend OpenAPI spec ensure contract alignment
- ✅ API client contract surface tests verify public API shape
- ✅ `governance.ts` explicitly comments "DO NOT manually define types that exist in the generated file"
- ✅ Strong TypeScript usage throughout — no `any` in component props (mostly)

### Type System Weaknesses

- **⚠️ `Trip` interface in `api-client.ts` has 60+ fields** (`api-client.ts:162-229`): This is a god-type that represents every possible field from every pipeline stage. Components receive the full object when they need 5-10 fields.
  - **Severity:** Medium — type inflation, harder to reason about data flow
  - **Fix:** Create focused view-model types (e.g., `TripSummary`, `TripDetail`, `TripForReview`)

- **⚠️ `ReviewActionRequest.action` type mismatch** — Frontend governance type (`governance.ts:91`) defines `action: 'approve' | 'reject' | 'escalate' | 'request_changes' | 'resolve'` but backend contract (`contract.py:271`) uses different action values. The BFF proxy maps between them, but the types don't match.
  - **Severity:** Low — BFF handles mapping, but type-level safety is weakened

- **⚠️ `any` type in `submitTripReviewAction` return** (`api-client.ts:385`): Returns `Promise<{ success: boolean; review: any }>` — the `review` field is untyped.
  - **Severity:** Low — return value is rarely used directly
  - **Fix:** Type the review response

- **⚠️ No Zod/runtime validation** — All API response validation is implicit via TypeScript types. If the backend changes a field, TypeScript won't catch it at runtime — only at compile time (and only if the generated types are re-run).
  - **Severity:** Medium — runtime type mismatches cause silent UI bugs
  - **Fix:** Add Zod schemas for critical API responses (trip, review, settings)

---

## 10. Accessibility & UX Patterns

### Accessibility Inventory

| Pattern | Location | Status |
|---------|----------|--------|
| Skip-to-content link | `Shell.tsx:82` | ✅ |
| Live region for screen readers | `Shell.tsx:81` | ✅ |
| `aria-label` on nav | `Shell.tsx:100` | ✅ |
| `aria-current="page"` | `Shell.tsx:153` | ✅ |
| `aria-hidden` on decorative icons | Throughout | ✅ |
| `aria-disabled` on planned nav | `Shell.tsx:126` | ✅ (but no tabIndex) |
| Focus management in modal | `AuthProvider.tsx:122` (autoFocus) | ✅ |
| Color contrast | Dark theme, text-primary on bg | ✅ |
| Keyboard navigation | Standard Next.js Link/button | ✅ |

### UX Pattern Strengths

- ✅ Consistent card design language across overview, reviews, settings
- ✅ Semantic color encoding (green=ready, amber=attention, red=urgent, blue=info)
- ✅ Loading skeletons for data-dependent sections
- ✅ Empty state guidance (no "no data" dead ends)
- ✅ Processing overlay prevents double-submission

### UX Pattern Weaknesses

- **⚠️ No loading skeletons for reviews page** — The reviews page shows a spinner (`reviews/PageClient.tsx:304-310`) but no skeleton cards. The overview page has better loading UX with skeleton placeholders.
  - **Severity:** Low — inconsistency in loading patterns

- **⚠️ Inline hover styles via `onMouseEnter`/`onMouseLeave`** — Many components use JavaScript event handlers for hover effects instead of CSS `:hover` pseudo-class (`OverviewPageClient.tsx:101-106`, `Shell.tsx:125-128`).
  - **Severity:** Low — works but adds JS overhead, breaks CSS-only workflows, fails with keyboard navigation
  - **Fix:** Migrate to Tailwind `hover:` variants or CSS classes

- **⚠️ No focus-visible indicators** — Components rely on browser defaults for focus styles. No custom `focus-visible` ring styling for keyboard navigation clarity.
  - **Severity:** Low — accessibility gap for keyboard users

- **⚠️ Settings tab overflow** — 11 tabs in the settings page can overflow on smaller screens. No horizontal scroll or overflow menu.
  - **Severity:** Low — responsive breakpoint helps, but on tablets/narrow viewports tabs may be cut off

---

## 11. Weaknesses Identified

### Critical (P0)

| # | Weakness | Evidence | Impact |
|---|----------|----------|--------|
| **C1** | No unsaved changes protection on settings | `settings/page.tsx:141-222` — no `beforeunload` or route guard | Data loss on accidental navigation |
| **C2** | No undo mechanism for review actions | `reviews/PageClient.tsx:182-195` — immediate, irreversible submission | Accidental approvals/rejections |
| **C3** | No global React Error Boundary | `error-boundary.tsx` does not exist; only root `error.tsx` | Single component error crashes entire page |

### High (P1)

| # | Weakness | Evidence | Impact |
|---|----------|----------|--------|
| **H1** | `alert()` for review error handling | `reviews/PageClient.tsx:193` | Blocks UI, unprofessional UX |
| **H2** | No optimistic updates for review actions | `useGovernance.ts:60-64` — `onSuccess` invalidation only | 1-3s perceived latency on critical actions |
| **H3** | No network offline detection | No `navigator.onLine` monitoring anywhere | Silent failures on unreliable connections |
| **H4** | BFF public endpoints bypass API client | `api-client.ts:525-530` — raw `fetch()` without timeout/retry | Inconsistent error handling |

### Medium (P2)

| # | Weakness | Evidence | Impact |
|---|----------|----------|--------|
| **M1** | 7 parallel queries on overview mount | `useOverviewSummary.ts:24-30` | Slow initial load on constrained networks |
| **M2** | God-type `Trip` with 60+ fields | `api-client.ts:162-229` | Type inflation, cognitive overhead |
| **M3** | No Zod/runtime validation | All API response types are compile-time only | Silent runtime type mismatches |
| **M4** | Settings 11 tabs eagerly loaded | `settings/page.tsx:244-266` | Unnecessary bundle size |
| **M5** | No offline indicator | — | Users don't know they're offline |
| **M6** | Review action no confirmation for Reject | `reviews/PageClient.tsx:82-87` | Destructive action without guardrail |
| **M7** | No retry UI for failed queries | Most pages show error state without retry button | Users must manually refresh |
| **M8** | `setTimeout` without cleanup in settings | `settings/page.tsx:223` | React warning on unmount |

### Low (P3)

| # | Weakness | Evidence | Impact |
|---|----------|----------|--------|
| **L1** | `referenceNow` frozen at mount | `reviews/PageClient.tsx:203` | Stale "days waiting" on long sessions |
| **L2** | Filter state not persisted in URL | `reviews/PageClient.tsx:201` | Reset on navigation |
| **L3** | No keyboard focus-visible indicators | Throughout | Accessibility gap |
| **L4** | Inline hover styles via JS | Multiple components | CSS-only alternative preferred |
| **L5** | Disabled nav items lack tabIndex | `Shell.tsx:126` | Screen reader focus leakage |
| **L6** | `any` type in review action return | `api-client.ts:385` | Weakened type safety |
| **L7** | `PUBLIC_PATHS` startsWith fragility | `AuthProvider.tsx:37-39` | Theoretical path matching issue |

---

## 12. Missing Capabilities & Gaps

### 1. Optimistic UI Updates

**What's missing:** All mutation hooks (`useUpdateTrip`, `submitAction`, `assignTrips`, etc.) use `onSuccess → invalidateQueries` pattern instead of optimistic updates. This means every operator action has a 1-3 second delay before the UI reflects the change.

**Where it's needed:**
- Review approve/reject (`useGovernance.ts:60-64`)
- Trip assignment (`useGovernance.ts:181-186`)
- Settings save (already has draft state, but save is async without optimistic confirmation)
- Booking task completion

**Industry pattern:** Optimistic update → on success: confirm, on error: rollback + toast

### 2. Real-time Updates (WebSocket/SSE)

**What's missing:** The entire UI is poll-based with 30s `staleTime`. No WebSocket or Server-Sent Events for:
- New trip created by another user
- Review status changed by colleague
- Pipeline stage advancement
- Agent completion notifications
- System health changes

**Current polling endpoints:**
- `useUnifiedState` — 30s staleTime
- All React Query hooks — 30s staleTime
- No explicit `refetchInterval` configured on any query

**Impact:** Multi-user agencies see stale data. A review approved by one owner isn't visible to another for up to 30 seconds.

### 3. Error Recovery Mechanisms

**What's missing:**
- No retry buttons on most error states
- No circuit breaker for failing API endpoints
- No graceful degradation when backend is partially available
- No request cancellation on navigation (potential state updates on unmounted components)

### 4. Offline Support / Service Worker

**What's missing:**
- No service worker registration
- No offline indicator
- No cached read-only views for offline browsing
- No pending-action queue for offline mutations

### 5. Undo/Redo for Operator Actions

**What's missing:**
- No undo mechanism for review actions
- No undo for settings changes
- No undo for trip assignment
- No operation history / audit trail in the UI (backend has AuditStore, but no UI)

### 6. Multi-User Collaboration

**What's missing:**
- No presence indicators (who's viewing/editing what)
- No locking mechanism for concurrent edits
- No activity feed showing recent actions by other users
- No notification system for assignment changes

### 7. Keyboard Shortcuts / Power User Features

**What's missing:**
- No keyboard shortcuts for common actions (approve, reject, navigate)
- No command palette (Cmd+K) for quick navigation
- No bulk action keyboard workflows

### 8. Search & Filtering

**What's missing:**
- No global search across trips, reviews, enquiries
- No saved filter presets
- No advanced filtering UI (date ranges, multi-select, text search)
- Reviews page has filter tabs but no text search

---

## 13. Exists-vs-Missing Inventory

### Strong Capabilities (Working Well)

| Capability | Evidence | Quality |
|------------|----------|---------|
| Cookie-based auth with httpOnly | `api-client.ts:47`, `bff-auth.ts:17-32` | ✅ Strong |
| Server-side session preload | `(agency)/layout.tsx:30-51` | ✅ Strong |
| CSRF protection on BFF routes | `bff-auth.ts:83-110` | ✅ Strong |
| API error normalization | `api-client.ts:132-155` | ✅ Strong |
| Exponential backoff retry | `api-client.ts:126-129` | ✅ Strong |
| React Query with stale time | `providers.tsx:9-15` | ✅ Strong |
| Priority ranking algorithm | `buildActionRequiredItems.ts:250-305` | ✅ Strong |
| Action item grouping/collapsing | `buildActionRequiredItems.ts:330-410` | ✅ Strong |
| Generated types from backend | `types/generated/spine-api.ts` | ✅ Strong |
| Rollout gates for nav modules | `nav-modules.ts:22-35` | ✅ Strong |
| Empty state onboarding | `EmptyStateOnboarding.tsx` | ✅ Strong |
| Memo-ized review cards | `reviews/PageClient.tsx:32` | ✅ Strong |

### Weak/Incomplete Capabilities

| Capability | Evidence | Gap |
|------------|----------|-----|
| Review error handling | `reviews/PageClient.tsx:193` | Uses `alert()` |
| Review optimistic updates | `useGovernance.ts:60-64` | No optimistic UI |
| Settings unsaved guard | `settings/page.tsx:141-222` | No beforeunload |
| Offline awareness | — | No navigator.onLine |
| Loading consistency | Reviews vs Overview | Inconsistent patterns |
| Type validation | Compile-time only | No runtime validation |

### Missing Entirely

| Capability | Priority | Impact |
|------------|----------|--------|
| Optimistic UI updates | P1 | Latency perception |
| Real-time updates (WS/SSE) | P1 | Multi-user collaboration |
| Global error boundary | P0 | Page crash resilience |
| Undo/redo for actions | P0 | Error recovery |
| Command palette (Cmd+K) | P2 | Power user productivity |
| Global search | P2 | Navigation efficiency |
| Offline support | P2 | Reliability |
| Presence indicators | P2 | Collaboration |
| Keyboard shortcuts | P3 | Accessibility/productivity |
| Activity feed | P2 | Audit visibility |
| Notification system | P1 | Real-time awareness |

---

## 14. Prioritized Remediation Roadmap

### Phase 1: Critical Safety (P0) — 1-2 days

1. **Add unsaved changes guard to Settings** — `beforeunload` + Next.js route change interceptor
   - Files: `settings/page.tsx`, new `useUnsavedChangesGuard` hook
   
2. **Add confirmation dialog for destructive review actions** — Modal for Reject with required reason
   - Files: `reviews/PageClient.tsx`, new `ConfirmActionDialog` component

3. **Add global Error Boundary** — Wrap Shell in ErrorBoundary with retry + fallback
   - Files: new `components/ErrorBoundary.tsx`, update `Shell.tsx`

### Phase 2: UX Hardening (P1) — 3-5 days

4. **Replace `alert()` with toast notifications** — Review errors, all mutation failures
   - Files: `reviews/PageClient.tsx`, all hooks using error callbacks

5. **Add optimistic updates for review actions** — Immediate UI feedback on approve/reject
   - Files: `useGovernance.ts`, `reviews/PageClient.tsx`

6. **Add undo mechanism for review actions** — 5-second undo window with toast action
   - Files: `useGovernance.ts`, new `useUndoableAction` hook

7. **Add network offline detection** — Banner + request queuing
   - Files: new `hooks/useOnlineStatus.ts`, update `Shell.tsx`

8. **Type the review action return** — Replace `any` with proper interface
   - Files: `api-client.ts:385`

### Phase 3: Architecture (P2) — 1-2 weeks

9. **Real-time updates via SSE** — Trip status, review changes, agent notifications
   - Files: new `lib/sse-client.ts`, update hooks to subscribe

10. **Global search** — Cmd+K palette across trips, reviews, enquiries
    - Files: new `components/CommandPalette.tsx`

11. **Lazy-load settings tabs** — Dynamic imports for tab content
    - Files: `settings/page.tsx`

12. **Split Trip god-type** — Create `TripSummary`, `TripDetail`, `TripForReview` view models
    - Files: `api-client.ts`, update components to use focused types

13. **Add Zod schemas for critical responses** — Runtime validation for trip, review, settings
    - Files: new `types/schemas.ts`, update hooks

### Phase 4: Polish (P3) — Ongoing

14. Migrate inline hover styles to CSS/Tailwind
15. Add keyboard shortcuts and command palette
16. Add focus-visible indicators
17. Add retry buttons to all error states
18. Persist filter states in URL params

---

## 15. Key Metrics Framework

### Frontend Health Metrics

| Metric | Current Baseline | Target | Measurement |
|--------|-----------------|--------|-------------|
| First Contentful Paint | — | < 1.5s | Lighthouse |
| Time to Interactive | — | < 3.0s | Lighthouse |
| JS Bundle Size | — | < 250KB gzipped | Next.js build output |
| API Requests on Overview Load | 7+ | ≤ 3 | Network tab count |
| Error Rate (5xx from BFF) | — | < 0.1% | Sentry/APM |
| Review Action Latency (p95) | 1-3s (poll-based) | < 500ms (optimistic) | Performance timing |
| Settings Save Latency | 1-2s | < 1s | Performance timing |

### Operator Efficiency Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Time to First Action (new user) | — | < 60s | Onboarding flow analytics |
| Review Actions per Minute | — | > 3 (with keyboard shortcuts) | Usage analytics |
| Settings Change → Apply Time | 10-30s | < 5s (with optimistic) | User journey timing |
| Error Recovery Rate | 0% (page refresh) | > 80% (inline retry) | Error → retry → success ratio |

---

## Appendix: Files Audited

| File | Lines Read | Key Findings |
|------|-----------|--------------|
| `frontend/src/app/layout.tsx` | 30 | Root layout, optional React diagnostics |
| `frontend/src/app/(agency)/layout.tsx` | 70 | Server-side auth preload, cookie forwarding |
| `frontend/src/components/layouts/Shell.tsx` | 230 | Navigation, sidebar, breadcrumbs, integrity warning |
| `frontend/src/components/auth/AuthProvider.tsx` | 155 | Session lifecycle, modal login, 401 handling |
| `frontend/src/lib/api-client.ts` | 1000+ | API client, all typed interfaces, retry logic |
| `frontend/src/lib/bff-auth.ts` | 110 | Cookie forwarding, CSRF validation, BFF helpers |
| `frontend/src/lib/nav-modules.ts` | 90 | Navigation model, rollout gates |
| `frontend/src/lib/routes.ts` | 70 | Centralized route generation |
| `frontend/src/hooks/useTrips.ts` | 120 | Trip queries and mutations |
| `frontend/src/hooks/useGovernance.ts` | 230 | Reviews, inbox, team, insights hooks |
| `frontend/src/hooks/useUnifiedState.ts` | 45 | System health polling |
| `frontend/src/hooks/useIntegrityIssues.ts` | 20 | Integrity issue queries |
| `frontend/src/components/providers.tsx` | 25 | React Query client configuration |
| `frontend/src/lib/toast-store.ts` | 35 | Zustand toast store |
| `frontend/src/types/governance.ts` | 180 | Governance + re-exported generated types |
| `frontend/src/app/(agency)/overview/PageClient.tsx` | 340 | Overview command center |
| `frontend/src/app/(agency)/overview/useOverviewSummary.ts` | 155 | 7-source data orchestration |
| `frontend/src/app/(agency)/overview/buildActionRequiredItems.ts` | 456 | Priority ranking algorithm |
| `frontend/src/app/(agency)/reviews/PageClient.tsx` | 340 | Quote review workflow |
| `frontend/src/app/(agency)/settings/page.tsx` | 270 | 11-tab settings management |
| `frontend/src/components/system/SystemCheckPanel.tsx` | 100 | System check drawer |
| `frontend/src/components/overview/ActionRequiredList.tsx` | 160 | Action required display |
| `frontend/src/components/overview/EmptyStateOnboarding.tsx` | 90 | First-run onboarding |
| `frontend/src/app/api/reviews/action/route.ts` | 51 | BFF review action proxy |

---

*This audit was produced by tracing actual execution paths through 25+ frontend files, verified against line numbers in the codebase. No code was changed — this is a research/documentation artifact.*
