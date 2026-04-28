# Refund & Cancellation Management — Modification & Rebooking

> Research document for booking modifications, date changes, and rebooking workflows.

---

## Key Questions

1. **What types of modifications do customers commonly request?**
2. **How do we price modification fees vs. cancellation + rebooking?**
3. **What's the modification workflow for different service types?**
4. **How do modifications affect payments, commissions, and accounting?**
5. **When is it cheaper to cancel and rebook vs. modify?**

---

## Research Areas

### Modification Types

```typescript
type ModificationType =
  // Date changes
  | 'date_change'                    // Move travel dates
  | 'extension'                      // Add nights/days
  | 'shortening'                     // Reduce nights/days
  // Traveler changes
  | 'traveler_add'                   // Add a traveler
  | 'traveler_remove'                // Remove a traveler
  | 'traveler_name_change'           // Correct name on booking
  // Service changes
  | 'hotel_upgrade'                  // Change to better hotel
  | 'hotel_downgrade'                // Change to cheaper hotel
  | 'room_change'                    // Different room type
  | 'flight_change'                  // Different flight/time
  | 'activity_swap'                  // Replace one activity with another
  | 'activity_add'                   // Add new activity
  | 'activity_remove'                // Remove activity
  | 'transfer_change'                // Change transfer details
  // Add-on changes
  | 'insurance_upgrade'              // Better coverage
  | 'meal_plan_change'               // Different meal plan
  | 'special_request';               // Wheelchair, early check-in, etc.

interface ModificationRequest {
  requestId: string;
  tripId: string;
  requestedBy: 'customer' | 'agent';
  modifications: Modification[];
  status: ModificationStatus;
  costImpact: CostImpact;
  approvalRequired: boolean;
}

interface Modification {
  type: ModificationType;
  targetItemId: string;
  currentValue: unknown;
  proposedValue: unknown;
  fee: Money;
  priceDifference: Money;
  supplierApproval: boolean;
}

interface CostImpact {
  additionalCharge: Money;           // Extra amount customer pays
  refundDue: Money;                  // Amount refunded to customer
  netImpact: Money;                  // Positive = customer pays more
  commissionAdjustment: Money;       // Change in agent commission
  feeBreakdown: ModificationFee[];
}

// Modification cost comparison:
// Option A: Modify existing booking
//   Date change fee: ₹2,500 × 2 passengers = ₹5,000
//   Price difference (new dates): +₹3,000
//   Total: ₹8,000 additional
//
// Option B: Cancel and rebook
//   Cancellation penalty: ₹5,000 × 2 = ₹10,000
//   New booking at current rate: ₹1,03,000
//   Original booking: ₹1,00,000
//   Total: ₹13,000 additional
//
// Recommendation: Option A (modify) saves ₹5,000
```

### Modification Workflow by Service

```typescript
interface ModificationWorkflow {
  serviceType: ServiceType;
  allowedModifications: AllowedModification[];
  processSteps: ProcessStep[];
  timeline: string;
}

// Modification workflows by service:

// FLIGHT MODIFICATIONS:
// Name correction: Minor spelling fix (free), legal name change (fee + reissue)
// Date change: Depends on fare class
//   Flexible fare: Free change + fare difference
//   Standard fare: ₹2,500 change fee + fare difference
//   Non-refundable: No changes allowed (cancel + rebook only)
// Route change: Treat as cancel + new booking
// Meal/seat change: Free (if available), via airline portal

// HOTEL MODIFICATIONS:
// Date change: Subject to availability, may change rate
// Room type: Upgrade (pay difference) or downgrade (partial refund)
// Add nights: Subject to availability at current rate
// Remove nights: Subject to hotel's minimum stay policy
// Guest name: Usually free with 24+ hours notice
// Special requests: Free but not guaranteed

// ACTIVITY MODIFICATIONS:
// Date change: Free if 48+ hours before, no change if <24 hours
// Activity swap: Treated as cancel + new booking
// Add participants: Subject to availability
// Remove participants: Partial refund per activity policy

// Modification approval matrix:
// Change < ₹1,000 → Agent can approve
// Change ₹1,000-10,000 → Agent can approve, customer confirmation required
// Change ₹10,000-50,000 → Team lead approval
// Change > ₹50,000 → Manager approval
// Date changes during peak season → Manager approval regardless of amount
```

