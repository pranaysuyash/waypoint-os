# Phase 4A Closure Report

**Date:** 2026-05-05
**Phase:** 4A — Secure Customer Booking-Data Collection Link
**Status:** CLOSED

## Audit Results

### Backend (41 tests, 41 pass)
- Encryption: pending_booking_data blob-encrypted, round-trips, excluded from _to_dict
- Token service: SHA-256 hash stored, plain token returned once, single-use, revocable
- Agent CRUD: generate, get status, revoke, regenerate (revokes old)
- Customer submission: writes to pending (not booking_data), validates via BookingDataModel, duplicate returns 409
- Agent review: accept copies to booking_data + sets source + recomputes readiness, reject clears pending
- Privacy: pending not in generic GET, not in _to_dict, booking_ready unaffected by pending
- Audit: hard-fail PII check (6 sentinels, no OR), reason_present instead of raw reason
- Stage gate: public GET/POST blocked after stage change, accept blocked at discovery, reject at any stage
- Fact slot leak: dict-shaped facts with metadata expose only primitive values in public summary

### Frontend (667 tests, 667 pass)
- OpsPanel: link generator, active link hint, pending review, accept/reject, source badges
- Customer form: loading, invalid, already_submitted, active form, success, error states
- No TypeScript errors across entire project

### Pre-existing Issues Fixed During Closure
1. **vitest.config.ts**: Added `.claude` to exclude list — git worktrees under `.claude/worktrees/` were polluting test discovery
2. **vitest.config.ts**: Increased `testTimeout` from 15000 to 30000 — heavy tests (marketing pages, ~9s in isolation) timeout under concurrent suite load
3. **EmptyStateOnboarding.test.tsx**: Added missing `import { describe, expect, it } from 'vitest'`
4. **overview/page.test.tsx**: Fixed "true empty-account state" test — was asserting "No trips in planning yet" but component renders `EmptyStateOnboarding` when both `leadInboxTotal: 0` and `planningTripsTotal: 0`
5. **TripCard.tsx**: Added `data-testid="trip-card-view-link"` to View link in QuickActions — test was asserting this testid but component didn't have it
6. **inbox/page.tsx**: Fixed `BulkActionsToolbar onAssign` prop — was using `handleCardAssign(tripId, agentId)` which has wrong signature; corrected to `handleBulkAssign(agentId)`
7. **Toolchain issue documented**: `npx vitest` resolves to global cache binary that can't find local `jsdom`; must use `npm test -- --run` or `./node_modules/.bin/vitest`

### Database
- Migration `add_booking_collection` applied at head `f1a2b3c4d5e6`
- `booking_collection_tokens` table with RLS, indexes on token_hash and trip_id
- `pending_booking_data` JSON column (encrypted) and `booking_data_source` VARCHAR(30) on trips
- Migration is idempotent (guarded table/column creation)

## Architectural Decisions

| Decision | Choice | Rationale |
|:---------|:-------|:----------|
| Pending data compartment | Separate encrypted column | Review gate enforced by data model, not readiness engine |
| Token storage | SHA-256 hash, plain token returned once | Standard password-reset pattern; can't reconstruct from hash |
| Audit reason | `reason_present: bool` not raw text | Free-text reasons can contain PII; metadata-only audit |
| Public summary | `_safe_fact_value()` extracts primitives | Fact slots may carry metadata (confidence, source, authority_level) |
| Stage gate re-check | Public endpoints re-check trip.stage after token validation | Prevents access if trip moved to discovery after link generated |
| Collection link contract | GET returns status (no URL), POST always generates new | Plain token cannot be reconstructed from hash |
| Body vs query param | `GenerateCollectionLinkRequest` body model | Aligns with frontend `api.post(..., { expires_in_hours })` |

## Files Changed

| File | Change |
|:-----|:-------|
| `alembic/versions/add_booking_collection.py` | New — table + columns migration |
| `spine_api/models/tenant.py` | `BookingCollectionToken` model |
| `spine_api/models/trips.py` | `pending_booking_data`, `booking_data_source` columns |
| `spine_api/persistence.py` | `_PRIVATE_BLOB_FIELDS`, `get_pending_booking_data()`, `_to_dict()` exclusion |
| `spine_api/services/collection_service.py` | New — token lifecycle |
| `spine_api/server.py` | 6 agent + 2 public endpoints, `_safe_fact_value()`, `GenerateCollectionLinkRequest` |
| `frontend/src/lib/api-client.ts` | Agent + public API functions, env guard |
| `frontend/src/app/(public)/layout.tsx` | Minimal public layout |
| `frontend/src/app/(public)/booking-collection/[token]/page.tsx` | Customer form |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | Link generator + pending review + source badge |
| `frontend/vitest.config.ts` | Added `.claude` to exclude, increased timeout to 30s |
| `frontend/src/components/inbox/TripCard.tsx` | Added `data-testid="trip-card-view-link"` |
| `frontend/src/app/(agency)/inbox/page.tsx` | Fixed `onAssign` prop to use `handleBulkAssign` |
| `tests/test_booking_collection.py` | 41 backend tests |
| `frontend/src/components/overview/__tests__/EmptyStateOnboarding.test.tsx` | Added vitest import |
| `frontend/src/app/(agency)/overview/__tests__/page.test.tsx` | Fixed empty-account state test |

## Known Future Work (Not Phase 4A Debt)

- `submission_ip_hash` column for token usage audit (architecturally correct but deferred)
- Customer email notifications on submission
- Multi-language form support
- Document upload (Phase 4B)

## Verification Commands

```bash
# Backend
cd /Users/pranay/Projects/travel_agency_agent
rm -rf data/audit/events.jsonl.lockdir
uv run pytest tests/test_booking_collection.py -v

# Frontend (use local binary, NOT npx)
cd frontend
npm test -- --run

# TypeScript
npx tsc --noEmit

# Migration
uv run alembic current
```
