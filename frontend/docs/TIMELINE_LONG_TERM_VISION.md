# Timeline: Long-Term Vision

> "What's the timeline thing and how would it help, what details we can capture, showcase, full long term thinking"

---

## Part 1: What Is Timeline?

### The Problem

**Current State:**
```
Inbox Card → Click → Workspace
                      ↓
              [Current State Only]

You see:
- Trip fields (destination, budget, dates)
- Decision status (Ready to Book, Needs Attention)
- Output bundles (internal/traveler)

You DON'T see:
- How did we get here?
- What did the customer originally ask?
- What did the AI analyze and why?
- What conversations happened?
- What changed and why?
```

**The Gap:**
The workspace shows the **result** but not the **story**. For an agent taking over a trip, or an owner reviewing a decision, this is critical missing context.

### The Solution: Timeline

**Timeline = Complete story of a trip, chronologically**

Think of it like:
- **GitHub commit history** — but for trips (who changed what, when, why)
- **Medical record** — every consultation, decision, treatment
- **Case file** — every piece of evidence, analysis, ruling

```
┌─────────────────────────────────────────────────────────────────────┐
│  TRIP STORY                                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🕐 Apr 23 — Ready to Book                                         │
│     "All questions answered, budget confirmed"                     │
│                                                                     │
│  🕐 Apr 22 — Customer added Phi Phi request                        │
│     "Added to itinerary, AI re-ran scenarios"                      │
│                                                                     │
│  🕐 Apr 21 — AI evaluated 3 scenarios, selected Phuket+Krabi       │
│     "Scenario A: Best balance of beach + budget"                   │
│                                                                     │
│  🕐 Apr 20 — Original inquiry received on WhatsApp                 │
│     "Honeymoon to Thailand, June, 2 people, ₹2L budget"            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: How Does Timeline Help?

### Use Case 1: Agent Handoff (The "11 PM Panic")

**Scenario:** Agent Rahul is handling a trip. He falls sick or goes on leave. Agent Priya needs to take over.

**Without Timeline:**
```
Priya: "What's the status of this Thailand trip?"
[Opens workspace, sees current state]
Priya: "Okay, it says Ready to Book. But why? What did customer ask?
        Did we promise anything specific? Are there any risks?"
[Goes through inbox, WhatsApp, notes manually]
```

**With Timeline:**
```
Priya: Opens Timeline panel
→ Sees: "Original inquiry: Honeymoon, June, ₹2L"
→ Sees: "Customer added Phi Phi on Apr 22"
→ Sees: "AI selected Phuket+Krabi for best balance"
→ Sees: "Budget tight but confirmed, no blockers"
→ Priya: "Got it. I can handle the customer now."
```

**Time saved:** 15 minutes of digging → 2 minutes of reading

---

### Use Case 2: Owner Review (The "Quote Disaster")

**Scenario:** Owner sees a trip marked "Needs Attention" with high budget. Wants to understand why.

**Without Timeline:**
```
Owner: "Why is this ₹5L when customer said ₹3L?"
[Opens Decision panel, sees blockers]
Owner: "But how did we get here? Did agent make a mistake?
        Did customer change requirements?"
```

**With Timeline:**
```
Owner: Opens Timeline panel
→ Sees: "Original inquiry: ₹3L budget"
→ Sees: "Customer added Venice on Apr 18 (budget impact +₹1.5L)"
→ Sees: "Agent Rahul escalated to owner"
→ Sees: "Owner (Priya) approved on Apr 19"
→ Sees: "Customer confirmed new budget on Apr 20"
→ Owner: "Ah, customer wanted Venice. Agent did the right thing.
         Budget is justified."
```

**Reassurance:** Owner sees the complete chain, feels confident

---

### Use Case 3: Learning & Patterns (The "How Do We Handle X?")

**Scenario:** New agent asks "How do we usually handle Thailand honeymoons?"

**Without Timeline:**
```
Senior agent: "Uh, let me think... we usually suggest Phuket...
               check budget... ask about dates..."
[Incomplete knowledge, based on memory]
```

**With Timeline:**
```
Senior agent: Filters Timeline → Destination: Thailand, Type: Honeymoon
→ Shows 15 past trips with timelines
→ Pattern: "80% chose Phuket+Krabi"
→ Pattern: "₹2L budget usually fits"
→ Pattern: "June is best weather window"
→ Pattern: "Common blocker: Visa expiry dates"
→ Senior agent: "Here's how we handle it. Look at these 3 examples."
```

**Knowledge transfer:** Captured tribal knowledge

---

### Use Case 4: Customer Context (The "What Did I Promise?")

**Scenario:** Customer calls "What did you say about Phi Phi again?"

**Without Timeline:**
```
Agent: [Scrolling through WhatsApp] "Uh, let me find the message...
                                    I think I said it was included..."
