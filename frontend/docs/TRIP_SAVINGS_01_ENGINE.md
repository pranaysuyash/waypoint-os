# Customer Trip Savings & Budget Planning — Savings Engine

> Research document for trip savings goals, automated savings plans, budget tracking, and readiness-triggered engagement for travel agencies.

---

## Key Questions

1. **How do customers save for trips and how can we help?**
2. **What automated savings mechanisms work for Indian consumers?**
3. **How do we engage customers during the savings phase?**
4. **When is a customer 'ready to book' and how do we detect it?**

---

## Research Areas

### Trip Savings Goal Engine

```typescript
interface TripSavingsGoal {
  // Customer sets a savings goal for a trip
  goal_setup: {
    // Goal creation
    creation: {
      destination: string;
      trip_type: "FAMILY" | "COUPLE" | "GROUP" | "SOLO";
      travelers: number;
      target_date: string;                  // when they want to travel
      estimated_budget: number;             // based on destination + trip type
      savings_duration_months: number;
      monthly_savings_required: number;
      current_savings: number;
    };

    // Smart estimation
    budget_estimator: {
      inputs: ["destination", "duration", "travelers", "travel_class", "hotel_tier", "activities"];
      output: {
        budget_range: { min: number; max: number };
        breakdown: {
          flights: number;
          accommodation: number;
          activities: number;
          visa: number;
          insurance: number;
          transfers: number;
          meals: number;
          shopping: number;
        };
        confidence: "HIGH" | "MEDIUM" | "LOW";
        based_on: "Last 50 similar trips booked with us";
      };
    };

    // Savings plan options
    savings_plans: {
      STEADY: {
        description: "Fixed monthly amount";
        example: "₹15,000/month × 8 months = ₹1,20,000";
        mechanism: "Customer manually transfers to savings pool";
      };

      MILESTONE: {
        description: "Variable amounts tied to income events";
        example: "₹20K (bonus month) + ₹8K (regular months)";
        mechanism: "Customer sets milestone dates with higher amounts";
      };

      ROUND_UP: {
        description: "Round up daily spending to nearest ₹100";
        example: "₹247 coffee → ₹300, ₹53 saved";
        mechanism: "UPI round-up integration (future)";
      };

      LOCK_IN: {
        description: "Deposit with agency that locks in current package price";
        example: "Pay ₹25,000 now to lock Singapore package at ₹55K (current price) for Dec travel";
        mechanism: "Agency holds deposit, guarantees price for 6 months";
      };
    };
  };
}

// ── Savings goal setup ──
// ┌─────────────────────────────────────────────────────┐
// │  Plan Your Singapore Trip Savings                        │
// │                                                       │
// │  Trip: Singapore Family (2A+2C) · 5N/6D                 │
// │  Target travel: December 2026                            │
// │                                                       │
// │  Estimated budget: ₹2,30,000                            │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Flights:      ₹1,28,000  ████████████████████ │   │
// │  │ Hotel:         ₹42,500   ██████                │   │
// │  │ Activities:    ₹12,400   ██                    │   │
// │  │ Transfers:      ₹7,100   █                     │   │
// │  │ Visa:           ₹3,000                         │   │
// │  │ Insurance:      ₹7,200   █                     │   │
// │  │ Meals+shopping:₹29,800   ████                  │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Savings plan:                                        │
// │  Duration: 7 months (Jun-Dec)                          │
// │  Monthly savings: ₹32,857                              │
// │  Current savings: ₹40,000                              │
// │  Remaining: ₹1,90,000                                  │
// │                                                       │
// │  Plan options:                                        │
// │  ● Steady: ₹27,143/month                               │
// │  ○ Milestone: ₹15K/mo + ₹60K (Diwali bonus)           │
// │  ○ Lock-in: ₹25K deposit now, locks price at ₹2.23L    │
// │                                                       │
// │  [Start Saving] [Adjust Budget] [Talk to Agent]         │
// └─────────────────────────────────────────────────────┘
```

### Automated Savings Tracking

