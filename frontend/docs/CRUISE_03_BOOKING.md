# Cruise Booking 03: Booking Flow

> Cruise booking process, passenger details, and documentation

---

## Document Overview

**Focus:** How customers book cruises
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Booking Process
- What information is required to book a cruise?
- How does cruise booking differ from other travel?
- What about passenger details for all travelers?
- How do we handle special requests?

### 2. Payments & Deposits
- What are the deposit structures?
- When is full payment due?
- How do payment terms vary by cruise line?
- What about installment plans?

### 3. Passenger Information
- What details are required for each passenger?
- What about passport information?
- How do we handle dietary requirements?
- What about mobility/accessibility needs?

### 4. Documentation
- What documents are needed before travel?
- How do we handle boarding passes?
- What about visa requirements?
- When do customers get final documents?

---

## Research Areas

### A. Booking Requirements

**Required Information:**

| Field | For Cruise vs Other Travel | Notes | Research Needed |
|-------|---------------------------|-------|-----------------|
| **Lead Passenger** | Same | Primary contact | ? |
| **All Passengers** | Same | Names, dates of birth | Weight required? |
| **Passport Details** | Required | International travel | Expiry rules? |
| **Citizenship** | Critical | For visa determination | ? |
| **Emergency Contact** | More critical | At sea | Required? |
| **Dining Preference** | Unique | Traditional/fixed/anytime | How to capture? |
| **Beverage Package** | Optional | Pre-book discount | Show at booking? |
| **Accessibility Needs** | Critical | Ship accessibility | Required? |
| **Special Occasions** | Optional | Honeymoon, birthday | How to handle? |

**Cruise-Specific Requirements:**

| Requirement | For | Research Needed |
|-------------|-----|-----------------|
| **Dining Time** | Traditional dining | Seating time? |
| **Table Size** | Traditional dining | Small/large table? |
| **Cabin Assignment** | Specific cabin vs. guarantee | Preference? |
| **Travel Insurance** | Strongly recommended | Mandatory? |
| **Medical Disclosure** | Some destinations | Required? |
| **Visa Information** | International | Due when? |

### B. Payment Structures

**Deposit Models by Cruise Line:**

| Model | Typical Amount | When Due | Balance Due | Research Needed |
|-------|----------------|----------|-------------|-----------------|
| **Percentage** | 15-25% | At booking | 75-120 days before | Varies by line? |
| **Fixed Amount** | $250-500/person | At booking | 75-120 days before | For short cruises? |
| **Full Payment** | 100% | At booking | N/A | Last-minute? |
| **Installment** | Spread | Scheduled | Final before travel | Some lines offer? |

**Payment Timing by Days Before Travel:**

| Days Before | Payment Required | Research Needed |
|-------------|------------------|-----------------|
| **120+ days** | Deposit only | Standard? |
| **90-120 days** | 50% of total | Some lines? |
| **75-90 days** | Final payment | Most lines? |
| **60-75 days** | Final payment | Some lines? |
| **< 60 days** | 100% at booking | Last-minute? |

**Research:**
- What are industry standard deposit amounts?
- How do payment terms vary by cruise line?
- What about different cabin categories?
- What about solo travelers (single supplement)?

### C. Booking Flow

**Standard Booking Flow:**

```
1. Review Cruise & Cabin
   - Customer views cruise details
   - Selects cabin category
   - Chooses specific cabin

2. Enter Passenger Details
   - Lead passenger info
   - All passenger details
   - Passport information
   - Emergency contacts

3. Select Options
   - Dining preference
   - Beverage packages
   - Wi-Fi packages
   - Special occasions
   - Accessibility needs

4. Review & Upgrade
   - Review booking summary
   - Select optional add-ons
   - Add special requests

5. Payment
   - Pay deposit or full amount
   - Select payment method
   - Get payment confirmation

6. Booking Confirmation
   - Receive booking reference
   - Get initial documents
   - Payment receipt
   - Next steps

7. Pre-Departure
   - Balance payment reminder
   - Online check-in opens
   - Final documents sent
   - Shore excursion booking
```

