# Dynamic Packaging Engine — Component Assembly & Pricing

> Research document for dynamic trip packaging from individual components, real-time pricing assembly, package templates, and multi-destination routing for travel agencies.

---

## Key Questions

1. **How do we assemble trips from individual components dynamically?**
2. **What pricing models work for dynamic packages?**
3. **How do we handle multi-destination routing and logistics?**
4. **What package templates accelerate the sales process?**

---

## Research Areas

### Component Assembly Engine

```typescript
interface DynamicPackageAssembly {
  // Build trip from individual components
  components: {
    FLIGHT: {
      search_params: ["origin", "destination", "dates", "travelers", "class"];
      sources: ["GDS", "NDC", "LCC direct", "consolidator"];
      constraints: ["arrival before hotel check-in", "departure after activity", "minimum connection time"];
      pricing_model: "Published fare + markup OR net fare + margin";
    };

    ACCOMMODATION: {
      search_params: ["destination", "check_in", "check_out", "room_type", "occupancy"];
      sources: ["Hotel bedbanks", "direct contracts", "chain APIs", "GDS"];
      constraints: ["location within activity radius", "room capacity for travelers", "meal plan preference"];
      pricing_model: "Dynamic rate + markup OR contracted rate + margin";
    };

    ACTIVITY: {
      search_params: ["destination", "date", "traveler_count", "category"];
      sources: ["Viator/KKday API", "direct operators", "in-house inventory"];
      constraints: ["operating hours", "capacity limits", "weather dependency", "advance booking window"];
      pricing_model: "Commission-based OR net rate + markup";
    };

    TRANSFER: {
      search_params: ["pickup", "dropoff", "date", "traveler_count", "vehicle_type"];
      sources: ["Local operators", "aggregator APIs", "in-house fleet"];
      constraints: ["flight arrival time + 45min buffer", "hotel proximity", "luggage capacity"];
      pricing_model: "Per-vehicle flat rate OR per-km + markup";
    };

    VISA: {
      search_params: ["nationality", "destination", "travel_dates", "passport"];
      sources: ["Visa processing partners", "embassy portals"];
      constraints: ["processing time buffer", "document requirements", "validity period"];
      pricing_model: "Service fee + government fee";
    };

    INSURANCE: {
      search_params: ["trip_value", "destination", "traveler_age", "duration"];
      sources: ["Insurance aggregators", "direct insurer APIs"];
      constraints: ["minimum coverage requirements", "activity-specific riders"];
      pricing_model: "Premium based on trip value and risk";
    };
  };

  // Assembly rules
  assembly_rules: {
    SEQUENTIAL: "Flight → Accommodation → Activities → Transfers → Visa → Insurance";
    CONCURRENT: "Search all components simultaneously, then resolve conflicts";
    PRIORITY: "Lock high-variability components first (flights), then stable ones (hotels, activities)";
  };
}

// ── Component assembly UI ──
// ┌─────────────────────────────────────────────────────┐
// │  Dynamic Package Builder — Singapore Family Trip        │
// │  Customer: Sharma family · 2A + 2C · Jun 15-20          │
// │                                                       │
// │  ┌─ Components ─────────────────────────────────────┐│
// │  │                                                   ││
// │  │ ✈️ Flights (LOCKED — price held 24h)              ││
// │  │ DEL→SIN 15 Jun AI-382 · SIN→DEL 20 Jun AI-381    ││
// │  │ ₹32,000/person × 4 = ₹1,28,000                   ││
// │  │ [Change] [Hold Extension]                          ││
// │  │                                                   ││
// │  │ 🏨 Accommodation                                  ││
// │  │ Pan Pacific Orchard · 5N · Family Suite           ││
// │  │ ₹8,500/night × 5 = ₹42,500                       ││
// │  │ [Change Hotel] [Upgrade] [Add Meal Plan]          ││
// │  │                                                   ││
// │  │ 🎢 Activities (3 selected)                        ││
// │  │ Universal Studios · Day 2 · ₹6,800/family        ││
// │  │ Night Safari · Day 3 · ₹3,200/family             ││
// │  │ Gardens by the Bay · Day 4 · ₹2,400/family       ││
// │  │ Total: ₹12,400                                    ││
// │  │ [+ Add Activity] [Replace]                        ││
// │  │                                                   ││
// │  │ 🚗 Transfers                                      ││
// │  │ Airport → Hotel · Day 1 · ₹2,800                 ││
// │  │ Sentosa round trip · Day 2 · ₹1,500              ││
// │  │ Hotel → Airport · Day 5 · ₹2,800                 ││
// │  │ Total: ₹7,100                                     ││
// │  │                                                   ││
// │  │ 📋 Visa (2 adults need e-visa)                    ││
// │  │ Service: ₹1,500/person × 2 = ₹3,000              ││
// │  │                                                   ││
// │  │ 🛡️ Insurance                                      ││
// │  │ Comprehensive · ₹1,800/person × 4 = ₹7,200       ││
// │  └────────────────────────────────────────────────────┘│
// │                                                       │
// │  Package Summary:                                     │
// │  Component cost:    ₹2,00,200                          │
// │  Agency margin:      ₹30,000 (13%)                    │
// │  ────────────────────────────                         │
// │  Customer price:   ₹2,30,200                          │
// │  Per person:        ₹57,550                           │
// │                                                       │
// │  [Generate Proposal] [Save Draft] [Compare Packages]    │
// └─────────────────────────────────────────────────────┘
```

