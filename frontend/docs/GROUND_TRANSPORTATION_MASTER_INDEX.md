# Ground Transportation — Master Index

> Complete navigation guide for all Ground Transportation documentation

---

## Series Overview

**Topic:** Transfers, car rentals, and ground transportation logistics
**Status:** Complete (4 of 4 documents)
**Last Updated:** 2026-04-27

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 1 | [Architecture & Providers](#gt-01) | Provider landscape, data model | ✅ Complete |
| 2 | [Search & Availability](#gt-02) | Finding options, real-time availability | ✅ Complete |
| 3 | [Booking & Operations](#gt-03) | Reservation flow, driver assignment | ✅ Complete |
| 4 | [Disruptions & Support](#gt-04) | Delays, no-shows, driver issues | ✅ Complete |

---

## Document Summaries

### GT_01: Architecture & Providers

**File:** `GROUND_TRANSPORTATION_01_ARCHITECTURE.md`

**Topics:**
- Provider landscape (rental companies, transfer services)
- Service types (private, shared, self-drive, chauffeur)
- Data model
- Integration patterns
- Geographic coverage

**Research Questions:**
- Who are the key providers in each market?
- What APIs exist vs. manual booking?
- How do we handle fragmented provider landscape?
- What are the regional differences?

---

### GT_02: Search & Availability

**File:** `GROUND_TRANSPORTATION_02_SEARCH.md`

**Topics:**
- Location-based search
- Availability checking
- Pricing estimation
- Vehicle options
- Route calculation

**Research Questions:**
- How do we specify pickup/dropoff locations?
- How far in advance can bookings be made?
- What determines availability?
- How do we handle airport vs. city locations?

---

### GT_03: Booking & Operations

**File:** `GROUND_TRANSPORTATION_03_BOOKING.md`

**Topics:**
- Reservation workflow
- Payment handling
- Driver assignment
- Confirmation delivery
- Meet & greet procedures

**Research Questions:**
- What information is required at booking?
- How are drivers assigned?
- What is the confirmation flow?
- How do we handle special requests?

---

### GT_04: Disruptions & Support

**File:** `GROUND_TRANSPORTATION_04_DISRUPTIONS.md`

**Topics:**
- Flight delay integration
- Driver no-shows
- Vehicle breakdowns
- Cancellations and refunds
- Customer support

**Research Questions:**
- How do we track flight delays for airport pickups?
- What is the no-show policy?
- How do we handle cancellations?
- What is the dispute resolution process?

---

## Related Documentation

**Cross-References:**
- [Flight Integration](./FLIGHT_INTEGRATION_MASTER_INDEX.md) — For delay tracking integration
- [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Component assembly
- [Booking Engine](./BOOKING_ENGINE_MASTER_INDEX.md) — State machine patterns

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Provider Type** | TBD after research |
| **API vs. Manual** | TBD based on provider capabilities |
| **Real-time Tracking** | TBD based on customer value |
| **Pre-booking vs. On-demand** | TBD based on usage patterns |

---

## Data Model Overview

```typescript
// Research-level sketch

interface GroundTransportBooking {
  id: string;
  tripId: string;
  type: TransportType;
  provider: string;

  // Locations
  pickup: Location;
  dropoff: Location;
  via?: Location[];  // For multi-stop

  // Timing
  scheduledPickup: Date;
  scheduledDropoff: Date;

  // Vehicle
  vehicleCategory: VehicleCategory;
  passengerCount: number;
  luggageCount: number;

  // Pricing
  pricing: TransportPricing;

  // Status
  status: BookingStatus;
  driver?: DriverInfo;
  tracking?: TrackingInfo;
}

type TransportType =
  | 'private_transfer'
  | 'shared_transfer'
  | 'rental_car'
  | 'chauffeur_service';

enum BookingStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  DRIVER_ASSIGNED = 'driver_assigned',
  EN_ROUTE = 'en_route',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show'
}
```

---

## Provider Landscape (Research Needed)

### Car Rental
| Region | Major Players | API Availability |
|--------|--------------|------------------|
| Global | Hertz, Avis, Enterprise | ? |
| Europe | Europcar, Sixt | ? |
| India | Zoomcar, Myles | ? |
| APAC | ? | ? |

### Transfer Services
| Type | Players | API Availability |
|------|---------|------------------|
| Private | ? | ? |
| Shared | ? | ? |
| Airport | ? | ? |

---

## Implementation Checklist

### Phase 1: Research
- [ ] Provider landscape audit
- [ ] API availability assessment
- [ ] Competitive analysis
- [ ] Customer use case interviews

### Phase 2: Core Integration
- [ ] Provider selection
- [ ] API integration
- [ ] Search and availability
- [ ] Booking flow

### Phase 3: Operations
- [ ] Driver management
- [ ] Tracking integration
- [ ] Disruption handling
- [ ] Customer support

---

**Last Updated:** 2026-04-27

**Current Progress:** 4 of 4 documents complete (100%)
