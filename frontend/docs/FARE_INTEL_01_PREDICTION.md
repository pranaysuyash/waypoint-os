# Flight Fare Intelligence — Price Prediction & Alerts

> Research document for flight fare intelligence, AI-powered price prediction, buy-now-vs-wait recommendations, fare alert systems, and booking timing optimization for the Waypoint OS platform.

---

## Key Questions

1. **How do we predict whether flight fares will rise or fall?**
2. **When should we advise customers to book vs. wait?**
3. **How do fare alerts keep customers engaged during planning?**
4. **What data sources drive accurate fare prediction?**

---

## Research Areas

### Fare Intelligence Engine

```typescript
interface FareIntelligenceEngine {
  // AI-powered flight fare prediction and timing optimization
  data_sources: {
    HISTORICAL_FARES: {
      description: "Past fare data for route-date combinations";
      sources: [
        "GDS historical fare archives (Amadeus, Sabre)",
        "Third-party fare history APIs (Skyscanner, Kayak, ATPCO)",
        "Own booking data (prices at which previous bookings were made)",
      ];
      granularity: "Route × airline × day-of-week × advance-purchase × season";
      retention: "3+ years of historical data for seasonal pattern detection";
    };

    LIVE_FARE_FEEDS: {
      description: "Real-time fare availability and pricing";
      sources: [
        "GDS live search (Amadeus Bargain Finder, Sabre API)",
        "Airline direct API fares (IndiGo, SpiceJet, Air India)",
        "NDC offers (personalized airline pricing)",
        "Meta-search APIs (Skyscanner, Google Flights)",
      ];
      refresh_rate: "Every 4 hours for monitored routes; on-demand for specific queries";
    };

    EXTERNAL_SIGNALS: {
      description: "Factors that influence fare movements";
      signals: [
        "Fuel price trends (jet fuel costs impact fares within 2-4 weeks)",
        "Seasonal demand patterns (school holidays, festivals, long weekends)",
        "Competitor airline route changes (new routes, frequency changes)",
        "Event calendar (conferences, sports events driving demand spikes)",
        "Currency exchange rates (INR vs. USD/SGD/THB affects international fares)",
        "Airline sale announcements (monitored via email and social media)",
      ];
    };
  };

  prediction_model: {
    APPROACH: {
      description: "Ensemble model combining multiple prediction methods";
      components: {
        seasonal_model: "Same route, same month, historical fare distribution — captures predictable seasonal patterns";
        advance_purchase_model: "Fare trajectory as departure date approaches — when do prices typically start rising?";
        demand_forecast: "Predicted demand based on events, holidays, school calendars";
        anomaly_detection: "Detect unusual fare drops (mistake fares, flash sales) for immediate alert";
      };
    };

    OUTPUT: {
      recommendation: {
        BOOK_NOW: {
          condition: "Current fare is below historical median AND trending up AND within optimal booking window";
          confidence: "85-92% accurate for 30-90 day predictions";
          message: "🔥 Book now — fares for this route typically rise 15-20% in the next 2 weeks";
        };

        WAIT: {
          condition: "Current fare is above historical median AND no demand spike expected AND far from departure";
          confidence: "70-80% accurate — riskier prediction as fares can spike unexpectedly";
          message: "⏳ Fares are slightly high right now. Historically, better prices appear 3-4 weeks before your dates";
        };

        MONITOR: {
          condition: "Fare is near historical average — could go either way";
          confidence: "N/A — no strong signal";
          message: "📊 Fares are average for this route. I'll set up an alert and notify you if they drop";
        };

        ACT_NOW: {
          condition: "Anomaly detected — fare significantly below historical range (possible mistake fare or flash sale)";
          confidence: "95%+ that this is an unusually low fare";
          message: "🚨 Unusual fare drop detected! This price is 40% below normal — book within 24 hours before it's gone";
        };
      };
    };
  };

  // ── Fare intelligence — agent dashboard ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Fare Intelligence · DEL → SIN · June 15-20               │
  // │                                                       │
  // │  Current Best Fares:                                  │
  // │  ✈️ IndiGo 6E-37 · ₹18,500 (round trip)                  │
  // │  ✈️ Air India AI-381 · ₹24,200 (round trip)               │
  // │  ✈️ Singapore Airlines SQ-403 · ₹38,500 (round trip)      │
  // │                                                       │
  // │  AI Recommendation: 🔥 BOOK NOW                          │
  // │  IndiGo ₹18,500 is 22% below historical average          │
  // │  for this route in June. Fares typically rise 15%+        │
  // │  when school holidays start (May 25).                     │
  // │                                                       │
  // │  Fare Trend (90 days):                                │
  // │  ₹28K ┤                                               │
  // │  ₹24K ┤    ╭──╮                                       │
  // │  ₹20K ┤───╯  ╰──₹18.5K ● (current)                    │
  // │  ₹16K ┤                                               │
  // │       └──┬──┬──┬──┬──┬──┬──→                          │
  // │        Mar Apr May Jun Jul Aug                          │
  // │                                                       │
  // │  Optimal booking window: Mar 15 - May 1                   │
  // │  Risk of waiting: High (school holidays drive fares up)   │
  // │                                                       │
  // │  [Book IndiGo ₹18,500] [Set Fare Alert] [Show Alternates] │
  // └─────────────────────────────────────────────────────────┘
}
```

