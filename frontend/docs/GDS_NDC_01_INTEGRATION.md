# GDS & NDC Integration — Technical Architecture

> Research document for Global Distribution System integration (Amadeus, Sabre, Travelport), New Distribution Capability (NDC) standard, API cost management, caching strategies, and airline/hotel connectivity for the Waypoint OS platform.

---

## Key Questions

1. **How do we integrate with GDS platforms (Amadeus, Sabre, Travelport)?**
2. **What is NDC and how does it change travel distribution?**
3. **How do we manage API costs and rate limiting for paid travel APIs?**
4. **What's the architecture for multi-source inventory aggregation?**

---

## Research Areas

### GDS Integration Architecture

```typescript
interface GDSIntegration {
  // Major Global Distribution Systems
  gds_platforms: {
    AMADEUS: {
      market_share: "40%+ of global travel agency bookings";
      api_suite: {
        SELF_SERVE: {
          description: "Free tier for development, paid for production";
          pricing: "Free up to 10K calls/month; ₹0.50-2 per call after";
          endpoints: ["Flight Search", "Hotel Search", "PNR Create", "Fare Rules", "Seat Map"];
          auth: "OAuth 2.0 (API key + secret → Bearer token)";
          rate_limits: "4 requests/second (free), 20/second (paid)";
        };

        ENTERPRISE: {
          description: "Dedicated access for high-volume agencies";
          pricing: "₹2-5L/year minimum commitment + per-transaction fee";
          benefit: "Higher rate limits, dedicated support, priority access to inventory";
          requirement: "IATA accreditation + agency registration";
        };
      };

      key_apis: {
        FLIGHT_OFFERS_SEARCH: "POST /v2/shopping/flight-offers";
        FLIGHT_PRICING: "POST /v1/shopping/flight-offers/pricing";
        FLIGHT_ORDER_CREATE: "POST /v1/booking/flight-orders";
        HOTEL_SEARCH: "GET /v1/reference-data/locations/hotel";
        HOTEL_OFFERS: "GET /v3/shopping/hotel-offers";
        HOTEL_BOOKING: "POST /v1/booking/hotel-bookings";
        SEAT_MAP: "POST /v1/shopping/seatmaps";
        PNR_MANAGE: "POST /v1/booking/flight-orders/{id}";
      };

      indian_market: "Strong presence — most Indian OTAs and agencies use Amadeus";
    };

    SABRE: {
      market_share: "30%+ globally, strong in North America";
      api_suite: {
        SABRE_DEV_STUDIO: {
          description: "REST APIs for developers";
          pricing: "Free sandbox; production pricing varies by volume";
          endpoints: ["Bargain Finder Max (flight search)", "Hotel Search", "Create PNR"];
          auth: "OAuth 2.0 with session tokens";
        };

        REDX: {
          description: "Sabre's NDC-enabled API platform";
          benefit: "Access to NDC content from participating airlines";
          status: "Growing airline adoption in Indian market";
        };
      };

      indian_market: "Moderate presence — used by some large agencies and consolidators";
    };

    TRAVELPORT: {
      market_share: "20%+ globally (Galileo, Worldspan, Apollo)";
      api_suite: {
        TRAVELPORT_PLUS: {
          description: "Unified API platform (REST + JSON)";
          pricing: "Usage-based with volume discounts";
          endpoints: ["Search", "Price", "Book", "Manage"];
          benefit: "Simpler API design than Amadeus/Sabre";
        };
      };

      indian_market: "Smaller presence via Galileo — some agencies in South India";
    };
  };
}

// ── GDS integration dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  GDS Integration — Connection Status                      │
// │                                                       │
// │  Amadeus:                                             │
// │  🔗 Connected · Environment: Production                    │
// │  Auth: OAuth 2.0 · Token refreshes: Every 30 min          │
// │  API calls today: 2,847 · Rate limit: 20/sec              │
// │  Avg response: 340ms · Error rate: 0.3%                   │
// │  [Test Connection] [View Logs] [Rate Limits]               │
// │                                                       │
// │  Sabre:                                               │
// │  🔗 Connected · Environment: Sandbox                      │
// │  Auth: OAuth 2.0 · Session: Active                        │
// │  API calls today: 142 · Rate limit: 4/sec (sandbox)       │
// │  Status: Testing NDC content access                        │
// │  [Upgrade to Production] [Test]                             │
// │                                                       │
// │  API Cost Tracker (this month):                       │
// │  Amadeus flight search: 1,240 calls × ₹1.2 = ₹1,488      │
// │  Amadeus hotel search:    890 calls × ₹0.8 = ₹712         │
// │  Amadeus booking:          85 calls × ₹3.0 = ₹255         │
// │  Sabre (sandbox):          142 calls × ₹0   = ₹0          │
// │  Total: ₹2,455 of ₹10,000 budget (24.5%)                  │
// │  [Cost Report] [Budget Alerts] [Optimize Caching]          │
// └─────────────────────────────────────────────────────┘
```

### NDC (New Distribution Capability)

