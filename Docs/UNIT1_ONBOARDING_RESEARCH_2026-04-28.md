# Unit-1: Onboarding & Workspace UI (AUTH-02) — Research & Findings

**Date:** April 28, 2026  
**Status:** Research Complete — Pending Decision  
**Researcher:** opencode

---

## Executive Summary

The Unit-1 ticket requests implementation of multi-step onboarding and workspace join flows. Research reveals a **significant discrepancy**: the current codebase already has a functioning single-step signup flow that creates agency + owner. The requested multi-step onboarding and workspace join features are **not in the master roadmap**.

| Aspect | Current State | Ticket Request |
|--------|---------------|----------------|
| Signup Flow | Single-step form (`/signup`) | Multi-step (`/onboarding`) |
| Agency Creation | Auto-created from signup | Step 1: Agency Info |
| User Creation | Inline with signup | Step 2: Admin User |
| Workspace Setup | Auto-generated code | Step 3: Workspace Setup |
| Join Workspace | **Missing** | Implement via WorkspaceCode |
| Backend Router | `auth.py` + `workspace.py` | New `tenant.py` router |

---

## 1. Current Codebase State

### 1.1 Backend — What Exists

**File:** `spine_api/routers/auth.py` (267 lines)
- `POST /api/auth/signup` — Creates User + Agency + Membership (owner) + WorkspaceCode
- `POST /api/auth/login` — Authenticates, sets httpOnly cookies
- `POST /api/auth/logout` — Clears auth cookies
- `GET /api/auth/me` — Returns current user + agency + membership
- `POST /api/auth/refresh` — Refreshes access token
- `POST /api/auth/request-password-reset` — Initiates reset flow
- `POST /api/auth/confirm-password-reset` — Completes reset flow

**File:** `spine_api/services/auth_service.py` (373 lines)
- `signup()` function (lines 47-148):
  - Creates `User` with bcrypt password hashing
  - Creates `Agency` with slug derived from name
  - Creates `Membership` with role="owner", is_primary=True
  - Creates `WorkspaceCode` with format `WP-{token}` for agent invites
  - Generates JWT access + refresh tokens
  - Detects test users by `@test.com` email domain

**File:** `spine_api/models/tenant.py` (161 lines)
- `Agency` — id, name, slug, email, phone, logo_url, plan, is_test, settings
- `User` — id, email, password_hash, name, is_active, last_login_at
- `Membership` — id, user_id, agency_id, role, is_primary
- `WorkspaceCode` — id, agency_id, code, code_type, status, created_by, used_by, used_at
- `PasswordResetToken` — id, user_id, token_hash, expires_at, used_at

**File:** `spine_api/routers/workspace.py` (56 lines)
- `GET /api/workspace` — Returns current agency workspace
- `PATCH /api/workspace` — Updates agency fields (name, email, phone, logo_url)

**Missing:** `spine_api/routers/tenant.py` — No dedicated tenant management router exists.

### 1.2 Frontend — What Exists

**File:** `frontend/src/app/(auth)/signup/page.tsx` (140 lines)
- Single-step signup form with fields:
  - Full name (optional)
  - Work email (required)
  - Password (required, min 8 chars)
  - Agency name (optional, expandable)
- On submit: calls `POST /api/auth/signup`, rehydrates auth, redirects to `/overview`
- Uses `useAuthStore` for state management
- Uses `api` client from `@/lib/api-client`

**File:** `frontend/src/app/overview/page.tsx` (572 lines)
- Dashboard with stats cards (Active Trips, Pending Triage, Ready to Book, Needs Attention)
- Recent trips list with links to `/workspace/[tripId]`
- Pipeline progress bar (collapsible)
- Quick navigation to Inbox, Trip Workspace, Reviews

**Missing:**
- `frontend/src/app/(auth)/onboarding/page.tsx` — Multi-step onboarding page
- `frontend/src/components/auth/OnboardingForm.tsx` — Multi-step form component
- Join Workspace page/component
- Any reference to "onboarding" in the frontend

### 1.3 Test Coverage

**File:** `frontend/src/app/__tests__/p2_owner_onboarding_journey.test.tsx` (340 lines)
- Tests P2 scenario (Owner Onboarding Journey)
- Tests: IntakePanel → DecisionPanel → SuitabilityPanel
- Mocks: useWorkbenchStore, useSpineRun, useTrips, useFieldAuditLog
- **Note:** This is NOT testing the signup/onboarding flow — it tests the trip decision workflow after onboarding.

**File:** `Docs/TEST_CASE_STUDY_SIGNUP_FLOWS.md` (259 lines)
- Documents test user flow (`@test.com` → mock data)
- Documents real user flow (blank slate)
- Documents existing user login
- **No mention of multi-step onboarding**

---

## 2. Discrepancy Analysis

### 2.1 Roadmap Mismatch

The Unit-1 ticket references "onboarding & workspace UI" but the **Master Roadmap** (`Docs/MASTER_PHASE_ROADMAP.md`) shows:

| Phase | Focus | Status |
|-------|--------|--------|
| Phase 1 | Foundation & Traceability | Done |
| Phase 2 | System Integrity & Cockpit | Active |
| Phase 3 | Agentic Autonomy | Pending |
| Phase 4 | LLM Cost & Per-Agency Controls | Partial |

