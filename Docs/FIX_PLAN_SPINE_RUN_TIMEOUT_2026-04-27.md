# Fix Plan: Process Trip 504 Timeout + Auth
## Waypoint OS — Singapore Scenario Test Blocker

**Date:** 2026-04-27
**Problem:** `POST /api/spine/run` returns 504 Gateway Timeout when user clicks "Process Trip" in Workbench
**Root Cause:** Multiple issues — see analysis below
**Status:** Planning

---

## Problem Analysis

### 1. Timeout Issue (Primary)

**What happens:**
1. User clicks "Process Trip" in Workbench
2. Frontend calls `POST /api/spine/run` (via Next.js proxy on :3000)
3. Next.js proxy forwards to FastAPI backend (`/run` on :8000)
4. Spine AI pipeline runs (can take 15-60 seconds)
5. Next.js proxy has `PROXY_TIMEOUT_MS = 10_000` (10 seconds)
6. Proxy aborts the request at 10s → returns 504 to browser

**Evidence:**
```
POST http://localhost:3000/api/spine/run 504 (Gateway Timeout)
Spine run failed: ApiException: The operation was aborted due to timeout
```

### 2. Auth Issue (Secondary)

**What happens:**
1. The `/run` endpoint in `spine_api/server.py` has NO auth requirement
2. It doesn't accept `agency` parameter
3. When `save_processed_trip()` is called, there's no `agency_id` passed
4. The created trip won't be scoped to the user's agency

**Evidence:**
```python
@app.post("/run", response_model=SpineRunResponse)
def run_spine(request: SpineRunRequest) -> SpineRunResponse:
    # No auth dependency
    # No agency parameter
```

### 3. Session Expiry (Contributing)

**What happens:**
1. User's access_token cookie expires (15-minute TTL)
2. Frontend shows 401 Unauthorized
3. AuthProvider redirects to login
4. User loses context

**Evidence:**
```
GET http://localhost:3000/api/auth/me 401 (Unauthorized)
```

---

## Proposed Fix (In Order)

### Phase 1: Fix Timeout (No Auth Changes Yet)

**Goal:** Make Process Trip not timeout

**Step 1.1:** Create dedicated Next.js route for `/api/spine/run`
- Path: `frontend/src/app/api/spine/run/route.ts`
- Use `proxyRequest` with `timeoutMs: 60_000`
- Modify `proxy-core.ts` to accept custom `timeoutMs` in `ProxyOptions`

**Step 1.2:** Ensure catch-all proxy doesn't intercept `/api/spine/run`
- Check `frontend/src/app/api/[...path]/route.ts`
- The explicit route `/api/spine/run` should take precedence over catch-all

**Step 1.3:** Verify timeout increase
- Backend `/run` endpoint should complete within 60s
- If spine pipeline takes >60s, need to investigate backend performance

### Phase 2: Fix Auth on /run Endpoint

**Goal:** Ensure processed trips are scoped to the logged-in user's agency

**Step 2.1:** Add auth to `/run` endpoint
```python
@app.post("/run", response_model=SpineRunResponse)
def run_spine(
    request: SpineRunRequest,
    agency: Agency = Depends(get_current_agency),
) -> SpineRunResponse:
```

**Step 2.2:** Pass agency_id to save_processed_trip
- Find where `save_processed_trip()` is called in the `/run` handler
- Add `agency_id=agency.id` parameter

**Step 2.3:** Update save_processed_trip signature
- Check `spine_api/persistence.py` `save_processed_trip()`
- Ensure it accepts and stores `agency_id`

### Phase 3: Test End-to-End

**Goal:** Verify the full flow works

**Step 3.1:** Login as real user
**Step 3.2:** Go to Workbench
**Step 3.3:** Paste Singapore scenario text
**Step 3.4:** Click Process Trip
**Step 3.5:** Wait for completion (should take 15-45s, not timeout)
**Step 3.6:** Check Inbox — trip should appear
**Step 3.7:** Verify trip is scoped to real user's agency (not test agency)

### Phase 4: Log UX Feedback

**Goal:** Document the "Agent Notes" label issue

**Observation:** "Agent Notes" doesn't resonate with agency owners
**Question:** What should it be called? "Call Notes"? "Internal Notes"? "Owner Notes"?
**Action:** Add to UX audit doc

---

## Files to Modify

| File | Change | Why |
|------|--------|-----|
| `frontend/src/lib/proxy-core.ts` | Add `timeoutMs` to `ProxyOptions` | Allow per-route timeout override |
| `frontend/src/app/api/spine/run/route.ts` | New file — dedicated proxy with 60s timeout | Fix 504 on Process Trip |
| `spine_api/server.py` | Add auth to `/run`, pass agency_id | Scope trips to user's agency |
| `spine_api/persistence.py` | Verify save_processed_trip accepts agency_id | Store trip with correct agency |

---

## Verification Checklist

- [ ] `/api/spine/run` responds within 60s without 504
- [ ] Created trip has correct `agency_id`
- [ ] Real user sees their own trip in Inbox
- [ ] Test user does NOT see real user's trip
- [ ] No 401 errors during the flow
- [ ] UX feedback logged

---

**Plan created:** 2026-04-27
**Next:** Execute Phase 1 (timeout fix)