```typescript
interface SavingsTracking {
  // Track customer savings progress
  tracking: {
    // Progress monitoring
    progress: {
      goal_id: string;
      customer_id: string;
      target_amount: number;
      saved_amount: number;
      progress_percentage: number;
      months_remaining: number;
      on_track: boolean;                    // is savings pace sufficient?
      projected_completion: string;         // when they'll hit goal at current pace
    };

    // Engagement touchpoints during savings phase
    touchpoints: {
      MILESTONE_25: {
        trigger: "Customer has saved 25% of goal";
        message: "Great start! You're 25% toward your Singapore trip. At this pace, you'll be ready by October. Keep it up! 🌟";
        action: "Send destination inspiration content (WhatsApp)";
      };

      MILESTONE_50: {
        trigger: "Customer has saved 50%";
        message: "Halfway there! Your Singapore dream is taking shape. Want to see sample itineraries for your dates?";
        action: "Share 2-3 itinerary options + current pricing";
      };

      MILESTONE_75: {
        trigger: "Customer has saved 75%";
        message: "Almost there! 🎉 75% saved. Let's start planning the details. Shall I send you hotel options?";
        action: "Connect with agent for pre-planning consultation";
      };

      MILESTONE_90: {
        trigger: "Customer has saved 90%";
        message: "Your Singapore trip is just weeks away from booking! Current package price: ₹2.23L. Shall we lock it in?";
        action: "Agent creates personalized proposal";
      };

      OFF_TRACK: {
        trigger: "Savings pace below target for 2 consecutive months";
        message: "We noticed your savings for the Singapore trip have slowed. No worries — would you like to adjust your travel dates or budget? We can find options at a lower price point too.";
        action: "Offer budget alternatives or date flexibility";
      };

      PRICE_ALERT: {
        trigger: "Package price drops below customer's saved amount";
        message: "Great news! Singapore package prices just dropped to ₹2.05L — and you've already saved ₹2.10L! Ready to book?";
        action: "Immediate booking opportunity";
      };
    };

    // Savings verification
    verification: {
      SELF_REPORTED: "Customer updates savings amount manually";
      UPI_TRACKED: "Customer links UPI for automatic tracking (optional)";
      DEPOSIT_WITH_AGENCY: "Customer deposits directly with agency (most reliable)";
    };
  };
}

// ── Savings tracking dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  My Trip Savings — Singapore Family Trip                  │
// │                                                       │
// │  ₹1,40,000 / ₹2,30,000  (61%)  ████████████████████░░░░│
// │                                                       │
// │  Monthly target: ₹27,143                                │
// │  This month: ₹30,000 ✅ Ahead of target                  │
// │                                                       │
// │  Timeline:                                             │
// │  Jun ██████ Jul ██████ Aug ██████ Sep ██████            │
// │  Oct ██████ Nov ██████ Dec ✈️                            │
// │  ↑ You are here (Aug)                                   │
// │                                                       │
// │  Projected completion: Nov 15 ✅ (2 weeks early!)        │
// │  Current package price: ₹2.23L (stable)                 │
// │                                                       │
// │  Next milestone: 75% (₹1,72,500) — ₹32,500 away        │
// │                                                       │
// │  💡 Tip: Add ₹8,000 more this month to hit 75% by Sep 1│
// │                                                       │
// │  [Add Savings] [View Itinerary Ideas] [Adjust Plan]      │
// └─────────────────────────────────────────────────────┘
```

### Budget Optimization Suggestions

```typescript
interface BudgetOptimization {
  // Help customers optimize their trip budget
  optimizations: {
    TIMING_FLEXIBILITY: {
      suggestion: "Shift travel from Dec to Jan and save ₹18,000";
      reasoning: "January is shoulder season — lower flight + hotel prices";
      impact: "₹2,30,000 → ₹2,12,000 (already within savings!)";
      tradeoff: "Slightly cooler weather, fewer crowds (actually a plus)";
    };

    COMPONENT_SWAP: {
      suggestion: "Switch to 3-star hotel and save ₹12,500";
      reasoning: "Village Hotel has family pool and great reviews at lower price";
      impact: "₹2,30,000 → ₹2,17,500";
      tradeoff: "Smaller rooms but family-friendly amenities";
    };

    ACTIVITY_OPTIMIZATION: {
      suggestion: "Replace paid activity with free alternatives";
      reasoning: "Gardens by the Bay outdoor gardens are free (paid conservatory optional)";
      impact: "Saves ₹2,400";
      tradeoff: "Skip conservatory but see the Supertrees (main attraction)";
    };

    MEAL_PLAN: {
      suggestion: "Include breakfast in hotel (₹3,500 extra vs ₹8,000 food court)";
      reasoning: "Hotel breakfast saves time and money vs. eating out every morning";
      impact: "Net saving of ₹4,500 on breakfasts";
      tradeoff: "Less variety but convenience with kids";
    };

    BOOKING_WINDOW: {
      suggestion: "Book flights by Sep 30 for early bird pricing";
      reasoning: "Flights are ₹28K now but typically ₹35K+ after October";
      impact: "Locks ₹28K × 4 = ₹1,12,000 (saves ₹28,000 total)";
      tradeoff: "Non-refundable advance payment needed";
    };
  };
}

// ── Budget optimizer ──
// ┌─────────────────────────────────────────────────────┐
// │  Budget Optimizer                                         │
// │  Current budget: ₹2,30,000 · Your savings: ₹1,40,000    │
// │  Gap: ₹90,000                                            │
// │                                                       │
// │  Suggestions to bridge the gap:                        │
// │                                                       │
// │  1. 📅 Shift to January      -₹18,000                  │
// │     Shoulder season, fewer crowds                        │
// │     [Apply]                                             │
// │                                                       │
// │  2. 🏨 Switch to Village Hotel -₹12,500                │
// │     Family-friendly, pool, great reviews                 │
// │     [Apply]                                             │
// │                                                       │
// │  3. ✈️ Book flights by Sep 30  -₹28,000 (guaranteed)  │
// │     Lock early bird pricing before Oct hike              │
// │     [Apply]                                             │
// │                                                       │
// │  If all applied: ₹2,30,000 → ₹1,71,500                  │
// │  Your savings: ₹1,40,000 + ₹31,500 remaining            │
// │  ✅ You can book this trip NOW with the savings you have! │
// │                                                       │
// │  [Apply All Optimizations] [Customize Budget]             │
// └─────────────────────────────────────────────────────┘
```

