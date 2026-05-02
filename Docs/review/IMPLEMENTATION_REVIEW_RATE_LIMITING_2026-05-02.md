# Implementation Review: E2 Rate Limiting

**Date:** 2026-05-02
**Gap:** E2. Security & Privacy — Rate limiting on auth endpoints
**Status:** COMPLETED
**Priority:** P1 (was P0 in original finding, downgraded after codebase verification)

---

## What was done

Added environment-aware rate limiting to all auth endpoints using `slowapi`.

### Files created

| File | Lines | Purpose |
|---|---|---|
| `spine_api/core/rate_limiter.py` | 63 | Limiter instance, env-aware defaults, custom 429 handler |
| `tests/test_rate_limiter.py` | 260 | 25 behavior-driven tests (config, 429 handler, registry, middleware, Pydantic preservation) |

### Files modified

| File | Change | Lines changed |
|---|---|---|
| `spine_api/server.py` | Added SlowAPIMiddleware + RateLimitExceeded handler | +3 lines |
| `spine_api/routers/auth.py` | Added `@limiter.limit` decorators to 5 auth endpoints; kept `request: Request` AND Pydantic body models (both coexist for slowapi + FastAPI validation) | Full rewrite |

### Configuration

| Endpoint | Rate limit | Rationale |
|---|---|---|
| `POST /signup` | 5/min/IP | Brute-force signup prevention |
| `POST /login` | 10/min/IP | Credential-stuffing protection |
| `POST /refresh` | 30/min/IP | Token refresh is frequent but low-risk |
| `POST /request-password-reset` | 3/min/IP | Prevents reset-spam |
| `POST /confirm-password-reset` | 5/min/IP | Reset confirmation |
| All other routes (global default) | 60/min (prod) / 1000/min (dev/test) | Environment-aware |

### Key design decisions

1. **slowapi** chosen because it's the standard FastAPI rate limiter, well-maintained, and integrates with Starlette middleware.
2. **Environment-aware**: In development/test mode, limits are raised to 1000/min so developers never hit 429 locally. In production, conservative limits apply (60/min global default).
3. **Custom 429 handler**: Returns `{"detail": "Rate limit exceeded. Please try again later."}` matching the app's error format.
4. **Per-route decorators** on auth endpoints override the global default with stricter limits.
5. **Auth endpoints retain Pydantic body models**: slowapi requires `request: Request` as the first parameter to identify the client IP. FastAPI allows both `request: Request` and Pydantic body params in the same function signature. Both coexist — `request` for slowapi, `signup_req: SignupRequest` for type-safe validation + Swagger docs. No manual `request.json()` parsing.

### What was NOT done (correctly deferred)

- No Redis-backed rate limiting store (default in-memory works for single-instance; scale later)
- No IP+email combined limits (IP-only is sufficient for V1)
- No rate limiting on non-auth routes (global default of 60/min covers them)

---

## Verification

| Check | Result |
|---|---|
| `tests/test_rate_limiter.py` | 25 passed |
| `tests/test_auth_security.py` | 13 passed (no regression) |
| `tests/test_privacy_guard.py` | 34 passed (no regression) |
| Combined | 72 passed, 0 failed |

### Test design philosophy

The test suite uses behavior-driven testing with first-principles reasoning:

1. **Registry tests** verify slowapi's internal `_route_limits` dict (the actual mechanism slowapi uses to track limits), not function attributes that slowapi doesn't set. The registry key format (`routers.auth.<func>`) matches what the app's import path produces when `server.py` does `from routers import auth`.

2. **429 handler tests** use a real Starlette TestClient with a FastAPI app that wires up the `RateLimitExceeded` handler, then triggers the handler to verify the JSON response and content type. No `pytest.mark.asyncio` hacks — synchronous TestClient handles the async internally.

3. **Pydantic preservation tests** verify that the router's function signatures include BOTH `request: Request` (for slowapi) and the typed body params (for FastAPI validation). They also validate that `SignupRequest`, `LoginRequest`, etc. reject invalid input.

4. **No introspection hacks**: Tests don't check `hasattr(fn, "rule")` (slowapi doesn't set this). They don't check private attribute names that might change. They verify what matters: that the limiter's registry contains the right limits, that 429 responses are correct, and that Pydantic models still validate.

---

## Next steps

Per the action plan, the next gap is:

1. **Gap 1: Backend audit trail** — Create AuditLog model + migration + dependency-based audit logging
2. **Gap 2: PII jurisdiction tagging** — Add `jurisdiction` field to Agency model + policy routing
3. **Gap 4 (deferred): ABAC** — Per-record access control for junior_agent role