# Owner & Executive Command Center — Dashboard & KPIs

> Research document for the agency owner/executive dashboard, key performance indicators, financial overview, and strategic decision support for travel agency management.

---

## Key Questions

1. **What KPIs does an agency owner need at a glance?**
2. **How does the executive dashboard surface actionable insights?**
3. **What financial health indicators matter most?**
4. **How do owners track team and business performance?**

---

## Research Areas

### Executive Dashboard Overview

```typescript
interface ExecutiveDashboard {
  // Owner's morning dashboard — everything at a glance
  morning_view: {
    // Today's pulse
    today: {
      date: string;
      active_trips: number;
      trips_departing_today: number;
      trips_returning_today: number;
      new_inquiries: number;
      pending_proposals: number;
      expected_payments: number;
      open_issues: number;
    };

    // Revenue pulse
    revenue: {
      mtd_revenue: number;                   // month-to-date
      mtd_target: number;
      mtd_achievement: number;               // % of target
      pipeline_value: number;                // proposals in play
      cash_position: number;                 // bank + receivables
    };

    // Alerts requiring attention
    alerts: {
      critical: Array<{
        type: string;
        message: string;
        action: string;
      }>;
      // Examples:
      // "3 trips departing this week have unresolved issues"
      // "₹2.4L payment overdue from Gupta booking"
      // "Margin on Europe packages below 10% threshold"
      // "Agent Amit's conversion rate dropped 40% this month"
    };
  };
}

// ── Executive dashboard — morning view ──
// ┌─────────────────────────────────────────────────────┐
// │  Waypoint Travel · Owner Dashboard                      │
// │  Good morning, Pranay · Tuesday, Apr 29, 2026           │
// │                                                       │
// │  ┌─ Today's Pulse ──────────────────────────────────┐│
// │  │ 🌏 Active trips: 14 · Departing: 2 · Returning: 1 │
// │  │ 📥 New inquiries: 6 · Proposals pending: 8         │
// │  │ 💰 Expected payments today: ₹3.2L                  │
// │  │ ⚠️ Open issues: 3 (1 urgent)                       │
// │  └───────────────────────────────────────────────────┘│
// │                                                       │
// │  ┌─ Revenue ───────────────────────────────────────┐│
// │  │ MTD: ₹18.4L / ₹25L target (73.6%)               ││
// │  │ ████████████████████████████████████████░░░░░░    ││
// │  │                                                       │
// │  │ Pipeline: ₹12.6L (8 active proposals)              ││
// │  │ Cash position: ₹8.2L (bank + receivables)           ││
// │  │                                                       │
// │  │ vs last month: +12% revenue · +8% pipeline           ││
// │  └───────────────────────────────────────────────────┘│
// │                                                       │
// │  🔴 Needs Attention:                                  │
// │  • ₹2.4L overdue from Gupta booking (7 days)          │
// │  • Agent Amit conversion dropped 40% — coaching needed│
// │  • 2 Singapore allotments releasing Jun 1 (₹85K)      │
// │                                                       │
// │  [View Details] [Take Action] [Weekly Report]           │
// └─────────────────────────────────────────────────────┘
```

### Key Performance Indicators