### Dynamic Pricing Assembly

```typescript
interface DynamicPricingAssembly {
  // How pricing is computed from components
  pricing_engine: {
    // Component-level pricing
    component_pricing: {
      NET_RATE: {
        description: "Supplier gives net price, agency adds margin";
        example: "Hotel room rate ₹5,000/night (net) → Agency sells at ₹6,500/night";
        margin_range: "15-30% depending on component type";
      };

      COMMISSION: {
        description: "Supplier gives published price, pays commission";
        example: "Activity ₹2,000 (published) → 15% commission = ₹300 to agency";
        commission_range: "8-25% depending on supplier relationship";
      };

      MARKUP: {
        description: "Agency buys at bulk/contracted rate, marks up";
        example: "Flight ₹28,000 (bulk) → Published ₹32,000 → ₹4,000 markup";
        markup_range: "Variable based on demand and booking window";
      };

      BUNDLED: {
        description: "Pre-negotiated package rate from supplier";
        example: "Resort 3N + 2 activities = ₹45,000 (bundled) vs ₹52,000 (individual)";
        discount_vs_individual: "12-20%";
      };
    };

    // Package-level pricing
    package_pricing: {
      COST_PLUS: {
        formula: "sum(component_costs) + agency_margin + service_fee";
        use_case: "Custom packages, high-touch sales";
        example: "₹2,00,200 (cost) + ₹25,000 (12.5% margin) + ₹5,000 (service) = ₹2,30,200";
      };

      VALUE_BASED: {
        formula: "what_customer_would_pay_individually × discount";
        use_case: "Pre-built packages, website bookings";
        example: "Individual booking: ₹2,80,000 · Package price: ₹2,45,000 (12.5% savings)";
      };

      COMPETITOR_ALIGNED: {
        formula: "min(competitor_price × 0.95, cost + minimum_margin)";
        use_case: "Price-sensitive markets, last-minute deals";
        floor: "Never below cost + 8% margin (business rule)";
      };

      DYNAMIC: {
        formula: "base_price × demand_multiplier × seasonality × days_to_travel";
        use_case: "Hotels, flights, peak season packages";
        factors: {
          demand: "Search volume + booking pace vs. historical";
          seasonality: "Peak/shoulder/off-season multiplier (0.7x - 1.5x)";
          urgency: "Days to travel (< 30 days = higher, > 90 = lower)";
          inventory: "Remaining availability (scarce = higher)";
        };
      };
    };

    // Margin guardrails
    margin_guardrails: {
      MINIMUM_MARGIN: "8% on total package value (hard floor)";
      TARGET_MARGIN: "15% on total package value (default)";
      PREMIUM_MARGIN: "22%+ for luxury/custom packages";
      LOSS_LEADER: "Below minimum only with manager approval + documented rationale";
      ALERT_THRESHOLD: "Flag if any component has negative margin (e.g., meals at -3%)";
    };
  };
}

// ── Pricing assembly view ──
// ┌─────────────────────────────────────────────────────┐
// │  Package Pricing Engine                                   │
// │                                                       │
// │  Component     │ Cost     │ Sell     │ Margin │ %     │
// │  ─────────────────────────────────────────────────── │
// │  Flights       │ ₹1,12,000│ ₹1,28,000│ ₹16,000│ 12.5% │
// │  Hotel (5N)    │ ₹35,000  │ ₹42,500  │ ₹7,500 │ 17.6% │
// │  Activities    │ ₹10,800  │ ₹12,400  │ ₹1,600 │ 12.9% │
// │  Transfers     │ ₹5,800   │ ₹7,100   │ ₹1,300 │ 18.3% │
// │  Visa          │ ₹2,400   │ ₹3,000   │ ₹600   │ 20.0% │
// │  Insurance     │ ₹5,800   │ ₹7,200   │ ₹1,400 │ 19.4% │
// │  ─────────────────────────────────────────────────── │
// │  Subtotal      │ ₹1,71,800│ ₹2,00,200│ ₹28,400│ 14.2% │
// │  Service fee   │          │ ₹5,000   │ ₹5,000 │ —     │
// │  ─────────────────────────────────────────────────── │
// │  TOTAL         │ ₹1,71,800│ ₹2,05,200│ ₹33,400│ 16.3% │
// │                                                       │
// │  ✅ Above 15% target margin                            │
// │  ⚠️ Activities margin below 15% — consider swap       │
// │                                                       │
// │  [Adjust Margins] [Lock Pricing] [Generate Quote]       │
// └─────────────────────────────────────────────────────┘
```

