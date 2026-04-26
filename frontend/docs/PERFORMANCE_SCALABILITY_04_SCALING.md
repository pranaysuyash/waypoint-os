# Performance & Scalability Part 4: Scalability Patterns

> Horizontal scaling, load balancing, CDN, and infrastructure

**Series:** Performance & Scalability
**Previous:** [Part 3: Backend Performance](./PERFORMANCE_SCALABILITY_03_BACKEND.md)
**Next:** [Part 5: Monitoring & Alerting](./PERFORMANCE_SCALABILITY_05_MONITORING.md)

---

## Table of Contents

1. [Scaling Strategy](#scaling-strategy)
2. [Load Balancing](#load-balancing)
3. [CDN Configuration](#cdn-configuration)
4. [Database Scaling](#database-scaling)
5. [Rate Limiting](#rate-limiting)
6. [Auto-Scaling](#auto-scaling)

---

## Scaling Strategy

### Vertical vs Horizontal

```typescript
// Scaling decision matrix

interface ScalingDecision {
  // Scale vertically (bigger machine) when:
  vertical: {
    singleThreaded: boolean;    // CPU-bound single thread
    memoryBound: boolean;       // Need more RAM
    simpleSetup: boolean;       // No architecture change
    lowTraffic: boolean;        // < 10k requests/day
  };

  // Scale horizontally (more machines) when:
  horizontal: {
    stateless: boolean;         // Services are stateless
    highAvailability: boolean;  // Need redundancy
    spikyTraffic: boolean;      // Variable load
    costEffective: boolean;     // Smaller instances cheaper
  };
}

// Our scaling strategy
export const scalingStrategy = {
  frontend: {
    type: 'horizontal',
    provider: 'vercel',
    edge: true,                 // Edge functions for global presence
    instances: 'auto',          // Auto-scale based on traffic
  },

  api: {
    type: 'horizontal',
    provider: 'fly.io',
    regions: ['iad', 'lax', 'fra', 'sin'], // Global regions
    instances: {
      min: 2,
      max: 20,
      targetCPU: 70,            // Scale up at 70% CPU
      targetMemory: 80,
    },
  },

  database: {
    type: 'vertical',           // Scale up first
    provider: 'neon',
    replication: true,          // Read replicas for scaling reads
    writeInstance: 'large',     // Dedicated write instance
    readInstances: 3,           // 3 read replicas
  },

  cache: {
    type: 'horizontal',
    provider: 'upstash',
    clustering: true,           // Redis cluster for scaling
    regions: ['us-east', 'eu-west', 'asia-south'],
  },
};
```

### Microservices Decomposition

```typescript
// Service boundaries for scaling

interface MicroserviceArchitecture {
  // Core services (high traffic, scale independently)
  core: {
    booking: {
      scale: 'high',            // 10+ instances
      cpu: '2x',
      memory: '4GB',
      database: 'dedicated',
    },
    search: {
      scale: 'medium',          // 5+ instances
      cpu: '4x',                // CPU intensive
      memory: '8GB',
      cache: 'heavy',
    },
    payment: {
      scale: 'medium',          // 5+ instances
      cpu: '1x',
      memory: '2GB',
      compliance: 'PCI',
    },
  },

  // Support services (lower traffic)
  support: {
    notifications: {
      scale: 'low',             // 2 instances
      queue: 'required',        // Job queue
      workers: 3,
    },
    reports: {
      scale: 'manual',          // On-demand
      batch: true,
      database: 'read-replica',
    },
    analytics: {
      scale: 'low',
      ingestion: 'async',
      storage: 'columnar',
    },
  },
};
```

---

## Load Balancing

### Application Load Balancer

```yaml
# infrastructure/load-balancer.yaml

apiVersion: v1
kind: Service
metadata:
  name: travel-agency-api
spec:
  type: LoadBalancer
  selector:
    app: travel-agency-api
  ports:
    - port: 80
      targetPort: 3000
      protocol: TCP
  sessionAffinity: ClientIP # Sticky sessions for websockets

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: travel-agency-ingress
  annotations:
    # Load balancer configuration
    nginx.ingress.kubernetes.io/load-balance: "least_conn"
    nginx.ingress.kubernetes.io/upstream-keepalive-connections: "100"
    nginx.ingress.kubernetes.io/upstream-keepalive-timeout: "60"

    # SSL configuration
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"

    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "2"

spec:
  tls:
    - hosts:
        - api.travelagency.com
      secretName: travel-agency-tls
  rules:
    - host: api.travelagency.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: travel-agency-api
                port:
                  number: 80
```

### Global Load Balancing

```typescript
// infrastructure/geo-routing.ts

// Geographic routing for global performance
export const geoRouting = {
  // Route to nearest region
  nearestRegion: (country: string): string => {
    const regionMap: Record<string, string> = {
      // North America
      US: 'iad', // Virginia
      CA: 'yyz', // Toronto
      MX: 'iad',

      // Europe
      GB: 'lhr', // London
      FR: 'cdg', // Paris
      DE: 'fra', // Frankfurt
      IT: 'lin', // Milan

      // Asia Pacific
      IN: 'blr', // Bangalore
      SG: 'sin', // Singapore
      AU: 'syd', // Sydney
      JP: 'nrt', // Tokyo
    };

    return regionMap[country] || 'iad'; // Default to Virginia
  },

  // Failover regions
  failover: {
    primary: 'iad',
    secondary: 'lax',  // Los Angeles
    tertiary: 'fra',   // Frankfurt
  },

  // Health check endpoints
  healthCheck: '/health',
  interval: 30,        // seconds
  timeout: 5,
  unhealthyThreshold: 3,
  healthyThreshold: 2,
};
```

---

## CDN Configuration

### Cloudflare Setup

```typescript
// infrastructure/cdn/cloudflare.ts

export const cloudflareConfig = {
  // Cache rules
  cacheRules: [
    {
      name: 'Static Assets',
      match: ['*.js', '*.css', '*.png', '*.jpg', '*.svg', '*.woff2'],
      edgeTTL: 365 * 24 * 60 * 60, // 1 year
      browserTTL: 365 * 24 * 60 * 60,
    },
    {
      name: 'API Responses',
      match: ['/api/*'],
      edgeTTL: 60,               // 1 minute
      browserTTL: 0,              // No browser caching
      cacheKey: ['cookie', 'authorization'], // Ignore these headers
    },
    {
      name: 'Images',
      match: ['/images/*'],
      edgeTTL: 30 * 24 * 60 * 60, // 30 days
      polish: 'lossless',         // Image optimization
    },
  ],

  // Page rules
  pageRules: [
    {
      url: '*/booking/*',
      settings: {
        cacheLevel: 'bypass',     // Don't cache booking pages
        disablePerformance: false,
      },
    },
    {
      url: '*/static/*',
      settings: {
        cacheLevel: 'cache_everything',
        edgeCacheTTL: 365 * 24 * 60 * 60,
        browserCacheTTL: 365 * 24 * 60 * 60,
      },
    },
  ],

  // Security settings
  security: {
    botFightMode: true,
    securityLevel: 'medium',
    challengePassage: 60,

    // Rate limiting rules
    rateLimits: [
      {
        name: 'Login Endpoint',
        match: ['/api/auth/login', '/api/auth/register'],
        rate: 5,                  // 5 requests per
        period: 60,                // minute
        action: 'block',
      },
      {
        name: 'Search Endpoint',
        match: ['/api/search/*'],
        rate: 30,
        period: 60,
        action: 'throttle',
      },
    ],
  },

  // Web Workers (edge computing)
  workers: [
    {
      name: 'geo-routing',
      route: '/*',
      script: 'geo-routing-worker',
    },
    {
      name: 'auth-check',
      route: '/api/*',
      script: 'auth-worker',
    },
  ],
};
```

### Image CDN Configuration

```typescript
// infrastructure/cdn/images.ts

export const imageCDNConfig = {
  provider: 'cloudinary',

  transformations: {
    // Responsive images
    responsive: {
      breakpoints: [320, 640, 960, 1280, 1920],
      formats: ['avif', 'webp', 'jpg'],
      quality: 85,
    },

    // Image types
    thumbnail: {
      width: 200,
      height: 150,
      crop: 'fill',
      gravity: 'auto',
      quality: 80,
    },

    gallery: {
      width: 800,
      height: 600,
      crop: 'fit',
      quality: 85,
    },

    hero: {
      width: 1920,
      height: 1080,
      crop: 'fill',
      quality: 90,
      fetch_format: 'auto',
    },
  },

  // Optimizations
  optimizations: {
    lazy: true,
    progressive: true,
    stripMetadata: true,
  },

  // Delivery
  delivery: {
    cdnSubdomain: true,
    secureDelivery: true,
    useRootPath: true,
    privateCDN: false,
  },
};
```

---

## Database Scaling

### Read Replicas

```typescript
// db/replicas.ts

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

// Primary (write) database
const primaryPool = postgres(process.env.DATABASE_PRIMARY_URL!, {
  max: 10,
});

export const primaryDb = drizzle(primaryPool);

// Read replicas
const replicaPools = [
  postgres(process.env.DATABASE_REPLICA_1_URL!, {
    max: 20, // More connections for reads
  }),
  postgres(process.env.DATABASE_REPLICA_2_URL!, {
    max: 20,
  }),
];

// Round-robin replica selection
let replicaIndex = 0;

function getReadDb() {
  const pool = replicaPools[replicaIndex];
  replicaIndex = (replicaIndex + 1) % replicaPools.length;
  return drizzle(pool);
}

// Smart query routing
export function getDb(write: boolean = false) {
  return write ? primaryDb : getReadDb();
}

// Usage
async function getBooking(id: string) {
  return getDb(false) // Use replica for reads
    .select()
    .from(bookings)
    .where(eq(bookings.id, id));
}

async function createBooking(data: NewBooking) {
  return getDb(true) // Use primary for writes
    .insert(bookings)
    .values(data)
    .returning();
}
```

### Connection Pooling with PgBouncer

```ini
; pgbouncer.ini

[databases]
travel_agency = host=db.primary.internal port=5432

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432

; Pool configuration
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3

; Timeouts
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15
query_timeout = 300

; Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

---

## Rate Limiting

### Token Bucket Algorithm

```typescript
// lib/rate-limit/token-bucket.ts

interface TokenBucketConfig {
  rate: number;      // Tokens per interval
  interval: number;   // Interval in milliseconds
  capacity: number;   // Maximum bucket size
}

class TokenBucket {
  private tokens: number;
  private lastUpdate: number;

  constructor(private config: TokenBucketConfig) {
    this.tokens = config.capacity;
    this.lastUpdate = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastUpdate;

    // Calculate tokens to add based on elapsed time
    const tokensToAdd = (elapsed / this.config.interval) * this.config.rate;

    this.tokens = Math.min(this.config.capacity, this.tokens + tokensToAdd);
    this.lastUpdate = now;
  }

  tryConsume(tokens: number = 1): boolean {
    this.refill();

    if (this.tokens >= tokens) {
      this.tokens -= tokens;
      return true;
    }

    return false;
  }

  // Time until next token available
  getRetryAfter(): number {
    this.refill();

    if (this.tokens >= 1) {
      return 0;
    }

    const tokensNeeded = 1 - this.tokens;
    const timeToWait = (tokensNeeded / this.config.rate) * this.config.interval;

    return Math.ceil(timeToWait / 1000); // Return in seconds
  }
}

// Rate limiter storage
const limiters = new Map<string, TokenBucket>();

// Rate limiting middleware
export function rateLimit(config: TokenBucketConfig & {
  keyGenerator: (req: Request) => string;
}) {
  return async (req: Request, res: Response, next: () => void) => {
    const key = config.keyGenerator(req);

    let limiter = limiters.get(key);
    if (!limiter) {
      limiter = new TokenBucket(config);
      limiters.set(key, limiter);
    }

    if (limiter.tryConsume()) {
      next();
    } else {
      const retryAfter = limiter.getRetryAfter();

      return new Response(
        JSON.stringify({ error: 'Rate limit exceeded' }),
        {
          status: 429,
          headers: {
            'Retry-After': retryAfter.toString(),
            'X-RateLimit-Limit': config.capacity.toString(),
            'X-RateLimit-Remaining': '0',
          },
        }
      );
    }
  };
}

// Usage
const apiRateLimit = rateLimit({
  rate: 100,        // 100 requests
  interval: 60000,   // per minute
  capacity: 200,     // burst capacity
  keyGenerator: (req) => {
    const url = new URL(req.url);
    const userId = req.headers.get('x-user-id');
    return userId ? `user:${userId}` : `ip:${req.headers.get('x-forwarded-for')}`;
  },
});
```

### Tiered Rate Limiting

```typescript
// lib/rate-limit/tiered.ts

interface RateLimitTier {
  name: string;
  requests: number;
  window: number; // seconds
}

export const rateLimitTiers: Record<string, RateLimitTier> = {
  free: {
    name: 'Free',
    requests: 100,
    window: 3600, // 100 requests per hour
  },
  basic: {
    name: 'Basic',
    requests: 1000,
    window: 3600, // 1000 requests per hour
  },
  pro: {
    name: 'Pro',
    requests: 10000,
    window: 3600, // 10000 requests per hour
  },
  enterprise: {
    name: 'Enterprise',
    requests: 100000,
    window: 3600, // 100000 requests per hour
  },
};

export async function getUserTier(userId: string): Promise<RateLimitTier> {
  const user = await db.query.users.findFirst({
    where: eq(users.id, userId),
    columns: { tier: true },
  });

  return rateLimitTiers[user?.tier || 'free'];
}
```

---

## Auto-Scaling

### Kubernetes HPA

```yaml
# infrastructure/k8s/hpa.yaml

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: travel-agency-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: travel-agency-api
  minReplicas: 2
  maxReplicas: 20

  # Scale based on CPU
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    # Scale based on memory
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Scale based on requests per second
    - type: Pods
      pods:
        metric:
          name: requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"

  # Scaling behavior
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
        - type: Pods
          value: 2
          periodSeconds: 60
      selectPolicy: Max

    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
        - type: Pods
          value: 1
          periodSeconds: 60
      selectPolicy: Min
```

### Scheduled Scaling

```yaml
# infrastructure/k8s/scaled-schedule.yaml

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: travel-agency-api-business-hours
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: travel-agency-api

  # Higher capacity during business hours
  minReplicas: 5
  maxReplicas: 30

  # Time-based scaling using cron
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60

---
# Separate configuration for off-hours
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: travel-agency-api-off-hours
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: travel-agency-api

  # Lower capacity during off-hours
  minReplicas: 2
  maxReplicas: 10

  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
```

### Predictive Scaling

```typescript
// infrastructure/scaling/predictive.ts

import * as nats from 'nats';

// Predict scaling based on historical patterns
export class PredictiveScaler {
  private forecastData: Map<string, number[]>;

  constructor() {
    this.forecastData = new Map();
  }

  async loadHistoricalData() {
    // Load last 30 days of traffic data
    const data = await loadTrafficMetrics({ days: 30 });

    // Group by hour of day
    const hourlyData = this.groupByHour(data);

    // Calculate hourly averages
    for (const [hour, values] of hourlyData.entries()) {
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      const trend = this.calculateTrend(values);

      this.forecastData.set(hour, [avg, trend]);
    }
  }

  predictTraffic(date: Date): number {
    const hour = date.getHours().toString().padStart(2, '0');
    const dayOfWeek = date.getDay();

    const baseValue = this.forecastData.get(hour)?.[0] || 0;
    const trend = this.forecastData.get(hour)?.[1] || 0;

    // Apply day-of-week multiplier
    const dowMultiplier = this.getDOWMultiplier(dayOfWeek);

    return Math.round(baseValue * trend * dowMultiplier);
  }

  getRecommendedInstances(predictedRPS: number): number {
    // Each instance can handle ~500 RPS
    const baseInstances = Math.ceil(predictedRPS / 500);

    // Add buffer for spikes
    return Math.ceil(baseInstances * 1.3);
  }

  private getDOWMultiplier(day: number): number {
    const multipliers: Record<number, number> = {
      0: 0.8, // Sunday
      1: 1.0, // Monday
      2: 1.0, // Tuesday
      3: 1.0, // Wednesday
      4: 1.0, // Thursday
      5: 1.2, // Friday
      6: 0.9, // Saturday
    };

    return multipliers[day] || 1;
  }

  private calculateTrend(values: number[]): number {
    // Simple linear regression
    const n = values.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = values.reduce((sum, y, i) => sum + i * y, 0);
    const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);

    return 1 + slope / 100; // Return as multiplier
  }
}

// Scheduled scaling based on predictions
export async function schedulePredictiveScaling() {
  const scaler = new PredictiveScaler();
  await scaler.loadHistoricalData();

  // Get predictions for next 24 hours
  const predictions: Array<{ hour: number; instances: number }> = [];

  for (let i = 0; i < 24; i++) {
    const date = new Date();
    date.setHours(date.getHours() + i);

    const predictedRPS = scaler.predictTraffic(date);
    const instances = scaler.getRecommendedInstances(predictedRPS);

    predictions.push({ hour: date.getHours(), instances });
  }

  // Apply to Kubernetes HPA
  await updateHPAMinReplicas(predictions);
}
```

---

## Summary

Scalability patterns for the travel agency platform:

- **Scaling Strategy**: Horizontal for stateless services, vertical for database
- **Load Balancing**: Application LB, global routing, health checks
- **CDN**: Cloudflare for static assets, API caching, image optimization
- **Database Scaling**: Read replicas, connection pooling, PgBouncer
- **Rate Limiting**: Token bucket algorithm, tiered limits
- **Auto-Scaling**: Kubernetes HPA, scheduled scaling, predictive scaling

**Key Targets:**
- Handle 10,000 concurrent users
- Scale to 100M+ requests/day
- < 100ms p95 latency
- 99.9% uptime SLA

---

**Next:** [Part 5: Monitoring & Alerting](./PERFORMANCE_SCALABILITY_05_MONITORING.md) — APM, metrics, dashboards, and incident response
