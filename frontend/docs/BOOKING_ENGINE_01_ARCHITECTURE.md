# Booking Engine — Architecture

> System design, data model, and core patterns for the booking engine

**Series:** Booking Engine | **Document:** 1 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Domain Model](#domain-model)
4. [State Machine Design](#state-machine-design)
5. [Integration Points](#integration-points)
6. [Scalability Patterns](#scalability-patterns)
7. [Data Consistency](#data-consistency)
8. [Error Handling](#error-handling)

---

## Overview

The Booking Engine is the core transactional system of the travel agency platform. It manages the entire lifecycle of travel bookings from initial request through confirmation, modification, and cancellation.

### Core Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Reservation** | Create and manage booking records |
| **Inventory** | Track and allocate available inventory |
| **Pricing** | Calculate and lock prices at booking time |
| **Payment** | Coordinate payment processing |
| **Confirmation** | Generate and deliver booking confirmations |
| **Modification** | Handle booking changes and rebooking |
| **Cancellation** | Process cancellations and refunds |
| **Compliance** | Maintain audit trails and legal records |

### Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Availability** | 99.9% uptime |
| **Latency** | <500ms for booking creation |
| **Throughput** | 1000+ bookings/minute |
| **Consistency** | Strong consistency for inventory |
| **Durability** | Zero data loss |

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BOOKING ENGINE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   API Layer  │  │  Validation  │  │  Orchestration│                  │
│  │              │  │    Service   │  │    Service    │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                  │                          │
│         └─────────────────┴──────────────────┘                          │
│                           │                                              │
│  ┌────────────────────────┴────────────────────────────────────────┐   │
│  │                        State Machine                             │   │
│  │  (Manages booking lifecycle and transitions)                     │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                                │                                         │
│  ┌─────────────────────────────┴────────────────────────────────────┐  │
│  │                        Event Bus                                  │  │
│  │  (Publishes booking events for downstream consumers)             │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                         │
│         ┌──────────────────────┼──────────────────────┐                │
│         ▼                      ▼                      ▼                │
│  ┌────────────┐        ┌────────────┐        ┌────────────┐           │
│  │  Booking   │        │ Inventory  │        │  Payment   │           │
│  │ Repository │        │  Service   │        │  Service   │           │
│  └────────────┘        └────────────┘        └────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   Database    │      │ Inventory DB  │      │Payment Gateway│
│  (PostgreSQL) │      │   (Redis)     │      │   (Stripe)    │
└───────────────┘      └───────────────┘      └───────────────┘
```

### Component Responsibilities

#### API Layer
- HTTP/REST endpoints for booking operations
- Request validation and authentication
- Response formatting
- Rate limiting

#### Validation Service
- Business rule validation
- Policy enforcement
- Data integrity checks
- Constraint verification

#### Orchestration Service
- Coordinates multi-step booking flows
- Manages transaction boundaries
- Handles compensation on failure
- Saga pattern implementation

#### State Machine
- Enforces valid state transitions
- Prevents invalid operations
- Tracks booking lifecycle
- Event-driven state changes

---

## Domain Model

### Core Entities

```typescript
// ============================================================================
// BOOKING AGGREGATE ROOT
// ============================================================================

interface Booking {
  // Identity
  id: string;                    // UUID
  reference: string;             // Human-readable (e.g., "TRV-2024-AB1234")

  // Status & State
  status: BookingStatus;         // Business status
  state: BookingState;           // Machine state
  version: number;               // Optimistic concurrency

  // Customer
  customerId: string;
  customer: CustomerInfo;

  // Booking Items
  items: BookingItem[];
  itemCounts: {
    total: number;
    confirmed: number;
    pending: number;
    cancelled: number;
  };

  // Pricing
  pricing: {
    subtotal: number;
    taxes: number;
    fees: number;
    discount: number;
    total: number;
    currency: string;
    lockedAt: Date;             // When price was locked
  };

  // Payments
  payments: BookingPayment[];
  paymentStatus: PaymentStatus;

  // Holds (temporary inventory reservations)
  holds: InventoryHold[];

  // Timeline (event sourcing)
  timeline: BookingEvent[];

  // Metadata
  metadata: {
    source: 'web' | 'mobile' | 'agent' | 'api';
    channel: string;
    campaign?: string;
    affiliate?: string;
    tags: string[];
  };

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
  expiresAt?: Date;
  confirmedAt?: Date;
  cancelledAt?: Date;
  completedAt?: Date;
}

// ============================================================================
// BOOKING STATUS (Business Status)
// ============================================================================

type BookingStatus =
  | 'draft'           // Initial state, being constructed
  | 'pending'         // Submitted, awaiting confirmation
  | 'confirmed'       // Successfully booked
  | 'modified'        // Changes in progress
  | 'partial'         // Some items confirmed, some pending
  | 'cancelled'       // Cancelled
  | 'refunded'        // Refunded
  | 'failed'          // Booking failed
  | 'expired'         // Draft/expired without completion
  | 'completed';      // Travel completed

// ============================================================================
// BOOKING STATE (Machine State)
// ============================================================================

type BookingState =
  | 'draft'
  | 'validating'
  | 'pricing'
  | 'reserving'
  | 'paying'
  | 'confirming'
  | 'confirmed'
  | 'modifying'
  | 'cancelling'
  | 'cancelled'
  | 'refunding'
  | 'refunded'
  | 'failed'
  | 'expired'
  | 'completed';

// ============================================================================
// BOOKING ITEM
// ============================================================================

interface BookingItem {
  id: string;
  bookingId: string;

  // Product Details
  type: ProductType;
  supplierId: string;
  supplierReference?: string;   // Supplier's booking reference
  productId: string;
  availabilityId: string;

  // Dates & Times
  dates: {
    start: Date;
    end: Date;
    nights?: number;
  };

  // Details (type-specific)
  accommodation?: AccommodationDetails;
  flight?: FlightDetails;
  transfer?: TransferDetails;
  activity?: ActivityDetails;

  // Pricing
  pricing: {
    baseRate: number;
    taxes: number;
    fees: number;
    discount: number;
    total: number;
    currency: string;
  };

  // Status
  status: ItemStatus;
  confirmationCode?: string;

  // Timestamps
  confirmedAt?: Date;
  cancelledAt?: Date;

  // Cancellation Terms
  cancellation: {
    allowed: boolean;
    deadline?: Date;
    penalty?: {
      amount: number;
      percentage: number;
    };
  };
}

type ProductType =
  | 'accommodation'
  | 'flight'
  | 'transfer'
  | 'activity'
  | 'insurance'
  | 'package';

type ItemStatus =
  | 'pending'         // Awaiting confirmation
  | 'confirmed'       // Confirmed by supplier
  | 'cancelled'       // Cancelled
  | 'failed'          // Failed to confirm
  | 'modified';       // Modified from original

// ============================================================================
// CUSTOMER INFO
// ============================================================================

interface CustomerInfo {
  id: string;
  type: 'guest' | 'registered' | 'agent';

  // Primary Contact
  primary: {
    title: string;
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
  };

  // Travelers (for the booking)
  travelers: Traveler[];

  // Billing (may differ from primary)
  billing?: {
    firstName: string;
    lastName: string;
    address: Address;
  };
}

interface Traveler {
  id: string;
  type: 'adult' | 'child' | 'infant';
  title: string;
  firstName: string;
  lastName: string;
  dateOfBirth: Date;
  nationality: string;
  passport?: PassportDetails;
  preferences?: Record<string, unknown>;
}

// ============================================================================
// INVENTORY HOLD
// ============================================================================

interface InventoryHold {
  id: string;
  bookingId: string;
  itemId: string;

  // Hold Details
  type: 'temp' | 'confirmed';
  quantity: number;
  expiresAt: Date;

  // Inventory Reference
  supplierId: string;
  inventoryId: string;

  // Status
  status: 'active' | 'released' | 'confirmed';

  // Timestamps
  createdAt: Date;
  releasedAt?: Date;
  confirmedAt?: Date;
}

// ============================================================================
// BOOKING EVENT (Event Sourcing)
// ============================================================================

interface BookingEvent {
  id: string;
  bookingId: string;
  type: EventType;
  state: BookingState;

  // Event Data
  data: Record<string, unknown>;

  // Causality
  causationId?: string;   // Command that caused this
  correlationId: string;  // Correlates events in a flow

  // Timestamps
  timestamp: Date;
  actor: {
    type: 'user' | 'system' | 'agent';
    id: string;
  };
}

type EventType =
  | 'booking.created'
  | 'booking.validated'
  | 'booking.priced'
  | 'booking.reserved'
  | 'booking.paid'
  | 'booking.confirmed'
  | 'booking.modified'
  | 'booking.cancelled'
  | 'booking.refunded'
  | 'booking.failed'
  | 'booking.expired'
  | 'item.confirmed'
  | 'item.cancelled'
  | 'hold.created'
  | 'hold.released';
```

### Database Schema

```sql
-- ============================================================================
-- BOOKINGS TABLE
-- ============================================================================

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference VARCHAR(50) UNIQUE NOT NULL,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    state VARCHAR(20) NOT NULL DEFAULT 'draft',
    version INT NOT NULL DEFAULT 1,

    -- Customer
    customer_id UUID NOT NULL,
    customer_info JSONB NOT NULL,

    -- Pricing
    pricing JSONB NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Holds
    hold_count INT NOT NULL DEFAULT 0,
    hold_expires_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'draft', 'pending', 'confirmed', 'modified', 'partial',
        'cancelled', 'refunded', 'failed', 'expired', 'completed'
    ))
);

-- Indexes
CREATE INDEX idx_bookings_reference ON bookings(reference);
CREATE INDEX idx_bookings_customer ON bookings(customer_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_state ON bookings(state);
CREATE INDEX idx_bookings_created ON bookings(created_at DESC);

-- ============================================================================
-- BOOKING_ITEMS TABLE
-- ============================================================================

CREATE TABLE booking_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,

    -- Product
    type VARCHAR(20) NOT NULL,
    supplier_id UUID NOT NULL,
    supplier_reference VARCHAR(100),
    product_id VARCHAR(100) NOT NULL,
    availability_id VARCHAR(100) NOT NULL,

    -- Details
    details JSONB NOT NULL,

    -- Dates
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    nights INT,

    -- Pricing
    pricing JSONB NOT NULL,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    confirmation_code VARCHAR(100),

    -- Cancellation
    cancellation_terms JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    confirmed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_item_type CHECK (type IN (
        'accommodation', 'flight', 'transfer', 'activity', 'insurance', 'package'
    )),
    CONSTRAINT valid_item_status CHECK (status IN (
        'pending', 'confirmed', 'cancelled', 'failed', 'modified'
    ))
);

-- Indexes
CREATE INDEX idx_booking_items_booking ON booking_items(booking_id);
CREATE INDEX idx_booking_items_supplier ON booking_items(supplier_id);
CREATE INDEX idx_booking_items_dates ON booking_items(start_date, end_date);
CREATE INDEX idx_booking_items_status ON booking_items(status);

-- ============================================================================
-- BOOKING_EVENTS TABLE (Event Sourcing)
-- ============================================================================

CREATE TABLE booking_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id),

    -- Event
    type VARCHAR(50) NOT NULL,
    state VARCHAR(20) NOT NULL,
    data JSONB NOT NULL DEFAULT '{}',

    -- Causality
    causation_id UUID,
    correlation_id UUID NOT NULL,

    -- Actor
    actor_type VARCHAR(20) NOT NULL,
    actor_id VARCHAR(100) NOT NULL,

    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_booking_events_booking ON booking_events(booking_id);
CREATE INDEX idx_booking_events_type ON booking_events(type);
CREATE INDEX idx_booking_events_timestamp ON booking_events(timestamp DESC);
CREATE INDEX idx_booking_events_correlation ON booking_events(correlation_id);

-- ============================================================================
-- INVENTORY_HOLDS TABLE
-- ============================================================================

CREATE TABLE inventory_holds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id),
    item_id UUID NOT NULL REFERENCES booking_items(id),

    -- Hold Details
    type VARCHAR(10) NOT NULL DEFAULT 'temp',
    quantity INT NOT NULL DEFAULT 1,
    expires_at TIMESTAMPTZ NOT NULL,

    -- Inventory
    supplier_id UUID NOT NULL,
    inventory_id VARCHAR(100) NOT NULL,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_hold_type CHECK (type IN ('temp', 'confirmed')),
    CONSTRAINT valid_hold_status CHECK (status IN ('active', 'released', 'confirmed')),
    CONSTRAINT hold_not_expired CHECK (expires_at > created_at)
);

