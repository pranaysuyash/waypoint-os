# Disruption Preview Fail-Closed Slice — 2026-09-04

**Finding:** simulator/provider truth audit S1 — `disruption_radar` fabricated
cancellations and rebooking success, mutated trip state, and emitted a
`disruption_rebooked` audit event without supplier evidence.

## Before

`spine_api/routers/disruption_radar.py` generated a default cancellation when
no disruption feed existed, generated local alternatives, then accepted a
one-click rebook request by mutating `trip.packet.flight_number`, setting
`disruption_resolved`, marking the disruption `REBOOKED`, persisting the trip,
and returning `ok=True`/`rebooked_at`.

## Implemented correction

- The module and endpoint documentation now identify the surface as a
  deterministic preview with no connected provider.
- Alert and option payloads expose `reality_tier=deterministic_preview`,
  `provider_connected=false`, and `effects=[]`.
- Preview options include standard `TierMetadata` describing the missing
  provider, freshness, fare, booking-reference, and idempotency evidence.
- The execute endpoint calls the canonical `assert_tier_capability` guard for
  `can_mutate_booking_state` before any mutation. The deterministic-preview
  tier fails closed with HTTP 403.
- No trip save, operational status change, or success audit event occurs on
  the no-provider path.
- The strategic lifecycle regression now asserts 403 and byte-for-byte trip
  state preservation.

## Verification

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_strategic_phases_6_to_9.py
1 passed
```

```text
.venv/bin/ruff check spine_api/routers/disruption_radar.py \
  tests/test_strategic_phases_6_to_9.py
All checks passed!
```

The route remains agency-scoped through `TripStore.get_trip_for_agency`.
This slice proves local fail-closed behavior only; it does not implement a
real flight/booking provider, external reference reconciliation, hosted
idempotency, or emergency-operation approval.

## Next provider-gated step

A future connected-provider implementation must supply provider evidence,
fresh availability/fare data, an external booking reference, an idempotency
key, reconciliation status, and an authenticated human/agent authorization
record before it may select a tier capable of mutating booking state.
