# Overview Action Required v1.1 Refinement (2026-05-18)

## Product correction

The original v1 implementation was technically safe but product-weak because it
restated totals as rows (`new enquiries waiting`, `agency health check`) instead
of telling the operator which exact record to open first.

This v1.1 refinement changes Action Required from a counts-adjacent summary into
a specific worklist.

## Rules now implemented

- Primary Action Required items must represent a specific record.
- Totals-only lead and agency-health rows are removed from the primary list.
- Specific trip items come from `workspaceTrips`.
- Specific quote-review items come from `pendingReviews`.
- Specific enquiry items come from `useInboxTrips(..., limit=5)`.
- No new backend endpoint.
- No per-trip Ops fetches.
- No payment/document/booking aggregation added in this slice.
- Empty state remains:
  - `No urgent action detected from available data.`

## Ranking

- Overdue trips first
- Then red trips
- Trip ordering uses travel-date proximity when `dateWindow` is explicitly parseable
- Quote reviews follow trips, oldest submitted first
- Enquiries follow quotes, sorted by SLA risk and submitted age

## UI changes

- Action Required rows are now more compact and queue-like
- Each row shows:
  - title
  - specific record label
  - travel/submitted metadata when available
  - reason
  - direct CTA

## Files updated

- `frontend/src/app/(agency)/overview/buildActionRequiredItems.ts`
- `frontend/src/app/(agency)/overview/useOverviewSummary.ts`
- `frontend/src/components/overview/ActionRequiredList.tsx`
- `frontend/src/app/(agency)/overview/__tests__/buildActionRequiredItems.test.ts`
- `frontend/src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts`
- `frontend/src/app/(agency)/overview/__tests__/page.test.tsx`
- `frontend/src/components/overview/__tests__/ActionRequiredList.test.tsx`

## Verification

Executed:

```bash
cd frontend && npx vitest run \
  src/app/(agency)/overview/__tests__/buildActionRequiredItems.test.ts \
  src/components/overview/__tests__/ActionRequiredList.test.tsx \
  src/app/(agency)/overview/__tests__/useOverviewSummary.test.ts \
  src/app/(agency)/overview/__tests__/page.test.tsx
```

Result:

- 4 test files passed
- 25 tests passed
