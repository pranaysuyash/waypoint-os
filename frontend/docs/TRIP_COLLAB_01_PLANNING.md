# Customer Trip Planning Collaboration — Group Planning & Coordination

> Research document for multi-stakeholder trip planning, collaborative itinerary building, group decision-making, and cost splitting for travel agencies.

---

## Key Questions

1. **How do multiple travelers collaborate on planning a trip?**
2. **What group decision-making tools reduce back-and-forth?**
3. **How does cost splitting work for group trips?**
4. **What's the agent's role in collaborative planning?**

---

## Research Areas

### Collaborative Trip Planning

```typescript
interface CollaborativeTripPlanning {
  // Multi-stakeholder planning workflows
  planning_models: {
    FAMILY_TRIP: {
      stakeholders: "2-3 decision makers + 2-4 participants";
      dynamics: "Parents decide budget and dates; kids influence activities; grandparents need comfort";
      planning_pattern: "Agent proposes → parents discuss → agent adjusts → finalize";
      pain_points: [
        "Different activity preferences (kids want adventure, grandparents want rest)",
        "Budget disagreement (one parent wants luxury, other wants value)",
        "Dietary requirements (vegetarian, Jain, allergies)",
        "Pace of travel (young want packed itinerary, elderly need rest days)",
      ];
      resolution: "Agent proposes balanced itinerary with optional activities per interest group";
    };

    FRIENDS_GROUP: {
      stakeholders: "4-8 friends, often equal decision makers";
      dynamics: "Consensus-driven, budget-sensitive, activity-focused";
      planning_pattern: "Group chat → someone volunteers to coordinate → agent engagement";
      pain_points: [
        "Different budget levels (some can afford luxury, others want budget)",
        "Commitment timing (some confirm instantly, others delay)",
        "Activity preferences (party vs. culture vs. adventure)",
        "Dietary and comfort requirements vary widely",
      ];
      resolution: "Tiered package options + activity add-ons + flexible payment schedules";
    };

    CORPORATE_TEAM: {
      stakeholders: "HR/manager decides budget + dates; team inputs preferences";
      dynamics: "Top-down budget with bottom-up preferences";
      planning_pattern: "HR briefs agent → agent proposes 2-3 options → team votes → finalize";
      pain_points: [
        "Budget ceiling is fixed but expectations vary",
        "Mixed ages and fitness levels in team",
        "Some team members have dietary restrictions",
        "Manager wants team bonding, team wants relaxation",
      ];
      resolution: "Structured options with team vote + guaranteed budget compliance";
    };

    MULTI_FAMILY: {
      stakeholders: "2-3 families (8-15 people), each with their own decision maker";
      dynamics: "Each family has different preferences and budget comfort";
      planning_pattern: "One family initiates → invites others → agent mediates preferences";
      pain_points: [
        "Room allocation (which family gets the better room?)",
        "Activity selection (can't please 3 families simultaneously)",
        "Payment timing (some families pay early, others late)",
        "Kids of different ages have different needs",
      ];
      resolution: "Modular itinerary with family-choice activity blocks + separate invoicing";
    };
  };
}

// ── Collaborative planning workspace ──
// ┌─────────────────────────────────────────────────────┐
// │  Trip Planning — Sharma Family Goa Trip                    │
// │  Status: Planning · 8 travelers · Mar 15-20, 2026         │
// │                                                       │
// │  Planning Board:                                      │
// │                                                       │
// │  🏨 Accommodation — DECIDED ✅                            │
// │     Taj Holiday Village · 4 rooms · ₹12K/night           │
// │     Agreed by: Mom, Dad, Uncle, Aunt                      │
// │                                                       │
// │  🚗 Transport — IN VOTE 🗳️                               │
// │     Option A: Fly + rental car · ₹4.2L total              │
// │       👍 Dad, Mom (2)  👎 Uncle (1)                       │
// │     Option B: Train + self-drive · ₹2.8L total            │
// │       👍 Uncle, Aunt (2)  👎 Dad (1)                       │
// │     [Add Option] [Decide]                                  │
// │                                                       │
// │  🎯 Activities — SUGGESTING 💬                            │
// │     ✅ Beach day (everyone agreed)                         │
// │     ✅ Spice plantation tour (5 interested)                │
// │     🔵 Dolphin spotting (4 interested, 2 maybe)           │
// │     🟡 Casino night (3 interested, 2 not for kids)        │
// │     [Add Activity] [Vote] [Schedule]                       │
// │                                                       │
// │  💰 Budget — ₹3.5L total                                 │
// │     So far committed: ₹2.8L (accommodation + base)        │
// │     Remaining for activities/food: ₹70K                   │
// │                                                       │
// │  Participants:                                        │
// │  👤 Dad (organizer) · 👤 Mom · 👤 Uncle · 👤 Aunt         │
// │  👤 Rahul (teen) · 👤 Priya (teen) · 👤 Grandma · 👤 Grandpa│
// │                                                       │
// │  [Invite People] [Agent Chat] [Share Proposal]             │
// └─────────────────────────────────────────────────────┘
```

### Group Decision-Making Tools

