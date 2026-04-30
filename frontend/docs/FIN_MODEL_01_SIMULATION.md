# Financial Modeling & Simulation — Revenue, Margin & ROI Engine

> Research document for financial modeling, revenue simulation, dynamic pricing simulation, profit margin modeling, ROI calculators, break-even analysis, and financial scenario planning for the Waypoint OS platform.

---

## Key Questions

1. **How do we model and simulate agency financial performance?**
2. **What scenarios should the financial model support?**
3. **How does dynamic pricing simulation work?**
4. **What ROI calculators are needed for agents and owners?**

---

## Research Areas

### Financial Modeling Architecture

```typescript
interface FinancialModelingSimulation {
  // Revenue, margin, and scenario modeling for travel agency
  model_components: {
    REVENUE_MODEL: {
      description: "Multi-stream revenue projection";
      streams: {
        PACKAGE_BOOKINGS: {
          formula: "Units × Average Selling Price × (1 - Cancellation Rate)";
          variables: {
            units: "Number of trip packages sold per month (by destination, by tier)";
            asp: "Average selling price per package (trending over time)";
            cancellation_rate: "Historical cancellation rate by destination and advance-purchase window";
            seasonality_factor: "Monthly multiplier (peak months 1.5-2x, off-peak 0.5-0.8x)";
          };
        };

        ANCILLARY_REVENUE: {
          components: ["Visa processing fees", "Travel insurance commissions", "Forex margin", "In-trip upsells", "Activity add-ons"];
          formula: "Per-booking ancillary revenue × total bookings";
          margin: "Higher margin than base bookings (40-70%)";
        };

        SERVICE_FEES: {
          components: ["Consultation fees (premium)", "Document processing", "Airport assistance", "Special requests"];
          model: "Fixed fee per service × volume";
        },
      };
      projection: "Monthly revenue = (Package + Ancillary + Service) × seasonality factor";
    };

    COST_MODEL: {
      description: "Fixed and variable cost projection";
      costs: {
        FIXED: {
          items: ["Office rent", "Staff salaries (base)", "Platform subscription", "Insurance premiums", "Internet/phone", "Marketing retainers"];
          model: "Monthly fixed regardless of booking volume";
        };

        VARIABLE: {
          items: ["Supplier payments (flights, hotels, activities)", "Marketing spend (performance)", "Payment gateway fees (1.5-2.5%)", "Agent commissions (8-15% of margin)", "WhatsApp API costs", "Customer support costs"];
          model: "Per-booking variable cost × booking volume";
          key_ratio: "COGS should be 70-80% of revenue; gross margin 20-30%";
        };
      };
    };

    PROFIT_MODEL: {
      formula: "Net Profit = Revenue - Fixed Costs - Variable Costs";
      margins: {
        gross_margin: "Revenue minus supplier payments (target: 20-30%)";
        operating_margin: "Gross margin minus operating costs (target: 12-18%)";
        net_margin: "After all costs including taxes (target: 8-12%)";
      };
    };
  };

  // ── Financial model dashboard ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Financial Model · FY2026-27 Simulation                    │
  // │                                                       │
  // │  Revenue Projection:                                  │
  // │  Package bookings:  ₹2.4Cr (200 trips × ₹1.2L avg)     │
  // │  Ancillary revenue:  ₹36L (15% of booking revenue)      │
  // │  Service fees:        ₹12L                              │
  // │  Total revenue:       ₹2.88Cr                           │
  // │                                                       │
  // │  Cost Projection:                                     │
  // │  Supplier payments:  ₹2.02Cr (70% of package revenue)   │
  // │  Fixed costs:         ₹42L (rent, salaries, platform)    │
  // │  Variable costs:      ₹24L (marketing, commissions)      │
  // │  Total costs:         ₹2.68Cr                           │
  // │                                                       │
  // │  Profit:                                              │
  // │  Gross margin:  ₹78L (27.1%)                            │
  // │  Net margin:    ₹20L (6.9%)  ⚠️ Below 8% target        │
  // │                                                       │
  // │  Scenario levers:                                     │
  // │  Trips/month:    [15] [20] [25] [30]                    │
  // │  Avg selling price: [₹1.0L] [₹1.2L] [₹1.5L]           │
  // │  Gross margin:    [22%] [25%] [28%]                     │
  // │  Marketing spend: [₹15K/mo] [₹25K/mo] [₹40K/mo]       │
  // │                                                       │
  // │  [Run Simulation] [Compare Scenarios] [Export Model]      │
  // └─────────────────────────────────────────────────────────┘
}
```

### Scenario Simulation Engine

