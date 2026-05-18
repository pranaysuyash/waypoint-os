# Overview “Action Required” v1 — Read-Only Design Pass (2026-05-18)

## Scope and Intent

Goal for this slice: convert Overview from a counts-first dashboard to a practical first-action list using **existing Overview data sources only**.

User-facing language to use:
- `Action Required`
- `Trips, enquiries, and quotes that need attention first.`
- `New enquiries`
- `Quotes to review`
- `Trips in planning`
- `Agency health`

Out of scope for v1:
- No new backend endpoints
- No additional per-trip Ops fetches
- No payment/booking/document aggregation logic from deeper Trip Ops

---

## Code Evidence Read (Current State)

Primary files inspected:
- `frontend/src/app/(agency)/overview/PageClient.tsx`
- `frontend/src/app/(agency)/overview/useOverviewSummary.ts`
- `frontend/src/hooks/useTrips.ts`
- `frontend/src/hooks/useGovernance.ts`
- `frontend/src/hooks/useIntegrityIssues.ts`
- `frontend/src/lib/api-client.ts` (`Trip` shape)
- `frontend/src/types/governance.ts` (`TripReview`, `InboxTrip`)
- `frontend/src/lib/planning-status.ts`
- `frontend/src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts`
- `frontend/src/app/(agency)/overview/__tests__/page.test.tsx`

Observations:
- Overview currently renders header + metric cards first, then main content (`PageClient.tsx`).
- `useOverviewSummary` already queries all four required sources:
  1. workspace trips (`useTrips({ view: 'workspace', limit: 5 })`)
  2. lead inbox (`useInboxTrips(undefined, 1, 1)`)
  3. pending quote reviews (`useReviews({ status: 'pending' })`)
  4. integrity/system issues (`useIntegrityIssues()`)
- The hook currently returns totals and a few arrays (`recentTrips`, `pipeline`) but **does not expose a unified actionable list**.

---

## 1) What item-level data is available today?

Available now (without backend changes):

1. Workspace trips item data (top 5)
- From `useTrips({ view: 'workspace', limit: 5 })` via `workspace.data`
- Includes trip-level fields like:
  - `id`, `destination`, `type`, `state`, `status`, `action`, `overdue`, `dateWindow`, `party`, `validation`, `decision`, etc.
- Sufficient for v1 trip-level action items (red/overdue/needs-details style items)

2. Reviews item data
- From `useReviews({ status: 'pending' })` via `pendingReviews.data`
- `TripReview` includes fields such as:
  - `id`, `tripId`, `destination`, `tripType`, `submittedAt`, `status`, `reason`, `feedbackSeverity`, etc.
- Sufficient to create actionable quote-review items and deep-link to `/reviews`

3. Inbox item data (limited by current call params)
- From `useInboxTrips(undefined, 1, 1)` via `inbox.data`
- Current call asks for only 1 item (plus total), so actionable list has very limited per-lead detail unless the query limit is raised
- `InboxTrip` has rich fields (`id`, `destination`, `stage`, `slaStatus`, `priority`, `customerName`, etc.)

4. Integrity issue item data
- From `useIntegrityIssues()` via `integrityIssues.data`
- Includes issue-level details (`id`, `issue_type`, `severity`, `reason`, etc.)
- Enough for v1 agency health action summary

---

## 2) Which sources expose only totals?

Strictly speaking, all four queried sources can return item arrays today.

But in **current Overview usage**:
- Lead inbox is effectively totals-first because `useInboxTrips` is called with `limit=1`
- Pending reviews are rendered as totals-only in metrics/nav even though item data exists
- Integrity issues are rendered as totals-only in metrics/nav even though item data exists

So the practical limitation is not endpoint capability; it is current summary shaping and the inbox limit.

---

## 3) What Action Required item types can be built without new backend endpoints?

Safe v1 item types from existing Overview-level data:

1. `Quotes to review` (`source: 'quote'`)
- Trigger: `pendingReviews.total > 0`
- CTA: `Review quotes` -> `/reviews`
- Can include count-based reason, and optionally first pending review’s destination in subtitle when present

2. `New enquiries waiting` (`source: 'lead'`)
- Trigger: `inbox.total > 0`
- CTA: `Open enquiries` -> `/inbox`
- Count-based reason is safe; item-level lead subtitle is optional unless inbox fetch limit is increased

3. `Trips in planning needing attention` (`source: 'trip'`)
- Trigger: from `workspace.data` trip states/flags already fetched for Overview
- Candidate signals:
  - `trip.overdue === true`
  - `trip.state === 'red'`
  - `trip.state === 'blue'` or planning blocker semantics from existing `planning-status` helpers
