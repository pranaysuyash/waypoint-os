# Design Brief: Owner Onboarding Flow

> Feature: Agency owner signup, workspace creation, and team onboarding
> Status: Design phase — ready for implementation
> Date: 2026-04-22

---

## 1. Feature Summary

The journey for a new agency owner from discovery to their first trip — covering signup, workspace access, agency profile setup, and team invitation. Designed for direct outreach initially (you contact them), with referral and search channels planned for later phases.

**Who:** Agency owners (solo or with team)
**What:** Complete onboarding from signup to first trip
**Why:** Without this front door, no one can use the system

---

## 2. Primary User Action

**Email + Password → Workspace → First Trip**

The critical path:
1. Owner receives outreach email with signup link
2. Enters email + password
3. Lands in workspace immediately (no gates)
4. Creates first trip manually
5. (Optional) Sets up agency profile when adding agents

**Success metric:** Owner creates first trip within 5 minutes of signup

---

## 3. Design Direction

**Tone:** Immediate, capable, welcoming. The onboarding should feel like "I can use this right now" — not a series of forms.

**Aesthetic alignment:**
- Palantir-inspired dark theme
- Data-dense but not overwhelming for first-timers
- Empty states teach by showing, not telling
- Progressive disclosure of features

**Reference patterns:**
- Linear: Immediate access, dismissible checklist
- AWS: Code-based team access
- Notion: Sample content over tutorials

---

## 4. Layout Strategy

### Signup Page
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    [Logo]                                   │
│                                                             │
│              Travel Agency Workspace                        │
│                                                             │
│              For fast, efficient operations                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  Email                                              │   │
│  │  [you@agency.com                     ]              │   │
│  │                                                     │   │
│  │  Password                                           │   │
│  │  [••••••••                          ]              │   │
│  │                                                     │   │
│  │  [              Create Account              ]       │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│              Already have an account? Sign in               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Empty State (First Login)
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Sidebar                    │  Main Content                           │
│                             │                                         │
│  ┌──────────────────────┐   │  ┌─────────────────────────────────────┐│
│  │ Getting Started  ●3  │   │  │                                     ││
│  ├──────────────────────┤   │  │   Welcome to your workspace!          ││
│  │ ☐ First trip         │   │  │                                     ││
│  │ ☐ Agency profile     │   │  │   Let's get you started.             ││
│  │ ☐ Add team members   │   │  │                                     ││
│  └──────────────────────┘   │  │   ┌─────────────────────────────┐    ││
│                             │   │   │  [N] New Trip               │    ││
│  ┌──────────────────────┐   │   │   │                             │    ││
│  │ Workspace            │   │   │   └─────────────────────────────┘    ││
│  ├──────────────────────┤   │   │                                     ││
│  │ Your code:           │   │   │   Your workspace is ready.          ││
│  │ TRI-7892-PLY  [Copy] │   │   │   Create your first trip or          ││
│  │                     │   │   │   explore the panels below.           ││
│  │ [Generate new]      │   │   │                                     ││
│  └──────────────────────┘   │   └─────────────────────────────────────┘│
│                             │                                         │
│  ┌──────────────────────┐   │  ┌─────────────────────────────────────┐│
│  │                     │   │  │  Workspace Panels                    ││
│  │  Inbox (0)          │   │  │  ┌─────┐ ┌─────┐ ┌─────┐             ││
│  │  Workspace          │   │  │  │Intake│ │Packet│ │... │             ││
│  │  Insights           │   │  │  └─────┘ └─────┘ └─────┘             ││
│  │  Settings           │   │  │                                     ││
│  │                     │   │  │  Configure panels for your workflow  ││
│  └──────────────────────┘   │  └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Agency Profile Modal (Triggered when needed)
```
┌─────────────────────────────────────────────────────────────┐
│  Set up your agency profile                    [×]          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Before adding team members, let's set up your agency:      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Agency Name *                                       │   │
│  │  [Priya Travels                          ]           │   │
│  │                                                     │   │
│  │  Email                                              │   │
│  │  [contact@priyatravels.com                ]           │   │
│  │                                                     │   │
│  │  Phone                                              │   │
│  │  [+91 98765 43210                       ]           │   │
│  │                                                     │   │
│  │  Logo                                               │   │
│  │  [Upload or paste URL]                   [Browse]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  This info appears on customer communications and           │
│  agent invitations.                                         │
│                                                             │
│              [Save and Continue]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Team Management Page
```
┌─────────────────────────────────────────────────────────────┐
│  Team Management                              [+ Add Agent] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Invite by sharing workspace code:                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │   Internal Agent Code:                              │   │
│  │   ┌───────────────────────────────────────────────┐ │   │
│  │   │       TRI-7892-PLY        [Copy] [Regenerate] │ │   │
│  │   └───────────────────────────────────────────────┘ │   │
│  │                                                     │   │
│  │   Share this code with your agents. They'll enter  │   │
│  │   it when signing up to join your workspace.       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │   External Agent Code:                              │   │
│  │   ┌───────────────────────────────────────────────┐ │   │
│  │   │       EXT-TRI-7892          [Copy] [Regenerate]│ │   │
│  │   └───────────────────────────────────────────────┘ │   │
│  │                                                     │   │
│  │   For vendors, contractors, and part-time agents.  │   │
│  │   External agents have limited access.             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Team Members (2/4 free slots used):                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  👤 You                      Owner                   │   │
│  │  👤 Rahul Sharma       rahul@...     Agent          │   │
│  │  👤 Priya Singh        priya@...     Agent          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Upgrade for unlimited agents]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Key States

