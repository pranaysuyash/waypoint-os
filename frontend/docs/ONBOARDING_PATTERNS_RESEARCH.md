# Workspace-Based Onboarding Pattern Research

**Goal:** Understand how successful tools handle first-time user onboarding

---

## Pattern Analysis

### Linear (Project Management)
```
1. Sign up (email + password)
2. Immediately dropped into workspace
3. Empty state with clear CTA: "Create your first issue"
4. Sidebar has onboarding checklist:
   ☐ Create your first issue
   ☐ Invite team members
   ☐ Set up your workspace
5. Checklist is dismissible, not blocking
```

**Key insight:** Immediate value, checklist as guide not gate

### AWS Console
```
1. Root account signs up
2. Dashboard shows "Get started" checklist
3. IAM section: Create users with access keys
4. Users sign in with:
   - Account ID (or alias)
   - Username
   - Password
5. No "invite" — admin creates credentials, shares them
```

**Key insight:** Code/ID based access, admin controls everything

### Notion
```
1. Sign up
2. "Take the tour" or "Skip to workspace"
3. Empty workspace with sample content
4. Progressive tooltips: "Click here to add a page"
5. Template gallery for quick start
```

**Key insight:** Sample content teaches by showing, not telling

### Slack
```
1. Sign up with email
2. "Create your workspace" — name required
3. "Invite your team" — skip or add emails
4. Channel creation: "#general" created automatically
5. "Get started" checklist in sidebar
```

**Key insight:** Workspace name required early, team invitation is skippable

### Figma (for design teams)
```
1. Sign up
2. "Enter your team name"
3. "Invite collaborators" (skippable)
4. Dropped into canvas with tutorial overlay
5. First file is auto-created "Untitled"
```

**Key insight:** Team identity first, everything else progressive

---

## Synthesis: What Works for Travel Agency Context

Based on patterns + your requirements:

### Signup Flow
```
1. Landing page: "Get started free"
2. Email + password
3. [Optional] Agency name — can add later
4. Immediate access to workspace
```

### First Experience (The "Empty State")
```
┌─────────────────────────────────────────────────────────────┐
│  Your Workspace                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Welcome! Let's get you set up.                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 1: Create your first trip                      │   │
│  │                                                     │   │
│  │ [New Trip] button highlighted                       │   │
│  │ "Click here or press N to create your first trip"  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 2: Add team members (optional)                 │   │
│  │                                                     │   │
│  │ Your invite code: XYZ-ABC-123                      │   │
│  │ "Share this code with your agents to add them"     │   │
│  │ [Copy Code] [Generate New]                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 3: Set up your agency profile                 │   │
│  │                                                     │   │
│  │ Agency name, logo, contact details                 │   │
│  │ [Complete Profile] →                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Team Invitation (Code-Based like AWS)

**Admin side:**
```typescript
// Admin sees in Settings > Team
┌─────────────────────────────────────────────────────────────┐
│  Team Management                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Your Workspace Code:                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     ABC-XYZ-786                                      │   │
│  │                                                        │   │
│  │  [Copy] [Regenerate]                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Share this code with agents. They'll enter it when        │
│  signing up to join your workspace.                        │
│                                                             │
│  Active Members (3/4 free slots used):                     │
│  • You (Owner)                                             │
│  • rahul@agency.com (Agent)                                │
│  • priya@agency.com (Agent)                                │
│                                                             │
│  [Upgrade for more agents]                                 │
└─────────────────────────────────────────────────────────────┘
```

**Agent signup flow:**
```
1. Agent goes to app/signup
2. Enters: Email + Password + Workspace Code
3. If code valid → joins workspace immediately
4. If code invalid → "Check with your agency owner"
5. First login → sees "Welcome to [Agency Name] workspace"
```

**Benefits:**
- No email invites needed (avoid spam folders)
- Admin controls who joins (code required)
- Easy to regenerate if compromised
- Clear free tier messaging (3/4 slots used)

---

## Progressive Setup Checklist

Sidebar shows dismissible checklist:

```
┌─────────────────────────────┐
│  Getting Started            │
├─────────────────────────────┤
│ ☐ Create your first trip    │
│ ☐ Add team members          │
│ ☐ Complete agency profile   │
│ ☐ Explore the workspace     │
└─────────────────────────────┘
```

- Items check off as they complete them
- Dismissible — not blocking
- Reopenable from Help menu

---

## Customer Portal Introduction (Later)

During onboarding, we can add a subtle "Did you know?" tip:

```
┌─────────────────────────────────────────────────────────────┐
│  💡 Tip: Share trip status with customers                   │
│                                                             │
│  When you're ready, click "Share" on any trip to generate  │
│  a magic link. Send it to customers via WhatsApp — they    │
│  can view their itinerary without logging in.              │
│                                                             │
│  [Learn More] [Dismiss]                                     │
└─────────────────────────────────────────────────────────────┘
```

This educates without forcing them to set it up immediately.

---

## Phased Approach

### Phase 1: Foundation (Current Focus)
- Email + password signup
- Immediate workspace access
- Empty state with "Create first trip" CTA
- Manual trip entry
- Workspace code generation for team

### Phase 2: Team Features
- Agent signup with workspace code
- Team management page
- Role assignment (owner/agent/external)
- Free tier messaging (3/4 slots)

### Phase 3: Polish
- Progressive checklist
- Onboarding tooltips
- Customer portal education
- First trip tutorial

---

## Open Questions

1. **Workspace code format** — ABC-XYZ-786? Something else?
2. **Agency name deadline** — When do we require it? First login? First trip creation?
3. **External agents** — Same code flow or different?
4. **Code expiration** — Should codes expire? Regenerate on what trigger?

---

**Status:** Pattern research complete, awaiting confirmation on flow