**Online Check-in Flow:**

```
1. Check-in Opens (usually 30-60 days before)
   - Passenger enters booking reference
   - Completes missing information

2. Additional Information
   - Passport photo upload
   - Travel address
   - Emergency contact update
   - Credit card for onboard account

3. Select Arrival Time
   - Choose arrival time at port
   - Select transportation option

4. Complete Check-in
   - Receive boarding pass
   - Get luggage tags
   - Arrival instructions

5. Boarding Day
   - Arrive at selected time
   - Drop luggage
   - Check-in at terminal
   - Receive cabin key
   - Board ship
```

### D. Confirmation & Documents

**Initial Confirmation:**

| Element | Timing | Content | Research Needed |
|---------|--------|---------|-----------------|
| **Booking Reference** | Immediate | Unique ID | Format? |
| **Cruise Details** | Immediate | Ship, dates, itinerary | Summary |
| **Cabin Details** | Immediate | Category, number | Deck plan? |
| **Passenger List** | Immediate | All passengers | Editable? |
| **Payment Receipt** | Immediate | Amount paid | Tax invoice? |
| **Next Steps** | Immediate | Balance due, check-in dates | Clear timeline? |

**Final Travel Documents:**

| Document | Timing | Content | Delivery Method | Research Needed |
|----------|--------|---------|-----------------|-----------------|
| **Boarding Pass** | After check-in | QR code, terminal info | App/email | ? |
| **Luggage Tags** | After check-in | Cabin number, tags | Mail/email | ? |
| **Detailed Itinerary** | 2-4 weeks before | Day-by-day, ports | Email/app | ? |
| **Terminal Info** | 2 weeks before | Parking, arrival | Email | ? |
| **Shore Excursions** | Anytime | Pre-booked excursions | App/email | ? |
| **Travel Insurance** | If purchased | Policy details | Email | ? |
| **Visa Info** | If required | Visa requirements | Email | ? |

---

## State Machine

**Cruise Booking States:**

```
DRAFT → PENDING_DEPOSIT → DEPOSIT_RECEIVED → CONFIRMED →
                              → BALANCE_DUE → BALANCE_RECEIVED →
                                               → CHECK_IN_OPEN →
                                               → CHECKED_IN →
                                               → FINALIZED →
                                                                   → BOARDED →
                                                                   → TRAVELLED →
                                                                   → COMPLETED
```

**State Definitions:**

| State | Description | Customer Actions |
|-------|-------------|------------------|
| **DRAFT** | Booking in progress | Continue, save, abandon |
| **PENDING_DEPOSIT** | Waiting for deposit | Pay deposit |
| **DEPOSIT_RECEIVED** | Deposit paid, cabin held | Add passengers, modify |
| **CONFIRMED** | Booking confirmed with line | Pay balance, add-ons |
| **BALANCE_DUE** | Balance payment approaching | Pay balance |
| **BALANCE_RECEIVED** | Fully paid | Complete check-in |
| **CHECK_IN_OPEN** | Online check-in available | Complete check-in |
| **CHECKED_IN** | Check-in completed | Wait for travel |
| **FINALIZED** | All documents ready | Pack and go |
| **BOARDED** | Passenger on ship | Enjoy cruise |
| **TRAVELLED** | Cruise completed | Review, feedback |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface CruiseBooking {
  id: string;
  cruiseId: string;
  cabinId: string;
  status: BookingStatus;

  // Passengers
  leadPassenger: PassengerDetails;
  passengers: PassengerDetails[];

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

  // Cabin & Dining
  cabinNumber?: string;
  diningPreference: DiningPreference;
  tableSize?: TableSize;
  specialRequests?: string[];

  // Options
  beveragePackage?: BeveragePackage;
  wifiPackage?: WifiPackage;
  excursions?: ShoreExcursion[];

  // Onboard Account
  onboardAccount?: {
    cardDetails: string; // Encrypted
    limit?: Money;
  };

  // Documents
  documents: BookingDocument[];

  // Check-in
  checkInCompleted: boolean;
  checkInDate?: Date;
  arrivalTime?: string;
  boardingPass?: string;
}

