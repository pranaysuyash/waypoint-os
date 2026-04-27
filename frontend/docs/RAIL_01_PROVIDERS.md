# Rail Integration 01: Provider Landscape

> Rail operators, rail passes, and the train booking ecosystem

---

## Document Overview

**Focus:** Understanding the rail booking ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Rail Operator Types
- What are the different rail systems? (Domestic, international, passes?)
- Who are the major rail operators?
- What are the rail pass products?
- How do systems differ by region?

### 2. Indian Railways
- How does Indian Railways booking work?
- What are the quotas (Tatkal, Premium Tatkal)?
- How does waitlist work?
- What API access exists?

### 3. International Rail
- What are Eurail and Interrail?
- What about JR Pass (Japan)?
- What are other regional passes?
- How do we book international trains?

### 4. Integration
- What APIs are available?
- How do we access schedules and pricing?
- What are the booking workflows?
- How do we handle seat selection?

---

## Research Areas

### A. Indian Railways

**System Overview:**

| Aspect | Details | Research Needed |
|--------|---------|-----------------|
| **Operator** | Indian Railways (IR) | ? |
| **Size** | 4th largest in world | ? |
| **Daily passengers** | 23+ million | ? |
| **Routes** | 7,000+ stations | ? |
| **Booking system** | IRCTC | ? |

**Booking Classes:**

| Class | Description | Air Conditioning | Research Needed |
|-------|-------------|------------------|-----------------|
| **1A** | First AC AC | Yes | ? |
| **2A** | Second AC AC | Yes | ? |
| **3A** | Third AC AC | Yes | ? |
| **3E** | AC 3 Tier Economy | Yes | ? |
| **CC** | AC Chair Car | Yes | ? |
| **EC** | Executive CC | Yes | ? |
| **SL** | Sleeper | No | ? |
| **2S** | Second Sitting | No | ? |

**Quota Types:**

| Quota | Description | Booking Window | Research Needed |
|-------|-------------|-----------------|-----------------|
| **General** | Regular quota | 120 days before | ? |
| **Tatkal** | Emergency quota | 1 day before | Timing? |
| **Premium Tatkal** | Premium emergency | 1 day before | Dynamic pricing? |
| **Ladies** | Women quota | Within general | Seats available? |
| **Senior Citizen** | Age-based quota | Within general | Discount %? |
| **Foreign Tourist** | Tourist quota | Within general | How to access? |
| **Duty Pass** | Rail employees | Separate | Not for public | ? |

**Waitlist System:**

| Status | Meaning | Confirmation Chance | Research Needed |
|--------|---------|---------------------|-----------------|
| **CNF** | Confirmed | 100% | ? |
| **RAC** | Reservation Against Cumulative | High (seats, not berths) | ? |
| **WL** | Waitlist | Varies by position, quota | How to assess? |
| **REGRET** | No seats available | None | ? |

**Research:**
- How to integrate with IRCTC?
- API availability and costs
- Tatkal booking automation
- Waitlist prediction algorithms

### B. International Rail Passes

**Eurail (for non-Europeans):**

| Aspect | Details | Research Needed |
|--------|---------|-----------------|
| **Eligibility** | Non-European residents | Indians qualify |
| **Coverage** | 33 countries | All countries? |
| **Pass Types** | Global, Select, One Country | ? |
| **Duration** | 3 days to 3 months | Popular options? |
| **Booking** | Online, print at home | API? |
| **Pricing** | Varies by countries, age | Age bands? |
| **Reservations** | Required for some trains | Additional cost? |

**Interrail (for Europeans):**

| Aspect | Details | Research Needed |
|--------|---------|-----------------|
| **Eligibility** | European residents | Indians NOT eligible |
| **Coverage** | 33 countries | ? |
| **Pass Types** | Similar to Eurail | ? |

**Japan Rail (JR) Pass:**

