# ADR-007: Product-B Agency and Platform Analytics Scopes

- Status: Accepted
- Date: 2026-09-03
- Decision owner: Product/platform owner
- Scope: Product-B KPI read models, authorization, API routes, frontend placement, and evidence
- Related audit: `Docs/review/RANDOM_DOCUMENT_AUDIT_V4_PRODUCTB_KPI_2026-09-03.md`
- Related design: `Docs/research/AGENT_GRAPH_AND_GLOBAL_ADMIN_EXPLORATION_2026-05-04.md`
- Canonical role contract: `Docs/CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`

## Context

Product-B KPIs answer two different questions:

1. How is Product-B performing for the agency/workspace currently being operated?
2. How is Product-B performing across the platform and participating agencies?

The existing `GET /analytics/product-b/kpis` route requires an authenticated
agency but discards the resolved agency before calculating metrics. The event
store preserves `workspace_id`, but KPI aggregation is unscoped. This makes a
global experiment metric look like an agency metric and leaves the authority
boundary implicit.

The canonical role matrix defines `Owner` and `Admin` as workspace-level human
roles. It does not make an agency owner a platform administrator. The global
admin exploration explicitly rejects reusing the agency `owner` role for
cross-tenant access and recommends a separate `platform_role` scope.

## Decision

Maintain both Product-B views as separate read-only projections over one
canonical event stream and one canonical KPI computation engine.

### Agency projection

The existing route remains the agency-facing capability:

```text
GET /analytics/product-b/kpis
```

It is scoped to the authenticated user’s active agency/workspace. The caller
cannot select another workspace, broaden the scope, or turn the route into a
global query through a request parameter.

### Platform projection

Global metrics are exposed through a separate platform-admin route:

```text
GET /platform/admin/analytics/product-b/kpis
```

This route requires an explicit platform-admin identity capability. Agency
membership roles (`owner`, `admin`, and all other workspace roles) do not imply
platform-global access.

The initial platform role vocabulary is:

```text
none | support | ops_admin | super_admin
```

The Product-B global KPI route is initially restricted to `super_admin`.
Additional platform roles may receive narrower read projections later through
an explicit permission decision.

The current product/platform owner may be the only `super_admin`, but that
access must be represented as a durable, revocable platform role rather than a
hard-coded email, user ID, environment bypass, or reused agency owner role.

### Shared computation

The KPI engine remains canonical and accepts an explicit scope boundary. A
missing workspace filter is never interpreted as permission to broaden access.

Conceptually:

```text
agency route        -> authenticated workspace scope -> filtered KPI engine
platform route      -> platform role scope           -> global KPI engine
```

The computation must filter events before grouping by inquiry. Both responses
must declare their scope, selected window, data source, freshness, definitions,
and unknown/no-data semantics.

## Authorization and data rules

- Workspace scope is derived from authenticated membership for the agency route.
- Platform scope is derived from a persisted platform role for the platform route.
- No client-provided `scope=global`, arbitrary `workspace_id`, or agency header
  may broaden authority in production.
- Global KPI responses are aggregate-only by default and do not return raw
  traveler notes, raw event payloads, or unnecessary cross-tenant identifiers.
- Platform-admin reads are separately observable and should record actor,
  platform role, requested metric, time window, and target scope/count.
- Platform-admin endpoints are rate-limited separately from agency analytics.
- Both routes are read-only in this decision. Global writes, exports, and
  cross-agency drill-downs require a later decision and stronger controls.

## API contract

Both response shapes expose a common top-level contract:

```json
{
  "scope": {
    "type": "agency|global",
    "workspace_id": "optional-for-agency",
    "workspace_count": 1
  },
  "window_days": 30,
  "qualified_only": false,
  "sample": {},
  "kpis": {},
  "confidence_tiers": {},
  "counts": {},
  "definitions": {},
  "provenance": {
    "data_source": "...",
    "generated_at": "..."
  }
}
```

The exact KPI value math remains owned by `ProductBEventStore`; scope and
provenance are part of the API contract rather than UI-only labels.

## Frontend placement

- Agency-scoped Product-B reporting belongs in the canonical agency Insights
  experience and must be labeled as the current agency/workspace.
- Global Product-B reporting belongs in a separate platform-admin experience
  and must be labeled as aggregate platform analytics.
- The frontend route map is a transport registry, not discoverability proof.
- Each surface must provide loading, empty/no-data, error, retry, scope, and
  metric-definition states.
- A global surface must not appear to be an agency performance view with a
  small or ambiguous “global” badge.

## Alternatives considered

### A. One endpoint with `scope=global`

Rejected. A query parameter makes a high-impact authority expansion look like
ordinary filtering and creates a confused-deputy/IDOR risk. It also makes
frontend labels and cache keys easy to misinterpret.

### B. Reuse agency `owner` or `admin` for global access

Rejected. These are workspace roles. Reusing them violates tenant isolation,
least privilege, and the canonical role matrix’s ownership semantics.

### C. Duplicate KPI implementations for agency and global views

Rejected. Duplicate mathematics would cause denominator, qualification, and
unknown-outcome drift. Use one canonical engine with explicit authorized scope.

### D. Keep global analytics hidden as an undocumented endpoint

Rejected as a long-term product model. Internal access may be restricted, but
the route, scope, authorization, audit, and response semantics must still be
explicit and testable.

## Migration and activation

The platform role is stored on the canonical `User` identity as a durable
field with a deny-by-default value of `none`. The schema migration must be
additive and must not grant global access to existing users automatically.

Granting the first `super_admin` is an explicit operational activation step,
performed against the intended user identity after migration and verified with
the platform-admin authorization tests. It is not performed implicitly by
signup, agency ownership, test-token issuance, or auth bypass.

## Verification and falsifiers

Acceptance requires:

1. An agency request returns only its own workspace’s events.
2. An agency user cannot select another workspace or global scope.
3. A non-platform user receives 403 from the platform route.
4. A `super_admin` receives global aggregate metrics.
5. Two workspaces with distinct synthetic event populations produce distinct
   agency results and one explicitly global result.
6. Both OpenAPI routes expose typed scope/provenance response contracts.
7. The agency and platform surfaces show different, unambiguous scope labels.
8. Global responses exclude raw event/PII payloads by default.
9. Platform-admin reads are auditable and separately rate-limited.
10. Browser proof confirms the actual authenticated routes and recovery states.

The decision should be revisited if Product-B becomes customer-visible across
multiple organizations, if a support role needs partial cross-tenant access,
if event storage moves from JSONL to SQL, or if global drill-down/export is
requested.

## Consequences

Positive:

- The same metric definitions serve both operational and platform learning.
- Agency users receive trustworthy tenant-local numbers.
- The platform owner gets the global view needed to evaluate Product-B.
- Global authority is explicit, revocable, auditable, and extensible.
- The UI, API, data, and tests share one scope vocabulary.

Costs and risks:

- A user identity schema/migration is required.
- Existing auth/session payloads must expose platform capability safely.
- Historical events with missing or ambiguous workspace ownership need a
  documented treatment policy.
- Global analytics may reveal business-sensitive aggregate trends and needs
  privacy-aware projection and access logging.

## Implementation boundary

This ADR authorizes the scoped implementation and its ordinary tests and
documentation. It does not authorize Git mutations, production deployment,
implicit database role activation for an unknown user, or global write actions.
