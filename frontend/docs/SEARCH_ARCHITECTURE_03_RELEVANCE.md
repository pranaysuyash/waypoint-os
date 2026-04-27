# Search Architecture Part 3: Relevance & Ranking

> Scoring algorithms, personalization, and ranking strategies

**Series:** Search Architecture
**Previous:** [Part 2: Indexing Strategy](./SEARCH_ARCHITECTURE_02_INDEXING.md)
**Next:** [Part 4: Search UX](./SEARCH_ARCHITECTURE_04_UX.md)

---

## Table of Contents

1. [Relevance Scoring](#relevance-scoring)
2. [Custom Ranking](#custom-ranking)
3. [Personalization](#personalization)
4. [Geo-Based Ranking](#geo-based-ranking)
5. [Business Logic Injection](#business-logic-injection)
6. [A/B Testing](#ab-testing)

---

## Relevance Scoring

### Default Ranking Strategy

```typescript
// Algolia ranking criteria

interface RankingCriteria {
  // Default ranking order
  default: [
    'typo',        // Better typo tolerance = higher rank
    'geo',         // Closer geo location = higher rank
    'words',       // More query words matched = higher rank
    'proximity',   // Closer word proximity = higher rank
    'attribute',   // Matches in important attributes = higher rank
    'exact',       // Exact matches = higher rank
    'custom',      // Custom ranking criteria
  ];
}

// Apply to index
await index.setSettings({
  ranking: [
    'typo',
    'geo',
    'words',
    'proximity',
    'attribute',
    'exact',
    'desc(popularity)',
    'desc(featured)',
  ],
  // Attribute priority (order matters)
  searchableAttributes: [
    'title',       // Highest priority
    'summary',
    'description',
    'country',     // Lower priority
  ],
});
```

### Attribute Weighting

```typescript
// Boost importance of specific attributes

await index.setSettings({
  searchableAttributes: [
    'title',        // Unspecified weight = default
    'summary',      // Unspecified weight = default
    'description(unordered)', // Lower priority
  ],

  // Or use custom ranking for more control
  customRanking: [
    'desc(title_match_exact)',  // Exact title match = highest
    'desc(title_match_words)',  // Title with all words
    'desc(popularity)',
  ],
});

// Alternative: Use attribute ranking
await index.setSettings({
  ranking: [
    'typo',
    'geo',
    'words',
    'proximity',
    'attribute',
    'exact',
    'custom',
  ],
  // Define attribute importance
  searchableAttributes: [
    'title',        // Most important
    'summary',
    'description',  // Less important
  ],
  // Optional: disable unordered matching for title
  disableTypoToleranceOnWords: ['paris'], // Don't allow typos on "paris"
});
```

---

## Custom Ranking

### Business Metrics Ranking

```typescript
// Custom ranking based on business metrics

await index.setSettings({
  customRanking: [
    'desc(featured)',           // Featured content first
    'desc(popularity)',         // Most popular
    'desc(rating)',             // Highest rated
    'desc(reviewCount)',        // Most reviewed
    'desc(bookings)',           // Most booked
    'desc(conversion_rate)',    // Best converting
    'asc(price)',               // Lower price (when sorting by value)
  ],

  // Dynamic ranking based on user intent
  // Use different indices for different contexts
});
```

### Contextual Ranking

```typescript
// Different ranking for different contexts

interface RankingContext {
  // Default search
  default: 'travel_destinations';

  // For deals/bargain hunters
  value: 'travel_destinations_by_value';

  // For luxury travelers
  luxury: 'travel_destinations_by_luxury';

  // For trending content
  trending: 'travel_destinations_trending';

  // For new discoveries
  new: 'travel_destinations_newest';
}

// Configure each replica for its context
async function setupContextualIndices() {
  // Value-focused: prioritize affordability
  await valueIndex.setSettings({
    customRanking: [
      'asc(avgPrice)',
      'desc(deals_available)',
      'desc(rating)',
    ],
  });

  // Luxury-focused: prioritize premium options
  await luxuryIndex.setSettings({
    customRanking: [
      'desc(starRating)',
      'desc(avgPrice)',
      'desc(rating)',
    ],
    // Add numeric filter for minimum price
    numericFilters: ['avgPrice >= 500'],
  });

  // Trending: prioritize recent engagement
  await trendingIndex.setSettings({
    customRanking: [
      'desc(views_last_7d)',
      'desc(views_last_24h)',
      'desc(bookings_last_7d)',
    ],
  });

  // New: prioritize recently added
  await newIndex.setSettings({
    customRanking: [
      'desc(createdAt)',
      'desc(featured)',
    ],
  });
}
```

---

## Personalization

### User-Based Personalization

```typescript
// Personalize based on user history

interface UserProfile {
  userId: string;
  interests: string[];
  pastDestinations: string[];
  budgetRange: [number, number];
  travelStyle: 'budget' | 'moderate' | 'luxury';
  preferences: {
    beach: boolean;
    city: boolean;
    adventure: boolean;
    culture: boolean;
  };
}

// Personalized search
export async function personalizedSearch(
  query: string,
  user: UserProfile
) {
  const index = algoliaAdmin.initIndex('travel_destinations');

  // Build filters based on user profile
  const filters = [];

  // Filter by budget
  if (user.budgetRange) {
    filters.push(`avgPrice:${user.budgetRange[0]} TO ${user.budgetRange[1]}`);
  }

  // Boost preferred destinations
  const optionalFilters = [];

  if (user.interests.length > 0) {
    optionalFilters.push(
      ...user.interests.map((interest) => `tags:${interest}<score=3>`)
    );
  }

  if (user.pastDestinations.length > 0) {
    // Exclude already visited
    filters.push(
      `NOT objectID:${user.pastDestinations.join(' AND NOT objectID:')}`
    );
  }

  // Select ranking index based on travel style
  const indexName = {
    budget: 'travel_destinations_by_value',
    moderate: 'travel_destinations',
    luxury: 'travel_destinations_by_luxury',
  }[user.travelStyle];

  const personalizedIndex = algoliaAdmin.initIndex(indexName);

  return personalizedIndex.search(query, {
    filters: filters.join(' AND '),
    optionalFilters: optionalFilters.length > 0 ? optionalFilters : undefined,
    userToken: user.userId, // Enable personalization
  });
}
```

### Behavioral Personalization

```typescript
// Algolia Recommend integration

import { recommendClient } from '@/lib/algolia';

// Related destinations based on user behavior
export async function getRelatedDestinations(
  destinationId: string,
  userId?: string
) {
  // Related products (based on co-viewing/co-booking)
  const related = await recommendClient.getRelatedProducts({
    indexName: 'travel_destinations',
    objectID: destinationId,
    userToken: userId,
    maxRecommendations: 6,
  });

  return related.hits;
}

// Frequently bought together
export async function getFrequentlyBookedTogether(
  destinationId: string
) {
  const fbTogether = await recommendClient.getFrequentlyBoughtTogether({
    indexName: 'travel_destinations',
    objectID: destinationId,
    maxRecommendations: 6,
  });

  return fbTogether.hits;
}

// Personalized recommendations
export async function getPersonalizedRecommendations(
  userId: string
) {
  const recommended = await recommendClient.getPersonalizedRecommendations({
    indexName: 'travel_destinations',
    userToken: userId,
    maxRecommendations: 10,
  });

  return recommended.hits;
}
```

---

## Geo-Based Ranking

### Location-Aware Search

```typescript
// Search with location priority

export async function searchNearby(
  query: string,
  location: { lat: number; lng: number },
  radius = 100000 // 100km in meters
) {
  const index = algoliaAdmin.initIndex('travel_accommodations');

  return index.search(query, {
    aroundLatLng: `${location.lat},${location.lng}`,
    aroundRadius: radius,
    // Or use predefined radiuses
    aroundRadius: [
      { radius: 10000, name: 'Very Close' },    // 10km
      { radius: 50000, name: 'Close' },         // 50km
      { radius: 100000, name: 'Nearby' },       // 100km
      { radius: 'all', name: 'Any Distance' },
    ],
  });
}
```

### User Location Detection

```typescript
// Detect and use user location

import { NextRequest } from 'next/server';

export function getUserLocation(request: NextRequest) {
  // From headers (Vercel/Cloudflare)
  const country = request.headers.get('x-vercel-ip-country');
  const region = request.headers.get('x-vercel-ip-region');
  const city = request.headers.get('x-vercel-ip-city');
  const lat = request.headers.get('x-vercel-ip-latitude');
  const lng = request.headers.get('x-vercel-ip-longitude');

  if (lat && lng) {
    return { lat: parseFloat(lat), lng: parseFloat(lng) };
  }

  // Or from browser geolocation API
  return null;
}

// Search with detected location
export async function searchWithLocation(
  query: string,
  request: NextRequest
) {
  const userLocation = getUserLocation(request);

  if (userLocation) {
    return searchNearby(query, userLocation);
  }

  // Fallback to IP-based country filtering
  const country = request.headers.get('x-vercel-ip-country');
  return index.search(query, {
    filters: country ? `country:${country}` : undefined,
  });
}
```

---

## Business Logic Injection

### Promotional Boosting

```typescript
// Boost promoted content

export async function searchWithPromotions(query: string) {
  const index = algoliaAdmin.initIndex('travel_destinations');

  return index.search(query, {
    // Boost featured destinations
    optionalFilters: [
      'featured:true<score=10>',      // 10x boost for featured
      'hasActiveDeal:true<score=5>',  // 5x boost for deals
    ],

    // Or use numeric filters for more control
    numericFilters: [
      'promotionBoost >= 0', // Add this field to promoted items
    ],

    // Custom ranking
    customRanking: [
      'desc(promotionBoost)',
      'desc(popularity)',
    ],
  });
}
```

### Availability-Based Ranking

```typescript
// Rank by availability

export async function searchAvailable(
  query: string,
  checkIn: Date,
  checkOut: Date
) {
  const index = algoliaAdmin.initIndex('travel_accommodations');

  // Get available accommodations from booking system
  const availableIds = await getAvailableAccommodations(
    checkIn,
    checkOut
  );

  return index.search(query, {
    filters: availableIds.length > 0
      ? `objectID:${availableIds.join(' OR objectID:')}`
      : undefined,

    // Boost highly available options
    customRanking: [
      'desc(availabilityScore)',
      'desc(rating)',
    ],
  });
}

// Pre-compute availability score
async function updateAvailabilityScores() {
  const accommodations = await prisma.accommodation.findMany();

  for (const accomm of accommodations) {
    // Calculate availability score (0-100)
    const score = await calculateAvailabilityScore(accomm.id);

    await index.partialUpdateObject({
      objectID: accomm.id,
      availabilityScore: score,
    });
  }
}
```

---

## A/B Testing

### Ranking Variant Testing

```typescript
// A/B test different ranking strategies

interface RankingVariant {
  name: string;
  index: string;
  allocation: number; // 0-1
}

const variants: RankingVariant[] = [
  { name: 'control', index: 'destinations_v1', allocation: 0.5 },
  { name: 'trending', index: 'destinations_v2_trending', allocation: 0.25 },
  { name: 'value', index: 'destinations_v3_value', allocation: 0.25 },
];

export function getVariantForUser(userId: string) {
  // Consistent hash for user
  const hash = hashCode(userId);
  const bucket = hash % 100;

  let cumulative = 0;
  for (const variant of variants) {
    cumulative += variant.allocation * 100;
    if (bucket < cumulative) {
      return variant;
    }
  }

  return variants[0];
}

// Search with variant
export async function searchWithVariant(
  query: string,
  userId: string
) {
  const variant = getVariantForUser(userId);
  const index = algoliaAdmin.initIndex(variant.index);

  const results = await index.search(query);

  // Track variant exposure
  await analytics.track('search_variant_exposure', {
    userId,
    variant: variant.name,
    query,
    resultsCount: results.nbHits,
  });

  return { ...results, variant: variant.name };
}

function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}
```

### Metric Tracking

```typescript
// Track A/B test metrics

interface VariantMetrics {
  variant: string;
  searches: number;
  clickRate: number;
  conversionRate: number;
  avgPosition: number;
}

export async function trackSearchMetric(
  event: 'search' | 'click' | 'conversion',
  variant: string,
  data: {
    userId: string;
    queryId?: string;
    position?: number;
    value?: number;
  }
) {
  await analytics.track(`search_${event}`, {
    variant,
    ...data,
  });

  // Update Redis metrics
  const key = `search_metrics:${variant}:${new Date().toISOString().split('T')[0]}`;

  if (event === 'search') {
    await redis.hincrby(key, 'searches', 1);
  } else if (event === 'click') {
    await redis.hincrby(key, 'clicks', 1);
  } else if (event === 'conversion') {
    await redis.hincrby(key, 'conversions', 1);
    await redis.hincrbyfloat(key, 'revenue', data.value || 0);
  }
}
```

---

## Summary

Relevance and ranking for the travel agency platform:

- **Scoring**: Attribute weighting, exact match priority
- **Custom Ranking**: Business metrics, featured content
- **Personalization**: User profiles, behavioral data
- **Geo-Ranking**: Location-aware search, distance sorting
- **Business Logic**: Promotional boost, availability filtering
- **A/B Testing**: Variant allocation, metric tracking

**Key Relevance Decisions:**
- Default ranking: typo → geo → words → proximity → attribute → exact → custom
- Featured content gets 10x boost
- Personalize based on user history and preferences
- Use geo-location for nearby results
- A/B test different ranking strategies
- Track click-through and conversion rates

---

**Next:** [Part 4: Search UX](./SEARCH_ARCHITECTURE_04_UX.md) — Autocomplete, faceted search, and results display
