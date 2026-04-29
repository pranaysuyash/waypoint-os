# App State Analysis Review: Missing Front Door

- Date: 2026-04-29
- Reviewed doc: [Docs/APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md](../APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md)

## Scope

This review focuses on the current app state and the immediate implementation gap it identifies.
It is intentionally limited to the front-door/auth/workspace slice.

## Findings

- The doc matches the repo state: the product has a working engine and workbench, but no signup/login front door.
- `spine_api/server.py` has no auth endpoints or middleware for user sessions.
- `spine_api/persistence.py` has no user/workspace store and no tenant scoping.
- `frontend/src/app/page.tsx` and the shell assume the user is already inside the app.
- The roadmap in `Docs/ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md` is the correct implementation follow-on.

## Immediate next implementation slice

Implement the P0 front door first:

1. signup page
2. login page
3. auth context/session state
4. protected routes
5. backend user/auth model and JWT middleware

After that, move to workspace isolation and team invitation.

## References

- `Docs/APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md`
- `Docs/ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md`
- `spine_api/server.py`
- `spine_api/persistence.py`
- `frontend/src/app/page.tsx`
- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/lib/api-client.ts`
- `frontend/src/app/layout.tsx`