```typescript
interface AgencyKPIs {
  // KPIs organized by business dimension
  dimensions: {
    REVENUE: {
      kpis: [
        { name: "Monthly Revenue", target: "₹25L", actual: "₹18.4L", trend: "+12% MoM" },
        { name: "Revenue per Trip", target: "₹1.8L", actual: "₹2.1L", trend: "+5% MoM" },
        { name: "Average Package Value", target: "₹2.0L", actual: "₹2.1L", trend: "Stable" },
        { name: "Revenue per Agent", target: "₹6L/mo", actual: "₹5.2L/mo", trend: "+8% MoM" },
        { name: "Revenue per Channel", values: { whatsapp: "42%", website: "18%", walkin: "25%", referral: "15%" } },
      ];
    };

    PROFITABILITY: {
      kpis: [
        { name: "Gross Margin", target: "18%", actual: "16.3%", trend: "+1.2% MoM" },
        { name: "Net Margin", target: "12%", actual: "10.8%", trend: "+0.5% MoM" },
        { name: "Cost per Acquisition", target: "₹1,500", actual: "₹1,850", trend: "-8% MoM" },
        { name: "Marketing ROI", target: "5x", actual: "6.2x", trend: "+15% MoM" },
        { name: "Referral ROI", target: "10x", actual: "19.5x", trend: "Best channel" },
      ];
    };

    SALES_PIPELINE: {
      kpis: [
        { name: "Inquiries per Month", target: "120", actual: "98", trend: "+22% MoM" },
        { name: "Inquiry-to-Booking Rate", target: "25%", actual: "22%", trend: "+3% MoM" },
        { name: "Avg Days to Close", target: "12", actual: "14", trend: "-2 days MoM" },
        { name: "Proposal Acceptance Rate", target: "50%", actual: "48%", trend: "Stable" },
        { name: "Lost Deal Recovery", target: "15%", actual: "12%", trend: "+4% MoM" },
      ];
    };

    CUSTOMER: {
      kpis: [
        { name: "NPS Score", target: "45", actual: "52", trend: "+5 pts" },
        { name: "Repeat Booking Rate", target: "30%", actual: "28%", trend: "+3% MoM" },
        { name: "Customer Lifetime Value", target: "₹2.5L", actual: "₹2.1L", trend: "+12% YoY" },
        { name: "Referral Rate", target: "10%", actual: "8%", trend: "+2% MoM" },
        { name: "Complaint Rate", target: "<3%", actual: "2.1%", trend: "Improving" },
      ];
    };

    OPERATIONS: {
      kpis: [
        { name: "Trip Issue Rate", target: "<5%", actual: "4.2%", trend: "-1% MoM" },
        { name: "Avg Resolution Time", target: "<4h", actual: "3.2h", trend: "Improving" },
        { name: "Supplier On-Time Rate", target: "95%", actual: "92%", trend: "+2% MoM" },
        { name: "Document Compliance", target: "100%", actual: "98%", trend: "1 case pending" },
        { name: "Payment Collection Rate", target: "95%", actual: "93%", trend: "+1% MoM" },
      ];
    };
  };
}

// ── KPI dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Agency KPIs — April 2026                               │
// │                                                       │
// │  [Revenue] [Profit] [Sales] [Customer] [Ops]            │
// │                                                       │
// │  ┌─ Revenue KPIs ───────────────────────────────────┐│
// │  │ Monthly Revenue    ₹18.4L / ₹25L    73.6%  ▲12% ││
// │  │ ████████████████████████████████████████░░░░░░   ││
// │  │                                                   ││
// │  │ Rev per Trip       ₹2.1L / ₹1.8L    116%   ▲5%  ││
// │  │ ██████████████████████████████████████████████   ││
// │  │                                                   ││
// │  │ Rev per Agent      ₹5.2L / ₹6.0L    86%    ▲8%  ││
// │  │ █████████████████████████████████████░░░░░░░░░   ││
// │  └───────────────────────────────────────────────────┘│
// │                                                       │
// │  Revenue by channel:                                  │
// │  WhatsApp:     42% ██████████████████████             │
// │  Walk-in:      25% ████████████                       │
// │  Website:      18% █████████                          │
// │  Referral:     15% ███████                            │
// │                                                       │
// │  Revenue by destination:                              │
// │  Singapore:    32% ████████████████                   │
// │  Dubai:        18% █████████                          │
// │  Kerala:       15% ███████                            │
// │  Europe:       14% ███████                            │
// │  Thailand:     11% █████                              │
// │  Other:        10% █████                              │
// │                                                       │
// │  [Export KPI Report] [Set Targets] [Trend Analysis]     │
// └─────────────────────────────────────────────────────┘
```

### Financial Health Indicators

```typescript
interface FinancialHealth {
  // Financial health dashboard for agency owner
  health_indicators: {
    CASH_FLOW: {
      metric: "Operating cash flow";
      formula: "collections - payments - expenses";
      healthy: "Positive and growing month-over-month";
      warning: "Negative for 2+ consecutive months";
      critical: "Negative for 3+ months or declining trend";
    };

    RECEIVABLES: {
      metric: "Accounts receivable aging";
      buckets: {
        current: "₹4.2L (within terms)";
        aging_1_7: "₹1.8L (1-7 days overdue)";
        aging_8_30: "₹2.4L (8-30 days overdue)";
        aging_30_plus: "₹0.5L (30+ days overdue — action needed)";
      };
      action: "Auto-reminder at 7 days, agent call at 14 days, owner call at 30 days";
    };

    PAYABLES: {
      metric: "Supplier payments due";
      buckets: {
        due_this_week: "₹3.2L";
        due_next_week: "₹2.8L";
        due_this_month: "₹8.5L";
      };
      cash_coverage: "Current cash covers 1.2x this month's payables";
    };

    MARGIN_TREND: {
      metric: "Margin trend by destination and package type";
      alerts: [
        "Europe margins dropped from 15% to 11% — investigate supplier rate changes",
        "Singapore margins improved from 12% to 16% — new hotel contract paying off",
        "Kerala margins stable at 22% — strongest performing destination",
      ];
    };
  };
}

// ── Financial health dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Financial Health — April 2026                           │
// │                                                       │
// │  Overall health: 🟢 GOOD                                │
// │                                                       │
// │  Cash Flow:                                           │
// │  Inflows (MTD):  ₹18.4L                               │
// │  Outflows (MTD): ₹14.2L                               │
// │  Net cash:       ₹4.2L  ✅ Positive                    │
// │                                                       │
// │  Receivables: ₹8.9L outstanding                        │
// │  Current:    ₹4.2L  ████████████████████████           │
// │  1-7 days:   ₹1.8L  █████████                         │
// │  8-30 days:  ₹2.4L  ████████████                      │
// │  30+ days:   ₹0.5L  ███ ⚠️ Follow up!                 │
// │                                                       │
// │  Payables: ₹8.5L due this month                        │
// │  Due this week:   ₹3.2L  (cash covered ✅)             │
// │  Due next week:   ₹2.8L  (cash covered ✅)             │
// │  Due rest of mo:  ₹2.5L                                │
// │                                                       │
// │  Margin trend:                                        │
// │  Singapore:  16% ▲ (+4% from new contract)             │
// │  Europe:     11% ▼ (-4% supplier rate increase)        │
// │  Kerala:     22% ━ (stable, best performer)            │
// │  Dubai:      14% ▲ (+2% from activity upselling)       │
// │  Overall:    16.3% ▲ (+1.2% MoM)                       │
// │                                                       │
// │  [Cash Flow Report] [Send Payment Reminders] [Plan]     │
// └─────────────────────────────────────────────────────┘
```

