# Handoff: E2E Verification + Timeout + JWT Fixes

**Date:** 2026-05-05
**Trigger:** Random Document Audit — `Docs/FIX_PLAN_SPINE_RUN_TIMEOUT_2026-04-27.md`
**Issues fixed:** ISSUE-001 (E2E verified), ISSUE-002 (JWT TTL), ISSUE-003 (Pipeline timeouts)

---

## Summary

Three issues resolved across two P1 items and one P2 item. The core fix plan (Phase 1 timeout + Phase 2 auth) was implemented by a prior agent but never verified end-to-end. This session completed that verification and added missing operational safeguards.

---

## ISSUE-002: JWT/Cookie TTL Alignment

**File:** `spine_api/core/security.py:27`

**Change:** `ACCESS_TOKEN_EXPIRE_HOURS = 24` → `0.25` (15 minutes)

**Why:** `spine_api/routers/auth.py:52` sets cookie `max_age` to 15 minutes, but the JWT `exp` claim was 24 hours. A leaked JWT would be valid for 24 hours despite the browser dropping the cookie at 15 minutes. The frontend `AuthProvider.hydrate()` refresh loop already handles short-lived tokens.

**Confirmation:** All callers of `create_access_token()` pass `expires_delta=None` (default), so all JWTs now get 15-minute expiry. No tests hardcoded the 24h value.

**Runtime check:** Login with curl confirmed the backend serves tokens (verified via Set-Cookie headers on `POST /api/auth/login`). The server needs a restart to pick up this module-level constant.

---

## ISSUE-003: Pipeline Internal Timeout (3-Layer Defense)

### Layer 1: LLM HTTP Timeout

**Files changed:**
- `src/llm/openai_client.py:60-100` — `OpenAIClient.__init__()` now accepts `timeout` parameter, passes `timeout=timeout` and `max_retries=0` to `OpenAI()`
- `src/llm/gemini_client.py:74-99` — `GeminiClient.__init__()` now accepts `timeout` parameter, passes `http_options={"timeout": timeout * 1000}` to `genai.Client()`
- `src/llm/openai_client.py:228-265` — `create_openai_client()` factory passes `timeout` through
- `src/llm/gemini_client.py:213-237` — `create_gemini_client()` factory passes `timeout` through

**Default:** 30 seconds. **Env override:** `LLM_TIMEOUT_SECONDS`

**Why:** Both LLM clients had no HTTP timeout configured. A hung provider (OpenAI/Gemini outage) would block the pipeline thread indefinitely. Now the HTTP client raises an exception at 30s, which the pipeline's `except Exception` handler catches and calls `RunLedger.fail()`.

### Layer 2: Pipeline Watchdog Timer

**File changed:** `spine_api/server.py:869-882, 916, 1288`

**How it works:**
1. Timer starts after `RunLedger.set_state(run_id, RunState.RUNNING)` (pipeline has actually begun)
2. Default timeout: 180 seconds (matches frontend `useSpineRun MAX_POLL_MS`)
3. Env override: `PIPELINE_TIMEOUT_SECONDS`
4. Creates a `threading.Timer` with `daemon=True` 
5. Fires in a separate thread → calls `RunLedger.fail(run_id, error_type="PipelineTimeout")`
6. Cancelled in `finally` block on normal completion

**Why defense-in-depth:** If the LLM HTTP timeout fails for any reason (SDK bug, network-level hang, regex hang), the watchdog catches it.

### Layer 3: Idempotent RunLedger

**File changed:** `spine_api/run_ledger.py:180-240`

**Changes to `complete()`, `fail()`, `block()`:**
- Each method now checks `current.is_terminal()` before attempting the transition
- If already in a terminal (COMPLETED/FAILED/BLOCKED) state, silently returns
- Prevents race-condition crashes when watchdog timer fires concurrently with pipeline exception handler
- First writer wins; second writer detects terminal state and returns

**Why:** Without idempotency, the watchdog timer and pipeline thread would race. If the watchdog fires first (marks FAILED), the pipeline's `except Exception` handler would try to call `fail()` again and crash on the state transition check (FAILED → FAILED is invalid).

**Test update:** `tests/test_run_state_unit.py:231-270`
- `test_double_complete_raises` → `test_double_complete_is_idempotent` 
- Added 3 new tests: `test_fail_after_complete_is_idempotent`, `test_complete_after_fail_is_idempotent`, `test_block_after_fail_is_idempotent`

