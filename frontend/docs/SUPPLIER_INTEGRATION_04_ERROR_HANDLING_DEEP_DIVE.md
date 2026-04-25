# Supplier Integration — Error Handling Deep Dive

> Fallback strategies, retry logic, circuit breakers, and graceful degradation

---

## Document Overview

**Series:** Supplier Integration Deep Dive
**Document:** 4 of 4
**Last Updated:** 2026-04-25
**Status:** ✅ Complete

**Previous Documents:**
1. [Technical Deep Dive](./SUPPLIER_INTEGRATION_01_TECHNICAL_DEEP_DIVE.md) — Architecture, API patterns, rate limiting
2. [Data Deep Dive](./SUPPLIER_INTEGRATION_02_DATA_DEEP_DIVE.md) — Data models, mapping, normalization
3. [Caching Deep Dive](./SUPPLIER_INTEGRATION_03_CACHING_DEEP_DIVE.md) — Cache strategies, invalidation, sync

---

## Table of Contents

1. [Error Taxonomy](#error-taxonomy)
2. [Retry Strategies](#retry-strategies)
3. [Circuit Breaker Pattern](#circuit-breaker-pattern)
4. [Fallback Suppliers](#fallback-suppliers)
5. [Graceful Degradation](#graceful-degradation)
6. [Error Monitoring](#error-monitoring)
7. [Supplier Health Tracking](#supplier-health-tracking)
8. [Implementation Reference](#implementation-reference)

---

## Error Taxonomy

### Error Classification

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPLIER ERROR CLASSIFICATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  TRANSIENT      │  │  PERMANENT      │  │  BUSINESS       │             │
│  │  (Retryable)    │  │  (Non-Retryable)│  │  (Action Needed)│             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  • Timeout          • Invalid Auth      • Insufficient Funds               │
│  • Rate Limit       • Invalid Request   • No Availability                   │
│  • 5xx Server       • Not Found         • Price Changed                     │
│  • Network Error    • Unsupported       • Booking Failed                    │
│  • Temp Unavailable                                                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HTTP STATUS MAPPING                                                        │
│  ────────────────────                                                       │
│                                                                             │
│  429 Too Many Requests    → TRANSIENT (Rate Limit)                          │
│  500 Internal Error       → TRANSIENT (Server Error)                       │
│  502 Bad Gateway          → TRANSIENT (Upstream Issue)                     │
│  503 Service Unavailable  → TRANSIENT (Temp Down)                          │
│  504 Gateway Timeout      → TRANSIENT (Timeout)                            │
│                                                                             │
│  400 Bad Request          → PERMANENT (Client Error)                       │
│  401 Unauthorized         → PERMANENT (Auth Required)                      │
│  403 Forbidden            → PERMANENT (No Permission)                      │
│  404 Not Found            → PERMANENT (Invalid Resource)                   │
│                                                                             │
│  200 + Error Code         → BUSINESS (Supplier Logic)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Error Response Structure

```typescript
/**
 * Standardized error response from supplier adapters
 */
interface SupplierError {
  // Error classification
  type: 'TRANSIENT' | 'PERMANENT' | 'BUSINESS';

  // HTTP status (if applicable)
  status?: number;

  // Error code from supplier
  code: string;

  // Human-readable message
  message: string;

  // Additional context
  details?: {
    supplier: string;
    endpoint: string;
    requestId?: string;
    correlationId: string;
    timestamp: Date;
    retryable: boolean;
    retryAfter?: number; // seconds
  };

  // Original error for debugging
  original?: unknown;

  // Suggested actions
  actions?: ErrorAction[];
}

interface ErrorAction {
  type: 'RETRY' | 'FALLBACK' | 'ESCALATE' | 'IGNORE';
  description: string;
  params?: Record<string, unknown>;
}
```

### Error Code Mapping by Supplier

```typescript
/**
 * Supplier-specific error code mappings
 */
const SUPPLIER_ERROR_CODES: Record<string, Record<string, SupplierErrorType>> = {
  TBO: {
    'TBO-001': 'TRANSIENT',   // Timeout
    'TBO-002': 'TRANSIENT',   // Rate limit
    'TBO-401': 'PERMANENT',   // Invalid credentials
    'TBO-404': 'PERMANENT',   // Hotel not found
    'TBO-500': 'TRANSIENT',   // Server error
    'TBO-A01': 'BUSINESS',    // No availability
    'TBO-A02': 'BUSINESS',    // Price changed
  },
  TravelBoutique: {
    'TB-1001': 'TRANSIENT',   // System busy
    'TB-1002': 'TRANSIENT',   // Temp unavailable
    'TB-2001': 'PERMANENT',   // Invalid auth
    'TB-3001': 'BUSINESS',    // Sold out
    'TB-3002': 'BUSINESS',    // Invalid booking
  },
  MakCorp: {
    'MK-ERR-01': 'TRANSIENT', // Connection failed
    'MK-ERR-02': 'PERMANENT', // Invalid API key
    'MK-ERR-03': 'BUSINESS',  // Rate exceeded (quota)
    'MK-ERR-10': 'BUSINESS',  // No inventory
  }
};
```

---

## Retry Strategies

### Retry Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RETRY STRATEGY MATRIX                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Error Type              │ Strategy              │ Max Retries              │
│  ──────────────────────  │ ───────────────────── │ ──────────────────────   │
│  Network Timeout         │ Exponential Backoff   │ 3                        │
│  Rate Limit (429)        │ Respect Retry-After   │ 5 (with delay)           │
│  5xx Server Error        │ Exponential Backoff   │ 2                        │
│  Connection Refused      │ Immediate + Backoff   │ 3                        │
│  DNS Failure             │ Exponential Backoff   │ 2                        │
│  Read Timeout            │ Exponential Backoff   │ 2                        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NO RETRY:                                                                  │
│  • 4xx Client Errors (except 429)                                           │
│  • Authentication Failures                                                  │
│  • Invalid Request Parameters                                               │
│  • Business Logic Errors (sold out, price changed)                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Exponential Backoff Implementation

```typescript
/**
 * Retry configuration for supplier calls
 */
interface RetryConfig {
  maxAttempts: number;
  initialDelay: number;    // milliseconds
  maxDelay: number;        // milliseconds
  multiplier: number;      // backoff multiplier
  jitter: boolean;         // add randomness
  jitterFactor: number;    // 0-1, amount of randomness
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  initialDelay: 1000,     // 1 second
  maxDelay: 30000,        // 30 seconds
  multiplier: 2,          // exponential
  jitter: true,
  jitterFactor: 0.1       // ±10%
};

/**
 * Calculate delay with exponential backoff and jitter
 */
function calculateRetryDelay(
  attempt: number,
  config: RetryConfig
): number {
  // Exponential backoff
  const exponentialDelay = Math.min(
    config.initialDelay * Math.pow(config.multiplier, attempt - 1),
    config.maxDelay
  );

  if (!config.jitter) {
    return exponentialDelay;
  }

  // Add jitter to prevent thundering herd
  const jitterRange = exponentialDelay * config.jitterFactor;
  const jitter = (Math.random() * 2 - 1) * jitterRange;

  return Math.max(0, exponentialDelay + jitter);
}

/**
 * Retry wrapper with exponential backoff
 */
async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
  isRetryable: (error: unknown) => boolean = defaultIsRetryable
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      // Check if error is retryable
      if (!isRetryable(error)) {
        throw error;
      }

      // Don't delay after last attempt
      if (attempt < config.maxAttempts) {
        const delay = calculateRetryDelay(attempt, config);

        logger.info('Retrying operation after error', {
          attempt,
          maxAttempts: config.maxAttempts,
          delay,
          error: error instanceof Error ? error.message : 'Unknown error'
        });

        await sleep(delay);
      }
    }
  }

  throw lastError;
}

/**
 * Default retryable error detection
 */
function defaultIsRetryable(error: unknown): boolean {
  // Network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }

  // Supplier errors
  if (isSupplierError(error)) {
    return error.type === 'TRANSIENT';
  }

  // HTTP errors
  if (isHttpError(error)) {
    const status = error.status;
    return status === 429 || status >= 500;
  }

  return false;
}
```

### Rate Limit Retry Strategy

```typescript
/**
 * Specialized retry handler for rate limits
 */
class RateLimitRetryHandler {
  async handleRetry(
    error: SupplierError,
    attempt: number,
    maxAttempts: number
  ): Promise<boolean> {
    if (error.code !== 'RATE_LIMIT_EXCEEDED') {
      return false;
    }

    // Use Retry-After header if present
    if (error.details?.retryAfter) {
      const retryAfter = error.details.retryAfter * 1000;

      logger.info('Rate limited, respecting Retry-After', {
        retryAfter,
        attempt,
        maxAttempts
      });

      await sleep(retryAfter);
      return true;
    }

    // Exponential backoff for rate limits
    const delay = Math.min(
      1000 * Math.pow(2, attempt),
      60000 // max 1 minute
    );

    logger.info('Rate limited, using exponential backoff', {
      delay,
      attempt,
      maxAttempts
    });

    await sleep(delay);
    return true;
  }
}
```

### Retry Queue Integration

```typescript
/**
 * Bull queue for retrying failed supplier operations
 */
import { Queue, Worker, Job } from 'bullmq';

interface RetryJobData {
  supplier: string;
  operation: 'search' | 'quote' | 'book' | 'cancel';
  params: unknown;
  attempt: number;
  maxAttempts: number;
  correlationId: string;
  lastError?: SupplierError;
}

class SupplierRetryQueue {
  private queue: Queue<RetryJobData>;
  private worker: Worker<RetryJobData>;

  constructor(redis: Redis) {
    this.queue = new Queue('supplier-retries', { connection: redis });

    this.worker = new Worker(
      'supplier-retries',
      async (job: Job<RetryJobData>) => {
        return await this.processRetry(job);
      },
      { connection: redis }
    );

    this.worker.on('completed', (job) => {
      logger.info('Retry job completed', { jobId: job.id });
    });

    this.worker.on('failed', (job, err) => {
      logger.error('Retry job failed', {
        jobId: job?.id,
        error: err
      });
    });
  }

  async scheduleRetry(data: RetryJobData, delay: number): Promise<void> {
    await this.queue.add('retry', data, {
      delay,
      attempts: data.maxAttempts - data.attempt,
      backoff: {
        type: 'exponential',
        delay: 1000
      }
    });
  }

  private async processRetry(job: Job<RetryJobData>): Promise<void> {
    const { supplier, operation, params, attempt, maxAttempts } = job.data;

    try {
      const adapter = await this.getAdapter(supplier);
      const result = await withRetry(
        () => adapter.execute(operation, params),
        { maxAttempts: maxAttempts - attempt + 1 }
      );

      // Store result or notify
      await this.handleSuccess(job.data.correlationId, result);
    } catch (error) {
      if (attempt >= maxAttempts) {
        await this.handleFailure(job.data.correlationId, error as SupplierError);
      }
      throw error;
    }
  }
}
```

---

## Circuit Breaker Pattern

### Circuit Breaker States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CIRCUIT BREAKER STATE MACHINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────┐                                                             │
│    │  CLOSED │◄────────────────────┐                                       │
│    │ (Normal │       Success       │                                       │
│    │  Pass)  │◄────────────────────┘                                       │
│    └────┬────┘                                                             │
│         │                                                                   │
│         │ Failure Threshold Reached                                        │
│         │ (e.g., 5 failures in 100 requests)                               │
│         │                                                                   │
│         ▼                                                                   │
│    ┌─────────┐     Timeout/Manual Reset     ┌─────────┐                    │
│    │  OPEN   │─────────────────────────────►│  CLOSED │                    │
│    │ (Block  │                             │         │                    │
│    │  Calls) │─────────────────────────────►│         │                    │
│    └────┬────┘     Half-Open Success       └─────────┘                    │
│         │                                                                   │
│         │ Half-Open Timeout                                                 │
│         │                                                                   │
│         ▼                                                                   │
│    ┌─────────┐                                                             │
│    │HALF-OPEN│◄────────────────────┐                                       │
│    │ (Test   │       Timeout        │                                       │
│    │  Calls) │◄────────────────────┘                                       │
│    └─────────┘                                                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATE TRANSITIONS:                                                         │
│  CLOSED → OPEN:     Failure threshold exceeded                              │
│  OPEN → HALF-OPEN:  Timeout expired (test if recovered)                     │
│  HALF-OPEN → CLOSED: Test call succeeded                                    │
│  HALF-OPEN → OPEN:   Test call failed (back to blocking)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Circuit Breaker Implementation

```typescript
/**
 * Circuit breaker configuration
 */
interface CircuitBreakerConfig {
  // Failure threshold
  failureThreshold: number;      // failures to open circuit
  samplingPeriod: number;        // milliseconds

  // Open state
  openTimeout: number;           // milliseconds before half-open

  // Half-open state
  permittedCalls: number;        // calls allowed in half-open

  // Success threshold
  successThreshold: number;      // successes to close circuit
}

const DEFAULT_CIRCUIT_CONFIG: CircuitBreakerConfig = {
  failureThreshold: 5,           // 5 failures
  samplingPeriod: 60000,         // in 60 seconds
  openTimeout: 30000,            // stay open for 30 seconds
  permittedCalls: 3,             // allow 3 test calls
  successThreshold: 2            // need 2 successes to close
};

/**
 * Circuit breaker state
 */
type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface CircuitStats {
  failures: number;
  successes: number;
  totalCalls: number;
  lastFailureTime?: Date;
  lastSuccessTime?: Date;
  openedAt?: Date;
}

/**
 * Circuit breaker implementation
 */
class CircuitBreaker {
  private config: CircuitBreakerConfig;
  private state: CircuitState = 'CLOSED';
  private stats: CircuitStats = {
    failures: 0,
    successes: 0,
    totalCalls: 0
  };
  private halfOpenCalls = 0;
  private failureWindow: Date[] = [];

  constructor(
    private readonly supplier: string,
    config: Partial<CircuitBreakerConfig> = {}
  ) {
    this.config = { ...DEFAULT_CIRCUIT_CONFIG, ...config };
  }

  /**
   * Execute operation with circuit breaker protection
   */
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    // Check if circuit is open
    if (this.state === 'OPEN') {
      if (this.shouldAttemptReset()) {
        this.transitionTo('HALF_OPEN');
      } else {
        throw new CircuitOpenError(
          `Circuit open for supplier ${this.supplier}`,
          this.stats
        );
      }
    }

    // Check half-open limit
    if (this.state === 'HALF_OPEN') {
      if (this.halfOpenCalls >= this.config.permittedCalls) {
        throw new CircuitOpenError(
          `Circuit half-open, max calls exceeded for ${this.supplier}`,
          this.stats
        );
      }
      this.halfOpenCalls++;
    }

    // Execute operation
    this.stats.totalCalls++;
    const startTime = Date.now();

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  /**
   * Handle successful operation
   */
  private onSuccess(): void {
    this.stats.successes++;
    this.stats.lastSuccessTime = new Date();

    if (this.state === 'HALF_OPEN') {
      // Check if we should close the circuit
      const recentSuccesses = this.getRecentSuccesses();
      if (recentSuccesses >= this.config.successThreshold) {
        this.transitionTo('CLOSED');
        this.halfOpenCalls = 0;
      }
    }
  }

  /**
   * Handle failed operation
   */
  private onFailure(): void {
    this.stats.failures++;
    this.stats.lastFailureTime = new Date();

    // Add to failure window
    this.failureWindow.push(new Date());

    // Trim old failures
    const cutoff = new Date(Date.now() - this.config.samplingPeriod);
    this.failureWindow = this.failureWindow.filter(d => d > cutoff);

    // Check if we should open the circuit
    if (this.failureWindow.length >= this.config.failureThreshold) {
      this.transitionTo('OPEN');
    } else if (this.state === 'HALF_OPEN') {
      // Fail in half-open goes back to open
      this.transitionTo('OPEN');
      this.halfOpenCalls = 0;
    }
  }

  /**
   * Transition to new state
   */
  private transitionTo(newState: CircuitState): void {
    const oldState = this.state;
    this.state = newState;

    if (newState === 'OPEN') {
      this.stats.openedAt = new Date();
    }

    logger.info('Circuit breaker state transition', {
      supplier: this.supplier,
      from: oldState,
      to: newState,
      stats: this.stats
    });

    // Emit event for monitoring
    this.emitStateChange(oldState, newState);
  }

  /**
   * Check if we should attempt reset
   */
  private shouldAttemptReset(): boolean {
    if (!this.stats.openedAt) return false;

    const timeSinceOpen = Date.now() - this.stats.openedAt.getTime();
    return timeSinceOpen >= this.config.openTimeout;
  }

  /**
   * Get recent successes in sampling period
   */
  private getRecentSuccesses(): number {
    // Simplified - in production, track success window like failures
    return this.stats.successes;
  }

  /**
   * Get current state
   */
  getState(): { state: CircuitState; stats: CircuitStats } {
    return {
      state: this.state,
      stats: { ...this.stats }
    };
  }

  /**
   * Manually reset circuit (for admin operations)
   */
  reset(): void {
    this.transitionTo('CLOSED');
    this.stats = {
      failures: 0,
      successes: 0,
      totalCalls: 0
    };
    this.failureWindow = [];
    this.halfOpenCalls = 0;
  }

  private emitStateChange(from: CircuitState, to: CircuitState): void {
    // Emit to monitoring system
    // ...
  }
}

/**
 * Error thrown when circuit is open
 */
class CircuitOpenError extends Error {
  constructor(
    message: string,
    public readonly stats: CircuitStats
  ) {
    super(message);
    this.name = 'CircuitOpenError';
  }
}
```

### Circuit Breaker Registry

```typescript
/**
 * Registry for managing multiple circuit breakers
 */
class CircuitBreakerRegistry {
  private breakers = new Map<string, CircuitBreaker>();

  get(supplier: string): CircuitBreaker {
    if (!this.breakers.has(supplier)) {
      this.breakers.set(
        supplier,
        new CircuitBreaker(supplier)
      );
    }
    return this.breakers.get(supplier)!;
  }

  getAllStates(): Record<string, { state: CircuitState; stats: CircuitStats }> {
    const result: Record<string, unknown> = {};

    for (const [supplier, breaker] of this.breakers) {
      result[supplier] = breaker.getState();
    }

    return result as Record<string, { state: CircuitState; stats: CircuitStats }>;
  }

  reset(supplier: string): void {
    this.breakers.get(supplier)?.reset();
  }

  resetAll(): void {
    for (const breaker of this.breakers.values()) {
      breaker.reset();
    }
  }
}

// Global registry
export const circuitBreakerRegistry = new CircuitBreakerRegistry();
```

---

## Fallback Suppliers

### Fallback Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FALLBACK SUPPLIER CHAIN                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Request ──► Primary Supplier ──┬── Success ──► Return Result               │
│                 (TBO)            │                                           │
│                                  ├── Circuit Open ──► Try Fallback 1        │
│                                  └── Error ──► Check Error Type             │
│                                                                             │
│  Fallback 1 ──────────────────────┬── Success ──► Return Result             │
│               (TravelBoutique)     │                                           │
│                                    └── Error ──► Try Fallback 2             │
│                                                                             │
│  Fallback 2 ──────────────────────┬── Success ──► Return Result             │
│               (MakCorp)            │                                           │
│                                    └── Error ──► Return Aggregated Error    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FALLBACK TRIGGERS:                                                         │
│  • Circuit breaker is OPEN                                                  │
│  • TRANSIENT error after max retries                                        │
│  • Timeout exceeded                                                         │
│                                                                             │
│  NO FALLBACK:                                                               │
│  • PERMANENT errors (auth, invalid request)                                 │
│  • BUSINESS errors specific to primary (sold out)                           │
│  • Operations that can't be retried (booking, cancel)                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fallback Configuration

```typescript
/**
 * Fallback chain configuration
 */
interface FallbackConfig {
  primary: string;
  fallbacks: string[];
  enableForOperations: ('search' | 'quote')[];
  fallbackTimeout: number;  // max time to spend on fallbacks
}

/**
 * Fallback chains by supplier category
 */
const FALLBACK_CHAINS: Record<string, FallbackConfig> = {
  HOTELS: {
    primary: 'TBO',
    fallbacks: ['TravelBoutique', 'MakCorp'],
    enableForOperations: ['search', 'quote'],
    fallbackTimeout: 5000  // 5 seconds max for fallbacks
  },
  FLIGHTS: {
    primary: 'TBO_Air',
    fallbacks: ['MakCorp_Air'],
    enableForOperations: ['search', 'quote'],
    fallbackTimeout: 5000
  }
};
```

### Fallback Executor

```typescript
/**
 * Execute operation with fallback chain
 */
class FallbackExecutor {
  constructor(
    private registry: SupplierAdapterRegistry,
    private circuitRegistry: CircuitBreakerRegistry
  ) {}

  async executeWithFallback<T>(
    category: string,
    operation: 'search' | 'quote',
    params: unknown,
    timeout: number
  ): Promise<T> {
    const config = FALLBACK_CHAINS[category];

    if (!config) {
      throw new Error(`No fallback chain for category: ${category}`);
    }

    if (!config.enableForOperations.includes(operation)) {
      // No fallback for this operation
      const adapter = this.registry.get(config.primary);
      return await adapter.execute(operation, params);
    }

    const suppliers = [config.primary, ...config.fallbacks];
    const errors: SupplierError[] = [];
    const startTime = Date.now();

    for (const supplierId of suppliers) {
      // Check timeout
      const elapsed = Date.now() - startTime;
      if (elapsed > timeout) {
        throw new FallbackTimeoutError(
          `Fallback chain exceeded timeout of ${timeout}ms`,
          errors
        );
      }

      // Get circuit breaker
      const circuitBreaker = this.circuitRegistry.get(supplierId);

      // Check if circuit is open
      const state = circuitBreaker.getState();
      if (state.state === 'OPEN') {
        errors.push({
          type: 'TRANSIENT',
          code: 'CIRCUIT_OPEN',
          message: `Circuit open for ${supplierId}`,
          details: { supplier: supplierId }
        } as SupplierError);
        continue;
      }

      try {
        // Execute with circuit breaker protection
        const adapter = this.registry.get(supplierId);
        const remainingTimeout = timeout - elapsed;

        const result = await this.executeWithTimeout(
          () => circuitBreaker.execute(() =>
            adapter.execute(operation, params)
          ),
          remainingTimeout
        );

        // Log successful fallback
        if (supplierId !== config.primary) {
          logger.info('Fallback supplier succeeded', {
            category,
            operation,
            primary: config.primary,
            fallback: supplierId,
            elapsed: Date.now() - startTime
          });
        }

        return result;

      } catch (error) {
        errors.push(error as SupplierError);

        // Don't continue on permanent errors
        if (error instanceof SupplierError && error.type === 'PERMANENT') {
          throw error;
        }
      }
    }

    // All suppliers failed
    throw new AllSuppliersFailedError(
      `All suppliers in fallback chain failed for ${category}.${operation}`,
      errors
    );
  }

  private async executeWithTimeout<T>(
    operation: () => Promise<T>,
    timeout: number
  ): Promise<T> {
    return Promise.race([
      operation(),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Timeout')), timeout)
      )
    ]);
  }
}

/**
 * Error thrown when fallback timeout exceeded
 */
class FallbackTimeoutError extends Error {
  constructor(
    message: string,
    public readonly errors: SupplierError[]
  ) {
    super(message);
    this.name = 'FallbackTimeoutError';
  }
}

/**
 * Error thrown when all suppliers fail
 */
class AllSuppliersFailedError extends Error {
  constructor(
    message: string,
    public readonly errors: SupplierError[]
  ) {
    super(message);
    this.name = 'AllSuppliersFailedError';
  }
}
```

---

## Graceful Degradation

### Degradation Levels

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GRACEFUL DEGRADATION LEVELS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Level 1: Full Service                                                      │
│  ─────────────────                                                          │
│  • All suppliers operational                                                │
│  • Real-time pricing                                                        │
│  • Live inventory                                                           │
│                                                                             │
│  Level 2: Cached Service                                                    │
│  ─────────────────                                                          │
│  • Suppliers slow/unavailable                                              │
│  • Serve from cache with staleness warning                                  │
│  • Indicate "prices may have changed"                                       │
│                                                                             │
│  Level 3: Limited Service                                                   │
│  ─────────────────                                                          │
│  • Most suppliers down                                                     │
│  • Read-only mode (no new bookings)                                         │
│  • Show cached inventory only                                               │
│                                                                             │
│  Level 4: Maintenance Mode                                                  │
│  ────────────────────                                                       │
│  • All suppliers down                                                       │
│  • Show maintenance page                                                    │
│  • Queue requests for later processing                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Degradation Manager

```typescript
/**
 * Service degradation level
 */
type DegradationLevel = 'FULL' | 'CACHED' | 'LIMITED' | 'MAINTENANCE';

interface DegradationStatus {
  level: DegradationLevel;
  reason: string;
  affectedSuppliers: string[];
  estimatedRecovery?: Date;
  features: {
    search: boolean;
    quote: boolean;
    book: boolean;
    cancel: boolean;
  };
}

/**
 * Manages service degradation based on supplier health
 */
class DegradationManager {
  private currentLevel: DegradationLevel = 'FULL';
  private supplierHealth = new Map<string, boolean>();

  constructor(
    private circuitRegistry: CircuitBreakerRegistry,
    private cacheManager: CacheManager
  ) {}

  /**
   * Update degradation level based on current state
   */
  async updateDegradationLevel(): Promise<DegradationStatus> {
    const states = this.circuitRegistry.getAllStates();
    const totalSuppliers = Object.keys(states).length;
    const openCircuits = Object.entries(states)
      .filter(([_, s]) => s.state === 'OPEN')
      .map(([supplier, _]) => supplier);

    const failureRate = openCircuits.length / totalSuppliers;

    // Determine degradation level
    if (failureRate === 0) {
      this.currentLevel = 'FULL';
    } else if (failureRate < 0.3) {
      this.currentLevel = 'CACHED';
    } else if (failureRate < 0.7) {
      this.currentLevel = 'LIMITED';
    } else {
      this.currentLevel = 'MAINTENANCE';
    }

    return this.getStatus();
  }

  /**
   * Get current degradation status
   */
  getStatus(): DegradationStatus {
    const states = this.circuitRegistry.getAllStates();
    const openCircuits = Object.entries(states)
      .filter(([_, s]) => s.state === 'OPEN')
      .map(([supplier, _]) => supplier);

    return {
      level: this.currentLevel,
      reason: this.getReason(),
      affectedSuppliers: openCircuits,
      features: this.getAvailableFeatures()
    };
  }

  private getReason(): string {
    switch (this.currentLevel) {
      case 'FULL':
        return 'All systems operational';
      case 'CACHED':
        return 'Some suppliers unavailable - serving cached data';
      case 'LIMITED':
        return 'Most suppliers unavailable - limited service';
      case 'MAINTENANCE':
        return 'All suppliers unavailable - maintenance mode';
    }
  }

  private getAvailableFeatures() {
    switch (this.currentLevel) {
      case 'FULL':
        return {
          search: true,
          quote: true,
          book: true,
          cancel: true
        };
      case 'CACHED':
        return {
          search: true,  // from cache
          quote: true,   // from cache with warning
          book: false,
          cancel: true
        };
      case 'LIMITED':
        return {
          search: true,  // cached only
          quote: false,
          book: false,
          cancel: true
        };
      case 'MAINTENANCE':
        return {
          search: false,
          quote: false,
          book: false,
          cancel: false
        };
    }
  }

  /**
   * Check if operation is available
   */
  isOperationAvailable(operation: keyof DegradationStatus['features']): boolean {
    return this.getAvailableFeatures()[operation];
  }
}
```

### Cached Response Handler

```typescript
/**
 * Handle requests using cached data when suppliers are down
 */
class CachedResponseHandler {
  constructor(
    private cacheManager: CacheManager,
    private degradationManager: DegradationManager
  ) {}

  async handleSearchWithCache(params: SearchParams): Promise<SearchResult> {
    const status = this.degradationManager.getStatus();

    if (status.level === 'FULL') {
      throw new Error('Should use live supplier in full mode');
    }

    // Try to get from cache
    const cacheKey = this.generateCacheKey(params);
    const cached = await this.cacheManager.get(cacheKey);

    if (!cached) {
      throw new NoCachedDataError('No cached data available');
    }

    // Add staleness warning
    const age = Date.now() - cached.timestamp;
    const warning = this.generateStalenessWarning(age);

    return {
      ...cached.data,
      _meta: {
        cached: true,
        age,
        warning,
        level: status.level
      }
    };
  }

  async handleQuoteWithCache(params: QuoteParams): Promise<QuoteResult> {
    const cached = await this.cacheManager.get(`quote:${params.hotelId}`);

    if (!cached) {
      throw new NoCachedDataError('No cached quote available');
    }

    // Add price change warning
    return {
      ...cached.data,
      _meta: {
        cached: true,
        warning: 'Price may have changed. Confirm before booking.',
        level: this.degradationManager.getStatus().level
      }
    };
  }

  private generateCacheKey(params: SearchParams): string {
    return `search:${hash(params)}`;
  }

  private generateStalenessWarning(age: number): string {
    const minutes = Math.floor(age / 60000);

    if (minutes < 15) {
      return `Data is ${minutes} minutes old. Prices may have changed.`;
    } else if (minutes < 60) {
      return `Data is ${minutes} minutes old. Prices likely changed.`;
    } else {
      return `Data is over an hour old. For current prices, try again later.`;
    }
  }
}

class NoCachedDataError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NoCachedDataError';
  }
}
```

---

## Error Monitoring

### Error Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR MONITORING DASHBOARD                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  ERROR RATE     │  │  ERROR TYPE     │  │  SUPPLIER       │             │
│  │                 │  │  DISTRIBUTION   │  │  HEALTH         │             │
│  │  Total: 2.3%    │  │                 │  │                 │             │
│  │  ────────────   │  │  TRANSIENT 60%  │  │  TBO         ●  │             │
│  │  TBO:      1.2% │  │  PERMANENT 25%  │  │  TravelBout  ●  │             │
│  │  TravelB:  3.1% │  │  BUSINESS  15%  │  │  MakCorp     ●  │             │
│  │  MakCorp:  0.8% │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  CIRCUIT        │  │  RETRY          │  │  RECENT         │             │
│  │  BREAKERS       │  │  STATISTICS     │  │  ERRORS         │             │
│  │                 │  │                 │  │                 │             │
│  │  TBO:       OPEN │  │  Total: 1,234   │  │  10:42 TBO-500  │             │
│  │  TravelB:  CLOSE│  │  Success: 89%   │  │  10:40 TB-A01   │             │
│  │  MakCorp:  HALF │  │  With Retry: 23%│  │  10:38 MK-ERR01 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Error Tracking

```typescript
/**
 * Error tracking service
 */
class ErrorTrackingService {
  private errorCounts = new Map<string, number>();
  private errorHistory: ErrorRecord[] = [];

  /**
   * Record an error
   */
  record(error: SupplierError, context: ErrorContext): void {
    const key = this.getErrorKey(error);

    // Increment count
    this.errorCounts.set(
      key,
      (this.errorCounts.get(key) || 0) + 1
    );

    // Add to history
    this.errorHistory.push({
      error,
      context,
      timestamp: new Date()
    });

    // Trim history
    if (this.errorHistory.length > 10000) {
      this.errorHistory = this.errorHistory.slice(-5000);
    }

    // Emit to monitoring
    this.emitError(error, context);
  }

  /**
   * Get error statistics
   */
  getStats(timeWindow?: number): ErrorStats {
    const now = Date.now();
    const relevantHistory = timeWindow
      ? this.errorHistory.filter(r => now - r.timestamp.getTime() < timeWindow)
      : this.errorHistory;

    return {
      total: relevantHistory.length,
      byType: this.groupBy(relevantHistory, 'type'),
      bySupplier: this.groupBy(relevantHistory, 'supplier'),
      byCode: this.groupByCode(relevantHistory),
      recent: relevantHistory.slice(-100)
    };
  }

  private getErrorKey(error: SupplierError): string {
    return `${error.details?.supplier}:${error.code}`;
  }

  private groupBy(records: ErrorRecord[], field: string): Record<string, number> {
    const result: Record<string, number> = {};

    for (const record of records) {
      const key = record.error.details?.[field as keyof typeof record.error.details] as string || 'unknown';
      result[key] = (result[key] || 0) + 1;
    }

    return result;
  }

  private groupByCode(records: ErrorRecord[]): Record<string, number> {
    const result: Record<string, number> = {};

    for (const record of records) {
      const key = record.error.code;
      result[key] = (result[key] || 0) + 1;
    }

    return result;
  }

  private emitError(error: SupplierError, context: ErrorContext): void {
    // Send to monitoring system (DataDog, New Relic, etc.)
    // ...
  }
}

interface ErrorRecord {
  error: SupplierError;
  context: ErrorContext;
  timestamp: Date;
}

interface ErrorContext {
  operation: string;
  params?: unknown;
  attempt?: number;
  duration?: number;
}

interface ErrorStats {
  total: number;
  byType: Record<string, number>;
  bySupplier: Record<string, number>;
  byCode: Record<string, number>;
  recent: ErrorRecord[];
}
```

### Alerting

```typescript
/**
 * Alert configuration
 */
interface AlertRule {
  id: string;
  name: string;
  condition: AlertCondition;
  threshold: number;
  window: number;  // milliseconds
  enabled: boolean;
  actions: AlertAction[];
}

type AlertCondition =
  | 'error_rate'
  | 'circuit_open'
  | 'supplier_down'
  | 'retry_exceeded';

interface AlertAction {
  type: 'EMAIL' | 'SLACK' | 'WEBHOOK' | 'SMS';
  target: string;
  template?: string;
}

/**
 * Alerting service
 */
class AlertingService {
  private rules: AlertRule[] = [
    {
      id: 'high-error-rate',
      name: 'High Error Rate',
      condition: 'error_rate',
      threshold: 0.05,  // 5%
      window: 300000,   // 5 minutes
      enabled: true,
      actions: [
        { type: 'SLACK', target: '#alerts-supplier' }
      ]
    },
    {
      id: 'circuit-open',
      name: 'Circuit Breaker Open',
      condition: 'circuit_open',
      threshold: 1,
      window: 60000,
      enabled: true,
      actions: [
        { type: 'SLACK', target: '#alerts-supplier' },
        { type: 'EMAIL', target: 'ops@example.com' }
      ]
    },
    {
      id: 'supplier-down',
      name: 'Supplier Down',
      condition: 'supplier_down',
      threshold: 1,
      window: 10000,
      enabled: true,
      actions: [
        { type: 'SLACK', target: '#alerts-critical' },
        { type: 'SMS', target: '+1234567890' }
      ]
    }
  ];

  constructor(
    private errorTracker: ErrorTrackingService,
    private circuitRegistry: CircuitBreakerRegistry
  ) {
    this.startMonitoring();
  }

  private startMonitoring(): void {
    // Check every 30 seconds
    setInterval(() => {
      this.checkRules();
    }, 30000);
  }

  private async checkRules(): Promise<void> {
    for (const rule of this.rules) {
      if (!rule.enabled) continue;

      const triggered = await this.evaluateRule(rule);
      if (triggered) {
        await this.fireAlert(rule);
      }
    }
  }

  private async evaluateRule(rule: AlertRule): Promise<boolean> {
    switch (rule.condition) {
      case 'error_rate':
        return this.checkErrorRate(rule);
      case 'circuit_open':
        return this.checkCircuitOpen(rule);
      case 'supplier_down':
        return this.checkSupplierDown(rule);
      default:
        return false;
    }
  }

  private checkErrorRate(rule: AlertRule): boolean {
    const stats = this.errorTracker.getStats(rule.window);
    const totalRequests = this.getTotalRequests(rule.window);
    const errorRate = stats.total / totalRequests;

    return errorRate >= rule.threshold;
  }

  private checkCircuitOpen(rule: AlertRule): boolean {
    const states = this.circuitRegistry.getAllStates();
    return Object.values(states).some(s => s.state === 'OPEN');
  }

  private checkSupplierDown(rule: AlertRule): boolean {
    const states = this.circuitRegistry.getAllStates();
    return Object.values(states).some(s => s.state === 'OPEN');
  }

  private async fireAlert(rule: AlertRule): Promise<void> {
    const message = this.formatAlertMessage(rule);

    for (const action of rule.actions) {
      switch (action.type) {
        case 'SLACK':
          await this.sendSlackAlert(action.target, message);
          break;
        case 'EMAIL':
          await this.sendEmailAlert(action.target, message);
          break;
        case 'SMS':
          await this.sendSmsAlert(action.target, message);
          break;
      }
    }
  }

  private formatAlertMessage(rule: AlertRule): string {
    return `🚨 Alert: ${rule.name}\nTriggered at ${new Date().toISOString()}`;
  }

  private async sendSlackAlert(channel: string, message: string): Promise<void> {
    // Send to Slack webhook
  }

  private async sendEmailAlert(email: string, message: string): Promise<void> {
    // Send email
  }

  private async sendSmsAlert(phone: string, message: string): Promise<void> {
    // Send SMS
  }

  private getTotalRequests(window: number): number {
    // Get from metrics
    return 1000;  // placeholder
  }
}
```

---

## Supplier Health Tracking

### Health Score

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPLIER HEALTH SCORE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Score Components:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Availability (40%)  │  Response Time (30%)  │  Error Rate (30%)    │   │
│  │  ─────────────────   │  ──────────────────   │  ────────────────    │   │
│  │  Uptime %            │  P95 latency          │  Error %              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Health Levels:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  90-100: 🟢 Healthy     │  Circuit CLOSED, <1% errors, <500ms p95   │   │
│  │  70-89:  🟡 Degraded    │  Circuit HALF-OPEN, 1-5% errors          │   │
│  │  50-69:  🟠 Poor        │  Frequent retries, 5-10% errors          │   │
│  │  0-49:   🔴 Unhealthy   │  Circuit OPEN, >10% errors               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Health Monitor

```typescript
/**
 * Supplier health metrics
 */
interface HealthMetrics {
  supplier: string;
  score: number;        // 0-100
  level: 'HEALTHY' | 'DEGRADED' | 'POOR' | 'UNHEALTHY';

  // Components
  availability: number;    // 0-100, uptime percentage
  responseTime: number;    // milliseconds, p95
  errorRate: number;       // 0-1, error percentage

  // Circuit state
  circuitState: CircuitState;
  circuitOpensToday: number;

  // Timestamps
  lastSuccess: Date | null;
  lastFailure: Date | null;
  lastChecked: Date;
}

/**
 * Health monitoring service
 */
class SupplierHealthMonitor {
  private healthScores = new Map<string, HealthMetrics>();
  private metricsHistory: HealthMetricsSnapshot[] = [];

  constructor(
    private circuitRegistry: CircuitBreakerRegistry,
    private errorTracker: ErrorTrackingService
  ) {
    this.startMonitoring();
  }

  private startMonitoring(): void {
    // Update health scores every minute
    setInterval(() => {
      this.updateAllHealthScores();
    }, 60000);
  }

  /**
   * Update health score for a supplier
   */
  updateHealthScore(supplier: string): HealthMetrics {
    const circuitState = this.circuitRegistry.get(supplier).getState();
    const errorStats = this.errorTracker.getStats(300000); // 5 min window

    // Calculate components
    const availability = this.calculateAvailability(supplier, circuitState);
    const responseTime = this.calculateResponseTime(supplier);
    const errorRate = this.calculateErrorRate(supplier, errorStats);

    // Calculate overall score
    const score =
      availability * 0.4 +
      (1 - Math.min(responseTime / 2000, 1)) * 100 * 0.3 +
      (1 - errorRate) * 100 * 0.3;

    // Determine health level
    const level = this.getHealthLevel(score);

    const metrics: HealthMetrics = {
      supplier,
      score: Math.round(score),
      level,
      availability,
      responseTime,
      errorRate,
      circuitState: circuitState.state,
      circuitOpensToday: 0, // track separately
      lastSuccess: circuitState.stats.lastSuccessTime || null,
      lastFailure: circuitState.stats.lastFailureTime || null,
      lastChecked: new Date()
    };

    this.healthScores.set(supplier, metrics);

    // Record for history
    this.recordSnapshot(metrics);

    return metrics;
  }

  private calculateAvailability(
    supplier: string,
    circuitState: { state: CircuitState; stats: CircuitStats }
  ): number {
    const { state, stats } = circuitState;

    if (state === 'OPEN') {
      return 0;
    }

    if (state === 'HALF_OPEN') {
      return 50;
    }

    // Calculate based on success rate
    const total = stats.successes + stats.failures;
    if (total === 0) return 100;

    return (stats.successes / total) * 100;
  }

  private calculateResponseTime(supplier: string): number {
    // Get from metrics store
    return 450;  // placeholder
  }

  private calculateErrorRate(
    supplier: string,
    errorStats: ErrorStats
  ): number {
    const supplierErrors = errorStats.bySupplier[supplier] || 0;
    const totalRequests = this.getTotalRequests(supplier);

    if (totalRequests === 0) return 0;

    return supplierErrors / totalRequests;
  }

  private getHealthLevel(score: number): HealthMetrics['level'] {
    if (score >= 90) return 'HEALTHY';
    if (score >= 70) return 'DEGRADED';
    if (score >= 50) return 'POOR';
    return 'UNHEALTHY';
  }

  private recordSnapshot(metrics: HealthMetrics): void {
    this.metricsHistory.push({
      timestamp: new Date(),
      supplier: metrics.supplier,
      score: metrics.score
    });

    // Trim history (keep 24 hours of data)
    const cutoff = Date.now() - 86400000;
    this.metricsHistory = this.metricsHistory.filter(
      s => s.timestamp.getTime() > cutoff
    );
  }

  /**
   * Update all suppliers
   */
  updateAllHealthScores(): Map<string, HealthMetrics> {
    const suppliers = ['TBO', 'TravelBoutique', 'MakCorp'];

    for (const supplier of suppliers) {
      this.updateHealthScore(supplier);
    }

    return this.healthScores;
  }

  /**
   * Get health report for all suppliers
   */
  getHealthReport(): HealthMetrics[] {
    return Array.from(this.healthScores.values());
  }

  /**
   * Get health trend for a supplier
   */
  getHealthTrend(supplier: string, hours: number = 24): HealthTrend {
    const cutoff = Date.now() - hours * 3600000;
    const snapshots = this.metricsHistory.filter(
      s => s.supplier === supplier && s.timestamp.getTime() > cutoff
    );

    if (snapshots.length === 0) {
      return { trend: 'UNKNOWN', change: 0 };
    }

    const startScore = snapshots[0].score;
    const endScore = snapshots[snapshots.length - 1].score;
    const change = endScore - startScore;

    let trend: 'IMPROVING' | 'STABLE' | 'DECLINING';
    if (change > 10) {
      trend = 'IMPROVING';
    } else if (change < -10) {
      trend = 'DECLINING';
    } else {
      trend = 'STABLE';
    }

    return { trend, change };
  }

  private getTotalRequests(supplier: string): number {
    // Get from metrics
    return 1000;  // placeholder
  }
}

interface HealthMetricsSnapshot {
  timestamp: Date;
  supplier: string;
  score: number;
}

interface HealthTrend {
  trend: 'IMPROVING' | 'STABLE' | 'DECLINING' | 'UNKNOWN';
  change: number;
}
```

---

## Implementation Reference

### Complete Error-Resilient Supplier Call

```typescript
/**
 * Complete example: Error-resilient supplier search
 */
async function searchWithFullResilience(
  params: SearchParams
): Promise<SearchResult> {
  // Get services
  const circuitRegistry = getCircuitBreakerRegistry();
  const fallbackExecutor = getFallbackExecutor();
  const healthMonitor = getSupplierHealthMonitor();
  const degradationManager = getDegradationManager();

  // Check degradation level
  const status = degradationManager.getStatus();

  if (status.level === 'MAINTENANCE') {
    throw new ServiceUnavailableError('Service in maintenance mode');
  }

  if (status.level === 'LIMITED' || status.level === 'CACHED') {
    // Try cached response
    try {
      return await getCachedResponseHandler().handleSearchWithCache(params);
    } catch {
      // Fall through to live attempt
    }
  }

  // Get health status
  const health = healthMonitor.updateHealthScore('TBO');

  if (health.level === 'UNHEALTHY') {
    // Skip to fallback
    logger.warn('Primary supplier unhealthy, using fallback', {
      supplier: 'TBO',
      health
    });
  }

  try {
    // Execute with fallback chain
    const result = await fallbackExecutor.executeWithFallback(
      'HOTELS',
      'search',
      params,
      10000  // 10 second timeout
    );

    return result;

  } catch (error) {
    // Handle all-suppliers-failure
    if (error instanceof AllSuppliersFailedError) {
      // Last resort: try cache
      try {
        const cached = await getCachedResponseHandler().handleSearchWithCache(params);
        return {
          ...cached,
          _meta: {
            ...cached._meta,
            fallbackReason: 'All suppliers unavailable'
          }
        };
      } catch {
        // Nothing worked
        throw new ServiceUnavailableError(
          'No suppliers available and no cached data',
          error.errors
        );
      }
    }

    throw error;
  }
}
```

### Error Handler Middleware

```typescript
/**
 * Express middleware for handling supplier errors
 */
export function supplierErrorHandler(
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Log error
  logger.error('Supplier error in request', {
    error: error.message,
    path: req.path,
    method: req.method
  });

  // Handle specific error types
  if (error instanceof CircuitOpenError) {
    return res.status(503).json({
      error: 'Service temporarily unavailable',
      retryAfter: 60,
      _meta: {
        type: 'CIRCUIT_OPEN',
        stats: error.stats
      }
    });
  }

  if (error instanceof AllSuppliersFailedError) {
    return res.status(503).json({
      error: 'Unable to process request - all suppliers unavailable',
      _meta: {
        type: 'ALL_SUPPLIERS_FAILED',
        errors: error.errors.map(e => ({
          code: e.code,
          message: e.message,
          supplier: e.details?.supplier
        }))
      }
    });
  }

  if (error instanceof ServiceUnavailableError) {
    return res.status(503).json({
      error: error.message,
      _meta: {
        type: 'SERVICE_UNAVAILABLE'
      }
    });
  }

  // Default error
  res.status(500).json({
    error: 'Internal server error'
  });
}

class ServiceUnavailableError extends Error {
  constructor(
    message: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ServiceUnavailableError';
  }
}
```

---

## Summary

This document covers comprehensive error handling for supplier integrations:

1. **Error Taxonomy** — Classification of transient, permanent, and business errors
2. **Retry Strategies** — Exponential backoff, rate limit handling, retry queues
3. **Circuit Breaker Pattern** — State machine, threshold configuration, automatic recovery
4. **Fallback Suppliers** — Fallback chains, timeout management, degraded service
5. **Graceful Degradation** — Service levels, cached responses, maintenance mode
6. **Error Monitoring** — Metrics tracking, alerting rules, notification channels
7. **Supplier Health Tracking** — Health scores, trend analysis, availability monitoring

**Key Takeaways:**

- Not all errors should be retried — classify correctly
- Circuit breakers prevent cascading failures
- Fallback suppliers provide resilience
- Graceful degradation maintains partial service during outages
- Monitoring and alerting enable rapid response
- Health scores guide routing decisions

**Related Documents:**
- [Technical Deep Dive](./SUPPLIER_INTEGRATION_01_TECHNICAL_DEEP_DIVE.md) — Base architecture
- [Caching Deep Dive](./SUPPLIER_INTEGRATION_03_CACHING_DEEP_DIVE.md) — Cached degradation

---

**End of Supplier Integration Deep Dive Series**