### Team Performance Overview

```typescript
interface TeamPerformanceOverview {
  // Owner's view of team performance
  team_view: {
    agents: {
      name: string;
      role: string;
      kpi_summary: {
        trips_handled: number;
        revenue_generated: number;
        conversion_rate: number;
        customer_satisfaction: number;
        avg_response_time: string;
      };
      trend: "IMPROVING" | "STABLE" | "DECLINING";
      alerts: string[];
    }[];

    // Team aggregate
    team_aggregate: {
      total_agents: number;
      avg_deal_value: number;
      team_conversion_rate: number;
      team_nps: number;
      revenue_per_agent: number;
    };

    // Staffing insights
    staffing: {
      workload_balance: "Evenly distributed" | "Uneven — some agents overloaded";
      peak_hours: string[];                // When most inquiries come
      understaffed_periods: string[];       // When no agent is available
      recommended_action: string;
    };
  };
}

// ── Team performance overview ──
// ┌─────────────────────────────────────────────────────┐
// │  Team Performance — April 2026                           │
// │                                                       │
// │  Agent    │ Trips │ Revenue │ Conv │ NPS  │ Trend     │
// │  ─────────────────────────────────────────────────────│
// │  Rahul    │  12   │ ₹6.8L  │ 52%  │ 4.7  │ ▲ TOP     │
// │  Priya    │  14   │ ₹6.2L  │ 45%  │ 4.5  │ ━ Stable  │
// │  Neha     │  10   │ ₹5.0L  │ 42%  │ 4.3  │ ▲ Good    │
// │  Amit     │   8   │ ₹3.2L  │ 35%  │ 4.1  │ ▼ Action  │
// │  ─────────────────────────────────────────────────────│
// │  Team     │  44   │ ₹21.2L │ 44%  │ 4.4  │           │
// │                                                       │
// │  Staffing insights:                                   │
// │  • Peak inquiries: 10 AM-12 PM, 8 PM-10 PM            │
// │  • Understaffed: Tue/Thu evenings (no coverage)        │
// │  • Rahul overloaded: 28% of active trips               │
// │  • Recommendation: Hire 1 agent for evening shift       │
// │                                                       │
// │  Coaching actions needed:                              │
// │  🔴 Amit: Conversion down 40%, escalation rate 8%       │
// │     → Schedule 1:1 coaching + pair with Rahul          │
// │  🟡 Neha: Good trajectory, ready for senior role        │
// │     → Assign Europe/Europe trips (higher complexity)   │
// │                                                       │
// │  [Detailed Agent View] [Schedule Coaching] [Hire Plan]  │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Alert fatigue** — Too many alerts desensitize owners. Need severity-based filtering: only surface what requires action today, batch the rest for weekly review.

2. **KPI gaming** — Agents may optimize for KPIs at expense of customer experience (e.g., rushing proposals to improve response time). Need balanced scorecards, not single-metric focus.

3. **Data freshness** — Financial data depends on timely entry (payments recorded, expenses logged). If agents delay entries, dashboard shows stale data. Need automated data capture.

4. **Benchmarking** — Agency owners want to know "am I doing well?" but industry benchmarks for Indian travel agencies are scarce. Need anonymous data sharing consortium.

---

## Next Steps

- [ ] Build executive dashboard with morning pulse view
- [ ] Implement KPI tracking across all business dimensions
- [ ] Create financial health monitoring with receivables aging
- [ ] Design team performance overview with coaching recommendations
