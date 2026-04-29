# Travel Package Lifecycle 03: Booking Lifecycle

> Research document for the complete package booking lifecycle, inventory management, group bookings, waitlists, amendments, and cancellations in Indian travel agency context.

---

## Document Overview

**Focus:** End-to-end booking lifecycle from inquiry to completion
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

1. **What are the distinct stages of a package booking from inquiry through post-tour?**
2. **How do we manage inventory allocation and blocking for fixed-departure packages?**
3. **What are departure guarantee rules and how do cancellation policies vary by timing?**
4. **How do group bookings differ from individual bookings in workflow and pricing?**
5. **How do we implement waitlist management that is fair and efficient?**
6. **What booking amendments are possible at each stage and what are the cost implications?**
7. **How do partial cancellations work when some members of a group cancel?**

---

## Research Areas

### A. Booking Lifecycle Stages

```typescript
// Research-level model — not final

type BookingStage =
  | 'inquiry'              // Customer asks about a package
  | 'quotation'            // Agent sends a quote
  | 'hold'                 // Temporary inventory hold
  | 'deposit_paid'         // Initial payment received
  | 'confirmed'            // Booking confirmed with suppliers
  | 'documents_pending'    // Awaiting vouchers, tickets
  | 'voucher_issued'       // Travel documents delivered
  | 'pre_departure'        // Final briefing, last payments
  | 'in_travel'            // Customer is traveling
  | 'completed'            // Trip completed successfully
  | 'cancelled'            // Booking cancelled
  | 'no_show';             // Customer did not show up

interface PackageBooking {
  id: string;                             // "PKG-2026-00456"
  packageId: string;
  variantId?: string;
  departureId?: string;                   // For fixed-departure

  // Booking parties
  leadTraveler: TravelerInfo;
  travelers: TravelerInfo[];              // All travelers
  bookingAgent: string;                   // Agent who booked
  source: BookingSource;

  // Timeline
  stage: BookingStage;
  stageHistory: StageTransition[];
  inquiryDate: Date;
  quotationDate?: Date;
  holdDate?: Date;
  bookingDate?: Date;                     // When deposit paid
  confirmationDate?: Date;
  travelStartDate: Date;
  travelEndDate: Date;

  // Financial
  pricing: BookingPricing;
  payments: PaymentRecord[];
  paymentSchedule: PaymentSchedule;

  // Travel details
  departureCity: string;
  roomAllocation: RoomAllocation[];
  specialRequests: SpecialRequest[];
  dietaryRequirements: string[];

  // Documents
  vouchers: Voucher[];
  tickets: Ticket[];
  itinerary: ItineraryDocument;

  // Post-travel
  feedbackId?: string;
  completedDate?: Date;
}

type BookingSource =
  | 'walk_in'
  | 'phone_call'
  | 'whatsapp'
  | 'website'
  | 'ota_makemytrip'
  | 'ota_yatra'
  | 'referral'
  | 'repeat_customer'
  | 'storefront'
  | 'travel_expo';

interface StageTransition {
  from: BookingStage;
  to: BookingStage;
  timestamp: Date;
  actor: string;                          // Agent ID or "system"
  reason?: string;
  notes?: string;
}
```

**Booking Lifecycle Diagram:**

```
INQUIRY ──► QUOTATION ──► HOLD ──► DEPOSIT_PAID ──► CONFIRMED ──► VOUCHER_ISSUED
   │            │           │           │                │               │
   │            │           │           │                │               │
   │            │           └──► EXPIRED (hold timeout)  │               │
   │            │                       │                │               │
   │            └──► LOST (customer declined)            │               │
   │                                    │                │               │
   └──► LOST (no response)             │                │               │
                                        │                │               │
                                     CANCELLED ◄─────────┘               │
                                     (with refund as per policy)         │
                                                                             │
                        PRE_DEPARTURE ◄────────────────────────────────────┘
                              │
                              ▼
                         IN_TRAVEL
                              │
                              ▼
                         COMPLETED
                              │
                              ▼
                        FEEDBACK_COLLECTED
                              │
                              ▼
                         ARCHIVED
```

### B. Inquiry & Quotation Stage