-- Indexes
CREATE INDEX idx_holds_booking ON inventory_holds(booking_id);
CREATE INDEX idx_holds_item ON inventory_holds(item_id);
CREATE INDEX idx_holds_inventory ON inventory_holds(supplier_id, inventory_id);
CREATE INDEX idx_holds_expires ON inventory_holds(expires_at);
CREATE INDEX idx_holds_status ON inventory_holds(status) WHERE status = 'active';

-- For cleanup job
CREATE INDEX idx_holds_expired ON inventory_holds(expires_at)
    WHERE status = 'active' AND expires_at < NOW();
```

---

## State Machine Design

### State Transition Diagram

```
                    ┌─────────────────────────────────────────────┐
                    │                                             │
                    │     ┌──────────┐      ┌──────────┐         │
                    │     │  DRAFT   │      │ EXPIRED  │         │
                    │     └─────┬────┘      └──────────┘         │
                    │           │                                  │
                    │           │ createBooking()                 │
                    │           ▼                                  │
                    │     ┌──────────┐                            │
                    │     │VALIDATING│                            │
                    │     └─────┬────┘                            │
                    │           │                                  │
                    │           │ valid                             │
                    │           ▼                                  │
                    │     ┌──────────┐                            │
                    │     │ PRICING  │                            │
                    │     └─────┬────┘                            │
                    │           │                                  │
                    │           │ price locked                     │
                    │           ▼                                  │
                    │     ┌──────────┐                            │
                    │     │RESERVING│─────────────┐               │
                    │     └─────┬────┘             │               │
                    │           │                   │ inventory     │
                    │           │ hold created      │ unavailable   │
                    │           ▼                   ▼               │
                    │     ┌──────────┐        ┌──────────┐        │
                    │     │  PAYING  │        │  FAILED  │        │
                    │     └─────┬────┘        └──────────┘        │
                    │           │                                      │
                    │           │ payment authorized                  │
                    │           ▼                                      │
                    │     ┌──────────┐                                │
                    │     │CONFIRMING│───┐                            │
                    │     └─────┬────┘   │                            │
                    │           │         │ supplier                  │
                    │           │         │ failed                    │
                    │           │         ▼                           │
                    │           │    ┌──────────┐                     │
                    │           │    │  FAILED  │                     │
                    │           │    └──────────┘                     │
                    │           │                                       │
                    │           │ all confirmed                        │
                    │           ▼                                       │
                    │     ┌──────────┐                                 │
                    └─────│CONFIRMED │─────────────────────────────┘
          ┌──────────────┐ └──────────┘
          │              │     │
          │ modify()     │     │ cancel()
          │              │     ▼
          ▼              │  ┌──────────┐
    ┌──────────┐         │  │CANCELLING│
    │MODIFYING │──────── │  └─────┬────┘
    └─────┬────┘         │        │
          │              │        │ refund processed
          │              │        ▼
          │              │  ┌──────────┐
          │              └──│CANCELLED │
          │                 └──────────┘
          │
          │ complete()
          ▼
    ┌──────────┐
    │COMPLETED │
    └──────────┘
