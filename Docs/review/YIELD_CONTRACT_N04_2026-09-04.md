# Yield contract repair — N-04

**Date:** 2026-09-04\
**Status:** canonical frontend contract wired and locally verified; live supplier
connectivity remains explicitly unimplemented\
**Scope:** the agency workbench `YieldArbitragePanel` and its parent trip-context
boundary

## Finding

The workbench panel called routes that do not exist in the canonical backend:

- `/api/v1/yield-arbitrage/rates/compare`
- `/api/v1/yield-arbitrage/reticket/execute`

Those calls were accompanied by fabricated booking IDs, supplier offers, savings,
and a successful reticket fallback when the network request failed. The backend's
actual contract is the authenticated `/api/v1/yield` router:

- `GET /api/v1/yield/arbitrage/{trip_id}`
- `GET /api/v1/yield/opportunities?trip_id=...`
- `POST /api/v1/yield/swap-supplier`

The canonical response includes `data_sufficient`, supplier options, and reality
tier metadata. A reachable endpoint is therefore not equivalent to having live
commercial supplier data.

## Implementation

- `frontend/src/app/(agency)/workbench/YieldArbitragePanel.tsx`
  - accepts a nullable `tripId` instead of inventing a booking/trip;
  - uses the centralized API client and canonical `/api/v1/yield` routes;
  - URL-encodes the trip identifier;
  - renders explicit loading, unavailable, no-contract, and success states;
  - removes offline fabricated opportunities and reticket-success copy;
  - only offers supplier selection for options returned by the backend.
- `frontend/src/app/(agency)/workbench/PersonaCouncilPanel.tsx`
  - accepts and forwards the workbench trip context.
- `frontend/src/app/(agency)/workbench/PageClient.tsx`
  - passes the existing resolved trip identifier into the council panel.

Supplier selection is still a guarded backend mutation that updates the trip's
selected supplier. It is not described as booking, reticketing, voucher issuance,
or live provider execution. The panel keeps a `Data-dependent` badge because the
current provider adapter is still sandbox/local-contract infrastructure.

## Verification

```text
npm run typecheck                         → passed
npm test -- --run simulated-panels...    → 11 passed
npm test -- --run                        → 171 files / 1,295 tests passed
npm run build                            → passed
```

The added regression proves:

1. no trip context renders a truthful “select a trip” state and never references
   the former `BKG-PARIS-882` fixture;
2. a trip context calls exactly `/api/v1/yield/arbitrage/{tripId}`;
3. a successful API response with `data_sufficient=false` renders the explicit
   no-contract state.

## Alignment and remaining boundary

This is first-principles aligned because authorization and commercial data now
come from the canonical trip/API contract, and network failure cannot become a
false business-success claim. It is long-term aligned because the panel shares
the centralized API client and backend response shape rather than creating a
second yield protocol. It is doctrine aligned because simulated/provider limits
are visible and local UI evidence is not promoted to live-provider proof.

Still open:

- live GDS/bedbank connector contracts and credentials;
- provider rate freshness, cancellation, reticket, and failure semantics;
- hosted/browser evidence for the authenticated BFF path;
- durable audit/compensation semantics for supplier swaps before autonomous
  booking mutations are allowed.

## Execution addendum — BFF route contract and caller proof

The final bounded repair also added the two canonical yield paths to the
deny-by-default frontend BFF registry in
`frontend/src/lib/route-map.ts`:

- `v1/yield/arbitrage/{trip_id}` → `api/v1/yield/arbitrage/{trip_id}`
- `v1/yield/swap-supplier` → `api/v1/yield/swap-supplier`

The former invented `v1/yield-arbitrage/rates/compare` and
`v1/yield-arbitrage/reticket/execute` paths remain intentionally unmapped.

The route-map regression now verifies both positive mappings, placeholder
substitution, and denial of both invented paths. The component contract
regression additionally verifies that no request is made without a trip ID,
the exact canonical GET path is requested with a real trip, and the exact
canonical supplier-selection POST payload is sent.

Final focused receipt:

```text
pnpm exec vitest run \
  'src/app/(agency)/workbench/__tests__/YieldArbitragePanel.contract.test.tsx' \
  src/lib/__tests__/route-map.test.ts
2 test files passed
21 tests passed
0 failures

Targeted ESLint: 0 errors, 0 warnings
Frontend TypeScript typecheck: passed
```

The app-local panel is rendered by
`frontend/src/app/(agency)/workbench/PersonaCouncilPanel.tsx`, which receives
`resolvedTripId` from `PageClient.tsx`; the panel has no local quote or
reticket-success fallback. A second older component remains under
`frontend/src/components/workspace/panels/YieldArbitragePanel.tsx`; it was
preserved because the live worktree contains concurrent unclassified changes.
Any future consolidation must apply the repository supersession workflow
before removing or merging that artifact.
