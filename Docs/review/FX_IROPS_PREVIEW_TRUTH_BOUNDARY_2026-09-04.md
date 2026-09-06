# FX Sentinel and IROPS Preview Truth Boundary — 2026-09-04

**Owner lane:** backend simulator/provider API routes
(`spine_api/routers/fx_sentinel.py`, `spine_api/routers/irops_healer.py`) plus
the consumer panel (`frontend/src/app/(agency)/workbench/IROPSAutoHealerPanel.tsx`).

**Review lens:** PER-0164 Assumption Auditor

**Decision:** accept deterministic local calculation as a preview capability;
do not claim live market data, an executed hedge, carrier rebooking, a legal
compensation entitlement, payment/VCC issuance, or supplier communication until
the required external evidence exists.

## Scope and evidence boundary

This slice covers:

- `GET /api/v1/fx/rates`;
- `GET /api/v1/fx/exposures`;
- `POST /api/v1/fx/lock-rate/{trip_id}`;
- `POST /api/v1/irops-healer/heal`.
- the workbench IROPS recovery-plan preview and its network-failure fallback.

The lower-level calculators and journey graph remain deterministic local
engines. They are useful for analysis and unit testing, but they are not
provider integrations. The API router is the consumer-facing trust boundary,
so this record evaluates the returned contract rather than treating engine
output as external truth.

No market-data feed, treasury/hedging provider, carrier/GDS, lodging/payment
provider, legal claims system, supplier waiver endpoint, hosted deployment, or
real traveler record was accessed.

## Findings before the change

### FX sentinel

The route described a static `FX_RATES_TABLE` as “live” and returned a runtime
timestamp without market-data provenance. Exposure calculation silently used a
`$3,000` cost when a trip had no recommended cost, inferred supplier currency
from destination text, and exposed a persistent `fx_locked` state. The lock
endpoint wrote trip strategy state and emitted an `fx_rate_locked` audit event,
although no treasury provider or external hedge reference existed.

### IROPS healer

The route returned `status: success` from a deterministic engine that generated
an in-memory VCC, a €600 statutory compensation amount, carrier rebooking-like
actions, PNR revalidation language, and a supplier fee-waiver letter. Those
values had no provider confirmation, jurisdiction-specific legal evidence,
payment effect, or message delivery receipt.

## Implemented contract

### FX rates and exposures

Each rate record now identifies:

- `status: PREVIEW_ONLY`;
- `reality_tier: deterministic_preview`;
- `evidence_status: UNVERIFIED_REFERENCE_RATE`;
- `source: local_reference_table`;
- `provider_connected: false`;
- `external_reference: null`;
- `effects: []`;
- canonical `metadata` containing computation method, missing upgrade
  requirements, and non-operative action flags.

Exposure records use `COMPUTED_PREVIEW` and preserve the distinction between a
local calculation and a provider observation. If the trip has no positive
recommended cost, the result is explicit `risk_level: UNKNOWN` with
`evidence_status: INSUFFICIENT_TRIP_DATA`; no synthetic dollar amount is
introduced.

The destination-to-currency mapping remains a heuristic and is therefore not
treated as supplier truth. A future provider-backed implementation must replace
or validate it with an authoritative supplier currency and quote record.

### FX lock request

`POST /lock-rate/{trip_id}` now returns HTTP 200 with a non-operative preview
contract:

- `ok: false`;
- `status: PREVIEW_ONLY`;
- `lock_applied: false`;
- `locked_at: null`;
- `provider_connected: false`;
- `external_reference: null`;
- `effects: []`.

The endpoint still checks that the trip belongs to the requested agency, but it
does not call `TripStore.save_trip` or `AuditStore.log_event`. This preserves a
safe review flow without representing a local write as an executed hedge.

### IROPS recovery plan

The route still invokes the canonical local journey-graph planner, then
sanitizes the API result:

- top-level status is `PREVIEW_ONLY` with canonical deterministic-preview
  metadata;
- incident ID is a stable `PREVIEW-IROPS-*` identifier;
- `resolved_at` is `null`, and the plan is marked
  `UNVERIFIED_LOCAL_INPUT`/`PREVIEW_ONLY`;
- statutory compensation amount is withheld as `null` and retained only as
  `estimated_amount_eur`, with `UNVERIFIED_LEGAL_ESTIMATE` status;