```

### State Transition Rules

```typescript
// ============================================================================
// STATE TRANSITION CONFIGURATION
// ============================================================================

interface StateTransition {
  from: BookingState;
  to: BookingState;
  trigger: string;
  guard?: (booking: Booking) => boolean;
  action?: (booking: Booking) => Promise<void>;
}

const STATE_TRANSITIONS: StateTransition[] = [
  // Draft lifecycle
  {
    from: 'draft',
    to: 'validating',
    trigger: 'validate',
    guard: (b) => b.items.length > 0,
  },
  {
    from: 'validating',
    to: 'pricing',
    trigger: 'price',
    guard: (b) => b.items.every(i => i.pricing.total > 0),
  },
  {
    from: 'pricing',
    to: 'reserving',
    trigger: 'reserve',
    guard: (b) => b.pricing.lockedAt !== undefined,
  },

  // Hold management
  {
    from: 'reserving',
    to: 'paying',
    trigger: 'hold_created',
    guard: (b) => b.holds.length === b.items.length,
  },

  // Payment
  {
    from: 'paying',
    to: 'confirming',
    trigger: 'pay',
    guard: (b) => b.payments.some(p => p.status === 'authorized'),
  },

  // Confirmation
  {
    from: 'confirming',
    to: 'confirmed',
    trigger: 'confirm',
    guard: (b) => b.items.every(i => i.status === 'confirmed'),
  },

  // Failure paths
  {
    from: 'reserving',
    to: 'failed',
    trigger: 'inventory_unavailable',
  },
  {
    from: 'paying',
    to: 'failed',
    trigger: 'payment_failed',
  },
  {
    from: 'confirming',
    to: 'failed',
    trigger: 'supplier_failed',
  },

  // Draft expiration
  {
    from: 'draft',
    to: 'expired',
    trigger: 'expire',
    guard: (b) => b.expiresAt && b.expiresAt < new Date(),
  },

  // Modification
  {
    from: 'confirmed',
    to: 'modifying',
    trigger: 'modify',
    guard: (b) => canModify(b),
  },
  {
    from: 'modifying',
    to: 'confirmed',
    trigger: 'complete_modification',
  },

  // Cancellation
  {
    from: 'confirmed',
    to: 'cancelling',
    trigger: 'cancel',
    guard: (b) => canCancel(b),
  },
  {
    from: 'cancelling',
    to: 'cancelled',
    trigger: 'complete_cancellation',
  },
  {
    from: 'cancelled',
    to: 'refunding',
    trigger: 'refund',
    guard: (b) => b.payments.some(p => p.status === 'captured'),
  },
  {
    from: 'refunding',
    to: 'refunded',
    trigger: 'refund_complete',
  },

  // Completion
  {
    from: 'confirmed',
    to: 'completed',
    trigger: 'complete',
    guard: (b) => isTripComplete(b),
  },
];

