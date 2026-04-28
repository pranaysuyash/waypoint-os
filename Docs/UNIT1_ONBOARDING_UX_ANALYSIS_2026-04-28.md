# Unit-1: Onboarding & Workspace UI — UX-First Analysis

**Date:** April 28, 2026  
**Approach:** First principles UX, ignore ticket wording  
**Status:** Analysis Complete — Recommendations Ready

---

## Executive Summary

The ticket requests multi-step onboarding. From UX first principles, **the current single-step signup is correct** for initial conversion. What's actually missing are two real UX gaps:

1. **Join Workspace flow** — Agents can't join existing agencies (WorkspaceCode exists in DB, no frontend)
2. **Post-signup activation** — Owners hit `/overview` with no guidance on what to do next

| Flow | Current | UX Verdict |
|------|---------|-------------|
| Owner signup | Single-step `/signup` → `/overview` | ✅ Correct (low friction) |
| Agent join | ❌ No flow exists | 🔴 Missing (blocks team adoption) |
| Post-signup setup | ❌ None | 🟡 Weak (blank dashboard, no activation) |
| Multi-step onboarding | ❌ Not built | ❌ Unnecessary (adds friction) |

---

## UX First Principles Analysis

### Principle 1: Minimize Initial Friction
- **Rule:** First interaction should be as simple as possible
- **Current state:** Single-step signup (email + password) → done
- **Verdict:** ✅ Correct. Adding steps before account creation **reduces conversion**
- **Action:** Keep `/signup` as-is. Don't build multi-step before signup.

### Principle 2: Progressive Disclosure
- **Rule:** Reveal complexity only when needed
- **Current state:** Agency created automatically with defaults
- **Better approach:** Post-signup "setup wizard" that can be **skipped**
- **Verdict:** 🟡 Current "blank /overview" is a dead end. Need guided activation.

### Principle 3: Support Team Collaboration
- **Rule:** B2B SaaS must support team members joining
- **Current state:** 
  - `WorkspaceCode` model exists in DB (backend ready)
  - NO frontend flow for agents to join via code
  - NO "Invite Team" UI for owners
- **Verdict:** 🔴 **Critical UX gap** — owners can't add their agents

### Principle 4: Activation > Signup
- **Rule:** Signup is not success; activated user is success
- **Current state:** After signup → `/overview` with "No trips yet"
- **Problem:** No guidance on:
  - How to invite team members
  - How to create first trip
  - What the workspace can do
- **Verdict:** 🟡 Weak activation path

---

## Recommended Implementation (UX-First)

### Priority 1: Join Workspace Flow (Critical Gap)
**Why:** Without this, agency owners can't add their agents. The backend model exists but frontend doesn't use it.

**Files to create:**
```
frontend/src/app/(auth)/join/page.tsx     # Join form (enter code)
frontend/src/app/(auth)/join/JoinForm.tsx  # Form component
```

**Flow:**
1. Agent receives `WP-xxxxx` code from owner
2. Visits `/join` (linked from `/login` page)
3. Enters code + their email + password
4. `POST /api/tenant/join` validates code, creates User + Membership
5. Sets auth cookies, redirects to `/overview`

**Backend needs:**
```
POST /api/tenant/join  # Validate WorkspaceCode, create User+Membership
GET  /api/tenant/members  # List agency members (for owner dashboard)
POST /api/tenant/invite  # Owner generates new invite codes
```

**Why this over ticket's "multi-step":** This solves a real blocker. Multi-step onboarding doesn't.

---

### Priority 2: Post-Signup Activation (Weak Point)
**Why:** Owners sign up and see a blank dashboard. No guidance = poor activation.

**Approach:** "Getting Started" checklist on `/overview` for new agencies:

```tsx
// Shown only when agency has <3 trips and <2 members
<GettingStartedCard>
  ✅ Create your agency (done)
  ⬜ Invite your first agent  → /settings/team
  ⬜ Process your first trip → /workbench
  ⬜ Customize agency profile → /settings
</GettingStartedCard>
```

**Files to modify:**
```
frontend/src/app/overview/page.tsx  # Add GettingStartedCard
frontend/src/app/settings/page.tsx    # Add team management UI
```

**Why not multi-step onboarding:** Progressive enhancement > forced wizard. Let owners explore, but guide them.

---

