# App State Analysis: The Missing Front Door

**Date:** 2026-04-23
**Scope:** Current app state vs. planned onboarding, auth, and workspace flows

---

## Executive Summary

The app is a **sophisticated engine wrapped in a UI that assumes you're already inside.** There is no front door. An agency owner who discovered this product today would have no way to sign up, create a workspace, invite agents, or create their first trip. We built the cockpit before building the airport.

---

## What Was Planned

`frontend/docs/DESIGN_BRIEF_Onboarding_Flow.md` (dated 2026-04-22) explicitly specified:

### Phase 1: Foundation
- [ ] Email + password signup
- [ ] Workspace auto-creation on signup
- [ ] Empty state with "New Trip" CTA
- [ ] Manual trip entry
- [ ] Workspace code generation (internal only)
- [ ] Agent signup with workspace code
- [ ] Agency profile modal (triggered by team add)

### Success Metrics
> "Owner creates first trip within 5 minutes of signup"

### User Model Specified
```typescript
interface User {
  id: string;
  email: string;
  passwordHash: string;
  workspaceId: string;
  role: 'owner' | 'admin' | 'agent' | 'external';
  // ...
}

interface Workspace {
  id: string;
  name: string;
  slug: string;
  ownerId: string;
  plan: 'free' | 'pro';
  // ...
}

interface WorkspaceCode {
  code: string; // e.g. TRI-7892-PLY
  codeType: 'internal' | 'external';
  status: 'generated' | 'shared' | 'active' | 'inactive';
  // ...
}
```

**Status: None of the above is implemented.**

---

## What Actually Exists

### Backend (`spine-api/`)

| Component | Status | Notes |
|-----------|--------|-------|
| TripStore | ✅ Built | JSON file-based trip persistence |
| AssignmentStore | ✅ Built | Who is assigned to which trip |
| AuditStore | ✅ Built | Event logging |
| OverrideStore | ✅ Built | Risk flag overrides |
| RunLedger | ✅ Built | Run lifecycle tracking |
| **UserStore** | ❌ **Missing** | No users table/model |
| **WorkspaceStore** | ❌ **Missing** | No workspace isolation |
| **Auth middleware** | ❌ **Missing** | No JWT, no sessions, no passwords |
| **Team API** | ❌ **Missing** | `GET /api/team/members` → 404 |
| **Inbox API** | ⚠️ Partial | `GET /api/inbox` route exists but backend has no `/inbox` endpoint |

**Critical finding:** The backend has **zero auth**. Every API endpoint is completely open. The only "user identification" is hardcoded strings:
- `user_id="owner"` in review actions
- `user_id="agent"` in IntakePanel
- `user_id="operator"` in audit logs

There is no `POST /signup`, no `POST /login`, no `GET /me`, no auth middleware on any route.

### Frontend (`frontend/src/app/`)

| Route | What It Is | Auth Gate? |
|-------|-----------|------------|
| `/` | Operations Dashboard | ❌ None |
| `/inbox` | Trip queue | ❌ None |
| `/workspace` | Active workspaces | ❌ None |
| `/workspace/[tripId]/...` | Trip detail panels | ❌ None |
| `/workbench` | AI analysis tool | ❌ None |
| `/owner/insights` | Analytics | ❌ None |
| `/owner/reviews` | Approvals | ❌ None |
| `/login` | **Does not exist** | N/A |
| `/signup` | **Does not exist** | N/A |
| `/onboarding` | **Does not exist** | N/A |
| `/settings/team` | **Does not exist** | N/A |

**The "user avatar" in the top-right corner:**
```tsx
// Shell.tsx:246
<div className='h-6 w-6 rounded-md bg-gradient-to-br from-violet-500 to-purple-600 ...'>
  OP
</div>
```
This is a hardcoded div. Not a user. Not clickable. No dropdown.

---

## Where We Deviated

### Deviation 1: Auth Was Never Started
The onboarding design brief was written on 2026-04-22. It has no corresponding implementation. No auth library was chosen (the brief suggested "Phase 1: Custom email/password, Phase 2: Clerk"). No auth context exists in React. No protected routes. No redirect-to-login logic.

### Deviation 2: Multi-Tenancy Was Never Started
The entire backend assumes a single global namespace. `AgencySettingsStore.load("waypoint-hq")` is hardcoded in `server.py:432`. All trips live in one flat `data/trips/` directory. All assignments in one `data/assignments/assignments.json`. There is no `workspace_id` filtering on any query.

### Deviation 3: Team Management Is a Frontend Mirage
The frontend has a full `governance-api.ts` with team endpoints (`/api/team/members`, `/api/team/invite`). The backend has none of these routes. If you tried to invite a team member, the request would 404.

