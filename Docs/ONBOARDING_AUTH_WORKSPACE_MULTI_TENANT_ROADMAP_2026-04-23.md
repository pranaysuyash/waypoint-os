# Onboarding, Auth, Workspace, and Multi-Tenant Roadmap

**Date**: 2026-04-23
**Status**: Active roadmap — implementation ready
**Scope**: Complete production system for agency owner onboarding, custom JWT authentication, workspace governance, multi-tenant isolation, and first-trip experience.
**Umbrella Reference**: [`WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`](WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md)

---

## 1. Executive Summary

The product has a world-class decision engine and a sophisticated operator workbench, but it lacks a front door. No agency owner can sign up, no workspace can be created, and no team member can be invited. The system is currently hardcoded to a single agency (`waypoint-hq`) with no user model, no session management, and no tenant isolation.

This roadmap defines the complete, production-grade implementation of the missing identity and onboarding layer. Every phase is designed to fit the final architecture without throwaway contracts. There is no "temporary" or "interim" solution — each deliverable is a permanent part of the platform.

**Locked Decisions:**
- **Auth**: Custom JWT (HS256) with bcrypt password hashing. Clerk deferred until revenue stage.
- **Database**: PostgreSQL + SQLAlchemy 2.0 async + Alembic migrations.
- **Tenant Model**: Shared database with `agency_id` scoping + PostgreSQL Row-Level Security (RLS) as hardening.
- **Onboarding**: Full first-trip experience — signup → workspace → empty state → manual trip creation → progressive disclosure.
- **Governance**: 5 canonical roles (Owner, Admin, SeniorAgent, JuniorAgent, Viewer) with full assignment/escalation/review engine.

---

## 2. Canonical Architecture

### 2.1 Auth & Session Contract

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AUTH LAYER (Custom JWT)                                                    │
│  ───────────────────────────────────────────────────────────────────────────│
│  Password Hashing: bcrypt (12 rounds)                                       │
│  Token Algorithm: HS256 (secret key rotation documented)                    │
│  Token Transport: httpOnly cookie + Authorization header fallback           │
│  Token Payload: { sub, agency_id, role, iat, exp }                          │
│  Session Duration: 24 hours access token, 7 days refresh token              │
│  Middleware: FastAPI dependency `require_auth` + `require_permission`       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why custom JWT over Clerk:**
- Zero external auth dependency during pre-revenue phase
- Full control over token payload shape (workspace_id, role embedded)
- No vendor lock-in — migration path to Clerk documented in Phase 8
- Password reset flow self-hosted (no external email service dependency)

**Migration path to Clerk (documented, not implemented):**
1. Add Clerk SDK alongside existing JWT middleware
2. Sync Clerk `user_id` to local `users` table via webhook
3. Map Clerk sessions to existing JWT payload shape
4. Gradually transition routes to Clerk session validation
5. Remove custom JWT once Clerk is fully adopted

### 2.2 Database Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Database | PostgreSQL 16+ | Relational integrity for agencies/users/memberships/trips. Already specified in `TECHNICAL_INFRASTRUCTURE.md`. |
| ORM | SQLAlchemy 2.0 async | Python ecosystem standard, native async support, type-safe `Mapped[]` syntax. |
| Migrations | Alembic | Version-controlled schema evolution. Required for production deployment. |
| Driver | asyncpg | Native async PostgreSQL driver. High performance for FastAPI async routes. |
| Connection Pool | SQLAlchemy built-in | Sufficient until >100 concurrent connections. |

**Dependencies to add:**
```toml
[project]
dependencies = [
    # ... existing deps ...
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.15.0",
    "pyjwt>=2.10.0",
    "bcrypt>=4.3.0",
    "python-multipart>=0.0.20",  # for form data in auth routes
]
```

### 2.3 Tenant Isolation Contract

Every database table that contains agency-scoped data MUST include:
1. **`agency_id` column** — foreign key to `agencies.id`
2. **Tenant scoping in queries** — every SELECT/UPDATE/DELETE filtered by `agency_id`
3. **RLS policy** — PostgreSQL row-level security as defense-in-depth

**Tenant ID flow through the stack:**
```
HTTP Request
    ↓ [JWT cookie decoded]
FastAPI Dependency `get_current_user()`
    ↓ [user.memberships → primary agency_id]
`get_tenant_id()` dependency
    ↓ [injected into every service call]
Service Layer
    ↓ [agency_id added to every query filter]
SQLAlchemy Query
    ↓ [RLS policy enforces agency_id match]
PostgreSQL
```

