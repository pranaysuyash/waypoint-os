# Agency Marketplace & Storefront — Direct Booking Engine

> Research document for storefront booking flow, payment processing, confirmation, and booking management.

---

## Key Questions

1. **How do customers book directly from the storefront?**
2. **What payment options are needed for online booking?**
3. **How do we handle provisional vs. confirmed bookings?**
4. **What's the customer communication flow after booking?**
5. **How do we manage booking modifications and cancellations?**

---

## Research Areas

### Booking Flow Architecture

```typescript
interface StorefrontBookingFlow {
  tripId: string;
  customer: CustomerInfo;
  configuration: TripConfiguration;
  pricing: BookingPricing;
  payment: BookingPayment;
  status: BookingStatus;
}

interface TripConfiguration {
  departureDate: Date;
  travelers: TravelerInfo[];
  roomConfiguration: RoomConfig[];
  addons: BookingAddon[];
  specialRequests: string;
}

interface RoomConfig {
  roomType: string;                   // "Standard", "Deluxe", "Luxury"
  occupancy: 'single' | 'double' | 'triple' | 'quad';
  adults: number;
  children: number;
  childAges: number[];
}

// Booking flow (step-by-step):
//
// Step 1: Select Configuration
//   - Choose departure date (calendar with available dates highlighted)
//   - Number of adults and children
//   - Room type and configuration
//   - Add-ons (airport transfer, extra activities, meal plans)
//   - Special requests (dietary, accessibility, celebrations)
//
// Step 2: Traveler Details
//   - Lead traveler: Full name, email, phone, WhatsApp
//   - Co-travelers: Full name, age, gender
//   - Document requirements noted (passport, visa info)
//   - Emergency contact
//   - GST details (for business travelers)
//
// Step 3: Review & Customize
//   - Full itinerary review
//   - Price breakdown
//   - Inclusions/exclusions summary
//   - Terms and conditions acceptance
//   - Cancellation policy acknowledgment
//
// Step 4: Payment
//   - Payment options (see payment section below)
//   - EMI options for high-value bookings
//   - Coupon code / referral discount
//   - Payment split (partial now, balance later)
//
// Step 5: Confirmation
//   - Booking reference number
//   - Provisional or confirmed status
//   - What happens next (timeline)
//   - Download receipt / itinerary
//   - WhatsApp notification

interface BookingStatus {
  current: BookingState;
  history: StatusChange[];
  agentNotified: boolean;
  customerNotified: boolean;
  nextStep: string;
}

type BookingState =
  | 'pending_payment'                 // Customer started booking, payment pending
  | 'provisional'                     // Payment received, awaiting agent confirmation
  | 'confirmed'                       // Agent confirmed all components booked
  | 'partially_confirmed'             // Some components confirmed, some pending
  | 'modification_requested'          // Customer wants changes
  | 'cancelled'                       // Booking cancelled
  | 'completed';                      // Trip completed

// Booking state machine:
// pending_payment → provisional → confirmed → completed
//       ↓              ↓              ↓
//   (expired)    (modification_requested)
//                    ↓              ↓
//               (cancelled)    (cancelled)
//
// Agent confirmation flow:
// Customer books online → Booking is "Provisional"
//   → Agent receives notification in Workbench
//   → Agent checks availability with suppliers
//   → Agent confirms booking (all components available)
//   → OR Agent proposes alternatives (some components unavailable)
//   → OR Agent cancels (trip not feasible, full refund)
//   → Customer notified of final status
//
// Confirmation SLA:
// - Standard trips: Agent confirms within 4 hours
// - Complex trips: Agent confirms within 24 hours
// - If no response: Auto-escalate to agency manager
// - Customer kept informed at each step (WhatsApp + email)
```

### Payment Processing