| Aspect | Details | Research Needed |
|--------|---------|-----------------|
| **Eligibility** | Temporary visitor visa | Required for exchange |
| **Coverage** | Most JR trains | Not Nozomi/Mizuho |
| **Pass Types** | 7, 14, 21 days | Pricing? |
| **Classes** | Ordinary, Green (first class) | ? |
| **Booking** | Order voucher, exchange in Japan | Process? |
| **Reservations** | Free for pass holders | Process? |

**Other Regional Passes:**

| Pass | Region | Coverage | Research Needed |
|------|--------|----------|-----------------|
| **BritRail** | UK | Nationwide | ? |
| **Swiss Travel Pass** | Switzerland | All transport | ? |
| **Brenner Pass** | Austria-Italy | Cross-border | ? |
| **Balkan Flexipass** | Balkans | Multiple countries | ? |
| **Korean Rail Pass** | South Korea | Korail trains | ? |
| **USA Rail Pass** | USA | Amtrak | ? |

### C. International Train Booking

**Major International Routes:**

| Route | Operators | Booking | Research Needed |
|-------|------------|---------|-----------------|
| **Eurostar** | London-Paris/Brussels | Direct | ? |
| **Thalys** | Paris-Brussels-Amsterdam | Direct | ? |
| **TGV** | France high-speed | SNCF | ? |
| **ICE** | Germany high-speed | DB | ? |
| **Railjet** | Austria-Germany | ÖBB | ? |
| **SJ** | Sweden high-speed | SJ | ? |
| **Vienna to Prague** | ÖBB, CD | Both | ? |

**Cross-Border Complexity:**

| Challenge | Description | Research Needed |
|-----------|-------------|-----------------|
| **Multiple operators** | Journey spans several | How to price? |
| **Different currencies** | Payment complexity | ? |
| **Language barriers** | Customer support | ? |
| **Timetables** | Time zones, connections | ? |
| **Reservations** | Vary by operator | Required vs optional? |

### D. Rail Booking Platforms

**Aggregators:**

| Platform | Coverage | API? | Notes | Research Needed |
|----------|----------|------|-------|-----------------|
| **Trainline** | Europe | ? | Largest | ? |
| **Omio** | Global | ? | Former GoEuro | ? |
| **Rail Ninja** | Global | ? | Focused | ? |
| **12Go** | Asia | ? | Trains + buses | ? |

**Direct Booking:**

| Operator | Direct Booking | API? | Research Needed |
|----------|----------------|------|-----------------|
| **IRCTC** | Yes | Limited | ? |
| **SNCF** | Yes | Yes | ? |
| **DB** | Yes | Yes | ? |
| **SJ** | Yes | Yes | ? |
| **Amtrak** | Yes | Yes | ? |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface RailProvider {
  id: string;
  name: string;
  type: RailProviderType;
  region: string;

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;

  // Coverage
  stations: RailStation[];
  routes: RailRoute[];

  // Commercial
  commissionRate?: number;
}

type RailProviderType =
  | 'national_rail'
  | 'high_speed_rail'
  | 'regional_rail'
  | 'rail_pass_provider'
  | 'aggregator';

interface RailRoute {
  id: string;
  providerId: string;
  routeNumber: string;

  origin: RailStation;
  destination: RailStation;

  // Schedule
  duration: number; // minutes
  frequency: FrequencyInfo;

  // Classes
  availableClasses: TravelClass[];

  // Pricing
  pricing: RailPricing;

  // Services
  hasWifi: boolean;
  hasFood: boolean;
  isOvernight: boolean;
}

interface RailStation {
  id: string;
  code: string; // Station code
  name: string;
  city: string;
  state?: string;
  country: string;

  // Facilities
  facilities?: StationFacility[];

  // Coordinates
  latitude?: number;
  longitude?: number;
}

type TravelClass =
  | '1A' // First AC
  | '2A' // Second AC
  | '3A' // Third AC
  | '3E' // AC 3 Tier Economy
  | 'CC' // AC Chair Car
  | 'EC' // Executive CC
  | 'SL' // Sleeper
  | '2S'; // Second Sitting

interface RailPricing {
  basePrice: Money;
  classPrices: Map<TravelClass, Money>;

