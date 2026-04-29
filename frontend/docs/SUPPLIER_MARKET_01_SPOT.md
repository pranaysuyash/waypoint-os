# Supplier Marketplace & Spot Buying — Spot Market & Inventory Access

> Research document for travel supplier marketplace design, spot buying workflows, emergency inventory sourcing, and supplier discovery for travel agencies.

---

## Key Questions

1. **How do agencies source inventory when contracted stock runs out?**
2. **What does a supplier marketplace for travel agencies look like?**
3. **How does spot buying work with dynamic pricing?**
4. **What's the operational model for emergency inventory access?**

---

## Research Areas

### Supplier Marketplace Design

```typescript
interface SupplierMarketplace {
  // Marketplace for travel inventory access
  marketplace_model: {
    LISTING_TYPES: {
      STANDARD_RATE: {
        description: "Supplier lists standard rates visible to all agencies";
        commission: "Platform takes 2-5% facilitation fee";
        visibility: "All registered agencies";
        booking_flow: "Search → Compare → Book → Confirm";
      };

      FLASH_DEAL: {
        description: "Time-limited inventory at deep discount (unsold rooms/flights)";
        discount: "30-60% off rack rate";
        duration: "24-72 hour availability window";
        use_case: "Last-minute bookings, distressed inventory";
        booking_flow: "Alert → Grab → Pay → Confirm";
      };

      REQUEST_FOR_QUOTE: {
        description: "Agency posts requirement, suppliers compete with quotes";
        use_case: "Group bookings, custom itineraries, high-value deals";
        response_time: "2-4 hours for standard requests";
        booking_flow: "Post → Receive Quotes → Compare → Select → Book";
      };

      ALLOTMENT_EXCHANGE: {
        description: "Agencies trade unused allotment with each other";
        use_case: "Agency has committed hotel rooms they can't sell";
        mechanism: "Post allotment → Other agency claims → Transfer fee";
        booking_flow: "Post Availability → Match → Transfer → Confirm";
      };
    };
  };

  // Supplier discovery
  supplier_discovery: {
    SEARCH_DIMENSIONS: {
      by_destination: "Country → City → Area";
      by_category: "Hotel · Activity · Transfer · Visa · Insurance · Guide";
      by_star_rating: "2-star to 5-star / Luxury";
      by_budget_range: "Budget · Standard · Premium · Luxury";
      by_amenity: "Pool · Spa · Vegetarian · Wheelchair · Family";
      by_rating: "Platform rating · Google rating · Agency reviews";
      by_availability: "Available dates · Last-minute · Guaranteed";
    };

    SUPPLIER_PROFILE: {
      basic_info: "Name, location, category, star rating, photos";
      rates: "Published rates, negotiated rates (if contracted), flash deals";
      availability: "Real-time availability calendar with pricing";
      reviews: "Ratings from agencies who've used this supplier";
      reliability_score: "On-time confirmation rate, cancellation rate, issue rate";
      payment_terms: "Advance %, cancellation policy, refund timeline";
      certifications: "Ministry of Tourism, IATA, local tourism board";
    };
  };
}

// ── Supplier marketplace search ──
// ┌─────────────────────────────────────────────────────┐
// │  Supplier Marketplace — Find Inventory                    │
// │                                                       │
// │  Destination: [Bali ▾]   Category: [Hotel ▾]            │
// │  Dates: Jun 15-20   Stars: [4★+]   Budget: [₹5-8K/night]│
// │  [Search]                                                 │
// │                                                       │
// │  Results: 23 hotels available                          │
// │                                                       │
// │  🏨 Bali Beach Resort · 4★ · Kuta                       │
// │     ₹6,200/night · Breakfast included                     │
// │     ⭐ 4.3 (18 agency reviews) · 95% confirmation rate    │
// │     Flash: 20% off for Jun 15-18 (3 rooms left)          │
// │     [Book Now] [Get Quote] [Add to Compare]              │
// │                                                       │
// │  🏨 Ubud Garden Villa · 4★ · Ubud                        │
// │     ₹4,800/night · Breakfast + Spa                       │
// │     ⭐ 4.6 (32 agency reviews) · 98% confirmation rate    │
// │     Your contracted rate: ₹4,200/night (save ₹600)       │
// │     [Book at Contracted] [View Rate Card]                 │
// │                                                       │
// │  🔥 Flash Deal: Sunset Paradise · 5★ · Seminyak          │
// │     ₹5,500/night (was ₹9,000) · All-inclusive             │
// │     ⏳ 6 hours remaining · 2 rooms left                    │
// │     [Grab Deal] [Details]                                 │
// │                                                       │
// │  [RFQ for Group] [Allotment Exchange] [Saved Suppliers]   │
// └─────────────────────────────────────────────────────┘
```