### Signup Form
- **Default:** Email + password fields
- **Validating:** Spinner on button
- **Error:** "Email already exists" with link to sign in
- **Success:** Redirect to workspace

### First Login (Empty State)
- **Default:** Welcome message, "New Trip" CTA highlighted, sidebar checklist
- **After first trip:** Checklist updates, normal workspace view
- **Dismissed checklist:** Sidebar collapses to normal

### Agency Profile Modal
- **Trigger:** User clicks "Add team members" OR starts customer comms
- **Validation:** Agency name required before saving
- **Skip allowed:** No, must complete if triggered
- **After save:** Modal closes, returns to previous action

### Team Codes
- **Generated:** New code shown, copy button highlighted
- **Shared:** Code marked as "shared" in DB
- **Active:** Agent joined, shown in team list
- **Regenerated:** Old code invalidated, new code generated

### Agent Signup (with code)
- **Code valid:** Shows agency name, continue to create account
- **Code invalid:** "Check with your agency owner"
- **Code expired:** Shouldn't happen (codes never expire)
- **Already joined:** "You're already part of this workspace"

---

## 6. Interaction Model

### Signup Flow
```
[Email/Password entry]
    ↓
[Validate format]
    ↓
[Create account → workspace → owner user]
    ↓
[Redirect to /workspace]
```

### First Login Flow
```
[Workspace loads empty]
    ↓
[Show welcome state + "New Trip" CTA]
    ↓
[User creates first trip]
    ↓
[Checklist updates, normal workspace]
```

### Agency Profile Trigger
```
[User clicks "Add team members"]
    ↓
[Check: agency.name exists?]
    ├─ Yes → Show team management
    └─ No → Show agency profile modal
           ↓
           [User saves profile]
           ↓
           [Show team management]
```

### Agent Signup Flow
```
[Agent enters email + password + workspace code]
    ↓
[Validate code → get workspace]
    ↓
[Create account → assign to workspace]
    ↓
[Redirect to /workspace]
```

### Keyboard Shortcuts
- `N` → New trip (from workspace)
- `Cmd+,` → Settings
- `Cmd+K` → Command palette (future)

---

## 7. Content Requirements

### Labels & Copy
- Signup page: "Create your account", "Already have an account? Sign in"
- Welcome: "Welcome to your workspace! Let's get you started."
- Empty state: "Create your first trip to get started"
- Checklist: "Getting Started", "Agency profile", "Add team members"
- Team page: "Invite by sharing workspace code", "Internal Agent Code", "External Agent Code"

### Validation Messages
- Email required: "Please enter your email"
- Email invalid: "Please enter a valid email"
- Password too short: "Password must be at least 8 characters"
- Email exists: "An account with this email already exists. Sign in?"
- Agency name required: "Please enter your agency name"
- Code invalid: "This workspace code is not valid. Check with your agency owner."

### Empty State Copy
- No trips: "No trips yet. Create your first trip to get started."
- No team: "No team members yet. Share your workspace code to add agents."
- Code section: "Your workspace code. Share it with agents to add them to your workspace."

---

## 8. Data Model

### Workspace
```typescript
interface Workspace {
  id: string;
  name: string;              // Agency name
  slug: string;              // URL-friendly
  email?: string;            // Contact email
  phone?: string;            // Contact phone
  logoUrl?: string;
  createdAt: string;
  ownerId: string;           // Reference to user
  plan: 'free' | 'pro';
  settings: {
    currency: string;
    timezone: string;
  };
}
```

