# Rail Integration 03: Booking & Ticketing

> Rail booking process, seat selection, and ticket issuance

---

## Document Overview

**Focus:** How customers book rail travel
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Booking Process
- What information is required to book trains?
- How does rail booking differ from flight booking?
- What about passenger details for all travelers?
- How do we handle berth preferences?

### 2. Seat/Berth Selection
- How does seat selection work?
- What about berth preferences (lower, upper, window?)
- How do we handle auto-allocation?
- What about group bookings?

### 3. Ticket Issuance
- How are rail tickets delivered?
- What about e-tickets vs. physical tickets?
- How do we handle confirmed vs. waitlist tickets?
- What about ID verification?

### 4. Special Cases
- How do we handle Tatkal booking?
- What about waitlist booking?
- How do we handle RAC?
- What about foreign tourist quota?

---

## Research Areas

### A. Booking Requirements

**Required Information:**

| Field | For Rail vs Other Travel | Notes | Research Needed |
|-------|---------------------------|-------|-----------------|
| **Passenger Name** | Same | As per ID | Exact match required? |
| **Age** | Critical | For quota eligibility | Proof required? |
| **Gender** | Critical | For berth allocation | For ladies quota? |
| **ID Type** | Critical | For verification | Allowed IDs? |
| **ID Number** | Critical | For verification | Mandatory for all? |
| **Contact** | Same | Phone, email | SMS required? |
| **Berth Preference** | Unique | Lower/upper/window | Guaranteed? |

**ID Proof Requirements (Indian Railways):**

| ID Type | Accepted | For Whom | Research Needed |
|---------|----------|----------|-----------------|
| **Aadhaar** | Yes | All | Digital copy OK? |
| **Voter ID** | Yes | All | ? |
| **Passport** | Yes | All | Required for foreigners? |
| **Driving License** | Yes | All | ? |
| **PAN Card** | No | Not accepted | ? |

**Berth Preferences:**

| Preference | Description | Guaranteed? | Research Needed |
|------------|-------------|-------------|-----------------|
| **Lower** | Lower berth | No | For seniors/medical? |
| **Upper** | Upper berth | No | ? |
| **Middle** | Middle berth (3A) | No | ? |
| **Window** | Window seat | No | ? |
| **Side Lower/Upper** | Side berths | No | ? |

### B. Booking Flows

**Standard Booking Flow (Indian Railways):**

```
1. Select Train & Class
   - Customer views search results
   - Selects train and class
   - Checks availability status

2. Enter Passenger Details
   - For each passenger:
     * Name (as per ID)
     * Age
     * Gender
     * Berth preference
   - Contact information
   - ID proof details

3. Review Booking
   - Review passenger details
   - Review total fare
   - Check auto-assigned berths (if any)

4. Payment
   - Pay fare
   - Payment confirmation

5. Ticket Issuance
   - If confirmed: E-ticket issued
   - If RAC: RAC ticket issued
   - If WL: Waitlist ticket issued
   - SMS and email sent

6. Before Travel
   - Check PNR status (if WL/RAC)
   - Chart preparation (4 hours before)
   - Final status update
```

**Tatkal Booking Flow:**

```
1. Timing Check
   - Tatkal opens at 10 AM (1 day before)
   - AC classes: 10 AM
   - Non-AC: 11 AM
   - Premium Tatkal: Same timing, dynamic pricing

2. Quick Entry
   - Pre-filled passenger details
   - Select train and class
   - Check availability in real-time

3. Fast Payment
   - Auto-fill payment
   - Quick checkout
   - Seats sell in seconds

4. Confirmation
   - Immediate confirmation if available
   - Or move to next train
```

**Rail Pass Booking Flow:**

```
1. Select Pass
   - Customer views pass options
   - Selects pass type, duration, class

2. Enter Traveler Details
   - Name as per passport
   - Passport number
   - Date of birth
   - Nationality

3. Review and Pay
   - Review pass details
   - Pay for pass

4. Receive Voucher
   - Email voucher
   - Print at home
   - Exchange for actual pass (if required)

5. Activation
   - Activate on first travel (some passes)
   - Or activate at exchange (JR Pass)
```

