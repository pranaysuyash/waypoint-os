# Ground Transportation 01: Architecture & Providers

> Provider landscape, service types, and integration patterns for ground transportation

---

## Document Overview

**Focus:** Understanding the ground transportation ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Provider Landscape
- Who are the major players in car rental?
- Who provides private transfer services?
- What about shared shuttles and ride-hailing integration?
- How does this differ by region?
- Which providers have APIs vs. require manual booking?

### 2. Service Types
- What types of ground transportation do customers need?
- Private transfer vs. rental car vs. ride-hailing — when is each preferred?
- How do we handle chauffeur services?
- What about specialized transport (wheelchair, child seats)?
- How do multi-stop trips work?

### 3. Integration Patterns
- Do providers offer APIs or is it email/phone?
- What is the booking flow for each provider type?
- How do we handle real-time availability?
- What about pricing — dynamic vs. fixed?
- How do we handle cancellations and modifications?

### 4. Regional Differences
- How does India differ from US/Europe/SE Asia?
- Are there regional champions in each market?
- What regulatory differences exist?
- How do we handle cross-border rentals?

---

## Research Areas

### A. Car Rental Ecosystem

**Global Players:**
| Provider | API | Coverage | Notes |
|----------|-----|----------|-------|
| Hertz | ? | Global | ? |
| Avis | ? | Global | ? |
| Enterprise | ? | Global | ? |
| Europcar | ? | Europe | ? |

**Regional Players:**
| Region | Provider | API | Notes |
|--------|----------|-----|-------|
| India | Zoomcar | ? | Self-drive |
| India | Myles | ? | Self-drive |
| India | Revv | ? | Self-drive |
| SE Asia | ? | ? | ? |
| ME | ? | ? | ? |

**Research Needed:**
- API availability for each major provider
- Commission structures
- Booking lead times
- Cancellation policies
- Integration complexity

### B. Transfer Services

**Service Categories:**

| Type | Description | Providers (Research) |
|------|-------------|---------------------|
| **Private Transfer** | Dedicated vehicle, point-to-point | ? |
| **Shared Shuttle** | Multiple passengers, shared vehicle | ? |
| **Airport Express** | Fixed route, airport to city | ? |
| **Chauffeur** | Professional driver, luxury vehicles | ? |
| **Ride-hailing** | On-demand (Uber, Grab, etc.) | ? |

**Questions:**
- Are transfer services aggregator-based or direct?
- What are the typical lead times?
- How do we handle flight delays for airport pickups?
- What are the pricing models?

### C. Ride-Hailing Integration

**Considerations:**
- Do customers want ride-hailing booked in advance?
- Or is it more of a "on arrival" recommendation?
- Can we integrate with Uber/Grab APIs?
- What value do we add vs. customer booking directly?

**Research:**
- Interview customers: do they want pre-booked rides?
- Check API availability: Uber API, Grab API, etc.
- Understand the value proposition

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface GroundTransportProvider {
  id: string;
  name: string;
  type: ProviderType;
  region: string[];
  hasApi: boolean;
  integrationStatus: 'not_integrated' | 'exploring' | 'integrated';

  // Capabilities
  supportedVehicleTypes: VehicleCategory[];
  supportedServices: TransportType[];
  bookingLeadTime: LeadTimeWindow;
  cancellationPolicy: CancellationPolicy;

  // Commercial
  commissionRate?: number;
  paymentTerms?: PaymentTerms;
}

type ProviderType =
  | 'rental_car_company'
  | 'transfer_service'
  | 'ride_hailing_platform'
  | 'chauffeur_service'
  | 'aggregator';

