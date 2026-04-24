# Auth & Identity System Deep Audit

**Date:** 2026-04-24  
**Auditor:** Hermes (systematic inspection)  
**Scope:** Full auth stack — Frontend UI → Next.js Proxy → spine-api Auth → Database  
**Method:** Code inspection, contract tracing, architecture review  

---

## Executive Summary

The auth system is **schizophrenic**: the backend has a production-grade JWT auth implementation with RBAC, PostgreSQL tenant models, and password reset flows. The frontend has polished auth UI and a Zustand store. But **the two halves are not wired together for actual API protection**, and **critical security gaps exist at every integration point**.

| Layer | Status | Verdict |
|-------|--------|---------|
| **Backend Auth (spine-api)** | Built but unused | 7/10 |
| **Frontend Auth UI** | Complete | 8/10 |
| **Frontend State Management** | Broken (no rehydration) | 3/10 |
| **Proxy / BFF Layer** | Missing auth forwarding | 2/10 |
| **Route Protection** | None | 0/10 |
| **API Security** | Completely open | 0/10 |
| **Tenant Isolation** | Schema exists, unused | 2/10 |

**Bottom line:** An attacker can read all trips, run the spine, and access any workspace data without credentials. A logged-in user loses their session on every page refresh. The auth system is a facade — it looks real but provides zero actual protection.

---

## 1. What Exists (The Good)

### 1.1 Backend Auth Implementation (spine-api)

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Auth routes | `spine-api/routers/auth.py` | Complete | signup, login, logout, me, refresh, password reset request/confirm |
| Auth service | `spine-api/services/auth_service.py` | Complete | bcrypt hashing, JWT create/refresh, password reset with SHA-256 token storage |
| Auth dependencies | `spine-api/core/auth.py` | Complete | `get_current_user`, `get_current_membership`, `get_current_agency_id`, `require_permission` |
| Security utils | `spine-api/core/security.py` | Complete | HS256 JWT, bcrypt (12 rounds), access + refresh tokens |
| Tenant models | `spine-api/models/tenant.py` | Complete | `User`, `Agency`, `Membership`, `WorkspaceCode`, `PasswordResetToken` |
| Database | `spine-api/core/database.py` | Complete | Async SQLAlchemy 2.0, PostgreSQL+asyncpg |
| Migrations | `alembic/versions/` | Complete | `init_tenant_schema`, `add_password_reset_tokens_table` |
| RBAC matrix | `spine-api/core/auth.py:119-138` | Complete | 5 roles: owner, admin, senior_agent, junior_agent, viewer |

**Evidence of quality:**
- Password reset tokens are hashed with SHA-256 before storage (not stored plain)
- Old reset tokens are invalidated on new request
- User existence is not revealed during password reset (returns same message either way)
- `Membership` has unique index on `(user_id, agency_id)` preventing duplicate memberships
- Role-based permissions are explicitly enumerated per role

### 1.2 Frontend Auth UI

| Page | File | Status |
|------|------|--------|
| Login | `frontend/src/app/(auth)/login/page.tsx` | Complete |
| Signup | `frontend/src/app/(auth)/signup/page.tsx` | Complete |
| Forgot Password | `frontend/src/app/(auth)/forgot-password/page.tsx` | Complete |
| Reset Password | `frontend/src/app/(auth)/reset-password/page.tsx` | Complete |
| Auth layout | `frontend/src/app/(auth)/layout.tsx` | Complete |

**Quality observations:**
- Proper form validation (minLength, required fields)
- Accessible labels and autocomplete attributes
- Error handling with `ApiException`
- Password confirmation matching on reset
- Loading states on all submit buttons

### 1.3 Frontend Auth Store

| Feature | Status |
|---------|--------|
| Login action | Stores user, agency, membership, token in Zustand |
| Logout action | Calls `/api/auth/logout` then clears state |
| Hydrate action | Calls `/api/auth/me` to restore from cookie |
| UserMenu component | Displays user initials, agency, role |

---

