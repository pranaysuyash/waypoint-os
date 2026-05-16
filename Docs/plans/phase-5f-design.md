# Phase 5F: Auth Bootstrap RLS Finalization

## Context

Phase 5E closed with 9 of 11 tenant tables under FORCE ROW LEVEL SECURITY. Two tables — `memberships` and `workspace_codes` — retain ENABLE RLS without FORCE because they are queried during login/join before `app.current_agency_id` is known. This is the chicken-and-egg problem: the auth flow needs memberships to discover the agency, but FORCE RLS requires the agency to be set first.

Phase 5F eliminates both exemptions. After this phase, all 11 tenant tables will have FORCE ROW LEVEL SECURITY with zero exemptions.

## Trigger

```text
RLS_FORCE_EXEMPT_TABLES = frozenset({"memberships", "workspace_codes"})
Two tables where the table owner bypasses RLS — a security compromise accepted in Phase 5E.
```

## Scope

1. Add `users.primary_agency_id` column (nullable FK to agencies)
2. Alembic migration + deterministic backfill from existing memberships
3. Rewrite login/refresh to read `primary_agency_id` from `users` (no RLS) before querying `memberships`
4. Rewrite workspace code flows to set RLS context before querying `workspace_codes`
5. Update audit context to use `primary_agency_id`
6. Re-enable FORCE RLS on `memberships` and `workspace_codes`
7. Remove startup dedup and orphan backfill guards (no longer needed)
8. Remove `RLS_FORCE_EXEMPT_TABLES` constant and all consumers
9. Regression tests proving all flows work under full FORCE RLS

## Non-goals

- No new product features
- No auth redesign (same JWT flow, same token structure)
- No non-owner runtime role split (future target)
- No changes to public booking collection flow (already FORCE-safe)
- No changes to business-logic RLS patterns (already FORCE-safe)

---

## 1. Schema change: `users.primary_agency_id`

### Column definition

```sql
ALTER TABLE users ADD COLUMN primary_agency_id VARCHAR(36) DEFAULT NULL;
ALTER TABLE users ADD CONSTRAINT fk_users_primary_agency
    FOREIGN KEY (primary_agency_id) REFERENCES agencies(id) ON DELETE SET NULL;
CREATE INDEX ix_users_primary_agency_id ON users(primary_agency_id);
```

### Why `users` has no RLS

The `users` table has no `agency_id` column and no RLS policies. It is a global table — users exist independent of agencies. A user's `primary_agency_id` is a denormalized pointer that bootstraps the RLS context, not a tenant-scoped attribute. This is why it breaks the chicken-and-egg: reading from `users` requires no RLS context.

### Deterministic backfill

```sql
UPDATE users u
SET primary_agency_id = m.agency_id
FROM (
    SELECT DISTINCT ON (user_id) user_id, agency_id
    FROM memberships
    WHERE status = 'active'
    ORDER BY user_id, is_primary DESC, created_at DESC
) m
WHERE u.id = m.user_id AND u.primary_agency_id IS NULL;
```

Selection rules:
- Active memberships only (inactive memberships cannot bootstrap login)
- Primary active membership wins (is_primary = true)
- If multiple active memberships (data inconsistency), most recent created_at wins
- If no primary active, most recent active membership wins
- Users with zero active memberships get NULL (handled by explicit login-time path, not silent creation)

### ORM model change

In `spine_api/models/tenant.py`, add to the `User` class:

```python
primary_agency_id: Mapped[Optional[str]] = mapped_column(
    String(36), ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True
)
```

---

## 2. Auth flow changes

### 2.1 `_ensure_user_membership` (auth_service.py:36-97)

**Current**: Queries `memberships` by `user_id` without RLS context. Returns primary or any membership. Creates agency + membership for orphans.

**After Phase 5F**:

