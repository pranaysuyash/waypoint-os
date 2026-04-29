# Dynamic Packaging Engine — Inventory & Availability

> Research document for real-time inventory management, availability checking, allocation systems, and overbooking prevention for travel agency dynamic packaging.

---

## Key Questions

1. **How do we manage real-time inventory across multiple suppliers?**
2. **What allocation strategies prevent overbooking?**
3. **How do we handle inventory conflicts during package assembly?**
4. **What caching strategies balance freshness with API costs?**

---

## Research Areas

### Multi-Supplier Inventory Aggregation

```typescript
interface InventoryAggregation {
  // Aggregate inventory from multiple sources
  sources: {
    DIRECT_CONTRACT: {
      description: "Agency's own contracted inventory with hotels/airlines";
      access: "Dedicated allotments, negotiated rates";
      freshness: "Near real-time (updated every 15 min)";
      reliability: "HIGH — guaranteed allotment until release date";
      cost: "No per-query API cost";
    };

    BEDBANK: {
      description: "Wholesale hotel aggregators (Hotelbeds, WebBeds, DOTW)";
      access: "Pre-negotiated net rates, large inventory pool";
      freshness: "Real-time via API (rate of change: medium)";
      reliability: "MEDIUM — allotment shared across agencies";
      cost: "Per-query API cost: ₹0.5-2.0";
    };

    GDS: {
      description: "Global Distribution System (Amadeus, Sabre, Travelport)";
      access: "Published fares, flight + hotel + car";
      freshness: "Real-time (live availability)";
      reliability: "HIGH — authoritative source";
      cost: "Per-query API cost: ₹2.0-5.0";
    };

    AGGREGATOR: {
      description: "Activity aggregators (Viator, Klook, KKday)";
      access: "Published activities and experiences";
      freshness: "Updated every 1-4 hours";
      reliability: "MEDIUM — third-party confirmation needed";
      cost: "Per-query API cost: ₹0.5-1.0";
    };

    DIRECT_API: {
      description: "Direct integration with airlines, hotel chains";
      access: "Published + loyalty inventory";
      freshness: "Real-time";
      reliability: "HIGH — source of truth";
      cost: "Per-query API cost: ₹1.0-3.0";
    };
  };

  // Aggregation strategy
  strategy: {
    SEARCH_ORDER: [
      "1. Check direct contract inventory (cheapest, fastest)",
      "2. Check bedbank inventory (good rates, medium cost)",
      "3. Check GDS for published rates (highest cost, widest coverage)",
      "4. Merge results, deduplicate, sort by margin",
    ];
    DEDUPLICATION: "Same hotel room from multiple sources → pick best margin";
    FALLBACK: "If primary source fails → try next source automatically";
  };
}

// ── Inventory aggregation dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Inventory Sources — Singapore · June 15-20              │
// │                                                       │
// │  Source          │ Results │ Avg Cost │ Avg Margin │ Latency│
// │  ─────────────────────────────────────────────────────────│
// │  Direct Contract │    8    │  ₹4,200  │   22%      │  80ms  │
// │  Hotelbeds       │   24    │  ₹5,100  │   16%      │ 450ms  │
// │  WebBeds         │   18    │  ₹4,800  │   18%      │ 380ms  │
// │  Amadeus (GDS)   │   35    │  ₹6,200  │   12%      │ 900ms  │
// │  ─────────────────────────────────────────────────────────│
// │  Total (deduped) │   52    │  ₹5,050  │   17%      │  —     │
// │                                                       │
// │  API cost this search: ₹12.40                          │
// │  Cache hits: 60% (saved ₹18.60)                        │
// │                                                       │
// │  [Refresh All] [Adjust Sources] [Cost Analysis]         │
// └─────────────────────────────────────────────────────┘
```

### Availability Checking & Caching