## 2. Critical Gaps (P0 — Production Blockers)

### 2.1 ZERO Authentication on Data API Routes

**Finding:** Not a single non-auth spine-api route requires authentication.

**Evidence:**
```bash
$ grep -rn "get_current_user\|require_auth\|require_permission" spine-api/server.py
# (no output)

$ grep -rn "get_current_user\|require_auth\|require_permission" spine-api/routers/workspace.py
# (no output)

$ grep -rn "get_current_user\|require_auth\|require_permission" spine-api/routers/frontier.py
# (no output)
```

**Affected endpoints (all completely open):**
- `POST /run` — Execute spine runs
- `GET /trips` — List all trips
- `GET /trips/{id}` — Get specific trip
- `GET /stats` — Dashboard statistics
- `GET /pipeline` — Pipeline data
- `POST /api/trips/{id}/review/action` — Review actions
- `POST /api/trips/{id}/override` — Submit overrides
- All workspace, frontier, settings, team endpoints

**Impact:** Any unauthenticated HTTP client can read all agency data, execute spine runs, and modify trips.

**Root cause:** The auth dependencies were built but never applied to routes. The server mounts auth router + workspace router + frontier router, but the data routes in `server.py` have no auth decorators.

---

### 2.2 Frontend Proxy Does NOT Forward Auth Credentials

**Finding:** Next.js API proxy routes for data do not send the access token to spine-api.

**Evidence from `/api/trips/route.ts`:**
```typescript
const response = await fetch(spineApiUrl, {
  method: "GET",
  headers: {
    "Content-Type": "application/json",  // ONLY this header
  },
});
```

Compare to `/api/auth/me/route.ts` which DOES forward auth:
```typescript
const headers: Record<string, string> = {
  'Content-Type': 'application/json',
};
if (cookie) headers['cookie'] = cookie;
if (authHeader) headers['authorization'] = authHeader;
```

**Inconsistency:** Auth routes forward credentials. Data routes do not. This means even if the user is logged in with a valid cookie, the spine-api receives no auth context for trip data requests.

**Affected proxy routes:** All non-auth routes in `frontend/src/app/api/` — trips, stats, pipeline, reviews, overrides, settings, team, insights, runs, scenarios, etc.

---

### 2.3 No Next.js Middleware for Route Protection

**Finding:** There is no `middleware.ts` in the frontend.

**Impact:**
- Anyone can directly visit `/overview`, `/workspace`, `/settings`, `/owner/reviews` without logging in
- The app shell renders for all routes except the hardcoded public pages in `Shell.tsx`
- No redirect to `/login` for unauthenticated users
- No role-based route guards (e.g., blocking `/owner/reviews` for junior agents)

**Evidence:**
```bash
$ find frontend/src -name "middleware.ts" -o -name "middleware.js"
# (no output)
```

The `Shell.tsx` component does check for public routes (lines 107-116) but this is client-side only. A direct URL visit to `/workspace` renders the full app shell with empty/null data.

---

### 2.4 Auth State Never Rehydrated = Broken Sessions

**Finding:** The `hydrate()` function in the auth store is defined but **never called anywhere in the codebase**.

**Evidence:**
```bash
$ grep -rn "hydrate()" frontend/src/ --include="*.tsx" --include="*.ts"
# (no output)
```

**Consequence flow:**
1. User logs in → Zustand stores token in memory
2. User refreshes page → Zustand state resets to initial values
3. `hydrate()` is NOT called → no request to `/api/auth/me`
4. `isAuthenticated` remains `false`
5. `user`, `agency`, `membership` are all `null`
6. `UserMenu` shows "U" initials and empty state
7. `api-client.ts` `getAuthToken()` reads `localStorage.getItem("access_token")` which is **never set by login**
8. All subsequent API calls are sent WITHOUT Authorization header

**This is a complete session brokenness bug.**

---

### 2.5 Token Storage Contract Contradiction

**Finding:** Three different token storage strategies are implemented simultaneously, creating a contradictions.