- generated lodging VCC is withheld (`null`, `NOT_ISSUED`);
- counterfactual options are explicitly preview-only, with no provider,
  external reference, or effect, and an operator-review action;
- supplier waiver output is marked `DRAFT_NOT_SENT` with no external reference.

The lower-level engine's historical unit contract is intentionally preserved;
the API boundary prevents its generated artifacts from becoming product or
provider claims. This is a migration-friendly containment step, not evidence
that real IROPS automation exists.

### Frontend consumer boundary

The workbench panel now consumes the preview contract defensively and keeps a
local fallback that is explicitly analysis-only. It renders compensation as
`Not assessed`, lodging/payment as `Not issued`, and every rerouting action as
`Review only`. It never renders the backend's estimated legal amount as an
entitlement, never displays a VCC/card number, and never exposes an action
button that could be mistaken for rebooking, endorsement, approval, waiver,
or issuance. A failed provider-preview request is surfaced as an unavailable
preview rather than a fabricated success.

## Tests and evidence

Command:

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_fx_irops_truth_boundary.py \
  tests/test_currency_fx.py \
  tests/test_irops_healer_simulator.py \
  tests/test_strategic_phases_6_to_9.py
```

Result on 2026-09-04: **8 passed** (Tier 2, S1). The new boundary tests cover:

- reference-rate provenance and preview status;
- missing-cost abstention rather than fabricated exposure;
- no trip persistence or audit event for a hedge preview;
- no VCC, legal entitlement, provider confirmation, or completed action in the
  IROPS API response;
- compatibility of the existing strategic lifecycle after the lock contract
  changed.

Command:

```bash
pnpm exec vitest run \
  'src/app/(agency)/workbench/__tests__/IROPSAutoHealerPanel.test.tsx'
```

Result on 2026-09-04: **1 file / 3 tests passed** (Tier 2, S1). The consumer
tests cover the preview-only heading/badge, no operational action controls,
backend candidate normalization, legal/payment withholding, and a truthful
network-failure fallback. Targeted ESLint and the repository typecheck also
pass for the panel and test.

Command:

```bash
.venv/bin/ruff check \
  spine_api/routers/fx_sentinel.py \
  spine_api/routers/irops_healer.py \
  tests/test_fx_irops_truth_boundary.py \
  tests/test_strategic_phases_6_to_9.py