```typescript
interface PackageInquiry {
  id: string;
  packageId?: string;                    // May not know exact package yet
  customerName: string;
  contactInfo: ContactInfo;

  // Requirements
  destination?: string;
  travelDates?: DateRange;
  travelerCount: number;
  travelerComposition: string;           // "2 adults, 1 child (8 years)"
  budget?: PriceRange;
  specialRequirements?: string[];

  // Source tracking
  source: BookingSource;
  assignedAgent?: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';

  // Timeline
  createdAt: Date;
  respondedAt?: Date;
  quotationSentAt?: Date;

  // Outcome
  status: 'open' | 'quoted' | 'converted' | 'lost' | 'expired';
  lostReason?: string;                   // "Price too high", "Went with competitor"
}

interface PackageQuotation {
  id: string;
  inquiryId: string;
  packageId: string;
  variantId?: string;
  departureId?: string;

  // Quoted pricing
  pricing: CalculatedPrice;              // From PACKAGE_02_PRICING engine
  priceValidity: DateRange;              // Quote valid for 7 days

  // Inclusions summary (from catalog)
  includedItems: string[];
  excludedItems: string[];
  optionalAddOns: QuotedAddOn[];

  // Terms
  paymentTerms: QuotedPaymentTerms;
  cancellationPolicy: CancellationPolicy;
  bookingDeadline: Date;                 // "Book by [date] to hold this price"

  // Customization notes
  customizationNotes?: string;           // Agent notes on modifications
  alternatives?: AlternativeQuote[];     // "Also consider this similar package"
}

interface QuotedPaymentTerms {
  depositAmount: Money;
  depositPercent: number;                // 20%
  depositDueBy: Date;
  balanceAmount: Money;
  balanceDueDate: Date;                  // Typically 30-45 days before travel
  installmentSchedule?: InstallmentSchedule[];
  acceptedPaymentMethods: PaymentMethod[];
}

type PaymentMethod =
  | 'upi'
  | 'credit_card'
  | 'debit_card'
  | 'net_banking'
  | 'bank_transfer_neft'
  | 'bank_transfer_rtgs'
  | 'bank_transfer_imps'
  | 'cheque'
  | 'cash'
  | 'emi'
  | 'wallet';                            // PayTM, PhonePe, etc.
```

### C. Inventory Allocation & Blocking

```typescript
// For fixed-departure packages, inventory must be managed carefully
// Seats/rooms are allocated from a finite pool

interface InventoryAllocation {
  departureId: string;
  componentType: 'seat' | 'room' | 'activity_slot';
  totalInventory: number;
  allocated: AllocationBucket[];

  // Blocking rules
  holdRules: InventoryHoldRules;
  overbookingPolicy: OverbookingPolicy;
}

interface AllocationBucket {
  bucket: AllocationBucketType;
  count: number;
  booked: number;
  held: number;
  available: number;
}

type AllocationBucketType =
  | 'guaranteed'           // Confirmed bookings
  | 'agency_hold'          // Agency blocked for expected clients
  | 'ota_hold'             // OTA allocation
  | 'waitlist'             // Waitlisted bookings
  | 'buffer';              // Emergency/buffer inventory

// Inventory allocation example:
//
// Kerala Backwaters, Dec 15 departure, Coach (20 seats)
//
// | Bucket       | Count | Booked | Held | Available |
// |-------------|-------|--------|------|-----------|
// | Guaranteed   | 16    | 12     | 2    | 2         |
// | Agency Hold  | 2     | 0      | 2    | 0         |
// | OTA Hold     | 2     | 1      | 1    | 0         |
// | Buffer       | 0     | 0      | 0    | 0         |
// |─────────────|───────|────────|──────|───────────|
// | Total        | 20    | 13     | 5    | 2         |
//
// Only 2 seats available for new bookings
// Waitlist: 3 people waiting

interface InventoryHoldRules {
  // How long can inventory be held without payment?
  defaultHoldDuration: number;           // 24 hours
  maxHoldDuration: number;               // 48 hours with manager approval

  // Hold extensions
  extensionAllowed: boolean;
  maxExtensions: number;                  // 1
  extensionDuration: number;             // 12 hours each

  // Auto-release
  autoRelease: boolean;
  releaseReminderBefore: number;         // Notify 2 hours before release
  releaseNotification: string[];         // Who gets notified

  // Hold deposit (optional)
  holdDepositRequired: boolean;
  holdDepositAmount?: Money;             // ₹5,000 non-refundable to hold
  holdDepositAdjustable: boolean;        // Adjusted against booking amount
}

// Hold lifecycle:
//
// AGENT REQUESTS HOLD
//    │
//    ├── Inventory available → HOLD_GRANTED (24h timer starts)
//    │       │
//    │       ├── Customer pays deposit → HOLD_CONVERTED → CONFIRMED
//    │       │
//    │       ├── Agent requests extension → EXTENDED (+12h, max 1x)
//    │       │       │
//    │       │       └── No payment → HOLD_RELEASED
//    │       │
//    │       └── Timer expires → HOLD_RELEASED → Inventory freed
//    │
//    └── Inventory not available → HOLD_DENIED
//            │
//            └── Offer waitlist → WAITLISTED

interface OverbookingPolicy {
  allowed: boolean;
  maxOverbookingPercent: number;         // Typically 5-10%
  rationale: string;                     // "Historical no-show rate is 8%"
  autoDowngrade: boolean;                // Auto-downgrade if overbooked
  compensationPolicy?: string;           // What if downgrade happens
}
```

