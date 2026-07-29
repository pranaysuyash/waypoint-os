# Onboarding & Agency Setup (#22) — Research Synthesis

**Date**: 2026-06-26
**Status**: ✅ Synthesis complete — consolidated from 7 prior documents + codebase audit
**Priority**: 🔴 High — blocks agency adoption

---

## 1. Executive Summary

Onboarding & Agency Setup is the **critical first mile** — how a new travel agency goes from signup to productive daily use. This is the make-or-break adoption flow. After synthesizing 7 prior research documents and auditing the current frontend/backend code, the verdict is:

**Current state**: The foundation exists (signup, login, workspace auto-creation, join-by-code, empty-state onboarding checklist), but the end-to-end experience has significant gaps. The product is closer to "auth + engine + shell" than to a complete agency onboarding flow.

**The critical insight**: The system has an excellent backend engine but the **business-user interfaces** for setup, team management, data import, and channel connection are still incomplete. The onboarding experience that exists (`EmptyStateOnboarding.tsx`) is a 3-step checklist — not a guided flow.

| Dimension | Status | Evidence |
|-----------|--------|----------|
| Signup/login | ✅ Working | Email/password, JWT cookies, auto-created workspace |
| Join workspace flow | ✅ Working | `/join/[code]` with WorkspaceCode validation |
| Post-signup guidance | 🟡 Partial | `EmptyStateOnboarding` component on `/overview` |
| Team management | 🟡 Partial | PeopleTab with WorkspaceCodePanel, role changes |
| Agency profile setup | ⬜ Missing | No setup wizard or guided profile configuration |
| Data import | ⬜ Missing | No Excel/CSV/email import tooling |
| Channel connection | ⬜ Missing | No WhatsApp/email/SMS integration setup UX |
| First-use guided trip | 🟡 Partial | Workbench works, but no "process your first inquiry" tutorial |
| Training mode | ⬜ Missing | No in-app guidance for junior agents |
| Resumable setup state | ⬜ Missing | Interrupted wizard state not persisted |

---

## 2. Existing Assets — What's Already Built

### 2.1 Auth & Workspace Foundation (✅ Working)

The following backend and frontend infrastructure is in place and operational:

| Component | Files | Status |
|-----------|-------|--------|
| **Signup** (owner) | `frontend/src/app/(auth)/signup/page.tsx`, `spine_api/routers/auth.py` | ✅ Creates User + Agency + Membership (Owner) |
| **Login** | `frontend/src/app/(auth)/login/page.tsx` | ✅ JWT cookie-based session |
| **Join workspace** (agent) | `frontend/src/app/(auth)/join/[code]/page.tsx`, `spine_api/routers/auth.py` | ✅ Validates WorkspaceCode, joins existing agency |
| **Auth middleware** | `spine_api/core/middleware.py`, `spine_api/core/auth.py` | ✅ Cookie-based JWT, redirects for unauthenticated |
| **Auth state** | `frontend/src/lib/bff-auth.ts`, Zustand store | ✅ Session hydration, refresh tokens |
| **Agency model** | `spine_api/models/tenant.py` — Agency, User, Membership, WorkspaceCode | ✅ SQLAlchemy with RLS |
| **Team management** | `frontend/src/app/(agency)/settings/components/PeopleTab.tsx` | ✅ Member list, role changes, invite code generation |
| **Workspace codes** | `frontend/src/lib/governance-api.ts` | ✅ Generate, list, copy invite codes |
| **Empty state** | `frontend/src/components/overview/EmptyStateOnboarding.tsx` | ✅ 3-step checklist: invite team → add inquiry → review inbox |
| **Settings tabs** | Profile, People, AiAgent, Guard, Comm, Support, Seasonal | ✅ Basic per-tab settings |

### 2.2 Key Architectural Decisions (Locked)

From `ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md`:

- **Auth**: Custom JWT (HS256) with bcrypt password hashing. Clerk deferred until revenue stage.
- **Database**: PostgreSQL + SQLAlchemy 2.0 async + Alembic migrations.
- **Tenant Model**: Shared database with `agency_id` scoping + PostgreSQL Row-Level Security (RLS).
- **Onboarding**: Full first-trip experience — signup → workspace → empty state → manual trip creation → progressive disclosure.
- **Governance**: 5 canonical roles (Owner, Admin, SeniorAgent, JuniorAgent, Viewer) with full assignment/escalation/review engine.

