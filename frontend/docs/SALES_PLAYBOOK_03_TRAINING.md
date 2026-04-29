# Agency Sales Playbook — Agent Training & Performance

> Research document for agent skill development, sales coaching, performance metrics, leaderboard systems, and continuous improvement for travel agency sales teams.

---

## Key Questions

1. **How do we measure agent sales performance?**
2. **What training and coaching systems improve conversion?**
3. **How do leaderboards motivate without demoralizing?**
4. **What does the agent performance analytics view look like?**

---

## Research Areas

### Agent Performance Metrics

```typescript
interface AgentPerformance {
  agent_id: string;
  period: string;

  // Activity metrics
  activity: {
    inquiries_received: number;
    proposals_sent: number;
    follow_ups_done: number;
    calls_made: number;
    whatsapp_messages_sent: number;
    avg_response_time_minutes: number;
  };

  // Conversion metrics
  conversion: {
    inquiry_to_qualified: number;        // %
    qualified_to_proposal: number;
    proposal_to_negotiation: number;
    negotiation_to_booking: number;
    overall_conversion: number;
    avg_deal_cycle_days: number;
  };

  // Revenue metrics
  revenue: {
    total_revenue: number;
    avg_deal_size: number;
    total_margin: number;
    avg_margin_percentage: number;
    revenue_vs_target: number;           // % achievement
  };

  // Quality metrics
  quality: {
    customer_satisfaction_avg: number;    // 1-5
    review_score_avg: number;
    complaint_rate: number;
    repeat_customer_rate: number;
    referral_rate: number;
  };
}

// ── Agent performance dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Agent Performance — Priya Sharma                       │
// │  April 2026                                           │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │₹6.2L│ │ 42%  │ │4.6★  │ │12min│               │
// │  │Revenue│ │Conv. │ │CSAT  │ │Resp. │               │
// │  │62% tgt│ │Rate  │ │Score │ │Time  │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │                                                       │
// │  Monthly trend:                                       │
// │  Revenue:  ████████████░░░░░░░░ 62% of target        │
// │  Conversion: ████████████████████ 42% (good)         │
// │  CSAT:     ████████████████████ 4.6/5                │
// │  Response: ████████████████████ 12min (under 30 SLA) │
// │                                                       │
// │  Strengths:                                           │
// │  ✅ Fastest response time in team (12 min avg)        │
// │  ✅ Highest CSAT score (4.6 vs team avg 4.1)          │
// │  ✅ Strong repeat customer rate (28%)                  │
// │                                                       │
// │  Improvement areas:                                   │
// │  ⚠️ Revenue at 62% of target (need ₹3.8L more)        │
// │  ⚠️ Proposal-to-negotiation rate: 45% (team avg 55%)  │
// │  ⚠️ Deal cycle: 12 days (team avg 10)                 │
// │                                                       │
// │  Coaching suggestions:                                │
// │  → Review 3 lost deals from this month                │
// │  → Practice objection handling for PRICE objections    │
// │  → Try ALTERNATIVE_CLOSE technique more often          │
// │                                                       │
// │  [View Deals] [Coaching Plan] [Compare with Team]      │
// └─────────────────────────────────────────────────────┘
```

### Sales Coaching System

```typescript
interface CoachingSystem {
  // AI-powered coaching recommendations
  coaching_recommendations: {
    agent_id: string;
    focus_area: string;                   // "objection_handling", "closing", "follow_up"
    current_performance: number;
    target_performance: number;
    gap: number;

    // Specific coaching actions
    actions: {
      type: "REVIEW_LOST_DEAL" | "PRACTICE_OBJECTION" | "SHADOW_TOP_PERFORMER" | "WATCH_TRAINING" | "ROLE_PLAY";
      description: string;
      estimated_impact: number;
      effort: "LOW" | "MEDIUM" | "HIGH";
    }[];

    // Learning resources
    resources: {
      title: string;
      type: "VIDEO" | "SCRIPT" | "CASE_STUDY" | "TEMPLATE";
      duration_minutes: number;
    }[];
  };
}

// ── Coaching recommendations ──
// ┌─────────────────────────────────────────────────────┐
// │  Sales Coach — Weekly Recommendations                   │
// │  For: Priya Sharma · Week of Apr 28                    │
// │                                                       │
// │  Focus area: Closing technique                         │
// │  Current: 45% proposal-to-booking · Target: 55%       │
// │                                                       │
// │  Recommended actions (priority order):                 │
// │                                                       │
// │  1. 📋 Review 3 lost deals from April                  │
// │     Deals: WP-431, WP-437, WP-445                     │
// │     Loss reasons: Price (2), Competitor (1)            │
// │     Pattern: Losing at negotiation stage               │
// │     [Open Deals] [Start Review]                        │
// │                                                       │
// │  2. 🎭 Practice: "Cheaper elsewhere" objection         │
// │     Your response rate: 30% success                    │
// │     Team best: 65% success (Rahul)                     │
// │     Rahul's approach: Compare effective price first     │
// │     [Watch Rahul's Recording] [Practice Script]        │
// │                                                       │
// │  3. 📊 Learn: ASSUMPTIVE_CLOSE technique               │
// │     You use this: 0% of the time                       │
// │     Top performers use: 35% of closings                │
// │     When to use: Customer asks "what's next?"           │
// │     [Watch Training Video — 8 min]                     │
// │                                                       │
// │  4. 🤝 Shadow: Rahul's next proposal call              │
// │     Rahul has highest proposal-to-booking rate (58%)    │
// │     Next opportunity: Patel Dubai (tomorrow 3 PM)       │
// │     [Schedule Shadow Session]                          │
// │                                                       │
// │  Expected impact: +10% proposal-to-booking in 4 weeks  │
// └─────────────────────────────────────────────────────┘
```

