# Product-B Scoped Analytics Implementation Status

- Date: 2026-09-04
- Project: `/Users/pranay/Projects/travel_agency_agent`
- Decision: `Docs/architecture/adr/ADR-007-PRODUCT-B-SCOPED-ANALYTICS_2026-09-03.md`
- Predecessor audit: `Docs/review/RANDOM_DOCUMENT_AUDIT_V4_PRODUCTB_KPI_2026-09-03.md`
- Worktree: dirty before this slice; unrelated changes were preserved and no Git mutation was performed

## Objective

Make Product-B KPI reporting coherent for the long term while retaining both
agency-scoped and platform-global views. The agency owner/operator receives
only the current workspace’s metrics. The platform owner/admin receives a
separate global read model only through an explicit, durable platform role.

## First-principles contract

1. Scope is an authority boundary, not a display filter.
2. Workspace membership roles and platform roles are separate capabilities.
3. Agency and global views share one KPI engine so denominators and definitions
   cannot drift.
4. Global reads are aggregate-only, auditable, and explicitly labeled.
5. No user is silently promoted during migration; activation requires verified
   identity and an explicit operational step.
6. Empty, unknown, and unavailable measurements remain distinguishable from
   zero.

## Implemented changes

### Backend

- `spine_api/models/product_b_analytics.py`: typed scope/provenance/KPI response.
- `spine_api/product_b_events.py`: workspace filtering before inquiry grouping;
  explicit empty workspace IDs fail closed; global scope is represented in the
  result rather than inferred by the client.
- `spine_api/routers/product_b_analytics.py`:
  - agency route now passes the authenticated agency ID;
  - platform route is separate and requires `super_admin`;
  - global reads emit a durable audit event.
- `spine_api/core/platform_auth.py`: deny-by-default platform-role dependency.
- `spine_api/models/tenant.py` and `alembic/versions/add_platform_role_to_users.py`:
  persisted `none|support|ops_admin|super_admin` capability field.
- Auth payloads expose the platform role for capability-aware UI labeling.
- Test fixture principals default to `platform_role='none'`.

### Frontend

- `frontend/src/types/product-b.ts`: typed response aligned to the backend
  contract.
- `frontend/src/lib/governance-api.ts` and `frontend/src/hooks/useGovernance.ts`:
  canonical agency/platform KPI clients and query keys.
- `frontend/src/components/insights/ProductBKpiPanel.tsx`: shared rendering
  component with loading, no-data, error/retry, scope, freshness, and metric
  interpretation states.
- `frontend/src/app/(agency)/insights/PageClient.tsx`: agency-scoped placement.
- `frontend/src/app/(agency)/platform-admin/product-b/`: separate global
  platform-admin surface.
- `frontend/src/lib/route-map.ts`: transport mappings for both API routes.

## Verification receipt

The focused backend lane passed after the migration and fixture update:

```text
28 passed in 5.03s
```

The broader contract lane passed:

```text
47 passed in 7.41s
```

The updated agency Insights component lane passed:

```text
2 passed
```

Frontend typecheck passed. The focused frontend lane passed with 2 tests.
Frontend lint completed with zero errors; the repository still reports
unrelated pre-existing hook warnings outside this feature’s ownership
boundary. Targeted backend Ruff checks passed.

The current route/OpenAPI receipt, generated with an ephemeral non-production
`PROPOSAL_SIGNING_KEY` and without writing fixture files, is:

```text
341 application routes
311 OpenAPI paths
/analytics/product-b/kpis                         present in both
/platform/admin/analytics/product-b/kpis          present in both
ProductBKpiResponse properties                     9, including scope/provenance
```

`npm run build` completed successfully. The new `/platform-admin/product-b`
route is included as a dynamic authenticated page. The build still prints
existing dynamic-server diagnostics for unrelated request-cookie/query API
routes during static generation; they do not prevent the build from exiting
successfully and are not attributed to this Product-B slice.

The local Alembic database is at `add_platform_role_to_users (head)`. The
preview runtime returned frontend `200` and backend `/health` `200`. Backend
`/metrics` returned `401 Not authenticated`, which is consistent with the
current protected-metrics middleware and is not claimed as an unauthenticated
200 contract. The browser visibly rendered both new routes and their loading /
failure-recovery states; the local browser session was unauthenticated, so no
authorized KPI values or global-admin success state were claimed.

The snapshot and focused matrix above are the current local receipt. No local
result in this document is hosted, production, real-user, provider, or release
proof.

## Activation boundary

The migration was applied to the local development database and existing users
remain `platform_role='none'`. No identity was guessed or promoted. Before
enabling the global page for the platform owner, verify the intended user
identity and perform an explicit role update through the approved operational
path, then verify:

- the intended owner receives 200 from the platform route;
- an ordinary agency owner/admin receives 403;
- the agency route never returns another workspace’s events;
- the global response contains no raw event payloads or traveler notes;
- the read appears in the audit trail.

## Remaining release gates

- Browser proof at `/insights` and `/platform-admin/product-b` with an
  authenticated test state and controlled known data.
- Platform-admin rate limiting is now locally verified at `60` requests/minute;
  production/shared-store behavior still needs deployment verification.
- Current route/OpenAPI snapshot generated with an explicit safe non-production
  configuration preflight.
- Privacy/retention review for global aggregate analytics.
- Verified first-owner platform-role activation.

## Status

**Implementation complete for the authorized local slice; release readiness
not claimed.** The next open item should be selected only after the above
evidence boundary is either closed or deliberately accepted as a documented
deferral.
