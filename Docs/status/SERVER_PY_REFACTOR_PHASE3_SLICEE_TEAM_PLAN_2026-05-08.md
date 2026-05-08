# Server.py Refactor Phase 3 — Slice E Team Plan (Plan Only)

Date: 2026-05-08
Status:
- Phase 3 Slice D: accepted
- Phase 3 Slice E candidate: Team routes approved
- This document: plan-only, no implementation

## Hard guardrails
- Do not implement anything.
- Do not move routes yet.
- Do not change startup/lifespan/app-factory/middleware.
- Do not change auth/rate-limit behavior.
- Do not perform cleanup-only refactors.

## Scope: exact routes to move
1. GET /api/team/members
2. GET /api/team/members/{member_id}
3. POST /api/team/invite
4. PATCH /api/team/members/{member_id}
5. DELETE /api/team/members/{member_id}
6. GET /api/team/workload

Current line references in spine_api/server.py:
- GET /api/team/members: line 4001
- GET /api/team/members/{member_id}: line 4011
- POST /api/team/invite: line 4023
- PATCH /api/team/members/{member_id}: line 4048
- DELETE /api/team/members/{member_id}: line 4064
- GET /api/team/workload: line 4078

## Critical preservation rule
Preserve current unscoped behavior of GET /api/team/members/{member_id}.
- Do not add agency scoping in this extraction.
- Do not add auth hardening in this extraction.
- Do not add new permission checks in this extraction.
Any security hardening is a later explicit slice.

## Current behavior per route (must preserve)

### 1) GET /api/team/members
- Async handler; response_model=dict.
- Dependencies:
  - agency: Agency = Depends(get_current_agency)
  - db: AsyncSession = Depends(get_db)
- Calls membership_service.list_members(db, agency_id=agency.id)
- Returns {"items": members, "total": len(members)}

### 2) GET /api/team/members/{member_id}
- Async handler.
- Dependencies:
  - db: AsyncSession = Depends(get_db)
- No agency dependency currently (must preserve in extraction slice).
- Calls membership_service.get_member(db, member_id)
- If not found: HTTP 404 "Team member not found"
- Else returns member object

### 3) POST /api/team/invite
- Async handler.
- Dependencies:
  - request: InviteTeamMemberRequest
  - agency: Agency = Depends(get_current_agency)
  - user: User = Depends(get_current_user)
  - _perm = require_permission("team:manage")
  - db: AsyncSession = Depends(get_db)
- Calls membership_service.invite_member with:
  - agency_id=agency.id
  - invited_by=user.id
  - request fields (email/name/role/capacity/specializations)
- On ValueError: HTTP 409 with error detail
- Returns {"success": True, "member": member}

### 4) PATCH /api/team/members/{member_id}
- Async handler.
- Dependencies:
  - request: InviteTeamMemberRequest
  - agency: Agency = Depends(get_current_agency)
  - _perm = require_permission("team:manage")
  - db: AsyncSession = Depends(get_db)
- updates = request.model_dump(exclude_none=True, include={"role", "capacity", "specializations"})
- Calls membership_service.update_member(db, member_id, agency.id, updates)
- If not found: HTTP 404 "Team member not found"
- Returns member object

### 5) DELETE /api/team/members/{member_id}
- Async handler.
- Dependencies:
  - agency: Agency = Depends(get_current_agency)
  - _perm = require_permission("team:manage")
  - db: AsyncSession = Depends(get_db)
- Calls membership_service.deactivate_member(db, member_id, agency.id)
- If false: HTTP 404 "Team member not found"
- Returns {"success": True}

### 6) GET /api/team/workload
- Async handler.
- Dependencies:
  - agency: Agency = Depends(get_current_agency)
  - db: AsyncSession = Depends(get_db)
- Calls membership_service.list_members(db, agency_id=agency.id, active_only=True)
- Loads assignments via AssignmentStore._load_assignments()
- Loads agency trips via TripStore.list_trips(agency_id=agency.id, limit=10000)
- Filters assignments to agency trip IDs only
- Returns {"items": distribution, "total": len(distribution)}

## Current dependency/auth/permission profile summary
- Agency dependency present on routes: members list, invite, patch, delete, workload
- Agency dependency absent on route: GET /api/team/members/{member_id} (must preserve)
- Permission dependency present on routes:
  - POST /api/team/invite -> team:manage
  - PATCH /api/team/members/{member_id} -> team:manage
  - DELETE /api/team/members/{member_id} -> team:manage
- No rate-limit decorators in this route family

## Router shape (post-approval target)
New file:
- spine_api/routers/team.py

Required shape:
- router = APIRouter()
- no prefix
- no tags
- no router-level dependencies
- preserve endpoint-level dependencies exactly

## Required imports in spine_api/routers/team.py
- membership_service
- get_current_agency
- get_current_user
- require_permission
- get_db
- Agency, User
- InviteTeamMemberRequest
- AssignmentStore, TripStore
- AsyncSession

## server.py wiring plan (after approval only)
1. Add normal import path:
   - from routers import team as team_router
2. Add fallback importlib path aligned to existing pattern:
   - routers.team module loading via importlib.util
3. Add include:
   - app.include_router(team_router.router)
4. Remove only the six moved handlers from server.py
5. Do not alter other route families or unrelated imports

## Tests to add (after approval only)
New file:
- tests/test_team_router_behavior.py

Must cover:
1. Preserve unscoped get_member behavior:
   - GET /api/team/members/{member_id} remains callable without adding agency dependency in this slice
2. List members remains agency-scoped:
   - verifies membership_service.list_members called with agency.id
3. Invite uses agency.id and user.id:
   - verifies membership_service.invite_member receives agency_id and invited_by
4. Update/deactivate preserve permission dependency presence:
   - confirm team:manage guard remains attached
5. Workload uses agency trip filtering:
   - assignment count only over agency trip IDs

## Verification matrix (after approval only)
- tests/test_server_route_parity.py
- tests/test_server_openapi_path_parity.py
- tests/test_server_startup_invariants.py
- tests/test_team_router_behavior.py

## Snapshot expectations (after approval only)
- scripts/snapshot_server_routes.py
- expected route_count=129
- expected openapi_path_count=113

## Forbidden import check (after approval only)
Command:
- grep -n "from spine_api.server\|import server" spine_api/routers/team.py
Expected:
- no matches

## Non-goals
- no hardening
- no public checker movement
- no agent runtime movement
- no settings movement
- no /run or /runs movement
- no startup/lifespan/app-factory/middleware changes

## Comparison correction note
Correction carried forward for Slice E planning:
- POST /run is excluded from Phase 3 router movement and must not be considered part of an agent-runtime candidate slice.

## Stop
Stop after writing this plan. Await approval before implementation.
