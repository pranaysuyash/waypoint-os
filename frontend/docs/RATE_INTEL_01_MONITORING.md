# Supplier Rate Intelligence — Rate Monitoring & Alerting

> Research document for real-time supplier rate monitoring, rate change detection, alerting systems, and the rate intelligence dashboard for travel agencies.

---

## Key Questions

1. **How do we monitor supplier rates across hotels, airlines, and activities?**
2. **What rate changes warrant agent alerts?**
3. **How do we track rate parity across booking channels?**
4. **What historical rate data informs pricing decisions?**

---

## Research Areas

### Rate Monitoring Architecture

```typescript
interface RateMonitor {
  monitor_id: string;
  agency_id: string;

  // What to monitor
  targets: {
    type: "HOTEL" | "FLIGHT" | "ACTIVITY" | "PACKAGE" | "VISA";
    supplier: string;                    // "Taj Hotels", "IndiGo", "SOTC"
    route: string | null;                // "DEL-SIN" for flights
    property_id: string | null;          // supplier-specific ID
    destination: string;

    // Monitoring parameters
    check_in_date: string | null;        // specific date or date range
    room_type: string | null;            // "Deluxe Sea View"
    meal_plan: string | null;            // "CP", "MAP", "AP"
    pax: number;
  };

  // Monitoring schedule
  schedule: {
    frequency: "HOURLY" | "EVERY_6H" | "DAILY" | "WEEKLY";
    active_from: string;
    active_until: string | null;
    last_checked: string | null;
    next_check: string | null;
  };

  // Alert conditions
  alerts: {
    condition: "PRICE_DROP" | "PRICE_INCREASE" | "AVAILABILITY_CHANGE" | "RATE_PARITY_BREACH";
    threshold: {
      type: "PERCENTAGE" | "ABSOLUTE" | "ANY_CHANGE";
      value: number;                     // 5% drop, ₹500 increase, any change
    };
    notification: "IN_APP" | "WHATSAPP" | "EMAIL" | "SLACK";
    enabled: boolean;
  }[];
}

// ── Rate monitoring dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Rate Intelligence — Monitor Dashboard                 │
// │                                                       │
// │  Active Monitors: 24 · Alerts Today: 3               │
// │                                                       │
// │  ┌─ Recent Rate Changes ──────────────────────────┐  │
// │  │                                                 │  │
// │  │  🔻 Taj Vivanta Singapore                      │  │
// │  │  Deluxe Room · Jun 1-6                         │  │
// │  │  ₹8,500 → ₹7,200 (-15.3%)                     │  │
// │  │  Source: Taj Direct · 2 hours ago               │  │
// │  │  [Book Now] [Set Alert] [Compare Sources]       │  │
// │  │                                                 │  │
// │  │  🔻 IndiGo DEL-SIN                             │  │
// │  │  Economy · Jun 1                               │  │
// │  │  ₹12,400 → ₹11,200 (-9.7%)                    │  │
// │  │  Source: IndiGo Direct · 4 hours ago            │  │
// │  │  [Book Now] [Set Alert] [View Route Prices]     │  │
// │  │                                                 │  │
// │  │  🔺 Marina Bay Sands                           │  │
// │  │  Premium Room · Jun 1-6                         │  │
// │  │  ₹18,000 → ₹21,500 (+19.4%)                   │  │
// │  │  Source: Booking.com · 6 hours ago              │  │
// │  │  [Alert Customer] [Find Alternatives]            │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  [Add Monitor] [Bulk Import] [View All Changes]       │
// └─────────────────────────────────────────────────────┘
```

### Rate Change Detection

