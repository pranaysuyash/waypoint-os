# AUTH-01 Verification Report: proxy.ts Request-Boundary Auth Guard

**Date**: 2026-04-26
**Status**: ✅ COMPLETE — Runtime verified with evidence
**Next**: AUTH-02 may proceed

---

## What Was Confused

The 2nd agent (this session's initial work):
1. Assumed `proxy.ts` was not running as Next.js middleware because it wasn't imported anywhere
2. Created `middleware.ts` to "wire it up" — broke the build with "Both middleware file and proxy file detected"
3. Panicked about named vs default export, edge runtime vs node runtime

**Root cause**: Wrong mental model. `proxy.ts` is a **file-system convention** in Next.js 16 — it is auto-discovered by Next.js at the correct path (`src/proxy.ts` when using `src` layout). It does NOT need to be imported.

---

## Verification Evidence

### 1. Build Evidence

```bash
cd frontend && npx next build
```

**Result**: Build succeeds. Output shows:

```
ƒ Proxy (Middleware)
```

This is explicit confirmation that Next.js 16 discovers `proxy.ts` as the request-boundary handler.

### 2. File Placement

| File | Status |
|---|---|
| `frontend/src/proxy.ts` | ✅ Exists, at correct Next.js 16 convention path |
| `frontend/src/middleware.ts` | ✅ Does NOT exist (deleted after build error) |

### 3. Export Shape

`proxy.ts` exports:
```typescript
export default function proxy(request: NextRequest) { ... }
export { proxy as proxy };  // named re-export for tests
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon\\.ico).*)'],
};
```

**Valid per Next.js 16**: Either default export or named `export function proxy(...)` is accepted. The config object with matcher is correct.

### 4. Runtime Verification (All Passed)

| # | Test | Expected | Actual |
|---|---|---|---|
| 1 | `curl http://localhost:3000/workspace` (no cookies) | 307 → /login | **✅ 307 Location: /login?redirect=%2Fworkspace** |
| 2 | `curl http://localhost:3000/login` (no cookies) | 200, no redirect | **✅ 200, no redirect** |
| 3 | `curl http://localhost:3000/signup` (no cookies) | 200, no redirect | **✅ 200, no redirect** |
| 4 | `curl http://localhost:3000/workspace` (with auth cookies) | 200, allowed | **✅ 200** |
| 5 | `curl http://localhost:3000/login` (with auth cookies) | 307 → /overview | **✅ 307 Location: /overview** |
| 6 | `curl http://localhost:3000/favicon.ico` | 200, passthrough | **✅ 200** |
| 7 | `curl http://localhost:3000/api/auth/me` (no cookies) | 401 from backend | **✅ 401** |

**Interpretation**: The proxy.ts runs BEFORE page rendering for matched routes. Unauthenticated users are redirected at the request boundary before any React component mounts. Authenticated users pass through. Static assets and API routes are excluded by matcher logic and `isAllowed()` checks.

### 5. Cookie-Based Auth Verified

Login endpoint at `POST /api/auth/login` with body `{"email":"newuser@test.com","password":"testpass123"}` returns:

```json
{
  "ok": true,
  "user": { "id": "...", "email": "newuser@test.com", "name": "New User" },
  "agency": { "id": "...", "name": "Test", "slug": "test" },
  "membership": { "role": "owner", "is_primary": true }
}
```

Cookies set by backend:
- `access_token` (httpOnly, path=/, 15min TTL)
- `refresh_token` (httpOnly, path=/api/auth, 7day TTL)

The proxy.ts reads `cookies.get('access_token')` and `cookies.get('refresh_token')` — this works because both cookies are on the same origin (localhost:3000), and the proxy (running on Next.js dev server :3000) can see all cookies.

### 6. Test Evidence

```bash
cd frontend && npm test -- --run src/__tests__/proxy.test.ts
```

```
✓ src/__tests__/proxy.test.ts (12 tests) 8ms
Test Files  1 passed (1)
Tests  12 passed (12)
```

**Note**: The existing 12 tests are unit tests for the `proxy()` function logic (redirects, public page passthrough, safe redirect validation). They do NOT test the Next.js matcher/runtime integration. The runtime verification (curl tests above) is the actual proof.

---

## Architecture Confirmed (Corrected Understanding)

### Request Flow (Authenticated User)

```
Browser → GET /workspace
  ↓
Next.js proxy.ts (request boundary)
  ├─ checks cookies → access_token found → passes through
  ↓
Page renders (/workspace/page.tsx)
  ↓
AuthProvider hydrates (client-side)
  ├─ calls /api/auth/me with cookies
  ├─ gets user data
  └─ sets isAuthenticated=true
  ↓
Components render with auth state
  ↓
Data fetching happens (useTrips, etc.)
  ↓
BFF routes (/api/trips, etc.) forward to FastAPI
  ↓
FastAPI AuthMiddleware validates JWT
  ├─ extracts access_token from cookie
  ├─ decodes + verifies
  └─ sets request.state.user
```

### Request Flow (Unauthenticated User)

```
Browser → GET /workspace
  ↓
Next.js proxy.ts (request boundary)
  ├─ checks cookies → no access_token, no refresh_token
  └─ 307 Redirect → /login?redirect=%2Fworkspace
  ↓
Browser follows redirect, renders /login page
  ↓
AuthProvider hydrates (client-side)
  ├─ calls /api/auth/me without cookies
  ├─ gets 401
  └─ sets isAuthenticated=false
  ↓
Login form renders, no flash of workspace content
```

### Why This Is Correct

- **No FOUC (Flash of Unauthenticated Content)**: The server-side redirect happens before React mounts. Users NEVER see a protected page flash before being redirected.
- **Defense-in-depth**: proxy.ts (server-side) + AuthProvider (client-side) + AuthMiddleware (backend). Each layer validates independently.
- **Zero localStorage**: All auth state is cookie-based (httpOnly). No XSS token theft risk.

---

## Wording Correction Applied

**Do NOT say**: "edge runtime"  
**Do say**: "request-boundary execution before page render"

The runtime label (edge vs node) is irrelevant for auth guarding. What matters is that proxy.ts runs BEFORE the route/page handler, so protected content is never served to unauthenticated users.

---

## Files Changed in This Session

| File | Change | Evidence |
|---|---|---|
| `frontend/src/proxy.ts` | Restored `export default function proxy()` + `export const config` | Build: `ƒ Proxy (Middleware)`, Runtime curl tests all pass |
| `frontend/src/middleware.ts` | **DELETED** | `ls` confirms it does not exist |
| `frontend/src/__tests__/proxy.test.ts` | **UNCHANGED** | 12 tests still pass |

No production code was broken. The auth guard was already working; the confusion was about understanding the Next.js 16 convention.

---

## VERDICT

**AUTH-01: COMPLETE**

- ✅ proxy.ts is at the correct Next.js 16 convention path (`frontend/src/proxy.ts`)
- ✅ middleware.ts does not exist (no conflict)
- ✅ Build passes with `ƒ Proxy (Middleware)`
- ✅ Unauthenticated /workspace → 307 redirect to /login
- ✅ Unauthenticated /login → 200 (no redirect loop)
- ✅ Authenticated /workspace → 200 (allowed through)
- ✅ Authenticated /login → 307 redirect away to /overview
- ✅ Static assets excluded from matcher
- ✅ API routes passthrough (not redirected by proxy)
- ✅ Cookie-based auth verified (httpOnly, same-origin)
- ✅ 12 unit tests passing

**AUTH-02 may proceed.**

---

## What Was Wrong Before

| Wrong Assumption | Correct Fact |
|---|---|
| "proxy.ts is dead code because it isn't imported" | It is a **file-system convention**, auto-discovered by Next.js 16 |
| "Need middleware.ts to wire it up" | Next.js 16 deprecated middleware.ts; proxy.ts IS the entrypoint |
| "Named export might not work; need default export" | Both work. Named `export function proxy()` is explicitly documented as valid |
| "It runs in edge runtime" | Runtime label irrelevant; it runs at request-boundary before page render |
| "AuthProvider is the only auth defense" | proxy.ts is the **first** defense (server-side redirect), AuthProvider is the **second** (client-side), AuthMiddleware is the **third** (backend API validation) |

---

## What Needs No Further Change

- `proxy.ts` export shape is valid
- `proxy.ts` file placement is correct
- `proxy.ts` matcher pattern is correct
- Cookie-based auth is verified working

What might be needed later (not AUTH-01 scope):
- Enhanced matcher for `/workspace/*` nested paths (wildcard already covered by `.*` in regex)
- Additional test files for runtime matcher behavior (not unit tests)
- Header-based debug logging (optional, dev-only)

---

*Document written after runtime verification. All claims backed by curl output, build logs, and test results.*
