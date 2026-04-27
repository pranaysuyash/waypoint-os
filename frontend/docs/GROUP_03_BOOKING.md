# Group Travel 03: Booking Process

> Group booking workflow and management

---

## Document Overview

**Focus:** How groups book travel
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Booking Flow
- How does group booking differ from individual?
- What are the stages?
- How do we handle deposits?
- What about rooming lists?

### Rooming Lists
- What information is needed?
- When are they due?
- How do guests submit details?
- How do we handle changes?

### Payment Management
- How does group payment work?
- What about individual payments?
- How do we track who paid?
- What about refunds?

### Guest Communication
- How do we communicate with guests?
- What information do they need?
- How do we collect details?
- What about updates?

---

## Research Areas

### A. Booking Stages

**Stage 1: Contract & Deposit**
- Sign group contract
- Pay deposit (usually 20-30%)
- Secure space

**Stage 2: Rooming List**
- Collect guest details
- Room assignments
- Due by cutoff date

**Stage 3: Final Payment**
- Balance due (usually 30-60 days before)
- Final guest count
- Any special requests

**Stage 4: Manifest**
- Final guest details
- Special requirements
- Distribution to suppliers

### B. Rooming List Management

**Information Needed:**

| Field | Required | Notes | Research Needed |
|-------|----------|-------|-----------------|
| **Guest name** | Yes | As per ID | ? |
| **Age** | Sometimes | For pricing | ? |
| **Gender** | Sometimes | For rooming | ? |
| **Room preference** | No | Request only | ? |
| **Dietary needs** | No | For meals | ? |
| **Special requests** | No | Accessibility etc. | ? |

**Room Assignment:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Specific assignment** | Pre-assign rooms | ? |
| **Run of house** | Assigned at check-in | Common? |
| **Block assignment** | Room types guaranteed | ? |

### C. Guest Portal

**Features:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Trip details** | What, when, where | ? |
| **Payment** | Pay share | ? |
| **Roommate selection** | Choose roommates | ? |
| **Details form** | Submit information | ? |
| **Updates** | Trip updates | ? |

### D. Payment Collection

**Models:**

| Model | Description | Research Needed |
|-------|-------------|-----------------|
| **Organizer pays** | Single payment | Most common |
| **Individual payments** | Each guest pays | Growing |
| **Hybrid** | Organizer pays deposit, guests pay balance | ? |

---

## Data Model Sketch

```typescript
interface GroupBooking {
  id: string;
  groupId: string;
  status: BookingStatus;

  // Guests
  guests: GroupGuest[];

  // Rooms
  rooms: RoomBlock[];

  // Payments
  payments: GroupPayment[];

  // Timeline
  contractSignedAt?: Date;
  depositPaidAt?: Date;
  roomingListDue: Date;
  finalPaymentDue: Date;
  manifestDue: Date;
}

interface GroupGuest {
  id: string;
  bookingId: string;

  // Details
  name: string;
  email: string;
  phone: string;
  age?: number;
  gender?: string;

  // Room
  roomId?: string;
  roommateIds?: string[];

  // Preferences
  roomPreference?: string;
  dietaryRequirements?: string;
  specialRequests?: string;

  // Payment
  paymentStatus: PaymentStatus;
  amountPaid: Money;
  amountDue: Money;
}

type BookingStatus =
  | 'contract_pending'
  | 'deposit_pending'
  | 'rooming_list_pending'
  | 'final_payment_pending'
  | 'manifest_pending'
  | 'confirmed'
  | 'travelled'
  | 'cancelled';
```

---

## Open Problems

### 1. Rooming List Complexity
**Challenge:** Collecting details from many people

**Options:** Guest portal, organizer provides, deadline enforcement

### 2. Payment Collection
**Challenge:** Getting everyone to pay

**Options:** Automated reminders, guest portal, organizer covers

### 3. Changes After Deadline
**Challenge:** Guests want changes after cutoff

**Options:** Strict policy, change fees, flexibility options

### 4. No-Shows
**Challenge:** Some guests don't show up

**Options:** Attrition clauses, payment policies, clear communication

---

## Next Steps

1. Design guest portal
2. Build rooming list tools
3. Implement payment collection
4. Create communication templates

---

**Status:** Research Phase — Booking patterns unknown

**Last Updated:** 2026-04-27