```typescript
interface RateChange {
  change_id: string;
  detected_at: string;

  // What changed
  target: {
    type: "HOTEL" | "FLIGHT" | "ACTIVITY";
    supplier: string;
    name: string;                        // "Taj Vivanta Singapore"
    search_params: Record<string, string>;
  };

  // Price change
  change: {
    previous_price: number;
    new_price: number;
    difference: number;
    percentage: number;
    direction: "UP" | "DOWN" | "SAME";
    currency: "INR";
  };

  // Source tracking
  source: {
    channel: "DIRECT" | "OTA" | "GDS" | "WHOLESALER" | "META";
    platform: string;                    // "MakeMyTrip", "Goibibo", "Taj Direct"
    url: string | null;
    screenshot_url: string | null;       // for audit trail
  };

  // Impact assessment
  impact: {
    affected_trips: string[];            // trip IDs with this supplier
    affected_agents: string[];
    potential_savings: number | null;    // if price dropped
    potential_overcharge: number | null; // if price increased
    urgency: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  };
}

// ── Rate change impact analysis ──
// ┌─────────────────────────────────────────────────────┐
// │  Rate Change — Impact Assessment                      │
// │                                                       │
// │  Taj Vivanta Singapore — Price Drop -15.3%            │
// │  ₹8,500 → ₹7,200 per night                          │
// │                                                       │
// │  Affected trips (3):                                  │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ WP-442 Sharma Family · Jun 1-6 · 5 nights     │   │
// │  │ Booked at: ₹8,500 · Current: ₹7,200           │   │
// │  │ Potential saving: ₹6,500 (if rebooked)         │   │
// │  │ Status: CONFIRMED · Can modify? YES            │   │
// │  │ [Rebook at lower rate] [Keep current]           │   │
// │  │                                               │   │
// │  │ WP-448 Gupta Family · Jun 8-12 · 4 nights     │   │
// │  │ Quoted at: ₹8,500 · Not yet confirmed          │   │
// │  │ Updated saving: ₹5,200                         │   │
// │  │ Status: DRAFT · Auto-update? YES               │   │
// │  │ [Update quote automatically]                    │   │
// │  │                                               │   │
// │  │ WP-451 Ravi Solo · Jun 15-17 · 2 nights       │   │
// │  │ Not quoted yet · Use new rate                  │   │
// │  │ Status: INTAKE · No action needed              │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Total potential savings across trips: ₹11,700        │
// │  Recommended action: Rebook WP-442, update WP-448     │
// └─────────────────────────────────────────────────────┘
```

### Rate Parity Checker

```typescript
interface RateParityCheck {
  check_id: string;
  hotel: string;
  check_in: string;
  check_out: string;
  room_type: string;

  // Prices across channels
  channels: {
    channel: string;
    platform: string;
    price: number;
    meal_plan: string;
    cancellation_policy: string;
    availability: boolean;
    checked_at: string;
  }[];

  // Parity analysis
  analysis: {
    lowest_price: { channel: string; price: number };
    highest_price: { channel: string; price: number };
    spread: number;                       // highest - lowest
    spread_percentage: number;
    parity_breached: boolean;             // spread > threshold
    recommended_channel: string;          // best price-reliability ratio
  };
}

// ── Rate parity comparison ──
// ┌─────────────────────────────────────────────────────┐
// │  Rate Parity — Taj Vivanta Singapore                   │
// │  Deluxe Room · CP · Jun 1-6, 2026                     │
// │                                                       │
// │  Channel comparison:                                  │
// │  ┌────────────────────────────────────────────────┐  │
// │  │ Source          │ Price   │ Policy     │ Avail │  │
// │  │ ──────────────────────────────────────────────  │  │
// │  │ Taj Direct      │ ₹7,200  │ Free cancel│  ✅   │  │
// │  │ MakeMyTrip      │ ₹7,800  │ Non-refund │  ✅   │  │
// │  │ Goibibo         │ ₹7,650  │ Free cancel│  ✅   │  │
// │  │ Booking.com     │ ₹8,200  │ Free cancel│  ✅   │  │
// │  │ Agoda           │ ₹7,500  │ Non-refund │  ✅   │  │
// │  │ Expedia         │ ₹8,100  │ Free cancel│  ✅   │  │
// │  │ B2B Wholesaler  │ ₹6,800  │ Non-refund │  ✅   │  │
// │  │ Thomas Cook B2B │ ₹7,100  │ Free cancel│  ✅   │  │
// │  └────────────────────────────────────────────────┘  │
// │                                                       │
// │  Analysis:                                            │
// │  Lowest:  B2B Wholesaler ₹6,800 (non-refundable)     │
// │  Best value: Thomas Cook B2B ₹7,100 (free cancel)    │
// │  Spread: ₹1,400 (20.6%) — parity breach!             │
// │                                                       │
// │  Recommendation: Book via Thomas Cook B2B             │
// │  Rationale: Best cancellable rate, B2B commission     │
// │                                                       │
// │  [Book Now] [Set Price Alert] [Export Comparison]      │
// └─────────────────────────────────────────────────────┘
```

