# Ground Transportation 03: Booking & Operations

> Reservation workflow, payment handling, and operational coordination

---

## Document Overview

**Focus:** Converting search selection into confirmed bookings
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Booking Data Requirements
- What information is mandatory vs. optional?
- How do we handle passenger details? (Names? Contacts? Flight numbers?)
- What about special requests? (Child seat, wheelchair, extra stops)
- How do we handle "hotel to be advised"?

### 2. Payment Flow
- When is payment taken? (Immediately? Later?)
- What payment methods work for each provider?
- How do we handle deposits vs. full payment?
- What about cash payments to drivers?

### 3. Confirmation Delivery
- How are confirmations delivered? (Email? SMS? App?)
- What information must be included?
- How do we handle vouchers vs. direct booking?
- What about driver contact information?

### 4. Operational Coordination
- How are drivers assigned?
- How do we communicate booking details to providers?
- What about meet-and-greet procedures?
- How do we handle special requests?

---

## Research Areas

### A. Booking Requirements by Transport Type

| Data Field | Private Transfer | Shared Shuttle | Rental Car | Chauffeur |
|------------|------------------|----------------|------------|----------|
| Passenger names | Required | Required | Required | Required |
| Contact number | Required | Required | Required | Required |
| Flight details | For airport | For airport | Maybe | For airport |
| Hotel name | Required | Required | Drop-off | Required |
| Special requests | Optional | Limited | Vehicle options | Yes |
| Driver details | Sent before | Sent before | N/A | Sent before |

**Research:**
- What are the minimum requirements per type?
- What happens if required info is missing?

### B. Payment Timing Models

| Model | Description | Providers Using |
|-------|-------------|-----------------|
| **Pre-pay full** | Charge at booking | Many transfers |
| **Deposit only** | Deposit now, balance later | Some chauffeurs |
| **Pay driver** | Book now, pay cash/card to driver | Some rentals |
| **Pay later** | No payment at booking | Rare |

**Research Needed:**
- Which model for which provider?
- What are the customer preferences?
- How do we handle payment failures?

### C. Confirmation Formats

**Information to Include:**

| Field | Private Transfer | Shared Shuttle | Rental Car | Chauffeur |
|-------|------------------|----------------|------------|----------|
| Booking reference | ✓ | ✓ | ✓ | ✓ |
| Provider contact | ✓ | ✓ | ✓ | ✓ |
| Driver details | ✓ | ✓ | N/A | ✓ |
| Pickup location | ✓ | ✓ | ✓ | ✓ |
| Pickup time | ✓ | ✓ | ✓ | ✓ |
| Vehicle type | ✓ | Maybe | ✓ | ✓ |
| Meeting point | ✓ | ✓ | Counter | ✓ |
| Emergency contact | ✓ | ✓ | ✓ | ✓ |
| Cancellation policy | ✓ | ✓ | ✓ | ✓ |

**Research:**
- How do we present multi-leg bookings?
- What about mobile tickets vs. printable vouchers?

### D. Provider Communication

**Communication Methods:**

| Method | When Used | Reliability |
|--------|-----------|-------------|
| **API** | Integrated providers | High |
| **Email** | Manual bookings | Medium |
| **Portal** | Some providers | Medium |
| **WhatsApp/Phone** | Last-mile, urgent | Low (unstructured) |

**Questions:**
- How do we ensure booking reached provider?
- What if provider doesn't confirm?
- How do we track confirmation status?

---

## Booking State Machine

```
PENDING → REQUESTED → CONFIRMED → DRIVER_ASSIGNED → IN_PROGRESS → COMPLETED
           ↓           ↓            ↓
        FAILED    CANCELLED    NO_SHOW
```

**States Explained:**

