# Booking Engine — Inventory Management

> Availability tracking, hold management, and allocation strategies

**Series:** Booking Engine | **Document:** 3 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Availability Model](#availability-model)
3. [Hold Management](#hold-management)
4. [Allocation Strategies](#allocation-strategies)
5. [Inventory Synchronization](#inventory-synchronization)
6. [Race Condition Handling](#race-condition-handling)
7. [Inventory Pooling](#inventory-pooling)
8. [Monitoring & Reconciliation](#monitoring--reconciliation)

---

## Overview

Inventory management ensures accurate availability tracking and prevents overbooking. It handles the complex challenge of syncing availability across multiple suppliers with different update patterns and data models.

### Key Challenges

| Challenge | Solution |
|-----------|----------|
| **Real-time sync** | Webhooks + polling fallback |
| **Concurrent bookings** | Distributed locks + atomic operations |
| **Supplier latency** | Local cache with TTL + holds |
| **Data inconsistency** | Reconciliation jobs + audit logs |
| **Complex allocation** | Rule engine + priority queues |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INVENTORY SERVICE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│  │   CHECK     │   │   HOLD      │   │   CONFIRM   │              │
│  │ AVAILABILITY│   │  INVENTORY  │   │   INVENTORY │              │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │
│         │                 │                 │                      │
│         └─────────────────┴─────────────────┘                      │
│                           │                                         │
│  ┌────────────────────────┴────────────────────────────────────┐   │
│  │                    INVENTORY CACHE (Redis)                   │   │
│  │  - Availability snapshots                                    │   │
│  │  - Active holds                                              │   │
│  │  - Allocation pools                                          │   │
│  └────────────────────────────┬───────────────────────────────────┘   │
│                                │                                     │
│  ┌─────────────────────────────┴─────────────────────────────────┐  │
│  │                      SYNC LAYER                               │  │
│  │  - Webhook handlers                                           │  │
│  │  - Polling workers                                            │  │
│  │  - Queue processors                                           │  │
│  └─────────────────────────────┬─────────────────────────────────┘  │
│                                │                                     │
│         ┌──────────────────────┼──────────────────────┐             │
│         ▼                      ▼                      ▼             │
│  ┌────────────┐        ┌────────────┐        ┌────────────┐        │
│  │ Supplier A │        │ Supplier B │        │ Supplier C │        │
│  │  (Webhook) │        │  (Polling) │        │  (Hybrid)  │        │
│  └────────────┘        └────────────┘        └────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Availability Model

### Data Structure

```typescript
// ============================================================================
// AVAILABILITY DATA MODEL
// ============================================================================

interface AvailabilitySnapshot {
  // Product identification
  supplierId: string;
  productId: string;
  variantId?: string; // For products with variants (room type, etc.)

  // Date range
  date: string; // ISO date (YYYY-MM-DD)

  // Availability counts
  availability: {
    total: number;      // Total inventory
    reserved: number;   // Reserved (holds)
    confirmed: number;  // Confirmed bookings
    available: number;  // total - reserved - confirmed
  };

  // Pricing (can vary by availability)
  pricing?: {
    baseRate: number;
    currency: string;
    available: boolean;
  };

  // Status
  status: 'available' | 'limited' | 'sold_out' | 'unavailable';

  // Metadata
  metadata?: {
    minStay?: number;
    maxStay?: number;
    checkinDays?: number[];
    restrictions?: string[];
  };

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
  expiresAt: Date; // TTL for cache
}

interface AvailabilityQuery {
  supplierId: string;
  productId: string;
  dates: DateRange;
  quantity?: number;
  flexibility?: {
    daysBefore?: number;
    daysAfter?: number;
  };
}

interface AvailabilityResponse {
  available: boolean;
  dates: AvailabilityByDate[];
  alternatives?: AlternativeDate[];
  reason?: string;
}

interface AvailabilityByDate {
  date: string;
  available: boolean;
  availability: number;
  pricing?: {
    baseRate: number;
    currency: string;
  };
  status: 'available' | 'limited' | 'sold_out';
}

interface AlternativeDate {
  date: string;
  availability: number;
  priceDifference: number;
  reason: string;
}
```

### Availability Check

```typescript
// ============================================================================
// AVAILABILITY CHECK IMPLEMENTATION
// ============================================================================

class InventoryService {
  private redis: Redis;
  private db: Database;

  async checkAvailability(
    query: AvailabilityQuery
  ): Promise<AvailabilityResponse> {
    // Try cache first
    const cached = await this.checkCache(query);
    if (cached && !this.isStale(cached)) {
      return cached;
    }

    // Fetch from source
    const fresh = await this.fetchAvailability(query);
    await this.updateCache(query, fresh);

    return fresh;
  }

  private async checkCache(
    query: AvailabilityQuery
  ): Promise<AvailabilityResponse | null> {
    const key = this.cacheKey(query);
    const data = await this.redis.get(key);

    if (!data) {
      return null;
    }

    const response = JSON.parse(data) as AvailabilityResponse;

    // Check if any dates are sold out
    const hasSoldOut = response.dates.some(
      d => d.status === 'sold_out' || d.availability < (query.quantity || 1)
    );

    if (hasSoldOut) {
      // Sold out data requires fresh check from supplier
      return null;
    }

    return response;
  }

  private isStale(response: AvailabilityResponse): boolean {
    // Check if data is too old
    const maxAge = 300; // 5 minutes for high-demand products
    const oldestDate = Math.min(
      ...response.dates.map(d => new Date(d.date).getTime())
    );

    // For dates in the near future, require fresh data
    const nearFuture = addDays(new Date(), 30);
    if (oldestDate < nearFuture.getTime()) {
      return true;
    }

    return false;
  }

  private async fetchAvailability(
    query: AvailabilityQuery
  ): Promise<AvailabilityResponse> {
    const supplier = await this.getSupplier(query.supplierId);

    switch (supplier.syncMode) {
      case 'webhook':
        return await this.fetchFromCache(query);
      case 'polling':
        return await this.fetchFromSupplier(query);
      case 'hybrid':
        return await this.fetchHybrid(query);
      default:
        throw new Error(`Unknown sync mode: ${supplier.syncMode}`);
    }
  }

  private async fetchFromCache(
    query: AvailabilityQuery
  ): Promise<AvailabilityResponse> {
    // For webhook-based suppliers, our cache is authoritative
    const dates = eachDayOfInterval(query.dates);

    const availability = await Promise.all(
      dates.map(async (date) => {
        const key = `inventory:${query.supplierId}:${query.productId}:${formatISO(date)}`;
        const snapshot = await this.redis.get(key);

        if (!snapshot) {
          return {
            date: formatISO(date),
            available: false,
            availability: 0,
            status: 'unavailable' as const,
          };
        }

        const data = JSON.parse(snapshot) as AvailabilitySnapshot;
        return {
          date: formatISO(date),
          available: data.availability.available > 0,
          availability: data.availability.available,
          pricing: data.pricing,
          status: this.mapStatus(data.availability.available),
        };
      })
    );

    // Check if all requested dates have availability
    const requestedQty = query.quantity || 1;
    const allAvailable = availability.every(
      d => d.available && d.availability >= requestedQty
    );

    let alternatives: AlternativeDate[] | undefined;
    if (!allAvailable) {
      alternatives = await this.findAlternatives(query, availability);
    }

    return {
      available: allAvailable,
      dates: availability,
      alternatives,
      reason: allAvailable ? undefined : 'Some dates are unavailable',
    };
  }

  private async fetchFromSupplier(
    query: AvailabilityQuery
  ): Promise<AvailabilityResponse> {
    const supplier = await this.getSupplier(query.supplierId);

    // Call supplier API
    const response = await fetch(supplier.availabilityEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supplier.apiKey}`,
      },
      body: JSON.stringify({
        product_id: query.productId,
        start_date: formatISO(query.dates.start),
        end_date: formatISO(query.dates.end),
        quantity: query.quantity || 1,
      }),
    });

    if (!response.ok) {
      throw new SupplierAPIError(supplier.id, response.status);
    }

    const data = await response.json();

    // Transform to our format
    return this.transformSupplierResponse(data, query);
  }

  private async findAlternatives(
    query: AvailabilityQuery,
    currentAvailability: AvailabilityByDate[]
  ): Promise<AlternativeDate[]> {
    const alternatives: AlternativeDate[] = [];

    // Check dates before
    if (query.flexibility?.daysBefore) {
      for (let i = 1; i <= query.flexibility.daysBefore; i++) {
        const date = subDays(query.dates.start, i);
        const alt = await this.checkSingleDate(query, date);
        if (alt.available && alt.availability >= (query.quantity || 1)) {
          alternatives.push({
            date: formatISO(date),
            availability: alt.availability,
            priceDifference: alt.pricing?.baseRate
              ? alt.pricing.baseRate - (currentAvailability[0]?.pricing?.baseRate || 0)
              : 0,
            reason: 'Earlier date available',
          });
        }
      }
    }

    // Check dates after
    if (query.flexibility?.daysAfter) {
      for (let i = 1; i <= query.flexibility.daysAfter; i++) {
        const date = addDays(query.dates.end, i);
        const alt = await this.checkSingleDate(query, date);
        if (alt.available && alt.availability >= (query.quantity || 1)) {
          alternatives.push({
            date: formatISO(date),
            availability: alt.availability,
            priceDifference: alt.pricing?.baseRate
              ? alt.pricing.baseRate - (currentAvailability[0]?.pricing?.baseRate || 0)
              : 0,
            reason: 'Later date available',
          });
        }
      }
    }

    return alternatives.slice(0, 5); // Top 5 alternatives
  }

  private cacheKey(query: AvailabilityQuery): string {
    return `availability:${query.supplierId}:${query.productId}:${formatISO(query.dates.start)}:${formatISO(query.dates.end)}:${query.quantity || 1}`;
  }

  private mapStatus(available: number): 'available' | 'limited' | 'sold_out' {
    if (available === 0) return 'sold_out';
    if (available < 5) return 'limited';
    return 'available';
  }
}
```

---

## Hold Management

### Hold Lifecycle

```typescript
// ============================================================================
// HOLD MANAGEMENT
// ============================================================================

interface Hold {
  id: string;
  type: 'temp' | 'confirmed';

  // References
  bookingId: string;
  bookingItemId: string;
  supplierId: string;
  productId: string;

  // Hold details
  dates: DateRange;
  quantity: number;
  unitId?: string; // Specific room/unit if assigned

  // Supplier hold
  supplierHoldId?: string;
  supplierHoldReference?: string;

  // Expiration
  expiresAt: Date;
  extendedAt?: Date;
  extensions: number;

  // Status
  status: 'active' | 'expired' | 'confirmed' | 'released' | 'failed';

  // Metadata
  metadata: {
    source: 'api' | 'webhook' | 'manual';
    priority: number;
    tags: string[];
  };

  // Timestamps
  createdAt: Date;
  confirmedAt?: Date;
  releasedAt?: Date;
}

class HoldManager {
  private redis: Redis;
  private db: Database;

  async createHold(request: {
    bookingId: string;
    bookingItemId: string;
    supplierId: string;
    productId: string;
    dates: DateRange;
    quantity: number;
    ttl?: number; // Time to live in seconds
  }): Promise<Hold> {
    // Acquire distributed lock
    const lockKey = `hold-lock:${request.supplierId}:${request.productId}:${formatISO(request.dates.start)}`;
    const lock = await this.acquireLock(lockKey, 5000);

    if (!lock) {
      throw new HoldCreationError('Could not acquire lock - concurrent operation');
    }

    try {
      // Check availability
      const available = await this.checkAvailabilityForHold(request);
      if (!available.available) {
        throw new InsufficientInventoryError(request.productId, available.available, request.quantity);
      }

      // Create hold record
      const hold: Hold = {
        id: crypto.randomUUID(),
        type: 'temp',
        bookingId: request.bookingId,
        bookingItemId: request.bookingItemId,
        supplierId: request.supplierId,
        productId: request.productId,
        dates: request.dates,
        quantity: request.quantity,
        expiresAt: addSeconds(new Date(), request.ttl || 900), // Default 15 min
        extensions: 0,
        status: 'active',
        metadata: {
          source: 'api',
          priority: 5,
          tags: [],
        },
        createdAt: new Date(),
      };

      // Store in database
      await this.db.holds.create(hold);

      // Update inventory cache (decrement available)
      await this.decrementAvailableInventory(hold);

      // Create hold with supplier if supported
      const supplier = await this.getSupplier(request.supplierId);
      if (supplier.features.holds) {
        const supplierHold = await this.createSupplierHold(hold);
        hold.supplierHoldId = supplierHold.id;
        hold.supplierHoldReference = supplierHold.reference;
        await this.db.holds.update(hold.id, hold);
      }

      // Set expiration in Redis
      await this.redis.setex(
        `hold:${hold.id}`,
        request.ttl || 900,
        JSON.stringify({ holdId: hold.id, status: 'active' })
      );

      // Schedule expiration
      await this.scheduleExpiration(hold);

      return hold;
    } finally {
      await lock.release();
    }
  }

  async extendHold(holdId: string, additionalSeconds: number): Promise<Hold> {
    const hold = await this.db.holds.findById(holdId);

    if (!hold) {
      throw new HoldNotFoundError(holdId);
    }

    if (hold.status !== 'active') {
      throw new InvalidHoldStatusError(hold.status, 'active');
    }

    // Check extension limit
    if (hold.extensions >= 3) {
      throw new HoldExtensionLimitError(holdId);
    }

    // Check if extension is allowed (close to expiration)
    const timeUntilExpiry = hold.expiresAt.getTime() - Date.now();
    if (timeUntilExpiry > 300000) { // More than 5 minutes left
      throw new HoldExtensionTooSoonError();
    }

    // Extend hold
    hold.expiresAt = addSeconds(hold.expiresAt, additionalSeconds);
    hold.extensions += 1;
    hold.extendedAt = new Date();

    await this.db.holds.update(holdId, hold);

    // Update Redis
    await this.redis.expire(
      `hold:${holdId}`,
      Math.floor((hold.expiresAt.getTime() - Date.now()) / 1000)
    );

    // Extend with supplier
    if (hold.supplierHoldId) {
      await this.extendSupplierHold(hold.supplierHoldId, additionalSeconds);
    }

    return hold;
  }

  async confirmHold(holdId: string): Promise<Hold> {
    const hold = await this.db.holds.findById(holdId);

    if (!hold) {
      throw new HoldNotFoundError(holdId);
    }

    if (hold.status !== 'active') {
      throw new InvalidHoldStatusError(hold.status, 'active');
    }

    // Update hold status
    hold.type = 'confirmed';
    hold.status = 'confirmed';
    hold.confirmedAt = new Date();
    hold.expiresAt = null; // Confirmed holds don't expire

    await this.db.holds.update(holdId, hold);

    // Remove from Redis (no longer expires)
    await this.redis.del(`hold:${holdId}`);

    // Confirm with supplier
    if (hold.supplierHoldId) {
      await this.confirmSupplierHold(hold.supplierHoldId);
    }

    // Update inventory (move from reserved to confirmed)
    await this.confirmInventoryAllocation(hold);

    return hold;
  }

  async releaseHold(holdId: string, reason: string): Promise<void> {
    const hold = await this.db.holds.findById(holdId);

    if (!hold) {
      return; // Already released
    }

    if (hold.status === 'released' || hold.status === 'confirmed') {
      return; // Already processed
    }

    // Update hold status
    hold.status = 'released';
    hold.releasedAt = new Date();
    await this.db.holds.update(holdId, hold);

    // Remove from Redis
    await this.redis.del(`hold:${holdId}`);

    // Release with supplier
    if (hold.supplierHoldId) {
      await this.releaseSupplierHold(hold.supplierHoldId);
    }

    // Increment available inventory
    await this.incrementAvailableInventory(hold);

    // Log release
    logger.info('Hold released', {
      holdId,
      bookingId: hold.bookingId,
      reason,
      duration: hold.releasedAt.getTime() - hold.createdAt.getTime(),
    });
  }

  private async scheduleExpiration(hold: Hold): Promise<void> {
    // Add to expiration queue
    await this.redis.zadd(
      'hold-expiration',
      {
        score: hold.expiresAt.getTime(),
        member: hold.id,
      }
    );
  }

  // Process expired holds (background job)
  async processExpiredHolds(): Promise<void> {
    const now = Date.now();
    const expiredIds = await this.redis.zrangebyscore(
      'hold-expiration',
      0,
      now
    );

    for (const holdId of expiredIds) {
      await this.releaseHold(holdId, 'expired');
      await this.redis.zrem('hold-expiration', holdId);
    }
  }

  private async acquireLock(
    key: string,
    timeout: number
  ): Promise<DistributedLock | null> {
    const lockValue = crypto.randomUUID();
    const acquired = await this.redis.set(
      key,
      lockValue,
      {
        NX: true,
        PX: timeout,
      }
    );

    if (acquired === 'OK') {
      return {
        key,
        value: lockValue,
        release: async () => {
          const script = `
            if redis.call("get", KEYS[1]) == ARGV[1] then
              return redis.call("del", KEYS[1])
            else
              return 0
            end
          `;
          await this.redis.eval(script, { keys: [key], arguments: [lockValue] });
        },
      };
    }

    return null;
  }

  private async decrementAvailableInventory(hold: Hold): Promise<void> {
    const dates = eachDayOfInterval(hold.dates);

    for (const date of dates) {
      const key = `inventory:${hold.supplierId}:${hold.productId}:${formatISO(date)}`;
      await this.redis.hincrby(key, 'reserved', hold.quantity);
      await this.redis.hincrby(key, 'available', -hold.quantity);
    }
  }

  private async incrementAvailableInventory(hold: Hold): Promise<void> {
    const dates = eachDayOfInterval(hold.dates);

    for (const date of dates) {
      const key = `inventory:${hold.supplierId}:${hold.productId}:${formatISO(date)}`;
      await this.redis.hincrby(key, 'reserved', -hold.quantity);
      await this.redis.hincrby(key, 'available', hold.quantity);
    }
  }
}
```

---

## Allocation Strategies

### Allocation Rules

```typescript
// ============================================================================
// ALLOCATION ENGINE
// ============================================================================

interface AllocationRequest {
  supplierId: string;
  productId: string;
  dates: DateRange;
  quantity: number;
  customerId?: string;
  tier?: CustomerTier;
  constraints?: AllocationConstraints;
}

interface AllocationConstraints {
  allowSplit?: boolean;         // Allow splitting across units
  preferredUnits?: string[];    // Specific unit preferences
  minPrice?: number;
  maxPrice?: number;
  allowUpgrades?: boolean;      // Allow better units at same price
}

interface AllocationResult {
  allocated: boolean;
  units: AllocatedUnit[];
  total: {
    baseRate: number;
    taxes: number;
    fees: number;
    total: number;
  };
  warnings: string[];
}

interface AllocatedUnit {
  unitId: string;
  unitType: string;
  dates: DateRange;
  pricing: UnitPricing;
  upgrade?: boolean; // If this is an upgrade from requested
}

class AllocationEngine {
  private rules: AllocationRule[];

  constructor() {
    this.rules = this.loadAllocationRules();
  }

  async allocate(request: AllocationRequest): Promise<AllocationResult> {
    // Get available inventory
    const inventory = await this.getAvailableInventory(request);

    if (!inventory || inventory.available < request.quantity) {
      return {
        allocated: false,
        units: [],
        total: { baseRate: 0, taxes: 0, fees: 0, total: 0 },
        warnings: ['Insufficient inventory'],
      };
    }

    // Apply allocation rules in priority order
    for (const rule of this.rules) {
      if (await rule.matches(request)) {
        const result = await rule.apply(inventory, request);
        if (result.allocated) {
          return result;
        }
      }
    }

    // Default allocation
    return this.defaultAllocation(inventory, request);
  }

  private loadAllocationRules(): AllocationRule[] {
    return [
      // Priority 1: VIP customers get best units
      new VIPAllocationRule(),

      // Priority 2: Returning customers
      new ReturningCustomerAllocationRule(),

      // Priority 3: Long stays get preference
      new LongStayAllocationRule(),

      // Priority 4: Early bookings
      new EarlyBookingAllocationRule(),

      // Priority 5: Fill gaps (occupancy optimization)
      new GapFillAllocationRule(),

      // Priority 6: Default (first available)
      new DefaultAllocationRule(),
    ];
  }
}

// ============================================================================
// ALLOCATION RULES
// ============================================================================

interface AllocationRule {
  priority: number;
  name: string;
  matches(request: AllocationRequest): Promise<boolean>;
  apply(inventory: AvailableInventory, request: AllocationRequest): Promise<AllocationResult>;
}

class VIPAllocationRule implements AllocationRule {
  priority = 1;
  name = 'VIP Allocation';

  async matches(request: AllocationRequest): Promise<boolean> {
    return request.tier === 'platinum' || request.tier === 'gold';
  }

  async apply(
    inventory: AvailableInventory,
    request: AllocationRequest
  ): Promise<AllocationResult> {
    // Get best available units
    const bestUnits = inventory.units
      .filter(u => u.available)
      .sort((a, b) => {
        // Sort by quality, then by price
        if (a.quality !== b.quality) {
          return b.quality - a.quality; // Higher quality first
        }
        return a.pricing.baseRate - b.pricing.baseRate; // Lower price first
      })
      .slice(0, request.quantity);

    if (bestUnits.length < request.quantity) {
      return { allocated: false, units: [], total: this.zeroTotal(), warnings: [] };
    }

    return {
      allocated: true,
      units: bestUnits.map(u => ({
        unitId: u.id,
        unitType: u.type,
        dates: request.dates,
        pricing: u.pricing,
      })),
      total: this.calculateTotal(bestUnits),
      warnings: [],
    };
  }

  private zeroTotal() {
    return { baseRate: 0, taxes: 0, fees: 0, total: 0 };
  }

  private calculateTotal(units: Unit[]): { baseRate: number; taxes: number; fees: number; total: number } {
    const baseRate = units.reduce((sum, u) => sum + u.pricing.baseRate, 0);
    const taxes = units.reduce((sum, u) => sum + u.pricing.taxes, 0);
    const fees = units.reduce((sum, u) => sum + u.pricing.fees, 0);
    return { baseRate, taxes, fees, total: baseRate + taxes + fees };
  }
}

class GapFillAllocationRule implements AllocationRule {
  priority = 5;
  name = 'Gap Fill';

  async matches(request: AllocationRequest): Promise<boolean> {
    // Match when booking fills a gap in existing inventory
    const surrounding = await this.getSurroundingBookings(request);
    return surrounding.hasGap;
  }

  async apply(
    inventory: AvailableInventory,
    request: AllocationRequest
  ): Promise<AllocationResult> {
    // Find units that have adjacent bookings (creating a gap fill)
    const gapFillUnits = inventory.units.filter(async (u) => {
      const bookings = await this.getUnitBookings(u.id, request.dates);
      return bookings.length > 0 && bookings.length < 3; // Some but not full
    });

    if (gapFillUnits.length >= request.quantity) {
      return {
        allocated: true,
        units: gapFillUnits.slice(0, request.quantity).map(u => ({
          unitId: u.id,
          unitType: u.type,
          dates: request.dates,
          pricing: u.pricing,
        })),
        total: this.calculateTotal(gapFillUnits.slice(0, request.quantity)),
        warnings: [],
      };
    }

    return { allocated: false, units: [], total: this.zeroTotal(), warnings: [] };
  }

  private zeroTotal() {
    return { baseRate: 0, taxes: 0, fees: 0, total: 0 };
  }

  private calculateTotal(units: Unit[]): { baseRate: number; taxes: number; fees: number; total: number } {
    const baseRate = units.reduce((sum, u) => sum + u.pricing.baseRate, 0);
    const taxes = units.reduce((sum, u) => sum + u.pricing.taxes, 0);
    const fees = units.reduce((sum, u) => sum + u.pricing.fees, 0);
    return { baseRate, taxes, fees, total: baseRate + taxes + fees };
  }

  private async getSurroundingBookings(request: AllocationRequest): Promise<{ hasGap: boolean }> {
    // Implementation checks for bookings immediately before/after requested dates
    return { hasGap: false };
  }

  private async getUnitBookings(unitId: string, dates: DateRange): Promise<Booking[]> {
    // Implementation returns bookings for this unit around these dates
    return [];
  }
}

class DefaultAllocationRule implements AllocationRule {
  priority = 6;
  name = 'Default';

  async matches(): Promise<boolean> {
    return true; // Always matches as fallback
  }

  async apply(
    inventory: AvailableInventory,
    request: AllocationRequest
  ): Promise<AllocationResult> {
    // Simple first-available allocation
    const units = inventory.units
      .filter(u => u.available)
      .slice(0, request.quantity);

    return {
      allocated: units.length === request.quantity,
      units: units.map(u => ({
        unitId: u.id,
        unitType: u.type,
        dates: request.dates,
        pricing: u.pricing,
      })),
      total: this.calculateTotal(units),
      warnings: units.length < request.quantity ? ['Some units could not be allocated'] : [],
    };
  }

  private calculateTotal(units: Unit[]): { baseRate: number; taxes: number; fees: number; total: number } {
    const baseRate = units.reduce((sum, u) => sum + u.pricing.baseRate, 0);
    const taxes = units.reduce((sum, u) => sum + u.pricing.taxes, 0);
    const fees = units.reduce((sum, u) => sum + u.pricing.fees, 0);
    return { baseRate, taxes, fees, total: baseRate + taxes + fees };
  }
}
```

---

## Inventory Synchronization

### Sync Strategies

```typescript
// ============================================================================
// INVENTORY SYNCHRONIZATION
// ============================================================================

enum SyncMode {
  Webhook = 'webhook',     // Supplier pushes updates
  Polling = 'polling',     // We pull updates
  Hybrid = 'hybrid',       // Both webhook + polling fallback
}

interface SupplierConfig {
  id: string;
  syncMode: SyncMode;
  syncInterval?: number;   // For polling (seconds)
  webhookSecret?: string;  // For webhook verification
  apiEndpoint: string;
  lastSyncAt?: Date;
}

class InventorySyncManager {
  private queue: Queue;

  async syncSupplier(supplierId: string): Promise<void> {
    const supplier = await this.getSupplierConfig(supplierId);

    switch (supplier.syncMode) {
      case SyncMode.Polling:
        await this.pollSupplier(supplier);
        break;

      case SyncMode.Hybrid:
        // Check if webhook is stale, if so poll
        const stale = this.isWebhookStale(supplier);
        if (stale) {
          await this.pollSupplier(supplier);
        }
        break;

      case SyncMode.Webhook:
        // Webhook-based - no active sync needed
        // But we can log a heartbeat
        await this.recordHeartbeat(supplierId);
        break;
    }
  }

  private async pollSupplier(supplier: SupplierConfig): Promise<void> {
    const since = supplier.lastSyncAt || new Date(0);

    try {
      // Fetch updates from supplier
      const updates = await this.fetchSupplierUpdates(supplier, since);

      // Process updates
      for (const update of updates) {
        await this.queue.add('process-inventory-update', {
          supplierId: supplier.id,
          update,
        });
      }

      // Update last sync time
      await this.updateLastSync(supplier.id, new Date());

    } catch (error) {
      logger.error(`Failed to poll supplier ${supplier.id}`, { error });
      await this.recordSyncFailure(supplier.id, error);
    }
  }

  private async fetchSupplierUpdates(
    supplier: SupplierConfig,
    since: Date
  ): Promise<InventoryUpdate[]> {
    const response = await fetch(
      `${supplier.apiEndpoint}/inventory/updates`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supplier.apiKey}`,
        },
        body: JSON.stringify({
          since: since.toISOString(),
        }),
      }
    );

    if (!response.ok) {
      throw new SupplierAPIError(supplier.id, response.status);
    }

    const data = await response.json();
    return data.updates;
  }

  private isWebhookStale(supplier: SupplierConfig): boolean {
    if (!supplier.lastSyncAt) {
      return true;
    }

    const staleThreshold = 3600000; // 1 hour
    return Date.now() - supplier.lastSyncAt.getTime() > staleThreshold;
  }

  // Webhook handler
  async handleWebhook(supplierId: string, payload: unknown, signature: string): Promise<void> {
    const supplier = await this.getSupplierConfig(supplierId);

    // Verify signature
    if (!this.verifyWebhookSignature(payload, signature, supplier.webhookSecret)) {
      throw new InvalidWebhookSignatureError();
    }

    // Process webhook
    await this.queue.add('process-webhook', {
      supplierId,
      payload,
    });
  }
}

// ============================================================================
// UPDATE PROCESSING
// ============================================================================

interface InventoryUpdate {
  productId: string;
  date: string;
  changes: {
    total?: number;
    confirmed?: number;
    available?: number;
    pricing?: {
      baseRate?: number;
      currency?: string;
    };
  };
  version: number;
  timestamp: Date;
}

class InventoryUpdateProcessor {
  private redis: Redis;
  private db: Database;

  async processUpdate(supplierId: string, update: InventoryUpdate): Promise<void> {
    // Check version (optimistic concurrency)
    const current = await this.getCurrentSnapshot(supplierId, update.productId, update.date);
    if (current && current.version >= update.version) {
      logger.debug('Skipping outdated update', {
        supplierId,
        productId: update.productId,
        version: update.version,
        currentVersion: current.version,
      });
      return;
    }

    // Apply update
    const snapshot: AvailabilitySnapshot = {
      supplierId,
      productId: update.productId,
      date: update.date,
      availability: {
        total: update.changes.total ?? current?.availability.total ?? 0,
        confirmed: update.changes.confirmed ?? current?.availability.confirmed ?? 0,
        reserved: current?.availability.reserved ?? 0, // Unchanged
        available: update.changes.available ?? 0,
      },
      pricing: update.changes.pricing,
      status: this.calculateStatus(update.changes.available),
      version: update.version,
      createdAt: current?.createdAt ?? new Date(),
      updatedAt: new Date(),
      expiresAt: this.calculateExpiry(),
    };

    // Store in Redis cache
    await this.storeSnapshot(snapshot);

    // Store in database (for reconciliation)
    await this.db.snapshots.create(snapshot);

    // Notify listeners
    await this.notifyAvailabilityChange(snapshot);
  }

  private calculateStatus(available: number): 'available' | 'limited' | 'sold_out' {
    if (available === 0) return 'sold_out';
    if (available < 5) return 'limited';
    return 'available';
  }

  private calculateExpiry(): Date {
    // Cache expires based on how far in the future the date is
    return addHours(new Date(), 24);
  }

  private async storeSnapshot(snapshot: AvailabilitySnapshot): Promise<void> {
    const key = `inventory:${snapshot.supplierId}:${snapshot.productId}:${snapshot.date}`;

    await this.redis.hset(key, {
      total: snapshot.availability.total,
      confirmed: snapshot.availability.confirmed,
      reserved: snapshot.availability.reserved,
      available: snapshot.availability.available,
      status: snapshot.status,
      version: snapshot.version,
      updatedAt: snapshot.updatedAt.toISOString(),
    });

    await this.redis.expire(key, 86400); // 24 hours
  }

  private async notifyAvailabilityChange(snapshot: AvailabilitySnapshot): Promise<void> {
    // Publish to Redis pub/sub
    await this.redis.publish('inventory:changes', JSON.stringify({
      supplierId: snapshot.supplierId,
      productId: snapshot.productId,
      date: snapshot.date,
      available: snapshot.availability.available,
      status: snapshot.status,
    }));

    // If sold out, notify waiting holds
    if (snapshot.status === 'sold_out') {
      await this.notifySoldOut(snapshot);
    }
  }

  private async notifySoldOut(snapshot: AvailabilitySnapshot): Promise<void> {
    // Find active holds for this product/date
    const holds = await this.db.holds.find({
      supplierId: snapshot.supplierId,
      productId: snapshot.productId,
      status: 'active',
    });

    for (const hold of holds) {
      const dateInRange = isWithinInterval(
        new Date(snapshot.date),
        hold.dates
      );

      if (dateInRange) {
        // Notify customer of sold out status
        await NotificationService.sendSoldOutNotification(hold.bookingId, {
          productId: snapshot.productId,
          date: snapshot.date,
        });
      }
    }
  }
}
```

---

## Race Condition Handling

### Distributed Locking

```typescript
// ============================================================================
// RACE CONDITION PREVENTION
// ============================================================================

class InventoryLockManager {
  private redis: Redis;

  async withLock<T>(
    key: string,
    fn: () => Promise<T>,
    options: {
      timeout?: number;
      retry?: number;
      retryDelay?: number;
    } = {}
  ): Promise<T> {
    const {
      timeout = 5000,
      retry = 3,
      retryDelay = 100,
    } = options;

    let lastError: Error;

    for (let attempt = 0; attempt < retry; attempt++) {
      const lockValue = crypto.randomUUID();
      const lockKey = `lock:${key}`;

      // Try to acquire lock
      const acquired = await this.redis.set(
        lockKey,
        lockValue,
        {
          NX: true,
          PX: timeout,
        }
      );

      if (acquired === 'OK') {
        try {
          return await fn();
        } finally {
          // Release lock using Lua script for atomicity
          const script = `
            if redis.call("get", KEYS[1]) == ARGV[1] then
              return redis.call("del", KEYS[1])
            else
              return 0
            end
          `;
          await this.redis.eval(script, { keys: [lockKey], arguments: [lockValue] });
        }
      }

      // Lock not acquired, wait and retry
      lastError = new LockAcquisitionError(`Could not acquire lock: ${key}`);
      await sleep(retryDelay * (attempt + 1)); // Exponential backoff
    }

    throw lastError;
  }

  // Atomic inventory check and reserve
  async atomicReserve(
    supplierId: string,
    productId: string,
    date: string,
    quantity: number
  ): Promise<boolean> {
    const key = `inventory:${supplierId}:${productId}:${date}`;

    const script = `
      local available = tonumber(redis.call("HGET", KEYS[1], "available")) or 0
      local reserved = tonumber(redis.call("HGET", KEYS[1], "reserved")) or 0

      if available >= tonumber(ARGV[1]) then
        redis.call("HINCRBY", KEYS[1], "available", -tonumber(ARGV[1]))
        redis.call("HINCRBY", KEYS[1], "reserved", tonumber(ARGV[1]))
        return 1
      else
        return 0
      end
    `;

    const result = await this.redis.eval(script, {
      keys: [key],
      arguments: [quantity.toString()],
    });

    return result === 1;
  }

  // Atomic batch reservation for multiple dates
  async atomicBatchReserve(
    supplierId: string,
    productId: string,
    dates: string[],
    quantity: number
  ): Promise<boolean> {
    const script = `
      for i, date in ipairs(ARGV) do
        local key = "inventory:" .. KEYS[1] .. ":" .. KEYS[2] .. ":" .. date
        local available = tonumber(redis.call("HGET", key, "available")) or 0

        if available < tonumber(ARGV[#ARGV]) then
          -- Not enough availability, rollback previous
          for j = 1, i - 1 do
            local rollbackKey = "inventory:" .. KEYS[1] .. ":" .. KEYS[2] .. ":" .. ARGV[j]
            redis.call("HINCRBY", rollbackKey, "available", tonumber(ARGV[#ARGV]))
            redis.call("HINCRBY", rollbackKey, "reserved", -tonumber(ARGV[#ARGV]))
          end
          return 0
        end

        redis.call("HINCRBY", key, "available", -tonumber(ARGV[#ARGV]))
        redis.call("HINCRBY", key, "reserved", tonumber(ARGV[#ARGV]))
      end

      return 1
    `;

    const result = await this.redis.eval(script, {
      keys: [supplierId, productId],
      arguments: [...dates, quantity.toString()],
    });

    return result === 1;
  }
}
```

---

## Inventory Pooling

### Shared Inventory

```typescript
// ============================================================================
// INVENTORY POOLING
// ============================================================================

interface InventoryPool {
  id: string;
  name: string;
  type: 'supplier' | 'agency' | 'consortium';

  // Members
  members: PoolMember[];

  // Pool configuration
  config: {
    shareable: boolean;
    allocationMethod: 'pro_rata' | 'first_come' | 'round_robin';
    releaseBack: boolean; // Release unused inventory back to pool
    minReserve: number;   // Minimum to keep for each member
  };

  // Products in pool
  products: PooledProduct[];
}

interface PoolMember {
  supplierId: string;
  priority: number;
  allocation: number; // Percentage or fixed count
  reserved: number;
  used: number;
}

interface PooledProduct {
  productId: string;
  totalPool: number;
  allocated: number;
  available: number;
  members: Record<string, number>; // Member allocations
}

class InventoryPoolManager {
  async getPoolAvailability(
    poolId: string,
    productId: string,
    dates: DateRange,
    quantity: number
  ): Promise<AvailabilityResponse> {
    const pool = await this.getPool(poolId);
    const product = pool.products.find(p => p.productId === productId);

    if (!product) {
      return { available: false, dates: [], reason: 'Product not in pool' };
    }

    // Check total pool availability
    const totalAvailable = product.totalPool - product.allocated;

    if (totalAvailable < quantity) {
      // Check individual member availability
      const memberAvailability = await this.checkMemberAvailability(
        pool,
        productId,
        dates,
        quantity
      );

      return {
        available: memberAvailability.some(m => m.available),
        dates: memberAvailability,
        reason: 'Pool exhausted, checking members directly',
      };
    }

    return {
      available: true,
      dates: dates,
    };
  }

  async allocateFromPool(
    poolId: string,
    productId: string,
    dates: DateRange,
    quantity: number,
    memberId?: string
  ): Promise<AllocationResult> {
    const pool = await this.getPool(poolId);

    if (memberId) {
      // Allocate from specific member
      return await this.allocateFromMember(pool, productId, dates, quantity, memberId);
    }

    // Allocate based on pool strategy
    switch (pool.config.allocationMethod) {
      case 'pro_rata':
        return await this.allocateProRata(pool, productId, dates, quantity);

      case 'first_come':
        return await this.allocateFirstCome(pool, productId, dates, quantity);

      case 'round_robin':
        return await this.allocateRoundRobin(pool, productId, dates, quantity);

      default:
        throw new Error(`Unknown allocation method: ${pool.config.allocationMethod}`);
    }
  }

  private async allocateProRata(
    pool: InventoryPool,
    productId: string,
    dates: DateRange,
    quantity: number
  ): Promise<AllocationResult> {
    const allocations: { memberId: string; quantity: number }[] = [];

    for (const member of pool.members) {
      const memberShare = Math.floor(quantity * (member.allocation / 100));

      if (memberShare > 0) {
        const allocated = await this.allocateFromMember(
          pool,
          productId,
          dates,
          memberShare,
          member.supplierId
        );

        if (allocated.allocated) {
          allocations.push({ memberId: member.supplierId, quantity: memberShare });
        }
      }
    }

    const totalAllocated = allocations.reduce((sum, a) => sum + a.quantity, 0);

    return {
      allocated: totalAllocated === quantity,
      units: allocations.map(a => ({
        unitId: `${a.memberId}-${productId}`,
        unitType: 'pooled',
        dates,
        pricing: { baseRate: 0, taxes: 0, fees: 0, total: 0 },
      })),
      total: { baseRate: 0, taxes: 0, fees: 0, total: 0 },
      warnings: totalAllocated < quantity ? ['Could not allocate full quantity'] : [],
    };
  }
}
```

---

## Monitoring & Reconciliation

### Health Checks

```typescript
// ============================================================================
// INVENTORY MONITORING
// ============================================================================

class InventoryMonitor {
  async checkHealth(): Promise<HealthReport> {
    const checks = await Promise.all([
      this.checkCacheConsistency(),
      this.checkStaleData(),
      this.checkOrphanedHolds(),
      this.checkSupplierSync(),
    ]);

    return {
      healthy: checks.every(c => c.healthy),
      checks,
      timestamp: new Date(),
    };
  }

  private async checkCacheConsistency(): Promise<HealthCheck> {
    // Sample random keys and compare Redis vs DB
    const samples = await this.sampleInventoryKeys(100);
    const inconsistencies: string[] = [];

    for (const key of samples) {
      const cached = await this.redis.get(key);
      const db = await this.db.snapshots.findByKey(key);

      if (!cached && !db) continue;

      if (cached && !db) {
        inconsistencies.push(`Cache only: ${key}`);
        continue;
      }

      if (!cached && db) {
        inconsistencies.push(`DB only: ${key}`);
        continue;
      }

      const cachedData = JSON.parse(cached);
      if (cachedData.version !== db.version) {
        inconsistencies.push(`Version mismatch: ${key}`);
      }
    }

    return {
      name: 'cache_consistency',
      healthy: inconsistencies.length === 0,
      details: {
        samples: samples.length,
        inconsistencies: inconsistencies.length,
      },
    };
  }

  private async checkStaleData(): Promise<HealthCheck> {
    // Find data older than expected
    const staleThreshold = subMinutes(new Date(), 30);
    const stale = await this.db.snapshots.find({
      updatedAt: { $lt: staleThreshold },
    });

    return {
      name: 'stale_data',
      healthy: stale.length === 0,
      details: {
        staleCount: stale.length,
      },
    };
  }

  private async checkOrphanedHolds(): Promise<HealthCheck> {
    // Find holds without corresponding bookings
    const orphaned = await this.db.holds.aggregate([
      {
        $lookup: {
          from: 'bookings',
          localField: 'bookingId',
          foreignField: 'id',
          as: 'booking',
        },
      },
      {
        $match: {
          status: 'active',
          booking: { $eq: [] },
        },
      },
    ]);

    return {
      name: 'orphaned_holds',
      healthy: orphaned.length === 0,
      details: {
        orphanedCount: orphaned.length,
      },
    };
  }
}

// ============================================================================
// RECONCILIATION
// ============================================================================

class InventoryReconciler {
  async reconcileSupplier(supplierId: string): Promise<ReconciliationReport> {
    const supplier = await this.getSupplier(supplierId);

    // Fetch current state from supplier
    const supplierState = await this.fetchSupplierState(supplier);

    // Fetch our cached state
    const ourState = await this.fetchOurState(supplierId);

    // Compare and find discrepancies
    const discrepancies = this.findDiscrepancies(supplierState, ourState);

    // Auto-fix what we can
    const autoFixed = await this.autoFixDiscrepancies(discrepancies);

    // Report what needs manual attention
    const needsAttention = discrepancies.filter(d => !autoFixed.includes(d));

    return {
      supplierId,
      totalProducts: Object.keys(supplierState).length,
      discrepanciesFound: discrepancies.length,
      autoFixed: autoFixed.length,
      needsAttention: needsAttention.length,
      details: needsAttention,
    };
  }

  private findDiscrepancies(
    supplierState: Record<string, SupplierProductState>,
    ourState: Record<string, OurProductState>
  ): Discrepancy[] {
    const discrepancies: Discrepancy[] = [];

    // Check each product
    for (const [productId, supplier] of Object.entries(supplierState)) {
      const ours = ourState[productId];

      if (!ours) {
        discrepancies.push({
          type: 'missing',
          productId,
          supplier: supplier.available,
          ours: null,
        });
        continue;
      }

      // Compare availability
      for (const [date, supplierAvail] of Object.entries(supplier.dates)) {
        const ourAvail = ours.dates[date];

        if (!ourAvail) {
          discrepancies.push({
            type: 'missing_date',
            productId,
            date,
            supplier: supplierAvail,
            ours: null,
          });
          continue;
        }

        if (Math.abs(supplierAvail - ourAvail) > 2) {
          discrepancies.push({
            type: 'availability_mismatch',
            productId,
            date,
            supplier: supplierAvail,
            ours: ourAvail,
            difference: supplierAvail - ourAvail,
          });
        }
      }
    }

    return discrepancies;
  }
}
```

---

**Next:** [Booking Confirmation](./BOOKING_ENGINE_04_CONFIRMATION.md) — Confirmation process, notifications, and document generation