type BookingStatus =
  | 'draft'
  | 'pending_deposit'
  | 'deposit_received'
  | 'confirmed'
  | 'balance_due'
  | 'balance_received'
  | 'check_in_open'
  | 'checked_in'
  | 'finalized'
  | 'boarded'
  | 'travelled'
  | 'cancelled'
  | 'refunded';

interface PassengerDetails {
  title: string;
  firstName: string;
  lastName: string;
  dateOfBirth: Date;
  citizenship: string;
  passportNumber: string;
  passportExpiry: Date;
  passportIssuingCountry: string;

  contactEmail: string;
  contactPhone: string;

  emergencyContact: {
    name: string;
    relationship: string;
    phone: string;
  };

  dietaryRequirements?: string;
  accessibilityNeeds?: string;
  medicalConditions?: string; // If required
}

type DiningPreference =
  | 'early' // 6-6:30pm
  | 'late' // 8-8:30pm
  | 'anytime' // Flexible dining
  | 'not_selected';

type TableSize =
  | 'small' // 2-4
  | 'large' // 6-10
  | 'any';

interface BeveragePackage {
  type: BeveragePackageType;
  price: Money;
  included: boolean; // Part of fare or add-on
}

type BeveragePackageType =
  | 'none'
  | 'classic' // Up to $12 drinks
  | 'premium' // Up to $15 drinks
  | 'ultimate'; // All drinks

interface ShoreExcursion {
  id: string;
  portId: string;
  name: string;
  price: Money;
  duration: number; // hours
  difficulty?: 'easy' | 'moderate' | 'strenuous';
  booked: boolean;
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
  | 'boarding_pass'
  | 'luggage_tags'
  | 'detailed_itinerary'
  | 'terminal_info'
  | 'shore_excursion_vouchers';
```

---

## Open Problems

### 1. Cabin Guarantee
**Challenge:** Some bookings are "guarantee" - cabin assigned later

**Options:**
- Clear disclosure
- Show potential categories
- Upgrade possibility as incentive
- Allow specific cabin for fee

### 2. Dining Seating
**Challenge:** Traditional dining requires assigned time and table

**Options:**
- Pre-assign at booking
- Select during check-in
- Choose anytime dining
- Mix of options

### 3. Single Supplement
**Challenge:** Solo travelers pay nearly double

**Options:**
- Show solo fare clearly
- Highlight solo-friendly cabins
- Find single share options
- Discounted solo promotions

### 4. Onboard Account
**Challenge:** Passengers need credit card on file for purchases

**Options:**
- Collect at booking
- Collect at check-in
- Cash deposit option
- Pre-paid limit

---

## Competitor Research Needed

| Competitor | Booking Flow | Check-in Process | Notable Patterns |
|------------|--------------|------------------|------------------|
| **Expedia Cruises** | ? | ? | ? |
| **CruiseDirect** | ? | ? | ? |
| **Direct from Line** | ? | ? | ? |

---

## Experiments to Run

1. **Booking usability test:** How smooth is the flow?
2. **Check-in usability test:** Can customers complete check-in?
3. **Cabin selection test:** Do customers understand guarantee vs. specific?
4. **Dining preference test:** How do customers choose dining options?

---

## References

- [Cruise - Providers](./CRUISE_01_PROVIDERS.md) — Cabin categories
- [Cruise - Search](./CRUISE_02_SEARCH.md) — Cabin selection
- [Package Tours - Booking](./PACKAGE_TOURS_03_BOOKING.md) — Similar booking flow

---

## Next Steps

1. Design booking flow
2. Implement payment integration
3. Build check-in system
4. Create document generation
5. Test end-to-end flow

---

**Status:** Research Phase — Booking flow unknown

**Last Updated:** 2026-04-27
