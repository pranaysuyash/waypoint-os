# Trip Control Room — Agent Operations Desk

> Research document for the agent operations desk interface, shift handoff protocols, trip issue queue management, and operational analytics for the control room team.

---

## Key Questions

1. **What does the agent operations desk interface look like?**
2. **How do shift handoffs work for 24/7 trip monitoring?**
3. **How is the issue queue prioritized and managed?**
4. **What operational analytics drive control room decisions?**

---

## Research Areas

### Agent Operations Desk

```typescript
interface OperationsDesk {
  // Per-agent operational view
  agent_view: {
    agent_id: string;
    shift: "MORNING" | "AFTERNOON" | "EVENING" | "NIGHT";

    // My active trips
    my_trips: {
      trip_id: string;
      destination: string;
      status: "ON_TRACK" | "MINOR_ISSUE" | "MAJOR_ISSUE";
      current_day: string;
      next_action: string | null;
      next_action_deadline: string | null;
    }[];

    // Issue queue
    issue_queue: {
      issue_id: string;
      trip_id: string;
      severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
      type: string;
      description: string;
      detected_at: string;
      assigned_to: string | null;
      sla_deadline: string;
      status: "NEW" | "IN_PROGRESS" | "ESCALATED" | "RESOLVED";
    }[];

    // Upcoming actions
    upcoming: {
      time: string;
      action: string;
      trip_id: string;
      auto_reminder: boolean;
    }[];
  };
}

// ── Agent operations desk ──
// ┌─────────────────────────────────────────────────────┐
// │  Operations Desk — Priya Sharma · Morning Shift         │
// │  9:00 AM - 6:00 PM · 8 active trips                    │
// │                                                       │
// │  ┌─ Immediate Actions (2) ────────────────────────┐  │
// │  │ 🔴 WP-455 Patel flight delay — send update      │  │
// │  │    SLA: 10 min remaining · [Handle Now]          │  │
// │  │                                                 │  │
// │  │ 🟡 WP-442 Sharma — respond to check-in          │  │
// │  │    SLA: 1h 45min remaining · [Respond]           │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  ┌─ My Active Trips (8) ──────────────────────────┐  │
// │  │ ✅ WP-448 Gupta · Dubai · Day 2/4 · On track    │  │
// │  │ ✅ WP-452 Singh · Thailand · Day 1/5 · On track │  │
// │  │ ✅ WP-456 Kumar · Kerala · Day 3/4 · On track   │  │
// │  │ ✅ WP-460 Reddy · Goa · Day 2/3 · On track      │  │
// │  │ ✅ WP-461 Shah · Bali · Pre-trip · On track      │  │
// │  │ 🟡 WP-442 Sharma · Singapore · Day 3/5 · Issue  │  │
// │  │ 🟡 WP-455 Patel · Dubai · Day 1/4 · Delay       │  │
// │  │ ✅ WP-458 Das · Singapore · Day 4/5 · On track   │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  ┌─ Upcoming Today ───────────────────────────────┐  │
// │  │ 10:00 AM · WP-448 Gupta · Desert safari confirm │  │
// │  │ 12:00 PM · WP-456 Kumar · Check-out reminder    │  │
// │  │  2:00 PM · WP-461 Shah · Final itinerary review │  │
// │  │  5:00 PM · WP-458 Das · Farewell dinner confirm │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  [Issue Queue (3)] [All Trips] [Shift Handoff Notes]    │
// └─────────────────────────────────────────────────────┘
```

### Shift Handoff Protocol

```typescript
interface ShiftHandoff {
  // Shift transition workflow
  handoff: {
    from_agent: string;
    to_agent: string;
    shift_change_time: string;

    // Context to transfer
    context: {
      // Active issues requiring attention
      open_issues: {
        issue_id: string;
        trip_id: string;
        summary: string;
        current_status: string;
        next_action: string;
        deadline: string;
        customer_mood: "HAPPY" | "NEUTRAL" | "FRUSTRATED" | "ANGRY";
      }[];

      // Trips with upcoming milestones
      upcoming_milestones: {
        trip_id: string;
        milestone: string;
        time: string;
        auto_handled: boolean;
        notes: string;
      }[];

      // General notes
      notes: string;

      // Pending follow-ups
      follow_ups: {
        trip_id: string;
        description: string;
        due_by: string;
      }[];
    };
  };
}

// ── Shift handoff ──
// ┌─────────────────────────────────────────────────────┐
// │  Shift Handoff — Priya → Rahul                           │
// │  Evening Shift · 6:00 PM · Apr 29, 2026                │
// │                                                       │
// │  Active issues to watch:                              │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🟡 WP-442 Sharma (Singapore, Day 3/5)          │   │
// │  │ Universal Studios was overcrowded — switched to │   │
// │  │ Night Safari. Traveler is okay but kids were    │   │
// │  │ disappointed. Mood: NEUTRAL.                    │   │
// │  │ Tomorrow: Gardens by the Bay + Orchid Garden    │   │
// │  │ No pending issues. Check-in at 8 PM SGT.        │   │
// │  │                                               │   │
// │  │ 🟡 WP-455 Patel (Dubai, Day 1/4)                │   │
// │  │ Flight delayed 2h, arrived 11:30 PM.            │   │
// │  │ Transfer completed, hotel checked in.           │   │
// │  │ Mood: TIRED but okay.                           │   │
// │  │ Tomorrow: Burj Khalifa 10 AM + Dubai Mall.     │   │
// │  │ Send morning briefing at 8 AM GST.              │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Upcoming milestones (tonight):                       │
// │  • 8 PM SGT: Sharma daily check-in (auto)             │
// │  • 10 PM SGT: Sharma Night Safari ends (confirm pickup)│
// │  • 8 AM GST tomorrow: Patel morning briefing           │
// │                                                       │
// │  Notes:                                               │
// │  • Patel family is vegetarian — all restaurants booked  │
// │  • Sharma has early flight Day 5 — wake-up call at 4 AM│
// │                                                       │
// │  [Accept Handoff] [Add Notes] [View Full Context]       │
// └─────────────────────────────────────────────────────┘
```

