# Cruise Booking 01: Provider Landscape

> Cruise lines, itineraries, ships, and the cruise ecosystem

---

## Document Overview

**Focus:** Understanding the cruise booking ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Cruise Types
- What are the different cruise types? (Ocean, river, expedition?)
- Who are the major cruise lines?
- What are the popular regions for Indian travelers?
- What are the departure ports?

### 2. Cruise Lines
- Which cruise lines serve the Indian market?
- What are the different service levels? (Budget, premium, luxury?)
- Who offers expedition cruises?
- What about river cruises?

### 3. Ships & Itineraries
- What are the popular cruise itineraries?
- What are ship categories?
- How do ships differ by size and amenities?
- What are the popular departure ports?

### 4. Integration
- Do cruise lines offer booking APIs?
- How do we access inventory and pricing?
- What are the booking workflows?
- How do we handle cabin selection?

---

## Research Areas

### A. Cruise Lines Serving Indian Market

**Major Ocean Cruise Lines:**

| Cruise Line | Region Focus | Class | API? | Notes | Research Needed |
|-------------|--------------|-------|------|-------|-----------------|
| **Carnival** | Caribbean, Europe | Mass | ? | Largest | ? |
| **Royal Caribbean** | Global | Mass | ? | Popular with families | ? |
| **Norwegian** | Caribbean, Europe | Mass | ? | Freestyle | ? |
| **MSC** | Europe, Asia | Mass | ? | Growing in Asia | ? |
| **Costa** | Europe, Asia | Mass | ? | Asian presence | ? |
| **Princess** | Global | Premium | ? | Alaska specialist | ? |
| **Celebrity** | Global | Premium | ? | Premium experience | ? |
| **Holland America** | Global | Premium | ? | Traditional | ? |

**Luxury Cruise Lines:**

| Cruise Line | Region Focus | Class | API? | Notes | Research Needed |
|-------------|--------------|-------|------|-------|-----------------|
| **Seabourn** | Global | Luxury | ? | Ultra-luxury | ? |
| **Silversea** | Global | Luxury | ? | All-inclusive | ? |
| **Regent Seven Seas** | Global | Luxury | ? | All-inclusive | ? |
| **Crystal** | Global | Luxury | ? | Resuming operations | ? |
| **Oceania** | Global | Upper premium | ? | Destination focus | ? |

**Expedition Cruise Lines:**

| Cruise Line | Region Focus | Class | API? | Notes | Research Needed |
|-------------|--------------|-------|------|-------|-----------------|
| **Quark** | Polar | Expedition | ? | Antarctica specialist | ? |
| **Hurtigruten** | Norway, Polar | Expedition | ? | Coastal voyages | ? |
| **Lindblad** | Galapagos, Polar | Expedition | ? | NatGeo partnership | ? |
| **Ponant** | Global | Luxury expedition | ? | French | ? |
| **Aurora** | Polar | Expedition | ? | Australian | ? |

**River Cruise Lines:**

| Cruise Line | Region Focus | Class | API? | Notes | Research Needed |
|-------------|--------------|-------|------|-------|-----------------|
| **Viking** | Europe, Asia | Premium | ? | Largest river line | ? |
| **AmaWaterways** | Europe, Asia | Premium | ? | ? | ? |
| **Avalon** | Europe | Premium | ? | ? | ? |
| **Uniworld** | Europe | Luxury | ? | Boutique ships | ? |
| **Crystal River** | Europe | Luxury | ? | Now part of Viking? | ? |

**Research:**
- API availability for each line
- Commission structures
- Integration complexity
- Which accept Indian customers

### B. Popular Itineraries for Indian Travelers

**Regional Preferences:**

| Region | Popularity | Duration | Season | Research Needed |
|--------|------------|----------|--------|-----------------|
| **Singapore-Malaysia-Thailand** | High | 3-7 nights | Year-round | ? |
| **Mediterranean** | High | 7-14 nights | Apr-Oct | ? |
| **Caribbean** | Medium | 7 nights | Nov-Apr | ? |
| **Alaska** | Medium | 7 nights | May-Sep | ? |
| **Northern Europe** | Medium | 7-14 nights | May-Sep | ? |
| **Dubai-Abu Dhabi** | High | 3-7 nights | Nov-Mar | ? |
| **Antarctica** | Low (niche) | 10-21 nights | Nov-Mar | ? |
| **European Rivers** | Medium | 7-14 nights | Mar-Nov | ? |
| **Yangtze** | Medium | 3-7 nights | Year-round | ? |
| **Mekong** | Medium | 7 nights | Year-round | ? |