```python
async def _ensure_user_membership(db: AsyncSession, user: User) -> Membership:
    # 1. If user has primary_agency_id, set RLS context and verify membership
    if user.primary_agency_id:
        await apply_rls(db, user.primary_agency_id)

        result = await db.execute(
            select(Membership)
            .where(Membership.user_id == user.id)
            .where(Membership.agency_id == user.primary_agency_id)
            .where(Membership.status == "active")
        )
        membership = result.scalar_one_or_none()
        if membership:
            return membership

        # Stale pointer: primary_agency_id exists but no active membership found.
        # Do NOT silently create a new agency.  A stale pointer means the user
        # was removed from their workspace, or their primary agency was deleted.
        # Either case needs explicit recovery or repair, not duplicate-creation.
        user.primary_agency_id = None
        await db.flush()
        # Fall through to step 2 without RLS context (just cleared it)

    # 2. No primary_agency_id — check for any active membership
    #    This query runs WITHOUT RLS context. It works because:
    #    - Between Migration A and Migration B: FORCE RLS is not on memberships yet
    #    - After Migration B: this path is only reached for truly orphan users
    #      (no primary_agency_id, no agency context) — the query will return zero
    #      rows under FORCE RLS, which is correct: we fall through to step 3.
    #    NOTE: For the transition period, the startup guard
    #    _ensure_rls_no_force_on_auth_tables keeps FORCE off memberships,
    #    so this query succeeds. After Migration B removes that guard,
    #    this query returns zero rows for orphans — which is the intended
    #    behavior (step 3 creates the agency).
    if not user.primary_agency_id:
        result = await db.execute(
            select(Membership)
            .where(Membership.user_id == user.id)
            .where(Membership.status == "active")
            .order_by(Membership.is_primary.desc(), Membership.created_at.desc())
            .limit(1)
        )
        membership = result.scalar_one_or_none()
        if membership:
            user.primary_agency_id = membership.agency_id
            await db.flush()
            await apply_rls(db, membership.agency_id)
            return membership

    # 3. No membership at all — create agency + membership
    agency_name = f"{user.name or user.email}'s Agency"
    slug_base = agency_name.lower().replace("'s agency", "").replace(" ", "-")
    slug = f"{slug_base[:40]}-{secrets.token_hex(4)}"

    slug_result = await db.execute(select(Agency).where(Agency.slug == slug))
    if slug_result.scalar_one_or_none():
        slug = f"{slug_base[:40]}-{secrets.token_hex(6)}"

    agency = Agency(name=agency_name, slug=slug, email=user.email)
    db.add(agency)
    await db.flush()

    await apply_rls(db, agency.id)

    membership = Membership(
        user_id=user.id, agency_id=agency.id,
        role="owner", is_primary=True, status="active",
    )
    db.add(membership)
    await db.flush()

    # Update denormalized pointer
    user.primary_agency_id = agency.id
    await db.flush()

    return membership
```

Key change: if `primary_agency_id` exists, set RLS context BEFORE querying memberships. If not, create agency + membership as before, then set the pointer.

### 2.2 `login` (auth_service.py:224-270)

**Current**: Authenticates user, calls `_ensure_user_membership`, generates JWT.

**After Phase 5F**: No structural change. The `_ensure_user_membership` rewrite handles RLS context. Login flow:

```
authenticate(email, password) → user object (no RLS needed)
_ensure_user_membership(db, user) → membership (RLS bootstrapped from user.primary_agency_id)
create_access_token(user_id, agency_id, role) → JWT
```

The login function already loads the `User` object via email lookup on `users` (no RLS). Passing the full `user` object to `_ensure_user_membership` gives it access to `primary_agency_id`.

### 2.3 `refresh_access_token` (auth_service.py:272-330)

**Current**: Decodes refresh token, loads user, calls `_ensure_user_membership`.

**After Phase 5F**: Same pattern as login. The user object loaded via `select(User).where(User.id == user_id)` has `primary_agency_id` available. No structural change needed.

### 2.4 `signup` (auth_service.py:115-222)

**Current**: Creates user + agency + membership + workspace code in one transaction.

**After Phase 5F**: After creating the membership, set `user.primary_agency_id = agency.id`:

```python
# After membership flush
user.primary_agency_id = agency.id
await db.commit()
```

This is a single additional line. The `signup` flow already sets RLS context via `apply_rls(db, agency.id)` before the membership INSERT.

### 2.5 `validate_workspace_code` (auth_service.py:435-474)

**Current**: Queries `workspace_codes` by code without RLS context. Under FORCE RLS, this returns zero rows.

**After Phase 5F**: This is the harder case. The code is submitted before we know which agency it belongs to. Two options:

**Option A (chosen): Include agency_id in the join URL.**

Join invitation links already include the agency context in some flows. The `/join/[code]` page can encode `agency_id` as a query parameter or path segment:

```
/join?code=WP-abc123&agency=agency-uuid
```

Then:

