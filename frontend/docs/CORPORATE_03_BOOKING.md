# Corporate Travel 03: Booking Flow

> Corporate booking process and traveler experience

---

## Document Overview

**Focus:** How corporate travelers book travel
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Booking Process
- How does corporate booking differ from leisure?
- What information is required?
- How do we integrate approvals?
- What about payment methods?

### 2. Search & Selection
- How do corporate travelers search?
- What about preferred suppliers?
- How do we show policy compliance?
- What about negotiated rates?

### 3. Payment Methods
- What are corporate payment options?
- How do we handle individual vs. central billing?
- What about travel cards?
- How do we handle receipts and invoices?

### 4. Post-Booking
- What information do travelers need?
- How do we handle itineraries?
- What about expense reports?
- How do we track for duty of care?

---

## Research Areas

### A. Booking Requirements

**Required Information:**

| Field | Corporate vs Leisure | Notes | Research Needed |
|-------|---------------------|-------|-----------------|
| **Traveler details** | Same | Name, contact | ? |
| **Business justification** | Corporate | Reason for travel | Required? |
| **Cost center** | Corporate | For expense allocation | Required? |
| **Project code** | Corporate | For billing | Optional? |
| **Approval reference** | Corporate | If pre-approved | Auto-populate? |

**Corporate-Specific Fields:**

| Field | Description | Required? | Research Needed |
|-------|-------------|-----------|-----------------|
| **Cost center** | Accounting code | Often | ? |
| **Project code** | Project billing | Sometimes | ? |
| **Business purpose** | Reason for travel | Usually | ? |
| **Client code** | If client billable | Sometimes | ? |
| **Approval ID** | Pre-approval reference | If applicable | ? |

### B. Search & Selection

**Search Behavior:**

| Aspect | Corporate Traveler | Research Needed |
|--------|-------------------|-----------------|
| **Flexibility** | Less flexible (dates set by meetings) | ? |
| **Price sensitivity** | Mixed (policy limits vs. convenience) | ? |
| **Preferred suppliers** | Often required or encouraged | Incentives? |
| **Booking timing** | Often last-minute | ? |

**Display Differences:**

| Element | Leisure Display | Corporate Display | Research Needed |
|---------|----------------|-------------------|-----------------|
| **Price** | Prominent | Within policy context | ? |
| **Policy status** | Not applicable | Compliant/Not compliant indicator | ? |
| **Preferred** | Not applicable | Badge for preferred suppliers | ? |
| **Approval** | Not applicable | Shows if pre-approved or needs approval | ? |

**Policy Indicators:**

| Status | Display | Color | Research Needed |
|--------|---------|-------|-----------------|
| **Within policy** | "Within policy" or green badge | Green | ? |
| **Outside policy** | "Outside policy - approval needed" | Yellow/Red | ? |
| **Preferred** | "Preferred supplier" badge | Blue | ? |
| **Negotiated rate** | "Corporate rate - ₹X" | Highlighted | ? |

### C. Payment Methods

**Payment Options:**

| Method | Description | When Used | Research Needed |
|--------|-------------|-----------|-----------------|
| **Corporate card** | Company-issued card | Most common | ? |
| **Personal card + reimbursement** | Employee pays, gets reimbursed | Common for small companies | ? |
| **Central billing** | Direct bill to company | Large enterprises | ? |
| **Travel account** | Pre-funded corporate account | Some companies | ? |
| **Virtual card** | Single-use digital card | Growing trend | ? |

**Corporate Cards:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Individual liability** | Employee liable, reimbursed | ? |
| **Central liability** | Company liable, no reimbursement | More common? |
| **Hybrid** | Company for travel, employee for incidentals | ? |

**Receipt Management:**

| Requirement | Description | Research Needed |
|-------------|-------------|-----------------|
| **E-receipts** | Digital receipts | Automatic? |
| **Itemized receipts** | Line-item breakdown | Required for expense? |
| **Invoice** | Company invoice | For central billing? |
| **GST invoice** | Tax invoice | India specific? |

### D. Post-Booking

**Traveler Documentation:**

| Document | Content | Delivery | Research Needed |
|----------|---------|----------|-----------------|
| **Itinerary** | Trip details, bookings | App, email | ? |
| **Booking confirmations** | Supplier confirmations | App, email | ? |
| **Policy summary** | What's allowed, per diem | App | ? |
| **Emergency contacts** | Company support, travel provider | App | ? |
| **Expense report** | Pre-populated expense data | App/email | ? |

**Duty of Care Tracking:**

| Data Point | Source | Use | Research Needed |
|------------|--------|-----|-----------------|
| **Location** | Flight, hotel bookings | Crisis response | Real-time? |
| **Contact** | Traveler profile | Emergency communication | ? |
| **Itinerary** | All bookings | Know where travelers are | ? |

**Expense Integration:**

| Data Point | Source | Use | Research Needed |
|------------|--------|-----|-----------------|
| **Booking total** | Our system | Pre-populate expense | ? |
| **Itemized costs** | Supplier receipts | Accurate expenses | ? |
| **Policy compliance** | Our system | Flag violations | ? |

---

## Booking Flow

**Standard Corporate Booking Flow:**