**Tables requiring tenant isolation:**
- `agencies` (root tenant table)
- `users` (global, but accessed via membership)
- `memberships` (junction with agency_id)
- `workspace_codes` (agency-scoped)
- `trips` (agency-scoped — migration from JSON in Phase 8)
- `assignments` (agency-scoped — migration from JSON in Phase 8)
- `audit_events` (agency-scoped — migration from JSON in Phase 8)
- `conversations` (agency-scoped)
- `overrides` (agency-scoped)
- `settings_changes` (agency-scoped)

### 2.4 Role & Permission Matrix

| Role | Capabilities |
|------|-------------|
| **Owner** | Commercial and governance authority. Final say on policy, billing, integration, hard safety controls. Cannot be deleted by anyone. |
| **Admin** | Day-to-day workspace administration. Team management, assignments, AI worker operations, routing defaults. Delegable by Owner. |
| **SeniorAgent** | Full operational trip work. Can claim, request handoff, operate assigned trips, act within thresholds. |
| **JuniorAgent** | Assigned-only default scope. Stronger review gates and restricted finalization powers. |
| **Viewer** | Read-only access to trips, customers, reports. |

**Permission Granularity (backend enforcement):**
```python
PERMISSIONS = {
    "owner": ["*"],
    "admin": [
        "team:manage", "trips:read", "trips:write", "trips:assign",
        "trips:reassign", "trips:escalate", "settings:read", "settings:write",
        "customers:read", "customers:write", "ai_workforce:manage",
        "reports:read", "audit:read",
    ],
    "senior_agent": [
        "trips:read", "trips:write", "trips:claim", "trips:request_handoff",
        "customers:read", "customers:write", "reports:read:own",
    ],
    "junior_agent": [
        "trips:read:assigned", "trips:write:assigned", "trips:request_review",
        "customers:read:assigned",
    ],
    "viewer": [
        "trips:read", "customers:read", "reports:read",
    ],
}
```

---

## 3. Canonical Data Model

### 3.1 Core Entities (SQLAlchemy 2.0)

```python
# spine_api/models/tenant.py
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Agency(Base):
    """A travel agency tenant."""
    __tablename__ = "agencies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships: Mapped[List["Membership"]] = relationship(
        "Membership", back_populates="agency", cascade="all, delete-orphan"
    )
    workspace_codes: Mapped[List["WorkspaceCode"]] = relationship(
        "WorkspaceCode", back_populates="agency", cascade="all, delete-orphan"
    )


class User(Base):
    """A human user of the system. Users can belong to multiple agencies."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    memberships: Mapped[List["Membership"]] = relationship(
        "Membership", back_populates="user", cascade="all, delete-orphan"
    )


class Membership(Base):
    """Junction table linking users to agencies with a role."""
    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    agency: Mapped["Agency"] = relationship("Agency", back_populates="memberships")


class WorkspaceCode(Base):
    """Invitation code for agents to join an agency workspace."""
    __tablename__ = "workspace_codes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    code_type: Mapped[str] = mapped_column(String(50), nullable=False)  # internal, external
    status: Mapped[str] = mapped_column(String(50), default="generated")
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    used_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    agency: Mapped["Agency"] = relationship("Agency", back_populates="workspace_codes")
```

### 3.2 Routing State Model (Phase 4)

```python
# spine_api/models/routing.py
class TripRoutingState(Base):
    """Operational routing state for a trip."""
    __tablename__ = "trip_routing_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id"), nullable=False)
    
    primary_assignee_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewer_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    escalation_owner_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    status: Mapped[str] = mapped_column(String(50), default="unassigned")
    priority: Mapped[str] = mapped_column(String(50), default="normal")
    
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    handoff_history: Mapped[list] = mapped_column(JSON, default=list)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### 3.3 AI Worker Registry Model (Phase 6)

```python
# spine_api/models/ai_workforce.py
class AIWorkerConfig(Base):
    """Governance configuration for a specialist AI worker."""
    __tablename__ = "ai_worker_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id"), nullable=False)
    worker_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    allowed_stages: Mapped[list] = mapped_column(JSON, default=list)
    action_mode: Mapped[str] = mapped_column(String(50), default="suggest")
    autonomy_mode: Mapped[str] = mapped_column(String(50), default="human_review")
    data_visibility_scope: Mapped[str] = mapped_column(
        String(50), default="traveler_safe_only"
    )
    escalation_behavior: Mapped[str] = mapped_column(String(50), default="flag_for_review")
    learning_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=True)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