```

**With Timeline:**
```
Agent: Opens Timeline → Filters: Conversation
→ Sees: "Apr 22: Agent said Phi Phi included in package"
→ Sees: "Apr 22: Customer asked about ferry travel"
→ Sees: "Apr 22: Agent explained ferry + monsoon caution"
→ Agent: "I included Phi Phi and warned about ferry travel in June.
         Here's exactly what I said."
```

**Accuracy:** Exact quote, no misremembering

---

### Use Case 5: Dispute Resolution (The "You Promised!")

**Scenario:** Customer claims "You promised 5-star hotels!"

**Without Timeline:**
```
Agent: "No I didn't..."
Customer: "Yes you did!"
[Ambiguous, he-said-she-said]
```

**With Timeline:**
```
Agent: Opens Timeline → Export conversation thread
→ Shows: "Apr 20: Customer asked for 'nice stays'"
→ Shows: "Apr 21: Agent quoted 4-star resorts (explicitly stated)"
→ Shows: "Apr 22: Customer confirmed quote"
→ Agent: "Here's the full transcript. I quoted 4-star resorts
         and you confirmed. Happy to upgrade to 5-star
         — here's the price difference."
```

**Protection:** Audit trail protects agent and agency

---

## Part 3: What Details Can We Capture?

### Event Categories

| Category | Events | Data Captured |
|----------|--------|---------------|
| **Origin** | Inquiry received | Raw message, channel, timestamp, customer info, extracted data |
| **Analysis** | AI extraction, scenario evaluation, decision | Confidence scores, rationale, scenarios considered, evidence |
| **Decision** | Status changes, approvals, rejections | From/to state, reason, actor, triggers |
| **Conversation** | Messages (inbound/outbound) | Full message, actor, channel, related events |
| **Action** | Field edits, manual updates | Field, old value, new value, actor, reason |
| **Review** | Owner/manager reviews | Reviewer, decision, notes, overrides |
| **System** | Auto-assignments, SLA alerts, reminders | Trigger, context, action taken |

### Complete Event Data Model

```typescript
interface TripEvent {
  // Identity
  id: string;
  tripId: string;
  workspaceId: string;

  // When
  timestamp: string;
  timezone: string;

  // What
  eventType: EventType;
  category: EventCategory;
  title: string;
  summary: string;

  // Who
  actor: {
    id: string;
    name: string;
    type: 'customer' | 'agent' | 'owner' | 'ai' | 'system';
    avatar?: string;
  };

  // Where (for conversations)
  source: {
    channel: 'whatsapp' | 'email' | 'phone' | 'web' | 'api';
    messageId?: string;
    threadId?: string;
  };

  // Content (varies by event type)
  content: {
    // For inquiries
    rawMessage?: string;
    extractedData?: Record<string, unknown>;

    // For AI analysis
    analysisType?: 'extraction' | 'scenarios' | 'decision';
    confidence?: number;
    rationale?: string;
    scenarios?: Scenario[];
    evidence?: Evidence[];

    // For decisions
    fromState?: string;
    toState?: string;
    reason?: string;
    triggers?: string[];

    // For conversations
    message?: string;
    direction?: 'inbound' | 'outbound';

    // For actions
    field?: string;
    oldValue?: unknown;
    newValue?: unknown;
  };

  // Relationships
  parentEventId?: string;      // This event responds to
  relatedEventIds?: string[];  // Related context
  triggeredEvents?: string[];  // Events this caused

  // Metadata
  isInternalOnly: boolean;     // Don't show customer
  isHighlighted: boolean;      // Important event
  tags?: string[];             // For filtering/grouping

  // Audit
  ipAddress?: string;
  userAgent?: string;

  // Attachments
  attachments?: Attachment[];

