# Onboarding & Agency Setup — Research Document

**Topic**: #22 (Exploration Topics Master Index)
**Status**: Synthesis complete — see Sections 2-4 for first-session flow outline
**Last Updated**: 2026-06-25

---

## 1. Sources Synthesized

This document synthesizes three research documents plus current app state analysis:

| Source | Key Contribution |
|--------|-----------------|
| [DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md](DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md) | 10 adoption principles, 5 entry CTAs, progressive disclosure model, outside-app adoption strategy |
| [INTAKE_LOW_CLICK_CAPTURE_STRATEGY_2026-05-04.md](INTAKE_LOW_CLICK_CAPTURE_STRATEGY_2026-05-04.md) | Low-click capture model, `Save and Process` atomic action, capture mode presets |
| [INQUIRY_TRIP_FLOW_UNIFICATION_FIRST_PRINCIPLES_ANALYSIS_2026-05-04.md](INQUIRY_TRIP_FLOW_UNIFICATION_FIRST_PRINCIPLES_ANALYSIS_2026-05-04.md) | Canonical lifecycle model, draft-first intake, inbox-as-view architecture |
| Current app state (Shell, EmptyStateOnboarding, route structure) | What exists today: 3-step onboarding, New Inquiry CTA, default "Agency Workspace" label |

---

## 2. Current State Assessment

### What exists today

- **Sign-up flow**: Auth routes exist (`/login`, `/signup`, `/forgot-password`, `/reset-password`), but sign-up route is basic — no agency creation during sign-up
- **Agency identity**: Shell reads `agencySettings?.profile?.agency_name` — defaults to `"Agency Workspace"` when unset. Brand descriptor (`sub_brand`, `plan_label`) also read but likely empty for new users.
- **Empty-state onboarding**: `EmptyStateOnboarding` component on `/overview` shows 3 steps when `planningTripsTotal === 0 && leadInboxTotal === 0`:
  1. Invite your team → `/settings?tab=people`
  2. Add your first inquiry → `/workbench?draft=new&tab=intake`
  3. Review in Lead Inbox → `/inbox`
- **New Inquiry CTA**: Links to `/workbench?draft=new&tab=intake&capture_mode=call&entry=new`, auto-opens `CaptureCallPanel`
- **Settings tabs**: Profile tab, People tab (team invitations) exist — these are the starting point for agency configuration

### What's missing for a first-session flow

| Gap | Impact |
|-----|--------|
| No agency setup during sign-up | New users land in a blank workspace with "Agency Workspace" label — no sense of ownership |
| No setup wizard | Settings are scattered across tabs with no guided flow |
| No channel connection step | New users don't know they can connect WhatsApp/email |
| No sample/template data | Empty states show a guide but no "try it now" with real data |
| No progress tracking | No way to know what setup steps are remaining |
| No role prompting | All users default to owner — no "are you a solo agent or agency team?" |
| No data import path | Existing agencies can't bring their data in during setup |
| No first-inquiry coaching | The EmptyStateOnboarding links to workbench but doesn't guide the capture |

---

## 3. First-Session Agency Setup Flow — End-to-End Outline

### Phase 0: Pre-Sign-Up (Landing / Marketing)

Not in scope for this doc, but the setup flow assumes the user arrives from:
- A sign-up page with clear value proposition
- An invitation link from an existing agency member (team join path)
- A trial/demo request that triggers an onboarding sequence

**Precondition checks**: Before showing the setup wizard, determine:
- Is this a brand-new agency owner (solo or team lead)?
- Is this a team member joining an existing agency (has invite code)?
- Is this a returning user whose setup was interrupted?

---

### Phase 1: Account + Agency Creation (0-2 minutes)

**Goal**: Create user account AND agency profile in one flow.

#### 1a. Sign-up with agency details

```
Screen: Sign up
├── Email / Password / Name
├── Agency name (required, single text field)
├── Your role: [Solo agent / Agency owner / Agency agent / Other]
├── Team size: [Just me / 2-5 / 6-20 / 20+]
└── [Create account] button
```

