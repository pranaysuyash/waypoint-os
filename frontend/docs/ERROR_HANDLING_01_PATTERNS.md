# Error Handling & Resilience — Patterns & Architecture

> Research document for error handling patterns, circuit breakers, and graceful degradation.

---

## Key Questions

1. **What error categories exist, and how should each be handled differently?**
2. **When do we retry vs. fail fast vs. degrade gracefully?**
3. **How do we implement circuit breakers for external service dependencies?**
4. **What's the error propagation model from backend to frontend?**
5. **How do we present errors to agents without exposing internal details?**

---

## Research Areas

### Error Taxonomy

```typescript
type ErrorCategory =
  // Client errors (4xx equivalent)
  | 'validation'            // Invalid input, missing fields
  | 'authentication'        // Not logged in, token expired
  | 'authorization'         // Insufficient permissions
  | 'not_found'             // Resource doesn't exist
  | 'conflict'              // Concurrent modification
  | 'rate_limited'          // Too many requests
  // Service errors (5xx equivalent)
  | 'internal'              // Unexpected server error
  | 'external_service'      // Third-party API failure
  | 'timeout'               // Request timed out
  | 'circuit_open'          // Circuit breaker tripped
  // Business errors
  | 'booking_failed'        // Booking couldn't be completed
  | 'payment_failed'        // Payment processing error
  | 'inventory_unavailable' // Sold out / no availability
  | 'policy_violation'      // Business rule violated
  | 'spine_failure';        // Spine processing error

interface AppError {
  code: string;                   // Machine-readable: "BOOKING.INVENTORY_UNAVAILABLE"
  category: ErrorCategory;
  message: string;                // User-readable: "This hotel is sold out for your dates"
  detail?: string;                // Agent-readable: "Marriott Mumbai: 0 rooms available for Jun 15-17"
  retryable: boolean;
  retryAfter?: number;            // Seconds
  suggestedAction?: string;       // "Try a different hotel or date"
  context?: Record<string, unknown>;
  correlationId: string;          // For tracing
  timestamp: Date;
}
```

### Retry Strategies

```typescript
interface RetryConfig {
  maxRetries: number;
  backoffStrategy: BackoffStrategy;
  retryableErrors: ErrorCategory[];
  idempotencyKey: string;         // Prevent duplicate side effects
}

type BackoffStrategy =
  | { type: 'fixed'; delayMs: number }
  | { type: 'exponential'; baseMs: number; maxMs: number; jitter: boolean }
  | { type: 'linear'; incrementMs: number };

// Retry rules:
// External API timeout → Retry with exponential backoff (2s, 4s, 8s)
// External API 5xx → Retry up to 3 times
// External API 4xx → No retry (client error)
// Database connection lost → Retry with fixed 1s backoff
// Payment failed → No auto-retry (manual intervention)
// Booking conflict → No retry (inform user)
```

### Circuit Breaker

```typescript
interface CircuitBreakerConfig {
  serviceName: string;
  failureThreshold: number;       // Failures before opening
  resetTimeoutMs: number;         // Time before half-open attempt
  halfOpenMaxRequests: number;    // Test requests in half-open
  monitoringWindowMs: number;     // Window for counting failures
}

// States:
// CLOSED → Normal operation, requests pass through
// OPEN → Requests fail fast, no calls to service
// HALF_OPEN → Testing if service recovered

// Circuit breakers for:
// - Hotel supplier APIs (Amadeus, Sabre)
// - Airline GDS
// - Payment gateway
// - Email/SMS service
// - Document generation
// - Spine processing pipeline
```

### Graceful Degradation

```typescript
interface DegradationConfig {
  feature: string;
  dependencies: string[];
  fallbackStrategy: FallbackStrategy;
}

type FallbackStrategy =
  | { type: 'cached_data'; maxAge: string }              // Show stale data
  | { type: 'reduced_functionality'; disabledFeatures: string[] }
  | { type: 'alternative_service'; service: string }     // Use backup provider
  | { type: 'manual_fallback'; message: string }         // "Contact support"
  | { type: 'queue_and_notify'; message: string };       // Process later

// Degradation examples:
// Hotel search API down → Show cached results (max 1 hour old) + "Prices may have changed" banner
// Payment gateway down → Queue payment, notify agent, process when recovered
// Spine API down → Allow manual intake, queue for processing
// Map service down → Show text-based directions instead of map
// Email service down → Queue notifications, show in-app only
```

---

## Open Problems

1. **Cascading failures** — Hotel API failure may cascade to booking failure, which cascades to payment failure. Need bulkhead isolation.

2. **Partial success** — A booking request succeeds for hotel but fails for flight. What state is the booking in? Need saga compensation.

3. **Error message design** — "Internal server error" is useless. "The hotel booking service is temporarily unavailable" is better. But too much detail (stack traces) is a security risk.

4. **Silent failures** — Some errors don't surface (webhook delivery failure, background job crash). Need proactive monitoring, not just reactive error handling.

5. **Error aggregation** — During a mass outage, thousands of errors flood the system. Need deduplication and aggregation for alerting.

---

## Next Steps

- [ ] Catalog all external service dependencies and failure modes
- [ ] Implement circuit breaker for top 3 external APIs calls
- [ ] Design error response format for API (RFC 7807 Problem Details)
- [ ] Create error message catalog with user-friendly + agent-friendly variants
- [ ] Study resilience patterns (Netflix Hystrix, Resilience4j, Polly)
