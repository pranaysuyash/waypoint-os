# Audit + Implementation Session — 2026-05-04

**Session type**: Random document audit → immediate implementation  
**Audited doc**: `Docs/ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md`  
**Agent**: Claude Sonnet 4.6

---

## What Was Done

### Task 1: Fix frontier router cross-tenant injection (P0 security)

**File changed**: `spine_api/routers/frontier.py`  
**Test added**: `tests/test_frontier_tenant_isolation.py`

**Problem**: `GhostWorkflowCreate` and `EmotionalLogRequest` schemas contained `agency_id: str` as a request body field. Any authenticated user with a valid JWT could set `agency_id=<any-other-agency>` and read/write another tenant's ghost workflows and emotion logs.

**Root cause**: The router handlers used `request.agency_id` (caller-supplied) instead of injecting `agency_id` from the JWT-backed membership dependency.

**Fix**:
- Removed `agency_id` from `GhostWorkflowCreate` and `EmotionalLogRequest` schemas
- Added `agency_id: str = Depends(get_current_agency_id)` to all mutable route handlers
- `get_ghost_workflow` (GET by ID) now does an ownership check: `workflow.agency_id != agency_id → 404`
  - Returns 404, not 403, to avoid confirming whether the workflow exists for another tenant
- `report_intelligence` uses `_agency_id` (intentional discard) since the federated pool is cross-agency by design and uses `source_agency_hash` instead

**Auth context**: `SPINE_API_DISABLE_AUTH` check. Server.py already wraps frontier router with `Depends(get_current_user)` at router inclusion level. That handles authentication (JWT presence). The per-handler `get_current_agency_id` handles authorization (tenant scoping). These are two separate concerns at two levels.

---

### Task 2: Agent join flow — workspace code invite path

**Files changed/added**:
- `spine_api/services/auth_service.py` — added `validate_workspace_code()` and `join_with_code()`
- `spine_api/routers/auth.py` — added `GET /api/auth/validate-code/{code}` and `POST /api/auth/join` + `JoinRequest` model
- `frontend/src/app/api/auth/validate-code/[code]/route.ts` — BFF route (GET, public)
- `frontend/src/app/api/auth/join/route.ts` — BFF route (POST, public)
- `frontend/src/app/(auth)/join/[code]/page.tsx` — agent join page
- `tests/test_agent_join_flow.py` — 10 service tests, all passing

**Problem**: Agents had no way to join an existing agency. The backend team APIs existed (`/api/team/members`, `/api/team/invite`), governance-api.ts had client functions, but there was no invitation code flow. An owner could not onboard an agent without manually creating their account.

**Design decisions**:

1. **Codes are multi-use**: Invitation codes are reusable links, not one-time tokens. The owner generates a new code to invalidate the old one (existing `generate_workspace_code()` marks old codes replaced). This matches the roadmap's "regeneratable" model.

2. **Separate endpoint, not extended signup**: `POST /api/auth/join` is separate from `POST /api/auth/signup` because:
   - Different semantics (join existing vs create new agency)
   - Different validation (code required, no agency_name)
   - Different default role (junior_agent, not owner)
   - Keeps signup semantics clean

3. **Always junior_agent**: Both `internal` and `external` code types default to `junior_agent`. Owner/Admin promotes after onboarding review. Reasoning: safety first — better to under-privilege and promote than over-privilege and audit.

4. **Route placement**: New endpoints go under `/api/auth/` prefix. This prefix is on `PUBLIC_PREFIXES` in the FastAPI auth middleware, so no JWT is required — correct for pre-signup flows.

5. **404 for all invalid codes**: `validate_workspace_code` returns `ValueError("Invalid or expired invitation code")` for: not found, revoked (`status != "active"`), orphaned agency. Never distinguishes between these cases — avoids leaking code format/existence information.

**Frontend flow**:
```
User visits /join/WP-abc123
  → mount: GET /api/auth/validate-code/WP-abc123
    → success: show "Join Best Travels" + signup form
    → 404: show "Invalid invitation" error state
  → submit: POST /api/auth/join {workspace_code, email, password, name}
    → success: backend sets httpOnly cookies → hydrate() → /overview
    → error: inline error in form
```

**What's still missing** (not in this session):
- Owner/Admin UI to view and copy the workspace code (WorkspaceCodePanel component)
- Owner/Admin UI to generate a new code (revoke old one)
- `settings/people` page with TeamMemberList

---

## Architecture Research: Why middleware.ts Is Not Needed (Yet)

**Context**: The audit identified `middleware.ts` as missing. This was investigated and explicitly decided against. Future agents: read this section before re-opening this issue.

**The proxy confusion**: The catch-all BFF proxy at `/api/[...path]/route.ts` handles API routes (`/api/*`). It does NOT handle page routes (`/overview`, `/inbox`, `/workbench`). These are different concerns. Saying "the proxy handles auth" is partially correct only for API calls, not for page navigation.

**Why middleware.ts was not built**:

Next.js `middleware.ts` runs at the edge before any page renders. It could redirect unauthenticated users without the React flash that `AuthProvider` causes. However:

