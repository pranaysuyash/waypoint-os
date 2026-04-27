# Flight Integration — Master Index

> Complete navigation guide for all Flight Integration documentation

---

## Series Overview

**Topic:** Airline booking, inventory, and ticketing
**Status:** Complete (6 of 6 documents)
**Last Updated:** 2026-04-27

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 1 | [Flight Architecture](#flight-01) | System design, data model, GDS integration | ✅ Complete |
| 2 | [Search & Shopping](#flight-02) | Flight search, filtering, sorting | ✅ Complete |
| 3 | [Pricing & Fares](#flight-03) | Fare types, pricing, taxes | ✅ Complete |
| 4 | [Seat Management](#flight-04) | Seat maps, selection, assignments | ✅ Complete |
| 5 | [Ticketing](#flight-05) | Ticket generation, issuance, modifications | ✅ Complete |
| 6 | [Operations](#flight-06) | Schedules, disruptions, rebooking | ✅ Complete |

---

## Document Summaries

### FLIGHT_01: Flight Architecture

**File:** `FLIGHT_INTEGRATION_01_ARCHITECTURE.md`

**Topics:**
- Flight domain model
- GDS/integrator integration patterns
- Search infrastructure
- Pricing architecture
- Ticketing systems

---

### FLIGHT_02: Search & Shopping

**File:** `FLIGHT_INTEGRATION_02_SEARCH.md`

**Topics:**
- Flight search algorithms
- Multi-leg routing
- Filtering and faceting
- Price sorting
- Alternative suggestions

---

### FLIGHT_03: Pricing & Fares

**File:** `FLIGHT_INTEGRATION_03_PRICING.md`

**Topics:**
- Fare types and classes
- Price calculation
- Tax and fee handling
- Currency conversion
- Dynamic pricing

---

### FLIGHT_04: Seat Management

**File:** `FLIGHT_INTEGRATION_04_SEATS.md`

**Topics:**
- Seat map management
- Seat selection
- Seat attributes
- Ancillary services

---

### FLIGHT_05: Ticketing

**File:** `FLIGHT_INTEGRATION_05_TICKETING.md`

**Topics:**
- Ticket generation
- PNR management
- E-ticket issuance
- Ticket modifications
- Refunds and exchanges

---

### FLIGHT_06: Operations

**File:** `FLIGHT_INTEGRATION_06_OPERATIONS.md`

**Topics:**
- Flight schedules
- Status tracking
- Disruption handling
- Rebooking workflows
- Notifications

---

## Related Documentation

**Cross-References:**
- [Booking Engine](./BOOKING_ENGINE_MASTER_INDEX.md) — Core booking orchestration
- [Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md) — Stay booking
- [Payment Processing](./PAYMENT_PROCESSING_MASTER_INDEX.md) — Payment handling
- [Supplier Integration](./SUPPLIER_INTEGRATION_MASTER_INDEX.md) — External APIs

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **GDS Aggregators** | Single API vs multiple airline integrations |
| **NDC Support** | New Distribution Capability for modern content |
| **Cache Shopping** | High-volume search performance |
| **Async Pricing** | Non-blocking price verification |
| **PNR Management** | Guest name record lifecycle tracking |

---

## Data Model Overview

```typescript
interface Flight {
  id: string;
  flightNumber: string;
  airline: Airline;
  departure: AirportSchedule;
  arrival: AirportSchedule;
  equipment: Aircraft;
  duration: number; // minutes
  distance: number; // km
  frequency: FlightFrequency;
}

interface FlightSearchRequest {
  origin: string; // IATA code
  destination: string;
  departureDate: Date;
  returnDate?: Date;
  passengers: PassengerCount;
  cabinClass: CabinClass;
  flexibleDates?: boolean;
  directOnly?: boolean;
}

interface FlightOffer {
  id: string;
  slices: FlightSlice[];
  pricing: FlightPricing;
  fareType: FareType;
  bookingClass: BookingClass;
  seatsAvailable: number;
  guarantee: 'guaranteed' | 'shopping';
}

interface FlightSlice {
  segments: FlightSegment[];
  duration: number;
  stops: number;
  layovers: LayoverInfo[];
}

interface FlightSegment {
  flight: Flight;
  cabinClass: CabinClass;
  bookingClass: BookingClass;
  fareBasis: string;
  marketingCarrier: string;
  operatingCarrier: string;
  codeshares: string[];
}
```

---

## Flight Classes

| Class | Description | Typical Amenities |
|-------|-------------|-------------------|
| **Economy** | Basic fare | Seat, carry-on |
| **Premium Economy** | Enhanced economy | Extra legroom, priority boarding |
| **Business** | Business class | Lie-flat seats, lounge access |
| **First** | First class | Suites, premium service |

---

## Fare Types

| Type | Description | Changes | Refund |
|------|-------------|---------|--------|
| **Basic** | Lowest price | No changes | Non-refundable |
| **Standard** | Regular fare | Fee-based changes | Refundable |
| **Flexible** | Premium fare | Free changes | Fully refundable |
| **Business** | Business fare | Free changes | Fully refundable |

---

## Implementation Checklist

### Phase 1: Core Search
- [ ] Flight search integration
- [ ] Real-time availability
- [ ] Price verification
- [ ] PNR creation

### Phase 2: Booking
- [ ] Passenger data collection
- [ ] Seat selection
- [ ] Payment processing
- [ ] Ticket issuance

### Phase 3: Operations
- [ ] Schedule tracking
- [ ] Status updates
- [ ] Disruption handling
- [ ] Rebooking automation

### Phase 4: Advanced Features
- [ ] Multi-city booking
- [ ] Code-share handling
- [ ] Ancillary services
- [ ] Loyalty integration

---

**Last Updated:** 2026-04-27

**Current Progress:** 6 of 6 documents complete (100%)
