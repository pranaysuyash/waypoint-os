# Agency Financial Dashboard — Alerts & Anomalies

> Research document for revenue anomaly detection, margin erosion alerts, payment overdue tracking, cash flow warnings, vendor payment monitoring, and fraud indicators.

---

## Key Questions

1. **What financial anomalies need immediate attention?**
2. **How do we detect margin erosion before it becomes critical?**
3. **What payment and cash flow alerts are essential?**
4. **How do we flag potential fraud indicators?**

---

## Research Areas

### Alert Architecture

```typescript
interface FinancialAlert {
  id: string;
  type: FinancialAlertType;
  severity: "INFO" | "WARNING" | "CRITICAL" | "EMERGENCY";
  category: string;
  title: string;
  description: string;

  // Context
  metric: string;
  current_value: number;
  threshold: number;
  deviation: number;                     // percentage deviation

  // Impact
  financial_impact: Money | null;
  affected_trips: string[];
  affected_agents: string[];

  // Action
  recommended_actions: string[];
  auto_actions_taken: string[];
  requires_approval: boolean;

  // Lifecycle
  status: "NEW" | "ACKNOWLEDGED" | "IN_PROGRESS" | "RESOLVED" | "SNOOZED";
  created_at: string;
  resolved_at: string | null;
  assigned_to: string | null;
}

type FinancialAlertType =
  | "REVENUE_ANOMALY"
  | "MARGIN_EROSION"
  | "PAYMENT_OVERDUE"
  | "CASH_FLOW_WARNING"
  | "VENDOR_PAYMENT_DUE"
  | "TAX_DEADLINE"
  | "FRAUD_INDICATOR"
  | "BUDGET_OVERRUN"
  | "COMMISSION_ANOMALY"
  | "REFUND_SPIKE"
  | "CURRENCY_RISK"
  | "VENDOR_PRICE_CHANGE";

// ── Alert center ──
// ┌─────────────────────────────────────────────────────┐
// │  Financial Alert Center                    3 new 🔴   │
// │                                                       │
// │  🔴 CRITICAL — Cash flow deficit projected W21      │
// │     Balance may drop to ₹8L (threshold: ₹10L)       │
// │     ₹5.3L outflow > ₹4.2L inflow                   │
// │     Action: Accelerate receivables or arrange credit │
// │     15 min ago                                       │
// │                                                       │
// │  🟡 WARNING — Margin erosion: Goa packages          │
// │     Average margin dropped from 18% → 14% this month│
// │     Cause: Vendor rates +8% without price increase   │
// │     Impact: ₹45K lost margin on 12 trips            │
// │     Action: Renegotiate vendor rates or increase MRP │
// │     2 hours ago                                      │
// │                                                       │
// │  🟡 WARNING — 5 payments overdue (>7 days)          │
// │     Total overdue: ₹3.8L                            │
// │     Largest: ₹1.2L (Trip #WP-442, due 12 days ago) │
// │     Action: Send reminders, consider hold on services│
// │     4 hours ago                                      │
// │                                                       │
// │  ℹ️ INFO — GST filing due in 5 days (GSTR-3B)       │
// │     Net payable: ₹1.2L                              │
// │     Auto-file ready: ✅                              │
// │     Yesterday                                        │
// └─────────────────────────────────────────────────────┘
```

### Revenue Anomaly Detection

```typescript
interface RevenueAnomalyDetector {
  // Detection methods
  detectSuddenDrop(period: string, threshold_pct: number): RevenueAnomaly[];
  detectUnusualPattern(historical_window_weeks: number): RevenueAnomaly[];
  detectChannelAnomaly(channel: string): RevenueAnomaly[];
  detectDestinationAnomaly(destination: string): RevenueAnomaly[];
}

interface RevenueAnomaly {
  metric: string;
  expected: Money;
  actual: Money;
  deviation_pct: number;
  possible_causes: string[];
  confidence: number;
}

// ── Revenue anomaly scenarios ──
// ┌─────────────────────────────────────────────────────┐
// │  Revenue Anomaly Detection Rules                      │
// │                                                       │
// │  Rule                  | Threshold   | Action         │
// │  ─────────────────────────────────────────────────── │
// │  Daily revenue drop    | >25% vs     | Alert finance │
// │                        | 7-day avg   | head           │
// │                                                       │
// │  Weekly revenue miss   | >15% below  | Alert owner,  │
// │                        | forecast    | review pipeline│
// │                                                       │
// │  Channel collapse      | >40% drop   | Check channel │
// │                        | in 3 days   | health         │
// │                                                       │
// │  Destination spike     | >50% above  | Check if      │
// │                        | normal      | sustainable    │
// │                                                       │
// │  Conversion rate drop  | >10% vs     | Check lead    │
// │                        | last month  | quality        │
// │                                                       │
// │  Deal size shrink      | >20% below  | Review pricing│
// │                        | 3-mo avg    | strategy       │
// └─────────────────────────────────────────────────────┘
```

