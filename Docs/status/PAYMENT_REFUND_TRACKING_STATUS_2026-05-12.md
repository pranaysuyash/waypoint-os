# Payment and Refund Tracking Status - 2026-05-12

## Context

This follows the random document audit of `frontend/docs/CUSTOMER_CREDIT_MASTER_INDEX.md`.
The audit found that the customer credit / wallet direction is not implemented and is too large for a safe first work unit.
The selected safe unit is status-only payment and refund tracking on the existing trusted booking-data path.

## Decision

Use the existing trip-scoped booking-data contract instead of creating a new payments route, wallet module, credit ledger, or gateway integration.

The implemented scope is:

- Agent/operator can record payment and refund status metadata on trusted `booking_data`.
- Backend computes `balance_due` from `agreed_amount - amount_paid`.
- Customer public collection cannot submit or promote payment tracking.
- Audit events record metadata only, not raw payment references or proof URLs.
- UI copy labels the section as status-only tracking.

Out of scope:

- Wallets.
- Customer credits.
- Payment collection.
- Refund execution.
- Gateway IDs.
- Ledger accounting.
- New `/payments` routes or modules.

## Files Changed

- `spine_api/server.py`
  - Added `PaymentTrackingModel`.
  - Added `booking_data.payment_tracking`.
  - Recomputed `balance_due` server-side.
  - Added customer-pending promotion guard.
  - Added metadata-only audit flags.
- `spine_api/routers/public_collection.py`
  - Forbids extra public booking-data fields so `payment_tracking` cannot be customer-submitted.
- `frontend/src/lib/api-client.ts`
  - Added `PaymentTracking`, `PaymentStatus`, and `RefundStatus`.
- `frontend/src/app/(agency)/workbench/OpsPanel.tsx`
  - Added status-only payment/refund display and edit controls inside the existing Ops booking details section.
- `tests/test_booking_data.py`
  - Added trusted booking-data payment tracking, computed balance, negative amount, and audit metadata tests.
- `tests/test_booking_collection.py`
  - Added public submission and tampered pending-data boundary tests.
- `frontend/src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx`
  - Added display and save tests for tracking-only payment state.

## Verification

Baseline red tests were intentionally added before implementation:

- Backend red:
  - `payment_tracking` was ignored by `PATCH /trips/{trip_id}/booking-data`.
  - Negative tracking amounts were accepted.
  - Audit lacked payment-tracking metadata.
  - Public customer submission accepted extra `payment_tracking`.
  - Tampered pending booking data could be accepted into trusted booking data.
- Frontend red:
  - OpsPanel had no payment tracking summary or editor controls.

Post-implementation targeted verification:

- `uv run pytest tests/test_booking_data.py tests/test_booking_collection.py -q`
  - Result: `71 passed in 34.11s`.
- `cd frontend && npm test -- --run 'src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx'`
  - Result: `21 passed`.
- `cd frontend && npm run typecheck`
  - Result: passed.
- `cd frontend && npm test -- --run`
  - Result: `112 passed`, `869 passed`.
- `uv run python - <<'PY' ... BookingDataModel(**payload).model_dump() ... PY`
  - Result: server model normalized `currency` to `INR`, recomputed `balance_due` from `1.0` to `70000.0`, and forced `tracking_only` to `true`.
- `uv run pytest -q`
  - Result: `9 failed, 2077 passed, 34 skipped, 1 xfailed`.
  - Failures were outside the payment/refund tracking path:
    - `tests/test_agent_events_api.py::test_get_agent_runtime_returns_registry_and_health`
    - `tests/test_agent_events_api.py::test_run_agent_runtime_once_returns_results`
    - `tests/test_analytics_router_contract.py::test_analytics_router_owns_non_product_b_analytics_paths`
    - `tests/test_followups_router_behavior.py::test_followups_dashboard_agency_filter_and_sort`
    - `tests/test_overview_analytics_hardening.py::test_inbox_stats_handles_non_dict_analytics`
    - `tests/test_partial_intake_lifecycle.py::TestFullData::test_full_data_completes_normally`
    - `tests/test_partial_intake_lifecycle.py::TestBlockedRun::test_blocked_when_no_destination_or_dates`
    - `tests/test_partial_intake_lifecycle.py::TestBlockedRun::test_blocked_run_has_blocked_event`
    - `tests/test_partial_intake_lifecycle.py::TestStaleRunTimeout::test_stale_run_appears_in_list`

Known broader baseline from the audit before this work:

- Frontend full test suite had one pre-existing failure in `ExtractionHistoryPanel.test.tsx`.
- Backend full pytest suite had five pre-existing failures unrelated to booking data.

Current note:

- The frontend baseline improved while parallel work was underway; the full frontend suite now passes.
- The backend suite still has unrelated failures. Four match the audit baseline, one appears to be a newer inbox hardening regression, and four partial-intake lifecycle failures require a live server on `127.0.0.1:8000`.

## Contract Notes

Current trusted shape:

```json
{
  "booking_data": {
    "travelers": [],
    "payer": null,
    "special_requirements": null,
    "booking_notes": null,
    "payment_tracking": {
      "agreed_amount": 120000,
      "currency": "INR",
      "amount_paid": 50000,
      "balance_due": 70000,
      "payment_status": "partially_paid",
      "payment_method": "bank_transfer",
      "payment_reference": "operator-only reference",
      "payment_proof_url": "operator-only URL",
      "refund_status": "not_applicable",
      "refund_amount_agreed": null,
      "refund_method": null,
      "refund_reference": null,
      "refund_paid_by_agency": false,
      "notes": null,
      "tracking_only": true
    }
  }
}
```

`balance_due` and `tracking_only` are server-authoritative.

## Remaining Work

1. Run full frontend and backend suites after the current parallel-agent churn settles and compare against the known audit baseline.
2. Decide whether payment references and proof URLs need encryption beyond the existing `booking_data` encrypted blob.
3. Add a future ledger only when the product decision requires money movement, reconciliation, or accounting-grade audit trails.
4. Keep `/payments` nav disabled until there is a real module with a canonical route and contract.

## Open Questions

1. Should payment references be visible to all agency operators, or should they require a narrower permission?
2. Should refund paid-by-agency be a boolean only, or should it eventually become a structured reimbursement event?
3. Should `agreed_amount` use minor units in the next schema phase if this moves toward ledger-grade accounting?
