# COMING SOON READINESS CONTRACT 02 — PAYMENTS

Date: 2026-05-17
Module: Payments
Mode: Plan-only (no product code changes)
Primary references: motto.md, AGENTS.md, module docs below

## 0) How this contract was used

This contract is derived from the shared template and anchored to current runtime/code evidence.
No product code changes are included.

## 1) Scope and evidence baseline

This contract is drafted after re-validating current implementation and docs.

Evidence anchors reviewed in this pass:
- `Docs/review/MODULE_READINESS_CONTRACT_TEMPLATE.md`
- `Docs/review/COMING_SOON_READINESS_CONTRACT_01_BOOKINGS_2026-05-17.md`
- `Docs/status/TRIP_WORKSPACE_OPS_PAYMENT_CORRECTNESS_PLAN_2026-05-15.md`
- `frontend/src/lib/nav-modules.ts`
- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/components/workspace/panels/PaymentTrackingCard.tsx`
- `frontend/src/components/workspace/panels/BookingExecutionPanel.tsx`
- `frontend/src/components/workspace/panels/ConfirmationPanel.tsx`
- `frontend/src/components/workspace/panels/DataIntakeZone.tsx`
- `frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx`
- `frontend/src/lib/api-client.ts`
- `frontend/src/app/api/[...path]/route.ts`
- `frontend/src/lib/route-map.ts`
- `spine_api/server.py`
- `spine_api/persistence.py`
- `spine_api/services/booking_task_service.py`
- `tests/test_booking_data.py`
- `frontend/src/components/workspace/panels/__tests__/PaymentTrackingCard.test.tsx`
- `frontend/src/components/workspace/panels/__tests__/DataIntakeZone.test.tsx`
- `frontend/docs/PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md`

Working-tree context (read-only):
- `git status --short --branch` -> `## master...origin/master` with multiple modified/untracked files (dirty working tree; no mutations performed in this pass).

## 2) Feedback/adjudication (if applicable)

No external adjudication input in this pass.

## 3) Module ownership statement (mandatory)

Payments owns payment tracking/readiness state for trip operations in v1.
Payments references Bookings task blockers, trip stage/readiness context, and confirmation workflow state.
Payments must not directly mutate charging gateways, supplier payout systems, accounting ledgers, or invoice engines.

## 4) Product contract

Payments is the operational tracking surface for collections/refunds risk and due-state visibility, not a processor.

Payments must answer:
- What is the current payment state for each trip (status, agreed/paid/balance, due date, refund state)?
- Which trips are payment-risky now (overdue, due-soon, refund pending)?
- What minimal operator mutation is allowed while preserving canonical write ownership and conflict safety?

Payments is not:
- A payment gateway integration surface (Razorpay/Stripe/etc.) in v1
- A ledger/accounting system of record in v1
- A supplier payout execution engine in v1

## 5) Surface/route contract

Required surface split:
- `/payments` (global): queue/read model for payment risk and prioritization
- `/trips/{tripId}/ops` (contextual): canonical payment detail + mutation surface

Current reality:
- Nav state: disabled (`frontend/src/lib/nav-modules.ts` line 89 `enabled: false`); disabled click shows "coming soon" toast (`frontend/src/components/layouts/Shell.tsx` line 259).
- Route presence: `/payments` page route is missing in `frontend/src` (no `*payments*` route file under `frontend/src/app`).

V1 required routes before enablement:
- Frontend page: `frontend/src/app/(agency)/payments/page.tsx`
- BFF read endpoint: `GET /api/payments` (or equivalent explicit route) for global queue/read-model
- Canonical mutation endpoint remains existing `PATCH /api/trips/{tripId}/booking-data/payment` -> backend `PATCH /trips/{trip_id}/booking-data/payment`

Optional later routes:
- `GET /api/payments/{tripId}` detail read endpoint
- `GET /api/payments/metrics` aggregate reporting endpoint

Critical routing gap discovered now:
- Catch-all proxy is deny-by-default and requires explicit mapping (`frontend/src/app/api/[...path]/route.ts`, `frontend/src/lib/route-map.ts`).
- `api-client.ts` calls `/api/trips/{id}/booking-data` and `/api/trips/{id}/booking-data/payment`, but these routes are not present in `route-map.ts` and no explicit Next API route exists for them under `frontend/src/app/api/trips/...`.
- This is an existing contract-drift risk and must be resolved/verified before `/payments` module rollout.

## 6) Domain/state lifecycle contract