### Issue Queue Management

```typescript
interface IssueQueue {
  // Prioritized issue queue for operations team
  queue: {
    issues: {
      id: string;
      trip_id: string;
      destination: string;
      severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
      type: "FLIGHT" | "HOTEL" | "ACTIVITY" | "TRANSPORT" | "HEALTH" | "DOCUMENT" | "PAYMENT" | "WEATHER" | "OTHER";
      title: string;
      description: string;
      detected_at: string;
      assigned_to: string | null;
      sla_remaining_minutes: number;
      suggested_actions: string[];
    }[];

    // Queue statistics
    stats: {
      total_open: number;
      by_severity: Record<string, number>;
      avg_resolution_time_minutes: number;
      sla_breaches_today: number;
    };
  };
}

// ── Issue queue ──
// ┌─────────────────────────────────────────────────────┐
// │  Issue Queue — All Operations                            │
// │  Open: 5 · SLA breaches today: 0                        │
// │                                                       │
// │  Sort: [Severity ▼] [Time Detected] [Trip ID]          │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🔴 CRITICAL · WP-470 Mehta · Bangkok            │   │
// │  │ MEDICAL — Traveler reported chest pain           │   │
// │  │ Detected: 2 min ago · SLA: 3 min remaining      │   │
// │  │ Assigned: Unassigned ⚠️                          │   │
// │  │ Insurance: Star Health (helpline: 1800-XXX)     │   │
// │  │ Nearest hospital: Bumrungrad (3 km)              │   │
// │  │ [Assign to Me] [Call Traveler] [Connect Insurance]│  │
// │  │                                               │   │
// │  │ 🟠 HIGH · WP-455 Patel · Dubai                   │   │
// │  │ FLIGHT — Connecting flight may be missed          │   │
// │  │ Detected: 15 min ago · SLA: 5 min remaining      │   │
// │  │ Assigned: Rahul ✅                                │   │
// │  │ Status: IN_PROGRESS                              │   │
// │  │ [View Progress] [Assist]                          │   │
// │  │                                               │   │
// │  │ 🟡 MEDIUM · WP-442 Sharma · Singapore            │   │
// │  │ ACTIVITY — Crowded, skipped Universal Studios     │   │
// │  │ Detected: 1h ago · SLA: 30 min remaining          │   │
// │  │ Assigned: Priya ✅                                │   │
// │  │ Status: RESOLVING (switched to Night Safari)      │   │
// │  │ [View Progress]                                   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Assign to Me] [Auto-Distribute] [Escalate All]         │
// └─────────────────────────────────────────────────────┘
```

### Operational Analytics

```typescript
interface OpsAnalytics {
  // Control room performance metrics
  metrics: {
    // Response metrics
    avg_first_response_time_minutes: number;
    avg_resolution_time_minutes: number;
    sla_compliance_rate: number;
    escalation_rate: number;

    // Disruption patterns
    top_disruption_types: { type: string; count: number }[];
    top_affected_destinations: { destination: string; count: number }[];
    disruption_frequency_trend: "INCREASING" | "STABLE" | "DECREASING";

    // Agent performance
    agent_workload_balance: {
      agent: string;
      active_trips: number;
      open_issues: number;
      avg_response_time: number;
    }[];

    // Traveler satisfaction
    avg_satisfaction_during_disruption: number;
    satisfaction_recovery_rate: number;    // % who rated 4+ after disruption resolved
  };
}

// ── Operations analytics dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Operations Analytics — April 2026                      │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │ 8min │ │ 42min│ │ 94%  │ │ 12%  │               │
// │  │First │ │Resol.│ │SLA   │ │Escal.│               │
// │  │Resp. │ │Time  │ │Compl.│ │Rate  │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │                                                       │
// │  Top disruption types:                                │
// │  Flight delays:     ████████████████ 38%             │
// │  Hotel issues:      ██████ 15%                       │
// │  Activity problems: ████ 10%                         │
// │  Weather:           ███ 8%                           │
// │  Transport:         ██ 5%                            │
// │                                                       │
// │  Agent workload:                                      │
// │  Priya:  8 trips · 2 issues · 6 min response ✅      │
// │  Rahul:  6 trips · 1 issue · 9 min response ✅      │
// │  Amit:   7 trips · 3 issues · 14 min response ⚠️    │
// │                                                       │
// │  Recovery rate: 89% of disrupted trips ended          │
// │  with 4+ star satisfaction                            │
// │                                                       │
// │  [Export Report] [Trend Analysis] [Agent Leaderboard]  │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Workload imbalance** — Some agents handle more disruption-prone destinations. Need workload normalization based on destination risk, not just trip count.

2. **Night shift coverage** — Small agencies can't staff 24/7. Need on-call rotation with automated first response for common disruptions.

3. **Context loss at handoff** — Critical details can be lost between shifts. Structured handoff templates help but can't capture everything.

4. **Queue prioritization subjectivity** — What's "critical" to one traveler may be "medium" to another. Need standardized severity criteria.

---

## Next Steps

- [ ] Build agent operations desk with prioritized issue queue
- [ ] Create shift handoff protocol with structured context transfer
- [ ] Implement issue queue management with auto-assignment
- [ ] Design operational analytics dashboard for control room
