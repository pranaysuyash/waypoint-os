# Runtime Console Triage

Date: 2026-05-11
Scope: Browser console logs reported from local frontend runtime.

## Reported Symptoms

1. `/api/auth/me` returned `401 Unauthorized`.
2. `/api/inbox?page=1&limit=1` returned `500 Internal Server Error` in the browser log.
3. Turbopack/HMR reported that `getPlanningStageProgressItems` was not exported from `frontend/src/lib/planning-list-display.ts`.
4. Browser reported repeated `[Violation] 'setInterval' handler took <N>ms` entries during development/HMR.

## Findings

### Missing Export

Current source exports `getPlanningStageProgressItems`:

- `frontend/src/lib/planning-list-display.ts:84`

Current consumers import it:

- `frontend/src/components/workspace/PlanningTripCard.tsx:7-12`
- `frontend/src/app/(agency)/trips/[tripId]/layout.tsx:27`

Relevant prior doc note:

- `Docs/react_doctor_supersession_audit_2026-05-11.md:271-290` says TypeScript caught this exact accidental removal and the export was restored.

Verification:

```bash
cd frontend && npx tsc --noEmit
# passed

cd frontend && npm run build
# passed

.venv/bin/python -m uvicorn spine_api.server:app --host 127.0.0.1 --port 8000
cd frontend && npm run dev
curl -s -i http://localhost:3000/overview
# HTTP/1.1 200 OK
```

Conclusion: the missing-export browser log does not match the current source/build/runtime state. Cold-restarted Next dev served `/overview` with no missing-export compile error. Most likely cause is stale dev-server/HMR state during the other agent's export-supersession pass.

### `/api/auth/me` 401

Direct check without cookies:

```bash
curl -s -i http://localhost:3000/api/auth/me
# HTTP/1.1 401 Unauthorized
# {"detail":"Not authenticated"}
```

Relevant source:

- `frontend/src/stores/auth.ts:81-124` intentionally calls `/api/auth/me`, then `/api/auth/refresh`, then clears auth state when unauthenticated.
- `frontend/src/components/auth/AuthProvider.tsx:44-57` hydrates auth on mount and rehydrates after protected API 401s.

Conclusion: `401` is expected when no valid `access_token` cookie is present. It is not by itself a regression.

### `/api/inbox` 500

Direct unauthenticated checks return `401`, not `500`:

```bash
curl -s -i 'http://localhost:3000/api/inbox?page=1&limit=1'
# HTTP/1.1 401 Unauthorized
# {"error":"Not authenticated"}

curl -s -i 'http://127.0.0.1:8000/inbox?page=1&limit=1'
# HTTP/1.1 401 Unauthorized
# {"detail":"Not authenticated"}
```

Relevant source:

- `frontend/src/app/api/inbox/route.ts:11-31` proxies `/api/inbox` to backend `/inbox` and maps auth statuses to `401/403`.
- `spine_api/server.py:1491-1558` owns backend `/inbox`.

Conclusion: the reported browser-side `500` was not reproduced without auth. If it recurs while authenticated, inspect the backend exception for `/inbox`; the BFF currently collapses non-auth backend failures into `{"error":"Failed to fetch inbox"}` with status `500`.

Authenticated checks also return `200` through the real frontend BFF path:

```bash
curl -s -i -c /tmp/waypoint_cookies.txt \
  -X POST http://localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  --data '{"email":"newuser@test.com","password":"testpass123"}'
# HTTP/1.1 200 OK

curl -s -i -b /tmp/waypoint_cookies.txt http://localhost:3000/api/auth/me
# HTTP/1.1 200 OK

curl -s -i -b /tmp/waypoint_cookies.txt \
  'http://localhost:3000/api/inbox?page=1&limit=1'
# HTTP/1.1 200 OK
# total: 1392
```

Direct backend verification with the extracted `access_token` cookie also returns `200`:

```bash
curl -s -i -H "Cookie: access_token=<token>" \
  'http://127.0.0.1:8000/inbox?page=1&limit=1'
# HTTP/1.1 200 OK
```

### `setInterval` Violation Noise

Static search found one real React hook misuse in the interval category:

- `frontend/src/app/(agency)/insights/page.tsx:96-103` used `useMemo` to start a `setInterval`.
- `Docs/frontend_component_architecture_audit_2026-05-08.md:399-401` calls out this exact side-effect-in-`useMemo` pattern as invalid.

Action taken:

- Changed `TimeRemaining` to use `useEffect` for the interval and cleanup in `frontend/src/app/(agency)/insights/page.tsx`.

Post-change verification:

```bash
cd frontend && npx tsc --noEmit
# passed

cd frontend && npm run build
# passed
```

Other inspected intervals already use effect/callback cleanup:

- `frontend/src/components/marketing/MarketingVisuals.tsx:53-62`
- `frontend/src/components/workspace/panels/IntakePanel.tsx:279-296`
- `frontend/src/app/(agency)/workbench/RunProgressPanel.tsx:91-102`

## Recommended Next Debug Step If It Recurs

1. Restart the frontend dev server to clear stale Turbopack/HMR state.
2. Hard refresh the browser.
3. If `/api/inbox` still returns `500`, capture the backend FastAPI stack trace for the matching `/inbox` request and test with authenticated cookies.

## Verification Commands Run

```bash
cd frontend && npx tsc --noEmit
cd frontend && npm run build
curl -s -i 'http://localhost:3000/api/inbox?page=1&limit=1'
curl -s -i 'http://127.0.0.1:8000/inbox?page=1&limit=1'
curl -s -i http://localhost:3000/api/auth/me
curl -s -i -c /tmp/waypoint_cookies.txt -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' --data '{"email":"newuser@test.com","password":"testpass123"}'
curl -s -i -b /tmp/waypoint_cookies.txt http://localhost:3000/api/auth/me
curl -s -i -b /tmp/waypoint_cookies.txt 'http://localhost:3000/api/inbox?page=1&limit=1'
```
