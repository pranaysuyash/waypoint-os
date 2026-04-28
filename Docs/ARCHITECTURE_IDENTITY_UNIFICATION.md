# Phase 0: Identity Unification — Architecture & Handoff

## Executive Summary

Eliminated the dual-identity antipattern where `TeamStore` (file-based JSON) stored
"team members" as separate records from `User`/`Membership` (PostgreSQL). Now every
team member is a real `User` with a `Membership` in an agency. The `Membership` model
was extended with operational fields (`capacity`, `specializations`, `status`, `updated_at`)
that were previously only in `TeamStore`.

**Current state:** Code-ready ✅. Tests pass. Migration script ready.
**Next:** Phase 1 (`POST /api/auth/join` + `/join` page).

## Architecture Change

### Before
```
TeamStore (JSON file)          DB (PostgreSQL)
  agent_{hex}.id  ←→          User.id (UUID)
  {email, name, role,          Membership {user_id, agency_id, role, is_primary}
   capacity, active}             ⋮  no capacity/specializations/status
```

- Two sources of truth for "who is on this team"
- Team members couldn't log in
- TeamStore IDs (`agent_hex`) incompatible with Membership UUIDs
- Team endpoints not agency-scoped

### After
```
DB (PostgreSQL)
  User {id, email, name, password_hash, is_active, ...}
    ↕
  Membership {id, user_id, agency_id, role, is_primary,
              capacity, specializations, status, updated_at, created_at}
```

- One source of truth: `Membership + User`
- Every team member can authenticate (Users have password hashes)
- All team operations agency-scoped via `agency_id`
- UUIDs everywhere, consistent with the rest of the system

## Files Changed

### New Files
- `spine_api/services/membership_service.py` — Team member CRUD backed by Membership + User
  - `invite_member()` — creates User (if new) + Membership
  - `list_members()` — agency-scoped User + Membership join
  - `get_member()` — single member by membership ID
  - `update_member()` — role/capacity/specializations
  - `deactivate_member()` — sets status="inactive"

- `alembic/versions/a1b2c3d4e5f6_add_capacity_specializations_status_to_memberships.py`
  - Adds `capacity` (int, default 5)
  - Adds `specializations` (JSON)
  - Adds `status` (str, default "active")
  - Adds `updated_at` (datetime, nullable)

### Modified Files

| File | Change |
|------|--------|
| `spine_api/models/tenant.py` | Added `capacity`, `specializations`, `status`, `updated_at` to Membership |
| `spine_api/contract.py` | `TeamMember` now has `user_id`, `status` (replaces `active`), required `specializations` |
| `spine_api/server.py` | 6 team endpoints + analytics team endpoint converted from sync/TeamStore to async/MembershipService |
| `spine_api/persistence.py` | `TeamStore` marked `DEPRECATED` |
| `frontend/src/types/generated/spine_api.ts` | Regenerated from updated contract.py |
| `frontend/src/types/governance.ts` | `TeamMember` updated to match backend (removed `isActive`, `avatarUrl`, `joinedAt`, `lastActiveAt`, `currentAssignments`) |
| `frontend/src/lib/governance-api.ts` | `getTeamMembers()` now unwraps `{items, total}`; `inviteTeamMember()` returns `{success, member}` |

### Deprecated (Kept for Reference)
- `spine_api/persistence.TeamStore` — no longer called by any endpoint

## Test Results

```
tests/test_team_metrics_contract.py ......... 7 passed
tests/test_catchall_auth_proxy.py .......... 2 passed
Frontend tsc --noEmit ...................... 0 TeamMember-related errors
```

## Migration Steps

Run the Alembic migration against your database:

```bash
uv run alembic upgrade head
```

This adds 4 columns to the `memberships` table. Existing memberships get
`capacity=5` and `status='active'` defaults.

## Schema Contract

### `TeamMember` (backed by Membership + User)

```python
class TeamMember(BaseModel):
    id: str                    # membership.id (UUID)
    user_id: str               # User.id (UUID)
    email: str
    name: str
    role: str
    capacity: int = 5
    status: str = "active"     # "active" | "inactive"
    specializations: List[str]
    created_at: str
    updated_at: Optional[str]
```

### `InviteTeamMemberRequest`

```python
class InviteTeamMemberRequest(BaseModel):
    email: str
    name: str
    role: str
    capacity: int = 5
    specializations: Optional[List[str]] = None
```

## Next Phase (Phase 1: Join Workspace)

The MembershipService already has `invite_member()` which creates Users + Memberships.
Phase 1 builds the complementary path—joining via WorkspaceCode:

1. **`POST /api/auth/join`** — redeem a WorkspaceCode:
   - Find WorkspaceCode by code string
   - Verify status is "active"
   - Create User (if new) + Membership (role=junior_agent)
   - Update WorkspaceCode: status="used", used_by=user.id, used_at=now()
   - Return JWT (same auth pipeline as signup)
   
2. **`/join` page** — code input form + invite link resolver
   - Manual code entry: POST to /api/auth/join with code
   - Invite link: pre-fills code from URL param
   - On success: hydrate() + redirect to /overview

3. **Link from `/login`** — "Join an existing workspace? Enter your code"
   - Directs to /join

## Commit

Not committed. Changes are staged and ready for review.
