# Real-Time Collaboration — Workflow & Handoffs

> Research document for trip handoffs, shift transitions, and collaborative workflow patterns.

---

## Key Questions

1. **How do agents hand off trips at end of shift?**
2. **What's the workflow for specialist escalation (visa, MICE, pricing)?**
3. **How do we track who's responsible for a trip at any given time?**
4. **What collaborative patterns exist beyond co-editing?**
5. **How do we measure collaboration effectiveness?**

---

## Research Areas

### Trip Ownership & Handoff

```typescript
interface TripOwnership {
  tripId: string;
  primaryAgent: string;
  secondaryAgent?: string;
  specialists: SpecialistAssignment[];
  ownerHistory: OwnershipEntry[];
  currentStatus: OwnershipStatus;
}

interface SpecialistAssignment {
  specialistId: string;
  specialty: SpecialistType;
  assignedAt: Date;
  assignedBy: string;
  reason: string;
  status: 'pending_acceptance' | 'active' | 'completed' | 'handed_back';
}

type SpecialistType =
  | 'visa_expert'
  | 'mice_planner'
  | 'pricing_specialist'
  | 'flight_expert'
  | 'corporate_travel'
  | 'luxury_travel'
  | 'group_travel'
  | 'insurance_advisor';

type OwnershipStatus =
  | 'with_primary'           // Primary agent handling
  | 'with_specialist'        // Specialist working on it
  | 'awaiting_owner_review'  // Specialist done, owner reviewing
  | 'in_handoff'             // Being transferred between agents
  | 'unassigned';            // No agent (needs triage)

interface OwnershipEntry {
  from: string;
  to: string;
  timestamp: Date;
  reason: string;
  handoffNotes: string;
  pendingItems: string[];
}

// Handoff scenarios:
// 1. End of shift: Agent A → Agent B (all trips)
// 2. Specialist: Agent A → Visa Expert → Agent A (after processing)
// 3. Escalation: Agent A → Senior Agent → Agent A (after review)
// 4. Customer request: Agent A → Agent B (customer asked for specific agent)
// 5. Workload rebalance: Agent A → Agent C (A is overloaded)
```

### Shift Transition

```typescript
interface ShiftHandoff {
  handoffId: string;
  fromAgent: string;
  toAgent: string;
  timestamp: Date;
  tripSummaries: TripHandoffSummary[];
  urgentItems: UrgentItem[];
  pendingActions: PendingAction[];
  customerCallbacks: CustomerCallback[];
  notes: string;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
}

interface TripHandoffSummary {
  tripId: string;
  tripName: string;
  stage: string;
  customerName: string;
  customerMood: 'happy' | 'neutral' | 'frustrated' | 'anxious';
  nextSteps: string[];
  blockers: string[];
  pendingDecisions: string[];
  lastActivity: Date;
  urgency: 'low' | 'medium' | 'high' | 'critical';
}

interface UrgentItem {
  tripId: string;
  description: string;
  deadline: Date;
  actionRequired: string;
  customerWaiting: boolean;
}

interface CustomerCallback {
  tripId: string;
  customerName: string;
  scheduledTime: Date;
  topic: string;
  context: string;
  preferredChannel: 'phone' | 'whatsapp' | 'email';
}

// Shift handoff workflow:
// 1. 30 min before shift end: System prompts for handoff prep
// 2. Agent reviews all trips, flags urgent items
// 3. System auto-generates trip summaries from activity log
// 4. Agent adds notes and context
// 5. Handoff package sent to incoming agent
// 6. Incoming agent acknowledges receipt
// 7. Trip ownership transferred
// 8. Customer notified if needed ("Your agent for the evening is Agent B")
```

### Collaborative Patterns

```typescript
interface CollaborationPattern {
  patternType: CollabPatternType;
  description: string;
  participants: string[];
  trigger: string;
  workflow: PatternStep[];
}

type CollabPatternType =
  | 'pair_booking'                   // Two agents on one complex booking
  | 'specialist_consult'             // Quick question to specialist
  | 'review_and_approve'             // Junior agent + senior review
  | 'divide_and_conquer'             // Split trip sections across agents
  | 'customer_facing_tag_team'       // Agent + specialist on customer call
  | 'knowledge_sharing';             // Experienced agent guides new agent

// Pattern: Divide and Conquer
// Trip: Complex international trip with flights, hotels, activities, visa
// Agent A: Handles flights + hotels
// Agent B: Handles activities + ground transport
// Agent C: Handles visa + insurance
// All work in parallel on the same trip, sections locked per agent

// Pattern: Specialist Consult
// Agent A is building a trip and needs visa advice
// Pings Visa Specialist: "Quick question: Nepal visa for Indian citizens?"
// Specialist responds inline (no ownership transfer)
// Agent A continues with the answer

// Pattern: Review and Approve
// Junior agent completes a ₹5L+ itinerary
// Submits for senior review
// Senior agent reviews, comments, approves or requests changes
// Junior agent addresses feedback
// Trip moves to customer delivery
```

### Collaboration Metrics

```typescript
interface CollaborationMetrics {
  // Handoff effectiveness
  averageHandoffTime: number;        // Time to complete handoff
  handoffErrorRate: number;          // Errors after handoff (missed info)
  customerDisruptionRate: number;    // Customers affected by handoff

  // Specialist utilization
  specialistUtilization: Record<SpecialistType, number>;
  averageConsultTime: number;
  consultToBookingRate: number;

  // Collaboration quality
  tripsRequiringCollaboration: number;
  averageCollaboratorsPerTrip: number;
  decisionTurnaroundTime: number;    // Time from question to decision

  // Agent satisfaction
  collaborationSatisfactionScore: number;
  handoffSatisfactionScore: number;
  toolUsabilityScore: number;
}

// Success criteria:
// Handoff error rate < 5% (minimal missed context)
// Customer disruption rate < 2% (seamless transitions)
// Specialist response time < 15 minutes (for consults)
// Collaboration satisfaction > 4/5 (agents find tools helpful)
```

---

## Open Problems

1. **Handoff quality** — The outgoing agent's mental model is hard to transfer. Even with detailed notes, context is lost. Need activity-based summaries, not manual notes.

2. **Specialist availability** — Visa experts are busy. When 5 agents need visa consults simultaneously, there's a bottleneck. Need queue management and async consult options.

3. **Ownership ambiguity** — When a specialist is working on a trip, who's responsible for the customer? Need clear RACI matrix per trip.

4. **Collaboration overhead** — If collaboration adds friction (too many tools, too many steps), agents will work around it. Need to measure and reduce overhead.

5. **Remote vs. in-office** — In-office agents can shout across the room. Remote agents need all communication through the platform. Need parity between work modes.

---

## Next Steps

- [ ] Design shift handoff workflow with auto-generated summaries
- [ ] Build specialist queue and consultation system
- [ ] Create trip ownership tracking with RACI model
- [ ] Design collaboration analytics dashboard
- [ ] Study handoff best practices (healthcare shift changes, air traffic control)
