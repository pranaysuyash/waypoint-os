# Activities & Experiences 02: Search & Availability

> Finding activities, checking availability, and time slots

---

## Document Overview

**Focus:** How customers discover and book activities
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Search Input
- What information do we need from customers?
- How do they specify location? (City? Attraction? Coordinates?)
- How do they specify dates/times?
- How do they filter by category/interest?
- What about group size and demographics?

### 2. Availability Checking
- How do we check real-time availability?
- What about time slots vs. open-dated tickets?
- How do we handle limited capacity?
- What about waitlists?
- How do we show "few places left"?

### 3. Pricing Display
- How are prices presented? (Per person? Per group?)
- What about discounts? (Children, seniors, groups?)
- How do we handle currency conversion?
- What about hidden fees? (Service fees, taxes)

### 4. Search Results
- How do we rank activities?
- What information must be shown?
- How do we handle filters and sorting?
- What about "recommended" or "popular"?

---

## Research Areas

### A. Search Parameters

**Required vs. Optional:**

| Parameter | Required? | Notes |
|-----------|-----------|-------|
| Location | Required | City or attraction |
| Date | Required | Specific date or date range |
| Participants | Optional | Affects pricing/availability |
| Category | Optional | Tours, tickets, food, etc. |
| Time preference | Optional | Morning, afternoon, evening |
| Budget | Optional | Filter by price |
| Duration | Optional | Quick vs. full-day |

**Research:**
- What are the most common search patterns?
- How do we handle "flexible date" searches?
- Can we search without a date?

### B. Availability Models

**Model Types:**

| Model | Examples | Availability Check |
|-------|----------|-------------------|
| **Open-dated** | Attraction tickets | Valid any date within period |
| **Time-slot** | Guided tours | Specific start times |
| **Scheduled** | Day trips, cruises | Fixed schedule |
| **On-demand** | Private tours | Request, confirmation |
| **Capacity-limited** | Small groups | Limited spots per slot |

**Research:**
- How do we display each type differently?
- What about "sold out" vs. "unavailable"?
- How do we handle waitlists?

### C. Pricing Complexity

**Pricing Variations:**

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Age-based** | Adult, child, senior, infant | How are ages defined? |
| **Group size** | Per person vs. flat rate | What are breakpoints? |
| **Seasonality** | High/low season pricing | How do we get seasonal rates? |
| **Dynamic** | Demand-based pricing | How predictable? |
| **Add-ons** | Photos, transfers, meals | Optional or included? |

### D. Time Slot Management

**Slot Information Needed:**

| Field | Description |
|-------|-------------|
| Start time | When the activity begins |
| Duration | How long it lasts |
| Capacity | Maximum participants |
| Available spots | Remaining places |
| Minimum participants | If below this, may cancel |
| Meeting point | Where to meet |

**Research:**
- How do we present multiple time slots?
- What about activities with multiple start times per day?
- How do we handle time zones?

---

## Search Request Model

```typescript
// Research-level model - not final

interface ActivitySearchRequest {
  // Location
  location: LocationSearch;
  radius?: number;  // km, for "near me"

  // Time
  date: Date | DateRange;
  timePreference?: 'morning' | 'afternoon' | 'evening' | 'any';
  flexibility?: number;  // days +/- acceptable

  // Participants
  participants: ParticipantSearch;

  // Preferences
  categories?: ActivityCategory[];
  duration?: DurationRange;
  budget?: PriceRange;
  language?: string[];

  // Constraints
    excludeSoldOut?: boolean;
    instantConfirmationOnly?: boolean;
    freeCancellation?: boolean;
  }
}

interface ParticipantSearch {
  adults: number;
  children?: number;
  childrenAges?: number[];  // Affects pricing
  seniors?: number;
}
```

---

## Search Response Model

