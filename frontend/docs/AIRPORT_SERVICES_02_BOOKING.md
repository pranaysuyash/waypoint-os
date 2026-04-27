# Airport Services 02: Availability & Booking

> Checking availability and booking airport services

---

## Document Overview

**Focus:** How customers discover and book airport services
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Availability Checking
- How do we check real-time availability?
- What are the capacity constraints?
- How do we handle sold-out scenarios?
- What are the booking windows?

### 2. Booking Flow
- What information is needed to book?
- How do we handle flight details?
- What about passenger details?
- How do we handle timing constraints?

### 3. Pricing
- How are prices determined? (Dynamic vs. static?)
- What about child pricing?
- What about group discounts?
- What are the fees?

### 4. Confirmation
- How are bookings confirmed?
- What are the delivery methods?
- What information must be on the confirmation?
- How do we handle last-minute bookings?

---

## Research Areas

### A. Availability by Service Type

| Service Type | Availability Model | Constraints | Research Needed |
|--------------|-------------------|-------------|-----------------|
| **Lounge access** | Capacity-based | Max pax, time limits | ? |
| **Fast track** | Usually available | Operating hours | ? |
| **Meet & greet** | Staff-dependent | Advance notice | ? |
| **Baggage service** | Capacity-based | Size/weight limits | ? |

**Research:**
- How far in advance can bookings be made?
- What are the same-day booking rules?
- How do we handle cancellations?

### B. Booking Requirements

**Required Information:**

| Field | Required | Purpose |
|-------|----------|---------|
| **Flight details** | Yes | Verify eligibility, timing |
| **Airport/terminal** | Yes | Service location |
| **Date/time** | Yes | Service availability |
| **Passenger count** | Yes | Capacity |
| **Contact details** | Yes | Communication |

**Optional Information:**

| Field | Why Optional |
|-------|-------------|
| **Frequent flyer number** | May affect access/price |
| **Special assistance** | May affect service needed |
| **Membership number** | May provide access |

### C. Pricing Models

**Pricing Factors:**

| Factor | Impact | Examples |
|--------|--------|----------|
| **Airport** | High | Major hubs cost more |
| **Service type** | Medium | Lounge > Fast track |
| **Time of day** | Low | Peak may cost more |
| **Advance booking** | Low | Earlier may be cheaper |
| **Quantity** | Low | Group discounts |

**Sample Pricing:**

| Service | Airport | Price Range | Notes |
|---------|---------|-------------|-------|
| **Lounge access** | DEL | ₹1,500-3,000 | 2-3 hours |
| **Fast track** | DEL | ₹500-1,500 | Security only |
| **Meet & greet** | DEL | ₹2,000-5,000 | Arrival |
| **Buggy** | DEL | ₹500-1,500 | Within terminal |

**Research:**
- What are the actual prices?
- How do prices vary by airport?
- Are there dynamic pricing models?

### D. Confirmation Delivery

**Delivery Methods:**

| Method | Used For | Timing |
|--------|----------|--------|
| **QR code** | Most services | Instant |
| **Print at home** | Some services | Instant |
| **Email** | All services | Immediate |
| **Collect at counter** | Some services | On arrival |

**Confirmation Content:**

| Field | Always Included | Notes |
|-------|-----------------|-------|
| **Service name** | ✓ | Clear description |
| **Airport/terminal** | ✓ | Exact location |
| **Date/time** | ✓ | Valid period |
| **Booking reference** | ✓ | For support |
| **Instructions** | ✓ | How to access |
| **QR/barcode** | Most | For scanning |
| **Emergency contact** | ✓ | Support number |

---

## Booking Data Model

```typescript
interface AirportServiceBooking {
  id: string;
  tripId?: string;
  customerId: string;

  // Service
  service: AirportService;
  provider: string;

  // Flight details
  flight: {
    airline: string;
    flightNumber: string;
    date: Date;
    departure?: string;
    arrival?: string;
    terminal?: string;
  };

  // Booking
  passengers: number;
  date: Date;
  time?: Time;
  duration?: Duration;  // For lounge access

  // Status
  status: BookingStatus;
  bookedAt: Date;

  // Pricing
  pricing: {
    basePrice: Money;
    taxes: Money;
    fees: Money;
    total: Money;
    currency: string;
  };

  // Confirmation
  confirmation: {
    reference: string;
    qrCode?: string;
    instructions: string[];
    deliveredAt: Date;
  };
}

type BookingStatus =
  | 'pending'
  | 'confirmed'
  | 'checked_in'
  | 'used'
  | 'cancelled'
  | 'refunded';
```

---

## Booking State Machine

```
SELECTED → VALIDATING_FLIGHT → COLLECTING_INFO → PAYMENT_PROCESSING
                                                           ↓
                                                CONFIRMED → DELIVERED
                                                           ↓
                                                       USED → COMPLETED
        ↓           ↓              ↓              ↓
     ABANDONED  FLIGHT_INVALID   PAYMENT_FAILED    BOOKING_FAILED
```

---

## Open Problems

### 1. Flight Changes
**Challenge:** Customer books lounge, flight changes terminal

**Options:**
- Rebook automatically
| Offer refund
| Credit for future use

**Research:** How do providers handle this?

### 2. No-Show
**Challenge:** Customer books but doesn't use

**Questions:**
- Is the booking chargeable?
| Can they get a refund?
| How do we verify usage?

### 3. Overbooking
**Challenge:** Lounge is full when customer arrives

**Options:**
- Guaranteed access (we pay for alternative)
| Best efforts
| Partial refund

### 4. Same-Day Booking
**Challenge:** Customer wants to book lounge for flight in 2 hours

**Questions:**
- Is this allowed?
| How do we confirm in time?
| What if booking fails?

---

## Competitor Research Needed

| Competitor | Booking UX | Notable Patterns |
|------------|-----------|------------------|
| **Priority Pass** | ? | ? |
| **Airline websites** | ? | ? |
| **Airport websites** | ? | ? |

---

## Experiments to Run

1. **API availability test:** Which providers have bookable APIs?
2. **Same-day booking test:** Can we book day-of?
3. **Price accuracy study:** Do quoted prices match final?
4. **Cancellation test:** How smooth is cancellation?

---

## References

- [Activities - Booking](./ACTIVITIES_03_BOOKING.md) — Similar booking patterns
| [Ground Transportation - Booking](./GROUND_TRANSPORTATION_03_BOOKING.md) — Similar patterns

---

## Next Steps

1. Test provider booking APIs
2. Design booking flow
3. Build availability checker
4. Implement confirmation delivery
5. Create cancellation process

---

**Status:** Research Phase — Booking patterns unknown

**Last Updated:** 2026-04-27
