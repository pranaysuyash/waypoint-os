# Discovery Gap Analysis: Communication & Channel Architecture

**Date**: 2026-04-16
**Gap Register**: #03 (P0 — system is a dead end without delivery)
**Preceded By**: MASTER_GAP_REGISTER_2026-04-16.md
**Scope**: Internal comms (agent-agent, owner-agent, system alerts), external comms (client portal, proposal delivery, WhatsApp, email, SMS), message templates, conversation flows

---

## 1. Executive Summary

The system can analyze inquiries and produce strategy — but cannot deliver anything to anyone. No copy-for-WhatsApp, no share link, no email, no SMS, no client portal, no agent-to-agent messaging, no system alerts, no notification bell.

**2,500+ lines of design docs** across 3 major spec docs (WhatsApp integration 884 lines, message templates 727 lines, multi-channel strategy 943 lines) plus in-app messaging spec (303 lines). **Zero lines of implementation code.** The `prompts/templates/` directory is empty. No `/trip/[shareToken]` route exists. No messaging API endpoints exist.

The single most critical gap: **the system produces insights it cannot share.**

---

## 2. Evidence Inventory

### 2.1 What's Documented

#### External Communication (Client-Facing)

| Doc | What It Specifies | Key Insight |
|-----|------------------|------------|
| `UX_WHATSAPP_INTEGRATION_STRATEGY.md` (884 lines) | 6 integration options, phased implementation (manual -> Business App -> WATI -> Official API), full `MessageComposer.tsx` component code, FastAPI router with `/api/whatsapp/*` endpoints, DB schema for conversation_turns/reminders/message_templates | **Manual copy-paste is the MVP. Don't let WhatsApp block you.** |
| `UX_MESSAGE_TEMPLATES_AND_FLOWS.md` (727 lines) | 40+ templates across 8 categories, 3 conversation flow maps, tone guidelines, personalization variables (10 from packet data), anti-patterns | **Templates exist only in docs — `prompts/templates/` is empty** |
| `UX_MULTI_CHANNEL_STRATEGY.md` (943 lines) | Channel matrix (WhatsApp/Email/SMS/Portal/Phone), secure link strategy, customer portal with 3-option comparison, full FastAPI router for `/portal/*` endpoints, channel routing logic, SMS via Twilio/MSG91, email templates | **Build portal first, not WhatsApp integration.** |
| `FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md` | Dual-view architecture, `/trip/[shareToken]` routes, traveler-safe proposal view | Dual-view not implemented |
| `UX_DASHBOARDS_BY_PERSONA.md` | "Suggested Questions (Copy to WhatsApp)" in agent dashboard | Not built |

#### Internal Communication (Team-Facing)

| Doc | What It Specifies | Key Insight |
|-----|------------------|------------|
| `IN_APP_MESSAGING_SYSTEM.md` (303 lines) | 5 message types (banner, tooltip, tour, help panel, callout), planned components, API endpoints for announcements | **System-to-user only. No agent-to-agent or owner-agent messaging spec.** |
| `IN_APP_MESSAGING_REQUIREMENTS.md` (177 lines) | 3 use cases (onboarding, operational updates, contextual help), 4 priority levels | Requirements gathered, discussion pending |
| `UX_REDESIGN_MASTERPLAN.md` | Notifications in header, email auto-import, settings/integrations page | Planned |

#### Safety Boundary (Implemented)

| Doc/Code | What It Does | Status |
|----------|-------------|--------|
| `src/intake/safety.py` | Strips internal terms (margin, commission, net_cost) from traveler-facing output | **Implemented — the safety boundary works, but there's no delivery mechanism to apply it to** |
| `src/intake/strategy.py` | Separate internal vs traveler-safe prompt paths | **Implemented — but output goes nowhere** |

### 2.2 What's Implemented

| Component | Status | Evidence |
|-----------|--------|----------|
| Traveler-safe output boundary | **Works** | safety.py + strategy.py produce two separate output streams |
| Inbox page (frontend) | **Mock only** | 562-line page with hardcoded data, `alert()` for actions |
| Output page placeholder | **Stub** | `<h1>Output</h1>` + "Traveler-safe proposal preview and send-prep" — 7 lines |
| NotificationTemplate type | **Defined but unused** | `governance.ts` L313-319 |
| Accessibility announcements | **Screen reader only** | Polite/assertive ARIA announcements for assistive tech |

### 2.3 What's NOT Implemented

- No copy-for-WhatsApp button
- No share link generation (`/trip/[shareToken]`)
- No client portal
- No email sending
- No SMS sending
- No push notifications
- No notification bell / alert queue
- No message templates in code (40+ templates in docs, 0 in code)
- No conversation history tracking
- No agent-to-agent messaging
- No owner-agent communication channel
- No system alert/inbox
- No announcement banners
- No message routing logic
- No WhatsApp Business API integration (even manual log)

---

## 3. Gap Taxonomy

### 3.1 Structural Gaps (No Entity/Component Exists)

