# Discovery Gap: Trip Story / Timeline / History

**Date:** 2026-04-22
**Issue:** Workspace shows current state but not the story of how we got there

---

## What Exists vs What's Missing

### What Exists (Current Panels)

| Panel | Shows | Doesn't Show |
|-------|-------|--------------|
| **IntakePanel** | Current field values (destination, budget, etc.) | How values evolved, why they were set |
| **DecisionPanel** | Current decision state, blockers, risk flags | Why these blockers exist, what was tried |
| **OutputPanel** | Final internal/traveler bundles | How we got to these outputs |
| **ChangeHistoryPanel** | Field edits (who changed what when) | Only tracks manual field edits, not AI decisions |

### What's Missing — The Story

```
INBOX CARD → Workspace
     ↓
    ???

Where's the narrative of:
- Original customer message/inquiry
- AI analysis steps and reasoning
- Conversations with customer
- Scenarios evaluated
- Decisions made and why
- Timeline of all events
```

---

## User's Vision

> "there's no history, log etc of all the conversations, ai decisions etc which has led to the current state of the card"

> "even with mock we should have everything played out, all kinds of scenarios mapped out"

**Key insight:** The workspace should tell the **complete story** of the trip — from first inquiry to current state. This is critical for:
1. **Agent handoffs** — New agent understanding the context
2. **Review/Audit** — Owner understanding why decisions were made
3. **Learning** — Understanding patterns across trips
4. **Reassurance** — Agent feels confident knowing the full context

---

## What the Timeline Should Include

### 1. Origin Story
```
┌─────────────────────────────────────────────────────────────┐
│  Trip Started                                               │
├─────────────────────────────────────────────────────────────┤
│  📅 April 20, 2026 at 2:30 PM                              │
│  📧 Source: WhatsApp                                        │
│  👤 Customer: John Doe (+91 98765 43210)                   │
│                                                             │
│  "Hi, planning a honeymoon to Thailand in June. 2 people,   │
│   around 2L budget. Looking for beaches and nice stays."    │
│                                                             │
│  [Raw Message] → [Extracted Data]                          │
└─────────────────────────────────────────────────────────────┘
```

### 2. AI Analysis Trail
```
┌─────────────────────────────────────────────────────────────┐
│  Analysis: Extracted Facts                                 │
├─────────────────────────────────────────────────────────────┤
│  ✅ Destination: Thailand (confidence: 95%)                 │
│  ✅ Trip Type: Honeymoon (confidence: 87%)                  │
│  ✅ Party Size: 2 (confidence: 99%)                         │
│  ✅ Budget: ₹2L (confidence: 92%)                           │
│  ⚠️ Date Window: June (confidence: 60%) — needs followup    │
│                                                             │
│  [View Rationale] → [View Evidence]                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Analysis: Decision Logic                                   │
├─────────────────────────────────────────────────────────────┤
│  🔍 Scenarios Evaluated:                                    │
│  • Scenario A: Phuket + Krabi (budget fit: ✅)             │
│  • Scenario B: Bangkok + Pattaya (budget fit: ✅)           │
│  • Scenario C: Samui + Phangan (budget fit: ⚠️ tight)       │
│                                                             │
│  ✅ Selected: Scenario A (best balance of beach + budget)   │
│                                                             │
│  [View Scenarios] → [View Comparison]                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┤
│  Decision: PROCEED_TRAVELER_SAFE                            │
├─────────────────────────────────────────────────────────────┤
│  Overall Confidence: 87%                                    │
│  Rationale:                                                 │
│  • Budget is realistic for Thailand destinations            │
│  • June is good weather for Andaman coast                   │
│  • Honeymoon travelers prefer relaxed itinerary             │
│  • No visa blockers identified                             │
│                                                             │
│  [View Full Rationale]                                      │
└─────────────────────────────────────────────────────────────┘
```

### 3. Conversation History
```
┌─────────────────────────────────────────────────────────────┐
│  💬 Conversation Thread                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🕐 Apr 20, 2:30 PM — Customer (WhatsApp)                  │
│  "Hi, planning a honeymoon to Thailand..."                  │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  🕐 Apr 20, 2:35 PM — AI (Auto-response)                   │
│  "Thanks for reaching out! I've extracted some details..."  │
│  [View AI Response]                                         │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  🕐 Apr 20, 3:15 PM — Customer (WhatsApp)                  │
│  "Can you also include Phi Phi islands? And any visa info?" │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  🕐 Apr 20, 3:20 PM — Agent (Rahul)                         │
│  "Sure! Phi Phi is great. I'll add it to the options.       │
│   For Indians, Thailand offers visa on arrival..."          │
│  [View Full Response]                                       │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  🕐 Apr 21, 10:00 AM — System                              │
│  "Trip updated: Added Phi Phi to itinerary"                 │
│  "Trip updated: Visa information added"                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Decision Timeline
```
┌─────────────────────────────────────────────────────────────┐
│  📊 Decision Timeline                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Apr 20, 2:32 PM — Needs Attention                         │
│  → Missing date specifics, budget vague                     │
│  → ASK_FOLLOWUP triggered                                   │
│                                                             │
│  Apr 20, 3:20 PM — Draft Quote                             │
│  → Agent provided more details                              │
│  → PROCEED_INTERNAL_DRAFT                                   │
│                                                             │
│  Apr 21, 9:00 AM — Ready to Book                           │
│  → All questions answered                                   │
│  → PROCEED_TRAVELER_SAFE                                    │
│  → Confidence: 87%                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Model Requirements

