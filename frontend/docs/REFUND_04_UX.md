# Refund & Cancellation Management — UX & Communication

> Research document for cancellation UX, customer communication, and refund tracking experience.

---

## Key Questions

1. **What's the customer-facing cancellation experience?**
2. **How do we communicate cancellation penalties transparently?**
3. **What's the refund tracking UX?**
4. **How do we present modification options to customers?**
5. **What's the agent experience for processing cancellations?**

---

## Research Areas

### Cancellation UX Patterns

```typescript
interface CancellationUX {
  initiationFlow: CancellationInitiation;
  penaltyDisplay: PenaltyDisplay;
  confirmationFlow: ConfirmationFlow;
  postCancellation: PostCancellationUX;
}

// Cancellation initiation:
// 1. Customer clicks "Cancel" on booking
// 2. System checks: Is cancellation allowed? (Non-refundable = blocked)
// 3. Show: "What would you like to cancel?"
//    - Entire trip
//    - Specific components (hotel, activity, transfer)
//    - Change dates instead (offer modification)
// 4. If specific components: Show affected items only
// 5. Calculate and display penalty

// Penalty display design:
// ┌─────────────────────────────────────────┐
// │  Cancellation Summary                    │
// │                                          │
// │  ✈ Delhi → Singapore (Indigo)           │
// │     ₹24,000 → Refund: ₹19,200           │
// │     Penalty: ₹4,800 (20%, airline fee)   │
// │                                          │
// │  🏨 Hotel Traders (3 nights)             │
// │     ₹45,000 → Refund: ₹30,000           │
// │     Penalty: ₹15,000 (1 night charge)    │
// │                                          │
// │  🎭 Universal Studios                   │
// │     ₹4,500 → Refund: ₹4,500             │
// │     Penalty: ₹0 (free cancellation)      │
// │                                          │
// │  ─────────────────────────────           │
// │  Total Paid:    ₹73,500                  │
// │  Total Refund:  ₹53,700                  │
// │  Total Penalty: ₹19,800                  │
// │                                          │
// │  Refund to: Credit Card (****1234)       │
// │  Expected by: April 30, 2026             │
// │                                          │
// │  [Cancel Booking]  [Keep Booking]        │
// └─────────────────────────────────────────┘

// Confirmation flow:
// Step 1: Review penalties (above)
// Step 2: "Are you sure?" with consequences:
//   "This action cannot be undone. ₹19,800 in penalties will apply."
// Step 3: Reason for cancellation (optional, helps analytics):
//   - Change of plans
//   - Found a better deal
//   - Emergency/unforeseen circumstances
//   - Travel advisory
//   - Other
// Step 4: Confirm cancellation
```

### Refund Tracking

```typescript
interface RefundTrackingUX {
  refundId: string;
  progressSteps: RefundStep[];
  currentStep: number;
  estimatedCompletion: Date;
}

interface RefundStep {
  step: string;
  status: 'completed' | 'in_progress' | 'pending';
  completedAt?: Date;
  description: string;
}

// Refund tracking display:
// ┌─────────────────────────────────────────┐
// │  Refund Tracker                          │
// │                                          │
// │  ✓ Booking cancelled        Apr 26       │
// │  ✓ Supplier confirmed        Apr 26      │
// │  ✓ Refund initiated        Apr 27        │
// │  ◐ Processing refund       ~Apr 29       │
// │  ○ Refund completed         ~Apr 30       │
// │                                          │
// │  Refund Amount: ₹53,700                  │
// │  Refund To: Credit Card (****1234)       │
// │  Reference: REF-2026-04-12345            │
// │                                          │
// │  Need help? [Contact Agent]              │
// └─────────────────────────────────────────┘

// Agent-side refund tracking:
// Dashboard showing all pending refunds:
// - Customer name, trip ID, refund amount
// - Current status (waiting on supplier, processing, completed)
// - Days since initiation
// - Escalation flag if overdue
// - Quick actions: Contact supplier, Process manually, Mark as complete
```

### Modification UX