```

Result: **All checks passed**.

The lower-level `tests/test_irops_healer_simulator.py` remains green to show
that the deterministic analysis engine was not unnecessarily rewritten. The
router tests are the relevant consumer-safety evidence for the truth boundary.

## First-principles and doctrine assessment

**First principles:** a calculation is not an observation, a recommendation is
not a reservation, and a generated object is not an external effect. The API
now encodes those distinctions in machine-readable status and provenance.

**Long term:** the contract is additive and provider-neutral. A future market,
treasury, carrier, payment, or supplier adapter can promote the response only
after supplying authenticated identity, freshness, idempotency, external
reference, reconciliation, and appropriate operator/user authorization.

**Architecture:** the canonical local engines remain reusable; the router owns
consumer-facing reality classification. Unsupported mutations are removed from
the preview path rather than hidden behind a boolean or a disclaimer.

**Testing:** the tests target API claims and the known fabricated-success
failure modes. They are Tier 2/S1 currently; an S2/S3 mutation run and a
provider-backed Tier 3–5 contract remain required before launch claims.

## Required upgrade gates and residual risk

The following remain open and are deliberately not implemented in this local
slice:

1. authenticated market-data and treasury provider contracts, quote freshness,
   expiry, and hedge lifecycle;
2. carrier/GDS disruption feed, availability, rebooking/hold/ticket semantics,
   idempotency, reconciliation, and unknown-outcome recovery;
3. authorized lodging/payment integration, PCI/data boundaries, and payment
   confirmation/refund behavior;
4. jurisdiction- and itinerary-specific legal review for compensation claims;
5. supplier waiver submission, delivery receipt, and operator escalation;
6. durable shared state and audit-head anchoring across hosted replicas;
7. authenticated browser evidence and user-facing copy updates for any other
   frontend panel that still renders its own fallback VCC, legal amount, or
   “executing” wording;
8. independent provider/real-data evidence and explicit release-owner approval.

Until these gates are separately evidenced, the routes must remain preview-only
and must not be marketed as live FX hedging, confirmed IROPS healing, issued
VCCs, guaranteed compensation, or completed supplier action.

## Completeness statement

### Established current state

The four routes now expose deterministic-preview metadata and no longer perform
the FX lock write or return IROPS effect-bearing artifacts. Focused tests and
Ruff pass.

### Implemented state

Local reference-rate and journey-graph computations remain available for
operator review, while unsupported financial and operational effects are
withheld at the API boundary.

### Unresolved decisions

Provider selection, legal authority, durable hosted state, frontend migration,
operator workflow, and release exposure remain decisions for the owning lanes.

### Known blind spots

This record does not prove provider behavior, hosted multi-worker consistency,
browser rendering, legal compliance, payment authorization, real-data quality,
or production recovery.

## Frontend financial settlement follow-up — 2026-09-04

The related `FinancialSettlementPanel` had a separate customer-visible
fallback defect: its VCC action called `/api/v1/settlement/vcc/issue`, then
fabricated an `ACTIVE` card identifier and masked card number for both non-2xx
responses and network failures. Its FX and schedule panels also used words such
as “margin protected”, “net settled revenue”, and “due immediately” for static
examples.

The panel is now a local preview by construction:

- FX values are labelled arithmetic/reference assumptions and `NOT A QUOTE`;
- no payment is captured and no settlement is represented;
- the VCC tab performs only local positive-number validation and amount
  formatting; it does not call an issuance endpoint, authorize funds, create
  card credentials, or display a card-like identifier;
- invalid input produces an explicit alert rather than a fallback success;
- payment schedules are labelled illustrative timing, with no invoice,
  authorization, charge, or schedule creation;
- tab controls expose `aria-pressed` state and the amount input has an
  accessible name.

This is an `ACCEPT+MODIFY` local truth-containment correction. It preserves
useful arithmetic and workflow exploration, while removing provider, payment,
card, invoice, and settlement authority from the consumer surface. It does not
claim that the backend settlement endpoint is safe for live use; that remains a
separate provider/financial gate.

Frontend verification on 2026-09-04:

```text
pnpm exec vitest run \
  'src/app/(agency)/workbench/__tests__/simulated-panels-honesty.test.tsx'
  Test Files  1 passed (1)
  Tests       11 passed (11)

pnpm exec eslint \
  'src/app/(agency)/workbench/FinancialSettlementPanel.tsx' \
  'src/app/(agency)/workbench/__tests__/simulated-panels-honesty.test.tsx'
  passed with no diagnostics

pnpm exec tsc -p tsconfig.json --noEmit
  passed
```

The updated suite provides Tier 2 / S1 evidence for the local UI boundary,
including the network-independent VCC preview and invalid-input path. It does
not provide Tier 3 authenticated browser evidence, Tier 4 operator/device
observation, or Tier 5 payment/provider evidence. The original provider,
durability, legal, PCI/data-boundary, and release gates in this record remain
open.

## Backend settlement-route follow-up — 2026-09-04

The direct settlement APIs now match the same truth boundary as the workbench:

- `POST /api/v1/financial-ops/convert-currency` returns
  `COMPUTED_PREVIEW` with local-reference provenance and no external effect;
- `POST /api/v1/settlement/fx/calculate-quote`,
  `POST /api/v1/settlement/schedules/build`, and
  `POST /api/v1/settlement/commission/split` preserve deterministic arithmetic
  as computed previews rather than issued quotes, invoices, or payouts;
- `POST /api/v1/settlement/vcc/issue` returns `PREVIEW_ONLY`,
  `issuance_status: NOT_ISSUED`, `virtual_card: null`, and no credential-shaped
  fields. The card generator is not called.

Focused verification on 2026-09-04:

```text
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_financial_settlement_vcc.py tests/test_currency_fx.py
  9 passed
.venv/bin/ruff check <owned financial routers and tests>
  All checks passed
```

This closes the direct-call copy/state mismatch locally. It does not authorize
payment execution, treasury hedging, supplier settlement, PCI processing, or
financial-ledger writes; those remain external/provider and legal gates.
