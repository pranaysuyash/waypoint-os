# Payments v1 Ownership + Read-Model Decision Note

Date: 2026-05-18
Mode: Non-coding decision note (no product code changes)
Scope source:
- Docs/review/PAYMENTS_PARALLEL_AGENT_EXECUTION_GUIDE_2026-05-18.md
- Docs/review/PAYMENTS_OPEN_ITEMS_WRITEUP_2026-05-18.md
- Docs/review/COMING_SOON_READINESS_CONTRACT_02_PAYMENTS_2026-05-17.md
- Current runtime/code references cited below

## Evidence revalidated in this pass

1) Canonical payment model + write path exists under trip booking data
- `spine_api/server.py`
  - `PaymentTrackingModel` enum values and validators
  - `BookingDataModel.payment_tracking`
  - `PATCH /trips/{trip_id}/booking-data/payment` (payment-only write owner)
  - `PATCH /trips/{trip_id}/booking-data` explicitly preserves existing `payment_tracking`

2) Frontend uses those trip-scoped paths
- `frontend/src/lib/api-client.ts`
  - `getBookingData(tripId)` -> `/api/trips/{tripId}/booking-data`
  - `updatePaymentTracking(tripId, ...)` -> `/api/trips/{tripId}/booking-data/payment`

3) BFF mapping for booking-data payment paths is currently present
- `frontend/src/lib/route-map.ts`
  - `trips/{id}/booking-data`
  - `trips/{id}/booking-data/payment`

4) Payments module is still intentionally disabled
- `frontend/src/lib/nav-modules.ts`
  - `/payments` has `enabled: false`
- No `/payments` route files under `frontend/src/app` (no `*payments*` route file)

5) Runtime booking task blocker taxonomy does not include `payment_required`
- `spine_api/models/tenant.py`
  - `BLOCKER_CODES` does not contain `payment_required`
- `spine_api/services/booking_task_service.py`
  - `collect_payment_proof` exists, currently generated without a payment-specific blocker code

---

## Decisions

### 1) Is `booking_data.payment_tracking` the durable v1 payment source of truth?
Decision: Yes.

Reason:
- It is already the implemented canonical write owner in backend runtime (`PATCH /trips/{trip_id}/booking-data/payment`).
- Traveler booking-data writes preserve it rather than overwrite it.
- Existing frontend ops panel already uses this model and endpoint.

v1 boundary:
- Do not introduce a second writable payment truth for `/payments`.

### 2) Should `/payments` v1 be queue/read-model only?
Decision: Yes.

Reason:
- Current architecture is trip-scoped write ownership with CAS semantics.
- Safest incremental step is global read/triage surface that drills into trip ops for mutation.
- Avoids parallel write sources and state divergence.

v1 rule:
- `/payments` reads/aggregates only.
- Writes continue through `PATCH /trips/{trip_id}/booking-data/payment`.

### 3) Minimal `/payments` read-model API contract
Decision: Add a single read endpoint first.

Proposed endpoint:
- `GET /payments`

Query params (minimal):
- `cursor` (optional)
- `limit` (optional)
- `queue_status` (optional, allowlist)
- `payment_status` (optional, allowlist)
- `refund_status` (optional, allowlist)
- `due_bucket` (optional: `overdue|due_0_3|due_4_7|due_8_14|none`)

Response shape (minimal):
- `items: PaymentQueueItem[]`
- `summary: PaymentQueueSummary`
- `next_cursor: string | null`

`PaymentQueueItem` (minimal actionable fields):
- `trip_id: string`
- `destination_label: string | null`
- `stage: string`
- `updated_at: string | null`
- `payment_tracking_present: boolean`
- `payment_status: PaymentStatus | null`
- `refund_status: RefundStatus | null`
- `agreed_amount: number | null`
- `amount_paid: number | null`
- `balance_due: number | null`
- `currency: string | null`
- `final_payment_due: string | null`
- `queue_status: QueueStatus` (derived)
- `has_payment_reference: boolean`
- `has_payment_proof_url: boolean`

`PaymentQueueSummary` (minimal):
- `total`
- `by_queue_status`
- `overdue_count`
- `due_7d_count`
- `not_configured_count`