- CTA: `Open trip` -> `/trips/{id}` (or canonical trip detail route used in app)

4. `Agency health` (`source: 'system'`)
- Trigger: `integrityIssues.total > 0`
- CTA: `Check status` -> `/overview?panel=system-check`

---

## 4) What needs future backend support?

For v2 “true agency queue” quality, backend support should provide:

1. Single aggregated action queue endpoint
- Unified, ranked actions across leads/trips/reviews/system to avoid frontend stitching and cross-query heuristics

2. First-class action semantics
- Canonical fields like `action_type`, `severity`, `is_blocking`, `due_at`, `entity_id`, `entity_route`

3. Deep Trip Ops rollups
- Booking-at-risk, payment due, missing customer submission/docs, confirmation blockers
- These are intentionally out of v1 scope

4. Pagination and deterministic ranking server-side
- Stable ordering across sessions and clients

---

## 5) What ranking rules are safe?

Safe v1 ranking (deterministic, no overclaiming):

1. Pending quote reviews (urgent/high)
2. Overdue or red trips from `workspace.data` (high)
3. New enquiries waiting (high/normal by count)
4. Blue/amber planning trips needing detail/options (normal)
5. Agency health system check (normal/low unless severity parsing is added)

Implementation-safe constraints:
- Cap to top 5 items
- Use only already-loaded Overview queries
- Avoid “all clear” language
- If data is partial/loading/error, prefer omission or conservative copy

---

## 6) What user-facing copy should be used?

Section title:
- `Action Required`

Section subtitle:
- `Trips, enquiries, and quotes that need attention first.`

Item copy templates (v1):
- Quote:
  - Title: `Quote needs review`
  - Reason: `{N} quote(s) are waiting for approval before sending.`
  - CTA: `Review quotes`
- Lead:
  - Title: `New enquiries waiting`
  - Reason: `{N} new enquiries need qualification or assignment.`
  - CTA: `Open enquiries`
- Trip (red/overdue):
  - Title: `Trip needs review`
  - Subtitle: `{Trip name/destination}`
  - Reason: `This trip is marked for attention in planning.`
  - CTA: `Open trip`
- Trip (missing details):
  - Title: `Trip needs customer details`
  - Subtitle: `{Trip name/destination}`
  - Reason: `Customer trip details are still missing.`
  - CTA: `Open trip`
- System:
  - Title: `Agency health check`
  - Reason: `{N} item(s) need review.`
  - CTA: `Check status`

Empty state copy (required):
- `No urgent action detected from available data.`

---

## 7) Where should the section render?

Recommended placement in `PageClient.tsx`:
- Render `Action Required` **immediately below the header and above metric cards**.

Reason:
- This aligns with the product objective: answer “What should I do now?” before showing counts.
- Keeps existing metric cards and rest of Overview intact.

---

## 8) What tests are needed?

New test file target:
- `frontend/src/components/overview/__tests__/ActionRequiredList.test.tsx`

Required scenarios:
1. Quote review item appears when pending reviews > 0
2. Lead inbox item appears when inbox total > 0
3. Red/overdue trip item appears from workspace trips
4. System issue item appears when integrity issues > 0
5. Empty state renders exact copy when no actionable items

Integration updates:
- `frontend/src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts`
  - Assert action-required list shaping/ranking from hook output
- `frontend/src/app/(agency)/overview/__tests__/page.test.tsx`
  - Assert section placement and item CTAs/routes

Test assertions should also verify:
- Max 5 items
- Ranking order respects v1 priority rules
- No “all clear” wording

---

## 9) What must not be built in v1?

Must not include:
- Payment due rollups
- Customer booking-data submission tasks
- Pending document review queue
- Booking confirmation issue aggregation
- Any per-trip extra fetch loop from Overview
- Any new backend endpoint
- Any language implying global completion (e.g., “Everything is done”)

---

## Suggested v1 shape (for implementation phase)

```ts
export type ActionRequiredPriority = 'urgent' | 'high' | 'normal' | 'low';

export type ActionRequiredItem = {
  id: string;
  priority: ActionRequiredPriority;
  source: 'quote' | 'lead' | 'trip' | 'system';
  title: string;
  subtitle: string;
  reason: string;
  href: string;
  ctaLabel: string;
};
```

Implementation notes for next step:
- Build a dedicated derivation hook (`useActionRequiredItems`) from existing summary query results
- Keep `useOverviewSummary` as query orchestration + typed outputs
- Keep UI component (`ActionRequiredList`) presentational and deterministic