// ============================================================================
// STATE MACHINE IMPLEMENTATION
// ============================================================================

class BookingStateMachine {
  private transitions = new Map<string, StateTransition[]>();

  constructor() {
    this.buildTransitionMap();
  }

  private buildTransitionMap() {
    for (const transition of STATE_TRANSITIONS) {
      const key = transition.from;
      if (!this.transitions.has(key)) {
        this.transitions.set(key, []);
      }
      this.transitions.get(key)!.push(transition);
    }
  }

  canTransition(booking: Booking, to: BookingState, trigger: string): boolean {
    const validTransitions = this.transitions.get(booking.state) || [];
    const transition = validTransitions.find(
      t => t.to === to && t.trigger === trigger
    );

    if (!transition) {
      return false;
    }

    return transition.guard ? transition.guard(booking) : true;
  }

  async transition(
    booking: Booking,
    to: BookingState,
    trigger: string,
    context?: Record<string, unknown>
  ): Promise<Booking> {
    if (!this.canTransition(booking, to, trigger)) {
      throw new InvalidStateTransitionError(
        booking.state,
        to,
        trigger
      );
    }

    const validTransitions = this.transitions.get(booking.state) || [];
    const transition = validTransitions.find(
      t => t.to === to && t.trigger === trigger
    )!;

    // Execute action if defined
    if (transition.action) {
      await transition.action(booking);
    }

    // Update state
    const previousState = booking.state;
    booking.state = to;
    booking.updatedAt = new Date();

    // Record event
    await this.recordEvent(booking, {
      type: `booking.${trigger}`,
      previousState,
      newState: to,
      trigger,
      context,
    });

    return booking;
  }