| State | Meaning | Next Actions |
|-------|---------|--------------|
| PENDING | Booking initiated, not sent to provider | Send to provider |
| REQUESTED | Sent to provider, awaiting confirmation | Wait/poll for response |
| CONFIRMED | Provider confirmed booking | Assign driver, send details |
| DRIVER_ASSIGNED | Driver allocated, details sent | Monitor pickup time |
| IN_PROGRESS | Journey underway | Track completion |
| COMPLETED | Journey finished | Handle feedback/reviews |
| FAILED | Provider rejected/unavailable | Offer alternatives |
| CANCELLED | Customer or provider cancelled | Process refund |
| NO_SHOW | Customer didn't appear | Handle per policy |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface TransportBooking {
  id: string;
  tripId: string;
  status: BookingStatus;

  // Journey details
  pickup: BookingLocation;
  dropoff: BookingLocation;
  stops?: BookingLocation[];
  scheduledTime: Date;

  // Provider
  provider: ProviderReference;
  type: TransportType;
  vehicle: VehicleCategory;

  // Passengers
  passengers: PassengerDetails[];
  leadPassenger: ContactInfo;

  // Flight integration (if applicable)
  flightDetails?: {
    number: string;
    arrivalTime: Date;
    terminal?: string;
  };

  // Special requests
  specialRequests?: string[];
  equipment?: EquipmentRequest[];  // Child seat, etc.

  // Pricing
  pricing: {
    quoted: Money;
    confirmed?: Money;
    paid: Money;
    remaining?: Money;
  };

  // Payment
  payment: {
    status: 'pending' | 'partial' | 'paid' | 'refunded';
    method: string;
    transactionId?: string;
  };

  // Confirmation
  confirmationCode?: string;
  providerReference?: string;
  driverInfo?: DriverDetails;

  // Policies
  cancellationPolicy: CancellationPolicy;
  amendmentPolicy: AmendmentPolicy;

  // Timeline
  createdAt: Date;
  confirmedAt?: Date;
  completedAt?: Date;
}

interface EquipmentRequest {
  type: 'child_seat' | 'wheelchair' | 'booster' | 'ski_rack';
  quantity: number;
  confirmed?: boolean;
}
```

---

## Operational Workflow

### For Private Transfer:

```
1. Customer books → Payment captured
2. Send booking to provider → Get confirmation
3. Provider assigns driver → Receive driver details
4. Send details to customer → Name, phone, vehicle plate
5. Monitor flight status (if applicable) → Adjust if delayed
6. Journey happens → Track completion
7. Post-journey → Collect feedback
```

### For Rental Car:

```
1. Customer books → Deposit/payment captured
2. Send booking to provider → Get voucher
3. Send voucher to customer → Present at counter
4. Customer picks up → Show license, voucher
5. Journey happens
6. Customer returns → Vehicle inspection
7. Final charges/refunds → Security deposit released
```

---

## Open Problems

### 1. Payment vs. Service Timing
**Challenge:** Some providers want payment at time of service, not booking

**Options:**
- Hold payment on card (authorization)
- Require payment anyway, we pay provider later
- Offer "pay later" with higher price

**Research:** What are customer expectations?

### 2. Special Requests Handling
**Challenge:** Customer requests child seat, provider doesn't confirm availability

**Options:**
- Treat as request only, not guarantee
- Confirm before booking (adds friction)
- Filter to only providers who can accommodate

**Research:** How often are special requests critical?

### 3. Multi-Currency Payments
**Challenge:** Customer pays in INR, provider wants USD/EUR

**Questions:**
- Who bears FX risk?
- What exchange rate do we use?
- How do we handle refunds?

### 4. Provider Non-Responsiveness
**Challenge:** Booking sent, provider doesn't confirm

**Questions:**
- How long do we wait?
- When do we escalate to manual?
- What do we tell customer?

---

## Disruption Handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| **Driver late** | Customer reports | Contact provider, ETA update |
| **No show** | Customer reports | Arrange alternative, refund |
| **Wrong vehicle** | Customer reports | Contact provider, replacement |
| **Driver rude** | Post-journey feedback | Flag provider, compensation? |
| **Vehicle breakdown** | Driver reports | Arrange replacement |

---

## References

- [Booking Engine - Reservation Flow](./BOOKING_ENGINE_02_RESERVATION_FLOW.md) — State patterns
- [Flight Integration - Ticketing](./FLIGHT_INTEGRATION_05_TICKETING.md) — Confirmation patterns
- [Payment Processing](./PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) — Payment flows

---

## Next Steps

1. Map booking requirements per provider
2. Design confirmation format
3. Build provider communication layer
4. Implement booking state machine
5. Design operational dashboard

---

**Status:** Research Phase — Booking flow unknown

**Last Updated:** 2026-04-27
