# Discussion: Fix Env Var Import-Time Caching

**Date:** 2026-05-04
**Context:** ISSUE-001 from random document audit of `Docs/ARCHITECTURE_DECISION_SPINE_API_2026-04-15.md`
**Previous work:** retention_consent agency/traveler boundary fix

## Problem

5+ locations in `spine_api/` read environment variables at **module import time** using `os.environ.get()`. This freezes the value for the entire process lifetime. Two concrete problems:

1. **Test isolation broken** — tests that monkeypatch `ENVIRONMENT`, `SPINE_API_DISABLE_AUTH`, or `TRIPSTORE_BACKEND` don't take effect because the module-level constant was already evaluated. Requires `importlib.reload()` or a separate process.

2. **Security bypass window** — `SPINE_API_DISABLE_AUTH` was checked at import time to decide whether to include `Depends(get_current_user)` on router dependencies. The lifespan handler (which runs later) had a safety check for production/staging, but it could NOT reapply auth dependencies that were already stripped at import time.

## Locations Fixed

| File | Before | After | Why |
|------|--------|-------|-----|
| `spine_api/core/auth.py` | No `_auth_or_skip` existed | Added `_auth_or_skip()` dependency that checks `SPINE_API_DISABLE_AUTH` at call time | Enables call-time auth bypass without import-time dependency stripping |
| `spine_api/routers/auth.py` | `_ENVIRONMENT` and `_COOKIE_SECURE` at module level | Call-time `_is_cookie_secure()` and inline `os.environ.get()` for development checks | Tests can now monkeypatch ENVIRONMENT for cookie-secure tests |
| `spine_api/core/rate_limiter.py` | `_ENVIRONMENT` defined at line 22 but never used anywhere | Removed (dead code) | Cleanup |
| `spine_api/server.py` (lines 465-472) | `[Depends(get_current_user)] if not os.environ.get("SPINE_API_DISABLE_AUTH") else []` — import-time check | Always `[Depends(_auth_or_skip)]` — call-time check | Security: auth deps are always registered; bypass is evaluated per-request |

## Architectural Pattern Change

**Before:**
```python
app.include_router(router, dependencies=(
    [Depends(get_current_user)] if not os.environ.get("SPINE_API_DISABLE_AUTH") else []
))
```
This freezes the auth decision at import time. If the env var changes after import, auth is still disabled.

**After:**
```python
app.include_router(router, dependencies=[Depends(_auth_or_skip)])

# In core/auth.py:
async def _auth_or_skip(request, credentials, db):
    if os.environ.get("SPINE_API_DISABLE_AUTH"):
        return None
    return await get_current_user(request, credentials, db)
```
The dep is always registered. The env var is checked on every request. Tests can toggle it freely.

For cookie security (auth router):
```python
# Before (import time):
_ENVIRONMENT = os.environ.get(...)
_COOKIE_SECURE = _ENVIRONMENT == "production"

# After (call time):
def _is_cookie_secure() -> bool:
    return os.environ.get("ENVIRONMENT", "development").lower() == "production"
```

## What Was NOT Changed

- **`_agent_work_coordinator` singleton** (server.py:245-248) — still reads `TRIPSTORE_BACKEND` at import time. This creates a module-level singleton that's passed to `AgentSupervisor`. Changing this requires lazy initialization of the supervisor, which is a larger refactor. Acceptable because: (a) the backend type shouldn't change mid-process, (b) tests that need a different backend can start a separate process.

- **`HOST`/`PORT`/`WORKERS`** (server.py:311-313) — these are server-startup configuration, only used in the `if __name__ == "__main__"` block (lines 4322-4324). Reading once at startup is correct.

- **`_get_default_limits()`** in rate_limiter.py — already reads at call time (correct pattern).

## Test Results

- Backend unit tests: **103 passed**
- Frontend unit tests: **664 passed** (1 pre-existing failure in overview page, unrelated)
- Zero regressions

## Files Changed

| File | Change |
|------|--------|
| `spine_api/core/auth.py:1,30-44` | Added `import os`, `_auth_or_skip()` call-time auth bypass |
| `spine_api/routers/auth.py:46-52` | Replaced `_ENVIRONMENT`/`_COOKIE_SECURE` with `_is_cookie_secure()` |
| `spine_api/routers/auth.py:72` | Cookie setter uses call-time `_is_cookie_secure()` |
| `spine_api/routers/auth.py:170` | Dev-test check uses call-time `os.environ.get()` |
| `spine_api/routers/auth.py:327` | Reset-token dev check uses call-time `os.environ.get()` |
| `spine_api/core/rate_limiter.py:22` | Removed dead `_ENVIRONMENT` |
| `spine_api/server.py:99` | Import `_auth_or_skip` from auth module |
| `spine_api/server.py:464-472` | Router deps use `Depends(_auth_or_skip)` always, no import-time conditional |

## Future Work

If test isolation for `TRIPSTORE_BACKEND` is needed later, the `_agent_work_coordinator` can be made lazy:

```python
_agent_work_coordinator: Optional[SQLWorkCoordinator] = None

def _get_work_coordinator() -> Optional[SQLWorkCoordinator]:
    global _agent_work_coordinator
    if _agent_work_coordinator is None and (
        os.environ.get("AGENT_WORK_COORDINATOR", "").lower() == "sql"
        or os.environ.get("TRIPSTORE_BACKEND", "").lower() == "sql"
    ):
        _agent_work_coordinator = SQLWorkCoordinator(lease_seconds=int(os.environ.get("AGENT_WORK_LEASE_SECONDS", "60")))
    return _agent_work_coordinator
```

This wasn't done now because it requires changing `AgentSupervisor`'s constructor to accept a lazy factory, which is a larger change with higher risk and lower payoff.