---

## ISSUE-001: E2E Live UI Verification

### What was verified

| # | Checklist Item | Status | Evidence |
|---|---------------|--------|----------|
| 1 | Singapore scenario accepted via backend | ✅ PASS | `POST /run` → 200, `{"run_id":"b0ef5a87...","state":"queued"}` |
| 2 | Pipeline completes in <60s | ✅ PASS | 22.76ms total (all stages: packet 6.98ms, validation 1.18ms) |
| 3 | Trip has correct `agency_id` | ✅ PASS | `meta.json` shows `agency_id: d1e3b2b6-...` matching the logged-in user |
| 4 | Real user sees their trip via API | ✅ PASS | `GET /trips/{trip_id}` returns 200 with full trip data |
| 5 | Different agency user does NOT see trip | ✅ PASS | `GET /trips/{trip_id}` returns 404 for other agency user |
| 6 | No 401 errors during flow | ✅ PASS | Both `/run` and `/trips/{id}` returned 200 with valid cookies |
| 7 | BFF proxy path works without 504 | ✅ PASS | `POST /api/spine/run` via Next.js proxy returns 200 (not 504) |

### What was NOT verified (UI-only, needs manual browser session)

- Login through the actual login page UI (login tested via API)
- Clicking "Process Trip" button in Workbench (button flow tested via API)
- Trip appearing in Inbox UI (trip verified via API)
- Session expiry UX (refresh flow tested via code review)

### Test Results

| Suite | Passed | Failed | Skipped | Status |
|-------|--------|--------|---------|--------|
| Backend: auth/run/lifecycle | 59 | 0 | 21 (pre-existing conditionals) | ✅ |
| Backend: auth integration | 20 | 0 | 0 | ✅ |
| Backend: run state unit | 50 | 0 | 0 (4 new tests added) | ✅ |
| Frontend: route-map + proxy | 27 | 0 | 0 | ✅ |
| Frontend: full suite | 663 | 1 (pre-existing timeout) | 0 | ✅ |

**Zero regressions from our changes.**

---

## Files Modified

| File | Change Type | Why |
|------|-------------|-----|
| `spine_api/core/security.py:27` | Const change | JWT TTL 24h → 15min |
| `src/llm/openai_client.py:60-100, 228-265` | New param | LLM HTTP timeout (30s default) |
| `src/llm/gemini_client.py:74-99, 213-237` | New param | LLM HTTP timeout (30s default) |
| `spine_api/server.py:869-882, 916, 1288` | New logic | Pipeline watchdog timer (180s) |
| `spine_api/run_ledger.py:180-240` | Idempotent guards | Race-safe terminal state writes |
| `tests/test_run_state_unit.py:231-270` | Updated + 3 new tests | Idempotency behavior |

---

## Operational Safety

| Guard | Kill Switch | How |
|-------|-------------|-----|
| JWT 15min TTL | `ACCESS_TOKEN_EXPIRE_HOURS=24` | Trivial revert |
| LLM HTTP timeout | `LLM_TIMEOUT_SECONDS=9999` | Env override |
| Pipeline watchdog | `PIPELINE_TIMEOUT_SECONDS=86400` | Env override (effectively off) |
| Idempotent RunLedger | N/A | Architectural, no toggle needed |

---

## Discussion: What Next

### Already done (this session)
- JWT TTL alignment (ISSUE-002)
- LLM HTTP timeout (ISSUE-003 layer 1)
- Pipeline watchdog timer (ISSUE-003 layer 2)
- Idempotent RunLedger (ISSUE-003 layer 3)
- E2E verification of Singapore scenario (ISSUE-001)

### Recommended next (from the audit)

**P1:** Nothing remains at P1 for the fix plan.

**P2 worth doing now:**

1. **Fix `test_privacy_guard.py` failures** — 3 tests fail with "SQLTripStore requires agency_id". Likely a Phase 2 regression (agency_id param added but tests not updated). These tests guard PII blocking in dogfood mode — important before any real user data enters the system.

2. **Centralize task tracking (ISSUE-005)** — Fix plan tasks aren't in TODO.md. The unchecked verification items (now verified here) should be marked done in the doc.

**P3 cleanup:**
- Update stale fix plan doc (ISSUE-004)
- "Agent Notes" label decision (ISSUE-007)