```typescript
interface GroupDecisionMaking {
  // Tools to reduce planning friction
  decision_tools: {
    VOTING: {
      description: "Structured voting on trip elements";
      formats: {
        thumbs_up_down: "Simple agree/disagree on an option";
        ranked_choice: "Rank 3 options in order of preference";
        budget_allocation: "Each person allocates ₹X budget to preferred activities";
      };
      rules: "Majority wins, with veto power for budget/health/safety concerns";
      auto_close: "Vote auto-closes when all participants have voted or deadline passes";
    };

    PREFERENCE_SURVEY: {
      description: "Pre-planning survey to understand group preferences";
      questions: [
        "Budget comfort level: ₹30K / ₹50K / ₹75K / ₹1L+ per person",
        "Travel style: Relaxing / Balanced / Packed itinerary",
        "Must-have: Beach / Mountains / City / Adventure / Culture",
        "Dietary: Vegetarian / Non-veg / Jain / Allergies",
        "Pace: Slow (2 activities/day) / Medium (3-4) / Fast (5+)",
        "Priority: Luxury / Experience / Value",
      ];
      output: "Preference overlap map showing where group aligns and conflicts";
      timing: "Sent after group confirms interest, before agent proposes itinerary";
    };

    COMPROMISE_ENGINE: {
      description: "Suggest itineraries that maximize group satisfaction";
      mechanism: "Score each itinerary option against all participants' preferences";
      output: "Best-compromise itinerary with satisfaction scores per person";
      example: "80% satisfaction for all (better than 95% for half + 40% for rest)";
    };
  };
}
```

### Cost Splitting & Payment

```typescript
interface CostSplitting {
  // Group payment management
  splitting_models: {
    EQUAL_SPLIT: {
      description: "Total cost divided equally among all travelers";
      use_case: "Friends group where everyone pays same";
      handling: "System generates equal payment links for each person";
    };

    PER_FAMILY: {
      description: "Cost split by family unit, not individual";
      use_case: "Multi-family trip where each family pays their share";
      handling: "System generates one invoice per family with their room/activity allocation";
    };

    PER_ROOM: {
      description: "Accommodation by room, activities by person";
      use_case: "Mixed group where some share rooms and some don't";
      handling: "Accommodation cost to room occupants, activity cost split equally";
    };

    CUSTOM_SPLIT: {
      description: "Custom allocation set by organizer";
      use_case: "Parents paying for kids, one person subsidizing another";
      handling: "Organizer sets who pays what; system generates individual payment links";
    };

    TIERED: {
      description: "Different package tiers for different budget levels";
      use_case: "Friends group where some want luxury room, others budget";
      handling: "Base cost split equally, upgrade costs charged to individual";
    };
  };

  // Payment collection
  payment_collection: {
    INDIVIDUAL_LINKS: "Each person gets their own payment link with amount due";
    REMINDER_AUTOMATION: "Auto-reminders to unpaid participants via WhatsApp";
    PARTIAL_PAYMENT: "Allow partial payments with balance tracking per person";
    ORGANIZER_VISIBILITY: "Organizer sees who has paid and who hasn't";
    DEADLINE_ENFORCEMENT: "Trip booking only proceeds when minimum payments received";
    REFUND_HANDLING: "Individual refunds if trip cancelled (proportional to payment)";
  };
}

// ── Cost splitting dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Cost Split — Goa Trip · ₹3.5L total                      │
// │                                                       │
// │  Split method: Per Family (3 families)                │
// │                                                       │
// │  Sharma Family (4 people · 2 rooms):                 │
// │  Share: ₹1.45L · Paid: ₹1.2L · Pending: ₹25K ✅ on track│
// │  [Send Reminder]                                          │
// │                                                       │
// │  Gupta Family (2 people · 1 room):                   │
// │  Share: ₹85K · Paid: ₹85K · Done ✅                      │
// │                                                       │
// │  Patel Family (2 people · 1 room):                   │
// │  Share: ₹85K · Paid: ₹20K · Pending: ₹65K ⚠️ behind     │
// │  [Send Reminder] [Call] [Extend Deadline]                 │
// │                                                       │
// │  Overall: ₹2.25L of ₹3.15L collected (71%)               │
// │  Booking threshold: ₹2.5L (need ₹25K more)               │
// │                                                       │
// │  Activity costs (separate):                           │
// │  Spice plantation: ₹3,500 · Split: Per person (₹437 each) │
// │  Dolphin trip: ₹6,000 · Split: Interested only (₹750 each)│
// │  Casino: ₹5,000 · Split: Adults only (₹714 each)         │
// │                                                       │
// │  [Generate Payment Links] [Adjust Split] [Agent Help]      │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Decision paralysis** — Too many options and too many opinions can stall planning indefinitely. Need structured decision frameworks with deadlines to prevent endless deliberation.

2. **Social dynamics** — Who decides what is often determined by hierarchy (who's paying, who's oldest) rather than preference alignment. The system must handle this sensitively without being prescriptive.

3. **Payment defaults** — In group trips, someone always pays late or drops out after partial payment. Need clear cancellation and refund policies for partial group bookings.

4. **Agent workload** — Collaborative planning requires more agent touchpoints than individual bookings. Need self-service tools that reduce agent involvement to critical decision moments.

---

## Next Steps

- [ ] Build collaborative planning workspace with voting and preference tools
- [ ] Implement cost splitting engine with multiple split models
- [ ] Create group payment collection with individual tracking
- [ ] Design preference survey and compromise recommendation engine
