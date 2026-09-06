# Duty-of-Care Cockpit Preview Truth Boundary — 2026-09-04

## Finding

The local duty-of-care engine is deterministic fixture logic. It constructs a
Tokyo incident, sample beacon statuses, a STEP-shaped manifest, a dispatch
fixture, and an SOS-shaped message. The route previously returned generic
`success` and exposed operational vocabulary such as active threat, registered
STEP travelers, active armored dispatches, and broadcast payloads without live
feed, trusted-device, consular, dispatch, or messaging evidence.

## Local correction

`spine_api/routers/duty_of_care_radar.py` now returns a canonical
`PREVIEW_ONLY` envelope with `RealityTier.DETERMINISTIC_PREVIEW`, explicit
source and missing-upgrade requirements, `provider_connected: false`, no
external reference, no external action, no operational write, and no effects.

The cockpit payload is marked `UNVERIFIED_LOCAL_FIXTURES`. STEP output is
`DRAFT_NOT_SUBMITTED`, dispatch output is `FIXTURE_NOT_DISPATCHED`, and the SOS
payload is `PAYLOAD_PREVIEW_NOT_SENT`. The existing local engine remains useful
for deterministic workflow analysis but no longer crosses the API boundary as
evidence of an emergency operation.

The workbench panel now uses sample/preview wording for geofences, beacon
status, STEP records, dispatch fixtures, threat incidents, and SOS payloads.

## Verification

```text
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_duty_of_care_router_truth_boundary.py \
  tests/test_duty_of_care_radar.py

2 passed
```

The broader frontend workbench honesty suite and typecheck must be rerun after
the panel copy change. Provider, hosted, legal, emergency-operations, trusted
device, consular, dispatch, messaging, and operator-approval evidence remain
open.

## Long-term upgrade gate

Live duty-of-care capability requires authenticated threat sources with
freshness/provenance, trusted traveler/device identity and consent, official
STEP submission receipts, dispatch assignment and delivery receipts,
idempotency and reconciliation, operator approval, audit references, privacy
controls, and tested failure/recovery behavior. Until those are present, this
surface remains a local preview or is disabled for operational use.
