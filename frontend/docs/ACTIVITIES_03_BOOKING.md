# Activities & Experiences 03: Booking & Vouchers

> Reservation flow, payment, and ticket delivery

---

## Document Overview

**Focus:** Converting activity selection into confirmed bookings
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Booking Data Requirements
- What information is mandatory vs. optional?
- How do we handle participant details? (Names? Ages? Weights?)
- What about special requirements? (Dietary restrictions, accessibility)
- How do we handle "book now, travel later"?

### 2. Pricing & Payment
- How is final price calculated?
- When is payment taken?
- What about deposits vs. full payment?
- How do we handle group discounts?

### 3. Voucher Delivery
- How are tickets/vouchers delivered?
- What information must be on the voucher?
- Mobile vs. printable vs. collect on arrival?
- How do we handle QR codes?

### 4. Confirmation Communication
- What information is in the confirmation email?
- How do we provide activity details? (Meeting point, what to bring)
- What about operator contact information?
- How do we handle reminders?

---

## Research Areas

### A. Booking Requirements

**Required Information:**

| Field | When Required | Notes |
|-------|---------------|-------|
| **Lead traveler name** | Always | For voucher |
| **Contact email** | Always | Delivery |
| **Contact phone** | Always | emergencies |
| **Date of travel** | Always | Even if open-dated |
| **Participant count** | Always | Affects capacity |
| **Participant ages** | Sometimes | Child pricing |
| **Special requests** | Optional | May not be guaranteed |

**Research:**
- What are the minimum requirements per activity type?
- Can we book with incomplete information?
- How do we collect missing info later?

### B. Pricing at Booking

**Pricing Scenarios:**

| Scenario | Pricing Approach |
|----------|------------------|
| **Fixed price** | Set price per person |
| **Tiered pricing** | Adult/child/senior rates |
| **Group pricing** | Per person or flat rate |
| **Dynamic pricing** | Varies by date/time |
| **Custom quote** | Operator provides quote |

**Research:**
- How do we handle pricing changes between search and booking?
- What if final price differs from quoted?
- How do we display price breakdowns?

### C. Voucher Types

**Voucher Formats:**

| Format | Used For | Delivery |
|--------|----------|----------|
| **QR code** | Most activities | Mobile app/PDF |
| **Barcode** | Attraction tickets | Mobile app/PDF |
| **Reference number** | Small operators | Email/collect |
| **Printable PDF** | All activities | Email/download |
| **Physical ticket** | Some attractions | Collect/mailed |

**Voucher Content:**

| Field | Always Included | Notes |
|-------|-----------------|-------|
| Booking reference | ✓ | Unique identifier |
| Activity name | ✓ | |
    Operator name | ✓ | |
| Date and time | ✓ | If scheduled |
| Meeting point | ✓ | Address/map |
| Participant names | Sometimes | If required |
| Special instructions | ✓ | What to bring, etc. |
| Emergency contact | ✓ | Operator contact |
| Cancellation policy | ✓ | How to cancel |

### D. Timing of Communication

**Communication Touchpoints:**

| Timing | Channel | Content |
|--------|---------|---------|
| **Immediately** | Email + App | Booking confirmation, voucher |
| **24-48 hours before** | Email/SMS | Reminder, details |
| **On day** | SMS (optional) | Last-minute reminder |
| **After activity** | Email | Review request, photos |

**Research:**
- What is the optimal reminder timing?
- Which channels do customers prefer?
- What about WhatsApp reminders?

---

## Booking State Machine

```
PENDING → REQUESTED → CONFIRMED → VOUCHER_SENT → COMPLETED
           ↓           ↓
        FAILED    CANCELLED
```

**States Explained:**