### Rebooking Optimization

```typescript
interface RebookingAnalysis {
  originalBooking: BookingSnapshot;
  proposedChanges: Modification[];
  options: RebookingOption[];
  recommendation: RebookingRecommendation;
}

interface RebookingOption {
  optionType: 'modify' | 'cancel_rebook' | 'partial_cancel';
  totalCost: Money;
  savings: Money;                    // Compared to most expensive option
  pros: string[];
  cons: string[];
  steps: string[];
}

interface RebookingRecommendation {
  bestOption: string;
  reason: string;
  savings: Money;
  riskLevel: 'low' | 'medium' | 'high';
}

// Rebooking scenarios:
//
// Scenario 1: Customer wants to add 1 night to 4-night Singapore trip
//   Option A (Extend): Add night at same hotel → ₹8,500 + ₹0 fee
//   Option B (New booking): Book the extra night separately → ₹9,000
//   → Recommend Option A (save ₹500, same room)
//
// Scenario 2: Customer wants to change from 3-star to 5-star hotel
//   Option A (Modify): Upgrade fee + rate difference → ₹25,000 additional
//   Option B (Cancel + rebook): Penalty ₹8,000 + new 5-star rate → ₹30,000 additional
//   → Recommend Option A (save ₹5,000)
//
// Scenario 3: Customer wants to move dates by 3 weeks
//   Option A (Date change): ₹5,000 change fee + ₹12,000 fare difference = ₹17,000
//   Option B (Cancel + rebook): ₹10,000 penalty + ₹1,08,000 new booking = ₹18,000 total extra
//   → Recommend Option A (save ₹1,000)
```

### Modification Accounting

```typescript
interface ModificationAccounting {
  originalBooking: Money;
  modificationFee: Money;
  priceDifference: Money;
  newTotal: Money;
  commissionAdjustment: Money;
  paymentDue: Money;                 // Additional payment from customer
  refundDue: Money;                  // Refund to customer
}

// Accounting impact:
// Original booking: ₹1,00,000 (Commission: ₹10,000 at 10%)
// Modification: Hotel upgrade
//   Modification fee: ₹500 (agency fee)
//   Price difference: +₹15,000 (3-star → 5-star)
//   New total: ₹1,15,500
//   New commission: ₹11,550 (10% on new total)
//   Commission adjustment: +₹1,550
//   Customer pays: ₹15,500 additional
//
// Accounting entries:
//   Debit: Customer Receivable ₹15,500
//   Credit: Revenue (Agency Fee) ₹500
//   Credit: Revenue (Markup) ₹15,000
//   Debit: Agent Commission Payable ₹1,550

// Invoice handling:
// Option A: Supplementary invoice for the difference
// Option B: Revised invoice replacing the original
// Option C: Credit note for original + new invoice for modified booking
// → India GST: Option A (supplementary invoice) is standard practice
```

---

## Open Problems

1. **Modification cascade** — Changing flight dates affects hotel check-in/out, transfer timing, and activity availability. Modifying one component triggers changes across the trip.

2. **Real-time pricing** — Modification uses current prices, not original booking prices. If prices have increased significantly, the modification cost surprises the customer.

3. **Supplier modification fees** — Each supplier has different modification fees. Some charge per change, some per passenger. The fee structure is opaque to agents.

4. **Modification limits** — How many times can a customer modify? Some airlines allow 1 free change, then charge. Tracking modification count per booking is needed.

5. **Partial group modification** — 2 of 4 travelers want to change dates. The group booking was at a group rate. Splitting the group may increase per-person cost for the remaining 2.

---

## Next Steps

- [ ] Design modification request workflow with cost comparison
- [ ] Build rebooking optimization engine (modify vs. cancel-rebook)
- [ ] Create modification accounting entries for GST compliance
- [ ] Design modification cascade detection for multi-component trips
- [ ] Study modification UX (MakeMyTrip date change, Booking.com modify booking)
