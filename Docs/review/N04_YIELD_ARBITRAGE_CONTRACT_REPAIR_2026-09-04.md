# N-04 Yield Arbitrage Contract Repair — Supplemental Evidence — 2026-09-04

> Canonical decision record: [YIELD_CONTRACT_N04_2026-09-04.md](YIELD_CONTRACT_N04_2026-09-04.md).
> This companion preserves the detailed source comparison and custody/evidence
> notes from this bounded audit; it is not a second product contract.

## Scope and ownership

This bounded review owns the frontend/backend contract mismatch identified as
N-04. It does not claim ownership of the other dirty worktree slices, add a
live supplier integration, or authorize Git staging, commit, or push.

The review was performed against the live checkout on 2026-09-04. Existing
concurrent changes in the agency workbench were preserved and re-checked
before this lane was changed.

## Finding

The app-local workbench panel had previously targeted frontend-only routes:

- `POST /api/v1/yield-arbitrage/rates/compare`
- `POST /api/v1/yield-arbitrage/reticket/execute`

Neither route exists in `spine_api/routers/yield_arbitrage.py`. The canonical
FastAPI router is mounted at `/api/v1/yield` and exposes:

- `GET /api/v1/yield/arbitrage/{trip_id}`
- `GET /api/v1/yield/opportunities?trip_id=...`
- `POST /api/v1/yield/swap-supplier`

The former panel also had a local sample fallback and a hard-coded booking
context. That behavior could present invented rate opportunities or a fake
reticket success when the backend was unavailable.

## Current implementation

The live app-local panel now uses `api.get` against the canonical
`/api/v1/yield/arbitrage/{trip_id}` route and `api.post` against
`/api/v1/yield/swap-supplier`. The parent workbench passes its resolved,
URL-derived trip ID through `PersonaCouncilPanel`; no default demo resource is
used. Missing trip context, transport/auth errors, and an agency with no
uploaded supplier contracts render explicit status/error states. Mutation
failure is rendered inline rather than reported as successful simulation.

The BFF route map now explicitly allows only the two panel-used canonical
paths:

| Frontend path | Backend path | Evidence |
| --- | --- | --- |
| `/api/v1/yield/arbitrage/{trip_id}` | `api/v1/yield/arbitrage/{trip_id}` | `frontend/src/lib/route-map.ts`, `spine_api/routers/yield_arbitrage.py` |
| `/api/v1/yield/swap-supplier` | `api/v1/yield/swap-supplier` | same |

The invented `yield-arbitrage/rates/compare` and
`yield-arbitrage/reticket/execute` paths remain unmapped and therefore return
the proxy's deny-by-default 404 if reintroduced by a future caller.

## Verification evidence

Focused frontend contract tests:

```text
pnpm exec vitest run src/lib/__tests__/route-map.test.ts
pnpm exec vitest run src/app/(agency)/workbench/__tests__/YieldArbitragePanel.contract.test.tsx src/lib/__tests__/route-map.test.ts
2 test files passed
21 tests passed
0 failures
```

The tests assert both canonical positive mappings, placeholder substitution for
an agency-scoped trip ID, negative denial of both invented legacy paths, no
request without a trip, the exact canonical GET path, and the exact canonical
supplier-selection POST payload.

Targeted ESLint for the changed yield files passed with zero errors or
warnings. Frontend TypeScript typecheck passed.

The parent workbench wiring is visible in:

- `frontend/src/app/(agency)/workbench/PageClient.tsx` — passes
  `resolvedTripId` to `PersonaCouncilPanel`.
- `frontend/src/app/(agency)/workbench/PersonaCouncilPanel.tsx` — forwards
  `tripId` to both yield panel render locations.
- `frontend/src/app/(agency)/workbench/YieldArbitragePanel.tsx` — calls the
  canonical routes and has no local quote/reticket fallback.

The backend contract and agency scoping are covered by the existing suites:

- `tests/test_yield_arbitrage_router.py`
- `tests/test_yield_arbitrage_real.py`

Those suites verify trip lookup, no-contract behavior, uploaded-contract
calculation, sorting, and supplier-selection mutation. They do not prove a
real external supplier feed or a real reticket/voucher operation.

## Alignment decision

**Decision: ACCEPT+MODIFY — align the visible panel to the existing canonical
contract; do not add compatibility routes for the invented API.**

This is first-principles and doctrine aligned because it:

1. has one source of truth for the route and response shape;
2. preserves deny-by-default proxy behavior;
3. requires a real trip context and server-side agency scoping;
4. fails honestly when data or transport is unavailable; and
5. separates a local supplier-selection mutation from an external booking
   reticket operation.

## Residual findings and gates

The repository still contains a second tracked component at
`frontend/src/components/workspace/panels/YieldArbitragePanel.tsx` that is not
the app-local panel currently rendered by Persona Council. It targets the same
canonical routes and has useful presentation behavior, but this lane did not
delete or merge it because the worktree contains concurrent unclassified
changes. A future owner should perform the required field-by-field
supersession/call-site audit and consolidate the duplicate only after semantic
ownership is established.

### Consolidation audit completed (2026-09-11, Claude Code session)

The deferred field-by-field supersession/call-site audit has been performed
per the repo Supersession Workflow. Verdict: **the workspace-panels copy is a
strict subset of the app-local canonical panel — deletion is correct and no
merge is required.**

| Dimension | workspace/panels copy (199 ln) | app-local canonical (207 ln, `096ceba`) |
|---|---|---|
| Call sites | **0 imports** anywhere in `frontend/src` | 3 live (PersonaCouncilPanel + contract + honesty tests) |
| Export shape | named export | default export (all 3 call sites import default) |
| Honesty contract | absent | SimulatedBadge + documented no-fabrication behavior |
| Response shape | older (no `generated_at`, no `_meta`) | `generated_at`, `_meta.reality_tier`, `missing_for_upgrade` |
| Swap typing | untyped `api.post` | typed `SupplierSwapResponse` |
| Routes | same canonical routes | same + N-04 repaired contract |

Deletion is executing this section's standing plan; the file remains
recoverable from history (`git show HEAD:<path>`) at any time. The unstaged
working-tree deletion observed 2026-09-11 belongs to the Elena
audit-remediation lane and should ride its commit.

The following remain open and are not proven by this repair:

- real GDS/bedbank/Hotelbeds/WebBeds provider credentials, rate freshness, and
  commercial contracts;
- provider-specific cancellation, inventory, voucher, and reticket semantics;
- durable multi-writer booking CAS and compensating-action records;
- hosted BFF/browser/session/SSE proof;
- real booking mutation and independent receipt verification;
- production metrics, rollback, legal/privacy, and pilot-release gates.

Accordingly, N-04 is **locally contract-aligned and repaired**, but the yield
capability remains **data-dependent and not launch-ready**.
