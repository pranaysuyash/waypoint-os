# Travel Marketplace & Aggregator — Aggregation Architecture

> Research document for travel deal aggregation architecture, multi-source inventory management, price comparison engine, and inventory normalization.

---

## Key Questions

1. **How do we aggregate inventory from multiple travel suppliers?**
2. **What normalization is needed across different supplier APIs?**
3. **How do we build a unified search across disparate data sources?**
4. **What caching strategy handles high-volume price queries?**
5. **How do we handle supplier API rate limits and reliability?**

---

## Research Areas

### Multi-Source Inventory Aggregation

```typescript
interface InventoryAggregation {
  sources: InventorySource[];
  normalizer: DataNormalizer;
  cache: AggregationCache;
  search: UnifiedSearch;
  reliability: SourceReliability;
}

interface InventorySource {
  id: string;
  name: string;                        // "TBO Holidays", "Hotelbeds", "Amadeus"
  type: SourceType;
  categories: SourceCategory[];
  api: SourceAPI;
  rateLimit: RateLimitConfig;
  reliability: number;                 // 0-100 uptime score
  latency: number;                     // Average response time ms
  cost: CostModel;
}

type SourceType =
  | 'gds'                              // Amadeus, Sabre, Travelport
  | 'bedbank'                          // Hotelbeds, GTA, DOTW
  | 'direct_connect'                   // Direct API with hotel/airline
  | ' consolidator'                    // TBO, Mystifly, Riya
  | 'ota_feed'                         // MakeMyTrip, Goibbi, Cleartrip
  | 'wholesale'                        // DMC, inbound operator rates
  | 'channel_manager';                 // SiteMinder, D-Edge connected hotels

// Inventory source landscape for Indian travel agency:
//
// FLIGHTS:
// 1. Amadeus (GDS): Full airline inventory, fare rules, ticketing
//    - Coverage: All airlines, domestic + international
//    - Latency: 2-5 seconds per search
//    - Cost: Per-search fee + booking fee
//
// 2. TBO (Travel Boutique Online): Indian consolidator
//    - Coverage: Domestic airlines, competitive fares
//    - Latency: 1-3 seconds
//    - Cost: Per-booking commission
//
// 3. NDC Direct Connect: New Distribution Capability feeds
//    - Coverage: Select airlines (IndiGo, Vistara, Air India)
//    - Latency: 1-2 seconds
//    - Cost: Lower than GDS
//
// HOTELS:
// 1. Hotelbeds (Bedbank): Largest hotel wholesaler
//    - Coverage: 170,000+ hotels globally
//    - Latency: 2-4 seconds per search
//    - Cost: Net rates + markup
//
// 2. TBO Hotels: Indian hotel consolidator
//    - Coverage: 50,000+ hotels in India
//    - Latency: 1-3 seconds
//    - Cost: Competitive net rates
//
// 3. Direct Connect: Chain hotels (Taj, Marriott, ITC)
//    - Coverage: Limited to specific chains
//    - Latency: <1 second
//    - Cost: Best rates (corporate/negotiated)
//
// ACTIVITIES:
// 1. Viator/TripAdvisor: Global activity inventory
// 2. Klook: Asia-focused activity bookings
// 3. Local suppliers: Direct contracts with tour operators
//
// TRANSFERS:
// 1. HolidayTaxis: Global airport transfers
// 2. Rome2Rio: Multi-modal transport search
// 3. Local operators: Direct contracts

interface SourceAPI {
  protocol: 'rest' | 'soap' | 'graphql';
  auth: AuthConfig;
  endpoints: APIEndpoint[];
  versioning: string;                  // "v2", "2024-01"
  sandbox: string;                     // Sandbox URL for testing
  production: string;                  // Production URL
  documentation: string;               // Docs URL
}

// API integration patterns:
// Synchronous search: Client calls → Server calls suppliers sequentially → Returns results
//   Simple but slow (5-15 seconds for multi-source search)
//
// Asynchronous search: Client calls → Server calls suppliers in parallel → Streams results
//   Fast (first results in 1-2 seconds) but complex
//
// Pre-cached search: Server pre-fetches popular routes/hotels → Client queries cache
//   Instant (<100ms) but stale data, limited coverage
//
// Hybrid (recommended):
// - Pre-cache popular routes, hotels, and dates
// - For uncached queries: Async parallel search
// - Stream results as they arrive (first results <2s, complete <10s)
// - Background refresh of cached results

interface DataNormalizer {
  flights: FlightNormalizer;
  hotels: HotelNormalizer;
  activities: ActivityNormalizer;
  transfers: TransferNormalizer;
}

// Normalization challenges:
// 1. Hotel identity: Same hotel has different IDs across suppliers
//    - Hotel X: "Taj Mahal Palace" = Hotelbeds ID 12345, TBO ID 67890
//    - Solution: Hotel mapping database (Giata, HotelIDs)
//    - Matching confidence: Name + address + coordinates → 95%+ accuracy
//
// 2. Room type mapping: Room names differ across suppliers
//    - "Deluxe Sea View" vs. "Premium Ocean Front" vs. "Superior Mer"
//    - Solution: Map to canonical room types (Standard, Superior, Deluxe, Suite)
//    - Amenities normalization: "WiFi" vs. "Free Internet" vs. "Complimentary Wi-Fi"
//
// 3. Rate comparison: Net rates vs. gross, with/without breakfast
//    - Supplier A: ₹8,500 net, room only
//    - Supplier B: ₹9,200 gross (20% commission), with breakfast
//    - Supplier C: ₹7,800 net, non-refundable
//    - Normalized: Show all with comparable pricing (₹/night after commission)
//
// 4. Flight fare normalization:
//    - Base fare + taxes + fees breakdown differs across GDS and consolidators
//    - Baggage allowance: Included vs. paid (₹500-2,000 per bag)
//    - Meal: Included vs. paid (₹300-800 per meal)
//    - Seat selection: Free vs. paid (₹200-2,000 per seat)
//    - Change/cancel fees: Vary by fare type
//    - Normalized: Show total all-in price with baggage + meal comparison

interface AggregationCache {
  strategy: CacheStrategy;
  popular: PopularCache;
  ttl: CacheTTL;
  invalidation: InvalidationStrategy;
}

// Caching strategy:
// Level 1: Hot cache (Redis) — Popular routes/hotels, 15-minute TTL
//   Delhi-Mumbai flights: 15 min TTL (prices change frequently)
//   Taj Mumbai hotel: 30 min TTL (hotel rates more stable)
//   Kerala package: 1 hour TTL (packages update less frequently)
//
// Level 2: Warm cache (Redis) — Recent searches, 5-minute TTL
//   Any search performed in last 5 minutes available instantly
//   Used for repeated searches by different agents/customers
//
// Level 3: Cold cache (PostgreSQL) — Historical pricing, 24-hour TTL
//   Yesterday's prices for the same route/hotel/date
//   Used for price comparison ("₹2,300 cheaper than yesterday!")
//
// Cache invalidation triggers:
// - Booking made: Invalidate availability cache for that hotel/flight
// - Price alert: Supplier notifies price change → invalidate specific cache
// - Scheduled: Full invalidation of hot cache every 15 minutes
// - Manual: Admin can force refresh for specific supplier/destination
//
// Cache hit rate targets:
// Hot cache: 60%+ (popular routes and hotels)
// Warm cache: 30%+ (recent searches)
// Cold cache: Used for price history, not real-time
// Total cache hit rate: 70%+ → 70% of searches served from cache
```