```
1. Search
   - Enter trip details
   - See policy-compliant options first
   - View preferred suppliers

2. Select Option
   - View details with policy status
   - See if approval needed
   - Check negotiated rates

3. Enter Details
   - Traveler details (auto-filled from profile)
   - Business purpose
   - Cost center, project code

4. Review
   - Trip summary
   - Total cost
   - Policy compliance
   - Payment method

5. Approval (if needed)
   - Submit for approval
   - Wait for decision
   - Receive notification

6. Payment
   - Select payment method
   - Complete payment
   - Receive confirmation

7. Post-Booking
   - Itinerary sent
   - Expense data prepared
   - Location tracked for duty of care
```

**Pre-Approved Booking Flow:**

```
1. Trip already approved (approval ID)
2. Search within approval parameters
3. Book (auto-approved within limits)
4. Payment
5. Confirmation
```

---

## State Machine

**Corporate Booking States:**

```
SEARCHING → SELECTED → DETAILS_ENTERED →
                                 ├── WITHIN_POLICY → PAYMENT → CONFIRMED
                                 ├── NEEDS_APPROVAL → SUBMITTED_FOR_APPROVAL →
                                 │                                                      ├── APPROVED → PAYMENT → CONFIRMED
                                 │                                                      └── REJECTED → CANCELLED
                                 └── OUTSIDE_POLICY → WARNING_ACKNOWLEDGED →
                                                                                  ├── PROCEED → NEEDS_APPROVAL
                                                                                  └── CANCELLED
```

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface CorporateBooking {
  id: string;
  companyId: string;
  tripId: string;

  // Requester
  requesterId: string;
  travelerId: string; // May be different

  // Business details
  businessPurpose: string;
  costCenter: string;
  projectCode?: string;
  clientCode?: string;
  approvalId?: string;

  // Booking details
  flights: CorporateFlightBooking[];
  hotels: CorporateHotelBooking[];
  other: CorporateOtherBooking[];

  // Policy
  policyCompliance: PolicyCompliance;

  // Payment
  paymentMethod: CorporatePaymentMethod;
  paymentStatus: PaymentStatus;

  // Expense
  expenseReport?: {
    reportId?: string;
    exportedAt?: Date;
    system?: string; // e.g., SAP, Concur
  };

  // Duty of care
  dutyOfCare: {
    itineraryShared: boolean;
    locationTracked: boolean;
    emergencyContactNotified: boolean;
  };
}

interface CorporateFlightBooking {
  bookingId: string;
  flightId: string;

  // Corporate details
  ticketDesignator: string; // Corporate fare code
  corporateFare: boolean;
  negotiatedRate?: Money;

  // Policy
  withinPolicy: boolean;
  policyException?: string;

  // Expense
  costCenter: string;
  projectCode?: string;
  billable: boolean;
}

type CorporatePaymentMethod =
  | { type: 'corporate_card'; cardId: string; holder: 'company' | 'employee' }
  | { type: 'personal_card'; cardId: string; reimbursable: true }
  | { type: 'central_billing'; billingAccountId: string }
  | { type: 'virtual_card'; virtualCardId: string }
  | { type: 'travel_account'; accountId: string };

interface CorporateReceipt {
  bookingId: string;

  // Receipt data
  receiptNumber: string;
  issuedAt: Date;
  totalAmount: Money;
  taxAmount: Money;
  currency: string;

  // GST (India)
  gstin?: string; // GST Number
  gstAmount?: Money;

  // Line items
  lineItems: ReceiptLineItem[];

  // Export
  exportedTo?: string; // Expense system
  exportedAt?: Date;
}

interface ReceiptLineItem {
  description: string;
  quantity: number;
  unitPrice: Money;
  amount: Money;
  taxCode?: string;
}
```

---

## Open Problems

### 1. Policy vs. User Preference
**Challenge**: Travelers prefer options outside policy

**Options**:
- Show compliant options first
- Clear disclosure of out-of-policy
- Allow with justification + approval
- Track policy violations

### 2. Payment Complexity
**Challenge**: Multiple payment methods, reimbursement needed

**Options**:
- Support all common methods
- Clear reimbursement timeline
- Automated expense reporting
- Receipt management

### 3. Booking Friction
**Challenge**: Corporate travel has more steps than leisure

**Options**:
- Auto-fill from profiles
- Streamlined approval
- Mobile-first design
- Quick rebooking

### 4. Duty of Care Privacy
**Challenge**: Tracking location vs. privacy concerns

**Options**:
- Clear disclosure
- Opt-in where possible
- Track only booking data
- Emergency access only

---

## Competitor Research Needed

| Competitor | Booking UX | Notable Patterns |
|------------|------------|------------------|
| **Concur** | ? | ? |
| **TravelPerk** | ? | ? |
| **Navan** | ? | ? |

---

## Experiments to Run

1. **Booking usability test**: How smooth is corporate booking?
2. **Policy clarity test**: Do travelers understand policy indicators?
3. **Payment preference test**: What payment methods do travelers prefer?
4. **Receipt test**: How do travelers use receipts?

---

## References

- [Corporate Travel - Requirements](./CORPORATE_01_REQUIREMENTS.md) — Policy structures
- [Corporate Travel - Approvals](./CORPORATE_02_APPROVALS.md) — Approval workflows
- [Payment Processing](./PAYMENT_PROCESSING_MASTER_INDEX.md) — Payment methods

---

## Next Steps

1. Design corporate booking flow
2. Build policy compliance engine
3. Implement payment methods
4. Create receipt management
5. Test booking UX

---

**Status**: Research Phase — Booking patterns unknown

**Last Updated**: 2026-04-27
