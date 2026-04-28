# API Gateway — Rate Limiting & Throttling

> Research document for rate limiting strategies, quota management, and abuse prevention.

---

## Key Questions

1. **What rate limits are appropriate for different API consumers (agents, customers, partners, internal)?**
2. **How do we implement rate limiting without redis dependency for simple cases?**
3. **What's the response when limits are hit — reject, queue, or degrade?**
4. **How do we handle burst traffic during peak booking seasons?**
5. **What's the monitoring and alerting for rate limit events?**

---

## Research Areas

### Rate Limiting Strategies

```typescript
type LimitStrategy =
  | 'fixed_window'          // X requests per minute/hour
  | 'sliding_window'        // Smoother than fixed window
  | 'token_bucket'          // Allow bursts, refill over time
  | 'leaky_bucket'          // Smooth output rate
  | 'concurrent';           // Max simultaneous requests

interface RateLimitConfig {
  strategy: LimitStrategy;
  limits: RateLimitTier[];
  keyFunction: KeyFunction;
  store: 'memory' | 'redis' | 'database';
  response: LimitResponse;
}

interface RateLimitTier {
  tier: string;                   // 'anonymous', 'agent', 'partner', 'internal'
  requestsPerMinute: number;
  requestsPerHour: number;
  requestsPerDay: number;
  burstAllowance: number;
  concurrentMax: number;
}

type KeyFunction =
  | 'ip'                    // Limit by IP address
  | 'user_id'               // Limit by authenticated user
  | 'api_key'               // Limit by API key
  | 'tenant'                // Limit by organization/tenant
  | 'composite';            // Combination of factors

interface LimitResponse {
  statusCode: number;             // 429 Too Many Requests
  headers: {
    'X-RateLimit-Limit': number;
    'X-RateLimit-Remaining': number;
    'X-RateLimit-Reset': number;
  };
  body: {
    error: string;
    retryAfter: number;           // Seconds
    documentationUrl: string;
  };
}
```

### Tiered Limits by Consumer

| Consumer | Per Minute | Per Hour | Per Day | Burst | Rationale |
|----------|-----------|----------|---------|-------|-----------|
| Anonymous | 10 | 100 | 500 | 20 | Prevent scraping |
| Customer (auth) | 30 | 500 | 2,000 | 50 | Normal browsing |
| Agent (web) | 60 | 2,000 | 10,000 | 100 | Active work |
| Agent (API) | 120 | 5,000 | 50,000 | 200 | Automated workflows |
| Partner API | 100 | 10,000 | 100,000 | 300 | Integration partner |
| Internal service | 500 | Unlimited | Unlimited | 1000 | No limit needed |

### Abuse Detection

```typescript
interface AbuseDetector {
  patterns: AbusePattern[];
  actions: AbuseAction[];
}

interface AbusePattern {
  name: string;
  detection: string;              // e.g., "same IP, 100+ req/min to /api/search"
  threshold: number;
  window: string;
}

type AbuseAction =
  | { type: 'block_temporarily'; duration: string }
  | { type: 'captcha_challenge' }
  | { type: 'require_authentication' }
  | { type: 'alert_security_team' }
  | { type: 'ip_blacklist'; duration: string };

// Common abuse patterns:
// 1. Scraping — rapid sequential requests to listing endpoints
// 2. Credential stuffing — repeated login attempts
// 3. Price scraping — repeated search queries with no bookings
// 4. Inventory probing — checking availability without booking
// 5. API key sharing — one key used from many IPs
```

---

## Open Problems

1. **Distributed rate limiting** — If we run multiple gateway instances, in-memory limits don't share state. Need Redis or a distributed counter.

2. **Legitimate burst traffic** — Peak booking season (Diwali, summer) may see 10x normal traffic. Fixed limits may block legitimate users.

3. **Rate limit bypass** — Sophisticated abusers rotate IPs or use distributed attacks. IP-based limiting is insufficient.

4. **Rate limit per supplier API** — Our outbound calls to supplier APIs (airlines, hotels) also have rate limits. Need back-pressure from supplier limits.

5. **Graceful degradation** — Instead of hard 429 errors, can we degrade service (simpler responses, cached data) when approaching limits?

---

## Next Steps

- [ ] Evaluate rate limiting libraries (rate-limiter-flexible, express-rate-limit)
- [ ] Design tiered limit configuration for current API consumers
- [ ] Implement standard rate limit response headers
- [ ] Study abuse detection patterns for travel APIs
- [ ] Design auto-scaling for peak traffic handling