```python
async def validate_workspace_code(
    db: AsyncSession,
    code: str,
    agency_id: str | None = None,
) -> dict:
    if agency_id:
        await apply_rls(db, agency_id)

    result = await db.execute(
        select(WorkspaceCode)
        .where(WorkspaceCode.code == code)
        .where(WorkspaceCode.agency_id == agency_id)
        .where(WorkspaceCode.status == "active")
    )
    workspace_code = result.scalar_one_or_none()
    # ... rest unchanged
```

**Why this works**: The invitation code is generated by an authenticated agent who knows their `agency_id`. The code is shared as a link that includes the agency. When the join page loads, it has both `code` and `agency_id` from the URL.

**No brute-force fallback**: If `agency_id` is not provided, the link is invalid/expired. Return a clear error message. The invitation code generation must always include the agency scope.

### 2.6 `join_with_code` (auth_service.py:484-594)

**Current**: Queries `workspace_codes` by code without RLS context.

**After Phase 5F**: Same as `validate_workspace_code` — accept `agency_id` parameter, set RLS context before querying. After creating the membership, set `user.primary_agency_id`:

```python
# After membership creation
user.primary_agency_id = agency.id
await db.commit()
```

---

### 2.7 RLS coverage gap: `membership_service.py` and `team.py` router

**Discovery**: `membership_service.py` (invite_member, list_members, get_member, update_member, deactivate_member) all receive `agency_id` as a parameter but use `get_db` instead of `get_rls_db`. The `team.py` router uses `Depends(get_db)` on all 6 endpoints.

**Current state**: Works because `memberships` lacks FORCE RLS (Phase 5E exemption). Table owner bypasses ENABLE RLS.

**After Migration B (FORCE RLS)**: All 6 team endpoints will fail. The service functions have `agency_id` — this is NOT a chicken-and-egg problem. Fix: switch to `get_rls_db` in the router, or call `apply_rls(db, agency_id)` at the top of each service function.

**Classification**: Not a Phase 5F design concern (no chicken-and-egg), but a required change before Migration B. Track as part of Step 2 code deploy.

### 2.8 RLS coverage gap: `validate-code` endpoint

**Discovery**: `GET /api/auth/validate-code/{code}` (auth.py:367) is an unauthenticated public endpoint that calls `validate_workspace_code(db, code)` using `Depends(get_db)`. The join page (`/join/[code]/page.tsx`) calls this endpoint with just the code, no agency_id.

**Current URL**: `/join/[code]` — code only, no agency parameter.

**Phase 5F change**: This endpoint must accept `agency_id` (query param). The join page URL must change from `/join/[code]` to `/join/[code]?agency=uuid`. The endpoint switches to `rls_session(agency_id)` or accepts agency_id and sets RLS context before calling the service function.

**Frontend impact**: The join page must be updated to:
1. Accept `agency` query param from URL
2. Pass it to the validate-code API call
3. Pass it to the join API call

---

## 3. Audit context change

### `_get_audit_context` (core/audit.py:122-167)

**Current**: Queries `memberships` by `user_id` without RLS context.

**After Phase 5F**:

```python
if user_obj and user_obj.is_active:
    user_id = user_obj.id
    if user_obj.primary_agency_id:
        agency_id = user_obj.primary_agency_id
    # else: agency_id stays "system" (the default).
    # Do NOT query memberships from audit fallback under FORCE RLS.
    # Users without primary_agency_id are audited as "system" — this is
    # correct and safe.  No apply_rls() call, no membership scan.
```

The common path reads `user.primary_agency_id` directly — no membership query, no RLS context needed. Users without a `primary_agency_id` (orphans, system accounts) are audited as agency `"system"` with no membership lookup. This avoids calling `apply_rls` with a fake agency ID and avoids querying `memberships` without RLS context.

---

## 4. Startup guard changes

### 4.1 Remove `_ensure_rls_no_force_on_auth_tables` (server.py:726-756)

This function runs `ALTER TABLE ... NO FORCE ROW LEVEL SECURITY` on exempt tables at startup. After Phase 5F, no tables are exempt. Remove this function entirely.

### 4.2 Remove `_deduplicate_memberships_and_agencies` (server.py:758-816)

This function deduplicates memberships created by the Phase 5E FORCE RLS bug. After Phase 5F, the bug cannot recur (login bootstraps from `users.primary_agency_id`). Remove this function only after verifying:

