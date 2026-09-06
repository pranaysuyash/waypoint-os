# S-12 — RLS Positive/Negative Write-Probe Addendum

**Date:** 2026-09-04\
**Scope:** PostgreSQL RLS catalog, runtime-role posture, tenant visibility, and
write-side negative probe\
**Owner:** security/isolation lane\
**Evidence:** Tier 1 catalog/configuration inspection and Tier 2 local live
PostgreSQL checks\
**Sensitivity:** S1 focused passes; the new probe is a load-bearing regression
check, but no pre-fix run or mutation score is claimed

## Finding

The existing RLS suite already checked catalog posture, policy presence,
cross-tenant SELECT isolation, model-to-policy coverage, and application
ContextVar wiring. It did not directly prove the write-side contract of the
`waypoint_rls_all` policies: that an agency cannot update/delete another
agency's row and cannot insert a row stamped with a different `agency_id`.

That omission matters because SELECT-only isolation can hide a leak while a
misconfigured `WITH CHECK` clause still permits cross-tenant mutation or
creation of rows that are owned by the wrong tenant.

## Implementation

Added `test_trips_rls_blocks_cross_tenant_writes_for_runtime_role()` to
`tests/test_rls_live_postgres.py`.

The rollback-only live probe:

1. creates two temporary test agencies;
2. inserts one trip under each agency while switching
   `app.current_agency_id` transaction-locally;
3. scopes the session to agency A;
4. attempts to update and delete agency B's trip and requires both row counts
   to be zero;
5. attempts to insert a new trip with agency B's `agency_id` while scoped to A
   and requires PostgreSQL to reject the operation through `WITH CHECK`;
6. wraps the expected policy violation in a savepoint and rolls back the whole
   probe, leaving no test rows behind.

If the runtime role owns the table without FORCE RLS, the test fails (or can be
classified by the existing posture guard), rather than treating owner bypass
as success.

## Current local runtime posture

Read-only catalog inspection on 2026-09-04:

```text
current_user | rolsuper | rolbypassrls
waypoint     | f         | f
```

Tenant-table posture:

```text
agency_integrations          | waypoint | rls_enabled=t | force_rls=t
booking_collection_tokens    | waypoint | rls_enabled=t | force_rls=t
booking_confirmations        | waypoint | rls_enabled=t | force_rls=t
booking_documents            | waypoint | rls_enabled=t | force_rls=t
booking_tasks                | waypoint | rls_enabled=t | force_rls=t
document_extraction_attempts | waypoint | rls_enabled=t | force_rls=t
document_extractions         | waypoint | rls_enabled=t | force_rls=t
execution_events             | waypoint | rls_enabled=t | force_rls=t
memberships                  | waypoint | rls_enabled=t | force_rls=f
trip_routing_states          | waypoint | rls_enabled=t | force_rls=t
trips                        | waypoint | rls_enabled=t | force_rls=t
workspace_codes              | waypoint | rls_enabled=t | force_rls=f
```

The two FORCE exemptions are intentional auth-bootstrap boundaries documented
in `spine_api/core/rls.py`: login needs to discover a user's agency from
`memberships`, and join-code validation needs to discover an agency from
`workspace_codes` before `app.current_agency_id` is known. They retain ENABLE
RLS and are not silently reported as fully enforced for the table owner.

## Verification

Focused live write probe:

```bash
.venv/bin/pytest -q tests/test_rls_live_postgres.py -k cross_tenant_writes -vv
```

```text
1 passed, 7 deselected in 0.96s
```

Combined live and mock RLS suite:

```bash
.venv/bin/pytest -q tests/test_rls_live_postgres.py tests/test_rls.py
```

```text
20 passed in 1.24s
```

Static coverage check:

```bash
.venv/bin/python scripts/check_rls_coverage.py
```

```text
RLS coverage check passed: 12 protected, 4 exempted, 15 total with agency_id
```

Startup posture tests:

```text
4 passed, 21 deselected in 4.12s
```

Ruff and `git diff --check` for the modified test passed.

## Alignment assessment

| Dimension | Assessment |
|---|---|
| First principles | Tenant isolation must constrain reads and writes. The added probe exercises both row filtering and `WITH CHECK`, not only application filters. |
| Long term | The test is attached to the canonical live RLS suite and uses the existing policy/table registry. It does not introduce a parallel tenant harness. |
| Doctrine | Local database evidence is labeled local. The two auth exemptions and runtime-role assumptions remain explicit. No hosted or production claim is made. |
| Operational value | A future migration that drops FORCE RLS, weakens `WITH CHECK`, or changes role privileges will fail the live check instead of silently weakening tenant boundaries. |

## Remaining boundary

This closes the missing local write-probe evidence, not the entire RLS program.

- The local runtime still uses the `waypoint` role as table owner. FORCE RLS is
  active on the 10 non-exempt tenant tables, while `memberships` and
  `workspace_codes` remain auth-bootstrap exemptions.
- Phase 5F remains the long-term path to remove those exemptions by resolving
  the agency-discovery chicken-and-egg problem before login/join queries.
- A separate non-owner runtime role remains a stronger defense if all SQL paths
  are audited for FORCE-safe context setup.
- The tests do not prove hosted deployment configuration, role provisioning,
  failover, connection-pool behavior across replicas, or production traffic.
- `scripts/check_rls_coverage.py` is model/registry coverage; it cannot prove
  every arbitrary raw SQL path sets tenant context.

No migration or role mutation was performed in this lane. No Git staging,
commit, push, reset, checkout, stash, or cleanup was performed.
