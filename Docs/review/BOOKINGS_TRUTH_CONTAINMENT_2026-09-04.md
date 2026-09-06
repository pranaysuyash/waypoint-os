# Bookings Surface Truth Containment — 2026-09-04

**Status:** implemented locally; provider-backed booking capability remains open
**Owner:** bookings surface (`frontend/src/app/(agency)/bookings/`)
**Review lens:** PER-0164 Assumption Auditor; Operating, Security/Privacy/Safety,
Testing, and Documentation doctrines
**Evidence boundary:** local source inspection and focused frontend tests only;
no supplier, GDS, DMC, payment, hosted, or production system was contacted

## Executive finding

The `/bookings` route had no booking-data API or provider evidence path, while
its client fixture was presented as fulfilled commercial state. The prior page
rendered hardcoded PNR-like references, voucher-issued and confirmed statuses,
a zero-cost hold, live GDS/DMC synchronization, encrypted confirmation
artifacts, and a 96% extraction confidence claim. That combination could cause
an operator to treat a visual fixture as a real reservation.

The local correction keeps the useful trip picker, sample itinerary roster,
task layout, navigation links, and document-preview interaction, but makes the
state boundary explicit: the route is a visual planning sandbox, not a booking
ledger.

## Observed pre-change evidence

Observed in the live checkout before this slice:

| Surface | Prior behavior | Risk |
|---|---|---|
| Initial roster | Hardcoded Emirates/Sabre, hotel, transfer, and helicopter rows with confirmation-like codes | A sample row looked provider-confirmed |
| Statuses | `confirmed`, `voucher_issued`, and `hold_active` | Implied external fulfillment and an active commercial hold |
| Header/table | “Confirmed Supplier Bookings & PNR Ledger” and “Live GDS & DMC Direct Sync” | Implied provider connectivity |
| Metrics | “Total Fulfilled Value”, voucher-contract backing, “48h zero-cost hold active”, and Fernet-encrypted artifacts | Implied money, contract, hold, and security guarantees |
| Parser | Browser-local timeout selected a supplier, generated a random confirmation-like reference, and returned `0.96` confidence | Implied verified extraction and a real booking artifact |
| Add action | “Record & Add to Ledger” | Implied persistence and ledger mutation |

These observations correspond to the broader simulator/provider audit in
`Docs/review/SIMULATOR_PROVIDER_TRUTH_AUDIT_2026-09-04.md`.

## Implemented correction

### Truthful data model

- Replaced `confirmationCode` and fake encrypted references with nullable
  `referenceCode`.
- Replaced operational statuses with the single local-only
  `sample_preview` status.
- Added `sourceLabel` so every displayed record identifies its fixture or
  browser-local parse provenance.
- Split `ExtractedPreview` from `BookingRecord`; a preview has no `id` until
  the user explicitly adds a sample to the current view.
- Removed random generated PNR/secret-looking values and the unsupported 96%
  confidence value.

### Truthful presentation

- Added the canonical shared `SimulatedBadge` with `Sample data`.
- Added a page-level notice stating that records, references, amounts, and
  task states are illustrative, provider-unverified, and not persisted.
- Renamed the roster to `Sample Booking Records` and all row states to
  `Sample / unverified`.
- Replaced live/fulfilled/hold/security claims with `Unavailable`, `Not
  connected`, and explanatory provider-boundary copy.
- Renamed the action to `Preview Booking Document`, the parser action to
  `Preview Parsed Details`, and the local add action to `Add Sample to This
  View`.
- Added `role="dialog"`, `aria-modal`, and an accessible title for the preview
  dialog.

### Preserved behavior

- Trip selection continues to use the canonical `useTrips`/`useTrip` hooks.
- Ops and timeline links remain available for the selected planning trip.
- Sample quick-paste inputs and local parsing remain available for UI/demo
  exploration.
- A parsed source reference may be displayed, but only as
  `Source reference (unverified)`; no provider lookup or mutation occurs.

## Verification evidence

Commands run from `frontend/`:

```text
npx vitest run 'src/app/(agency)/bookings/__tests__/page.test.tsx'
  Test Files  1 passed (1)
  Tests       2 passed (2)

npx tsc --noEmit
  passed

npx eslint 'src/app/(agency)/bookings/PageClient.tsx' \
  'src/app/(agency)/bookings/page.tsx' \
  'src/app/(agency)/bookings/__tests__/page.test.tsx'
  passed with no diagnostics
```

The focused tests cover two claims (Tier 2, S1):

1. The route exposes sample provenance and unavailable provider state, and no
   longer renders the removed confirmed/live/zero-cost copy.
2. The local parser displays an unverified source reference and illustrative
   value, never renders the old success/ledger language, and adds only a sample
   record to the current browser view.

The test suite is intentionally not presented as provider or browser proof.
The parser regression is S1 in this run; a future mutation run should remove
the sample badge or reintroduce a fulfilled status and demonstrate failure for
S3 promotion.

## Remaining provider-backed work

This correction is containment, not completion of booking execution. The
following work remains `Unknown` or `Proposed` and must not be inferred from
the green local tests:

- Define and implement a canonical persisted booking contract tied to a trip
  and tenant, including source, freshness, provider, external reference,
  status, amount, currency, and reconciliation state.
- Add a real booking API/store before replacing the sample roster with live
  records; verify tenant authorization, idempotency, retries, timeouts, and
  unknown provider outcomes.
- Establish explicit Amadeus/Sabre/NDC, hotel/DMC, transfer/activity, and
  voucher-provider contracts, credentials, costs, rate limits, callbacks, and
  reconciliation semantics.
- Replace the local parser with a reviewed document-ingestion path if that
  capability is intended: raw-input provenance, extraction confidence,
  abstention, PII handling, encrypted persistence, retention, and human
  confirmation are required before a reference can become operational state.
- Add authenticated browser/device evidence for the real booking workflow and
  verify independently against provider/order/receipt state; a success banner
  or local row is insufficient.
- Revisit the navigation description in
  `frontend/src/lib/nav-modules.ts`, which remains outside this owned slice and
  still describes the module as confirmed operational records.

## Decision

**Accepted as local truth containment.** This is additive because it preserves
the useful planning/demo interaction while removing unsupported authority and
commercial claims. It does not authorize provider integration, production
booking mutations, payment activity, legal approval, or Git staging/commit/push.