  // AI-generated (future)
  aiSummary?: string;          // AI-generated summary
  aiSentiment?: 'positive' | 'neutral' | 'negative';
  aiUrgency?: 'low' | 'medium' | 'high';
}
```

### What Each Event Type Captures

#### 1. Inquiry Received
```typescript
{
  eventType: 'inquiry_received',
  content: {
    rawMessage: "Hi, planning honeymoon to Thailand...",
    channel: 'whatsapp',
    extractedData: {
      destination: 'Thailand',
      tripType: 'honeymoon',
      budget: 200000,
      partySize: 2,
      dateWindow: 'June'
    },
    confidence: {
      destination: 0.95,
      budget: 0.92,
      dates: 0.60  // Low confidence!
    }
  }
}
```

#### 2. AI Analysis: Scenarios
```typescript
{
  eventType: 'analysis_scenarios',
  content: {
    scenarios: [
      {
        id: 's1',
        name: 'Phuket + Krabi',
        budget: { low: 180000, high: 220000 },
        fit: 'excellent',
        pros: ['Best beaches', 'Good weather', 'Direct flights'],
        cons: ['Can be crowded', 'Touristy'],
        selected: true
      },
      {
        id: 's2',
        name: 'Bangkok + Pattaya',
        budget: { low: 150000, high: 190000 },
        fit: 'good',
        pros: ['Budget-friendly', 'More activities'],
        cons: ['Less romantic', 'Busy city'],
        selected: false
      }
    ],
    rationale: 'Selected Scenario A for best balance of romance and budget',
    evidence: [
      { type: 'search_result', source: 'internal_db', relevance: 0.9 },
      { type: 'pricing', source: 'supplier_api', relevance: 0.95 }
    ]
  }
}
```

#### 3. Decision Changed
```typescript
{
  eventType: 'decision_changed',
  actor: { type: 'ai', name: 'Decision Engine' },
  content: {
    fromState: 'ASK_FOLLOWUP',
    toState: 'PROCEED_INTERNAL_DRAFT',
    reason: 'Customer provided missing dates (June 15-25)',
    confidence: 0.87,
    triggers: [
      'field_updated: dates',
      'analysis_re_run'
    ]
  }
}
```

#### 4. Conversation Message
```typescript
{
  eventType: 'conversation_message',
  actor: { type: 'customer', name: 'John Doe' },
  source: { channel: 'whatsapp', messageId: 'wa_abc123' },
  content: {
    direction: 'inbound',
    message: "Can you also include Phi Phi islands?",
    timestamp: '2026-04-22T15:20:00Z',
    attachments: []
  },
  triggeredEvents: ['evt_field_update_phi_phi', 'evt_analysis_re_run']
}
```

#### 5. Owner Review
```typescript
{
  eventType: 'owner_review',
  actor: { type: 'owner', name: 'Priya' },
  content: {
    decision: 'approved',
    reason: 'High-value customer, budget justified',
    notes: 'Confirm they want premium hotels',
    overrides: [
      'risk_flag: budget_over_customer_stated'
    ]
  }
}
```

---

## Part 4: What Can We Showcase?

### Visual Presentation Levels

#### Level 1: Compact (Dashboard View)
```
┌─────────────────────────────────────────────────────────────┐
│  Thailand Honeymoon  •  Last: 2 hours ago  •  12 events     │
│                                                                     │
│  🕐 2h ago  ✅ Ready to Book                                   │
│  🕐 1d ago  💬 Customer added Phi Phi                         │
│  🕐 2d ago  🤖 AI: Selected Phuket+Krabi                      │
│  🕐 3d ago  📧 Inquiry received                              │
│                                                                     │
│  [View Full Timeline →]                                        │
└─────────────────────────────────────────────────────────────┘
```

#### Level 2: Summary (Panel View)
```
┌─────────────────────────────────────────────────────────────┐
│  Timeline                                               [▼] │
├─────────────────────────────────────────────────────────────┤
│                                                                     │
│  🕐 TODAY — 9:00 AM                                            │
│  ✅ Ready to Book (87% confidence)                            │
│                                                                     │
│  🕐 YESTERDAY — 3:20 PM                                        │
│  💬 Agent → Customer: "Phi Phi is great..."                   │
│                                                                     │
│  🕐 YESTERDAY — 2:35 PM                                        │
│  🤖 AI: Evaluated 3 scenarios, selected A                     │
│                                                                     │
│  🕐 YESTERDAY — 2:30 PM                                        │
│  📧 Inquiry: "Honeymoon to Thailand..."                        │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