### Margin Erosion Alerts

```typescript
interface MarginAlert {
  scope: "AGENCY" | "DESTINATION" | "AGENT" | "SEGMENT" | "PRODUCT";
  scope_id: string;

  current_margin: number;
  previous_margin: number;
  target_margin: number;
  erosion_pct: number;

  causes: {
    vendor_price_increase: boolean;
    discount_too_deep: boolean;
    currency_impact: boolean;
    overhead_growth: boolean;
    product_mix_shift: boolean;
  };

  impact: {
    lost_margin_this_month: Money;
    projected_annual_impact: Money;
  };
}

// ── Margin erosion dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Margin Erosion Monitor — April 2026                  │
// │                                                       │
// │  🔴 Goa packages: 18.5% → 14.2% (-4.3%)            │
// │     Root cause: Hotel rates +12% (seasonal surge)    │
// │     Lost margin: ₹45K (12 trips)                    │
// │     Fix: Increase Goa package prices by 8%           │
// │                                                       │
// │  🟡 Thailand packages: 16.8% → 14.5% (-2.3%)       │
// │     Root cause: INR/THB depreciation +5%             │
// │     Lost margin: ₹22K (6 trips)                     │
// │     Fix: Adjust THB pricing or hedge currency        │
// │                                                       │
// │  🟡 Budget segment: 12% → 10.2% (-1.8%)            │
// │     Root cause: Excessive discounting to win deals   │
// │     Lost margin: ₹38K (28 trips)                    │
// │     Fix: Cap discount at 8% for budget packages      │
// │                                                       │
// │  ✅ Dubai packages: 24.2% → 24.8% (+0.6%)          │
// │     No action needed                                  │
// └─────────────────────────────────────────────────────┘
```

### Payment Overdue Tracking

```typescript
interface PaymentOverdueTracker {
  overdue_payments: {
    trip_id: string;
    customer: string;
    amount: Money;
    due_date: string;
    days_overdue: number;
    reminders_sent: number;
    last_reminder: string | null;
    escalation_level: "NONE" | "SOFT" | "FIRM" | "FINAL" | "LEGAL";
    agent_assigned: string;
  }[];

  summary: {
    total_overdue: Money;
    count: number;
    avg_days_overdue: number;
    aging: {
      "1-7_days": Money;
      "8-15_days": Money;
      "16-30_days": Money;
      "31-60_days": Money;
      "60_plus_days": Money;
    };
  };
}

// ── Overdue payment aging ──
// ┌─────────────────────────────────────────────────────┐
// │  Payment Aging Report — As of Apr 29, 2026            │
// │                                                       │
// │  Bucket       | Count | Amount  | Action Level       │
// │  ─────────────────────────────────────────────────── │
// │  1-7 days     | 8     | ₹2.4L   | Soft reminder      │
// │  8-15 days    | 5     | ₹3.8L   | Firm reminder      │
// │  16-30 days   | 3     | ₹2.2L   | Final notice       │
// │  31-60 days   | 2     | ₹1.8L   | Legal review       │
// │  60+ days     | 1     | ₹0.8L   | Collection agency  │
// │  ─────────────────────────────────────────────────── │
// │  TOTAL        | 19    | ₹11L    |                     │
// │                                                       │
// │  Auto-escalation rules:                               │
// │  Day 3: WhatsApp reminder                            │
// │  Day 7: Email reminder + agent call                  │
// │  Day 15: Firm email + hold on future services        │
// │  Day 30: Final notice + legal review                 │
// │  Day 60: Collection agency referral                  │
// └─────────────────────────────────────────────────────┘
```

### Cash Flow Warnings

```typescript
interface CashFlowWarning {
  type: "PROJECTED_DEFICIT" | "UNUSUAL_OUTFLOW" | "CONCENTRATION_RISK" | "LIQUIDITY_LOW";
  severity: "WARNING" | "CRITICAL";
  message: string;
  projected_date: string;
  amount_at_risk: Money;
  recommended_actions: string[];
}

// ── Cash flow warning scenarios ──
// ┌─────────────────────────────────────────────────────┐
// │  Cash Flow Warning Rules                               │
// │                                                       │
// │  Warning Type         | Trigger                     │
// │  ─────────────────────────────────────────────────── │
// │  Projected deficit    | Balance < safety threshold   │
// │                       | in next 4 weeks              │
// │                                                       │
// │  Unusual outflow      | Single payment > 20% of     │
// │                       | monthly average              │
// │                                                       │
// │  Concentration risk   | >40% of receivables from    │
// │                       | single customer              │
// │                                                       │
// │  Liquidity low        | Current ratio < 1.5          │
// │                       | (assets / liabilities)        │
// │                                                       │
// │  Large vendor payment | >₹5L vendor payment due     │
// │  approaching          | within 7 days                │
// │                                                       │
// │  Tax payment upcoming | GST/TDS/TCS payment due      │
// │                       | within 10 days               │
// └─────────────────────────────────────────────────────┘
```

