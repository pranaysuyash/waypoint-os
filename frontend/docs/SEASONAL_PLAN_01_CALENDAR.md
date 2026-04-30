# Seasonal Campaign Planner — Travel Marketing Calendar

> Research document for seasonal campaign planning, Indian travel demand calendar, peak/shoulder/off-season strategy, advance booking campaigns, and revenue planning around travel seasons for the Waypoint OS platform.

---

## Key Questions

1. **What are the key travel seasons for Indian outbound travel?**
2. **How do we plan marketing campaigns around seasonal demand?**
3. **What advance booking campaigns maximize shoulder-season revenue?**
4. **How does seasonal planning affect pricing and inventory strategy?**

---

## Research Areas

### Indian Travel Demand Calendar

```typescript
interface SeasonalCampaignPlanner {
  // Travel marketing calendar aligned with Indian demand patterns
  indian_travel_calendar: {
    PEAK_SEASON: {
      SUMMER_HOLIDAYS: {
        months: "April - June";
        driver: "School summer holidays (all boards: CBSE, ICSE, state boards)";
        demand: "Highest outbound travel period — 40% of annual leisure trips";
        top_destinations: ["Singapore", "Thailand", "Dubai", "Europe", "Australia"];
        booking_pattern: "Bookings start February-March; last-minute surge in April";
        pricing: "Highest airfares and hotel rates; 30-50% above off-season";
        campaign_window: "January-March (early bird offers) → April-May (last-minute deals)";
      };

      DIWALI_BREAK: {
        months: "October - November";
        driver: "Diwali holidays (1-2 week school break varies by state)";
        demand: "Second highest travel period — 15% of annual trips";
        top_destinations: ["Dubai", "Singapore", "Maldives", "Thailand", "Domestic (Goa, Kerala)"];
        booking_pattern: "Bookings peak September-October";
        pricing: "High — especially for Maldives and Dubai (Diwali = luxury travel)";
        campaign_window: "August-September (early bird) → October (urgency)";
      };

      CHRISTMAS_NEW_YEAR: {
        months: "December - January";
        driver: "Christmas + New Year school holidays";
        demand: "12% of annual trips — skews towards luxury and couples";
        top_destinations: ["Maldives", "Bali", "Thailand", "Europe (snow)", "Dubai"];
        booking_pattern: "Bookings peak October-November";
        pricing: "Peak pricing for Maldives and beach destinations";
        campaign_window: "September-November";
      };
    };

    SHOULDER_SEASON: {
      AUTUMN: {
        months: "September - October";
        driver: "Post-monsoon pleasant weather; pre-Diwali planning";
        opportunity: "Lower prices than peak; good weather in Southeast Asia";
        campaign: "'Pre-book your Diwali trip now — save 20% on early booking'";
      };

      SPRING: {
        months: "February - March";
        driver: "Pre-summer planning; honeymoon season (Feb weddings)";
        opportunity: "Advance booking for summer trips; honeymoon packages";
        campaign: "'Summer holidays are coming — lock in your trip at last year's prices'";
      };
    };

    OFF_SEASON: {
      MONSOON: {
        months: "July - August";
        driver: "Monsoon in India; low outbound leisure travel";
        opportunity: "Cheapest airfares; attractive hotel deals; less crowded destinations";
        strategy: "Target monsoon-escape campaigns for destinations with good weather (Dubai, Europe, Bali dry season)";
        campaign: "'Escape the monsoon — Dubai at ₹35K (40% off summer rates)'";
      };

      POST_HOLIDAY: {
        months: "January - February";
        driver: "Post-holiday fatigue; exam season for students";
        opportunity: "Cheapest travel window; retirees and couples without school-age children";
        campaign: "'Travel when the crowds are gone — Singapore from ₹25K'";
      };
    };

    EVENT_DRIVEN: {
      LONG_WEEKENDS: {
        examples: ["Republic Day (Jan 26)", "Holi (Mar)", "Independence Day (Aug 15)", "Gandhi Jayanti (Oct 2)", "Dussehra (variable)"];
        strategy: "Short-haul 3-4 day packages (Thailand, Dubai, Sri Lanka, Nepal)";
        booking_pattern: "2-4 weeks in advance; impulse bookings common";
        campaign: "Launched 4 weeks before long weekend; urgency messaging";
      };

      HONEYMOON_SEASON: {
        peak: "February-April (peak wedding season honeymoon travel)";
        secondary: "December-January (winter weddings)";
        strategy: "Dedicated honeymoon packages with romantic inclusions (couple's spa, dinner cruise, room upgrade)";
        campaign: "Partner with wedding planners; Instagram ads targeting newly engaged couples";
      };
    };
  };

  // ── Seasonal campaign calendar view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Seasonal Campaign Planner · 2026                          │
  // │                                                       │
  // │  Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec │
  // │  ████ ████ ████ ─── ─── ─── ─── ─── ─── ─── ─── ─── │
  // │  ▲ Off ▲Spring    ▲SUMMER   ▲Mon  ▲Autumn ▲Diwali ▲Xmas  │
  // │                                                       │
  // │  Active Campaigns:                                    │
  // │  🔵 Summer Early Bird (Jan 15 - Mar 31)                   │
  // │     Target: Families · Routes: SIN, BKK, DXB              │
  // │     Budget: ₹50K · Bookings: 45 · Revenue: ₹54L           │
  // │                                                       │
  // │  🟢 Honeymoon Season (Feb 1 - Apr 30)                     │
  // │     Target: Newlyweds · Routes: Maldives, Bali            │
  // │     Budget: ₹30K · Bookings: 18 · Revenue: ₹32L           │
  // │                                                       │
  // │  Upcoming Campaigns:                                  │
  // │  ○ Diwali Early Bird (Aug 15 - Sep 30)                    │
  // │  ○ Monsoon Escape (Jun 15 - Jul 31)                       │
  // │  ○ Christmas NY (Oct 1 - Nov 15)                          │
  // │                                                       │
  // │  [Create Campaign] [View Calendar] [Revenue Forecast]      │
  // └─────────────────────────────────────────────────────────┘
}
```