### 2.3 Current Onboarding Flow (As-Is)

```
Signup → /overview (empty state)
    ↓
EmptyStateOnboarding shows 3 steps:
  1. Invite your team → /settings?tab=people
  2. Add your first inquiry → /workbench?draft=new&tab=intake
  3. Review in Lead Inbox → /inbox
    ↓
After first trip/lead → EmptyStateOnboarding auto-hides
    ↓
Normal workspace: overview, inbox, trips, settings
```

---

## 3. Research Synthesis — Key Findings from 7 Documents

### 3.1 From `AGENCY_ONBOARDING_READINESS_CHECKLIST_2026-04-27.md`

**Current Status**: ❌ NOT READY for agency partner launch
**Blocking Issues**: 18 critical gaps identified
**Estimated Timeline**: 8-12 weeks to launch readiness

**P1 Launch Blockers:**
1. **Customer-Facing Booking Interface** — Missing entirely. Customers cannot self-serve.
2. **Agency Operator Dashboard** — Missing entirely. Owners cannot manage business operations.
3. **Marketing Landing Page** — Missing. Cannot acquire agency partners.

**P2 Scale Enablers:**
1. **Agency Setup Wizard** — Missing. No guided agency profile, templates, or integration configuration.
2. **Trip Builder Interface** — Technical API exists, no business-user UI.
3. **Business Process Automation** — All processes currently manual.

**Key metrics from simulation (P2-TrainingProblem):**
- Junior ramp: 12 months at ₹2-3L training cost per hire
- Setup completion rate: ~40% (target >90%)
- Time-to-first-inquiry: estimated >3 days (target <2 hours)

### 3.2 From `FIRST_AGENCY_ONBOARDING_SIMULATION_2026-04-27.md`

**"Sarah Chen" simulation** — A boutique adventure travel agency owner's 47 friction points across 6 phases:

**Phase 1 (Discovery & Signup):**
- No landing page content explaining value proposition
- Previously required manual database user creation (now fixed with self-service signup)
- 3-day delay before access

**Phase 2 (Initial Configuration):**
- No guided setup flow for agency information
- No progressive disclosure of features
- 73% abandonment risk for non-technical users
- No sample data or demo trip

**Phase 3 (Trip Creation):**
- Technical JSON knowledge required for trip creation
- Activity database has no management interface
- No pricing/billing management

**Phase 4 (Customer Onboarding):**
- No customer-facing booking interface
- Manual suitability collection (email/phone)
- No integrated booking workflow
- 10-day process that should take 2 days

**Phase 5 (Operations):**
- No operational dashboard for business metrics
- Manual data entry for every interaction
- Cross-platform coordination overhead
- Limits scale to ~10 customers/month

**Phase 6 (Growth):**
- Cannot hire staff without technical training
- No analytics/reporting
- System requires API knowledge for optimal use

### 3.3 From `ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md`

**8-phase implementation plan** (Phase 0-7 complete, Phase 8 pending):

| Phase | Status | Key Deliverable |
|-------|--------|-----------------|
| 0. Foundation | ✅ Done | DB models, auth framework, Alembic |
| 1. Identity & Tenancy | ✅ Done | Signup, login, workspace creation, JWT middleware |
| 2. Onboarding & First Trip | ⬜ Not started | Empty state, checklist, manual trip form, keyboard shortcuts |
| 3. Team Management | ✅ Done | Invite codes, join flow, role management |
| 4. Assignment & Routing | ⬜ Not started | Trip assignment, escalation, SLA tracking |
| 5. Settings Control Center | 🟡 Partial | Settings shell exists, subroutes partially wired |
| 6. AI Workforce Governance | ⬜ Not started | Worker registry, policy configuration |
| 7. Adaptive Governance | ⬜ Not started | Override learning, policy suggestions |
| 8. Data Migration | ⬜ Not started | JSON → PostgreSQL for trips, assignments, audit |

