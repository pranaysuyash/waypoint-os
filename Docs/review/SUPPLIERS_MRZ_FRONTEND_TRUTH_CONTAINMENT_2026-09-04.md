# Suppliers and Document MRZ Frontend Truth Containment — 2026-09-04

**Status:** implemented locally; provider, hosted, legal, and browser-release
evidence remain open\
**Owner:** `frontend/src/app/(agency)/suppliers/` and
`frontend/src/app/(agency)/workbench/DocumentMRZPanel.tsx`\
**Review lens:** PER-0164 Assumption Auditor\
**Doctrines:** Operating, Review, Security/Privacy/Safety, Testing, and
Documentation\
**Evidence boundary:** current source inspection and focused jsdom tests only;
no supplier, GDS, airline, hotel, border authority, scanner, hosted deployment,
or production system was contacted

## Executive assessment

The two frontend surfaces were useful local demonstrations but their primary
visual hierarchy overstated what the system knew:

- the supplier route rendered hardcoded records as a verified partner ledger;
- contract, SLA, soft-hold, and supplier contact affordances looked operational;
- the MRZ route converted an unavailable parser into a hardcoded successful
  passport result;
- checksum validity was presented alongside wording that could be read as
  document or identity verification;
- voucher fixtures claimed Delta validation, Amadeus synchronization, and a
  direct hotel API link without a provider lookup.

The correction keeps local exploration valuable while making the evidence grade
part of the primary interface state. It does not create a provider integration
or claim one exists.

## Observed pre-change evidence

| Surface | Observed behavior | Why it was unsafe or misleading |
|---|---|---|
| Suppliers header | `Suppliers & DMC Directory`, “Preferred Partners”, “18 Contracts”, “98.8%”, and “48h Zero-Cost” | A reasonable operator could infer a populated commercial directory, measured SLA, active contracts, and available inventory |
| Supplier table | “Showing N Verified Partners”, green check icon, direct-looking company email targets, `48h Hold` | Fixture data was visually promoted to verified partner and hold state; a click could target an external organization |
| Rate-sheet action | `Ingest Wholesale Rate Sheet` and `Process & Ingest Contract` | The browser action closed the modal but did not upload or persist a contract |
| Trip context | “Current supplier risk” and “Synced with active itineraries” | A stored/derived trip snapshot was indistinguishable from live supplier verification or fresh provider data |
| MRZ fallback | Failed fetch populated Eriksson sample fields and `is_fully_verified: true` | Backend outage or route failure could look like successful verification of the submitted text |
| MRZ result state | `ZERO TRANSCRIPTION ERROR` and `CHECKSUMS VALID (SAMPLE PASSPORT)` | Check digits establish a format-level property, not document authenticity, identity, or complete transcription certainty |
| Voucher tab | `Delta (006) Validated`, `Amadeus Synchronized`, `Direct API Linked` | Static strings implied airline, GDS, and hotel-provider evidence that was not collected |

## Implemented local correction

### Suppliers

- Added the canonical shared `SimulatedBadge` with `Sample data` to the page
  heading.
- Added a page-level `Local preview only` note that explicitly denies
  contract, current-rate, SLA, inventory, and provider-confirmation claims.
- Added an `evidenceStatus: 'sample'` field to every fixture record so the
  model carries its evidence grade rather than relying only on copy.
- Renamed preferred/active/health/hold metrics to illustrative or sample
  states and explicitly state that no contract or inventory hold is persisted.
- Changed the table title and count from a master/verified ledger to
  `Illustrative Supplier Records` and `sample records`.
- Replaced the green verification icon with a clock and labels the row scores
  as fixture values rather than live SLA measurements.
- Reframed trip risk as `trip-derived` and marks supplier verification and
  snapshot freshness as unknown.
- Replaced real-looking mail targets with `example.invalid` values and removed
  the active mailto action; contact is unavailable in local preview.
- Renamed rate-sheet controls to preview language and added dialog semantics
  (`role="dialog"`, `aria-modal`, labelled title). The modal states that no
  upload, persistence, or supplier contact occurs.

### Document MRZ and voucher panel

- Preserved the deterministic backend MRZ parser path but removed the hardcoded
  passport fallback on request failure.
- Added an explicit parser-unavailable error and clears prior output before a
  new attempt, so stale or fabricated results cannot survive a failed request.
- Renamed the action to `Compute Checksum Preview` and the status to
  `CHECKSUM RULES APPLIED`.
- Labels the positive result `CHECKSUMS VALID — FORMAT ONLY` and explains that
  identity, authenticity, immigration status, and external records remain
  unchecked.
- Adds accessible labels and pressed state to tab controls and field inputs.
- Retains voucher strings only as clearly marked sample fixtures and removes
  airline/GDS/hotel synchronization claims.