```typescript
interface BookingPayment {
  totalAmount: Money;
  paymentSchedule: PaymentSchedule;
  methods: PaymentMethod[];
  transactions: PaymentTransaction[];
  refundPolicy: RefundPolicy;
}

interface PaymentSchedule {
  type: PaymentScheduleType;
  installments: PaymentInstallment[];
}

type PaymentScheduleType =
  | 'full_upfront'                    // 100% at booking
  | 'partial_upfront'                 // 20-40% at booking, balance later
  | 'milestone_based'                 // Multiple installments by dates
  | 'pay_later';                      // Book now, pay before departure

// Payment schedule examples:
// Budget trips (< ₹25,000): 100% upfront
// Standard trips (₹25-75,000): 30% now + 70% 15 days before departure
// Premium trips (₹75-2,00,000): 25% now + 25% at 30 days + 50% at 15 days
// Luxury trips (> ₹2,00,000): 20% now + 30% at 60 days + 50% at 30 days
//
// Late payment handling:
// Reminder at 7 days before due date (WhatsApp)
// Reminder at 3 days before (WhatsApp + Email)
// Warning at 1 day before (Phone call)
// Grace period: 3 days after due date
// Auto-cancellation after grace period (booking cancelled, forfeiture per terms)

interface PaymentMethod {
  type: PaymentType;
  provider: string;
  enabled: boolean;
  processingFee?: Money;
  limits?: PaymentLimits;
}

type PaymentType =
  | 'upi'                             // UPI (GPay, PhonePe, Paytm)
  | 'credit_card'                     // Visa, Mastercard, RuPay
  | 'debit_card'                      // Debit card
  | 'net_banking'                     // Direct bank transfer
  | 'wallet'                          // Paytm, PhonePe wallet
  | 'emi'                             // Credit card EMI
  | 'bank_transfer'                   // NEFT/RTGS/IMPS
  | 'cash';                           // Pay at office (for hybrid bookings)

// Payment method preferences (India):
// UPI: 45% of transactions (fastest growing)
// Credit/Debit Card: 25%
// Net Banking: 15%
// EMI: 10% (for trips > ₹30,000)
// Wallet: 3%
// Cash/Transfer: 2%
//
// Payment gateway integration:
// - Razorpay (recommended): UPI, Cards, EMI, Net Banking, International
// - PhonePe Business: UPI-first, good for mobile payments
// - Paytm for Business: Wallet + UPI
// - Cashfree: Multi-gateway, competitive rates
//
// Payment security:
// - PCI DSS Level 1 compliance (gateway handles this)
// - 3D Secure 2.0 for all card transactions (RBI mandate)
// - Tokenization for saved cards (RBI mandate, no raw card storage)
// - 2FA for UPI payments (existing UPI PIN)
// - Refund processing: Auto-refund within 5-7 business days
// - Dispute resolution: 15-day window for customer disputes

interface PaymentInstallment {
  installmentNumber: number;
  amount: Money;
  dueDate: Date;
  status: 'pending' | 'paid' | 'overdue' | 'waived';
  paidAt?: Date;
  transactionId?: string;
}
```

### Customer Communication

```typescript
interface BookingCommunication {
  bookingId: string;
  customer: CustomerContact;
  channel: CommunicationChannel;
  timeline: CommunicationTimeline;
}

// Communication timeline:
//
// Immediately after booking:
// → WhatsApp: "Booking received! Ref: #TRV-12345. Our team is confirming your trip details. We'll update you within 4 hours."
// → Email: Booking confirmation with itinerary summary and receipt
// → SMS: Booking reference and support number
//
// When agent confirms:
// → WhatsApp: "Great news! Your Kerala trip is confirmed! 🎉 Here's your detailed itinerary [PDF Link]"
// → Email: Confirmed itinerary with booking vouchers
// → In-app: Booking status updated to "Confirmed"
//
// Pre-departure (7 days):
// → WhatsApp: "Your Kerala trip starts in 7 days! 🏖️ Here's your packing list and check-in info."
// → Email: Pre-departure guide with hotel addresses, contact numbers, weather forecast
//
// Pre-departure (1 day):
// → WhatsApp: "Tomorrow's the day! 🌴 Your cab will pick you up at 8 AM. Driver: Rajesh (+91 98765 43210)"
//
// During trip:
// → WhatsApp (Day 1): "Hope you're enjoying Kerala! Need anything? Just message us."
// → WhatsApp (mid-trip): "How's your trip going? We'd love your feedback [link]"
//
// Post-trip:
// → WhatsApp: "Welcome back! How was your trip? Rate us ⭐⭐⭐⭐⭐ [link]"
// → Email: Post-trip survey + review request
// → Email (1 week later): "Plan your next adventure! Here are trips you might love [recommendations]"

// Cancellation communication:
// Customer cancels:
// → Immediate WhatsApp: "We've received your cancellation request for trip #TRV-12345. Our team is processing it."
// → Agent review (within 2 hours): Confirm cancellation and refund amount
// → WhatsApp: "Cancellation confirmed. Refund of ₹XX,XXX will be processed within 5-7 days."
// → Email: Cancellation confirmation with refund details and policy
//
// Agent cancels (supplier issue):
// → Immediate WhatsApp: "We're sorry, but we need to make changes to your trip. Our team is working on alternatives."
// → Agent call: Explain situation and offer alternatives
// → If customer accepts alternative: Updated confirmation
// → If customer cancels: Full refund + ₹2,000 inconvenience credit
```