```typescript
interface NDCStandard {
  // IATA NDC standard for airline distribution
  ndc_overview: {
    what: "IATA standard (Resolution 793) for XML-based airline distribution";
    why: "Replace legacy EDIFACT with modern API-based airline content access";
    benefit_for_agencies: {
      richer_content: "Full airline ancillaries (seat selection, meals, baggage, lounge) directly from airline";
      dynamic_pricing: "Real-time airline pricing with offers, not static fares";
      personalized_offers: "Airlines can provide customer-specific pricing based on loyalty/status";
      transparency: "See exactly what airline is offering, no intermediary markup confusion";
    };

    current_adoption_india: {
      airlines_offering_ndc: ["IndiGo (NDC pioneer)", "Vistara", "Air India", "SpiceJet (partial)"];
      international_via_ndc: ["Singapore Airlines", "Emirates", "Qatar Airways", "Lufthansa", "British Airways"];
      ota_adoption: "MakeMyTrip, Cleartrip, Goiblis testing NDC";
      agency_adoption: "Very low — most agencies still use GDS EDIFACT or OTA portals";
    };

    challenges: {
      migration_cost: "NDC requires new API integrations alongside existing GDS";
      content_gap: "Not all airlines offer full content via NDC yet";
      complexity: "NDC XML messages are complex (Offer/Order model vs. PNR model)";
      training: "Agents need to understand new booking flow (Shop → Order vs. Search → Book)";
    };
  };

  // NDC message flow
  ndc_message_flow: {
    SHOPPING: {
      AirShoppingRQ: "Request flight offers with preferences";
      AirShoppingRS: "Response with available offers including ancillaries";
    };

    PRICING: {
      OfferPriceRQ: "Request final price for selected offer";
      OfferPriceRS: "Confirmed price with full breakdown";
    };

    ORDERING: {
      OrderCreateRQ: "Create order (replaces PNR creation)";
      OrderCreateRS: "Order confirmation with order ID";
      OrderRetrieveRQ: "Retrieve order details";
      OrderCancelRQ: "Cancel an order";
      OrderChangeRQ: "Modify order (change date, add ancillary)";
    };

    SERVICING: {
      ServiceListRQ: "List available ancillary services for an offer";
      ServicePriceRQ: "Price a specific ancillary service";
    };
  };

  // GDS vs NDC comparison
  comparison: {
    TRADITIONAL_GDS: {
      protocol: "EDIFACT (legacy) or REST API wrapping EDIFACT";
      content: "Standardized fares from ATPCo — limited ancillary access";
      pricing: "Filed fares + negotiated rates — static until re-shopped";
      booking: "PNR-based (passenger name record)";
      settlement: "BSP (Billing and Settlement Plan)";
      advantage: "Mature, reliable, all airlines, all content";
      limitation: "Limited ancillary access, static pricing, intermediary model";
    };

    NDC: {
      protocol: "XML/REST API (IATA standard)";
      content: "Full airline catalog including all ancillaries and services";
      pricing: "Dynamic, personalized offers directly from airline";
      booking: "Order-based (Offer + Order model)";
      settlement: "Varies — some via BSP, some direct settlement";
      advantage: "Richer content, dynamic pricing, direct airline relationship";
      limitation: "Incomplete airline coverage, complex XML, evolving standard";
    };

    HYBRID_APPROACH: {
      description: "Use GDS for broad coverage + NDC for airlines with rich content";
      strategy: "Default to GDS search; augment with NDC for airlines that offer better content";
      benefit: "Best of both — complete coverage + rich ancillaries";
      cost: "Double integration effort but justified by revenue from ancillary sales";
    };
  };
}

// ── NDC vs GDS comparison view ──
// ┌─────────────────────────────────────────────────────┐
// │  Flight Search — Delhi → Singapore · Jun 15               │
// │                                                       │
// │  GDS Results (Amadeus):                               │
// │  IndiGo 6E-37 · Dep 08:15 · ₹12,400 · Economy Saver     │
// │     Base fare only · Ancillaries: Add at airline website  │
// │  Singapore Airlines SQ-403 · Dep 09:45 · ₹28,600         │
// │     Base fare + standard baggage · Meal included           │
// │                                                       │
// │  NDC Results (IndiGo Direct):                         │
// │  IndiGo 6E-37 · Dep 08:15 · ₹11,800 · NDC Offer          │
// │     ✈️ Base: ₹9,200 + 🧳 Baggage 20kg: ₹1,100            │
// │     🍽️ Meal: ₹600 + 💺 Seat selection: ₹400               │
// │     📱 NDC Exclusive: ₹200 off with Express boarding      │
// │     → Total: ₹11,800 (₹600 cheaper than GDS)             │
// │     → Ancillary margin for agency: ₹450 (sell at markup)  │
// │                                                       │
// │  [Book via GDS] [Book via NDC] [Compare Both]             │
// └─────────────────────────────────────────────────────┘
```

### API Cost Management & Caching