### Campaign Strategy Templates

```typescript
interface CampaignStrategyTemplates {
  // Reusable campaign templates for each season
  templates: {
    EARLY_BIRD: {
      description: "Advance booking campaign with price lock guarantee";
      timing: "8-12 weeks before peak season";
      offer: "Book now at this season's prices for next season's travel";
      elements: {
        headline: "'Lock in summer 2026 at 2025 prices'";
        incentive: "₹2,000-5,000 early bird discount per booking";
        urgency: "Offer valid until {date} or first 50 bookings — whichever earlier";
        guarantee: "Price match: if fares drop before departure, we pass the savings";
        payment: "Only ₹5,000 token advance to lock the price; balance closer to travel";
      };
      conversion_target: "30-40% of annual bookings from early bird campaigns";
    };

    LAST_MINUTE_DEALS: {
      description: "Unsold inventory clearance at discounted rates";
      timing: "2-4 weeks before travel dates";
      offer: "Heavily discounted packages for flexible travelers";
      channels: "WhatsApp broadcast + Instagram stories + email";
      urgency: "3-day flash sale; 10 seats only; non-refundable";
      margin: "Lower margin but covers fixed costs; better than empty seats";
    };

    DESTINATION_SPOTLIGHT: {
      description: "Deep-dive campaign for a specific destination";
      timing: "Shoulder season to build demand for upcoming peak";
      content: [
        "Week 1: Destination overview post (Instagram carousel)",
        "Week 2: Customer testimonial from recent trip",
        "Week 3: 'Day in the life' itinerary post",
        "Week 4: Limited-time offer for that destination",
      ];
    };

    REFERRAL_BOOST: {
      description: "Time-limited referral incentive during booking season";
      timing: "Peak booking period (Feb-Mar for summer, Sep-Oct for Diwali)";
      offer: "Refer a friend who books → both get ₹2,000 credit";
      urgency: "Valid for 30 days; double credit for first 10 referrals";
    };
  };

  campaign_execution: {
    CHANNEL_MIX: {
      whatsapp_broadcast: "40% of campaign reach (highest conversion per message)";
      instagram_ads: "25% of campaign reach (visual inspiration + retargeting)";
      email_marketing: "20% of campaign reach (detailed offers + itinerary previews)";
      google_ads: "10% of campaign reach (intent-based search capture)";
      website_banner: "5% of campaign reach (homepage + landing pages)";
    };

    BUDGET_ALLOCATION: {
      principle: "Spend more during booking windows, less during travel periods";
      peak_booking_months: "February-March and September-October — 60% of annual marketing budget";
      shoulder_months: "January, August — 25% of budget";
      off_peak_months: "April-July, November — 15% of budget (maintenance mode)";
    };
  };
}
```

