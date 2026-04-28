# Customer Self-Service — Booking Management & Modifications

> Research document for customer-initiated booking changes, cancellations, and modification requests.

---

## Key Questions

1. **What booking changes can customers initiate without agent involvement?**
2. **How do we present modification options with price impact transparency?**
3. **What's the cancellation flow, and how do refunds work from the customer view?**
4. **How do we prevent conflicting modifications (customer + agent editing simultaneously)?**
5. **What's the notification strategy when a modification is approved/rejected?**

---

## Research Areas

### Modification Types

```typescript
type CustomerModification =
  // Self-service (instant)
  | 'update_contact_info'
  | 'add_dietary_preference'
  | 'upload_passport_copy'
  | 'add_special_request'
  // Agent-assisted (request flow)
  | 'change_dates'
  | 'change_hotel'
  | 'change_flight'
  | 'add_activity'
  | 'remove_activity'
  | 'change_room_type'
  | 'add_traveler'
  | 'remove_traveler'
  | 'upgrade_class'
  | 'change_transfer';

interface ModificationRequest {
  requestId: string;
  tripId: string;
  modificationType: CustomerModification;
  currentDetails: Record<string, unknown>;
  requestedChanges: Record<string, unknown>;
  reason: string;
  priceImpact?: PriceImpact;
  status: 'submitted' | 'under_review' | 'quoted' | 'approved' | 'rejected' | 'completed';
  submittedAt: Date;
  agentResponse?: AgentModificationResponse;
}

interface PriceImpact {
  additionalCost: number;
  refund: number;
  netChange: number;
  currency: string;
  breakdown: PriceImpactItem[];
}

interface PriceImpactItem {
  description: string;
  amount: number;
}
```

### Cancellation Flow

```typescript
interface CancellationFlow {
  tripId: string;
  cancellationPolicy: CancellationPolicy;
  refundEstimate: RefundEstimate;
  steps: CancellationStep[];
}

interface CancellationPolicy {
  freeCancellationUntil: Date;
  cancellationFeePercent: number;
  nonRefundableComponents: string[];
  insuranceCoverage: boolean;
  insuranceClaimAmount?: number;
}

interface RefundEstimate {
  totalPaid: number;
  cancellationFee: number;
  supplierPenalties: number;
  refundAmount: number;
  refundMethod: 'original_payment' | 'credit_note' | 'bank_transfer';
  estimatedProcessingDays: number;
}

// Flow:
// 1. Customer initiates cancellation
// 2. System shows refund estimate with breakdown
// 3. Customer confirms (with 24h cooling-off if > ₹1L refund)
// 4. Agent reviews (within 4 hours)
// 5. Cancellation processed with suppliers
// 6. Refund initiated
// 7. Customer receives confirmation + refund timeline
```

### Conflict Resolution

```typescript
interface ModificationConflict {
  tripId: string;
  source: 'customer_portal' | 'agent_workbench';
  conflictType: 'concurrent_edit' | 'status_mismatch' | 'permission_denied';
  resolution: ConflictResolution;
}

type ConflictResolution =
  | { type: 'agent_priority'; message: string }      // Agent changes win
  | { type: 'customer_priority'; message: string }    // Customer request processed
  | { type: 'queue'; message: string };               // Queued for agent review

// Policy: Agent changes always take priority.
// If agent is actively editing a trip, customer modifications are queued.
// Customer sees: "Your agent is currently updating this trip.
//                 Your request will be processed shortly."
```

---

## Open Problems

1. **Price impact accuracy** — Modification cost estimates are based on current rates, which may change between request and processing. How to handle discrepancies?

2. **Partial cancellations** — Customer wants to cancel the hotel but keep the flight. Partial trip modifications are complex across multiple suppliers.

3. **Group trip modifications** — One traveler in a group wants to cancel. How does this affect shared bookings (shared room, group transfer)?

4. **Modification history** — Customer modifies, then wants to revert. Need to track modification chains and support undo within a window.

5. **Supplier modification policies** — Each supplier has different modification rules. Presenting this clearly to customers without overwhelming them is challenging.

---

## Next Steps

- [ ] Design modification request UI with price impact preview
- [ ] Map cancellation policies per supplier and service type
- [ ] Design cancellation flow with refund estimate calculator
- [ ] Study self-service modification patterns (airline change flows)
- [ ] Design concurrent edit conflict resolution UX