**Key decisions**:
- Merge agency creation into sign-up (don't make it a separate step)
- The agency name becomes the default display name in Shell
- Role and team size choices affect subsequent setup steps and defaults

**Backend actions**:
- Create user record + agency record atomically
- Set user as `owner` of the agency
- Set default agency settings (autonomy levels, brand defaults)
- Generate workspace invite code

#### 1b. Post-sign-up landing (first screen after auth)

After sign-up, route to a **setup wizard**, not the blank overview. The overview with EmptyStateOnboarding is the fallback for users who haven't completed setup.

```
Screen: Welcome to Waypoint OS
├── "Let's get your workspace ready"
├── Progress indicator: [1/4] [2/4] [3/4] [4/4]
├── Skip link: "I'll do this later → Overview"
└── Next button
```

---

### Phase 2: Agency Profile Setup (2-4 minutes)

**Goal**: Configure the agency's identity, brand, and operational preferences.

#### 2a. Brand & Identity

```
Screen: Your Agency Profile (2/4)
├── Agency name (prefilled from sign-up)
├── Sub-brand / trading name (optional)
├── Default currency (INR, USD, KES, GBP, EUR, etc.)
├── Default country/market (India, Kenya, UAE, UK, etc.)
├── Logo upload (optional)
├── Contact phone number
└── Contact email
```

**Key decisions**:
- Default currency affects budget parsing, formatting, and supplier defaults
- Default country/market affects regulatory compliance scope and destination scoring
- These can all be changed later in Settings

#### 2b. Operational Preferences

```
Screen: How You Work (2/4 continued or 2c)
├── How do you capture most inquiries?
│   [Phone calls / WhatsApp / Email / A mix / Not sure yet]
├── Who handles trip planning?
│   [I do everything / I have agents who plan / We split by destination]
├── Follow-up style:
│   [I set explicit due dates / I work through a queue / Ad-hoc]
└── Autonomy preference:
    [Let me review everything / Auto-process when confident / Something in between]
```

**Key decisions**:
- Channel preference affects which entry CTAs to emphasize
- Autonomy preference maps directly to existing `AgencyAutonomyPolicy` settings
- These choices prefill settings so the user doesn't need to configure them later

---

### Phase 3: Team & Channels (2-3 minutes)

**Goal**: Invite team members and connect communication channels.

#### 3a. Invite Team

```
Screen: Invite Your Team (3/4)
├── [Copy invite link] — generates workspace join code
├── Or enter email addresses to send invites:
│   [email1@example.com]
│   [email2@example.com]
│   [+ Add another]
├── Role on invite: [Agent (creates trips) / Reviewer (approves quotes) / Admin (full access)]
├── [Skip — I work alone]
└── Note: Team members can be added later in Settings
```

**Key decisions**:
- Solo agents skip this step and proceed to channels
- The invite link is the same one available in Settings → People tab
- Role-based permissions are assigned at invite time

#### 3b. Connect Channels (Optional but Prominent)

```
Screen: Connect Your Channels (3/4 continued or 3b)
├── WhatsApp Business
│   [Connect] — [Skip for now]
│   Benefit: Forward WhatsApp chats directly to create trips
├── Email
│   [Connect Gmail] — [Connect Outlook] — [Skip for now]
│   Benefit: Import email inquiries as structured leads
├── Phone (Call Recording)
│   [Set up later]
│   Benefit: Record and transcribe customer calls
└── [Skip all — I'll paste manually]
```

**Key decisions**:
- This is the "outside-app adoption" layer from the Data Capture UX audit
- Channel connections should not block proceeding — they're additive value
- WhatsApp is the highest-value, highest-complexity channel
- Email (Gmail/IMAP) is the easiest first integration

---

### Phase 4: First Inquiry (3-5 minutes)

**Goal**: Guide the user through capturing and processing their first real inquiry.

#### 4a. Choose Entry Method

Based on Phase 2b choices, the wizard offers the most relevant option:

```
Screen: Your First Inquiry (4/4)
├── "Let's capture your first lead. Choose how to start:"
├── [Capture a Phone Call] — "Paste your call notes or recap"
├── [Paste a WhatsApp Chat] — "Copy and paste the conversation"
├── [Paste an Email] — "Paste the email content"
├── [Try a Sample] — "Practice with a real-world scenario" ★ NEW
│   └── Sample options: Singapore family trip, Nairobi corporate group, Mumbai honeymoon
└── [I'll do this later → Go to Overview]
```

**Key decisions**:
- The **Sample scenario** is critical for first-time users who don't have a real inquiry handy (from DATA_CAPTURE_UX_AUDIT adoption principle #8: turn empty states into practice states)
- The sample loads the Ravi/Singapore scenario (or similar) with realistic data
- Users can edit, process, and follow through like a real lead

#### 4b. Capture & Review

The capture assistant opens (from the low-click model):

```
Screen: Capture New Lead
├── Entry method label: "📞 Phone Call Capture" / "💬 WhatsApp Paste" / etc.
├── Large text area: "Paste your call notes, WhatsApp chat, or email content here..."
├── Optional fields (collapsed):
│   ├── Call date / received date
│   ├── Caller name / contact
│   ├── Source / referral
│   └── Follow-up promised by
├── [Save and Process] — Primary CTA
└── [Save Draft] — Secondary CTA
```

After processing, show the understanding check (from DATA_CAPTURE_UX_AUDIT adoption principle #3):

```
Screen: What Waypoint Understood
├── "I understood this as:"
├── Destination: Singapore ✓
├── Dates: Feb 9-14, 2025 (inferred from call context in Nov 2024) ⚠
├── Travelers: 5 (2 adults, 1 toddler, 2 seniors) ⚠
├── Budget: Not specified ✗ — needs clarification
├── [Looks good! → Continue to Trip]
├── [Edit details]
└── [Ask follow-up questions]
```

#### 4c. First Result

```
Screen: Your First Trip
├── Trip name: Singapore family leisure trip
├── Status: Ready to build options
├── [Open Options] — Starts the planning flow
├── [View Lead Inbox] — See where it sits in the queue
└── [Finish Setup] — Continue to complete remaining setup steps
```

---

### Phase 5: Post-First-Inquiry (Ongoing)

**Goal**: Transition from setup mode to daily use.

#### 5a. Setup Completion Celebration

After the first inquiry is processed, show a completion state:

```
Screen: You're All Set! 🎉
├── ✓ Account created
├── ✓ Agency profile configured
├── ✓ First inquiry captured and processed
├── Next recommended actions:
│   ├── [Invite team members] — If not done yet
│   ├── [Connect WhatsApp] — If not done yet
│   ├── [Explore the Lead Inbox]
│   └── [Start planning your trip]
├── [Go to Overview] — Primary CTA
└── Optional: "Show me a quick tour of the workspace"
```

#### 5b. Setup Progress Indicator

In the Shell, show a subtle setup completion badge until all recommended steps are done:

```
Shell header (next to agency name):
┌──────────────────────┐
│ Waypoint OS          │
│ Ravi's Travels · ⚡ Setup 80% complete  │
└──────────────────────┘
```

Clicking the indicator reopens the setup wizard at the next incomplete step.

#### 5c. First Week Follow-Ups

Post-setup, the system should guide the user through deeper engagement:

| Day | Action | Channel |
|-----|--------|---------|
| Day 1 | "Your first trip is in planning. Ready to build options?" | In-app |
| Day 2 | "Want to connect WhatsApp for faster capture?" | Email |
| Day 3 | "Invite a team member so they can help with planning" | In-app |
| Day 5 | "You've captured N leads this week. Here's your pipeline summary" | Email digest |
| Day 7 | "How's your first week going? Any questions?" | In-app prompt |

---

## 4. Architecture & Implementation Considerations

### 4.1 Setup State Machine

The setup wizard should maintain a persisted state so users can resume if interrupted:

```typescript
enum SetupStep {
  ACCOUNT_CREATED = 'account_created',           // After sign-up
  PROFILE_CONFIGURED = 'profile_configured',       // Phase 2 complete
  TEAM_CHANNELS_CONFIGURED = 'team_channels_done', // Phase 3 complete
  FIRST_INQUIRY_CAPTURED = 'first_inquiry_done',   // Phase 4 complete
  SETUP_COMPLETE = 'setup_complete',               // All phases done
}
```

Persistence: Store in agency settings table (`setup_progress` field) so it survives logout, device change, and browser clear.

### 4.2 Routing

```
Pre-setup routes:
/setup                      → Setup wizard (resumes at current step)
/setup?step=profile         → Phase 2
/setup?step=team            → Phase 3
/setup?step=channels        → Phase 3b
/setup?step=first-inquiry   → Phase 4

Post-setup routes (existing):
/overview                   → Main workspace (shows EmptyStateOnboarding if no trips)
/workbench                  → Inquiry capture
/trips                      → Trip list
/inbox                      → Lead inbox
/settings                   → Full settings (superset of setup)
```

### 4.3 Guard: Redirect to Setup

If `setup_progress < SETUP_COMPLETE` and user navigates to `/overview`, redirect to `/setup` instead. Exception: allow direct navigation to `/settings` for power users who want to configure manually.

### 4.4 Backend Changes Required

| Change | Scope |
|--------|-------|
| `setup_progress` field in agency settings table | Add field, default `null` |
| `POST /api/auth/signup` — create agency alongside user | Modify signup endpoint |
| `GET /api/setup/progress` — return current step | New endpoint |
| `PUT /api/setup/progress` — advance setup step | New endpoint |
| `POST /api/setup/sample-trip` — create sample scenario trip | New endpoint |

### 4.5 Frontend Changes Required

| Component | Scope |
|-----------|-------|
| `SetupWizard` (new) | Multi-step wizard component with progress tracking |
| `SetupStepProfile` (new) | Agency profile + operational preferences form |
| `SetupStepTeam` (new) | Team invitation flow |
| `SetupStepChannels` (new) | Channel connection UI |
| `SetupStepFirstInquiry` (new) | Guided first inquiry capture |
| `SetupGuard` (new) | Route guard that checks `setup_progress` |
| `EmptyStateOnboarding` (modify) | Simplify to show setup link instead of 3 steps |
| `Shell` (modify) | Add setup progress indicator |
| Settings pages (modify) | Ensure all setup-available fields are editable later |

### 4.6 Principles (from Synthesis)

These principles are drawn from the three research docs:

1. **Never show internal architecture as first-run experience** — no "packet", "decision", "strategy" terminology on first screen (DATA_CAPTURE_UX_AUDIT)
2. **Make first-session success use real data** — the sample scenario should feel like real work, not a demo (DATA_CAPTURE_UX_AUDIT)
3. **Single atomic action for inquiry capture** — `Save and Process` not `Save` → `Process Trip` (LOW_CLICK_CAPTURE)
4. **One entity, one lifecycle** — trips from first capture onwards, no separate lead vs trip model (UNIFICATION)
5. **Preserve raw evidence before structure** — paste area first, extraction review second (DATA_CAPTURE_UX_AUDIT)
6. **Channel connections are additive, not blocking** — paste first, integrate later (DATA_CAPTURE_UX_AUDIT)
7. **Progressive disclosure** — show what the user needs now, hide advanced views behind navigation (ALL)
8. **Teach by doing** — every step produces real value, not a configuration dead-end (DATA_CAPTURE_UX_AUDIT)

---

## 5. Key Questions (Remaining)

- Should the setup wizard be skippable entirely? (Yes — power users who go to `/settings` bypass it)
- Should the sample scenario persist as a real trip or be destroyed after learning? (Persist — it becomes the first data point)
- What happens when a user signs up but their agency already has an invite code? (Different flow — team join, not owner setup)
- Should setup progress be tracked per-user or per-agency? (Per-agency — setup is an agency-level concern)
- How do we handle multi-currency agencies during setup? (Default currency is set at setup, additional currencies configured later)

---

## 6. Deliverables (Next Steps)

1. **Setup wizard UI prototype** — wireframes for Phases 1-5
2. **Setup state machine backend spec** — `setup_progress` field, endpoints, transitions
3. **Sample scenario content pack** — 3 pre-built sample inquiries with expected outcomes
4. **First-week follow-up sequence** — email + in-app prompt design
5. **Migration path for existing users** — what happens to current users who never completed setup?

---

## 7. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-25 | Merge agency creation into sign-up, not separate step | Fewer form fields before value; agency is scaffolding for trips |
| 2026-06-25 | Setup wizard is redirect-guarded until complete | Prevents blank-workspace confusion for new users |
| 2026-06-25 | Sample scenarios are critical for first-session success | Users without real inquiry data need practice path (from DATA_CAPTURE_UX_AUDIT) |
| 2026-06-25 | Channel connections are skip-invariant, never blocking | Paste-first is the minimum; WhatsApp/email integration adds value later |