1. No duplicate active memberships per user exist in the database (run the dedup CTE as a CHECK query, not a DELETE)
2. Every user with an active membership has `primary_agency_id` set
3. `_should_run_startup_mutations()` gate is confirmed in production (no mutations on startup)

If any check fails, keep the dedup guard active until data is repaired via migration.

### 4.3 Simplify `_ensure_users_have_memberships` (server.py:611-723)

This function backfills agencies + memberships for orphan users. After Phase 5F, `_ensure_user_membership` handles this at login time. The startup backfill is still useful for bulk migration but should be simplified:

1. Create agencies + memberships for orphans (same as current)
2. Set `primary_agency_id` on each user after creating the membership
3. Keep `_should_run_startup_mutations()` gate — production does not run this

After verifying no orphans remain, this function can be removed in a future cleanup.

### 4.4 Update `_validate_rls_runtime_posture_configuration`

Remove the "9 FORCE + 2 exempt" exception logging. After Phase 5F, posture validation asserts FORCE RLS on all 11 tables.

---

## 5. RLS constant changes

### Remove `RLS_FORCE_EXEMPT_TABLES` (core/rls.py:70-75)

This constant becomes empty after Phase 5F. Remove it and all consumers:

| Consumer | File | Change |
|---|---|---|
| `_ensure_rls_no_force_on_auth_tables` | server.py:726 | Remove entire function |
| `RlsRuntimePosture.risks()` | core/rls.py | Remove exempt-aware skip logic |
| `test_all_tenant_tables_have_force_rls` | test_rls_live_postgres.py | Remove exempt branch, assert FORCE on all |

### Update `RlsRuntimePosture.risks()`

Current logic:

```python
if table.owner == self.current_user and not table.force_rls:
    if table.table_name not in RLS_FORCE_EXEMPT_TABLES:
        risks.append(...)
```

After Phase 5F:

```python
if table.owner == self.current_user and not table.force_rls:
    risks.append(...)
```

No exemption. Any table without FORCE RLS is a risk.

---

## 6. Migration (two-step deploy)

### Migration A: `add_users_primary_agency_id_phase5f_a.py`

Column + backfill only. Deployed first, does not change RLS posture. Keep existing FORCE exemptions.

```python
def upgrade():
    # 1. Add column
    op.add_column('users', sa.Column('primary_agency_id', sa.String(36), nullable=True))
    op.create_foreign_key('fk_users_primary_agency', 'users', 'agencies', ['primary_agency_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_users_primary_agency_id', 'users', ['primary_agency_id'])

    # 2. Backfill from active memberships only
    op.execute("""
        UPDATE users u
        SET primary_agency_id = m.agency_id
        FROM (
            SELECT DISTINCT ON (user_id) user_id, agency_id
            FROM memberships
            WHERE status = 'active'
            ORDER BY user_id, is_primary DESC, created_at DESC
        ) m
        WHERE u.id = m.user_id AND u.primary_agency_id IS NULL
    """)

def downgrade():
    op.drop_index('ix_users_primary_agency_id')
    op.drop_constraint('fk_users_primary_agency', 'users', type_='foreignkey')
    op.drop_column('users', 'primary_agency_id')
```

### Deploy code after Migration A

After the column exists and primary_agency_id is populated, deploy the code changes:
- `auth_service.py` — login/refresh/signup/join use `primary_agency_id`
- `audit.py` — use `primary_agency_id` directly
- `server.py` — update startup guards
- Frontend — join links include `agency_id`

### Migration B: `enable_force_rls_on_auth_tables_phase5f_b.py`

FORCE RLS on memberships and workspace_codes. Remove exemptions. Deployed only after code deploy proves stable.

```python
def upgrade():
    op.execute("ALTER TABLE memberships FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_codes FORCE ROW LEVEL SECURITY")

def downgrade():
    op.execute("ALTER TABLE memberships NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_codes NO FORCE ROW LEVEL SECURITY")
```

### Verification between Migrations

```bash
uv run pytest tests/test_auth_under_force_rls.py -v  # must pass without FORCE
uv run pytest tests/test_auth_membership_regression.py -v
```

### Posture after migration

```text
Table                             RLS   FORCE
──────────────────────────────────────────────
booking_collection_tokens          Y      Y
booking_confirmations              Y      Y
booking_documents                  Y      Y
booking_tasks                      Y      Y
document_extraction_attempts       Y      Y
document_extractions               Y      Y
execution_events                   Y      Y
trip_routing_states                Y      Y
trips                              Y      Y
memberships                        Y      Y    ← was exempt, now FORCE
workspace_codes                    Y      Y    ← was exempt, now FORCE
```

