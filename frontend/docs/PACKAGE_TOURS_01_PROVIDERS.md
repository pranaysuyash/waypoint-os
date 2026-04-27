# Package Tours 01: Provider Landscape

> Tour operators, package types, and the vacation packages ecosystem

---

## Document Overview

**Focus:** Understanding the package tour ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Provider Types
- What are the different tour operator types? (Outbound, inbound, domestic?)
- Who are the major players serving Indian travelers?
- What are the aggregator platforms?
- How do operators differ by region/service level?

### 2. Package Types
- What are the different package formats?
- What's the difference between fixed departure and flexible?
- What are group tours vs. independent packages?
- What about special interest packages?

### 3. Integration
- Do tour operators offer booking APIs?
- How do we access inventory and pricing?
- What are the booking workflows?
- How do we handle confirmations?

### 4. Commercial
- What are the commission structures?
- What are the payment terms?
- What about net rates vs. commission?
- How do margins compare to a la carte?

---

## Research Areas

### A. Indian Tour Operators

**Major Outbound Operators:**

| Operator | Destinations | API? | Notes | Research Needed |
|----------|-------------|------|-------|-----------------|
| **Cox & Kings** | Global | ? | Legacy, large | ? |
| **SOTC** | Global | ? | Part of Fairfax | ? |
| **Thomas Cook India** | Global | ? | Now part of Thomas Cook India | ? |
| **MakeMyTrip** | Popular | ? | OTA, packages section | ? |
| **Yatra** | Popular | ? | OTA, packages section | ? |
| **TravelTriangle** | Custom | ? | Marketplace model | ? |
| **PickYourTrail** | Custom | ? | Honeymoon focus | ? |

**Niche/Specialist Operators:**

| Operator | Focus | API? | Notes |
|----------|-------|------|-------|
| **Adventure Nation** | Adventure | ? | ? |
| **India Someday** | Custom | ? | Independent |
| **Wandering Jane** | Women-only | ? | Niche |
| **Blue Bulb** | Offbeat | ? | Boutique |

**Research:**
- API availability for each
- Package types offered
- Commission structures
- Integration complexity

### B. International Package Providers

**Global Operators:**

| Operator | Destinations | API? | Notes |
|----------|-------------|------|-------|
| **TUI** | Europe | ? | Largest |
| **Expedia Local Expert** | Global | ? | ? |
| **Viator Packages** | Global | ? | Now TripAdvisor |
| **Klook Packages** | Asia | ? | Growing |
| **GetYourGuide** | Europe | ? | Mostly activities |

**Research:**
- Which serve Indian market?
- API availability
- Currency/pricing considerations

### C. Package Types

**By Departure Model:**

| Type | Description | Pros | Cons | Research Needed |
|------|-------------|------|------|-----------------|
| **Fixed Departure** | Specific dates, guaranteed | Predictable, easier | Less flexibility | ? |
| **Flexible Departure** | Date range, choose dates | Customer choice | Complex pricing | ? |
| **Private/Custom** | Build your own | Fully customizable | Expensive, complex | ? |
| **Group Join** | Join existing group | Social, cheaper | Fixed dates | ? |

**By Composition:**

| Type | Components | Typical For | Research Needed |
|------|------------|-------------|-----------------|
| **Air + Land** | Flights + hotels + transfers | Standard vacation | ? |
| **Land Only** | Hotels + tours + transfers | Those with flights | ? |
| **Guided Tours** | Everything + guide | First-time travelers | ? |
| **Semi-Guided** | Key elements guided, some free time | Independent travelers | ? |

**By Interest:**

| Category | Examples | Research Needed |
|----------|----------|-----------------|
| **Honeymoon** | Romantic destinations | ? |
| **Family** | Kid-friendly destinations | ? |
| **Pilgrimage** | Religious sites | ? |
| **Adventure** | Trekking, safaris, extreme sports | ? |
| **Wildlife** | Safari, nature tours | ? |
| **Cultural** | Heritage sites, museums | ? |
| **Beach** | Island destinations | ? |
| **Luxury** | Premium properties, experiences | ? |

### D. Aggregator Platforms

**Package Aggregators:**

| Platform | Model | API? | Notes |
|----------|-------|------|-------|
| **TourRadar** | Multi-operator | ? | 50,000+ tours |
| **TravelComponent** | B2B API | ? | ? |
| **GTA** | B2B | ? | Traditional |
| **HotelBeds** | B2B | ? | Expanding to packages |

**Research:**
- Which offer APIs?
- What are the integration costs?
- How do we access their inventory?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface PackageTourProvider {
  id: string;
  name: string;
  type: ProviderType;

  // Coverage
  destinations: string[];
  packageTypes: PackageType[];

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;

  // Commercial
  commissionRate?: number;
  paymentTerms: PaymentTerms;
}

