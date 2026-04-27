# Booking Engine — State Machine

> Complete booking lifecycle, state transitions, and event-driven architecture

**Series:** Booking Engine | **Document:** 8 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [State Definitions](#state-definitions)
3. [State Transitions](#state-transitions)
4. [Event-Driven Architecture](#event-driven-architecture)
5. [State Persistence](#state-persistence)
6. [Recovery & Rollback](#recovery--rollback)
7. [State Queries](#state-queries)
8. [Observability](#observability)

---

## Overview

The booking state machine manages the complete lifecycle of a booking from initial creation through completion. It ensures valid transitions, maintains audit trails, and enables recovery from failures.

### State Machine Benefits

| Benefit | Description |
|---------|-------------|
| **Validity** | Only valid state transitions allowed |
| **Auditability** | Complete history of all state changes |
| **Recoverability** | Can replay events to rebuild state |
| **Debugging** | Clear view of booking lifecycle |
| **Testing** | Deterministic state transitions |

---

## State Definitions

### Complete State Model

```typescript
// ============================================================================
// STATE DEFINITIONS
// ============================================================================

type BookingState =
  // Lifecycle states
  | 'draft'           // Initial state, being constructed
  | 'validating'      // Validating request data
  | 'pricing'         // Calculating and locking prices
  | 'reserving'       // Reserving inventory
  | 'paying'          // Processing payment
  | 'confirming'      // Confirming with suppliers
  | 'confirmed'       // Successfully confirmed
  | 'modifying'       // Being modified
  | 'cancelling'      // Being cancelled
  | 'cancelled'       // Cancelled
  | 'refunding'       // Processing refund
  | 'refunded'        // Refund complete
  | 'completed'       // Travel completed

  // Error states
  | 'failed'          // Operation failed
  | 'expired'         // Draft/pricing expired

  // Waitlist states
  | 'waitlisted'      // On waitlist
  | 'waitlist_offered' // Offered waitlist spot
  | 'waitlist_converting'; // Converting from waitlist

type BookingStatus =
  | 'draft'           // Being created
  | 'pending'         // Submitted, awaiting confirmation
  | 'confirmed'       // Successfully booked
  | 'modified'        // Has been modified
  | 'partial'         // Some items confirmed, some pending
  | 'cancelled'       // Cancelled
  | 'refunded'        // Refunded
  | 'failed'          // Failed
  | 'expired'         // Expired
  | 'completed'       // Travel completed
  | 'waitlisted';     // On waitlist

interface StateMetadata {
  // Current state info
  currentState: BookingState;
  currentStatus: BookingStatus;
  version: number;

  // State history
  previousStates: StateHistoryEntry[];

  // Transition info
  lastTransitionAt: Date;
  lastTransitionBy: string;

  // Expiration
  expiresAt?: Date;

  // Blocking conditions
  blockedBy?: string[];
  blockReason?: string;
}

interface StateHistoryEntry {
  from: BookingState;
  to: BookingState;
  at: Date;
  by: string;
  reason?: string;
  duration?: number; // milliseconds spent in state
}
```

### State Descriptions

```typescript
// ============================================================================
// STATE CONFIGURATION
// ============================================================================

interface StateConfig {
  state: BookingState;
  description: string;
  category: 'initial' | 'transient' | 'terminal' | 'error';
  timeout?: number; // milliseconds
  autoTransition?: {
    to: BookingState;
    after: number; // milliseconds
    condition?: string;
  };
  allowedTransitions: BookingState[];
  entryActions?: string[];
  exitActions?: string[];
}

const STATE_CONFIGS: Record<BookingState, StateConfig> = {
  draft: {
    state: 'draft',
    description: 'Booking being constructed by customer',
    category: 'initial',
    timeout: 1800000, // 30 minutes
    autoTransition: {
      to: 'expired',
      after: 1800000,
    },
    allowedTransitions: ['validating', 'expired'],
    entryActions: ['initialize_timeline'],
    exitActions: ['freeze_items'],
  },

  validating: {
    state: 'validating',
    description: 'Validating booking request',
    category: 'transient',
    timeout: 30000, // 30 seconds
    autoTransition: {
      to: 'failed',
      after: 30000,
    },
    allowedTransitions: ['pricing', 'failed'],
    entryActions: ['validate_customer', 'validate_items', 'validate_dates'],
  },

  pricing: {
    state: 'pricing',
    description: 'Calculating and locking prices',
    category: 'transient',
    timeout: 15000, // 15 seconds
    allowedTransitions: ['reserving', 'failed', 'expired'],
    entryActions: ['calculate_prices', 'lock_prices'],
    exitActions: ['release_price_lock'],
  },

  reserving: {
    state: 'reserving',
    description: 'Reserving inventory',
    category: 'transient',
    timeout: 60000, // 1 minute
    allowedTransitions: ['paying', 'failed'],
    entryActions: ['create_holds', 'check_inventory'],
    exitActions: ['release_holds'],
  },

  paying: {
    state: 'paying',
    description: 'Processing payment',
    category: 'transient',
    timeout: 120000, // 2 minutes
    allowedTransitions: ['confirming', 'failed'],
    entryActions: ['authorize_payment', 'verify_funds'],
    exitActions: ['void_authorization'],
  },

  confirming: {
    state: 'confirming',
    description: 'Confirming with suppliers',
    category: 'transient',
    timeout: 300000, // 5 minutes
    allowedTransitions: ['confirmed', 'partial', 'failed'],
    entryActions: ['confirm_suppliers', 'generate_documents'],
  },

  confirmed: {
    state: 'confirmed',
    description: 'Booking confirmed',
    category: 'terminal',
    allowedTransitions: ['modifying', 'cancelling', 'completed'],
    entryActions: ['send_confirmation', 'update_analytics'],
  },

  modifying: {
    state: 'modifying',
    description: 'Booking being modified',
    category: 'transient',
    timeout: 300000, // 5 minutes
    allowedTransitions: ['confirmed', 'partial', 'failed'],
    entryActions: ['calculate_changes', 'check_availability'],
    exitActions: ['rollback_changes'],
  },

  cancelling: {
    state: 'cancelling',
    description: 'Booking being cancelled',
    category: 'transient',
    timeout: 120000, // 2 minutes
    allowedTransitions: ['cancelled', 'refunding', 'failed'],
    entryActions: ['cancel_suppliers', 'release_inventory'],
  },

  cancelled: {
    state: 'cancelled',
    description: 'Booking cancelled',
    category: 'terminal',
    allowedTransitions: ['refunding'],
    entryActions: ['send_cancellation_notice'],
  },

  refunding: {
    state: 'refunding',
    description: 'Processing refund',
    category: 'transient',
    timeout: 300000, // 5 minutes
    allowedTransitions: ['refunded', 'failed'],
    entryActions: ['process_refund'],
  },

  refunded: {
    state: 'refunded',
    description: 'Refund processed',
    category: 'terminal',
    allowedTransitions: [],
    entryActions: ['send_refund_notice'],
  },

  completed: {
    state: 'completed',
    description: 'Travel completed',
    category: 'terminal',
    allowedTransitions: [],
    entryActions: ['send_feedback_request', 'archive_booking'],
  },

  failed: {
    state: 'failed',
    description: 'Operation failed',
    category: 'error',
    allowedTransitions: ['validating', 'cancelling'],
    entryActions: ['notify_failure', 'log_error'],
  },

  expired: {
    state: 'expired',
    description: 'Booking expired',
    category: 'error',
    allowedTransitions: [],
    entryActions: ['notify_expiry', 'cleanup'],
  },

  waitlisted: {
    state: 'waitlisted',
    description: 'On waitlist',
    category: 'terminal',
    allowedTransitions: ['waitlist_offered', 'cancelling'],
    entryActions: ['send_waitlist_confirmation'],
  },

  waitlist_offered: {
    state: 'waitlist_offered',
    description: 'Waitlist spot offered',
    category: 'transient',
    timeout: 86400000, // 24 hours
    autoTransition: {
      to: 'waitlisted',
      after: 86400000,
    },
    allowedTransitions: ['waitlist_converting', 'waitlisted', 'expired'],
    entryActions: ['send_availability_notice'],
  },

  waitlist_converting: {
    state: 'waitlist_converting',
    description: 'Converting from waitlist',
    category: 'transient',
    timeout: 3600000, // 1 hour
    allowedTransitions: ['confirmed', 'waitlisted', 'failed'],
    entryActions: ['create_booking', 'process_payment'],
  },
};
```

---

## State Transitions

### Transition Rules

```typescript
// ============================================================================
// STATE TRANSITION ENGINE
// ============================================================================

interface StateTransition {
  from: BookingState;
  to: BookingState;
  trigger: string;
  guard?: (booking: Booking, context?: TransitionContext) => boolean | Promise<boolean>;
  action?: (booking: Booking, context?: TransitionContext) => Promise<void>;
  compensation?: (booking: Booking, context?: TransitionContext) => Promise<void>;
}

interface TransitionContext {
  trigger: string;
  actor: {
    type: 'user' | 'system' | 'agent';
    id: string;
  };
  data?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

interface TransitionResult {
  success: boolean;
  previousState: BookingState;
  newState: BookingState;
  transition: StateTransition;
  error?: string;
}

class BookingStateMachine {
  private transitions: Map<string, StateTransition[]> = new Map();

  constructor() {
    this.initializeTransitions();
  }

  private initializeTransitions(): void {
    const transitions: StateTransition[] = [
      // Draft lifecycle
      {
        from: 'draft',
        to: 'validating',
        trigger: 'submit',
        guard: (b) => b.items.length > 0 && b.customerId,
        action: async (b) => {
          b.status = 'pending';
        },
      },

      {
        from: 'draft',
        to: 'expired',
        trigger: 'expire',
        guard: (b) => b.expiresAt && b.expiresAt < new Date(),
      },

      // Validation flow
      {
        from: 'validating',
        to: 'pricing',
        trigger: 'validated',
        guard: async (b) => await this.isValid(b),
      },

      {
        from: 'validating',
        to: 'failed',
        trigger: 'validation_failed',
      },

      // Pricing flow
      {
        from: 'pricing',
        to: 'reserving',
        trigger: 'priced',
        guard: (b) => b.pricing.lockedAt !== undefined,
        action: async (b) => {
          // Price lock created
        },
        compensation: async (b) => {
          await releasePricingLock(b.pricing.lockId);
        },
      },

      {
        from: 'pricing',
        to: 'expired',
        trigger: 'price_expired',
      },

      // Reservation flow
      {
        from: 'reserving',
        to: 'paying',
        trigger: 'reserved',
        guard: async (b) => {
          const holds = await InventoryHold.find({ bookingId: b.id, status: 'active' });
          return holds.length === b.items.length;
        },
        action: async (b) => {
          b.holdCount = b.items.length;
        },
        compensation: async (b) => {
          await releaseAllHolds(b.id);
        },
      },

      {
        from: 'reserving',
        to: 'failed',
        trigger: 'inventory_unavailable',
      },

      // Payment flow
      {
        from: 'paying',
        to: 'confirming',
        trigger: 'paid',
        guard: async (b) => {
          const payment = await BookingPayment.findOne({ bookingId: b.id, status: 'authorized' });
          return !!payment;
        },
        action: async (b) => {
          b.paymentStatus = 'paid';
        },
        compensation: async (b) => {
          await voidAllPayments(b.id);
        },
      },

      {
        from: 'paying',
        to: 'failed',
        trigger: 'payment_failed',
      },

      // Confirmation flow
      {
        from: 'confirming',
        to: 'confirmed',
        trigger: 'confirmed',
        guard: async (b) => {
          const confirmedItems = b.items.filter(i => i.status === 'confirmed');
          return confirmedItems.length === b.items.length;
        },
        action: async (b) => {
          b.status = 'confirmed';
          b.confirmedAt = new Date();
          b.reference = await generateBookingReference();
        },
      },

      {
        from: 'confirming',
        to: 'partial',
        trigger: 'partial_confirm',
        guard: async (b) => {
          const confirmedItems = b.items.filter(i => i.status === 'confirmed');
          return confirmedItems.length > 0 && confirmedItems.length < b.items.length;
        },
        action: async (b) => {
          b.status = 'partial';
          b.confirmedAt = new Date();
        },
      },

      {
        from: 'confirming',
        to: 'failed',
        trigger: 'supplier_failed',
      },

      // Confirmed state transitions
      {
        from: 'confirmed',
        to: 'modifying',
        trigger: 'modify',
        guard: async (b) => await canModify(b),
      },

      {
        from: 'confirmed',
        to: 'cancelling',
        trigger: 'cancel',
        guard: async (b) => await canCancel(b),
      },

      {
        from: 'confirmed',
        to: 'completed',
        trigger: 'complete',
        guard: (b) => isTripComplete(b),
        action: async (b) => {
          b.status = 'completed';
          b.completedAt = new Date();
        },
      },

      // Modification flow
      {
        from: 'modifying',
        to: 'confirmed',
        trigger: 'modification_complete',
        action: async (b) => {
          b.status = 'modified';
        },
      },

      {
        from: 'modifying',
        to: 'partial',
        trigger: 'modification_partial',
      },

      {
        from: 'modifying',
        to: 'failed',
        trigger: 'modification_failed',
      },

      // Cancellation flow
      {
        from: 'cancelling',
        to: 'cancelled',
        trigger: 'cancel_complete',
        action: async (b) => {
          b.status = 'cancelled';
          b.cancelledAt = new Date();
        },
      },

      {
        from: 'cancelling',
        to: 'failed',
        trigger: 'cancellation_failed',
      },

      // Refund flow
      {
        from: 'cancelled',
        to: 'refunding',
        trigger: 'refund',
        guard: async (b) => {
          const payment = await BookingPayment.findOne({ bookingId: b.id, status: 'captured' });
          return !!payment;
        },
      },

      {
        from: 'refunding',
        to: 'refunded',
        trigger: 'refund_complete',
        action: async (b) => {
          b.status = 'refunded';
        },
      },

      // Waitlist flow
      {
        from: 'waitlisted',
        to: 'waitlist_offered',
        trigger: 'available',
      },

      {
        from: 'waitlist_offered',
        to: 'waitlist_converting',
        trigger: 'accept',
      },

      {
        from: 'waitlist_offered',
        to: 'waitlisted',
        trigger: 'decline',
      },

      {
        from: 'waitlist_converting',
        to: 'confirmed',
        trigger: 'convert_complete',
      },

      {
        from: 'waitlist_converting',
        to: 'failed',
        trigger: 'convert_failed',
      },
    ];

    // Build transition map
    for (const transition of transitions) {
      const key = transition.from;
      if (!this.transitions.has(key)) {
        this.transitions.set(key, []);
      }
      this.transitions.get(key)!.push(transition);
    }
  }

  async transition(
    booking: Booking,
    to: BookingState,
    context: TransitionContext
  ): Promise<TransitionResult> {
    const previousState = booking.state;

    // Find matching transition
    const transition = this.findTransition(booking.state, to, context.trigger);
    if (!transition) {
      return {
        success: false,
        previousState,
        newState: booking.state,
        transition: null,
        error: `No transition found from ${booking.state} to ${to} with trigger ${context.trigger}`,
      };
    }

    // Check guard
    if (transition.guard) {
      const guardResult = await transition.guard(booking, context);
      if (!guardResult) {
        return {
          success: false,
          previousState,
          newState: booking.state,
          transition,
          error: 'Guard condition failed',
        };
      }
    }

    // Execute transition
    try {
      // Record entry
      await this.recordStateEntry(booking, to, context);

      // Execute action
      if (transition.action) {
        await transition.action(booking, context);
      }

      // Update state
      const previousTimestamp = booking.updatedAt;
      booking.state = to;
      booking.updatedAt = new Date();
      booking.version += 1;

      // Calculate duration in previous state
      const duration = booking.updatedAt.getTime() - previousTimestamp.getTime();

      await booking.save();

      // Record state history
      await this.recordStateHistory(booking, {
        from: previousState,
        to,
        at: booking.updatedAt,
        by: context.actor.id,
        duration,
      });

      // Publish event
      await this.publishStateChangeEvent(booking, previousState, to, context);

      return {
        success: true,
        previousState,
        newState: to,
        transition,
      };

    } catch (error) {
      // Rollback state
      booking.state = previousState;
      await booking.save();

      // Execute compensation if defined
      if (transition.compensation) {
        try {
          await transition.compensation(booking, context);
        } catch (compensationError) {
          logger.error('Compensation failed', {
            bookingId: booking.id,
            transition: `${previousState} -> ${to}`,
            error: compensationError,
          });
        }
      }

      return {
        success: false,
        previousState,
        newState: previousState,
        transition,
        error: error.message,
      };
    }
  }

  private findTransition(
    from: BookingState,
    to: BookingState,
    trigger: string
  ): StateTransition | undefined {
    const transitions = this.transitions.get(from) || [];
    return transitions.find(
      t => t.to === to && (t.trigger === trigger || t.trigger === '*')
    );
  }

  private async recordStateEntry(
    booking: Booking,
    to: BookingState,
    context: TransitionContext
  ): Promise<void> {
    // Execute entry actions for new state
    const config = STATE_CONFIGS[to];
    if (config?.entryActions) {
      for (const action of config.entryActions) {
        await this.executeAction(action, booking, context);
      }
    }
  }

  private async executeAction(
    action: string,
    booking: Booking,
    context: TransitionContext
  ): Promise<void> {
    // Action registry
    const actions: ActionRegistry = {
      send_confirmation: () => sendBookingConfirmation(booking),
      send_cancellation_notice: () => sendCancellationNotice(booking),
      update_analytics: () => updateAnalytics(booking),
      calculate_prices: () => calculateBookingPrices(booking),
      lock_prices: () => lockBookingPrices(booking),
      create_holds: () => createInventoryHolds(booking),
      release_holds: () => releaseInventoryHolds(booking),
      confirm_suppliers: () => confirmWithSuppliers(booking),
      cancel_suppliers: () => cancelWithSuppliers(booking),
      generate_documents: () => generateBookingDocuments(booking),
      // ... more actions
    };

    const handler = actions[action];
    if (handler) {
      await handler();
    }
  }

  private async recordStateHistory(
    booking: Booking,
    entry: StateHistoryEntry
  ): Promise<void> {
    await StateHistory.create({
      bookingId: booking.id,
      ...entry,
    });
  }

  private async publishStateChangeEvent(
    booking: Booking,
    from: BookingState,
    to: BookingState,
    context: TransitionContext
  ): Promise<void> {
    await EventPublisher.publish('booking.state_changed', {
      bookingId: booking.id,
      previousState: from,
      newState: to,
      actor: context.actor,
      timestamp: new Date(),
      metadata: context.metadata,
    });
  }
}

type ActionRegistry = Record<string, () => Promise<void>>;
```

---

## Event-Driven Architecture

### Event Sourcing

```typescript
// ============================================================================
// EVENT SOURCING
// ============================================================================

interface BookingEvent {
  id: string;
  bookingId: string;
  eventType: string;
  version: number;
  data: Record<string, unknown>;
  metadata: {
    causationId?: string;
    correlationId: string;
    timestamp: Date;
    actor: {
      type: string;
      id: string;
    };
  };
}

class EventStore {
  async append(event: BookingEvent): Promise<void> {
    await BookingEventRecord.create(event);
  }

  async getEvents(bookingId: string): Promise<BookingEvent[]> {
    return await BookingEventRecord.find({ bookingId }).sort({ version: 1 });
  }

  async replay(bookingId: string): Promise<Booking> {
    const events = await this.getEvents(bookingId);

    let booking: Booking | null = null;

    for (const event of events) {
      booking = await this.applyEvent(booking, event);
    }

    return booking;
  }

  private async applyEvent(
    booking: Booking | null,
    event: BookingEvent
  ): Promise<Booking> {
    switch (event.eventType) {
      case 'booking.created':
        return event.data as Booking;

      case 'booking.item_added':
        booking.items.push(event.data.item);
        return booking;

      case 'booking.pricing_locked':
        booking.pricing = event.data.pricing;
        return booking;

      case 'booking.payment_authorized':
        booking.paymentStatus = 'authorized';
        return booking;

      case 'booking.confirmed':
        booking.state = 'confirmed';
        booking.status = 'confirmed';
        booking.confirmedAt = event.data.confirmedAt;
        return booking;

      case 'booking.cancelled':
        booking.state = 'cancelled';
        booking.status = 'cancelled';
        booking.cancelledAt = event.data.cancelledAt;
        return booking;

      default:
        return booking;
    }
  }
}
```

### Event Handlers

```typescript
// ============================================================================
// EVENT HANDLERS
// ============================================================================

class BookingEventHandler {
  private handlers: Map<string, EventHandler[]> = new Map();

  constructor() {
    this.registerHandlers();
  }

  private registerHandlers(): void {
    this.on('booking.confirmed', async (event) => {
      // Send confirmation email
      await sendConfirmationEmail(event.bookingId);

      // Update analytics
      await Analytics.track('booking_confirmed', { bookingId: event.bookingId });

      // Trigger post-confirmation actions
      await triggerPostConfirmationActions(event.bookingId);
    });

    this.on('booking.cancelled', async (event) => {
      // Send cancellation email
      await sendCancellationEmail(event.bookingId);

      // Release inventory
      await releaseInventoryForBooking(event.bookingId);

      // Check waitlist
      await checkWaitlistForAvailability(event.data.productId);
    });

    this.on('booking.payment_failed', async (event) => {
      // Notify customer
      await sendPaymentFailedEmail(event.bookingId);

      // Offer retry
      await offerPaymentRetry(event.bookingId);
    });

    this.on('booking.state_changed', async (event) => {
      // Log state change
      logger.info('Booking state changed', {
        bookingId: event.bookingId,
        previousState: event.previousState,
        newState: event.newState,
      });

      // Check for timeout
      if (event.newState === 'confirming') {
        await scheduleTimeoutCheck(event.bookingId, 300000); // 5 min
      }
    });
  }

  on(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  async emit(event: BookingEvent): Promise<void> {
    const handlers = this.handlers.get(event.eventType) || [];

    for (const handler of handlers) {
      try {
        await handler(event);
      } catch (error) {
        logger.error('Event handler failed', {
          eventType: event.eventType,
          bookingId: event.bookingId,
          error,
        });
      }
    }
  }
}

type EventHandler = (event: BookingEvent) => Promise<void>;
```

---

## State Persistence

### Storage Strategy

```typescript
// ============================================================================
// STATE PERSISTENCE
// ============================================================================

interface StateSnapshot {
  bookingId: string;
  state: BookingState;
  status: BookingStatus;
  version: number;
  data: Record<string, unknown>;
  createdAt: Date;
}

class StateRepository {
  private eventStore: EventStore;
  private snapshotStore: SnapshotStore;

  async save(booking: Booking): Promise<void> {
    // Save to primary database
    await booking.save();

    // Create snapshot for large bookings or every N versions
    if (booking.version % 10 === 0) {
      await this.createSnapshot(booking);
    }
  }

  async load(bookingId: string): Promise<Booking | null> {
    // Try to load from latest snapshot
    const snapshot = await this.snapshotStore.getLatest(bookingId);

    if (snapshot) {
      // Replay events since snapshot
      const events = await this.eventStore.getEventsSince(bookingId, snapshot.createdAt);
      let booking = snapshot.data as Booking;

      for (const event of events) {
        booking = await this.eventStore['applyEvent'](booking, event);
      }

      return booking;
    }

    // No snapshot, replay all events
    return await this.eventStore.replay(bookingId);
  }

  private async createSnapshot(booking: Booking): Promise<void> {
    const snapshot: StateSnapshot = {
      bookingId: booking.id,
      state: booking.state,
      status: booking.status,
      version: booking.version,
      data: booking.toJSON(),
      createdAt: new Date(),
    };

    await this.snapshotStore.save(snapshot);
  }
}
```

---

## Recovery & Rollback

### Failure Recovery

```typescript
// ============================================================================
// RECOVERY & ROLLBACK
// ============================================================================

class StateRecoveryManager {
  async recoverBooking(bookingId: string): Promise<RecoveryResult> {
    const booking = await Booking.findById(bookingId);

    if (!booking) {
      return {
        success: false,
        reason: 'Booking not found',
      };
    }

    // Check if booking is in a transient state
    const config = STATE_CONFIGS[booking.state];
    if (config.category === 'transient') {
      // Check if state timeout has passed
      const timeInState = Date.now() - booking.updatedAt.getTime();
      if (timeInState > (config.timeout || 300000)) {
        return await this.handleTimeout(booking);
      }
    }

    // Check for incomplete operations
    const incomplete = await this.checkIncompleteOperations(booking);
    if (incomplete.length > 0) {
      return await this.handleIncomplete(booking, incomplete);
    }

    return {
      success: true,
      booking,
    };
  }

  private async handleTimeout(booking: Booking): Promise<RecoveryResult> {
    const stateMachine = new BookingStateMachine();

    // Attempt to transition to failed state
    const result = await stateMachine.transition(booking, 'failed', {
      trigger: 'timeout',
      actor: { type: 'system', id: 'recovery-manager' },
      data: { reason: 'State timeout' },
    });

    if (result.success) {
      // Run compensation actions
      await this.runCompensation(booking);
    }

    return {
      success: result.success,
      booking,
      reason: result.success ? undefined : result.error,
    };
  }

  private async checkIncompleteOperations(
    booking: Booking
  ): Promise<IncompleteOperation[]> {
    const incomplete: IncompleteOperation[] = [];

    // Check for unconfirmed holds
    const holds = await InventoryHold.find({
      bookingId: booking.id,
      status: 'active',
    });

    for (const hold of holds) {
      const age = Date.now() - hold.createdAt.getTime();
      if (age > 300000) { // 5 minutes
        incomplete.push({
          type: 'hold',
          id: hold.id,
          age,
          action: 'release',
        });
      }
    }

    // Check for pending payments
    const payments = await BookingPayment.find({
      bookingId: booking.id,
      status: 'pending',
    });

    for (const payment of payments) {
      const age = Date.now() - payment.createdAt.getTime();
      if (age > 120000) { // 2 minutes
        incomplete.push({
          type: 'payment',
          id: payment.id,
          age,
          action: 'cancel',
        });
      }
    }

    return incomplete;
  }

  private async handleIncomplete(
    booking: Booking,
    incomplete: IncompleteOperation[]
  ): Promise<RecoveryResult> {
    for (const op of incomplete) {
      switch (op.type) {
        case 'hold':
          await new HoldManager().releaseHold(op.id, 'recovery');
          break;

        case 'payment':
          await PaymentService.cancel(op.id);
          break;
      }
    }

    // Transition to failed state
    const stateMachine = new BookingStateMachine();
    await stateMachine.transition(booking, 'failed', {
      trigger: 'recovery',
      actor: { type: 'system', id: 'recovery-manager' },
    });

    return {
      success: true,
      booking,
    };
  }

  private async runCompensation(booking: Booking): Promise<void> {
    // Get state history to find compensation actions
    const history = await StateHistory.find({ bookingId: booking.id })
      .sort({ at: -1 })
      .limit(1);

    if (history.length > 0) {
      const lastTransition = history[0];
      const transition = STATE_CONFIGS[lastTransition.to];

      if (transition.exitActions) {
        for (const action of transition.exitActions) {
          await this.executeCompensationAction(action, booking);
        }
      }
    }
  }

  private async executeCompensationAction(
    action: string,
    booking: Booking
  ): Promise<void> {
    const compensations: Record<string, () => Promise<void>> = {
      release_holds: () => releaseAllHolds(booking.id),
      release_price_lock: () => releasePricingLock(booking.pricing.lockId),
      void_authorization: () => voidAllPayments(booking.id),
      rollback_changes: () => rollbackBookingChanges(booking.id),
      cancel_suppliers: () => cancelAllSupplierBookings(booking.id),
    };

    const handler = compensations[action];
    if (handler) {
      await handler();
    }
  }
}

interface RecoveryResult {
  success: boolean;
  booking?: Booking;
  reason?: string;
}

interface IncompleteOperation {
  type: string;
  id: string;
  age: number;
  action: string;
}
```

---

## State Queries

### Query Interface

```typescript
// ============================================================================
// STATE QUERIES
// ============================================================================

class StateQueryService {
  async getBookingsInState(state: BookingState): Promise<Booking[]> {
    return await Booking.find({ state });
  }

  async getBookingsInStates(states: BookingState[]): Promise<Booking[]> {
    return await Booking.find({ state: { $in: states } });
  }

  async getStaleBookings(): Promise<Booking[]> {
    const now = Date.now();
    const staleBookings: Booking[] = [];

    const transientStates = Object.values(STATE_CONFIGS)
      .filter(c => c.category === 'transient')
      .map(c => c.state);

    const bookings = await Booking.find({
      state: { $in: transientStates },
    });

    for (const booking of bookings) {
      const config = STATE_CONFIGS[booking.state];
      const timeInState = now - booking.updatedAt.getTime();

      if (timeInState > (config.timeout || 300000)) {
        staleBookings.push(booking);
      }
    }

    return staleBookings;
  }

  async getStateHistory(bookingId: string): Promise<StateHistoryEntry[]> {
    return await StateHistory.find({ bookingId }).sort({ at: 1 });
  }

  async getTimeInState(bookingId: string, state: BookingState): Promise<number> {
    const history = await StateHistory.find({
      bookingId,
      to: state,
    }).sort({ at: -1 });

    if (history.length === 0) {
      return 0;
    }

    const entry = history[0];
    const nextEntry = await StateHistory.findOne({
      bookingId,
      at: { $gt: entry.at },
    }).sort({ at: 1 });

    const end = nextEntry ? nextEntry.at : new Date();
    return end.getTime() - entry.at.getTime();
  }

  async getStateTransitions(
    bookingId: string,
    from?: Date,
    to?: Date
  ): Promise<StateHistoryEntry[]> {
    const query: any = { bookingId };

    if (from || to) {
      query.at = {};
      if (from) query.at.$gte = from;
      if (to) query.at.$lte = to;
    }

    return await StateHistory.find(query).sort({ at: 1 });
  }
}
```

---

## Observability

### Monitoring & Metrics

```typescript
// ============================================================================
// OBSERVABILITY
// ============================================================================

class StateMachineMetrics {
  private metrics: MetricsClient;

  constructor() {
    this.metrics = new MetricsClient();
  }

  recordTransition(booking: Booking, transition: TransitionResult): void {
    const labels = {
      from: transition.previousState,
      to: transition.newState,
      success: transition.success.toString(),
    };

    this.metrics.increment('booking.state_transition', labels);

    if (transition.success) {
      this.metrics.timing('booking.state_transition_duration', Date.now(), labels);
    } else {
      this.metrics.increment('booking.state_transition_error', labels);
    }
  }

  recordStateEntry(state: BookingState, count: number): void {
    this.metrics.gauge('booking.state_entries', count, { state });
  }

  recordStateDuration(state: BookingState, duration: number): void {
    this.metrics.timing('booking.state_duration', duration, { state });
  }

  async getMetrics(): Promise<StateMachineMetricsReport> {
    return {
      totalBookings: await Booking.countDocuments(),
      bookingsByState: await this.getCountByState(),
      bookingsByStatus: await this.getCountByStatus(),
      staleBookings: (await new StateQueryService().getStaleBookings()).length,
      averageStateDuration: await this.getAverageDurations(),
      transitionRate: await this.getTransitionRate(),
    };
  }

  private async getCountByState(): Promise<Record<string, number>> {
    const pipeline = [
      { $group: { _id: '$state', count: { $sum: 1 } } },
    ];

    const results = await Booking.aggregate(pipeline);
    return Object.fromEntries(results.map(r => [r._id, r.count]));
  }

  private async getCountByStatus(): Promise<Record<string, number>> {
    const pipeline = [
      { $group: { _id: '$status', count: { $sum: 1 } } },
    ];

    const results = await Booking.aggregate(pipeline);
    return Object.fromEntries(results.map(r => [r._id, r.count]));
  }

  private async getAverageDurations(): Promise<Record<string, number>> {
    // Calculate average time in each state
    const history = await StateHistory.aggregate([
      {
        $group: {
          _id: '$to',
          avgDuration: { $avg: '$duration' },
        },
      },
    ]);

    return Object.fromEntries(
      history.map(h => [h._id, h.avgDuration])
    );
  }

  private async getTransitionRate(): Promise<Record<string, number>> {
    // Transitions per hour in the last 24 hours
    const since = new Date(Date.now() - 86400000);

    const results = await StateHistory.aggregate([
      { $match: { at: { $gte: since } } },
      {
        $group: {
          _id: {
            from: '$from',
            to: '$to',
          },
          count: { $sum: 1 },
        },
      },
    ]);

    return Object.fromEntries(
      results.map(r => [`${r._id.from}->${r._id.to}`, r.count / 24])
    );
  }
}

interface StateMachineMetricsReport {
  totalBookings: number;
  bookingsByState: Record<string, number>;
  bookingsByStatus: Record<string, number>;
  staleBookings: number;
  averageStateDuration: Record<string, number>;
  transitionRate: Record<string, number>;
}
```

---

**Series Complete:** The Booking Engine series (8 documents) is now complete.

**Related Documentation:**
- [Payment Processing](../PAYMENT_PROCESSING_MASTER_INDEX.md) — Payment integration
- [Supplier Integration](../SUPPLIER_INTEGRATION_MASTER_INDEX.md) — External booking APIs
- [Notifications](../COMMUNICATION_HUB_MASTER_INDEX.md) — Notification delivery
