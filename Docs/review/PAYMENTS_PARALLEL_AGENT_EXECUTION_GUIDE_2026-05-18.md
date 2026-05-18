# Payments Parallel Agent Execution Guide
Date: 2026-05-18
Scope: Non-coding guidance + safest implementation sequencing
Owner context: /Users/pranay/Projects/travel_agency_agent

## 0) Decision
Do not enable Payments as a canonical module yet.

Reason:
Payments has embedded operational mechanics (`booking_data.payment_tracking` + payment patch endpoint), but module-level contracts are incomplete:
- canonical `/payments` route missing
- dedicated `/payments` read-model API missing
- BFF route-map alignment risk for existing booking-data/payment client paths
- blocker taxonomy still docs-heavy (`payment_required` runtime gap)
- concurrency remains trip-level CAS

## 1) First task for the parallel agent (highest-risk first)
Fix or verify BFF route-map alignment for existing booking-data/payment calls before any `/payments` page work.

Why first:
This is the highest near-term runtime breakage risk for already-existing payment tracking UI.

Expected proof:
- Client paths resolve through BFF safely:
  - `/api/trips/{tripId}/booking-data`
  - `/api/trips/{tripId}/booking-data/payment`
- Either explicit route-map entries exist OR explicit Next API route files exist.
- deny-by-default policy remains intact.
- tests updated and passing.

## 2) Guardrails (must follow)
- Read `motto_v2.md`, `AGENTS.md`, and repo instruction files before coding.
- Use read-only git unless explicit permission for mutation.
- Assume parallel agents are active.
- Revalidate current state before each patch group.
- No nav enablement for `/payments` in this phase.
- No broad proxy passthrough/fallback route policy changes.

## 3) Priority order

### Priority 0: Preservation + revalidation
- classify current local state, do not discard anything.
- verify previous report facts against current code before edits.

### Priority 1: BFF route-map/proxy alignment
Likely touch:
- `frontend/src/lib/route-map.ts`
- route-map tests
- only minimal proxy handling changes if required

Do not touch:
- `/payments` page/nav
- backend payment model design
- unrelated shell/nav components

### Priority 2: Ownership decision (before building `/payments`)
Adopt explicit v1 model:
- `/payments` is queue/read model only
- payment truth stays in trip `booking_data.payment_tracking`
- writes remain trip-context via existing booking-data payment endpoint
- Bookings consumes payment dependency state read-only

### Priority 3: Dedicated `/payments` read model
After ownership is approved:
- add top-level read endpoint (queue/list/filter/detail semantics)
- no writes in `/payments` v1 unless explicitly approved

### Priority 4: Runtime blocker taxonomy
If blockers are used in workflow/UI automation, move from docs-only to runtime enum/contract.
- avoid duplicated literals across FE/BE.
- keep Bookings as consumer, not payment truth owner.

### Priority 5: Concurrency evolution
Keep trip-level CAS for v1 unless conflict/volume evidence forces payment-subresource versioning.
Define trigger threshold for introducing `payment_tracking`-scoped version token.

## 4) Non-goals for this phase
- payment processor/gateway integration
- payouts
- general ledger/accounting engine
- invoicing engine
- reconciliation system
- refunds/chargebacks platform
- multi-currency settlement engine

## 5) Suggested execution sequence
A) Revalidation note (if facts changed)
- update/create `Docs/review/PAYMENTS_OPEN_ITEMS_REVALIDATION_YYYY-MM-DD.md`

B) Patch group 1
- BFF booking-data/payment path alignment + tests

C) Patch group 2 (optional, only if already consumed)
- runtime blocker taxonomy normalization + tests

D) Patch group 3 (later)
- `/payments` read model + page (queue/read-only), then rollout gates

## 6) Readiness gates before enabling Payments nav
All must pass:
1. `/payments` direct route loads
2. read-model API contract exists and tested
3. BFF mapping includes all required paths
4. deny-by-default policy preserved
5. legacy/missing payment data handled safely
6. unauthorized access prevented
7. blocker taxonomy runtime-backed
8. frontend typecheck/build pass
9. backend targeted tests pass

## 7) Required validation commands (as applicable)
- `npm test -- route-map`
- `npm run typecheck`
- `npm run build` (if app routes/pages touched)
- `uv run pytest tests/test_booking_data.py -q`
- targeted API/auth tests for new `/payments` read model

## 8) Questions to settle before `/payments` implementation
1. Is `booking_data.payment_tracking` the durable v1 source of truth?
2. Is `/payments` strictly queue/read model in v1?
3. Which queue statuses are canonical?
4. Is `payment_required` booking-only, payment-only, or shared workflow blocker?
5. What is direct URL behavior for `/payments` while nav remains disabled?
6. How should missing legacy payment data be represented (`not_configured`, `not_required`, `unknown`)?

## 9) Final stance for parallel execution
- Do not start with a `/payments` page.
- Start with BFF route-map gap closure for existing payment tracking paths.
- Keep payment writes trip-context for v1.
- Build `/payments` as operational queue/read model only after ownership + contract gates are explicit.