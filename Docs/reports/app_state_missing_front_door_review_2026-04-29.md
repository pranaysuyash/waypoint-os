# App State Analysis Review: Missing Front Door

- Date: 2026-04-29
- Reviewed doc: [Docs/APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md](../APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md)
- Correction note: this review was superseded by the live auth front door already present in the codebase on 2026-05-01.

## Scope

This review focuses on the current app state and the immediate implementation gap it identifies.
It is intentionally limited to the front-door/auth/workspace slice.

## Findings

- The doc no longer matches the current repo state. The product now has signup/login pages, auth proxying, and backend auth endpoints/middleware.
- The remaining work is around onboarding completeness, workspace/tenant hardening, and replacing older placeholder UI state.
- `spine_api/persistence.py` still has tenant-scoping and persistence consolidation work to finish.
- `frontend/src/components/layouts/Shell.tsx` still contains placeholder identity UI that should be replaced with real user state.
- The roadmap in `Docs/ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md` remains useful for the remaining implementation slices, but its opening assumption about missing auth is stale.

## Immediate next implementation slice

The P0 front door is already present. The next implementation slice is:

1. workspace/tenant scoping audits across remaining data paths
2. onboarding and first-trip flow completion
3. replace placeholder identity UI in the shell
4. reduce auth/persistence drift with verification tests
5. keep the roadmap synchronized with the live code

After that, continue with team invitation and broader tenant management.

## References

- `Docs/APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md`
- `Docs/ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md`
- `spine_api/server.py`
- `spine_api/persistence.py`
- `frontend/src/app/page.tsx`
- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/lib/api-client.ts`
- `frontend/src/app/layout.tsx`