  private async recordEvent(
    booking: Booking,
    event: Partial<BookingEvent>
  ): Promise<void> {
    // Event storage implementation
    await BookingEvent.create({
      bookingId: booking.id,
      type: event.type!,
      state: booking.state,
      data: event.context || {},
      correlationId: booking.id,
      actorType: 'system',
      actorId: 'booking-engine',
    });
  }
}

// ============================================================================
// GUARD FUNCTIONS
// ============================================================================

function canModify(booking: Booking): boolean {
  const now = new Date();

  // Cannot modify if already cancelled
  if (booking.status === 'cancelled') {
    return false;
  }

  // Check modification deadline for each item
  for (const item of booking.items) {
    if (item.cancellation.deadline && item.cancellation.deadline < now) {
      return false;
    }
  }

  return true;
}

function canCancel(booking: Booking): boolean {
  const now = new Date();

  // Cannot cancel already cancelled bookings
  if (booking.status === 'cancelled' || booking.status === 'refunded') {
    return false;
  }

  // Check if any items are non-refundable
  for (const item of booking.items) {
    if (!item.cancellation.allowed) {
      return false;
    }
    if (item.cancellation.deadline && item.cancellation.deadline < now) {
      return false;
    }
  }

  return true;
}

function isTripComplete(booking: Booking): boolean {
  const now = new Date();
  const lastEndDate = Math.max(
    ...booking.items.map(i => i.dates.end.getTime())
  );
  return now > new Date(lastEndDate);
}
```

---

## Integration Points

### External Dependencies

| Service | Purpose | SLA | Fallback |
|---------|---------|-----|----------|
| **Payment Gateway** | Process payments | 99.9% | Retry, alternative gateway |
| **Supplier APIs** | Confirm bookings | 95% | Queue for retry |
| **Notification Service** | Send confirmations | 99% | Queue for retry |
| **Inventory Service** | Check availability | 99.9% | Cached data |
| **Pricing Service** | Calculate prices | 99% | Cached prices |

### API Contracts

```typescript
// ============================================================================
// PAYMENT SERVICE CONTRACT
// ============================================================================