### Spot Buying Workflow

```typescript
interface SpotBuyingWorkflow {
  // When contracted inventory runs out
  spot_buy_triggers: {
    SOLD_OUT: "Contracted hotel fully booked for requested dates";
    OVERBOOKED: "Agency has more customers than allotted rooms";
    NEW_DESTINATION: "Customer wants destination agency doesn't have contracts for";
    UNEXPECTED_DEMAND: "Seasonal demand exceeded forecast by 30%+";
    SUPPLIER_FAILURE: "Contracted supplier cancelled or went bankrupt";
    QUALITY_UPGRADE: "Customer wants upgrade beyond contracted inventory";
  };

  spot_buy_process: {
    STEP_1_ALERT: {
      trigger: "Agent searches contracted inventory → no availability";
      action: "System shows 'Contracted rates unavailable' + marketplace options";
      time_budget: "Agent needs answer within 5 minutes to keep customer engaged";
    };

    STEP_2_COMPARE: {
      action: "System pulls marketplace rates alongside contracted rates";
      display: "Show price delta, quality comparison, and reliability score";
      recommendation: "Highlight best-value option based on past reliability";
    };

    STEP_3_BOOK: {
      options: {
        INSTANT_CONFIRM: "Pre-approved credit line → instant booking at marketplace rate";
        REQUEST_QUOTE: "RFQ to 3-5 suppliers → compare → select within 2 hours";
        HOLD_REQUEST: "24-hour hold on inventory while confirming with customer";
      };
    };

    STEP_4_MARGIN_CHECK: {
      action: "System calculates impact on trip margin with spot rate";
      display: "Margin with contracted rate vs. margin with spot rate";
      threshold: "Alert if margin drops below minimum (e.g., <8%)";
      options: "Absorb lower margin | Adjust customer price | Find alternative";
    };
  };

  // Emergency sourcing
  emergency_sourcing: {
    SCENARIO: "Customer arrives at hotel, hotel has no reservation";
    PROTOCOL: {
      t_plus_0_min: "Agent receives distress call from customer";
      t_plus_5_min: "Agent searches marketplace for nearby alternatives";
      t_plus_10_min: "Agent confirms backup hotel at marketplace rate";
      t_plus_15_min: "Agent sends new hotel details + transfer arrangement to customer";
      t_plus_30_min: "Customer checked in at alternative hotel";
      t_plus_2_hours: "Issue logged, supplier flagged, follow-up with original hotel";
    };
    COST_HANDLING: "Agency absorbs cost difference if supplier fault; passes to customer if customer-caused change";
  };
}

// ── Spot buy workflow ──
// ┌─────────────────────────────────────────────────────┐
// │  Spot Buy — Bali Hotel · Jun 15-20                        │
// │                                                       │
// │  Contracted: Grand Bali Resort · 5 rooms                  │
// │  Status: ❌ Fully booked for Jun 15-17                    │
// │  Contracted rate: ₹5,800/night                            │
// │                                                       │
// │  Marketplace alternatives:                            │
// │  ┌──────────────────────────────────────────────────┐ │
// │  │ ⭐ Recommended: Bali Sunset Resort · 4★             │ │
// │  │ ₹6,100/night · 0.5km from original · 97% reliable   │ │
// │  │ Margin impact: -2.1% (still above 8% minimum) ✅    │ │
// │  │ [Book Instantly]                                      │ │
// │  └──────────────────────────────────────────────────┘ │
// │  ┌──────────────────────────────────────────────────┐ │
// │  │ 🏨 Kuta Palace · 4★                                │ │
// │  │ ₹4,900/night · 2km away · 88% reliable             │ │
// │  │ Margin impact: +1.5% ✅                              │ │
// │  │ [Book Instantly]                                      │ │
// │  └──────────────────────────────────────────────────┘ │
// │  ┌──────────────────────────────────────────────────┐ │
// │  │ 🔥 Flash: Ocean View Villa · 5★                    │ │
// │  │ ₹5,500/night (was ₹8,200) · Limited: 2 rooms       │ │
// │  │ [Grab Deal]                                           │ │
// │  └──────────────────────────────────────────────────┘ │
// │                                                       │
// │  [Send RFQ to Suppliers] [Adjust Customer Price]          │
// └─────────────────────────────────────────────────────┘
```

