# Local Recommendations 01: Sources & Data

> Where local recommendation data comes from

---

## Document Overview

**Focus:** Recommendation data sources
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Data Sources
- Where do we get local data?
- What APIs are available?
- How do we integrate them?
- What are the costs?

### Data Quality
- How do we ensure accuracy?
- What about stale data?
- How do we handle inconsistencies?
- What about coverage gaps?

### Data Types
- What information do we need?
- How structured is the data?
- What about images and media?
- How do we handle different languages?

### Legal & Access
- What are the API terms?
- How do we attribute sources?
- What about rate limits?
- Are there usage restrictions?

---

## Research Areas

### A. Primary Sources

**Global Platforms:**

| Source | Coverage | API Access | Research Needed |
|--------|----------|------------|-----------------|
| **Google Places** | Global | Yes, paid | ? |
| **TripAdvisor** | Global | Limited/Partner | ? |
| **Yelp** | US-focused | Yes, paid | ? |
| **Foursquare** | Global | Yes, paid | ? |
| **OpenStreetMap** | Global | Free, crowd-sourced | ? |

**Regional Players:**

| Source | Region | Coverage | Research Needed |
|--------|--------|----------|-----------------|
| **Zomato** | India, Global | Yes, API | ? |
| **Swiggy** | India | Restaurant data | ? |
| **Dineout** | India | Restaurant bookings | ? |
| **Magicpin** | India | Local discovery | ? |
| **Burpple** | SE Asia | Food & drink | ? |
| **Delivery Hero** | Europe | Restaurant data | ? |

**Travel-Specific:**

| Source | Focus | API Access | Research Needed |
|--------|-------|-----------|-----------------|
| **Lonely Planet** | Attractions | Partner? | ? |
| **Viator/TripAdvisor** | Experiences | API | ? |
| **GetYourGuide** | Experiences | API | ? |
| **Klook** | Asia experiences | API | ? |

### B. Data Structure

**Core Data Points:**

| Field | Type | Availability | Research Needed |
|-------|------|--------------|-----------------|
| **Name** | String | Universal | ? |
| **Category** | Enum | Varies | ? |
| **Location** | Lat/long | Universal | ? |
| **Address** | String | Universal | ? |
| **Phone** | String | Most | ? |
| **Hours** | Object | Most | ? |
| **Price level** | Enum | Most | ? |
| **Rating** | Number | Most | ? |
| **Photos** | Array | Many | ? |
| **Description** | String | Some | ? |
| **Cuisine** | Array | Restaurants | ? |
| **Features** | Array | Some | ? |

**Category Taxonomy:**

| Level | Examples | Research Needed |
|-------|----------|-----------------|
| **Type** | Restaurant, Attraction, Activity | ? |
| **Category** | Indian, Chinese, Museum, Park | ? |
| **Subcategory** | Fine dining, Street food, Art museum | ? |

### C. Data Quality

**Quality Dimensions:**

| Dimension | Measure | Research Needed |
|-----------|---------|-----------------|
| **Accuracy** | Correct info | ? |
| **Completeness** | Required fields present | ? |
| **Currency** | How recently updated | ? |
| **Consistency** | Across sources | ? |
| **Coverage** | Geographic breadth | ? |

**Validation Approaches:**

| Approach | Description | Research Needed |
|----------|-------------|-----------------|
| **Cross-reference** | Multiple sources agree | ? |
| **User feedback** | Report issues | ? |
| **Automated checks** | Validate formats | ? |
| **Periodic refresh** | Re-fetch data | ? |
| **Manual review** | Spot checks | ? |

### D. Integration Strategy

**Fetch Patterns:**

| Pattern | Description | Research Needed |
|---------|-------------|-----------------|
| **On-demand** | Fetch when needed | ? |
| **Pre-cache** | Load for destinations | ? |
| **Periodic sync** | Regular updates | ? |
| **Event-driven** | Update on change | ? |

**Storage Strategy:**

| Approach | Description | Research Needed |
|----------|-------------|-----------------|
| **Cache only** | Temporary storage | ? |
| **Mirror** | Full copy | ? |
| **Hybrid** | Cache + reference | ? |
| **Live API** | Always fetch | ? |

---

## Data Model Sketch

```typescript
interface LocalRecommendationSource {
  sourceId: string;
  name: string;
  type: SourceType;

  // Access
  apiAvailable: boolean;
  apiKey?: string;
  rateLimit?: RateLimit;
  cost?: CostStructure;

  // Coverage
  coverage: CoverageInfo;
  dataTypes: string[];

  // Quality
  reliability: number; // 0-1
  lastUpdate?: Date;
}

interface RecommendationData {
  externalId: string;
  sourceId: string;

  // Core
  name: string;
  category: RecommendationCategory;
  location: Location;

  // Details
  address?: string;
  phone?: string;
  hours?: OpeningHours;
  priceLevel?: PriceLevel;
  rating?: number;
  reviewCount?: number;

  // Content
  description?: string;
  photos?: string[];
  cuisine?: string[];
  features?: string[];

  // Metadata
  fetchedAt: Date;
  lastVerified?: Date;
  confidence: number; // 0-1
}

type RecommendationCategory =
  | 'restaurant'
  | 'attraction'
  | 'activity'
  | 'nightlife'
  | 'shopping'
  | 'entertainment';

type PriceLevel = 1 | 2 | 3 | 4; // $ to $$$$

interface OpeningHours {
  [key: string]: { // Day of week
    open: string; // "09:00"
    close: string; // "22:00"
    closed?: boolean;
  };
}
```

---

## Open Problems

### 1. Data Fragmentation
**Challenge:** Data scattered across many sources

**Options:** Aggregation services, multi-source integration

### 2. Attribution
**Challenge:** Properly crediting sources

**Options:** Clear UI labels, API compliance

### 3. Cost
**Challenge:** Multiple paid APIs add up

**Options:** Hybrid approach, prioritize by value

### 4. Maintenance
**Challenge:** Keeping data current

**Options:** Automation, user feedback, caching strategy

### 5. Coverage Gaps
**Challenge:** Some places have poor data

**Options:** Manual curation, user contributions

---

## Next Steps

1. Audit available APIs
2. Build integration framework
3. Design data storage
4. Create quality checks

---

**Status:** Research Phase — Source landscape unknown

**Last Updated:** 2026-04-27
