# Discovery Gap Analysis: Auth/Identity & Multi-Agent

**Date**: 2026-04-16
**Gap Register**: #08 (P1 — who is who, who can do what)
**Scope**: User authentication, role-based access control, multi-tenant isolation, agent identity, trip assignment, internal vs. traveler boundary. NOT: LLM integration (#07), customer portal auth (future phase).

---

## 1. Executive Summary

The system has a sophisticated information-flow control model (`AuthorityLevel`, `OwnerConstraint.visibility`, `INTERNAL_ONLY_FIELDS`, traveler-safe sanitization) but **zero user authentication**. There is no login, no session, no JWT, no role enforcement, no tenant isolation, no middleware. The `model_client` of authority is data provenance (who said what, at what confidence level), not user identity (who is logged in, what they can see).

The frontend has extensive governance types defined (`UserRole`, `TeamMember`, `ApprovalThreshold`, `AuditEvent`) with hooks and API clients — but the backend they call returns empty data because no auth endpoints exist. The system knows what data should be internal-only vs. traveler-safe, but has no concept of WHO is viewing it.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What It Says | Location |
|-----|-------------|----------|
| `MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md` (510 lines) | Full 4-layer access model: Agency (tenant), Agency User, Customer Portal, Vendor. Role system: owner/agent/junior/viewer with granular permissions. JWT auth flow. DB schema: `agency_users` table. Customer portal: Magic Link (MVP), Phone+OTP (Phase 2). 7 explicit "Next Steps" | Docs/ |
| `TECHNICAL_INFRASTRUCTURE.md` | Recommends **Clerk** (or Auth0) for auth: drop-in, handles OAuth/magic links, free tier generous. "Create Clerk account for auth" in quick start. | Docs/ |
| `UX_TECHNICAL_ARCHITECTURE.md` | WebSocket-based customer updates, `get_customer_history()` API, `customer_id` throughout frontend models. Multi-agent sync via `/ws/customer/{customer_id}` with `agent_id` in updates. | Docs/ |
| `DISCOVERY_GAP_DATA_PERSISTENCE_2026-04-16.md` L97 | PC-02: "Customer lookup / repeat detection" — keyword-based, no DB. `customers` table schema defined but not implemented. PS-05: "No session/auth persistence". | Docs/ |
| `DISCOVERY_GAP_COMMUNICATION_CHANNELS_2026-04-16.md` | Customer portal at `/trip/[shareToken]` — ShareToken links (no login) for MVP. CM-04 (Internal Comms) blocked by #08 (auth/sessions). | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS_2026-04-16.md` L44 | "No `customer_id`, no history lookup, no repeat detection". "No user sessions/auth — no login, no JWT, no cookies". "Permission model — Who can do what" listed as missing. | Docs/ |

### What's Implemented

| Code | What It Does | Status |
|------|-------------|--------|
| `safety.py` (545 lines) | `INTERNAL_ONLY_FIELDS`, `FORBIDDEN_TRAVELER_CONCEPTS`, `SanitizedPacketView`, `sanitize_for_traveler()`, `check_no_leakage()`, `enforce_no_leakage()` | **Working** — information-flow control, not user auth |
| `packet_models.py` | `AuthorityLevel` hierarchy (manual_override > explicit_user > ... > unknown), `OwnerConstraint.visibility` ("internal_only" vs "traveler_safe_transformable"), `SourceEnvelope.actor_type` ("agent" | "traveler" | "owner" | "system") | **Working** — data provenance, not access control |
| `spine_api/server.py` | FastAPI app with CORS middleware (permissive `allow_origins=["*"]`) | **No auth** — all endpoints unauthenticated |
| `persistence.py` (246 lines) | JSON file I/O for trips, assignments, audit events | **No auth** — no multi-user isolation |
| `frontend/src/types/governance.ts` (319 lines) | `UserRole`, `TeamMember`, `ApprovalThreshold`, `AuditEvent` TypeScript types | **Types only** — no backend enforcement |
| `frontend/src/lib/governance-api.ts` (262 lines) | API client for reviews, team management, inbox, audit, settings | **API calls exist** — backend endpoints return nothing |
| `frontend/src/hooks/useGovernance.ts` (567 lines) | `useReviews`, `useTeamMembers`, `useWorkloadDistribution`, etc. | **Hooks exist** — data is empty because backend has no auth/users |

### What's NOT Implemented

- No login/logout/token refresh endpoints
- No JWT middleware or session management
- No user database (no `agency_users`, no `customers` table)
- No role-based access control enforcement
- No tenant isolation middleware
- No rate limiting
- No customer portal auth (no share tokens, no magic links)
- No agent assignment model (backend)
- No inbox routing to specific agents
- No approval gating for junior agents
- No API key management for vendor access
- No multi-tenant data scoping
- No audit log of WHO did WHAT (only data provenance of where data came from)

---

## 3. Gap Taxonomy

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **AU-01** | User authentication system | None — no login, no JWT, no sessions | All user-specific features |
| **AU-02** | Role-based access control | Frontend types defined, zero backend enforcement | Owner/agent/viewer permissions, approval gating |
| **AU-03** | Multi-tenant isolation | None — all data is global, no `tenant_id` scoping | Multi-agency deployment |
| **AU-04** | Agent identity & assignment | `AssignmentStore` in JSON only, `governance.ts` types only | Trip ownership, inbox routing, workload balancing |
| **AU-05** | Customer portal auth | None — no share tokens, no magic links, no portal | Client-facing trip status |

### Computation Gaps

| Gap ID | What Needs Computing | Current State | Blocked By |
|--------|---------------------|---------------|------------|
| **AC-01** | Permission check on API routes | No auth middleware, all routes open | AU-01 |
| **AC-02** | Tenant data scoping (only see your agency's data) | No tenant_id, no scoping | AU-01, AU-03 |
| **AC-03** | Agent workload calculation | Frontend hooks defined, backend returns empty | AU-04 |
| **AC-04** | Approval gating for low-confidence decisions | Frontend types defined, no backend logic | AU-02 |
| **AC-05** | Owner review queue | Frontend hooks defined, no backend data | AU-02 |

### Integration Gaps

| Gap ID | Connection | Status | Blocked By |
|--------|-----------|--------|------------|
| **AI-01** | Auth middleware → API routes | No middleware exists | AU-01 |
| **AI-02** | User session → LifecycleInfo population | No session, LifecycleInfo always empty | AU-01, #06 |
| **AI-03** | Agent identity → Trip assignment | No agent identity model | AU-04 |
| **AI-04** | Tenant isolation → Trip/Customer queries | No tenant scoping | AU-03 |
| **AI-05** | Owner review queue → Decision confidence | Frontend expects review queue, backend doesn't enforce | AU-02 |

---

## 4. Data Model

```python
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from datetime import datetime

@dataclass
class AgencyUser:
    """From MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md spec."""
    id: str
    agency_id: str
    email: str
    name: str
    role: Literal["owner", "manager", "agent", "viewer"]
    permissions: List[str] = field(default_factory=list)  # ["packets:read", "packets:write", ...]
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login_at: Optional[str] = None
    
@dataclass
class Agency:
    """Multi-tenant agency entity."""
    id: str
    name: str
    slug: str  # URL-friendly identifier
    plan: str = "starter"  # "starter" | "professional" | "enterprise"
    settings: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

# Role Permission Matrix (from MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md)
ROLE_PERMISSIONS = {
    "owner": ["*"],  # All permissions
    "manager": [
        "team:manage", "packets:read", "packets:write", "packets:delete",
        "reports:read", "settings:read", "settings:write",
        "customers:read", "customers:write",
        "trips:read", "trips:write", "trips:assign",
    ],
    "agent": [
        "packets:read", "packets:write",
        "customers:read", "customers:write",
        "trips:read", "trips:write",
    ],
    "viewer": [
        "packets:read", "customers:read", "trips:read", "reports:read",
    ],
}

@dataclass
class AuthConfig:
    """Auth configuration for MVP."""
    provider: str = "clerk"  # "clerk" | "auth0" | "custom_jwt"
    clerk_frontend_api: str = ""
    clerk_secret_key: str = ""
    session_duration_hours: int = 24
    require_email_verification: bool = True
    
@dataclass
class ShareToken:
    """Customer portal access — no login required."""
    token: str
    trip_id: str
    customer_id: str
    created_by: str  # agent_id who shared
    expires_at: Optional[str] = None  # None = no expiry
    view_only: bool = True  # Customers can view but not edit
```

---

## 5. Phase-In Recommendations

### Phase 1: Agent Auth + Role System (P0, ~3-4 days, blocked by #02)

1. **Integrate Clerk for agency user auth** — following TECHNICAL_INFRASTRUCTURE recommendation
2. **Add `agency_users` table** — id, agency_id, email, role, permissions, timestamps
3. **Add `agencies` table** — id, name, slug, plan, settings
4. **Implement JWT middleware** — protect all API routes, extract user from token
5. **Implement role-based permission checks** — `require_permission("packets:write")` decorator
6. **Add agent identity to trip creation** — `agent_id` field populated from JWT session
7. **Wire existing safety.py** — use `actor_type` from session instead of hardcoded values

**Acceptance**: Agent logs in via Clerk, JWT token on every request, role-based permissions enforced. Owner sees all trips, agent sees only assigned trips, viewer sees read-only. No anonymous access to API.

### Phase 2: Trip Assignment + Workload Distribution (P1, ~2-3 days, blocked by Phase 1)

1. **Add `agent_id` to trips table** — who is assigned to this trip
2. **Implement inbox routing** — new trips auto-assigned based on workload or manually by owner
3. **Implement workload balancing** — `GET /api/team/workload` returns real data
4. **Implement owner review queue** — trips with confidence < threshold flagged for owner review
5. **Wire frontend governance hooks** to real backend data

**Acceptance**: Owner can assign trips to agents. Agent dashboard shows only their trips. Owner review queue shows trips needing approval. Workload distribution shows real numbers.

### Phase 3: Customer Portal + Share Tokens (P2, ~2-3 days, blocked by #02, #03)

1. **Implement ShareToken generation** — agent creates shareable link for client
2. **Add `/trip/[shareToken]` route** — client views trip status without login
3. **View-only enforcement** — customer portal shows traveler-safe view only
4. **Token expiry** — configurable expiry, optional
5. **Wire to safety.py** — share token view uses `sanitize_for_traveler()` automatically

**Acceptance**: Agent clicks "Share with client" → generates link. Client opens link → sees trip status, itinerary, financial summary (traveler-safe only). No internal data leaked.

### Phase 4: Multi-Tenant Isolation (P2, ~2-3 days, blocked by Phase 1)

1. **Add tenant_id scoping to all queries** — agency_id filter on every DB query
2. **Implement row-level security** — PostgreSQL RLS policies for agency isolation
3. **Add agency settings** — per-agency configuration (default margins, preferred suppliers, branding)
4. **Add vendor API keys** — agencies can configure their own supplier integrations

**Acceptance**: Agency A cannot see Agency B's data. All queries scoped to authenticated user's agency.

---

## 6. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| Auth provider | (a) Clerk (managed), (b) Auth0 (managed), (c) Custom JWT, (d) Supabase Auth | **(a) Clerk** — matches TECHNICAL_INFRASTRUCTURE recommendation, drop-in, free tier generous | AU-01 |
| Permission model | (a) Role-based (4 roles), (b) Resource-based (granular), (c) Both (role-based MVP, resource-based later) | **(c) Role-based for MVP, migrate to resource-based** | AU-02 |
| Agent assignment | (a) Owner assigns manually, (b) Auto-assign by workload, (c) Manual with auto-suggestion | **(c) Manual with workload display** — owner decides, system shows current workload | AU-04 |
| Customer portal auth | (a) ShareToken (no login), (b) Phone+OTP, (c) Email+Password, (d) Magic Link | **(a) ShareToken for MVP** — simplest, matches agency workflow where agent shares link | AU-05 |
| Multi-tenant approach | (a) Shared DB with tenant_id, (b) Separate DB per agency, (c) Shared DB with RLS | **(a) Shared DB with tenant_id for MVP**, add RLS later for security | AU-03 |
| Junior agent approval | (a) All actions need approval, (b) Only low-confidence actions, (c) Configurable threshold | **(b) Only low-confidence actions** — confidence < threshold triggers review queue | AU-02 |

---

## 7. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Clerk vendor lock-in | Medium | Auth interface abstracted behind provider protocol. Migration path documented. JWT tokens are standard. |
| Role permissions too rigid for real agency workflows | Medium | Start with 4 roles (owner/manager/agent/viewer), add custom permissions later. Agency owners can configure per-agent. |
| Customer share tokens leak | High | Tokens are short-lived, single-trip scoped, view-only. Revoke tokens from agent dashboard. Audit all token access. |
| Multi-tenant data leakage | Critical | Row-level security from Phase 4. Integration tests that verify cross-tenant isolation. Regular security audits. |
| Agency onboarding friction | Medium | Clerk handles email verification, magic links, social login. Owner creates agent accounts. Minimize steps to first trip. |

---

## 8. What's Out of Scope

- Vendor portal authentication (API key only for MVP)
- Social login (Clerk provides, but not priority)
- Two-factor authentication enforcement (optional in Phase 2)
- SSO/SAML integration (enterprise only, much later)
- Customer account creation (ShareToken access only for MVP)
- Audit log frontend (data model exists, UI later)
- Granular resource-level permissions (role-based for MVP, resource-based later)