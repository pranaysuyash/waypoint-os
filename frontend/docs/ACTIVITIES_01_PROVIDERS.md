# Activities & Experiences 01: Provider Landscape

> Tours, activities, attractions, and experience providers

---

## Document Overview

**Focus:** Understanding the activities and experiences ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Provider Landscape
- Who are the major global aggregators? (Viator, GetYourGuide, Klook, etc.)
- Who are the regional players? (India-specific, SE Asia, ME)
- What about direct-to-operator bookings?
- Which providers offer APIs vs. require manual booking?
- What are the commission structures?

### 2. Activity Types
- What categories of activities exist?
- How do we classify them? (Tours, tickets, experiences, transportation?)
- What are the operational differences between types?
- Which types are most booked?

### 3. Inventory Models
- How do providers handle availability?
- What are the booking lead times?
- How do time-slots work?
- What about capacity management?
- How do we handle "sold out"?

### 4. Regional Differences
- How does the activity landscape differ by region?
- Are there regional champions in key markets?
- What cultural differences exist?
- How do we handle language barriers?

---

## Research Areas

### A. Global Aggregators

| Provider | Coverage | API | Notes |
|----------|----------|-----|-------|
| **Viator** (TripAdvisor) | Global | ? | ? |
| **GetYourGuide** | Global | ? | ? |
| **Klook** | Asia-focused | ? | ? |
| **Viator** | Global | ? | ? |
| **Expedia Activities** | Global | ? | ? |
| **Booking.com Experiences** | Global | ? | ? |
| **Airbnb Experiences** | Select cities | ? | ? |

**Research Needed:**
- API availability and quality
- Commission rates
- Integration complexity
- Coverage in key destinations

### B. Regional Players

**India:**
| Provider | Focus | API | Notes |
|----------|-------|-----|-------|
| ? | ? | ? | ? |

**SE Asia:**
| Provider | Focus | API | Notes |
|----------|-------|-----|-------|
| ? | ? | ? | ? |

**Middle East:**
| Provider | Focus | API | Notes |
|----------|-------|-----|-------|
| ? | ? | ? | ? |

**Research:** Who are the regional champions?

### C. Activity Categories

**Proposed Taxonomy:**

| Category | Sub-categories | Characteristics |
|----------|----------------|-----------------|
| **Sightseeing Tours** | City tours, day trips, multi-day | Scheduled, guide-led |
| **Attraction Tickets** | Museums, monuments, parks | Skip-the-line, date-specific |
| **Food & Drink** | Cooking classes, food tours, winery | Time-specific, capacity-limited |
| **Outdoor Activities** | Hiking, water sports, adventure | Weather-dependent, equipment |
| **Cultural Experiences** | Workshops, classes, local life | Host-dependent |
| **Transportation** | Scenic rides, transfers | Schedule-based |
| **Nightlife** | Shows, cruises, pub crawls | Age-restricted |
| **Wellness** | Spas, yoga, retreats | Booking flexibility |

**Research:**
- Is this taxonomy comprehensive?
- How do competitors categorize?
- Which categories drive most revenue?

### D. Direct Operators

**Considerations:**

| Aspect | Question |
|--------|----------|
| **API availability** | Do individual operators offer APIs? |
| **Aggregator dependency** | Must we work through aggregators? |
| **Direct relationships** | Value in building direct operator relationships? |
| **Long-tail** | How to handle niche activities? |

**Research:**
- Can we work with operators directly?
- What is the operational overhead?
- What are the economics?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface ActivityProvider {
  id: string;
  name: string;
  type: 'aggregator' | 'operator' | 'operator_network';

  // Coverage
  regions: string[];
  cities: string[];
  categories: ActivityCategory[];

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;
  apiDocumentation?: string;

  // Commercial
  commissionRate?: number;
  paymentTerms?: PaymentTerms;
  currency: string[];

  // Capabilities
  realTimeAvailability: boolean;
  instantConfirmation: boolean;
  cancellationPolicy: CancellationPolicy;
}

interface Activity {
  id: string;
  providerId: string;
  title: string;
  description: string;

