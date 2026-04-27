# Trip Builder 04: Collaboration

> Multi-person trip planning, approval workflows, and shared decision-making

---

## Document Overview

**Focus:** How multiple people collaborate on trip planning
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Sharing & Access
- Who can share a trip with whom?
- What are the different permission levels?
- How do we handle external (non-customer) participants?
- What happens when a trip is shared vs. transferred?

### 2. Approval Workflows
- What trips require approval? (Corporate? Budget thresholds?)
- Who are the approvers? (Manager? Finance? Travel admin?)
- What is the approval flow? (Sequential? Parallel?)
- How are rejections handled?
- Can approval be delegated?

### 3. Real-time Collaboration
- Do multiple people edit simultaneously?
- How do we handle conflicting changes?
- What is the broadcast mechanism? (WebSockets? Polling?)
- What UI shows "who is viewing"?

### 4. Communication
- Is there in-app chat/comments?
- How are notifications delivered?
- What gets logged to the timeline?
- Can customers @mention agents?

---

## Research Areas

### A. Permission Model

**Known Patterns:**
| Role | Capabilities |
|------|-------------|
| Owner | Full control, can delete, can share |
| Editor | Can modify components, cannot delete trip |
| Viewer | Read-only, can comment |
| Approver | Can approve/reject, limited edits |

**Open Questions:**
- Are permissions trip-level or component-level?
- Can permissions be time-bounded?
- How do we handle "guest" access (no account)?

### B. Approval State Machine

**States to Research:**
```
DRAFT → PENDING_APPROVAL → APPROVED → can book
                ↓              ↓
            REJECTED      (return to DRAFT)
```

**Questions:**
- Can a trip be partially approved? (Some components yes, some no?)
- What happens to pricing during approval wait?
- How long is approval valid?
- Can approvals be revoked?

### C. Conflict Resolution

**Approaches to Explore:**

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| Last write wins | Simple, but data loss possible | Low-collaboration scenarios |
| Optimistic locking | Detect conflicts, prompt user | Medium collaboration |
| Operational transforms | Merge changes algorithmically | High collaboration (complex) |
| Component-level locks | Lock specific components | Granular collaboration |

**Research Needed:**
- What is our expected conflict frequency?
- What UX for conflict resolution?
- Performance implications of each approach?

### D. Notification Strategy

**Events That May Need Notifications:**
- Trip shared with you
- Approval requested
- Approval approved/rejected
- Component added/modified
- Price change (significant)
- Comment/@mention
- Trip booked

**Open Questions:**
- Immediate vs. batched notifications?
- Per-trip notification preferences?
- Escalation rules for urgent changes?

---

## Integration Points

| System | Integration Question |
|--------|---------------------|
| **Timeline** | Do collaboration events appear in trip timeline? |
| **Communication Hub** | Reuse messaging infrastructure? |
| **User Accounts** | How are collaborators identified? |
| **Customer Portal** | What collaboration features exist there? |
| **Decision Engine** | How does approval affect workflow state? |

---

## Trade-offs to Explore

### 1. Real-time vs. Refresh
| Aspect | Real-time (WebSockets) | Poll-based |
|--------|----------------------|------------|
| Infrastructure | More complex | Simpler |
| UX | Instant updates | Delayed |
| Scalability | Connection overhead | Request overhead |
| Reliability | Stateful | Stateless |

**Research:** Which pattern matches our expected usage?

### 2. Granular Permissions vs. Simple Roles
| Aspect | Granular | Simple Roles |
|--------|----------|--------------|
| Flexibility | High | Low |
| Complexity | High | Low |
| UX burden | Confusing | Clear |
| Implementation | Complex | Simple |

**Research:** What are real-world permission scenarios?

### 3. In-app Communication vs. External
| Aspect | In-app | External (email/WhatsApp) |
|--------|--------|--------------------------|
| Context | Rich (linked to trip) | Lost (separate thread) |
| Reach | Logged-in users only | Everyone |
| Sync | Single source | Multiple threads |
| Preference | Agent-facing | Customer-facing |

**Research:** How do customers prefer to communicate?

---

## Open Problems

### 1. External Approver Access
Corporate trips often require approval from people who don't have customer accounts.

**Options to Explore:**
- Magic link for one-time access
- Email-based approval (click link in email)
- Allow approvers without full accounts
- Require account creation (friction)

### 2. Version History for Collaboration
When multiple people edit, how do we:
- Show who changed what and when?
- Roll back to previous versions?
- Compare versions?
- Resolve merge conflicts?

### 3. Multi-Currency Approval
When approver and traveler see different currencies:
- Which currency is approved against?
- How do FX changes affect approved budgets?
- What happens when budget exceeds due to FX?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface TripCollaboration {
  tripId: string;
  owner: string;  // userId
  collaborators: Collaborator[];
  approval?: ApprovalWorkflow;
  sharing: SharingSettings;
}

interface Collaborator {
  userId: string;
  role: 'owner' | 'editor' | 'viewer' | 'approver';
  addedAt: Date;
  addedBy: string;
  permissions: Permission[];
}

interface ApprovalWorkflow {
  status: 'not_required' | 'pending' | 'approved' | 'rejected';
  approvers: Approver[];
  requestedAt?: Date;
  decidedAt?: Date;
  decisionComments?: string;
}

interface Approver {
  userId?: string;  // empty if external
  email: string;    // always present
  status: 'pending' | 'approved' | 'rejected';
  respondedAt?: Date;
}
```

---

## Competitor Research Needed

| Product | Collaboration Features | Notable Patterns |
|---------|----------------------|------------------|
| **Expedia TAAP** | ? | ? |
| **TravelPerk** | ? | ? |
| **TripActions** | ? | ? |
| **Concur** | ? | ? |
| **Airbnb Groups** | ? | ? |

---

## Experiments to Run

1. **Permission complexity interview:** Ask 5 agents what permission scenarios they encounter
2. **Approval flow mapping:** Document 3 real corporate approval processes
3. **Conflict frequency:** Instrument current system to see concurrent edit rate
4. **Notification preference survey:** Ask customers how they want to be notified

---

## References

- [Booking Engine - State Machine](./BOOKING_ENGINE_08_STATE_MACHINE.md) — State patterns
- [Timeline Feature - Events](./TIMELINE_11_EVENT_TAXONOMY_COMPLETE.md) — Event types
- [Communication Hub](./COMM_HUB_01_TECHNICAL_DEEP_DIVE.md) — Messaging patterns

---

## Next Steps

1. Interview agents about collaboration scenarios
2. Map corporate approval workflows
3. Research competitor approaches
4. Prototype permission model
5. Design conflict resolution UX

---

**Status:** Research Phase — Questions identified, exploration needed

**Last Updated:** 2026-04-27