### Fare Alert System

```typescript
interface FareAlertSystem {
  // Automated fare monitoring and customer notifications
  alert_types: {
    PRICE_DROP_ALERT: {
      trigger: "Monitored fare drops below customer's threshold";
      channel: "WhatsApp (primary) + email (secondary)";
      template: `
        💸 Fare Drop Alert!

        {route} on {date}
        Was: ₹{previous_price}
        Now: ₹{new_price} (↓{drop_pct}%)

        This is {below_above} your budget of ₹{target}.
        Book now before it goes back up!

        [Book Now] [Keep Watching]
      `;
    };

    OPTIMAL_WINDOW_ALERT: {
      trigger: "Route enters historically optimal booking window";
      template: `
        📅 Best Time to Book Alert

        Flights for {destination} in {month} are entering the optimal booking window.
        Historically, the best prices appear {weeks} weeks before departure.

        Current best: ₹{current_price}
        Our prediction: Book within the next {days} days

        [Search Flights] [Set Target Price]
      `;
    };

    FLASH_SALE_ALERT: {
      trigger: "Anomaly detected — unusual fare drop or airline sale";
      priority: "HIGH — send immediately, bypass quiet hours";
      template: `
        🚨 Flash Fare — Book Within 24 Hours!

        {airline} just dropped {route} to ₹{price}
        That's {discount}% below normal!

        Travel dates: {dates}
        Availability: Very limited (showing {seats} seats left)

        [Book Now — ₹{price}] [Too Good — Show Me]
      `;
    };

    PREDICTION_UPDATE: {
      trigger: "AI prediction changes (e.g., from WAIT to BOOK_NOW)";
      template: `
        📊 Fare Update for Your {destination} Trip

        Our previous advice: Wait
        Updated advice: 📕 Book within this week

        Reason: Fares have started their seasonal upward trend.
        Current: ₹{price} · Expected in 2 weeks: ₹{projected_price}

        [Book at ₹{price}] [I'll Wait]
      `;
    };
  };

  customer_engagement: {
    TARGET_PRICE: {
      description: "Customer sets a target price for their route";
      flow: "Customer says 'I want DEL→SIN under ₹20K' → system monitors → alerts when price hits target";
      benefit: "Keeps customer engaged even when fares are high — they know we're watching for them";
    };

    COMPARISON_TRACKING: {
      description: "Show customer how today's fare compares to their options";
      content: "If you'd booked 2 weeks ago: ₹17,200 · Current: ₹18,500 · Our prediction for next week: ₹19,800";
      benefit: "Creates urgency with data, not pressure";
    };
  };
}

// ── Customer-facing fare alert (WhatsApp) ──
// ┌─────────────────────────────────────────────────────┐
// │  💸 Waypoint Travel · Fare Alert                            │
// │                                                       │
// │  Delhi → Singapore · June 15-20                        │
// │                                                       │
// │  IndiGo just dropped to ₹17,800!                       │
// │  ↓ 15% from last week (₹20,900)                       │
// │                                                       │
// │  📊 This is 25% below June average                        │
// │  ⚠️ Only 4 seats at this price                            │
// │                                                       │
// │  [Book Now ₹17,800] [Keep Watching]                        │
// └─────────────────────────────────────────────────────┘
```

### Booking Timing Optimization

```typescript
interface BookingTimingOptimization {
  // Optimal timing rules for common Indian routes
  timing_rules: {
    DOMESTIC_ROUTES: {
      general_rule: "Book 3-6 weeks in advance for best domestic fares";
      exceptions: {
        peak_season: "Diwali, Christmas, summer holidays — book 8-12 weeks ahead";
        last_minute: "Airlines release unsold seats at discount 3-5 days before (risky but cheap)";
      };
    };

    SOUTHEAST_ASIA: {
      routes: "DEL/BOM/BLR → SIN/BKK/KUL/CGK";
      general_rule: "Book 6-10 weeks in advance";
      best_months: "February-March and September-October (shoulder season pricing)";
      avoid: "June-July (Indian summer holidays spike demand 40%+)";
    };

    EUROPE: {
      routes: "DEL/BOM → LON/CDG/FRA/AMS";
      general_rule: "Book 10-16 weeks in advance";
      best_months: "March-April and October-November";
      peak: "June-August (European summer + Indian school holidays = double peak)";
    };

    MIDDLE_EAST: {
      routes: "DEL/BOM/CCJ → DXB/DOH/AUH/MUS";
      general_rule: "Book 4-8 weeks in advance";
      note: "Well-connected with frequent flights — less price volatility than long-haul";
      peak: "Eid, Ramadan period, Kerala school holidays for CCJ routes";
    };
  };

  agent_guidance: {
    WHEN_TO_ADVISE_BOOKING: [
      "Fare is below historical 25th percentile for the route/season",
      "Within 6 weeks of departure and fare is rising",
      "Airline announces route reduction or frequency cut",
      "Major event announced at destination (demand spike incoming)",
    ];

    WHEN_TO_ADVISE_WAITING: [
      "Fare is above historical 75th percentile",
      "More than 12 weeks until departure",
      "No demand spike events on the horizon",
      "Customer has flexible dates (can shift by 2-3 days)",
    ];
  };
}
```

---

## Open Problems

1. **Prediction accuracy ceiling** — Fare prediction is inherently probabilistic; airlines use dynamic pricing algorithms that are opaque. Best achievable accuracy is ~80% for direction (up/down) and much lower for exact price. Over-promising accuracy erodes trust.

2. **Alert fatigue** — Too many fare alerts train customers to ignore them. Need smart throttling: only send alerts that are genuinely actionable (significant drops, optimal windows, flash sales — not every ₹200 fluctuation).

3. **Airline API limitations** — Many Indian airlines (especially IndiGo) don't offer public fare APIs. Data must be collected via GDS, meta-search, or web scraping (legally complex). Incomplete data limits prediction quality.

4. **Customer irrationality** — Even with perfect prediction showing "book now," some customers wait because "a friend got a better deal last year." Behavioral economics (loss aversion framing) matters as much as data.

5. **Multi-city/multi-airline complexity** — Fare prediction for simple round-trips is straightforward. Multi-city itineraries (DEL→SIN→KUL→DEL) with mixed airlines involve dozens of fare combinations — prediction complexity grows exponentially.

---

## Next Steps

- [ ] Build fare data collection pipeline from GDS and airline sources
- [ ] Create fare prediction model with seasonal, advance-purchase, and demand components
- [ ] Implement fare alert system with WhatsApp and email delivery
- [ ] Design booking timing recommendation engine for agents
- [ ] Build fare intelligence dashboard with trend visualization