### D. Departure Guarantee & Cancellation Policies

```typescript
interface DepartureGuarantee {
  departureId: string;
  packageId: string;

  // Guarantee rules
  guaranteedDeparture: boolean;          // Always runs?
  minimumPaxToGuarantee: number;
  currentBookingCount: number;
  isGuaranteed: boolean;                 // Has min pax been reached?

  // Guarantee timeline
  guaranteeDecisionDate: Date;           // When we decide if trip runs
  latestCancellationDate: Date;          // Latest we can cancel

  // Customer protection
  ifNotGuaranteed: NotGuaranteedAction;
  fullRefundIfCancelled: boolean;
  alternativeOffered: boolean;
}

type NotGuaranteedAction =
  | 'cancel_full_refund'    // Cancel and refund everything
  | 'offer_alternative'     // Offer different dates or package
  | 'run_anyway'            // Run even below minimum (loss for agency)
  | 'upgrade_pax';          // Upgrade remaining pax to higher tier

// Standard cancellation policy (Indian travel industry):
//
// | Days before departure | Cancellation charge | Refund    |
// |----------------------|--------------------| ---------|
// | 60+ days             | Deposit only        | Balance   |
// | 45-59 days           | 25% of package      | 75%       |
// | 30-44 days           | 50% of package      | 50%       |
// | 15-29 days           | 75% of package      | 25%       |
// | 7-14 days            | 90% of package      | 10%       |
// | < 7 days             | 100% (no refund)    | 0%        |
// | No show              | 100% (no refund)    | 0%        |

interface CancellationPolicy {
  policyId: string;
  packageId: string;

  // Policy tiers
  tiers: CancellationTier[];

  // Special conditions
  nonRefundableComponents: string[];     // What's never refundable
  thirdPartyCancellationFees: boolean;   // Pass through airline/hotel fees
  insuranceCoveredCancellation: string[]; // Reasons covered by insurance

  // Processing
  processingTimeDays: number;            // 7-15 business days
  refundMethod: 'original_payment' | 'credit_note' | 'bank_transfer';
  refundDeduction: Money;                // Processing fee ₹500
}

interface CancellationTier {
  daysBeforeDeparture: number;           // Minimum days
  chargePercent: number;
  description: string;                   // "25% of package cost retained"
  fixedCharge?: Money;                   // Instead of percentage
  excludes?: string[];                   // "Airfare non-refundable"
}

// Force majeure / pandemic cancellation:
interface ForceMajeurePolicy {
  triggers: string[];                    // "Government advisory", "Natural disaster"
  refundPolicy: 'full_refund' | 'credit_note_full_value' | 'reschedule_free';
  creditNoteValidity: number;            // 12 months
  rescheduleWindow: number;              // Within 6 months
  documentationRequired: string[];       // Government advisory link
}
```

### E. Group Booking Management