### C. Ticket Types

**By Status:**

| Type | Meaning | Boarding Allowed | Research Needed |
|------|---------|------------------|-----------------|
| **Confirmed** | Berth assigned | Yes | ? |
| **RAC** | Seat confirmed, berth not | Yes | Share seat? |
| **Waitlist** | No seat/berth | No | Until confirmed |
| **E-Ticket** | Electronic ticket | Yes with ID | ? |
| **I-Ticket** | Physical ticket delivered | Yes with ticket | ? |

**By Delivery:**

| Type | Description | Pros | Cons | Research Needed |
|------|-------------|------|------|-----------------|
| **E-Ticket** | Electronic, show on phone | Immediate, no print | Phone battery | ? |
| **Print at home** | PDF to print | Immediate | Need printer | ? |
| **Physical delivery** | Courier to address | No phone needed | Delay, cost | ? |
| **Station pickup** | Collect at machine | Flexible | Need to go early | ? |

**International Tickets:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **E-Ticket** | QR code on phone | ? |
| **Print at home** | PDF ticket | ? |
| **Mobile wallet** | Apple Wallet, Google Pay | ? |
| **Smart card** | Reusable card | Some systems? |

### D. Seat/Berth Allocation

**Auto-Allocation Logic (Indian Railways):**

| Factor | Priority | Research Needed |
|--------|----------|-----------------|
| **Age/Senior citizen** | Lower berth | Guaranteed for seniors? |
| **Women quota** | Lower/accommodation | How allocated? |
| **Group booking** | Together | Algorithm? |
| **Preference** | If available | Not guaranteed |

**Berth Layout:**

| Class | Layout | Research Needed |
|-------|--------|-----------------|
| **1A** | 2- or 4-berth cabins | ? |
| **2A** | Open bays, 2 side berths | ? |
| **3A** | Open bays, 2 side berths | ? |
| **CC** | 2x2 seating | ? |
| **SL** | Open bays, 2 side berths | ? |

**Group Booking:**

| Scenario | Allocation | Research Needed |
|----------|------------|-----------------|
| **6 passengers in 3A** | One bay (6 berths) | Guaranteed together? |
| **4 passengers in 2A** | One bay (4 berths) | ? |
| **Odd number** | Some may be separated | How to warn? |
| **RAC for group** | All get RAC | ? |

---

## State Machine

**Rail Booking States:**

```
DRAFT → PENDING_PAYMENT → PAYMENT_RECEIVED →
                                      ├── CONFIRMED → TICKET_ISSUED → TRAVELLED → COMPLETED
                                      ├── RAC → CHART_PREPARED → CONFIRMED/REMAINING_RAC → TRAVELLED
                                      └── WAITLIST → CHART_PREPARED →
                                                          ├── CONFIRMED → TICKET_ISSUED
                                                          ├── RAC → CHART_PREPARED
                                                          └── CANCELLED → REFUNDED
```

**State Definitions:**

| State | Description | Customer Actions |
|-------|-------------|------------------|
| **DRAFT** | Booking in progress | Continue, abandon |
| **PENDING_PAYMENT** | Waiting for payment | Pay within timeout |
| **PAYMENT_RECEIVED** | Payment confirmed | Wait for ticket |
| **CONFIRMED** | Berth assigned | Board with ID |
| **RAC** | Seat confirmed | Board with ID, share seat |
| **WAITLIST** | Not confirmed | Wait for update |
| **CHART_PREPARED** | Final assignment done | Check final status |
| **TICKET_ISSUED** | Ticket sent | Download/view |
| **TRAVELLED** | Journey completed | Provide feedback |
| **CANCELLED** | Booking cancelled | Refund processing |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface RailBooking {
  id: string;
  pnrNumber: string; // Passenger Name Record
  railProviderId: string;
  trainNumber: string;

  // Journey
  origin: RailStation;
  destination: RailStation;
  departureDate: Date;
  departureTime: string;
  arrivalDate: Date;
  arrivalTime: string;

  // Booking
  class: TravelClass;
  quota: QuotaType;
  status: BookingStatus;

  // Passengers
  passengers: RailPassenger[];

  // Seat/Berth Assignment
  seatAllocation?: SeatAllocation[];

  // Pricing
  pricing: {
    totalFare: Money;
    fareBreakdown: FareBreakdown[];
  };

  // Payment
  paymentId: string;
  paymentStatus: PaymentStatus;

  // Ticket
  ticketType: TicketType;
  ticketUrl?: string;
  issuedAt?: Date;

  // Timeline
  bookedAt: Date;
  chartPreparedAt?: Date;
  statusUpdatedAt?: Date;
}

