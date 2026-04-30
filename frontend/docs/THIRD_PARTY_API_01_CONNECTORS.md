# Third-Party Travel API Connectors — Activity, Hotel & Service Aggregators

> Research document for travel API connectors beyond GDS — activity aggregators, hotel bedbanks, transfer APIs, insurance APIs, and visa processing APIs for the Waypoint OS platform.

---

## Key Questions

1. **What third-party travel APIs provide inventory beyond GDS?**
2. **How do activity aggregators (Viator, Klook, GetYourGuide) work?**
3. **What hotel bedbank APIs (Hotelbeds, WebBeds) provide access to contracted inventory?**
4. **How do we unify multi-source API responses into a single search result?**

---

## Research Areas

### Activity & Experience Aggregators

```typescript
interface ActivityAggregators {
  // APIs for tours, activities, and experiences
  aggregators: {
    VIATOR_TRIPADVISOR: {
      parent: "TripAdvisor Group";
      inventory: "300K+ bookable experiences in 2,500+ destinations";
      api: {
        name: "Viator API (now called TripAdvisor Experiences)";
        auth: "API key in header";
        endpoints: {
          search_products: "GET /products/search (by destination, date, category)";
          product_details: "GET /products/{productId}";
          check_availability: "GET /availability/schedules/{productId}";
          create_booking: "POST /booking/book";
          cancel_booking: "POST /booking/cancel";
        };
        pricing: {
          commission: "8-15% of retail price (you sell at Viator's price, keep commission)";
          model: "Agency model — you earn commission, no upfront cost";
          min_payout: "₹5,000";
          payment: "Monthly payout for previous month's bookings";
        };
        content: {
          reviews: "TripAdvisor review scores included";
          photos: "High-quality images for each experience";
          descriptions: "Detailed descriptions with inclusions/exclusions";
          cancellation: "Per-product cancellation policy (most: free cancel 24-48h before)";
        };
      };
      strengths: "Largest inventory globally, strong in tourist destinations, good reviews integration";
      weakness: "Commission model (can't set your own markup), limited exclusive content";
    };

    KLOOK: {
      origin: "Asia-focused activity platform";
      inventory: "100K+ activities, strong in Asia-Pacific";
      api: {
        auth: "API key + OAuth";
        endpoints: "Similar to Viator — search, details, availability, book, cancel";
        pricing: {
          commission: "5-12% commission per booking";
          model: "Agency or merchant model (option to set your own price)";
        };
      };
      strengths: "Best Asia coverage (Singapore, Thailand, Japan, Korea, Bali), competitive prices";
      weakness: "Weaker outside Asia, fewer reviews than Viator/TripAdvisor";
    };

    GETYOURGUIDE: {
      origin: "European activity platform";
      inventory: "60K+ experiences globally";
      api: {
        auth: "API key";
        pricing: {
          commission: "10-18% (varies by product and volume)";
          model: "Agency model";
        };
      };
      strengths: "Strong Europe coverage, curated quality (vetted suppliers), good descriptions";
      weakness: "Smaller inventory than Viator, weaker Asia coverage";
    };

    TIQETS: {
      origin: "Museum and attraction ticketing";
      inventory: "Museum entries, skip-the-line tickets, city passes";
      api: {
        auth: "API key";
        pricing: "Commission 8-15% per ticket";
      };
      strengths: "Best for museum/attraction tickets in Europe, instant confirmation";
    };
  };

  // Unified activity search
  unified_search: {
    description: "Search across all aggregators simultaneously, deduplicate, present best options";
    mechanism: {
      step_1: "Customer/agent searches 'Singapore activities Jun 15'";
      step_2: "Query sent to Viator + Klook + direct contracts in parallel";
      step_3: "Results merged, deduplicated (same activity from multiple sources)";
      step_4: "Sort by: price, rating, relevance, commission for agency";
      step_5: "Display unified results with source indicator";
    };

    deduplication: {
      challenge: "Same activity appears on Viator AND Klook at different prices";
      approach: "Match by activity name + location + duration → group variants";
      display: "Show lowest price variant, mark 'Also available from {other source}'";
    };
  };
}

// ── Activity aggregator dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Activity Search — Singapore · Jun 15, 2026               │
// │                                                       │
// │  Results: 42 activities · 3 sources                      │
// │                                                       │
// │  🎢 Universal Studios Singapore                           │
// │     Viator: ₹3,200 · Klook: ₹2,800 ⬅ Best price         │
// │     ⭐ 4.5 (12,400 reviews) · Instant confirmation        │
// │     Commission: ₹280 (10%) · [Book via Klook]             │
// │                                                       │
// │  🌃 Night Safari Experience                               │
// │     Direct contract: ₹2,200 · Viator: ₹2,500             │
// │     ⭐ 4.6 (8,200 reviews) · Direct is ₹300 cheaper ⬅     │
// │     Commission: ₹220 (10%) · [Book Direct]                 │
// │                                                       │
// │  🍳 Cooking Class — Local Hawker Tour                      │
// │     GetYourGuide: ₹3,800 · Only on this platform          │
// │     ⭐ 4.8 (340 reviews) · Curated quality ✨              │
// │     Commission: ₹570 (15%) · [Book via GYG]               │
// │                                                       │
// │  Source breakdown:                                     │
// │  Viator: 22 activities · Klook: 14 · GYG: 8 · Direct: 6  │
// │  [Filter by Source] [Sort by Price] [Sort by Rating]       │
// └─────────────────────────────────────────────────────┘
```

