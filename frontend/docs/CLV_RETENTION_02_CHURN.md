# Customer Lifetime Value & Retention — Churn Prediction & Prevention

> Research document for churn prediction models, early warning signals, retention strategies, win-back campaigns, and loyalty mechanics for travel agencies.

---

## Key Questions

1. **How do we predict which customers will churn?**
2. **What early warning signals indicate churn risk?**
3. **What retention strategies work for each risk level?**
4. **How do we design effective win-back campaigns?**

---

## Research Areas

### Churn Prediction Model

```typescript
interface ChurnPrediction {
  customer_id: string;
  churn_risk: "VERY_LOW" | "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  churn_probability: number;            // 0-1
  predicted_churn_date: string | null;  // when they'll likely stop engaging

  // Risk factors
  risk_factors: {
    factor: string;
    weight: number;
    evidence: string;
  }[];

  // Protective factors
  protective_factors: {
    factor: string;
    weight: number;
    evidence: string;
  }[];

  // Recommended intervention
  intervention: {
    urgency: "IMMEDIATE" | "THIS_WEEK" | "THIS_MONTH" | "MONITOR";
    action: string;
    channel: "CALL" | "WHATSAPP" | "EMAIL" | "AGENT_OUTREACH";
    offer: string | null;
    assigned_to: string | null;
  };
}

// ── Churn risk factors for travel ──
// ┌─────────────────────────────────────────────────────┐
// │  Churn Risk Factors — Travel Agency                    │
// │                                                       │
// │  Signal                  | Weight | Example           │
// │  ─────────────────────────────────────────────────── │
// │  No trip in 12+ months   | HIGH   | Last trip: Feb 25│
// │  Declining trip value    | HIGH   | ₹3L → ₹2L → ₹1L│
// │  Complaints on last trip | HIGH   | Hotel was dirty   │
// │  Switched to competitor  | HIGH   | Booked on MakeMyTrip│
// │  Ignored last 3 offers   | MED    | Didn't open emails│
// │  Agent relationship ended| MED    | Agent left agency │
// │  Reduced response rate   | MED    | 80% → 20% reply  │
// │  Cancelled last 2 trips  | MED    | Booked then cancel│
// │  Negative review given   | MED    | 2-star on Google  │
// │  Life event change       | LOW    | Moved, had baby   │
// │  Reduced group size      | LOW    | Family of 5 → solo│
// │                                                       │
// │  Protective factors:                                  │
// │  • Referred 2+ customers (vested interest)           │
// │  • Upcoming trip booked (active customer)            │
// │  • Loyalty tier: Gold+ (sunk cost in program)        │
// │  • Personal agent relationship (trust)               │
// │  • Multi-generational family trips (tradition)       │
// └─────────────────────────────────────────────────────┘
```

### Retention Strategy Matrix

```typescript
// ── Retention strategies by risk level ──
// ┌─────────────────────────────────────────────────────┐
// │  Retention Strategy Matrix                             │
// │                                                       │
// │  Risk: LOW (churn < 15%)                              │
// │  Strategy: Nurture & Upsell                           │
// │  • Send personalized destination recommendations     │
// │  • Offer loyalty tier upgrade path                   │
// │  • Share new destination/event packages              │
// │  • Annual travel planning call                        │
// │  • Birthday/anniversary trip offers                  │
// │                                                       │
// │  Risk: MODERATE (churn 15-35%)                        │
// │  Strategy: Re-engage                                  │
// │  • Personal call from assigned agent                 │
// │  • Exclusive "we miss you" offer (10% discount)      │
// │  • New destination pitch (something they haven't tried│
// │  • Invite to agency event (travel meetup)            │
// │  • Share travel inspiration content                  │
// │                                                       │
// │  Risk: HIGH (churn 35-65%)                            │
// │  Strategy: Win-back with incentives                   │
// │  • Agent visits/calls with personalized offer        │
// │  • Significant discount (15-20%) on next trip        │
// │  • Free travel insurance on next booking             │
// │  • Address previous complaints directly              │
// │  • Offer a different agent if relationship issue     │
// │                                                       │
// │  Risk: CRITICAL (churn > 65%)                         │
// │  Strategy: Last-chance retention                      │
// │  • Owner/manager direct call                         │
// │  • Best possible offer (25% off + free add-ons)      │
// │  • Acknowledge and resolve past issues               │
// │  • If budget traveler, shift to email-only nurturing │
// │  • If high-value, assign senior agent personally     │
// └─────────────────────────────────────────────────────┘
```