---

## 4. API Contract Specification

### 4.1 Auth Routes

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| POST | `/api/auth/signup` | Create account + workspace | No |
| POST | `/api/auth/login` | Authenticate, set JWT cookie | No |
| POST | `/api/auth/logout` | Clear JWT cookie | Yes |
| GET | `/api/auth/me` | Current user + primary membership | Yes |
| POST | `/api/auth/refresh` | Refresh access token | Yes (refresh token) |
| POST | `/api/auth/password-reset-request` | Initiate password reset | No |
| POST | `/api/auth/password-reset` | Complete password reset | No (token) |

**Signup Request:**
```json
{
  "email": "owner@priyatravels.com",
  "password": "securePassword123",
  "name": "Priya Sharma"
}
```

**Signup Response:**
```json
{
  "user": {
    "id": "usr_abc123",
    "email": "owner@priyatravels.com",
    "name": "Priya Sharma"
  },
  "agency": {
    "id": "agy_def456",
    "name": "Priya Travels",
    "slug": "priya-travels"
  },
  "membership": {
    "role": "owner",
    "is_primary": true
  },
  "workspace_code": "TRI-7892-PLY"
}
```

### 4.2 Workspace & Team Routes

| Method | Route | Description | Permission |
|--------|-------|-------------|------------|
| GET | `/api/workspace` | Current workspace details | Any |
| PATCH | `/api/workspace` | Update agency profile | admin+ |
| GET | `/api/workspace/codes` | List workspace codes | admin+ |
| POST | `/api/workspace/codes` | Generate new code | admin+ |
| POST | `/api/workspace/codes/:id/revoke` | Revoke a code | admin+ |
| GET | `/api/team` | List team members | Any |
| POST | `/api/team/invite` | Invite by code (legacy) | admin+ |
| PATCH | `/api/team/:id/role` | Change member role | admin+ |
| DELETE | `/api/team/:id` | Remove member | admin+ |

### 4.3 Assignment & Routing Routes

| Method | Route | Description | Permission |
|--------|-------|-------------|------------|
| POST | `/api/trips/:id/assign` | Assign trip to agent | admin+ |
| POST | `/api/trips/:id/claim` | Claim trip (agent) | senior_agent+ |
| POST | `/api/trips/:id/request-handoff` | Request reassignment | senior_agent+ |
| POST | `/api/trips/:id/escalate` | Escalate trip | Any (creator/assignee) |
| POST | `/api/trips/:id/reassign` | Explicit reassignment | admin+ |
| GET | `/api/team/workload` | Current workload distribution | admin+ |
| GET | `/api/review-queue` | Trips needing review | admin+ |

### 4.4 Settings Routes

| Method | Route | Description | Permission |
|--------|-------|-------------|------------|
| GET | `/api/settings/agency` | Agency settings | Any |
| PATCH | `/api/settings/agency` | Update agency settings | admin+ |
| GET | `/api/settings/pipeline` | Pipeline autonomy config | owner+ |
| PATCH | `/api/settings/pipeline` | Update pipeline config | owner+ |
| GET | `/api/settings/ai-workforce` | AI worker registry | admin+ |
| PATCH | `/api/settings/ai-workforce/:worker_type` | Update worker config | admin+ |
| GET | `/api/settings/audit` | Settings audit log | owner+ |

---

## 5. Frontend Route Architecture

### 5.1 Auth Pages (unauthenticated)

| Route | File | Purpose |
|-------|------|---------|
| `/signup` | `app/(auth)/signup/page.tsx` | Agency owner signup |
| `/login` | `app/(auth)/login/page.tsx` | User login |
| `/logout` | `app/(auth)/logout/page.tsx` | Clear session, redirect |
| `/join/:code` | `app/(auth)/join/[code]/page.tsx` | Agent signup with workspace code |
| `/reset-password` | `app/(auth)/reset-password/page.tsx` | Password reset flow |

### 5.2 Workspace Pages (authenticated)

| Route | File | Purpose | Role Gate |
|-------|------|---------|-----------|
| `/workspace` | `app/workspace/page.tsx` | Dashboard / empty state | Any |
| `/workspace/trips/new` | `app/workspace/trips/new/page.tsx` | Manual trip creation | Any |
| `/workspace/trips/:id` | `app/workspace/trips/[id]/page.tsx` | Trip detail / workbench | Any (scoped) |
| `/inbox` | `app/inbox/page.tsx` | Trip inbox | Any |

### 5.3 Settings Pages (authenticated, role-gated)

