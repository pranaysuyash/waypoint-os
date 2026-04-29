# Destination Event & Festival Intelligence — Demand Prediction

> Research document for event-driven demand prediction, booking lead time analysis, event-aware inventory management, and festival-specific travel packages.

---

## Key Questions

1. **How do events predict travel demand spikes?**
2. **What booking lead times do events create?**
3. **How do we manage inventory around events?**
4. **What event-specific travel packages can agencies create?**

---

## Research Areas

### Event-Driven Demand Model

```typescript
interface EventDemandModel {
  event_id: string;
  destination: string;

  // Demand curve
  demand_curve: {
    weeks_before_event: number;         // 0 = event week, -1 = 1 week before
    demand_index: number;               // 100 = normal, 200 = double
    booking_velocity: number;           // bookings per day (vs baseline)
  }[];

  // Booking window
  booking_window: {
    early_bird_start: number;           // weeks before event
    standard_booking_start: number;
    last_minute_start: number;
    soldout_expected: number;           // when inventory typically gone
  };

  // Customer segments attracted
  attracted_segments: {
    segment: string;
    percentage: number;
    avg_trip_length_days: number;
    avg_group_size: number;
    budget_tier: "BUDGET" | "MID_RANGE" | "PREMIUM" | "LUXURY";
  }[];
}

// ── Demand curve: Goa at New Year ──
// ┌─────────────────────────────────────────────────────┐
// │  Demand Curve: Goa — New Year's Eve 2026              │
// │                                                       │
// │  Weeks Before | Demand Index | Bookings/Day | Status  │
// │  ─────────────────────────────────────────────────── │
// │  20 weeks     | 120           | 5             │ Early │
// │  16 weeks     | 140           | 8             │ Early │
// │  12 weeks     | 180           | 15            │ Rising│
// │  8 weeks      | 250           | 28            │ HOT   │
// │  6 weeks      | 350           | 42            │ PEAK  │
// │  4 weeks      | 400           | 35            │ Sellou│
// │  2 weeks      | 450           | 20            │ Limit │
// │  1 week       | 500           | 5             │ Waitli│
// │  Event week   | 500           | 0             │ SOLD  │
// │                                                       │
// │  Inventory Status:                                    │
// │  5★ Hotels: Sold out by week 8                       │
// │  4★ Hotels: Sold out by week 6                       │
// │  3★ Hotels: Sold out by week 4                       │
// │  Flights: Sold out by week 3                         │
// │                                                       │
// │  Customer Segments:                                   │
// │  Groups (friends): 35% | 4 days | Mid-range          │
// │  Couples: 25% | 3 days | Premium                     │
// │  Families: 20% | 5 days | Mid-range                  │
// │  Solo/party: 15% | 3 days | Budget                  │
// │  Corporate: 5% | 2 days | Luxury                     │
// └─────────────────────────────────────────────────────┘
```

### Event-Specific Travel Packages

```typescript
interface EventTravelPackage {
  id: string;
  event_id: string;
  package_name: string;

  description: string;
  included_event_access: string;        // "VIP entry to Sunburn Festival"

  // Package components
  components: {
    flights: {
      class: string;
      route: string;
      included: boolean;
    };
    hotel: {
      type: string;
      nights: number;
      distance_to_event_km: number;
      shuttle_included: boolean;
    };
    event_access: {
      ticket_type: "GENERAL" | "PREMIUM" | "VIP" | "BACKSTAGE";
      days_covered: number;
    };
    transfers: {
      airport_transfer: boolean;
      event_shuttle: boolean;
    };
    extras: string[];                   // "Welcome hamper", "Afterparty entry"
  };

  // Pricing
  pricing: {
    per_person: Money;
    per_couple: Money;
    group_of_4: Money;
    valid_from: string;
    valid_to: string;
    early_bird_discount_pct: number;
    last_minute_markup_pct: number;
  };

  // Availability
  inventory: {
    total_packages: number;
    sold: number;
    remaining: number;
    cutoff_date: string;
  };
}

// ── Festival travel package example ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Package: Goa Sunburn Festival 2026             │
// │                                                       │
// │  🎵 3-Night Sunburn Experience                       │
// │                                                       │
// │  Includes:                                            │
// │  ✈️ Mumbai → Goa return (economy)                    │
// │  🏨 3 nights, Taj Holiday Village (500m to venue)   │
// │  🎫 3-day Sunburn VIP pass                          │
// │  🚐 Airport transfer + daily event shuttle           │
// │  🎁 Welcome kit (sunscreen, earplugs, merch)        │
// │                                                       │
// │  Pricing:                                             │
// │  Solo: ₹45,000  | Couple: ₹82,000 (₹41K each)     │
// │  Group of 4: ₹1,52,000 (₹38K each)                 │
// │  Early bird (8+ weeks): -15%                         │
// │  Last minute (<2 weeks): +20%                        │
// │                                                       │
// │  Inventory: 150 packages total, 78 sold, 72 left     │
// │  Cutoff: Dec 15 or when sold out                     │
// │                                                       │
// │  Agent commission: 8% (₹3,600 per solo package)      │
// │  Upsell: Upgrade to backstage (+₹15K)               │
// │  Add-on: Pre-party boat cruise (+₹4,500)            │
// └─────────────────────────────────────────────────────┘
```

### Event Calendar Integration for Agents

```typescript
// ── Agent event calendar view ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Intelligence Calendar — 2026                   │
// │                                                       │
// │  June                              July               │
// │  Mo Tu We Th Fr Sa Su  Mo Tu We Th Fr Sa Su          │
// │  1  2  3  4  5  6  7   1  2  3  4  5  6  7          │
// │  8  9  10 11 12 13 14  8  9  10 11 12 13 14          │
// │  15 16 17 18 19 20 21  15 16 17 18 19 20 21          │
// │  22 23 24 25 26 27 28  22 23 24 25 26 27 28          │
// │  29 30                   29 30 31                     │
// │                                                       │
// │  🔴 = Extreme demand  🟡 = High  🔵 = Moderate       │
// │                                                       │
// │  Upcoming events (book now!):                         │
// │  🔴 Dec 31 — New Year (Goa, Singapore, Dubai)        │
// │     Hotels selling fast, quote by October             │
// │                                                       │
// │  🟡 Nov 1 — Diwali (domestic + international)        │
// │     Goa/Kerala/Rajasthan bookings surge              │
// │                                                       │
// │  🔵 Oct 20 — Dussehra (domestic)                     │
// │     Moderate domestic travel, school holidays        │
// │                                                       │
// │  💡 Suggested actions:                                │
// │  • Create Diwali package flyers by August            │
// │  • Pre-book Goa hotel inventory for New Year         │
// │  • Pitch Singapore families (Dec school holidays)    │
// │  • Push Dubai Shopping Festival (Jan) early birds    │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Event discovery** — New events emerge constantly. Need automated event discovery from tourism boards, social media, and news sources, not just manual entry.

2. **Cannibalization** — Promoting an event package for one destination may cannibalize bookings for another. Need portfolio-level demand management.

3. **Overbooking risk** — Event inventory is scarce. Agencies that overcommit face severe reputation damage. Need strict inventory tracking.

4. **Post-event drop** — Demand drops sharply after events. Need strategies for post-event travel packages (quieter, cheaper alternative).

---

## Next Steps

- [ ] Build event-driven demand prediction model
- [ ] Create event-specific travel package templates
- [ ] Implement event calendar integration for agents
- [ ] Design event-aware inventory management alerts
