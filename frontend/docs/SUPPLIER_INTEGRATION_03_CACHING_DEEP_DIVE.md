# Supplier Integration 03: Caching Deep Dive

> Complete guide to supplier caching strategies, invalidation, and synchronization

---

## Document Overview

**Series:** Supplier Integration Deep Dive (Document 3 of 4)
**Focus:** Caching — Price caching, inventory caching, invalidation, sync strategies
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Cache Architecture](#cache-architecture)
3. [Cache Strategies by Data Type](#cache-strategies-by-data-type)
4. [Cache Warming](#cache-warming)
5. [Cache Invalidation](#cache-invalidation)
6. [Distributed Caching](#distributed-caching)
7. [Cache Monitoring](#cache-monitoring)
8. [Implementation Reference](#implementation-reference)

---

## Executive Summary

Supplier API calls are expensive and rate-limited. Caching reduces API calls by 80-90%, improves response times from seconds to milliseconds, and ensures availability during supplier outages. The system uses multi-layer caching (Redis CDN) with intelligent invalidation and warming strategies.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Multi-Layer Cache** | Redis for hot data, CDN for static content |
| **Smart TTL** | Different cache durations by data type |
| **Cache Warming** | Pre-populate cache for popular searches |
| **Selective Invalidation** | Invalidate only affected cache keys |
| **Graceful Degradation** | Serve stale cache on supplier failures |

---

## Cache Architecture

### Cache Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CACHE ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REQUEST FLOW                                                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Application                                                          │   │
│  │       │                                                               │   │
│  │       ▼                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ L1: In-Memory Cache (Node.js)                                   │ │   │
│  │  │ - Hot search results                                            │ │   │
│  │  │ - TTL: 30 seconds                                              │ │   │
│  │  │ - Hit rate: ~40%                                                │ │   │
│  │  │ - Size: ~100MB                                                  │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │       │ Miss                                                         │   │
│  │       ▼                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ L2: Redis Cache (Distributed)                                  │ │   │
│  │  │ - All supplier responses                                       │ │   │
│  │  │ - TTL: 5-60 minutes (by data type)                            │ │   │
│  │  │ - Hit rate: ~85%                                                │ │   │
│  │  │ - Size: ~2GB                                                   │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │       │ Miss                                                         │   │
│  │       ▼                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ L3: Supplier API                                                │ │   │
│  │  │ - Real-time data                                               │ │   │
│  │  │ - Rate limited                                                 │ │   │
│  │  │ - Can fail                                                    │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  Response flows back up, caching at each layer                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATIC ASSET CACHING                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Hotel images, static info → CDN (CloudFront/Cloudflare)           │   │
│  │  TTL: 24 hours                                                       │   │
│  │  Invalidation: On manual refresh only                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Key Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CACHE KEY DESIGN                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY FORMAT                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  supplier:{supplierId}:{operation}:{hash(params)}                   │   │
│  │                                                                      │   │
│  │  Examples:                                                           │   │
│  │  - supplier:tbo:search:a1b2c3d4                                    │   │
│  │  - supplier:travelboutique:quote:e5f6g7h8                         │   │
│  │  - supplier:makcorp:inventory:i9j0k1l2                            │   │
│  │  - supplier:tbo:hotel:12345                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HASH STRATEGY                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  hash = md5(sorted_query_params)                                    │   │
│  │                                                                      │   │
│  │  Normalization:                                                     │   │
│  │  - Sort parameters alphabetically                                    │   │
│  │  - Normalize dates (YYYY-MM-DD)                                    │   │
│  │  - Lowercase strings                                               │   │
│  │  - Remove empty/null values                                        │   │
│  │                                                                      │   │
│  │  This ensures equivalent queries have same cache key               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Cache Strategies by Data Type

### Search Results

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SEARCH RESULT CACHING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CACHE CONFIGURATION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TTL: 5 minutes                                                      │   │
│  │  Grace Period: 5 minutes (serve stale while refreshing)             │   │
│  │  Key: supplier:{id}:search:{hash}                                   │   │
│  │                                                                      │   │
│  │  Rationale:                                                           │   │
│  │  - Prices change frequently                                          │   │
│  │  - Availability changes frequently                                    │   │
│  │  - 5 min balance between freshness and API calls                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STALE-WHILE-REFETCH                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Client requests search                                           │   │
│  │  2. Return cached data immediately (age: 3 min)                      │   │
│  │  3. Trigger background refresh                                        │   │
│  │  4. Update cache for next request                                     │   │
│  │                                                                      │   │
│  │  Benefit: Fast response, always have fresh-ish data                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Hotel Details

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOTEL DETAILS CACHING                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CACHE CONFIGURATION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TTL: 60 minutes (static info), 5 minutes (pricing/availability)   │   │
│  │  Key: supplier:{id}:hotel:{hotelId}                                │   │
│  │                                                                      │   │
│  │  Static info (cached longer):                                       │   │
│  │  - Name, description, address                                       │   │
│  │  - Amenities, facilities                                            │   │
│  │  - Images, star rating                                             │   │
│  │                                                                      │   │
│  │  Dynamic info (cached shorter):                                     │   │
│  │  - Pricing, availability                                            │   │
│  │  - Current offers                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Inventory

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INVENTORY CACHING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CACHE CONFIGURATION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TTL: 1 minute                                                       │   │
│  │  Grace Period: 2 minutes                                             │   │
│  │  Key: supplier:{id}:inventory:{hotelId}:{date}                     │   │
│  │                                                                      │   │
│  │  Rationale:                                                           │   │
│  │  - Inventory changes very frequently                                  │   │
│  │  - High cost of overselling (customer disappointment)               │   │
│  │  - Short TTL ensures accuracy                                        │   │
│  │  - Grace period handles temporary supplier issues                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PARTIAL INVALIDATION                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  When booking made:                                                  │   │
│  │  - Invalidate inventory for specific hotel/date/room                │   │
│  │  - Don't invalidate all cache for supplier                           │   │
│  │                                                                      │   │
│  │  Key pattern to invalidate:                                        │   │
│  │  supplier:tbo:inventory:hotel123:2026-12-15:*                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Quote Data

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUOTE CACHING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CACHE CONFIGURATION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TTL: 15 minutes                                                     │   │
│  │  Grace Period: 5 minutes                                             │   │
│  │  Key: supplier:{id}:quote:{quoteId}                                │   │
│  │                                                                      │   │
│  │  Rationale:                                                           │   │
│  │  - Quotes are price commitments                                       │   │
│  │  - Need to be valid for customer decision period                    │   │
│  │  - 15 min balance between validity and freshness                    │   │
│  │  - Extend quote on customer view (reset TTL)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  QUOTE EXTENSION                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  When customer views quote:                                         │   │
│  │  - Extend TTL by 5 minutes (up to max 30 min)                      │   │
│  │  - Log extension for audit                                          │   │
│  │  - Invalidate on booking                                            │   │
│  │                                                                      │   │
│  │  Benefit: Gives customer time to decide without re-fetching         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Cache Warming

### Warming Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CACHE WARMING STRATEGIES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCHEDULED WARMING                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Popular Destinations (every 30 minutes):                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  - Goa: Dec 20-25, 2 adults                                    ││   │
│  │  │  - Goa: Dec 20-25, 2 adults + 1 child                           ││   │
│  │  │  - Kerala: Dec 20-25, 2 adults                                 ││   │
│  │  │  - Rajasthan: Dec 20-25, 2 adults                               ││   │
│  │  │  - Himachal: Dec 20-25, 2 adults                               ││   │
│  │  │  - Dubai: Dec 20-25, 2 adults                                   ││   │
│  │  │  - Thailand: Jan 5-10, 2 adults                                 ││   │
│  │  │  - Singapore: Jan 5-10, 2 adults                                ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                      │   │
│  │  Top Hotels (every hour):                                            │   │
│  │  - Fetch inventory for top 100 hotels by booking volume            │   │
│  │                                                                      │   │
│  │  Benefit: Common searches are always fast (cache hit)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ON-DEMAND WARMING                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  When search is performed:                                          │   │
│  │  - Fetch from requested supplier                                    │   │
│  │  - Also fetch from other suppliers in background                   │   │
│  │  - Cache those results for future                                   │   │
│  │                                                                      │   │
│  │  Benefit: Second search is faster (multiple suppliers already cached)│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PREDICTIVE WARMING                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Based on search patterns:                                          │   │
│  │  - If "Goa, Dec 20-25" is trending (10+ searches/hour)             │   │
│  │  - Reduce warm interval to 10 minutes                               │   │
│  │  - Add related searches to warming schedule                         │   │
│  │                                                                      │   │
│  │  Benefit: Cache is proactively ready for popular searches           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Warming Job

```typescript
// jobs/cache-warming.job.ts
import { CronJob } from 'bull';
import { SupplierOrchestrator } from '../services/supplier-orchestrator.service';

export class CacheWarmingJob {
  private orchestrator: SupplierOrchestrator;
  private redis: Redis;

  async warmPopularSearches() {
    const popularSearches = await this.getPopularSearches();

    for (const search of popularSearches) {
      // Don't wait, let them run in parallel
      this.orchestrator.search(search).catch(err => {
        console.error(`Cache warming failed for ${search.destination}`, err);
      });
    }
  }

  async warmTopHotels() {
    const topHotels = await this.getTopHotels();

    for (const hotelId of topHotels) {
      this.orchestrator.getHotelDetails(hotelId).catch(err => {
        console.error(`Cache warming failed for hotel ${hotelId}`, err);
      });
    }
  }

  private async getPopularSearches(): Promise<SearchParams[]> {
    // From analytics: most searched destinations/dates in last 24 hours
    const key = 'analytics:popular_searches:24h';
    const cached = await this.redis.get(key);

    if (cached) {
      return JSON.parse(cached);
    }

    // Default popular searches if no analytics data
    return [
      { destination: 'Goa', dates: { checkIn: '2026-12-20', checkOut: '2026-12-25' }, guests: { adults: 2 } },
      { destination: 'Kerala', dates: { checkIn: '2026-12-20', checkOut: '2026-12-25' }, guests: { adults: 2 } },
      { destination: 'Dubai', dates: { checkIn: '2026-12-20', checkOut: '2026-12-25' }, guests: { adults: 2 } },
    ];
  }

  schedule() {
    // Warm every 30 minutes
    new CronJob('*/30 * * * *', async () => {
      console.log('Running cache warming job...');
      await this.warmPopularSearches();
      await this.warmTopHotels();
      console.log('Cache warming job completed');
    }).start();

    // Warm top hotels every hour
    new CronJob('0 * * * *', async () => {
      await this.warmTopHotels();
    }).start();
  }
}
```

---

## Cache Invalidation

### Invalidation Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CACHE INVALIDATION STRATEGIES                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIME-BASED (TTL Expiry)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Let cache expire naturally based on TTL                              │   │
│  │                                                                      │   │
│  │  Pros: Simple, no manual invalidation needed                         │   │
│  │  Cons: May serve stale data, inefficient refresh                    │   │
│  │                                                                      │   │
│  │  Best for: Static data (hotel info, images)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  EVENT-BASED (Triggered)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Invalidate on specific events:                                      │   │
│  │  - Booking made → Invalidate inventory                              │   │
│  │  - Price change from supplier → Invalidate pricing                   │   │
│  │  - Supplier notification → Invalidate affected keys                 │   │
│  │                                                                      │   │
│  │  Pros: Always accurate, efficient                                     │   │
│  │  Cons: Complex, requires event handling                              │   │
│  │                                                                      │   │
│  │  Best for: Dynamic data (inventory, pricing)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SELECTIVE INVALIDATION                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Invalidate only affected cache keys:                               │   │
│  │                                                                      │   │
│  │  Example: Hotel 123 booking for Dec 25                               │   │
│  │  - Invalidate: supplier:tbo:inventory:123:2026-12-25               │   │
│  │  - Don't invalidate: Other dates, other hotels                       │   │
│  │                                                                      │   │
│  │  Pros: Efficient, preserves valid cache                              │   │
│  │  Cons: Complex key pattern matching                                   │   │
│  │                                                                      │   │
│  │  Best for: Inventory, pricing by hotel/date                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TAG-BASED                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Add tags to cache keys, invalidate by tag:                          │   │
│  │                                                                      │   │
│  │  Example:                                                           │   │
│  │  - Key: supplier:tbo:search:a1b2c3                                   │   │
│  │  - Tags: ["destination:goa", "dates:2026-12-20"]                    │   │
│  │  - Invalidate: All keys with "destination:goa" tag                 │   │
│  │                                                                      │   │
│  │  Pros: Flexible, expressive                                         │   │
│  │  Cons: Tag management overhead                                       │   │
│  │                                                                      │   │
│  │  Best for: Destination-wide changes, date ranges                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Invalidation Service

```typescript
// services/cache-invalidation.service.ts
import { Redis } from 'ioredis';

export class CacheInvalidationService {
  private redis: Redis;

  async invalidateBooking(booking: Booking) {
    const { supplierId, hotelId, checkIn, checkOut, roomId } = booking;

    // Invalidate inventory for all affected nights
    const dates = this.getDatesInRange(checkIn, checkOut);
    for (const date of dates) {
      const pattern = `supplier:${supplierId}:inventory:${hotelId}:${date}:*`;
      await this.invalidatePattern(pattern);
    }

    // Invalidate search results that include this hotel
    await this.invalidateHotelSearches(hotelId);

    // Invalidate quote if exists
    await this.redis.del(`supplier:${supplierId}:quote:${booking.quoteId}`);
  }

  async invalidateHotelSearches(hotelId: string) {
    // Find all search results containing this hotel
    // This requires tracking which searches returned which hotels
    const pattern = 'supplier:*:search:*';
    const keys = await this.redis.keys(pattern);

    for (const key of keys) {
      const cached = await this.redis.get(key);
      if (cached) {
        const results = JSON.parse(cached);
        const containsHotel = results.some(r => r.hotelId === hotelId);
        if (containsHotel) {
          await this.redis.del(key);
        }
      }
    }
  }

  async invalidatePattern(pattern: string) {
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }

  async invalidateByTag(tag: string) {
    // For tag-based invalidation, maintain index of tags
    const tagKey = `cache:tag:${tag}`;
    const keys = await this.redis.smembers(tagKey);

    if (keys.length > 0) {
      await this.redis.del(...keys);
      await this.redis.del(tagKey);
    }
  }

  private getDatesInRange(start: Date, end: Date): string[] {
    const dates: string[] = [];
    const current = new Date(start);

    while (current <= end) {
      dates.push(current.toISOString().split('T')[0]);
      current.setDate(current.getDate() + 1);
    }

    return dates;
  }
}
```

---

## Distributed Caching

### Redis Cluster Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REDIS CLUSTER SETUP                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Redis Cluster (3 masters, 3 replicas)                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Shard 1      │  │ Shard 2      │  │ Shard 3      │              │   │
│  │  │  Port 7000   │  │ Port 7001    │  │ Port 7002    │              │   │
│  │  │     ┌─────┐  │  │     ┌─────┐  │  │     ┌─────┐  │              │   │
│  │  │     │Rep 1│  │  │     │Rep 2│  │  │     │Rep 3│  │              │   │
│  │  │     └─────┘  │  │     └─────┘  │  │     └─────┘  │              │   │
│  │  │  Port 7003   │  │ Port 7004    │  │ Port 7005    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                                                                      │   │
│  │  Hash tags for supplier-based sharding:                             │   │
│  │  - {supplier:tbo}:data → Shard 1                                   │   │
│  │  - {supplier:travelboutique}:data → Shard 2                        │   │
│  │  - {supplier:makcorp}:data → Shard 3                               │   │
│  │                                                                      │   │
│  │  Benefits:                                                           │   │
│  │  - Even distribution of load                                         │   │
│  │  - Supplier isolation (one supplier's issues don't affect others)   │   │
│  │  - High availability (replicas)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Stampede Prevention

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CACHE STAMPEDE PREVENTION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROBLEM                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Cache expires for popular search                                    │   │
│  │  100 simultaneous requests hit supplier API                         │   │
│  │  → Rate limit exceeded                                               │   │
│  │  → Supplier timeout                                                  │   │
│  │  → All requests fail                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SOLUTION: REFRESH TOKEN                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. First request gets "refresh token"                               │   │
│  │  2. Request proceeds to supplier                                     │   │
│  │  3. Other requests wait for token                                    │   │
│  │  4. First request completes, sets cache                             │   │
│  │  5. Waiting requests get cached result                               │   │
│  │                                                                      │   │
│  │  Implementation (Redis):                                            │   │
│  │  - SET cache:key "REFRESHING" NX EX 30                             │   │
│  │  - Other requests: GET cache:key, wait if "REFRESHING"              │   │
│  │  - On complete: SET cache:value, DEL "REFRESHING"                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Stampede Prevention Implementation

```typescript
// services/cache-stampede.service.ts

export class CacheStampedeService {
  private redis: Redis;

  async getWithRefresh<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T> {
    // Try cache first
    const cached = await this.redis.get(key);
    if (cached && cached !== 'REFRESHING') {
      return JSON.parse(cached);
    }

    // Check if refresh is in progress
    const refreshKey = `${key}:refresh`;
    const refreshing = await this.redis.get(refreshKey);

    if (refreshing) {
      // Wait for refresh to complete
      return this.waitForRefresh(key);
    }

    // Set refresh flag
    await this.redis.set(refreshKey, '1', 'EX', 30);

    try {
      // Fetch fresh data
      const data = await fetcher();

      // Set cache
      await this.redis.setex(key, ttl, JSON.stringify(data));

      // Clear refresh flag
      await this.redis.del(refreshKey);

      // Notify any waiters
      await this.redis.publish(`${key}:updated`, JSON.stringify(data));

      return data;
    } catch (error) {
      // Clear refresh flag on error
      await this.redis.del(refreshKey);
      throw error;
    }
  }

  private async waitForRefresh<T>(key: string): Promise<T> {
    return new Promise((resolve, reject) => {
      const subscriber = this.redis.duplicate();
      const channel = `${key}:updated`;

      const timeout = setTimeout(() => {
        subscriber.unsubscribe(channel);
        reject(new Error('Cache refresh timeout'));
      }, 10000); // 10 second max wait

      subscriber.subscribe(channel, (message) => {
        if (message) {
          clearTimeout(timeout);
          subscriber.unsubscribe(channel);
          resolve(JSON.parse(message));
        }
      });
    });
  }
}
```

---

## Cache Monitoring

### Cache Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CACHE METRICS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PERFORMANCE METRICS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Metric                      │ Target    │ Current    │ Trend        │   │
│  │  ────────────────────────────┼───────────┼───────────┼─────────────│   │
│  │  Hit Rate                    │ >80%      │ 87%       │ ↑           │   │
│  │  Miss Rate                   │ <20%      │ 13%       │ ↓           │   │
│  │  Avg Response Time           │ <50ms     │ 42ms      │ →           │   │
│  │  Cache Size                  │ <2GB      │ 1.8GB     │ ↑           │   │
│  │  Evictions per hour         │ <1000     │ 342       │ →           │   │
│  │  Expired per hour            │ <5000     │ 4,821     │ →           │   │
│  │  Stampede prevented         │ >95%      │ 97%       │ →           │   │
│  │  Stale served                │ <5%       │ 2.3%      │ ↓           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PER-SUPPLIER METRICS                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Supplier   │ Hit Rate │ Misses/Hr │ Avg Latency │ Cache Size       │   │
│  │  ────────────┼──────────┼───────────┼─────────────┼───────────────│   │
│  │  TBO         │ 89%      │ 1,240     │ 38ms         │ 680MB         │   │
│  │  TravelBout  │ 85%      │ 890       │ 45ms         │ 420MB         │   │
│  │  MakCorp     │ 82%      │ 2,100     │ 52ms         │ 550MB         │   │
│  │  Airlines    │ 78%      │ 450       │ 120ms        │ 150MB         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Monitoring Dashboard

```typescript
// services/cache-monitor.service.ts

export class CacheMonitorService {
  async getMetrics(): Promise<CacheMetrics> {
    const info = await this.redis.info('stats');
    const keyspace = await this.redis.info('keyspace');

    return {
      hitRate: this.calculateHitRate(info),
      memory: this.parseMemoryInfo(info),
      keys: this.parseKeyspaceInfo(keyspace),
      operations: this.parseOperations(info),
      perSupplier: await this.getPerSupplierMetrics(),
    };
  }

  async getPerSupplierMetrics(): Promise<Record<string, SupplierCacheMetrics>> {
    const suppliers = ['tbo', 'travelboutique', 'makcorp'];
    const metrics: Record<string, SupplierCacheMetrics> = {};

    for (const supplier of suppliers) {
      const pattern = `supplier:${supplier}:*`;
      const keys = await this.redis.keys(pattern);

      let totalSize = 0;
      let hitCount = 0;
      let missCount = 0;

      for (const key of keys.slice(0, 100)) { // Sample 100 keys
        const info = await this.redis.debug('object', key) as any;
        totalSize += info SerializedLength || 0;
      }

      // Get stats from cache stats keys
      const statsKey = `cache:stats:${supplier}`;
      const stats = await this.redis.hgetall(statsKey);
      hitCount = parseInt(stats.hits || '0');
      missCount = parseInt(stats.misses || '0');

      metrics[supplier] = {
        keyCount: keys.length,
        estimatedSize: totalSize,
        hitRate: hitCount / (hitCount + missCount),
        hitCount,
        missCount,
      };
    }

    return metrics;
  }
}
```

---

## Summary

The Supplier Caching system provides:

- **Multi-Layer Cache**: In-memory + Redis + CDN for optimal performance
- **Smart TTL**: Different cache durations by data type
- **Cache Warming**: Pre-populate popular searches
- **Selective Invalidation**: Invalidate only affected keys
- **Stampede Prevention**: Refresh tokens prevent simultaneous API calls
- **Distributed Caching**: Redis cluster for high availability

This completes the Caching Deep Dive. The next document covers Error Handling and resilience.

---

**Related Documents:**
- [Technical Deep Dive](./SUPPLIER_INTEGRATION_01_TECHNICAL_DEEP_DIVE.md) — Architecture
- [Data Deep Dive](./SUPPLIER_INTEGRATION_02_DATA_DEEP_DIVE.md) — Data models
- [Error Handling Deep Dive](./SUPPLIER_INTEGRATION_04_ERROR_HANDLING_DEEP_DIVE.md) — Fallback patterns

**Master Index:** [Supplier Integration Deep Dive Master Index](./SUPPLIER_INTEGRATION_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
