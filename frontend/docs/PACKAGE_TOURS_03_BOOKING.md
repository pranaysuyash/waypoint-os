# Package Tours 03: Booking Flow

> Package booking process, deposits, and confirmations

---

## Document Overview

**Focus:** How customers book package tours
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Booking Process
- What information is required to book?
- How does package booking differ from a la carte?
- What about traveler details for all passengers?
- How do we handle special requests?

### 2. Payments & Deposits
- What are the deposit structures?
- When is full payment due?
- How do we handle installments?
- What about payment security?

### 3. Confirmations
- What information goes on confirmations?
- How do we deliver travel documents?
- What about vouchers and tickets?
- When do customers get final details?

### 4. Group Bookings
- How do group bookings work?
- What are room lists?
- How do we handle individual payments?
- What about group contracts?

---

## Research Areas

### A. Booking Requirements

**Required Information:**

| Field | For Package vs A La Carte | Notes | Research Needed |
|-------|---------------------------|-------|-----------------|
| **Lead Traveler** | Same | Primary contact | ? |
| **All Travelers** | Same | Names, dates of birth | Passport numbers? |
| **Passport Details** | Often required | International travel | When required? |
| **Contact Info** | Same | Email, phone | ? |
| **Emergency Contact** | More critical | Remote destinations | Required? |
| **Dietary Requirements** | More important | Group meals | How to capture? |
| **Room Preferences** | Same | Bed type, smoking | ? |
| **Special Requests** | More options | Accessibility, occasions | How to handle? |

**Package-Specific Requirements:**

| Requirement | For | Research Needed |
|-------------|-----|-----------------|
| **Rooming List** | Groups | Format? Due when? |
| **Travel Insurance** | Often required | Mandatory or optional? |
| **Medical Disclosure** | Adventure trips | Liability? |
| **Visa Information** | International | Due when? |
| **Waiver Forms** | Adventure activities | Digital or paper? |

### B. Payment Structures

**Deposit Models:**

| Model | Typical Amount | When Due | Balance Due | Research Needed |
|-------|----------------|----------|-------------|-----------------|
| **Percentage Deposit** | 20-30% | At booking | 30-45 days before | Standard? |
| **Fixed Deposit** | ₹10,000-25,000 | At booking | 60 days before | For high-value? |
| **Full Payment** | 100% | At booking | N/A | Last-minute? |
| **Installment Plan** | Spread | Scheduled | Final before travel | Who offers? |

**Payment Timing:**

| Timing | Scenario | Research Needed |
|--------|----------|-----------------|
| **Immediate deposit** | Most bookings | Amount? |
| **Balance 60 days** | Standard trips | Exceptions? |
| **Balance 30 days** | Short trips | ? |
| **Full immediate** | < 30 days to travel | ? |
| **Custom schedule** | High-value | Flexibility? |

**Research:**
- What are industry standard deposit amounts?
- How do payment terms vary by destination/value?
- What about refund policies if customer cancels after deposit?

### C. Booking Flow

**Standard Booking Flow:**

```
1. Review Package
   - Customer views package details
   - Checks availability for dates
   - Confirms pricing

2. Enter Traveler Details
   - Lead traveler info
   - All passenger details
   - Special requirements

3. Review & Customize
   - Review booking summary
   - Select optional upgrades
   - Add special requests

4. Payment
   - Pay deposit or full amount
   - Select payment method
   - Get payment confirmation

5. Booking Confirmation
   - Receive booking reference
   - Get initial documents
   - Payment receipt

6. Pre-Departure
   - Balance payment reminder
   - Final documents sent
   - Travel briefing
```

**Group Booking Flow:**

```
1. Group Quote Request
   - Group details
   - Dates and requirements
   - Receive quote

2. Contract & Deposit
   - Review contract terms
   - Pay group deposit
   - Secure space

3. Rooming List
   - Collect passenger details
   - Room assignments
   - Submit by deadline

4. Individual Payments (Optional)
   - Passengers pay individually
   - Track payments
   - Final balance

5. Final Details
   - Rooming list confirmation
   - Final documents
   - Group coordination
```

### D. Confirmation & Documents

**Initial Confirmation:**

| Element | Timing | Content | Research Needed |
|---------|--------|---------|-----------------|
| **Booking Reference** | Immediate | Unique ID | Format? |
| **Payment Receipt** | Immediate | Amount paid | Tax invoice? |
| **Booking Summary** | Immediate | Trip details | What level of detail? |
| **Next Steps** | Immediate | What happens next | Balance due date? |

**Final Travel Documents:**

| Document | Timing | Content | Delivery Method | Research Needed |
|----------|--------|---------|-----------------|-----------------|
| **Detailed Itinerary** | 2-4 weeks before | Day-by-day breakdown | Email/app | ? |
| **Vouchers** | 2-4 weeks before | Hotel, transfer, activity vouchers | Email/app | Digital/print? |
| **Tickets** | When available | Flight/train tickets | Email | E-tickets? |
| **Travel Guide** | 2-4 weeks before | Destination info, tips | Email/app | ? |
| **Emergency Contacts** | 2-4 weeks before | 24/7 support, local offices | App/email | ? |
| **Joining Instructions** | 2 weeks before | Where to meet, when | Email | ? |

