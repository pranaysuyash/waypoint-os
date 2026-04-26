# Search Architecture Part 2: Indexing Strategy

> Data synchronization, index schema design, and reindexing

**Series:** Search Architecture
**Previous:** [Part 1: Search Infrastructure](./SEARCH_ARCHITECTURE_01_ARCHITECTURE.md)
**Next:** [Part 3: Relevance & Ranking](./SEARCH_ARCHITECTURE_03_RELEVANCE.md)

---

## Table of Contents

1. [Index Schema Design](#index-schema-design)
2. [Data Synchronization](#data-synchronization)
3. [Incremental Updates](#incremental-updates)
4. [Full Reindexing](#full-reindexing)
5. [Multi-Index Strategy](#multi-index-strategy)

---

## Index Schema Design

### Destination Index

```typescript
// Algolia index schema for destinations

interface DestinationRecord {
  // Identity
  objectID: string; // Sanity document ID

  // Searchable attributes
  title: string;
  summary: string;
  description: string;
  country: string;
  region: string;

  // Faceted attributes
  country: string; // Facet
  region: string; // Facet
  bestTimeToVisit: string[]; // Facet

  // Display attributes
  imageUrl: string;
  slug: string;

  // Geo
  _geoloc: {
    lat: number;
    lng: number;
  };

  // Ranking
  popularity: number;
  featured: boolean;

  // Metadata
  createdAt: number;
  updatedAt: number;
}

// Index settings
const destinationSettings = {
  searchableAttributes: [
    'title',
    'summary',
    'description',
    'country',
    'region',
  ],
  attributesForFaceting: [
    'filterOnly(country)',
    'filterOnly(region)',
    'bestTimeToVisit',
    'featured',
  ],
  customRanking: [
    'desc(popularity)',
    'desc(featured)',
    'desc(updatedAt)',
  ],
  ranking: [
    'typo',
    'geo',
    'words',
    'filters',
    'proximity',
    'attribute',
    'exact',
    'custom',
  ],
  // Geo search
  aroundPrecision: 1000, // 1km
  // Typo tolerance
  typoTolerance: 'min',
  ignorePlurals: true,
  // Display
  attributesToRetrieve: [
    'title',
    'summary',
    'imageUrl',
    'slug',
    'country',
    'region',
  ],
  attributesToHighlight: ['title', 'summary'],
  attributesToSnippet: [['description', 200]],
};
```

### Accommodation Index

```typescript
// Accommodation index schema

interface AccommodationRecord {
  // Identity
  objectID: string;

  // Searchable
  name: string;
  description: string;
  destination: string; // Denormalized for search
  address: string;

  // Faceted
  type: string; // hotel, resort, villa, etc.
  starRating: number; // Numeric filter
  country: string;
  destinationId: string;
  amenities: string[];

  // Display
  images: string[];
  slug: string;

  // Geo
  _geoloc: {
    lat: number;
    lng: number;
  };

  // Pricing (display only - actual pricing in DB)
  startingPrice: number;

  // Ranking
  rating: number;
  reviewCount: number;
  featured: boolean;
}

const accommodationSettings = {
  searchableAttributes: [
    'name',
    'description',
    'destination',
    'address',
  ],
  attributesForFaceting: [
    'filterOnly(type)',
    'searchable(starRating)',
    'filterOnly(country)',
    'filterOnly(destinationId)',
    'amenities',
    'featured',
  ],
  numericAttributesToFilter: [
    'starRating',
    'startingPrice',
    'rating',
  ],
  customRanking: [
    'desc(rating)',
    'desc(featured)',
    'desc(reviewCount)',
  ],
  attributesToHighlight: ['name', 'description'],
  distinct: 3, // Max 3 accommodations per property
  attributeForDistinct: 'propertyId',
};
```

### Deal Index

```typescript
// Deal/promotion index schema

interface DealRecord {
  objectID: string;

  // Searchable
  title: string;
  description: string;
  terms: string;

  // Faceted
  dealType: string; // percentage, fixed, package
  discountType: string; // percentage, fixed
  status: string; // active, scheduled, expired

  // Display
  bannerImage: string;
  slug: string;
  promoCode?: string;

  // Destinations (array for filtering)
  destinationIds: string[];

  // Time-based
  validFrom: number; // Unix timestamp
  validTo: number;

  // Ranking
  discountValue: number;
  featured: boolean;
  priority: number;

  // Usage
  usageLimit?: number;
  usageCount: number;
}

const dealSettings = {
  searchableAttributes: [
    'title',
    'description',
    'terms',
  ],
  attributesForFaceting: [
    'dealType',
    'discountType',
    'status',
    'destinationIds',
    'featured',
  ],
  numericAttributesToFilter: [
    'discountValue',
    'validFrom',
    'validTo',
    'usageLimit',
    'usageCount',
  ],
  customRanking: [
    'desc(priority)',
    'desc(discountValue)',
    'desc(featured)',
  ],
  // Time-based filtering
  filters: `validTo > ${Date.now()} AND status = 'active'`,
};
```

---

## Data Synchronization

### Webhook-Driven Updates

```typescript
// Sanity webhook handler for real-time updates

import { algoliaAdmin } from '@/lib/algolia';
import { sanityClient } from '@/lib/sanity';

export async function POST(request: NextRequest) {
  const body = await request.json();

  // Verify webhook signature
  const signature = request.headers.get('sanity-webhook-signature');
  if (!verifySignature(body, signature)) {
    return Response.json({ error: 'Invalid signature' }, { status: 401 });
  }

  // Handle different content types
  switch (body._type) {
    case 'destination':
      await syncDestination(body);
      break;
    case 'accommodation':
      await syncAccommodation(body);
      break;
    case 'deal':
      await syncDeal(body);
      break;
    default:
      console.log(`Unhandled type: ${body._type}`);
  }

  return Response.json({ synced: true });
}

async function syncDestination(document: SanityDocument) {
  const index = algoliaAdmin.initIndex('travel_destinations');

  // Map Sanity document to Algolia record
  const record = {
    objectID: document._id,
    title: document.title,
    summary: document.summary,
    description: toPlainText(document.description),
    country: document.country?.name || '',
    region: document.region || '',
    bestTimeToVisit: document.bestTimeToVisit || [],
    imageUrl: urlFor(document.heroImage).url(),
    slug: document.slug.current,
    _geoloc: document.coordinates
      ? { lat: document.coordinates.lat, lng: document.coordinates.lng }
      : undefined,
    popularity: document.popularity || 0,
    featured: document.featured || false,
    createdAt: new Date(document._createdAt).getTime(),
    updatedAt: new Date(document._updatedAt).getTime(),
  };

  // Delete if draft or deleted
  if (document._id.startsWith('drafts.') || !defined?.status) {
    await index.deleteObject(document._id.replace('drafts.', ''));
    return;
  }

  // Save or update
  await index.saveObject(record);
}

function toPlainText(blocks: Block[]): string {
  return blocks
    .map((block) => {
      if (block._type !== 'block' || !block.children) {
        return '';
      }
      return block.children.map((child) => child.text).join('');
    })
    .join('\n');
}
```

### Database Sync

```typescript
// Sync from database (for non-CMS data)

import { prisma } from '@/lib/db';
import { algoliaAdmin } from '@/lib/algolia';

export async function syncBooking(id: string) {
  const index = algoliaAdmin.initIndex('travel_bookings');

  const booking = await prisma.booking.findUnique({
    where: { id },
    include: {
      user: { select: { id: true, name: true, email: true } },
      destination: true,
    },
  });

  if (!booking) {
    await index.deleteObject(id);
    return;
  }

  // Only index non-sensitive data for internal search
  const record = {
    objectID: booking.id,
    status: booking.status,
    destination: booking.destination.name,
    user: booking.user.name,
    userId: booking.user.id,
    checkIn: booking.checkIn.getTime(),
    checkOut: booking.checkOut.getTime(),
    createdAt: booking.createdAt.getTime(),
  };

  await index.saveObject(record);
}
```

---

## Incremental Updates

### Change Data Capture

```typescript
// Process incremental updates

import { sanityClient } from '@/lib/sanity';
import { algoliaAdmin } from '@/lib/algolia';

const BATCH_SIZE = 1000;

export async function incrementalSync(
  contentType: string,
  since: Date
) {
  const indexName = `travel_${contentType}s`;
  const index = algoliaAdmin.initIndex(indexName);

  // Fetch changed documents
  const changed = await sanityClient.fetch(
    groq`*[
      _type == $type &&
      _updatedAt > $since
    ]{
      _id,
      _rev,
      ... // all fields
    }`,
    { type: contentType, since: since.toISOString() }
  );

  console.log(`Found ${changed.length} changed ${contentType}s`);

  // Process in batches
  const batches = chunk(changed, BATCH_SIZE);

  for (const batch of batches) {
    const records = batch.map((doc) =>
      mapToAlgoliaRecord(doc, contentType)
    );

    await index.partialUpdateObjects(records);
  }

  return { updated: changed.length };
}
```

### Event-Driven Updates

```typescript
// Queue-based updates for reliability

import { Queue } from 'bullmq';
import { Redis } from 'ioredis';

const syncQueue = new Queue('search-sync', {
  connection: new Redis(process.env.REDIS_URL!),
});

// Add to queue on webhook
export async function POST(request: NextRequest) {
  const body = await request.json();

  await syncQueue.add('sync', {
    type: body._type,
    id: body._id,
    operation: body.operation || 'upsert',
  });

  return Response.json({ queued: true });
}

// Worker processes queue
const worker = new Worker(
  'search-sync',
  async (job) => {
    const { type, id, operation } = job.data;

    switch (type) {
      case 'destination':
        await syncDestination(id);
        break;
      // ... more types
    }
  },
  { connection: new Redis(process.env.REDIS_URL!) }
);
```

---

## Full Reindexing

### Reindex Job

```typescript
// Full reindex of all data

import { sanityClient } from '@/lib/sanity';
import { algoliaAdmin } from '@/lib/algolia';

const BATCH_SIZE = 1000;

export async function reindex(contentType: string) {
  const indexName = `travel_${contentType}s`;
  const index = algoliaAdmin.initIndex(indexName);

  console.log(`Starting reindex of ${contentType}`);

  // Clear existing index
  await index.clearObjects();
  console.log(`Cleared ${indexName}`);

  // Fetch all documents
  let hasMore = true;
  let offset = 0;
  let total = 0;

  while (hasMore) {
    const documents = await sanityClient.fetch(
      groq`*[
        _type == $type &&
        !(_id in path("drafts.**"))
      ][${offset}...${offset + BATCH_SIZE}]`,
      { type: contentType }
    );

    if (documents.length === 0) {
      hasMore = false;
      break;
    }

    // Transform to Algolia records
    const records = documents.map((doc) =>
      mapToAlgoliaRecord(doc, contentType)
    );

    // Save batch
    await index.saveObjects(records);
    total += documents.length;
    offset += BATCH_SIZE;

    console.log(`Indexed ${total} ${contentType}s...`);
  }

  console.log(`Reindex complete: ${total} ${contentType}s`);

  return { total };
}
```

### Vercel Cron Reindex

```typescript
// Scheduled reindexing

import { cron } from '@vercel/triggers-job';

export const config = {
  schedule: [
    // Full reindex at 2 AM daily
    '0 2 * * *',
  ],
};

export default cron.handler(async (req, res) => {
  const results = await Promise.allSettled([
    reindex('destinations'),
    reindex('accommodations'),
    reindex('deals'),
  ]);

  const summary = results.map((r, i) => ({
    type: ['destinations', 'accommodations', 'deals'][i],
    status: r.status,
    total: r.status === 'fulfilled' ? r.value.total : 0,
  }));

  return res.status(200).json({
    reindexed: summary,
    timestamp: new Date().toISOString(),
  });
});
```

---

## Multi-Index Strategy

### Primary and Replica Indices

```typescript
// Set up primary and replica indices

import { algoliaAdmin } from '@/lib/algolia';

async function setupReplicas() {
  const primaryIndex = algoliaAdmin.initIndex('travel_destinations_en');

  // Create replicas for different ranking strategies
  await primaryIndex.setSettings({
    replicas: [
      'travel_destinations_en_by_popularity',
      'travel_destinations_en_by_rating',
      'travel_destinations_en_by_newest',
    ],
  });

  // Configure each replica
  const byPopularity = algoliaAdmin.initIndex(
    'travel_destinations_en_by_popularity'
  );
  await byPopularity.setSettings({
    ranking: [
      'typo',
      'geo',
      'words',
      'filters',
      'proximity',
      'attribute',
      'exact',
      'desc(popularity)',
    ],
  });

  const byRating = algoliaAdmin.initIndex(
    'travel_destinations_en_by_rating'
  );
  await byRating.setSettings({
    ranking: [
      'typo',
      'geo',
      'words',
      'filters',
      'proximity',
      'attribute',
      'exact',
      'desc(rating)',
    ],
  });

  const byNewest = algoliaAdmin.initIndex(
    'travel_destinations_en_by_newest'
  );
  await byNewest.setSettings({
    ranking: [
      'typo',
      'geo',
      'words',
      'filters',
      'proximity',
      'attribute',
      'exact',
      'desc(createdAt)',
    ],
  });
}
```

### Per-Language Indices

```typescript
// Multi-language index setup

interface LanguageConfig {
  code: string;
  name: string;
  index: string;
}

const languages: LanguageConfig[] = [
  { code: 'en', name: 'English', index: 'travel_destinations_en' },
  { code: 'es', name: 'Spanish', index: 'travel_destinations_es' },
  { code: 'fr', name: 'French', index: 'travel_destinations_fr' },
];

export async function syncMultiLanguage(document: SanityDocument) {
  const records = languages.map((lang) => ({
    objectID: `${document._id}_${lang.code}`,
    title: document.title[lang.code] || document.title.en,
    summary: document.summary[lang.code] || document.summary.en,
    description: toPlainText(
      document.description[lang.code] || document.description.en
    ),
    language: lang.code,
    // ... shared fields
    imageUrl: urlFor(document.heroImage).url(),
    slug: `${lang.code}/${document.slug[lang.code]?.current || document.slug.en.current}`,
  }));

  // Save to all language indices
  await Promise.all(
    languages.map((lang) => {
      const index = algoliaAdmin.initIndex(lang.index);
      return index.saveObject(records.find((r) => r.language === lang.code)!);
    })
  );
}
```

---

## Summary

Indexing strategy for the travel agency platform:

- **Schema**: Optimized for search, faceting, and display
- **Sync**: Webhook-driven real-time updates
- **Incremental**: Queue-based batch updates
- **Reindex**: Daily cron jobs for full refresh
- **Multi-Index**: Language replicas and ranking variants

**Key Indexing Decisions:**
- Denormalize data for search performance
- Webhook-driven updates for freshness
- Batch processing for efficiency
- Replica indices for different ranking strategies
- Separate indices per language

---

**Next:** [Part 3: Relevance & Ranking](./SEARCH_ARCHITECTURE_03_RELEVANCE.md) — Scoring algorithms and personalization
