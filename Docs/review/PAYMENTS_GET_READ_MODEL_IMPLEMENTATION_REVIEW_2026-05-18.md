# Payments v1 Read-Model Implementation Review

Date: 2026-05-18
Scope: Backend only (`GET /payments`) + backend tests

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

## 1) Scope and Constraints Compliance

Implemented:
- `GET /payments` read-model endpoint (tenant-scoped via existing agency auth dependency).
- Read-model derivation/filter/summary service.
- Backend tests for required scenarios.

Not implemented (as required):
- No `/payments` frontend page.
- No Payments nav enablement.
- No payment write endpoint additions.
- No ownership change for payment writes (`booking_data.payment_tracking` remains source of truth).
- No proxy policy broadening.

## 2) Technical Changes

### Files changed

1. `spine_api/services/payment_queue_service.py` (new)
- Added queue derivation/filter/summary logic.
- Key anchors:
  - `PAYMENT_QUEUE_STATUSES` at line 6
  - `_derive_queue_status` at line 92
  - `build_payment_queue_response` at line 186
- Behavior:
  - Derives queue states from `booking_data.payment_tracking`.
  - Applies filters first, computes summary on filtered set, then paginates.
  - Excludes raw notes/PII-heavy fields from list rows.

2. `spine_api/server.py`
- Added service import at line 167.
- Added response models + endpoint:
  - `PaymentQueueItemModel` at line 1882
  - `@app.get("/payments")` at line 1953
- Endpoint stays thin:
  - Reads trip summaries
  - Reads booking_data per trip
  - Delegates derivation/filter/summary/pagination to service
- Uses `TripStore.list_trip_summaries_for_agency(...)` at line 1989 for explicit agency-scoped read.

3. `spine_api/persistence.py`
- Added SQL helper with explicit agency RLS context:
  - `SQLTripStore.list_trip_summaries_for_agency(...)` at line 817
- Added facade helper:
  - `TripStore.list_trip_summaries_for_agency(...)` at line 1356
- Purpose:
  - Prevent empty-list behavior from context-var-only RLS sessions in sync/test surfaces.
  - Narrow fix, not broad trip-store refactor.

4. `tests/test_payments_queue_api.py` (new)
- Test class at line 116.
- Coverage includes:
  - tenant isolation (`test_tenant_isolation`, line 117)
  - missing/partial/overdue/paid_complete/refund_in_progress derivation (`line 151`)
  - invalid filters and pagination validation (`line 227`)
  - pagination-after-filtering and summary-from-filtered-set (`line 231`)

### Schema/API contract

New endpoint:
- `GET /payments`
- Query params:
  - `limit` (1..200)
  - `offset` (>=0)
  - enums: `queue_status`, `payment_status`, `refund_status`, `due_bucket`
- Response shape:
  - `summary`
  - `pagination`
  - `items[]`

Ownership unchanged:
- Payment source of truth remains `booking_data.payment_tracking`.

## 3) Test Results

Executed commands:
1. `uv run pytest tests/test_payments_queue_api.py -q`
- Result: `9 passed`

2. `uv run pytest tests/test_booking_data.py -q`
- Result: `47 passed`

## 4) Review Findings (Implementation Cycles)

Cycle 1 findings fixed:
- Initial list projection used generic summary listing path that depends on ambient RLS context and produced empty results in this execution path.
- Fix: introduced explicit agency-scoped summary listing helper in persistence and used it in `/payments` endpoint.

Cycle 2 findings fixed:
- Test isolation assumptions around agency IDs conflicted with FK constraints.
- Fix: tests resolve real agency IDs from DB and only use existing agencies for overrides.

Final verdict:
- Backend `/payments` read-model implementation is ready within requested scope.

## 5) Launch Readiness (for this backend slice)

- Code ready: ✅ Yes
- Feature slice ready (backend-only `/payments` read-model): ✅ Yes
- Launch ready for full Payments module (UI/nav/write workflow): 🟡 Partial by design (not in scope)

## 6) Workspace Drift Note (not part of this change)

Current git status also includes unrelated frontend changes/untracked artifacts outside this task scope:
- `frontend/src/app/(agency)/overview/PageClient.tsx`
- `frontend/src/app/(agency)/overview/useOverviewSummary.ts`
- `overview-runtime-check-unauth-session-gate.png`

Those were not modified for this backend `/payments` implementation.
