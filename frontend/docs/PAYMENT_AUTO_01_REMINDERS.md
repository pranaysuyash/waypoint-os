# Payment Automation — Reminders, Scheduling & Follow-Up

> Research document for automated payment reminders, payment scheduling, balance tracking alerts, EMI management, overdue payment escalation, and payment lifecycle automation for the Waypoint OS platform.

---

## Key Questions

1. **How does the system automate payment collection and reminders?**
2. **What payment scheduling options are available for customers?**
3. **How are overdue payments escalated?**
4. **What payment automation reduces agent workload?**

---

## Research Areas

### Payment Automation Engine

```typescript
interface PaymentAutomation {
  // Automated payment reminders, scheduling, and follow-up
  payment_lifecycle: {
    ADVANCE_COLLECTION: {
      timing: "At booking confirmation";
      automation: "Payment link auto-generated and sent via WhatsApp + email";
      amount: "10-25% of total trip cost (configurable per package)";
      deadline: "48 hours from booking confirmation";
      reminder: "Auto-reminder at 24 hours if not paid";
      escalation: "Agent call if not paid within 48 hours — booking may be released";
    };

    MILESTONE_PAYMENTS: {
      description: "Scheduled payment milestones for large bookings";
      schedule: {
        booking: "25% advance at booking confirmation",
        visa_approval: "25% upon visa approval (or 60 days before departure)",
        pre_departure: "50% balance 14 days before departure",
      };
      automation: {
        reminder: "Payment reminder sent 7 days, 3 days, and 1 day before each milestone";
        link: "Fresh payment link with exact amount and due date in each reminder",
        confirmation: "Payment receipt auto-sent within 5 minutes of successful payment",
      };
    };

    FULL_PAYMENT: {
      deadline: "7-14 days before departure (configurable)";
      critical: "Trip documents (vouchers, tickets) released only after full payment received";
      final_reminder: "Auto-call from agent 3 days before if balance outstanding";
    };
  };

  reminder_templates: {
    FRIENDLY_REMINDER: {
      timing: "7 days before payment due";
      channel: "WhatsApp + Email";
      template: `
        Hi {name}! 👋

        Quick reminder: Your next payment for the Singapore trip is due on {date}.

        💰 Amount: ₹{amount}
        📅 Due date: {date}
        💳 Balance after this: ₹{remaining}

        [Pay Now via Razorpay]

        Questions? Just reply to this message!
      `;
    };

    URGENT_REMINDER: {
      timing: "1 day before payment due";
      channel: "WhatsApp + SMS + Phone call";
      template: `
        Hi {name}! ⚠️

        Your payment of ₹{amount} is due TOMORROW.

        To keep your bookings confirmed, please complete the payment today.

        [Pay Now]

        Need help? Call {agent_name} at {agent_phone}
      `;
    };

    OVERDUE_NOTICE: {
      timing: "1 day after payment due";
      channel: "Phone call from agent + WhatsApp";
      template: `
        Hi {name},

        Your payment of ₹{amount} was due on {date} and is now overdue.

        ⚠️ Bookings may be cancelled if payment is not received within 48 hours.

        Please pay now to keep your trip confirmed:
        [Pay Now]

        If you're facing any issues, please call us immediately.
      `;
    };
  };

  // ── Payment automation dashboard ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Payment Automation · Collection Status                    │
  // │                                                       │
  // │  Upcoming Payments (next 7 days):                     │
  // │  Sharma  · ₹42K · Due May 5 · [Reminder Sent ✅]        │
  // │  Patel   · ₹28K · Due May 7 · [Reminder Scheduled]      │
  // │  Gupta   · ₹55K · Due May 8 · [Reminder Scheduled]      │
  // │                                                       │
  // │  Overdue Payments:                                    │
  // │  Mehta   · ₹35K · Due Apr 28 · 2 days overdue           │
  // │    → WhatsApp sent Apr 28 ✅                              │
  // │    → Phone call attempted Apr 29 ✅                       │
  // │    → Agent follow-up assigned to Rahul ⚠️                │
  // │                                                       │
  // │  Collection Summary:                                  │
  // │  Total outstanding:   ₹4.2L                              │
  // │  Due this week:       ₹1.25L (3 customers)              │
  // │  Overdue:             ₹35K (1 customer)                  │
  // │  Collection rate:     94% (last 30 days)                 │
  // │                                                       │
  // │  [Send Bulk Reminder] [View Overdue] [Export Report]      │
  // └─────────────────────────────────────────────────────────┘
}
```