### Historical Rate Tracker

```typescript
interface HistoricalRate {
  target: string;                        // "Taj Vivanta Singapore, Deluxe, CP"
  rates: {
    date: string;
    channel: string;
    price: number;
    availability: boolean;
  }[];

  // Derived analytics
  analytics: {
    avg_price_30d: number;
    min_price_30d: number;
    max_price_30d: number;
    current_percentile: number;          // 0-100, where current price sits
    trend: "RISING" | "FALLING" | "STABLE";
    seasonal_pattern: string;            // "Prices spike 2 weeks before check-in"
    best_booking_window: string;         // "Book 45-60 days ahead for best rates"
  };
}

// ── Historical rate chart ──
// ┌─────────────────────────────────────────────────────┐
// │  Rate History — Taj Vivanta Singapore Deluxe CP        │
// │  Check-in: Jun 1, 2026 (33 days out)                  │
// │                                                       │
// │  Price (₹/night)                                      │
// │  9,000 ┤                                              │
// │  8,800 ┤     ╭─╮                                      │
// │  8,600 ┤    ╭╯ ╰╮                                     │
// │  8,400 ┤   ╭╯   ╰╮                                    │
// │  8,200 ┤  ╭╯     ╰──╮                                 │
// │  8,000 ┤ ╭╯         ╰╮                                │
// │  7,800 ┤╭╯            ╰──╮                            │
// │  7,600 ┤╯                ╰╮                           │
// │  7,400 ┤                  ╰╮╌╌╌ CURRENT ₹7,200        │
// │  7,200 ┤                   ╰─●                         │
// │        └──┬────┬────┬────┬────┬──→                     │
// │         90d  60d  45d  30d  NOW                       │
// │                                                       │
// │  Stats:                                               │
// │  90-day avg: ₹8,100 · Current: ₹7,200 (11% below)   │
// │  All-time low: ₹6,900 (Mar 2025)                     │
// │  Recommendation: BOOK NOW — price is in 15th          │
// │  percentile and trend is still falling                 │
// │                                                       │
// │  [Set Alert at ₹7,000] [View Full History]            │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Rate scraping legality** — Scraping supplier websites may violate ToS. Need authorized API partnerships (hotel wholesalers, GDS feeds) supplemented by manual rate entry for non-API suppliers.

2. **Rate freshness** — Hotel rates change multiple times daily. Hourly monitoring may miss flash sales. Need real-time push integrations where available.

3. **Multi-currency complexity** — International hotels price in local currency. INR conversion adds a variable that must be tracked alongside base rate changes.

4. **Cancellation policy comparison** — Same hotel, different cancellation policies make price comparison misleading. Need normalized comparison (effective price including cancellation risk).

---

## Next Steps

- [ ] Design rate monitoring system with authorized data sources
- [ ] Build rate change detection with trip impact analysis
- [ ] Create rate parity checker across channels
- [ ] Implement historical rate tracker with booking window recommendations