### Seasonal Revenue Planning

```typescript
interface SeasonalRevenuePlanning {
  // Revenue forecasting and planning by season
  revenue_model: {
    ANNUAL_TARGET: {
      breakdown: {
        peak_season: "55-60% of annual revenue (April-June, October-December)";
        shoulder_season: "25-30% of annual revenue (February-March, September)";
        off_season: "10-15% of annual revenue (January, July-August)";
      };
    };

    BOOKING_VELOCITY: {
      description: "How far in advance bookings come by season";
      peak_season: "8-16 weeks advance booking; high competition for inventory";
      shoulder_season: "4-8 weeks advance booking; moderate inventory pressure";
      off_season: "1-4 weeks advance booking; easy inventory; impulse-friendly";
    };

    MARGIN_OPTIMIZATION: {
      peak: "Standard margins (15-20%) — customers accept premium pricing";
      shoulder: "Higher margins (20-25%) — lower supplier costs with reasonable selling prices";
      off_peak: "Lower margins (10-15%) — discounted to move; focus on volume";
    };

    INVENTORY_STRATEGY: {
      advance_commitment: "Commit to hotel allotments 6+ months before peak season at contracted rates";
      flexible_hold: "Option-to-release contracts for shoulder season — hold without financial commitment";
      spot_buying: "Off-season relies on spot rates and last-minute supplier deals";
      risk: "Over-commitment in peak season → unsold inventory loss; under-commitment → sold-out hotels";
    };
  };
}
```

---

## Open Problems

1. **Seasonal cash flow mismatch** — Peak revenue months (April-June, October-December) don't align with peak expense months (marketing spend February-March, September-October). Cash flow management across seasonal cycles is critical for agency survival.

2. **Weather disruption** — Campaign built around "Singapore in June" can be disrupted by unexpected weather (haze from Indonesia, typhoons). Need contingency messaging and flexible rebooking policies.

3. **Competitor timing** — If every agency launches early bird campaigns in January, the message drowns in noise. Differentiation through unique destinations, better value-adds, or earlier/later timing is needed.

4. **Shoulder season activation** — Most agencies only market during peak seasons. Activating demand in shoulder/off-season (when costs are lower and travelers could get better deals) requires educating customers on the value of off-peak travel.

5. **Multi-year planning** — Families plan major trips (Europe, Australia) 6-12 months in advance. Campaign cycles for these trips start a year before the travel date, not 2-3 months like short-haul trips.

---

## Next Steps

- [ ] Build seasonal campaign calendar with automated scheduling
- [ ] Create campaign templates for early bird, last-minute, destination spotlight
- [ ] Implement seasonal revenue forecasting with booking velocity tracking
- [ ] Design campaign analytics with channel-mix performance comparison
- [ ] Build inventory planning tool with advance commitment management