### Fraud Indicators

```typescript
interface FraudIndicator {
  type: FraudType;
  confidence: number;
  evidence: string[];
  trip_ids: string[];
  agent_ids: string[];
  financial_impact: Money;
  recommended_action: string;
}

type FraudType =
  | "PHANTOM_BOOKING"
  | "SELF_REFERRAL"
  | "COMMISSION_GAMING"
  | "VENDOR_KICKBACK"
  | "DUPLICATE_PAYMENT"
  | "FAKE_CANCELLATION"
  | "PRICE_MANIPULATION"
  | "UNAUTHORIZED_DISCOUNT";

// ── Fraud detection dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Fraud Detection — Suspicious Activity Flags           │
// │                                                       │
// │  🔴 Agent #A12: Commission gaming                    │
// │     Pattern: Splitting bookings to earn more comm.   │
// │     Evidence: 8 bookings for same group, all < ₹50K  │
// │     Impact: ₹12K excess commission                  │
// │     Action: Review agent commission structure         │
// │                                                       │
// │  🟡 Trip #WP-489: Possible phantom booking           │
// │     Pattern: Large booking, paid in cash, no traveler│
// │     Evidence: No traveler documents uploaded,        │
// │               cash payment > ₹2L, agent is payee     │
// │     Impact: ₹3.2L potential loss                    │
// │     Action: Verify traveler identity                 │
// │                                                       │
// │  🟡 Vendor #V34: Price manipulation suspected       │
// │     Pattern: Quoting higher rates for agency vs B2C  │
// │     Evidence: Same hotel ₹8K/night B2C vs ₹10K B2B  │
// │     Impact: ₹15K overpayment across 8 bookings      │
// │     Action: Renegotiate or find alternative vendor   │
// └─────────────────────────────────────────────────────┘
```

### Notification & Escalation

```typescript
interface AlertNotificationConfig {
  alert_type: FinancialAlertType;
  severity: "INFO" | "WARNING" | "CRITICAL" | "EMERGENCY";

  channels: ("DASHBOARD" | "WHATSAPP" | "EMAIL" | "SMS" | "PUSH")[];
  recipients: {
    role: string;
    immediate: boolean;
  }[];

  escalation: {
    after_minutes: number;
    escalate_to: string;
  }[];

  auto_actions: {
    condition: string;
    action: string;
  }[];
}

// ── Escalation matrix ──
// ┌─────────────────────────────────────────────────────┐
// │  Alert Escalation Matrix                              │
// │                                                       │
// │  Severity  | Channel        | Who gets notified       │
// │  ─────────────────────────────────────────────────── │
// │  INFO      | Dashboard      | Assigned person         │
// │  WARNING   | Dashboard +    | Assigned + manager      │
// │            | Email          |                         │
// │  CRITICAL  | All channels   | Manager + finance head  │
// │            |                | + owner (if > ₹2L)      │
// │  EMERGENCY | All channels   | Owner + finance head    │
// │            | + SMS + call   | + immediate action      │
// │                                                       │
// │  Escalation timers:                                   │
// │  INFO:     No escalation (self-resolve in 7 days)    │
// │  WARNING:  Escalate if unresolved in 24 hours        │
// │  CRITICAL: Escalate if unresolved in 4 hours         │
// │  EMERGENCY: Immediate war room                       │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Alert fatigue** — Too many alerts cause desensitization. Need smart aggregation (combine related alerts) and tuning based on which alerts actually get acted on.

2. **False positives** — Revenue dips during festivals or off-season are normal but may trigger anomaly alerts. Need seasonality-aware thresholds.

3. **Fraud vs legitimate** — Some patterns (large cash payments, last-minute changes) are common in Indian travel agencies. Fraud detection must account for cultural norms.

4. **Real-time vs batch** — Payment and cash flow alerts need real-time monitoring, but revenue anomalies require daily aggregation. Mixing both in one system is complex.

---

## Next Steps

- [ ] Build financial alert engine with configurable rules
- [ ] Create revenue anomaly detection with ML-based thresholds
- [ ] Implement margin erosion monitor with root cause analysis
- [ ] Design payment aging and auto-escalation system
- [ ] Build fraud indicator detection for travel agency patterns
- [ ] Create alert notification and escalation framework