### Hotel Bedbank & Wholesaler APIs

```typescript
interface HotelBedbankAPIs {
  // Wholesale hotel inventory APIs
  bedbanks: {
    HOTELBEDS: {
      description: "World's largest hotel bedbank (part of WebBeds group)";
      inventory: "180K+ hotels in 190+ countries";
      api: {
        name: "Hotelbeds API";
        version: "V5.0 (REST JSON)";
        auth: "API key + signature (HMAC-SHA256 of key + secret + timestamp)";
        endpoints: {
          hotel_search: "POST /hotel-api/1.0/hotels (by destination, dates, occupancy)";
          hotel_details: "GET /hotel-content-api/1.0/hotels/{hotelCode}";
          booking_create: "POST /hotel-api/1.0/bookings";
          booking_cancel: "DELETE /hotel-api/1.0/bookings/{bookingReference}";
          booking_details: "GET /hotel-api/1.0/bookings/{bookingReference}";
        };
        pricing: {
          model: "Net rate model — you see net price, set your own selling price";
          markup: "Agency sets markup (typically 15-30% on net rate)";
          payment: "Agency pays net rate at booking; customer pays agency's selling price";
          advantage: "Full control over markup vs. fixed commission model";
        };
        content: {
          descriptions: "Detailed hotel descriptions, facilities, photos";
          geo_data: "Exact coordinates, nearby attractions, airport distance";
          reviews: "Aggregated review scores";
        };
        cancellation: "Per-rate cancellation policy (non-refundable to free cancel 24h before)";
      };
      strengths: "Largest inventory, net rate model (full markup control), reliable";
      weakness: "Requires pre-payment commitment (₹1-5L deposit or credit line)";
    };

    WEBBEDS: {
      description: "Second largest bedbank, strong in Asia-Pacific";
      api: {
        endpoints: "Similar to Hotelbeds — search, book, manage";
        pricing: "Net rate model with volume-based discounts";
      };
      strengths: "Strong Asia-Pacific inventory, competitive rates for Thai/Bali/Singapore";
      weakness: "Smaller global coverage than Hotelbeds";
    };

    STUBA_GRNCONNECT: {
      description: "Indian hotel aggregator with 15,000+ Indian hotels";
      api: {
        pricing: "Net rate model, Indian hotel specialization";
        strength: "Best rates for domestic Indian hotels";
      };
      use_case: "Domestic travel packages where Indian hotel inventory is primary";
    };

    TRAVCOLOGY_GTA: {
      description: "Asia-focused bedbank";
      strengths: "Strong Southeast Asia inventory, competitive Singapore/Bali rates";
    };
  };

  // Multi-source hotel comparison
  multi_source_comparison: {
    STRATEGY: {
      primary: "Direct hotel contracts for top 20 destinations (best rates, 15-25% below rack)";
      secondary: "Hotelbeds/WebBeds for broad coverage (net rate, 10-15% markup)";
      tertiary: "Aggregators (Booking.com API) for last resort / sold-out situations";
    };

    RATE_COMPARISON: {
      example: {
        hotel: "Marina Bay Sands, Singapore";
        rack_rate: "₹35,000/night";
        direct_contract: "₹22,000/night (37% off rack) ✅ Best";
        hotelbeds: "₹24,500/night (30% off rack)";
        booking_com: "₹28,000/night (20% off rack)";
        selling_price: "₹30,000/night (agency markup on direct contract)";
        margin: "₹8,000/night (36% margin on direct contract)";
      };
    };
  };
}

// ── Hotel source comparison ──
// ┌─────────────────────────────────────────────────────┐
// │  Hotel Rate Comparison — Singapore · Jun 15-20             │
// │  Marina Bay Sands · 5★ · Bay View Room                    │
// │                                                       │
// │  Sources:                                             │
// │  🏆 Direct contract: ₹22,000/night · 37% off rack        │
// │     Min 3 nights · Free cancel 48h · Margin: ₹8,000/night │
// │     [Book Direct] ✅ Best rate                             │
// │                                                       │
// │  📦 Hotelbeds: ₹24,500/night · 30% off rack              │
// │     Net rate · Non-refundable · Margin: ₹5,500/night      │
// │     [Book Hotelbeds]                                       │
// │                                                       │
// │  🌐 Booking.com: ₹28,000/night · 20% off rack            │
// │     Commission: 15% · Free cancel 24h · Margin: ₹2,000    │
// │     [Book Booking.com] (fallback only)                     │
// │                                                       │
// │  Recommendation: Book via Direct Contract                  │
// │  5-night saving vs. Booking.com: ₹30,000                  │
// │  [Confirm Booking] [Compare Other Hotels]                  │
// └─────────────────────────────────────────────────────┘
```

