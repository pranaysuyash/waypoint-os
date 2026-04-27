# Booking Engine — Booking Modifications

> Change requests, modifications, and rebooking flows

**Series:** Booking Engine | **Document:** 5 of 8 | **Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Modification Types](#modification-types)
3. [Modification Rules Engine](#modification-rules-engine)
4. [Price Difference Handling](#price-difference-handling)
5. [Change Fees & Penalties](#change-fees--penalties)
6. [Inventory Re-availability](#inventory-re-availability)
7. [Rebooking Flows](#rebooking-flows)
8. [Modification Limits](#modification-limits)

---

## Overview

Booking modifications allow customers to change their travel plans after confirmation. This is a complex process involving price adjustments, change fees, inventory availability checks, and supplier coordination.

### Modification Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Date Changes** | Move booking to different dates | Reschedule hotel stay |
| **Guest Changes** | Change traveler details | Update passenger name |
| **Upgrade/Downgrade** | Change room class or fare | Economy → Business |
| **Add/Remove Items** | Add or remove booking items | Add airport transfer |
| **Cancellation** | Cancel entire or partial booking | Cancel one night |
| **Special Requests** | Add preferences or notes | Request high floor |

### Modification Constraints

| Constraint | Description |
|------------|-------------|
| **Time-based** | Deadlines for changes (e.g., 48h before) |
| **Supplier Rules** | Each supplier's modification policy |
| **Inventory** | New dates/items must be available |
| **Pricing** | Price differences and change fees |
| **Ticket Type** | Non-refundable vs flexible fares |

---

## Modification Types

### Type Definitions

```typescript
// ============================================================================
// MODIFICATION TYPES
// ============================================================================

type ModificationType =
  | 'change_dates'        // Change travel dates
  | 'change_guests'       // Update traveler information
  | 'upgrade'             // Upgrade room/fare class
  | 'downgrade'           // Downgrade room/fare class
  | 'add_item'            // Add new booking item
  | 'remove_item'         // Remove booking item
  | 'cancel_partial'      // Cancel part of booking
  | 'special_request'     // Add special requests
  | 'correction';         // Fix errors

interface ModificationRequest {
  id: string;
  bookingId: string;

  // Request details
  type: ModificationType;
  description: string;
  urgent: boolean;

  // Changes
  changes: ModificationChange[];

  // Customer
  requestedBy: {
    type: 'customer' | 'agent' | 'system';
    id: string;
    name: string;
  };

  // Status
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'processing' | 'completed' | 'failed';

  // Approval
  requiresApproval: boolean;
  approvedBy?: string;
  approvedAt?: Date;
  rejectionReason?: string;

  // Pricing
  priceDifference: number;
  changeFee: number;
  refundAmount: number;
  additionalPayment: number;

  // Timestamps
  createdAt: Date;
  processedAt?: Date;
  completedAt?: Date;
}

interface ModificationChange {
  itemId: string;
  type: 'date' | 'guest' | 'upgrade' | 'cancel' | 'custom';
  from: Record<string, unknown>;
  to: Record<string, unknown>;
}

// Date change
interface DateChange extends ModificationChange {
  type: 'date';
  from: { dates: DateRange };
  to: { dates: DateRange };
}

// Guest change
interface GuestChange extends ModificationChange {
  type: 'guest';
  from: { travelers: Traveler[] };
  to: { travelers: Traveler[] };
}

// Upgrade
interface UpgradeChange extends ModificationChange {
  type: 'upgrade';
  from: { roomType?: string; cabinClass?: string };
  to: { roomType?: string; cabinClass?: string };
}
```

---

## Modification Rules Engine

### Rule Evaluation

```typescript
// ============================================================================
// MODIFICATION RULES ENGINE
// ============================================================================

interface ModificationRule {
  id: string;
  name: string;
  priority: number;

  // Conditions
  conditions: {
    bookingStatus?: string[];
    timeBeforeDeparture?: { min?: number; max?: number }; // hours
    modificationTypes?: ModificationType[];
    productTypes?: ProductType[];
    supplierIds?: string[];
    ticketTypes?: string[];
  };

  // Actions
  actions: {
    allowed?: boolean;
    requiresApproval?: boolean;
    changeFee?: number | 'percentage' | 'supplier';
    minChangeFee?: number;
    maxChangeFee?: number;
    refundPolicy?: 'full' | 'partial' | 'none' | 'supplier';
    timeLimit?: number; // hours before departure
  };

  // Fees
  fees?: {
    fixed?: number;
    percentage?: number;
    perItem?: boolean;
    supplierRule?: boolean; // Use supplier's rule
  };
}

class ModificationRulesEngine {
  private rules: ModificationRule[];

  constructor() {
    this.rules = this.loadRules();
  }

  async evaluateModification(
    request: ModificationRequest
  ): Promise<ModificationEvaluation> {
    const booking = await Booking.findById(request.bookingId);

    // Evaluate applicable rules
    const applicableRules = this.rules.filter(rule =>
      this.matchesRule(booking, request, rule)
    );

    // Sort by priority
    applicableRules.sort((a, b) => b.priority - a.priority);

    // Apply rules in order
    const evaluation: ModificationEvaluation = {
      allowed: true,
      requiresApproval: false,
      changeFees: [],
      totalChangeFee: 0,
      refundAmount: 0,
      additionalPayment: 0,
      restrictions: [],
    };

    for (const rule of applicableRules) {
      this.applyRule(evaluation, booking, request, rule);
    }

    // Calculate price difference
    evaluation.priceDifference = await this.calculatePriceDifference(booking, request);

    // Calculate final amounts
    evaluation.additionalPayment = Math.max(0, evaluation.priceDifference + evaluation.totalChangeFee);
    evaluation.refundAmount = Math.max(0, -evaluation.priceDifference - evaluation.totalChangeFee);

    return evaluation;
  }

  private matchesRule(
    booking: Booking,
    request: ModificationRequest,
    rule: ModificationRule
  ): boolean {
    const conditions = rule.conditions;

    // Check booking status
    if (conditions.bookingStatus && !conditions.bookingStatus.includes(booking.status)) {
      return false;
    }

    // Check time before departure
    if (conditions.timeBeforeDeparture) {
      const departure = this.getDepartureDate(booking);
      const hoursUntil = differenceInHours(departure, new Date());

      if (conditions.timeBeforeDeparture.min !== undefined &&
          hoursUntil < conditions.timeBeforeDeparture.min) {
        return false;
      }

      if (conditions.timeBeforeDeparture.max !== undefined &&
          hoursUntil > conditions.timeBeforeDeparture.max) {
        return false;
      }
    }

    // Check modification type
    if (conditions.modificationTypes && !conditions.modificationTypes.includes(request.type)) {
      return false;
    }

    // Check product types
    if (conditions.productTypes) {
      const itemTypes = new Set(booking.items.map(i => i.type));
      if (!conditions.productTypes.some(t => itemTypes.has(t))) {
        return false;
      }
    }

    // Check supplier IDs
    if (conditions.supplierIds) {
      const supplierIds = new Set(booking.items.map(i => i.supplierId));
      if (!conditions.supplierIds.some(s => supplierIds.has(s))) {
        return false;
      }
    }

    return true;
  }

  private applyRule(
    evaluation: ModificationEvaluation,
    booking: Booking,
    request: ModificationRequest,
    rule: ModificationRule
  ): void {
    const actions = rule.actions;

    // Check if modification is allowed
    if (actions.allowed === false) {
      evaluation.allowed = false;
      evaluation.restrictions.push({
        rule: rule.name,
        reason: 'Modification not allowed by policy',
      });
      return;
    }

    // Check approval requirement
    if (actions.requiresApproval) {
      evaluation.requiresApproval = true;
    }

    // Calculate change fees
    if (rule.fees) {
      const fee = this.calculateFee(booking, request, rule);
      evaluation.changeFees.push({
        rule: rule.name,
        amount: fee,
      });
      evaluation.totalChangeFee += fee;
    }
  }

  private calculateFee(
    booking: Booking,
    request: ModificationRequest,
    rule: ModificationRule
  ): number {
    const fees = rule.fees!;

    // Fixed fee
    if (fees.fixed !== undefined) {
      return fees.perItem
        ? fees.fixed * request.changes.length
        : fees.fixed;
    }

    // Percentage fee
    if (fees.percentage !== undefined) {
      const baseAmount = booking.pricing.total;
      return (baseAmount * fees.percentage) / 100;
    }

    // Supplier rule
    if (fees.supplierRule) {
      // Will be calculated when checking with supplier
      return 0; // Placeholder
    }

    return 0;
  }

  private async calculatePriceDifference(
    booking: Booking,
    request: ModificationRequest
  ): Promise<number> {
    let difference = 0;

    for (const change of request.changes) {
      const item = booking.items.find(i => i.id === change.itemId);
      if (!item) continue;

      const oldPrice = item.pricing.total;

      // Calculate new price based on change type
      let newPrice = oldPrice;

      switch (change.type) {
        case 'date':
          newPrice = await this.getPriceForDates(item, change.to.dates as DateRange);
          break;

        case 'upgrade':
          newPrice = await this.getPriceForUpgrade(item, change.to);
          break;

        case 'downgrade':
          newPrice = await this.getPriceForDowngrade(item, change.to);
          break;

        case 'cancel':
          newPrice = 0;
          break;
      }

      difference += newPrice - oldPrice;
    }

    return difference;
  }

  private loadRules(): ModificationRule[] {
    return [
      // Rule 1: No changes within 24 hours
      {
        id: 'no-changes-24h',
        name: 'No changes within 24 hours of departure',
        priority: 100,
        conditions: {
          bookingStatus: ['confirmed'],
          timeBeforeDeparture: { max: 24 },
        },
        actions: {
          allowed: false,
        },
      },

      // Rule 2: Date changes within 48 hours require approval
      {
        id: 'date-changes-48h',
        name: 'Date changes within 48 hours require approval',
        priority: 90,
        conditions: {
          bookingStatus: ['confirmed'],
          timeBeforeDeparture: { min: 24, max: 48 },
          modificationTypes: ['change_dates'],
        },
        actions: {
          allowed: true,
          requiresApproval: true,
        },
      },

      // Rule 3: Standard change fee
      {
        id: 'standard-change-fee',
        name: 'Standard change fee',
        priority: 50,
        conditions: {
          bookingStatus: ['confirmed'],
          timeBeforeDeparture: { min: 48 },
        },
        actions: {
          allowed: true,
          requiresApproval: false,
        },
        fees: {
          fixed: 50,
          perItem: true,
        },
      },

      // Rule 4: Non-refundable tickets
      {
        id: 'non-refundable',
        name: 'Non-refundable ticket restrictions',
        priority: 80,
        conditions: {
          ticketTypes: ['non-refundable'],
        },
        actions: {
          allowed: true,
          requiresApproval: false,
        },
        fees: {
          fixed: 0, // No fee, but no refund either
        },
      },

      // Rule 5: Flexible tickets
      {
        id: 'flexible',
        name: 'Flexible ticket benefits',
        priority: 70,
        conditions: {
          ticketTypes: ['flexible', 'premium'],
        },
        actions: {
          allowed: true,
          requiresApproval: false,
        },
        fees: {
          fixed: 0, // No change fee
        },
      },

      // Rule 6: Flight-specific rules
      {
        id: 'flight-changes',
        name: 'Flight change rules',
        priority: 85,
        conditions: {
          productTypes: ['flight'],
        },
        actions: {
          allowed: true,
        },
        fees: {
          supplierRule: true, // Use airline's rules
        },
      },
    ];
  }
}
```

---

## Price Difference Handling

### Price Adjustment

```typescript
// ============================================================================
// PRICE DIFFERENCE HANDLING
// ============================================================================

interface PriceAdjustment {
  originalTotal: number;
  newTotal: number;
  difference: number;
  changeFee: number;
  refundAmount: number;
  additionalPayment: number;

  // Breakdown by item
  items: ItemPriceAdjustment[];
}

interface ItemPriceAdjustment {
  itemId: string;
  itemName: string;
  originalPrice: number;
  newPrice: number;
  difference: number;
}

class PriceAdjustmentCalculator {
  async calculateAdjustment(
    booking: Booking,
    request: ModificationRequest
  ): Promise<PriceAdjustment> {
    const items: ItemPriceAdjustment[] = [];
    let originalTotal = 0;
    let newTotal = 0;

    for (const change of request.changes) {
      const item = booking.items.find(i => i.id === change.itemId);
      if (!item) continue;

      const originalPrice = item.pricing.total;
      let newPrice = originalPrice;

      // Calculate new price based on change type
      switch (change.type) {
        case 'date':
          newPrice = await this.calculateDateChangePrice(item, change.to);
          break;

        case 'upgrade':
        case 'downgrade':
          newPrice = await this.calculateGradeChangePrice(item, change.to);
          break;

        case 'cancel':
          // Calculate refund amount based on cancellation policy
          newPrice = await this.calculateCancellationRefund(item);
          break;
      }

      items.push({
        itemId: item.id,
        itemName: this.getItemName(item),
        originalPrice,
        newPrice,
        difference: newPrice - originalPrice,
      });

      originalTotal += originalPrice;
      newTotal += newPrice;
    }

    // Calculate change fee
    const evaluation = await new ModificationRulesEngine().evaluateModification(request);
    const changeFee = evaluation.totalChangeFee;

    const difference = newTotal - originalTotal;

    return {
      originalTotal,
      newTotal,
      difference,
      changeFee,
      refundAmount: Math.max(0, -difference - changeFee),
      additionalPayment: Math.max(0, difference + changeFee),
      items,
    };
  }

  private async calculateDateChangePrice(
    item: BookingItem,
    toData: Record<string, unknown>
  ): Promise<number> {
    const newDates = toData.dates as DateRange;

    // Get pricing for new dates
    const pricing = await PricingService.calculatePrice({
      productId: item.productId,
      dates: newDates,
      quantity: 1,
    });

    return pricing.total;
  }

  private async calculateGradeChangePrice(
    item: BookingItem,
    toData: Record<string, unknown>
  ): Promise<number> {
    const newRoomType = toData.roomType as string | undefined;
    const newCabinClass = toData.cabinClass as string | undefined;

    // Get pricing for new grade
    const pricing = await PricingService.calculatePrice({
      productId: item.productId,
      dates: item.dates,
      quantity: 1,
      options: {
        roomType: newRoomType,
        cabinClass: newCabinClass,
      },
    });

    return pricing.total;
  }

  private async calculateCancellationRefund(
    item: BookingItem
  ): Promise<number> {
    if (!item.cancellation.allowed) {
      return 0; // Non-refundable
    }

    const now = new Date();

    // Check if past cancellation deadline
    if (item.cancellation.deadline && now > item.cancellation.deadline) {
      // Check penalty
      if (item.cancellation.penalty) {
        if (item.cancellation.penalty.amount) {
          return Math.max(0, item.pricing.total - item.cancellation.penalty.amount);
        }
        if (item.cancellation.penalty.percentage) {
          return item.pricing.total * (1 - item.cancellation.penalty.percentage / 100);
        }
      }

      return 0; // Past deadline, no refund
    }

    // Full refund if before deadline
    return item.pricing.total;
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
}
```

---

## Change Fees & Penalties

### Fee Calculation

```typescript
// ============================================================================
// CHANGE FEES & PENALTIES
// ============================================================================

interface ChangeFeeCalculation {
  baseFee: number;
  additionalFees: AdditionalFee[];
  totalFee: number;
  waived: boolean;
  waiverReason?: string;
}

interface AdditionalFee {
  type: string;
  description: string;
  amount: number;
  supplierId?: string;
}

class ChangeFeeCalculator {
  async calculateChangeFee(
    booking: Booking,
    request: ModificationRequest
  ): Promise<ChangeFeeCalculation> {
    const additionalFees: AdditionalFee[] = [];
    let baseFee = 0;

    // 1. Base change fee from rules engine
    const evaluation = await new ModificationRulesEngine().evaluateModification(request);
    baseFee = evaluation.totalChangeFee;

    // 2. Supplier-specific change fees
    for (const change of request.changes) {
      const item = booking.items.find(i => i.id === change.itemId);
      if (!item) continue;

      const supplierFee = await this.getSupplierChangeFee(item, change);
      if (supplierFee > 0) {
        additionalFees.push({
          type: 'supplier',
          description: `Supplier change fee for ${this.getItemName(item)}`,
          amount: supplierFee,
          supplierId: item.supplierId,
        });
      }
    }

    // 3. Fare difference penalties (for downgrades)
    for (const change of request.changes) {
      if (change.type === 'downgrade') {
        const item = booking.items.find(i => i.id === change.itemId);
        if (!item) continue;

        const penalty = await this.getDowngradePenalty(item);
        if (penalty > 0) {
          additionalFees.push({
            type: 'downgrade_penalty',
            description: `Downgrade penalty for ${this.getItemName(item)}`,
            amount: penalty,
          });
        }
      }
    }

    // 4. Urgent processing fee
    if (request.urgent) {
      additionalFees.push({
        type: 'urgent',
        description: 'Urgent processing fee',
        amount: 25,
      });
    }

    const totalFee = baseFee + additionalFees.reduce((sum, f) => sum + f.amount, 0);

    // Check for fee waivers
    const waived = await this.checkFeeWaiver(booking, request);

    return {
      baseFee,
      additionalFees,
      totalFee: waived ? 0 : totalFee,
      waived,
      waiverReason: waived ? 'Elite status benefit' : undefined,
    };
  }

  private async getSupplierChangeFee(
    item: BookingItem,
    change: ModificationChange
  ): Promise<number> {
    const supplier = await SupplierService.get(item.supplierId);

    if (!supplier.changeFees) {
      return 0;
    }

    // Call supplier API to get change fee
    try {
      const fee = await SupplierService.getChangeFee({
        supplierId: item.supplierId,
        bookingReference: item.supplierReference,
        changeType: change.type,
        changeDetails: change,
      });

      return fee.amount;
    } catch (error) {
      logger.error('Failed to get supplier change fee', {
        supplierId: item.supplierId,
        itemId: item.id,
        error,
      });
      return 0;
    }
  }

  private async getDowngradePenalty(item: BookingItem): Promise<number> {
    // Typically 10-25% of price difference
    return item.pricing.total * 0.10;
  }

  private async checkFeeWaiver(
    booking: Booking,
    request: ModificationRequest
  ): Promise<boolean> {
    // Check customer tier
    const customer = await CustomerService.get(booking.customerId);

    if (customer.tier === 'platinum') {
      return true;
    }

    if (customer.tier === 'gold' && request.type !== 'cancel_partial') {
      return true;
    }

    // Check if first modification
    const previousModifications = await ModificationRequest.find({
      bookingId: booking.id,
      status: 'completed',
    });

    if (previousModifications.length === 0) {
      // First modification free
      return true;
    }

    return false;
  }

  private getItemName(item: BookingItem): string {
    // Same as previous implementation
    return item.type === 'accommodation'
      ? item.accommodation?.name || 'Accommodation'
      : item.type;
  }
}
```

---

## Inventory Re-availability

### Availability Checks for Modifications

```typescript
// ============================================================================
// INVENTORY RE-AVAILABILITY
// ============================================================================

class ModificationInventoryChecker {
  async checkAvailabilityForModification(
    booking: Booking,
    request: ModificationRequest
  ): Promise<AvailabilityCheckResult> {
    const results: ItemAvailabilityResult[] = [];

    for (const change of request.changes) {
      const item = booking.items.find(i => i.id === change.itemId);
      if (!item) {
        results.push({
          itemId: change.itemId,
          available: false,
          reason: 'Item not found',
        });
        continue;
      }

      const result = await this.checkItemAvailability(item, change);
      results.push(result);
    }

    const allAvailable = results.every(r => r.available);
    const alternatives = allAvailable
      ? []
      : await this.findAlternatives(booking, request, results);

    return {
      allAvailable,
      items: results,
      alternatives,
    };
  }

  private async checkItemAvailability(
    item: BookingItem,
    change: ModificationChange
  ): Promise<ItemAvailabilityResult> {
    switch (change.type) {
      case 'date':
        return await this.checkDateChangeAvailability(item, change.to.dates as DateRange);

      case 'upgrade':
        return await this.checkUpgradeAvailability(item, change.to);

      case 'downgrade':
        // Downgrades always available (moving to lower class)
        return {
          itemId: item.id,
          available: true,
        };

      case 'cancel':
        // Cancellations don't need availability
        return {
          itemId: item.id,
          available: true,
        };

      default:
        return {
          itemId: item.id,
          available: false,
          reason: 'Unknown change type',
        };
    }
  }

  private async checkDateChangeAvailability(
    item: BookingItem,
    newDates: DateRange
  ): Promise<ItemAvailabilityResult> {
    const available = await InventoryService.checkAvailability({
      supplierId: item.supplierId,
      productId: item.productId,
      dates: newDates,
      quantity: 1,
    });

    if (!available.available) {
      return {
        itemId: item.id,
        available: false,
        reason: available.reason || 'No availability for requested dates',
      };
    }

    return {
      itemId: item.id,
      available: true,
    };
  }

  private async checkUpgradeAvailability(
    item: BookingItem,
    toData: Record<string, unknown>
  ): Promise<ItemAvailabilityResult> {
    const newRoomType = toData.roomType as string | undefined;
    const newCabinClass = toData.cabinClass as string | undefined;

    // Check if upgrade is available
    const available = await InventoryService.checkAvailability({
      supplierId: item.supplierId,
      productId: item.productId,
      dates: item.dates,
      quantity: 1,
      options: {
        roomType: newRoomType,
        cabinClass: newCabinClass,
      },
    });

    if (!available.available) {
      return {
        itemId: item.id,
        available: false,
        reason: 'Upgrade not available',
      };
    }

    return {
      itemId: item.id,
      available: true,
    };
  }

  private async findAlternatives(
    booking: Booking,
    request: ModificationRequest,
    results: ItemAvailabilityResult[]
  ): Promise<AlternativeOption[]> {
    const alternatives: AlternativeOption[] = [];

    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (result.available) continue;

      const change = request.changes[i];
      const item = booking.items.find(item => item.id === change.itemId);
      if (!item) continue;

      if (change.type === 'date') {
        // Find alternative dates
        const dateAlternatives = await this.findAlternativeDates(item, change.to.dates as DateRange);
        alternatives.push(...dateAlternatives);
      } else if (change.type === 'upgrade') {
        // Find alternative upgrades
        const upgradeAlternatives = await this.findAlternativeUpgrades(item, change.to);
        alternatives.push(...upgradeAlternatives);
      }
    }

    return alternatives;
  }

  private async findAlternativeDates(
    item: BookingItem,
    requestedDates: DateRange
  ): Promise<AlternativeOption[]> {
    const alternatives: AlternativeOption[] = [];

    // Check dates ±3 days
    for (let offset = -3; offset <= 3; offset++) {
      if (offset === 0) continue;

      const newDates = {
        start: addDays(requestedDates.start, offset),
        end: addDays(requestedDates.end, offset),
      };

      const available = await InventoryService.checkAvailability({
        supplierId: item.supplierId,
        productId: item.productId,
        dates: newDates,
        quantity: 1,
      });

      if (available.available) {
        const priceDiff = await this.calculatePriceDifference(item, newDates);

        alternatives.push({
          itemId: item.id,
          type: 'date',
          description: `${offset > 0 ? '+' : ''}${offset} days`,
          value: newDates,
          priceDifference: priceDiff,
        });
      }
    }

    return alternatives;
  }

  private async calculatePriceDifference(
    item: BookingItem,
    newDates: DateRange
  ): Promise<number> {
    const pricing = await PricingService.calculatePrice({
      productId: item.productId,
      dates: newDates,
      quantity: 1,
    });

    return pricing.total - item.pricing.total;
  }
}

interface AvailabilityCheckResult {
  allAvailable: boolean;
  items: ItemAvailabilityResult[];
  alternatives: AlternativeOption[];
}

interface ItemAvailabilityResult {
  itemId: string;
  available: boolean;
  reason?: string;
}

interface AlternativeOption {
  itemId: string;
  type: string;
  description: string;
  value: Record<string, unknown>;
  priceDifference: number;
}
```

---

## Rebooking Flows

### Modification Orchestration

```typescript
// ============================================================================
// MODIFICATION ORCHESTRATION
// ============================================================================

interface ModificationResult {
  success: boolean;
  booking: Booking;
  changes: AppliedChange[];
  priceAdjustment: PriceAdjustment;
  newDocuments: GeneratedDocument[];
  payment: {
    additionalPaymentCollected?: PaymentResult;
    refundProcessed?: RefundResult;
  };
}

class ModificationOrchestrator {
  async processModification(
    request: ModificationRequest
  ): Promise<ModificationResult> {
    const booking = await Booking.findById(request.bookingId);

    // Validate request
    await this.validateRequest(booking, request);

    // Evaluate modification
    const evaluation = await new ModificationRulesEngine().evaluateModification(request);

    if (!evaluation.allowed) {
      throw new ModificationNotAllowedError(evaluation.restrictions[0]?.reason || 'Modification not allowed');
    }

    // Check availability
    const availability = await new ModificationInventoryChecker().checkAvailabilityForModification(
      booking,
      request
    );

    if (!availability.allAvailable && !this.hasCustomerApprovedAlternatives(request)) {
      throw new NoAvailabilityError(availability.alternatives);
    }

    // Calculate price adjustment
    const priceAdjustment = await new PriceAdjustmentCalculator().calculateAdjustment(
      booking,
      request
    );

    // Collect additional payment if needed
    let additionalPaymentCollected: PaymentResult | undefined;
    if (priceAdjustment.additionalPayment > 0) {
      additionalPaymentCollected = await this.collectAdditionalPayment(
        booking,
        priceAdjustment.additionalPayment
      );
    }

    // Process refund if applicable
    let refundProcessed: RefundResult | undefined;
    if (priceAdjustment.refundAmount > 0) {
      refundProcessed = await this.processRefund(
        booking,
        priceAdjustment.refundAmount
      );
    }

    // Apply changes
    const changes = await this.applyChanges(booking, request);

    // Update booking
    booking.status = 'modified';
    booking.state = 'confirmed';
    booking.version += 1;
    booking.updatedAt = new Date();
    await booking.save();

    // Generate new documents
    const newDocuments = await this.generateUpdatedDocuments(booking, changes);

    // Send notifications
    await this.sendModificationNotification(booking, request, priceAdjustment);

    // Record event
    await BookingEvent.create({
      bookingId: booking.id,
      type: 'booking.modified',
      state: booking.state,
      data: {
        modificationId: request.id,
        changes: changes,
        priceAdjustment: priceAdjustment,
      },
      correlationId: request.id,
      actorType: 'system',
      actorId: 'modification-engine',
    });

    return {
      success: true,
      booking,
      changes,
      priceAdjustment,
      newDocuments,
      payment: {
        additionalPaymentCollected,
        refundProcessed,
      },
    };
  }

  private async validateRequest(
    booking: Booking,
    request: ModificationRequest
  ): Promise<void> {
    // Check booking status
    if (booking.status === 'cancelled' || booking.status === 'refunded') {
      throw new InvalidBookingStatusError(booking.status, 'modification');
    }

    // Check modification deadline
    const departure = this.getDepartureDate(booking);
    const hoursUntil = differenceInHours(departure, new Date());

    if (hoursUntil < 24) {
      throw new ModificationDeadlineError();
    }

    // Verify all items exist
    for (const change of request.changes) {
      const item = booking.items.find(i => i.id === change.itemId);
      if (!item) {
        throw new ItemNotFoundError(change.itemId);
      }
    }
  }

  private async collectAdditionalPayment(
    booking: Booking,
    amount: number
  ): Promise<PaymentResult> {
    // Use existing payment method or request new one
    const existingPayment = await BookingPayment.findOne({
      bookingId: booking.id,
      status: 'captured',
    }).sort({ createdAt: -1 });

    if (!existingPayment) {
      throw new PaymentNotFoundError();
    }

    return await PaymentService.charge({
      paymentMethodId: existingPayment.paymentMethodId,
      amount,
      currency: booking.pricing.currency,
      bookingId: booking.id,
      description: `Modification for booking ${booking.reference}`,
    });
  }

  private async processRefund(
    booking: Booking,
    amount: number
  ): Promise<RefundResult> {
    const payments = await BookingPayment.find({
      bookingId: booking.id,
      status: 'captured',
    });

    if (payments.length === 0) {
      throw new PaymentNotFoundError();
    }

    // Refund from most recent payment
    const payment = payments[0];

    return await PaymentService.refund({
      paymentId: payment.paymentId,
      amount: Math.min(amount, payment.amount),
      reason: `Booking modification refund for ${booking.reference}`,
    });
  }

  private async applyChanges(
    booking: Booking,
    request: ModificationRequest
  ): Promise<AppliedChange[]> {
    const applied: AppliedChange[] = [];

    for (const change of request.changes) {
      const item = booking.items.find(i => i.id === change.itemId);
      if (!item) continue;

      const appliedChange = await this.applyItemChange(item, change);
      applied.push(appliedChange);

      await item.save();
    }

    // Recalculate booking total
    await this.recalculateBookingTotal(booking);

    return applied;
  }

  private async applyItemChange(
    item: BookingItem,
    change: ModificationChange
  ): Promise<AppliedChange> {
    const previous = { ...item };

    switch (change.type) {
      case 'date':
        item.dates = change.to.dates as DateRange;
        break;

      case 'guest':
        // Guest changes are handled separately
        break;

      case 'upgrade':
      case 'downgrade':
        if (change.to.roomType) {
          item.accommodation = { ...item.accommodation, roomType: change.to.roomType as string };
        }
        if (change.to.cabinClass) {
          item.flight = { ...item.flight, cabinClass: change.to.cabinClass as string };
        }
        break;

      case 'cancel':
        item.status = 'cancelled';
        item.cancelledAt = new Date();
        break;
    }

    // Get new pricing
    const newPricing = await PricingService.calculatePrice({
      productId: item.productId,
      dates: item.dates,
      quantity: 1,
    });

    item.pricing = newPricing;

    return {
      itemId: item.id,
      type: change.type,
      previous,
      current: item,
    };
  }

  private async recalculateBookingTotal(booking: Booking): Promise<void> {
    const activeItems = booking.items.filter(i => i.status !== 'cancelled');

    const totals = activeItems.reduce(
      (acc, item) => ({
        subtotal: acc.subtotal + item.pricing.baseRate,
        taxes: acc.taxes + item.pricing.taxes,
        fees: acc.fees + item.pricing.fees,
        discount: acc.discount + (item.pricing.discount || 0),
        total: acc.total + item.pricing.total,
      }),
      { subtotal: 0, taxes: 0, fees: 0, discount: 0, total: 0 }
    );

    booking.pricing = {
      ...totals,
      currency: booking.pricing.currency,
    };
  }

  private async generateUpdatedDocuments(
    booking: Booking,
    changes: AppliedChange[]
  ): Promise<GeneratedDocument[]> {
    // Regenerate affected documents
    const affectedItems = changes.map(c => c.itemId);

    const documents: GeneratedDocument[] = [];

    // Regenerate itinerary
    const itinerary = await new DocumentGenerator().generateItinerary(booking);
    documents.push(itinerary);

    // Regenerate item-specific documents for affected items
    for (const itemId of affectedItems) {
      const item = booking.items.find(i => i.id === itemId);
      if (!item || item.status === 'cancelled') continue;

      if (item.type === 'accommodation') {
        const voucher = await new DocumentGenerator().generateHotelVoucher(booking, item);
        documents.push(voucher);
      } else if (item.type === 'flight') {
        const eticket = await new DocumentGenerator().generateETicket(booking, item);
        documents.push(eturket);
      }
    }

    return documents;
  }

  private async sendModificationNotification(
    booking: Booking,
    request: ModificationRequest,
    priceAdjustment: PriceAdjustment
  ): Promise<void> {
    const template = await EmailTemplate.get('booking-modified');

    await EmailService.send({
      to: booking.customerInfo.primary.email,
      subject: template.renderSubject({ reference: booking.reference }),
      html: template.renderBody({
        customerName: booking.customerInfo.primary.firstName,
        reference: booking.reference,
        changes: request.changes,
        priceAdjustment,
      }),
    });
  }

  private getDepartureDate(booking: Booking): Date {
    // Find earliest date across all items
    return booking.items.reduce((earliest, item) => {
      return item.dates.start < earliest ? item.dates.start : earliest;
    }, booking.items[0].dates.start);
  }

  private hasCustomerApprovedAlternatives(request: ModificationRequest): boolean {
    return request.metadata?.alternativesApproved === true;
  }
}

interface AppliedChange {
  itemId: string;
  type: string;
  previous: Record<string, unknown>;
  current: Record<string, unknown>;
}
```

---

## Modification Limits

### Restriction Enforcement

```typescript
// ============================================================================
// MODIFICATION LIMITS
// ============================================================================

interface ModificationLimits {
  maxModifications: number;
  maxDateChanges: number;
  maxGuestChanges: number;
  timeLimits: {
    minHoursBeforeDeparture: number;
    maxModificationsPerDay: number;
  };
}

class ModificationLimitsChecker {
  private limits: ModificationLimits = {
    maxModifications: 10,
    maxDateChanges: 3,
    maxGuestChanges: 2,
    timeLimits: {
      minHoursBeforeDeparture: 24,
      maxModificationsPerDay: 3,
    },
  };

  async checkLimits(
    booking: Booking,
    request: ModificationRequest
  ): Promise<LimitCheckResult> {
    const violations: LimitViolation[] = [];

    // Check total modifications
    const totalModifications = await this.countModifications(booking.id);
    if (totalModifications >= this.limits.maxModifications) {
      violations.push({
        type: 'max_modifications',
        limit: this.limits.maxModifications,
        current: totalModifications,
        message: `Maximum ${this.limits.maxModifications} modifications allowed`,
      });
    }

    // Check date changes
    if (request.type === 'change_dates') {
      const dateChanges = await this.countModificationsByType(booking.id, 'change_dates');
      if (dateChanges >= this.limits.maxDateChanges) {
        violations.push({
          type: 'max_date_changes',
          limit: this.limits.maxDateChanges,
          current: dateChanges,
          message: `Maximum ${this.limits.maxDateChanges} date changes allowed`,
        });
      }
    }

    // Check guest changes
    if (request.type === 'change_guests') {
      const guestChanges = await this.countModificationsByType(booking.id, 'change_guests');
      if (guestChanges >= this.limits.maxGuestChanges) {
        violations.push({
          type: 'max_guest_changes',
          limit: this.limits.maxGuestChanges,
          current: guestChanges,
          message: `Maximum ${this.limits.maxGuestChanges} guest changes allowed`,
        });
      }
    }

    // Check time before departure
    const departure = this.getDepartureDate(booking);
    const hoursUntil = differenceInHours(departure, new Date());
    if (hoursUntil < this.limits.timeLimits.minHoursBeforeDeparture) {
      violations.push({
        type: 'too_close_to_departure',
        limit: this.limits.timeLimits.minHoursBeforeDeparture,
        current: hoursUntil,
        message: `Modifications not allowed within ${this.limits.timeLimits.minHoursBeforeDeparture}h of departure`,
      });
    }

    // Check modifications per day
    const todayModifications = await this.countModificationsToday(booking.id);
    if (todayModifications >= this.limits.timeLimits.maxModificationsPerDay) {
      violations.push({
        type: 'max_daily_modifications',
        limit: this.limits.timeLimits.maxModificationsPerDay,
        current: todayModifications,
        message: `Maximum ${this.limits.timeLimits.maxModificationsPerDay} modifications per day`,
      });
    }

    return {
      allowed: violations.length === 0,
      violations,
    };
  }

  private async countModifications(bookingId: string): Promise<number> {
    return await ModificationRequest.countDocuments({
      bookingId,
      status: { $in: ['completed', 'processing'] },
    });
  }

  private async countModificationsByType(
    bookingId: string,
    type: ModificationType
  ): Promise<number> {
    return await ModificationRequest.countDocuments({
      bookingId,
      type,
      status: { $in: ['completed', 'processing'] },
    });
  }

  private async countModificationsToday(bookingId: string): Promise<number> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return await ModificationRequest.countDocuments({
      bookingId,
      status: { $in: ['completed', 'processing'] },
      createdAt: { $gte: today },
    });
  }

  private getDepartureDate(booking: Booking): Date {
    return booking.items.reduce((earliest, item) => {
      return item.dates.start < earliest ? item.dates.start : earliest;
    }, booking.items[0].dates.start);
  }
}

interface LimitCheckResult {
  allowed: boolean;
  violations: LimitViolation[];
}

interface LimitViolation {
  type: string;
  limit: number;
  current: number;
  message: string;
}
```

---

**Next:** [Cancellations & Refunds](./BOOKING_ENGINE_06_CANCELLATIONS.md) — Cancellation flows, refund processing, and penalties