**Indian Ocean Cruises:**

| Route | Duration | Cruise Lines | Research Needed |
|-------|----------|--------------|-----------------|
| **Mumbai-Goa** | 2-5 nights | Cordelia, others | ? |
| **India-Sri Lanka** | 7 nights | Various | ? |
| **India-Maldives** | 7 nights | Various | ? |
| **Round-India** | 7-14 nights | Luxury lines | ? |

**Research:**
- Which routes are most popular?
- What are typical prices?
- Which cruise lines serve these routes?

### C. Ship Categories

**By Size:**

| Size | Passengers | Pros | Cons | Research Needed |
|------|------------|------|------|-----------------|
| **Small** | < 500 | Intimate, unique ports | Fewer amenities | ? |
| **Medium** | 500-2,000 | Balanced | Less crowded | ? |
| **Large** | 2,000-4,000 | Many amenities | Crowded | ? |
| **Mega** | 4,000-6,000+ | Most amenities | Very crowded | ? |

**By Experience:**

| Type | Description | Examples | Research Needed |
|------|-------------|----------|-----------------|
| **Mass Market** | Affordable, family-friendly | Carnival, Royal Caribbean | ? |
| **Premium** | Better food, service | Princess, Celebrity | ? |
| **Luxury** | All-inclusive, high service | Seabourn, Silversea | ? |
| **Expedition** | Adventure, education-focused | Quark, Lindblad | ? |
| **River** | Cultural, destination-focused | Viking, AmaWaterways | ? |

### D. Cabin Categories

**Standard Cabin Types:**

| Category | Description | Price Level | Amenities | Research Needed |
|----------|-------------|-------------|-----------|-----------------|
| **Interior** | No windows | Lowest | Basic | ? |
| **Ocean View** | Window/porthole | Low-Mid | Light | ? |
| **Balcony** | Private balcony | Mid-High | Outdoor space | ? |
| **Suite** | Separate living area | High | More space, perks | ? |

**Specialty Cabins:**

| Type | Description | Premium | Research Needed |
|------|-------------|---------|-----------------|
| **Family Suite** | Multiple rooms | High | ? |
| **Spa Suite** | Near spa, amenities | High | ? |
| **Aft/Front Suite** | Large balconies | Very High | ? |
| **Haven/Suites** | Private areas | Ultra | ? |
| **Single Cabins** | Solo travelers | Varied | ? |

**Pricing Factors:**

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Deck level** | Higher = more expensive | How much? |
| **Location** | Midship preferred | Premium? |
| **View type** | Obstructed vs. clear | Difference? |
| **Size** | Square footage | Per sq ft price? |
| **Accessibility** | Accessible cabins | Availability? |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface CruiseLine {
  id: string;
  name: string;
  type: CruiseLineType;
  class: ServiceClass;

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;

  // Fleet
  ships: CruiseShip[];

  // Commercial
  commissionRate?: number;
}

type CruiseLineType =
  | 'ocean'
  | 'river'
  | 'expedition'
  | 'luxury';

type ServiceClass =
  | 'mass_market'
  | 'premium'
  | 'luxury'
  | 'ultra_luxury';

interface CruiseShip {
  id: string;
  name: string;
  cruiseLineId: string;

  // Details
  capacity: number;
  crew: number;
  builtYear: number;
  lastRefurbished?: number;

  // Features
  amenities: ShipAmenity[];
  dining: DiningOption[];
  entertainment: EntertainmentOption[];
  cabins: CabinCategory[];

  // Itineraries
  itineraries: CruiseItinerary[];
}

interface CruiseItinerary {
  id: string;
  shipId: string;
  name: string;
  region: string;

  // Schedule
  duration: number; // nights
  departurePort: Port;
  arrivalPort?: Port;

  // Route
  portsOfCall: PortCall[];
  daysAtSea: number;

  // Schedule
  departures: CruiseDeparture[];

  // Pricing
  pricing: CruisePricing;
}

interface PortCall {
  port: Port;
  arrivalTime?: string;
  departureTime?: string;
  overnight?: boolean;
  tenderRequired?: boolean;
}