| Route | File | Purpose | Min Role |
|-------|------|---------|----------|
| `/settings` | `app/settings/page.tsx` | Settings redirect | Any |
| `/settings/profile` | `app/settings/profile/page.tsx` | Personal profile | Any |
| `/settings/agency` | `app/settings/agency/page.tsx` | Agency branding/info | Admin |
| `/settings/people` | `app/settings/people/page.tsx` | Team management | Admin |
| `/settings/assignments` | `app/settings/assignments/page.tsx` | Routing rules | Admin |
| `/settings/ai-workforce` | `app/settings/ai-workforce/page.tsx` | AI worker governance | Admin |
| `/settings/pipeline` | `app/settings/pipeline/page.tsx` | Autonomy matrix | Owner |
| `/settings/integrations` | `app/settings/integrations/page.tsx` | External systems | Owner |
| `/settings/audit` | `app/settings/audit/page.tsx` | Audit trail | Owner |

---

## 6. Phase-by-Phase Implementation Plan

### Phase 0: Foundation & Contract Hardening

**Goal**: Lock the canonical model, establish database infrastructure, and create the auth framework before any UI or API routes are built.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/core/database.py` | Async SQLAlchemy engine, session factory, dependency `get_db()` |
| `spine_api/core/security.py` | Password hashing (bcrypt), JWT encode/decode, token validation |
| `spine_api/core/auth.py` | FastAPI dependencies: `get_current_user()`, `require_auth()`, `require_permission()` |
| `spine_api/models/tenant.py` | Agency, User, Membership, WorkspaceCode models |
| `spine_api/models/__init__.py` | Model registry for Alembic |
| `alembic.ini` | Alembic configuration |
| `alembic/env.py` | Async Alembic environment |
| `alembic/versions/001_init_tenant_schema.py` | Initial migration |

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/lib/api-client.ts` | Add auth header injection (`Authorization: Bearer <token>`) |
| `frontend/src/stores/auth.ts` | Zustand auth store: `user`, `agency`, `token`, `isAuthenticated`, `login()`, `logout()` |

**Database Changes:**
- Create `agencies`, `users`, `memberships`, `workspace_codes` tables
- Add unique constraints: `users.email`, `agencies.slug`, `workspace_codes.code`
- Add indexes: `memberships(agency_id)`, `memberships(user_id)`, `workspace_codes(agency_id)`

**Acceptance Criteria:**
- [ ] `alembic upgrade head` runs successfully against a local Postgres instance
- [ ] All models can be created and queried via async session
- [ ] `security.py` can hash a password and verify it
- [ ] `auth.py` can encode and decode a JWT with correct payload shape
- [ ] Frontend API client injects auth headers when token exists
- [ ] Zustand auth store persists token in `localStorage` (secure, httpOnly cookie handled by backend)

**Estimated Effort**: 2-3 days

**Dependencies**: None

---

### Phase 1: Identity, Tenancy, and Workspace Ownership

