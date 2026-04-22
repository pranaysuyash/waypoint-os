# Owner Onboarding Flow - Discovery Session

**Date:** 2026-04-22
**Goal:** Design the agency owner onboarding journey — from discovery to first trip

---

## Original Request

> "if i was an agency owner how would i signup, add people, setup stuff etc?"

**Context:**
- Current state: No signup/auth implemented, but types and permissions defined
- Business model: 1 admin + 3-4 agents free (from pricing discussion)
- Target: Travel agencies who want fast, efficient, correct operations

---

## Role Structure (User Clarification)

### Simplified Roles

| Role | Who | Permissions |
|------|-----|-------------|
| **Owner-Admin-Manager** | Agency owner / person who runs it | Full access: settings, team, trips, analytics, billing |
| **Agent** | Internal team members | Trips assigned to them, customer communication |
| **External Agent** | Vendors/contractors they work with | Limited access, specific trips only |

### Scenarios

| Agency Type | Structure |
|-------------|-----------|
| Solo agent | Just "owner" — no team needed |
| Small team | 1 owner + 3-4 agents (free tier) |
| Vendor model | Owner + external agents (vendors) |

---

## Pricing Context (From Previous Discussion)

- **Free tier:** 1 admin + 3-4 agents
- Implies: Onboarding should show "3/4 agent slots used" messaging
- Upgrade path: When they need more agents

---

## Customer Portal Context

- Owner mentioned "customer portal?" — wants to understand this as part of onboarding
- From docs: Magic link access (no login required for customers)
- Question: When/how is this introduced to the owner?

---

## Open Questions for Design

### Discovery & Signup
1. **How do they find us?** — Google, referral, direct?
2. **What do we collect initially?** — Just email? Email + agency name? More?
3. **Is there approval?** — Instant access or manual approval?

### Setup Wizard
4. **What's required before first trip?** — Agency name only? Or also destinations, pricing templates, integrations?
5. **Can they skip and explore?** — Or must complete setup to see the workspace?
6. **How do we add team?** — During setup or after first value?

### Team Invitation
7. **How do agents join?** — Email invite? Invite code? You create them?
8. **How do external agents work?** — Same flow or different?
9. **What does agent see first?** — Empty workspace? Tutorial trip?

### First Value
10. **How do they create first trip?** — Manual entry? WhatsApp integration? Import?
11. **What's the "aha moment"?** — When do they feel "this works"?

---

## Design Principles (From UX Discovery)

- **Precise:** Ask for what we need, nothing more
- **Efficient:** Get to value fast, minimal setup friction
- **Reassuring:** Make them feel confident they can set this up

---

## Related Documents

- `DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md` — Auth backend model
- `MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md` — Role permissions, tenant isolation
- `PRICING_PACKAGING_DISCUSSION_DRAFT_2026-04-17.md` — Pricing context

---

## Next Steps

1. Clarify the open questions above
2. Design the complete onboarding journey
3. Create wireframes/states for each step
4. Document the phased implementation plan

---

## Progress Tracker

| Step | Status | Document |
|------|--------|----------|
| Requirements gathering | ✅ Complete | This document |
| Workspace code format analysis | ✅ Complete | `WORKSPACE_CODE_FORMAT_ANALYSIS.md` |
| Design brief | ✅ Complete | `DESIGN_BRIEF_Onboarding_Flow.md` |
| Implementation | ⏳ Pending | Awaiting approval |

---

## Related Documents

- `ONBOARDING_PATTERNS_RESEARCH.md` — Linear/AWS/Notion pattern analysis
- `WORKSPACE_CODE_FORMAT_ANALYSIS.md` — Code format decision with pros/cons
- `DESIGN_BRIEF_Onboarding_Flow.md` — Complete design brief with wireframes
- `DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md` — Backend auth model
- `MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md` — Role permissions

---

**Status:** Design complete, ready for implementation