```typescript
// Group bookings: 6+ travelers, often complex room allocation and payment splitting

interface GroupBooking extends PackageBooking {
  isGroupBooking: true;
  groupSize: number;

  // Group leader / coordinator
  groupLeader: TravelerInfo;
  coordinatorContact: ContactInfo;       // May differ from leader

  // Room allocation
  rooms: RoomAllocation[];

  // Individual payments
  individualPayments: IndividualPayment[];

  // Group-specific terms
  groupContract?: GroupContract;
  groupDiscountApplied: boolean;
  discountAmount: Money;
}

interface RoomAllocation {
  roomNumber: number;
  roomType: 'double' | 'twin' | 'triple' | 'quad' | 'family_suite';
  occupancy: RoomOccupancy;
  travelers: string[];                   // Traveler IDs in this room
  specialRequest?: string;               // "Connecting room", "Ground floor"
  extraBed: boolean;
  childBed: boolean;
}

interface IndividualPayment {
  travelerId: string;
  travelerName: string;
  shareAmount: Money;                    // This person's share
  paidAmount: Money;
  outstandingAmount: Money;
  paymentStatus: 'pending' | 'partial' | 'paid' | 'overdue';
  payments: PaymentRecord[];
}

interface GroupContract {
  contractDate: Date;
  agreedPrice: Money;                    // Per person or total
  includedItems: string[];
  exclusions: string[];
  paymentSchedule: PaymentSchedule;
  cancellationTerms: string;
  minimumGroupSize: number;
  freeLeaderPolicy?: FreeLeaderPolicy;   // "1 free for every 15 paying"
  roomingListDeadline: Date;
  finalPaymentDeadline: Date;
}

interface FreeLeaderPolicy {
  enabled: boolean;
  ratio: string;                         // "1:15" = 1 free per 15 paying
  maxFreeLeaders: number;
  freeLeaderInclusions: string[];        // What's free vs. excluded
}

// Group booking flow:
//
// 1. GROUP INQUIRY
//    - Agent receives inquiry (school, corporate, family group)
//    - Collects: group size, dates, budget, special needs
//    - Creates group quotation
//
// 2. GROUP CONTRACT
//    - Signed contract between agency and group organizer
//    - Includes payment schedule, rooming list deadline
//    - May include free leader, group discount
//
// 3. ROOMING LIST COLLECTION
//    - Group leader provides room allocations
//    - Agency enters into system
//    - Special requests noted (connecting rooms, ground floor)
//
// 4. PAYMENT COLLECTION
//    - Individual payments tracked separately
//    - Group leader may collect and pay as lump sum
//    - Or each member pays their share directly
//
// 5. FINAL CONFIRMATION
//    - All payments received
//    - Rooming list finalized
//    - Special dietary requirements confirmed
//    - Vouchers generated

// Common Indian group booking scenarios:
//
// SCHOOL TRIP (40 students + 4 teachers):
// - Teacher-student ratio maintained
// - Parent consent forms required
// - Insurance mandatory
// - Special meal arrangements (vegetarian/jain)
// - Safety protocols documented
//
// CORPORATE OFFSITE (25 employees):
// - Company PO required
// - GST invoice with company GSTIN
// - Meeting room included
// - AV equipment, projector
// - Team building activities
//
// FAMILY WEDDING GROUP (30-50 pax):
// - Multiple room types needed
// - Event venue coordination
// - Catering customization
// - Airport transfers in bulk
// - Individual arrivals/departures
//
// PILGRIMAGE GROUP (50+ pax):
// - Coach transport
// - Vegetarian meals only
// - Pandit/priest arrangements
// - Registration with authorities (Amarnath)
// - Medical fitness certificates
```

### F. Waitlist Management

```typescript
interface WaitlistEntry {
  id: string;
  packageId: string;
  departureId: string;

  // Party
  leadTraveler: string;
  partySize: number;                     // 2 adults + 1 child = 3
  contactInfo: ContactInfo;

  // Waitlist position
  position: number;                      // 1st, 2nd, 3rd in line
  waitlistedAt: Date;
  priority: WaitlistPriority;

  // Status
  status: WaitlistStatus;
  offeredAt?: Date;
  offerExpiresAt?: Date;
  convertedToBooking?: string;           // Booking ID if converted

  // Preferences
  acceptableAlternatives?: string[];     // Other departures/packages
  maxWaitDays?: number;                  // Willing to wait 14 days
}

type WaitlistPriority =
  | 'normal'
  | 'repeat_customer'
  | 'vip'
  | 'large_group';                       // Prioritize filling multiple seats

type WaitlistStatus =
  | 'waiting'
  | 'offered'
  | 'accepted'
  | 'declined'
  | 'expired'
  | 'converted';

// Waitlist processing rules:
//
// 1. FIFO with priority overrides
//    - Normal: First-in, first-out
//    - Repeat customers get +1 priority boost
//    - Large groups (>4) may fill multiple seats at once
//
// 2. When seats become available:
//    a. Cancellation frees N seats
//    b. System checks waitlist in order
//    c. First entry that fits (party size ≤ available seats)
//    d. If party size > available: skip or offer partial
//    e. Send notification: "2 seats available. Accept within 4 hours?"
//    f. If no response: move to next in line
//
// 3. Fairness rules:
//    - Cannot skip line by calling agent directly (audited)
//    - Priority overrides documented and approved by manager
//    - Waitlist position visible to customer
//    - Estimated wait time shown (based on historical data)
//
// 4. Offer expiry:
//    - Standard: 4 hours to respond
//    - Last minute (< 14 days): 2 hours
//    - Urgent (< 3 days): 1 hour
//    - No response = decline, move to next

interface WaitlistConfig {
  maxWaitlistSize: number;               // Per departure
  offerExpiryHours: number;
  reminderBeforeExpiry: number;          // Minutes
  autoExpireDays: number;                // Auto-remove after 30 days
  allowPartialAcceptance: boolean;       // Accept fewer seats than requested?
  notificationChannels: NotificationChannel[];
}

type NotificationChannel =
  | 'whatsapp'
  | 'sms'
  | 'email'
  | 'phone_call'
  | 'app_push';
```