All 11 tables. Zero exemptions.

---

## 7. Frontend changes

### Join URL format

Update the join invitation link to include `agency_id`:

```
Before: /join?code=WP-abc123
After:  /join?code=WP-abc123&agency=agency-uuid
```

### Changes in `api-client.ts`

- `validateWorkspaceCode(code, agencyId?)` — add optional `agencyId` parameter
- `joinWithCode(code, email, password, name, agencyId?)` — add optional `agencyId` parameter

### Changes in join page component

- Extract `agency` from URL query params
- Pass to `validateWorkspaceCode` and `joinWithCode`

### Workspace code generation

When generating invitation links, include the current user's `agency_id`:

```typescript
const inviteLink = `/join?code=${code}&agency=${currentAgencyId}`;
```

---

## 8. `primary_agency_id` maintenance

### When to update

1. **Signup**: Set to the created agency's ID (new code in `signup`)
2. **Join**: Set to the joined agency's ID (new code in `join_with_code`)
3. **Orphan backfill**: Set by `_ensure_user_membership` when creating first membership
4. **Agency switch** (future): When user switches active agency in multi-agency UI, update `primary_agency_id`. Not in Phase 5F scope but the column supports it.

### Consistency guarantee

The `primary_agency_id` is a denormalized pointer. The source of truth is the `memberships` table. If they diverge:

1. **Stale pointer** (`primary_agency_id` points to agency with no active membership): `_ensure_user_membership` clears the pointer, scans for any other active membership, and repairs. If no active membership exists, creates a new agency + membership and updates the pointer. **Does NOT silently create duplicate agencies when a pointer is stale — pointer is cleared first, then a full scan determines whether recovery or creation is needed.**

2. **Missing pointer** (`primary_agency_id` is NULL): Scans for any active membership. If found, repairs the pointer. If not, creates agency + membership.

3. **Agency deleted** (`ON DELETE SET NULL` fires): Same as missing pointer — scan, repair, or create.

---

## 9. Test plan (~30 tests)

### Backend

`test_auth_under_force_rls.py` (~22 new tests):

| Test | What it proves |
|---|---|
| `test_login_with_primary_agency_id` | Login succeeds when user has `primary_agency_id`, RLS context set before membership query |
| `test_login_without_primary_agency_id_creates_agency` | Login succeeds for orphan user, creates agency + membership + sets `primary_agency_id` |
| `test_refresh_with_primary_agency_id` | Refresh succeeds when user has `primary_agency_id` |
| `test_refresh_without_primary_agency_id` | Refresh succeeds for orphan user |
| `test_signup_sets_primary_agency_id` | Signup sets `user.primary_agency_id` to created agency |
| `test_join_with_code_sets_primary_agency_id` | Join sets `user.primary_agency_id` to joined agency |
| `test_validate_workspace_code_with_agency_id` | Code validation works with `agency_id` under FORCE RLS |
| `test_join_with_code_with_agency_id` | Join works with `agency_id` under FORCE RLS |
| `test_audit_context_uses_primary_agency_id` | Audit reads agency_id from `user.primary_agency_id`, no membership query |
| `test_stale_primary_agency_id_does_not_create_duplicate` | Stale pointer (agency deleted or membership removed) clears pointer, scans for other active membership, does NOT create duplicate agency |
| `test_backfill_migration_populates_primary_agency_id` | Migration backfills from memberships deterministically |
| `test_force_rls_on_all_11_tables` | All 11 tenant tables have FORCE RLS (no exemptions) — only after Migration B |
| `test_no_rls_force_exempt_tables_constant_removed` | `RLS_FORCE_EXEMPT_TABLES` does not exist or is empty |
| `test_login_idempotent_under_force_rls` | Re-login returns same agency, no duplicates |
| `test_cross_tenant_membership_invisible_under_force_rls` | User A cannot see User B's memberships even with FORCE RLS |
| `test_workspace_code_invisible_without_agency_context` | Workspace code query returns zero rows without RLS context |
| `test_inactive_membership_cannot_login` | User with only inactive memberships is treated as orphan, does not get stale access |
| `test_active_primary_wins_over_inactive_primary` | If user has inactive primary and active non-primary, active one is used |
| `test_no_agency_legacy_join_link_fails_safely` | Join link without agency_id returns invalid/expired error, no brute-force |
| `test_workspace_code_with_wrong_agency_id_fails` | Workspace code queried with wrong agency_id returns invalid, no cross-tenant leak |
| `test_all_11_force_rls_only_after_migration_b` | FORCE RLS on memberships/workspace_codes verified only after Migration B, not before |
| `test_startup_dedup_removed_after_migration_b` | `_deduplicate_memberships_and_agencies` and `_ensure_rls_no_force_on_auth_tables` do not exist in codebase |

