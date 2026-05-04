# Workspace Invite Loop — Implementation Notes (2026-05-04)

**Task**: Complete the agent onboarding invite loop (Task 1 from 5-task plan)
**Status**: Shipped — 11 new tests passing, 30 total (no regressions)

---

## What Was Built

### Problem
The previous session shipped the agent join page (`/join/[code]`) and the `POST /api/auth/join` backend, but owners had no way to:
1. See their current workspace invitation code
2. Copy a shareable invite link
3. Regenerate the code (revoke old one)
4. See who is already on their team

Without this, the onboarding loop was open on the agent side but sealed on the owner side.

### Solution: People Tab in Settings

Added a **People tab** to the existing `/settings` page (tab-based navigation with `?tab=people`). This avoids creating a parallel navigation path and keeps all agency-level config in one place.

The tab contains two sections:
1. **WorkspaceCodePanel** — shows current invite URL, copy-to-clipboard button, regenerate button
2. **TeamMemberList** — shows all members with name, email, role badge

---

## Files Changed

| File | Change |
|------|--------|
| `spine_api/routers/workspace.py` | Added `POST /api/workspace/codes` endpoint |
| `spine_api/services/workspace_service.py` | Fixed `generate_workspace_code` to revoke old codes |
| `frontend/src/lib/route-map.ts` | Added `workspace` and `workspace/codes` entries |
| `frontend/src/lib/governance-api.ts` | Added `getWorkspace()`, `generateWorkspaceCode()`, `WorkspaceInfo` type |
| `frontend/src/hooks/useGovernance.ts` | Added `useWorkspace()` hook |
| `frontend/src/app/(agency)/settings/page.tsx` | Added People tab (import + TABS array + render branch) |
| `frontend/src/app/(agency)/settings/components/PeopleTab.tsx` | New — WorkspaceCodePanel + TeamMemberList |
| `tests/test_workspace_invite_flow.py` | 11 new tests |

---

## Key Design Decisions

### 1. One active code at a time (revocation fix)

The original `generate_workspace_code` only created a new code — it did NOT mark old codes inactive. `get_workspace` used `ORDER BY created_at DESC LIMIT 1` to surface the newest, which worked visually but left stale "active" codes in the DB. Any stale code could still be used for joins via `validate_workspace_code` (which checks `status == "active"`).

**Fix**: Before inserting the new code, `generate_workspace_code` now fetches all `status=="active"` codes for the agency and sets each to `status="replaced"`. This is the correct revocation semantics aligned with the roadmap's "generate new → revokes old" model.

### 2. Tab extension vs new page

The roadmap mentioned `settings/people` as a page. Two options:
- New route: `frontend/src/app/(agency)/settings/people/page.tsx`
- New tab: add `{ id: 'people' }` to the existing settings tab list

Chose **tab** because:
- Zero navigation proliferation (no new sidebar entry needed)
- Consistent with existing profile/operations/autonomy pattern
- `?tab=people` is deep-linkable (same mechanism as other tabs)
- People settings are agency-level config, not a separate concern

### 3. People tab owns its own data fetching

The existing settings page uses a shared `draft` state + `isDirty` + save/reset flow. The People tab doesn't participate in this (workspace code and team members are server-driven, not form fields). `PeopleTab` fetches its own data via `useWorkspace()` and `useTeamMembers()` — no props passed from the parent, no draft state involvement.

This means the "Save / Reset" buttons in the settings header are invisible/disabled when on the People tab (since `isDirty` is false). That is correct behavior.

### 4. Window.location.origin in WorkspaceCodePanel

`window.location.origin` constructs the full join URL from the user's browser origin. This handles:
- Local dev: `http://localhost:3000/join/WP-abc`
- Staging: `https://staging.waypoint.ai/join/WP-abc`
- Production: `https://app.waypoint.ai/join/WP-abc`

No env var needed. The component is `'use client'` so `window` is always available.

### 5. Optimistic cache update on code regeneration

`useWorkspace().generateCode()` calls `generateWorkspaceCode()` and then does:
```typescript
queryClient.setQueryData<WorkspaceInfo>(QK.workspace(), (prev) =>
  prev ? { ...prev, workspace_code: newCode } : prev
);
```
This updates the displayed URL immediately without a round-trip `refetch()`. The backend is the source of truth — if the POST fails, the `generateCode` throws and the error is caught/displayed, leaving the old cached value intact.

---

## Complete Onboarding Flow (End-to-End)

```
Owner → Settings → People tab
  → sees current invite link (or "Generate link" if none)
  → clicks Copy → shares link with agent

Agent → visits /join/WP-abc123
  → page validates code: GET /api/auth/validate-code/WP-abc123
  → sees "Join {AgencyName}" form
  → submits: POST /api/auth/join
  → backend creates User + Membership(junior_agent) + sets httpOnly cookies
  → agent redirected to /overview

Owner → Settings → People tab
  → TeamMemberList shows new agent
  → Owner promotes role via future role-edit UI (backend: PATCH /api/team/members/{id})

Owner regenerates code → old WP-abc123 becomes status="replaced" → invalid for new joins
```

---

## What's Still Missing (Not in This Session)

- Role promotion UI in TeamMemberList (PATCH /api/team/members/{id} backend exists; no frontend edit flow)
- Pagination for TeamMemberList (fine for now; most agencies < 20 members)
- Email notification on join (not in roadmap yet)
- Owner-only gate on "New link" button (currently any authenticated user who can reach this page can regenerate — should check `role in {owner, admin}` client-side and return 403 server-side for non-admins)

The last item (role gate on code generation) is a security gap worth a fast follow. The endpoint currently only requires `Depends(get_current_membership)` — any member can regenerate the code and break active invite links. Backend should add `require_permission("workspace:manage_codes")` or a direct role check.
