# Local Recommendations 03: Display & Discovery

> How recommendations are presented and discovered

---

## Document Overview

**Focus:** Recommendation display and discovery
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Discovery Experience
- How do users discover recommendations?
- What is the browsing experience?
- How do we handle different trip stages?
- What about spontaneous discovery?

### Visual Design
- How do we present items?
- What information is most important?
- How do we handle photos?
- What about maps?

### Organization
- How do we group items?
- What categories do we use?
- How do we handle filters?
- What about sorting?

### Integration
- Where do recommendations appear?
- How do they integrate with bookings?
- What about trip planning?
- How do we drive action?

---

## Research Areas

### A. Discovery Patterns

**Entry Points:**

| Entry Point | Trigger | Research Needed |
|-------------|---------|-----------------|
| **Destination page** | Viewing destination | ? |
| **Trip builder** | Planning trip | ? |
| **During trip** | On the go | ? |
| **Post-booking** | After hotel/activity booked | ? |
| **Browse** | Exploring | ? |

**Discovery Modes:**

| Mode | Description | Research Needed |
|------|-------------|-----------------|
| **Browse** | Explore by category | ? |
| **Search** | Specific intent | ? |
| **Map view** | Location-based | ? |
| **Near me** | Proximity-based | ? |
| **Trending** | What's popular | ? |
| **For you** | Personalized | ? |

### B. Item Display

**Card Content:**

| Element | Priority | Research Needed |
|---------|----------|-----------------|
| **Photo** | High | ? |
| **Name** | High | ? |
| **Category** | High | ? |
| **Rating** | High | ? |
| **Price indicator** | High | ? |
| **Distance** | Medium | ? |
| **Short description** | Medium | ? |
| **Why recommended** | Medium | ? |
| **Open status** | Medium | ? |

**Card Actions:**

| Action | Location | Research Needed |
|--------|----------|-----------------|
| **View details** | Primary button | ? |
| **Save** | Icon | ? |
| **Book/Reserve** | If applicable | ? |
| **Get directions** | If nearby | ? |
| **Share** | Secondary | ? |
| **Not interested** | Feedback | ? |

**Layout Options:**

| Layout | Use Case | Research Needed |
|--------|----------|-----------------|
| **Card grid** | Browse, many items | ? |
| **List view** | Detailed info | ? |
| **Featured** | Highlight specific | ? |
| **Map markers** | Location context | ? |

### C. Filtering & Sorting

**Filter Categories:**

| Category | Options | Research Needed |
|----------|---------|-----------------|
| **Type** | Restaurant, attraction, etc. | ? |
| **Subtype** | Cuisine, activity type | ? |
| **Price** | $, $$, $$$, $$$$ | ? |
| **Rating** | 3+, 4+, etc. | ? |
| **Distance** | <1km, <5km, etc. | ? |
| **Open now** | Yes/No | ? |
| **Features** | WiFi, parking, etc. | ? |

**Sort Options:**

| Option | Use Case | Research Needed |
|--------|----------|-----------------|
| **Relevance** | Default, personalized | ? |
| **Rating** | Quality-focused | ? |
| **Distance** | Nearby | ? |
| **Price** | Budget | ? |
| **Popularity** | Social proof | ? |
| **Newest** | Fresh options | ? |

### D. Detail View

**Detail Sections:**

| Section | Content | Research Needed |
|---------|---------|-----------------|
| **Hero** | Main photo, name, rating | ? |
| **About** | Description, highlights | ? |
| **Practical** | Hours, location, contact | ? |
| **Media** | Photo gallery | ? |
| **Reviews** | Selected reviews | ? |
| **Similar** | Related recommendations | ? |
| **Why recommended** | Personalization explainer | ? |

**Booking Actions:**

| Action | When | Research Needed |
|--------|------|-----------------|
| **Book now** | Direct booking available | ? |
| **Reserve** | Reservation available | ? |
| **Get directions** | Navigation | ? |
| **Call** | Direct contact | ? |
| **Visit website** | External link | ? |
| **Add to trip** | Trip planning | ? |

### E. Map Integration

**Map Features:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Markers** | Item locations | ? |
| **Clustering** | Handle density | ? |
| **Category layers** | Filter by type | ? |
| **Selected preview** | Quick info on tap | ? |
| **Route planning** | Multiple stops | ? |
| **Nearby radius** | Current location | ? |

---

## Data Model Sketch

```typescript
interface RecommendationDisplayConfig {
  viewMode: ViewMode;
  sortBy: SortOption;
  filters: RecommendationFilters;

  // Layout
  cardSize: 'compact' | 'standard' | 'detailed';
  showMap: boolean;
  mapVisible: boolean;
}

type ViewMode =
  | 'browse'
  | 'search'
  | 'map'
  | 'near_me'
  | 'for_you';

interface RecommendationFilters {
  categories?: RecommendationCategory[];
  subcategories?: string[];
  priceLevel?: PriceLevel[];
  minRating?: number;
  maxDistance?: number; // meters
  openNow?: boolean;
  features?: string[];

  // Advanced
  openAt?: TimeRange;
  goodFor?: string[]; // families, couples, etc.
}

interface RecommendationCard {
  item: RecommendationData;
  display: RecommendationDisplayData;

  // Personalization
  relevanceScore: number;
  recommendationReasons: RecommendationReason[];

  // Status
  saved: boolean;
  viewed: boolean;
}

interface RecommendationDisplayData {
  // Images
  primaryImage?: string;
  imageCount: number;

  // Key info
  displayName: string;
  category: RecommendationCategory;
  subcategory?: string;

  // Signals
  rating?: number;
  reviewCount?: number;
  priceLevel?: PriceLevel;

  // Status
  isOpenNow?: boolean;
  distance?: number; // meters

  // Why
  personalizationNote?: string;
}
```

---

## Open Problems

### 1. Overwhelming Choice
**Challenge:** Too many options

**Options:** Curation, progressive disclosure, smart defaults

### 2. Decision Paralysis
**Challenge:** Hard to choose

**Options:** Clear comparisons, highlights, expert picks

### 3. Context Relevance
**Challenge:** Right recommendation at right time

**Options:** Context awareness, trip stage detection

### 4. Action Conversion
**Challenge:** Browse but don't book/visit

**Options:** Clear CTAs, easy planning, urgency

### 5. Data Accuracy
**Challenge:** Wrong hours, closed places

**Options:** User feedback, verification, frequent updates

---

## Next Steps

1. Design discovery experience
2. Build recommendation UI components
3. Integrate with trip planning
4. Implement map view

---

**Status:** Research Phase — Display patterns unknown

**Last Updated:** 2026-04-27
