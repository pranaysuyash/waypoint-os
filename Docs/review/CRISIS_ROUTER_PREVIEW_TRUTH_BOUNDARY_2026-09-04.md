# Crisis Router Preview Truth Boundary — 2026-09-04

**Owner lane:** crisis operations API router (`spine_api/routers/crisis_ops.py`)
**Review lens:** PER-0164 Assumption Auditor
**Decision:** accept the local deterministic-preview containment; keep all
provider-backed crisis operations out of the release claim until external
evidence exists.

## Scope and evidence boundary

This slice covers the five endpoints mounted under `/api/v1/crisis`:

- `POST /incidents/declare`
- `POST /evacuation/plan`
- `POST /ground/dispatch`
- `POST /beacon/check-in`
- `POST /consular/step-manifest`

The lower-level engines under `src/crisis/` remain available for their existing
unit contracts. They are deterministic local code and are not provider
integrations. This change hardens the API router, which is the boundary that a
frontend or external client would otherwise interpret as an operational result.

Evidence is local source and test evidence only. No crisis feed, licensed
dispatch service, SMS/WhatsApp provider, device beacon, embassy/STEP endpoint,
carrier, charter operator, hosted deployment, legal review, or real traveler
record was accessed.

## Findings before the change

The router previously returned operational-looking claims produced by local
engines, including:

- `success` incident/plan/dispatch/check-in/STEP statuses;
- evacuation legs marked `DISPATCHED`, `CONFIRMED_SLOT`, `TICKETED`, or
  `REBOOKED_HK`;
- `is_charter_confirmed: true` and generated consular case references;
- a hardcoded driver, phone number, plate, `EN_ROUTE` state, and dispatched SMS
  text;
- `duty_of_care_acknowledged: true` and a real-time-looking beacon timestamp;
- `TRANSMITTED_TO_EMBASSY_DESK`, generated registry references, and fabricated
  defaults for missing passport, nationality, phone, and hotel data;
- hardcoded affected trips and passenger counts on a declared incident.

None of those claims had provider evidence or a durable operational write.

## Implemented contract

Every router response now contains:

```json
{
  "status": "PREVIEW_ONLY",
  "reality_tier": "deterministic_preview",
  "simulation": true,
  "provider_connected": false,
  "external_action": false,
  "operational_write": false,
  "effects": [],
  "metadata": {
    "source": "local_deterministic_preview",
    "external_reference": null,
    "simulation": true
  }
}
```

The metadata is generated through the canonical `RealityTier` and
`TierMetadata` contract. It also declares the missing evidence needed for an
upgrade to a connected capability.

Endpoint-specific safeguards:

| Endpoint | Safe behavior | Explicitly prevented claim |
|---|---|---|
| Incident declaration | reflects only the submitted geofence/headline; no affected trips or passenger registry state | active incident registry or official advisory claim |
| Evacuation plan | computes candidate legs but rewrites all leg statuses and carrier labels to preview-only; charter and consular fields are unconfirmed | dispatch, ticketing, charter slot, or consular case confirmation |
| Ground dispatch | creates a stable `PREVIEW-DRV-*` request id; omits driver/plate/phone assignment and reports `NOT_SENT` | driver assignment, `EN_ROUTE`, SMS/WhatsApp delivery, emergency notification |
| Beacon check-in | reflects submitted values as requested input; reports no persistence, acknowledgement, or timestamp | verified safety, duty-of-care acknowledgement, durable telemetry |
| STEP manifest | keeps supplied fields only; missing fields remain `null`; draft status and no transmission receipt | official registration, embassy transmission, or fabricated identity/contact data |

No endpoint calls the ground-dispatch or safety-beacon engines after the
boundary hardening. The evacuation engine is retained only as a local candidate
planner; its operational-looking fields are sanitized before returning to the
client.

## Tests and commands

Command:

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_crisis_router_truth_boundary.py \
  tests/test_crisis_evacuation.py
```

Result on 2026-09-04: **8 passed**.

Command:

```bash
.venv/bin/ruff check \
  spine_api/routers/crisis_ops.py \
  tests/test_crisis_router_truth_boundary.py \
  tests/test_crisis_evacuation.py
```

Result: **All checks passed**.

The new tests assert the common metadata contract and specifically reject:

- fabricated incident registry state;
- `CONFIRMED`, `TICKETED`, `DISPATCHED`, `REBOOKED`, or charter-confirmed plan
  output;
- assigned driver identity, phone, plate, or notification;
- persisted/acknowledged safety beacon output;
- STEP transmission, external references, and default fake identity/contact
  values.

## Alignment assessment

**First principles:** a crisis preview may calculate a plan, but cannot claim
that a person, vehicle, carrier, embassy, or safety system acted. The API now
models that distinction directly instead of relying on frontend copy.

**Long term:** the response contract is additive and provider-neutral. A future
connected adapter can promote a response only when it supplies authenticated
provider evidence, an external reference, freshness, idempotency, and an
operator/human gate appropriate to the action. The current tier cannot mutate
operational state.

**Doctrine:** local computation, external evidence, and side effects remain
separate. The change does not rename or delete the lower-level engine paths,
overwrite concurrent work, or infer production readiness from a passing unit
test.

## Still open and not safely implementable locally

The following require external authority or a separate integration package:

1. licensed ground-dispatch and vehicle/driver provider contract;
2. authenticated emergency messaging provider and delivery receipts;
3. trusted device/beacon ingestion, identity binding, consent, retention, and
   operator acknowledgement;
4. official State Department/STEP or consular integration, acceptance receipt,
   and jurisdictional policy;
5. carrier/charter/rail availability, ticketing, and cancellation/rebooking
   APIs with reconciliation and unknown-outcome handling;
6. crisis-source provenance, freshness, geographic confidence, and escalation
   policy;
7. privacy, safety, duty-of-care, legal, and contractual approval for handling
   location, passport, contact, and emergency data;
8. hosted multi-replica durability, audit anchoring, backup/restore, and
   operator runbooks.

Until those are separately evidenced, these endpoints must remain preview-only
and must not be marketed or exposed as live crisis dispatch, official STEP
transmission, confirmed evacuation, or verified safety telemetry.
