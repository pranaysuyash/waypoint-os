# Booking Engine — Reservation Flow

> Detailed booking creation, validation, and processing flows

**Series:** Booking Engine | **Document:** 2 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Booking Creation Flow](#booking-creation-flow)
3. [Request Validation](#request-validation)
4. [Price Locking](#price-locking)
5. [Inventory Reservation](#inventory-reservation)
6. [Payment Processing](#payment-processing)
7. [Supplier Confirmation](#supplier-confirmation)
8. [Booking Finalization](#booking-finalization)
9. [Error Recovery](#error-recovery)

---

## Overview

The reservation flow orchestrates the creation of a new booking from initial request through confirmation. It's a multi-step process that must handle failures gracefully while maintaining data consistency.

### Flow Summary

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   REQUEST   │────▶│ VALIDATION  │────▶│ PRICE LOCK  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CONFIRMED │◀────│  SUPPLIER   │◀────│   PAYMENT   │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ NOTIFICATION│
                   └─────────────┘
```

### Key Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| **Exactly Once** | Idempotency keys |
| **No Double-Booking** | Distributed locks |
| **Price Consistency** | Price locks with TTL |
| **Atomic Operations** | Saga compensation |
| **Audit Trail** | Event sourcing |

---

## Booking Creation Flow

### High-Level Sequence

```typescript
// ============================================================================
// MAIN BOOKING CREATION ORCHESTRATOR
// ============================================================================

interface CreateBookingRequest {
  idempotencyKey: string;

  // Customer
  customerId?: string;
  customerInfo: CustomerInfo;

  // Items
  items: BookingItemRequest[];

  // Payment
  paymentMethod: PaymentMethod;

  // Metadata
  metadata?: {
    source?: string;
    channel?: string;
    campaign?: string;
  };
}

interface BookingItemRequest {
  type: ProductType;
  productId: string;
  quantity: number;
  dates: DateRange;
  travelers: Traveler[];
  options?: Record<string, unknown>;
}

interface CreateBookingResponse {
  booking: Booking;
  requiresAction?: {
    type: 'payment' | 'verification' | 'approval';
    data: Record<string, unknown>;
  };
}

async function createBookingFlow(
  request: CreateBookingRequest
): Promise<CreateBookingResponse> {
  // Step 0: Check idempotency
  const existing = await checkIdempotency(request.idempotencyKey);
  if (existing) {
    return { booking: existing };
  }

  // Start distributed trace
  const tracer = trace.getTracer('booking-engine');
  return await tracer.startActiveSpan('createBookingFlow', async (span) => {
    const saga = new BookingSaga('create-booking');
    let booking: Booking;

    try {
      // Step 1: Create draft booking
      booking = await saga.addStep(
        () => createDraftBooking(request),
        (b) => deleteDraftBooking(b.id)
      );

      span.setAttribute('booking.id', booking.id);
      span.setAttribute('booking.item_count', request.items.length);

      // Step 2: Validate booking request
      await validateBookingRequest(booking, request);

      // Step 3: Enrich with product details
      booking = await enrichBookingItems(booking);

      // Step 4: Lock pricing
      await saga.addStep(
        () => lockBookingPricing(booking),
        (lock) => releasePricingLock(lock.id)
      );

      // Step 5: Reserve inventory
      await saga.addStep(
        () => reserveInventory(booking),
        (holds) => releaseInventoryHolds(holds)
      );

      // Step 6: Process payment
      const paymentResult = await saga.addStep(
        () => processPayment(booking, request.paymentMethod),
        (payment) => voidPaymentIfCaptured(payment.id)
      );

      // Step 7: Confirm with suppliers
      await saga.addStep(
        () => confirmWithSuppliers(booking),
        (confirmations) => cancelSupplierBookings(confirmations)
      );

      // Step 8: Finalize booking
      booking = await finalizeBooking(booking, paymentResult);

      // Store idempotency record
      await storeIdempotency(request.idempotencyKey, booking.id);

      span.setStatus({ code: SpanStatusCode.OK });

      return { booking };

    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });

      // Compensate completed steps
      await saga.compensate();

      throw mapBookingError(error);
    } finally {
      span.end();
    }
  });
}
```

---

## Request Validation

### Validation Pipeline

```typescript
// ============================================================================
// VALIDATION PIPELINE
// ============================================================================

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

interface ValidationError {
  field: string;
  code: string;
  message: string;
  severity: 'error' | 'warning';
}

const VALIDATION_RULES = {
  // Customer validation
  customer: [
    {
      field: 'customerInfo.primary.email',
      check: (email: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),
      code: 'INVALID_EMAIL',
      message: 'Email address is invalid',
    },
    {
      field: 'customerInfo.primary.phone',
      check: (phone: string) => /^\+?[\d\s\-()]+$/.test(phone),
      code: 'INVALID_PHONE',
      message: 'Phone number is invalid',
    },
  ],

  // Date validation
  dates: [
    {
      field: 'items.*.dates',
      check: (dates: DateRange) => {
        const now = new Date();
        const minStart = addDays(now, 1); // At least tomorrow
        const maxEnd = addYears(now, 2);   // Within 2 years
        return dates.start >= minStart && dates.end <= maxEnd;
      },
      code: 'DATES_OUT_OF_RANGE',
      message: 'Travel dates must be within 1 day to 2 years from now',
    },
    {
      field: 'items.*.dates',
      check: (dates: DateRange) => dates.end > dates.start,
      code: 'END_BEFORE_START',
      message: 'End date must be after start date',
    },
  ],

  // Traveler validation
  travelers: [
    {
      field: 'items.*.travelers',
      check: (travelers: Traveler[], item: BookingItemRequest) => {
        return travelers.length === item.quantity;
      },
      code: 'TRAVELER_MISMATCH',
      message: 'Number of travelers must match quantity',
    },
    {
      field: 'items.*.travelers.*.dateOfBirth',
      check: (dob: Date) => {
        const age = differenceInYears(new Date(), dob);
        return age >= 0 && age < 150;
      },
      code: 'INVALID_DOB',
      message: 'Invalid date of birth',
    },
  ],

  // Item-specific validation
  accommodation: [
    {
      field: 'items.accommodation',
      check: (item: BookingItemRequest) => {
        return item.quantity >= 1 && item.quantity <= 30;
      },
      code: 'INVALID_QUANTITY',
      message: 'Accommodation quantity must be between 1 and 30 rooms',
    },
  ],

  flight: [
    {
      field: 'items.flight',
      check: (item: BookingItemRequest) => {
        const infantCount = item.travelers.filter(t => t.type === 'infant').length;
        const adultCount = item.travelers.filter(t => t.type === 'adult').length;
        return infantCount <= adultCount;
      },
      code: 'TOO_MANY_INFANTS',
      message: 'Each infant must be accompanied by an adult',
    },
  ],
};

async function validateBookingRequest(
  booking: Booking,
  request: CreateBookingRequest
): Promise<ValidationResult> {
  const errors: ValidationError[] = [];
  const warnings: ValidationWarning[] = [];

  // 1. Schema validation
  const schemaErrors = validateSchema(request);
  errors.push(...schemaErrors);

  // 2. Business rule validation
  const businessErrors = await validateBusinessRules(booking, request);
  errors.push(...businessErrors);

  // 3. Cross-item validation
  const crossItemErrors = validateCrossItems(request);
  errors.push(...crossItemErrors);

  // 4. Policy validation
  const policyWarnings = await validatePolicies(request);
  warnings.push(...policyWarnings);

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

async function validateBusinessRules(
  booking: Booking,
  request: CreateBookingRequest
): Promise<ValidationError[]> {
  const errors: ValidationError[] = [];

  // Check for duplicate bookings
  const duplicate = await findDuplicateBooking(request);
  if (duplicate) {
    errors.push({
      field: 'booking',
      code: 'DUPLICATE_BOOKING',
      message: `Similar booking already exists: ${duplicate.reference}`,
      severity: 'error',
    });
  }

  // Check customer restrictions
  const restrictions = await checkCustomerRestrictions(request.customerInfo);
  if (restrictions.blocked) {
    errors.push({
      field: 'customer',
      code: 'CUSTOMER_BLOCKED',
      message: restrictions.reason || 'Customer is blocked from booking',
      severity: 'error',
    });
  }

  // Validate item availability (pre-check)
  for (const item of request.items) {
    const available = await checkAvailability(item);
    if (!available.available) {
      errors.push({
        field: `items[${item.type}]`,
        code: 'NOT_AVAILABLE',
        message: available.reason || 'Item is not available',
        severity: 'error',
      });
    }
  }

  return errors;
}

function validateCrossItems(request: CreateBookingRequest): ValidationError[] {
  const errors: ValidationError[] = [];

  // Check for overlapping dates
  const itemsByDate = groupBy(request.items, i => i.dates.start.toISOString());
  for (const [date, items] of Object.entries(itemsByDate)) {
    if (items.length > 1) {
      // Check for conflicts (e.g., two flights at same time)
      const flights = items.filter(i => i.type === 'flight');
      if (flights.length > 1) {
        errors.push({
          field: 'items',
          code: 'CONFLICTING_FLIGHTS',
          message: 'Cannot book multiple flights for the same departure',
          severity: 'error',
        });
      }
    }
  }

  // Check traveler consistency across items
  const allTravelers = new Map<string, Traveler[]>();
  for (const item of request.items) {
    const key = item.travelers.map(t => `${t.firstName}-${t.lastName}`).sort().join(',');
    if (!allTravelers.has(key)) {
      allTravelers.set(key, []);
    }
    allTravelers.get(key)!.push(...item.travelers);
  }

  return errors;
}

async function validatePolicies(
  request: CreateBookingRequest
): Promise<ValidationWarning[]> {
  const warnings: ValidationWarning[] = [];

  // Check cancellation policy
  for (const item of request.items) {
    const policy = await getCancellationPolicy(item);
    if (!policy.refundable) {
      warnings.push({
        field: `items[${item.type}].cancellation`,
        code: 'NON_REFUNDABLE',
        message: 'This booking is non-refundable',
      });
    }
  }

  // Check payment deadlines
  const paymentDeadline = await getPaymentDeadline(request);
  if (paymentDeadline.hours < 24) {
    warnings.push({
      field: 'payment',
      code: 'URGENT_PAYMENT',
      message: `Payment must be completed within ${paymentDeadline.hours} hours`,
    });
  }

  return warnings;
}
```

---

## Price Locking

### Price Lock Implementation

```typescript
// ============================================================================
// PRICE LOCKING
// ============================================================================

interface PriceLock {
  id: string;
  bookingId: string;
  items: PriceLockedItem[];
  total: {
    subtotal: number;
    taxes: number;
    fees: number;
    total: number;
    currency: string;
  };
  expiresAt: Date;
  createdAt: Date;
}

interface PriceLockedItem {
  itemId: string;
  productId: string;
  price: ItemPricing;
  priceHash: string; // For change detection
}

async function lockBookingPricing(booking: Booking): Promise<PriceLock> {
  // Calculate pricing for all items
  const pricedItems = await Promise.all(
    booking.items.map(async (item) => {
      const price = await calculateItemPrice(item);
      return {
        itemId: item.id,
        productId: item.productId,
        price,
        priceHash: hashPrice(price),
      };
    })
  );

  // Calculate totals
  const totals = calculateTotals(pricedItems);

  // Create price lock with TTL
  const lock: PriceLock = {
    id: crypto.randomUUID(),
    bookingId: booking.id,
    items: pricedItems,
    total: totals,
    expiresAt: addMinutes(new Date(), 30), // 30-minute lock
    createdAt: new Date(),
  };

  // Store in Redis with expiration
  await redis.setex(
    `price-lock:${lock.id}`,
    1800, // 30 minutes
    JSON.stringify(lock)
  );

  // Update booking
  booking.pricing = {
    ...totals,
    lockedAt: new Date(),
    lockId: lock.id,
  };

  await booking.save();

  // Record event
  await recordEvent(booking.id, {
    type: 'price.locked',
    data: {
      lockId: lock.id,
      total: totals.total,
      expiresAt: lock.expiresAt,
    },
  });

  return lock;
}

async function verifyPriceLock(
  booking: Booking
): Promise<boolean> {
  if (!booking.pricing.lockId) {
    return false;
  }

  const lockData = await redis.get(`price-lock:${booking.pricing.lockId}`);
  if (!lockData) {
    return false; // Lock expired
  }

  const lock: PriceLock = JSON.parse(lockData);

  // Verify prices haven't changed
  for (const lockedItem of lock.items) {
    const currentItem = booking.items.find(i => i.id === lockedItem.itemId);
    if (!currentItem) {
      return false;
    }

    const currentPrice = await calculateItemPrice(currentItem);
    const currentHash = hashPrice(currentPrice);

    if (currentHash !== lockedItem.priceHash) {
      // Price has changed - need customer approval
      await notifyPriceChange(booking, lockedItem, currentPrice);
      return false;
    }
  }

  return true;
}

async function releasePricingLock(lockId: string): Promise<void> {
  await redis.del(`price-lock:${lockId}`);
}

function hashPrice(price: ItemPricing): string {
  const data = JSON.stringify({
    baseRate: price.baseRate,
    taxes: price.taxes,
    fees: price.fees,
    discount: price.discount,
  });
  return createHash('sha256').update(data).digest('hex');
}

async function calculateItemPrice(item: BookingItem): Promise<ItemPricing> {
  // Get base price from catalog
  const catalogPrice = await PricingService.getCatalogPrice(
    item.productId,
    item.dates
  );

  // Apply dynamic pricing rules
  const dynamicPrice = await PricingService.applyDynamicPricing(
    catalogPrice,
    item
  );

  // Calculate taxes
  const taxes = await TaxService.calculateTaxes(dynamicPrice, item);

  // Calculate fees
  const fees = await FeeService.calculateFees(dynamicPrice, item);

  // Apply discounts if applicable
  const discount = await DiscountService.applyDiscounts(
    dynamicPrice,
    item
  );

  return {
    baseRate: dynamicPrice.baseRate,
    taxes: taxes.total,
    fees: fees.total,
    discount: discount.amount,
    total: dynamicPrice.baseRate + taxes.total + fees.total - discount.amount,
    currency: dynamicPrice.currency,
    breakdown: {
      baseRate: dynamicPrice.baseRate,
      taxes: taxes.breakdown,
      fees: fees.breakdown,
      discount: discount.breakdown,
    },
  };
}
```

---

## Inventory Reservation

### Hold Management

```typescript
// ============================================================================
// INVENTORY HOLDS
// ============================================================================

interface HoldRequest {
  bookingId: string;
  itemId: string;
  supplierId: string;
  productId: string;
  quantity: number;
  dates: DateRange;
}

interface HoldConfirmation {
  holdId: string;
  supplierHoldId?: string;
  expiresAt: Date;
  status: 'pending' | 'confirmed' | 'failed';
}

async function reserveInventory(booking: Booking): Promise<HoldConfirmation[]> {
  const confirmations: HoldConfirmation[] = [];

  for (const item of booking.items) {
    // Acquire distributed lock for this inventory
    const lockKey = `inventory:${item.supplierId}:${item.productId}:${item.dates.start}`;
    const lock = await distributedLock.acquire(lockKey, 10000); // 10s timeout

    if (!lock) {
      throw new Error(`Could not acquire lock for ${item.productId}`);
    }

    try {
      // Check current availability
      const available = await InventoryService.checkAvailability({
        supplierId: item.supplierId,
        productId: item.productId,
        dates: item.dates,
        quantity: 1, // Per item
      });

      if (!available.available) {
        throw new InventoryUnavailableError(item.productId, available.reason);
      }

      // Create hold with supplier
      const hold = await createSupplierHold(item);

      // Create local hold record
      const localHold = await InventoryHold.create({
        bookingId: booking.id,
        itemId: item.id,
        type: 'temp',
        quantity: 1,
        expiresAt: addMinutes(new Date(), 15),
        supplierId: item.supplierId,
        inventoryId: item.productId,
        supplierHoldId: hold.supplierHoldId,
        status: 'active',
      });

      confirmations.push({
        holdId: localHold.id,
        supplierHoldId: hold.supplierHoldId,
        expiresAt: localHold.expiresAt,
        status: hold.status,
      });

    } finally {
      await lock.release();
    }
  }

  // Update booking hold count
  booking.holdCount = confirmations.length;
  booking.holdExpiresAt = min(confirmations.map(c => c.expiresAt));
  await booking.save();

  return confirmations;
}

async function createSupplierHold(
  item: BookingItem
): Promise<{ supplierHoldId?: string; status: HoldConfirmation['status'] }> {
  const supplier = await SupplierService.get(item.supplierId);

  // Some suppliers don't support holds - confirm immediately
  if (!supplier.features.holds) {
    return { status: 'confirmed' };
  }

  try {
    const result = await SupplierService.createHold({
      supplierId: item.supplierId,
      productId: item.productId,
      dates: item.dates,
      quantity: 1,
      expiresAt: addMinutes(new Date(), 15),
    });

    return {
      supplierHoldId: result.holdId,
      status: 'pending',
    };
  } catch (error) {
    if (error.code === 'HOLDS_NOT_SUPPORTED') {
      return { status: 'confirmed' };
    }
    throw error;
  }
}

async function releaseInventoryHolds(holds: HoldConfirmation[]): Promise<void> {
  await Promise.all(
    holds.map(async (hold) => {
      // Update local hold
      await InventoryHold.update(hold.holdId, {
        status: 'released',
        releasedAt: new Date(),
      });

      // Release supplier hold if exists
      if (hold.supplierHoldId) {
        try {
          await SupplierService.releaseHold(hold.supplierHoldId);
        } catch (error) {
          // Log but don't fail - hold will expire naturally
          logger.error('Failed to release supplier hold', { hold, error });
        }
      }
    })
  );
}

// Hold expiration cleanup (background job)
async function expireHolds(): Promise<void> {
  const expiredHolds = await InventoryHold.find({
    status: 'active',
    expiresAt: { $lt: new Date() },
  });

  for (const hold of expiredHolds) {
    await releaseInventoryHolds([{
      holdId: hold.id,
      supplierHoldId: hold.supplierHoldId,
      expiresAt: hold.expiresAt,
      status: 'active',
    }]);

    // Cancel booking if all holds expired
    const booking = await Booking.findById(hold.bookingId);
    if (booking && booking.status === 'pending') {
      const activeHolds = await InventoryHold.find({
        bookingId: booking.id,
        status: 'active',
      });

      if (activeHolds.length === 0) {
        await expireBooking(booking);
      }
    }
  }
}
```

---

## Payment Processing

### Payment Flow

```typescript
// ============================================================================
// PAYMENT PROCESSING
// ============================================================================

interface PaymentResult {
  paymentId: string;
  status: 'authorized' | 'captured' | 'failed';
  authorizationCode?: string;
  declineCode?: string;
  requiresAction?: {
    type: '3ds' | 'redirect' | 'verification';
    data: Record<string, unknown>;
  };
}

async function processPayment(
  booking: Booking,
  paymentMethod: PaymentMethod
): Promise<PaymentResult> {
  // Verify price lock is still valid
  const lockValid = await verifyPriceLock(booking);
  if (!lockValid) {
    throw new PriceExpiredError('Prices have changed. Please review and confirm.');
  }

  // Calculate final amount
  const amount = booking.pricing.total;

  // Create payment intent
  const paymentIntent = await PaymentService.createIntent({
    bookingId: booking.id,
    amount,
    currency: booking.pricing.currency,
    paymentMethod,
    customer: booking.customerInfo,
    metadata: {
      bookingReference: booking.reference,
      itemCount: booking.items.length,
    },
  });

  // Handle payment based on method
  switch (paymentMethod.type) {
    case 'card':
      return await processCardPayment(booking, paymentIntent);

    case 'paypal':
      return await processPayPalPayment(booking, paymentIntent);

    case 'bank_transfer':
      return await processBankTransfer(booking, paymentIntent);

    case 'installments':
      return await processInstallmentPayment(booking, paymentIntent);

    default:
      throw new UnsupportedPaymentMethodError(paymentMethod.type);
  }
}

async function processCardPayment(
  booking: Booking,
  intent: PaymentIntent
): Promise<PaymentResult> {
  // Authorize the payment (don't capture yet)
  const authorization = await PaymentService.authorize({
    paymentMethodId: intent.paymentMethod.id,
    amount: intent.amount,
    currency: intent.currency,
    bookingId: booking.id,
  });

  if (authorization.status === 'requires_action') {
    // 3D Secure or other verification required
    return {
      paymentId: authorization.paymentId,
      status: 'authorized',
      requiresAction: {
        type: authorization.nextAction.type,
        data: authorization.nextAction.data,
      },
    };
  }

  if (authorization.status === 'failed') {
    throw new PaymentDeclinedError(
      authorization.declineCode || 'DECLINED',
      authorization.message
    );
  }

  // Record successful authorization
  await BookingPayment.create({
    bookingId: booking.id,
    paymentId: authorization.paymentId,
    amount: intent.amount,
    currency: intent.currency,
    status: 'authorized',
    authorizationCode: authorization.code,
  });

  return {
    paymentId: authorization.paymentId,
    status: 'authorized',
    authorizationCode: authorization.code,
  };
}

async function capturePayment(bookingId: string): Promise<void> {
  const booking = await Booking.findById(bookingId);
  const payments = await BookingPayment.find({
    bookingId,
    status: 'authorized',
  });

  for (const payment of payments) {
    const capture = await PaymentService.capture(payment.paymentId);

    if (capture.status === 'succeeded') {
      payment.status = 'captured';
      payment.capturedAt = new Date();
      await payment.save();
    } else {
      throw new PaymentCaptureError(payment.paymentId, capture.error);
    }
  }

  booking.paymentStatus = 'paid';
  await booking.save();
}

async function voidPaymentIfCaptured(paymentId: string): Promise<void> {
  const payment = await BookingPayment.findOne({ paymentId });

  if (!payment) {
    return;
  }

  if (payment.status === 'captured') {
    // Already captured - need to refund
    await PaymentService.refund(paymentId, payment.amount);
    payment.status = 'refunded';
  } else if (payment.status === 'authorized') {
    // Not yet captured - void the authorization
    await PaymentService.void(paymentId);
    payment.status = 'voided';
  }

  await payment.save();
}
```

---

## Supplier Confirmation

### Supplier Booking Flow

```typescript
// ============================================================================
// SUPPLIER CONFIRMATION
// ============================================================================

interface SupplierBookingResult {
  itemId: string;
  supplierReference: string;
  status: 'confirmed' | 'pending' | 'failed';
  confirmation?: SupplierConfirmationDetails;
  error?: string;
}

async function confirmWithSuppliers(
  booking: Booking
): Promise<SupplierBookingResult[]> {
  const results: SupplierBookingResult[] = [];

  // Confirm items in dependency order
  // (e.g., flights before accommodations, primary before transfers)
  const orderedItems = orderItemsByDependency(booking.items);

  for (const item of orderedItems) {
    try {
      const result = await confirmSupplierItem(booking, item);
      results.push(result);

      // Update item status
      item.status = result.status;
      item.supplierReference = result.supplierReference;
      if (result.status === 'confirmed') {
        item.confirmationCode = result.confirmation?.code;
        item.confirmedAt = new Date();
      }
      await item.save();

    } catch (error) {
      results.push({
        itemId: item.id,
        supplierReference: '',
        status: 'failed',
        error: error.message,
      });

      // Don't fail entire booking - log for manual handling
      logger.error('Supplier confirmation failed', {
        bookingId: booking.id,
        itemId: item.id,
        error,
      });
    }
  }

  // Update booking status based on results
  const allConfirmed = results.every(r => r.status === 'confirmed');
  const someConfirmed = results.some(r => r.status === 'confirmed');

  if (allConfirmed) {
    booking.status = 'confirmed';
  } else if (someConfirmed) {
    booking.status = 'partial';
  } else {
    booking.status = 'failed';
  }

  await booking.save();

  return results;
}

async function confirmSupplierItem(
  booking: Booking,
  item: BookingItem
): Promise<SupplierBookingResult> {
  const supplier = await SupplierService.get(item.supplierId);

  // Build booking request for supplier
  const supplierRequest = buildSupplierBookingRequest(booking, item);

  // Call supplier API
  const response = await SupplierService.createBooking({
    supplierId: item.supplierId,
    request: supplierRequest,
  });

  if (response.success) {
    return {
      itemId: item.id,
      supplierReference: response.reference,
      status: 'confirmed',
      confirmation: {
        code: response.confirmationCode,
        url: response.confirmationUrl,
        documents: response.documents,
      },
    };
  }

  // Handle pending confirmations (some suppliers take time)
  if (response.pending) {
    return {
      itemId: item.id,
      supplierReference: response.reference,
      status: 'pending',
    };
  }

  throw new Error(`Supplier booking failed: ${response.error}`);
}

function buildSupplierBookingRequest(
  booking: Booking,
  item: BookingItem
): Record<string, unknown> {
  const baseRequest = {
    reference: booking.reference,
    customer: {
      name: `${booking.customerInfo.primary.firstName} ${booking.customerInfo.primary.lastName}`,
      email: booking.customerInfo.primary.email,
      phone: booking.customerInfo.primary.phone,
    },
    dates: {
      start: item.dates.start.toISOString(),
      end: item.dates.end.toISOString(),
    },
    travelers: booking.customerInfo.travelers,
    pricing: {
      total: item.pricing.total,
      currency: item.pricing.currency,
    },
  };

  // Add type-specific details
  switch (item.type) {
    case 'accommodation':
      return {
        ...baseRequest,
        rooms: item.accommodation?.rooms,
        mealPlan: item.accommodation?.mealPlan,
        specialRequests: item.accommodation?.specialRequests,
      };

    case 'flight':
      return {
        ...baseRequest,
        flights: item.flight?.segments,
        cabinClass: item.flight?.cabinClass,
        baggage: item.flight?.baggage,
      };

    case 'activity':
      return {
        ...baseRequest,
        activity: item.activity?.name,
        timeslot: item.activity?.timeslot,
        notes: item.activity?.notes,
      };

    default:
      return baseRequest;
  }
}

function orderItemsByDependency(items: BookingItem[]): BookingItem[] {
  const ordered: BookingItem[] = [];
  const seen = new Set<string>();

  function addItem(item: BookingItem) {
    if (seen.has(item.id)) return;

    // Add dependencies first
    if (item.type === 'transfer') {
      // Transfers depend on flights
      const flights = items.filter(i => i.type === 'flight');
      flights.forEach(addItem);
    }

    seen.add(item.id);
    ordered.push(item);
  }

  items.forEach(addItem);
  return ordered;
}

// Check pending confirmations (background job)
async function checkPendingConfirmations(): Promise<void> {
  const pendingItems = await BookingItem.find({
    status: 'pending',
  });

  for (const item of pendingItems) {
    try {
      const status = await SupplierService.getBookingStatus({
        supplierId: item.supplierId,
        reference: item.supplierReference,
      });

      if (status.confirmed) {
        item.status = 'confirmed';
        item.confirmationCode = status.confirmationCode;
        item.confirmedAt = new Date();
        await item.save();

        // Send confirmation notification
        await NotificationService.sendItemConfirmed(item);
      } else if (status.failed) {
        item.status = 'failed';
        await item.save();

        // Notify for manual intervention
        await NotificationService.sendItemFailed(item);
      }
    } catch (error) {
      logger.error('Failed to check pending confirmation', { itemId: item.id, error });
    }
  }
}
```

---

## Booking Finalization

### Finalization Steps

```typescript
// ============================================================================
// BOOKING FINALIZATION
// ============================================================================

interface FinalizationResult {
  booking: Booking;
  documents: Document[];
  notifications: Notification[];
}

async function finalizeBooking(
  booking: Booking,
  paymentResult: PaymentResult
): Promise<Booking> {
  // Capture payment
  if (paymentResult.status === 'authorized') {
    await capturePayment(booking.id);
  }

  // Convert holds to confirmed
  await convertHolds(booking);

  // Generate booking reference if not exists
  if (!booking.reference) {
    booking.reference = await generateBookingReference();
  }

  // Update final status
  booking.status = 'confirmed';
  booking.state = 'confirmed';
  booking.confirmedAt = new Date();
  booking.version += 1;

  await booking.save();

  // Record confirmation event
  await recordEvent(booking.id, {
    type: 'booking.confirmed',
    data: {
      reference: booking.reference,
      confirmedAt: booking.confirmedAt,
      total: booking.pricing.total,
    },
  });

  // Generate documents
  await generateBookingDocuments(booking);

  // Send notifications
  await sendConfirmationNotifications(booking);

  // Update analytics
  await Analytics.track('booking.confirmed', {
    bookingId: booking.id,
    reference: booking.reference,
    total: booking.pricing.total,
    itemCount: booking.items.length,
  });

  return booking;
}

async function convertHolds(booking: Booking): Promise<void> {
  const holds = await InventoryHold.find({
    bookingId: booking.id,
    status: 'active',
  });

  for (const hold of holds) {
    hold.type = 'confirmed';
    hold.status = 'confirmed';
    hold.confirmedAt = new Date();
    hold.expiresAt = null; // Confirmed holds don't expire
    await hold.save();
  }
}

async function generateBookingReference(): Promise<string> {
  // Format: TRV-YYYY-XXXX
  const year = new Date().getFullYear();
  const sequence = await Redis.getCounter(`booking-ref:${year}`);
  const code = base32Encode(sequence).padStart(4, '0').toUpperCase();
  return `TRV-${year}-${code}`;
}

async function generateBookingDocuments(booking: Booking): Promise<Document[]> {
  const documents: Document[] = [];

  // Generate itinerary/voucher
  const voucher = await DocumentService.generateVoucher(booking);
  documents.push(voucher);

  // Generate item-specific documents
  for (const item of booking.items) {
    if (item.type === 'flight') {
      const eticket = await DocumentService.generateETicket(booking, item);
      documents.push(eturket);
    } else if (item.type === 'accommodation') {
      const voucher = await DocumentService.generateHotelVoucher(booking, item);
      documents.push(voucher);
    }
  }

  // Store documents
  for (const doc of documents) {
    await BookingDocument.create({
      bookingId: booking.id,
      type: doc.type,
      url: doc.url,
      filename: doc.filename,
      generatedAt: new Date(),
    });
  }

  return documents;
}

async function sendConfirmationNotifications(booking: Booking): Promise<void> {
  const documents = await BookingDocument.find({ bookingId: booking.id });

  // Email confirmation
  await NotificationService.sendBookingConfirmation({
    to: booking.customerInfo.primary.email,
    booking,
    documents: documents.map(d => d.url),
  });

  // SMS confirmation (if opted in)
  if (booking.customerInfo.primary.phone && booking.metadata.notifications?.sms) {
    await NotificationService.sendSMS({
      to: booking.customerInfo.primary.phone,
      template: 'booking-confirmed',
      data: {
        reference: booking.reference,
        total: booking.pricing.total,
      },
    });
  }

  // Push notification (if mobile app)
  if (booking.metadata.deviceTokens) {
    await NotificationService.sendPush({
      tokens: booking.metadata.deviceTokens,
      title: 'Booking Confirmed',
      body: `Your trip ${booking.reference} has been confirmed!`,
      data: { bookingId: booking.id },
    });
  }

  // Notify agent if booked through agent
  if (booking.metadata.source === 'agent') {
    await NotificationService.notifyAgent({
      agentId: booking.metadata.agentId,
      type: 'booking-confirmed',
      booking,
    });
  }
}
```

---

## Error Recovery

### Error Handling Strategy

```typescript
// ============================================================================
// ERROR RECOVERY
// ============================================================================

class BookingSaga {
  private steps: SagaStep[] = [];
  private completedSteps: SagaStep[] = [];

  constructor(private name: string) {}

  async addStep<T>(
    execute: () => Promise<T>,
    compensate: (result: T) => Promise<void>
  ): Promise<T> {
    const step: SagaStep = {
      execute,
      compensate,
      result: null,
    };

    try {
      step.result = await execute();
      this.completedSteps.push(step);
      return step.result;
    } catch (error) {
      // Step failed - compensate previous steps
      await this.compensate();
      throw error;
    }
  }

  async compensate(): Promise<void> {
    // Compensate in reverse order
    for (let i = this.completedSteps.length - 1; i >= 0; i--) {
      const step = this.completedSteps[i];
      if (step.result) {
        try {
          await step.compensate(step.result);
        } catch (error) {
          logger.error(`Compensation failed for ${this.name} step ${i}`, { error });
        }
      }
    }
    this.completedSteps = [];
  }
}

interface SagaStep<T = unknown> {
  execute: () => Promise<T>;
  compensate: (result: T) => Promise<void>;
  result: T | null;
}

// Error mapping
function mapBookingError(error: unknown): BookingError {
  if (error instanceof ValidationError) {
    return new BookingValidationError(error.message, error.errors);
  }

  if (error instanceof InventoryUnavailableError) {
    return new BookingAvailabilityError(error.productId, error.reason);
  }

  if (error instanceof PaymentDeclinedError) {
    return new BookingPaymentError(error.code, error.message);
  }

  if (error instanceof PriceExpiredError) {
    return new BookingPriceExpiredError(error.message);
  }

  // Default to generic error
  return new BookingError('BOOKING_FAILED', error.message);
}

// Retry logic for transient failures
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: {
    maxAttempts: number;
    initialDelay: number;
    maxDelay: number;
  }
): Promise<T> {
  let lastError: Error;

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry non-transient errors
      if (!isTransientError(error)) {
        throw error;
      }

      if (attempt < config.maxAttempts) {
        const delay = Math.min(
          config.initialDelay * Math.pow(2, attempt - 1),
          config.maxDelay
        );
        await sleep(delay);
      }
    }
  }

  throw lastError;
}

function isTransientError(error: Error): boolean {
  const transientCodes = [
    'ECONNRESET',
    'ETIMEDOUT',
    'ECONNREFUSED',
    'SERVICE_UNAVAILABLE',
    'GATEWAY_TIMEOUT',
  ];

  return transientCodes.some(code =>
    error.message.includes(code) || (error as any).code === code
  );
}
```

---

**Next:** [Inventory Management](./BOOKING_ENGINE_03_INVENTORY.md) — Detailed availability tracking and hold management
