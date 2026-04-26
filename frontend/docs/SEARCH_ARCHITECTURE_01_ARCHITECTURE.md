# Search Architecture Part 1: Search Infrastructure

> Search providers, infrastructure design, and API patterns

**Series:** Search Architecture
**Next:** [Part 2: Indexing Strategy](./SEARCH_ARCHITECTURE_02_INDEXING.md)

---

## Table of Contents

1. [Search Provider Evaluation](#search-provider-evaluation)
2. [Architecture Overview](#architecture-overview)
3. [Search API Design](#search-api-design)
4. [Multi-Language Search](#multi-language-search)
5. [Search Analytics](#search-analytics)

---

## Search Provider Evaluation

### Search Engine Options

```typescript
// Search provider comparison

interface SearchProviders {
  algolia: {
    strengths: ['Fast (<50ms)', 'Great UX features', 'Hosted'];
    weaknesses: ['Cost at scale', 'Vendor lock-in'];
    pricing: 'Free tier + usage-based';
    bestFor: 'User-facing search, autocomplete';
  };

  typesense: {
    strengths: ['Open source', 'Self-hostable', 'Fast'];
    weaknesses: ['Less mature', 'Self-hosting overhead'];
    pricing: 'Free (self-hosted)';
    bestFor: 'Cost-sensitive, control requirements';
  };

  meilisearch: {
    strengths: ['Open source', 'Great relevance', 'Easy setup'];
    weaknesses: ['Less features', 'Smaller community'];
    pricing: 'Free (self-hosted)';
    bestFor: 'MVP, cost-sensitive projects';
  };

  elasticsearch: {
    strengths: ['Powerful', 'Highly customizable', 'Mature'];
    weaknesses: ['Complex', 'Resource intensive', 'Expensive'];
    pricing: 'Self-hosted or cloud';
    bestFor: 'Complex search, log analytics';
  };
}
```

### Our Choice: Algolia

```typescript
// Algolia configuration

import algoliasearch from 'algoliasearch/lite';

// Client-side search (limited API key)
export const searchClient = algoliasearch(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID!,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_KEY!
);

// Server-side client (full admin)
import algoliasearch from 'algoliasearch';
export const algoliaAdmin = algoliasearch(
  process.env.ALGOLIA_APP_ID!,
  process.env.ALGOLIA_ADMIN_KEY!
);

interface AlgoliaConfig {
  // Indices
  indices: {
    destinations: 'travel_destinations';
    accommodations: 'travel_accommodations';
    deals: 'travel_deals';
    blog: 'travel_blog';
  };

  // Settings
  settings: {
    typoTolerance: 'min'; // Allow some typos
    ignorePlurals: true; // "hotel" matches "hotels"
    advancedSyntax: true; // Allow quotes, AND/OR
    facetFilters: true; // Enable filtering
    distinct: true; // Deduplicate results
  };
}
```

---

## Architecture Overview

### Search Flow

```typescript
// Search request flow

interface SearchArchitecture {
  // User search flow
  userSearch: {
    1: 'User types in search box';
    2: 'Frontend sends query to Algolia (direct)';
    3: 'Algolia returns results';
    4: 'Frontend displays results';
    latency: '<100ms';
  };

  // Admin update flow
  adminUpdate: {
    1: 'Admin updates content in Sanity/DB';
    2: 'Webhook triggers sync function';
    3: 'Function updates Algolia index';
    4: 'New content searchable';
    latency: '<5s';
  };

  // Reindex flow
  reindex: {
    1: 'Scheduled job triggers';
    2: 'Fetch all records from DB';
    3: 'Batch update Algolia index';
    4: 'Verify index health';
    frequency: 'Daily for full, hourly for deals';
  };
}
```

### Infrastructure Diagram

```typescript
// Search infrastructure components

interface SearchInfrastructure {
  frontend: {
    component: 'InstantSearch.js';
    provider: 'Algolia JavaScript API';
    authentication: 'Search-only API key';
  };

  backend: {
    component: 'API routes / Edge functions';
    provider: 'Algolia Admin API';
    authentication: 'Admin API key';
  };

  sync: {
    component: 'Webhook handlers + Cron jobs';
    triggers: ['Sanity webhooks', 'DB triggers', 'Scheduled jobs'];
    authentication: 'Admin API key';
  };

  analytics: {
    component: 'Algolia Analytics + Custom events';
    metrics: ['queries', 'clicks', 'conversions', 'zero results'];
  };
}
```

---

## Search API Design

### Server-Side Search API

```typescript
// Next.js API route for search

import { NextRequest, NextResponse } from 'next/server';
import { algoliaAdmin } from '@/lib/algolia';

export const runtime = 'edge';

interface SearchParams {
  query: string;
  index?: string;
  filters?: string;
  facetFilters?: string[][];
  numericFilters?: string[];
  aroundLatLng?: string;
  aroundRadius?: number;
  page?: number;
  hitsPerPage?: number;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const params: SearchParams = {
    query: searchParams.get('q') || '',
    index: searchParams.get('index') || 'destinations',
    filters: searchParams.get('filters') || undefined,
    facetFilters: searchParams.getAll('facetFilters[]'),
    numericFilters: searchParams.getAll('numericFilters[]'),
    aroundLatLng: searchParams.get('aroundLatLng') || undefined,
    aroundRadius: searchParams.get('aroundRadius')
      ? parseInt(searchParams.get('aroundRadius')!)
      : undefined,
    page: parseInt(searchParams.get('page') || '1'),
    hitsPerPage: parseInt(searchParams.get('hitsPerPage') || '20'),
  };

  const index = algoliaAdmin.initIndex(
    `travel_${params.index}`
  );

  try {
    const results = await index.search(params.query, {
      filters: params.filters,
      facetFilters: params.facetFilters,
      numericFilters: params.numericFilters,
      aroundLatLng: params.aroundLatLng,
      aroundRadius: params.aroundRadius,
      page: params.page,
      hitsPerPage: params.hitsPerPage,
    });

    // Track search query
    await trackSearchQuery({
      query: params.query,
      index: params.index,
      hits: results.hits.length,
      userId: request.headers.get('x-user-id'),
    });

    return NextResponse.json(results);
  } catch (error) {
    return NextResponse.json(
      { error: 'Search failed' },
      { status: 500 }
    );
  }
}
```

### Multi-Index Search

```typescript
// Search across multiple indices

import { multipleQueries } from '@algolia/client-search';

export async function searchAll(
  query: string,
  options?: Record<string, unknown>
) {
  const indices = ['destinations', 'accommodations', 'deals', 'blog'];

  const requests = indices.map((index) => ({
    indexName: `travel_${index}`,
    query,
    params: {
      hitsPerPage: 5,
      ...options,
    },
  }));

  const results = await multipleQueries(algoliaAdmin, { requests });

  return results.results.map((result, index) => ({
    type: indices[index],
    hits: result.hits,
    nbHits: result.nbHits,
  }));
}

// Usage: Federated search results
const results = await searchAll('Paris');
// Returns:
// [
//   { type: 'destinations', hits: [...], nbHits: 42 },
//   { type: 'accommodations', hits: [...], nbHits: 156 },
//   { type: 'deals', hits: [...], nbHits: 3 },
//   { type: 'blog', hits: [...], nbHits: 7 },
// ]
```

### Secure Search API

```typescript
// Rate-limited, authenticated search

import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'),
});

export async function GET(request: NextRequest) {
  // Rate limiting
  const ip = request.headers.get('x-forwarded-for') || 'unknown';
  const { success } = await ratelimit.limit(ip);

  if (!success) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429 }
    );
  }

  // Authenticated user gets higher limits
  const userId = request.headers.get('x-user-id');
  if (userId) {
    const { success: userSuccess } = await ratelimit.limit(
      `user:${userId}`,
      { rate: 100, interval: '60 s' }
    );

    if (!userSuccess) {
      return NextResponse.json(
        { error: 'User rate limit exceeded' },
        { status: 429 }
      );
    }
  }

  // ... proceed with search
}
```

---

## Multi-Language Search

### Language-Specific Indices

```typescript
// Multi-language search strategy

interface MultiLanguageSearch {
  // Option 1: Separate indices per language
  separateIndices: {
    indices: [
      'travel_destinations_en',
      'travel_destinations_es',
      'travel_destinations_fr',
    ];
    pros: ['Independent relevance tuning', 'Language-specific settings'];
    cons: ['More indices to manage', 'Cross-language search complex'];
  };

  // Option 2: Single index with language attribute
  singleIndex: {
    index: 'travel_destinations';
    attributes: ['title_en', 'title_es', 'title_fr'];
    pros: ['Single index', 'Easy cross-language search'];
    cons: ['Larger index', 'Complex relevance tuning'];
  };

  // Option 3: Replica indices (RECOMMENDED)
  replicas: {
    primary: 'travel_destinations_en';
    replicas: [
      'travel_destinations_es',
      'travel_destinations_fr',
    ];
    pros: ['Shared settings', 'Language-specific ranking', 'Easy management'];
    cons: ['Requires Algolia plan that supports replicas'];
  };
}
```

### Language-Aware Search

```typescript
// Search in user's language

import { searchClient } from '@/lib/algolia';

export function searchDestinations(
  query: string,
  locale = 'en'
) {
  const indexName = `travel_destinations_${locale}`;
  const index = searchClient.initIndex(indexName);

  return index.search(query, {
    attributesToRetrieve: [
      `title_${locale}`,
      `summary_${locale}`,
      'country',
      'imageUrl',
    ],
    attributesToHighlight: [`title_${locale}`, `summary_${locale}`],
  });
}

// Fallback to English if no results
export async function searchWithFallback(
  query: string,
  locale = 'en'
) {
  const results = await searchDestinations(query, locale);

  if (results.nbHits === 0 && locale !== 'en') {
    // Search in English as fallback
    const englishResults = await searchDestinations(query, 'en');
    return {
      ...englishResults,
      fallback: true,
      locale: 'en',
    };
  }

  return { ...results, locale };
}
```

---

## Search Analytics

### Query Tracking

```typescript
// Track search queries for insights

interface SearchEvent {
  query: string;
  index: string;
  hits: number;
  userId?: string;
  sessionId: string;
  timestamp: string;
  filters?: Record<string, unknown>;
}

export async function trackSearchQuery(event: SearchEvent) {
  // Send to analytics
  await analytics.track('search_query', {
    query: event.query,
    index: event.index,
    results_count: event.hits,
    user_id: event.userId,
    session_id: event.sessionId,
  });

  // Track zero results queries
  if (event.hits === 0) {
    await analytics.track('search_zero_results', {
      query: event.query,
      index: event.index,
    });
  }
}
```

### Click Tracking

```typescript
// Track result clicks for relevance tuning

interface ClickEvent {
  queryId: string;
  position: number;
  objectId: string;
  index: string;
  userId?: string;
  timestamp: string;
}

export async function trackClick(event: ClickEvent) {
  // Send to Algolia for insights
  await algoliaAdmin.initIndex(event.index).search('', {
    clickAnalytics: true,
  });

  // Track custom event
  await analytics.track('search_result_click', {
    query_id: event.queryId,
    position: event.position,
    object_id: event.objectId,
    index: event.index,
    user_id: event.userId,
  });
}
```

### Conversion Tracking

```typescript
// Track bookings from search

interface ConversionEvent {
  queryId: string;
  objectId: string;
  index: string;
  value: number;
  userId?: string;
  timestamp: string;
}

export async function trackConversion(event: ConversionEvent) {
  await analytics.track('search_conversion', {
    query_id: event.queryId,
    object_id: event.objectId,
    index: event.index,
    value: event.value,
    user_id: event.userId,
  });

  // Also send to Algolia for personalization
  await algoliaAdmin.initIndex(event.index).search('', {
    clickAnalytics: true,
  });
}
```

---

## Summary

Search architecture for the travel agency platform:

- **Provider**: Algolia for fast, user-facing search
- **Architecture**: Direct client queries + server-side sync
- **Multi-Language**: Replica indices per language
- **Analytics**: Query, click, and conversion tracking
- **Performance**: <100ms search latency

**Key Architectural Decisions:**
- Algolia for speed and UX features
- Direct client queries for low latency
- Webhook-driven index updates
- Separate indices per content type
- Replica indices for multi-language

---

**Next:** [Part 2: Indexing Strategy](./SEARCH_ARCHITECTURE_02_INDEXING.md) — Data synchronization and schema design
