# Content Management Part 3: Content Delivery

> CDN integration, caching strategies, and edge delivery

**Series:** Content Management
**Previous:** [Part 2: Content Modeling](./CONTENT_MANAGEMENT_02_MODELING.md)
**Next:** [Part 4: Content Workflows](./CONTENT_MANAGEMENT_04_WORKFLOWS.md)

---

## Table of Contents

1. [Content API Patterns](#content-api-patterns)
2. [CDN Integration](#cdn-integration)
3. [Caching Strategies](#caching-strategies)
4. [Image Optimization](#image-optimization)
5. [Real-Time Updates](#real-time-updates)
6. [Edge Functions](#edge-functions)

---

## Content API Patterns

### Server-Side Fetching

```typescript
// Next.js server component fetching

import { client } from '@/lib/sanity/client';
import { groq } from 'next-sanity';

// Server component - direct fetch
export default async function DestinationPage({
  params,
}: {
  params: { slug: string };
}) {
  const destination = await client.fetch<
    Destination | null
  >(
    groq`*[
      _type == "destination" &&
      slug.current == $slug
    ][0]`,
    { slug: params.slug },
    {
      // Next.js caching
      next: {
        revalidate: 3600, // 1 hour
        tags: ['destination', params.slug],
      },
    }
  );

  if (!destination) {
    notFound();
  }

  return <DestinationView destination={destination} />;
}
```

### Client-Side Fetching

```typescript
// Client component fetching

'use client';

import { useEffect, useState } from 'react';
import { client } from '@/lib/sanity/client';
import { groq } from 'next-sanity';

export function DestinationSearch() {
  const [results, setResults] = useState<Destination[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const search = async () => {
      setLoading(true);
      try {
        const data = await client.fetch(
          groq`*[
            _type == "destination" &&
            title match $query
          ]|order(title asc){
            _id,
            title,
            slug,
            "imageUrl": heroImage.asset->url
          }`,
          { query: 'Paris' }
        );
        setResults(data);
      } finally {
        setLoading(false);
      }
    };

    search();
  }, []);

  return <DestinationList results={results} loading={loading} />;
}
```

### Combined Fetching Pattern

```typescript
// Hybrid: Server fetch + client hydration

import { draftMode } from 'next/headers';
import { client } from '@/lib/sanity/client';
import { groq } from 'next-sanity';

// Server component fetches initial data
export default async function DestinationPage({
  params,
}: {
  params: { slug: string };
}) {
  const { isEnabled } = draftMode();

  const destination = await client.fetch({
    query: groq`*[_type == "destination" && slug.current == $slug][0]`,
    params: { slug: params.slug },
    // Use different cache strategy for drafts
    config: isEnabled
      ? { cache: 'no-store' }
      : {
          next: {
            revalidate: 3600,
            tags: ['destination', params.slug],
          },
        },
  });

  return (
    <>
      <DestinationView destination={destination} />
      {/* Client component for real-time updates */}
      <DestinationLivePreview id={destination._id} />
    </>
  );
}
```

---

## CDN Integration

### Vercel Edge Network

```typescript
// Vercel edge caching configuration

import { unstable_cache } from 'next/cache';

// Cache function for repeated queries
export const getDestination = unstable_cache(
  async (slug: string) => {
    return client.fetch(
      groq`*[_type == "destination" && slug.current == $slug][0]`,
      { slug }
    );
  },
  ['destination'], // Cache key prefix
  {
    revalidate: 3600, // 1 hour
    tags: ['destination'],
  }
);

// Usage in server component
export default async function Page({ params }: { params: { slug: string } }) {
  const destination = await getDestination(params.slug);
  return <DestinationView destination={destination} />;
}
```

### Sanity CDN Configuration

```typescript
// Sanity client with CDN

import { createClient } from 'next-sanity';

export const client = createClient({
  projectId: process.env.NEXT_PUBLIC_SANITY_PROJECT_ID!,
  dataset: process.env.NEXT_PUBLIC_SANITY_DATASET!,
  apiVersion: '2025-01-01',

  // Enable CDN for faster reads
  useCdn: true,

  // Edge network
  perspective: 'published',

  // Stega for live preview
  stega: {
    enabled: process.env.NEXT_PUBLIC_VERCEL_ENV === 'preview',
    studioUrl: '/studio',
  },
});

// Separate client for mutations (no CDN)
export const writeClient = createClient({
  projectId: process.env.SANITY_PROJECT_ID!,
  dataset: process.env.SANITY_DATASET!,
  apiVersion: '2025-01-01',
  useCdn: false, // Disable CDN for writes
  token: process.env.SANITY_WRITE_TOKEN!,
});
```

### Cache Tags

```typescript
// Next.js cache tags for invalidation

import { revalidateTag } from 'next/cache';

// Fetch with tags
export async function getAllDestinations() {
  return client.fetch(
    groq`*[_type == "destination"]|order(title asc)`,
    {},
    {
      next: {
        tags: ['destinations'], // Tag for revalidation
      },
    }
  );
}

// Revalidate on webhook
export async function POST(request: Request) {
  const body = await request.json();

  if (body._type === 'destination') {
    // Revalidate specific destination
    revalidateTag(`destination-${body.slug.current}`);

    // Also revalidate list
    revalidateTag('destinations');
  }

  return Response.json({ revalidated: true });
}
```

---

## Caching Strategies

### Cache Strategy Hierarchy

```typescript
// Caching strategy by content type

interface CacheStrategy {
  // Static content - long cache
  static: {
    types: ['About page', 'Terms of service', 'Privacy policy'];
    strategy: 'ISR with 1-day revalidation';
    implementation: 'revalidate: 86400';
  };

  // Dynamic content - medium cache
  dynamic: {
    types: ['Destinations', 'Accommodations', 'Blog posts'];
    strategy: 'ISR with 1-hour revalidation';
    implementation: 'revalidate: 3600, tags';
  };

  // Time-sensitive - short cache
  timeSensitive: {
    types: ['Deals', 'Featured content'];
    strategy: 'ISR with 5-minute revalidation';
    implementation: 'revalidate: 300';
  };

  // Real-time - no cache
  realtime: {
    types: ['User-generated content', 'Live data'];
    strategy: 'SSR or no-store';
    implementation: 'cache: "no-store"';
  };
}
```

### On-Demand Revalidation

```typescript
// Webhook-driven revalidation

import { revalidatePath, revalidateTag } from 'next/cache';
import { type NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Verify webhook signature
    const signature = request.headers.get('sanity-webhook-signature');
    if (!verifySignature(body, signature)) {
      return Response.json({ error: 'Invalid signature' }, { status: 401 });
    }

    // Revalidate based on content type
    switch (body._type) {
      case 'destination':
        revalidateTag(`destination-${body.slug.current}`);
        revalidateTag('destinations');
        revalidatePath('/destinations');
        revalidatePath(`/destinations/${body.slug.current}`);
        break;

      case 'accommodation':
        revalidateTag(`accommodation-${body.slug.current}`);
        revalidatePath(`/accommodations/${body.slug.current}`);
        break;

      case 'deal':
        revalidateTag('deals');
        revalidatePath('/deals');
        revalidatePath('/'); // Homepage if featured
        break;

      case 'blogPost':
        revalidateTag(`blog-${body.slug.current}`);
        revalidateTag('blog');
        revalidatePath('/blog');
        revalidatePath(`/blog/${body.slug.current}`);
        break;
    }

    return Response.json({ revalidated: true, now: Date.now() });
  } catch (err) {
    return Response.json(
      { error: 'Revalidation failed' },
      { status: 500 }
    );
  }
}

function verifySignature(body: unknown, signature: string | null): boolean {
  if (!signature) return false;

  const secret = process.env.SANITY_WEBHOOK_SECRET!;
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(JSON.stringify(body)).digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(`sha256=${digest}`)
  );
}
```

### Stale-While-Revalidate

```typescript
// SWR pattern for content

import useSWR from 'swr';

const fetcher = (query: string, params: Record<string, unknown>) =>
  client.fetch(query, params);

export function useDestination(slug: string) {
  const { data, error, isLoading, mutate } = useSWR(
    ['destination', slug],
    () => fetcher(
      groq`*[_type == "destination" && slug.current == $slug][0]`,
      { slug }
    ),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      dedupingInterval: 60000, // Don't refetch within 1 minute
      refreshInterval: 0, // No auto-refresh
    }
  );

  return {
    destination: data,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}
```

---

## Image Optimization

### Sanity Image Builder

```typescript
// Sanity image URL builder

import { urlFor } from '@/lib/sanity/image';

import { createClient } from 'next-sanity';
import imageUrlBuilder from '@sanity/image-url';

const client = createClient({
  projectId: process.env.NEXT_PUBLIC_SANITY_PROJECT_ID!,
  dataset: process.env.NEXT_PUBLIC_SANITY_DATASET!,
});

export const urlFor = (source: unknown) =>
  imageUrlBuilder(client).image(source);

// Usage in component
export function DestinationHero({ image }: { image: SanityImage }) {
  const imageUrl = urlFor(image)
    .width(1920)
    .height(1080)
    .fit('crop')
    .auto('format')
    .quality(80)
    .url();

  return (
    <div
      className="hero"
      style={{ backgroundImage: `url(${imageUrl})` }}
    />
  );
}
```

### Next.js Image Component

```typescript
// Next.js Image integration with Sanity

import Image from 'next/image';
import { urlFor } from '@/lib/sanity/image';

interface SanityImageProps {
  image: SanityImage;
  width?: number;
  height?: number;
  priority?: boolean;
}

export function SanityImage({
  image,
  width = 800,
  height = 600,
  priority = false,
}: SanityImageProps) {
  const imageUrl = urlFor(image)
    .width(width)
    .height(height)
    .fit('crop')
    .auto('format')
    .quality(80)
    .url();

  return (
    <Image
      src={imageUrl}
      alt={image.alt || ''}
      width={width}
      height={height}
      priority={priority}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      // Enable blur placeholder
      placeholder="blur"
      blurDataURL={urlFor(image).width(20).quality(20).url()}
    />
  );
}
```

### Responsive Image Gallery

```typescript
// Responsive image gallery

import Image from 'next/image';
import { urlFor } from '@/lib/sanity/image';

export function DestinationGallery({
  images,
}: {
  images: SanityImage[];
}) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {images.map((image, index) => (
        <div key={image._key || index} className="aspect-square">
          <Image
            src={urlFor(image).width(400).height(400).fit('crop').url()}
            alt={image.alt || ''}
            width={400}
            height={400}
            sizes="(max-width: 768px) 50vw, 25vw"
            // Lazy load all but first image
            priority={index === 0}
            placeholder="blur"
            blurDataURL={urlFor(image).width(20).quality(20).url()}
          />
        </div>
      ))}
    </div>
  );
}
```

---

## Real-Time Updates

### Sanity Listen API

```typescript
// Real-time content updates

import { useEffect } from 'react';
import { client } from '@/lib/sanity/client';

export function useLiveDestination(slug: string) {
  const [destination, setDestination] = useState<Destination | null>(null);

  useEffect(() => {
    // Initial fetch
    client
      .fetch(
        groq`*[_type == "destination" && slug.current == $slug][0]`,
        { slug }
      )
      .then(setDestination);

    // Subscribe to changes
    const subscription = client
      .listen(
        groq`*[_type == "destination" && slug.current == $slug][0]`,
        { slug }
      )
      .subscribe((update) => {
        if (update.result) {
          setDestination(update.result);
        }
      });

    return () => subscription.unsubscribe();
  }, [slug]);

  return destination;
}
```

### Live Preview

```typescript
// Draft mode for content preview

import { defineLivePreviewConfig } from 'next-sanity/drupal';

export const defineConfig = defineLivePreviewConfig({
  token: process.env.SANITY_API_READ_TOKEN!,
  studioUrl: '/studio',
});

// In page component
import { draftMode } from 'next/headers';

export default async function Page({ params }: { params: { slug: string } }) {
  const { isEnabled } = draftMode();

  const destination = await client.fetch({
    query: groq`*[_type == "destination" && slug.current == $slug][0]`,
    params: { slug: params.slug },
    // Include drafts in preview mode
    perspective: isEnabled ? 'previewDrafts' : 'published',
    // No cache in preview
    cache: isEnabled ? 'no-store' : 'force-cache',
  });

  return <DestinationView destination={destination} />;
}
```

---

## Edge Functions

### Edge Content Fetching

```typescript
// Edge function for content delivery

import { NextRequest, NextResponse } from 'next/server';
import { client } from '@/lib/sanity/client';
import { groq } from 'next-sanity';

export const runtime = 'edge';

export async function GET(
  request: NextRequest,
  { params }: { params: { slug: string } }
) {
  // Check cache header
  const cacheHeader = request.headers.get('x-vercel-cache');

  // Fetch from Sanity
  const destination = await client.fetch(
    groq`*[_type == "destination" && slug.current == $slug][0]{
      _id,
      title,
      slug,
      summary,
      "imageUrl": heroImage.asset->url,
      country
    }`,
    { slug: params.slug }
  );

  if (!destination) {
    return NextResponse.json(
      { error: 'Not found' },
      { status: 404 }
    );
  }

  // Cache at edge
  return NextResponse.json(destination, {
    headers: {
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      'Vercel-CDN-Cache-Control': 'max-age=3600',
    },
  });
}
```

### Regional Content

```typescript
// Geo-aware content delivery

import { NextRequest, NextResponse } from 'next/server';
import { client } from '@/lib/sanity/client';
import { groq } from 'next-sanity';

export const runtime = 'edge';

export async function GET(request: NextRequest) {
  // Get user's country from request
  const country = request.geo?.country || 'US';

  // Fetch regional content
  const destinations = await client.fetch(
    groq`*[
      _type == "destination" &&
      $country in popularFor[]
    ]|order(popularity desc)[0...10]{
      _id,
      title,
      slug,
      "imageUrl": heroImage.asset->url
    }`,
    { country }
  );

  return NextResponse.json(destinations, {
    headers: {
      'Cache-Control': 'public, s-maxage=3600',
      'X-Content-Region': country,
    },
  });
}
```

---

## Summary

Content delivery for the travel agency platform:

- **API Patterns**: Server-side, client-side, hybrid fetching
- **CDN**: Vercel Edge Network + Sanity CDN
- **Caching**: ISR with tags, on-demand revalidation
- **Images**: Next.js Image with Sanity URL builder
- **Real-Time**: Listen API for live updates
- **Edge**: Regional content, geo-aware delivery

**Key Delivery Decisions:**
- ISR for most content (1-hour revalidation)
- Cache tags for targeted invalidation
- Webhook-driven revalidation
- Edge functions for geo-routing
- Draft mode for live preview

---

**Next:** [Part 4: Content Workflows](./CONTENT_MANAGEMENT_04_WORKFLOWS.md) — Editorial workflows, approvals, and versioning