```typescript
interface ModificationUX {
  initiationFlow: ModificationInitiation;
  optionComparison: OptionComparison;
  confirmationFlow: ModificationConfirmation;
}

// Modification initiation:
// Customer: "I want to change my hotel dates"
// 1. Show: "What would you like to change?"
//    [Dates] [Hotel] [Flights] [Activities] [Travelers]
// 2. For date changes:
//    "Select new dates" → Calendar with available dates highlighted
//    "Current: Jun 15-18 (3 nights) → New: Jun 20-23 (3 nights)"
// 3. Show price impact:
//    "New rate: ₹52,000 (was ₹45,000) → Additional: ₹7,000"
//    "Modification fee: ₹500"
//    "Total additional charge: ₹7,500"
// 4. Offer alternatives:
//    "Want to save money? These dates are ₹43,000 (₹2,000 less than original)"

// Option comparison for date changes:
// ┌──────────────────────────────────────────────────┐
// │  Change Options                                    │
// │                                                    │
// │  Option A: Modify Dates          Option B: Cancel  │
// │  New dates: Jun 20-23           Full cancellation  │
// │  Additional cost: ₹7,500        Refund: ₹53,700    │
// │  Same hotel ✓                   Rebook: ₹58,000    │
// │  Keep flights ✓                 Net cost: ₹4,300   │
// │                                  New hotel ✗       │
// │  → Recommended                                   │
// └──────────────────────────────────────────────────┘

// Agent-side modification tools:
// 1. Quick modify: Change dates/rates directly
// 2. Guided modify: Step-by-step wizard
// 3. Cancel + rebook: Auto-compare with modification
// 4. Template: "Based on similar modifications, suggest X"
// 5. Risk indicator: "This modification may affect group pricing"
```

### Communication Templates

```typescript
interface CancellationCommunication {
  templates: CommunicationTemplate[];
}

// Communication templates:

// Pre-cancellation: Free cancellation reminder
// "Your hotel booking for [hotel] has free cancellation until [date].
//  After that, a cancellation fee of [amount] will apply."

// Cancellation confirmation:
// "Your booking has been cancelled as requested.
//  Refund of ₹[amount] will be processed to your [card/UPI] within [X] business days.
//  Reference: [REF-ID]. Questions? Reply to this message."

// Refund processed:
// "Great news! Your refund of ₹[amount] for trip [ID] has been processed.
//  It should appear in your [payment method] within [X] business days.
//  Reference: [REF-ID]"

// Refund delayed:
// "Your refund of ₹[amount] is taking longer than expected.
//  We're following up with [supplier] and will update you within [X] days.
//  Your agent [name] is tracking this for you."

// Modification confirmation:
// "Your trip has been updated as requested:
//  [Change summary]
//  Additional charge: ₹[amount] (or Refund: ₹[amount])
//  Updated itinerary: [Link to view]
//  Questions? Contact your agent [name]."

// Agent-to-supplier:
// "Cancellation request for booking [ID]. Guest: [name].
//  Travel dates: [dates]. Please confirm cancellation and refund eligibility.
//  Agency: [agency name]. Contact: [agent phone]"
```

---

## Open Problems

1. **Penalty shock** — Customers don't expect ₹20,000+ in penalties. Need to communicate cancellation terms at booking time, not just at cancellation time.

2. **Refund anxiety** — "Will I actually get my money back?" is the #1 customer concern during cancellation. Real-time refund tracking reduces anxiety.

3. **Self-service vs. agent-assisted** — Should customers be able to cancel without an agent? Risk: Wrong component cancelled, partial cancellation confusion. Need clear guardrails.

4. **Modification temptation** — Offering modification as an alternative to cancellation keeps revenue but may frustrate customers who just want to cancel.

5. **Cancellation reason insight** — Why customers cancel (price, change of plans, emergency) drives product improvements. Need structured reason collection without being intrusive.

---

## Next Steps

- [ ] Design cancellation penalty display with transparent breakdown
- [ ] Build refund tracking progress indicator for customer portal
- [ ] Create modification option comparison UI
- [ ] Design cancellation communication templates
- [ ] Study cancellation UX (Booking.com, Airbnb, MakeMyTrip cancellation flows)