## Verification evidence

Commands run from `frontend/` on 2026-09-04:

```text
pnpm exec vitest run \
  'src/app/(agency)/suppliers/__tests__/page.test.tsx' \
  'src/app/(agency)/workbench/__tests__/DocumentMRZPanel.test.tsx'
  Test Files  2 passed (2)
  Tests       4 passed (4)

pnpm exec eslint \
  'src/app/(agency)/suppliers/PageClient.tsx' \
  'src/app/(agency)/suppliers/__tests__/page.test.tsx' \
  'src/app/(agency)/workbench/DocumentMRZPanel.tsx' \
  'src/app/(agency)/workbench/__tests__/DocumentMRZPanel.test.tsx'
  passed with no diagnostics

pnpm exec tsc -p tsconfig.json --noEmit
  passed
```

Evidence classification:

- Focused test existence: Tier 2 / S0.
- Focused tests passing: Tier 2 / S1.
- Tests cover both positive and failure boundary behavior: successful checksum
  response, unavailable parser, and voucher fixture copy.
- The failure test demonstrates that no hardcoded passport result is emitted
  when the parser rejects or is unreachable.
- A future S3 mutation should remove the sample banner, restore a provider
  synchronization phrase, or restore fallback data and demonstrate test
  failure.
- No Tier 3 authenticated browser flow or Tier 4/5 provider observation was
  attempted in this bounded slice.

## First-principles decision

The user-facing question is not “can the checksum engine calculate a number?”
It is “what may an operator safely believe and act on after seeing this
screen?” A checksum engine can support a format-level assertion. It cannot by
itself support identity, authenticity, provider booking, contract, inventory,
SLA, or payment assertions. The chosen correction preserves the lower-risk
computation and removes unsupported authority from the UI and action surface.

This is `ACCEPT+MODIFY` for local truth containment. It is additive because the
planning and parser demonstrations remain available, while false operational
meaning is removed. A separate provider-backed implementation would be a new
architecture and authorization boundary, not an implicit continuation of this
patch.

## Remaining work and exact gates

The following remain open and are intentionally not implied as complete:

1. Define a canonical persisted supplier contract model with tenant ownership,
   source, provider, freshness, status, rate validity, provenance, and
   reconciliation state.
2. Replace hardcoded supplier rows with authenticated agency-scoped data only
   after a canonical API/store exists; prove multi-worker durability,
   authorization, expiry, and recovery.
3. Define provider contracts and credentials for DMC, hotel, airline/GDS/NDC,
   transfer, insurance, and voucher sources; include idempotency, retries,
   timeouts, unknown outcomes, cost, and reconciliation.
4. For MRZ/document intake, add a reviewed raw-input pipeline, scanner/OCR
   provenance, confidence and abstention rules, PII minimization, retention,
   encryption, access control, and human confirmation before operational use.
5. Add authenticated browser/accessibility evidence over the real intended
   workflows, then independently verify provider/order/receipt state; visual
   success or a local route response is insufficient.
6. Revisit `frontend/src/lib/nav-modules.ts` and other customer-facing copy
   that may still describe suppliers or documents as verified/live outside this
   owned slice.

## Review completeness

### Reviewed

- Current suppliers route/page client, existing supplier test, and all visible
  supplier metrics/table/modal actions.
- Current `DocumentMRZPanel`, its route-map entry, parser response shape, and
  parser fallback behavior.
- Existing simulated-panel test conventions and shared `SimulatedBadge`.
- Focused tests, lint, and TypeScript checks after the change.

### Not reviewed

- Backend supplier router, provider adapters, external contracts, deployment,
  legal/privacy approval, scanner hardware, or production data.
- Other provider-shaped frontend surfaces outside suppliers and MRZ.
- Authenticated browser rendering and screen-reader/device behavior.

### Remaining uncertainties

- Whether any current persisted `supplierIntelligenceSnapshot` has a provider,
  freshness, or evidence contract; the UI now treats those properties as
  unknown.
- Whether the backend MRZ response should eventually expose a canonical
  `RealityTier` envelope; this slice only prevents frontend overclaiming.
- Which organization owns future supplier, document, and legal acceptance
  decisions.

### Evidence needed

- Authenticated browser proof of preview copy and keyboard/dialog behavior.
- Provider contract and credential evidence before any live supplier state.
- Independent scanner/OCR and document-authenticity evidence before identity or
  compliance claims.
- Hosted persistence, audit, and recovery proof for agency records.

### Known blind spots

- Static text in other routes may still overclaim live supplier/document
  behavior; the broader simulator audit remains authoritative for that queue.
- Local tests do not prove visual hierarchy, contrast, mobile reflow, or
  provider behavior.
