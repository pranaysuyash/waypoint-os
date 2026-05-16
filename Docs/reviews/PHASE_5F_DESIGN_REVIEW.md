# Phase 5F: Auth Bootstrap RLS Finalization — Design Review

**Date**: 2026-05-15
**Status**: Design revised, not yet approved for implementation.
**Design doc**: `Docs/plans/phase-5f-design.md`

---

## What this is

Phase 5F is the final RLS hardening step. It removes the two FORCE RLS exemptions accepted in Phase 5E on `memberships` and `workspace_codes`. After Phase 5F, all 11 tenant-scoped tables will have `FORCE ROW LEVEL SECURITY` with zero exemptions.

This review covers the design revision (v2) incorporating 8 specific fixes from reviewer feedback on the initial design.

---

## Reviewer feedback and resolution

The initial design had the right direction (`users.primary_agency_id` to bootstrap RLS context) but several details that could recreate the lockout/duplicate-workspace bug in new forms. Eight issues were identified and fixed.

### Fix 1: Backfill ordering (resolved)

**Problem**: Original SQL used `ORDER BY created_at ASC` (earliest membership wins). If the Phase 5E duplicate bug created stale agencies over time, earliest could preserve the wrong workspace.

**Fix**: Backfill now uses:
```sql
WHERE status = 'active'
ORDER BY user_id, is_primary DESC, created_at DESC
```
Active memberships only. Primary active first. Most recent active wins as tiebreaker. Users with zero active memberships get NULL (handled at login time, not by silent creation).

**Verified**: Design doc sections 1 (backfill SQL), 6 (Migration A backfill).

### Fix 2: Stale pointer handling (resolved)

**Problem**: Original design fell through to orphan-creation when `primary_agency_id` pointed to an agency with no matching membership. This could silently create duplicate agencies — the same bug Phase 5E had.