```typescript
interface AvailabilityCaching {
  // Smart caching to reduce API costs
  cache_strategy: {
    FLIGHT: {
      ttl: "5 minutes (prices change frequently)";
      cache_key: "origin-destination-date-class-airline";
      invalidation: "Price change > 2%, seat count change, manual refresh";
      pre_warm: "Pre-cache popular routes for next 30 days overnight";
    };

    HOTEL: {
      ttl: "30 minutes (rates change less frequently)";
      cache_key: "hotel-checkin-checkout-room_type-occupancy";
      invalidation: "Rate change > 3%, availability change, manual refresh";
      pre_warm: "Pre-cache top 50 destinations for next 90 days";
    };

    ACTIVITY: {
      ttl: "2 hours (relatively stable)";
      cache_key: "activity-date-traveler_count";
      invalidation: "Availability change, price change";
      pre_warm: "Pre-cache top activities per destination";
    };

    TRANSFER: {
      ttl: "4 hours (very stable)";
      cache_key: "route-vehicle_type-date";
      invalidation: "Manual refresh or booking";
    };
  };

  // Availability check flow
  check_flow: {
    STEP_1: "Check cache for all components simultaneously";
    STEP_2: "For cached results: verify availability hasn't expired";
    STEP_3: "For uncached/expired: query live API";
    STEP_4: "Merge cached + live results";
    STEP_5: "Apply agency markup and margin rules";
    STEP_6: "Return sorted results to package builder";
  };

  // Cost optimization
  cost_control: {
    DAILY_API_BUDGET: "₹500/day for inventory queries";
    CACHE_TARGET: "70% cache hit rate (reduces API costs)";
    SMART_PREFETCH: "Prefetch likely searches based on customer inquiry patterns";
    BATCH_QUERIES: "Combine multiple component queries into single API call where possible";
  };
}

// ── Availability check flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Availability Engine — Cache Performance                 │
// │                                                       │
// │  Today's stats:                                       │
// │  Total queries: 1,247                                 │
// │  Cache hits: 873 (70%) · Cache misses: 374 (30%)      │
// │  API cost: ₹312 / ₹500 daily budget                   │
// │  Avg response time: 180ms (cached) vs 1,200ms (live)  │
// │                                                       │
// │  Cache hit rate by component:                         │
// │  Transfers:   92% ████████████████████████             │
// │  Activities:  78% ███████████████                      │
// │  Hotels:      65% █████████████                        │
// │  Flights:     45% █████████                            │
// │                                                       │
// │  Prefetch accuracy: 68% of prefetched results used     │
// │  Waste: ₹45/day on unused prefetched queries            │
// │                                                       │
// │  Active holds: 3 packages (₹180 inventory held)        │
// │  Expiring holds: 1 (Sharma package — 4h remaining)     │
// │                                                       │
// │  [Clear Cache] [Adjust TTL] [Prefetch Settings]         │
// └─────────────────────────────────────────────────────┘
```

### Inventory Allocation & Overbooking Prevention

```typescript
interface InventoryAllocation {
  // Prevent overbooking across multiple sales channels
  allocation: {
    // Allotment management
    ALLOTMENT: {
      description: "Pre-allocated inventory from supplier contracts";
      management: {
        total_allotment: 20;              // 20 rooms contracted for June
        allocated_to_trips: 14;           // 14 rooms booked into trips
        soft_hold: 3;                     // 3 rooms held for proposals in progress
        released: 3;                      // 3 rooms still available to sell
      };
      release_schedule: "Unsold allotment released back to supplier 14 days before";
      overbooking_rule: "Cannot allocate more than total_allotment";
    };

    // Hold and release system
    HOLDS: {
      PROPOSAL_HOLD: {
        duration: "24 hours";
        deposit: "None (free hold)";
        limit: "Max 5 holds per agent at a time";
        auto_release: "Released if proposal not sent within 24h";
      };
      BOOKING_HOLD: {
        duration: "48 hours (or until payment deadline)";
        deposit: "₹5,000 or 10% of package value";
        confirmation: "Supplier notified immediately";
        auto_release: "Released if payment not received by deadline";
      };
    };

    // Conflict resolution
    conflicts: {
      DOUBLE_BOOK: {
        detection: "Two agents try to book same inventory simultaneously";
        resolution: "First-to-confirm wins; second agent gets alternative options";
        prevention: "Real-time inventory lock when booking initiated";
      };

      SUPPLIER_OVERBOOK: {
        detection: "Supplier confirms unavailability after we sold";
        resolution: "Immediate alternative sourcing + customer notification + upgrade if possible";
        prevention: "Buffer allotment (hold 5% more than needed)";
      };

      RATE_CHANGE: {
        detection: "Supplier changes rate after package quoted to customer";
        resolution: "Absorb difference if < 5%, re-quote if > 5%";
        prevention: "Rate lock in supplier contract (24-48h guaranteed rates)";
      };
    };
  };
}

// ── Inventory allocation ──
// ┌─────────────────────────────────────────────────────┐
// │  Inventory Allocation — June 2026 Singapore              │
// │                                                       │
// │  Hotel: Pan Pacific Orchard · Family Suite              │
// │  Contracted allotment: 20 room-nights                   │
// │                                                       │
// │  Status breakdown:                                    │
// │  ✅ Confirmed bookings:  12 nights (₹1,02,000)         │
// │  🟡 Soft holds (proposals): 4 nights (₹34,000)         │
// │  🔵 Available to sell:    4 nights                      │
// │                                                       │
// │  ████████████████████                                   │
// │  ✅✅✅✅✅✅✅✅✅✅✅✅🟡🟡🟡🟡🔵🔵🔵🔵             │
// │                                                       │
// │  Release schedule:                                    │
// │  ⚠️ 4 unsold nights release on Jun 1 (14 days before) │
// │  Action: Promote remaining inventory or release early   │
// │                                                       │
// │  Active holds:                                        │
// │  🟡 Sharma proposal — 2 nights held — expires 4h       │
// │  🟡 Verma proposal — 2 nights held — expires 18h       │
// │                                                       │
// │  [Release Unused] [Request More Allotment] [Transfer]   │
// └─────────────────────────────────────────────────────┘
```