**Goal**: Make the workspace creator model real. A new user can sign up, get a workspace, and be bootstrapped as Owner + Admin.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/routers/auth.py` | Signup, login, logout, me, refresh endpoints |
| `spine_api/services/auth_service.py` | Business logic: create user, create agency, create membership, generate workspace code |
| `spine_api/services/workspace_service.py` | Workspace CRUD, code generation |
| `spine_api/routers/workspace.py` | GET /api/workspace, PATCH /api/workspace |
| `spine_api/server.py` | Wire auth router, apply `require_auth` to ALL existing routes (with tenant scoping) |

**API Contract:**
- `POST /api/auth/signup` → creates User + Agency + Membership (Owner) + WorkspaceCode
- `POST /api/auth/login` → validates password, sets httpOnly JWT cookie
- `GET /api/auth/me` → returns `{ user, agency, membership }`
- All existing `/api/*` routes now require valid JWT

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/app/(auth)/signup/page.tsx` | Signup form with email, password, name |
| `frontend/src/app/(auth)/login/page.tsx` | Login form with email, password |
| `frontend/src/app/(auth)/layout.tsx` | Auth layout (clean, centered, dark theme) |
| `frontend/src/middleware.ts` | Next.js middleware: redirect unauthenticated users to `/login`, authenticated users away from auth pages |
| `frontend/src/components/layouts/Shell.tsx` | Replace hardcoded "OP" avatar with real user name/initials from auth store |
| `frontend/src/components/layouts/UserMenu.tsx` | Dropdown with user name, agency name, settings link, logout |

**Database Changes:**
- Seed with first workspace code on agency creation
- Add trigger or application logic: `created_by` on agency = first user

**Acceptance Criteria:**
- [ ] User can sign up with email + password
- [ ] Workspace is auto-created with agency name derived from email domain (or prompt for name)
- [ ] Creator receives Owner role + Admin capabilities
- [ ] JWT cookie is set on login, cleared on logout
- [ ] Unauthenticated requests to `/api/*` return 401
- [ ] Frontend redirects unauthenticated users to `/login`
- [ ] Shell shows real user name instead of "OP"
- [ ] `GET /api/auth/me` returns correct user, agency, and role

**Estimated Effort**: 3-4 days

**Dependencies**: Phase 0

---

### Phase 2: Onboarding Flow & First-Trip Experience

**Goal**: Complete the journey from signup to first trip. The empty state teaches by showing, not telling. The owner creates value within 5 minutes.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/routers/trips.py` | `POST /api/trips` for manual trip creation (no AI processing) |
| `spine_api/services/trip_service.py` | Create trip with agency_id scoping, basic validation |
| `spine_api/models/trip.py` | SQLAlchemy Trip model (initial, will evolve in Phase 8) |

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/app/workspace/page.tsx` | Dashboard with empty state / trip list |
| `frontend/src/components/onboarding/EmptyState.tsx` | Welcome message, "New Trip" CTA, workspace readiness indicator |
| `frontend/src/components/onboarding/Checklist.tsx` | Sidebar checklist: "Create first trip", "Set agency profile", "Add team members" |
| `frontend/src/components/onboarding/ProgressTracker.tsx` | Persist checklist state in localStorage + backend |
| `frontend/src/components/trips/ManualTripForm.tsx` | Form to create a trip: customer name, destination, dates, party size, budget |
| `frontend/src/components/trips/TripCreatedConfirmation.tsx` | Success state after first trip, prompt to explore workbench |
| `frontend/src/app/workspace/trips/new/page.tsx` | Full-page manual trip creation |
| `frontend/src/hooks/useKeyboardShortcuts.ts` | Global shortcut: `N` → navigate to `/workspace/trips/new` |

**UX Flow:**
```
Signup → Login → /workspace (empty)
    ↓
EmptyState: "Welcome to your workspace! Let's get you started."
    ↓
User clicks [N]ew Trip or CTA button
    ↓
ManualTripForm: customer, destination, dates, party, budget
    ↓
TripCreatedConfirmation: "Your first trip is ready. Explore the workbench."
    ↓
Checklist updates: "Create first trip" ✅
    ↓
Workbench becomes available with real trip data
```

**Acceptance Criteria:**
- [ ] Owner lands in workspace immediately after signup (no setup gates)
- [ ] Empty state is welcoming and actionable (not a blank screen)
- [ ] "New Trip" CTA is the most prominent element
- [ ] Manual trip form captures: customer name, destination, start/end dates, party size, budget
- [ ] Trip appears in inbox after creation
- [ ] Checklist shows "Create first trip" as complete
- [ ] Keyboard shortcut `N` works from any workspace page
- [ ] Success metric: owner creates first trip within 5 minutes of signup

**Estimated Effort**: 4-5 days

**Dependencies**: Phase 1

---

### Phase 3: People, Team Management, and Invitation

**Goal**: Make the human governance plane operable. The owner can invite agents, agents can join, and roles are enforced.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/routers/team.py` | CRUD for team members, role changes |
| `spine_api/services/team_service.py` | Invite logic, code validation, role assignment |
| `spine_api/routers/workspace_codes.py` | Generate, list, revoke workspace codes |
| `spine_api/services/workspace_codes.py` | Code generation algorithm (syllable-based) |

**API Contract:**
- `POST /api/workspace/codes` → generates new internal/external code
- `POST /api/auth/signup` (with `workspace_code`) → joins existing agency as agent
- `PATCH /api/team/:id/role` → changes role (admin only)
- `DELETE /api/team/:id` → removes member (admin only, cannot remove owner)

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/app/settings/people/page.tsx` | Team management page |
| `frontend/src/components/team/TeamMemberList.tsx` | List with avatars, roles, status |
| `frontend/src/components/team/WorkspaceCodePanel.tsx` | Display internal/external codes with copy/regenerate |
| `frontend/src/components/team/InviteModal.tsx` | Modal for generating and sharing codes |
| `frontend/src/components/team/RoleBadge.tsx` | Visual role indicators (Owner, Admin, Agent, etc.) |
| `frontend/src/app/(auth)/join/[code]/page.tsx` | Agent signup page with pre-filled agency name from code |
| `frontend/src/components/onboarding/AgencyProfileModal.tsx` | Triggered when user clicks "Add team members" without agency name set |

**UX Flow (Owner):**
```
/workspace → Settings → People
    ↓
WorkspaceCodePanel shows: TRI-7892-PLY
    ↓
Owner copies code, shares with agent
    ↓
Agent visits /join/TRI-7892-PLY
    ↓
Code validated → shows agency name → agent creates account
    ↓
Agent appears in TeamMemberList with "Agent" role
```

**Acceptance Criteria:**
- [ ] Owner can generate internal and external workspace codes
- [ ] Codes are copyable and regeneratable (old code invalidated)
- [ ] Agent can sign up with a valid workspace code
- [ ] Agent joins the correct agency automatically
- [ ] Team list shows all members with correct roles
- [ ] Admin can change member roles (except Owner)
- [ ] Admin can remove members (except Owner)
- [ ] Agency profile modal triggers if agency name is missing when accessing team page
- [ ] Membership changes emit audit events

**Estimated Effort**: 4-5 days

**Dependencies**: Phase 1, Phase 2

---

### Phase 4: Assignment, Escalation, and Operational Routing

**Goal**: Turn assignment into a real routing system with continuity preservation.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/models/routing.py` | TripRoutingState model |
| `spine_api/routers/assignments.py` | Assign, claim, handoff, escalate, reassign endpoints |
| `spine_api/services/routing_service.py` | Business logic for routing state transitions |
| `spine_api/services/sla_service.py` | SLA tracking: ownership SLA, review SLA, handoff SLA |
| `spine_api/routers/review_queue.py` | Review queue for low-confidence trips and junior agent actions |

**Routing State Machine:**
```
Unassigned
    ↓ [assign] / [claim]
Assigned (primary_assignee set)
    ↓ [escalate]
Escalated (escalation_owner added, primary_assignee preserved)
    ↓ [reassign]
Reassigned (handoff_history updated, new primary_assignee)
    ↓ [return_for_changes]
Returned (back to assigned, with reviewer notes)
```

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/components/routing/AssignmentPanel.tsx` | Trip-level assignment controls |
| `frontend/src/components/routing/ClaimButton.tsx` | Allow senior agents to claim unassigned trips |
| `frontend/src/components/routing/EscalateButton.tsx` | Escalate with reason, preserve assignee |
| `frontend/src/components/routing/HandoffRequest.tsx` | Request reassignment with context |
| `frontend/src/components/routing/ReviewQueue.tsx` | Owner/admin view of trips needing review |
| `frontend/src/components/routing/SLAIndicator.tsx` | Time-badges for ownership/review/handoff SLAs |
| `frontend/src/app/inbox/page.tsx` | Inbox with routing state indicators |

**Acceptance Criteria:**
- [ ] Trip can be assigned to an agent (admin action)
- [ ] Unassigned trips can be claimed by senior agents
- [ ] Escalation adds escalation_owner without removing primary_assignee
- [ ] Reassignment is explicit, audited, and updates handoff_history
- [ ] Review queue shows trips with: low confidence, junior agent actions, escalated items
- [ ] SLA indicators show time elapsed for ownership, review, and handoff
- [ ] Routing state is visible in trip workspace
- [ ] All routing actions emit audit events

**Estimated Effort**: 5-6 days

**Dependencies**: Phase 1, Phase 3

---

### Phase 5: Settings Control Center

**Goal**: Ship the real governance surface at `/settings` with all subroutes.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/routers/settings.py` | Unified settings router |
| `spine_api/services/settings_service.py` | Settings CRUD with change tracking |
| `spine_api/models/settings.py` | SettingsAuditLog model |

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/app/settings/layout.tsx` | Settings shell with sidebar navigation |
| `frontend/src/components/settings/SettingsNav.tsx` | Sidebar with all 8 subroutes |
| `frontend/src/app/settings/profile/page.tsx` | Personal profile editing |
| `frontend/src/app/settings/agency/page.tsx` | Agency name, email, phone, logo, timezone, currency |
| `frontend/src/app/settings/people/page.tsx` | (Already built in Phase 3, enhance with audit trail) |
| `frontend/src/app/settings/assignments/page.tsx` | Routing rules, escalation defaults, claim policy |
| `frontend/src/app/settings/pipeline/page.tsx` | D1 autonomy matrix, stage rules, operational parameters |
| `frontend/src/app/settings/integrations/page.tsx` | External systems placeholder (future: WhatsApp, email) |
| `frontend/src/app/settings/audit/page.tsx` | Settings change audit log |
| `frontend/src/components/settings/SettingsAuditLog.tsx` | Table of who changed what and when |

**Acceptance Criteria:**
- [ ] `/settings` has consistent shell + sidebar navigation
- [ ] Each subroute is gated by minimum role (Viewer cannot access Owner routes)
- [ ] Agency settings can be updated by Admin+
- [ ] Pipeline settings can be updated by Owner only
- [ ] Settings changes are logged with user_id, timestamp, old_value, new_value
- [ ] Audit log is viewable by Owner
- [ ] No more governance hidden in workbench drawers

**Estimated Effort**: 4-5 days

**Dependencies**: Phase 1, Phase 3, Phase 4

---

### Phase 6: AI Workforce Governance

**Goal**: Make AI workers first-class governed actors with explicit policies.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/models/ai_workforce.py` | AIWorkerConfig model |
| `spine_api/routers/ai_workforce.py` | CRUD for worker configurations |
| `spine_api/services/ai_workforce_service.py` | Worker registry, policy enforcement |
| `spine_api/core/ai_policy.py` | Decorator to check worker permissions before AI actions |

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/app/settings/ai-workforce/page.tsx` | AI workforce roster |
| `frontend/src/components/ai-workforce/WorkerCard.tsx` | Individual worker config card |
| `frontend/src/components/ai-workforce/WorkerToggle.tsx` | Enable/disable with confirmation |
| `frontend/src/components/ai-workforce/ScopeSelector.tsx` | Stage scope, action mode, visibility scope |
| `frontend/src/components/ai-workforce/WorkerAuditLog.tsx` | Worker action history |

**Acceptance Criteria:**
- [ ] Owner/Admin can view all 7 canonical worker types
- [ ] Each worker shows: enabled status, allowed stages, action mode, visibility scope
- [ ] Workers can be enabled/disabled by Admin+
- [ ] Workers with `commercial_sensitive` access are flagged visually
- [ ] Worker actions are logged with timestamp, input, output, and decision
- [ ] UI explains what each worker can and cannot do (permission glossary)

**Estimated Effort**: 4-5 days

**Dependencies**: Phase 1, Phase 5

---

### Phase 7: Adaptive Governance & Override Learning

**Goal**: Let the system suggest governance changes from evidence, with owner approval required.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/services/adaptive_governance.py` | Pattern detection from override events |
| `spine_api/models/adaptive.py` | PolicySuggestion model |
| `spine_api/routers/adaptive.py` | Suggestion inbox, approve/reject endpoints |
| `spine_api/core/event_bus.py` | D5 override event bus (publish/subscribe) |

**Frontend Deliverables:**

| File | Purpose |
|------|---------|
| `frontend/src/app/settings/adaptive/page.tsx` | Suggestion inbox |
| `frontend/src/components/adaptive/SuggestionCard.tsx` | Evidence + proposed change + approve/reject |
| `frontend/src/components/adaptive/GovernanceInsights.tsx` | Charts: override frequency by worker, over-review rate |

**Acceptance Criteria:**
- [ ] System captures override events with context (trip type, worker, stage, reason)
- [ ] System detects patterns: "intake_extractor overridden 15x on family trips"
- [ ] Suggestions appear in inbox with evidence and proposed policy change
- [ ] Owner can approve or reject each suggestion
- [ ] Approved suggestions update the relevant policy config
- [ ] Rejected suggestions are archived with reason
- [ ] No policy changes without owner approval

**Estimated Effort**: 5-6 days

**Dependencies**: Phase 5, Phase 6

---

### Phase 8: Data Migration & Persistence Hardening

**Goal**: Complete the transition from JSON file persistence to PostgreSQL for all operational data.

**Backend Deliverables:**

| File | Purpose |
|------|---------|
| `spine_api/models/trip.py` | Full SQLAlchemy Trip model (migrate from JSON) |
| `spine_api/models/assignment.py` | Assignment model (migrate from JSON) |
| `spine_api/models/audit.py` | AuditEvent model (migrate from JSON) |
| `spine_api/repositories/trip_repository.py` | Trip CRUD with agency scoping |
| `spine_api/repositories/assignment_repository.py` | Assignment CRUD with agency scoping |
| `spine_api/repositories/audit_repository.py` | Audit CRUD with agency scoping |
| `spine_api/services/migration_service.py` | One-time migration: JSON files → Postgres |
| `spine_api/core/rls.py` | PostgreSQL RLS policy setup |

**Migration Strategy:**
```
1. Deploy new SQLAlchemy models alongside existing JSON stores
2. Write to BOTH JSON and Postgres (dual-write mode)
3. Run backfill migration: JSON files → Postgres
4. Verify data integrity (count match, sample validation)
5. Switch reads to Postgres
6. Remove JSON writes
7. Archive JSON files
```

**PostgreSQL RLS Policies:**
```sql
-- Example RLS policy for trips
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON trips
    USING (agency_id = current_setting('app.current_agency_id')::UUID);

-- Set agency_id per request
SET LOCAL app.current_agency_id = '<agency_id>';
```

**Acceptance Criteria:**
- [ ] All trips stored in Postgres with agency_id
- [ ] All assignments stored in Postgres with agency_id
- [ ] All audit events stored in Postgres with agency_id
- [ ] JSON file writes removed (reads kept as fallback during transition)
- [ ] RLS policies active on all tenant-scoped tables
- [ ] Migration script runs without data loss
- [ ] Query performance is equal or better than JSON file I/O
- [ ] Connection pooling configured (asyncpg pool size: 20)
- [ ] Backup strategy documented: Render automated backups + daily S3/R2 export

**Estimated Effort**: 5-7 days

**Dependencies**: Phase 0, Phase 1, Phase 4

---

## 7. Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Auth middleware breaks existing API consumers | High | Phase 1 applies auth to all routes simultaneously with frontend update. No external API consumers exist yet. |
| Password hashing performance | Low | bcrypt 12 rounds is standard (~250ms/hash). Async execution prevents blocking. |
| Tenant isolation bypass | Critical | RLS as defense-in-depth. Integration tests that verify cross-tenant access returns 403. |
| Data loss during JSON→Postgres migration | Critical | Dual-write during transition. Backfill script with validation. Keep JSON files until verification complete. |
| Custom JWT security vulnerability | Medium | Use HS256 with strong secret (32+ random bytes). Rotate secret documented. No custom crypto. |
| Frontend auth state desync | Medium | Zustand store subscribes to token changes. Middleware validates session on route change. |
| Role permission too rigid | Medium | Start with 5 roles. Permission system designed for extension (add roles without schema change). |
| Workspace code brute force | Low | Codes are 12-character syllable combinations (~40^2 * 10^4 = 16M possibilities). Rate limit on `/join/:code`. |

---

## 8. Cross-Reference Map

| Topic | Primary Doc | This Roadmap Section |
|-------|-------------|----------------------|
| Governance phases (0-8) | `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md` | All phases align 1:1 |
| Onboarding UX design | `frontend/docs/DESIGN_BRIEF_Onboarding_Flow.md` | Phase 2, Phase 3 |
| Auth gap analysis | `Docs/DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md` | Phase 0, Phase 1 |
| Persistence gaps | `Docs/BACKEND_MISSING_PERSISTENCE_STATE_2026-04-18.md` | Phase 0, Phase 8 |
| Access control model | `Docs/MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md` | Section 2.4, Phase 1 |
| Stack recommendation | `Docs/TECHNICAL_INFRASTRUCTURE.md` | Section 2.2 |
| Current gap analysis | `Docs/APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md` | Executive Summary |
| Canonical role matrix | `Docs/CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md` | Section 2.4 |
| Assignment state machine | `Docs/ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md` | Phase 4 |
| AI workforce registry | `Docs/AI_WORKFORCE_REGISTRY_CONTRACT_2026-04-22.md` | Phase 6 |

---

## 9. Immediate Next Actions

To begin implementation:

1. **Add dependencies** to `pyproject.toml`: `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pyjwt`, `bcrypt`, `python-multipart`
2. **Set up local PostgreSQL** (Docker Compose or local install)
3. **Initialize Alembic**: `alembic init alembic`
4. **Create `spine_api/core/database.py`** with async engine and session factory
5. **Create `spine_api/models/tenant.py`** with Agency, User, Membership, WorkspaceCode
6. **Generate first migration**: `alembic revision --autogenerate -m "init tenant schema"`
7. **Create `spine_api/core/security.py`** with bcrypt + JWT utilities
8. **Create `spine_api/core/auth.py`** with FastAPI dependencies

These 8 steps complete Phase 0 foundation and enable Phase 1 auth routes.

---

*This is a living document. Update it when architecture decisions change, phases ship, or new constraints emerge. Preserve history — do not silently rewrite.*