**The master roadmap does NOT include "Unit-1: Onboarding & Workspace UI (AUTH-02)" as a tracked task.**

### 2.2 Agency Onboarding Readiness Checklist

**File:** `Docs/AGENCY_ONBOARDING_READINESS_CHECKLIST_2026-04-27.md` (543 lines)
- Status: ❌ NOT READY for agency partner launch
- 18 critical gaps identified
- P1-02: Agency Operator Dashboard (Missing entirely)
- P2-01: Agency Setup Wizard (Missing entirely)
- **No mention of multi-step onboarding form**

The checklist assumes a single-step signup exists and focuses on post-signup configuration.

---

## 3. Required Implementation (If Proceeding)

### 3.1 Backend — New `spine_api/routers/tenant.py`

```python
"""
Tenant router — agency creation, workspace codes, member management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from spine_api.core.database import get_db
from spine_api.core.auth import get_current_user, get_current_agency_id
from spine_api.services.tenant_service import (
    create_workspace_code,
    join_workspace,
    list_agency_members,
    remove_member,
)

router = APIRouter(prefix="/api/tenant", tags=["tenant"])

# POST /api/tenant/join — Join existing workspace via code
# GET /api/tenant/members — List agency members
# POST /api/tenant/members — Invite new member
# DELETE /api/tenant/members/{user_id} — Remove member
# POST /api/tenant/workspace-codes — Generate new invite code
# GET /api/tenant/workspace-codes — List active codes
```

**Note:** `tenant_service.py` would also need to be created (or add to `auth_service.py`).

### 3.2 Frontend — New Files

**`frontend/src/app/(auth)/onboarding/page.tsx`**
- 3-step form using `react-hook-form` or similar:
  - Step 1: Agency Info (name, email, phone, logo)
  - Step 2: Admin User (name, email, password)
  - Step 3: Workspace Setup (confirm code, review)
- Progress indicator
- Back/Next navigation
- On complete: call signup API, redirect to `/overview`

**`frontend/src/components/auth/OnboardingForm.tsx`**
- Multi-step form component
- State management for current step
- Validation per step
- Submit handler

**`frontend/src/app/(auth)/join-workspace/page.tsx`** (New)
- Form: Enter Workspace Code
- Calls `POST /api/tenant/join`
- On success: redirect to `/overview`

### 3.3 API Endpoints Needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tenant/join` | POST | Join workspace via WorkspaceCode |
| `/api/tenant/members` | GET | List agency members |
| `/api/tenant/members` | POST | Invite member (generate code) |
| `/api/tenant/members/{id}` | DELETE | Remove member |
| `/api/tenant/workspace-codes` | GET | List active invite codes |
| `/api/tenant/workspace-codes` | POST | Generate new invite code |

---

## 4. Decision Points

### Option A: Implement as Requested
- Build multi-step onboarding
- Build join-workspace flow
- Create `tenant.py` router
- **Pros:** Matches ticket exactly
- **Cons:** Not in master roadmap, may conflict with existing single-step signup

### Option B: Enhance Existing Signup
- Keep single-step signup (it works)
- Add post-signup "Agency Setup Wizard" (P2-01 from checklist)
- Add "Join Workspace" page linked from login
- **Pros:** Aligns with master roadmap, enhances rather than replaces
- **Cons:** Doesn't match ticket exactly

### Option C: Defer to P2 (Recommended)
- Current signup flow is functional for beta/dogfood
- P2-01 (Agency Setup Wizard) in checklist covers similar ground
- Focus on Phase 2 tasks from master roadmap (System Integrity & Cockpit)
- **Pros:** Follows master roadmap, avoids duplicate work
- **Cons:** Ticket remains open

---

## 5. Recommended Next Action

**Before coding, clarify with user:**

1. Is this ticket from an older roadmap that's been superseded by `MASTER_PHASE_ROADMAP.md`?
2. Should we enhance the existing single-step signup or replace it with multi-step?
3. Is "Join Workspace" a priority over Phase 2 system integrity work?
4. Should `spine_api/routers/tenant.py` be created, or should endpoints go in existing `auth.py`/`workspace.py`?

**If proceeding with implementation:**
- Read `Docs/DEVELOPMENT_METHODOLOGY_2026-04-23.md` for coding standards
- Apply 4-Phase Workflow (Fix → Review → Audit → Handoff)
- Minimum 2 code review cycles for schema changes
- Apply `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

---

## 6. Evidence Files

| File | Relevance |
|------|-----------|
| `spine_api/routers/auth.py` | Current signup/login implementation |
| `spine_api/services/auth_service.py` | Business logic for signup (creates agency + user + membership + code) |
| `spine_api/models/tenant.py` | Data models (Agency, User, Membership, WorkspaceCode) |
| `frontend/src/app/(auth)/signup/page.tsx` | Current single-step signup form |
| `frontend/src/app/overview/page.tsx` | Post-signup destination |
| `Docs/MASTER_PHASE_ROADMAP.md` | Official roadmap (no Unit-1 reference) |
| `Docs/AGENCY_ONBOARDING_READINESS_CHECKLIST_2026-04-27.md` | Onboarding gaps (18 critical) |
| `Docs/TEST_CASE_STUDY_SIGNUP_FLOWS.md` | Signup flow test cases |

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-28  
**Next Step:** User decision on Opts A/B/C
