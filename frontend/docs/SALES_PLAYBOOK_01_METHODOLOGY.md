# Agency Sales Playbook — Sales Methodology & Deal Stages

> Research document for travel agency sales methodologies, deal stage management, the agent sales workflow, and India-specific sales patterns for the Waypoint OS platform.

---

## Key Questions

1. **What sales methodology fits Indian travel agencies?**
2. **How do deal stages map to the existing trip lifecycle?**
3. **What does the agent sales workflow look like end-to-end?**
4. **How do we track sales pipeline and conversion?**

---

## Research Areas

### Travel Agency Sales Methodology

```typescript
interface SalesMethodology {
  name: "CONSULTATIVE_TRAVEL";
  description: "Diagnose → Prescribe → Deliver → Nurture";

  // 4-phase approach tailored for Indian travel agencies
  phases: {
    DISCOVER: {
      goal: "Understand traveler needs, constraints, and preferences";
      duration_target: "First conversation (15-30 min)";
      key_actions: [
        "Ask open-ended questions about trip purpose",
        "Identify traveler segment (family, couple, corporate, group)",
        "Understand budget range and flexibility",
        "Check travel history and preferences",
        "Identify decision-making timeline",
      ];
      tools: ["Customer CRM profile", "Previous trip history", "WhatsApp conversation context"];
      exit_criteria: "Budget range + destination interest + travel dates confirmed";
    };

    DESIGN: {
      goal: "Create a tailored trip proposal that matches needs";
      duration_target: "24-48 hours";
      key_actions: [
        "Research best options within budget",
        "Design 2-3 package variants (good/better/best)",
        "Check rate intelligence for pricing",
        "Prepare visual itinerary presentation",
        "Anticipate objections and prepare responses",
      ];
      tools: ["Workbench", "Rate Intelligence", "Supplier Database", "Package Templates"];
      exit_criteria: "Proposal sent to customer";
    };

    DECIDE: {
      goal: "Guide customer to booking decision";
      duration_target: "3-7 days from proposal";
      key_actions: [
        "Follow up on proposal within 24 hours",
        "Address questions and objections",
        "Offer alternatives if needed",
        "Create urgency (limited availability, rate changes)",
        "Negotiate if required (within margin guardrails)",
      ];
      tools: ["Objection Handler", "Rate Alerts", "Margin Calculator", "WhatsApp Templates"];
      exit_criteria: "Customer confirms booking OR provides clear rejection reason";
    };

    DELIVER_NURTURE: {
      goal: "Execute trip flawlessly and build relationship for future";
      duration_target: "Pre-trip + trip + 12 months post-trip";
      key_actions: [
        "Confirm all bookings and share itinerary",
        "Monitor trip in real-time (Trip Control Room)",
        "Post-trip follow-up and review collection",
        "Nurture for next trip (CLV strategy)",
        "Referral request when timing is right",
      ];
      tools: ["Trip Workspace", "Timeline", "CLV Engine", "Memory Products", "WhatsApp"];
      exit_criteria: "Customer returns from trip satisfied + next touchpoint scheduled";
    };
  };
}

// ── Sales methodology overview ──
// ┌─────────────────────────────────────────────────────┐
// │  Waypoint OS Sales Methodology                         │
// │  CONSULTATIVE TRAVEL: Diagnose → Prescribe → Deliver   │
// │                                                       │
// │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐│
// │  │ DISCOVER  │→│  DESIGN  │→│  DECIDE  │→│NURTURE││
// │  │ 15-30min  │  │ 24-48hr  │  │  3-7d   │  │ 12mo  ││
// │  │           │  │          │  │          │  │       ││
// │  │ • Needs   │  │ • Research│  │ • Follow │  │• Trip ││
// │  │ • Budget  │  │ • Package │  │ • Handle │  │• Post ││
// │  │ • Segment │  │ • Price   │  │ • Close  │  │• CLV  ││
// │  │ • Timeline│  │ • Present │  │ • Negot. │  │• Refer││
// │  └──────────┘  └──────────┘  └──────────┘  └───────┘│
// │                                                       │
// │  Conversion targets:                                  │
// │  Discover → Design: 80% (some inquiries are tire-kickers)│
// │  Design → Decide: 65% (proposal quality matters)     │
// │  Decide → Booked: 60% (closing skill matters)        │
// │  Overall: ~31% inquiry-to-booking conversion          │
// └─────────────────────────────────────────────────────┘
```

