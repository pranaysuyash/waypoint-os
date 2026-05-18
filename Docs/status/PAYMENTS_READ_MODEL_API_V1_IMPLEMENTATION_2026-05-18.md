# Payments Read-Model API v1 — Implementation Status
Date: 2026-05-18

## What was built

### Backend — `GET /payments`

File: `spine_api/server.py`

- Endpoint: `GET /payments`
- Auth: tenant-scoped (`Depends(get_current_agency)`)
- Trip listing: `TripStore.list_trip_summaries_for_agency` (uses `_rls_session_for_agency` — RLS-safe in test and background contexts)
- Booking data: `TripStore.get_booking_data_for_agency` per trip
- Delegation: `build_payment_queue_response` in service module
- Response model: `PaymentQueueResponseModel` (Pydantic)
- Filters: `queue_status`, `payment_status`, `refund_status`, `due_bucket` (all Literal-typed → 422 on bad values)
- Pagination: `limit` (1–200), `offset` (≥0)

File: `spine_api/services/payment_queue_service.py`

- `_derive_queue_status` — canonical derivation of `queue_status` from payment/refund status, due date, and balance
- `_build_item` — constructs read-only queue row from trip + booking_data; notes field excluded
- `build_payment_queue_response` — applies filters, paginates, computes summary counts
- `queue_status` values: `not_configured | unknown | due_later | due_soon | overdue | paid_complete | refund_in_progress`

### Tests — `tests/test_payments_queue_api.py`

9 tests, all passing:

- Tenant isolation (trip visible under own agency, not under other agency)
- Queue status derivation for: `not_configured`, `unknown`, `overdue`, `paid_complete`, `refund_in_progress`
- Notes field excluded from response (PII guard)
- Invalid filter/pagination values → 422
- Pagination: correct offset slicing, consistent summary across pages
- Filter combinations: `queue_status + payment_status + refund_status`

### BFF — `frontend/src/lib/route-map.ts`

Added: `["payments", { backendPath: "payments" }]`

Route-map test added: `frontend/src/lib/__tests__/route-map.test.ts`
14 tests pass (was 13).

### Frontend client — `frontend/src/lib/api-client.ts`

Added types:
- `QueueStatus`
- `PaymentQueueItem`
- `PaymentQueueSummary`
- `PaymentQueuePagination`
- `PaymentQueueResponse`
- `PaymentQueueParams`

Added method:
- `getPaymentsQueue(params?: PaymentQueueParams): Promise<PaymentQueueResponse>`

Typecheck: clean (`tsc --noEmit` → 0 errors).

## What is explicitly NOT done

- `/payments` page route not created (`frontend/src/app/(agency)/payments/`)
- Nav not enabled (`nav-modules.ts` → `enabled: false` unchanged)
- No write actions under `/payments`
- `payment_required` blocker taxonomy not wired into runtime
- No cursor-based pagination (offset only for v1)

## Regression results

| Suite | Result |
|---|---|
| `test_payments_queue_api.py` | 9/9 passed |
| `test_booking_collection.py` | 67/67 passed |
| `test_booking_data.py` | 47/47 passed |
| `route-map.test.ts` | 14/14 passed |
| `tsc --noEmit` | 0 errors |

## Architecture decisions preserved

- `booking_data.payment_tracking` remains the sole payment write source of truth
- `GET /payments` is a read-only aggregation view over trip booking data
- No second payment write source was introduced
- Nav stays disabled pending full readiness gate from `COMING_SOON_READINESS_CONTRACT_02_PAYMENTS_2026-05-17.md`
