# Design Brief: Trip Timeline Panel

> Feature: Complete story timeline showing how a trip reached its current state
> Status: Design phase — with mock scenarios
> Date: 2026-04-22

---

## 1. Feature Summary

A timeline panel in the workspace that shows the complete narrative of a trip — from first customer inquiry through all AI analyses, conversations, decisions, and state changes. This enables agent handoffs, owner review, and learning from patterns.

**Who:** Agents (understanding context), Owners (reviewing decisions), New agents (onboarding)
**What:** Chronological timeline of all trip events with full context
**Why:** "There's no history of conversations, AI decisions, etc. which led to the current state"

---

## 2. Primary User Action

**Click Timeline panel → See complete story → Understand context**

The critical use cases:
1. **Agent handoff:** "I'm taking over this trip — what happened?"
2. **Owner review:** "Why was this marked NEEDS ATTENTION?"
3. **Pattern learning:** "How do we usually handle Thailand honeymoons?"
4. **Customer context:** "What did we promise this customer?"

---

## 3. Design Direction

**Tone:** Narrative, contextual, reassuring. The timeline should read like a story — not a log file.

**Visual approach:**
- Chronological flow (oldest at bottom, newest at top)
- Event types visually distinct
- Expandable details (summary → full context)
- Related events grouped

**Reference patterns:**
- GitHub commit timeline (chronological, expandable)
- Linear activity feed (grouped events, clear actors)
- Notion page history (show what changed)

---

## 4. Mock Scenario: Thailand Honeymoon

### Complete Timeline Story

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRIP: Thailand Honeymoon | John Doe | ID: THA-2024-001               │
│                                                                         │
│  Timeline                                               [▼ Filter]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 TODAY — 9:00 AM                                                    │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ ✅ STATUS: Ready to Book                                         │ │
│  │                                                                   │ │
│  │   Confidence: 87% • Decision by: AI                              │ │
│  │                                                                   │ │
│  │   All questions answered. Budget confirmed at ₹2L.              │ │
│  │   Selected scenario: Phuket + Krabi + Phi Phi.                  │ │
│  │   No blockers. Awaiting owner approval.                          │ │
│  │                                                                   │ │
│  │   [View Rationale] [View Scenarios] [View Budget Breakdown]      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 YESTERDAY — 3:20 PM                                                │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 💬 AGENT (Rahul) → CUSTOMER (WhatsApp)                          │ │
│  │                                                                   │ │
│  │   "Sure! Phi Phi is great. I'll add it to the options.           │ │
│  │    For Indians, Thailand offers visa on arrival — just           │ │
│  │    need passport with 6 months validity."                         │ │
│  │                                                                   │ │
│  │   Customer replied: "Great, thanks! What about the              │ │
│  │    best time to visit in June?"                                  │ │
│  │                                                                   │ │
│  │   [View Full Thread]                                             │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  → TRIGGERED: Fields updated (destination, visa_info)                 │
│  → TRIGGERED: AI re-analysis with new constraints                     │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 YESTERDAY — 2:35 PM                                                │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 🤖 AI ANALYSIS: Scenarios Evaluated                             │ │
│  │                                                                   │ │
│  │   Evaluated 3 scenarios for honeymoon + ₹2L budget:              │ │
│  │                                                                   │ │
│  │   ✅ Scenario A: Phuket + Krabi (₹1.8L - ₹2.2L)                  │ │
│  │      • Best balance of beach + budget                           │ │
│  │      • Good weather in June                                      │ │
│  │      • Direct flights available                                  │ │
│  │                                                                   │ │
│  │   ✅ Scenario B: Bangkok + Pattaya (₹1.5L - ₹1.9L)              │ │
│  │      • More budget-friendly                                      │ │
│  │      • Less romantic, more touristy                              │ │
│  │                                                                   │ │
│  │   ⚠️  Scenario C: Samui + Phangan (₹2.1L - ₹2.6L)                │ │
│  │      • Beautiful but over budget                                 │ │
│  │      • Ferry travel can be rough in monsoon                      │ │
│  │                                                                   │ │
│  │   🏆 SELECTED: Scenario A (recommended)                          │ │
│  │                                                                   │ │
│  │   [View Detailed Comparison] [Why This Selection?]              │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  → TRIGGERED: Decision state → PROCEED_INTERNAL_DRAFT                 │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 YESTERDAY — 2:32 PM                                                │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 🤖 AI ANALYSIS: Decision Logic                                    │ │
│  │                                                                   │ │
│  │   STATE: ASK_FOLLOWUP → Needs Attention                          │ │
│  │                                                                   │ │
│  │   Rationale:                                                     │ │
│  │   • Date window "June" is too broad (confidence: 45%)            │ │
│  │   • Need specific dates for flight booking                      │ │
│  │   • Budget range is reasonable (confidence: 92%)                 │ │
│  │   • Honeymoon intent confirmed (confidence: 87%)                 │ │
│  │                                                                   │ │
│  │   FOLLOWUP QUESTIONS:                                            │ │
│  │   1. [HIGH] What are your specific travel dates in June?         │ │
│  │   2. [MEDIUM] Any preference for beach vs. activities?           │ │
│  │   3. [LOW] Any dietary restrictions for food planning?           │ │
│  │                                                                   │ │
│  │   [View Full Analysis]                                           │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  → TRIGGERED: Followup questions sent to customer                     │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 YESTERDAY — 2:30 PM                                                │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 📧 INQUIRY RECEIVED                                              │ │
│  │                                                                   │ │
│  │   Source: WhatsApp (+91 98765 43210)                            │ │
│  │   Customer: John Doe                                             │ │
│  │                                                                   │ │
│  │   "Hi, planning a honeymoon to Thailand in June.                │ │
│  │    2 people, around 2L budget. Looking for beaches              │ │
│  │    and nice stays. Any suggestions?"                            │ │
│  │                                                                   │ │
│  │   EXTRACTED DATA:                                                │ │
│  │   • Destination: Thailand (95% confidence)                       │ │
│  │   • Trip Type: Honeymoon (87% confidence)                        │ │
│  │   • Party Size: 2 (99% confidence)                               │ │
│  │   • Budget: ₹2L (92% confidence)                                 │ │
│  │   • Date Window: June (60% confidence) ⚠️                        │ │
│  │   • Preferences: Beach, nice stays (80% confidence)             │ │
│  │                                                                   │ │
│  │   [View Raw Message] [View Extraction Evidence]                 │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  → TRIGGERED: Trip created • Initial analysis run                     │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Mock Scenario 2: Complex Decision Path