  // Indian Railways specific
  quota?: QuotaType;
  waitlist?: boolean;

  // Dynamic pricing
  dynamicPricing: boolean;
  priceVariations?: PriceVariation[];
}

type QuotaType =
  | 'general'
  | 'tatkal'
  | 'premium_tatkal'
  | 'ladies'
  | 'senior_citizen'
  | 'foreign_tourist';

interface RailPass {
  id: string;
  name: string;
  providerId: string;
  type: RailPassType;

  // Coverage
  countries: string[];
  validity: number; // days

  // Usage
  travelDays: number; // Within validity
  class: TravelClass;

  // Pricing
  price: Money;
  agePrices?: Map<string, Money>; // Adult, child, senior

  // Reservations
  reservationRequired: boolean;
  reservationProcess: string;
}

type RailPassType =
  | 'global' // All countries
  | 'select' // Choose countries
  | 'one_country' // Single country
  | 'regional'; // Specific region
```

---

## Integration Approaches

### 1. Direct API Integration
**Best for:** Operators with open APIs

**Pros:**
- Real-time availability
- Direct pricing
- Full functionality

**Cons:**
- Each operator different
- Maintenance overhead
- Some have no APIs

### 2. Aggregator Integration
**Best for:** Broad coverage

**Pros:**
- Single integration
- Multiple operators
- Standardized interface

**Cons:**
- Additional cost
- Dependent on aggregator
- May have limited features

### 3. Manual/Assisted Booking
**Best for:** Complex routes, no API

**Pros:**
- Can work with anyone
- Human expertise for complex trips

**Cons:**
- Labor intensive
- Not scalable
- Slow

---

## Commercial Considerations

### Commission Structures

| Market | Typical Commission | Notes |
|--------|-------------------|-------|
| **Indian Railways** | Very low/none | Fixed service charge? |
| **European rail** | 0-5% | Low margin |
| **Rail passes** | 5-10% | Better margin |
| **Aggregator** | Varies | Revenue share? |

**Research:**
- What are actual commission rates?
- Are there volume incentives?
- What about service fees?

### Payment Terms

| Operator | Payment Timing | Research Needed |
|----------|----------------|-----------------|
| **IRCTC** | Immediate | ? |
| **European rail** | Immediate | ? |
| **Rail passes** | Immediate | ? |

---

## Open Problems

### 1. IRCTC API Access
**Challenge:** IRCTC API is limited/restricted

**Options:**
- Official API partnership
- Third-party API providers
- Screen scraping (risky)
- Assisted booking

### 2. Waitlist Uncertainty
**Challenge:** Customers book on waitlist, may not confirm

**Options:**
- Show probability
- Offer alternatives
- Automatic cancellation if not confirmed
- Clear communication

### 3. Tatkal Automation
**Challenge:** High demand, limited seats, fast booking required

**Options:**
- Automated booking system
- Pre-fill forms
- Multiple attempts
- Agent-assisted

### 4. Cross-Border Complexity
**Challenge:** Multiple operators, currencies, languages

**Options:**
- Aggregator integration
- Segment by segment booking
- Expert routing
- Clear disclaimers

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **IRCTC** | Direct | ? |
| **MakeMyTrip** | Indian rail | ? |
| **Yatra** | Indian rail | ? |
| **Trainline** | European rail | ? |
| **Omio** | Global rail | ? |

---

## Experiments to Run

1. **API availability test:** Which rail systems have APIs?
2. **Waitlist accuracy test:** How predictive is waitlist confirmation?
3. **Tatkal success test:** Can we book Tatkal successfully?
4. **Cross-border booking test:** How smooth is multi-operator booking?

---

## References

- [Flight Integration](./FLIGHT_INTEGRATION_MASTER_INDEX.md) — Similar scheduled transport
- [Ground Transportation](./GROUND_TRANSPORTATION_MASTER_INDEX.md) — Overlapping category

---

## Next Steps

1. Audit rail operator APIs
2. Analyze Indian Railways booking patterns
3. Design rail search interface
4. Build booking integration
5. Implement waitlist management

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
