# Flight Integration 02: Search & Shopping

> Flight search algorithms, multi-leg routing, filtering, sorting, and recommendations

---

## Overview

This document details the flight search and shopping subsystem, covering search algorithms, multi-leg routing, filtering, faceting, sorting, and alternative suggestions. The search service orchestrates parallel queries across multiple GDS providers and NDC APIs, normalizes results, and presents ranked options to users.

**Key Capabilities:**
- Real-time multi-source flight search
- Complex multi-leg itinerary construction
- Intelligent filtering and faceting
- Relevance-based result ranking
- Alternative date/route suggestions
- Shopping vs. guaranteed pricing modes

---

## Table of Contents

1. [Search Architecture](#search-architecture)
2. [Search Request Model](#search-request-model)
3. [Multi-Provider Search](#multi-provider-search)
4. [Itinerary Construction](#itinerary-construction)
5. [Filtering & Faceting](#filtering--faceting)
6. [Sorting & Ranking](#sorting--ranking)
7. [Alternative Suggestions](#alternative-suggestions)
8. [Caching Strategy](#caching-strategy)
9. [Performance Optimization](#performance-optimization)

---

## Search Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLIGHT SEARCH ORCHESTRATION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   CLIENT     │───▶│   SEARCH     │───▶│   REQUEST    │                  │
│  │   REQUEST    │    │   CONTROLLER │    │   VALIDATOR  │                  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘                  │
│                             │                                                  │
│                             ▼                                                  │
│                    ┌──────────────┐                                           │
│                    │    QUERY     │                                           │
│                    │  BUILDER     │                                           │
│                    └──────┬───────┘                                           │
│                           │                                                   │
│           ┌───────────────┼───────────────┐                                   │
│           │               │               │                                    │
│      ┌────▼────┐    ┌────▼────┐    ┌────▼────┐                               │
│      │ AMADEUS │    │  SABRE  │    │ TRAVEL  │                               │
│      │ ADAPTER │    │ ADAPTER │    │  PORT   │                               │
│      └────┬────┘    └────┬────┘    └────┬────┘                               │
│           │              │              │                                    │
│           └──────────────┼──────────────┘                                    │
│                          ▼                                                   │
│                   ┌──────────────┐                                          │
│                   │  RESULT      │                                          │
│                   │  MERGER      │                                          │
│                   └──────┬───────┘                                          │
│                          │                                                   │
│                          ▼                                                   │
│                   ┌──────────────┐                                          │
│                   │   FILTER     │                                          │
│                   │   PIPELINE   │                                          │
│                   └──────┬───────┘                                          │
│                          │                                                   │
│                          ▼                                                   │
│                   ┌──────────────┐                                          │
│                   │    RANKER    │                                          │
│                   └──────┬───────┘                                          │
│                          │                                                   │
│                          ▼                                                   │
│                   ┌──────────────┐                                          │
│                   │  RESPONSE    │                                          │
│                   │  BUILDER     │                                          │
│                   └──────────────┘                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Search Controller** | Request handling, validation, orchestration |
| **Query Builder** | Translates search request to provider-specific queries |
| **Provider Adapters** | Parallel search execution across GDS/NDC sources |
| **Result Merger** | Combines and de-duplicates results from multiple sources |
| **Filter Pipeline** | Applies user filters and business rules |
| **Ranker** | Scores and sorts results by relevance |
| **Response Builder** | Formats results for client consumption |

---

## Search Request Model

### Core Search Request

```typescript
interface FlightSearchRequest {
  // Basic search criteria
  origin: string;              // IATA code (e.g., "JFK")
  destination: string;         // IATA code (e.g., "LHR")
  departureDate: Date;         // Local date at origin
  returnDate?: Date;           // For round-trip searches

  // Passenger details
  passengers: PassengerCount;
  cabinClass: CabinClass;

  // Search options
  tripType: TripType;
  directOnly?: boolean;        // Exclude connections
  maxStops?: number;           // Maximum allowed stops (default: 2)
  maxDuration?: number;        // Maximum journey duration (hours)

  // Flexibility options
  flexibleDates?: boolean;     // Search +/- 3 days
  flexibleLocations?: boolean; // Include nearby airports
  fareType?: FareType;         // basic, standard, flexible

  // Provider control
  providers?: string[];        // Specific GDS providers to query
  includeLCC?: boolean;        // Include low-cost carriers

  // Shopping mode
  pricingMode: 'shopping' | 'guaranteed';

  // Pagination
  offset?: number;
  limit?: number;              // Default: 50, Max: 200
}

interface PassengerCount {
  adults: number;              // Age 12+
  children: number;            // Age 2-11
  infants: number;             // Age 0-1 (lap)
  infantsOnSeat?: number;      // Age 0-1 (with seat)
}

enum TripType {
  ONE_WAY = 'one-way',
  ROUND_TRIP = 'round-trip',
  MULTI_CITY = 'multi-city'
}

enum CabinClass {
  ECONOMY = 'economy',
  PREMIUM_ECONOMY = 'premium_economy',
  BUSINESS = 'business',
  FIRST = 'first',
  ANY = 'any'
}

enum FareType {
  BASIC = 'basic',             // Most restricted, lowest price
  STANDARD = 'standard',       // Normal restrictions
  FLEXIBLE = 'flexible',       // Flexible changes
  BUSINESS = 'business',       // Business class rules
  FIRST = 'first'              // First class rules
}
```

### Multi-City Search Request

```typescript
interface MultiCitySearchRequest extends FlightSearchRequest {
  tripType: TripType.MULTI_CITY;
  slices: FlightSliceRequest[];
}

interface FlightSliceRequest {
  origin: string;
  destination: string;
  departureDate: Date;
  flexibleDates?: boolean;
}
```

### Search Context

```typescript
interface SearchContext {
  requestId: string;
  userId?: string;
  sessionId: string;
  timestamp: Date;
  userAgent: string;
  ipAddress: string;
  currency: string;
  locale: string;
  market: string;              // Point of sale
  corporateCode?: string;      // For corporate negotiated fares
  loyaltyPrograms?: LoyaltyAccount[];
}
```

---

## Multi-Provider Search

### Parallel Search Execution

```typescript
class SearchOrchestrator {
  private adapters: Map<string, GDSAdapter>;
  private timeout: number = 5000; // 5 seconds per provider

  async search(request: FlightSearchRequest, context: SearchContext): Promise<FlightSearchResponse> {
    // 1. Build provider-specific queries
    const queries = await this.buildQueries(request, context);

    // 2. Execute parallel searches with timeout
    const searchPromises = Array.from(this.adapters.entries())
      .filter(([provider]) => this.shouldUseProvider(provider, request))
      .map(async ([provider, adapter]) => {
        try {
          return await Promise.race([
            adapter.search(queries[provider]),
            this.timeoutProvider(provider)
          ]);
        } catch (error) {
          this.logProviderError(provider, error);
          return { provider, results: [], errors: [error] };
        }
      });

    // 3. Wait for all providers (with partial success handling)
    const providerResults = await Promise.allSettled(searchPromises);

    // 4. Extract and merge successful results
    const allResults = providerResults
      .filter(result => result.status === 'fulfilled')
      .flatMap(result => (result.value as ProviderSearchResult).results);

    // 5. Merge and normalize
    const mergedResults = await this.mergeResults(allResults, request);

    // 6. Filter and rank
    const filteredResults = await this.filterResults(mergedResults, request);
    const rankedResults = await this.rankResults(filteredResults, request, context);

    // 7. Build response
    return this.buildResponse(rankedResults, request, context);
  }

  private async buildQueries(
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<Map<string, ProviderQuery>> {
    const queries = new Map<string, ProviderQuery>();

    for (const [provider, adapter] of this.adapters) {
      queries.set(provider, await adapter.buildQuery(request, context));
    }

    return queries;
  }

  private shouldUseProvider(provider: string, request: FlightSearchRequest): boolean {
    // Check explicit provider selection
    if (request.providers && request.providers.length > 0) {
      return request.providers.includes(provider);
    }

    // Check LCC inclusion
    if (provider === 'LCC' && !request.includeLCC) {
      return false;
    }

    return true;
  }

  private async timeoutProvider(provider: string): Promise<ProviderSearchResult> {
    await new Promise(resolve => setTimeout(resolve, this.timeout));
    throw new SearchTimeoutError(`Provider ${provider} timed out`);
  }
}
```

### Result Merging

```typescript
class ResultMerger {
  async mergeResults(
    results: RawFlightOffer[],
    request: FlightSearchRequest
  ): Promise<FlightOffer[]> {
    // 1. Normalize to common format
    const normalized = results.map(offer => this.normalizeOffer(offer));

    // 2. De-duplicate identical itineraries
    const unique = this.deduplicateOffers(normalized);

    // 3. Group by itinerary fingerprint
    const groups = this.groupByItinerary(unique);

    // 4. Select best offer per group (lowest price, best guarantee)
    const bestOffers = this.selectBestOffers(groups);

    return bestOffers;
  }

  private normalizeOffer(raw: RawFlightOffer): FlightOffer {
    return {
      id: raw.id || this.generateOfferId(raw),
      slices: raw.segments.map(seg => this.normalizeSlice(seg)),
      pricing: this.normalizePricing(raw.pricing),
      fareType: this.mapFareType(raw.fareType),
      bookingClass: raw.bookingClass,
      cabinClass: this.mapCabinClass(raw.cabinClass),
      seatsAvailable: raw.seatsAvailable,
      guarantee: this.determineGuarantee(raw),
      source: raw.source,
      metadata: {
        provider: raw.provider,
        providerOfferId: raw.providerOfferId,
        lastRefreshed: new Date(),
        isShopping: raw.isShopping || false
      }
    };
  }

  private deduplicateOffers(offers: FlightOffer[]): FlightOffer[] {
    const seen = new Set<string>();
    const unique: FlightOffer[] = [];

    for (const offer of offers) {
      // Create fingerprint from: flights + times + fare class
      const fingerprint = this.createItineraryFingerprint(offer);

      if (!seen.has(fingerprint)) {
        seen.add(fingerprint);
        unique.push(offer);
      } else {
        // Update existing with better price if found
        const existing = unique.find(o =>
          this.createItineraryFingerprint(o) === fingerprint
        );
        if (existing && offer.pricing.total < existing.pricing.total) {
          Object.assign(existing, offer);
        }
      }
    }

    return unique;
  }

  private createItineraryFingerprint(offer: FlightOffer): string {
    const flights = offer.slices.flatMap(slice =>
      slice.segments.map(seg => [
        seg.flight.flightNumber,
        seg.flight.departure.time.toISOString(),
        seg.flight.arrival.time.toISOString(),
        seg.bookingClass
      ]).flat()
    );

    return crypto
      .createHash('sha256')
      .update(flights.join('|'))
      .digest('hex')
      .substring(0, 16);
  }
}
```

---

## Itinerary Construction

### Single-Leg Routing

```typescript
interface DirectItinerary {
  type: 'direct';
  segments: [FlightSegment];
  duration: number;
}

interface ConnectingItinerary {
  type: 'connecting';
  segments: FlightSegment[];
  duration: number;
  stops: number;
  layovers: LayoverInfo[];
}

type Itinerary = DirectItinerary | ConnectingItinerary;
```

### Multi-Leg Routing Algorithm

```typescript
class ItineraryBuilder {
  private readonly MAX_LAYOVER = 6; // hours
  private readonly MIN_LAYOVER = 0.5; // 30 minutes
  private readonly MIN_CONNECTION_DOMESTIC = 0.75; // 45 minutes
  private readonly MIN_CONNECTION_INTERNATIONAL = 1.5; // 90 minutes

  async buildItineraries(
    request: FlightSearchRequest,
    flights: Flight[]
  ): Promise<Itinerary[]> {
    if (request.tripType === TripType.ONE_WAY) {
      return this.buildOneWayItineraries(request, flights);
    } else if (request.tripType === TripType.ROUND_TRIP) {
      return this.buildRoundTripItineraries(request, flights);
    } else {
      return this.buildMultiCityItineraries(request as MultiCitySearchRequest, flights);
    }
  }

  private buildOneWayItineraries(
    request: FlightSearchRequest,
    flights: Flight[]
  ): Itinerary[] {
    const itineraries: Itinerary[] = [];

    // Direct flights
    const directFlights = flights.filter(f =>
      f.departure.airport.code === request.origin &&
      f.arrival.airport.code === request.destination
    );

    for (const flight of directFlights) {
      itineraries.push({
        type: 'direct',
        segments: [this.createSegment(flight, request)],
        duration: flight.durationMinutes
      });
    }

    // Connecting flights (if allowed)
    if (!request.directOnly && request.maxStops !== 0) {
      const connections = this.findConnections(request, flights);
      itineraries.push(...connections);
    }

    return itineraries;
  }

  private findConnections(
    request: FlightSearchRequest,
    flights: Flight[]
  ): ConnectingItinerary[] {
    const connections: ConnectingItinerary[] = [];
    const maxStops = request.maxStops ?? 2;

    // Get all flights departing from origin
    const outboundFlights = flights.filter(f =>
      f.departure.airport.code === request.origin
    );

    // For each outbound flight, find onward connections
    for (const firstFlight of outboundFlights) {
      this.searchRecursiveConnections(
        firstFlight,
        request.destination,
        flights,
        [firstFlight],
        connections,
        maxStops,
        request
      );
    }

    return connections;
  }

  private searchRecursiveConnections(
    currentFlight: Flight,
    finalDestination: string,
    allFlights: Flight[],
    path: Flight[],
    results: ConnectingItinerary[],
    maxStops: number,
    request: FlightSearchRequest
  ): void {
    const currentAirport = currentFlight.arrival.airport.code;

    // Check if we've reached destination
    if (currentAirport === finalDestination && path.length > 1) {
      const layovers = this.calculateLayovers(path);

      // Validate minimum connection times
      if (this.areConnectionsValid(path)) {
        results.push({
          type: 'connecting',
          segments: path.map(f => this.createSegment(f, request)),
          duration: this.calculateTotalDuration(path),
          stops: path.length - 1,
          layovers
        });
      }
      return;
    }

    // Check if we've exceeded max stops
    if (path.length - 1 >= maxStops) {
      return;
    }

    // Find onward flights from current airport
    const onwardFlights = allFlights.filter(f => {
      // Depart from connection airport
      if (f.departure.airport.code !== currentAirport) return false;

      // Must be after current flight arrival + minimum connection time
      const minDeparture = new Date(
        currentFlight.arrival.time.getTime() +
        this.getMinimumConnectionTime(currentFlight) * 60 * 60 * 1000
      );

      if (f.departure.time < minDeparture) return false;

      // Must be within maximum layover
      const maxDeparture = new Date(
        currentFlight.arrival.time.getTime() +
        this.MAX_LAYOVER * 60 * 60 * 1000
      );

      if (f.departure.time > maxDeparture) return false;

      // Avoid circles
      if (path.some(p => p.flightNumber === f.flightNumber)) return false;

      return true;
    });

    // Recursively search for connections
    for (const onwardFlight of onwardFlights) {
      this.searchRecursiveConnections(
        onwardFlight,
        finalDestination,
        allFlights,
        [...path, onwardFlight],
        results,
        maxStops,
        request
      );
    }
  }

  private getMinimumConnectionTime(flight: Flight): number {
    // International flights need more connection time
    const isInternational = flight.departure.airport.country !== flight.arrival.airport.country;
    return isInternational ? this.MIN_CONNECTION_INTERNATIONAL : this.MIN_CONNECTION_DOMESTIC;
  }

  private areConnectionsValid(path: Flight[]): boolean {
    for (let i = 0; i < path.length - 1; i++) {
      const current = path[i];
      const next = path[i + 1];

      const connectionTime = (next.departure.time.getTime() - current.arrival.time.getTime()) / (60 * 60 * 1000);
      const minTime = this.getMinimumConnectionTime(current);

      if (connectionTime < minTime) return false;
    }
    return true;
  }

  private calculateLayovers(path: Flight[]): LayoverInfo[] {
    const layovers: LayoverInfo[] = [];

    for (let i = 0; i < path.length - 1; i++) {
      const current = path[i];
      const next = path[i + 1];

      const duration = (next.departure.time.getTime() - current.arrival.time.getTime()) / (60 * 1000);

      layovers.push({
        airport: current.arrival.airport,
        durationMinutes: Math.round(duration),
        flightChange: true,
        terminalChange: current.arrival.terminal !== next.departure.terminal
      });
    }

    return layovers;
  }
}
```

---

## Filtering & Faceting

### Filter Pipeline

```typescript
class FilterPipeline {
  private filters: Filter[];

  constructor() {
    this.filters = [
      new CabinClassFilter(),
      new StopsFilter(),
      new DurationFilter(),
      new DepartureTimeFilter(),
      new ArrivalTimeFilter(),
      new AirlineFilter(),
      new AllianceFilter(),
      new AirportFilter(),
      new PriceFilter(),
      new AvailabilityFilter(),
      new VisaRequirementFilter()
    ];
  }

  async filter(
    offers: FlightOffer[],
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<FlightOffer[]> {
    let filtered = [...offers];

    for (const filter of this.filters) {
      if (filter.isEnabled(request)) {
        filtered = await filter.apply(filtered, request, context);
      }
    }

    return filtered;
  }

  async getFacets(offers: FlightOffer[]): Promise<SearchFacets> {
    return {
      airlines: this.getAirlineFacet(offers),
      alliances: this.getAllianceFacet(offers),
      stops: this.getStopsFacet(offers),
      cabinClasses: this.getCabinClassFacet(offers),
      departureTimes: this.getDepartureTimeFacet(offers),
      arrivalTimes: this.getArrivalTimeFacet(offers),
      duration: this.getDurationRange(offers),
      price: this.getPriceRange(offers),
      airports: this.getAirportFacet(offers)
    };
  }
}
```

### Cabin Class Filter

```typescript
class CabinClassFilter implements Filter {
  isEnabled(request: FlightSearchRequest): boolean {
    return request.cabinClass !== CabinClass.ANY;
  }

  async apply(
    offers: FlightOffer[],
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<FlightOffer[]> {
    if (request.cabinClass === CabinClass.ANY) {
      return offers;
    }

    return offers.filter(offer => {
      // All segments must have at least the requested cabin class
      return offer.slices.every(slice =>
        slice.segments.every(seg =>
          this.isCabinClassEqualOrBetter(seg.cabinClass, request.cabinClass)
        )
      );
    });
  }

  private isCabinClassEqualOrBetter(actual: CabinClass, requested: CabinClass): boolean {
    const hierarchy = [
      CabinClass.ECONOMY,
      CabinClass.PREMIUM_ECONOMY,
      CabinClass.BUSINESS,
      CabinClass.FIRST
    ];

    const actualIndex = hierarchy.indexOf(actual);
    const requestedIndex = hierarchy.indexOf(requested);

    return actualIndex >= requestedIndex;
  }
}
```

### Stops Filter

```typescript
class StopsFilter implements Filter {
  isEnabled(request: FlightSearchRequest): boolean {
    return request.directOnly || (request.maxStops !== undefined && request.maxStops < 2);
  }

  async apply(
    offers: FlightOffer[],
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<FlightOffer[]> {
    return offers.filter(offer => {
      const totalStops = offer.slices.reduce((sum, slice) => sum + slice.stops, 0);

      if (request.directOnly) {
        return totalStops === 0;
      }

      if (request.maxStops !== undefined) {
        return totalStops <= request.maxStops;
      }

      return true;
    });
  }
}
```

### Time Window Filter

```typescript
interface TimeWindow {
  start: string; // HH:mm
  end: string;   // HH:mm
}

class DepartureTimeFilter implements Filter {
  isEnabled(request: FlightSearchRequest): boolean {
    return !!(request as any).departureTimeWindow;
  }

  async apply(
    offers: FlightOffer[],
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<FlightOffer[]> {
    const window = (request as any).departureTimeWindow as TimeWindow;
    if (!window) return offers;

    return offers.filter(offer => {
      const firstSegment = offer.slices[0].segments[0];
      const departureTime = firstSegment.flight.departure.time;
      const hour = departureTime.getHours();
      const minute = departureTime.getMinutes();
      const timeValue = hour * 60 + minute;

      const [startHour, startMin] = window.start.split(':').map(Number);
      const [endHour, endMin] = window.end.split(':').map(Number);
      const startValue = startHour * 60 + startMin;
      const endValue = endHour * 60 + endMin;

      return timeValue >= startValue && timeValue <= endValue;
    });
  }
}
```

### Airline Filter

```typescript
class AirlineFilter implements Filter {
  isEnabled(request: FlightSearchRequest): boolean {
    const preferred = (request as any).preferredAirlines;
    const excluded = (request as any).excludedAirlines;
    return !!(preferred?.length || excluded?.length);
  }

  async apply(
    offers: FlightOffer[],
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<FlightOffer[]> {
    const preferred = (request as any).preferredAirlines as string[] || [];
    const excluded = (request as any).excludedAirlines as string[] || [];

    return offers.filter(offer => {
      const airlines = new Set(
        offer.slices.flatMap(slice =>
          slice.segments.map(seg => seg.marketingCarrier)
        )
      );

      // Check exclusions first
      if (excluded.some(code => airlines.has(code))) {
        return false;
      }

      // If preferences specified, at least one segment must match
      if (preferred.length > 0) {
        return preferred.some(code => airlines.has(code));
      }

      return true;
    });
  }
}
```

### Facet Generation

```typescript
interface SearchFacets {
  airlines: FacetItem[];
  alliances: FacetItem[];
  stops: FacetItem[];
  cabinClasses: FacetItem[];
  departureTimes: TimeFacetBucket[];
  arrivalTimes: TimeFacetBucket[];
  duration: RangeFacet;
  price: RangeFacet;
  airports: AirportFacetItem[];
}

interface FacetItem {
  value: string;
  label: string;
  count: number;
  minPrice?: number;
}

interface TimeFacetBucket {
  label: string;
  start: string;
  end: string;
  count: number;
}

interface RangeFacet {
  min: number;
  max: number;
}

interface AirportFacetItem {
  code: string;
  name: string;
  city: string;
  count: {
    departure: number;
    arrival: number;
  };
}
```

---

## Sorting & Ranking

### Ranking Algorithm

```typescript
class ResultRanker {
  private weights = {
    price: 0.3,
    duration: 0.15,
    stops: 0.2,
    departureTime: 0.1,
    airlineQuality: 0.1,
    scheduleQuality: 0.1,
    popularity: 0.05
  };

  async rank(
    offers: FlightOffer[],
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<FlightOffer[]> {
    // Calculate scores for each offer
    const scored = await Promise.all(
      offers.map(async offer => ({
        offer,
        score: await this.calculateScore(offer, request, context)
      }))
    );

    // Sort by score (descending)
    scored.sort((a, b) => b.score - a.score);

    return scored.map(s => s.offer);
  }

  private async calculateScore(
    offer: FlightOffer,
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<number> {
    const priceScore = this.calculatePriceScore(offer, request);
    const durationScore = this.calculateDurationScore(offer);
    const stopsScore = this.calculateStopsScore(offer);
    const timeScore = this.calculateDepartureTimeScore(offer);
    const airlineScore = await this.calculateAirlineQualityScore(offer);
    const scheduleScore = this.calculateScheduleQualityScore(offer);
    const popularityScore = await this.calculatePopularityScore(offer, context);

    return (
      priceScore * this.weights.price +
      durationScore * this.weights.duration +
      stopsScore * this.weights.stops +
      timeScore * this.weights.departureTime +
      airlineScore * this.weights.airlineQuality +
      scheduleScore * this.weights.scheduleQuality +
      popularityScore * this.weights.popularity
    );
  }

  private calculatePriceScore(offer: FlightOffer, request: FlightSearchRequest): number {
    // Lower price = higher score
    // Normalize against typical price range for route
    const typicalPrice = this.getTypicalPrice(request);
    const priceRatio = offer.pricing.total / typicalPrice;

    if (priceRatio <= 0.7) return 1.0; // Great price
    if (priceRatio <= 0.9) return 0.8; // Good price
    if (priceRatio <= 1.1) return 0.6; // Normal price
    if (priceRatio <= 1.3) return 0.4; // High price
    return 0.2; // Very high price
  }

  private calculateDurationScore(offer: FlightOffer): number {
    const totalDuration = offer.slices.reduce((sum, slice) => sum + slice.duration, 0);
    const totalStops = offer.slices.reduce((sum, slice) => sum + slice.stops, 0);

    // Direct flights get bonus
    if (totalStops === 0) return 1.0;

    // Score decreases with duration and stops
    const baseScore = Math.max(0, 1 - (totalDuration / (24 * 60))); // 24+ hours = 0
    const stopPenalty = totalStops * 0.15;

    return Math.max(0, baseScore - stopPenalty);
  }

  private calculateStopsScore(offer: FlightOffer): number {
    const totalStops = offer.slices.reduce((sum, slice) => sum + slice.stops, 0);

    switch (totalStops) {
      case 0: return 1.0;
      case 1: return 0.7;
      case 2: return 0.4;
      default: return 0.1;
    }
  }

  private calculateDepartureTimeScore(offer: FlightOffer): number {
    const departure = offer.slices[0].segments[0].flight.departure.time;
    const hour = departure.getHours();

    // Preferred departure times: 6am-10am, 2pm-6pm
    if ((hour >= 6 && hour <= 10) || (hour >= 14 && hour <= 18)) {
      return 1.0;
    }

    // Acceptable: 10am-2pm, 6pm-9pm
    if ((hour > 10 && hour < 14) || (hour > 18 && hour <= 21)) {
      return 0.7;
    }

    // Less desirable: early morning, late night
    if ((hour >= 5 && hour < 6) || (hour > 21 && hour <= 23)) {
      return 0.4;
    }

    // Red-eye flights
    return 0.2;
  }

  private async calculateAirlineQualityScore(offer: FlightOffer): Promise<number> {
    const airlines = offer.slices.flatMap(slice =>
      slice.segments.map(seg => seg.marketingCarrier)
    );

    // Get average airline rating
    const ratings = await Promise.all(
      airlines.map(code => this.getAirlineRating(code))
    );

    const avgRating = ratings.reduce((sum, r) => sum + r, 0) / ratings.length;

    // Normalize 0-5 scale to 0-1
    return avgRating / 5;
  }

  private calculateScheduleQualityScore(offer: FlightOffer): number {
    let score = 1.0;

    // Penalize long layovers
    for (const slice of offer.slices) {
      for (const layover of slice.layovers || []) {
        if (layover.durationMinutes > 4 * 60) {
          score -= 0.1;
        }
        if (layover.durationMinutes > 6 * 60) {
          score -= 0.15;
        }
      }
    }

    // Penalize very short connections
    for (const slice of offer.slices) {
      for (const layover of slice.layovers || []) {
        if (layover.durationMinutes < 45) {
          score -= 0.1;
        }
      }
    }

    return Math.max(0, score);
  }

  private async calculatePopularityScore(
    offer: FlightOffer,
    context: SearchContext
  ): Promise<number> {
    // Get booking/conversion rate for this itinerary
    const popularity = await this.getItineraryPopularity(offer, context);

    // Normalize to 0-1
    return Math.min(1, popularity / 100);
  }
}
```

### Sorting Options

```typescript
enum SortOption {
  BEST = 'best',                    // Relevance score
  PRICE_LOW = 'price_low',          // Lowest total price
  PRICE_HIGH = 'price_high',        // Highest total price
  DURATION_SHORT = 'duration_short',// Shortest total duration
  DURATION_LONG = 'duration_long',  // Longest total duration
  DEPARTURE_EARLY = 'dept_early',   // Earliest departure
  DEPARTURE_LATE = 'dept_late',     // Latest departure
  ARRIVAL_EARLY = 'arr_early',      // Earliest arrival
  ARRIVAL_LATE = 'arr_late'         // Latest arrival
}

class SortEngine {
  sort(offers: FlightOffer[], option: SortOption): FlightOffer[] {
    switch (option) {
      case SortOption.PRICE_LOW:
        return [...offers].sort((a, b) => a.pricing.total - b.pricing.total);

      case SortOption.PRICE_HIGH:
        return [...offers].sort((a, b) => b.pricing.total - a.pricing.total);

      case SortOption.DURATION_SHORT:
        return [...offers].sort((a, b) => {
          const durationA = a.slices.reduce((sum, s) => sum + s.duration, 0);
          const durationB = b.slices.reduce((sum, s) => sum + s.duration, 0);
          return durationA - durationB;
        });

      case SortOption.DEPARTURE_EARLY:
        return [...offers].sort((a, b) => {
          const timeA = a.slices[0].segments[0].flight.departure.time.getTime();
          const timeB = b.slices[0].segments[0].flight.departure.time.getTime();
          return timeA - timeB;
        });

      case SortOption.DEPARTURE_LATE:
        return [...offers].sort((a, b) => {
          const timeA = a.slices[0].segments[0].flight.departure.time.getTime();
          const timeB = b.slices[0].segments[0].flight.departure.time.getTime();
          return timeB - timeA;
        });

      case SortOption.ARRIVAL_EARLY:
        return [...offers].sort((a, b) => {
          const lastSegA = a.slices[a.slices.length - 1].segments.slice(-1)[0];
          const lastSegB = b.slices[b.slices.length - 1].segments.slice(-1)[0];
          return lastSegA.flight.arrival.time.getTime() - lastSegB.flight.arrival.time.getTime();
        });

      default:
        return offers;
    }
  }
}
```

---

## Alternative Suggestions

### Flexible Date Suggestions

```typescript
class FlexibleDateSearcher {
  private readonly DAYS_TO_SEARCH = 3;

  async findAlternativeDates(
    request: FlightSearchRequest,
    bestPrice: number
  ): Promise<DateSuggestion[]> {
    if (!request.flexibleDates) {
      return [];
    }

    const suggestions: DateSuggestion[] = [];
    const departureDate = new Date(request.departureDate);

    // Search +/- days
    for (let offset = -this.DAYS_TO_SEARCH; offset <= this.DAYS_TO_SEARCH; offset++) {
      if (offset === 0) continue; // Skip original date

      const altDate = new Date(departureDate);
      altDate.setDate(altDate.getDate() + offset);

      // Check if better price available
      const altPrice = await this.getLowestPriceForDate({
        ...request,
        departureDate: altDate
      });

      if (altPrice && altPrice < bestPrice) {
        suggestions.push({
          date: altDate,
          price: altPrice,
          savings: bestPrice - altPrice,
          savingsPercent: ((bestPrice - altPrice) / bestPrice) * 100
        });
      }
    }

    return suggestions.sort((a, b) => b.savings - a.savings);
  }
}

interface DateSuggestion {
  date: Date;
  price: number;
  savings: number;
  savingsPercent: number;
}
```

### Alternative Airport Suggestions

```typescript
class AlternativeAirportSearcher {
  private readonly MAX_DISTANCE = 150; // km

  async findAlternativeAirports(
    request: FlightSearchRequest,
    context: SearchContext
  ): Promise<AirportSuggestion[]> {
    const suggestions: AirportSuggestion[] = [];

    // Get nearby origin airports
    const nearbyOrigins = await this.getNearbyAirports(
      request.origin,
      this.MAX_DISTANCE
    );

    // Get nearby destination airports
    const nearbyDests = await this.getNearbyAirports(
      request.destination,
      this.MAX_DISTANCE
    );

    // Check all combinations
    for (const origin of nearbyOrigins) {
      for (const dest of nearbyDests) {
        const price = await this.getLowestPrice({
          ...request,
          origin: origin.code,
          destination: dest.code
        });

        if (price) {
          suggestions.push({
            origin: origin,
            destination: dest,
            price,
            distanceFromOrigin: origin.distance,
            distanceFromDestination: dest.distance
          });
        }
      }
    }

    return suggestions.sort((a, b) => a.price - b.price);
  }

  private async getNearbyAirports(
    code: string,
    maxDistance: number
  ): Promise<NearbyAirport[]> {
    const airport = await this.getAirport(code);
    const allAirports = await this.getAllAirports();

    return allAirports
      .filter(a => a.code !== code)
      .map(a => ({
        ...a,
        distance: this.calculateDistance(airport, a)
      }))
      .filter(a => a.distance <= maxDistance)
      .sort((a, b) => a.distance - b.distance);
  }

  private calculateDistance(a1: Airport, a2: Airport): number {
    // Haversine formula
    const R = 6371; // Earth's radius in km
    const dLat = this.toRad(a2.location.latitude - a1.location.latitude);
    const dLon = this.toRad(a2.location.longitude - a1.location.longitude);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(a1.location.latitude)) *
      Math.cos(this.toRad(a2.location.latitude)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  private toRad(degrees: number): number {
    return degrees * (Math.PI / 180);
  }
}

interface AirportSuggestion {
  origin: NearbyAirport;
  destination: NearbyAirport;
  price: number;
  distanceFromOrigin: number;
  distanceFromDestination: number;
}

interface NearbyAirport extends Airport {
  distance: number;
}
```

### Split Ticket Suggestions

```typescript
class SplitTicketSearcher {
  async findSplitTicketOptions(
    request: FlightSearchRequest
  ): Promise<SplitTicketSuggestion[]> {
    const suggestions: SplitTicketSuggestion[] = [];

    // Find common hub airports
    const hubs = await this.getHubAirportsBetween(
      request.origin,
      request.destination
    );

    for (const hub of hubs) {
      // Price as two separate one-way tickets
      const outboundPrice = await this.getLowestPrice({
        ...request,
        destination: hub.code,
        tripType: TripType.ONE_WAY
      });

      const returnPrice = request.returnDate
        ? await this.getLowestPrice({
            ...request,
            origin: hub.code,
            departureDate: request.returnDate,
            tripType: TripType.ONE_WAY
          })
        : 0;

      if (outboundPrice && returnPrice) {
        const splitTotal = outboundPrice + returnPrice;
        const directPrice = await this.getLowestPrice(request);

        if (directPrice && splitTotal < directPrice) {
          suggestions.push({
            hub,
            outboundPrice,
            returnPrice,
            splitTotal,
            directPrice,
            savings: directPrice - splitTotal
          });
        }
      }
    }

    return suggestions;
  }
}

interface SplitTicketSuggestion {
  hub: Airport;
  outboundPrice: number;
  returnPrice: number;
  splitTotal: number;
  directPrice: number;
  savings: number;
}
```

---

## Caching Strategy

### Multi-Level Caching

```typescript
class SearchCacheManager {
  private redis: Redis;
  private memoryCache: LRUCache<string, any>;

  // Cache TTLs
  private readonly TTL = {
    SEARCH_RESULT: 300,      // 5 minutes
    PRICE_LOOKUP: 60,        // 1 minute
    AVAILABILITY: 180,       // 3 minutes
    ROUTE_CACHE: 86400,      // 24 hours
    AIRPORT_INFO: 604800     // 7 days
  };

  async get(request: FlightSearchRequest): Promise<FlightSearchResponse | null> {
    const cacheKey = this.buildCacheKey(request);

    // Check memory cache first (fastest)
    const memResult = this.memoryCache.get(cacheKey);
    if (memResult) {
      return memResult;
    }

    // Check Redis cache
    const redisResult = await this.redis.get(cacheKey);
    if (redisResult) {
      const parsed = JSON.parse(redisResult);
      // Store in memory cache
      this.memoryCache.set(cacheKey, parsed);
      return parsed;
    }

    return null;
  }

  async set(
    request: FlightSearchRequest,
    response: FlightSearchResponse
  ): Promise<void> {
    const cacheKey = this.buildCacheKey(request);
    const serialized = JSON.stringify(response);

    // Store in both caches
    this.memoryCache.set(cacheKey, response);
    await this.redis.setex(cacheKey, this.TTL.SEARCH_RESULT, serialized);
  }

  private buildCacheKey(request: FlightSearchRequest): string {
    const normalized = {
      o: request.origin,
      d: request.destination,
      dd: request.departureDate.toISOString().split('T')[0],
      rd: request.returnDate?.toISOString().split('T')[0],
      p: request.passengers,
      c: request.cabinClass,
      dt: request.tripType,
      do: request.directOnly ? 1 : 0,
      mx: request.maxStops ?? 2
    };

    return `flight:search:${Buffer.from(JSON.stringify(normalized)).toString('base64')}`;
  }

  async invalidateRoute(origin: string, destination: string): Promise<void> {
    // Invalidate all cache entries for this route
    const pattern = `flight:search:*`;
    const keys = await this.redis.keys(pattern);

    for (const key of keys) {
      const decoded = JSON.parse(
        Buffer.from(key.split(':')[2], 'base64').toString()
      );

      if (decoded.o === origin || decoded.d === destination) {
        await this.redis.del(key);
      }
    }
  }
}
```

---

## Performance Optimization

### Search Optimization Strategies

```typescript
class SearchOptimizer {
  // Pre-fetch common routes during off-peak hours
  async preFetchPopularRoutes(): Promise<void> {
    const popularRoutes = await this.getPopularRoutes();

    for (const route of popularRoutes) {
      const requests = this.generateSearchRequestsForRoute(route);
      for (const request of requests) {
        // Trigger async search to warm cache
        this.searchOrchestrator.search(request, this.createContext())
          .then(() => console.log(`Warmed cache for ${route.origin}-${route.destination}`))
          .catch(err => console.error(`Failed to warm cache:`, err));
      }
    }
  }

  // Parallelize independent searches
  async parallelMultiCitySearch(request: MultiCitySearchRequest): Promise<FlightOffer[]> {
    // Search each slice independently in parallel
    const sliceResults = await Promise.all(
      request.slices.map(slice =>
        this.searchOrchestrator.search(
          { ...request, ...slice, tripType: TripType.ONE_WAY },
          this.createContext()
        )
      )
    );

    // Combine results
    return this.combineSliceResults(sliceResults);
  }

  // Progressive result loading
  async searchWithProgressiveResults(
    request: FlightSearchRequest,
    onProgress: (results: FlightOffer[]) => void
  ): Promise<FlightOffer[]> {
    // Return cached results immediately if available
    const cached = await this.cacheManager.get(request);
    if (cached) {
      onProgress(cached.offers);
    }

    // Start fresh search
    const searchPromise = this.searchOrchestrator.search(request, this.createContext());

    // Return partial results as they arrive from providers
    const providerResults = await this.getProviderResultsProgressively(request);
    onProgress(providerResults);

    // Wait for complete results
    const final = await searchPromise;
    return final.offers;
  }
}
```

### Response Compression

```typescript
class ResponseCompressor {
  compress(offers: FlightOffer[]): CompressedFlightResponse {
    // Extract common data to avoid repetition
    const airlines = this.extractAirlines(offers);
    const airports = this.extractAirports(offers);
    const aircraft = this.extractAircraft(offers);

    // Create lookup maps
    const airlineMap = this.createLookupMap(airlines);
    const airportMap = this.createLookupMap(airports);
    const aircraftMap = this.createLookupMap(aircraft);

    // Compress offers by using references
    const compressedOffers = offers.map(offer => ({
      ...offer,
      slices: offer.slices.map(slice => ({
        ...slice,
        segments: slice.segments.map(seg => ({
          ...seg,
          airline: airlineMap.get(seg.marketingCarrier),
          departureAirport: airportMap.get(seg.flight.departure.airport.code),
          arrivalAirport: airportMap.get(seg.flight.arrival.airport.code),
          equipment: aircraftMap.get(seg.flight.equipment?.code)
        }))
      }))
    }));

    return {
      offers: compressedOffers,
      dictionaries: { airlines, airports, aircraft }
    };
  }

  decompress(response: CompressedFlightResponse): FlightOffer[] {
    // Reconstruct full offers from compressed format
    return response.offers.map(offer => ({
      ...offer,
      slices: offer.slices.map(slice => ({
        ...slice,
        segments: slice.segments.map(seg => ({
          ...seg,
          marketingCarrier: response.dictionaries.airlines[seg.airline].code,
          flight: {
            ...seg.flight,
            departure: {
              ...seg.flight.departure,
              airport: response.dictionaries.airports[seg.departureAirport]
            },
            arrival: {
              ...seg.flight.arrival,
              airport: response.dictionaries.airports[seg.arrivalAirport]
            },
            equipment: seg.equipment
              ? response.dictionaries.aircraft[seg.equipment]
              : undefined
          }
        }))
      }))
    }));
  }
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
