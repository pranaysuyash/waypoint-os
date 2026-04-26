# Performance & Scalability Part 3: Backend Performance

> Database optimization, caching strategies, and API performance

**Series:** Performance & Scalability
**Previous:** [Part 2: Frontend Optimization](./PERFORMANCE_SCALABILITY_02_FRONTEND.md)
**Next:** [Part 4: Scalability Patterns](./PERFORMANCE_SCALABILITY_04_SCALING.md)

---

## Table of Contents

1. [Database Optimization](#database-optimization)
2. [Query Optimization](#query-optimization)
3. [Caching Strategies](#caching-strategies)
4. [API Performance](#api-performance)
5. [Background Jobs](#background-jobs)
6. [Connection Management](#connection-management)

---

## Database Optimization

### Indexing Strategy

```sql
-- Indexes for common queries

-- Primary lookups
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_created_at ON bookings(created_at DESC);

-- Composite indexes for filtered queries
CREATE INDEX idx_bookings_user_status ON bookings(user_id, status);
CREATE INDEX idx_bookings_status_dates ON bookings(status, dates->>'start');

-- Covering indexes for hot queries
CREATE INDEX idx_bookings_listing ON bookings(user_id, status, destination, total_price)
  INCLUDE (id, created_at);

-- Partial indexes for specific conditions
CREATE INDEX idx_bookings_active ON bookings(user_id, dates)
  WHERE status IN ('pending', 'confirmed');

-- JSON indexes for structured data
CREATE INDEX idx_bookings_destination ON bookings USING GIN (destination gin_trgm_ops);
```

### Query Patterns

```typescript
// db/queries/bookings.ts

import { db } from '@/db';
import { bookings, users, payments } from '@/db/schema';
import { eq, and, gte, lte, desc, sql } from 'drizzle-orm';

// Efficient pagination with cursor
export async function getBookingsCursor(
  userId: string,
  limit: number,
  cursor?: string
) {
  let query = db
    .select()
    .from(bookings)
    .where(eq(bookings.userId, userId))
    .orderBy(desc(bookings.createdAt))
    .limit(limit + 1); // Fetch one extra to check for more

  if (cursor) {
    const cursorDate = new Date(parseInt(cursor)).toISOString();
    query = query.where(lte(bookings.createdAt, cursorDate));
  }

  const results = await query;

  const hasMore = results.length > limit;
  const items = hasMore ? results.slice(0, limit) : results;

  return {
    items,
    nextCursor: hasMore ? items[items.length - 1].createdAt : null,
  };
}

// Efficient count with estimate for large tables
export async function getBookingCountEstimate(userId: string) {
  const result = await db
    .select({ count: sql<number>`count(*)` })
    .from(bookings)
    .where(eq(bookings.userId, userId));

  return result[0]?.count || 0;
}

// Batch loading to avoid N+1
export async function getBookingsWithRelations(bookingIds: string[]) {
  return db.query.bookings.findMany({
    where: eq(bookings.id, sql.placeholder('id')),
    with: {
      user: {
        columns: { id: true, name: true, email: true },
      },
      payments: {
        columns: { id: true, amount: true, status: true },
        limit: 1,
        orderBy: [desc(payments.createdAt)],
      },
    },
  });
}

// Aggregation query with materialized view refresh
export async function getBookingStats(userId: string) {
  return db
    .select({
      total: sql<number>`sum(${bookings.totalPrice})`,
      count: sql<number>`count(*)`,
      pending: sql<number>`count(*) FILTER (WHERE ${bookings.status} = 'pending')`,
      confirmed: sql<number>`count(*) FILTER (WHERE ${bookings.status} = 'confirmed')`,
    })
    .from(bookings)
    .where(eq(bookings.userId, userId));
}
```

### Materialized Views

```sql
-- Materialized view for booking statistics
CREATE MATERIALIZED VIEW booking_stats_mv AS
SELECT
  user_id,
  COUNT(*) as total_bookings,
  SUM(total_price) as total_spent,
  COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
  COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed_count,
  COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_count,
  MAX(created_at) as last_booking_at
FROM bookings
GROUP BY user_id;

-- Indexes for the materialized view
CREATE UNIQUE INDEX idx_booking_stats_user ON booking_stats_mv(user_id);
CREATE INDEX idx_booking_stats_last_booking ON booking_stats_mv(last_booking_at DESC);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_booking_stats()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY booking_stats_mv;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh every 5 minutes
-- (Use pg_cron or external scheduler)
```

---

## Query Optimization

### N+1 Prevention

```typescript
// ❌ Bad: N+1 query problem

async function getUserBookingsBad(userId: string) {
  const userBookings = await db
    .select()
    .from(bookings)
    .where(eq(bookings.userId, userId));

  // N+1: Separate query for each booking
  for (const booking of userBookings) {
    booking.payments = await db
      .select()
      .from(payments)
      .where(eq(payments.bookingId, booking.id));
  }

  return userBookings;
}

// ✅ Good: Single query with joins

async function getUserBookingsGood(userId: string) {
  return db.query.bookings.findMany({
    where: eq(bookings.userId, userId),
    with: {
      payments: true, // Eager load
      user: {
        columns: { id: true, name: true, email: true },
      },
    },
  });
}

// ✅ Better: DataLoader pattern for batch loading

import { DataLoader } from 'dataloader';

const paymentLoader = new DataLoader(async (bookingIds: string[]) => {
  const payments = await db
    .select()
    .from(payments)
    .where(sql`${payments.bookingId} = ANY(${bookingIds})`);

  // Group by booking ID
  const grouped = new Map<string, typeof payments>();
  for (const payment of payments) {
    const existing = grouped.get(payment.bookingId) || [];
    grouped.set(payment.bookingId, [...existing, payment]);
  }

  return bookingIds.map(id => grouped.get(id) || []);
});

async function getBookingWithPayments(bookingId: string) {
  const booking = await db.query.bookings.findFirst({
    where: eq(bookings.id, bookingId),
  });

  if (booking) {
    booking.payments = await paymentLoader.load(bookingId);
  }

  return booking;
}
```

### Query Optimization Tips

```typescript
// Use EXPLAIN ANALYZE to identify slow queries

async function analyzeQuery() {
  const result = await db.execute(sql`
    EXPLAIN ANALYZE
    SELECT b.*, u.name, u.email
    FROM bookings b
    JOIN users u ON b.user_id = u.id
    WHERE b.status = 'confirmed'
    ORDER BY b.created_at DESC
    LIMIT 50
  `);

  console.log(result);
  // Look for:
  // - Seq Scan (should use Index Scan)
  // - high cost
  // - Filter vs Index Cond
}

// Use CTEs for complex queries
async function getBookingReport(startDate: Date, endDate: Date) {
  return db.execute(sql`
    WITH booking_counts AS (
      SELECT
        user_id,
        COUNT(*) as booking_count,
        SUM(total_price) as total_spent
      FROM bookings
      WHERE created_at >= ${startDate}
        AND created_at <= ${endDate}
      GROUP BY user_id
    ),
    user_stats AS (
      SELECT
        u.id,
        u.name,
        u.email,
        COALESCE(bc.booking_count, 0) as booking_count,
        COALESCE(bc.total_spent, 0) as total_spent
      FROM users u
      LEFT JOIN booking_counts bc ON u.id = bc.user_id
    )
    SELECT * FROM user_stats
    WHERE booking_count > 0
    ORDER BY total_spent DESC
  `);
}

// Use window functions for analytics
async function getBookingRankings() {
  return db.execute(sql`
    SELECT
      id,
      user_id,
      total_price,
      RANK() OVER (PARTITION BY user_id ORDER BY total_price DESC) as user_rank,
      ROW_NUMBER() OVER (ORDER BY total_price DESC) as global_rank,
      PERCENT_RANK() OVER (ORDER BY total_price) as percentile
    FROM bookings
    WHERE status = 'confirmed'
  `);
}
```

---

## Caching Strategies

### Redis Caching

```typescript
// lib/cache/redis.ts

import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!, {
  maxRetriesPerRequest: 3,
  retryStrategy: (times) => Math.min(times * 50, 2000),
  enableReadyCheck: true,
});

export class CacheService {
  // Simple get/set
  async get<T>(key: string): Promise<T | null> {
    const value = await redis.get(key);
    return value ? JSON.parse(value) : null;
  }

  async set(key: string, value: any, ttl: number = 3600): Promise<void> {
    await redis.setex(key, ttl, JSON.stringify(value));
  }

  async delete(key: string): Promise<void> {
    await redis.del(key);
  }

  // Cache-aside pattern
  async getOrSet<T>(
    key: string,
    fetch: () => Promise<T>,
    ttl: number = 3600
  ): Promise<T> {
    // Try cache first
    const cached = await this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    // Cache miss - fetch and cache
    const value = await fetch();
    await this.set(key, value, ttl);
    return value;
  }

  // Multi-get
  async getMany<T>(keys: string[]): Promise<(T | null)[]> {
    const values = await redis.mget(keys);
    return values.map(v => (v ? JSON.parse(v) : null));
  }

  // Set many
  async setMany(
    items: Array<{ key: string; value: any; ttl?: number }>,
    ttl: number = 3600
  ): Promise<void> {
    const pipeline = redis.pipeline();
    for (const { key, value, ttl: itemTtl } of items) {
      pipeline.setex(key, itemTtl || ttl, JSON.stringify(value));
    }
    await pipeline.exec();
  }

  // Tag-based cache invalidation
  async setWithTag(
    key: string,
    value: any,
    tags: string[],
    ttl: number = 3600
  ): Promise<void> {
    await this.set(key, value, ttl);

    // Add key to each tag's set
    const pipeline = redis.pipeline();
    for (const tag of tags) {
      pipeline.sadd(`tag:${tag}`, key);
      pipeline.expire(`tag:${tag}`, ttl);
    }
    await pipeline.exec();
  }

  async invalidateTag(tag: string): Promise<void> {
    const keys = await redis.smembers(`tag:${tag}`);
    if (keys.length > 0) {
      await redis.del(...keys, `tag:${tag}`);
    }
  }
}

export const cache = new CacheService();
```

### Query Result Caching

```typescript
// lib/cache/query-cache.ts

import { cache } from './redis';

interface QueryCacheOptions {
  key: string;
  ttl?: number;
  tags?: string[];
}

export function cacheQuery<T extends (...args: any[]) => Promise<any>>(
  queryFn: T,
  options: QueryCacheOptions
): T {
  return (async (...args: Parameters<T>) => {
    const cacheKey = `${options.key}:${JSON.stringify(args)}`;

    return cache.getOrSet(
      cacheKey,
      () => queryFn(...args),
      options.ttl
    );
  }) as T;
}

// Usage
const getUserBookings = cacheQuery(
  async (userId: string) => {
    return db.query.bookings.findMany({
      where: eq(bookings.userId, userId),
    });
  },
  {
    key: 'bookings:user',
    ttl: 300, // 5 minutes
    tags: ['bookings', `user:${userId}`],
  }
);

// Invalidate on mutation
async function updateBooking(id: string, data: any) {
  const booking = await db
    .update(bookings)
    .set(data)
    .where(eq(bookings.id, id))
    .returning();

  // Invalidate related caches
  await cache.invalidateTag(`user:${booking[0].userId}`);
  await cache.invalidateTag(`booking:${id}`);

  return booking;
}
```

### Cache Warming

```typescript
// lib/cache/warmer.ts

export async function warmCache() {
  // Warm frequently accessed data
  const warmTasks = [
    warmPopularDestinations(),
    warmFeaturedPackages(),
    warmHomePageContent(),
  ];

  await Promise.all(warmTasks);
}

async function warmPopularDestinations() {
  const destinations = await db.query.destinations.findMany({
    where: eq(destinations.popular, true),
    limit: 20,
  });

  await cache.setMany(
    destinations.map(d => ({
      key: `destination:${d.id}`,
      value: d,
      ttl: 3600,
    })),
    3600,
    ['destinations']
  );
}

// Schedule cache warming
cron.schedule('*/10 * * * *', warmCache); // Every 10 minutes
```

---

## API Performance

### Response Optimization

```typescript
// lib/api/response-optimizer.ts

import { compress } from '@compression';

// Compression middleware
export function compressionMiddleware() {
  return compress({
    threshold: 1024, // Only compress responses > 1KB
    level: 6,        // Compression level (1-9)
  });
}

// Field selection (GraphQL-like)
export function selectFields<T extends Record<string, any>>(
  data: T,
  fields?: string[]
): Partial<T> {
  if (!fields || fields.length === 0) {
    return data;
  }

  return fields.reduce((acc, field) => {
    if (field in data) {
      acc[field] = data[field];
    }
    return acc;
  }, {} as Partial<T>);
}

// Usage in API route
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const fields = searchParams.get('fields')?.split(',');

  const booking = await getBooking(id);

  return Response.json(selectFields(booking, fields));
}

// Pagination helpers
export function paginate<T>({
  data,
  page,
  limit,
}: {
  data: T[];
  page: number;
  limit: number;
}) {
  const total = data.length;
  const totalPages = Math.ceil(total / limit);
  const start = (page - 1) * limit;
  const end = start + limit;
  const items = data.slice(start, end);

  return {
    data: items,
    meta: {
      page,
      limit,
      total,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1,
    },
  };
}
```

### Batch API Calls

```typescript
// lib/api/batch.ts

interface BatchRequest {
  id: string;
  method: string;
  path: string;
  body?: any;
}

interface BatchResponse {
  id: string;
  status: number;
  body?: any;
  error?: string;
}

export async function batchHandler(
  requests: BatchRequest[]
): Promise<BatchResponse[]> {
  // Process requests in parallel
  const responses = await Promise.allSettled(
    requests.map(async (req) => {
      try {
        // Simulate internal request
        const response = await handleInternalRequest(req);
        return {
          id: req.id,
          status: response.status,
          body: await response.json(),
        };
      } catch (error) {
        return {
          id: req.id,
          status: 500,
          error: error.message,
        };
      }
    })
  );

  return responses.map((result, index) => {
    if (result.status === 'fulfilled') {
      return result.value;
    }
    return {
      id: requests[index].id,
      status: 500,
      error: 'Internal server error',
    };
  });
}

// Usage: POST /api/batch
// [{ "id": "1", "method": "GET", "path": "/api/bookings/123" }]
```

---

## Background Jobs

### Job Queue with BullMQ

```typescript
// lib/queues/index.ts

import { Queue, Worker } from 'bullmq';
import { Redis } from 'ioredis';

const connection = new Redis(process.env.REDIS_URL!);

// Define queues
export const emailQueue = new Queue('emails', { connection });
export const pdfQueue = new Queue('pdf-generation', { connection });
export const syncQueue = new Queue('supplier-sync', { connection });

// Email worker
new Worker(
  'emails',
  async (job) => {
    const { type, to, data } = job.data;

    switch (type) {
      case 'booking-confirmation':
        await sendBookingEmail(to, data);
        break;
      case 'payment-receipt':
        await sendReceiptEmail(to, data);
        break;
    }
  },
  { connection }
);

// PDF generation worker
new Worker(
  'pdf-generation',
  async (job) => {
    const { bookingId, template } = job.data;

    const pdf = await generatePDF(bookingId, template);

    // Upload to storage
    const url = await uploadToStorage(pdf, `bookings/${bookingId}.pdf`);

    // Update database
    await db
      .update(bookings)
      .set({ documentUrl: url })
      .where(eq(bookings.id, bookingId));

    return url;
  },
  { connection }
);

// Supplier sync worker
new Worker(
  'supplier-sync',
  async (job) => {
    const { supplierId, action } = job.data;

    switch (action) {
      case 'sync-availability':
        await syncAvailability(supplierId);
        break;
      case 'sync-pricing':
        await syncPricing(supplierId);
        break;
    }
  },
  { connection, concurrency: 5 }
);
```

### Job Scheduling

```typescript
// lib/queues/scheduler.ts

import { Queue } from 'bullmq';

// Scheduled jobs
export async function setupScheduledJobs() {
  // Daily booking report
  await pdfQueue.add(
    'daily-report',
    { type: 'daily-bookings' },
    {
      repeat: {
        pattern: '0 9 * * *', // 9 AM daily
        tz: 'America/New_York',
      },
    }
  );

  // Cache warming every hour
  await syncQueue.add(
    'warm-cache',
    { type: 'warm-cache' },
    {
      repeat: {
        pattern: '0 * * * *', // Every hour
      },
    }
  );

  // Cleanup old sessions
  await syncQueue.add(
    'cleanup-sessions',
    { type: 'cleanup-sessions', days: 30 },
    {
      repeat: {
        pattern: '0 2 * * *', // 2 AM daily
      },
    }
  );
}
```

---

## Connection Management

### Database Connection Pooling

```typescript
// db/connection.ts

import { drizzle, PostgresJsDatabase } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

const connectionString = process.env.DATABASE_URL!;

// Connection pool configuration
const pool = postgres({
  connectionString,
  max: 20,              // Maximum connections
  idle_timeout: 20,      // Idle timeout in seconds
  connect_timeout: 10,   // Connection timeout in seconds
  max_lifetime: 60 * 30, // Connection lifetime in seconds

  // Connection pool monitoring
  onnotice: (notice) => console.log('DB Notice:', notice),
});

export const db = drizzle(pool);

// Graceful shutdown
process.on('beforeExit', async () => {
  await pool.end();
});
```

### HTTP Client Pooling

```typescript
// lib/http/pooled-client.ts

import { Agent } from 'undici';

// HTTP connection pool for external APIs
const pool = new Agent({
  connections: 100,           // Max concurrent connections
  pipelining: 10,             // Pipeline multiple requests
  keepAliveTimeout: 60000,    // Keep connections alive for 60s
  keepAliveMaxTimeout: 300000, // 5 minutes
});

export async function fetchWithPool(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  return fetch(url, {
    ...options,
    // @ts-ignore - undici agent
    dispatcher: pool,
  });
}

// Usage for supplier APIs
export async function fetchSupplierAPI(endpoint: string) {
  return fetchWithPool(`https://api.supplier.com${endpoint}`, {
    headers: {
      'Authorization': `Bearer ${process.env.SUPPLIER_API_KEY}`,
    },
  });
}
```

---

## Summary

Backend performance strategies:

- **Database**: Indexes, materialized views, query optimization
- **Caching**: Redis for hot data, cache-aside pattern, tag-based invalidation
- **API**: Compression, field selection, batching, pagination
- **Background jobs**: BullMQ for async tasks, scheduled jobs
- **Connections**: Database pooling, HTTP client pooling

**Key Targets:**
- API p95 latency: < 500ms
- Database queries: < 100ms (p95)
- Cache hit rate: > 80%
- Connection pool utilization: < 70%

---

**Next:** [Part 4: Scalability Patterns](./PERFORMANCE_SCALABILITY_04_SCALING.md) — Horizontal scaling, load balancing, and CDN