### Win-Back Campaign Design

```typescript
interface WinBackCampaign {
  name: string;
  target_segment: string;
  churn_risk_range: [number, number];

  stages: {
    day: number;
    channel: "CALL" | "WHATSAPP" | "EMAIL" | "SMS";
    message_template: string;
    offer: string | null;
    success_metric: string;
  }[];

  expected_response_rate: number;
  expected_conversion_rate: number;
  cost_per_win_back: Money;
  avg_win_back_value: Money;
}

// ── Win-back campaign example ──
// ┌─────────────────────────────────────────────────────┐
// │  Win-Back Campaign: "We Miss You"                      │
// │  Target: No trip in 9+ months, Gold/Platinum tier     │
// │                                                       │
// │  Day 1: WhatsApp message                              │
// │  "Hi [Name]! It's been a while. We have exclusive    │
// │   early access to Diwali packages. Your agent [Name]  │
// │   would love to catch up. Reply YES for a callback." │
// │  Offer: Early bird pricing + free airport transfer   │
// │                                                       │
// │  Day 3: If no response, follow-up call               │
// │  Agent calls personally, asks about travel plans     │
// │  Offer: 10% discount on any trip booked this month   │
// │                                                       │
// │  Day 7: If no response, email with curated options   │
// │  Personalized destination picks based on history     │
// │  Offer: 15% discount + free travel insurance         │
// │                                                       │
// │  Day 14: Final attempt — SMS with best offer         │
// │  "Last chance: 20% off your next trip. Valid 48hrs." │
// │  Offer: Best available discount                      │
// │                                                       │
// │  Expected: 8% response, 3% conversion                │
// │  Cost per win-back: ₹1,800                           │
// │  Avg win-back trip value: ₹2.8L (155x CAC)          │
// └─────────────────────────────────────────────────────┘
```

### Loyalty Mechanics for Retention

```typescript
// ── Retention-focused loyalty mechanics ──
// ┌─────────────────────────────────────────────────────┐
// │  Loyalty Mechanics That Drive Retention                │
// │                                                       │
// │  1. Tier-based benefits (sunk cost to leave)         │
// │     • Silver: 5% discount, priority support          │
// │     • Gold: 10% discount, free insurance, room upgrade│
// │     • Platinum: 15% discount, concierge, lounge access│
// │     • Points don't expire for active tiers           │
// │                                                       │
// │  2. Anniversary rewards                               │
// │     • Trip anniversary: "1 year since your Kerala    │
// │       trip! Here's ₹2,000 off your next adventure." │
// │     • Customer anniversary: "3 years with us!        │
// │       Free upgrade on your next booking."            │
// │                                                       │
// │  3. Referral rewards (creates network effect)        │
// │     • Refer a friend: Both get ₹2,000 credit        │
// │     • Refer 3 friends: Free weekend getaway         │
// │     • Top referrer quarterly: Premium trip giveaway  │
// │                                                       │
// │  4. Early access (exclusivity)                        │
// │     • Gold+ members see new packages 48hrs early     │
// │     • Festival packages: pre-sale for loyal customers│
// │     • New destinations: invitation-only preview      │
// │                                                       │
// │  5. Surprise & delight                                │
// │     • Random upgrades on trips (hotel/flight)        │
// │     • Birthday surprise (cake at hotel, spa voucher) │
// │     • Trip photo book after return (free)            │
// │     • "We noticed you love Goa" — personalized gift │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Churn vs natural cycle** — Not traveling for 12 months may be normal (pregnancy, job change, financial). Distinguishing temporary pause from permanent churn is hard.

2. **Offer fatigue** — Constant discounts train customers to wait for deals. Retention offers must be non-discount value (upgrades, experiences) when possible.

3. **Agent turnover** — When an agent leaves the agency, their customers are at high churn risk. Need relationship transfer protocols.

4. **Measurement attribution** — Did the customer return because of the win-back campaign or would they have anyway? Need control groups.

---

## Next Steps

- [ ] Build churn prediction model with risk scoring
- [ ] Create automated retention workflow by risk level
- [ ] Design win-back campaign templates
- [ ] Implement loyalty mechanics for retention
