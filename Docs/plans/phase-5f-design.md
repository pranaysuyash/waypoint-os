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
    ORDER BY user_id, is_primary DESC, created_at ASC
) m
WHERE u.id = m.user_id AND u.primary_agency_id IS NULL;
```

Selection rules:
- Primary membership wins (is_primary = true)
- If multiple primaries (data inconsistency), earliest created_at wins
- If no primary, earliest membership wins
- Users with zero memberships get NULL (handled by `_ensure_user_membership`)

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
    # 1. If user has primary_agency_id, set RLS context and query memberships
    if user.primary_agency_id:
        await apply_rls(db, user.primary_agency_id)

        result = await db.execute(
            select(Membership)
            .where(Membership.user_id == user.id)
            .where(Membership.agency_id == user.primary_agency_id)
        )
        membership = result.scalar_one_or_none()
        if membership:
            return membership

    # 2. No primary_agency_id or membership not found — create agency + membership
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
        .where(WorkspaceCode.status == "active")
    )
    workspace_code = result.scalar_one_or_none()
    # ... rest unchanged
```

**Why this works**: The invitation code is generated by an authenticated agent who knows their `agency_id`. The code is shared as a link that includes the agency. When the join page loads, it has both `code` and `agency_id` from the URL.

**Fallback**: If `agency_id` is not provided (legacy links), fall back to a brute-force approach: iterate known agency IDs. This is acceptable because:
- Join codes are rare (not high-frequency)
- The number of agencies is small
- This fallback path logs a warning and can be removed after a migration period

### 2.6 `join_with_code` (auth_service.py:484-594)

**Current**: Queries `workspace_codes` by code without RLS context.

**After Phase 5F**: Same as `validate_workspace_code` — accept `agency_id` parameter, set RLS context before querying. After creating the membership, set `user.primary_agency_id`:

```python
# After membership creation
user.primary_agency_id = agency.id
await db.commit()
```

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
    else:
        # Fallback for users without primary_agency_id (shouldn't exist after backfill)
        await apply_rls(db, "system")  # no-op, just for safety
        m_result = await db.execute(
            select(Membership).where(Membership.user_id == user_id)
        )
        membership_obj = m_result.scalar_one_or_none()
        if membership_obj:
            agency_id = membership_obj.agency_id