| Gap ID | Concept | Documented In | Implementation | Blocks |
|--------|---------|---------------|----------------|--------|
| **CM-01** | Copy-for-WhatsApp output | UX_WHATSAPP (MessageComposer.tsx), PERSONA_GAP (P0 #5) | None | Core JTBD #4 (send proposal) |
| **CM-02** | Client portal (shareToken) | UX_MULTI_CHANNEL (portal strategy), FRONTEND_SPEC (Surface D) | One empty placeholder page | Client self-service, doc upload, option selection |
| **CM-03** | Message template system | UX_MESSAGE_TEMPLATES (40+ templates), PROMPT_VERSIONING | `prompts/templates/` is empty | All outbound messaging |
| **CM-04** | Internal comms (agent-agent, owner-agent) | Not spec'd beyond in-app messaging for system announcements | None | Team collaboration, escalations |
| **CM-05** | Notification/alert engine | PERSONA_GAP (P0), UX_MULTI_CHANNEL (routing logic) | `NotificationTemplate` type only | Payment reminders, visa deadlines, quote expiry |
| **CM-06** | Conversation history | UX_WHATSAPP (conversation_turns table) | None | Repeat detection, continuity across sessions |
| **CM-07** | Email delivery | UX_MULTI_CHANNEL (email templates) | None | Proposal sending, confirmations |
| **CM-08** | SMS delivery | UX_MULTI_CHANNEL (Twilio/MSG91) | None | Urgent alerts, OTP |

### 3.2 Integration Gaps (Designed But Not Wired)

| Gap ID | Integration | Designed In | Current State | Blocked By |
|--------|-------------|------------|---------------|------------|
| **CI-01** | Proposal → WhatsApp copy | UX_WHATSAPP L33-196 | Safety boundary splits output but no copy button | Nothing (can build now) |
| **CI-02** | Proposal → secure link | UX_MULTI_CHANNEL L346-436 | No share token generation, no portal API | #02 (needs DB for token storage) |
| **CI-03** | Channel routing | UX_MULTI_CHANNEL L711-806 | Full routing logic in docs, no code | CM-03, CM-05 |
| **CI-04** | Message → conversation history | UX_WHATSAPP L809-824 | DB schema designed, no implementation | #02 (needs DB) |
| **CI-05** | System → notification alert | PERSONA_GAP L177 | No push/email/SMS, no alert queue | CM-05, #02 |

---

## 4. The Agency's Own Channel

**User's insight**: The system should have its own communication channel — both internal (between agents, owner) and external (to clients) — rather than relying on WhatsApp exclusively.

This is architecturally correct and already partially designed:

### Internal Channel (Team Comms)
- **Not spec'd** for peer messaging. The IN_APP_MESSAGING_SYSTEM doc only covers system-to-user (announcements, tours, help).
- **What's needed**: Agent inbox with threads, owner broadcast messages, escalation channel, @mention capability.
- **Architecture**: WebSocket-based real-time messaging, persisted in DB, visible in trip workspace.

### External Channel (Client Portal)
- **Extensively spec'd** in UX_MULTI_CHANNEL_STRATEGY.md (lines 80-313).
- The portal IS the agency's own channel. WhatsApp is a notification spoke that drives clients to the portal.
- **Key design**: "Build portal first, not WhatsApp integration" (line 912).

### Hybrid Architecture (What the Docs Recommend)

```
Agency's Own Channel (Portal)
├── Client Portal (/trip/[shareToken])
│   ├── Proposal viewing
│   ├── Option selection
│   ├── Document upload
│   ├── Payment status
│   └── Client-agent messaging
│
├── Internal Messaging
│   ├── Agent workspace chat
│   ├── Owner broadcasts/escalations
│   ├── System alerts/notifications
│   └── Thread-per-trip context
│
└── Notification Spokes (push, not pull)
    ├── WhatsApp (quick questions, proposals)
    ├── Email (confirmations, formal)
    ├── SMS (urgent, OTP)
    └── Push notifications (mobile)
```

---

## 5. Dependency Graph

```
CM-01 (Copy-for-WhatsApp) ─── no blockers, build NOW
  └── Unblocks: Core JTBD #4

CM-02 (Client Portal) ─── blocked by #02 (persistence for share_token)
  └── Unblocks: Client self-service, doc upload, payment tracking

CM-03 (Message Templates) ─── partially blocked by #02 (template storage)
  └── Unblocks: All outbound messaging quality

CM-05 (Notification Engine) ─── blocked by #02 (alert storage)
  └── Unblocks: Payment reminders, visa deadlines, quote expiry

CM-04 (Internal Comms) ─── blocked by #02 (message persistence), #08 (auth/sessions)
  └── Unblocks: Team collaboration, escalation

CI-01 (Proposal → WhatsApp) ─── can build with just CM-01
CI-02 (Proposal → Portal Link) ─── blocked by CM-02 + #02
```

---

## 6. Phase-In Recommendations

### Phase 0: Copy-for-WhatsApp (P0, ~0.5 days, no blockers)
1. Add "Copy for WhatsApp" button to workbench Output tab
2. Format traveler-safe output as WhatsApp-friendly text (bullet points, emoji headers)
3. Add wa.me deep link for quick send
4. Add "Mark as Sent" tracking (local state for now)

**Acceptance**: Agent can copy proposal text and paste into WhatsApp in one click. This alone makes the system usable.

### Phase 1: Client Portal MVP (P0, ~5 days, blocked by #02)
1. Add `/trip/[shareToken]` route to frontend
2. Generate share tokens on trip creation (stored in DB)
3. Build traveler-safe proposal view (use safety.py output)
4. Add document upload section
5. Add option selection (customer picks option A/B/C)

**Acceptance**: Agent shares link, client views proposal in browser, selects option, uploads passport. No login required.

### Phase 2: Message Templates + Notifications (P1, ~3 days)
1. Move 40+ templates from doc into `prompts/templates/` as YAML
2. Build template selection in output view
3. Add notification bell in frontend header
4. Add in-app alert queue (payment due, visa deadline, quote expiring)

**Acceptance**: Agent picks "Follow Up After Silence" template, personalizes, sends. Owner sees alert for overdue payment.

### Phase 3: Internal Comms (P1, ~3 days, blocked by #08)
1. Add per-trip messaging thread in workspace
2. Add owner broadcast capability
3. Add escalation @mention
4. Build in-app messaging components from IN_APP_MESSAGING_SYSTEM spec

**Acceptance**: Agent can ask owner a question in-context. Owner sees escalation in inbox.

### Phase 4: Multi-Channel Routing (P2, ~5 days)
1. Wire channel routing logic from UX_MULTI_CHANNEL
2. Add email delivery (SendGrid/Resend)
3. Add SMS for critical alerts (Twilio/MSG91)
4. Add WhatsApp Business API logging

**Acceptance**: System routes proposal to portal link + WhatsApp message. Payment reminder goes to SMS + email.

---

## 7. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| Build own comms or rely on WhatsApp? | (a) Own portal + WhatsApp as spoke, (b) WhatsApp only, (c) Portal only | **(a) Portal is hub, WhatsApp is spoke** — already designed in MULTI_CHANNEL_STRATEGY | Confirms "Build portal first" |
| Do clients need accounts? | (a) ShareToken links (no login), (b) Full client auth, (c) Hybrid | **(a) ShareToken for MVP** — no friction. Full auth later for return clients. | Faster time-to-value |
| Message templates: code or config? | (a) Hardcoded strings, (b) YAML files in repo, (c) DB-stored | **(b) YAML files** — version controlled, editable, A/B testable. DB later. | Enables template versioning |
| Real-time internal comms? | (a) WebSocket, (b) Polling, (c) Webhook + email | **(a) WebSocket** for MVP — simpler than it sounds with FastAPI | Live collaboration |
| WhatsApp integration depth? | (a) Copy-paste only, (b) WhatsApp Business App, (c) WATI, (d) Official API | **(a) Copy-paste for MVP** — per UX_WHATSAPP phased plan | No API cost, no policy risk |

---

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Copy-for-WhatsApp bypassed — agents just screenshot | Medium | Format output specifically for WhatsApp (short, bulleted, emoji). Make copy easier than screenshot. |
| Portal links shared publicly | Medium | Token has expiry. View tracking. Owner can revoke. |
| No WhatsApp API means no delivery confirmation | Low | "Mark as Sent" manual tracking. Good enough for MVP. |
| Internal comms scope creep | Medium | Phase 1: only per-trip threads. Phase 2: owner broadcasts. No general chat until core workflows work. |
| Template maintenance burden | Low | Start with 10 essential templates, not 40. Grow from usage data. |

---

## 9. Files Audited

- `Docs/UX_WHATSAPP_INTEGRATION_STRATEGY.md` (884 lines)
- `Docs/UX_MESSAGE_TEMPLATES_AND_FLOWS.md` (727 lines)
- `Docs/UX_MULTI_CHANNEL_STRATEGY.md` (943 lines)
- `frontend/docs/IN_APP_MESSAGING_SYSTEM.md` (303 lines)
- `frontend/docs/IN_APP_MESSAGING_REQUIREMENTS.md` (177 lines)
- `Docs/PERSONA_PROCESS_GAP_ANALYSIS_2026-04-16.md` — P0 communication gaps
- `Docs/INDUSTRY_PROCESS_GAP_ANALYSIS_2026-04-16.md` — Communication gaps
- `Docs/FRONTEND_COMPREHENSIVE_AUDIT_2026-04-16.md` — Surface D ~5%
- `src/intake/safety.py` — Traveler-safe boundary (implemented)
- `src/intake/strategy.py` — Internal/traveler output split (implemented)
- `frontend/src/app/workspace/[tripId]/output/page.tsx` — Empty stub
- `frontend/src/types/governance.ts` — NotificationTemplate type