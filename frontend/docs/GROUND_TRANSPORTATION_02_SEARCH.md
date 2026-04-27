# Ground Transportation 02: Search & Availability

> Finding transportation options, checking availability, and pricing estimation

---

## Document Overview

**Focus:** How customers discover and select ground transportation options
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Search Input
- What information do we need from customers?
- How do we specify pickup/dropoff locations? (Coordinates? Address? Airport codes?)
- How do we handle vague locations? ("Hotel in city center")
- What about multi-stop trips?
- How do we specify time? (Exact time? Window?)

### 2. Availability Checking
- How do we check real-time availability?
- What if providers don't have APIs?
- How far ahead can bookings be made?
- What about same-day requests?
- How do we handle "sold out" scenarios?

### 3. Pricing
- How is pricing calculated? (Fixed rates? Distance-based? Time-based?)
- Are prices dynamic or static?
- What about tolls, parking, airport fees?
- How do we handle currency conversion?
- What determines surge pricing?

### 4. Result Presentation
- How do we rank options? (Price? Quality? Speed?)
- What information must be shown? (Vehicle type? Provider? Cancellation policy?)
- How do we handle limited inventory?
- What about "similar options" when exact match unavailable?

---

## Research Areas

### A. Location Specification

**Pickup/Dropoff Input Types:**

| Type | Examples | Complexity |
|------|----------|------------|
| **Airport** | JFK, T3, Arrivals | Low (standardized) |
| **Hotel** |ByName, address, chain | Medium (name matching) |
| **Address** | Street address, coordinates | Medium (geocoding) |
| **Landmark** | "City center", train station | High (ambiguous) |
| **Coordinates** | Lat/long | Low (direct) |

**Research Questions:**
- How do we resolve hotel names to addresses?
- What about airport terminals vs. just airport code?
- How do we handle "pickup at hotel" when hotel unknown at booking time?
- Can we support "I'll decide later" for pickup location?

### B. Time Specification

**Time Input Scenarios:**

| Scenario | How to Handle |
|----------|---------------|
| **Flight arrival** | Auto-calculate based on landing + buffer |
| **Exact time** | Customer specifies |
| **Time window** | "Morning", "Afternoon", flexible |
| **ASAP** | Same-day, on-demand |
| **Schedule-based** | Shared shuttles with fixed times |

**Research Needed:**
- What buffer time after flight landing is typical?
- How do we handle flight delays affecting pickup time?
- What's the earliest customers can book?
- How far in advance do customers book?

### C. Availability by Transport Type

| Type | Availability Model | Research Needed |
|------|-------------------|-----------------|
| **Private transfer** | Vehicle/driver availability | ? |
| **Shared shuttle** | Scheduled, seat-based | ? |
| **Rental car** | Fleet inventory | ? |
| **Chauffeur** | Driver availability | ? |
| **Ride-hailing** | Real-time driver proximity | ? |

### D. Pricing Models

**Pricing Structures:**

| Model | Used By | Characteristics |
|-------|---------|-----------------|
| **Fixed rate** | Airport transfers, point-to-point | Known upfront, simple |
| **Distance-based** | Some car rentals, taxis | Depends on route |
| **Time-based** | Chauffeur, hourly rentals | Duration-based |
| **Dynamic** | Ride-hailing | Surge pricing |
| **Zone-based** | Some city transfers | Pickup/dropoff zones |

**Research:**
- Which providers use which model?
- How do we get price estimates without booking?
- Are prices guaranteed or estimated?
- What additional fees may apply? (Tolls, parking, airport fees, etc.)

---

## Search Request Model

```typescript
// Research-level model - not final

interface TransportSearchRequest {
  // Journey
  pickup: LocationSearch;
  dropoff: LocationSearch;
  stops?: LocationSearch[];

  // Time
  pickupTime: TimeSpecification;
  pickupTimeFlexibility?: Duration;

  // Requirements
  passengers: number;
  luggage: number;
  vehiclePreferences?: VehicleCategory[];

  // Constraints
    maxPrice?: Money;
    providers?: string[];  // Specific providers to include/exclude
  }

type TimeSpecification =
  | { type: 'exact', datetime: Date }
  | { type: 'flight_based', flightNumber: string, bufferMinutes?: number }
  | { type: 'window', start: Date, end: Date }
  | { type: 'flexible', date: Date, period: 'morning' | 'afternoon' | 'evening' }
  | { type: 'asap' };

interface LocationSearch {
  type: 'airport' | 'hotel' | 'address' | 'landmark' | 'coordinates';
  query: string;
  terminal?: string;  // For airports
}
```