### Service & Utility APIs

```typescript
interface ServiceUtilityAPIs {
  // Supporting APIs for non-core travel services
  service_apis: {
    TRANSFER: {
      providers: {
        HOPPY_RIDE: {
          coverage: "Airport transfers in 100+ countries";
          api: "REST API with instant confirmation";
          pricing: "Net rate + markup model";
          strength: "India-focused, covers Tier 2 cities";
        };

        SUNTRANSFERS: {
          coverage: "Global airport transfers";
          api: "XML/REST API";
          pricing: "Commission model (15-20%)";
          strength: "Global coverage, reliable";
        };

        WELCOME_PICKUPS: {
          coverage: "Airport transfers with meet & greet in 60+ countries";
          api: "REST API";
          pricing: "Commission (15-25%)";
          strength: "Premium experience, driver tracks flight";
        };
      };
    };

    INSURANCE: {
      providers: {
        TATA_AIG: {
          api: "Quoting + issuance API for travel insurance";
          products: "Domestic and international travel insurance";
          pricing: "Commission 15-25% on premium";
          integration: "Quote API → Compare → Issue → Certificate PDF";
        };

        CHOLA_MS: {
          api: "Travel insurance API";
          products: "Schengen visa compliant, international, domestic";
          pricing: "Commission 15-20%";
        };

        WORLD_NOMADS: {
          api: "Global travel insurance for international travelers";
          products: "Adventure sports coverage, long-trip coverage";
          pricing: "Commission 20-30%";
        };
      };
    };

    VISA_PROCESSING: {
      providers: {
        VFS_GLOBAL: {
          coverage: "Visa application processing for 60+ countries";
          integration: "No public API — manual process with agent portal";
          status: "Check status via scraping or manual lookup";
        };

        VISA2FLY: {
          coverage: "Indian e-visa and visa assistance platform";
          api: "REST API for visa requirement check and application tracking";
          pricing: "Per-visa commission or white-label fee";
        };

        ATLAS_VISA: {
          coverage: "Visa processing for Indian travelers";
          api: "Requirement check + document collection + submission tracking";
        };
      };
    };

    ESIM_CONNECTIVITY: {
      providers: {
        AIRALO: {
          coverage: "200+ countries eSIM";
          api: "REST API for eSIM purchase and activation";
          pricing: "Commission 10-15% on eSIM sale";
          integration: "Search → Purchase → QR code delivery via WhatsApp";
        };

        HOLAFLY: {
          coverage: "Unlimited data eSIMs in 150+ countries";
          api: "Partner API for eSIM distribution";
          pricing: "Commission 10-15%";
        };
      };
    };
  };
}
```

### Unified API Architecture

```typescript
interface UnifiedAPIArchitecture {
  // How to unify multi-source API responses
  architecture: {
    API_GATEWAY: {
      description: "Single gateway that routes to appropriate provider";
      mechanism: {
        search_request: "Agent/customer searches → Gateway fans out to all providers in parallel";
        response_aggregation: "Gateway collects all responses → normalizes → deduplicates → sorts";
        booking_routing: "Booking sent to the source that provided the selected rate";
      };
    };

    NORMALIZATION_LAYER: {
      description: "Map different provider response schemas to unified internal schema";
      mapping: {
        hotel: "Provider-specific hotel codes → Internal canonical hotel ID";
        activity: "Activity name + location + duration → Deduplication key";
        transfer: "Route (airport + hotel) + vehicle type → Comparison key";
      };
    };

    RATE_CACHING: {
      hotel_rates: "Cache hotel rates for 30 minutes (rates change frequently)";
      activity_rates: "Cache activity availability for 2 hours (less volatile)";
      transfer_rates: "Cache transfer rates for 4 hours (relatively stable)";
      invalidation: "Pre-book check always hits live API (never cache at booking time)";
    };
  };
}
```

---

## Open Problems

1. **Rate parity** — Some suppliers enforce rate parity (selling price must match across channels). Selling below Booking.com price may violate contracts. Need to understand each supplier's parity rules.

2. **API reliability variance** — Viator's API is reliable; smaller aggregators have outages. Need fallback logic: if primary source fails, route to secondary.

3. **Inventory ownership** — When the same hotel room appears on Hotelbeds, WebBeds, and Booking.com, booking via one may remove inventory from others. Need real-time availability checks.

4. **Net rate cash flow** — Bedbank net rate model requires agency to pre-pay. With 50+ active bookings, this ties up ₹5-15L in float. Need working capital management.

---

## Next Steps

- [ ] Build unified activity search aggregator (Viator + Klook + GetYourGuide)
- [ ] Implement Hotelbeds API integration with net rate management
- [ ] Create multi-source hotel rate comparison with best-source recommendation
- [ ] Design unified API gateway with normalization and caching