**Waitlist UI Mockup:**

```
+-------------------------------------------------------------------+
| Waitlist: Kerala Backwaters, Dec 15 Departure                      |
+-------------------------------------------------------------------+
|                                                                    |
| Position: #2 (1 party ahead of you)                               |
| Party: 2 adults                                                    |
| Waitlisted: Oct 15, 2026                                          |
|                                                                    |
| Availability Status:                                               |
| ┌─────────────────────────────────────────────────────────────┐   |
| │ Total seats: 20   Booked: 18   Available: 2                 │   |
| │ ████████████████████████████████████████████░░ 90% full     │   |
| └─────────────────────────────────────────────────────────────┘   |
|                                                                    |
| Estimated wait: Moderate (based on cancellation history)           |
| Historical: 70% chance of seat opening in next 21 days            |
|                                                                    |
| Alternative departures with availability:                          |
| • Dec 22 departure: 4 seats available → [Switch to this]          |
| • Jan 5 departure:  8 seats available → [Switch to this]          |
|                                                                    |
| [Stay on Waitlist] [Switch to Alternative] [Cancel Waitlist]      |
+-------------------------------------------------------------------+
```

### G. Booking Amendments & Modifications

```typescript
interface BookingAmendment {
  id: string;
  bookingId: string;
  requestedAt: Date;
  requestedBy: string;                   // Traveler or agent
  approvedBy?: string;                   // Manager for significant changes

  // Amendment details
  amendmentType: AmendmentType;
  changes: AmendmentChange[];
  status: AmendmentStatus;

  // Financial impact
  priceImpact?: Money;                   // +₹3,500 or -₹2,000
  refundDue?: Money;
  additionalPayment?: Money;
  amendmentFee?: Money;                  // Agency may charge amendment fee

  // Supplier coordination
  supplierNotifications: SupplierNotification[];
}

type AmendmentType =
  | 'date_change'                       // Change travel dates
  | 'traveler_add'                       // Add a traveler
  | 'traveler_remove'                    // Remove a traveler
  | 'traveler_name_change'               // Correction or swap
  | 'room_change'                        // Different room type
  | 'variant_upgrade'                    // Standard → Deluxe
  | 'variant_downgrade'                  // Deluxe → Standard
  | 'add_on_service'                     // Add insurance, activity, meal plan
  | 'remove_service'                     // Remove an included service
  | 'departure_city_change'              // Mumbai → Delhi departure
  | 'special_request'                    // Dietary, accessibility
  | 'transfer_change';                   // Shared → private transfer

interface AmendmentChange {
  field: string;                         // "travelDates", "roomType"
  oldValue: string;
  newValue: string;
  supplierImpact: boolean;               // Does supplier need to be notified?
  costImpact: Money;
}

type AmendmentStatus =
  | 'requested'
  | 'approved'
  | 'rejected'
  | 'pending_supplier_confirmation'
  | 'completed'
  | 'cancelled';

// Amendment rules by booking stage:
//
// | Amendment Type       | Inquiry | Quoted | Hold | Deposit | Confirmed | Voucher | Travel |
// |---------------------|---------|--------|------|---------|-----------|---------|--------|
// | Date change         | Free    | Free   | Free | ₹500    | ₹1,000   | ₹2,000  | N/A    |
// | Add traveler        | Free    | Free   | Free | Cost    | Cost+₹500| Cost+₹1K| Hard   |
// | Remove traveler     | Free    | Free   | Free | Refund  | Refund-₹1K| Refund-₹2K| No    |
// | Name change         | Free    | Free   | Free | ₹200    | ₹500      | ₹1,000  | Hard   |
// | Room upgrade        | Free    | Free   | Free | Diff    | Diff+₹500 | Diff+₹1K| Hard   |
// | Variant upgrade     | Free    | Free   | Free | Diff    | Diff+₹500 | Diff+₹1K| N/A    |
// | Add-on service      | N/A     | N/A    | Free | Cost    | Cost+₹300 | Cost+₹500| Hard   |
//
// "Free" = no amendment fee (price difference still applies)
// "Cost" = price difference only
// "Cost+₹X" = price difference + amendment fee
// "Hard" = may be possible but requires operations team involvement
// "N/A" = not applicable at this stage

interface AmendmentPolicy {
  stage: BookingStage;
  amendmentType: AmendmentType;
  allowed: boolean;
  amendmentFee: Money;
  requiresApproval: boolean;
  requiresSupplierConfirmation: boolean;
  deadline?: number;                     // Days before travel
}
```