```typescript
interface ScenarioSimulation {
  // What-if modeling for business decisions
  scenarios: {
    GROWTH_SCENARIO: {
      description: "What happens if we increase bookings by 30%?";
      model: {
        revenue: "30% more bookings × same ASP = 30% more revenue";
        costs: "Variable costs increase 30% (more supplier payments, commissions)";
        fixed: "Fixed costs may need to increase (hire 1-2 more agents, bigger office?)";
        net_impact: "Revenue +30%, Variable +30%, Fixed +10-15% → Net margin improves (operating leverage)";
        investment: "Additional ₹2-3L/month in marketing to generate 30% more inquiries";
        roi: "₹24-36L additional marketing → ₹86L additional revenue (2.4x-3.6x ROI)";
      };
    };

    PRICING_SCENARIO: {
      description: "What happens if we increase package prices by 10%?";
      model: {
        revenue: "Same bookings × 10% higher ASP = 10% more revenue";
        demand_impact: "Price elasticity: 10% price increase → ~5% fewer bookings (estimated)";
        net_revenue: "+10% × -5% = +4.5% net revenue increase";
        margin: "Higher price with same cost → margin improves from 25% to 32%";
        risk: "If demand drops >8%, total revenue declines despite higher prices";
      };
    };

    MARGIN_SCENARIO: {
      description: "What happens if we negotiate better supplier rates (5% savings)?";
      model: {
        cogs_reduction: "5% lower supplier costs → COGS drops from 75% to 72%";
        margin_impact: "Gross margin improves from 25% to 28% at same selling price";
        profit_impact: "₹2.4Cr revenue × 3% margin improvement = ₹7.2L more profit";
        alternative: "Pass savings to customer: 5% lower prices → more competitive → more bookings";
      };
    };

    NEW_DESTINATION_SCENARIO: {
      description: "What happens if we add Japan as a new destination?";
      model: {
        market_research: "Japan outbound from India: 50K+ travelers/year, growing 25% YoY";
        investment: "Agent training (₹50K), supplier relationships (₹30K), marketing (₹2L)";
        revenue_potential: "20 Japan trips/year × ₹2L ASP = ₹40L additional revenue";
        margin: "Higher-margin destination (25-30% vs. 20-25% for Southeast Asia)";
        payback: "₹2.8L investment → ₹40L revenue × 25% margin = ₹10L profit. Payback: 4 months";
      };
    };

    SEASONAL_SCENARIO: {
      description: "What happens if monsoon season revenue drops 50%?";
      model: {
        revenue_drop: "July-August revenue: ₹8L → ₹4L (50% drop)";
        fixed_costs: "Still ₹3.5L/month (rent, salaries, platform)";
        impact: "2 months × ₹4L shortfall = ₹8L seasonal cash gap";
        mitigation: "Off-season campaigns + pilgrimage travel + visa processing services";
        cash_reserve: "Need ₹10-15L cash reserve to cover seasonal shortfalls";
      };
    };
  };

  simulation_engine: {
    inputs: [
      "Monthly booking volume (by destination)",
      "Average selling price (by destination and tier)",
      "Gross margin percentage (by destination)",
      "Fixed costs (monthly)",
      "Variable cost ratios",
      "Seasonality multipliers (monthly)",
      "Marketing spend (monthly)",
      "Cancellation rates",
      "Repeat customer rate",
    ];
    outputs: [
      "Monthly and annual revenue projection",
      "Monthly and annual profit projection",
      "Cash flow projection (12 months)",
      "Break-even analysis (bookings needed to cover costs)",
      "Margin sensitivity analysis",
      "ROI on marketing spend",
      "Payback period for investments",
    ];
  };
}
```

### Dynamic Pricing Simulation

```typescript
interface DynamicPricingSimulation {
  // Simulate pricing strategies before deploying
  pricing_simulator: {
    INPUTS: {
      base_cost: "Supplier cost for the package (flights + hotel + activities)";
      current_margin: "Current margin percentage";
      competitor_prices: "Prices of similar packages from competitors";
      demand_signal: "Demand level for the route/dates (low/medium/high/peak)";
      booking_velocity: "How fast bookings are coming in vs. historical average";
      advance_purchase: "How far in advance the booking is";
    };

    SIMULATION_RULES: {
      PEAK_DEMAND: {
        condition: "Demand > 80% of capacity AND booking velocity above average";
        action: "Increase margin by 3-5%; no discounts; urgency messaging";
        simulation: "Show projected revenue and bookings at higher price";
      };

      LOW_DEMAND: {
        condition: "Demand < 40% of capacity AND departure < 30 days";
        action: "Reduce margin by 2-3%; offer flash discount; value-add instead of price cut";
        simulation: "Show revenue with lower price × more bookings vs. higher price × fewer bookings";
      };

      COMPETITOR_UNDERCUT: {
        condition: "Competitor offering similar package at 10%+ lower price";
        action: "Match or differentiate (add value — free insurance, room upgrade) instead of pure price match";
        simulation: "Revenue at matched price vs. revenue at higher price with value-adds";
      };

      EARLY_BIRD: {
        condition: "Booking > 90 days before departure";
        action: "Offer 5-10% discount for early commitment (locks inventory, reduces risk)";
        simulation: "Revenue from early bookings at discount vs. waiting for full-price last-minute";
      };
    };

    // ── Pricing simulator — agent view ──
    // ┌─────────────────────────────────────────────────────┐
    // │  Pricing Simulator · Singapore 5D/4N                      │
    // │                                                       │
    // │  Base cost (suppliers): ₹88,000                         │
    // │  Current selling price: ₹1,20,000                       │
    // │  Current margin: ₹32,000 (26.7%)                        │
    // │                                                       │
    // │  Simulate:                                            │
    // │  Selling price: [₹1,10,000] [₹1,20,000] [₹1,35,000]    │
    // │                                                       │
    // │  At ₹1,10,000 (discounted):                           │
    // │  Margin: ₹22,000 (20.0%)                                │
    // │  Estimated bookings: +15% (price-sensitive customers)    │
    // │  Total margin: ₹22K × 1.15 = ₹25.3K per trip            │
    // │  Revenue impact: -₹6.7K per trip × more trips            │
    // │                                                       │
    // │  At ₹1,35,000 (premium):                              │
    // │  Margin: ₹47,000 (34.8%)                                │
    // │  Estimated bookings: -10% (some price resistance)        │
    // │  Total margin: ₹47K × 0.90 = ₹42.3K per trip            │
    // │  Revenue impact: +₹10.3K per trip × fewer trips          │
    // │                                                       │
    // │  Recommendation: Premium pricing at ₹1,35,000           │
    // │  Reason: Peak season demand absorbs price increase       │
    // │                                                       │
    // │  [Apply Premium] [Keep Current] [Show Competitor Data]    │
    // └─────────────────────────────────────────────────────────┘
  };
}
```