interface PaymentService {
  authorize(request: {
    bookingId: string;
    amount: number;
    currency: string;
    paymentMethod: PaymentMethod;
    customer: CustomerInfo;
  }): Promise<PaymentAuthorization>;

  capture(authorizationId: string): Promise<PaymentCapture>;

  refund(paymentId: string, amount?: number): Promise<PaymentRefund>;

  void(authorizationId: string): Promise<void>;
}

// ============================================================================
// SUPPLIER SERVICE CONTRACT
// ============================================================================

interface SupplierService {
  checkAvailability(request: {
    supplierId: string;
    productId: string;
    dates: DateRange;
    quantity: number;
  }): Promise<AvailabilityResponse>;

  createHold(request: {
    supplierId: string;
    productId: string;
    dates: DateRange;
    quantity: number;
    expiresAt: Date;
  }): Promise<HoldConfirmation>;

  confirmBooking(request: {
    supplierId: string;
    holdId: string;
    customerDetails: CustomerInfo;
  }): Promise<SupplierBooking>;

  cancelBooking(supplierBookingRef: string): Promise<CancellationConfirmation>;
}

// ============================================================================
// NOTIFICATION SERVICE CONTRACT
// ============================================================================

interface NotificationService {
  sendBookingConfirmation(booking: Booking): Promise<void>;

  sendCancellationNotice(booking: Booking): Promise<void>;

  sendModificationNotice(booking: Booking, changes: Modification[]): Promise<void>;

  sendRefundNotice(booking: Booking, refund: Refund): Promise<void>;
}
```

---

## Scalability Patterns

### Horizontal Scaling

**Stateless API Layer**
- Multiple instances behind load balancer
- No session state in memory
- All state in database/cache

**Distributed Locking**
- Redis-based locks for inventory
- Prevents double-booking across instances
- Automatic expiry

```typescript
// Distributed lock implementation
class DistributedLock {
  constructor(private redis: Redis) {}

  async acquire(key: string, ttl: number): Promise<Lock | null> {
    const lockKey = `lock:${key}`;
    const lockValue = crypto.randomUUID();

    const acquired = await this.redis.set(
      lockKey,
      lockValue,
      {
        NX: true,  // Only set if not exists
        PX: ttl,   // Expire after TTL ms
      }
    );

    if (acquired === 'OK') {
      return {
        key: lockKey,
        value: lockValue,
        release: async () => this.release(lockKey, lockValue),
      };
    }

    return null;
  }