### Allotment Management & Exchange

```typescript
interface AllotmentManagement {
  // Manage committed inventory and enable exchange
  allotment_tracking: {
    COMMITTED: {
      description: "Rooms/flights committed to agency for season";
      tracking: "Total committed → Booked → Available → Released";
      release_schedule: "Unsold inventory released 7-14 days before date";
      penalty: "Release too late → pay for unsold inventory";
    };

    HOLD: {
      description: "Temporary hold for customer considering booking";
      duration: "24-48 hours (varies by supplier)";
      limit: "Max 3 holds per agent at a time";
      auto_release: "Hold expires if not confirmed → returns to available pool";
    };

    GUARANTEED: {
      description: "Non-refundable committed booking";
      payment: "Advance or credit line charged immediately";
      cancellation: "Strict cancellation terms (48-72 hours for partial refund)";
    };
  };

  // Allotment exchange between agencies
  exchange: {
    SCENARIO: "Agency A has 5 unsold rooms in Goa for next weekend";
    ACTION: "Agency A posts rooms on exchange at cost + small margin";
    BUYER: "Agency B has a last-minute Goa inquiry → books from exchange";
    FEE: "Platform facilitation fee of 3-5% on exchange transaction";
    BENEFIT: "Agency A recovers cost instead of paying penalty; Agency B serves customer";
    TRUST: "Both agencies verified; original supplier confirms transfer";
  };
}

// ── Allotment dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Allotment Management — Peak Season 2026                  │
// │                                                       │
// │  Inventory Summary:                                   │
// │  Destination  │ Committed │ Booked │ Avail │ Expiring │
// │  ──────────────────────────────────────────────────────  │
// │  Bali         │    20     │   15   │   3   │    2 ⚠️   │
// │  Singapore    │    15     │   12   │   2   │    1      │
// │  Dubai        │    10     │    4   │   6   │    0      │
// │  Thailand     │    25     │   20   │   4   │    1      │
// │                                                       │
// │  Expiring soon (release or sell):                      │
// │  ⚠️ Bali · Grand Resort · 2 rooms · Jun 10-12            │
// │     Release deadline: Jun 3 (3 days)                      │
// │     Options: [Post to Exchange] [Run Flash Deal] [Release]│
// │                                                       │
// │  ⚠️ Thailand · Beach Hotel · 1 room · Jun 8-10           │
// │     Release deadline: Jun 1 (tomorrow)                    │
// │     Options: [Post to Exchange] [Release]                  │
// │                                                       │
// │  [Allotment Calendar] [Exchange Board] [Auto-Release]     │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Real-time availability** — Supplier inventory systems vary wildly (some have APIs, some use WhatsApp). Maintaining real-time availability data requires multiple integration approaches.

2. **Trust and quality assurance** — Agencies booking from unknown suppliers via marketplace risk quality issues. Need robust rating and reliability scoring based on past performance.

3. **Margin compression** — Spot rates are typically 15-30% higher than contracted rates. Agencies must either absorb the cost or adjust customer pricing, both of which are uncomfortable conversations.

4. **Supplier relationship tension** — Bypassing contracted suppliers for marketplace options can strain relationships. Need to frame marketplace as overflow channel, not replacement.

---

## Next Steps

- [ ] Build supplier marketplace search and comparison engine
- [ ] Implement spot buying workflow with margin impact analysis
- [ ] Create allotment management dashboard with exchange capability
- [ ] Design supplier discovery and rating system