### Package Versioning & Price Changes

```typescript
interface PackageVersioning {
  // Handle package changes and price movements
  versioning: {
    // Package version lifecycle
    VERSION_1: {
      trigger: "Initial package created";
      content: "Component selection + pricing + margins";
      status: "DRAFT";
    };

    VERSION_2: {
      trigger: "Package sent to customer as proposal";
      content: "Locked pricing with 24h hold";
      status: "PROPOSED";
      price_guarantee: "24 hours from proposal timestamp";
    };

    VERSION_3: {
      trigger: "Customer requests changes (swap hotel, add activity)";
      content: "Updated components + re-priced";
      status: "REVISED";
      delta_tracking: "Show customer what changed from V2 and price impact";
    };

    VERSION_FINAL: {
      trigger: "Customer confirms and pays advance";
      content: "Final locked package with confirmed inventory";
      status: "CONFIRMED";
      price_guarantee: "Until trip completion (supplier contracts)";
    };
  };

  // Price change handling
  price_changes: {
    BEFORE_PROPOSAL: "Free to change — customer hasn't seen price yet";
    DURING_PROPOSAL: "If price drops: pass savings to customer (builds trust). If price rises: absorb if <3%, re-quote if >3%";
    AFTER_CONFIRMATION: "Supplier absorbs per contract terms. If supplier can't: agency absorbs up to 5%, above 5% requires customer consent";
    MARGIN_ADJUSTMENT: "Auto-adjust margin within guardrails to absorb small price changes without customer-visible impact";
  };
}

// ── Package version history ──
// ┌─────────────────────────────────────────────────────┐
// │  Package History — Singapore Family Trip                  │
// │  Customer: Sharma family · WP-502                        │
// │                                                       │
// │  V1 (Draft) · Apr 15 · Created by Priya               │
// │  Total: ₹2,30,200 · Status: Draft                     │
// │                                                       │
// │  V2 (Proposed) · Apr 16 · Sent to customer            │
// │  Changes from V1: Added travel insurance               │
// │  Total: ₹2,37,400 (+₹7,200) · Status: Awaiting reply  │
// │                                                       │
// │  V3 (Revised) · Apr 18 · Customer requested changes   │
// │  Changes from V2:                                     │
// │  • Hotel: Pan Pacific → Village Hotel (-₹12,500)      │
// │  • Activity: Added Sentosa Luge (+₹1,800)             │
// │  • Removed: Night Safari (-₹3,200)                    │
// │  Total: ₹2,23,500 (-₹13,900) · Status: Proposed       │
// │                                                       │
// │  ✅ V4 (Confirmed) · Apr 20 · Payment received         │
// │  Changes from V3: Flight price held (saved ₹4,200)     │
// │  Total: ₹2,23,500 · Status: CONFIRMED                 │
// │                                                       │
// │  [Compare Versions] [Export History]                     │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Cache staleness vs. cost** — Aggressive caching reduces API costs but risks showing sold-out inventory. Need smart invalidation based on booking velocity (high-velocity periods = shorter TTL).

2. **Allotment optimization** — Contracting too much inventory ties up capital; too little means lost sales. Need demand forecasting to optimize allotment levels per season.

3. **Multi-channel inventory sync** — Agency sells via WhatsApp, website, walk-in, and phone. All channels must see the same inventory in real-time. Race conditions are inevitable.

4. **Supplier API reliability** — Some supplier APIs go down during peak booking periods (ironically when you need them most). Need graceful degradation with cached fallbacks.

---

## Next Steps

- [ ] Build multi-source inventory aggregation with deduplication
- [ ] Implement tiered caching strategy with cost controls
- [ ] Create allotment management with hold/release system
- [ ] Design package versioning with price change handling