### Multi-Destination Routing

```typescript
interface MultiDestinationRouting {
  // Plan complex multi-city/country itineraries
  routing_engine: {
    // Route optimization
    optimization: {
      MINIMIZE_TRAVEL_TIME: "Sort destinations by geographic proximity, minimize backtracking";
      MINIMIZE_COST: "Choose routing that minimizes total transport cost";
      BALANCED: "Optimize for best experience within budget (default)";
    };

    // Routing constraints
    constraints: {
      MAX_CITIES_PER_TRIP: 6;
      MIN_STAY_PER_CITY: "1 night";
      TRAVEL_DAY_BUFFER: "0.5 day per city change (packing, transit, check-in)";
      VISA_OVERLAP: "All destinations must be visa-feasible for traveler nationality";
      SEASONALITY: "Avoid monsoon/closed season at each destination";
    };

    // Route patterns
    patterns: {
      LINEAR: "A → B → C → D (one direction, e.g., Europe rail trip)";
      HUB_SPOKE: "Base city → day trips → next base (e.g., Singapore → KL → Singapore)";
      CIRCULAR: "Start and end at same city (e.g., Golden Triangle: Delhi → Jaipur → Agra → Delhi)";
      ISLAND_HOP: "Island 1 → Island 2 → Island 3 (e.g., Thailand: Phuket → Krabi → Koh Samui)";
    };
  };

  // Example: Multi-destination routing
  example: {
    trip: "Europe Grand Tour — 14 days";
    destinations: ["Paris", "Switzerland (Lucerne)", "Italy (Rome, Florence)"];
    routing: {
      option_A: {
        path: "DEL → Paris (4N) → Lucerne (3N) → Florence (3N) → Rome (3N) → DEL";
        flights: "DEL-CDG · CDG-ZRH · FLR-FCO (train) · FCO-DEL";
        travel_days: 3 (flights + train transfers);
        cost: "₹3,20,000/person";
        experience_rating: "4.2/5 (too many travel days)";
      };
      option_B: {
        path: "DEL → Paris (3N) → Lucerne (4N, base) → day trips → Florence (3N) → Rome (3N) → DEL";
        flights: "DEL-CDG · CDG-ZRH · ZRH-FLR · FCO-DEL";
        travel_days: 3 (flights only, Swiss base avoids packing/unpacking)";
        cost: "₹2,95,000/person (saves on Swiss hotel changes)";
        experience_rating: "4.7/5 (recommended)";
      };
    };
  };
}

// ── Multi-destination routing ──
// ┌─────────────────────────────────────────────────────┐
// │  Route Planner — Europe Grand Tour                      │
// │  14 days · 4 travelers · June 2026                      │
// │                                                       │
// │  Recommended Route (Option B):                         │
// │                                                       │
// │  DEL ──✈️──▶ Paris ──✈️──▶ Lucerne ──✈️──▶ Florence ──🚆──▶ Rome ──✈️──▶ DEL│
// │       3N          4N (base)      3N           3N       │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Day 1-3: Paris (Eiffel, Louvre, Seine)         │   │
// │  │ Day 4-7: Lucerne (Mt. Titlis, Interlaken day   │   │
// │  │          trip, Jungfrau day trip)               │   │
// │  │ Day 8-10: Florence (Uffizi, Tuscany day trip)   │   │
// │  │ Day 11-13: Rome (Colosseum, Vatican, Trastevere)│   │
// │  │ Day 14: Departure                               │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Route comparison:                                    │
// │  Option A (linear):  ₹3.2L · 4.2★ · 3 travel days    │
// │  Option B (hub-spoke): ₹2.95L · 4.7★ · 3 travel days │
// │  Option C (open jaw): ₹3.4L · 4.5★ · 2 travel days   │
// │                                                       │
// │  ⚠️ Visa: Schengen covers all destinations             │
// │  ⚠️ Season: June = peak (book hotels early)            │
// │                                                       │
// │  [Select Route] [Customize] [Save as Template]          │
// └─────────────────────────────────────────────────────┘
```

### Package Template Library