type ProviderType =
  | 'tour_operator'
  | 'ota'
  | 'marketplace'
  | 'aggregator'
  | 'niche_specialist';

interface PackageTour {
  id: string;
  providerId: string;
  name: string;
  type: PackageType;

  // Details
  destination: string;
  duration: number; // days
  difficulty?: 'easy' | 'moderate' | 'challenging';

  // Departure
  departureModel: DepartureModel;
  departureDates?: Date[];
  dateRange?: DateRange;

  // Components
  includes: PackageComponent[];
  excludes?: string[];

  // Pricing
  pricing: PackagePricing;

  // Availability
  availability: AvailabilityInfo;
}

type PackageType =
  | 'fixed_departure'
  | 'flexible_departure'
  | 'private_custom'
  | 'group_join';

type DepartureModel =
  | 'guaranteed' // Runs regardless of bookings
  | 'on_request' // Needs minimum to confirm
  | 'private'; // Custom dates

interface PackageComponent {
  type: ComponentType;
  included: boolean;
  details: string;
}

type ComponentType =
  | 'flights'
  | 'accommodation'
  | 'transfers'
  | 'meals'
  | 'guide'
  | 'activities'
  | 'visas'
  | 'insurance';

interface PackagePricing {
  // Pricing can be complex
  basePrice: Money;
  perPerson: boolean;

  // Price components
  landPrice?: Money;
  airPrice?: Money;

  // Variations
  singleSupplement?: Money;
  childPrice?: Money;
  tripleShare?: Money;

  // What's included
  includes: {
    meals: MealPlan;
    activities: string[];
    transport: string[];
  };
}

type MealPlan =
  | 'no_meals'
  | 'breakfast_only'
  | 'half_board' // breakfast + dinner
  | 'full_board' // all meals
  | 'all_inclusive';
```

---

## Integration Approaches

### 1. Direct API Integration
**Best for:** Large operators with APIs

**Pros:**
- Real-time availability
- Direct pricing
- Full product details

**Cons:**
- Each operator different
- Maintenance overhead
- May require partnership

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

### 3. Manual/White Label
**Best for:** Niche operators, custom packages

**Pros:**
- Can work with anyone
- Full control over experience

**Cons:**
- Manual work
- No real-time availability
- Slow to scale

---

## Commercial Considerations

### Commission Structures

| Model | Typical Commission | Notes |
|-------|-------------------|-------|
| **Standard Commission** | 10-15% | Most common |
| **Net Rates** | Markup on net | Higher margin possible |
| **Tiered** | Volume-based | Better for high volume |
| **Exclusive** | Negotiated | Key partnerships |

**Research:**
- What are actual commission rates?
- Who offers net rates?
- What are the volume thresholds?

### Payment Terms

| Term | Description | Research Needed |
|------|-------------|-----------------|
| **Deposit on Booking** | % at booking, balance before travel | Standard %? |
| **Full Payment** | 100% at booking | When required? |
| **Installment Plans** | Pay over time | Who offers? |
| **Credit Terms** | Pay after travel | For agents only? |

---

## Open Problems

### 1. Availability Synchronization
**Challenge:** Package availability changes frequently

**Options:**
- Real-time API sync
- Periodic polling
- Manual updates
- Customer inquiry for availability

**Research:** What do operators support?

### 2. Dynamic Pricing
**Challenge:** Package prices change based on demand, season, flights

**Questions:**
- How do we handle price updates?
- Do we show live prices?
- How long are quotes valid?

### 3. Minimum Group Size
**Challenge:** Some packages need minimum bookings to run

**Questions:**
- How do we show "guaranteed" vs "on request"?
- What if a trip gets cancelled?
- How do we handle waitlists?

### 4. Custom vs. Fixed
**Challenge:** Customers want custom but operators sell fixed

**Options:**
- Sell fixed as-is
- Offer customization for fee
- Build custom from components

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **MakeMyTrip** | ? | ? |
| **Yatra** | ? | ? |
| **TravelTriangle** | ? | Marketplace model? |
| **PickYourTrail** | ? | Custom packages? |

---

## Experiments to Run

1. **API audit:** Which operators have bookable APIs?
2. **Package analysis:** What are the best-selling packages?
3. **Customer survey:** What package types do customers want?
4. **Pricing study:** How do package prices compare to a la carte?

---

## References

- [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Multi-component planning
- [Flight Integration](./FLIGHT_INTEGRATION_MASTER_INDEX.md) — Air components
- [Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md) — Hotel components
- [Activities](./ACTIVITIES_MASTER_INDEX.md) — Tour components

---

## Next Steps

1. Audit tour operator APIs
2. Analyze package types by destination
3. Design package search flow
4. Build booking integration
5. Implement availability checking

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