### Trip Event
```typescript
interface TripEvent {
  id: string;
  tripId: string;
  timestamp: string;
  eventType: 'inquiry_received' | 'analysis_complete' | 'decision_changed'
              | 'conversation_message' | 'field_updated' | 'status_changed';
  source: 'customer' | 'agent' | 'ai' | 'system';
  actorId?: string;  // userId or 'system'
  actorName?: string;

  // Event-specific data
  data: {
    // For inquiry_received
    originalMessage?: string;
    channel?: 'whatsapp' | 'email' | 'phone';

    // For analysis_complete
    analysisType?: 'extraction' | 'scenario_evaluation' | 'decision';
    confidence?: number;
    rationale?: string;
    scenariosEvaluated?: Scenario[];

    // For decision_changed
    fromState?: string;
    toState?: string;
    reason?: string;

    // For conversation_message
    message?: string;
    direction?: 'inbound' | 'outbound';
    medium?: string;

    // For field_updated
    field?: string;
    oldValue?: any;
    newValue?: any;
  };

  // Relationships
  relatedEvents?: string[];  // IDs of related events
  evidence?: Evidence[];     // Source data for AI decisions
}
```

### Scenario
```typescript
interface Scenario {
  id: string;
  name: string;
  description: string;
  budgetFit: 'excellent' | 'good' | 'tight' | 'over';
  pros: string[];
  cons: string[];
  estimatedCost: { low: number; high: number };
  selected: boolean;
  rationale?: string;
}
```

---

## UI Approach: Timeline Panel

### Location in Workspace
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Sidebar                    │  Main Content                           │
│                             │                                         │
│  ┌──────────────────────┐   │  ┌─────────────────────────────────────┐│
│  │ Panels               │   │  │  [Intake, Packet, Decision, etc.]   ││
│  ├──────────────────────┤   │  │                                     ││
│  │ ☑ Intake             │   │  │                                     ││
│  │ ☑ Packet             │   │  │                                     ││
│  │ ☑ Decision           │   │  │                                     ││
│  │ ☐ Timeline  [NEW]    │   │  │                                     ││
│  │ ☑ Output             │   │  │                                     ││
│  │ ☑ Feedback           │   │  │                                     ││
│  └──────────────────────┘   │  └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Timeline Panel Design
```
┌─────────────────────────────────────────────────────────────┐
│  Timeline                                            [Filter]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🕐 Apr 21 — 9:00 AM                                │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ ✅ Ready to Book                              │  │   │
│  │  │    Confidence: 87%                            │  │   │
│  │  │                                               │  │   │
│  │  │   All questions answered. Budget confirmed.  │  │   │
│  │  │   Destination: Phuket + Krabi + Phi Phi      │  │   │
│  │  │                                               │  │   │
│  │  │   [View Details] [View Rationale]            │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🕐 Apr 20 — 3:20 PM                                │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ 💬 Agent (Rahul) → Customer                  │  │   │
│  │  │                                               │  │   │
│  │  │   "Sure! Phi Phi is great. I'll add it to    │  │   │
│  │  │    the options. For Indians, Thailand        │  │   │
│  │  │    offers visa on arrival..."                │  │   │
│  │  │                                               │  │   │
│  │  │   [View Full Message]                         │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  │  → Triggered: Trip updated with Phi Phi            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🕐 Apr 20 — 2:35 PM                                │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ 🤖 AI Analysis: Scenarios Evaluated          │  │   │
│  │  │                                               │  │   │
│  │  │   Scenario A: Phuket + Krabi ✅               │  │   │
│  │  │   Scenario B: Bangkok + Pattaya ✅             │   │   │
│  │  │   Scenario C: Samui + Phangan ⚠️                │   │   │
│  │  │                                               │  │   │
│  │  │   Selected: A (best balance)                  │   │   │
│  │  │                                               │  │   │
│  │  │   [View All Scenarios] [Compare]              │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🕐 Apr 20 — 2:30 PM                                │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ 📧 Inquiry Received                           │  │   │
│  │  │                                               │  │   │
│  │  │   "Hi, planning a honeymoon to Thailand       │  │   │
│  │  │    in June. 2 people, around 2L budget."     │  │   │
│  │  │                                               │  │   │
│  │  │   [View Raw Message] [Extracted Data]        │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  │  → Triggered: Initial extraction, ASK_FOLLOWUP     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Event Storage (Backend)
- Trip events table in database
- Event types defined
- API to store/retrieve events
- Mock data generator for testing

### Phase 2: Timeline Panel (Frontend)
- Timeline component
- Event type renderers
- Filtering (by type, source, date)
- Expandable details

### Phase 3: Integration
- Wire up actual AI events from pipeline
- Connect conversation sources (WhatsApp, email)
- Real-time updates

### Phase 4: Mock Scenarios
- Generate realistic timeline data
- Show various decision paths
- Demonstrate handoff scenarios

---

## Open Questions

1. **Event storage** — Where do events live? New table or augment existing?
2. **Mock data** — Should we build a mock scenario generator?
3. **Conversation sources** — How do we integrate WhatsApp/email history?
4. **AI decision trail** — Is this already captured in spine output?
5. **Performance** — Timeline for long-running trips (months of history)?

---

**Status:** Gap identified, requirements gathering in progress