### H. Partial Cancellation Handling

```typescript
// When some members of a group cancel but others continue

interface PartialCancellation {
  id: string;
  bookingId: string;
  requestedAt: Date;

  // Who is cancelling
  cancelingTravelerIds: string[];
  remainingTravelerIds: string[];

  // Financial
  refundCalculation: PartialCancellationRefund;
  priceAdjustment: RemainingPaxPriceAdjustment;

  // Room reallocation
  roomReallocation: RoomReallocation[];

  // Supplier notifications
  supplierImpact: SupplierImpact[];
}

interface PartialCancellationRefund {
  // Cancellation charges apply per canceling person
  perPersonPackageCost: Money;
  cancellationChargePercent: number;     // Based on days before departure
  cancellationChargePerPerson: Money;
  totalCancellationCharge: Money;
  totalRefundAmount: Money;

  // Non-refundable components
  nonRefundableComponents: string[];     // "Flights (already ticketed)"

  // Deductions
  processingFee: Money;                  // ₹500 per cancellation
  thirdPartyFees: Money;                 // Airline/hotel cancellation fees
}

interface RemainingPaxPriceAdjustment {
  // When travelers cancel, remaining pax may need price adjustment
  // Example: 4 pax in 2 double rooms → 2 pax now need 1 room (same price)
  // But: 3 pax in 1 triple → 2 pax now in double (may be cheaper or need single supp)

  adjustmentRequired: boolean;
  reason: string;                        // "Room occupancy changed from triple to double"
  priceChangePerPerson: Money;           // +₹3,000 (single supplement applies)
  additionalPaymentRequired: boolean;
  newTotalForRemaining: Money;
}

// Partial cancellation scenarios:
//
// SCENARIO 1: Family of 4, 2 cancel
// Original: 2 rooms (2 double), ₹42,000/person, Total: ₹1,68,000
// After: 2 travelers in 1 double room, ₹42,000/person, Total: ₹84,000
// Refund: ₹84,000 - cancellation charges
// Remaining: No price change (still double occupancy)
//
// SCENARIO 2: Couple + friend, friend cancels
// Original: 1 triple room, ₹38,000/person, Total: ₹1,14,000
// After: 2 travelers in 1 double room, ₹42,000/person (upgraded to double rate)
// Refund: ₹38,000 - 25% cancellation = ₹28,500
// Remaining: Now pay ₹84,000 instead of ₹76,000 → additional ₹8,000
// Friend's refund: ₹28,500 - ₹8,000 adjustment = ₹20,500
//
// SCENARIO 3: Group of 10, 2 cancel
// Original: 5 double rooms, group discount 10%, ₹37,800/person
// After: 8 travelers in 4 double rooms
// Group discount still applies? (8 < 10 minimum?)
// If discount removed: price goes up for remaining 8
// Policy decision needed: grandfather discount or not?

interface RoomReallocation {
  originalAllocation: RoomAllocation;
  newAllocation: RoomAllocation;
  reason: string;                        // "Pax reduced from 3 to 2, changed to double"
  priceImpactPerNight: Money;
}

interface SupplierImpact {
  supplierType: string;
  supplierId: string;
  impact: string;                        // "Reduce from 10 rooms to 8"
  cancellationFee?: Money;
  deadline: Date;                        // By when we must notify
}
```