interface Port {
  id: string;
  name: string;
  country: string;
  region: string;

  // Logistics
  airportCode?: string;
  distanceFromAirport?: number;
  portFacilities?: string[];
}

interface CruiseDeparture {
  date: Date;
  status: DepartureStatus;
  availability: AvailabilityInfo;
  pricing: DeparturePricing;
}

type DepartureStatus =
  | 'guaranteed'
  | 'on_request'
  | 'waitlist_only'
  | 'sold_out';

interface CabinCategory {
  id: string;
  shipId: string;
  name: string;
  type: CabinType;

  // Details
  maxOccupancy: number;
  squareFeet?: number;
  hasView: boolean;
  hasBalcony: boolean;
  isAccessible: boolean;

  // Pricing
  basePriceMultiplier: number; // relative to base
  amenities: string[];
}

type CabinType =
  | 'interior'
  | 'ocean_view'
  | 'balcony'
  | 'suite'
  | 'family_suite'
  | 'spa_suite'
  | 'single';
```

---

## Integration Approaches

### 1. Direct API Integration
**Best for:** Large cruise lines with APIs

**Pros:**
- Real-time availability
- Direct pricing
- Full inventory access

**Cons:**
- Each line different
- Complex integration
- May require partnership

### 2. Aggregator Integration
**Best for:** Broad coverage

**Aggregators:**
| Platform | Coverage | API? | Notes |
|----------|----------|------|-------|
| **CruiseOnly** | Multiple lines | ? | ? |
| **VacationsToGo** | Multiple lines | ? | ? |
| **Expedia Cruises** | Multiple lines | ? | ? |

**Pros:**
- Single integration
- Multiple lines
- Standardized interface

**Cons:**
- Additional cost
- May not have all lines
- Limited functionality

### 3. Manual/White Label
**Best for:** Small operators, custom quotes

**Pros:**
- Can work with anyone
- Full control

**Cons:**
- Manual work
- No real-time availability
- Slow to scale

---

## Commercial Considerations

### Commission Structures

| Model | Typical Commission | Notes |
|-------|-------------------|-------|
| **Standard Commission** | 10-16% | Most common |
| **Net Rates** | Markup on net | Higher margin |
| **Tiered** | Volume-based | Better for high volume |
| **Consortium** | Higher rates | For agency members |

**Research:**
- What are actual commission rates by line?
- Who offers net rates?
- What are the volume thresholds?

### Payment Terms

| Term | Description | Research Needed |
|------|-------------|-----------------|
| **Deposit on Booking** | % at booking | Standard %? |
| **Final Payment** | 75-120 days before | Varies by line? |
| **Full Payment** | < 75 days | Last-minute? |

---

## Open Problems

### 1. Dynamic Pricing
**Challenge:** Cruise prices change constantly, like airlines

**Options:**
- Real-time API sync
- Cache with TTL
- Show "from" pricing
- Price on request

### 2. Cabin Selection Complexity
**Challenge:** Many cabin types, locations, prices

**Options:**
- Simplified categories
- Visual deck plans
- Recommendation engine
- Agent-assisted selection

### 3. Synchronous Booking
**Challenge:** Cabins sell while viewing

**Options:**
- Hold cabin temporarily
- Fast checkout
- Show availability status
- Accept some failed bookings

### 4. Shore Excursions
**Challenge:** Pre-book vs. on-board booking

**Options:**
- Pre-booking available
- Book on cruise
- Mix of both
- Third-party excursions

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **Cruise Competitor** | ? | ? |
| **Travel Agents** | ? | ? |

---

## Experiments to Run

1. **API audit:** Which cruise lines have bookable APIs?
2. **Cabin selection study:** How do customers choose cabins?
3. **Pricing analysis:** How do prices vary?
4. **Excursion booking:** Pre-book vs. on-board preference?

---

## References

- [Package Tours - Providers](./PACKAGE_TOURS_01_PROVIDERS.md) — Similar provider landscape
- [Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md) — Cabin as accommodation
- [Activities](./ACTIVITIES_MASTER_INDEX.md) — Shore excursions

---

## Next Steps

1. Audit cruise line APIs
2. Analyze popular itineraries for Indians
3. Design cabin selection UX
4. Build booking integration
5. Implement shore excursion booking

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