```typescript
interface PackageTemplateLibrary {
  // Pre-built package templates for quick assembly
  templates: {
    DESTINATION_STARTER: {
      description: "Base template per destination with recommended components";
      example: {
        name: "Singapore Starter — 5N/6D Family";
        includes: ["Round-trip flights", "4-star hotel (5N)", "Airport transfers", "2 activities", "Visa assistance", "Insurance"];
        excludes: ["Meals", "additional activities", "shopping"];
        price_range: "₹55,000 - ₹75,000/person";
        customization_points: ["Hotel upgrade/downgrade", "Activity swap", "Meal plan add-on", "Extension nights"];
      };
    };

    THEME_BASED: {
      description: "Themed packages for specific interests";
      examples: [
        { name: "Honeymoon Special — Bali", duration: "6N/7D", highlights: ["Private villa", "Couples spa", "Sunset dinner", "Photography session"] },
        { name: "Adventure — New Zealand", duration: "10N/11D", highlights: ["Bungee jumping", "Milford Sound", "Hobbiton", "Glacier walk"] },
        { name: "Pilgrimage — Varanasi + Ayodhya", duration: "4N/5D", highlights: ["Ganga Aarti", "Temple visits", "Sarnath", "Boat ride"] },
        { name: "Shopping + Food — Bangkok + Pattaya", duration: "5N/6D", highlights: ["Floating market", "Street food tour", "MBK shopping", "Coral Island"] },
      ];
    };

    SEASONAL: {
      description: "Season-specific packages";
      examples: [
        { name: "Summer Escape — Kashmir", months: "May-Aug", target: "Families escaping heat" },
        { name: "Winter Wonderland — Switzerland", months: "Dec-Feb", target: "Couples, skiing" },
        { name: "Monsoon Getaway — Kerala", months: "Jun-Sep", target: "Couples, Ayurveda" },
        { name: "Diwali Special — Dubai", months: "Oct-Nov", target: "Families, shopping" },
      ];
    };

    BUDGET_TIERED: {
      description: "Same destination at different price points";
      example: {
        destination: "Singapore 5N/6D";
        tiers: {
          BUDGET: { hotel: "3-star", activities: "1 included", meals: "Breakfast only", price: "₹45,000/person" };
          STANDARD: { hotel: "4-star", activities: "3 included", meals: "Breakfast + 2 dinners", price: "₹62,000/person" };
          PREMIUM: { hotel: "5-star", activities: "5 included", meals: "All meals", price: "₹85,000/person" };
          LUXURY: { hotel: "5-star suite", activities: "VIP/private", meals: "All meals + fine dining", price: "₹1,20,000/person" };
        };
      };
    };
  };
}

// ── Package template library ──
// ┌─────────────────────────────────────────────────────┐
// │  Package Templates                                       │
// │                                                       │
// │  [Destination] [Theme] [Season] [Budget] [+ Create]    │
// │                                                       │
// │  🏙️ Singapore Family — 5N/6D                           │
// │  ★ 4.8 · Used 34 times · 67% conversion               │
// │  Budget: ₹45K · Standard: ₹62K · Premium: ₹85K        │
// │  [Use Template] [Edit] [Analytics]                     │
// │                                                       │
// │  🏖️ Bali Honeymoon — 6N/7D                             │
// │  ★ 4.9 · Used 28 times · 72% conversion               │
// │  Budget: ₹38K · Standard: ₹55K · Premium: ₹78K        │
// │  [Use Template] [Edit] [Analytics]                     │
// │                                                       │
// │  🏔️ Kashmir Summer — 4N/5D                             │
// │  ★ 4.6 · Used 22 times · 58% conversion               │
// │  Budget: ₹22K · Standard: ₹35K · Premium: ₹52K        │
// │  [Use Template] [Edit] [Analytics]                     │
// │                                                       │
// │  🌍 Europe Grand Tour — 14N/15D                        │
// │  ★ 4.7 · Used 12 times · 42% conversion               │
// │  Budget: ₹2.4L · Standard: ₹3.2L · Premium: ₹4.5L    │
// │  [Use Template] [Edit] [Analytics]                     │
// │                                                       │
// │  Most popular this month: Singapore Family (+18%)       │
// │  Highest conversion: Bali Honeymoon (72%)               │
// │                                                       │
// │  [+ New Template] [Import] [Clone & Customize]          │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Component price volatility** — Flight and hotel prices change every few minutes. A package quoted at ₹2.3L may cost ₹2.5L when customer decides 2 hours later. Need price hold mechanisms (24h hold for ₹500 deposit?).

2. **Multi-supplier coordination** — A single trip may involve 5+ suppliers. Each has different cancellation terms, payment schedules, and communication channels. Need unified supplier management layer.

3. **Margin optimization across components** — Low-margin flights can be offset by high-margin activities. Need holistic margin view, not per-component floor enforcement.

4. **Customs duty on imported packages** — For Indian agencies selling international packages, customs and tax implications vary by component type. Need tax-aware pricing assembly.

---

## Next Steps

- [ ] Build component assembly engine with multi-source search
- [ ] Implement dynamic pricing with margin guardrails
- [ ] Create multi-destination route optimization
- [ ] Design package template library with conversion tracking