---

## Search Response Model

```typescript
interface TransportSearchResponse {
  searchId: string;
  options: TransportOption[];
  filters: AvailableFilters;
  sorting: SortingOptions;
}

interface TransportOption {
  id: string;
  provider: ProviderInfo;
  type: TransportType;
  vehicle: VehicleInfo;

  // Pricing
  pricing: {
    estimated: Money;
    guaranteed: boolean;
    breakdown?: PriceBreakdown;
  };

  // Timing
  estimatedDuration: Duration;
  pickupTime: Date;
  dropoffTime: Date;

  // Availability
  availability: 'available' | 'limited' | 'sold_out';
  seatsAvailable?: number;

  // Policies
  cancellationPolicy: CancellationInfo;
  amendmentPolicy: AmendmentInfo;

  // Display
  badges?: string[];  // "Best value", "Fastest", etc.
  rating?: number;
}
```

---

## Integration Patterns

### 1. Direct API Search
**For:** Providers with bookable APIs

**Flow:**
```
Customer request → Transform to provider format → Call provider API → Transform response → Present
```

**Considerations:**
- How do we handle slow provider responses?
- What if provider is down?
- How do we cache results?

### 2. Aggregator Search
**For:** Working through aggregators (CarTrawler, etc.)

**Pros:**
- Single integration
- Broad coverage

**Cons:**
- Less control over results
- Additional margin

### 3. Manual/Static Catalog
**For:** Providers without APIs

**Approach:**
- Maintain rate catalog
- Check availability via phone/email
- Present "on request" options

**Research:**
- Is this viable for our scale?
- What operational overhead?

---

## Ranking & Personalization

**Ranking Factors to Explore:**

| Factor | Weight | Notes |
|--------|--------|-------|
| **Price** | High | Primary for many customers |
| **Quality/Rating** | Medium | Provider/vehicle rating |
| **Speed** | Medium | Duration, wait time |
| **Reliability** | High | On-time performance |
| **Cancellation** | Low | Flexibility of policy |
| **Previous bookings** | Medium | Customer preferences |

**Questions:**
- Can we personalize based on history?
- How do we handle "sponsored" rankings?
- What about business vs. leisure preferences?

---

## Open Problems

### 1. "Hotel To Be Decided"
**Scenario:** Customer books transfer, but hotel not yet finalized

**Options:**
- Require hotel name at booking (rigid)
- Allow "city center" as placeholder (vague)
- Allow modification later (complex)

**Research:** How do competitors handle this?

### 2. Multi-Leg Journeys
**Scenario:** Transfer from Airport → Hotel → Sightseeing → Hotel

**Questions:**
- Is this one booking or multiple?
- How do we price?
- What if one leg is unavailable?

### 3. Flight Delay Integration
**Scenario:** Booking based on flight arrival time

**Questions:**
- How do we track flight status?
- How do we auto-adjust pickup time?
- What is the buffer time?
- Who pays for waiting if flight is very late?

### 4. Real-Time Availability for Same-Day
**Challenge:** Customer wants transfer in 2 hours

**Questions:**
- Can providers confirm instantly?
- What fallback if fully booked?
- Do we show "on request" with disclaimer?

---

## Competitor Research Needed

| Competitor | Search Experience | Notable Patterns |
|------------|-------------------|------------------|
| **Rentalcars.com** | ? | ? |
| **Uber (scheduled)** | ? | ? |
| **GetYourGuide (transfers)** | ? | ? |
| **Viator (transfers)** | ? | ? |
| **Local India companies** | ? | ? |

---

## Experiments to Run

1. **Location resolution test:** How do we handle "pickup at Hilton in Singapore"?
2. **API availability test:** Which providers return real-time availability?
3. **Pricing accuracy study:** Do quoted prices match final prices?
4. **Search latency measurement:** How long do provider searches take?

---

## References

- [Flight Integration - Search](./FLIGHT_INTEGRATION_02_SEARCH.md) — Similar search patterns
- [Accommodation Catalog - Search](./ACCOMMODATION_CATALOG_04_SEARCH.md) — Location handling

---

## Next Steps

1. Test provider search APIs
2. Design location resolution system
3. Map pricing models by provider
4. Prototype search UI
5. Measure search latency

---

**Status:** Research Phase — Search patterns unknown

**Last Updated:** 2026-04-27
