# Content Management Part 1: CMS Architecture

> Headless CMS evaluation, content architecture, and implementation strategy

**Series:** Content Management
**Next:** [Part 2: Content Modeling](./CONTENT_MANAGEMENT_02_MODELING.md)

---

## Table of Contents

1. [CMS Evaluation](#cms-evaluation)
2. [Architecture Overview](#architecture-overview)
3. [Content Strategy](#content-strategy)
4. [Multi-Tenant Content](#multi-tenant-content)
5. [Migration Strategy](#migration-strategy)

---

## CMS Evaluation

### Headless CMS Options

```typescript
// CMS comparison matrix

interface CMSComparison {
  sanity: {
    strengths: ['Real-time collaboration', 'Flexible schemas', 'Great DX'];
    weaknesses: ['Query complexity', 'Learning curve'];
    pricing: 'Free tier + usage-based';
    bestFor: 'Custom content models, real-time features';
  };

  contentful: {
    strengths: ['Mature platform', 'Rich ecosystem', 'Good docs'];
    weaknesses: ['Rigid schemas', 'Expensive at scale'];
    pricing: 'Free tier + usage-based';
    bestFor: 'Standard content models, enterprise';
  };

  strapi: {
    strengths: ['Self-hosted', 'Open source', 'Admin panel'];
    weaknesses: ['Infrastructure overhead', 'Plugin complexity'];
    pricing: 'Free (self-hosted)';
    bestFor: 'Full control, custom hosting';
  };
}
```

### Our Choice: Sanity.io

```typescript
// Sanity.io architecture

interface SanityArchitecture {
  // Core components
  core: {
    studio: 'React-based content editing interface';
    api: 'GROQ query language + REST API';
    cdn: 'Global edge CDN built-in';
    realtime: 'Live collaboration and updates';
  };

  // Key features
  features: {
    schemas: 'Code-first schema definitions';
    references: 'Cross-document references';
    arrays: 'Reusable content blocks';
    i18n: 'Built-in localization';
    patches: 'Optimistic updates';
  };

  // Deployment model
  deployment: {
    hosting: 'SaaS (sanity.io)';
    data: 'Multi-region replication';
    studio: 'Deployed to Vercel/Netlify';
  };
}
```

### Sanity Project Structure

```typescript
// Sanity studio configuration

// sanity.config.ts
import { defineConfig } from 'sanity';
import { structureTool } from 'sanity/structure';
import { visionTool } from '@sanity/vision';
import { schemaTypes } from './schemas';

export default defineConfig({
  projectId: 'your-project-id',
  dataset: 'production',

  plugins: [
    structureTool(),
    visionTool(),
  ],

  schema: {
    types: schemaTypes,
  },
});

// schemas/index.ts
import { schema } from './schemas/destination';
import { schema } from './schemas/accommodation';
import { schema } from './schemas/deal';
import { schema } from './schemas/blogPost';
import { schema } from './schemas/page';

export const schemaTypes = [
  destination,
  accommodation,
  deal,
  blogPost,
  page,
  // ... more schemas
];
```

---

## Architecture Overview

### Content Flow

```typescript
// Content delivery architecture

interface ContentArchitecture {
  // Content creation flow
  creation: {
    1: 'Editor creates content in Sanity Studio';
    2: 'Content saved to Sanity API';
    3: 'Webhook triggered to frontend';
    4: 'Frontend revalidates cache';
    5: 'New content available on CDN';
  };

  // Content delivery flow
  delivery: {
    1: 'User requests page';
    2: 'Frontend checks edge cache (Vercel)';
    3: 'If miss, query Sanity API';
    4: 'Sanity serves from CDN';
    5: 'Frontend caches response';
  };
}
```

### Frontend Integration

```typescript
// Sanity client configuration

import { createClient } from 'next-sanity';

export const client = createClient({
  projectId: process.env.NEXT_PUBLIC_SANITY_PROJECT_ID!,
  dataset: process.env.NEXT_PUBLIC_SANITY_DATASET!,
  apiVersion: '2025-01-01',
  useCdn: true, // Use CDN for faster reads
  stega: {
    enabled: process.env.NEXT_PUBLIC_VERCEL_ENV === 'preview',
    studioUrl: '/studio',
  },
});

// GROQ query helper
export async function sanityFetch<T>({
  query,
  params = {},
  tags = [],
}: {
  query: string;
  params?: Record<string, unknown>;
  tags?: string[];
}): Promise<T> {
  return client.fetch<T>(
    query,
    params,
    {
      cache: 'force-cache', // or 'no-store' for real-time
      next: { tags },
    }
  );
}
```

### Content Fetching Patterns

```typescript
// Common query patterns

import { groq } from 'next-sanity';

// Get single document by slug
export async function getDestination(slug: string) {
  return sanityFetch<Destination>({
    query: groq`*[
      _type == "destination" &&
      slug.current == $slug &&
      !(_id in path("drafts.**"))
    ][0]{
      _id,
      title,
      slug,
      description,
      image,
      "imageUrl": image.asset->url,
      country,
      region,
      coordinates,
      attractions,
      bestTimeToVisit,
      localInfo,
    }`,
    params: { slug },
    tags: ['destination'],
  });
}

// Get all destinations
export async function getAllDestinations() {
  return sanityFetch<Destination[]>({
    query: groq`*[
      _type == "destination" &&
      !(_id in path("drafts.**"))
    ]|order(title asc){
      _id,
      title,
      slug,
      "imageUrl": image.asset->url,
      country,
    }`,
    tags: ['destination'],
  });
}

// Get destinations with pagination
export async function getDestinationsPage(
  page = 1,
  limit = 12
) {
  const start = (page - 1) * limit;

  return sanityFetch<{
    items: Destination[];
    total: number;
  }>({
    query: groq`{
      "items": *[
        _type == "destination" &&
        !(_id in path("drafts.**"))
      ]|order(title asc)[${start}...${start + limit}]{
        _id,
        title,
        slug,
        "imageUrl": image.asset->url,
        country,
      },
      "total": count(*[
        _type == "destination" &&
        !(_id in path("drafts.**"))
      ]),
    }`,
    tags: ['destination'],
  });
}
```

---

## Content Strategy

### Content vs Database

```typescript
// When to use CMS vs Database

interface ContentDecision {
  // Use CMS for:
  cms: [
    'Marketing content (landing pages, blogs)',
    'User-facing descriptions (destinations, hotels)',
    'Frequently changing content (deals, offers)',
    'Multi-language content',
    'Content managed by non-developers',
    'SEO-optimized pages',
  ];

  // Use Database for:
  database: [
    'Transactional data (bookings, payments)',
    'User-generated content (reviews, messages)',
    'Application data (users, permissions)',
    'Highly relational data',
    'Real-time operational data',
    'Complex business logic',
  ];

  // Hybrid approach:
  hybrid: [
    'Store reference IDs in CMS',
    'Join with database at runtime',
    'Use CMS for display data',
    'Use database for operations',
  ];
}
```

### Content Types

```typescript
// Core content types

interface ContentTypes {
  // Destination content
  destination: {
    fields: [
      'title',
      'slug',
      'description',
      'heroImage',
      'gallery',
      'country',
      'region',
      'coordinates',
      'attractions',
      'bestTimeToVisit',
      'localInfo',
      'travelAdvisory',
    ];
    localization: 'Full content translated';
    seo: 'Title, description, og:image';
  };

  // Accommodation content
  accommodation: {
    fields: [
      'name',
      'slug',
      'description',
      'images',
      'destination',
      'address',
      'amenities',
      'roomTypes',
      'policies',
      'rating',
    ];
    localization: 'Name, description, policies';
    seo: 'Name, description, image gallery';
  };

  // Deal/Promotion content
  deal: {
    fields: [
      'title',
      'slug',
      'description',
      'promoCode',
      'discount',
      'validFrom',
      'validTo',
      'destinations',
      'terms',
      'bannerImage',
    ];
    localization: 'Title, description, terms';
    seo: 'Title, description';
  };
}
```

---

## Multi-Tenant Content

### Agency Content Isolation

```typescript
// Multi-tenant content strategy

interface MultiTenantContent {
  // Approach 1: Filter by agency
  filter: {
    implementation: 'Add agency_id field to all documents';
    query: '*[_type == "destination" && agency_id == $agencyId]';
    pros: ['Simple', 'Single dataset'];
    cons: ['Risk of data leakage', 'Query overhead'];
  };

  // Approach 2: Separate datasets (RECOMMENDED)
  datasets: {
    implementation: 'Each agency gets own dataset';
    datasets: [
      'agency-abc-production',
      'agency-abc-staging',
      'agency-xyz-production',
    ];
    pros: ['Complete isolation', 'Clean separation'];
    cons: ['Multiple configs', 'Cost scaling'];
  };

  // Approach 3: Separate projects
  projects: {
    implementation: 'Each agency gets own Sanity project';
    pros: ['Full isolation', 'Independent billing'];
    cons: ['Management overhead', 'No shared content'];
  };
}

// Selected: Separate datasets with shared schema
export function getClientForAgency(agencyId: string) {
  return createClient({
    projectId: process.env.NEXT_PUBLIC_SANITY_PROJECT_ID!,
    dataset: `agency-${agencyId}-production`,
    useCdn: true,
  });
}
```

### Shared vs Agency-Specific Content

```typescript
// Content ownership model

interface ContentOwnership {
  // Global content (platform-managed)
  global: {
    owner: 'platform';
    examples: ['Popular destinations', 'Featured deals', 'Blog content'];
    access: 'Read-only for agencies';
    dataset: 'platform-content';
  };

  // Agency content (agency-managed)
  agency: {
    owner: 'agency';
    examples: ['Custom deals', 'Agency info', 'Branded pages'];
    access: 'Full CRUD for agency';
    dataset: 'agency-{id}-production';
  };

  // User content (user-managed)
  user: {
    owner: 'user';
    examples: ['Reviews', 'Travel stories', 'Photos'];
    access: 'Not in CMS - use database';
    dataset: 'N/A (database)';
  };
}
```

---

## Migration Strategy

### Content Audit

```typescript
// Content audit process

interface ContentAudit {
  phases: {
    1: 'Inventory existing content';
    2: 'Classify by type and priority';
    3: 'Map to new schema';
    4: 'Identify gaps and redundancies';
    5: 'Plan migration order';
  };

  // Content inventory template
  inventory: {
    id: 'Unique identifier';
    type: 'Content type (destination, hotel, etc.)';
    source: 'Current location (DB, CMS, files)';
    priority: 'Migration priority (high/medium/low)';
    status: 'Migration status';
    dependencies: 'Related content';
  };
}
```

### Migration Scripts

```typescript
// Content migration utilities

import { createClient } from '@sanity/client';
import { BATCH_SIZE } from './config';

const migrationClient = createClient({
  projectId: process.env.SANITY_PROJECT_ID!,
  dataset: process.env.SANITY_DATASET!,
  token: process.env.SANITY_WRITE_TOKEN!,
  useCdn: false,
});

export async function migrateDestinations(
  sourceData: SourceDestination[]
) {
  const batches = chunk(sourceData, BATCH_SIZE);

  for (const [index, batch] of batches.entries()) {
    const documents = batch.map((item) => ({
      _type: 'destination',
      _id: `destination-${item.id}`,
      title: item.name,
      slug: { current: slugify(item.name) },
      description: item.description,
      country: item.country,
      region: item.region,
      // Map remaining fields...
    }));

    const transaction = documents.reduce((tx, doc) => {
      return tx.create(doc);
    }, migrationClient.transaction());

    await transaction.commit();

    console.log(`Migrated batch ${index + 1}/${batches.length}`);
  }
}

export async function verifyMigration() {
  const sourceCount = await getSourceCount();
  const targetCount = await migrationClient.fetch(
    'count(*[_type == "destination"])'
  );

  if (sourceCount !== targetCount) {
    throw new Error(
      `Migration verification failed: ${sourceCount} source vs ${targetCount} target`
    );
  }

  console.log('Migration verified successfully');
}
```

### Rollback Strategy

```typescript
// Migration rollback

interface RollbackPlan {
  preMigration: {
    action: 'Create dataset backup';
    command: 'sanity dataset export';
  };

  duringMigration: {
    action: 'Keep source data read-only';
    reason: 'Can rollback if issues found';
  };

  postMigration: {
    action: 'Monitor for issues';
    duration: '7 days';
    rollback: 'Restore from backup if critical issues';
  };
}

export async function createBackup(dataset: string) {
  const timestamp = new Date().toISOString();
  const filename = `${dataset}-backup-${timestamp}.tar.gz`;

  // Sanity CLI backup
  execSync(`sanity dataset export ${dataset} ${filename}`);

  // Upload to S3 for safekeeping
  await uploadToS3(filename, `backups/${filename}`);

  return filename;
}
```

---

## Summary

CMS architecture for the travel agency platform:

- **Platform**: Sanity.io for headless CMS
- **Architecture**: API-first, CDN-delivered content
- **Multi-tenant**: Separate datasets per agency
- **Content Strategy**: CMS for marketing, DB for transactions
- **Migration**: Phased approach with verification

**Key Decisions:**
- Sanity.io for flexible schemas and real-time collaboration
- Separate datasets for agency content isolation
- Global content shared across agencies
- Hybrid approach: CMS + Database

---

**Next:** [Part 2: Content Modeling](./CONTENT_MANAGEMENT_02_MODELING.md) — Schema design, relationships, and field types