| Source | Claims | Reality |
|--------|--------|---------|
| `auth.ts` store comment | "Token storage is now cookie-based (httpOnly)" | Token stored in Zustand memory only |
| `auth.ts` `hydrate()` | Reads from httpOnly cookie via `/api/auth/me` | Never called |
| `api-client.ts` `getAuthToken()` | Reads from `localStorage` | localStorage is never written to |
| Login page | Stores token in Zustand via `login()` | Does NOT write to localStorage |
| Login proxy (`/api/auth/login/route.ts`) | Sets `access_token` as httpOnly cookie | Cookie IS set correctly |

**The result:** After login, the access token exists in three places with different lifetimes:
1. **Zustand memory** — lost on refresh
2. **httpOnly cookie** — survives refresh but never read by `hydrate()`
3. **localStorage** — empty (never written)

The `api-client` expects localStorage but login writes to Zustand. The auth store claims cookies but `hydrate()` is never invoked. This is an architectural contradiction that breaks all auth flows.

---

### 2.6 Cookie `secure=False` Hardcoded in Production

**Finding:** Backend auth routes set `secure=False` on cookies unconditionally.

**Evidence from `spine-api/routers/auth.py`:**
```python
response.set_cookie(
    key="refresh_token",
    value=result["refresh_token"],
    httponly=True,
    secure=False,  # <-- hardcoded
    samesite="lax",
    ...
)
```

**Impact:** In production (HTTPS), cookies will be sent over insecure connections. This enables session hijacking via man-in-the-middle attacks.

**Note:** The frontend proxy routes (`/api/auth/login/route.ts`) correctly use `secure: process.env.NODE_ENV === 'production'`, but the backend ignores this.

---

### 2.7 Password Reset Returns Plain Token in Production

**Finding:** `request_password_reset` returns the plain reset token in the JSON response.

**Evidence from `spine-api/services/auth_service.py:316`:**
```python
return {
    "ok": True,
    "message": "If the email exists, a reset link has been sent",
    "reset_token": plain_token,  # Remove in production (use email instead)
}
```

While the comment says "Remove in production," there is no environment check. This means anyone who knows a user's email can request a password reset and receive the token directly in the API response, bypassing email entirely.

---

## 3. High-Priority Gaps (P1)

### 3.1 No Tenant Isolation on Trip Endpoints

**Finding:** Even if auth were enforced, trip endpoints do not filter by `agency_id`.

**Evidence from `spine-api/server.py` (trip routes):**
- No `agency_id` parameter in trip query handlers
- No `get_current_agency_id` dependency injection
- `TripStore.get_trip()` does not validate tenant ownership

**Impact:** If auth were added today, any authenticated user from any agency could read all trips across all agencies.

---

### 3.2 No Rate Limiting on Auth Endpoints

**Finding:** Login, signup, and password reset endpoints have no rate limiting.

**Impact:**
- Brute-force password attacks are possible
- Email enumeration via timing or error messages (though reset is masked)
- Account creation abuse

---

### 3.3 CORS `allow_methods=["*"]` and `allow_headers=["*"]`

**Finding:** CORS is overly permissive.

**Evidence from `spine-api/server.py:201-207`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

While this is acceptable for development, it should be restricted in production.

---

### 3.4 JWT Secret Uses Weak Default

**Finding:** `JWT_SECRET` falls back to a hardcoded development secret.

**Evidence from `spine-api/core/security.py:17`:**
```python
JWT_SECRET = os.getenv("JWT_SECRET", "waypoint-dev-secret-change-in-production")
```

If `JWT_SECRET` is not set in production, an attacker can forge JWT tokens with the known default secret.

---

## 4. Frontend-Specific Issues

### 4.1 Auth Pages Use Inline Styles

**Finding:** The signup page uses inline styles for conditional UI.

**Evidence from `frontend/src/app/(auth)/signup/page.tsx:109`:**
```tsx
style={{ background: '#1c2128', color: '#8b949e' }}
```

This bypasses the design system and creates maintenance overhead.

