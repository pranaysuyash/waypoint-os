# Supplier Integration 01: Technical Deep Dive

> Complete guide to supplier API integration architecture and patterns

---

## Document Overview

**Series:** Supplier Integration Deep Dive (Document 1 of 4)
**Focus:** Technical Architecture — Integration patterns, rate limiting, authentication
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Integration Architecture](#integration-architecture)
3. [Base Adapter Pattern](#base-adapter-pattern)
4. [Rate Limiting](#rate-limiting)
5. [Authentication](#authentication)
6. [Request/Response Handling](#requestresponse-handling)
7. [Logging & Monitoring](#logging--monitoring)
8. [Implementation Reference](#implementation-reference)

---

## Executive Summary

Supplier Integration provides unified access to travel inventory from multiple third-party providers (TBO, TravelBoutique, MakCorp, airlines, hotels). The system uses an adapter pattern to normalize supplier APIs, rate limiting to prevent blocking, multi-layer caching for performance, and circuit breakers for resilience.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Unified Interface** | Single API for all suppliers regardless of differences |
| **Rate Limiting** | Per-supplier rate limits with intelligent queuing |
| **Caching** | Multi-layer cache (Redis, CDN) for price and inventory |
| **Resilience** | Circuit breakers, retries, fallback suppliers |
| **Monitoring** | Real-time health tracking, performance metrics |

---

## Integration Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPLIER INTEGRATION ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        APPLICATION LAYER                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Booking Service                                               ││   │
│  │  │  Quote Service                                                 ││   │
│  │  │  Search Service                                                ││   │
│  │  │  Inventory Service                                              ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     SUPPLIER ORCHESTRATION LAYER                    │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  SupplierOrchestrator                                          ││   │
│  │  │  - Routes requests to appropriate adapter                      ││   │
│  │  │  - Aggregates results from multiple suppliers                   ││   │
│  │  │  - Handles fallback logic                                       ││   │
│  │  │  - Manages retries and circuit breakers                         ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        ADAPTER LAYER                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      ││   │
│  │  │  │   TBO    │  │TravelBout│  │  MakCorp │  │ Airlines │      ││   │
│  │  │  │  Adapter │  │   Adapter │  │  Adapter │  │  Adapter  │      ││   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      ││   │
│  │  │                                                                  ││   │
│  │  │  Implements: ISupplierAdapter interface                         ││   │
│  │  │  - search()                                                     ││   │
│  │  │  - quote()                                                      ││   │
│  │  │  - book()                                                       ││   │
│  │  │  - cancel()                                                     ││   │
│  │  │  - retrieve()                                                   ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│ │                      CROSS-CUTTING SERVICES                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Rate Limiter          │ Cache Manager      │ Circuit Breaker   ││   │
│  │  │  (per-supplier limits) │ (multi-layer)      │ (failure detection)││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Auth Manager          │ Logger             │ Health Monitor    ││   │
│  │  │  (token management)    │ (request tracking)  │ (supplier status) ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      EXTERNAL API LAYER                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  HTTPS Client with:                                             ││   │
│  │  │  - Connection pooling                                          ││   │
│  │  │  - Timeout management                                          ││   │
│  │  │  - Retry logic                                                 ││   │
│  │  │  - Request signing                                             ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       SUPPLIER APIS                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │   TBO    │  │TravelBout│  │  MakCorp │  │ Airlines │          │   │
│  │  │   API    │  │   API    │  │   API    │  │   GDS    │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SUPPLIER REQUEST FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SEARCH REQUEST                                                         │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  User searches: "Goa, Dec 15-20, 2 adults"                          │ │
│     │                                                                      │ │
│     │  POST /api/supplier/search                                          │ │
│     │  {                                                                  │ │
│     │    "destination": "Goa",                                             │ │
│     │    "checkIn": "2026-12-15",                                         │ │
│     │    "checkOut": "2026-12-20",                                        │ │
│     │    "guests": { "adults": 2, "children": 0 },                        │ │
│     │    "suppliers": ["auto"]  // Or specific list                       │ │
│     │  }                                                                  │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                  │                                          │
│                                  ▼                                          │
│  2. ORCHESTRATOR PROCESSING                                                │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  SupplierOrchestrator.receiveSearch(request)                        │ │
│     │  ├─ Parse request                                                   │ │
│     │  ├─ Determine eligible suppliers (based on destination, etc.)      │ │
│     │  ├─ Check circuit breaker state for each supplier                   │ │
│     │  ├─ Check cache (return if available and fresh)                     │ │
│     │  └─ Parallel requests to healthy suppliers                         │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                  │                                          │
│                                  ▼                                          │
│  3. ADAPTER REQUESTS                                                       │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  For each healthy supplier:                                        │ │
│     │                                                                      │ │
│     │  adapter.search({                                                   │ │
│     │    destination: "Goa",                                              │ │
│     │    checkIn: "2026-12-15",                                           │ │
│     │    checkOut: "2026-12-20",                                          │ │
│     │    guests: 2                                                        │ │
│     │  })                                                                 │ │
│     │                                                                      │ │
│     │  Adapter responsibilities:                                          │ │
│     │  ├─ Check rate limit (wait if needed)                               │ │
│     │  ├─ Transform to supplier-specific format                           │ │
│     │  ├─ Add authentication headers                                       │ │
│     │  ├─ Call supplier API                                               │ │
│     │  ├─ Parse response                                                  │ │
│     │  ├─ Transform to standard format                                    │ │
│     │  └─ Cache result                                                    │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                  │                                          │
│                                  ▼                                          │
│  4. RESPONSE AGGREGATION                                                   │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │  Collect responses from all suppliers                               │ │
│     │  ├─ Deduplicate (same property from multiple suppliers)            │ │
│     │  ├─ Sort by price/relevance                                        │ │
│     │  ├─ Apply margin rules                                             │ │
│     │  └─ Return unified results                                         │ │
│     │                                                                      │ │
│     │  {                                                                  │ │
│     │    "results": [                                                     │ │
│     │      {                                                              │ │
│     │        "id": "prop_123",                                            │ │
│     │        "name": "Taj Resort Goa",                                   │ │
│     │        "supplier": "tbo",                                           │ │
│     │        "price": 45000,                                             │ │
│     │        "available": true                                           │ │
│     │      },                                                             │ │
│     │      ...                                                            │ │
│     │    ]                                                               │ │
│     │  }                                                                  │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Base Adapter Pattern

### Adapter Interface

```typescript
// interfaces/supplier-adapter.interface.ts

export interface SupplierAdapter {
  // Adapter metadata
  readonly id: string;
  readonly name: string;
  readonly type: SupplierType;

  // Lifecycle
  initialize(): Promise<void>;
  healthCheck(): Promise<SupplierHealth>;

  // Core operations
  search(request: SearchRequest): Promise<SearchResponse>;
  quote(request: QuoteRequest): Promise<QuoteResponse>;
  book(request: BookingRequest): Promise<BookingResponse>;
  cancel(request: CancellationRequest): Promise<CancellationResponse>;
  retrieve(request: RetrievalRequest): Promise<BookingDetails>;

  // Inventory
  checkAvailability(request: AvailabilityRequest): Promise<AvailabilityResponse>;
  getRates(request: RatesRequest): Promise<RatesResponse>;

  // Support
  supports(operation: string): boolean;
  getRateLimit(): RateLimitInfo;
}

export enum SupplierType {
  HOTEL = 'hotel',
  FLIGHT = 'flight',
  ACTIVITY = 'activity',
  TRANSFER = 'transfer',
  PACKAGE = 'package',
}

export interface SearchRequest {
  destination: Destination;
  dates: DateRange;
  guests: GuestCount;
  filters?: SearchFilters;
}

export interface SearchResponse {
  results: SearchResult[];
  totalCount: number;
  hasMore: boolean;
  searchId: string;
  supplier: string;
  timestamp: Date;
}
```

### Base Adapter Implementation

```typescript
// adapters/base/base-adapter.abstract.ts
import { Redis } from 'ioredis';
import { SupplierAdapter, SearchRequest, SearchResponse } from '@/interfaces';

export abstract class BaseSupplierAdapter implements SupplierAdapter {
  abstract readonly id: string;
  abstract readonly name: string;
  abstract readonly type: SupplierType;

  protected httpClient: HttpClient;
  protected rateLimiter: RateLimiter;
  protected cache: Redis;
  protected logger: Logger;
  protected circuitBreaker: CircuitBreaker;

  constructor(config: SupplierConfig) {
    this.httpClient = new HttpClient({
      timeout: config.timeout || 30000,
      retries: config.retries || 3,
    });
    this.rateLimiter = new RateLimiter(config.rateLimit);
    this.cache = new Redis(config.redisUrl);
    this.circuitBreaker = new CircuitBreaker({
      threshold: config.circuitBreakerThreshold || 5,
      timeout: config.circuitBreakerTimeout || 60000,
    });
  }

  async initialize(): Promise<void> {
    // Initialize connection, fetch auth token, etc.
    await this.authenticate();
  }

  async healthCheck(): Promise<SupplierHealth> {
    try {
      const start = Date.now();
      await this.ping();
      return {
        status: 'healthy',
        latency: Date.now() - start,
        lastCheck: new Date(),
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        lastCheck: new Date(),
      };
    }
  }

  async search(request: SearchRequest): Promise<SearchResponse> {
    // Check circuit breaker
    if (!this.circuitBreaker.canRequest()) {
      throw new Error(`Circuit breaker open for ${this.name}`);
    }

    // Check cache
    const cacheKey = this.getCacheKey('search', request);
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // Rate limit wait
    await this.rateLimiter.wait();

    try {
      // Transform request to supplier format
      const supplierRequest = await this.transformSearchRequest(request);

      // Call supplier API
      const response = await this.httpClient.post(
        this.getEndpoint('search'),
        supplierRequest
      );

      // Transform response to standard format
      const standardResponse = await this.transformSearchResponse(response);

      // Cache result
      await this.cache.setex(
        cacheKey,
        this.getCacheTTL('search'),
        JSON.stringify(standardResponse)
      );

      // Record success
      this.circuitBreaker.recordSuccess();

      return standardResponse;
    } catch (error) {
      // Record failure
      this.circuitBreaker.recordFailure();
      throw error;
    }
  }

  async book(request: BookingRequest): Promise<BookingResponse> {
    // Bookings are never cached
    await this.rateLimiter.wait();

    const supplierRequest = await this.transformBookingRequest(request);
    const response = await this.httpClient.post(
      this.getEndpoint('book'),
      supplierRequest
    );

    return this.transformBookingResponse(response);
  }

  // Abstract methods to be implemented by concrete adapters
  protected abstract authenticate(): Promise<void>;
  protected abstract transformSearchRequest(request: SearchRequest): Promise<any>;
  protected abstract transformSearchResponse(response: any): Promise<SearchResponse>;
  protected abstract transformBookingRequest(request: BookingRequest): Promise<any>;
  protected abstract transformBookingResponse(response: any): Promise<BookingResponse>;
  protected abstract getEndpoint(operation: string): string;
  protected abstract ping(): Promise<void>;

  // Utility methods
  protected getCacheKey(operation: string, request: any): string {
    const hash = crypto
      .createHash('md5')
      .update(JSON.stringify(request))
      .digest('hex');
    return `supplier:${this.id}:${operation}:${hash}`;
  }

  protected getCacheTTL(operation: string): number {
    const TTLs = {
      search: 300,      // 5 minutes for search
      quote: 180,      // 3 minutes for quotes
      rates: 600,      // 10 minutes for rates
      availability: 60, // 1 minute for availability
    };
    return TTLs[operation] || 300;
  }
}
```

### Concrete Adapter Example

```typescript
// adapters/tbo/tbo-adapter.ts
import { BaseSupplierAdapter } from '../base/base-adapter.abstract';
import { SearchRequest, SearchResponse } from '@/interfaces';

export class TBOAdapter extends BaseSupplierAdapter {
  readonly id = 'tbo';
  readonly name = 'Travel Bed Online';
  readonly type = SupplierType.HOTEL;

  private apiKey: string;
  private password: string;
  private token: string;

  constructor(config: TBOConfig) {
    super(config);
    this.apiKey = config.apiKey;
    this.password = config.password;
  }

  protected async authenticate(): Promise<void> {
    const response = await this.httpClient.post(
      'https://api.travelboutique.online/auth/Token',
      {
        ApiKey: this.apiKey,
        Password: this.password,
      }
    );
    this.token = response.Token;
  }

  protected async transformSearchRequest(request: SearchRequest): Promise<any> {
    return {
      TokenId: this.token,
      CheckIn: request.dates.checkIn,
      CheckOut: request.dates.checkOut,
      CityCode: this.getCityCode(request.destination),
      NoOfRooms: this.calculateRooms(request.guests),
      GuestNationality: 'IN',
      ResponseTime: 30,
    };
  }

  protected async transformSearchResponse(response: any): Promise<SearchResponse> {
    return {
      results: response.HotelSearchResult.HotelResults.map(hotel => ({
        id: hotel.HotelCode,
        name: hotel.HotelName,
        supplier: this.id,
        price: {
          base: hotel.Price.Price,
          tax: hotel.Price.Tax,
          total: hotel.Price.TotalFare,
        },
        availability: hotel.Status === 'Available',
        images: hotel.HotelPictures?.map(p => p.URL) || [],
        rating: hotel.StarRating,
        address: hotel.HotelAddress,
      })),
      totalCount: response.HotelSearchResult.HotelResults.length,
      hasMore: false,
      searchId: response.HotelSearchResult.TraceId,
      supplier: this.id,
      timestamp: new Date(),
    };
  }

  protected getEndpoint(operation: string): string {
    const endpoints = {
      search: 'https://api.travelboutique.online/hotel/HotelSearch',
      quote: 'https://api.travelboutique.online/hotel/HotelBookingPrice',
      book: 'https://api.travelboutique.online/hotel/HotelBook',
      cancel: 'https://api.travelboutique.online/hotel/CancelBooking',
    };
    return endpoints[operation];
  }

  private getCityCode(destination: Destination): string {
    // TBO city code mapping
    const cityMap = {
      'Goa': 'GOI',
      'Mumbai': 'BOM',
      // ... more mappings
    };
    return cityMap[destination.city] || destination.city;
  }
}
```

---

## Rate Limiting

### Rate Limiting Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RATE LIMITING STRATEGY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SUPPLIER LIMITS                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Supplier    │ Limit      │ Window  │ Strategy                      │   │
│  │  ────────────┼───────────┼────────┼───────────────────────          │   │
│  │  TBO         │ 100 req/min │ 60s    │ Token bucket                  │   │
│  │  TravelBoutique│ 50 req/min │ 60s    │ Fixed window                  │   │
│  │  MakCorp     │ 200 req/hr  │ 3600s  │ Sliding window                │   │
│  │  Airlines    │ 10 req/sec  │ 1s     │ Leaky bucket                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IMPLEMENTATION                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  class RateLimiter {                                                │   │
│  │    private tokens: Map<string, number>;                              │   │
│  │    private lastRefill: Map<string, number>;                          │   │
│  │                                                                      │   │
│  │    async wait(supplierId: string): Promise<void> {                  │   │
│  │      while (!this.canRequest(supplierId)) {                          │   │
│  │        const waitTime = this.calculateWaitTime(supplierId);          │   │
│  │        await this.sleep(waitTime);                                   │   │
│  │      }                                                               │   │
│  │      this.consume(supplierId);                                       │   │
│  │    }                                                                 │   │
│  │                                                                      │   │
│  │    private canRequest(supplierId: string): boolean {                │   │
│  │      const tokens = this.getTokens(supplierId);                     │   │
│  │      return tokens > 0;                                              │   │
│  │    }                                                                 │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  QUEUING FOR BULK REQUESTS                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  For parallel searches (multiple suppliers):                        │   │
│  │                                                                      │   │
│  │  - Create separate queue per supplier                                │   │
│  │  - Process requests respecting each supplier's limit                 │   │
│  │  - Return results as they arrive                                     │   │
│  │                                                                      │   │
│  │  Benefit: Maximize throughput without hitting limits                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Rate Limiter Implementation

```typescript
// services/rate-limiter.service.ts
import Bull from 'bull';

export class RateLimiterService {
  private queues: Map<string, Bull.Queue> = new Map();
  private limits: Map<string, RateLimitConfig> = new Map();

  constructor() {
    this.setupSuppliers();
  }

  private setupSuppliers() {
    // TBO: 100 requests/minute
    this.setupQueue('tbo', {
      limit: 100,
      window: 60000, // 1 minute
    });

    // TravelBoutique: 50 requests/minute
    this.setupQueue('travelboutique', {
      limit: 50,
      window: 60000,
    });

    // MakCorp: 200 requests/hour
    this.setupQueue('makcorp', {
      limit: 200,
      window: 3600000, // 1 hour
    });
  }

  private setupQueue(supplierId: string, config: RateLimitConfig) {
    const queue = new Bull(`supplier:${supplierId}`, {
      redis: process.env.REDIS_URL,
      limiter: {
        max: config.limit,
        duration: config.window,
      },
    });

    this.queues.set(supplierId, queue);
    this.limits.set(supplierId, config);
  }

  async addRequest<T>(
    supplierId: string,
    request: () => Promise<T>
  ): Promise<T> {
    const queue = this.queues.get(supplierId);

    if (!queue) {
      // No rate limiting configured
      return request();
    }

    // Add to queue
    const job = await queue.add(async () => {
      return request();
    });

    return job.finished();
  }

  async getRateLimitStatus(supplierId: string): Promise<RateLimitStatus> {
    const queue = this.queues.get(supplierId);
    const config = this.limits.get(supplierId);

    if (!queue || !config) {
      return { status: 'unlimited' };
    }

    const waiting = await queue.getWaitingCount();
    const active = await queue.getActiveCount();

    return {
      status: active >= config.limit ? 'throttled' : 'available',
      waiting,
      active,
      limit: config.limit,
      window: config.window,
    };
  }
}
```

---

## Authentication

### Authentication Methods by Supplier

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AUTHENTICATION METHODS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  API KEY + SECRET (Most Common)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Used by: TBO, TravelBoutique, MakCorp                              │   │
│  │                                                                      │   │
│  │  Flow:                                                               │   │
│  │  1. Send API key + secret to /auth/token                             │   │
│  │  2. Receive JWT/session token                                       │   │
│  │  3. Use token in Authorization header for subsequent requests       │   │
│  │  4. Refresh token before expiry                                       │   │
│  │                                                                      │   │
│  │  Token management:                                                  │   │
│  │  - Store in Redis with TTL                                          │   │
│  │  - Auto-refresh 5 minutes before expiry                              │   │
│  │  - Handle re-auth on 401 responses                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  OAUTH 2.0                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Used by: Expedia, some airline APIs                                │   │
│  │                                                                      │   │
│  │  Flow:                                                               │   │
│  │  1. Redirect user to OAuth provider                                  │   │
│  │  2. Receive authorization code                                      │   │
│  │  3. Exchange code for access token                                   │   │
│  │  4. Use access token for API calls                                  │   │
│  │  5. Refresh using refresh token                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HMAC SIGNING                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Used by: Some payment APIs, high-security suppliers                │   │
│  │                                                                      │   │
│  │  Method:                                                             │   │
│  │  signature = HMAC-SHA256(request_body, secret_key)                  │   │
│  │                                                                      │   │
│  │  Include signature in header:                                       │   │
│  │  X-Signature: {timestamp}:{signature}                              │   │
│  │                                                                      │   │
│  │  Server verifies signature to authenticate request                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Token Management Service

```typescript
// services/auth-manager.service.ts
import { Redis } from 'ioredis';

export class AuthManagerService {
  private redis: Redis;
  private tokens: Map<string, SupplierToken> = new Map();

  async getToken(supplierId: string): Promise<string> {
    // Check memory cache first
    const memToken = this.tokens.get(supplierId);
    if (memToken && !this.isExpired(memToken)) {
      return memToken.access_token;
    }

    // Check Redis
    const redisKey = `auth:token:${supplierId}`;
    const cached = await this.redis.get(redisKey);
    if (cached) {
      const token = JSON.parse(cached);
      if (!this.isExpired(token)) {
        this.tokens.set(supplierId, token);
        return token.access_token;
      }
    }

    // Fetch new token
    return this.fetchToken(supplierId);
  }

  private async fetchToken(supplierId: string): Promise<string> {
    const supplier = this.getSupplierConfig(supplierId);

    let token: string;

    switch (supplier.authType) {
      case 'api_key':
        token = await this.authenticateWithApiKey(supplier);
        break;
      case 'oauth2':
        token = await this.authenticateWithOAuth(supplier);
        break;
      default:
        throw new Error(`Unknown auth type: ${supplier.authType}`);
    }

    // Cache token
    const tokenData = {
      access_token: token,
      expires_at: Date.now() + supplier.tokenTTL,
    };

    this.tokens.set(supplierId, tokenData);
    await this.redis.setex(
      `auth:token:${supplierId}`,
      supplier.tokenTTL / 1000,
      JSON.stringify(tokenData)
    );

    return token;
  }

  private async authenticateWithApiKey(supplier: SupplierConfig): Promise<string> {
    const response = await fetch(supplier.authUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ApiKey: supplier.apiKey,
        Password: supplier.apiSecret,
      }),
    });

    if (!response.ok) {
      throw new Error(`Authentication failed for ${supplier.id}`);
    }

    const data = await response.json();
    return data.Token || data.access_token;
  }

  private isExpired(token: SupplierToken): boolean {
    // Refresh 5 minutes before expiry
    return Date.now() > (token.expires_at - 300000);
  }
}
```

---

## Request/Response Handling

### HTTP Client Configuration

```typescript
// services/supplier-http-client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

export class SupplierHttpClient {
  private client: AxiosInstance;
  private logger: Logger;

  constructor(config: HttpClientConfig) {
    this.client = axios.create({
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'TravelAgency/1.0',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // Add auth token
        const supplierId = this.extractSupplierId(config.url);
        const token = await this.getAuthToken(supplierId);
        config.headers.Authorization = `Bearer ${token}`;

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId();

        // Log request
        this.logger.info('Supplier API Request', {
          supplier: supplierId,
          method: config.method,
          url: config.url,
          requestId: config.headers['X-Request-ID'],
        });

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Log success
        this.logger.info('Supplier API Response', {
          supplier: this.extractSupplierId(response.config.url),
          status: response.status,
          requestId: response.config.headers['X-Request-ID'],
          duration: Date.now() - response.config.metadata.startTime,
        });

        return response;
      },
      async (error) => {
        // Log error
        this.logger.error('Supplier API Error', {
          supplier: this.extractSupplierId(error.config?.url),
          status: error.response?.status,
          message: error.message,
          requestId: error.config?.headers?.['X-Request-ID'],
        });

        // Handle specific error codes
        if (error.response?.status === 401) {
          // Token expired, force refresh
          await this.invalidateToken(this.extractSupplierId(error.config.url));
          // Retry once with new token
          return this.retryRequest(error.config);
        }

        if (error.response?.status === 429) {
          // Rate limited, extract retry-after
          const retryAfter = error.response.headers['retry-after'];
          if (retryAfter) {
            await this.sleep(parseInt(retryAfter) * 1000);
            return this.retryRequest(error.config);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  async post<T>(url: string, data: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, {
      ...config,
      metadata: { startTime: Date.now() },
    });
    return response.data;
  }
}
```

---

## Logging & Monitoring

### Request Logging

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REQUEST LOGGING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOG LEVELS                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ERROR   │ Failed requests, 5xx errors                              │   │
│  │  WARN    │ Rate limits, slow responses, 4xx errors                   │   │
│  │  INFO    │ All requests (with request ID)                           │   │
│  │  DEBUG   │ Request/response bodies (dev only)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LOG FORMAT                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  {                                                                  │   │
│  │    "timestamp": "2026-04-25T10:30:00Z",                             │   │
│  │    "level": "info",                                                 │   │
│  │    "message": "Supplier API Request",                                │   │
│  │    "supplier": "tbo",                                               │   │
│  │    "operation": "search",                                           │   │
│  │    "requestId": "req_abc123",                                       │   │
│  │    "duration": 245,                                                 │   │
│  │    "status": "success",                                             │   │
│  │    "resultCount": 45                                                │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Health Monitoring

```typescript
// services/supplier-health.service.ts
export class SupplierHealthService {
  async getHealthStatus(supplierId: string): Promise<SupplierHealthStatus> {
    const recent = await this.getRecentMetrics(supplierId, '5m');

    return {
      supplier: supplierId,
      status: this.calculateStatus(recent),
      metrics: {
        successRate: this.calculateSuccessRate(recent),
        avgResponseTime: this.calculateAvgResponseTime(recent),
        errorRate: this.calculateErrorRate(recent),
        rateLimitHits: this.countRateLimitHits(recent),
      },
      lastError: await this.getLastError(supplierId),
      lastSuccess: await this.getLastSuccess(supplierId),
      circuitBreakerState: await this.getCircuitBreakerState(supplierId),
    };
  }

  async getAllHealthStatus(): Promise<SupplierHealthStatus[]> {
    const suppliers = ['tbo', 'travelboutique', 'makcorp'];
    return Promise.all(
      suppliers.map(s => this.getHealthStatus(s))
    );
  }

  private calculateStatus(metrics: RequestMetric[]): HealthStatus {
    if (metrics.length === 0) return 'unknown';

    const errorRate = this.calculateErrorRate(metrics);
    const recentErrors = metrics.filter(m =>
      m.status >= 400 &&
      m.timestamp > Date.now() - 60000 // Last minute
    ).length;

    if (recentErrors >= 5) return 'unhealthy';
    if (errorRate > 0.1) return 'degraded';
    return 'healthy';
  }
}
```

---

## Summary

The Supplier Integration technical architecture provides:

- **Unified Interface**: Base adapter pattern for consistent supplier access
- **Rate Limiting**: Per-supplier token bucket with queuing
- **Authentication**: Token management with auto-refresh
- **Resilience**: Circuit breakers and retry logic
- **Monitoring**: Request logging, health tracking, metrics

This completes the Technical Deep Dive. The next document covers Data models and mapping.

---

**Related Documents:**
- [Data Deep Dive](./SUPPLIER_INTEGRATION_02_DATA_DEEP_DIVE.md) — Data models and mapping
- [Caching Deep Dive](./SUPPLIER_INTEGRATION_03_CACHING_DEEP_DIVE.md) — Cache strategies
- [Error Handling Deep Dive](./SUPPLIER_INTEGRATION_04_ERROR_HANDLING_DEEP_DIVE.md) — Fallback and resilience

**Master Index:** [Supplier Integration Deep Dive Master Index](./SUPPLIER_INTEGRATION_DEEP_DIVE_MASTER_INDEX.md)

---

**Last Updated:** 2026-04-25