### Timeline Showing Decision Reversal

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRIP: Europe Family | Smith Family | ID: EUR-2024-045                │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 Apr 18 — 4:30 PM                                                    │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ ✅ STATUS: Needs Attention (Reverted)                            │ │
│  │                                                                   │ │
│  │   PREVIOUS: Ready to Book (Apr 17)                               │ │
│  │   REVERTED BY: Owner (Priya)                                     │ │
│  │                                                                   │ │
│  │   "Customer just informed they want to add Venice.               │ │
│  │    This changes the budget significantly. Needs review."         │ │
│  │                                                                   │ │
│  │   [View Reversion Details]                                       │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 Apr 17 — 2:00 PM                                                    │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ ✅ STATUS: Ready to Book (Owner Approved)                       │ │
│  │                                                                   │ │
│  │   Quote: Switzerland + Paris (₹4.2L)                             │ │
│  │   Approved by: Priya (Owner)                                    │ │
│  │                                                                   │ │
│  │   "Budget is tight but customer is high-value.                  │ │
│  │    Proceed with premium option."                                 │ │
│  │                                                                   │ │
│  │   [View Approval Notes]                                          │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
│  🕐 Apr 16 — 11:00 AM                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ ⚠️  STATUS: Owner Review Required                                │ │
│  │                                                                   │ │
│  │   FLAG: Budget over customer stated amount (₹4.2L vs ₹3.5L)      │ │
│  │   RISK: High-value customer, needs owner approval               │ │
│  │                                                                   │ │
│  │   AI Recommendation: "Discuss budget increase with               │ │
│  │                      customer before proceeding"                  │ │
│  │                                                                   │ │
│  │   [View Risk Analysis]                                           │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Event Types & Visual Design

### Event Type Badges

| Type | Icon | Color | Example |
|------|------|-------|----------|
| **Inquiry Received** | 📧 | Blue | Customer WhatsApp/email |
| **AI Analysis** | 🤖 | Purple | Extraction, scenarios, decision |
| **Status Changed** | ✅ | Green | Ready to Book, Needs Attention |
| **Conversation** | 💬 | Orange | Agent ↔ Customer messages |
| **Field Updated** | ✏️ | Gray | Manual field edits |
| **Owner Review** | 👁️ | Red | Approval, rejection, reversion |
| **System Event** | ⚙️ | Gray | Auto-assignments, SLA alerts |

### Timeline Item Structure

```
┌─────────────────────────────────────────────────────────────┐
│ 🕐 [RELATIVE TIME] — [ABSOLUTE TIME]                       │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ [ICON] [EVENT TYPE] — [SUBTITLE]                     │  │
│ │                                                       │  │
│ │ Summary text (1-2 lines)                             │  │
│ │                                                       │  │
│ │ [Action Button 1] [Action Button 2]                  │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                          │
│ → [TRIGGERED EFFECTS] (if any)                          │
└─────────────────────────────────────────────────────────────┘
```

### Expanded Details