### 4.2 Signup Button Shows Without Agency Field

**Finding:** The signup form has a "Customize agency name (optional)" button that reveals the agency field. But the main submit button is always visible. This is fine UX-wise but the conditional styling is inconsistent.

### 4.3 No Loading State on Hydrate

**Finding:** If `hydrate()` were called, there's no global loading state to prevent UI flicker while auth state is being determined.

---

## 5. Architecture Diagram: Current vs Intended

### Current (Broken)

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────┐
│   Browser   │────▶│  Next.js Proxy   │────▶│   spine-api     │────▶│  PostgreSQL  │
│             │     │  /api/trips      │     │  /trips         │     │          │
└─────────────┘     │  (NO auth sent)  │     │  (NO auth req)  │     └──────────┘
                    └──────────────────┘     └─────────────────┘
                           │
                    ┌──────────────────┐
                    │  /api/auth/login │────▶│  /api/auth/login  │
                    │  (sets cookie)   │     │  (sets cookie)    │
                    └──────────────────┘     └───────────────────┘
```

**Problem:** The auth path works in isolation, but the data path bypasses auth entirely.

### Intended (Fixed)

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────┐     ┌──────────┐
│   Browser   │────▶│  Next.js Middleware  │────▶│  Next.js Proxy      │────▶│ spine-api│
│  (cookie)   │     │  (redirect if no     │     │  (forwards cookie   │     │ (validate│
│             │     │   session)           │     │   + header)         │     │  JWT)    │
└─────────────┘     └──────────────────────┘     └─────────────────────┘     └────┬─────┘
                                                                                   │
                                                                            ┌──────┴──────┐
                                                                            │  PostgreSQL  │
                                                                            │ (tenant-scoped│
                                                                            │   queries)   │
                                                                            └─────────────┘
```

---

## 6. Fix Priority Matrix

### P0 — Fix Before ANY Production Deployment

| # | Issue | Files to Change | Effort |
|---|-------|-----------------|--------|
| 1 | Add `require_auth` to ALL non-public spine-api routes | `spine-api/server.py`, `spine-api/routers/*.py` | 2-3 hours |
| 2 | Forward auth cookies/headers in ALL Next.js proxy routes | `frontend/src/app/api/**/route.ts` | 2-3 hours |
| 3 | Create `frontend/src/middleware.ts` for route protection | New file | 1-2 hours |
| 4 | Call `hydrate()` on app mount + fix token storage contract | `frontend/src/app/layout.tsx`, `frontend/src/stores/auth.ts`, `frontend/src/lib/api-client.ts` | 2-3 hours |
| 5 | Make cookie `secure` flag environment-aware | `spine-api/routers/auth.py` | 30 min |
| 6 | Remove or gate `reset_token` from password reset response | `spine-api/services/auth_service.py` | 30 min |

### P1 — Fix Before Beta

| # | Issue | Files to Change | Effort |
|---|-------|-----------------|--------|
| 7 | Add tenant isolation (agency_id filtering) to all data queries | `spine-api/persistence.py`, `spine-api/server.py` | 4-6 hours |
| 8 | Add rate limiting to auth endpoints | `spine-api/routers/auth.py` or middleware | 2 hours |
| 9 | Restrict CORS in production | `spine-api/server.py` | 30 min |
| 10 | Enforce `JWT_SECRET` env var (fail startup if default) | `spine-api/core/security.py` | 30 min |
| 11 | Add auth provider component with loading state | `frontend/src/components/providers/AuthProvider.tsx` | 1-2 hours |

### P2 — Hardening

| # | Issue | Files to Change | Effort |
|---|-------|-----------------|--------|
| 12 | Add refresh token rotation | `spine-api/services/auth_service.py` | 2 hours |
| 13 | Add CSRF protection for cookie-based auth | `spine-api/core/auth.py` | 2 hours |
| 14 | Add audit logging for auth events | `spine-api/services/auth_service.py` | 2 hours |
| 15 | Remove inline styles from auth pages | `frontend/src/app/(auth)/**/*.tsx` | 1 hour |