  // Classification
  category: ActivityCategory;
  subCategory?: string;
  tags: string[];

  // Location
  location: {
    city: string;
    country: string;
    coordinates?: Coordinates;
    meetingPoint?: string;
  };

  // Logistics
  duration: Duration;
    schedule: ScheduleInfo;
  capacity: CapacityInfo;
  requirements: Requirements;

  // Pricing
  pricing: ActivityPricing;

  // Media
  images: string[];
  videos?: string[];

  // Ratings
  rating?: number;
  reviewCount?: number;
}

interface CapacityInfo {
  minimumParticipants?: number;
  maximumParticipants: number;
  ageRestrictions?: AgeRestriction;
}
```

---

## Integration Approaches

### 1. Aggregator API
**Best for:** Broad coverage, standard interface

**Pros:**
- Single integration for many activities
- Standardized data model
- Established reliability

**Cons:**
- Additional margin
- Less control
- Dependent on aggregator's inventory

### 2. Direct Operator API
**Best for:** Large operators, premium experiences

**Pros:**
- Better margin
- Direct relationship
- Real-time inventory

**Cons:**
- Many integrations
- Non-standard interfaces
- Maintenance overhead

### 3. Manual/White Label
**Best for:** Niche operators, custom experiences

**Pros:**
- Can work with anyone
- Flexibility

**Cons:**
- Operational overhead
- Slower turnaround

**Research:**
- Which approach for which segment?
- Can we mix approaches?

---

## Operational Considerations

### A. Booking Lead Times

| Activity Type | Typical Lead Time | Same-day? |
|---------------|-------------------|-----------|
| Attraction tickets | Minutes | Yes |
| Scheduled tours | Days | Sometimes |
| Custom experiences | Weeks | No |
| Multi-day trips | Weeks | No |

### B. Cancellation Policies

| Activity Type | Free Cancellation | Typical Notice |
|---------------|-------------------|----------------|
| Attraction tickets | Often flexible | 24-48 hours |
| Small group tours | Varies | 24-72 hours |
| Multi-day trips | Strict | 7+ days |
| Custom experiences | Very strict | 14+ days |

### C. Voucher Delivery

| Delivery Method | Used For | Timing |
|-----------------|----------|--------|
| Mobile ticket | Attraction tickets | Immediate |
| PDF voucher | Tours, activities | After booking |
| Email confirmation | All | Immediate |
| Physical pickup | Some tours | On arrival |

---

## Open Problems

### 1. Content Quality
**Challenge:** Activity descriptions vary widely in quality and completeness

**Options:**
- Accept provider content as-is
- Curate and enhance content
- Standardize content format

**Research:** How important is content quality for conversion?

### 2. Image Rights
**Challenge:** Can we use provider images? What are the rights?

**Questions:**
- Do we get image rights via API?
- Can we hotlink images?
- Do we need to host ourselves?

### 3. Price Accuracy
**Challenge:** Prices may vary by date, season, group size

**Questions:**
- How do we get accurate pricing?
- Are prices guaranteed?
- How do we handle price changes?

### 4. Review Authenticity
**Challenge:** Are reviews from real customers?

**Questions:**
- Do we trust provider reviews?
- Can we collect our own?
- How do we verify authenticity?

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **Viator** | ? | ? |
| **GetYourGuide** | ? | ? |
| **Klook** | ? | ? |
| **Airbnb Experiences** | ? | ? |
| **Local India agents** | ? | ? |

---

## Experiments to Run

1. **API availability test:** Which aggregators offer bookable APIs?
2. **Content quality audit:** Compare content quality across providers
3. **Commission analysis:** What are the commission structures?
4. **Coverage analysis:** Which destinations have good coverage?

---

## References

- [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Component assembly
- [Ground Transportation](./GROUND_TRANSPORTATION_MASTER_INDEX.md) — Similar provider patterns

---

## Next Steps

1. Audit aggregator API availability
2. Test key integrations
3. Map activity categories
4. Analyze commission structures
5. Research regional players

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