type BookingStatus =
  | 'confirmed'
  | 'rac'
  | 'waitlist'
  | 'cancelled'
  | 'chart_prepared';

interface RailPassenger {
  bookingId: string;
  sequence: number;

  // Details
  name: string;
  age: number;
  gender: 'male' | 'female' | 'other';

  // ID
  idType: string;
  idNumber: string;

  // Berth
  berth?: string; // Assigned berth number
  coach?: string; // Coach number
  bookingStatus: 'confirmed' | 'rac' | 'waitlist';
  currentStatus: 'confirmed' | 'rac' | 'waitlist';

  // Preference
  berthPreference?: BerthPreference;
}

type BerthPreference =
  | 'lower'
  | 'upper'
  | 'middle'
  | 'side_lower'
  | 'side_upper'
  | 'window'
  | 'no_preference';

interface SeatAllocation {
  coachNumber: string;
  berthNumber: string;
  berthType: BerthType;
  position: 'lower' | 'upper' | 'middle' | 'side_lower' | 'side_upper';
}

type BerthType =
  | 'lower'
  | 'middle'
  | 'upper'
  | 'side_lower'
  | 'side_upper';

interface RailPass {
  id: string;
  passProviderId: string;
  type: RailPassType;

  // Traveler
  travelerName: string;
  passportNumber: string;
  nationality: string;
  dateOfBirth: Date;

  // Pass Details
  countries: string[];
  validityDays: number;
  travelDays: number;
  class: TravelClass;

  // Pricing
  price: Money;

  // Status
  status: 'ordered' | 'activated' | 'expired';
  orderedAt: Date;
  activatedAt?: Date;
  expiresAt?: Date;

  // Voucher
  voucherUrl: string;
  exchangeLocations?: string[];
}
```

---

## Open Problems

### 1. Waitlist Uncertainty
**Challenge:** Customers book on waitlist, may not confirm

**Options:**
- Show historical confirmation rate
- Auto-refund if not confirmed
- Suggest confirmed alternatives
- Clear communication

### 2. Tatkal Speed
**Challenge:** Tatkal seats sell in seconds

**Options:**
- Pre-filled forms
- Multiple payment methods
- Auto-refresh availability
- Queue system

### 3. ID Verification
**Challenge:** Name must match ID exactly

**Options:**
- Clear instructions
- ID validation
- Allow name correction (with fee)
- Strict enforcement warning

### 4. Group Allocation
**Challenge:** Groups may get separated

**Options:**
- Warn about possible separation
- Offer confirmed alternatives
- Book in multiple bookings
- Clear explanation

---

## Competitor Research Needed

| Competitor | Booking Flow | Notable Patterns |
|------------|--------------|------------------|
| **IRCTC** | ? | ? |
| **MakeMyTrip** | ? | ? |
| **Yatra** | ? | ? |
| **Trainline** | ? | ? |

---

## Experiments to Run

1. **Booking usability test:** How smooth is the flow?
2. **Tatkal success test:** Can we book Tatkal?
3. **Waitlist booking test:** Do customers understand WL?
4. **Group booking test:** How do groups book?

---

## References

- [Rail - Providers](./RAIL_01_PROVIDERS.md) — Quota and class types
- [Rail - Search](./RAIL_02_SEARCH.md) — Availability display

---

## Next Steps

1. Design booking flow
2. Implement payment integration
3. Build ticket generation
4. Create PNR status tracking
5. Test end-to-end flow

---

**Status:** Research Phase — Booking flow unknown

**Last Updated:** 2026-04-27
