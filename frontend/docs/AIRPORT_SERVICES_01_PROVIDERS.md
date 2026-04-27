# Airport Services 01: Provider Landscape

> Lounge access, fast track, meet & greet, and airport assistance

---

## Document Overview

**Focus:** Understanding the airport services ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Service Types
- What are the different airport services?
- Who operates lounges? (Airlines, independent, Priority Pass?)
- Who offers fast track? (Airport, airline, third-party?)
- What about meet & greet services?

### 2. Provider Landscape
- Who are the major lounge operators?
- Who provides fast track services?
- Who offers meet & greet?
- What are the regional differences?

### 3. Access Models
- How do customers access these services?
- What are the eligibility rules? (Class of service, status, paid?)
- Can we book these services separately?
- What about bundled offerings?

### 4. Integration
- Do providers offer booking APIs?
- How do we confirm availability?
- What are the delivery methods?
- How do we handle same-day bookings?

---

## Research Areas

### A. Lounge Access

**Lounge Types:**

| Type | Operator | Access Method | Research Needed |
|------|----------|---------------|-----------------|
| **Airline lounges** | Airlines | Status, class, paid | ? |
| **Independent lounges** | Lounge group, Plaza Premium | Paid, memberships | ? |
| **Credit card lounges** | Priority Pass, etc. | Card membership | ? |
| **Pay-per-use** | Various | Online, walk-in | ? |

**Major Operators:**

| Operator | Locations | Booking | Notes |
|----------|----------|---------|-------|
| **Plaza Premium** | Global | Online/API? | ? |
| **LoungeGroup** | Global | Online/API? | ? |
| **Aspire** | Global | Online/API? | ? |
| **No1 Lounges** | UK/Europe | Online/API? | ? |
| **Airport lounges** | Various | Direct/airline | ? |

**Research:**
- API availability for booking
- Commission structures
- Integration complexity

### B. Fast Track Services

**Fast Track Types:**

| Type | Description | Providers |
|------|-------------|-----------|
| **Security fast track** | Skip security lines | Airport, some airlines |
| **Immigration fast track** | Skip immigration | Airport, visa services |
| **Boarding fast track** | Priority boarding | Airlines (status/class) |

**Research:**
- Can fast track be booked separately?
- How does it vary by airport?
- What are the typical costs?

### C. Meet & Greet

**Service Levels:**

| Level | Description | Research Needed |
|-------|-------------|-----------------|
| **Arrival meet** | Meet at gate/baggage, assist to exit | ? |
| **Departure assist** | Meet at curb, assist through check-in/security | ? |
| **Connection assist** | Meet at gate, assist to connection | ? |
| **Full service** | Airport to car transfer, baggage handling | ? |

**Providers:**

| Type | Examples | Notes |
|------|----------|-------|
| **Airport service** | Many airports | Direct booking |
| **Airlines** | First/business, some economy | Status/Class |
| **Specialized services** | Airport helpers | Pre-booked |

### D. Airport Service Aggregators

**Platforms:**

| Platform | Services | API? | Notes |
|----------|----------|------|-------|
| **Priority Pass** | Lounges | ? | Membership |
| **LoungePass** | Lounges | ? | Day passes |
| **Dr. Pingpong** | Lounges, fast track | ? | Global |
| **Booking.com** | Some services | ? | Travel add-ons |

**Research:**
- Which offer APIs?
- What are the commissions?
- How do we integrate?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface AirportServiceProvider {
  id: string;
  name: string;
  type: ServiceProviderType;

  // Coverage
  airports: string[];
  services: AirportServiceType[];

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;

  // Commercial
  commissionRate?: number;
}

type ServiceProviderType =
  | 'lounge_operator'
  | 'airport_authority'
  | 'airline'
  | 'aggregator'
  | 'concierge_service';

type AirportServiceType =
  | 'lounge_access'
  | 'fast_track_security'
  | 'fast_track_immigration'
  | 'meet_greet_arrival'
  | 'meet_greet_departure'
  | 'baggage_service'
  | 'buggy_service';

interface AirportService {
  id: string;
  providerId: string;
  airport: string;
  terminal?: string;
  type: AirportServiceType;

  // Availability
  availability: ServiceAvailability;
  operatingHours?: OperatingHours;

  // Access
  accessMethods: AccessMethod[];

  // Pricing
  pricing: {
    basePrice: Money;
    childPrice?: Money;
    currency: string;
  };

  // Restrictions
  restrictions?: ServiceRestriction[];

  // Delivery
  deliveryMethod: ServiceDelivery;
}

type AccessMethod =
  | 'paid_entry'
  | 'membership'
  | 'airline_status'
  | 'class_of_service'
  | 'credit_card';

type ServiceDelivery =
  | 'qr_code'
  | 'print_at_home'
  | 'collect_at_counter'
  | 'name_on_list';
```

---

## Access Eligibility

**Lounge Access:**

| Method | Typical Requirements | Examples |
|--------|---------------------|----------|
| **Paid** | Anyone with booking | Independent lounges |
| **Membership** | Priority Pass, etc. | Lounge network |
| **Status** | Elite tier | Airline lounges |
| **Class** | Business/first | Airline lounges |
| **Credit card** | Specific cards | Various lounges |

**Fast Track Access:**

| Method | Requirements | Examples |
|--------|--------------|----------|
| **Paid** | Anyone with booking | Many airports |
| **Status** | Elite tier | Some airlines |
| **Class** | Business/first | Most airlines |
| **Credit card** | Premium cards | Some airports |

**Research:**
- Which methods work at which airports?
- How do we verify eligibility?
- What about combinations?

---

## Open Problems

### 1. Real-Time Availability
**Challenge:** Lounges can reach capacity

**Options:**
- Real-time API check
- Time-slot booking
- First-come, first-served

**Research:** How do providers handle capacity?

### 2. Terminal/Gate Specificity
**Challenge:** Services may be terminal-specific

**Questions:**
- How do we know which terminal?
- What if flight changes terminal?
- What if airline changes?

### 3. Eligibility Verification
**Challenge:** Customer claims they have access

**Options:**
- Trust customer
- Verify at service entrance
| Pre-verify via API

### 4. Booking Timing
**Challenge:** Can we book same-day? Day-of?

**Options:**
- Advance booking only
| Same-day until X hours
| Real-time booking

**Research:** What are the cutoff times?

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **Priority Pass** | ? | ? |
| **Airlines** | ? | ? |
| **Airport websites** | ? | ? |

---

## Experiments to Run

1. **API availability test:** Which providers have bookable APIs?
2. **Capacity test:** How often are lounges full?
3. **Price comparison study:** How do prices compare?
4. **User test:** How do customers book these services?

---

## References

- [Flight Integration](./FLIGHT_INTEGRATION_MASTER_INDEX.md) — Flight context
| [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Add-on component

---

## Next Steps

1. Audit airport service APIs
2. Map coverage by airport
3. Design booking flow
4. Test availability systems
5. Build integration

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
