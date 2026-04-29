# Auth & Identity System Review

- Date: 2026-04-29
- Reviewed doc: [Docs/AUTH_IDENTITY_SYSTEM_AUDIT_2026-04-24.md](../AUTH_IDENTITY_SYSTEM_AUDIT_2026-04-24.md)

## Scope

This review uses the audit as a starting point, but prioritizes the current implementation state.

## Findings

- The old headline is stale: auth wiring now exists across backend, frontend, proxy, and route protection.
- `spine_api/routers/auth.py` sets cookie-only auth transport and supports signup, login, refresh, and password reset.
- `spine_api/core/auth.py` now enforces JWT validation and role-based agency scoping.
- `frontend/src/components/auth/AuthProvider.tsx`, `frontend/src/stores/auth.ts`, and `frontend/src/proxy.ts` are wired for hydrate/redirect/protected-route behavior.
- The real current gaps are hardening issues:
  - `spine_api/core/security.py` still falls back to a dev JWT secret.
  - No auth rate limiting exists in `spine_api`.
  - Password reset still returns the plain reset token in the API response for now.

## Evidence

- `spine_api/server.py:304-354`
- `spine_api/routers/auth.py:39-79, 120-233, 249-328`
- `spine_api/core/auth.py:26-189`
- `spine_api/core/security.py:17-18, 38-91`
- `frontend/src/components/auth/AuthProvider.tsx:23-56`
- `frontend/src/stores/auth.ts:67-105`
- `frontend/src/proxy.ts:49-108`
- `frontend/src/app/(auth)/login/page.tsx:18-45`
- `frontend/src/app/(auth)/signup/page.tsx:21-45`
- `tests/test_catchall_auth_proxy.py`

## Immediate next implementation slice

1. Require `JWT_SECRET` at startup instead of using the dev fallback.
2. Remove or gate `reset_token` from password-reset responses outside local testing.
3. Add rate limiting to auth endpoints.
4. Refresh the stale audit doc so it reflects the current wired state.

## References

- `Docs/AUTH_IDENTITY_SYSTEM_AUDIT_2026-04-24.md`
- `spine_api/server.py`
- `spine_api/routers/auth.py`
- `spine_api/core/auth.py`
- `spine_api/core/security.py`
- `spine_api/services/auth_service.py`
- `frontend/src/components/auth/AuthProvider.tsx`
- `frontend/src/stores/auth.ts`
- `frontend/src/proxy.ts`
