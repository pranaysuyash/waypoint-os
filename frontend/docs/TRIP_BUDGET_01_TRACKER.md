# Trip Budget Management — Real-Time Tracking & Alerts

> Research document for real-time trip budget tracking, expense categorization, budget alerts during travel, spend analytics, and post-trip budget reconciliation for the Waypoint OS platform.

---

## Key Questions

1. **How do travelers track spending against budget during a trip?**
2. **What expense categorization works for travel spending?**
3. **How do budget alerts prevent overspending while traveling?**
4. **How does post-trip budget analysis improve future planning?**

---

## Research Areas

### Real-Time Trip Budget Tracker

```typescript
interface TripBudgetTracker {
  // Budget tracking for travelers during their trip
  budget_setup: {
    PRE_TRIP: {
      total_budget: number;                     // overall trip budget
      categories: {
        prepaid: {
          description: "Already paid to agency (package, flights, hotel)";
          tracking: "Fixed amount — deducted from budget at trip start";
          examples: ["Flight tickets", "Hotel stay", "Package activities", "Transfers"];
        };

        daily_allowance: {
          description: "Per-day spending budget for variable expenses";
          amount_per_day: number;
          examples: ["Meals", "Local transport", "Shopping", "Tips"];
          tracking: "Running total vs. daily budget";
        };

        activity_fund: {
          description: "Budget for optional/add-on activities";
          amount: number;
          examples: ["Spa treatments", "Premium excursions", "Water sports", "Nightlife"];
          tracking: "Drawdown from fixed activity fund";
        };

        shopping_budget: {
          description: "Separate allocation for shopping";
          amount: number;
          examples: ["Souvenirs", "Clothes", "Electronics", "Gifts"];
          tracking: "Separate tracking to prevent shopping from eating into daily allowance";
        };

        emergency_reserve: {
          description: "Untouchable reserve for emergencies";
          amount: number;
          access: "Only for medical, lost documents, or urgent travel changes";
          note: "Remaining reserve returned to traveler post-trip";
        };
      };
    };
  };

  // Expense capture
  expense_capture: {
    METHODS: {
      MANUAL_ENTRY: {
        description: "Traveler enters expense manually in app";
        fields: ["Amount", "Currency", "Category", "Note", "Photo of receipt"];
        time: "30 seconds per entry";
        friction: "Travelers forget or delay entry";
      };

      PHOTO_RECEIPT: {
        description: "Take photo of receipt → OCR extracts amount and merchant";
        fields: "Auto-extracted: amount, merchant, date";
        time: "10 seconds (snap photo)";
        accuracy: "80-90% (better for printed receipts, poor for handwritten)";
      };

      SMS_BANK_CAPTURE: {
        description: "Auto-capture from bank SMS alerts";
        mechanism: "Read bank transaction SMS → extract amount and merchant";
        advantage: "Zero-effort capture";
        limitation: "Only works for card transactions, not cash";
        privacy: "Requires SMS read permission (sensitive — optional feature)";
      };

      AGENT_ASSISTED: {
        description: "Traveler sends expense photo via WhatsApp to agent";
        mechanism: "Agent enters into system on behalf of traveler";
        use_case: "Less tech-savvy travelers (seniors, parents)";
        cost: "Agent time — justified for premium packages";
      };
    };
  };
}

// ── Trip budget tracker (traveler view) ──
// ┌─────────────────────────────────────────────────────┐
// │  Trip Budget — Singapore Day 3 of 5                       │
// │                                                       │
// │  Overall: ₹1,20,000 budget · ₹68,000 spent (57%)        │
// │  ████████████░░░░░░░░  ₹52,000 remaining                  │
// │                                                       │
// │  Breakdown:                                           │
// │  ✅ Prepaid (package): ₹75,000 — Already covered         │
// │  🍽️ Daily allowance: ₹6,000/day                          │
// │     Day 1: ₹4,200 ✅  Day 2: ₹5,800 ✅  Day 3: ₹1,200 🔵│
// │     Daily avg: ₹3,733 · On track ✅                      │
// │  🎯 Activity fund: ₹15,000                               │
// │     Sentosa: ₹3,500 · Night Safari: ₹2,000              │
// │     Remaining: ₹9,500                                     │
// │  🛍️ Shopping: ₹10,000                                    │
// │     Orchard Road: ₹4,200 · Bugis: ₹1,800                │
// │     Remaining: ₹4,000 ⚠️ (60% spent in 3 days)          │
// │  🚨 Emergency: ₹10,000 — Untouched ✅                    │
// │                                                       │
// │  Today's spending: ₹1,200 (lunch + MRT)              │
// │  [Add Expense] [Snap Receipt] [Budget Settings]           │
// │                                                       │
// │  ⚠️ Shopping alert: You've used 60% of shopping          │
// │  budget in 3 days. ₹4,000 left for 2 more days.         │
// │  [Adjust Budget] [Ignore]                                 │
// └─────────────────────────────────────────────────────┘
```

### Budget Alerts & Intelligence