**Phases 2, 4, 6, 7, 8 are unstarted** — significant work remains.

### 3.4 From `UNIT1_ONBOARDING_UX_ANALYSIS_2026-04-28.md`

**UX-first principles approach:**

| Flow | UX Verdict |
|------|-----------|
| Owner signup (single-step) | ✅ Correct (low friction) |
| Agent join (by code) | 🟡 Now works (was blocking) |
| Post-signup activation | 🟡 Weak — blank dashboard with checklist, no guided flow |
| Multi-step pre-signup | ❌ Unnecessary (adds friction before value) |

**Key recommendations adopted/remaining:**
- ✅ Single-step signup kept (correct UX decision)
- ✅ Join workspace flow built (was critical gap)
- 🟡 Post-signup activation exists but is a static checklist, not guided
- ❌ GettingStartedCard as post-signup activation not yet implemented
- ❌ Team management in Settings > People exists but could be enhanced

### 3.5 From `discussions/onboarding_2026-04-29.md`

**Solo-dev pragmatic approach:**
- `ONBOARDING_GUIDE.md` in repo root (not yet created)
- Minimal 3-tooltip system on first login (not implemented)
- SOPs for critical workflows (not implemented)
- First-login tour (3 minutes max) — not implemented

### 3.6 From `SUPPORT_AND_CUSTOMER_SUCCESS.md`

- **Onboarding**: Self-service with optional 15-min call
- **Welcome email** on signup: not implemented
- **Day 1**: Welcome email + "book a 15-min onboarding call": not implemented
- **Conversion funnel**: Visitor → Sign up (10%) → Onboarding started (60%) → First inquiry (40%)

### 3.7 From `APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md`

- Auth front door now exists (was missing when doc was written)
- Remaining gap: onboarding and workspace experience is not fully end-to-end
- `/onboarding` route: **Does not exist**
- Owner should create first trip within 5 minutes of signup: not benchmarked

---

## 4. Codebase State — Current Implementation Audit

### 4.1 Frontend Components

| Component | Status | Purpose |
|-----------|--------|---------|
| `EmptyStateOnboarding.tsx` | ✅ Built | 3-step onboarding checklist (invite → add inquiry → review) |
| `PeopleTab.tsx` → `WorkspaceCodePanel` | ✅ Built | Invite code generation and sharing |
| `PeopleTab.tsx` → member management | ✅ Built | Role badges, member removal |
| `Join/[code]/page.tsx` | ✅ Built | Agent join-by-code flow |
| Profile settings tabs | ✅ Built | Per-tab agency settings |
| `GettingStartedCard` | ❌ Missing | Post-signup guided activation (proposed but not built) |
| Setup wizard | ❌ Missing | Guided agency profile, channel connection, first trip |
| First-use tooltip system | ❌ Missing | Minimal in-app guidance on first login |
| Agent training mode | ❌ Missing | Guided workflows for junior agents |

### 4.2 Backend Routes

| Route | Status | Purpose |
|-------|--------|---------|
| `POST /api/auth/signup` | ✅ | Create account + workspace |
| `POST /api/auth/login` | ✅ | Authenticate, set JWT cookie |
| `POST /api/auth/join` | ✅ | Join existing agency via code |
| `GET /api/auth/me` | ✅ | Current user + membership |
| `GET /api/workspace` | ✅ | Current workspace details |
| `PATCH /api/workspace` | ✅ | Update agency profile |
| `GET /api/team/members` | ✅ | List team members |
| `PATCH /api/team/:id/role` | ✅ | Change member role |
| `POST /api/workspace/codes` | ✅ | Generate invite code |
| `POST /api/auth/validate-code/:code` | ✅ | Validate invite code before join |
| `POST /api/team/invite` | ✅ | Invite team member |
| Setup wizard state | ❌ Missing | Resumable onboarding progress |
| Data import | ❌ Missing | Excel/CSV/email import endpoints |
| Channel connection | ❌ Missing | WhatsApp/email integration setup |

---

## 5. Gap Analysis — What's Missing

### 5.1 Critical Gaps (Block Adoption)