---

## 7. Specific Code Fixes (Ready to Implement)

### 7.1 Fix: Add Auth to spine-api Routes

In `spine-api/server.py`, import and apply auth to all data routes:

```python
from core.auth import get_current_user, get_current_agency_id, require_auth

# Example for /trips route
@app.get("/trips")
async def get_trips(
    agency_id: str = Depends(get_current_agency_id),  # Add this
    # ... existing params
):
    # Filter by agency_id
    trips = TripStore.get_trips_for_agency(agency_id)
    # ...
```

### 7.2 Fix: Forward Auth in Next.js Proxy

Create a shared helper in `frontend/src/lib/proxy-utils.ts`:

```typescript
export function buildProxyHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  const cookie = request.headers.get('cookie');
  if (cookie) headers['cookie'] = cookie;
  
  const authHeader = request.headers.get('authorization');
  if (authHeader) headers['authorization'] = authHeader;
  
  return headers;
}
```

Use it in every proxy route.

### 7.3 Fix: Create middleware.ts

```typescript
import { NextResponse } from 'next/server';
import type { NextRequest };

const PUBLIC_PATHS = ['/', '/login', '/signup', '/forgot-password', '/reset-password', '/itinerary-checker'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  if (PUBLIC_PATHS.includes(pathname)) return NextResponse.next();
  
  const token = request.cookies.get('access_token')?.value;
  if (!token) {
    return NextResponse.redirect(new URL('/login?redirect=' + encodeURIComponent(pathname), request.url));
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

### 7.4 Fix: Unify Token Storage

**Option A (Recommended): Cookie-only**
- Remove `getAuthToken()` from `api-client.ts`
- Remove `token` from Zustand auth store
- Keep access token in httpOnly cookie only
- Frontend proxy routes automatically include cookies in requests to spine-api
- `api-client.ts` relies on cookies being sent automatically by browser

**Option B (Hybrid): Cookie + Memory**
- Keep access token in httpOnly cookie
- Zustand store holds user/agency/membership but NOT token
- On app mount, call `hydrate()` which hits `/api/auth/me`
- `api-client.ts` removes `getAuthToken()` and `Authorization` header injection
- Rely on cookie forwarding through proxy layer

**Recommendation: Option A** — It's simpler, more secure (no token in JS memory), and aligns with the existing cookie infrastructure. The only requirement is that proxy routes forward cookies, which they should do anyway.

---

## 8. Verification Steps

After implementing fixes, verify:

1. **Unauthenticated access blocked:**
   ```bash
   curl http://localhost:8000/trips
   # Should return 401 Unauthorized
   ```

2. **Auth forwarding works:**
   ```bash
   # Login
   TOKEN=$(curl -s -X POST http://localhost:3000/api/auth/login -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"password123"}' | jq -r '.access_token')
   
   # Access trips through proxy
   curl http://localhost:3000/api/trips -H "Authorization: Bearer $TOKEN"
   # Should return trips
   ```

3. **Middleware redirects:**
   ```bash
   curl -I http://localhost:3000/workspace
   # Should return 307 redirect to /login
   ```

4. **Session survives refresh:**
   - Log in
   - Refresh page
   - UserMenu should still show name/initials
   - Network tab should show `/api/auth/me` called on mount

5. **Tenant isolation:**
   - Create user A with agency A
   - Create user B with agency B
   - User A's trips should not appear in User B's `/api/trips`

---

## 9. Related Documents

- `Docs/ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md` — Implementation roadmap (this audit supersedes the "is auth done?" question)
- `Docs/FRONTEND_SECURITY_QUALITY_AUDIT_2026-04-18.md` — Prior security audit (flagged missing auth as FAIL)
- `Docs/DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md` — Auth identity discovery gap
- `Docs/WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md` — Workspace governance roadmap

---

*Audit complete. This is a P0-blocking issue for any production deployment. The auth infrastructure exists but is completely un wired to the actual API surface.*
