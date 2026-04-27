# Booking Engine — Cancellations & Refunds

> Cancellation flows, refund processing, and penalty enforcement

**Series:** Booking Engine | **Document:** 6 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Cancellation Policies](#cancellation-policies)
3. [Cancellation Flow](#cancellation-flow)
4. [Refund Calculation](#refund-calculation)
5. [Penalty Enforcement](#penalty-enforcement)
6. [Supplier Cancellations](#supplier-cancellations)
7. [Refund Processing](#refund-processing)
8. [Partial Cancellations](#partial-cancellations)

---

## Overview

Cancellations are a critical part of travel booking operations. This document covers the complete cancellation and refund process, including policy enforcement, penalty calculation, supplier coordination, and refund processing.

### Cancellation Categories

| Category | Description | Refund |
|----------|-------------|--------|
| **Full Refund** | Cancellation within free window | 100% |
| **Partial Refund** | Cancellation with penalty | % based on timing |
| **Non-Refundable** | No refund permitted | 0% |
| **Force Majeure** | Unforeseeable circumstances | Case by case |
| **Supplier Failure** | Supplier cancelled | 100% |

### Cancellation Timeline

```
Booking → 30 days → 14 days → 7 days → 48h → 24h → Departure
         │           │          │        │      │
         ▼           ▼          ▼        ▼      ▼
      Full      90% Refund  50% Refund 25%   No Refund
      Refund
```

---

## Cancellation Policies

### Policy Structure

```typescript
// ============================================================================
// CANCELLATION POLICY MODEL
// ============================================================================

interface CancellationPolicy {
  id: string;
  name: string;
  description: string;

  // Policy tiers
  tiers: CancellationTier[];

  // Default policy
  defaultRefundPercentage: number;

  // Special conditions
  forceMajeureCovered: boolean;
  noShowPolicy: NoShowPolicy;

  // Applicability
  productTypes?: ProductType[];
  supplierIds?: string[];
  ticketTypes?: string[];
}

interface CancellationTier {
  // Time window
  cutoff: RelativeTime;
  cutoffType: 'before_departure' | 'before_checkin' | 'before_confirmation';

  // Refund rules
  refundPercentage: number;
  fixedFee?: number;
  minimumRefund?: number;

  // Penalties
  supplierPenaltyApplies: boolean;
}

type RelativeTime =
  | { days: number }
  | { hours: number }
  | { datetime: string }; // e.g., "18:00" on day of arrival

interface NoShowPolicy {
  refundPercentage: number;
  requiresNotification: boolean;
  notificationDeadline: RelativeTime;
}

// Standard policies
const STANDARD_POLICIES: Record<string, CancellationPolicy> = {
  flexible: {
    id: 'flexible',
    name: 'Flexible',
    description: 'Free cancellation up to 24 hours before departure',
    tiers: [
      {
        cutoff: { hours: 24 },
        cutoffType: 'before_departure',
        refundPercentage: 100,
        supplierPenaltyApplies: true,
      },
      {
        cutoff: { hours: 0 },
        cutoffType: 'before_departure',
        refundPercentage: 0,
        supplierPenaltyApplies: false,
      },
    ],
    defaultRefundPercentage: 100,
    forceMajeureCovered: true,
    noShowPolicy: {
      refundPercentage: 0,
      requiresNotification: true,
      notificationDeadline: { hours: 24 },
    },
  },

  moderate: {
    id: 'moderate',
    name: 'Moderate',
    description: 'Full refund up to 7 days, then partial',
    tiers: [
      {
        cutoff: { days: 7 },
        cutoffType: 'before_departure',
        refundPercentage: 100,
        supplierPenaltyApplies: true,
      },
      {
        cutoff: { days: 3 },
        cutoffType: 'before_departure',
        refundPercentage: 50,
        supplierPenaltyApplies: true,
      },
      {
        cutoff: { hours: 24 },
        cutoffType: 'before_departure',
        refundPercentage: 25,
        supplierPenaltyApplies: true,
      },
      {
        cutoff: { hours: 0 },
        cutoffType: 'before_departure',
        refundPercentage: 0,
        supplierPenaltyApplies: false,
      },
    ],
    defaultRefundPercentage: 50,
    forceMajeureCovered: true,
    noShowPolicy: {
      refundPercentage: 0,
      requiresNotification: true,
      notificationDeadline: { hours: 48 },
    },
  },

  strict: {
    id: 'strict',
    name: 'Strict',
    description: 'Non-refundable',
    tiers: [
      {
        cutoff: { days: 30 },
        cutoffType: 'before_departure',
        refundPercentage: 50,
        supplierPenaltyApplies: true,
      },
      {
        cutoff: { hours: 0 },
        cutoffType: 'before_departure',
        refundPercentage: 0,
        supplierPenaltyApplies: false,
      },
    ],
    defaultRefundPercentage: 0,
    forceMajeureCovered: false,
    noShowPolicy: {
      refundPercentage: 0,
      requiresNotification: false,
      notificationDeadline: { hours: 0 },
    },
  },
};

class CancellationPolicyService {
  async getPolicyForItem(item: BookingItem): Promise<CancellationPolicy> {
    // Check if item has specific policy
    if (item.cancellationPolicyId) {
      return await CancellationPolicy.findById(item.cancellationPolicyId);
    }

    // Check supplier default policy
    const supplier = await SupplierService.get(item.supplierId);
    if (supplier.defaultCancellationPolicy) {
      return STANDARD_POLICIES[supplier.defaultCancellationPolicy];
    }

    // Return moderate as default
    return STANDARD_POLICIES.moderate;
  }

  async getRefundPercentage(
    item: BookingItem,
    cancellationTime: Date = new Date()
  ): Promise<number> {
    const policy = await this.getPolicyForItem(item);
    const departureTime = this.getDepartureTime(item);
    const timeUntilDeparture = differenceInHours(departureTime, cancellationTime);

    // Find applicable tier
    for (const tier of policy.tiers) {
      const cutoffTime = this.calculateCutoffTime(departureTime, tier);

      if (cancellationTime <= cutoffTime) {
        return tier.refundPercentage;
      }
    }

    return policy.defaultRefundPercentage;
  }

  private getDepartureTime(item: BookingItem): Date {
    // For accommodation, it's check-in time (usually 15:00)
    if (item.type === 'accommodation') {
      const checkinTime = item.accommodation?.checkInTime || '15:00';
      const [hours, minutes] = checkinTime.split(':').map(Number);
      const checkin = new Date(item.dates.start);
      checkin.setHours(hours, minutes, 0, 0);
      return checkin;
    }

    // For flights, it's departure time
    if (item.type === 'flight') {
      return item.flight?.segments[0]?.departure?.date || item.dates.start;
    }

    // Default to start date
    return item.dates.start;
  }

  private calculateCutoffTime(departure: Date, tier: CancellationTier): Date {
    if (tier.cutoffType === 'before_departure') {
      if ('days' in tier.cutoff) {
        return subDays(departure, tier.cutoff.days);
      }
      if ('hours' in tier.cutoff) {
        return subHours(departure, tier.cutoff.hours);
      }
    }

    if (tier.cutoffType === 'before_checkin') {
      const checkin = setHours(departure, 15); // 15:00
      if ('days' in tier.cutoff) {
        return subDays(checkin, tier.cutoff.days);
      }
    }

    return departure;
  }
}
```

---

## Cancellation Flow

### Cancellation Orchestration

```typescript
// ============================================================================
// CANCELLATION FLOW
// ============================================================================

interface CancellationRequest {
  id: string;
  bookingId: string;
  itemId?: string; // For partial cancellations

  // Request details
  reason: string;
  reasonCode?: string;
  category: 'voluntary' | 'involuntary' | 'force_majeure' | 'supplier_failure';

  // Customer
  requestedBy: {
    type: 'customer' | 'agent' | 'system';
    id: string;
    name: string;
  };

  // Status
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'rejected';

  // Refund
  refundAmount: number;
  refundStatus: 'pending' | 'processing' | 'completed' | 'failed';

  // Timestamps
  createdAt: Date;
  processedAt?: Date;
  completedAt?: Date;
}

interface CancellationResult {
  success: boolean;
  booking: Booking;
  cancelledItems: BookingItem[];
  refund: {
    grossAmount: number;
    penalties: number;
    netAmount: number;
    status: string;
  };
  supplierCancellations: SupplierCancellation[];
  notificationsSent: boolean;
}

class CancellationOrchestrator {
  async cancelBooking(
    request: CancellationRequest
  ): Promise<CancellationResult> {
    const booking = await Booking.findById(request.bookingId);

    // Validate cancellation request
    await this.validateCancellation(booking, request);

    // Calculate refund
    const refundCalculation = await this.calculateRefund(booking, request);

    // Start distributed trace
    const tracer = trace.getTracer('booking-engine');

    return await tracer.startActiveSpan('cancelBooking', async (span) => {
      span.setAttribute('booking.id', booking.id);
      span.setAttribute('cancellation.reason', request.reason);
      span.setAttribute('cancellation.category', request.category);

      try {
        // Step 1: Update booking status
        booking.status = 'cancelling';
        booking.state = 'cancelling';
        await booking.save();

        // Step 2: Cancel with suppliers
        const supplierCancellations = await this.cancelWithSuppliers(booking, request);

        // Step 3: Release inventory holds
        await this.releaseInventory(booking, request);

        // Step 4: Process refund
        const refundResult = await this.processRefund(booking, refundCalculation);

        // Step 5: Update final status
        booking.status = request.itemId ? 'modified' : 'cancelled';
        booking.state = 'cancelled';
        booking.cancelledAt = new Date();
        await booking.save();

        // Step 6: Send notifications
        await this.sendCancellationNotifications(booking, request, refundCalculation);

        // Step 7: Record event
        await this.recordCancellationEvent(booking, request, refundCalculation);

        span.setStatus({ code: SpanStatusCode.OK });

        return {
          success: true,
          booking,
          cancelledItems: request.itemId
            ? booking.items.filter(i => i.id === request.itemId)
            : booking.items,
          refund: refundCalculation,
          supplierCancellations,
          notificationsSent: true,
        };

      } catch (error) {
        span.recordException(error as Error);
        span.setStatus({ code: SpanStatusCode.ERROR });

        booking.status = 'confirmed'; // Revert
        booking.state = 'confirmed';
        await booking.save();

        throw error;
      } finally {
        span.end();
      }
    });
  }

  private async validateCancellation(
    booking: Booking,
    request: CancellationRequest
  ): Promise<void> {
    // Check booking status
    if (booking.status === 'cancelled' || booking.status === 'refunded') {
      throw new AlreadyCancelledError(booking.id);
    }

    // Check if departure has passed
    const departure = this.getDepartureDate(booking);
    if (departure < new Date()) {
      throw new DeparturePassedError();
    }

    // Check for partial cancellation
    if (request.itemId) {
      const item = booking.items.find(i => i.id === request.itemId);
      if (!item) {
        throw new ItemNotFoundError(request.itemId);
      }

      if (item.status === 'cancelled') {
        throw new ItemAlreadyCancelledError(request.itemId);
      }

      // Check if partial cancellation is allowed
      const policy = await new CancellationPolicyService().getPolicyForItem(item);
      if (!this.partialCancellationAllowed(policy)) {
        throw new PartialCancellationNotAllowedError();
      }
    }

    // Check if force majeure documentation is required
    if (request.category === 'force_majeure') {
      if (!request.reasonCode || !this.hasForceMajeureDocumentation(request)) {
        throw new MissingDocumentationError('force_majeure');
      }
    }
  }

  private async cancelWithSuppliers(
    booking: Booking,
    request: CancellationRequest
  ): Promise<SupplierCancellation[]> {
    const itemsToCancel = request.itemId
      ? booking.items.filter(i => i.id === request.itemId)
      : booking.items;

    const cancellations: SupplierCancellation[] = [];

    for (const item of itemsToCancel) {
      if (item.status === 'cancelled') continue;

      try {
        // Cancel with supplier
        const cancellation = await this.cancelSupplierItem(item, request);

        // Update item status
        item.status = 'cancelled';
        item.cancelledAt = new Date();
        item.cancellationReason = request.reason;
        await item.save();

        cancellations.push({
          itemId: item.id,
          supplierId: item.supplierId,
          supplierReference: item.supplierReference,
          status: 'cancelled',
          confirmation: cancellation.confirmation,
        });

      } catch (error) {
        logger.error('Supplier cancellation failed', {
          bookingId: booking.id,
          itemId: item.id,
          supplierId: item.supplierId,
          error,
        });

        cancellations.push({
          itemId: item.id,
          supplierId: item.supplierId,
          supplierReference: item.supplierReference,
          status: 'failed',
          error: error.message,
        });

        // Continue with other items
      }
    }

    return cancellations;
  }

  private async cancelSupplierItem(
    item: BookingItem,
    request: CancellationRequest
  ): Promise<{ confirmation?: string }> {
    const supplier = await SupplierService.get(item.supplierId);

    if (!item.supplierReference) {
      // No supplier booking yet - nothing to cancel
      return {};
    }

    // Check if supplier supports cancellation
    if (!supplier.features.cancellation) {
      logger.warn('Supplier does not support cancellation', {
        supplierId: item.supplierId,
        itemId: item.id,
      });
      return {};
    }

    // Call supplier API
    try {
      const result = await SupplierService.cancelBooking({
        supplierId: item.supplierId,
        bookingReference: item.supplierReference,
        reason: request.reason,
        reasonCode: request.reasonCode,
        category: request.category,
      });

      return { confirmation: result.confirmationNumber };

    } catch (error) {
      // Log but don't fail - we'll handle refund separately
      logger.error('Supplier API cancellation failed', {
        supplierId: item.supplierId,
        bookingReference: item.supplierReference,
        error,
      });
      return {};
    }
  }

  private async releaseInventory(
    booking: Booking,
    request: CancellationRequest
  ): Promise<void> {
    const itemsToCancel = request.itemId
      ? booking.items.filter(i => i.id === request.itemId)
      : booking.items;

    for (const item of itemsToCancel) {
      // Release any active holds
      const holds = await InventoryHold.find({
        bookingItemId: item.id,
        status: 'active',
      });

      for (const hold of holds) {
        await new HoldManager().releaseHold(hold.id, 'booking_cancelled');
      }

      // Increment inventory availability
      const dates = eachDayOfInterval(item.dates);
      for (const date of dates) {
        await InventoryService.incrementAvailability({
          supplierId: item.supplierId,
          productId: item.productId,
          date: formatISO(date),
          quantity: 1,
        });
      }
    }
  }

  private getDepartureDate(booking: Booking): Date {
    return booking.items.reduce((earliest, item) => {
      const departure = item.type === 'accommodation'
        ? item.dates.start
        : item.flight?.segments[0]?.departure?.date || item.dates.start;
      return departure < earliest ? departure : earliest;
    }, booking.items[0].dates.start);
  }

  private partialCancellationAllowed(policy: CancellationPolicy): boolean {
    // Partial cancellations usually allowed for flexible policies
    return policy.id === 'flexible';
  }

  private hasForceMajeureDocumentation(request: CancellationRequest): boolean {
    // Check if required documentation is attached
    return request.metadata?.documentationAttached === true;
  }
}

interface SupplierCancellation {
  itemId: string;
  supplierId: string;
  supplierReference: string;
  status: 'cancelled' | 'failed';
  confirmation?: string;
  error?: string;
}
```

---

## Refund Calculation

### Refund Computation

```typescript
// ============================================================================
// REFUND CALCULATION
// ============================================================================

interface RefundCalculation {
  // Amounts
  grossAmount: number;       // Original payment amount
  penalties: number;          // Total penalties
  netAmount: number;          // Amount to refund

  // Breakdown
  breakdown: RefundBreakdown[];

  // Status
  refundable: boolean;
  reason?: string;
}

interface RefundBreakdown {
  itemId: string;
  itemName: string;
  grossAmount: number;
  penalty: number;
  refundPercentage: number;
  netAmount: number;
  penaltyReason: string;
}

class RefundCalculator {
  async calculateRefund(
    booking: Booking,
    request: CancellationRequest
  ): Promise<RefundCalculation> {
    const itemsToCancel = request.itemId
      ? booking.items.filter(i => i.id === request.itemId)
      : booking.items;

    const breakdown: RefundBreakdown[] = [];
    let totalGross = 0;
    let totalPenalty = 0;
    let totalNet = 0;

    for (const item of itemsToCancel) {
      if (item.status === 'cancelled') continue;

      const itemRefund = await this.calculateItemRefund(item, request);

      breakdown.push(itemRefund);
      totalGross += itemRefund.grossAmount;
      totalPenalty += itemRefund.penalty;
      totalNet += itemRefund.netAmount;
    }

    // Add any change fees if partial cancellation
    if (request.itemId) {
      const changeFee = await this.calculatePartialCancellationChangeFee(booking);
      totalPenalty += changeFee;
      totalNet = Math.max(0, totalNet - changeFee);
    }

    return {
      grossAmount: totalGross,
      penalties: totalPenalty,
      netAmount: totalNet,
      breakdown,
      refundable: totalNet > 0,
      reason: totalNet === 0 ? 'Non-refundable booking' : undefined,
    };
  }

  private async calculateItemRefund(
    item: BookingItem,
    request: CancellationRequest
  ): Promise<RefundBreakdown> {
    const policyService = new CancellationPolicyService();
    const policy = await policyService.getPolicyForItem(item);

    // Get refund percentage based on timing
    const refundPercentage = request.category === 'supplier_failure'
      ? 100  // Full refund if supplier failed
      : request.category === 'force_majeure' && policy.forceMajeureCovered
      ? 100  // Full refund for force majeure if covered
      : await policyService.getRefundPercentage(item, new Date());

    // Calculate amounts
    const grossAmount = item.pricing.total;
    let penalty = 0;
    let netAmount = grossAmount;

    if (refundPercentage < 100) {
      penalty = grossAmount * (1 - refundPercentage / 100);
      netAmount = grossAmount - penalty;
    }

    // Check for fixed fees
    const tier = this.getApplicableTier(policy, item);
    if (tier?.fixedFee) {
      penalty = Math.max(penalty, tier.fixedFee);
      netAmount = Math.max(0, grossAmount - penalty);
    }

    // Check supplier penalties
    if (tier?.supplierPenaltyApplies) {
      const supplierPenalty = await this.getSupplierPenalty(item);
      if (supplierPenalty > 0) {
        penalty += supplierPenalty;
        netAmount = Math.max(0, netAmount - supplierPenalty);
      }
    }

    return {
      itemId: item.id,
      itemName: this.getItemName(item),
      grossAmount,
      penalty,
      refundPercentage,
      netAmount,
      penaltyReason: this.getPenaltyReason(policy, refundPercentage),
    };
  }

  private getApplicableTier(
    policy: CancellationPolicy,
    item: BookingItem
  ): CancellationTier | undefined {
    const departureTime = new CancellationPolicyService()['getDepartureTime'](item);
    const now = new Date();

    return policy.tiers.find(tier => {
      const cutoff = new CancellationPolicyService()['calculateCutoffTime'](departureTime, tier);
      return now <= cutoff;
    });
  }

  private async getSupplierPenalty(item: BookingItem): Promise<number> {
    try {
      const penalty = await SupplierService.getCancellationPenalty({
        supplierId: item.supplierId,
        bookingReference: item.supplierReference,
      });

      return penalty.amount;
    } catch (error) {
      logger.error('Failed to get supplier penalty', {
        supplierId: item.supplierId,
        itemId: item.id,
        error,
      });
      return 0;
    }
  }

  private async calculatePartialCancellationChangeFee(
    booking: Booking
  ): Promise<number> {
    // Partial cancellations may incur a processing fee
    const activeItems = booking.items.filter(i => i.status !== 'cancelled');
    return activeItems.length > 1 ? 25 : 0; // $25 fee if still have other items
  }

  private getItemName(item: BookingItem): string {
    switch (item.type) {
      case 'accommodation':
        return item.accommodation?.name || 'Accommodation';
      case 'flight':
        return 'Flight';
      case 'transfer':
        return 'Transfer';
      case 'activity':
        return item.activity?.name || 'Activity';
      default:
        return 'Item';
    }
  }

  private getPenaltyReason(
    policy: CancellationPolicy,
    refundPercentage: number
  ): string {
    if (refundPercentage === 0) {
      return 'Non-refundable rate';
    }
    if (refundPercentage === 100) {
      return 'No penalty';
    }
    return `${100 - refundPercentage}% cancellation penalty`;
  }
}
```

---

## Penalty Enforcement

### Penalty Application

```typescript
// ============================================================================
// PENALTY ENFORCEMENT
// ============================================================================

interface PenaltyEnforcement {
  applicable: boolean;
  penalties: Penalty[];
  totalPenalty: number;
  waiver: {
    applicable: boolean;
    reason?: string;
  };
}

interface Penalty {
  type: 'cancellation' | 'no_show' | 'processing' | 'supplier';
  amount: number;
  percentage?: number;
  description: string;
  waiveable: boolean;
}

class PenaltyEnforcer {
  async enforcePenalties(
    booking: Booking,
    request: CancellationRequest
  ): Promise<PenaltyEnforcement> {
    const penalties: Penalty[] = [];

    // 1. Cancellation penalty based on timing
    const cancellationPenalty = await this.calculateCancellationPenalty(booking, request);
    if (cancellationPenalty.amount > 0) {
      penalties.push(cancellationPenalty);
    }

    // 2. No-show penalty if applicable
    const noShowPenalty = await this.calculateNoShowPenalty(booking, request);
    if (noShowPenalty.amount > 0) {
      penalties.push(noShowPenalty);
    }

    // 3. Processing fee
    const processingFee = this.calculateProcessingFee(booking);
    if (processingFee.amount > 0) {
      penalties.push(processingFee);
    }

    // 4. Supplier penalties
    const supplierPenalties = await this.getSupplierPenalties(booking, request);
    penalties.push(...supplierPenalties);

    const totalPenalty = penalties.reduce((sum, p) => sum + p.amount, 0);

    // Check for waiver eligibility
    const waiver = await this.checkWaiverEligibility(booking, request, penalties);

    return {
      applicable: totalPenalty > 0 && !waiver.applicable,
      penalties,
      totalPenalty: waiver.applicable ? 0 : totalPenalty,
      waiver,
    };
  }

  private async calculateCancellationPenalty(
    booking: Booking,
    request: CancellationRequest
  ): Promise<Penalty> {
    const items = request.itemId
      ? booking.items.filter(i => i.id === request.itemId)
      : booking.items;

    let totalPenalty = 0;
    let totalGross = 0;

    for (const item of items) {
      if (item.status === 'cancelled') continue;

      const policyService = new CancellationPolicyService();
      const refundPercentage = await policyService.getRefundPercentage(item, new Date());

      totalPenalty += item.pricing.total * (1 - refundPercentage / 100);
      totalGross += item.pricing.total;
    }

    const percentage = totalGross > 0 ? (totalPenalty / totalGross) * 100 : 0;

    return {
      type: 'cancellation',
      amount: totalPenalty,
      percentage,
      description: `Cancellation penalty (${percentage.toFixed(0)}%)`,
      waiveable: percentage < 50, // Small penalties more likely to be waived
    };
  }

  private async calculateNoShowPenalty(
    booking: Booking,
    request: CancellationRequest
  ): Promise<Penalty> {
    // Check if this qualifies as a no-show
    const departure = this.getDepartureDate(booking);
    const hoursUntil = differenceInHours(departure, new Date());

    if (hoursUntil > 24) {
      return { type: 'no_show', amount: 0, description: '', waiveable: false };
    }

    // Get no-show policy for items
    const items = request.itemId
      ? booking.items.filter(i => i.id === request.itemId)
      : booking.items;

    let totalPenalty = 0;

    for (const item of items) {
      const policy = await new CancellationPolicyService().getPolicyForItem(item);
      totalPenalty += item.pricing.total * (1 - policy.noShowPolicy.refundPercentage / 100);
    }

    return {
      type: 'no_show',
      amount: totalPenalty,
      description: 'No-show penalty',
      waiveable: false,
    };
  }

  private calculateProcessingFee(booking: Booking): Penalty {
    // Standard processing fee for cancellations
    return {
      type: 'processing',
      amount: 25,
      description: 'Processing fee',
      waiveable: true,
    };
  }

  private async getSupplierPenalties(
    booking: Booking,
    request: CancellationRequest
  ): Promise<Penalty[]> {
    const items = request.itemId
      ? booking.items.filter(i => i.id === request.itemId)
      : booking.items;

    const penalties: Penalty[] = [];

    for (const item of items) {
      if (!item.supplierReference) continue;

      try {
        const supplierPenalty = await SupplierService.getCancellationPenalty({
          supplierId: item.supplierId,
          bookingReference: item.supplierReference,
        });

        if (supplierPenalty.amount > 0) {
          penalties.push({
            type: 'supplier',
            amount: supplierPenalty.amount,
            description: `Supplier penalty (${item.supplierId})`,
            waiveable: false, // Supplier penalties usually not waiveable
          });
        }
      } catch (error) {
        logger.error('Failed to get supplier penalty', {
          supplierId: item.supplierId,
          error,
        });
      }
    }

    return penalties;
  }

  private async checkWaiverEligibility(
    booking: Booking,
    request: CancellationRequest,
    penalties: Penalty[]
  ): Promise<{ applicable: boolean; reason?: string }> {
    // Force majeure - all penalties waived
    if (request.category === 'force_majeure') {
      return {
        applicable: true,
        reason: 'Force majeure - all penalties waived',
      };
    }

    // Supplier failure - all penalties waived
    if (request.category === 'supplier_failure') {
      return {
        applicable: true,
        reason: 'Supplier failure - all penalties waived',
      };
    }

    // Elite customer status - waive waiveable penalties
    const customer = await CustomerService.get(booking.customerId);
    if (customer.tier === 'platinum') {
      const waiveablePenalties = penalties.filter(p => p.waiveable);
      if (waiveablePenalties.length === penalties.length) {
        return {
          applicable: true,
          reason: 'Platinum tier benefit - penalties waived',
        };
      }
    }

    // First-time cancellation - waive processing fee
    const previousCancellations = await CancellationRequest.countDocuments({
      bookingId: booking.id,
      status: 'completed',
    });

    if (previousCancellations === 0) {
      const processingFee = penalties.find(p => p.type === 'processing');
      if (processingFee && penalties.length === 1) {
        return {
          applicable: true,
          reason: 'First-time cancellation courtesy - processing fee waived',
        };
      }
    }

    return { applicable: false };
  }

  private getDepartureDate(booking: Booking): Date {
    return booking.items.reduce((earliest, item) => {
      const departure = item.type === 'accommodation'
        ? item.dates.start
        : item.flight?.segments[0]?.departure?.date || item.dates.start;
      return departure < earliest ? departure : earliest;
    }, booking.items[0].dates.start);
  }
}
```

---

## Supplier Cancellations

### Supplier Coordination

```typescript
// ============================================================================
// SUPPLIER CANCELLATION HANDLING
// ============================================================================

interface SupplierCancellationRequest {
  supplierId: string;
  bookingReference: string;
  reason: string;
  reasonCode?: string;
  category: 'voluntary' | 'involuntary' | 'force_majeure';
}

interface SupplierCancellationResponse {
  success: boolean;
  confirmationNumber?: string;
  penalty?: {
    amount: number;
    currency: string;
    description: string;
  };
  refund?: {
    amount: number;
    currency: string;
    processingTime: number; // days
  };
  error?: string;
}

class SupplierCancellationClient {
  async cancelBooking(
    item: BookingItem,
    request: CancellationRequest
  ): Promise<SupplierCancellationResponse> {
    const supplier = await SupplierService.get(item.supplierId);

    // Check if supplier supports cancellation
    if (!supplier.features.cancellation) {
      logger.warn('Supplier does not support cancellation', {
        supplierId: item.supplierId,
      });
      return {
        success: false,
        error: 'Supplier does not support cancellation',
      };
    }

    // Build cancellation request
    const supplierRequest: SupplierCancellationRequest = {
      supplierId: item.supplierId,
      bookingReference: item.supplierReference || '',
      reason: request.reason,
      reasonCode: request.reasonCode,
      category: request.category,
    };

    // Call supplier API
    try {
      const response = await this.callSupplierAPI(
        supplier,
        supplierRequest
      );

      // Store cancellation confirmation
      if (response.success && response.confirmationNumber) {
        await SupplierCancellation.create({
          bookingId: item.bookingId,
          itemId: item.id,
          supplierId: item.supplierId,
          supplierBookingReference: item.supplierReference,
          cancellationReference: response.confirmationNumber,
          penalty: response.penalty,
          refund: response.refund,
          cancelledAt: new Date(),
        });
      }

      return response;

    } catch (error) {
      logger.error('Supplier cancellation API failed', {
        supplierId: item.supplierId,
        bookingReference: item.supplierReference,
        error,
      });

      return {
        success: false,
        error: error.message,
      };
    }
  }

  private async callSupplierAPI(
    supplier: Supplier,
    request: SupplierCancellationRequest
  ): Promise<SupplierCancellationResponse> {
    // Supplier-specific implementations
    switch (supplier.integrationType) {
      case 'rest':
        return await this.cancelViaREST(supplier, request);

      case 'soap':
        return await this.cancelViaSOAP(supplier, request);

      case 'email':
        return await this.cancelViaEmail(supplier, request);

      case 'manual':
        return await this.cancelManually(supplier, request);

      default:
        throw new Error(`Unknown integration type: ${supplier.integrationType}`);
    }
  }

  private async cancelViaREST(
    supplier: Supplier,
    request: SupplierCancellationRequest
  ): Promise<SupplierCancellationResponse> {
    const response = await fetch(`${supplier.apiEndpoint}/cancellations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supplier.apiKey}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new SupplierAPIError(supplier.id, response.status);
    }

    return await response.json();
  }

  private async cancelViaSOAP(
    supplier: Supplier,
    request: SupplierCancellationRequest
  ): Promise<SupplierCancellationResponse> {
    // SOAP client implementation
    const client = new SOAPClient(supplier.wsdlUrl);
    return await client.cancelBooking(request);
  }

  private async cancelViaEmail(
    supplier: Supplier,
    request: SupplierCancellationRequest
  ): Promise<SupplierCancellationResponse> {
    // Send cancellation email
    await EmailService.send({
      to: supplier.cancellationEmail,
      subject: `Cancellation Request: ${request.bookingReference}`,
      body: this.buildCancellationEmailBody(request),
    });

    // Return pending status
    return {
      success: true,
      // Email cancellations don't get immediate confirmation
    };
  }

  private async cancelManually(
    supplier: Supplier,
    request: SupplierCancellationRequest
  ): Promise<SupplierCancellationResponse> {
    // Queue for manual processing
    await Queue.add('manual-cancellation', {
      supplierId: supplier.id,
      request,
      priority: 'high',
    });

    return {
      success: true,
      // Manual cancellations will be processed later
    };
  }

  private buildCancellationEmailBody(request: SupplierCancellationRequest): string {
    return `
      Cancellation Request

      Booking Reference: ${request.bookingReference}
      Reason: ${request.reason}
      Category: ${request.category}

      Please process this cancellation and confirm.
    `;
  }
}
```

---

## Refund Processing

### Refund Execution

```typescript
// ============================================================================
// REFUND PROCESSING
// ============================================================================

interface RefundRequest {
  bookingId: string;
  cancellationId: string;
  amount: number;
  currency: string;
  reason: string;

  // Refund method
  method: 'original' | 'wallet' | 'bank_transfer';
  walletCredit?: boolean;

  // Processing
  priority: 'normal' | 'urgent';
}

interface RefundResult {
  refundId: string;
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processor: string;
  estimatedCompletion?: Date;
  transactionId?: string;
  failureReason?: string;
}

class RefundProcessor {
  async processRefund(
    booking: Booking,
    calculation: RefundCalculation,
    request: CancellationRequest
  ): Promise<RefundResult> {
    if (calculation.netAmount === 0) {
      return {
        refundId: crypto.randomUUID(),
        amount: 0,
        currency: booking.pricing.currency,
        status: 'completed',
        processor: 'none',
      };
    }

    // Get original payment
    const payment = await BookingPayment.findOne({
      bookingId: booking.id,
      status: 'captured',
    }).sort({ createdAt: -1 });

    if (!payment) {
      throw new PaymentNotFoundError();
    }

    // Create refund request
    const refundRequest: RefundRequest = {
      bookingId: booking.id,
      cancellationId: request.id,
      amount: calculation.netAmount,
      currency: booking.pricing.currency,
      reason: request.reason,
      method: 'original',
      priority: calculation.netAmount > 1000 ? 'urgent' : 'normal',
    };

    // Process refund based on payment method
    const result = await this.executeRefund(payment, refundRequest);

    // Record refund
    await RefundRecord.create({
      bookingId: booking.id,
      cancellationId: request.id,
      paymentId: payment.paymentId,
      ...result,
    });

    return result;
  }

  private async executeRefund(
    payment: BookingPayment,
    request: RefundRequest
  ): Promise<RefundResult> {
    // Check if refund is possible
    const timeSinceCapture = differenceInMilliseconds(new Date(), payment.capturedAt);
    const refundWindow = 180 * 24 * 60 * 60 * 1000; // 180 days in ms

    if (timeSinceCapture > refundWindow) {
      throw new RefundWindowExpiredError();
    }

    // Process refund based on payment method
    switch (payment.method) {
      case 'card':
        return await this.refundToCard(payment, request);

      case 'paypal':
        return await this.refundToPayPal(payment, request);

      case 'bank_transfer':
        return await this.refundToBank(payment, request);

      case 'wallet':
        return await this.refundToWallet(payment, request);

      default:
        throw new UnsupportedPaymentMethodError(payment.method);
    }
  }

  private async refundToCard(
    payment: BookingPayment,
    request: RefundRequest
  ): Promise<RefundResult> {
    try {
      const refund = await PaymentService.refund({
        paymentId: payment.paymentId,
        amount: request.amount,
        reason: request.reason,
      });

      return {
        refundId: refund.id,
        amount: request.amount,
        currency: request.currency,
        status: refund.status === 'succeeded' ? 'completed' : 'processing',
        processor: 'stripe',
        transactionId: refund.id,
      };

    } catch (error) {
      return {
        refundId: crypto.randomUUID(),
        amount: request.amount,
        currency: request.currency,
        status: 'failed',
        processor: 'stripe',
        failureReason: error.message,
      };
    }
  }

  private async refundToPayPal(
    payment: BookingPayment,
    request: RefundRequest
  ): Promise<RefundResult> {
    try {
      const refund = await PayPalService.refund({
        captureId: payment.transactionId,
        amount: request.amount,
        currency: request.currency,
      });

      return {
        refundId: refund.id,
        amount: request.amount,
        currency: request.currency,
        status: refund.state === 'completed' ? 'completed' : 'processing',
        processor: 'paypal',
        transactionId: refund.id,
      };

    } catch (error) {
      return {
        refundId: crypto.randomUUID(),
        amount: request.amount,
        currency: request.currency,
        status: 'failed',
        processor: 'paypal',
        failureReason: error.message,
      };
    }
  }

  private async refundToBank(
    payment: BookingPayment,
    request: RefundRequest
  ): Promise<RefundResult> {
    // Bank transfers require manual processing
    await Queue.add('bank-refund', {
      paymentId: payment.paymentId,
      amount: request.amount,
      currency: request.currency,
      reason: request.reason,
    });

    // Estimate 5-10 business days
    const estimatedCompletion = addBusinessDays(new Date(), 7);

    return {
      refundId: crypto.randomUUID(),
      amount: request.amount,
      currency: request.currency,
      status: 'processing',
      processor: 'bank_transfer',
      estimatedCompletion,
    };
  }

  private async refundToWallet(
    payment: BookingPayment,
    request: RefundRequest
  ): Promise<RefundResult> {
    // Credit to customer wallet
    await WalletService.credit({
      customerId: payment.customerId,
      amount: request.amount,
      currency: request.currency,
      reference: `Refund for booking ${request.bookingId}`,
    });

    return {
      refundId: crypto.randomUUID(),
      amount: request.amount,
      currency: request.currency,
      status: 'completed',
      processor: 'wallet',
    };
  }
}
```

---

## Partial Cancellations

### Partial Item Cancellation

```typescript
// ============================================================================
// PARTIAL CANCELLATIONS
// ============================================================================

class PartialCancellationHandler {
  async cancelPartialBooking(
    booking: Booking,
    request: CancellationRequest
  ): Promise<CancellationResult> {
    if (!request.itemId) {
      throw new ItemRequiredError();
    }

    const item = booking.items.find(i => i.id === request.itemId);
    if (!item) {
      throw new ItemNotFoundError(request.itemId);
    }

    // Validate partial cancellation allowed
    const policy = await new CancellationPolicyService().getPolicyForItem(item);
    if (!this.partialCancellationAllowed(policy, booking)) {
      throw new PartialCancellationNotAllowedError();
    }

    // Check if this is the last item
    const remainingItems = booking.items.filter(i => i.status !== 'cancelled' && i.id !== request.itemId);
    if (remainingItems.length === 0) {
      // This would cancel the whole booking - redirect to full cancellation
      return await new CancellationOrchestrator().cancelBooking({
        ...request,
        itemId: undefined,
      });
    }

    // Process partial cancellation
    const result = await new CancellationOrchestrator().cancelBooking(request);

    // Update booking status (not cancelled, just modified)
    booking.status = 'modified';
    await booking.save();

    return {
      ...result,
      booking,
    };
  }

  private partialCancellationAllowed(
    policy: CancellationPolicy,
    booking: Booking
  ): boolean {
    // Flexible policies allow partial cancellation
    if (policy.id === 'flexible') {
      return true;
    }

    // Check if booking has multiple items
    const activeItems = booking.items.filter(i => i.status !== 'cancelled');
    if (activeItems.length <= 1) {
      return false; // Can't partially cancel single-item booking
    }

    // Moderate policies allow partial cancellation for some product types
    if (policy.id === 'moderate') {
      return true;
    }

    // Strict policies don't allow partial cancellation
    return false;
  }
}
```

---

**Next:** [Waitlist System](./BOOKING_ENGINE_07_WAITLIST.md) — Waitlist management, notifications, and conversion