| Gap | Impact | Evidence |
|-----|--------|----------|
| **No setup wizard** | Agency owner must manually configure everything | Phase 2 never implemented from roadmap |
| **No data import** | Can't migrate from Excel, WhatsApp exports, past trips | No import endpoints or UI exist |
| **No channel connection UX** | WhatsApp, email, SMS channels have no setup flow | Noted in exploration backlog |
| **No training mode** | Junior agents have no guided workflow | Directly linked to #23 Knowledge Management |
| **No resumable wizard state** | Interrupted setup requires restart | Noted in topic backlog |
| **No welcome/onboarding email** | No Day-1 engagement sequence | Noted in SUPPORT_AND_CUSTOMER_SUCCESS |
| **No first-use tooltips** | 3 tooltip system proposed but never built | UX analysis recommendation |

### 5.2 Medium Gaps (Reduce Friction)

| Gap | Impact | Notes |
|-----|--------|-------|
| **ONBOARDING_GUIDE.md** not in repo | No written guide for new agents | Solo-dev discussion doc recommendation |
| **SOPs folder** not created | No standard operating procedures | 5 critical SOPs proposed |
| **No sample/demo data** | Can't see system value without real work | First agency simulation finding |
| **No setup progress tracking** | No localStorage/backend persistence of wizard state | UX analysis recommendation |
| **Keyboard shortcuts** | `N` for new trip not implemented | Mentioned in Phase 2 roadmap |
| **First-trip creation <5 minutes** | Not benchmarked or optimized | Target from UX analysis |

### 5.3 Gaps Addressed Since Research Docs Were Written

| Original Gap | Current Status | Fix |
|-------------|---------------|-----|
| Manual DB user creation | ✅ Fixed | Self-service signup via `/signup` |
| No join-by-code flow | ✅ Fixed | `/join/[code]` with WorkspaceCode validation |
| No team management UI | ✅ Fixed | PeopleTab with member list, role changes |
| No empty state | ✅ Fixed | EmptyStateOnboarding on `/overview` |
| No workspace code generation | ✅ Fixed | WorkspaceCodePanel in PeopleTab |
| Blank dashboard post-signup | 🟡 Partial | 3-step checklist (not guided) |

---

## 6. Recommended Sequencing

### Phase 1 (Now — High Impact, Low Effort)
Build the pieces that make the existing foundation feel complete:

1. **Persist onboarding progress** — Store checklist state in localStorage so completed steps survive refresh
2. **Add welcome modal** — Show a brief "Welcome to Waypoint" modal on first login with the 3 steps
3. **Add "N" keyboard shortcut** — Global shortcut for new trip (from roadmap Phase 2)
4. **Create `ONBOARDING_GUIDE.md`** — Single-page markdown in repo root (from solo-dev discussion)
5. **Add first-trip timing metric** — Track time from signup to first inquiry processed

**Effort**: 2-3 days | **Dependencies**: None

### Phase 2 (Next — Core Setup Flow)
Build the guided agency setup experience:

1. **Agency profile setup wizard** — Guided flow: company info, branding, specialization, timezone/currency
2. **Initial trip template guidance** — "Process your first inquiry" walkthrough with sample data option
3. **Channel connection setup** — First-time prompt to connect WhatsApp/email channels
4. **Team invitation prompt** — "Invite your first agent" as part of wizard, not buried in settings
5. **Resumable wizard state** — Save progress to backend, allow resume later

**Design principles** (from UX analysis):
- Wizard must be **skippable** — power users bypass, new users follow
- **Progressive disclosure** — show next step only after current one is meaningful
- **3 minutes max** per wizard step — don't over-educate
- **Sample data option** — "Load demo data" one-click for immediate value

**Effort**: 2-3 weeks | **Dependencies**: Phase 1

### Phase 3 (Scale — Team & Operations)
Enable agency growth beyond solo operation:

