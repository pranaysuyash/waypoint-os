# Fix: Remove `any` Types from API Routes

**Date**: 2026-04-23
**Scope**: `frontend/src/app/api/reviews/route.ts`, `frontend/src/app/api/stats/route.ts`
**Problem**: Another agent added `any` type annotations to suppress TypeScript errors instead of defining proper types.

---

## What Was Wrong

The other agent hit implicit-`any` TypeScript errors and sprayed `: any` across both files:

```ts
// reviews/route.ts — before
const frontendReviews = reviews.map((review: any) => transformReviewToFrontendFormat(review));
filteredReviews = frontendReviews.filter((review: any) => review.status === statusFilter);
function transformReviewToFrontendFormat(review: any): any { ... }

// stats/route.ts — before
const totalInPipeline = (spineApiPipeline as any[]).reduce(
  (sum: number, stage: any) => sum + (stage.tripCount || 0), 0);
const strategyStage = (spineApiPipeline as any[]).find((stage: any) => stage.stageId === "strategy");
// ... 3 more instances
```

This defeated TypeScript's compile-time safety. Changing API response shapes would silently break these routes.

---

## What Was Done

### 1. Added `AnalyticsPipelineStage` to canonical types

**File**: `frontend/src/lib/api-client.ts`

```ts
export interface AnalyticsPipelineStage {
  stageId: string;
  tripCount: number;
  exitRate: number;
  avgTimeInStage: number;
}
```

Documented as "runtime metrics, not configuration" to distinguish from the existing `PipelineStage` config type.

### 2. Rewrote `reviews/route.ts` with proper types

**Types added locally** (spine-specific raw shapes):
```ts
interface SpineReview { ... }
interface SpineReviewsResponse { items: SpineReview[]; total: number; }
```

**Used existing** `TripReview` from `@/types/governance` for the output.

**Changes**:
- `transformReviewToFrontendFormat(review: SpineReview): TripReview` — explicit input/output types
- `.map()` and `.filter()` callbacks infer types automatically — no manual annotations needed
- Added `STATUS_MAP` record for safe string-to-union mapping with fallback to `"pending"`
- Used nullish coalescing (`??`) consistently instead of `||` for defaults

### 3. Rewrote `stats/route.ts` with proper types

**Types used**:
- `AnalyticsPipelineStage` from `@/lib/api-client`
- `AnalyticsSummary` defined locally for the summary endpoint shape

**Changes**:
- Cast API responses once at parse time: `await response.json() as AnalyticsPipelineStage[]`
- All `.reduce()`, `.find()` callbacks are fully typed — no `: any` anywhere
- Used optional chaining (`?.`) and nullish coalescing (`??`) for safe field access

---

## Verification

| Check | Before | After |
|-------|--------|-------|
| Build | ❌ Type errors (implicit any) | ✅ Zero errors |
| Tests | 245 passed, 1 failed | 306 passed, 1 failed |
| Regressions | — | 0 |
| `any` count in 2 files | 9 instances | 0 instances |

---

## Files Changed

| File | Lines | Change |
|------|-------|--------|
| `frontend/src/lib/api-client.ts` | +11 | Added `AnalyticsPipelineStage` |
| `frontend/src/app/api/reviews/route.ts` | ~80 | Full rewrite with types |
| `frontend/src/app/api/stats/route.ts` | ~83 | Full rewrite with types |

---

## Principle Applied

> **Additive, better, comprehensive.**
>
> Instead of suppressing the compiler with `any`, we added real type definitions. The fix makes the codebase stricter, not looser. Future API changes will be caught at compile time.