**Fix**: `_ensure_user_membership` now has a 3-step decision tree:
1. If `primary_agency_id` exists → set RLS, query active membership. If found, return it. If not found → **clear the pointer** (set to NULL), do NOT create a new agency.
2. If `primary_agency_id` is NULL → scan for any active membership (works between migrations because FORCE isn't on memberships yet). If found, repair the pointer and return.
3. If no active membership exists → create agency + membership + set pointer.

The key change: step 1 clears the stale pointer instead of falling through to creation. Step 2 does a full scan before step 3 creates anything.

**Verified**: Design doc section 2.1 (full `_ensure_user_membership` rewrite with stale-pointer comment block).

### Fix 3: `status='active'` filter everywhere (resolved)

**Problem**: Original membership lookups queried by `user_id` and `agency_id` but did not consistently require active status. Inactive memberships could bootstrap login.

**Fix**: All three membership queries in `_ensure_user_membership` include `.where(Membership.status == "active")`. The backfill SQL includes `WHERE status = 'active'`.

**Verified**: Lines 104, 125 in the design doc's `_ensure_user_membership` pseudocode. Backfill SQL in sections 1 and 6.

### Fix 4: No brute-force workspace-code fallback (resolved)

**Problem**: Original design proposed iterating all agency IDs as a fallback for legacy join links without `agency_id`. This weakens FORCE RLS, creates a timing/enumeration surface, and keeps legacy ambiguity alive.

**Fix**: Removed entirely. If `agency_id` is not provided, the link is invalid/expired. Return a clear error. Invitation code generation must always include agency scope.

**Verified**: Section 2.5 now says "No brute-force fallback" explicitly. All references to brute-force in the doc are "no brute-force" statements.

### Fix 5: Workspace-code queries filter by both agency_id and code (resolved)

**Problem**: Original `validate_workspace_code` set RLS context from `agency_id` but queried only by code and status. RLS is defense-in-depth; application predicates should still be precise.

**Fix**: Added explicit `.where(WorkspaceCode.agency_id == agency_id)` to the query.

**Verified**: Section 2.5 `validate_workspace_code` pseudocode line 229.

### Fix 6: Two-step migration/deploy plan (resolved)

**Problem**: Original design put column, backfill, and FORCE RLS in one migration. If old code ran against the new DB (during deploy), login could break again.

**Fix**: Split into:
- **Migration A**: Add `primary_agency_id` column, backfill, indexes, FK. No RLS change. Old code still works.
- **Code deploy**: Login/refresh/signup/join use `primary_agency_id`. `_ensure_rls_no_force_on_auth_tables` stays active as safety net.
- **Migration B**: FORCE RLS on `memberships` and `workspace_codes`. Remove exemptions.

This means there's never a window where FORCE RLS is active but code doesn't use `primary_agency_id`.

**Verified**: Section 6 (two separate migration files with explicit deploy step between them). Section 11 (implementation order split into 3 steps).

### Fix 7: Audit fallback fix (resolved)

**Problem**: Original audit context called `apply_rls(db, "system")` when `primary_agency_id` was absent. `"system"` is not a valid agency ID.

**Fix**: Audit context now reads `primary_agency_id` directly. If absent, agency_id stays `"system"` (the default) with no membership query and no `apply_rls` call. Orphans are audited as "system" — correct and safe.

**Verified**: Section 3 (audit pseudocode). No remaining `apply_rls("system")` in the doc.

### Fix 8: Proof before dedup removal (resolved)

**Problem**: Original design removed `_deduplicate_memberships_and_agencies` immediately, assuming Phase 5F code prevents recurrence. But data cleanup proof was missing.

**Fix**: Section 4.2 now requires verification before removal:
1. No duplicate active memberships per user (run dedup CTE as CHECK, not DELETE)
2. Every user with active membership has `primary_agency_id` set
3. `_should_run_startup_mutations()` gate confirmed in production

If any check fails, keep the dedup guard active until data is repaired.

**Verified**: Section 4.2 (3-item verification checklist). Section 11 Step 3 (dedup removal only after Migration B).

---

## Remaining design decisions

### `_ensure_user_membership` step 2 relies on no-FORCE transition window

Between Migration A and Migration B, `memberships` does NOT have FORCE RLS. Step 2 of `_ensure_user_membership` queries memberships by `user_id` without RLS context. This works during the transition. After Migration B applies FORCE RLS, this query returns zero rows for orphans — which is the intended behavior (step 3 creates the agency).

**Implication**: Step 2 is only useful during the transition period. After Migration B, it becomes a no-op for true orphans. The code is correct at both stages, but the comment block explaining WHY should survive code review during implementation.

### Legacy join links break immediately

After Phase 5F, any existing join links that don't include `agency_id` will return invalid/expired. This is a deliberate breaking change. Existing active invitation links need to be regenerated after Phase 5F ships.

### Test count grew from 16 to 22

The reviewer requested 6 additional tests:
- `test_inactive_membership_cannot_login`
- `test_active_primary_wins_over_inactive_primary`
- `test_no_agency_legacy_join_link_fails_safely`
- `test_workspace_code_with_wrong_agency_id_fails`
- `test_all_11_force_rls_only_after_migration_b`
- `test_startup_dedup_removed_after_migration_b`

---

## Architecture summary

### How it breaks the chicken-and-egg

```
Phase 5E (current):
  login → query memberships by user_id (NO RLS context) → discover agency
  Problem: FORCE RLS blocks this query

Phase 5F (after):
  login → load User from users table (NO RLS, no agency_id column)
        → user.primary_agency_id provides agency context
        → set app.current_agency_id
        → query memberships (RLS context set, FORCE RLS passes)
```

`users` is a global table with no RLS. `primary_agency_id` is a denormalized pointer. Reading it requires no RLS context. This breaks the circular dependency.

### Workspace codes

```
Phase 5E (current):
  join → query workspace_codes by code (NO RLS context)
  Problem: FORCE RLS blocks this query

Phase 5F (after):
  join link includes agency_id → set app.current_agency_id
       → query workspace_codes by code + agency_id (RLS context set, FORCE RLS passes)
```

The join URL changes from `/join?code=WP-abc123` to `/join?code=WP-abc123&agency=uuid`.

---

## Coverage gap discovered during audit

During codebase verification, two additional RLS coverage gaps were found that the initial design missed. These are NOT chicken-and-egg problems (they have `agency_id` available) but they WILL break after Migration B applies FORCE RLS.

### Gap 1: `membership_service.py` / `team.py` router — `get_db` instead of `get_rls_db`

All 6 endpoints in `team.py` use `Depends(get_db)` while querying `memberships`. The service functions in `membership_service.py` receive `agency_id` as a parameter but never call `apply_rls`. Currently works because memberships lacks FORCE RLS. After Migration B: all team management endpoints fail.

**Fix**: Switch `team.py` router from `Depends(get_db)` to `Depends(get_rls_db)`. No service-layer changes needed.

**Files**: `spine_api/routers/team.py` (6 lines)

### Gap 2: `validate-code` endpoint — public, uses `get_db`, no `agency_id`

`GET /api/auth/validate-code/{code}` (auth.py:367) is unauthenticated and calls `validate_workspace_code(db, code)` with `Depends(get_db)`. The frontend join page at `/join/[code]/page.tsx` calls this with just the code, no agency parameter.

**Fix**: Accept `agency_id` as query param, switch to `rls_session(agency_id)`. Frontend join page must extract `agency` from URL query params.

**Files**: `spine_api/routers/auth.py` (1 endpoint), `frontend/src/app/(auth)/join/[code]/page.tsx`

Both gaps are now documented in the design doc (sections 2.7, 2.8) and added to the files-to-modify table.

---

## Files to change (summary)

### Create
- `alembic/versions/add_users_primary_agency_id_phase5f_a.py` — column + backfill
- `alembic/versions/enable_force_rls_on_auth_tables_phase5f_b.py` — FORCE RLS
- `tests/test_auth_under_force_rls.py` — 22 regression tests

### Modify
- `spine_api/models/tenant.py` — `primary_agency_id` on User
- `spine_api/services/auth_service.py` — 4 function rewrites
- `spine_api/core/rls.py` — remove `RLS_FORCE_EXEMPT_TABLES`
- `spine_api/core/audit.py` — direct `primary_agency_id` read
- `spine_api/server.py` — remove 2 startup guards, update 2 others
- `spine_api/routers/team.py` — switch 6 endpoints to `get_rls_db` (coverage gap)
- `spine_api/routers/auth.py` — `validate-code` endpoint accept `agency_id` (coverage gap)
- `tests/test_rls_live_postgres.py` — remove exempt branch
- `frontend/src/lib/api-client.ts` — agency_id on join functions
- `frontend/src/app/(auth)/join/[code]/page.tsx` — extract agency from URL query params

---

## Verdict

```text
Direction: approved
Design v2: addresses all 8 reviewer concerns
Coverage audit: found 2 additional RLS gaps not in original design (team.py router, validate-code endpoint)
Risk level: medium (schema change + auth rewrite, but two-step migration limits blast radius)
Ready for: implementation pending final approval
```

The 8 fixes address the real danger zones: stale-pointer duplicate creation, inactive membership bootstrap, brute-force fallback, single-migration deploy risk, and fake audit RLS context. The two-step migration strategy means there's never a window where the database is locked but the code can't unlock it.

The coverage audit found 2 additional files (`team.py` router with `get_db` instead of `get_rls_db`, and `validate-code` public endpoint) that would break under FORCE RLS. These are not chicken-and-egg problems (they have agency_id available) but must be fixed before Migration B.