interface VehicleCategory {
  code: string;
  name: string;
  capacity: {
    passengers: number;
    luggage: number;
  };
  features: string[];  // AC, automatic, etc.
}
```

---

## Integration Approaches

### 1. Direct API Integration
**Best for:** Large providers with mature APIs

**Pros:**
- Real-time availability
- Instant confirmation
- Automated operations

**Cons:**
- Development effort per provider
- Maintenance burden
- Provider dependency

### 2. Aggregator Integration
**Best for:** Fragmented provider landscape

**Examples:** CarTrawler, Rentalcars.com

**Pros:**
- Single integration
- Broad coverage
- Standardized interface

**Cons:**
- Additional margin/commission
- Less control
- Dependent on aggregator

### 3. Manual/White-label
**Best for:** Small providers, complex requests

**Pros:**
- Can work with anyone
- Flexibility

**Cons:**
- Manual overhead
- Slower turnaround
- Error-prone

**Research Question:**
Which approach for which segment?

---

## Operational Considerations

### A. Booking Lead Times
| Service Type | Typical Lead Time | Research Needed |
|--------------|-------------------|-----------------|
| Airport transfer | ? | How much advance notice? |
| Car rental | ? | Same-day possible? |
| Chauffeur | ? | How far ahead? |
| Shared shuttle | ? | Schedule-based? |

### B. Cancellation Windows
| Service Type | Free Cancellation | Penalty Structure |
|--------------|-------------------|-------------------|
| Car rental | ? | ? |
| Private transfer | ? | ? |
| Shared shuttle | ? | ? |

### C. Payment Timing
| Service Type | Payment Required | Deposit Model |
|--------------|------------------|---------------|
| Car rental | ? | At pickup? |
| Private transfer | ? | Pre-pay? |
| Shared | ? | ? |

---

## Customer Use Cases

**Research Needed: Interview agents/customers**

1. **Airport arrival pickup**
   - Flight delayed → how is driver informed?
   - Meet and greet → where exactly?
   - What if customer can't find driver?

2. **Inter-city transfer**
   - How do we specify route/stops?
   - What about tolls and parking?
   - Driver for the day vs. point-to-point?

3. **Self-drive rental**
   - License requirements (international?)
   - Insurance coverage
   - Fuel policy
   - Drop-off charges

4. **Special requirements**
   - Child seats
   - Wheelchair accessibility
   - Extra luggage
   - Pet-friendly vehicles

---

## Competitor Research Needed

| Competitor | Transport Options | Notable Features |
|------------|-------------------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **Rentalcars.com** | ? | ? |
| **GetYourGuide** (transfers) | ? | ? |
| **Viator** (transfers) | ? | ? |
| **Local India agents** | ? | ? |

---

## Open Problems

### 1. Flight Delay Integration
**Scenario:** Airport pickup booked, flight is delayed

**Questions:**
- How do we track flight status?
- How do we notify the provider?
- What is the grace period?
- Who pays for waiting time?

### 2. Cross-Border Rentals
**Scenario:** Renting in one country, dropping in another

**Questions:**
- What fees apply?
- Which providers allow this?
- Insurance implications?
- How do we display this to customers?

### 3. Provider Fragmentation
**Challenge:** Many small providers, no APIs

**Options:**
- Focus only on API-enabled providers (limited coverage)
- Build manual booking workflow (operational cost)
- Use aggregators (margin cost)

**Research:** What is the coverage vs. cost trade-off?

---

## Experiments to Run

1. **Provider audit:** Catalog available providers in top 5 destinations
2. **API availability test:** Check which providers have bookable APIs
3. **Agent interviews:** What are the pain points in booking transport?
4. **Customer survey:** What transport options do they ask for?

---

## References

- [Flight Integration - Operations](./FLIGHT_INTEGRATION_06_OPERATIONS.md) — For flight delay tracking
- [Trip Builder - Components](./TRIP_BUILDER_01_ARCHITECTURE.md) — Component model
- [Booking Engine](./BOOKING_ENGINE_01_ARCHITECTURE.md) — Booking patterns

---

## Next Steps

1. Audit provider landscape for key destinations
2. Test API availability for major providers
3. Interview agents about current transport booking
4. Map customer use cases
5. Evaluate aggregator options

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
