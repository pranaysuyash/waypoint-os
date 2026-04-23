# Timeline Deep Dive 02: UX/UI Design

> Complete UI/UX exploration: every interaction state, edge case, visual design

---

## Part 1: Visual Design System

### Timeline Layout Options

#### Option A: Vertical Feed (Recommended)
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                               [Filter] [│]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🕐 TODAY — 9:00 AM                                            │  │
│  │ ┌─────────────────────────────────────────────────────────────┐ │  │
│  │ │ ✅ STATUS: Ready to Book                                    │ │  │
│  │ │                                                           │ │  │
│  │ │   Confidence: 87% • Decision by AI                        │ │  │
│  │ │   All questions answered. Budget confirmed.              │ │  │
│  │ │                                                           │ │  │
│  │ │   [View Rationale] [View Scenarios]                        │ │  │
│  │ └─────────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │ → This triggered: Customer notification sent                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🕐 YESTERDAY — 3:20 PM                                        │  │
│  │ ┌─────────────────────────────────────────────────────────────┐ │  │
│  │ │ 💬 CONVERSATION: Agent → Customer                           │ │  │
│  │ │                                                           │ │  │
│  │ │   "Sure! Phi Phi is great. I'll add it to the options."    │ │  │
│  │ │   [View Full Thread]                                       │ │  │
│  │ └─────────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │ → This triggered: Trip updated, AI re-analysis              │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🕐 YESTERDAY — 2:35 PM                                        │  │
│  │ 🤖 AI ANALYSIS: Scenarios Evaluated                          │  │
│  │ [▶ Expand]                                                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Familiar mental model (like social media feeds)
- Natural chronology
- Easy to scan
- Mobile-friendly

**Cons:**
- Can get long for complex trips
- Hard to compare parallel events

---

#### Option B: Swimlane Timeline
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Customer │    📧 Apr 20 ────────💬 Apr 22 ────────💬 Apr 25        │
│           │                                                   │        │
│  AI       │    🤖 Apr 20 ──🤖 Apr 20 ──🤖 Apr 21 ──✅ Apr 23          │
│           │          │          │          │         │        │
│  Agent    │              💬 Apr 22 ────────💬 Apr 23                 │
│           │                                                   │        │
│  Owner    │                            ┑─────────✅ Apr 23          │
│           │                                                   │        │
└─────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Shows parallel activity
- Clear responsibility
- Easy to spot gaps

**Cons:**
- Complex to implement
- Mobile-unfriendly
- Can get wide

---

#### Option C: Kanban Board
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline by Stage                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INQUIRY      │  ANALYSIS      │  DECISION      │  BOOKING       │
│  ┌──────────┐  │  ┌──────────┐  │  ┌──────────┐  │  ┌──────────┐  │
│  │📧 Apr 20 │  │  │🤖 Extract│  │  │✅ Ready  │  │  │          │  │
│  │          │  │  │🤖 Scenar │  │  │          │  │  │          │  │
│  └──────────┘  │  │🤖 Decide │  │  └──────────┘  │  └──────────┘  │
│               │  └──────────┘  │               │               │
└─────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Clear stages
- Easy to see what's pending
- Good for process visualization

**Cons:**
- Loses chronology
- Hard to see relationships
- Not story-like

---

### Design Decision: Vertical Feed with Expandable Details

**Why:**
1. Story-driven (chronological narrative)
2. Mobile-friendly (vertical scroll)
3. Progressive disclosure (summary → expand → detail)
4. Familiar mental model

---

## Part 2: Event Type Visual Design

### Event Card Components

```
┌─────────────────────────────────────────────────────────────────────┐
│  [ICON] [EVENT TYPE] — [TIME]                           [▲] [⋯]   │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                                                               │ │
│  │  [SUMMARY TEXT - 1-2 lines]                                   │ │
│  │                                                               │ │
│  │  [BADGES] [TAGS]                                              │ │
│  │                                                               │ │
│  │  [ACTION BUTTONS]                                             │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  → [TRIGGERED EFFECTS] (if any)                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Icon System

| Event Category | Icons (Lucide) | Color |
|---------------|----------------|-------|
| Origin | `Mail`, `MessageCircle`, `Phone` | Blue |
| Analysis | `BrainCircuit`, `GitBranch`, `Search` | Purple |
| Decision | `CheckCircle`, `XCircle`, `AlertTriangle` | Green/Red/Yellow |
| Conversation | `MessageSquare`, `Send` | Orange |
| Action | `Edit`, `UserPlus`, `Tag` | Gray |
| Review | `Eye`, `Shield`, `Stamp` | Indigo |
| System | `Settings`, `Clock`, `Zap` | Gray |

### Badge System

```
┌─────────────────────────────────────────────────────────────────────┐
│  [✅ Ready] [87% confidence] [AI] [Customer: John Doe]             │
└─────────────────────────────────────────────────────────────────────┘

