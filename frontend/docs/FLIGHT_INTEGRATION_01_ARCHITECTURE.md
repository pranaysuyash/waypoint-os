# Flight Integration 01: Architecture

> System design, data model, GDS integration, and infrastructure

---

## Overview

This document details the flight integration subsystem, covering airline booking, inventory management, pricing, and ticketing. The system integrates with multiple GDS providers (Amadeus, Sabre, Travelport) and modern NDC APIs to provide comprehensive flight search and booking capabilities.

**Key Capabilities:**
- Multi-source flight search
- Real-time availability and pricing
- Complex itinerary routing
- Seat map integration
- E-ticket generation
- Disruption management

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Domain Model](#domain-model)
3. [GDS Integration](#gds-integration)
4. [Search Infrastructure](#search-infrastructure)
5. [Pricing Architecture](#pricing-architecture)
6. [Ticketing System](#ticketing-system)

---

## System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FLIGHT INTEGRATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐│
│  │   CLIENT    │───▶│  API GATEWAY│───▶│  SEARCH     │───▶│  CACHE      ││
│  │  REQUESTS   │    │             │    │  SERVICE    │    │  (Redis)    ││
│  └─────────────┘    └─────────────┘    └──────┬──────┘    └─────────────┘│
│                                                 │                           │
│                     ┌─────────────────────────┴─────────────────┐          │
│                     │       FLIGHT BOOKING SERVICE            │          │
│                     └─────────────────────────┬─────────────────┘          │
│                                   │                                   │
│           ┌───────────────────────┼───────────────────────┐               │
│           │                       │                       │               │
│  ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐       │
│  │  PRICING        │   │  INVENTORY      │   │  SEAT MAP       │       │
│  │  ENGINE         │   │  TRACKER        │   │  SERVICE        │       │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘       │
│           │                     │                      │                 │
│           └─────────────────────┴──────────────────────┘                 │
│                                   │                                       │
│  ┌────────────────────────────────┴─────────────────────────────────┐   │
│  │                      SUPPLIER ADAPTERS                          │   │
│  ├──────────┬──────────┬──────────┬──────────┬──────────┬───────┤   │
│  │ Amadeus  │  Sabre   │Travelport│  NDC     │  LCC     │Direct│   │
│  └────┬─────┴─────┬────┴─────┬────┴─────┬────┴─────┬────┴──────┘   │
│       │           │           │           │          │              │
│       └───────────┴───────────┴───────────┴──────────┘              │
│                              │                                       │
│                   AIRLINE SUPPLIER APIs                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **API Gateway** | Request routing, auth, rate limiting | Node.js/Express |
| **Search Service** | Flight search, routing, filtering | TypeScript |
| **Pricing Engine** | Fare calculation, tax computation | Python |
| **Inventory Tracker** | Availability monitoring | Node.js |
| **Seat Map Service** | Seat selection, maps | TypeScript |
| **Cache Layer** | Search results, pricing | Redis |
| **PNR Manager** | Booking record management | PostgreSQL |
| **Ticket Service** | E-ticket generation | Python |

---

## Domain Model

### Core Entities

```typescript
interface Flight {
  id: string;
  flightNumber: string;
  airline: Airline;

  // Schedule
  departure: FlightSchedule;
  arrival: FlightSchedule;
  durationMinutes: number;
  distanceKm: number;

  // Equipment
  equipment: Aircraft;
  equipmentCode?: string;

  // Frequency
  frequency: FlightFrequency;
  operationalStatus: OperationalStatus;

  // Metadata
  isCodeshare: boolean;
  isWetlease: boolean;
  codeshares: CodeshareInfo[];
}

interface Airline {
  iataCode: string;
  icaoCode: string;
  name: LocalizedText;
  logoUrl: string;
  country: string;
  callsign: string;
}

interface FlightSchedule {
  date: Date; // LocalDate for recurring
  time: string; // HH:MM format
  airport: Airport;
  terminal?: string;
  gate?: string;
}

interface Airport {
  iataCode: string;
  icaoCode: string;
  name: LocalizedText;
  city: LocalizedText;
  country: LocalizedText;
  countryCode: string;
  latitude: number;
  longitude: number;
  timezone: string;
  hubs: string[]; // Airline hubs
}

interface Aircraft {
  iataCode: string;
  icaoCode: string;
  name: string;
  manufacturer: string;
  model: string;
  seats: number;
  cargoCapacityKg: number;
}

interface FlightFrequency {
  daysOfWeek: number[]; // 0-6 (Sun-Sat)
  effectiveFrom: Date;
  effectiveUntil?: Date;
  seasonal: boolean;
}

type OperationalStatus =
  | 'scheduled'
  | 'delayed'
  | 'cancelled'
  | 'diverted'
  | 'in_air';

interface CodeshareInfo {
  marketingCarrier: string;
  marketingFlightNumber: string;
  operatingCarrier: string;
  operatingFlightNumber: string;
}

interface FlightOffer {
  id: string;
  source: string; // GDS or airline
  slices: FlightSlice[];
  pricing: FlightPricing;
  fareType: FareType;
  cabinClass: CabinClass;
  bookingClass: BookingClass;
  fareBasis: string;
  seatsAvailable: number;
  guarantee: 'guaranteed' | 'shopping';

  // Restrictions
  restrictions: FareRestrictions;

  // Metadata
  eticketEligible: boolean;
  multipartIndicator: boolean;
  interlineAgreement: boolean;
}

interface FlightSlice {
  id: string;
  segments: FlightSegment[];
  durationMinutes: number;
  stops: number;
  layovers: LayoverInfo[];

  // Connection info
  connectionDuration?: number;
  overnightConnection: boolean;
  aircraftChange: boolean;
  terminalChange: boolean;
}

interface FlightSegment {
  id: string;
  flight: Flight;
  marketingCarrier: string;
  operatingCarrier: string;
  flightNumber: string;

  // Schedule
  departure: FlightSchedule;
  arrival: FlightSchedule;

  // Booking details
  cabinClass: CabinClass;
  bookingClass: BookingClass;
  fareBasis: string;

  // Baggage
  baggageAllowance: BaggageAllowance;

  // Meal
  mealService?: MealService;
}

interface LayoverInfo {
  airport: Airport;
  durationMinutes: number;
  isOvernight: boolean;
  internationalTransfer: boolean;
  visaRequired: boolean;
  terminalChange: boolean;
}

interface FlightPricing {
  base: Money;
  taxes: TaxBreakdown;
  fees: FeeBreakdown;
  total: Money;
  currency: string;

  // Per-passenger breakdown
  passengerBreakdown: PassengerPricing[];

  // Price components
  components: PriceComponent[];
}

interface TaxBreakdown {
  items: TaxItem[];
  total: Money;
}

interface TaxItem {
  code: string;
  name: LocalizedText;
  amount: Money;
  type: 'tax' | 'fee' | 'surcharge';
  included: boolean;
}

interface FeeBreakdown {
  items: FeeItem[];
  total: Money;
}

interface FeeItem {
  code: string;
  name: LocalizedText;
  amount: Money;
  type: 'carrier' | 'service' | 'agency';
  optional: boolean;
}

interface PassengerPricing {
  type: PassengerType;
  count: number;
  baseFare: Money;
  taxes: Money;
  fees: Money;
  total: Money;
  fareInfo: FareInfo[];
}

interface FareInfo {
  code: string;
  cabinClass: CabinClass;
  bookingClass: BookingClass;
  fareBasis: string;
  price: Money;
  restrictions: FareRestrictions;
}

interface FareRestrictions {
  refundable: boolean;
  changeable: boolean;
  advancePurchase?: number; // days
  minimumStay?: number; // days
  maximumStay?: number; // days
  blackoutDates?: DateRange[];
  seasonalPricing?: boolean;
  saturdayNightStay?: boolean;
}

interface PriceComponent {
  type: 'base' | 'tax' | 'fee' | 'surcharge' | 'discount';
  code: string;
  name: LocalizedText;
  amount: Money;
  included: boolean;
}

interface BaggageAllowance {
  carryOn: {
    pieces: number;
    weightKg?: number;
    dimensionsCm?: [number, number, number];
  };
  checked: {
    pieces: number;
    weightKg?: number;
    dimensionsCm?: [number, number, number];
  };
  sportsEquipment?: BaggageAllowanceItem[];
}

interface MealService {
  provided: boolean;
  type?: MealType;
  specialMealsAvailable?: SpecialMealType[];
}

interface PNR {
  id: string; // Record locator
  source: string; // GDS or airline
  airlineCode: string;

  // Flights
  segments: FlightSegment[];

  // Passengers
  passengers: Passenger[];

  // Contact
  contact: ContactInfo;

  // Pricing
  pricing: FlightPricing;

  // Status
  status: PNRStatus;
  ticketing: TicketingInfo;

  // Timestamps
  createdAt: Date;
  modifiedAt: Date;
  expiresAt?: Date;
}

interface Passenger {
  id: string;
  type: PassengerType;
  title: string;
  firstName: string;
  lastName: string;
  dateOfBirth?: Date;
  nationality?: string;
  passport?: PassportInfo;
  loyaltyPrograms?: LoyaltyMembership[];
  specialAssistance?: SpecialAssistance[];
}

type PassengerType = 'adult' | 'child' | 'infant' | 'senior';

interface PassportInfo {
  number: string;
  expiryDate: Date;
  issuingCountry: string;
}

interface Ticket {
  id: string; // Ticket number
  pnrId: string;
  passengerId: string;

  // Flight
  flights: FlightSegment[];

  // Fare
  fareInfo: FareInfo;
  pricing: Money;

  // Status
  status: TicketStatus;
  issued: boolean;
  issuedAt?: Date;

  // Restrictions
  endorsements: string[];
  restrictions: FareRestrictions;

  // Barcode
  barcode?: string;
}

type PNRStatus = 'held' | 'confirmed' | 'ticketed' | 'cancelled' | 'void';
type TicketStatus = 'draft' | 'issued' | 'void' | 'refunded' | 'exchanged';

type CabinClass = 'economy' | 'premium_economy' | 'business' | 'first';
type BookingClass =
  | 'R' | 'O' | 'N' | 'Q' | 'G' | // Discount economy
  | 'V' | 'W' | 'S' | 'Y' | 'B' | 'M' | // Regular economy
  | 'E' | 'U' | 'H' | // Premium economy
  | 'J' | 'C' | 'D' | 'I' | 'Z' | // Business
  | 'F' | 'A' | 'P'; // First

type FareType =
  | 'public'
  | 'private'
  | 'corporate'
  | 'government'
  | 'military'
  | 'youth'
  | 'student';

type MealType =
  | 'none'
  | 'snack'
  | 'breakfast'
  | 'lunch'
  | 'dinner'
  | 'full_meal';

type SpecialMealType =
  | 'vegetarian'
  | 'vegan'
  | 'kosher'
  | 'halal'
  | 'diabetic'
  | 'gluten_free'
  | 'low_sodium'
  | 'low_fat'
  | 'child'
  | 'baby';

interface Seat {
  id: string;
  number: string;
  row: number;
  column: string;
  deck: number;

  // Characteristics
  characteristics: SeatCharacteristics;

  // Availability
  available: boolean;
  occupiedBy?: string; // Passenger ID when occupied

  // Pricing
  price?: Money;

  // Location
  location: SeatLocation;
}

interface SeatCharacteristics {
  type: SeatType;
  class: CabinClass;
  exitRow: boolean;
  bulkhead: boolean;
  window: boolean;
  aisle: boolean;
  middle: boolean;
  reclining: boolean;
  legroom: 'standard' | 'extra' | 'limited';
  nearLavatory: boolean;
  nearGalley: boolean;
  crewSeat: boolean;
}

type SeatType = 'standard' | 'preferred' | 'extra_legroom' | 'suite';

interface SeatLocation {
  zone: string;
  position: 'front' | 'middle' | 'rear';
  side: 'left' | 'right';
}
```

### Database Schema

```sql
-- Airlines
CREATE TABLE airlines (
  icao_code CHAR(7) PRIMARY KEY,
  iata_code CHAR(2) UNIQUE NOT NULL,
  name JSONB NOT NULL,
  logo_url TEXT,
  country_code CHAR(2) NOT NULL,
  callsign VARCHAR(20),

  INDEX idx_airlines_iata (iata_code),
  INDEX idx_airlines_country (country_code)
);

-- Airports
CREATE TABLE airports (
  iata_code CHAR(3) PRIMARY KEY,
  icao_code CHAR(4) UNIQUE,
  name JSONB NOT NULL,
  city JSONB NOT NULL,
  country JSONB NOT NULL,
  country_code CHAR(2) NOT NULL,
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  timezone VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_airports_country (country_code),
  INDEX idx_airports_location (latitude, longitude)
);

-- Flights
CREATE TABLE flights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  airline_icao CHAR(7) NOT NULL REFERENCES airlines(icao_code),
  flight_number VARCHAR(10) NOT NULL,
  departure_airport CHAR(3) NOT NULL REFERENCES airports(iata_code),
  arrival_airport CHAR(3) NOT NULL REFERENCES airports(iata_code),

  departure_time TIME NOT NULL,
  arrival_time TIME NOT NULL,
  duration_minutes INTEGER NOT NULL,
  distance_km INTEGER,

  equipment_code VARCHAR(10),
  operational_status VARCHAR(20) DEFAULT 'scheduled',

  frequency_days INTEGER[] NOT NULL,
  effective_from DATE NOT NULL,
  effective_until DATE,

  is_codeshare BOOLEAN DEFAULT false,
  operating_carrier_icao CHAR(7) REFERENCES airlines(icao_code),

  INDEX idx_flights_route (departure_airport, arrival_airport),
  INDEX idx_flights_airline (airline_icao),
  INDEX idx_flights_frequency (effective_from, effective_until)
);

-- Flight Offers (cache)
CREATE TABLE flight_offers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source VARCHAR(20) NOT NULL,

  search_params JSONB NOT NULL,
  slices JSONB NOT NULL,
  pricing JSONB NOT NULL,

  fare_type VARCHAR(20) NOT NULL,
  cabin_class VARCHAR(20) NOT NULL,
  booking_class CHAR(1) NOT NULL,
  seats_available INTEGER NOT NULL,

  guarantee VARCHAR(20) NOT NULL,
  valid_until TIMESTAMP WITH TIME ZONE NOT NULL,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_flight_offers_search (search_params),
  INDEX idx_flight_offers_valid (valid_until)
);

-- PNRs
CREATE TABLE pnrs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  record_locator CHAR(6) UNIQUE NOT NULL,
  source VARCHAR(20) NOT NULL,
  airline_code CHAR(2) NOT NULL,

  segments JSONB NOT NULL,
  passengers JSONB NOT NULL,
  contact JSONB NOT NULL,
  pricing JSONB NOT NULL,

  status VARCHAR(20) NOT NULL,
  ticketing_status VARCHAR(20),
  ticketing_deadline TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE,

  INDEX idx_pnrs_locator (record_locator),
  INDEX idx_pnrs_status (status),
  INDEX idx_pnrs_created (created_at)
);

-- Tickets
CREATE TABLE tickets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_number VARCHAR(20) UNIQUE NOT NULL,
  pnr_id UUID NOT NULL REFERENCES pnrs(id) ON DELETE CASCADE,
  passenger_id UUID NOT NULL,

  flights JSONB NOT NULL,
  fare_info JSONB NOT NULL,
  pricing JSONB NOT NULL,

  status VARCHAR(20) NOT NULL,
  issued BOOLEAN DEFAULT false,
  issued_at TIMESTAMP WITH TIME ZONE,

  barcode VARCHAR(100),
  endorsements TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  INDEX idx_tickets_pnr (pnr_id),
  INDEX idx_tickets_number (ticket_number),
  INDEX idx_tickets_status (status)
);
```

---

## GDS Integration

### Integration Architecture

```typescript
export interface GDSAdapter {
  readonly providerId: string;
  readonly name: string;

  // Capabilities
  readonly capabilities: GDSCapabilities;

  // Shopping
  searchFlights(request: FlightSearchRequest): Promise<FlightOffer[]>;
  getFlightDetails(offerId: string): Promise<FlightOffer>;

  // Pricing
  verifyPrice(offer: FlightOffer): Promise<PriceVerification>;

  // Availability
  checkAvailability(offer: FlightOffer): Promise<AvailabilityStatus>;

  // Booking
  createPNR(request: BookingRequest): Promise<PNR>;
  cancelPNR(recordLocator: string): Promise<Cancellation>;

  // Ticketing
  issueTicket(pnrId: string): Promise<Ticket>;
  voidTicket(ticketNumber: string): Promise<void>;

  // Seat maps
  getSeatMap(flightId: string, cabinClass: CabinClass): Promise<SeatMap>;
  selectSeats(pnrId: string, seats: SeatSelection[]): Promise<void>;

  // Schedules
  getFlightSchedule(flightNumber: string, date: Date): Promise<FlightScheduleInfo>;
}

interface GDSCapabilities {
  shopping: {
    oneWay: boolean;
    roundTrip: boolean;
    multiCity: boolean;
    flexibleDates: boolean;
    nearbyAirports: boolean;
  };
  pricing: {
    realTimePricing: boolean;
    priceVerification: boolean;
    shoppingCacheTTL: number;
  };
  booking: {
    pnrCreation: boolean;
    ticketing: boolean;
    voiding: boolean;
    refunding: boolean;
    exchanging: boolean;
  };
  seats: {
    seatMaps: boolean;
    seatSelection: boolean;
    advanceSelection: boolean;
  };
  schedules: {
    realTimeStatus: boolean;
    scheduleChanges: boolean;
  };
}
```

### Normalization Pipeline

```typescript
export class FlightDataNormalizer {
  async normalizeFlightOffer(
    rawOffer: RawFlightOffer,
    source: string
  ): Promise<FlightOffer> {
    // Normalize airline info
    const airline = await this.normalizeAirline(rawOffer.airline, source);

    // Normalize airports
    const departure = await this.normalizeAirport(rawOffer.departure);
    const arrival = await this.normalizeAirport(rawOffer.arrival);

    // Normalize schedule
    const schedule = this.normalizeSchedule(rawOffer.schedule);

    // Normalize pricing
    const pricing = await this.normalizePricing(rawOffer.pricing, source);

    // Normalize fare information
    const fareInfo = await this.normalizeFareInfo(rawOffer.fareInfo);

    // Normalize segments
    const segments = await this.normalizeSegments(
      rawOffer.segments,
      source
    );

    return {
      id: this.generateOfferId(source, rawOffer.id),
      source,
      slices: this.buildSlices(segments),
      pricing,
      fareType: fareInfo.type,
      cabinClass: fareInfo.cabinClass,
      bookingClass: fareInfo.bookingClass,
      fareBasis: fareInfo.fareBasis,
      seatsAvailable: rawOffer.seatsAvailable,
      guarantee: this.determineGuarantee(rawOffer),
      restrictions: this.normalizeRestrictions(rawOffer.restrictions),
      eticketEligible: rawOffer.eticketEligible ?? true,
      multipartIndicator: rawOffer.multipart ?? false,
      interlineAgreement: rawOffer.interline ?? false,
    };
  }

  private async normalizeAirline(
    raw: RawAirline,
    source: string
  ): Promise<Airline> {
    // Try to find by IATA code
    let airline = await this.airlineRepository.findByIATA(raw.iataCode);

    if (!airline) {
      // Create new airline entry
      airline = await this.airlineRepository.create({
        iataCode: raw.iataCode,
        icaoCode: raw.icaoCode || raw.iataCode.padStart(7, 'X'),
        name: { en: raw.name },
        logoUrl: raw.logoUrl,
        countryCode: raw.countryCode,
        callsign: raw.callsign,
      });
    }

    return airline;
  }

  private async normalizeAirport(
    raw: RawAirport
  ): Promise<Airport> {
    let airport = await this.airportRepository.findByIATA(raw.iataCode);

    if (!airport) {
      airport = await this.airportRepository.create({
        iataCode: raw.iataCode,
        icaoCode: raw.icaoCode,
        name: { en: raw.name },
        city: { en: raw.city },
        country: { en: raw.country },
        countryCode: raw.countryCode,
        latitude: raw.latitude,
        longitude: raw.longitude,
        timezone: raw.timezone,
      });
    }

    return airport;
  }

  private async normalizePricing(
    raw: RawPricing,
    source: string
  ): Promise<FlightPricing> {
    // Normalize taxes
    const taxes = await this.normalizeTaxes(raw.taxes, source);

    // Normalize fees
    const fees = await this.normalizeFees(raw.fees, source);

    // Build price components
    const components: PriceComponent[] = [
      {
        type: 'base',
        code: 'FARE',
        name: { en: 'Base Fare' },
        amount: raw.base,
        included: true,
      },
      ...taxes.items.map(t => ({
        type: 'tax' as const,
        code: t.code,
        name: t.name,
        amount: t.amount,
        included: t.included,
      })),
      ...fees.items.map(f => ({
        type: 'fee' as const,
        code: f.code,
        name: f.name,
        amount: f.amount,
        included: f.included,
      })),
    ];

    return {
      base: raw.base,
      taxes,
      fees,
      total: raw.total,
      currency: raw.currency,
      passengerBreakdown: raw.passengerBreakdown,
      components,
    };
  }

  private async normalizeTaxes(
    raw: RawTax[],
    source: string
  ): Promise<TaxBreakdown> {
    const items: TaxItem[] = [];

    for (const tax of raw) {
      const mapped = await this.taxMapper.map(tax.code, source);
      if (mapped) {
        items.push({
          code: mapped.code,
          name: mapped.name,
          amount: tax.amount,
          type: mapped.type,
          included: tax.included,
        });
      }
    }

    return {
      items,
      total: items.reduce((sum, t) => sum + t.amount.amount, 0),
    };
  }

  private determineGuarantee(raw: RawFlightOffer): 'guaranteed' | 'shopping' {
    // Shopping offers are approximate and require re-pricing
    if (raw.requiresRepricing || !raw.realTimeAvailability) {
      return 'shopping';
    }
    return 'guaranteed';
  }
}
```

---

## Search Infrastructure

### Search Service

```typescript
export class FlightSearchService {
  async search(request: FlightSearchRequest): Promise<FlightSearchResult> {
    // 1. Check cache first
    const cached = await this.cacheService.get(request);
    if (cached) {
      return this.validateCachedResults(cached);
    }

    // 2. Build search queries for each provider
    const providers = this.getProvidersForRequest(request);

    // 3. Parallel search across providers
    const results = await Promise.allSettled(
      providers.map(provider =>
        this.searchProvider(provider, request)
      )
    );

    // 4. Merge and deduplicate results
    const merged = this.mergeResults(results);

    // 5. Sort by price and quality
    const sorted = this.sortResults(merged, request);

    // 6. Cache results
    await this.cacheService.set(request, sorted, this.CACHE_TTL);

    return {
      request,
      offers: sorted.offers,
      metadata: {
        providers: providers.map(p => p.id),
        searchTime: sorted.searchTime,
        totalResults: sorted.offers.length,
      },
    };
  }

  private async searchProvider(
    provider: GDSProvider,
    request: FlightSearchRequest
  ): Promise<FlightOffer[]> {
    const adapter = this.adapterFactory.getAdapter(provider.id);

    try {
      const raw = await adapter.searchFlights(request);
      return Promise.all(
        raw.map(r => this.normalizer.normalizeFlightOffer(r, provider.id))
      );
    } catch (error) {
      this.logger.error(`Search failed for provider ${provider.id}`, { error });
      return [];
    }
  }

  private mergeResults(
    results: PromiseSettledResult<FlightOffer[]>[]
  ): FlightOffer[] {
    const offers = results
      .filter(r => r.status === 'fulfilled')
      .flatMap(r => r.value);

    // Deduplicate by flight numbers and times
    const unique = new Map<string, FlightOffer>();

    for (const offer of offers) {
      const key = this.generateOfferKey(offer);
      const existing = unique.get(key);

      if (!existing || offer.pricing.total.amount < existing.pricing.total.amount) {
        unique.set(key, offer);
      }
    }

    return Array.from(unique.values());
  }

  private generateOfferKey(offer: FlightOffer): string {
    const segments = offer.slices.flatMap(s => s.segments);

    const flightKeys = segments
      .map(s => `${s.marketingCarrier}${s.flightNumber}${s.departure.time}`)
      .join('-');

    return `${flightKeys}-${offer.cabinClass}-${offer.bookingClass}`;
  }

  private sortResults(
    results: { offers: FlightOffer[]; searchTime: number },
    request: FlightSearchRequest
  ): FlightSearchResult {
    const offers = [...results.offers];

    switch (request.sortBy) {
      case 'price':
        offers.sort((a, b) =>
          a.pricing.total.amount - b.pricing.total.amount
        );
        break;

      case 'duration':
        offers.sort((a, b) => {
          const aDuration = this.totalDuration(a);
          const bDuration = this.totalDuration(b);
          return aDuration - bDuration;
        });
        break;

      case 'departure':
        offers.sort((a, b) => {
          const aTime = this.firstDeparture(a);
          const bTime = this.firstDeparture(b);
          return aTime.getTime() - bTime.getTime();
        });
        break;

      case 'quality':
      default:
        // Score by price, duration, stops, and quality
        offers.sort((a, b) => this.calculateQualityScore(b) - this.calculateQualityScore(a));
    }

    return {
      offers,
      searchTime: results.searchTime,
    };
  }

  private calculateQualityScore(offer: FlightOffer): number {
    let score = 0;

    // Price score (lower is better, but normalize)
    const priceScore = Math.max(0, 1000 - offer.pricing.total.amount) / 1000;
    score += priceScore * 0.4;

    // Duration score (shorter is better)
    const duration = this.totalDuration(offer);
    const durationScore = Math.max(0, 1 - duration / (24 * 60)); // Normalize to 0-1
    score += durationScore * 0.2;

    // Stops score (fewer is better)
    const stops = this.totalStops(offer);
    const stopsScore = Math.max(0, 1 - stops / 3);
    score += stopsScore * 0.2;

    // Quality score (guaranteed offers preferred)
    if (offer.guarantee === 'guaranteed') {
      score += 0.15;
    }

    // Refundable bonus
    if (offer.restrictions.refundable) {
      score += 0.05;
    }

    return score;
  }

  private totalDuration(offer: FlightOffer): number {
    return offer.slices.reduce((sum, s) => sum + s.durationMinutes, 0);
  }

  private totalStops(offer: FlightOffer): number {
    return offer.slices.reduce((sum, s) => sum + s.stops, 0);
  }

  private firstDeparture(offer: FlightOffer): Date {
    const firstSegment = offer.slices[0]?.segments[0];
    return new Date(`${firstSegment.departure.date}T${firstSegment.departure.time}`);
  }

  private readonly CACHE_TTL = 300; // 5 minutes
}
```

---

## Pricing Architecture

### Pricing Engine

```typescript
export class FlightPricingEngine {
  async calculatePrice(
    offer: FlightOffer,
    passengers: PassengerCount,
    currency: string
  ): Promise<FlightPricing> {
    // 1. Convert base price to requested currency
    const converted = await this.convertCurrency(
      offer.pricing.base,
      currency
    );

    // 2. Calculate per-passenger pricing
    const passengerPricing = await Promise.all([
      this.calculateAdultPricing(offer, passengers.adults, currency),
      this.calculateChildPricing(offer, passengers.children || 0, currency),
      this.calculateInfantPricing(offer, passengers.infants || 0, currency),
    ]);

    // 3. Calculate total
    const total = passengerPricing.reduce(
      (sum, p) => sum + p.total.amount,
      0
    );

    // 4. Build tax and fee breakdowns
    const taxes = await this.calculateTaxes(offer, total, currency);
    const fees = await this.calculateFees(offer, total, currency);

    return {
      base: converted,
      taxes,
      fees,
      total: {
        amount: total,
        currency,
      },
      currency,
      passengerBreakdown: passengerPricing.flat(),
      components: this.buildComponents(offer, taxes, fees),
    };
  }

  private async calculateAdultPricing(
    offer: FlightOffer,
    count: number,
    currency: string
  ): Promise<PassengerPricing[]> {
    const pricing: PassengerPricing[] = [];

    for (let i = 0; i < count; i++) {
      const baseFare = await this.convertCurrency(
        offer.pricing.base,
        currency
      );

      const taxes = await this.calculatePassengerTaxes(
        offer,
        baseFare,
        'adult'
      );

      const fees = await this.calculatePassengerFees(
        offer,
        baseFare,
        'adult'
      );

      pricing.push({
        type: 'adult',
        count: 1,
        baseFare,
        taxes,
        fees,
        total: {
          amount: baseFare.amount + taxes.amount + fees.amount,
          currency,
        },
        fareInfo: offer.pricing.passengerBreakdown
          .filter(p => p.type === 'adult')
          .map(p => p.fareInfo),
      });
    }

    return pricing;
  }

  private async calculateChildPricing(
    offer: FlightOffer,
    count: number,
    currency: string
  ): Promise<PassengerPricing[]> {
    // Children typically pay a percentage of adult fare
    const childDiscount = 0.25; // 25% discount

    const pricing: PassengerPricing[] = [];

    for (let i = 0; i < count; i++) {
      const adultFare = await this.convertCurrency(
        offer.pricing.base,
        currency
      );

      const baseFare: Money = {
        amount: adultFare.amount * (1 - childDiscount),
        currency,
      };

      const taxes = await this.calculatePassengerTaxes(
        offer,
        baseFare,
        'child'
      );

      const fees = await this.calculatePassengerFees(
        offer,
        baseFare,
        'child'
      );

      pricing.push({
        type: 'child',
        count: 1,
        baseFare,
        taxes,
        fees,
        total: {
          amount: baseFare.amount + taxes.amount + fees.amount,
          currency,
        },
        fareInfo: offer.pricing.passengerBreakdown
          .filter(p => p.type === 'child')
          .map(p => p.fareInfo),
      });
    }

    return pricing;
  }

  private async calculateInfantPricing(
    offer: FlightOffer,
    count: number,
    currency: string
  ): Promise<PassengerPricing[]> {
    // Infants typically pay only taxes
    const pricing: PassengerPricing[] = [];

    for (let i = 0; i < count; i++) {
      const baseFare: Money = {
        amount: 0,
        currency,
      };

      const taxes = await this.calculatePassengerTaxes(
        offer,
        baseFare,
        'infant'
      );

      const fees = await this.calculatePassengerFees(
        offer,
        baseFare,
        'infant'
      );

      pricing.push({
        type: 'infant',
        count: 1,
        baseFare,
        taxes,
        fees,
        total: {
          amount: baseFare.amount + taxes.amount + fees.amount,
          currency,
        },
        fareInfo: offer.pricing.passengerBreakdown
          .filter(p => p.type === 'infant')
          .map(p => p.fareInfo),
      });
    }

    return pricing;
  }

  private async convertCurrency(
    amount: Money,
    toCurrency: string
  ): Promise<Money> {
    if (amount.currency === toCurrency) {
      return amount;
    }

    const rate = await this.fxService.getRate(amount.currency, toCurrency);
    return {
      amount: amount.amount * rate,
      currency: toCurrency,
    };
  }
}
```

---

## Ticketing System

### Ticket Generation

```typescript
export class TicketService {
  async issueTicket(pnrId: string): Promise<Ticket> {
    const pnr = await this.pnrRepository.findById(pnrId);

    if (!pnr) {
      throw new NotFoundError('PNR not found');
    }

    if (pnr.status === 'ticketed') {
      throw new ConflictError('PNR already ticketed');
    }

    // Generate ticket for each passenger
    const tickets: Ticket[] = [];

    for (const passenger of pnr.passengers) {
      const ticket = await this.generateTicket(pnr, passenger);
      tickets.push(ticket);
    }

    // Issue tickets with supplier
    const adapter = this.adapterFactory.getAdapter(pnr.source);
    const issuedTickets = await adapter.issueTicket(pnrId);

    // Update tickets with supplier ticket numbers
    for (let i = 0; i < tickets.length; i++) {
      tickets[i].id = issuedTickets[i].ticketNumber;
      tickets[i].issued = true;
      tickets[i].issuedAt = new Date();

      await this.ticketRepository.create(tickets[i]);
    }

    // Update PNR status
    await this.pnrRepository.update(pnrId, {
      status: 'ticketed',
      ticketingStatus: 'complete',
    });

    // Generate PDF tickets
    for (const ticket of tickets) {
      await this.generateTicketPDF(ticket);
    }

    return tickets[0];
  }

  private async generateTicket(pnr: PNR, passenger: Passenger): Promise<Ticket> {
    const ticketNumber = await this.generateTicketNumber(
      pnr.airlineCode,
      pnr.source
    );

    // Get passenger's flights
    const passengerFlights = pnr.segments;

    return {
      id: ticketNumber,
      pnrId: pnr.id,
      passengerId: passenger.id,

      flights: passengerFlights,

      fareInfo: {
        code: 'Y',
        cabinClass: 'economy',
        bookingClass: 'Y',
        fareBasis: 'YLOW',
        price: {
          amount: 0, // Calculated from PNR pricing
          currency: 'USD',
        },
        restrictions: {
          refundable: false,
          changeable: false,
        },
      },

      pricing: {
        amount: 0,
        currency: 'USD',
      },

      status: 'draft',
      issued: false,

      endorsements: [],
      restrictions: {
        refundable: false,
        changeable: false,
      },
    };
  }

  private async generateTicketNumber(
    airlineCode: string,
    source: string
  ): Promise<string> {
    // Ticket number format: airline-code (3 digits) serial number (10 digits)
    const airlineNumeric = this.airlineToNumeric(airlineCode);
    const serial = await this.getNextSerialNumber(airlineCode);

    return `${airlineNumeric}-${serial.toString().padStart(10, '0')}`;
  }

  private airlineToNumeric(iataCode: string): string {
    // Convert airline IATA code to numeric (IATA resolution 785)
    const mapping: Record<string, string> = {
      'AA': '001', // American Airlines
      'UA': '016', // United Airlines
      'DL': '006', // Delta
      'BA': '125', // British Airways
      'LH': '220', // Lufthansa
      'AF': '057', // Air France
      // ... more mappings
    };

    return mapping[iataCode] || '000';
  }

  private async getNextSerialNumber(airlineCode: string): Promise<number> {
    // Get next serial number from sequence
    return await this.sequenceService.next(`ticket:${airlineCode}`);
  }

  private async generateTicketPDF(ticket: Ticket): Promise<void> {
    const pdf = await this.pdfGenerator.generate({
      template: 'flight_ticket',
      data: {
        ticket,
        pnr: await this.pnrRepository.findById(ticket.pnrId),
        passenger: await this.passengerRepository.findById(ticket.passengerId),
        flights: ticket.flights,
      },
    });

    const storageKey = `tickets/${ticket.id}.pdf`;
    await this.storageService.upload(storageKey, pdf);

    // Update ticket with PDF URL
    await this.ticketRepository.update(ticket.id, {
      pdfUrl: `${process.env.CDN_URL}/${storageKey}`,
    });
  }

  async voidTicket(ticketNumber: string): Promise<void> {
    const ticket = await this.ticketRepository.findByNumber(ticketNumber);

    if (!ticket) {
      throw new NotFoundError('Ticket not found');
    }

    if (ticket.status !== 'issued') {
      throw new ValidationError('Only issued tickets can be voided');
    }

    // Void with supplier
    const pnr = await this.pnrRepository.findById(ticket.pnrId);
    const adapter = this.adapterFactory.getAdapter(pnr.source);

    await adapter.voidTicket(ticketNumber);

    // Update status
    await this.ticketRepository.update(ticket.id, {
      status: 'void',
    });
  }
}
```

---

## API Endpoints

### Search Endpoints

```
POST   /flights/search
GET    /flights/suggestions
POST   /flights/autocomplete
```

### Offer Endpoints

```
POST   /flights/offers/verify-price
GET    /flights/offers/:offerId
```

### Booking Endpoints

```
POST   /flights/bookings
GET    /flights/bookings/:bookingId
POST   /flights/bookings/:bookingId/ticket
```

### Seat Map Endpoints

```
GET    /flights/offers/:offerId/seat-map
POST   /flights/bookings/:bookingId/seats
```

### Ticket Endpoints

```
GET    /flights/tickets/:ticketNumber
POST   /flights/tickets/:ticketNumber/void
POST   /flights/tickets/:ticketNumber/refund
```

---

**Next:** [Search & Shopping](./FLIGHT_INTEGRATION_02_SEARCH.md) — Flight search, filtering, and sorting