```

The common path reads `user.primary_agency_id` directly — no membership query, no RLS context needed. The fallback queries memberships only for users without a primary_agency_id (should be zero after backfill).

---

## 4. Startup guard changes

### 4.1 Remove `_ensure_rls_no_force_on_auth_tables` (server.py:726-756)

This function runs `ALTER TABLE ... NO FORCE ROW LEVEL SECURITY` on exempt tables at startup. After Phase 5F, no tables are exempt. Remove this function entirely.

### 4.2 Remove `_deduplicate_memberships_and_agencies` (server.py:758-816)

This function deduplicates memberships created by the FORCE RLS bug. After Phase 5F, the bug cannot recur (login bootstraps from `users.primary_agency_id`). Remove this function entirely.

### 4.3 Simplify `_ensure_users_have_memberships` (server.py:611-723)

This function backfills agencies + memberships for orphan users. After Phase 5F, `_ensure_user_membership` handles this at login time. The startup backfill is still useful for bulk migration but should be simplified:

1. Create agencies + memberships for orphans (same as current)
2. Set `primary_agency_id` on each user after creating the membership

This function can be moved to a migration or kept as a startup guard with the existing `_should_run_startup_mutations()` gate.

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

## 6. Migration

### `alembic/versions/add_users_primary_agency_id_phase5f.py`

```python
def upgrade():
    # 1. Add column
    op.add_column('users', sa.Column('primary_agency_id', sa.String(36), nullable=True))
    op.create_foreign_key('fk_users_primary_agency', 'users', 'agencies', ['primary_agency_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_users_primary_agency_id', 'users', ['primary_agency_id'])

    # 2. Backfill from memberships
    op.execute("""
        UPDATE users u
        SET primary_agency_id = m.agency_id
        FROM (
            SELECT DISTINCT ON (user_id) user_id, agency_id
            FROM memberships
            ORDER BY user_id, is_primary DESC, created_at ASC
        ) m
        WHERE u.id = m.user_id AND u.primary_agency_id IS NULL
    """)

    # 3. Re-enable FORCE RLS on previously-exempt tables
    op.execute("ALTER TABLE memberships FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_codes FORCE ROW LEVEL SECURITY")

def downgrade():
    # 1. Remove FORCE RLS (restore Phase 5E posture)
    op.execute("ALTER TABLE memberships NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_codes NO FORCE ROW LEVEL SECURITY")

    # 2. Drop column
    op.drop_index('ix_users_primary_agency_id')
    op.drop_constraint('fk_users_primary_agency', 'users', type_='foreignkey')
    op.drop_column('users', 'primary_agency_id')
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

The `primary_agency_id` is a cache. The source of truth is the `memberships` table. If they diverge:
- Login uses `primary_agency_id` to bootstrap RLS context
- Then queries `memberships` with RLS context to find the actual membership
- If the membership doesn't exist (stale pointer), falls through to orphan path which creates a new agency + membership and updates the pointer

This is self-healing: the worst case is an orphan-user backfill, not a login failure.

---

## 9. Test plan (~30 tests)

### Backend

`test_auth_under_force_rls.py` (~16 new tests):

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
| `test_stale_primary_agency_id_self_heals` | If `primary_agency_id` points to agency without membership, orphan path creates new agency |
| `test_backfill_migration_populates_primary_agency_id` | Migration backfills from memberships deterministically |
| `test_force_rls_on_all_11_tables` | All 11 tenant tables have FORCE RLS (no exemptions) |
| `test_no_rls_force_exempt_tables_constant_removed` | `RLS_FORCE_EXEMPT_TABLES` does not exist or is empty |
| `test_login_idempotent_under_force_rls` | Re-login returns same agency, no duplicates |
| `test_cross_tenant_membership_invisible_under_force_rls` | User A cannot see User B's memberships even with FORCE RLS |
| `test_workspace_code_invisible_without_agency_context` | Workspace code query returns zero rows without RLS context |

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
| `test_join_without_agency_id_fallback` | Legacy links still show join page |

---

## 10. Files to create/modify

### Create

| File | Purpose |
|---|---|
| `alembic/versions/add_users_primary_agency_id_phase5f.py` | Migration: column, backfill, FORCE RLS re-enable |
| `tests/test_auth_under_force_rls.py` | Regression tests under full FORCE RLS |

### Modify

| File | Change |
|---|---|
| `spine_api/models/tenant.py` | Add `primary_agency_id` to `User` model |
| `spine_api/services/auth_service.py` | Rewrite `_ensure_user_membership`, `validate_workspace_code`, `join_with_code`; update `signup` to set `primary_agency_id` |
| `spine_api/core/rls.py` | Remove `RLS_FORCE_EXEMPT_TABLES`; update `RlsRuntimePosture.risks()` |
| `spine_api/core/audit.py` | Update `_get_audit_context` to use `primary_agency_id` |
| `spine_api/server.py` | Remove `_ensure_rls_no_force_on_auth_tables`, `_deduplicate_memberships_and_agencies`; simplify `_ensure_users_have_memberships` to set `primary_agency_id`; update posture validation |
| `tests/test_rls_live_postgres.py` | Remove exempt branch from FORCE RLS assertion |
| `frontend/src/lib/api-client.ts` | Add `agencyId` parameter to join functions |
| `frontend/src/app/(auth)/join/page.tsx` | Extract and pass `agency` from URL |

---

## 11. Implementation order

1. **Migration**: `add_users_primary_agency_id_phase5f.py` — column, backfill, FORCE RLS
2. **ORM model**: `tenant.py` — add `primary_agency_id` to `User`
3. **Auth core**: `auth_service.py` — rewrite `_ensure_user_membership`, update `signup`, `validate_workspace_code`, `join_with_code`
4. **Audit**: `audit.py` — use `primary_agency_id` in `_get_audit_context`
5. **RLS module**: `rls.py` — remove `RLS_FORCE_EXEMPT_TABLES`, update `RlsRuntimePosture`
6. **Server**: `server.py` — remove startup guards, update posture validation
7. **Tests**: `test_auth_under_force_rls.py` — 16 new tests
8. **Update existing tests**: `test_rls_live_postgres.py` — remove exempt branch
9. **Frontend**: `api-client.ts` + join page — pass agency_id
10. **Frontend tests**: join page tests

---

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Migration backfill misses users with zero memberships | `_ensure_user_membership` handles at login time; `primary_agency_id` stays NULL |
| `primary_agency_id` points to deleted agency | FK `ON DELETE SET NULL` clears the pointer; orphan path creates new agency |
| Join links without `agency_id` parameter (legacy) | Fallback brute-force scan with warning log; remove after migration period |
| Two-phase migration (column → FORCE RLS) leaves inconsistent state | Migration is single transaction: column + backfill + FORCE in one `upgrade()`. If backfill fails, transaction rolls back and FORCE RLS is not applied. |
| Audit middleware query fails under FORCE RLS | `primary_agency_id` read avoids membership query entirely; fallback has explicit RLS context |

---

## 13. Verification

```bash
# 1. Migration
alembic upgrade head

# 2. Verify all 11 tables have FORCE RLS
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

# 3. Verify primary_agency_id backfill
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

# 4. Auth regression tests
uv run pytest tests/test_auth_under_force_rls.py -v
uv run pytest tests/test_auth_membership_regression.py -v

# 5. RLS tests
uv run pytest tests/test_rls.py tests/test_rls_live_postgres.py -v

# 6. Full backend suite
uv run pytest tests/ -q

# 7. Frontend
cd frontend && npm test -- --run
cd frontend && npx tsc --noEmit
```

---

## 14. Success criteria

- All 11 tenant tables have `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`
- `RLS_FORCE_EXEMPT_TABLES` does not exist (or is empty)
- Login, refresh, signup, join all work under full FORCE RLS
- No startup dedup or orphan backfill guards needed for normal operation
- `test_auth_under_force_rls.py` — 16 new tests pass
- Full backend suite: 0 failures
- Full frontend suite: 0 failures