Badge styles:
- Status: Solid background, white text
- Confidence: Outlined, colored text
- Actor: Subtle gray background
- Tags: Outlined, small
```

### Color Palette

```
Semantic Colors:
- Success: #3fb950 (green)
- Warning: #d29922 (yellow)
- Error: #f85149 (red)
- Info: #58a6ff (blue)

Category Colors:
- Origin: #58a6ff (blue)
- Analysis: #a371f7 (purple)
- Decision: #3fb950 (green)
- Conversation: #f0883e (orange)
- Review: #8957e5 (indigo)
- System: #8b949e (gray)
```

---

## Part 3: Interaction States

### State 1: Loading
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ⏳ Loading timeline...                                         │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │ ████████████████░░░░░░░  Loading events...             │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### State 2: Empty (No Events)
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  📭 No events yet                                              │  │
│  │                                                               │  │
│  │  Events will appear here as the trip progresses.             │  │
│  │                                                               │  │
│  │  Typical events:                                              │  │
│  │  • Customer inquiries                                         │  │
│  │  • AI analysis results                                        │  │
│  │  • Decision status changes                                    │  │
│  │  • Conversations with customer                                │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### State 3: Error State
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ⚠️ Couldn't load timeline                                     │  │
│  │                                                               │  │
│  │  There was a problem loading the timeline.                   │  │
│  │                                                               │  │
│  │  [Retry] [Load Cached] [Report Issue]                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### State 4: Collapsed (Default View)
```
┌─────────────────────────────────────────────────────────────────────┐
│  🕐 TODAY — 9:00 AM                                                │
│  ✅ STATUS: Ready to Book (87% confidence)                   [▶]   │
└─────────────────────────────────────────────────────────────────────┘
```

### State 5: Expanded (Detail View)
```
┌─────────────────────────────────────────────────────────────────────┐
│  🕐 TODAY — 9:00 AM                                                │
│  ✅ STATUS: Ready to Book                                    [▲]   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │   Confidence: 87% • Decision by AI                            │  │
│  │   All questions answered. Budget confirmed at ₹2L.           │  │
│  │   Selected scenario: Phuket + Krabi + Phi Phi               │  │
│  │                                                               │  │
│  │   ┌─────────────────────────────────────────────────────────┐ │  │
│  │   │ RATIONALE:                                             │ │  │
│  │   │ • Budget is realistic for Thailand destinations        │ │  │
│  │   │ • June is good weather for Andaman coast                │ │  │
│  │   │ • No visa blockers identified                           │ │  │
│  │   │ • Honeymoon travelers prefer relaxed itinerary           │ │  │
│  │   └─────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │   [View Full Rationale] [View Scenarios] [Export]           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  → Triggered: Customer notification sent                           │
└─────────────────────────────────────────────────────────────────────┘
```

### State 6: Filtered
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                               [× Clear]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Active filters: [Conversation] [Last 7 days]                     │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 YESTERDAY — 3:20 PM                                        │  │
│  │  💬 CONVERSATION: Agent → Customer                           │  │
│  │  [View Full Thread]                                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 YESTERDAY — 2:35 PM                                        │  │
│  │  💬 CONVERSATION: Customer → Agent                           │  │
│  │  [View Full Thread]                                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [Showing 2 of 15 events — View all]                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Filter & Search UI

### Filter Panel
```
┌─────────────────────────────────────────────────────────────────────┐
│  Filter Timeline                                        [Reset]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  EVENT TYPES                                                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ☑ Inquiries (12)    ☑ Analysis (8)    ☑ Decisions (3)      │  │
│  │  ☑ Conversations (5)  ☐ Reviews (0)     ☐ System (1)        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ACTORS                                                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ☑ Customer (5)      ☑ Agents (3)       ☑ Owner (1)         │  │
│  │  ☑ AI (8)            ☐ System (0)                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  TIME RANGE                                                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ● All time  ○ Last 7 days  ○ Last 30 days  ○ Custom        │  │
│  │                                                           │  │
│  │  Custom:  [Apr 15] to [Apr 23]                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  SEARCH                                                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  [Search in timeline...                   🔍]               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  TAGS                                                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ☐ #budget-issue    ☐ #visa-question    ☐ #escalation       │  │
│  │  ☐ #customer-happy ☐ #high-value       ☐ #followup-needed  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│                            [Apply Filters] [Cancel]               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Search Autocomplete
```
┌─────────────────────────────────────────────────────────────────────┐
│  [Search in timeline... "budget"                     🔍]        │  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  "budget" in timeline...                                      │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │ 📊 Budget analysis — Apr 22                           │  │  │
│  │  │ 💬 "Is 2L enough?" — Apr 21                           │  │  │
│  │  │ 🤖 Budget breakdown decision — Apr 21                 │  │  │
│  │  │ 💬 "Budget confirmed" — Apr 20                         │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │  [Search all events for "budget" →]                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 5: Specialized Views

### View 1: Conversation Thread
```
┌─────────────────────────────────────────────────────────────────────┐
│  Conversation Thread                                  [Back]        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  💬 Conversation with John Doe (+91 98765 43210)                  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 Apr 22 — 3:20 PM — YOU → CUSTOMER                       │  │
│  │  ┌───────────────────────────────────────────────────────────┐ │  │
│  │  │ Sure! Phi Phi is great. I'll add it to the options.      │ │  │
│  │  │ For Indians, Thailand offers visa on arrival — just need │ │  │
│  │  │ passport with 6 months validity.                         │ │  │
│  │  │                                                           │ │  │
│  │  │ [Sent via WhatsApp • Delivered at 3:20 PM]               │ │  │
│  │  └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 Apr 22 — 3:15 PM — CUSTOMER → YOU                         │  │
│  │  ┌───────────────────────────────────────────────────────────┐ │  │
│  │  │ Can you also include Phi Phi islands? And any visa info? │ │  │
│  │  │                                                           │ │  │
│  │  │ [Received via WhatsApp]                                   │ │  │
│  │  └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 Apr 20 — 2:35 PM — AI → CUSTOMER (Auto-response)         │  │
│  │  ┌───────────────────────────────────────────────────────────┐ │  │
│  │  │ Thanks for reaching out! I've extracted some details...   │ │  │
│  │  │ [View Full AI Response]                                   │ │  │
│  │  └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [Send Message] [View on WhatsApp] [Export Thread]                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### View 2: Decision Trail
```
┌─────────────────────────────────────────────────────────────────────┐
│  Decision Trail                                        [Back]        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DECISION EVOLUTION                                                  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ✅ READY TO BOOK — Apr 23, 9:00 AM                            │  │
│  │  ┌───────────────────────────────────────────────────────────┐ │  │
│  │  │ Confidence: 87%                                            │ │  │
│  │  │ All blockers cleared. Budget confirmed.                  │ │  │
│  │  │                                                           │ │  │
│  │  │ CHANGED FROM: Draft Quote (Apr 22)                       │ │  │
│  │  │ REASON: Customer confirmed final dates                    │ │  │
│  │  └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  📝 DRAFT QUOTE — Apr 22, 3:30 PM                             │  │
│  │  ┌───────────────────────────────────────────────────────────┐ │  │
│  │  │ Confidence: 72%                                            │ │  │
│  │  │ Awaiting customer confirmation on final dates              │ │  │
│  │  │                                                           │ │  │
│  │  │ CHANGED FROM: Needs Attention (Apr 21)                   │ │  │
│  │  │ REASON: Customer provided dates: June 15-25              │ │  │
│  │  └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ⚠️  NEEDS ATTENTION — Apr 21, 2:32 PM                        │  │
│  │  ┌───────────────────────────────────────────────────────────┐ │  │
│  │  │ Confidence: 45%                                            │ │  │
│  │  │ Date window too broad. Budget unclear.                     │ │  │
│  │  │                                                           │ │  │
│  │  │ CHANGED FROM: Ask Followup (Apr 20)                      │ │  │
│  │  │ REASON: AI extracted partial info                          │ │  │
│  │  └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [View Decision Graph] [Export Decision Log]                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### View 3: Analytics Timeline
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline Analytics                                   [Back]        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TIME IN STAGE                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Intake        │███████████████████░░░░░│ 2 days             │  │
│  │  Analysis      │█████████████████████████│ 3 days             │  │
│  │  Options       │███████████████████████████████████│ 5 days   │  │
│  │  Decision      │███████████████░░░░░░░░░░░│ 1.5 days           │  │
│  │  Booking       │███████████░░░░░░░░░░░░░░░│ 1 day            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Total: 12.5 days • Compared to avg: 11 days • +14% slower           │
│                                                                      │
│  BOTTLENECKS                                                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ⚠️ Options Stage — 5 days (avg: 3 days)                      │  │
│  │     Cause: Waiting for supplier quotes, 2 customer revisions  │  │
│  │     Suggestion: Pre-negotiate supplier rates                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ACTIVITY HEATMAP                                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Mon Tue Wed Thu Fri Sat Sun                                 │  │
│  │  ░░░ ████████ ░░░ ░░░ ░░░ ██████                          │  │
│  │  12  34       5   8   3   12                               │  │
│  │                                                           │  │
│  │  Most active: Tuesday (34 events)                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Edge Cases & Error States

### Edge Case 1: Very Long Timeline (1000+ events)
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                               [Load more]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ⚠️ This trip has 1,247 events. Showing recent 50.                 │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 TODAY — 9:00 AM                                            │  │
│  │  ✅ STATUS: Ready to Book                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 YESTERDAY — 3:20 PM                                       │  │
│  │  💬 CONVERSATION: Agent → Customer                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [Load 50 more] [Jump to beginning] [Filter events]                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Edge Case 2: Timeline with Gaps
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 TODAY — 9:00 AM                                            │  │
│  │  ✅ STATUS: Ready to Book                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ⏸️ 7-day gap — No activity                                       │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 APR 16 — 2:30 PM                                           │  │
│  │  💬 CONVERSATION: Customer → Agent                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [What happened during the gap?]                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Edge Case 3: Corrupted/Invalid Event
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 TODAY — 9:00 AM                                            │  │
│  │  ✅ STATUS: Ready to Book                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ⚠️ UNREADABLE EVENT — Apr 22, 3:15 PM                        │  │
│  │  ┌───────────────────────────────────────────────────────────┐ │  │
│  │  │ This event could not be loaded. Data may be corrupted.  │ │  │
│  │  │                                                           │ │  │
│  │  │ [Report Issue] [Attempt Repair]                            │ │  │
│  │  └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Responsive Design

### Desktop (> 1024px)
```
┌─────────────────────────────────────────────────────────────────────┐
│  Left Panel (300px) │  Timeline (auto)     │  Right Panel (300px) │
│  - Trip details      │  - Events feed       │  - Related events    │
│  - Quick actions     │  - Chronological     │  - Filters           │
│  - Participants      │                      │  - Search            │
└─────────────────────────────────────────────────────────────────────┘
```

### Tablet (768px - 1024px)
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline (auto)                                     [Filters] [⋮] │
│  - Events feed                                                      │
│  - Filters in drawer                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Mobile (< 768px)
```
┌─────────────────────────────────────────────────────────────────────┐
│  Timeline                                                 [⋯] [Filter] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 TODAY — 9:00 AM                                  [▶]       │  │
│  │  ✅ STATUS: Ready to Book (87%)                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  🕐 YESTERDAY — 3:20 PM                               [▶]       │  │
│  │  💬 Agent → Customer                                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 8: Accessibility

### Keyboard Navigation
```
Shortcuts:
- Arrow Down/Up: Navigate events
- Enter/Space: Expand/collapse event
- Escape: Close expanded view
- Cmd+F: Focus search
- Cmd+K: Open filter panel
- Home: Jump to first event
- End: Jump to last event
```

### Screen Reader Support
```html
<!-- ARIA labels -->
<div role="feed" aria-label="Trip timeline">
  <article role="article" aria-label="Event: Ready to Book, April 23 9 AM">
    <div aria-level="2">Ready to Book</div>
    <p>Confidence: 87%. Decision by AI.</p>
    <button aria-expanded="false" aria-controls="event-details">
      Show details
    </button>
    <div id="event-details" role="region" aria-live="polite">
      <!-- Expanded content -->
    </div>
  </article>
</div>
```

### High Contrast Mode
```
Colors adjusted for WCAG AAA:
- Text: #ffffff on #0d1117
- Links: #58a6ff (underline)
- Borders: 2px solid #30363d
- Focus: 3px solid #58a6ff
```

---

**Status:** UX/UI deep dive complete