`test_rls_live_postgres.py` (update existing):

| Test | Change |
|---|---|
| `test_all_tenant_tables_have_force_rls` | Remove exempt branch — assert FORCE on all 11 |

### Frontend

`join-page.test.tsx` (~4 tests):

| Test | What it proves |
|---|---|
| `test_join_url_includes_agency_id` | Join link includes agency parameter |
| `test_validate_code_passes_agency_id` | Validation request includes agency_id |
| `test_join_passes_agency_id` | Join request includes agency_id |
| `test_join_without_agency_id_fails_safely` | Legacy links show invalid/expired error, no brute-force fallback |

---

## 10. Files to create/modify

### Create

| File | Purpose |
|---|---|
| `alembic/versions/add_users_primary_agency_id_phase5f_a.py` | Migration A: column, backfill, indexes, FK (no RLS change) |
| `alembic/versions/enable_force_rls_on_auth_tables_phase5f_b.py` | Migration B: FORCE RLS on memberships + workspace_codes |
| `tests/test_auth_under_force_rls.py` | Regression tests under full FORCE RLS |

### Modify

| File | Change |
|---|---|
| `spine_api/models/tenant.py` | Add `primary_agency_id` to `User` model |
| `spine_api/services/auth_service.py` | Rewrite `_ensure_user_membership`, `validate_workspace_code`, `join_with_code`; update `signup` to set `primary_agency_id` |
| `spine_api/core/rls.py` | Remove `RLS_FORCE_EXEMPT_TABLES`; update `RlsRuntimePosture.risks()` |
| `spine_api/core/audit.py` | Update `_get_audit_context` to use `primary_agency_id` |
| `spine_api/server.py` | Remove `_ensure_rls_no_force_on_auth_tables`, `_deduplicate_memberships_and_agencies`; simplify `_ensure_users_have_memberships` to set `primary_agency_id`; update posture validation |
| `spine_api/routers/team.py` | Switch all 6 endpoints from `Depends(get_db)` to `Depends(get_rls_db)` |
| `spine_api/routers/auth.py` | Update `validate-code` endpoint to accept `agency_id` param and use `rls_session` |
| `tests/test_rls_live_postgres.py` | Remove exempt branch from FORCE RLS assertion |
| `frontend/src/lib/api-client.ts` | Add `agencyId` parameter to join functions |
| `frontend/src/app/(auth)/join/[code]/page.tsx` | Extract `agency` from URL query params, pass to validate-code and join calls |

---

## 11. Implementation order

### Step 1: Migration A (additive only)

1. **Migration A**: `add_users_primary_agency_id_phase5f_a.py` — column, backfill, indexes, FK
2. **ORM model**: `tenant.py` — add `primary_agency_id` to `User`

### Step 2: Code deploy (works with or without FORCE RLS)

3. **Auth core**: `auth_service.py` — rewrite `_ensure_user_membership`, update `signup`, `validate_workspace_code`, `join_with_code`
4. **Audit**: `audit.py` — use `primary_agency_id` in `_get_audit_context`, remove membership fallback
5. **Server**: `server.py` — update startup guards to set `primary_agency_id`, keep `_ensure_rls_no_force_on_auth_tables` active until Migration B
6. **Frontend**: `api-client.ts` + join page — pass agency_id in join links
7. **Tests**: `test_auth_under_force_rls.py` — 22 new tests (pass without FORCE on auth tables)
8. **Update existing tests**: `test_rls_live_postgres.py` — test plan updated but exempt branch kept until Migration B

### Step 3: Migration B (finalize FORCE RLS)

9. **Migration B**: `enable_force_rls_on_auth_tables_phase5f_b.py` — FORCE RLS on memberships + workspace_codes
10. **RLS module**: `rls.py` — remove `RLS_FORCE_EXEMPT_TABLES`, update `RlsRuntimePosture`
11. **Server**: `server.py` — remove `_ensure_rls_no_force_on_auth_tables`, `_deduplicate_memberships_and_agencies`
12. **Final tests**: verify all 11 tables have FORCE RLS, remove exempt branch from live postgres tests
13. **Frontend tests**: join page tests