### Workspace Code
```typescript
interface WorkspaceCode {
  id: string;
  workspaceId: string;
  code: string;              // e.g., TRI-7892-PLY or EXT-TRI-7892
  codeType: 'internal' | 'external';
  status: 'generated' | 'shared' | 'active' | 'inactive';
  createdBy: string;
  createdAt: string;
  usedBy?: string;           // Agent who used this code
  usedAt?: string;
}
```

### User (enhanced)
```typescript
interface User {
  id: string;
  email: string;
  passwordHash: string;
  name?: string;
  workspaceId: string;
  role: 'owner' | 'admin' | 'agent' | 'external';
  isActive: boolean;
  createdAt: string;
  lastLoginAt?: string;
}
```

---

## 9. Technical Considerations

### Auth Provider
- **Phase 1:** Custom email/password (simple, fast)
- **Phase 2:** Integrate Clerk for OAuth, magic links
- **Migration path:** Hash compatibility, token structure

### Code Generation
```typescript
const SYLLABLES = [
  'TRI', 'VOY', 'TUR', 'DES', 'TIN',
  'JOU', 'RNY', 'RNE', 'EXL', 'SCP',
  // ... 40 total
];

function generateInternalCode(): string {
  const s1 = SYLLABLES[Math.floor(Math.random() * SYLLABLES.length)];
  const s2 = SYLLABLES[Math.floor(Math.random() * SYLLABLES.length)];
  const digits = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
  return `${s1}-${digits}-${s2}`; // TRI-7892-PLY
}

function generateExternalCode(): string {
  const s1 = SYLLABLES[Math.floor(Math.random() * SYLLABLES.length)];
  const digits = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
  return `EXT-${s1}-${digits}`; // EXT-TRI-7892
}
```

### Agency Name Validation
```typescript
// Trigger: User tries to add team OR start customer comms
function requireAgencyProfile(workspace: Workspace): boolean {
  if (!workspace.name) {
    showAgencyProfileModal();
    return false; // Block action until profile complete
  }
  return true;
}
```

### Session Management
```typescript
// JWT token structure
interface JWTPayload {
  sub: string;           // userId
  workspaceId: string;
  role: string;
  exp: number;
}

// Middleware: scope all queries by workspaceId
app.use((req, res, next) => {
  const token = decodeJWT(req.headers.authorization);
  req.user = token;
  req.workspaceId = token.workspaceId; // For multi-tenant scoping
  next();
});
```

---

## 10. Phased Implementation

### Phase 1: Foundation (Current)
- Email + password signup
- Workspace auto-creation
- Empty state with "New Trip" CTA
- Manual trip entry
- Workspace code generation (internal only)
- Agent signup with workspace code
- Agency profile modal (triggered by team add)

### Phase 2: Team Features
- Team management page
- Internal vs external code types
- Free tier messaging (3/4 slots)
- Role assignment
- Team member list

### Phase 3: Polish
- Progressive onboarding checklist
- Onboarding tooltips
- First trip tutorial
- Agency profile customization (logo, branding)
- Workspace settings page

### Phase 4: Customer Comms
- Agency profile requirement enforcement
- Email templates with agency branding
- Customer portal education (when ready)

---

## 11. Success Criteria

- [ ] Owner can sign up with email + password
- [ ] Workspace created immediately on signup
- [ ] Owner lands in workspace with clear "New Trip" CTA
- [ ] Owner can create first trip manually
- [ ] Workspace code generated and visible
- [ ] Agent can signup with workspace code
- [ ] Agent joins workspace successfully
- [ ] Agency profile required before adding team
- [ ] Empty state feels welcoming, not empty

---

## 12. Anti-Patterns to Avoid

- ❌ Don't gate workspace behind setup forms
- ❌ Don't show generic "welcome" carousel
- ❌ Don't force agency name entry before first value
- ❌ Don't use email invites (use codes instead)
- ❌ Don't make codes expire
- ❌ Don't show generic illustrations
- ❌ Don't hide the workspace code

---

## 13. Open Questions

1. **Password reset flow** — Self-service or you handle manually?
2. **Workspace name vs agency name** — Can they differ?
3. **External agent permissions** — What exactly can they access?
4. **Code regeneration** — Does old code stop working immediately?
5. **Multiple workspaces** — Can one user belong to multiple agencies?

---

**Ready for implementation.** This brief aligns with the Palantir-inspired, data-dense, fast, and reassuring design direction.