Current canonical lifecycle states (from code):
- Payment status: `unknown`, `not_started`, `deposit_paid`, `partially_paid`, `paid`, `overdue`, `waived`, `refunded`
- Refund status: `not_applicable`, `not_requested`, `pending_review`, `approved`, `processing`, `paid`, `rejected`, `cancelled`

Current canonical transitions:
- Payment: `unknown|not_started -> deposit_paid|partially_paid|paid|overdue|waived|refunded`
- Refund: `not_requested -> pending_review -> approved|rejected -> processing -> paid|cancelled`

Contract decision:
- V1 preserves these lifecycle values unless explicit migration is approved.
- Any richer lifecycle model is Phase-2+ and requires migration/versioning contract.

Canonical blocker/error/reason codes (module-specific) needed for `/payments` queue:
- `final_payment_due_soon`
- `final_payment_overdue`
- `refund_review_pending`
- `refund_processing_stalled`
- `payment_reference_missing`
- `payment_proof_missing`
- `payment_data_conflict`
- `payment_data_invalid`

Validation rules for codes:
- Codes must come from a finite allowlist shared by backend + frontend; no free-text code names.
- `*_missing` codes require the corresponding field null/empty in canonical payment_tracking data.

## 7) API/read-model/write-model contract

Current API reality:
- `GET /trips/{trip_id}/booking-data` (returns booking_data envelope)
- `PATCH /trips/{trip_id}/booking-data` (traveler/payer path; preserves existing payment_tracking)
- `PATCH /trips/{trip_id}/booking-data/payment` (payment-only write path)

Related adjacent APIs:
- Booking tasks: `GET/POST/PATCH /booking-tasks/...` (contains `collect_payment_proof` task type in generator)
- Confirmation APIs under `/trips/{trip_id}/confirmations...`

Module-enablement API gates:
1. Define canonical global payment read/query contract (queue semantics, filtering, sorting).
2. Keep tenant/agency scoping server-derived.
3. Require audit event emission for all state-changing mutations.
4. Define explicit mutation safety/conflict model and UX recovery.
5. Ensure all writes resolve to canonical write owner (`PATCH /trips/{trip_id}/booking-data/payment`).

Read-model vs write-model boundary:
- Read model: global aggregation over canonical trip `booking_data.payment_tracking` + minimal trip metadata.
- Write model owner: `PATCH /trips/{trip_id}/booking-data/payment` in `spine_api/server.py`.
- Rule: `/payments` global surface must not become an independent write source of truth.

Mutation safety/conflict model:
- Strategy: optimistic concurrency using trip-level `updated_at` CAS (`expected_updated_at`) via `TripStore.update_trip_if_version_for_agency`.
- Error semantics: 409 with shape `{ message, expected_updated_at, actual_updated_at }` and payment-specific message (`Payment tracking conflict`).
- Retry/compensation behavior: on 409, UI must reload canonical booking_data then reattempt explicit operator action.

Migration/versioning needs:
- Schema/version gaps today: no payment-specific version counter; conflict granularity is trip-level.
- Required migration contract before large-scale concurrent ops: optional `payment_tracking_version` or equivalent subresource versioning if conflict rates become operationally high.

## 8) Data ownership boundaries

Payments owns:
- `booking_data.payment_tracking` semantic contract and lifecycle interpretation
- payment-risk queue/read-model semantics for `/payments`

Payments references:
- Trip identity/stage/readiness context
- Bookings task dependencies (example: `collect_payment_proof` task type)
- Confirmation/evidence context where needed for operator decisions

Payments must not own:
- Payment gateway transaction execution/settlement state machine
- Accounting ledger/invoice/tax authority records

## 9) UI acceptance contract

Minimum sections/views:
- Global payment queue (risk/prioritized)
- Trip-linked payment detail panel
- Conflict/error/reload recovery states

Minimum row/detail fields:
- Trip id/destination
- payment_status
- agreed_amount / amount_paid / balance_due / currency
- final_payment_due and derived due-risk state
- refund_status + refund_amount_agreed
- payment_reference/proof presence flags

Mandatory actions in v1:
- Open trip ops from queue item
- Edit/update payment tracking through canonical endpoint
- Resolve conflicts via explicit reload + retry flow

Deferred risky actions:
- Charge customer / capture funds
- Trigger supplier payout / settlement release

Stale-data/refetch behavior:
1. After mutation: replace local payment state from server response and refresh from canonical booking_data on conflict/reload.
2. UI must not assume mutation success before server confirmation.
3. On refresh failure: show explicit stale warning + retry action; keep last confirmed state visible.

Empty-state acceptance:
1. Empty payment queue is valid success.
2. Empty state must explain that payments are tracked inside trip ops until queue criteria are met.
3. No seeded/mock runtime data on `/payments` production route.