Guardrails:
- Tenant scoping server-side only.
- No PII-heavy notes in list rows.
- No write actions in this endpoint.

### 4) Canonical queue statuses
Decision: Keep payment lifecycle enums as-is; add a small derived queue status layer.

Canonical v1 `queue_status`:
- `not_configured`
- `unknown`
- `due_later`
- `due_soon`
- `overdue`
- `paid_complete`
- `refund_in_progress`

Derivation policy:
- `not_configured`: `payment_tracking` absent.
- `unknown`: tracking present but payment status unknown/insufficient.
- `overdue`: explicit overdue, or due date past with positive balance.
- `due_soon`: due date 0–7 days with positive balance.
- `due_later`: due date >7 days (or no due date) with unpaid balance.
- `paid_complete`: paid/waived/refunded with no payable balance.
- `refund_in_progress`: refund status in `pending_review|approved|processing`.

Note:
- This is queue triage status, not replacement of `payment_status`/`refund_status` enums.

### 5) Missing legacy payment data representation
Decision: `not_configured`.

Reason:
- Missing `payment_tracking` object means no explicit tracking record exists.
- `unknown` should represent configured-but-uncertain state.
- `not_required` should only be used when explicitly derivable from business state, not inferred from absence.

### 6) `payment_required` semantic placement
Decision: Shared workflow blocker, with Payments ownership and Bookings consumption.

Clarification:
- Payments domain owns evaluation semantics.
- Bookings/ops workflows may consume it as a blocker signal.
- Do not add runtime `payment_required` enum/code until an actual consuming workflow requires it.

### 7) Likely files touched in later implementation (when coding starts)
Backend/API:
- `spine_api/server.py` (or extracted payments router) for `GET /payments`
- `spine_api/persistence.py` (query/read-model composition helpers)
- Optional: `spine_api/services/*` if read-model derivation is isolated into service layer

Frontend BFF + client:
- `frontend/src/lib/route-map.ts` (map `/payments` API path)
- `frontend/src/app/api/[...path]/route.ts` (no policy broadening; only mapped route usage)
- `frontend/src/lib/api-client.ts` (typed `getPaymentsQueue` client)

Frontend UI:
- `frontend/src/app/(agency)/payments/page.tsx`
- Supporting components under `frontend/src/components/...` for queue list/filter states
- `frontend/src/lib/nav-modules.ts` (enablement only after all gates pass)

Docs/contracts:
- `Docs/review/COMING_SOON_READINESS_CONTRACT_02_PAYMENTS_2026-05-17.md` (status update)
- `Docs/review/PAYMENTS_OPEN_ITEMS_WRITEUP_2026-05-18.md` (close/open gate tracking)

### 8) Tests required before nav enablement
Must pass before enabling `/payments` nav:

Backend:
1. `GET /payments` tenant isolation and auth tests.
2. Read-model derivation tests for each `queue_status`.
3. Legacy/missing-data mapping test (`payment_tracking` absent -> `not_configured`).
4. Filter/sort/pagination contract tests.
5. Parity tests: queue row values match canonical trip `booking_data.payment_tracking`.

Frontend:
6. `/payments` route render tests: loading/empty/error/hydrated.
7. API client typing/contract tests for read-model response.
8. Queue filtering behavior tests.
9. Drill-in navigation test from queue row -> trip ops.

BFF/proxy:
10. Route-map resolution tests for new `/payments` read endpoint.
11. Deny-by-default preservation tests for unknown API paths.

Regression safety (existing):
12. Keep passing booking-data payment ownership tests (`tests/test_booking_data.py`).
13. Keep passing route-map tests including booking-data/payment paths.

---

## Final v1 stance

- Payment truth for v1 remains `booking_data.payment_tracking`.
- `/payments` v1 should be queue/read-model only.
- No separate payment write source should be introduced.
- Missing legacy payment data should be surfaced as `not_configured`.
- `payment_required` should be treated as a shared blocker concept only when runtime consumers exist.

No code implementation in this pass.
No nav enablement in this pass.
No changes to unrelated overview test or screenshot in this pass.