### EMI & Flexible Payment Options

```typescript
interface FlexiblePayments {
  // EMI and flexible payment for customers
  options: {
    EMI_PLANS: {
      description: "Convert trip cost to monthly EMIs";
      providers: ["Razorpay EMI", "ZestMoney", "Bajaj Finserv", "HDFC EMI"];
      eligibility: "Based on customer's credit profile; instant approval for pre-approved customers";
      terms: {
        "3_month": "No interest (0% EMI on select cards)";
        "6_month": "₹500-1,000 processing fee";
        "12_month": "12-15% interest rate";
      };
      integration: "EMI option shown at checkout; customer selects tenure → instant approval → auto-debit setup";
    };

    PARTIAL_PAYMENT_SCHEDULING: {
      description: "Customer sets their own payment schedule within limits";
      rules: {
        minimum_advance: "25% at booking (non-negotiable)";
        final_deadline: "Full payment 7 days before departure (non-negotiable)";
        middle_flexibility: "Customer can schedule middle payments at their preferred dates";
      };
      automation: "Auto-reminders on customer's chosen dates; payment link auto-generated";
    };

    GROUP_PAYMENT_SPLIT: {
      description: "Split trip cost across multiple payers (group travel)";
      mechanism: {
        total: "Trip total: ₹3.6L for family of 3";
        split: "Each family member pays ₹1.2L separately via individual payment links";
        tracking: "Dashboard shows who has paid and who hasn't";
        deadline: "All splits must be complete by same deadline";
      };
    };
  };
}
```

### Payment Analytics & Risk

```typescript
interface PaymentAnalyticsRisk {
  // Payment collection analytics and risk management
  analytics: {
    COLLECTION_METRICS: {
      on_time_rate: "Payments received by due date (target: 90%+)";
      avg_days_to_pay: "Average days from reminder to payment (target: <3 days)";
      overdue_rate: "Payments overdue by >3 days (target: <5%)";
      default_rate: "Payments never received (target: <1%)";
      collection_efficiency: "Total collected / total invoiced (target: 98%+)";
    };

    RISK_INDICATORS: {
      flags: [
        "Customer has missed 2+ payment reminders → higher default risk",
        "Customer requested 3rd extension on payment deadline → escalate",
        "First-time customer with large booking value → verify payment",
        "Customer paid advance but no communication for 30+ days → re-engage",
      ];
    };

    CASH_FLOW_PROJECTION: {
      description: "Projected cash inflow from upcoming payments";
      weekly: "This week: ₹1.25L expected from 3 customers";
      monthly: "May: ₹8.2L expected from 18 customers";
      seasonal: "Peak season (Apr-Jun): ₹24L expected collection";
    };
  };
}
```

---

## Open Problems

1. **Payment vs. cancellation timing** — If a customer doesn't pay and the booking is cancelled, the agency may lose supplier deposits. Need clear policies: when to hold, when to release, and how much to refund.

2. **EMI defaults** — EMI defaults are the bank's problem (not the agency's) once the full payment is received via EMI financing. But approval delays can push past booking deadlines.

3. **Cultural sensitivity** — Indian customers may find aggressive payment reminders offensive. The tone must be friendly and helpful, not demanding. "Just a friendly reminder" >> "Your payment is overdue."

4. **WhatsApp payment links** — Payment links in WhatsApp messages are convenient but some customers are wary of clicking links in messages. Need clear branding (Razorpay/PhonePe) to build trust.

5. **Partial payment tracking** — Group payments where multiple people contribute to one booking create complex tracking. Each payer's contribution must be tracked individually while maintaining the unified booking.

---

## Next Steps

- [ ] Build automated payment reminder engine with milestone tracking
- [ ] Create payment scheduling system with customer-configurable dates
- [ ] Implement EMI integration with multiple providers
- [ ] Design overdue payment escalation workflow
- [ ] Build payment collection analytics and cash flow projection