### Booking Management

```typescript
interface StorefrontBookingManagement {
  customerPortal: CustomerBookingPortal;
  modificationFlow: ModificationFlow;
  cancellationFlow: CancellationFlow;
  disputeFlow: DisputeFlow;
}

interface CustomerBookingPortal {
  bookingId: string;
  accessCode: string;                 // Sent via WhatsApp/Email
  views: BookingView[];
  actions: BookingAction[];
}

type BookingView =
  | 'summary'                         // Booking overview and status
  | 'itinerary'                       // Full day-by-day itinerary
  | 'documents'                       // Vouchers, tickets, invoices
  | 'payments'                        // Payment history and upcoming
  | 'communication'                   // Message history with agency
  | 'reviews';                        // Review and feedback

type BookingAction =
  | 'download_itinerary'
  | 'download_voucher'
  | 'request_modification'
  | 'cancel_booking'
  | 'make_payment'
  | 'contact_agent'
  | 'submit_review';

// Customer booking portal:
// ┌──────────────────────────────────────────┐
// │  My Trip: Kerala Backwaters              │
// │  Ref: #TRV-12345 · ✅ Confirmed          │
// │                                          │
// │  📅 Dec 15-20, 2026 · 5N/6D             │
// │  👥 2 Adults · 💰 ₹37,000 (Paid)        │
// │                                          │
// │  [Itinerary] [Documents] [Payments]      │
// │  [Contact Agent] [Request Changes]       │
// │                                          │
// │  Upcoming:                               │
// │  - Dec 15: Flight AI-XXX at 6:00 AM     │
// │  - Dec 15: Airport pickup at 8:30 AM    │
// │  - Dec 15: Check-in Spice Routes Resort  │
// │                                          │
// │  Documents:                              │
// │  📄 Booking Confirmation                │
// │  📄 Flight E-Ticket                     │
// │  📄 Hotel Voucher                       │
// │  📄 Tax Invoice                         │
// └──────────────────────────────────────────┘

interface ModificationFlow {
  allowedModifications: ModificationType[];
  cutoffDays: number;                 // Days before departure
  feeSchedule: ModificationFee[];
  approvalRequired: boolean;
}

type ModificationType =
  | 'change_date'                     // Change travel dates
  | 'change_travelers'                // Add/remove travelers
  | 'upgrade_room'                    // Upgrade room type
  | 'add_addon'                       // Add extra activities/transfers
  | 'remove_addon'                    // Remove add-ons
  | 'special_request';                // Dietary, accessibility, etc.

// Modification rules:
// Date change: Free if >30 days before, ₹500 fee if 15-30 days,
//              Subject to availability, price difference may apply
// Add traveler: Subject to availability, additional cost applies
// Remove traveler: Cancellation policy applies for removed traveler
// Room upgrade: Price difference charged, subject to availability
// Add add-on: Anytime before 48 hours of departure
// Special request: Anytime, no fee, subject to availability
```

---

## Open Problems

1. **Abandoned bookings** — 60-70% of started bookings are abandoned. Need cart recovery (WhatsApp reminders, price alerts, limited-time offers).

2. **Payment failures** — UPI and card payments fail 15-20% of the time. Need retry mechanisms, alternative payment suggestions, and saved payment state.

3. **Agent confirmation delay** — Customer expects instant confirmation (like OTAs). Agent-mediated confirmation creates friction. Need to set expectations clearly.

4. **Partial booking scenarios** — Customer books online but some components aren't available. How to handle partial confirmation with alternatives.

5. **International payments** — NRI and foreign customers may book through storefronts. Need forex handling, international card support, and compliant invoicing.

---

## Next Steps

- [ ] Design storefront booking flow with multi-step checkout
- [ ] Build payment processing with Razorpay integration
- [ ] Create customer communication timeline with WhatsApp-first approach
- [ ] Design customer booking management portal
- [ ] Study booking engines (Booking.com, MakeMyTrip, TourRadar, Klook)
