# Simulator and Provider Truth Audit — 2026-09-04

**Lens:** PER-0164 Assumption Auditor\
**Method:** read-only source, route, caller, and existing-test inspection\
**Evidence boundary:** local source/tests only; no provider credentials, hosted
traffic, legal approval, or production side effects were used.

## Executive finding

The repository has improved labeling in several workbench panels, but truth is
not enforced at the API, route, legacy-page, or state-transition boundaries.
The highest-risk residuals are public/agency pages that render hardcoded sample
records as confirmed commercial state and backend endpoints that return
operational-looking statuses or mutate trip state without external provider
evidence.

## S0 — public and agency sample state

### Bookings page

`frontend/src/app/(agency)/bookings/PageClient.tsx` constructs hardcoded
records in the client:

- lines 91–139: Emirates/Sabre PNR, confirmed hotel, voucher-issued transfer,
  and an active helicopter hold;
- lines 192–242: “Auto-Extract Booking Voucher” fabricates supplier, PNR,
  amount, and confidence `0.96`;
- lines 263–269 and 344–397: claims confirmed supplier PNRs, live GDS/DMC
  sync, zero-cost holds, and confirmed supplier bookings.

This is a trust-boundary violation, not merely a copy issue. Preferred fix is
canonical persisted booking data with an empty/unavailable state. Interim fix
is a whole-surface `Sample/Demo` label plus removal of confirmed/live claims.

### Legacy public proposal route

`frontend/src/app/proposals/[proposalId]/page.tsx` contains client-side
operational claims:

- lines 167–173: “Loading verified proposal”;
- lines 203–206: “48h Price Lock Active”;
- lines 254–258: “Direct DMC Verified”;
- line 270: “Live Pricing Updated”;
- lines 159–165: acceptance is local timeout/state behavior, not persisted
  acceptance.

This route must be consolidated with the canonical persisted proposal route or
explicitly reduced to a labeled demonstration.

### Other public/agency residue

- `frontend/src/app/(agency)/suppliers/PageClient.tsx:55–267` contains
  hardcoded supplier/rate/SLA/contact data and claims ingested wholesale
  contracts, zero-cost holds, and active itinerary sync without provider
  evidence.
- `frontend/src/app/(agency)/workbench/DocumentMRZPanel.tsx:174–184` claims
  “Delta (006) Validated”, “Amadeus Synchronized”, and “Direct API Linked”
  despite sample-data labeling.
- `PersonaCouncilPanel.tsx:249,258` still says “All Operational Engines” and
  “Autonomous Proposal Compiler”; these should read as demo engines/simulation.

## S1 — backend operational simulator mutation

### Disruption radar

`spine_api/routers/disruption_radar.py`:

- lines 1–6 and 57–61 describe a real-time/autonomous system;
- lines 68–91 fabricate a cancellation when no disruption exists;
- lines 96–134 generate local rebooking options;
- lines 137–179 mutate trip flight/status fields, write an audit event, and
  return `ok=True`/`rebooked_at` without supplier confirmation.

Required invariant: without provider evidence, return `SIMULATED`, `DRAFT`, or
`AWAITING_PROVIDER`; do not mutate operational booking state or return
`REBOOKED`/`CONFIRMED`.

### Crisis, dispatch, and STEP

`spine_api/routers/crisis_ops.py:1–167` uses live ground-dispatch,
consular-liaison, official STEP, and real-time telemetry language. The local
engines generate random manifest references, hardcoded drivers, client-supplied
coordinates, and `TRANSMITTED_TO_EMBASSY_DESK`/`DISPATCHED`/`TICKETED` states
without an integration. The frontend has a simulation badge, but still says
“Live Ground Driver Dispatch” at `CrisisEvacuationPanel.tsx:114`.

### Financial/VCC

`spine_api/routers/financial_settlement.py:1–78`,
`src/fees/settlement_engine.py:100–132`, and
`spine_api/providers/stripe_issuing_adapter.py:92–204` generate pseudo-card
identifiers and unconditional approval-like results. The workbench panel is
more honest, but the backend needs an explicit simulation contract. Real
Stripe Issuing requires compliance/PCI controls, provider webhooks,
replay/idempotency, and secure card-data handling.

### GDS/distribution

- `spine_api/routers/gds_sandbox.py:2–76` claims live sandbox queries, PNR,
  e-ticket, and generic success statuses;
- `src/distribution/amadeus_sandbox_adapter.py:26–56` and
  `sabre_sandbox_adapter.py:31–58` explicitly return deterministic simulated
  offers/tickets;
- `spine_api/routers/distribution.py:63,104` claims confirmed IATA NDC order
  creation without external evidence.

The UI is partly labeled, but API responses and schemas still invite incorrect
future use. Return reality metadata and non-operational statuses.

### Other backend surfaces

The same pattern appears in:

- `spine_api/routers/fx_sentinel.py:17–105` — fixed local rates described as
  live rates;
- `spine_api/routers/irops_healer.py:1–64` and
  `src/orchestration/irops_healer.py:1–70` — local rebooking/VCC/waiver
  simulation presented as autonomous healing;
- `spine_api/services/ghost_concierge.py:1–97` and
  `src/intake/frontier_orchestrator.py:77–86` — telemetry/dispatch claims and
  fabricated workflow IDs;
- `spine_api/routers/duty_of_care_radar.py:1–30` and
  `src/orchestration/duty_of_care_radar.py:53–107` — static incidents, SOS,
  STEP, and dispatch payloads without providers.

## Provider namespace finding

The following files are deterministic simulators under provider-like paths:

- `spine_api/providers/amadeus_enterprise_adapter.py`
- `spine_api/providers/stripe_issuing_adapter.py`
- `spine_api/providers/twilio_telephony_adapter.py`

No non-test production callers were found in the reviewed paths. A long-term
correction is an explicit simulator namespace plus a separate real-provider
interface. Do not rename or migrate the dirty tree without ownership
classification and a separate plan.

## Required contract and test hardening

Use the canonical `RealityTier` contract where appropriate and add response
metadata such as:

- `reality_tier: SIMULATED | DRAFT | PROVIDER_UNAVAILABLE | LIVE`;
- `provider_connected: bool`;
- `effects: []` for non-operational simulations;
- source, freshness, external reference, and evidence provenance.

Add tests that reject operational statuses without provider evidence, including
`CONFIRMED`, `TICKETED`, `DISPATCHED`, `TRANSMITTED`, `REBOOKED`, `ISSUED`,
`OFFICIAL`, and `VERIFIED`. Add a source/rendered-copy corpus covering public
proposal, bookings, suppliers, MRZ, crisis, GDS, VCC, IROPS, FX, and dispatch
surfaces. Add a disruption test proving execution cannot mutate a real booking
without provider confirmation.

## Authorization-dependent work

Real Amadeus/Sabre/NDC, Stripe Issuing, Twilio, crisis/STEP/SMS/dispatch, FX,
and empty-leg integrations require provider contracts, credentials, legal and
privacy review, webhook/reconciliation semantics, rate/cost limits, and human
gating. Those are not implied by local implementation or tests.

## Separate signoff-integrity issue

This audit does not close F-03. `team_workflows.py:86` accepts client-supplied
`reviewer_id`, and `corporate_policy.py:49` accepts client-supplied
`approver_name`. That is a distinct authenticated-principal and artifact-hash
authorization package.
