# Payments Open Blockers Revalidation (motto_v2)
Date: 2026-05-18
Mode: Non-coding, read-only verification

## Scope
Re-validate whether previously identified Payments readiness blockers are still open.

## Fresh-state checks run
- `git status --short --branch`
- route/file searches across frontend app routes, nav config, route map, API client, backend server routes
- targeted tests:
  - `npm test -- route-map` (frontend)
  - `uv run pytest tests/test_booking_data.py -q` (backend)

## Current repo state
- Branch: `master...origin/master`
- Working tree is dirty (overview-related frontend files + `motto_v2.md` + one status doc)
- No git-mutating command executed.

## Revalidation results (previous top blockers)

1. `/payments` route missing
- Status: OPEN
- Evidence:
  - `search_files(path='frontend/src/app', pattern='*payments*') -> total_count: 0`
  - nav still includes planned item only: `frontend/src/lib/nav-modules.ts` line with `href: '/payments', enabled: false`

2. Dedicated `/payments` read-model API contract missing
- Status: OPEN
- Evidence:
  - no backend route declarations for `/payments` found in `spine_api` python files
  - only payment write endpoint still present: `PATCH /trips/{trip_id}/booking-data/payment` in `spine_api/server.py`

3. BFF route-map/proxy alignment for booking-data/payment paths
- Status: OPEN (high risk)
- Evidence:
  - API client calls:
    - `/api/trips/{tripId}/booking-data`
    - `/api/trips/{tripId}/booking-data/payment`
  - Catch-all proxy is deny-by-default unless mapped: `frontend/src/app/api/[...path]/route.ts`
  - `frontend/src/lib/route-map.ts` currently contains `collection-link` and `pending-booking-data*`, but no `booking-data` or `booking-data/payment` mapping entries.
  - no explicit Next route files exist for these subpaths under `frontend/src/app/api/trips/**`

4. `payment_required` blocker taxonomy not implemented in runtime
- Status: OPEN
- Evidence:
  - repo-wide `payment_required` search returns docs-only matches; no runtime backend/frontend implementation

5. Conflict granularity remains trip-level CAS, not payment-subresource versioning
- Status: OPEN
- Evidence:
  - persistence still uses `expected_updated_at` against trip `updated_at` in `update_trip_if_version_for_agency` (`spine_api/persistence.py`)
  - no payment-specific version field surfaced in current payment tracking flow

## Additional check outcomes
- Frontend route-map tests pass (`12 passed`) but do not cover missing booking-data/payment path mapping.
- Backend booking-data test suite passes (`47 passed`) confirming current backend behavior but not resolving frontend BFF mapping gap.

## Verdict
All previously identified Payments readiness blockers remain open as of this revalidation pass.
