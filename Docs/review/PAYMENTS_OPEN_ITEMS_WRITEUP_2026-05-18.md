# Payments Open Items Writeup
Date: 2026-05-18
Mode: Non-coding, read-only revalidation (motto_v2)

## Executive summary
Payments is still a planned module, not an enabled canonical module.
Core payment-tracking mechanics exist inside the Trips booking-data surface, but module-level route, API, ownership, and blocker taxonomy contracts are still incomplete.

Bottom line:
- The implementation has enough internal primitives to support tracking updates.
- It does not yet have safe module-level contracts to expose/enable `/payments`.

## What is open

### 1) No `/payments` page route exists
Status: OPEN

Evidence:
- `frontend/src/app` search for `*payments*` returns no route files.
- Nav still marks Payments as planned/disabled:
  - `frontend/src/lib/nav-modules.ts` has `{ href: '/payments', ..., enabled: false }`.
- Disabled modules render as coming-soon in shell:
  - `frontend/src/components/layouts/Shell.tsx` disabled click toast.

Why this is important:
- You cannot claim a module exists if its canonical route does not exist.
- Enabling nav before route+contract readiness creates a broken IA path and immediate trust loss.

---

### 2) No dedicated `/payments` read-model API contract
Status: OPEN

Evidence:
- Backend has payment write endpoint under trips booking-data:
  - `PATCH /trips/{trip_id}/booking-data/payment` (`spine_api/server.py`).
- No backend route declarations for top-level `/payments` endpoints were found.

Why this is important:
- A top-level module needs top-level read contracts (queue/list/filter/detail) or a clearly documented alternate ownership model.
- Without this, there is no single stable API for payments module UX, filtering, pagination, and operational reporting.

---

### 3) BFF route-map/proxy alignment gap for booking-data payment paths
Status: OPEN (highest immediate runtime risk)

Evidence:
- Client calls:
  - `/api/trips/{tripId}/booking-data`
  - `/api/trips/{tripId}/booking-data/payment`
  in `frontend/src/lib/api-client.ts`.
- Catch-all BFF route is deny-by-default unless explicit mapping exists:
  - `frontend/src/app/api/[...path]/route.ts`.
- `frontend/src/lib/route-map.ts` currently includes:
  - `collection-link`
  - `pending-booking-data*`
  but no `booking-data` or `booking-data/payment` entries.
- No explicit Next API route files exist for booking-data subpaths under `frontend/src/app/api/trips/**`.

Why this is important:
- This is a contract drift risk between client and BFF routing policy.
- If these paths are unresolved by explicit routing/mapping, requests can fail at the gateway layer regardless of backend support.
- This is the most likely near-term break point for payments-related UI behavior.

---

### 4) `payment_required` taxonomy is not runtime-implemented
Status: OPEN

Evidence:
- Repo-wide `payment_required` appears in docs/review writeups, not runtime code paths.

Why this is important:
- Bookings dependency semantics can become ambiguous or inconsistent if taxonomy exists only in docs.
- Operators and automation need a canonical blocker code map in runtime, not implied prose.

---

### 5) Concurrency is trip-level CAS, not payment-subresource versioning
Status: OPEN

Evidence:
- Persistence uses `expected_updated_at` against trip `updated_at` in trip store update path (`spine_api/persistence.py`).
- No payment-specific version token is surfaced for payment-only optimistic concurrency.

Why this is important:
- At low volume, trip-level CAS is workable.
- As payment update frequency and concurrent edits increase, false conflicts and wider write contention become more likely.
- This is not a launch blocker by itself, but it is a scalability/operability consideration.

## What is implemented and usable today
- Embedded payment-tracking source-of-truth exists under `booking_data.payment_tracking`.
- Backend payment update endpoint exists and is test-covered within booking-data test suite.
- Frontend PaymentTrackingCard/DataIntakeZone integration exists.

This means there is real progress, but module readiness is still incomplete.

## Why these items are still open (root causes)
1. Planned-module-first IA exists, but module ownership contracts are still maturing incrementally.
2. Payment capability was introduced as an embedded trip workflow first (good for incremental delivery), without fully finishing top-level module packaging.
3. BFF deny-by-default routing policy is stricter than client surface growth, which is good for safety but exposes mapping drift quickly.
4. Documentation and contracts evolved faster than runtime taxonomy implementation for blocker semantics.

## Business and operational impact if left unresolved
- Module trust risk: users click/expect payments module, but no canonical route/API.
- Operator ambiguity: no canonical queue semantics means inconsistent handling of due/overdue states.
- Incident risk: BFF mapping drift can produce hard-to-explain frontend failures despite backend endpoint existence.
- Future migration cost: taxonomy and ownership drift grows if not normalized before enabling module.

## Readiness gate recommendation (non-coding decision order)
1. Confirm canonical module ownership model for Payments:
   - top-level `/payments` read-model vs explicit "embedded-only" v1 stance.
2. Confirm BFF contract policy for booking-data payment paths:
   - explicit route entries or explicit route files, then lock with tests.
3. Approve runtime blocker taxonomy scope:
   - whether/when `payment_required` becomes canonical runtime code.
4. Decide whether trip-level CAS is acceptable for v1 rollout volume, with a threshold trigger for subresource versioning.
5. Only then discuss nav enablement sequencing.

## Extra discussion points worth deciding now
- Should `/payments` v1 be queue-only (read model + drill-in) while write operations remain in trip context?
- Should Bookings reference payment dependency only as a read-only blocker view, never as payment truth owner?
- What are explicit non-goals for v1 to prevent scope creep (processor, payouts, ledger, invoicing engine)?
- What observability events/alerts are mandatory before user-facing launch?

## Verification evidence used in this writeup
- `git status --short --branch`
- Route and API searches across:
  - `frontend/src/app`
  - `frontend/src/lib/nav-modules.ts`
  - `frontend/src/lib/route-map.ts`
  - `frontend/src/lib/api-client.ts`
  - `frontend/src/app/api/[...path]/route.ts`
  - `spine_api/server.py`
  - `spine_api/persistence.py`
- Tests:
  - `npm test -- route-map` -> pass
  - `uv run pytest tests/test_booking_data.py -q` -> pass

## Final verdict
Open items are still genuinely open.
The current system is partially implemented and directionally correct, but not yet in a safe state to treat Payments as a fully enabled module.