### ROI Calculator & Break-Even Analysis

```typescript
interface ROICalculator {
  // ROI calculators for different business decisions
  calculators: {
    MARKETING_ROI: {
      description: "ROI on marketing spend by channel";
      formula: "(Revenue from channel - Marketing spend) / Marketing spend × 100";
      example: "₹50K WhatsApp ads → 25 inquiries → 8 bookings → ₹9.6L revenue → ROI: 1,820%";
      tracking: "UTM parameters + inquiry source + booking attribution";
    };

    AGENT_ROI: {
      description: "Revenue generated per agent vs. total agent cost";
      formula: "(Agent revenue - Agent cost) / Agent cost × 100";
      components: {
        agent_revenue: "Total booking revenue attributed to agent";
        agent_cost: "Base salary + commission + desk cost + training";
      };
      target: "Agent ROI > 300% (i.e., agent generates 4x their cost in revenue)";
      example: "Agent costs ₹60K/month → generates ₹2.4L revenue → ROI: 300%";
    };

    NEW_DESTINATION_ROI: {
      description: "Payback analysis for launching a new destination";
      formula: "Investment / Monthly profit from new destination = Payback months";
      example: "₹3L investment (training + marketing + supplier setup) / ₹2L monthly profit = 1.5 months";
    };

    BREAK_EVEN_ANALYSIS: {
      description: "How many bookings needed to cover fixed costs";
      formula: "Fixed costs / Gross margin per booking = Break-even bookings";
      example: "₹3.5L monthly fixed / ₹25K margin per booking = 14 bookings/month to break even";
      visualization: "Chart showing: X bookings at current pace vs. break-even line";
    };

    PLATFORM_INVESTMENT_ROI: {
      description: "ROI on the Waypoint OS platform itself";
      formula: "(Revenue increase + Cost savings from platform) / Platform cost × 100";
      savings: [
        "Agent time saved: 2-4 hours/agent/day × hourly cost",
        "Error reduction: fewer booking mistakes → fewer claims",
        "Customer retention: repeat booking rate improvement",
        "Upsell revenue: in-trip upsells enabled by platform",
      ];
    };
  };
}
```

---

## Open Problems

1. **Garbage in, garbage out** — Financial models are only as good as the input assumptions. Small agencies with limited historical data may have unreliable baseline assumptions, leading to inaccurate projections.

2. **External shocks** — Financial models assume stable conditions. A pandemic, currency crash, or airline bankruptcy invalidates all projections. Scenario modeling helps but can't predict black swans.

3. **Price elasticity estimation** — "If we raise prices 10%, how many bookings do we lose?" requires historical A/B testing data that most agencies don't have. Estimated elasticity is a guess, not a fact.

4. **Cash flow vs. profit timing** — Revenue is recognized when the trip happens, but costs (marketing, salaries) are incurred months before. Cash flow modeling is more critical than profit modeling for agency survival.

5. **Model complexity vs. usability** — A financial model with 50 input variables is accurate but unusable. A model with 5 variables is usable but may miss important dynamics. Need tiered complexity: simple view for owners, detailed view for finance.

---

## Next Steps

- [ ] Build financial model with revenue, cost, and profit projections
- [ ] Create scenario simulation engine with what-if analysis
- [ ] Implement dynamic pricing simulator with demand-based rules
- [ ] Design ROI calculators for marketing, agents, and new destinations
- [ ] Build break-even analysis tool with cash flow projection
