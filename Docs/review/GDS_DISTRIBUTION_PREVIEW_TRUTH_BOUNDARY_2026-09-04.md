# GDS and Distribution Preview Truth Boundary — 2026-09-04

## Finding

The Amadeus/Sabre sandbox adapters and NDC engine are deterministic local
implementations. The route layer previously returned generic `success` values,
synthetic PNR/e-ticket identifiers, `TICKETED_CONFIRMED`, `CONFIRMED`, and
charged amounts. Those values were shaped like supplier-backed outcomes even
though no network call, provider credential, order submission, payment, or
reconciliation occurred.

## Implemented local boundary

`spine_api/routers/gds_sandbox.py` and
`spine_api/routers/distribution.py` now use the canonical
`RealityTier.DETERMINISTIC_PREVIEW` envelope:

- `status` is `PREVIEW_ONLY` for searches, parsing, request construction, and
  order-shaped operations; fare calculations use `COMPUTED_PREVIEW`.
- `reality.reality_tier` is `deterministic_preview`.
- `reality.provider_connected` is `false`.
- `reality.external_reference` is `null`.
- `reality.effects` is `[]`.
- `reality.missing_for_upgrade` names credentials, authenticated provider
  session, confirmation, idempotency, reconciliation, and audit requirements.

Booking/order-shaped responses retain compatible payload fields but clear
synthetic operational artifacts:

- GDS `booking_reference` → `null`;
- GDS `pnr_locator` → `null`;
- GDS `e_ticket_number` → `null`;
- GDS `total_charged_usd` → `null`;
- NDC `order_id` → `null`;
- NDC `pnr_reference` → `null`;
- provider confirmation → `null`;
- status → `PREVIEW_ONLY`.

The local engines remain useful for parsing, schema/protocol construction, and
UI demonstrations. They no longer provide evidence that a booking was made,
ticketed, charged, confirmed, or reconciled.

## Verification

```text
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_gds_distribution_truth_boundary.py \
  tests/test_gds_sandbox_adapters.py \
  tests/test_distribution_engine.py

11 passed in 1.65s
```

The workbench GDS/distribution panels were also updated to remove the
fallback PNR/e-ticket/charge fabrication and to label NDC output as an
illustrative preview. The focused workbench regression remains **15 passed**;
frontend lint and typecheck are clean.

```text
.venv/bin/ruff check \
  spine_api/routers/gds_sandbox.py \
  spine_api/routers/distribution.py \
  tests/test_gds_distribution_truth_boundary.py

All checks passed!
```

The regression suite proves that search, NDC request construction, fare
evaluation, and order-shaped responses carry the preview envelope and cannot
expose synthetic provider confirmation, PNR, e-ticket, or charged-amount
claims.

## Remaining provider boundary

Real Amadeus/Sabre/NDC work is intentionally not implemented in this local
slice. It requires an owner-approved provider contract covering:

- OAuth/token lifecycle and sandbox/live separation;
- offer freshness, price expiration, and availability semantics;
- PNR/order/ticket lifecycle and cancellation/change behavior;
- payment and financial authorization boundaries;
- webhook replay/idempotency and reconciliation;
- rate limits, cost ceilings, timeout, retry, and unknown-outcome behavior;
- agency/tenant ownership and audit references;
- customer-visible copy and legal/provider terms.

Until those gates are evidenced, the routes must remain preview-only or be
disabled for operational mutation. Local route tests, fixtures, and protocol
payloads are not provider, hosted, payment, or production evidence.