| State | Meaning | Next Actions |
|-------|---------|--------------|
| PENDING | Booking initiated, not submitted | Submit to provider |
| REQUESTED | Sent to provider, awaiting confirmation | Wait/poll |
| CONFIRMED | Provider confirmed booking | Generate voucher |
| VOUCHER_SENT | Voucher delivered to customer | Await activity date |
| COMPLETED | Activity has happened | Request review |
| FAILED | Provider rejected | Offer alternatives |
| CANCELLED | Cancelled by customer or provider | Process refund |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface ActivityBooking {
  id: string;
  tripId?: string;
  status: BookingStatus;

  // Activity details
  activityId: string;
  title: string;
  provider: ProviderReference;

  // Scheduling
  scheduledDate: Date;
  scheduledTime?: Time;
  duration: Duration;

  // Participants
  participants: ActivityParticipant[];
  leadTraveler: LeadTravelerInfo;

  // Pricing
  pricing: {
    basePrice: Money;
    discounts: Discount[];
    taxes: Money;
    fees: Money;
    total: Money;
    currency: string;
  };

  // Payment
  payment: {
    status: PaymentStatus;
    method: string;
    transactionId?: string;
    paidAt?: Date;
  };

  // Voucher
  voucher?: {
    type: VoucherType;
    code: string;
    url: string;
    sentAt: Date;
    deliveryMethod: string;
  };

  // Logistics
  meetingPoint: MeetingPointInfo;
  whatToBring?: string[];
  specialInstructions?: string;

  // Policies
  cancellationPolicy: CancellationPolicy;
  amendmentPolicy: AmendmentPolicy;

  // Timeline
  createdAt: Date;
  confirmedAt?: Date;
  completedAt?: Date;
}

interface ActivityParticipant {
  type: 'adult' | 'child' | 'senior' | 'infant';
  age?: number;
  name?: string;  // Sometimes required
  weight?: number;  // For some activities
}

type VoucherType = 'qr_code' | 'barcode' | 'reference' | 'printable';
```

---

## Special Booking Scenarios

### 1. Age-Dependent Pricing
**Challenge:** Price depends on participant ages

**Options:**
- Collect ages before showing price
- Show price range "from $X"
- Assume all adults, adjust later

**Research:** What are UX best practices?

### 2. Capacity-Constrained Activities
**Challenge:** Only 3 spots left, customer needs 5

**Options:**
- Show availability and let customer decide
- Offer alternative dates/times
- Offer split booking

**Research:** How do competitors handle this?

### 3. Weather-Dependent Activities
**Challenge:** Outdoor activity, weather forecast poor

**Options:**
- Show weather warning
- Allow free cancellation if bad weather
- Operator decides day-of

**Research:** What are customer expectations?

### 4. Multi-Language Activities
**Challenge:** Activity offered in multiple languages

**Questions:**
- How do we show language options?
- Does language affect availability?
- How do we capture language preference?

---

## Open Problems

### 1. Name Collection
**Challenge:** Some activities require participant names, others don't

**Questions:**
- When do we ask for names?
- What if customer doesn't know yet?
- How do we handle name changes?

### 2. Participant Details
**Challenge:** Some activities need specific details (weight for diving, shoe size, etc.)

**Questions:**
- When do we collect these?
- What if customer doesn't provide?
- How do we validate?

### 3. Voucher Security
**Challenge:** Preventing voucher sharing/reuse

**Questions:**
- Do we need ID checks?
- How do we prevent duplicate use?
- What about screenshot sharing?

### 4. Operator Communication
**Challenge:** Last-minute changes from operator

**Questions:**
- How do we communicate changes to customer?
- What if activity is cancelled?
- Who handles refunds?

---

## References

- [Ground Transportation - Booking](./GROUND_TRANSPORTATION_03_BOOKING.md) — Similar booking patterns
- [Booking Engine - Confirmation](./BOOKING_ENGINE_04_CONFIRMATION.md) — Confirmation patterns

---

## Next Steps

1. Map booking requirements per activity type
2. Design voucher format
3. Build booking state machine
4. Create communication templates
5. Implement voucher delivery

---

**Status:** Research Phase — Booking flow unknown

**Last Updated:** 2026-04-27
