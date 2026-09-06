# F-30 Corporate Policy Authorization Boundary — 2026-09-05

**Status:** Partial local remediation; runtime/hosted authorization proof open.

## Finding

The corporate-policy trip routes previously accepted a raw `X-Agency-ID`
header and fell back to `TEST_AGENCY_ID`. That allowed an unauthenticated
caller to select the agency used for a read or policy-override write.

## Remediation

`spine_api/routers/corporate_policy.py` now injects the canonical
`get_current_agency_id` dependency for both:

- `POST /api/v1/corporate/audit-policy/{trip_id}`
- `POST /api/v1/corporate/approve-policy-override/{trip_id}`

The handlers no longer import `Header` or `TEST_AGENCY_ID`, read no client
agency header, and pass the dependency-provided agency to
`TripStore.get_trip_for_agency`. The shared dependency retains its existing
pytest/auth-bypass header behavior only for test isolation; production derives
the agency from the authenticated membership/JWT.

## Local evidence

Hermetic source-contract assertions (without importing the app or starting its
lifespan):

```text
F30 hermetic assertions: 2 passed
.venv/bin/ruff check spine_api/routers/corporate_policy.py \
  tests/test_corporate_policy_auth_boundary.py
All checks passed!
python3 -m py_compile ...
success
```

The repository pytest harness currently imports the full app from
`tests/conftest.py`; a TestClient attempt remained in startup for more than
five minutes with no output and was terminated. Therefore no HTTP 401/200
receipt is claimed here. The next gate is an app-startup/runtime test proving
anonymous denial, authenticated positive control, cross-tenant denial, and
audited override identity under a running dependency stack.

## Remaining work

1. Run the focused HTTP contract under a healthy app/DB lifespan.
2. Prove JWT subject → membership → agency binding across two agencies,
   including indistinguishable cross-tenant denial.
3. Replace client-supplied `approver_name` with an authenticated principal
   identity or document the delegated-approver contract; F-03 remains the
   related signoff-integrity finding.
4. Add durable audit verification and hosted role/RLS evidence before launch.

This local source fix is additive and fail-closed, but F-30 stays open until
runtime and external evidence match the route’s authorization scope.