### Team Leaderboard

```typescript
interface Leaderboard {
  period: "WEEKLY" | "MONTHLY" | "QUARTERLY";
  metric: "REVENUE" | "CONVERSION" | "CSAT" | "DEALS_CLOSED" | "MARGIN";

  rankings: {
    rank: number;
    agent_id: string;
    agent_name: string;
    value: number;
    trend: "UP" | "STABLE" | "DOWN";
    change_from_last_period: number;
  }[];

  // Team averages for context
  team_avg: number;
  team_target: number;
}

// ── Team leaderboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Leaderboard — April 2026                              │
// │  Metric: Revenue · Target: ₹10L/agent                 │
// │                                                       │
// │  🏆 Revenue                                           │
// │  1. Rahul M.    ₹11.2L  ↑ +₹1.8L  ████████████ 112% │
// │  2. Priya S.    ₹6.2L   ↑ +₹0.8L  ██████░░░░░░ 62%  │
// │  3. Amit K.     ₹5.8L   ↓ -₹0.3L  ██████░░░░░░ 58%  │
// │  4. Neha T.     ₹4.5L   ↑ +₹1.2L  █████░░░░░░░ 45%  │
// │  ── Team avg: ₹6.9L ── Team target: ₹40L ──          │
// │                                                       │
// │  🎯 Conversion Rate                                    │
// │  1. Rahul M.    52%  ↑ +4%     ████████████           │
// │  2. Priya S.    42%  ↑ +2%     ████████░░░░           │
// │  3. Neha T.     38%  ↑ +8%     ███████░░░░░           │
// │  4. Amit K.     35%  ↓ -3%     ███████░░░░░           │
// │  ── Team avg: 42% ──                                   │
// │                                                       │
// │  ⭐ Customer Satisfaction                              │
// │  1. Priya S.    4.6  ↑ +0.2    ████████████████       │
// │  2. Rahul M.    4.3  → same    ██████████████░        │
// │  3. Amit K.     4.1  ↑ +0.1    █████████████░░       │
// │  4. Neha T.     3.9  ↑ +0.3    ████████████░░░       │
// │  ── Team avg: 4.2 ──                                   │
// │                                                       │
// │  Design principles:                                   │
// │  • Show multiple metrics (not just revenue)           │
// │  • Always show team avg for context                   │
// │  • Show trend arrows (improvement matters)            │
// │  • Celebrate personal bests, not just #1              │
// │  • Monthly reset (don't penalize slow starters)       │
// │                                                       │
// │  [My Performance] [Team Report] [Settings]             │
// └─────────────────────────────────────────────────────┘
```

### Continuous Improvement Loop

```typescript
interface ContinuousImprovement {
  // Win/loss analysis drives playbooks
  analysis: {
    // Auto-analyze lost deals
    lost_deal_analysis: {
      pattern: string;                    // "Price objection at negotiation stage"
      frequency: number;
      affected_agents: string[];
      suggested_playbook_update: string;
    }[];

    // Best practices from top performers
    top_performer_patterns: {
      agent_id: string;
      technique: string;
      success_rate: number;
      shareable: boolean;
    }[];
  };

  // Playbook evolution
  playbook_updates: {
    update_type: "NEW_OBJECTION" | "NEW_TECHNIQUE" | "UPDATED_TEMPLATE" | "MARKET_SHIFT";
    description: string;
    data_source: string;
    approved_by: string | null;
    effective_date: string;
  };
}

// ── Continuous improvement feed ──
// ┌─────────────────────────────────────────────────────┐
// │  Sales Improvement Feed — This Week                     │
// │                                                       │
// │  📊 Pattern detected:                                  │
// │  "Customers asking about visa processing time           │
// │   increased 3x this month — add visa timeline           │
// │   to all Singapore proposals automatically"              │
// │  [Apply to Templates] [Dismiss]                         │
// │                                                       │
// │  🏆 Rahul's winning pattern:                           │
// │  "Sending a comparison sheet with MakeMyTrip             │
// │   effective price within 1 hour of inquiry               │
// │   increased his conversion by 15%"                       │
// │  [Add to Playbook] [Share with Team]                     │
// │                                                       │
// │  ⚠️ Market shift detected:                             │
// │  "Singapore hotel rates up 15% for June.                 │
// │   Update all June Singapore proposals with                │
// │   rate change notice."                                   │
// │  [Update All Proposals] [Send Alert to Customers]        │
// │                                                       │
// │  📝 New objection recorded:                             │
// │  "Is GST included?" — 4 times this week                 │
// │  Add to FAQ and proposal templates                      │
// │  [Add Response] [Auto-Include in Proposals]              │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Attribution fairness** — Revenue leaderboard can be unfair if some agents get more walk-in leads or premium segment customers. Need normalized metrics (conversion rate, margin %, CSAT) alongside raw revenue.

2. **Coaching without surveillance** — Call recording and analysis improves coaching but may feel like surveillance. Need opt-in framing focused on growth, not monitoring.

3. **Leaderboard demotivation** — Consistently bottom-ranked agents may disengage. Need personal improvement tracking (beat your own score) alongside team rankings.

4. **Playbook update velocity** — Playbooks can become stale quickly. Need a lightweight update process that doesn't require manager approval for minor template tweaks.

---

## Next Steps

- [ ] Build agent performance dashboard with multi-metric view
- [ ] Create AI-powered coaching recommendation engine
- [ ] Implement team leaderboard with normalized metrics
- [ ] Design continuous improvement loop with pattern detection