---

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Migration backfill misses users with zero memberships | `_ensure_user_membership` handles at login time; `primary_agency_id` stays NULL |
| `primary_agency_id` points to deleted agency | FK `ON DELETE SET NULL` clears the pointer; `_ensure_user_membership` scans for other active memberships, repairs pointer, or creates new agency |
| Join links without `agency_id` parameter (legacy) | Return clear invalid/expired-link error. No brute-force fallback. Invitation code generation must always include agency scope. |
| Two-step deploy (Migration A → code → Migration B) leaves inconsistent state | Migration A is additive only (column + backfill, no RLS change). Old code still works. Migration B (FORCE RLS) only runs after code deploy proves stable. |
| Stale `primary_agency_id` creates duplicate agencies | `_ensure_user_membership` clears stale pointer before falling through. Step 2 scans for any active membership first. Only creates agency if truly zero active memberships. |
| Audit middleware query fails under FORCE RLS | `primary_agency_id` read avoids membership query entirely. No `apply_rls("system")` call. Orphans audited as agency="system" with no membership lookup. |

---

## 13. Verification

### After Step 1 (Migration A)

```bash
# Column exists and backfilled
alembic upgrade head
uv run python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def check():
    e = create_async_engine('postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os')
    async with e.connect() as conn:
        rows = await conn.execute(text(
            'SELECT COUNT(*) FROM users WHERE primary_agency_id IS NULL'
        ))
        nulls = rows.scalar()
        print(f'Users without primary_agency_id: {nulls}')
    await e.dispose()
asyncio.run(check())
"
```

### After Step 2 (code deploy)

```bash
# Auth regression tests (pass without FORCE on auth tables)
uv run pytest tests/test_auth_under_force_rls.py -v
uv run pytest tests/test_auth_membership_regression.py -v

# Full suite
uv run pytest tests/ -q

# Frontend
cd frontend && npm test -- --run
cd frontend && npx tsc --noEmit
```

### After Step 3 (Migration B — final state)

```bash
# Verify all 11 tables have FORCE RLS
uv run python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def check():
    e = create_async_engine('postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os')
    async with e.connect() as conn:
        rows = await conn.execute(text(
            \"SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class \"
            \"WHERE relname IN ('trips','memberships','workspace_codes','booking_collection_tokens',\"
            \"'trip_routing_states','booking_documents','document_extractions',\"
            \"'document_extraction_attempts','booking_tasks','booking_confirmations','execution_events') \"
            \"ORDER BY relname\"
        ))
        for r in rows.fetchall():
            assert r[1] and r[2], f'{r[0]}: RLS={r[1]} FORCE={r[2]}'
            print(f'{r[0]:<35} rls={r[1]}  force={r[2]}')
    await e.dispose()
asyncio.run(check())
"

# RLS tests (no more exempt branch)
uv run pytest tests/test_rls.py tests/test_rls_live_postgres.py -v

# Full suite
uv run pytest tests/ -q

# Frontend
cd frontend && npm test -- --run
cd frontend && npx tsc --noEmit
```

---

## 14. Success criteria

### After Step 2 (code deploy, before Migration B)

- `users.primary_agency_id` populated for all users with active memberships
- Login, refresh, signup, join all work using `primary_agency_id` bootstrap
- Audit context reads from `user.primary_agency_id` (no membership fallback query)
- Join links include `agency_id`; legacy links return clear error
- `_ensure_rls_no_force_on_auth_tables` still active (safety net during transition)
- `RLS_FORCE_EXEMPT_TABLES` still exists but code no longer depends on exemptions
- `test_auth_under_force_rls.py` — 22 tests pass (auth logic tested without requiring FORCE on auth tables)
- Full backend suite: 0 failures

### After Step 3 (Migration B, final state)

- All 11 tenant tables have `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`
- `RLS_FORCE_EXEMPT_TABLES` removed from codebase
- `_ensure_rls_no_force_on_auth_tables` and `_deduplicate_memberships_and_agencies` removed from codebase
- Login, refresh, signup, join all work under full FORCE RLS
- No startup dedup or orphan backfill guards needed for normal operation
- Full backend suite: 0 failures
- Full frontend suite: 0 failures
