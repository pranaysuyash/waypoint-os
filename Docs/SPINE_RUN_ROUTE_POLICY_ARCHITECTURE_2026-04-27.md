# Spine Run Route Policy Architecture

**Date:** 2026-04-27
**Scope:** `POST /api/spine/run` timeout failure during the Singapore scenario live test
**Status:** Implemented

## First-Principles Decision

`POST /api/spine/run` is not a normal quick REST read. It is a synchronous command that runs the intake, decision, strategy, audit, leakage, fee, and frontier analysis chain. The backend can legitimately take longer than the generic frontend proxy default.

The clean architectural fix is not a duplicate explicit route. The clean fix is to make route execution policy part of the canonical route registry:

- route identity: frontend path segments such as `["spine", "run"]`
- backend target: `run`
- execution policy: `timeoutMs: 60_000`

That keeps the BFF behavior centralized and prevents drift between:

- `frontend/src/lib/route-map.ts`
- `frontend/src/app/api/[...path]/route.ts`
- `frontend/src/lib/proxy-core.ts`

## Why Not Restore A Dedicated Route File

A dedicated `frontend/src/app/api/spine/run/route.ts` would fix the symptom, but it would create a second proxy path for a backend-backed route already covered by the catch-all route map. The project guardrail is one canonical route path per resource/action. A second route file would make future timeout, auth forwarding, header, cookie, and cache behavior easier to drift.

The canonical route-map approach keeps:

- deny-by-default behavior for unmapped routes
- shared auth/cookie forwarding in `proxy-core.ts`
- shared timeout error handling
- a single place to read backend route contracts

## Implementation

Updated `frontend/src/lib/route-map.ts`:

- Added `BackendRouteConfig`.
- Added `resolveBackendRoute(...)`, returning `{ backendPath, timeoutMs? }`.
- Kept `resolveBackendPath(...)` as a compatibility wrapper for existing callers.
- Marked `spine/run` as:

```ts
{
  backendPath: "run",
  timeoutMs: 60_000,
}
```

Updated `frontend/src/app/api/[...path]/route.ts`:

- Uses `resolveBackendRoute(...)`.
- Passes `backendRoute.timeoutMs` into `proxyRequest(...)`.

Updated `frontend/src/lib/__tests__/route-map.test.ts`:

- Added coverage that `spine/run` resolves to backend `run` with `timeoutMs: 60_000`.

## Verification

Fresh checks run:

- `npm test -- --run src/lib/__tests__/route-map.test.ts`
  - Result: 5 tests passed.
- `./node_modules/.bin/tsc --noEmit`
  - Result: exited 0 with no TypeScript errors.
- `npm run build`
  - Result: production build compiled successfully, TypeScript finished, and 34 static pages generated.

Note: a temporary Next route-handler integration test was attempted and removed because importing the Next route runtime caused Vitest lifecycle hangs after assertions completed. The durable contract is covered at the route-registry boundary, which is the changed abstraction.

## Remaining Product Work

This resolves the frontend BFF timeout policy for the live scenario. It does not complete the broader scenario evaluation. The next validation step is to run the Singapore scenario through the UI and record:

- process duration
- extracted destination/date/party/budget fields
- generated blockers and clarification questions
- whether the resulting trip is visible and useful to the logged-in agency owner
- whether agency scoping/auth behavior is correct
