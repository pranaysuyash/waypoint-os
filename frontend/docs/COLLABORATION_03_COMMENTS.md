# Real-Time Collaboration — Comments & Communication

> Research document for in-context comments, threaded discussions, and collaborative decision-making.

---

## Key Questions

1. **How do agents communicate in-context while building a trip?**
2. **What's the comment model — inline, panel-based, or hybrid?**
3. **How do comments resolve and transition to actions?**
4. **How do we handle @mentions and notifications for comments?**
5. **What's the relationship between comments and the trip timeline?**

---

## Research Areas

### Comment Model

```typescript
interface TripComment {
  commentId: string;
  tripId: string;
  parentCommentId?: string;         // For threaded replies
  author: string;
  authorRole: 'agent' | 'admin' | 'owner' | 'system';
  content: string;
  contentType: 'text' | 'markdown' | 'rich';
  location: CommentLocation;
  mentions: Mention[];
  reactions: Reaction[];
  status: CommentStatus;
  resolution?: CommentResolution;
  createdAt: Date;
  updatedAt: Date;
}

type CommentStatus =
  | 'active'
  | 'resolved'
  | 'dismissed'
  | 'pinned';

interface CommentLocation {
  type: CommentLocationType;
  target: string;
  field?: string;
  range?: { start: number; end: number };
}

type CommentLocationType =
  | 'trip_overview'          // General trip comment
  | 'itinerary_day'          // Comment on specific day
  | 'itinerary_activity'     // Comment on specific activity/hotel/flight
  | 'pricing_section'        // Comment on pricing
  | 'pricing_item'           // Comment on specific pricing line item
  | 'traveler_info'          // Comment on traveler details
  | 'document'               // Comment on a generated document
  | 'field';                 // Inline comment on a specific field

// Comment examples:
// "Is the Taj Palace available for these dates? @AgentB can you check?"
// "This hotel is over budget. Suggest downgrade to 3-star."
// "Customer confirmed they want the early morning flight. Updating."
// "Visa processing may take longer for this nationality. Flag to owner."
```

### Threaded Discussions

```typescript
interface CommentThread {
  threadId: string;
  tripId: string;
  location: CommentLocation;
  title?: string;
  participants: string[];
  comments: TripComment[];
  status: ThreadStatus;
  priority: ThreadPriority;
  assignedTo?: string;
  createdAt: Date;
  resolvedAt?: Date;
  resolvedBy?: string;
}

type ThreadStatus =
  | 'open'
  | 'in_discussion'
  | 'awaiting_response'
  | 'resolved'
  | 'archived';

type ThreadPriority =
  | 'normal'
  | 'high'                  // Needs response within 4 hours
  | 'urgent';               // Blocking trip progress

// Thread to action flow:
// 1. Agent opens thread by commenting on a field
// 2. Other agents respond with suggestions
// 3. Thread assigned to decision-maker
// 4. Decision made → Thread resolved
// 5. Action taken based on resolution
// 6. Resolution logged in trip timeline

// Example: Pricing discussion thread
// Agent A: "Hotel rate seems high. Can we negotiate?"
// Agent B: "I checked, this is the corporate rate. No lower available."
// Agent A: "What about the competitor hotel 2 blocks away?"
// Agent B: "Available at ₹8,500 vs ₹12,000. Suggest switching."
// Agent A: "Agreed. Making the change." → Thread resolved → Price updated
```

### Mentions & Notifications

```typescript
interface Mention {
  mentionedAgent: string;
  mentionType: 'direct' | 'team' | 'role' | 'all';
  notifiedAt?: Date;
  readAt?: Date;
}

// Mention patterns:
// @AgentB → Direct mention, notify immediately
// @pricing-team → Team mention, notify all team members
// @owner → Role mention, notify trip owner
// @all → All participants (use sparingly)

// Notification rules for comments:
// Direct mention → Immediate push notification
// Thread participant → In-app notification within 5 minutes
// Thread in your section → In-app notification within 15 minutes
// Thread you're not involved in → Daily digest only
// Resolved thread → In-app notification only (no push)

// Comment notification integration:
// 1. In-app: Badge count on Comments panel
// 2. Push: Mobile push for direct mentions and urgent threads
// 3. Email: Daily digest of unresolved threads
// 4. Slack: Thread posted to channel if integrated
```

### Decision Logging

```typescript
interface CollaborativeDecision {
  decisionId: string;
  tripId: string;
  decisionType: DecisionType;
  description: string;
  context: string;                   // What was the situation
  options: DecisionOption[];
  selectedOption: string;
  decidedBy: string;
  participants: string[];
  discussionThread: string;          // Link to comment thread
  decidedAt: Date;
}

type DecisionType =
  | 'supplier_selection'             // Chose hotel/airline/transport
  | 'pricing_strategy'               // Margin, discount, upsell
  | 'itinerary_change'               // Added/removed/modified activity
  | 'customer_preference'            // Customer chose X over Y
  | 'risk_acceptance'                // Accepted a flagged risk
  | 'escalation_resolution'          // Resolved an owner escalation
  | 'policy_override';               // Overrode a business policy

interface DecisionOption {
  optionId: string;
  label: string;
  description: string;
  pros: string[];
  cons: string[];
  estimatedCost?: number;
  estimatedImpact?: string;
  votes?: Record<string, boolean>;   // Who voted for this option
}

// Decision logging purpose:
// 1. Audit trail: Why was this hotel chosen over that one?
// 2. Training: New agents learn from past decisions
// 3. Quality: Review decisions for improvement
// 4. Dispute resolution: Customer asks "why this hotel?" — we have the answer
```

---

## Open Problems

1. **Comment clutter** — Active trips may accumulate dozens of threads. Need filtering, sorting, and archival to keep the comment panel useful.

2. **Cross-trip comments** — An agent may want to reference a decision from a previous trip. Need cross-trip linking or a knowledge base of past decisions.

3. **Customer-facing visibility** — Should customers see any of the internal discussion? Probably not raw comments, but a sanitized "decision summary" could build trust.

4. **Comment-to-action gap** — Discussions happen but actions aren't always taken. Need "convert comment to task" functionality.

5. **Historical context** — A comment from 2 weeks ago references "the hotel" but the hotel has since changed. Need comment anchoring to preserve context.

---

## Next Steps

- [ ] Design comment component with inline and panel views
- [ ] Build threaded discussion model with resolution workflow
- [ ] Create mention and notification integration for comments
- [ ] Design decision logging for key trip choices
- [ ] Study in-context comment UX (Figma, Notion, Google Docs)