#### Level 3: Detailed (Expanded Event)
```
┌─────────────────────────────────────────────────────────────┐
│  🕐 YESTERDAY — 2:35 PM                              [▲]    │
│  🤖 AI ANALYSIS: Scenarios Evaluated                       │
├─────────────────────────────────────────────────────────────┤
│                                                                     │
│  Evaluated 3 scenarios for honeymoon + ₹2L budget:        │
│                                                                     │
│  ✅ Scenario A: Phuket + Krabi (₹1.8L - ₹2.2L)              │
│     • Best balance of beach + budget                         │
│     • Good weather in June                                    │
│     • Direct flights available                               │
│     [View Full Details]                                      │
│                                                                     │
│  ✅ Scenario B: Bangkok + Pattaya (₹1.5L - ₹1.9L)          │
│     • More budget-friendly                                    │
│     • Less romantic                                          │
│     [View Full Details]                                      │
│                                                                     │
│  ⚠️  Scenario C: Samui + Phangan (₹2.1L - ₹2.6L)           │
│     • Over budget                                             │
│     • Ferry travel issues in monsoon                         │
│     [View Full Details]                                      │
│                                                                     │
│  🏆 SELECTED: Scenario A                                       │
│                                                                     │
│  Rationale:                                                     │
│  "Scenario A offers the best balance of romantic beaches    │
│   and budget fit. June is optimal weather for Andaman       │
│   coast. Customer preference for 'nice stays' aligns        │
│   with 4-star resorts in Phuket."                            │
│                                                                     │
│  Confidence: 87%                                                │
│  Evidence: 12 sources (internal DB, pricing API)              │
│                                                                     │
│  [View Evidence] [Compare Scenarios] [Export]                 │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

#### Level 4: Raw (Technical View)
```json
{
  "id": "evt_abc123",
  "eventType": "analysis_scenarios",
  "timestamp": "2026-04-22T14:35:00Z",
  "actor": { "type": "ai", "name": "Decision Engine" },
  "content": { ... }
}
```

---

## Part 5: Long-Term Vision

### Phase 1: Foundation (Now)
**Goal:** Capture and display basic timeline

**Build:**
- TripEvents table
- Basic event creation (inquiry, decision, status change)
- Timeline panel with chronological display
- Mock scenarios for demo

**Value:** Agents see trip history, basic handoff enabled

---

### Phase 2: Integration (Next Quarter)
**Goal:** Connect to real data sources

**Build:**
- WhatsApp integration (auto-capture messages)
- Email integration
- Spine pipeline event streaming
- Field edit tracking (enhanced ChangeHistoryPanel)

**Value:** Timeline auto-populates, no manual entry

---

### Phase 3: Intelligence (6 Months)
**Goal:** AI-enhanced timeline

**Build:**
- AI-generated summaries ("Customer changed budget 3 times, final: ₹2.5L")
- Sentiment analysis (customer frustration, urgency detection)
- Anomaly detection ("Unusual number of status reversals")
- Smart grouping ("All conversations about hotels")

**Value:** Faster understanding, pattern recognition

---

### Phase 4: Cross-Trip Insights (1 Year)
**Goal:** Learn across trips

**Build:**
- Pattern detection ("90% of Thailand honeymoons choose Phuket")
- Timeline comparison ("This trip is similar to these 3")
- Predictive suggestions ("Based on pattern, suggest asking about visas")
- Knowledge base extraction ("Common questions about Thailand")

**Value:** Organizational learning, smarter decisions

---

### Phase 5: Real-Time Collaboration (18 Months)
**Goal:** Live timeline for team coordination

**Build:**
- Real-time event streaming (WebSocket)
- Collaborative notes on events
- @mentions in timeline
- Timeline comments/discussion

**Value:** Team coordination, collective intelligence

---

### Phase 6: Customer-Facing Timeline (2 Years)
**Goal:** Share trip story with customers

**Build:**
- Customer-safe timeline filter
- Trip tracker (customer view)
- Milestone notifications
- Trip memory ("Your trip 2 years ago")

**Value:** Transparency, customer engagement

---

## Part 6: Advanced Features (Future)

### Timeline Search
```
Search: "Thailand honeymoon budget change"
→ Shows all budget-related events across all Thailand trips
```

### Timeline Compare
```
Compare: This trip vs. Similar trips
→ Shows: "This trip took 3 days longer than average for decision"
```

### Timeline Export
```
Export: Full timeline → PDF for customer
→ Professional trip dossier
```

### Timeline Templates
```
Template: "Honeymoon Workflow"
→ Auto-generates checklist based on past successful trips
```

### Timeline Analytics
```
Analytics: "Where do trips get stuck?"
→ Timeline shows: "Most trips stall at 'Options' stage for 48 hours"
```

---

## Part 7: Data Retention & Privacy

### Retention Policy
| Event Type | Retention | Rationale |
|------------|-----------|-----------|
| Inquiries | 7 years | Legal compliance |
| Conversations | 7 years | Legal compliance |
| AI Analysis | 2 years | Learning value decreases |
| System Events | 6 months | Low value after |
| Draft/Unsent | 30 days | Privacy |

### Privacy Controls
- **Internal-only flag:** Events never shown to customers
- **Redaction:** Sensitive data masked in exports
- **Access control:** Who can see what (role-based)
- **Right to forget:** Customer data deletion

---

## Part 8: Success Metrics

### Adoption
- % of trips with timeline data
- % of agents using timeline for handoffs
- Timeline views per trip

### Value
- Time saved on handoffs (target: 15 min → 2 min)
- Dispute resolution accuracy
- Owner review satisfaction

### Quality
- Event completeness (% of events captured)
- Timeline accuracy (no missing events)
- Search relevance

---

## Summary

**Timeline is the trip's story.** It captures every decision, conversation, and analysis from first inquiry to final booking.

**Immediate value:** Agent handoffs, owner reviews, accuracy

**Long-term value:** Organizational learning, pattern recognition, customer transparency

**Implementation:** Start simple (capture → display), iterate toward intelligence

---

**Status:** Vision complete. Ready for Phase 1 implementation planning.