```typescript
interface BudgetAlerts {
  // Proactive budget management alerts
  alert_rules: {
    DAILY_OVERSPEND: {
      trigger: "Daily spending exceeds daily allowance";
      timing: "Real-time when expense entered";
      message: "Today's spending: ₹{amount}. Daily budget: ₹{budget}. ₹{over} over budget.";
      action: "Option to reallocate from another category or reduce tomorrow's budget";
    };

    CATEGORY_DEPLETION: {
      trigger: "Category budget >75% spent with >40% of trip remaining";
      message: "You've spent {pct}% of {category} budget with {days} days remaining.";
      suggestions: ["Reduce spending in this category", "Reallocate from another category", "Add more budget"];
    };

    PACE_WARNING: {
      trigger: "Overall spending pace exceeds budget pace by >20%";
      calculation: "If at day 3 of 5, should have spent ~60%. At 75%? Alert.";
      message: "At this pace, you'll exceed budget by ₹{amount}. Consider adjusting.";
    };

    EMERGENCY_RESERVE_TOUCH: {
      trigger: "Attempt to log expense against emergency reserve";
      message: "This would use your emergency reserve. Confirm this is an emergency expense?";
      confirmation: "Yes, this is emergency | No, reassign category";
    };

    CURRENCY_OVERSIGHT: {
      trigger: "Expense entered in foreign currency with unfavorable conversion";
      message: "₹{amount} at {rate}. Current market rate: {market_rate}. Consider paying by card for better rates.";
    };
  };

  // Post-trip budget analysis
  post_trip_analysis: {
    SPENDING_SUMMARY: {
      total_budget: number;
      total_spent: number;
      variance: number;                          // positive = under budget, negative = over
      category_breakdown: Map<string, { budget: number; actual: number; variance: number }>;
    };

    INSIGHTS: {
      biggest_saving: "You saved ₹8,500 on meals by eating at hawker centers instead of restaurants";
      biggest_overspend: "Shopping exceeded budget by ₹3,200 (mainly electronics at Sim Lim Square)";
      daily_average: "Average daily spend: ₹4,100 (budget: ₹5,000)";
      recommendation: "For your next Singapore trip, allocate ₹4,500/day (realistic) and ₹12,000 shopping";
    };

    FUTURE_PLANNING: {
      description: "Use actual trip spending to improve budget estimates for future trips";
      mechanism: "Compare estimated vs. actual per category → adjust templates";
      benefit: "Budget estimates improve with each trip, making future proposals more accurate";
    };
  };
}

// ── Post-trip budget report ──
// ┌─────────────────────────────────────────────────────┐
// │  Budget Report — Singapore Trip · Completed               │
// │                                                       │
// │  Budget vs Actual:                                    │
// │  Category    │ Budget  │ Actual │ Variance │ %        │
// │  ─────────────────────────────────────────────────────── │
// │  Package     │ ₹75,000│ ₹75,000│      ₹0  │  0%     │
// │  Daily spend │ ₹30,000│ ₹24,600│  +₹5,400 │ +18%    │
// │  Activities  │ ₹15,000│ ₹13,200│  +₹1,800 │ +12%    │
// │  Shopping    │ ₹10,000│ ₹13,200│  -₹3,200 │ -32%    │
// │  Emergency   │ ₹10,000│     ₹0 │ +₹10,000 │ +100%   │
// │  ─────────────────────────────────────────────────────── │
// │  TOTAL       │₹1,40,000│₹1,26,000│+₹14,000│ +10%     │
// │                                                       │
// │  Trip came in ₹14,000 UNDER budget ✅                    │
// │                                                       │
// │  Key Insights:                                        │
// │  📉 Meals were 30% cheaper than estimated (hawker ftw!)   │
// │  📈 Shopping went over — electronics at Sim Lim           │
// │  ✅ Activity budget was accurate                           │
// │  ✅ Emergency reserve untouched — good planning            │
// │                                                       │
// │  Save for future planning:                             │
// │  [Save as Template] [Share with Agent]                     │
// │                                                       │
// │  Next trip suggestion:                                │
// │  Based on your spending, recommend ₹1.1L budget          │
// │  for similar 5-day Singapore trip (more accurate)         │
// │  [Plan Next Trip]                                          │
// └─────────────────────────────────────────────────────┘
```

### Multi-Currency Expense Tracking

```typescript
interface MultiCurrencyTracking {
  // Handle expenses in multiple currencies during international trips
  currency_handling: {
    BASE_CURRENCY: "INR (Indian Rupees) — all budgets and reports in INR";
    SPENDING_CURRENCIES: ["SGD (Singapore)", "USD (Universal)", "THB (Thailand)", "AED (Dubai)", "EUR (Europe)"];

    conversion: {
      real_time_rate: "Use live forex rate at time of expense entry";
      rate_source: "RBI reference rate or xe.com API";
      rounding: "Round to nearest ₹10 for display; store exact for calculations";
      card_transactions: "Use bank's actual conversion rate from statement (more accurate)";
      cash_transactions: "Use rate at time of withdrawal or exchange";
    };

    forex_optimization: {
      tip_1: "Pay by international debit/credit card for better rates than cash exchange";
      tip_2: "Withdraw local currency from ATMs in larger amounts to reduce per-withdrawal fees";
      tip_3: "Use forex card for locked-in rates (better than credit card markup)";
      tip_4: "Avoid airport currency exchange (worst rates, 5-10% markup)";
      tip_5: "Track all expenses in INR to see real cost — foreign amounts hide the true spend";
    };
  };
}
```

---

## Open Problems

1. **Expense capture friction** — Travelers on vacation don't want to log expenses. The photo-receipt method (snap and forget) has highest compliance, but OCR accuracy varies. Need to minimize input while maximizing capture.

2. **Cash vs. card tracking** — Cash spending is hardest to track (no digital trail). Travelers often forget cash expenses entirely, making budget tracking inaccurate. May need end-of-day cash reconciliation prompt.

3. **Shared trip budgets** — When couples or groups share expenses, tracking "who paid for what" adds complexity. Need shared budget mode with individual contribution tracking.

4. **Offline expense entry** — Travelers may not have data connectivity when spending (especially on activities/tours). Need offline expense entry that syncs when connected.

---

## Next Steps

- [ ] Build trip budget setup wizard with category allocation
- [ ] Implement expense capture with photo receipt OCR
- [ ] Create real-time budget alerts with category-specific thresholds
- [ ] Design post-trip budget analysis with future planning recommendations