### Priority 3: Team Management UI (Enables P1-02)
**Why:** Owners need to manage their team. Currently no UI for this.

**Files to create:**
```
frontend/src/app/settings/components/TeamTab.tsx  # List/invite/remove members
```

**Flow:**
1. Owner goes to `/settings` → "Team" tab
2. Sees current members + "Invite Agent" button
3. Clicks → generates new `WorkspaceCode`
4. Shares code with agent (copy link / email)

**Backend needs:**
```
GET  /api/tenant/members       # List agency members
POST /api/tenant/invite       # Generate new WorkspaceCode
DELETE /api/tenant/members/{id} # Remove member (owner only)
```

---

## What NOT to Build (Based on UX Principles)

### ❌ Multi-Step Pre-Signup Onboarding
**Why:** Adds friction before value. Users don't want to "setup agency" before trying the product.
- **Better:** Let them sign up in 30 seconds → see the value → then guide setup.

### ❌ "Agency Info → Admin User → Workspace Setup" Wizard
**Why:** This is B2C thinking applied to B2B. In B2B SaaS:
- Owners want to see the product first
- Forced wizards have high drop-off rates
- Progressive disclosure works better

### ❌ Separate `/onboarding` Page
**Why:** Creates a "dead end" page. Better to integrate guidance into the actual workspace.
- **Better:** GettingStarted checklist ON the `/overview` dashboard

---

## Implementation Plan (If Proceeding)

### Phase 1: Join Workspace (Critical)
**Files to create:**
1. `frontend/src/app/(auth)/join/page.tsx` — Join form page
2. `frontend/src/app/(auth)/join/JoinForm.tsx` — Form component
3. `spine_api/routers/tenant.py` — New router (or add to `auth.py`)
4. `spine_api/services/tenant_service.py` — Join logic

**Verification:**
```bash
# Test join flow
curl -X POST http://localhost:8000/api/tenant/join \
  -H "Content-Type: application/json" \
  -d '{"code":"WP-xxxxx","email":"agent@agency.com","password":"TestPass123"}'
```

### Phase 2: Post-Signup Guidance (Activation)
**Files to modify:**
1. `frontend/src/app/overview/page.tsx` — Add GettingStartedCard
2. Create `frontend/src/components/onboarding/GettingStartedCard.tsx`

**Verification:**
- Signup as new user → See GettingStartedCard
- Complete actions → Checklist updates
- After 3+ trips → Card auto-hides

### Phase 3: Team Management (Enables Collaboration)
**Files to create/modify:**
1. `frontend/src/app/settings/components/TeamTab.tsx` — Team UI
2. Add to `frontend/src/app/settings/page.tsx` — New tab

**Verification:**
- Owner can invite agents
- Agents receive codes
- Agents can join via `/join`
- Owner can remove members

---

## Comparison: Ticket vs UX-First Approach

| Aspect | Ticket Request | UX-First Approach |
|--------|----------------|---------------------|
| **Pre-signup** | 3-step form | ✅ Keep simple (1 step) |
| **Join flow** | Part of onboarding | ✅ **Separate /join page** |
| **Post-signup** | Redirect to /overview | ✅ **Guided activation** |
| **Team UI** | Not mentioned | ✅ **Settings > Team tab** |
| **Friction** | High (3 steps before entry) | Low (30sec signup) |
| **Activation** | None | Guided checklist |

---

## Key Insight: The Backend is Ready

The `WorkspaceCode` model already supports:
- `code` — The invite code (e.g., `WP-xxxxx`)
- `code_type` — "internal" or "external"
- `status` — "generated" → "shared" → "active"
- `used_by` — Tracks who joined
- `used_at` — Timestamp

**The only thing missing is the frontend + join endpoint.**

---

## Recommended Next Action

**Build the Join Workspace flow first** (Priority 1):
1. Create `spine_api/routers/tenant.py` with `POST /api/tenant/join`
2. Create `frontend/src/app/(auth)/join/page.tsx`
3. Link it from `/login` page ("Have an invite code? Join workspace")
4. Verify end-to-end: code generation → share → agent joins

**Then enhance activation:**
5. Add GettingStartedCard to `/overview`
6. Add TeamTab to `/settings`

**Don't build:** Multi-step onboarding before signup (violates UX principles).

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-28  
**Next Step:** User approval on UX-first approach vs ticket requirements
