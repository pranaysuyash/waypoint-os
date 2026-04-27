# Loyalty Programs 03: Redemption & Burning

> Using points for bookings and maximizing value

---

## Document Overview

**Focus**: How customers use and redeem loyalty points
**Status**: Research Exploration
**Last Updated**: 2026-04-27

---

## Key Questions to Answer

### 1. Redemption Options
- How can points be redeemed? (Flights, hotels, upgrades?)
- What are the redemption rates?
- What are the blackout dates?
- How do we handle partial cash + points?

### 2. Booking with Points
- How do we search for award availability?
- How do we handle different award charts?
- What about partner redemptions?
- How do we handle taxes and fees?

### 3. Point Transfers
- How do points transfer between programs?
- What are the transfer ratios?
- What are the transfer times?
- What are the transfer limits?

### 4. Value Optimization
- How do customers maximize point value?
- What are the best redemption values?
- What are the worst values?
- How do we recommend optimal redemptions?

---

## Research Areas

### A. Award Availability

**Award Space Types:**

| Type | Availability | Advance Booking | Notes |
|------|--------------|-----------------|-------|
| **Saver awards** | Limited | 330-360 days | Best value |
| **Standard awards** | Better | Shorter notice | Medium value |
| **Anytime awards** | Usually available | Any time | Worst value |
| **Partner awards** | Variable | Varies | Good value |

**Research:**
- How do we check award availability?
- What are the booking windows?
- How do we handle lack of availability?

### B. Redemption Pricing

**Award Charts:**

| Program | Pricing Model | Examples | Research Needed |
|----------|---------------|----------|-----------------|
| **Most airlines** | Zone/distance based | 12.5K-50K miles one-way | ? |
| **Some airlines** | Revenue-based | Varies by cash price | ? |
| **Hotels** | Category based | 5K-100K points/night | ? |

**Cash + Points:**

| Program | Split Payment | Minimum Points | Notes |
|----------|---------------|-----------------|-------|
| **Some airlines** | Yes | Varies | ? |
| **Some hotels** | Yes | Varies | ? |
| **Many programs** | No | N/A | All points or all cash |

### C. Transfer Partners

**Transfer Partnerships:**

| Program | Transfer To | Ratio | Time | Notes |
|---------|-------------|-------|------|-------|
| **Amex** | Airlines, hotels | Varies | Instant | ? |
| **Chase** | Airlines, hotels | Varies | Instant | ? |
| **Capital One** | Airlines, hotels | Varies | Instant | ? |
| **Indian cards** | ? | ? | ? | ? |

**Transfer Considerations:**

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Transfer ratio** | Value calculation | ? |
| **Transfer time** | Availability risk | ? |
| **Transfer bonuses** | Extra value | ? |
| **Minimum transfer** | Flexibility | ? |

### D. Value Calculations

**Valuation Examples:**

| Redemption | Points Required | Cash Value | Point Value |
|------------|-----------------|------------|-------------|
| **Economy flight India-Singapore** | 25K miles | ₹15,000 | ₹0.60/point |
| **Business class flight** | 60K miles | ₹60,000 | ₹1.00/point |
| **Hotel night (category 4)** | 25K points | ₹10,000 | ₹0.40/point |
| **Merchandise** | Varies | Usually low | < ₹0.30/point |

**Best Redemption Types:**
- International business class
| Premium cabin upgrades
| Category 5+ hotels
| Experience bookings

**Worst Redemption Types:**
- Merchandise
| Gift cards (usually)
| Economy domestic (sometimes)

---

## Redemption Data Model

```typescript
interface LoyaltyRedemption {
  id: string;
  customerId: string;
  bookingId?: string;

  // Source
  sourceProgram: string;
  sourceAccount: string;

  // Redemption
  type: RedemptionType;
  pointsUsed: number;
  cashPaid?: Money;

  // Value
  cashValue: Money;
  pointValue: Money;  // Calculated value per point

  // Booking
  booking: {
    type: 'flight' | 'hotel' | 'upgrade' | 'transfer';
    details: any;
    confirmation?: string;
  };

  // Status
  status: RedemptionStatus;
  processedAt: Date;
  confirmedAt?: Date;
}

type RedemptionType =
  | 'award_booking'
  | 'cash_and_points'
  | 'upgrade'
  | 'transfer'
  | 'merchandise';

type RedemptionStatus =
  | 'pending'
  | 'processing'
  | 'confirmed'
  | 'ticketed'
  | 'cancelled'
  | 'failed';
```

---

## Redemption Flow

**Award Booking:**

```
1. Customer selects "Book with Points"
2. Search for award availability
3. Select option
4. Authorize points deduction
5. Points placed on hold
6. Booking confirmed
7. Points deducted
8. Ticket/confirmation issued
```

**Points + Cash:**

```
1. Customer selects split payment
2. System calculates required points and cash
3. Customer authorizes both
4. Points deducted, payment processed
5. Booking confirmed
```

---

## Open Problems

### 1. Award Availability
**Challenge**: No award seats on desired flight

**Options:**
- Show alternative dates
- Partner airlines
| Cash + points
| Waitlists (rare now)

### 2. Point Reversal
**Challenge**: Booking cancelled, points return

**Questions:**
- Do points refund fully?
- Is there a fee?
| How long does refund take?

### 3. Taxes on Awards
**Challenge**: "Free" awards still have taxes

**Education needed:**
- Award taxes vs. cash tickets
| Fuel surcharges
| Airport fees

### 4. Transfer Reversal
**Challenge**: Points transferred, want to reverse

**Questions:**
- Is reversal possible?
| What are the fees?
| How long does it take?

---

## Competitor Research Needed

| Competitor | Redemption UX | Notable Patterns |
|------------|---------------|------------------|
| **AwardWallet** | ? | ? |
| **UsingMiles** | ? | ? |
| **Airline sites** | ? | ? |

---

## Experiments to Run

1. **Award availability test**: How hard is it to find awards?
2. **Value comparison test**: Which redemptions offer best value?
3. **Transfer test**: How do transfers work?
4. **Cancellation test**: How do refunds work?

---

## References

- [Flight Integration - Ticketing](./FLIGHT_INTEGRATION_05_TICKETING.md) — Award tickets
| [Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md) — Award nights

---

## Next Steps

1. Build award search
2. Implement redemption booking
3. Create value calculator
4. Design transfer system
5. Build refund handling

---

**Status**: Research Phase — Redemption patterns unknown

**Last Updated**: 2026-04-27