```
┌─────────────────────────────────────────────────────────────┐
│ [Event summary collapsed...]                               │
│ [▼] Expanded Details                                        │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ FULL CONTEXT:                                          │  │
│ │ • Actor: Rahul (Agent)                                 │  │
│ │ • Timestamp: April 20, 3:20:35 PM                     │  │
│ │ • Related Events: [3] linked events                   │  │
│ │                                                       │  │
│ │ FULL DATA:                                             │  │
│ │ [Raw JSON / Full content]                             │  │
│ │                                                       │  │
│ │ EVIDENCE:                                              │  │
│ │ • Source: WhatsApp API                                │  │
│ │ • Message ID: wa_abc123xyz                            │  │
│ │ • Screenshot: [View]                                   │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Data Model

### TripEvent
```typescript
interface TripEvent {
  id: string;
  tripId: string;
  timestamp: string;

  // Event classification
  eventType: EventType;
  category: EventCategory;
  source: EventSource;

  // Actor
  actorId: string;
  actorName: string;
  actorType: 'customer' | 'agent' | 'owner' | 'ai' | 'system';

  // Content
  title: string;
  summary: string;
  fullData?: Record<string, unknown>;

  // Relationships
  parentEventId?: string;      // For follow-ups
  relatedEventIds?: string[];  // Related events
  triggeredEffects?: string[];  // IDs of events this triggered

  // Visibility
  isInternalOnly: boolean;     // Don't show to customers
  isHighlighted: boolean;      // Important event

  // UI state
  isExpanded: boolean;
  viewCount: number;
}

type EventType =
  | 'inquiry_received'
  | 'analysis_extraction'
  | 'analysis_scenarios'
  | 'analysis_decision'
  | 'status_changed'
  | 'conversation_message'
  | 'field_updated'
  | 'owner_review'
  | 'owner_approval'
  | 'owner_rejection'
  | 'owner_reversion'
  | 'system_alert'
  | 'system_auto_assign';

type EventCategory = 'origin' | 'analysis' | 'decision' | 'conversation' | 'review' | 'system';

type EventSource = 'whatsapp' | 'email' | 'phone' | 'web' | 'ai_pipeline' | 'manual';
```

### Event Grouping
```typescript
interface EventGroup {
  id: string;
  tripId: string;
  groupId: string;           // Events grouped together
  groupTitle: string;        // "AI Analysis Cycle", "Conversation Thread"
  startTime: string;
  endTime: string;
  eventIds: string[];
  summary: string;
}
```

---

## 8. Filtering & Search

### Filter Options
```
┌─────────────────────────────────────────────────────────────┐
│  Filter Timeline                              [Clear All]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Event Types:                                               │
│  ☑ Inquiries  ☑ AI Analysis  ☑ Decisions                  │
│  ☑ Conversations  ☑ Reviews  ☐ System                      │
│                                                             │
│  Actors:                                                    │
│  ☑ Customer  ☑ Agents  ☑ Owner  ☑ AI  ☐ System            │
│                                                             │
│  Time Range:                                                │
│  ○ All time  ● Last 7 days  ○ Custom                       │
│                                                             │
│  Search: [___________________]                              │
│                                                             │
│            [Apply] [Reset]                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Implementation Phases

### Phase 1: Data Layer
- TripEvents table
- Event creation API
- Mock data generator (critical for demo)

### Phase 2: Timeline Panel
- Timeline component
- Event type renderers
- Expand/collapse
- Basic filtering

### Phase 3: Integration
- Wire to spine pipeline events
- Connect WhatsApp/email sources
- Real-time event streaming

### Phase 4: Advanced Features
- Event grouping
- Related events visualization
- Export timeline
- Search across timelines

---

## 10. Mock Data Generator

To enable demos without real data:

```typescript
// Mock scenario generator
interface MockScenario {
  name: string;
  description: string;
  events: Partial<TripEvent>[];
}

const MOCK_SCENARIOS: MockScenario[] = [
  {
    name: 'Thailand Honeymoon',
    description: 'Standard inquiry → analysis → quote → ready flow',
    events: [/* 15 events spanning 2 days */],
  },
  {
    name: 'Europe Budget Crisis',
    description: 'Quote → owner review → budget rework → approval',
    events: [/* 25 events with reversals */],
  },
  {
    name: 'Multi-Agent Handoff',
    description: 'Agent A handles → leaves → Agent B takes over',
    events: [/* Shows handoff events */],
  },
  {
    name: 'Emergency Cancellation',
    description: 'Customer cancels → refund process → rebooking',
    events: [/* Crisis handling flow */],
  },
];
```

---

## 11. Success Criteria

- [ ] Timeline shows complete trip story from inquiry to current state
- [ ] Events are visually distinct by type
- [ ] Expandable details show full context
- [ ] Related events are linked
- [ ] Mock scenarios demonstrate various decision paths
- [ ] Timeline works for agent handoffs
- [ ] Owner can review decision rationale
- [ ] New agents can understand trip context quickly

---

## 12. Open Questions

1. **Event persistence** — New table or augment existing trip structure?
2. **Conversation sources** — How to integrate WhatsApp/email history?
3. **Mock data priority** — Should we build mock generator first?
4. **Performance** — Timeline for trips with months of history?
5. **Privacy** — What's internal-only vs customer-shareable?

---

**Ready for implementation with mock scenarios.**