  private async release(key: string, value: string): Promise<void> {
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
      else
        return 0
      end
    `;
    await this.redis.eval(script, { keys: [key], arguments: [value] });
  }
}
```

### Database Scaling

**Partitioning Strategy**
- Partition by booking date range
- Partition by customer region
- Partition by supplier

**Read Replicas**
- Writes to primary
- Reads from replicas for queries
- Lag-aware queries

**Connection Pooling**
- PgBouncer for connection management
- Transaction mode pooling
- Prepared statement caching

### Caching Strategy

```typescript
// Cache layers
const CACHE_STRATEGY = {
  // L1: In-memory (per instance)
  memory: {
    ttl: 60, // seconds
    items: ['pricing-rules', 'cancellation-policies'],
  },

  // L2: Redis (shared)
  redis: {
    ttl: 300, // seconds
    items: ['availability', 'supplier-catalog'],
  },

  // L3: CDN (static content)
  cdn: {
    ttl: 3600, // seconds
    items: ['images', 'documents'],
  },
};
```

---

## Data Consistency

### Transaction Boundaries

```typescript
// Booking transaction with compensation
async function createBooking(
  request: CreateBookingRequest
): Promise<Booking> {
  const saga = new Saga('create-booking');

  try {
    // Step 1: Create booking record
    const booking = await saga.addStep(
      async () => {
        return await Booking.create({
          status: 'draft',
          state: 'validating',
          ...request,
        });
      },
      async (booking) => {
        await Booking.delete(booking.id);
      }
    );

    // Step 2: Validate items
    await saga.addStep(
      async () => {
        return await validateBookingItems(booking);
      },
      async () => {
        // No compensation needed - validation is read-only
      }
    );

    // Step 3: Lock pricing
    await saga.addStep(
      async () => {
        return await lockPricing(booking);
      },
      async (pricing) => {
        await releasePricingLock(pricing.id);
      }
    );

    // Step 4: Create inventory holds
    await saga.addStep(
      async () => {
        return await createInventoryHolds(booking);
      },
      async (holds) => {
        await Promise.all(holds.map(h => releaseHold(h.id)));
      }
    );

    // Step 5: Process payment
    await saga.addStep(
      async () => {
        return await processPayment(booking);
      },
      async (payment) => {
        await voidPayment(payment.id);
      }
    );

    // Step 6: Confirm with suppliers
    await saga.addStep(
      async () => {
        return await confirmWithSuppliers(booking);
      },
      async (confirmations) => {
        await Promise.all(
          confirmations.map(c => cancelSupplierBooking(c.reference))
        );
      }
    );

    // All steps successful
    booking.status = 'confirmed';
    booking.state = 'confirmed';
    booking.confirmedAt = new Date();
    await booking.save();

    return booking;

  } catch (error) {
    // Compensate all completed steps
    await saga.compensate();
    throw error;
  }
}
```

### Idempotency

```typescript
// Idempotent booking creation
async function createBookingIdempotent(
  request: CreateBookingRequest,
  idempotencyKey: string
): Promise<Booking> {
  // Check if already processed
  const existing = await IdempotencyStore.get(idempotencyKey);
  if (existing) {
    return await Booking.findByID(existing.bookingId);
  }

  // Create new booking
  const booking = await createBooking(request);

  // Store idempotency record
  await IdempotencyStore.set(idempotencyKey, {
    bookingId: booking.id,
    createdAt: new Date(),
  }, { ttl: 86400 }); // 24 hours

  return booking;
}
```

---

## Error Handling

### Error Categories

| Category | Example | Handling |
|----------|---------|----------|
| **Validation** | Invalid dates, missing fields | Return 400, detailed errors |
| **Business Rule** | Cancellation deadline passed | Return 422, explain rule |
| **Inventory** | No availability | Return 409, suggest alternatives |
| **Payment** | Card declined | Return 402, retry guidance |
| **Supplier** | API timeout | Queue for retry |
| **System** | Database connection | Return 503, automatic retry |

### Error Response Format

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    retryable?: boolean;
    retryAfter?: number; // seconds
  };
  request_id: string;
}
```

### Retry Strategy

```typescript
const RETRY_CONFIG = {
  payment: {
    maxAttempts: 3,
    backoff: 'exponential',
    initialDelay: 1000, // ms
    maxDelay: 10000,
  },
  supplier: {
    maxAttempts: 5,
    backoff: 'exponential',
    initialDelay: 2000,
    maxDelay: 60000,
  },
  notification: {
    maxAttempts: 10,
    backoff: 'exponential',
    initialDelay: 5000,
    maxDelay: 300000, // 5 minutes
  },
};
```

---

## Monitoring & Observability

### Key Metrics

| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| Booking creation rate | Counter | - |
| Booking creation latency | Histogram | p95 > 1s |
| Booking failure rate | Gauge | > 5% |
| Hold expiration rate | Counter | - |
| Payment success rate | Gauge | < 95% |
| Supplier confirmation latency | Histogram | p95 > 30s |

### Distributed Tracing

```typescript
// OpenTelemetry instrumentation
import { trace } from '@opentelemetry/api';

async function createBookingTraced(request: CreateBookingRequest) {
  const tracer = trace.getTracer('booking-engine');

  return await tracer.startActiveSpan('createBooking', async (span) => {
    span.setAttribute('booking.customer_id', request.customerId);
    span.setAttribute('booking.item_count', request.items.length);

    try {
      const booking = await createBooking(request);
      span.setAttribute('booking.id', booking.id);
      span.setStatus({ code: SpanStatusCode.OK });
      return booking;
    } catch (error) {
      span.recordException(error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw error;
    } finally {
      span.end();
    }
  });
}
```

---

**Next:** [Reservation Flow](./BOOKING_ENGINE_02_RESERVATION_FLOW.md) — Detailed booking creation and processing flows