## 10) Security/privacy/compliance contract

1. Tenant/agency isolation: all reads/writes must be agency-scoped server-side (`get_current_agency` + store methods).
2. Sensitive-field handling: payment metadata only; avoid storing raw card/bank secrets.
3. Detail-vs-list exposure constraints: queue list should expose minimal flags, not full sensitive notes by default.
4. Metadata allowlist/forbidden patterns: audit events remain metadata-only (`payment_tracking_updated` event pattern).
5. Cross-module ownership validation: booking/payment references must resolve within same trip + agency boundary.

## 11) Observability contract

Required events (minimum):
- `payment_tracking_updated`
- `booking_data_updated` (traveler path; must not mutate payment fields)
- payment conflict events (HTTP 409 counters / structured logs)

Required operational metrics:
- count of trips by payment_status
- overdue and due-soon payment counts
- refund pipeline counts by refund_status
- mutation conflict rate for payment endpoint
- mean time from not_started -> paid (derived)

## 12) Test gates (enablement gate)

Must pass before nav/feature enablement:
1. Nav gate test (`/payments` remains disabled until contract gates pass).
2. Route rendering tests for `/payments` (loading/empty/error/hydrated).
3. Tenant isolation tests (queue reads + payment mutations).
4. Lifecycle validity tests for payment/refund status values.
5. Guard tests that non-payment booking update path preserves `payment_tracking`.
6. Cross-surface parity tests (`/payments` view == trip ops payment state).
7. Audit emission tests for payment mutations.
8. Booking dependency linkage tests (`collect_payment_proof` consistency with payment state).
9. Conflict behavior tests for concurrent mutation semantics.

Existing evidence today:
- Backend includes payment preservation/conflict tests in `tests/test_booking_data.py`.
- Frontend includes `PaymentTrackingCard` and `DataIntakeZone` tests.
- Missing explicit `/payments` route tests (route not implemented yet).

## 13) Rollout/rollback gates

Enablement preconditions:
1. `/payments` route exists and is production-safe.
2. Global payment query/read contract defined and verified.
3. Parity with canonical trip payment owner path proven.
4. Security/privacy checks pass.
5. Core test matrix passes.

Immediate rollback triggers:
- Cross-tenant payment visibility bug
- State divergence between `/payments` queue and trip ops payment detail
- Conflict handling failure causing silent overwrite
- Route crashes or persistent 404 on payment surfaces

Rollback action:
- Disable `/payments` nav/entry.
- Retain underlying payment data/APIs.
- Publish gate-failure note + defect list.

## 14) Top risks (ranked)

1. Route-contract drift: booking-data/payment client paths not explicitly mapped in BFF route-map.
2. No dedicated `/payments` read model, causing premature nav enablement pressure.
3. Trip-level CAS lock may cause noisy conflicts under concurrent multi-operator edits.
4. Blocker/reason taxonomy for payment queue not yet canonicalized in runtime.
5. Payment docs include broad processor/compliance ambitions that exceed v1 scope and can cause scope creep.

## 15) Explicit non-goals for Payments v1

1. Build payment gateway integrations (Razorpay/Stripe/etc.).
2. Build customer checkout/payment-link orchestration.
3. Build supplier payout orchestration.
4. Build accounting ledger/invoice/reconciliation engine.
5. Do not enable `/payments` nav until all gates pass.

## 16) Open questions blocking implementation

1. Should `/payments` queue be backed by a new backend endpoint or composed server-side from existing trip reads? (recommended: explicit backend read endpoint)
2. What is the canonical blocker-code mapping from payment states to bookings dependencies (without inventing `payment_required` runtime code prematurely)?
3. Do we need payment-specific subresource versioning now, or defer until measured conflict pain?
4. What exact list fields are allowed on global payment queue to stay privacy-safe yet actionable?
5. Should due-date risk be computed server-side for consistency or remain client-derived in v1?

## 17) Implementation sequencing (required order)

1. Close BFF route contract gaps for booking_data/payment endpoints and verify deny-by-default mapping parity.
2. Define global payment read/query contract (`/payments` queue semantics + filters + sort).
3. Canonicalize payment blocker/error/reason code taxonomy and validation.
4. Add test gates: isolation, lifecycle validity, parity, observability, conflict behavior.
5. Build `/payments` read-only route/surface.
6. Expose limited safe mutations that delegate to canonical payment write owner.
7. Enable nav only after route/test/security/observability gates pass.

## 18) Stop condition

This document is planning-only.
No product code changes are included.
Await approval before implementation or nav/module state changes.