```typescript
interface APICostManagement {
  // Managing costs for paid travel APIs
  cost_structure: {
    AMADEUS: {
      flight_search: "₹0.80-1.50 per search";
      hotel_search: "₹0.50-1.00 per search";
      flight_pricing: "₹1.50-3.00 per pricing request";
      booking_create: "₹2.50-5.00 per booking";
      monthly_minimum: "₹5,000 (self-serve) or ₹2L+ (enterprise)";
    };

    SABRE: {
      flight_search: "₹0.60-1.20 per search";
      hotel_search: "₹0.40-0.80 per search";
      booking: "₹2.00-4.00 per booking";
    };

    THIRD_PARTY_AGGREGATORS: {
      daukr: "₹0.30-0.60 per flight search";
      kiwi_tequila: "₹0.20-0.50 per search";
      hotelbeds: "₹0.40-0.80 per hotel search";
    };
  };

  // Cost optimization strategies
  caching_strategy: {
    FLIGHT_SEARCH: {
      cache_ttl: "15 minutes for domestic, 30 minutes for international";
      cache_key: "origin + destination + date + airline (optional)";
      hit_rate_target: "40-60% (many searches are repeat or similar)";
      invalidation: "Price change alerts from GDS webhook → invalidate cache";
      cost_saving: "40% fewer API calls = 40% cost reduction";
    };

    HOTEL_SEARCH: {
      cache_ttl: "60 minutes for availability, 30 minutes for rates";
      cache_key: "hotel_id + check_in + check_out + occupancy";
      hit_rate_target: "50-70% (agents often search same hotels)";
      cost_saving: "50% fewer API calls";
    };

    STATIC_DATA: {
      description: "Airline codes, airport data, city mappings — rarely changes";
      cache_ttl: "24 hours to weekly";
      cache_key: "Data type + record ID";
      hit_rate_target: "95%+";
      storage: "Local database sync from API — not per-request";
    };
  };

  // Rate limiting management
  rate_management: {
    REQUEST_QUEUING: {
      description: "Queue API requests and process at optimal rate";
      mechanism: "Token bucket algorithm per API provider";
      benefit: "Stay within rate limits without wasting capacity";
    };

    BATCHING: {
      description: "Combine multiple similar requests into one";
      example: "3 agents searching Singapore hotels → 1 API call with 3 hotel IDs";
      benefit: "Fewer API calls, better rate utilization";
    };

    PRIORITY_QUEUING: {
      description: "Prioritize booking-related API calls over browsing";
      levels: {
        CRITICAL: "Booking creation, ticketing (always immediate)";
        HIGH: "Active customer on phone searching (process within 2s)";
        MEDIUM: "Agent browsing for proposal preparation (within 10s)";
        LOW: "Background data refresh, price monitoring (within 60s)";
      };
    };
  };
}

// ── API cost optimization dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  API Cost Management — Monthly Overview                   │
// │                                                       │
// │  Spending (Apr 2026):                                 │
// │  Amadeus:   ₹8,200 (62%) · 6,840 calls                   │
// │  Sabre:     ₹1,800 (14%) · 2,100 calls                    │
// │  HotelBeds: ₹2,400 (18%) · 3,200 calls                    │
// │  Other:       ₹800 (6%) · 1,100 calls                     │
// │  Total:    ₹13,200 of ₹20,000 budget (66%)                │
// │                                                       │
// │  Optimization:                                        │
// │  Cache hit rate: 48% · Saving: ~₹5,800/month              │
// │  Without caching would be: ₹19,000 (over budget)          │
// │  Batch savings: 12% fewer calls through request combining │
// │                                                       │
// │  Cost per booking:                                    │
// │  Avg API cost per booking: ₹82                            │
// │  Avg booking value: ₹52,000                               │
// │  API cost as % of booking: 0.16% ✅                       │
// │                                                       │
// │  Rate limit status:                                   │
// │  Amadeus: 12/sec of 20/sec · ✅ Healthy                    │
// │  Sabre:   3/sec of 4/sec (sandbox) · ⚠️ Near limit        │
// │                                                       │
// │  [Optimize Caching] [Budget Forecast] [Provider Compare]  │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **NDC maturity** — NDC is still evolving. Airlines implement different versions with different capabilities. Building for NDC today means constant adaptation as the standard matures and airlines add features.

2. **Dual inventory management** — Same flight may appear via GDS and NDC at different prices with different ancillaries. Need intelligent deduplication and best-offer selection without confusing agents.

3. **API cost unpredictability** — During peak season (Oct-Feb in India), search volume spikes 3-5x, causing API costs to spike proportionally. Need budget alerts and automatic caching aggressiveness adjustment.

4. **GDS certification barrier** — Getting Amadeus/Sabre production access requires IATA accreditation, business verification, and sometimes minimum volume commitments. Small agencies can't access GDS directly.

---

## Next Steps

- [ ] Build Amadeus API integration with OAuth 2.0 authentication flow
- [ ] Implement multi-layer caching with TTL-based invalidation
- [ ] Create API cost tracking dashboard with budget alerts
- [ ] Design NDC adapter layer for direct airline content access
- [ ] Build request queuing system with priority-based processing