1. **access_token TTL is 15 minutes** (set in `spine_api/routers/auth.py:_ACCESS_TTL_SECONDS`). After 15 minutes, the httpOnly cookie expires and is removed from the browser.

2. **Middleware can only see access_token**, not refresh_token. The refresh_token has `path="/api/auth"`, meaning browsers only send it to `/api/auth/*` requests, not to page requests. The middleware running for `/inbox` would not see the refresh_token cookie.

3. **AuthProvider handles the refresh correctly**: It tries `/api/auth/me`, then `/api/auth/refresh` (which does see refresh_token at `/api/auth/refresh`), then retries `/api/auth/me`. This is the only correct flow.

4. **What middleware would break**: If middleware checks `access_token` presence and redirects when absent, it redirects users after every 15-minute token expiry before the refresh flow runs. Result: broken UX — users get kicked to login every 15 minutes.

5. **The right time to add middleware**: When/if token refresh is moved to a server-side mechanism (e.g., middleware makes a server-side call to `/api/auth/me`, or the access_token TTL is extended significantly). In those cases, a middleware presence check becomes viable.

**Current auth architecture is correct**:
- `AuthProvider` (client-side): hydrate → refresh → redirect if both fail. Handles expiry.
- FastAPI `AuthMiddleware` (backend): validates every API call. Authoritative.
- BFF proxy (`proxy-core.ts`): forwards cookies to FastAPI on every API request.
- `middleware.ts`: **not present, not needed** given current cookie architecture.

**Auth router docstring note**: The docstring says "enables Next.js middleware to authenticate page-route requests without client-side JavaScript." This was written as a future capability, not a current requirement. The cookie-only transport does make middleware possible in principle, but the 15-min TTL makes it unreliable without server-side refresh logic in the middleware itself.

---

## SPINE_API_DISABLE_AUTH — operational safety note

`spine_api/server.py:390` has a guard: if `ENVIRONMENT` is `production` or `staging`, setting `SPINE_API_DISABLE_AUTH` raises `RuntimeError` at startup. This was confirmed during the audit. The auth kill switch is safer than the test agent initially reported — it's blocked in production/staging at startup, not just at runtime. Development/test only.

Still recommended: rename to `SPINE_API_DEV_DISABLE_AUTH` for clarity. Not implemented in this session (out of scope of the 2-task focus).

---

## Test Environment Fix

The project uses `uv` with a `.venv`. Run tests as:
```bash
.venv/bin/python -m pytest tests/
```
Not `python -m pytest` — the system Python at `/opt/homebrew/bin/python` does not have the project's dependencies installed. The venv at `.venv/bin/python` has all deps including `sqlalchemy`, `bcrypt`, `asyncpg`, `pyjwt`.

This was the root cause of the 31 collection errors in the original audit baseline. All 19 new tests pass in the venv.

---

## Issues Confirmed by This Session

| Issue | Status | Notes |
|-------|--------|-------|
| ISSUE-001: Frontier cross-tenant injection | **Fixed** | `frontier.py` — agency_id now from JWT dep |
| ISSUE-002: SPINE_API_DISABLE_AUTH | Production guard exists; rename suggested | Not fixed this session |
| ISSUE-003: middleware.ts absent | **Won't fix** (with explanation) | AuthProvider + 15min TTL makes middleware unreliable |
| ISSUE-005: Phase 4 routing state machine | Open | Not started |
| ISSUE-006: Phase 2 onboarding UX | Open | Not started |
| ISSUE-007: Phase 3 Team UI | Partial | Join flow built; settings/people page not yet |
| ISSUE-009: Auth integration tests | Partially addressed | Schema + handler tests added; no live JWT round-trip tests yet |
| ISSUE-010: Test env broken | **Fixed** | Use `.venv/bin/python -m pytest` |

---

## Files Changed in This Session

```
spine_api/routers/frontier.py              — Task 1: cross-tenant fix
spine_api/services/auth_service.py        — Task 2: validate_workspace_code + join_with_code
spine_api/routers/auth.py                 — Task 2: validate-code + join endpoints

frontend/src/app/api/auth/validate-code/[code]/route.ts  — Task 2: BFF GET
frontend/src/app/api/auth/join/route.ts                  — Task 2: BFF POST
frontend/src/app/(auth)/join/[code]/page.tsx             — Task 2: join page

tests/test_frontier_tenant_isolation.py   — Task 1: 9 schema + signature tests
tests/test_agent_join_flow.py             — Task 2: 10 service unit tests
Docs/AUDIT_AND_IMPLEMENTATION_2026-05-04.md  — This doc
```

---

## Next Recommended Work Units

**P0 (done)**: Frontier cross-tenant — fixed.

**Next P1**: Auth integration tests — JWT round-trip, cross-tenant denial, role enforcement. These don't need a live DB if using FastAPI's TestClient with a real `AsyncSession` backed by SQLite in-memory. No tests currently prove auth middleware rejects tampered tokens or that Agency A cannot call Agency B's endpoints.

**Next P2 (team flow)**:
1. Settings/People page — show TeamMemberList + workspace code + regenerate button
2. WorkspaceCodePanel — copy/share/regenerate the workspace code (owner/admin only)

Both build on complete backend APIs and the join flow just shipped.