### Deviation 4: Inbox Is Half-Wired
The frontend has `/api/inbox` routes. The backend has no `/inbox` endpoint. The inbox page fetches from `useInboxTrips()` which calls `governanceApi.getInboxTrips()` which hits `/api/inbox` — but the backend only knows `/trips` and `/assignments`. The inbox likely falls back to the trips endpoint or returns mock data.

### Deviation 5: We Built the Engine, Not the Product
The AI spine pipeline works. The workbench can process a raw note and populate 7 tabs of analysis. The dashboard shows real trip data. But the **product assumption** — that an agency owner arrives with no account, no data, and no context — was never addressed.

---

## Current User Journey (Reality)

```
Developer starts spine-api on :8000
Developer starts Next.js on :3000
Developer opens localhost:3000
→ Lands on Operations Overview
→ Stats show whatever trips exist in data/trips/
→ If no trips: empty states with "Process Your First Trip" CTA
→ CTA links to /workbench
→ Workbench has empty text fields
→ Developer types a customer note
→ Clicks "Process Trip"
→ AI spine runs, results populate
→ Trip is saved to data/trips/
```

**This is a developer demo, not a user onboarding.**

---

## What Needs to Be True for an Agency Owner to Start

### Immediate (P0): Create the Front Door
1. **Signup page** (`/signup`) — Email + password
2. **Login page** (`/login`) — Existing accounts
3. **Auth context** — React context or Zustand store with user/session
4. **Protected routes** — Redirect unauthenticated users to `/login`
5. **Backend auth** — At minimum: user model, password hashing, JWT issuance, middleware to validate tokens

### Short-term (P1): Workspace Isolation
1. **Workspace model** — Created on signup, owned by user
2. **Multi-tenant scoping** — All API queries filtered by `workspace_id`
3. **Workspace switcher** — If user belongs to multiple (future)
4. **Team invitation** — Generate workspace codes, agent signup flow

### Medium-term (P2): First-Trip Experience
1. **Empty state design** — Welcome message, checklist, "New Trip" CTA
2. **Manual trip creation** — Form to create a trip without processing through AI
3. **Getting started checklist** — "Create first trip", "Set agency profile", "Add team"
4. **Onboarding tooltip system** — Guide first-time users through the workbench

---

## Locked Direction: Option B++ (Comprehensive Multi-Tenant Platform)

> **Decision locked on 2026-04-23.** The system is being built as a full multi-tenant platform with production-grade auth, workspace governance, and comprehensive onboarding from the outset. There is no "minimal" or "MVP" path — every phase is complete and production-ready.

### Auth Strategy
- **Custom JWT** (HS256) with bcrypt password hashing
- Clerk deferred until revenue stage; migration path documented
- JWT middleware on all API routes from day one
- httpOnly cookies for session management

### Data Strategy
- **PostgreSQL** with **SQLAlchemy 2.0 async** + Alembic migrations
- Shared database with `agency_id` tenant scoping
- Row-level security (RLS) as hardening layer
- Gradual migration of JSON file stores (trips, assignments, audit) to relational tables without breaking engine contracts

### Onboarding Strategy
- **Full first-trip experience**: signup → workspace → empty state with checklist → "New Trip" CTA → manual trip creation → progressive disclosure
- Workspace auto-created on owner signup
- Workspace codes for agent invitation (internal/external)
- Agency profile modal triggered before team operations
- Success metric: owner creates first trip within 5 minutes of signup

### Governance Strategy
- 5 canonical roles: Owner, Admin, SeniorAgent, JuniorAgent, Viewer
- Creator bootstrap: Owner + Admin on workspace creation
- Full assignment/escalation/review engine with continuity preservation
- Settings control center at `/settings` with 8 subroutes
- AI workforce governance as first-class control plane

### Reference
- Implementation roadmap: [`ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md`](ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md)
- Governance model: [`WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`](WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md)
- Onboarding design: [`frontend/docs/DESIGN_BRIEF_Onboarding_Flow.md`](frontend/docs/DESIGN_BRIEF_Onboarding_Flow.md)

---

## Files That Need Attention

| File | Issue |
|------|-------|
| `spine-api/server.py` | No auth middleware, no user routes, hardcoded `waypoint-hq` |
| `spine-api/persistence.py` | No UserStore, no WorkspaceStore, no tenant scoping |
| `frontend/src/app/page.tsx` | Assumes user is already authenticated |
| `frontend/src/components/layouts/Shell.tsx` | Hardcoded "OP" avatar, no user menu |
| `frontend/src/lib/api-client.ts` | No auth header injection |
| `frontend/src/app/layout.tsx` | No auth provider wrapper |
| `frontend/src/lib/governance-api.ts` | Calls `/api/team/*` routes that don't exist in backend |

---

## Conclusion

The product has a **world-class engine and a beautiful dashboard, but no front door.** The deviation is clear: we built from the inside out (engine → dashboard → operations) instead of from the outside in (landing page → signup → first trip → operations). 

An agency owner cannot start because we never built the starting line.