1. **Assignment & routing** (Phase 4 from roadmap) — Trip assignment, escalation, SLA tracking
2. **Agent onboarding flows** — Training mode for junior agents (links to #23)
3. **Data import tooling** — Excel CSV parser, WhatsApp export importer
4. **First-use tooltip system** — 3 tooltips on first login (from UX analysis)
5. **SOPs folder** — Document 5 critical workflows

**Effort**: 4-5 weeks | **Dependencies**: Phase 2, #23 Knowledge Management

### Phase 4 (Advanced — Full Activation)
Complete the agency lifecycle:

1. **Customer-facing booking interface** (P1-01 from checklist)
2. **Agency operator dashboard** (P1-02 from checklist)
3. **Marketing landing page** (P1-03 from checklist)
4. **Advanced analytics** — Onboarding metrics dashboard
5. **Automated onboarding emails** — Day 1 welcome, Day 3 tips, Day 7 check-in

**Effort**: 6-8 weeks | **Dependencies**: Phases 1-3

---

## 7. Success Metrics

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Time from signup to first inquiry | Unknown (estimated >3 days) | <30 minutes | P1 |
| Setup wizard completion rate | ~40% (estimated) | >90% | P2 |
| Trial to first-trip capture | ~20% (estimated) | >60% | P2 |
| Time-to-first-inquiry (new agency) | Not tracked | <5 minutes | P1 |
| Team invitation rate (owner → agent) | Not tracked | >80% within 7 days | P2 |
| Channel connection rate | 0% (no UX) | >70% | P2 |
| Onboarding completion (non-technical) | Unknown | <2 hours | P2 |
| First inquiry → actionable trip | Unknown | <60 seconds | P1 |

---

## 8. Cross-Reference Map

| Document | Link | Topics Covered |
|----------|------|----------------|
| Onboarding Readiness Checklist | `Docs/AGENCY_ONBOARDING_READINESS_CHECKLIST_2026-04-27.md` | P1-P3 priorities, success metrics, risk management |
| First Agency Onboarding Simulation | `Docs/FIRST_AGENCY_ONBOARDING_SIMULATION_2026-04-27.md` | 47 friction points across 6 phases, "Sarah Chen" journey |
| Auth/Workspace Multi-Tenant Roadmap | `Docs/ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md` | 8-phase implementation plan, data model, API contracts |
| UX Analysis | `Docs/UNIT1_ONBOARDING_UX_ANALYSIS_2026-04-28.md` | UX-first principles, join flow, post-signup activation |
| Solo-Dev Discussion | `Docs/discussions/onboarding_2026-04-29.md` | Lean onboarding, tooltips, SOPs, first-login tour |
| App State Analysis | `Docs/APP_STATE_ANALYSIS_MISSING_FRONT_DOOR_2026-04-23.md` | Pre-auth gap analysis (historical) |
| Support & Customer Success | `Docs/SUPPORT_AND_CUSTOMER_SUCCESS.md` | Onboarding email sequence, support model |
| Knowledge Management (#23) | `Docs/exploration/KNOWLEDGE_MANAGEMENT_TRAINING_SYNTHESIS_2026-06-26.md` | Training mode, junior ramp, override learning |
| Exploration Master Index | `Docs/EXPLORATION_TOPICS.md` | Topic #22 entry, related topics |
| Frontend EmptyStateOnboarding | `frontend/src/components/overview/EmptyStateOnboarding.tsx` | Current 3-step checklist implementation |
| Settings PeopleTab | `frontend/src/app/(agency)/settings/components/PeopleTab.tsx` | WorkspaceCodePanel, team management UI |
| Join page | `frontend/src/app/(auth)/join/[code]/page.tsx` | Agent join-by-code flow |

---

## 9. Related Topics

- **Knowledge Management & Training (#23)** — Phase 3 onboarding training mode directly depends on this
- **Integration Architecture (#1)** — Channel connection (WhatsApp, email) setup UX depends on integration registry
- **Real-World Validation (#7)** — Onboarding flow should be validated with real agency owners
- **Mobile Experience (#27)** — Mobile onboarding surface considerations
- **Deployment & Operations (#25)** — Production infrastructure needed before agency partner launch
- **Testing & QA Strategy (#24)** — Onboarding flow E2E tests
- **Pricing & Monetization (#10)** — Free trial → paid conversion depends on onboarding success

---

*This is a living document. Update it as implementation progresses, new documents are created, or phases ship.*