### Deal Stages & Pipeline

```typescript
interface DealPipeline {
  // Deal stages mapped to existing trip lifecycle
  stages: {
    NEW_INQUIRY: {
      description: "Customer first contact via WhatsApp/call/walk-in";
      trip_status: "INQUIRY";
      auto_actions: ["Create CRM entry", "Assign to available agent", "Send welcome message"];
      exit_triggers: ["Agent responds", "Customer provides trip details"];
      sla: "Respond within 30 minutes during business hours";
    };

    QUALIFIED: {
      description: "Budget, dates, and destination confirmed";
      trip_status: "DRAFT";
      auto_actions: ["Create draft in workbench", "Pull customer history", "Check rate intelligence"];
      exit_triggers: ["Agent starts designing proposal"];
      qualification_criteria: [
        "Budget stated (even approximate)",
        "Travel dates (even flexible)",
        "Destination interest (region or specific)",
        "Traveler count",
      ];
    };

    PROPOSAL_SENT: {
      description: "Trip package proposal sent to customer";
      trip_status: "PROPOSED";
      auto_actions: ["Start follow-up timer", "Monitor rate changes for quoted prices"];
      exit_triggers: ["Customer responds to proposal"];
      required_artifacts: ["Itinerary PDF", "Price breakdown", "Inclusions/exclusions"];
    };

    NEGOTIATING: {
      description: "Customer interested but wants changes";
      trip_status: "REVISED";
      auto_actions: ["Track revision count", "Monitor margin erosion"];
      exit_triggers: ["Customer accepts", "Customer declines", "Stale 7+ days"];
      margin_guardrails: {
        min_margin_percentage: 10;
        approval_required_below: 12;
        auto_reject_below: 8;
      };
    };

    COMMITTED: {
      description: "Customer verbally confirmed, awaiting payment";
      trip_status: "CONFIRMED";
      auto_actions: ["Send payment link", "Start supplier booking timer", "Hold inventory"];
      exit_triggers: ["Payment received", "Customer backs out"];
      payment_sla: "Collect advance within 48 hours";
    };

    BOOKED: {
      description: "Payment received, all bookings confirmed";
      trip_status: "BOOKED";
      auto_actions: ["Generate booking confirmations", "Share itinerary", "Set pre-trip reminders"];
      exit_triggers: ["Trip starts"];
    };

    TRAVELING: {
      description: "Customer is on the trip";
      trip_status: "IN_PROGRESS";
      auto_actions: ["Monitor trip", "Daily check-in messages", "Handle real-time issues"];
    };

    COMPLETED: {
      description: "Trip completed successfully";
      trip_status: "COMPLETED";
      auto_actions: ["Send review request", "Generate memory products", "Schedule follow-up", "Update CLV"];
    };

    LOST: {
      description: "Deal lost at any stage";
      trip_status: "LOST";
      auto_actions: ["Record loss reason", "Update CRM", "Schedule win-back touchpoint"];
      required_fields: ["loss_reason", "lost_to_competitor"];
    };
  };
}

// ── Sales pipeline view ──
// ┌─────────────────────────────────────────────────────┐
// │  Sales Pipeline — April 2026                           │
// │                                                       │
// │  NEW      QUALIFIED   PROPOSAL   NEGOTIAT  COMMITTED  │
// │  ┌───┐    ┌───┐      ┌───┐     ┌───┐     ┌───┐     │
// │  │ 5 │    │ 8 │      │ 6 │     │ 4 │     │ 3 │     │
// │  │₹9L│    │₹16L│     │₹12L│    │₹8L│     │₹6L│     │
// │  └─┬─┘    └─┬─┘      └─┬─┘     └─┬─┘     └─┬─┘     │
// │    │80%     │65%       │60%      │85%      │90%      │
// │    ↓        ↓          ↓         ↓         ↓         │
// │  ─────────────────────────────────────────────────    │
// │                                                       │
// │  Pipeline value: ₹51L                                 │
// │  Weighted pipeline: ₹31.2L                            │
// │  Target this month: ₹40L                              │
// │  Gap: ₹8.8L (need 3-4 more qualified leads)          │
// │                                                       │
// │  Stage velocity:                                      │
// │  New → Qualified: 1.2 days avg                        │
// │  Qualified → Proposal: 2.1 days avg                   │
// │  Proposal → Negotiation: 1.8 days avg                 │
// │  Negotiation → Committed: 3.5 days avg                │
// │  Committed → Booked: 1.5 days avg                     │
// │  Total cycle: 10.1 days avg                           │
// │                                                       │
// │  [Add Deal] [View Forecast] [Agent Leaderboard]       │
// └─────────────────────────────────────────────────────┘
```