**Document Delivery:**

| Method | Pros | Cons | Research Needed |
|--------|------|------|-----------------|
| **Email** | Universal, familiar | Can get lost, not offline | ? |
| **App** | Offline access, updates | Download friction | ? |
| **Print** | Backup, familiarity | Cost, delivery time | ? |
| **WhatsApp** | High engagement | Platform limits | ? |

---

## State Machine

**Package Booking States:**

```
DRAFT → PENDING_DEPOSIT → DEPOSIT_RECEIVED → CONFIRMED →
                              → BALANCE_DUE → BALANCE_RECEIVED → FINALIZED →
                                                                   → TRAVELLED →
                                                                   → COMPLETED
```

**State Definitions:**

| State | Description | Customer Actions |
|-------|-------------|------------------|
| **DRAFT** | Booking in progress | Continue, save, abandon |
| **PENDING_DEPOSIT** | Waiting for deposit | Pay deposit |
| **DEPOSIT_RECEIVED** | Deposit paid, space held | Add travelers, modify |
| **CONFIRMED** | Booking confirmed with operator | Pay balance, modify |
| **BALANCE_DUE** | Balance payment approaching | Pay balance |
| **BALANCE_RECEIVED** | Fully paid | Review documents |
| **FINALIZED** | Documents sent | Wait for travel |
| **TRAVELLED** | Trip completed | Review, feedback |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface PackageBooking {
  id: string;
  packageId: string;
  status: BookingStatus;

  // Travelers
  leadTraveler: TravelerDetails;
  travelers: TravelerDetails[];

  // Dates
  bookingDate: Date;
  departureDate: Date;
  returnDate: Date;

  // Pricing
  pricing: {
    totalPrice: Money;
    depositPaid: Money;
    balanceDue: Money;
    balanceDueDate: Date;
  };

  // Customizations
  roomPreferences?: RoomPreference[];
  specialRequests?: string[];
  optionalAddOns?: AddOn[];

  // Documents
  documents: BookingDocument[];

  // Payments
  payments: Payment[];

  // Operator
  operatorBookingId?: string;
  operatorConfirmation?: string;
}

type BookingStatus =
  | 'draft'
  | 'pending_deposit'
  | 'deposit_received'
  | 'confirmed'
  | 'balance_due'
  | 'balance_received'
  | 'finalized'
  | 'travelled'
  | 'cancelled'
  | 'refunded';

interface TravelerDetails {
  title: string;
  firstName: string;
  lastName: string;
  dateOfBirth: Date;
  nationality: string;
  passportNumber?: string;
  passportExpiry?: string;
  contactEmail: string;
  contactPhone: string;
  dietaryRequirements?: string;
  medicalConditions?: string;
}

interface RoomPreference {
  roomType: string;
  bedConfiguration: 'single' | 'double' | 'twin' | 'triple';
  smoking: boolean;
  specialRequests?: string;
}

interface AddOn {
  id: string;
  name: string;
  price: Money;
  selected: boolean;
}

interface BookingDocument {
  type: DocumentType;
  url: string;
  sentAt: Date;
  accessedAt?: Date;
}

type DocumentType =
  | 'booking_confirmation'
  | 'payment_receipt'
  | 'detailed_itinerary'
  | 'voucher'
  | 'ticket'
  | 'travel_guide'
  | 'joining_instructions';
```

---

## Open Problems

### 1. Room Allocation
**Challenge:** Allocating rooms for groups, especially with odd numbers

**Options:**
- Customer specifies rooming
- Auto-optimize allocation
- Single supplements apply
- Triple sharing options

### 2. Payment Collection
**Challenge:** Collecting deposits and balances on time

**Options:**
- Automatic reminders
- Easy payment links
- Installment plans
- Auto-charge authorization

### 3. Changes After Booking
**Challenge:** Customer wants to modify booking

**Options:**
- Allowed changes (name, date)
- Fees for changes
- Operator-dependent rules
- Some changes not allowed

### 4. Document Delivery
**Challenge:** Ensuring customers get and can access documents

**Options:**
- Multiple delivery methods
- App with offline access
- Print on demand
- 24/7 access line

---

## Competitor Research Needed

| Competitor | Booking Flow | Notable Patterns |
|------------|--------------|------------------|
| **MakeMyTrip** | ? | ? |
| **Yatra** | ? | ? |
| **TravelTriangle** | ? | Custom quotes? |
| **TourRadar** | ? | International? |

---

## Experiments to Run

1. **Booking usability test:** How smooth is the flow?
2. **Form completion test:** Do customers abandon?
3. **Payment timing test:** When do customers prefer to pay?
4. **Document access test:** Can customers find documents?

---

## References

- [Package Tours - Providers](./PACKAGE_TOURS_01_PROVIDERS.md) — Operator requirements
- [Trip Builder - Booking Management](./TRIP_BUILDER_05_BOOKING_MANAGEMENT.md) — Similar patterns
- [Payment Processing](./PAYMENT_PROCESSING_MASTER_INDEX.md) — Payment integration

---

## Next Steps

1. Design booking flow
2. Implement payment integration
3. Build document generation
4. Create booking management
5. Test end-to-end flow

---

**Status:** Research Phase — Booking flow unknown

**Last Updated:** 2026-04-27