### Readiness Detection & Booking Trigger

```typescript
interface ReadinessDetection {
  // Detect when customer is ready to book
  signals: {
    FINANCIAL_READINESS: {
      signal: "Savings ≥ 80% of estimated budget";
      weight: 40;
    };

    ENGAGEMENT_READINESS: {
      signal: "Customer has viewed 3+ itineraries or opened proposal";
      weight: 25;
    };

    TIMING_READINESS: {
      signal: "Travel date is within 90 days or customer has set firm dates";
      weight: 20;
    };

    BEHAVIORAL_READINESS: {
      signal: "Customer asking specific questions (visa, hotel, activities)";
      weight: 15;
    };
  };

  readiness_score: {
    formula: "weighted_sum(signals)";
    thresholds: {
      COLD: { range: "0-30", action: "Inspiration content only" };
      WARM: { range: "30-60", action: "Send itineraries and pricing" };
      HOT: { range: "60-80", action: "Agent creates personalized proposal" };
      READY: { range: "80-100", action: "Urgent: book now before prices change" };
    };
  };
}

// ── Readiness detection ──
// ┌─────────────────────────────────────────────────────┐
// │  Customer Readiness Score                                 │
// │                                                       │
// │  Customer: Sharma family · Singapore · Dec 2026          │
// │                                                       │
// │  Readiness: 72/100 🔥 HOT                                │
// │                                                       │
// │  Signals:                                             │
// │  💰 Financial:  80%  Savings at 61% of budget (weighted) │
// │  📋 Engagement: 75%  Viewed 4 itineraries this week      │
// │  📅 Timing:     60%  Dec travel, 4 months out            │
// │  💬 Behavior:   70%  Asked about visa process            │
// │                                                       │
// │  Recommended action:                                   │
// │  → Agent creates personalized proposal THIS WEEK         │
// │  → Share 2 hotel options + activity selection            │
// │  → Offer price lock for 48 hours                        │
// │                                                       │
// │  Risk: If we wait, customer may book with competitor     │
// │  (searching "Singapore packages" actively)                │
// │                                                       │
// │  [Create Proposal] [Assign Agent] [Send Price Lock]      │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Savings verification** — Customers may over-report savings. Need to balance trust with verification. Agency deposit is most reliable but requires customer commitment.

2. **Price lock risk** —Locking package prices for 6 months exposes agency to supplier rate increases. Need to price the lock-in appropriately (₹5K deposit + 3% price buffer).

3. **Engagement without spam** — Monthly savings updates are useful but weekly pings feel like nagging. Need to calibrate frequency based on customer engagement level.

4. **Abandoned savings goals** — What happens when customer stops saving? Need graceful re-engagement (offer cheaper alternatives, different dates, or different destinations).

---

## Next Steps

- [ ] Build trip savings goal engine with budget estimator
- [ ] Create automated savings tracking with milestone engagement
- [ ] Implement budget optimization suggestion engine
- [ ] Design readiness detection with booking trigger workflow