### Agent Sales Workflow

```typescript
interface AgentSalesWorkflow {
  // Daily sales routine
  daily_routine: {
    morning: {
      time: "9:00 AM";
      actions: [
        "Review overnight WhatsApp messages (auto-categorized by AI)",
        "Check rate alerts for active proposals",
        "Review pipeline: which deals need follow-up today?",
        "Check trip departures: any issues with today's trips?",
      ];
    };

    active_selling: {
      time: "9:30 AM - 6:00 PM";
      actions: [
        "Respond to new inquiries within 30 min SLA",
        "Design proposals for qualified leads",
        "Follow up on proposals sent yesterday",
        "Handle objections for negotiating deals",
        "Process bookings for committed deals",
      ];
    };

    evening: {
      time: "6:00 PM";
      actions: [
        "Send follow-up WhatsApp messages for pending deals",
        "Update deal stages in CRM",
        "Flag stuck deals for manager review",
        "Review tomorrow's trip departures",
      ];
    };
  };

  // Per-deal workflow
  deal_workflow: {
    step: number;
    action: string;
    tool: string;
    duration_target: string;
    automated: boolean;
  }[];
}

// ── Agent daily sales dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Good morning, Priya! · 5 deals need attention         │
// │                                                       │
// │  🔴 Urgent (2):                                      │
// │  • Gupta family — committed, payment due TODAY         │
// │    [Send Payment Reminder] [Call Customer]             │
// │  • Singapore DMC rate change affects 2 proposals       │
// │    [Review Impact] [Update Proposals]                  │
// │                                                       │
// │  🟡 Follow-up (3):                                   │
// │  • Sharma proposal sent 2 days ago — no response       │
// │    [WhatsApp Follow-up] [Call]                         │
// │  • Patel Dubai inquiry — qualified, proposal due today │
// │    [Open Workbench] [Design Proposal]                  │
// │  • Mehta negotiation — margin at 11%, need approval    │
// │    [Review Margin] [Approve] [Push Back]               │
// │                                                       │
// │  📊 Your pipeline: 12 deals · ₹24L weighted           │
// │  Monthly target: ₹10L · Achieved: ₹6.2L (62%)        │
// │                                                       │
// │  [Start Working] [View All Deals] [Pipeline Report]    │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Inquiry source attribution** — Customers often inquire via WhatsApp after seeing a social post, but don't mention it. Attribution is fuzzy across WhatsApp, walk-ins, referrals, and social media.

2. **SLA enforcement** — 30-minute response SLA is aspirational for small agencies. Need graduated SLAs based on inquiry source and customer segment.

3. **Pipeline vs. reality** — Agents may not update deal stages in real-time. Auto-stage progression (proposal sent = PROPOSAL_SENT) reduces manual burden but needs reliable triggers.

4. **Margin guardrails in negotiation** — Agents may override margin warnings to close deals. Need approval workflows, not just alerts, for below-threshold deals.

---

## Next Steps

- [ ] Design sales pipeline with auto-stage progression
- [ ] Build agent daily sales dashboard with prioritized actions
- [ ] Create margin guardrail system with approval workflows
- [ ] Implement pipeline forecasting with weighted deal values