### I. Payment Schedule & Tracking

```typescript
interface PaymentSchedule {
  bookingId: string;
  milestones: PaymentMilestone[];
  totalAmount: Money;
  totalPaid: Money;
  totalOutstanding: Money;
  nextPaymentDue?: PaymentMilestone;
  overduePayments: PaymentMilestone[];
}

interface PaymentMilestone {
  id: string;
  milestoneType: PaymentMilestoneType;
  amount: Money;
  dueDate: Date;
  status: PaymentMilestoneStatus;
  gracePeriodDays: number;               // 3 days grace before overdue
  lateFee?: Money;
  reminderSchedule: ReminderSchedule;
}

type PaymentMilestoneType =
  | 'hold_deposit'         // Non-refundable to hold inventory
  | 'booking_deposit'      // 20-30% at booking
  | 'first_installment'    // 25% at 60 days
  | 'second_installment'   // 25% at 30 days
  | 'final_payment'        // Remaining at 15-30 days before travel
  | 'on_tour_extras';      // Additional charges during travel

type PaymentMilestoneStatus =
  | 'upcoming'
  | 'due'
  | 'overdue'
  | 'paid'
  | 'waived'
  | 'cancelled';

interface ReminderSchedule {
  firstReminder: number;                 // Days before due date
  secondReminder: number;                // Days before due date
  finalReminder: number;                 // Day of due date
  overdueReminder: number;               // Days after due date
  channels: NotificationChannel[];
}

// Payment schedule example:
//
// Kerala Backwaters Deluxe, ₹44,100/person, 2 pax = ₹88,200 total
//
// | Milestone          | Amount   | Due Date     | Status  |
// |-------------------|----------|--------------|---------|
// | Booking deposit   | ₹17,640  | Oct 15 (20%) | Paid    |
// | First installment | ₹26,460  | Nov 15 (30%) | Paid    |
// | Final payment     | ₹44,100  | Nov 30 (50%) | Upcoming|
// |──────────────────|──────────|──────────────|─────────|
// | Total             | ₹88,200  |              |         |
```

---

## Open Problems

1. **Hold abuse prevention** — Agents may hold inventory speculatively, blocking real customers. How do we detect and prevent hold abuse while allowing legitimate holds?

2. **Partial cancellation fairness** — When group members cancel and remaining members' prices increase (occupancy change, lost group discount), who bears the cost? The canceling party or the remaining members?

3. **Name change verification** — Package tickets are non-transferable but name corrections are allowed. Where is the line between correction and transfer? How do we prevent scalping?

4. **Multi-agent booking ownership** — If one agent creates the inquiry and another closes the booking, who gets commission? How do we track and split?

5. **Waitlist for multi-room bookings** — A family needs 2 rooms on the same departure. If only 1 room opens up from the waitlist, do we offer it or wait for both?

6. **Amendment cascading** — Changing travel dates may affect flights (availability), hotels (rates), and activities (seasonal). How do we present the full financial impact before confirming the amendment?

7. **Group payment collection** — For 30-person groups with individual payments, tracking who has paid and chasing overdue payments is operationally intensive. Can we automate this?

8. **OTA booking sync** — Bookings from MakeMyTrip/Yatra may have different cancellation policies than direct bookings. How do we reconcile policy differences?

---

## Next Steps

1. **Map cancellation policies** — Document cancellation policies from top 5 Indian tour operators to establish industry norms
2. **Design waitlist algorithm** — Prototype the waitlist processing algorithm with priority rules and fair position tracking
3. **Group booking workflow research** — Interview agency operations teams about their current group booking management process
4. **Partial cancellation policy** — Define clear rules for price adjustment when group members cancel
5. **Payment schedule templates** — Create standard payment schedule templates for different package types and price ranges
6. **Amendment fee matrix** — Validate the proposed amendment fee structure with agency managers
7. **Hold inventory simulation** — Model hold/release patterns to optimize hold duration and overbooking percentages
8. **Cross-reference with Pricing Engine** — Ensure booking payment schedule integrates with pricing milestones from PACKAGE_02_PRICING.md
9. **Cross-reference with Operations** — Validate that booking stages align with operational handoff points in PACKAGE_04_OPERATIONS.md

---

**Status:** Research exploration, not implementation
**Last Updated:** 2026-04-28
