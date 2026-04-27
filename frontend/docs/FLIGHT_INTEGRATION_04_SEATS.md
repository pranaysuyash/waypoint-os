# Flight Integration 04: Seat Management

> Seat map retrieval, seat selection, seat assignments, and ancillary services

---

## Overview

This document details the flight seat management subsystem, covering seat map retrieval, seat selection, seat assignment, and related ancillary services. The seat service integrates with GDS providers and NDC APIs to provide real-time seat availability and handles the complete seat selection workflow from map display to assignment.

**Key Capabilities:**
- Real-time seat map retrieval
- Visual seat map display
- Seat selection and hold
- Seat attribute filtering (window, aisle, extra legroom)
- Ancillary service integration
- Seat assignment for check-in
- Group seating management

---

## Table of Contents

1. [Seat Architecture](#seat-architecture)
2. [Seat Map Data Model](#seat-map-data-model)
3. [Seat Map Retrieval](#seat-map-retrieval)
4. [Seat Selection](#seat-selection)
5. [Seat Attributes](#seat-attributes)
6. [Ancillary Services](#ancillary-services)
7. [Seat Assignment](#seat-assignment)
8. [Group Seating](#group-seating)

---

## Seat Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SEAT MANAGEMENT SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   CLIENT     │───▶│  SEAT MAP    │───▶│    CACHE     │                  │
│  │   REQUEST    │    │  SERVICE     │    │   (Redis)    │                  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘                  │
│                             │                                                  │
│                             ▼                                                  │
│                     ┌──────────────┐                                         │
│                     │   SEAT MAP   │                                         │
│                     │   BUILDER    │                                         │
│                     └──────┬───────┘                                         │
│                            │                                                │
│          ┌─────────────────┼─────────────────┐                             │
│          │                 │                 │                              │
│     ┌────▼────┐      ┌────▼────┐      ┌────▼────┐                          │
│     │ GDS      │      │ NDC      │      │ AIRLINE  │                          │
│     │ SEAT MAP │      │ SEAT MAP │      │ DIRECT  │                          │
│     └────┬────┘      └────┬────┘      └────┬────┘                          │
│          │                 │                 │                               │
│          └─────────────────┼─────────────────┘                               │
│                            ▼                                                │
│                     ┌──────────────┐                                         │
│                     │   SEAT MAP   │                                         │
│                     │  MERGER      │                                         │
│                     └──────┬───────┘                                         │
│                            │                                                │
│                            ▼                                                │
│                     ┌──────────────┐                                         │
│                     │   SEAT       │                                         │
│                     │  SELECTOR    │                                         │
│                     └──────┬───────┘                                         │
│                            │                                                │
│                            ▼                                                │
│                     ┌──────────────┐                                         │
│                     │   HOLD       │                                         │
│                     │  MANAGER     │                                         │
│                     └──────┬───────┘                                         │
│                            │                                                │
│                            ▼                                                │
│                     ┌──────────────┐                                         │
│                     │  ASSIGNMENT  │                                         │
│                     │  ENGINE      │                                         │
│                     └──────────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Seat Map Service** | Handles seat map requests and orchestration |
| **Seat Map Builder** | Constructs normalized seat map from provider data |
| **Provider Adapters** | Fetches seat maps from GDS/NDC/Direct sources |
| **Seat Map Merger** | Combines seat maps from multiple sources |
| **Seat Selector** | Manages seat selection and validation |
| **Hold Manager** | Manages temporary seat holds |
| **Assignment Engine** | Handles seat assignment and confirmation |

---

## Seat Map Data Model

### Seat Map Structure

```typescript
interface SeatMap {
  flightId: string;
  flightNumber: string;
  departure: ScheduledFlight;
  aircraft: AircraftInfo;

  decks: SeatDeck[];

  // Layout information
  layout: SeatMapLayout;
  amenities: CabinAmenity[];

  // Pricing
  seatPricing: SeatPricingInfo;

  // Availability timestamp
  timestamp: Date;
  expiresAt: Date;
}

interface SeatDeck {
  deck: 'main' | 'upper' | 'lower';
  name: string;

  // Cabins on this deck
  cabins: SeatCabin[];
}

interface SeatCabin {
  cabinClass: CabinClass;
  name: string;
  rows: SeatRow[];

  // Cabin boundaries
  firstRow: number;
  lastRow: number;
}

interface SeatRow {
  rowNumber: number;
  seats: Seat[];

  // Row attributes
  attributes?: RowAttribute[];
  emergencyExit: boolean;
  bulkhead: boolean;
  wing: boolean;
}

interface Seat {
  // Identification
  number: string;              // e.g., "12A"
  column: string;              // A, B, C, etc.
  row: number;

  // Position
  deck: 'main' | 'upper' | 'lower';
  cabinClass: CabinClass;

  // Availability
  status: SeatStatus;
  available: boolean;

  // Characteristics
  type: SeatType;
  attributes: SeatAttribute[];

  // Pricing
  price?: number;
  currency?: string;
  priceIncluded: boolean;

  // Occupancy
  occupiedBy?: PassengerInfo;

  // Restrictions
  restrictions: SeatRestriction[];
}

enum SeatStatus {
  AVAILABLE = 'available',
  OCCUPIED = 'occupied',
  BLOCKED = 'blocked',          // Not assignable (crew, inoperative)
  HELD = 'held',                // Temporarily held
  UNAVAILABLE = 'unavailable'   // Not available for selection
}

enum SeatType {
  STANDARD = 'standard',
  WINDOW = 'window',
  AISLE = 'aisle',
  MIDDLE = 'middle',
  BULKHEAD = 'bulkhead',
  EMERGENCY_EXIT = 'emergency_exit',
  EXTRA_LEGROOM = 'extra_legroom',
  FORWARD_ZONE = 'forward_zone',
  REAR_ZONE = 'rear_zone',
  QUIET_ZONE = 'quiet_zone',
  PREFERRED = 'preferred'
}

enum SeatAttribute {
  WINDOW = 'window',
  AISLE = 'aisle',
  MIDDLE = 'middle',
  BULKHEAD = 'bulkhead',
  EMERGENCY_EXIT = 'emergency_exit',
  EXTRA_LEGROOM = 'extra_legroom',
  RECLINING = 'reclining',
  LIE_FLAT = 'lie_flat',
  SUITE = 'suite',
  POWER_OUTLET = 'power_outlet',
  USB_PORT = 'usb_port',
  WIFI = 'wifi',
  ENTERTAINMENT = 'entertainment',
  QUIET_ZONE = 'quiet_zone',
  FORWARD = 'forward',
  REAR = 'rear',
  WING = 'wing',
  NEAR_LAVATORY = 'near_lavatory',
  NEAR_GALLEY = 'near_galley'
}

interface SeatRestriction {
  type: 'age' | 'physical' | 'safety' | 'eligibility';
  description: string;
  requirement?: string;
}

interface AircraftInfo {
  iataCode: string;        // e.g., "B737"
  icaoCode: string;        // e.g., "B737-800"
  name: string;
  manufacturer: string;
  registration?: string;
}

interface SeatMapLayout {
  // Column configuration
  columns: SeatColumn[];

  // Seat numbering
  numberingStart: number;
  numberingEnd: number;
  skipRows: number[];

  // Cabin dividers
  dividers: CabinDivider[];
}

interface SeatColumn {
  letter: string;
  position: 'left' | 'center_left' | 'center' | 'center_right' | 'right';
  aisleAfter: boolean;
}

interface CabinDivider {
  afterRow: number;
  type: 'curtain' | 'bulkhead' | 'wall';
}

interface SeatPricingInfo {
  currency: string;
  basePrices: Map<SeatType, number>;
  dynamicPricing: boolean;
  taxesIncluded: boolean;
}
```

### Row Attributes

```typescript
interface RowAttribute {
  type: 'emergency_exit' | 'bulkhead' | 'wing' | 'quiet_zone';
  description: string;
  seatImplications: SeatImplication[];
}

interface SeatImplication {
  seatNumbers: string[];
  implication: string; // e.g., "recline limited", "must be 15+"
}
```

---

## Seat Map Retrieval

### Seat Map Service

```typescript
class SeatMapService {
  private adapters: Map<string, SeatMapAdapter>;
  private cache: SeatMapCache;

  async getSeatMap(
    flightId: string,
    offerId: string,
    context: SearchContext
  ): Promise<SeatMap> {
    // 1. Check cache
    const cached = await this.cache.get(flightId);
    if (cached && !this.isCacheExpired(cached)) {
      return cached;
    }

    // 2. Get flight details
    const flight = await this.getFlightDetails(flightId);

    // 3. Determine source (GDS, NDC, or direct)
    const source = await this.determineSource(flight);

    // 4. Fetch seat map from source
    const seatMap = await this.fetchSeatMap(flight, source, context);

    // 5. Normalize and enrich
    const normalized = await this.normalizeSeatMap(seatMap, flight);

    // 6. Cache the result
    await this.cache.set(flightId, normalized);

    return normalized;
  }

  private async fetchSeatMap(
    flight: FlightDetails,
    source: string,
    context: SearchContext
  ): Promise<RawSeatMap> {
    const adapter = this.adapters.get(source);

    if (!adapter) {
      throw new Error(`No adapter available for source: ${source}`);
    }

    return await adapter.getSeatMap(flight, context);
  }

  private async normalizeSeatMap(
    raw: RawSeatMap,
    flight: FlightDetails
  ): Promise<SeatMap> {
    // Map raw seats to normalized format
    const decks: SeatDeck[] = [];

    for (const rawDeck of raw.decks) {
      const cabins: SeatCabin[] = [];

      for (const rawCabin of rawDeck.cabins) {
        const rows: SeatRow[] = [];

        for (const rawRow of rawCabin.rows) {
          const seats: Seat[] = [];

          for (const rawSeat of rawRow.seats) {
            seats.push({
              number: rawSeat.number,
              column: rawSeat.column,
              row: rawRow.rowNumber,
              deck: rawDeck.deck,
              cabinClass: rawCabin.cabinClass,
              status: this.mapSeatStatus(rawSeat.status),
              available: rawSeat.status === 'available',
              type: this.determineSeatType(rawSeat),
              attributes: this.determineSeatAttributes(rawSeat),
              price: rawSeat.price,
              currency: rawSeat.currency,
              priceIncluded: !rawSeat.price || rawSeat.price === 0,
              restrictions: rawSeat.restrictions || []
            });
          }

          rows.push({
            rowNumber: rawRow.rowNumber,
            seats,
            attributes: rawRow.attributes,
            emergencyExit: rawRow.emergencyExit || false,
            bulkhead: rawRow.bulkhead || false,
            wing: rawRow.wing || false
          });
        }

        cabins.push({
          cabinClass: rawCabin.cabinClass,
          name: rawCabin.name,
          rows,
          firstRow: rawCabin.firstRow,
          lastRow: rawCabin.lastRow
        });
      }

      decks.push({
        deck: rawDeck.deck,
        name: rawDeck.name,
        cabins
      });
    }

    return {
      flightId: flight.id,
      flightNumber: flight.flightNumber,
      departure: flight.departure,
      aircraft: flight.aircraft,
      decks,
      layout: this.buildLayout(decks),
      amenities: this.getAmenities(flight),
      seatPricing: raw.pricing || this.getDefaultPricing(),
      timestamp: new Date(),
      expiresAt: new Date(Date.now() + 30 * 60 * 1000) // 30 minutes
    };
  }

  private determineSeatType(rawSeat: RawSeat): SeatType {
    if (rawSeat.attributes.includes('emergency_exit')) {
      return SeatType.EMERGENCY_EXIT;
    }
    if (rawSeat.attributes.includes('extra_legroom')) {
      return SeatType.EXTRA_LEGROOM;
    }
    if (rawSeat.attributes.includes('bulkhead')) {
      return SeatType.BULKHEAD;
    }
    if (rawSeat.position === 'window') {
      return SeatType.WINDOW;
    }
    if (rawSeat.position === 'aisle') {
      return SeatType.AISLE;
    }
    if (rawSeat.position === 'middle') {
      return SeatType.MIDDLE;
    }
    return SeatType.STANDARD;
  }

  private determineSeatAttributes(rawSeat: RawSeat): SeatAttribute[] {
    const attributes: SeatAttribute[] = [];

    // Position
    if (rawSeat.position === 'window') attributes.push(SeatAttribute.WINDOW);
    if (rawSeat.position === 'aisle') attributes.push(SeatAttribute.AISLE);
    if (rawSeat.position === 'middle') attributes.push(SeatAttribute.MIDDLE);

    // Special attributes
    if (rawSeat.attributes.includes('emergency_exit')) {
      attributes.push(SeatAttribute.EMERGENCY_EXIT);
    }
    if (rawSeat.attributes.includes('bulkhead')) {
      attributes.push(SeatAttribute.BULKHEAD);
    }
    if (rawSeat.attributes.includes('extra_legroom')) {
      attributes.push(SeatAttribute.EXTRA_LEGROOM);
    }
    if (rawSeat.attributes.includes('lie_flat')) {
      attributes.push(SeatAttribute.LIE_FLAT);
    }
    if (rawSeat.attributes.includes('suite')) {
      attributes.push(SeatAttribute.SUITE);
    }

    // Amenities
    if (rawSeat.amenities?.includes('power')) {
      attributes.push(SeatAttribute.POWER_OUTLET);
    }
    if (rawSeat.amenities?.includes('usb')) {
      attributes.push(SeatAttribute.USB_PORT);
    }
    if (rawSeat.amenities?.includes('wifi')) {
      attributes.push(SeatAttribute.WIFI);
    }
    if (rawSeat.amenities?.includes('entertainment')) {
      attributes.push(SeatAttribute.ENTERTAINMENT);
    }

    return attributes;
  }

  private buildLayout(decks: SeatDeck[]): SeatMapLayout {
    // Extract column information from seat maps
    const columns: SeatColumn[] = [];
    const dividers: CabinDivider[] = [];

    for (const deck of decks) {
      for (const cabin of deck.cabins) {
        // Add cabin divider
        dividers.push({
          afterRow: cabin.firstRow - 1,
          type: 'bulkhead'
        });

        // Extract columns from first row
        if (cabin.rows.length > 0) {
          const firstRow = cabin.rows[0];
          let position = 'left';

          for (let i = 0; i < firstRow.seats.length; i++) {
            const seat = firstRow.seats[i];
            const nextSeat = firstRow.seats[i + 1];

            columns.push({
              letter: seat.column,
              position: position as any,
              aisleAfter: nextSeat && parseInt(nextSeat.column, 36) - parseInt(seat.column, 36) > 1
            });

            // Update position after aisle
            if (columns[columns.length - 1].aisleAfter) {
              position = this.getNextPosition(position);
            }
          }
        }
      }
    }

    return {
      columns,
      numberingStart: 1,
      numberingEnd: 50,
      skipRows: [],
      dividers
    };
  }

  private getNextPosition(current: string): string {
    const positions = ['left', 'center_left', 'center', 'center_right', 'right'];
    const currentIndex = positions.indexOf(current);
    return positions[Math.min(currentIndex + 1, positions.length - 1)];
  }
}
```

### Caching

```typescript
class SeatMapCache {
  private redis: Redis;
  private TTL = 30 * 60; // 30 minutes

  async get(flightId: string): Promise<SeatMap | null> {
    const key = this.buildKey(flightId);
    const data = await this.redis.get(key);

    if (!data) return null;

    return JSON.parse(data);
  }

  async set(flightId: string, seatMap: SeatMap): Promise<void> {
    const key = this.buildKey(flightId);
    const data = JSON.stringify(seatMap);
    await this.redis.setex(key, this.TTL, data);
  }

  async invalidate(flightId: string): Promise<void> {
    const key = this.buildKey(flightId);
    await this.redis.del(key);
  }

  private buildKey(flightId: string): string {
    return `seatmap:${flightId}`;
  }
}
```

---

## Seat Selection

### Seat Selection Service

```typescript
class SeatSelectionService {
  private holdManager: SeatHoldManager;

  async selectSeat(
    request: SeatSelectionRequest,
    context: BookingContext
  ): Promise<SeatSelectionResult> {
    // 1. Validate request
    await this.validateRequest(request, context);

    // 2. Get current seat map
    const seatMap = await this.getSeatMap(request.flightId);

    // 3. Find requested seat
    const seat = this.findSeat(seatMap, request.seatNumber);

    if (!seat) {
      throw new Error(`Seat ${request.seatNumber} not found`);
    }

    // 4. Check availability
    if (!seat.available || seat.status !== SeatStatus.AVAILABLE) {
      throw new Error(`Seat ${request.seatNumber} is not available`);
    }

    // 5. Check eligibility
    await this.checkEligibility(seat, request.passenger, context);

    // 6. Check for pricing
    const price = await this.calculateSeatPrice(seat, request, context);

    // 7. Create hold
    const hold = await this.holdManager.createHold({
      flightId: request.flightId,
      seatNumber: request.seatNumber,
      passengerId: request.passenger.id,
      bookingId: context.bookingId,
      price
    });

    return {
      success: true,
      seat,
      hold,
      price,
      expiresAt: hold.expiresAt
    };
  }

  async selectMultipleSeats(
    request: MultiSeatSelectionRequest,
    context: BookingContext
  ): Promise<SeatSelectionResult[]> {
    const results: SeatSelectionResult[] = [];

    // Get seat map once
    const seatMap = await this.getSeatMap(request.flightId);

    // Validate all seats are available first
    for (const seatRequest of request.seats) {
      const seat = this.findSeat(seatMap, seatRequest.seatNumber);

      if (!seat) {
        throw new Error(`Seat ${seatRequest.seatNumber} not found`);
      }

      if (!seat.available || seat.status !== SeatStatus.AVAILABLE) {
        throw new Error(`Seat ${seatRequest.seatNumber} is not available`);
      }
    }

    // Select seats in order
    for (const seatRequest of request.seats) {
      const result = await this.selectSeat(
        {
          ...seatRequest,
          flightId: request.flightId
        },
        context
      );

      results.push(result);
    }

    return results;
  }

  async findBestSeats(
    request: FindSeatsRequest,
    context: BookingContext
  ): Promise<Seat[]> {
    const seatMap = await this.getSeatMap(request.flightId);

    // Build scoring criteria
    const criteria = this.buildCriteria(request);

    // Score all available seats
    const scoredSeats = this.scoreSeats(seatMap, criteria);

    // Filter and sort
    const eligible = scoredSeats
      .filter(s => this.isEligible(s.seat, request.passengers, context))
      .sort((a, b) => b.score - a.score);

    // Return top N seats
    return eligible.slice(0, request.count).map(s => s.seat);
  }

  private scoreSeats(seatMap: SeatMap, criteria: SeatCriteria): ScoredSeat[] {
    const scored: ScoredSeat[] = [];

    for (const deck of seatMap.decks) {
      for (const cabin of deck.cabins) {
        for (const row of cabin.rows) {
          for (const seat of row.seats) {
            if (!seat.available) continue;

            const score = this.scoreSeat(seat, criteria);
            scored.push({ seat, score });
          }
        }
      }
    }

    return scored;
  }

  private scoreSeat(seat: Seat, criteria: SeatCriteria): number {
    let score = 0;

    // Position preference
    if (criteria.preferWindow && seat.attributes.includes(SeatAttribute.WINDOW)) {
      score += 20;
    }
    if (criteria.preferAisle && seat.attributes.includes(SeatAttribute.AISLE)) {
      score += 20;
    }

    // Avoid middle seats
    if (criteria.avoidMiddle && seat.attributes.includes(SeatAttribute.MIDDLE)) {
      score -= 30;
    }

    // Extra legroom
    if (seat.attributes.includes(SeatAttribute.EXTRA_LEGROOM)) {
      score += 15;
    }

    // Forward zone preference
    if (criteria.preferForward && seat.attributes.includes(SeatAttribute.FORWARD)) {
      score += 10;
    }

    // Quiet zone
    if (criteria.preferQuiet && seat.attributes.includes(SeatAttribute.QUIET_ZONE)) {
      score += 10;
    }

    // Avoid undesirable locations
    if (seat.attributes.includes(SeatAttribute.NEAR_LAVATORY)) {
      score -= 15;
    }
    if (seat.attributes.includes(SeatAttribute.NEAR_GALLEY)) {
      score -= 10;
    }

    // Price consideration
    if (criteria.maxPrice && seat.price && seat.price > criteria.maxPrice) {
      score -= 100; // Exclude overpriced seats
    }

    return score;
  }

  private async checkEligibility(
    seat: Seat,
    passenger: PassengerInfo,
    context: BookingContext
  ): Promise<void> {
    // Check age restrictions
    for (const restriction of seat.restrictions) {
      if (restriction.type === 'age') {
        const age = this.calculateAge(passenger.dateOfBirth);
        if (restriction.requirement === '15+' && age < 15) {
          throw new Error(`Passenger must be 15+ for seat ${seat.number}`);
        }
        if (restriction.requirement === '18+' && age < 18) {
          throw new Error(`Passenger must be 18+ for seat ${seat.number}`);
        }
      }

      if (restriction.type === 'physical') {
        // Check for physical requirements (e.g., emergency exit)
        // This might require passenger to confirm capability
      }
    }
  }

  private calculateAge(dateOfBirth: Date): number {
    const today = new Date();
    let age = today.getFullYear() - dateOfBirth.getFullYear();
    const monthDiff = today.getMonth() - dateOfBirth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dateOfBirth.getDate())) {
      age--;
    }
    return age;
  }
}

interface SeatSelectionRequest {
  flightId: string;
  seatNumber: string;
  passenger: PassengerInfo;
}

interface MultiSeatSelectionRequest {
  flightId: string;
  seats: Array<{
    seatNumber: string;
    passenger: PassengerInfo;
  }>;
}

interface FindSeatsRequest {
  flightId: string;
  count: number;
  passengers: PassengerInfo[];
  preferWindow?: boolean;
  preferAisle?: boolean;
  preferForward?: boolean;
  preferQuiet?: boolean;
  avoidMiddle?: boolean;
  maxPrice?: number;
  together?: boolean; // Try to seat together
}

interface SeatCriteria {
  preferWindow: boolean;
  preferAisle: boolean;
  preferForward: boolean;
  preferQuiet: boolean;
  avoidMiddle: boolean;
  maxPrice?: number;
  together: boolean;
}

interface ScoredSeat {
  seat: Seat;
  score: number;
}

interface SeatSelectionResult {
  success: boolean;
  seat: Seat;
  hold: SeatHold;
  price: number;
  expiresAt: Date;
}
```

---

## Seat Attributes

### Seat Attribute Filtering

```typescript
class SeatFilter {
  filter(
    seats: Seat[],
    filters: SeatFilterOptions
  ): Seat[] {
    return seats.filter(seat => this.matchesFilters(seat, filters));
  }

  private matchesFilters(seat: Seat, filters: SeatFilterOptions): boolean {
    // Position filter
    if (filters.position) {
      switch (filters.position) {
        case 'window':
          if (!seat.attributes.includes(SeatAttribute.WINDOW)) return false;
          break;
        case 'aisle':
          if (!seat.attributes.includes(SeatAttribute.AISLE)) return false;
          break;
        case 'middle':
          if (!seat.attributes.includes(SeatAttribute.MIDDLE)) return false;
          break;
      }
    }

    // Seat type filter
    if (filters.type) {
      if (seat.type !== filters.type) return false;
    }

    // Attributes filter
    if (filters.attributes && filters.attributes.length > 0) {
      for (const attr of filters.attributes) {
        if (!seat.attributes.includes(attr)) return false;
      }
    }

    // Price filter
    if (filters.maxPrice && seat.price) {
      if (seat.price > filters.maxPrice) return false;
    }

    // Availability filter
    if (filters.availableOnly && !seat.available) {
      return false;
    }

    // Cabin class filter
    if (filters.cabinClasses && !filters.cabinClasses.includes(seat.cabinClass)) {
      return false;
    }

    return true;
  }
}

interface SeatFilterOptions {
  position?: 'window' | 'aisle' | 'middle';
  type?: SeatType;
  attributes?: SeatAttribute[];
  maxPrice?: number;
  availableOnly?: boolean;
  cabinClasses?: CabinClass[];
}
```

### Seat Recommendations

```typescript
class SeatRecommender {
  recommend(
    seatMap: SeatMap,
    passenger: PassengerInfo,
    preferences: SeatPreferences
  ): SeatRecommendation[] {
    const recommendations: SeatRecommendation[] = [];

    // Get all available seats
    const availableSeats = this.getAvailableSeats(seatMap);

    // Score and rank seats
    const scored = availableSeats.map(seat => ({
      seat,
      score: this.calculateScore(seat, passenger, preferences)
    }));

    // Sort by score
    scored.sort((a, b) => b.score - a.score);

    // Generate recommendations
    for (const item of scored.slice(0, 10)) {
      recommendations.push({
        seat: item.seat,
        score: item.score,
        reasons: this.explainScore(item.seat, passenger, preferences),
        price: item.seat.price || 0
      });
    }

    return recommendations;
  }

  private calculateScore(
    seat: Seat,
    passenger: PassengerInfo,
    preferences: SeatPreferences
  ): number {
    let score = 50; // Base score

    // Position preference
    if (preferences.preferWindow && seat.attributes.includes(SeatAttribute.WINDOW)) {
      score += 25;
    }
    if (preferences.preferAisle && seat.attributes.includes(SeatAttribute.AISLE)) {
      score += 25;
    }
    if (preferences.avoidMiddle && seat.attributes.includes(SeatAttribute.MIDDLE)) {
      score -= 40;
    }

    // Extra legroom preference
    if (preferences.extraLegroom && seat.attributes.includes(SeatAttribute.EXTRA_LEGROOM)) {
      score += 20;
    }

    // Quiet zone preference
    if (preferences.quietZone && seat.attributes.includes(SeatAttribute.QUIET_ZONE)) {
      score += 15;
    }

    // Forward zone preference
    if (preferences.forwardZone && seat.attributes.includes(SeatAttribute.FORWARD)) {
      score += 10;
    }

    // Penalty for undesirable locations
    if (seat.attributes.includes(SeatAttribute.NEAR_LAVATORY)) {
      score -= 20;
    }
    if (seat.attributes.includes(SeatAttribute.NEAR_GALLEY)) {
      score -= 15;
    }

    // Price penalty (if budget conscious)
    if (preferences.budgetConscious && seat.price) {
      score -= seat.price * 0.1;
    }

    // Business class bonus
    if (seat.cabinClass === CabinClass.BUSINESS) {
      score += 30;
    }

    return Math.max(0, Math.min(100, score));
  }

  private explainScore(
    seat: Seat,
    passenger: PassengerInfo,
    preferences: SeatPreferences
  ): string[] {
    const reasons: string[] = [];

    if (seat.attributes.includes(SeatAttribute.WINDOW) && preferences.preferWindow) {
      reasons.push('Window seat');
    }
    if (seat.attributes.includes(SeatAttribute.AISLE) && preferences.preferAisle) {
      reasons.push('Aisle seat for easy access');
    }
    if (seat.attributes.includes(SeatAttribute.EXTRA_LEGROOM) && preferences.extraLegroom) {
      reasons.push('Extra legroom');
    }
    if (seat.attributes.includes(SeatAttribute.QUIET_ZONE) && preferences.quietZone) {
      reasons.push('Quiet zone');
    }
    if (seat.attributes.includes(SeatAttribute.NEAR_LAVATORY)) {
      reasons.push('Near lavatory (may be noisy)');
    }
    if (seat.price && seat.price > 0) {
      reasons.push(`Additional fee: ${seat.price} ${seat.currency}`);
    }

    return reasons;
  }
}

interface SeatPreferences {
  preferWindow: boolean;
  preferAisle: boolean;
  avoidMiddle: boolean;
  extraLegroom: boolean;
  quietZone: boolean;
  forwardZone: boolean;
  budgetConscious: boolean;
}

interface SeatRecommendation {
  seat: Seat;
  score: number;
  reasons: string[];
  price: number;
}
```

---

## Ancillary Services

### Service Types

```typescript
interface AncillaryService {
  id: string;
  type: AncillaryServiceType;
  name: string;
  description: string;

  // Pricing
  price: number;
  currency: string;
  taxIncluded: boolean;

  // Availability
  available: boolean;
  maxQuantity: number;

  // Conditions
  required: boolean;
  passengerType?: PassengerType;
  cabinClass?: CabinClass;

  // Restrictions
  restrictions: ServiceRestriction[];

  // Flight applicability
  flightApplicability: FlightApplicability;
}

enum AncillaryServiceType {
  // Baggage
  CHECKED_BAGGAGE = 'checked_baggage',
  CARRY_ON = 'carry_on',
  SPORTS_EQUIPMENT = 'sports_equipment',
  MUSICAL_INSTRUMENT = 'musical_instrument',
  PET_TRANSPORT = 'pet_transport',

  // Seat related
  SEAT_SELECTION = 'seat_selection',
  EXTRA_LEGROOM = 'extra_legroom',
  PREFERRED_SEAT = 'preferred_seat',
  FRONT_SEAT = 'front_seat',

  // In-flight
  MEAL = 'meal',
  DRINK = 'drink',
  WIFI = 'wifi',
  ENTERTAINMENT = 'entertainment',
  DUTY_FREE = 'duty_free',

  // Services
  PRIORITY_BOARDING = 'priority_boarding',
  LOUNGE_ACCESS = 'lounge_access',
  FAST_TRACK = 'fast_track',
  INSURANCE = 'insurance'
}

interface ServiceRestriction {
  type: 'weight' | 'size' | 'quantity' | 'passenger' | 'route';
  description: string;
  value?: any;
}

interface FlightApplicability {
  routes?: string[];           // Specific routes
  airlines?: string[];         // Specific airlines
  flightNumbers?: string[];    // Specific flights
  cabinClasses?: CabinClass[]; // Specific cabins
  duration?: {                 // Flight duration range
    min?: number;              // minutes
    max?: number;              // minutes
  };
}
```

### Ancillary Service Manager

```typescript
class AncillaryServiceManager {
  async getAvailableServices(
    flightId: string,
    offerId: string,
    context: BookingContext
  ): Promise<AncillaryService[]> {
    // 1. Get flight details
    const flight = await this.getFlightDetails(flightId);

    // 2. Get base services from airline
    const baseServices = await this.getAirlineServices(flight.airline);

    // 3. Filter by flight applicability
    const applicable = baseServices.filter(service =>
      this.isApplicable(service, flight)
    );

    // 4. Add marketplace services (insurance, etc.)
    const marketplaceServices = await this.getMarketplaceServices(flight);

    // 5. Check availability and pricing
    const available = await Promise.all(
      [...applicable, ...marketplaceServices].map(async service => ({
        ...service,
        available: await this.checkAvailability(service, flight, context),
        price: await this.getServicePrice(service, flight, context)
      }))
    );

    // 6. Filter unavailable services
    return available.filter(s => s.available);
  }

  async purchaseService(
    request: ServicePurchaseRequest,
    context: BookingContext
  ): Promise<ServicePurchaseResult> {
    // 1. Validate request
    await this.validatePurchaseRequest(request, context);

    // 2. Get service details
    const service = await this.getService(request.serviceId);

    // 3. Check availability
    const available = await this.checkAvailabilityForPurchase(
      service,
      request.flightId,
      request.quantity,
      context
    );

    if (!available) {
      throw new Error('Service not available for purchase');
    }

    // 4. Calculate total price
    const totalPrice = service.price * request.quantity;

    // 5. Process payment if required
    if (totalPrice > 0) {
      await this.processPayment(context.bookingId, totalPrice, context);
    }

    // 6. Create service record
    const record = await this.createServiceRecord({
      serviceId: service.id,
      bookingId: context.bookingId,
      passengerId: request.passengerId,
      flightId: request.flightId,
      quantity: request.quantity,
      price: service.price,
      totalPrice
    });

    // 7. Confirm with supplier if needed
    if (service.requiresConfirmation) {
      await this.confirmWithSupplier(record, service);
    }

    return {
      success: true,
      record,
      confirmationCode: record.confirmationCode
    };
  }

  private isApplicable(service: AncillaryService, flight: FlightDetails): boolean {
    const applicability = service.flightApplicability;

    // Check routes
    if (applicability.routes && applicability.routes.length > 0) {
      const route = `${flight.origin}-${flight.destination}`;
      if (!applicability.routes.includes(route)) {
        return false;
      }
    }

    // Check airlines
    if (applicability.airlines && !applicability.airlines.includes(flight.airline)) {
      return false;
    }

    // Check flight numbers
    if (applicability.flightNumbers && !applicability.flightNumbers.includes(flight.flightNumber)) {
      return false;
    }

    // Check cabin class
    if (applicability.cabinClasses && !applicability.cabinClasses.includes(flight.cabinClass)) {
      return false;
    }

    // Check duration
    if (applicability.duration) {
      const duration = flight.durationMinutes;
      if (applicability.duration.min && duration < applicability.duration.min) {
        return false;
      }
      if (applicability.duration.max && duration > applicability.duration.max) {
        return false;
      }
    }

    return true;
  }
}
```

---

## Seat Assignment

### Assignment Engine

```typescript
class SeatAssignmentEngine {
  async assignSeat(
    request: SeatAssignmentRequest,
    context: AssignmentContext
  ): Promise<SeatAssignment> {
    // 1. Validate assignment request
    await this.validateAssignment(request, context);

    // 2. Get current seat map
    const seatMap = await this.getSeatMap(request.flightId);

    // 3. Check seat availability
    const seat = this.findSeat(seatMap, request.seatNumber);

    if (!seat || !seat.available) {
      throw new Error(`Seat ${request.seatNumber} is not available`);
    }

    // 4. Release any existing hold
    await this.releaseHold(request.holdId);

    // 5. Confirm with airline/GDS
    const confirmation = await this.confirmWithAirline({
      flightId: request.flightId,
      seatNumber: request.seatNumber,
      passengerId: request.passengerId,
      bookingId: context.bookingId
    });

    // 6. Create assignment record
    const assignment = await this.createAssignment({
      flightId: request.flightId,
      seatNumber: request.seatNumber,
      passengerId: request.passengerId,
      bookingId: context.bookingId,
      confirmationCode: confirmation.confirmationCode
    });

    // 7. Update seat map cache
    await this.invalidateSeatMap(request.flightId);

    return assignment;
  }

  async autoAssignSeats(
    request: AutoAssignRequest,
    context: AssignmentContext
  ): Promise<SeatAssignment[]> {
    const assignments: SeatAssignment[] = [];

    // Get seat map
    const seatMap = await this.getSeatMap(request.flightId);

    // Get available seats
    const availableSeats = this.getAvailableSeats(seatMap);

    // Build criteria based on preferences
    const criteria = this.buildCriteria(request.preferences);

    // For each passenger
    for (const passenger of request.passengers) {
      // Find best seat
      const seat = this.findBestSeat(availableSeats, criteria, passenger);

      if (!seat) {
        throw new Error(`No available seats for passenger ${passenger.id}`);
      }

      // Assign seat
      const assignment = await this.assignSeat({
        flightId: request.flightId,
        seatNumber: seat.number,
        passengerId: passenger.id,
        holdId: null
      }, context);

      assignments.push(assignment);

      // Remove seat from available list
      const index = availableSeats.indexOf(seat);
      availableSeats.splice(index, 1);
    }

    return assignments;
  }

  async changeSeat(
    request: ChangeSeatRequest,
    context: AssignmentContext
  ): Promise<SeatAssignment> {
    // 1. Get current assignment
    const currentAssignment = await this.getCurrentAssignment(
      request.bookingId,
      request.passengerId
    );

    if (!currentAssignment) {
      throw new Error('No current seat assignment found');
    }

    // 2. Check if change is allowed
    const canChange = await this.canChangeSeat(currentAssignment, context);

    if (!canChange.allowed) {
      throw new Error(`Cannot change seat: ${canChange.reason}`);
    }

    // 3. Check if fee applies
    const changeFee = await this.calculateChangeFee(currentAssignment, request.newSeatNumber, context);

    // 4. Process fee if applicable
    if (changeFee > 0) {
      await this.processPayment(context.bookingId, changeFee, context);
    }

    // 5. Release current seat
    await this.releaseSeat(currentAssignment);

    // 6. Assign new seat
    return await this.assignSeat({
      flightId: request.flightId,
      seatNumber: request.newSeatNumber,
      passengerId: request.passengerId,
      holdId: null
    }, context);
  }

  private async canChangeSeat(
    assignment: SeatAssignment,
    context: AssignmentContext
  ): Promise<{ allowed: boolean; reason?: string }> {
    // Check fare rules
    const booking = await this.getBooking(assignment.bookingId);
    const fareRules = await this.getFareRules(booking);

    if (fareRules.seatChanges === 'not_allowed') {
      return { allowed: false, reason: 'Fare does not allow seat changes' };
    }

    // Check time restrictions
    const departureTime = await this.getDepartureTime(assignment.flightId);
    const hoursUntilDeparture = (departureTime.getTime() - Date.now()) / (1000 * 60 * 60);

    if (hoursUntilDeparture < fareRules.seatChangeDeadlineHours) {
      return { allowed: false, reason: 'Seat changes not allowed within deadline' };
    }

    return { allowed: true };
  }
}

interface SeatAssignmentRequest {
  flightId: string;
  seatNumber: string;
  passengerId: string;
  holdId?: string;
}

interface AutoAssignRequest {
  flightId: string;
  passengers: PassengerInfo[];
  preferences?: SeatPreferences;
  together?: boolean;
}

interface ChangeSeatRequest {
  bookingId: string;
  flightId: string;
  passengerId: string;
  newSeatNumber: string;
}

interface SeatAssignment {
  id: string;
  bookingId: string;
  flightId: string;
  passengerId: string;
  seatNumber: string;
  confirmationCode: string;
  assignedAt: Date;
  confirmed: boolean;
}
```

---

## Group Seating

### Group Seating Manager

```typescript
class GroupSeatingManager {
  async findGroupSeats(
    request: GroupSeatingRequest,
    context: BookingContext
  ): Promise<GroupSeatingOption[]> {
    const seatMap = await this.getSeatMap(request.flightId);

    // Get all available seats
    const availableSeats = this.getAvailableSeats(seatMap);

    // Find contiguous seat blocks
    const blocks = this.findContiguousBlocks(availableSeats, request.passengerCount);

    // Score each block
    const scoredBlocks = blocks.map(block => ({
      seats: block,
      score: this.scoreBlock(block, request.preferences)
    }));

    // Sort by score
    scoredBlocks.sort((a, b) => b.score - a.score);

    // Generate options
    return scoredBlocks.slice(0, 5).map(block => ({
      seats: block.seats,
      score: block.score,
      totalPrice: this.calculateBlockPrice(block.seats),
      description: this.describeBlock(block.seats)
    }));
  }

  private findContiguousBlocks(
    seats: Seat[],
    count: number
  ): Seat[][] {
    const blocks: Seat[][] = [];

    // Group seats by row
    const byRow = new Map<number, Seat[]>();
    for (const seat of seats) {
      if (!byRow.has(seat.row)) {
        byRow.set(seat.row, []);
      }
      byRow.get(seat.row)!.push(seat);
    }

    // Find contiguous blocks in each row
    for (const [row, rowSeats] of byRow) {
      // Sort by column
      rowSeats.sort((a, b) => a.column.localeCompare(b.column));

      // Find contiguous sequences
      for (let i = 0; i <= rowSeats.length - count; i++) {
        const block = rowSeats.slice(i, i + count);

        // Check if contiguous (no gaps larger than 1 seat)
        if (this.isContiguous(block)) {
          blocks.push(block);
        }
      }
    }

    return blocks;
  }

  private isContiguous(seats: Seat[]): boolean {
    for (let i = 0; i < seats.length - 1; i++) {
      const current = parseInt(seats[i].column, 36);
      const next = parseInt(seats[i + 1].column, 36);

      // More than 1 column apart means there's a gap
      if (next - current > 1) {
        return false;
      }
    }
    return true;
  }

  private scoreBlock(seats: Seat[], preferences?: SeatPreferences): number {
    let score = 50;

    // Prefer blocks with more window/aisle seats
    const windowCount = seats.filter(s => s.attributes.includes(SeatAttribute.WINDOW)).length;
    const aisleCount = seats.filter(s => s.attributes.includes(SeatAttribute.AISLE)).length;
    const middleCount = seats.filter(s => s.attributes.includes(SeatAttribute.MIDDLE)).length;

    score += windowCount * 10;
    score += aisleCount * 8;
    score -= middleCount * 5;

    // Prefer blocks together (lower row spread)
    const rows = new Set(seats.map(s => s.row));
    if (rows.size === 1) {
      score += 20; // All in same row
    }

    // Avoid undesirable locations
    const nearLavatory = seats.filter(s => s.attributes.includes(SeatAttribute.NEAR_LAVATORY)).length;
    score -= nearLavatory * 10;

    const nearGalley = seats.filter(s => s.attributes.includes(SeatAttribute.NEAR_GALLEY)).length;
    score -= nearGalley * 5;

    return score;
  }

  private calculateBlockPrice(seats: Seat[]): number {
    return seats.reduce((sum, seat) => sum + (seat.price || 0), 0);
  }

  private describeBlock(seats: Seat[]): string {
    const rows = [...new Set(seats.map(s => s.row))].sort((a, b) => a - b);
    const rowDesc = rows.length === 1
      ? `Row ${rows[0]}`
      : `Rows ${rows[0]}-${rows[rows.length - 1]}`;

    const windowSeats = seats.filter(s => s.attributes.includes(SeatAttribute.WINDOW)).length;
    const aisleSeats = seats.filter(s => s.attributes.includes(SeatAttribute.AISLE)).length;

    return `${rowDesc}, ${windowSeats} window, ${aisleSeats} aisle`;
  }
}

interface GroupSeatingRequest {
  flightId: string;
  passengerCount: number;
  preferences?: SeatPreferences;
}

interface GroupSeatingOption {
  seats: Seat[];
  score: number;
  totalPrice: number;
  description: string;
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** ✅ Complete