### Price Comparison Engine

```typescript
interface PriceComparisonEngine {
  comparison: ComparisonModel;
  ranking: ResultRanking;
  valueScoring: ValueScore;
  alternatives: AlternativeSuggestions;
}

interface ComparisonModel {
  id: string;
  type: ComparisonType;
  sources: string[];                   // Source IDs included in comparison
  normalization: NormalizationRule[];
  presentation: ComparisonPresentation;
}

type ComparisonType =
  | 'flight'                           // Same route, different airlines/suppliers
  | 'hotel'                            // Same hotel, different suppliers/rates
  | 'hotel_alternative'                // Different hotels, same destination/category
  | 'package'                          // Different packages for same itinerary
  | 'activity'                         // Same activity, different operators
  | 'multi_component';                 // Full trip comparison across suppliers

// Flight price comparison:
// Delhi → Mumbai, Oct 15, Economy, 1 Adult
//
// Source          | Airline    | Depart  | Arrive  | Price    | Bag | Meal | Cancel Fee
// Amadeus         | IndiGo 6E  | 07:00   | 09:15   | ₹5,200   | 15kg| Paid  | ₹2,500
// TBO             | IndiGo 6E  | 07:00   | 09:15   | ₹4,850   | 15kg| Paid  | ₹2,500
// Amadeus         | Vistara UK | 08:30   | 10:45   | ₹6,100   | 20kg| Free  | ₹1,500
// NDC Direct      | Air India  | 10:00   | 12:15   | ₹5,800   | 25kg| Free  | ₹1,000
// TBO             | SpiceJet   | 11:30   | 13:45   | ₹4,200   | 15kg| Paid  | ₹3,000
//
// Same IndiGo flight available from 2 sources → Show lowest price (₹4,850 from TBO)
// Value score factors:
//   Price: 40% weight (lower is better)
//   Timing: 25% weight (convenient hours preferred)
//   Baggage: 15% weight (more included = better)
//   Meal: 10% weight (included = better)
//   Flexibility: 10% weight (lower cancel fee = better)
//
// Value score result:
// 1. IndiGo 07:00 via TBO: ₹4,850 — Score: 82/100 (best value)
// 2. Vistara 08:30: ₹6,100 — Score: 78/100 (better timing + baggage)
// 3. Air India 10:00: ₹5,800 — Score: 75/100 (good baggage + meal)
// 4. SpiceJet 11:30: ₹4,200 — Score: 68/100 (cheapest but inflexible)

// Hotel price comparison:
// Taj Mahal Palace, Mumbai, Oct 15-16, 1 Night, Deluxe Room
//
// Source          | Room Type         | Price     | Breakfast | Cancel Policy     | Commission
// Hotelbeds       | Deluxe Sea View   | ₹18,500   | Not incl. | Free cancel 48h   | 15%
// TBO             | Deluxe Sea View   | ₹17,200   | Included  | Free cancel 24h   | 12%
// Direct (Taj)    | Deluxe Sea View   | ₹16,800   | Included  | Free cancel 24h   | Corporate rate
// Hotelbeds       | Superior City     | ₹12,500   | Not incl. | Free cancel 48h   | 15%
//
// After normalization (agency margin calculation):
// TBO with breakfast: ₹17,200 (agent margin: ₹2,064 at 12%)
// Direct with breakfast: ₹16,800 (best rate, corporate)
// Hotelbeds without breakfast: ₹18,500 + ₹1,500 breakfast = ₹20,000 total
//
// Recommended: Direct rate ₹16,800 with breakfast — best price + best terms

// Multi-component trip comparison:
// 5N Kerala Trip: Kochi → Munnar → Thekkady → Alleppey → Kochi
//
// Option A (Best Value): ₹42,500 per person
//   Hotels: Standard 3-star, local transport, houseboat
//   Sources: TBO hotels + local transport operator
//   Agent margin: ₹6,375 (15%)
//
// Option B (Premium): ₹68,000 per person
//   Hotels: Premium 4/5-star, private car, luxury houseboat
//   Sources: Hotelbeds + direct connect hotels
//   Agent margin: ₹10,200 (15%)
//
// Option C (Luxury): ₹1,15,000 per person
//   Hotels: Taj/Kumararakom Lake Resort, luxury houseboat, private transfers
//   Sources: Direct connect (Taj) + TBO + premium houseboat operator
//   Agent margin: ₹17,250 (15%)

interface ResultRanking {
  algorithm: RankingAlgorithm;
  weights: RankingWeight[];
  personalization: PersonalizationConfig;
  diversity: DiversityConfig;
}

// Ranking algorithm:
// 1. Price score: Normalize prices to 0-100 scale (lowest = 100)
// 2. Quality score: Rating × category tier × review count weight
// 3. Value score: Price × quality composite (best value bubble to top)
// 4. Personalization: Boost based on traveler preferences (past bookings)
// 5. Commission: Boost results with higher agent margin (configurable)
// 6. Diversity: Ensure results aren't all from same supplier/category
//
// Default ranking: Value score (40%) + Quality (30%) + Price (20%) + Personalization (10%)
// Agent-configurable: Agents can adjust weights for their clients
```

---

## Open Problems

1. **Hotel mapping accuracy** — Matching the same hotel across 5+ suppliers with different IDs, names, and addresses is error-prone. Incorrect mapping shows wrong prices, leading to booking failures and customer complaints.

2. **API reliability cascading** — If one supplier API is slow or down, it affects the entire search experience. Timeout handling, fallback to cached data, and graceful degradation are essential.

3. **Rate parity compliance** — Some suppliers enforce rate parity (same price across all channels). Showing undercut prices from one channel can result in supplier penalties or access termination.

4. **Search result quality vs. quantity** — 200 hotel results for Mumbai is overwhelming. Intelligent filtering, ranking, and progressive disclosure are needed to surface relevant results without hiding good options.

5. **Real-time availability vs. cache staleness** — Hotel availability changes every minute. Cached results may show rooms as available that are actually sold out, leading to booking failures at checkout.

---

## Next Steps

- [ ] Build multi-source inventory aggregation pipeline with async parallel search
- [ ] Create hotel/flight normalization engine with cross-supplier mapping
- [ ] Design price comparison engine with value scoring algorithm
- [ ] Implement multi-level caching strategy for search results
- [ ] Study aggregation platforms (TBO, Mystifly, Hotelbeds, Amadeus, Skyscanner API)