```typescript
interface ActivitySearchResponse {
  searchId: string;
  totalResults: number;
  activities: ActivitySearchResult[];
  filters: ActiveFilters;
  pagination?: PaginationInfo;
}

interface ActivitySearchResult {
  // Basic info
  id: string;
  title: string;
  category: ActivityCategory;
  provider: string;

  // Media
  image: string;
  rating?: number;
  reviewCount?: number;

  // Key details
  duration: Duration;
  availableSlots?: TimeSlot[];

  // Pricing
  pricing: {
    from: Money;  // "Starting from"
    perPerson: boolean;
    currency: string;
  };

  // Availability
  availability: 'available' | 'limited' | 'sold_out';
  nextAvailable?: Date;

  // Badges
  badges?: Badge[];  // "Bestseller", "Free cancellation", etc.

  // Logistics
  cancellationPolicy: CancellationSummary;
  instantConfirmation: boolean;
}
```

---

## Ranking & Personalization

**Ranking Factors:**

| Factor | Weight | Notes |
|--------|--------|-------|
| **Relevance** | High | Match to search criteria |
| **Popularity** | Medium | Sales, reviews |
| **Rating** | High | Customer reviews |
| **Price** | Medium | Value for money |
| **Availability** | Low | Bias toward available |
| **Commission** | Internal | Business consideration |

**Personalization:**
- Previous bookings
- Search history
- Demographics
- Travel context

**Research:**
- Can we personalize effectively?
- What data do we need?
- What are privacy considerations?

---

## Filters & Facets

**Available Filters:**

| Category | Filters |
|----------|---------|
| **Price** | Range slider, per person vs. total |
| **Duration** | < 1 hour, 1-4 hours, full day, multi-day |
| **Category** | Tours, tickets, food, outdoor, etc. |
| **Cancellation** | Free cancellation allowed |
| **Confirmation** | Instant booking only |
| **Rating** | 4+ stars, etc. |
| **Time of day** | Morning, afternoon, evening |
| **Features** | Wheelchair accessible, child-friendly |

**Research:**
- Which filters do customers use most?
- How do we handle "no results"?
- Can we suggest alternatives?

---

## Open Problems

### 1. "Flexible Date" Search
**Challenge:** Customer wants activities "sometime next week"

**Options:**
- Show calendar with availability
- Show "available next week" flag
- Require specific date

**Research:** What are customer expectations?

### 2. Group Pricing Complexity
**Challenge:** Price varies by group composition (ages, sizes)

**Questions:**
- How do we show pricing without knowing exact ages?
- When do we collect participant details?
- What if price changes after details entered?

### 3. Time Slot Selection UX
**Challenge:** Activity has 20+ start times

**Questions:**
- How do we present this without overwhelming?
- What about activities with flexible timing?
- How do we handle timezone differences?

### 4. Sold Out vs. Unavailable
**Challenge:** Some activities are temporarily unavailable, others permanently

**Questions:**
- How do we distinguish?
- Can we show "back in stock" notifications?
- What about waitlists?

---

## Competitor Research Needed

| Competitor | Search UX | Notable Patterns |
|------------|-----------|------------------|
| **Viator** | ? | ? |
| **GetYourGuide** | ? | ? |
| **Klook** | ? | ? |
| **Airbnb Experiences** | ? | ? |

---

## Experiments to Run

1. **Search latency test:** How fast do provider APIs respond?
2. **Availability accuracy test:** Do sold out activities appear?
3. **Pricing accuracy test:** Do quoted prices match final?
4. **Filter usage analysis:** Which filters are most used?

---

## References

- [Ground Transportation - Search](./GROUND_TRANSPORTATION_02_SEARCH.md) — Similar search patterns
- [Accommodation Catalog - Search](./ACCOMMODATION_CATALOG_04_SEARCH.md) — Location handling

---

## Next Steps

1. Test provider search APIs
2. Design search UI
3. Map availability models
4. Build ranking algorithm
5. Create filter system

---

**Status:** Research Phase — Search patterns unknown

**Last Updated:** 2026-04-27
