# Group Travel 05: Operations

> Modifications, cancellations, and group support

---

## Document Overview

**Focus:** Managing group bookings after confirmation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Modifications
- What changes can groups make?
- How do modification fees work?
- What about attrition?
- How do we handle room count changes?

### Cancellations
- What are group cancellation policies?
- How do refunds work?
- What about force majeure?
- What if organizer cancels?

### During Travel
- How do we support groups during travel?
- What if there are issues?
- How do we handle emergencies?
- What about on-ground problems?

### Post-Travel
- How do we collect feedback?
- What about disputes?
- How do we handle settlement?
- What about future bookings?

---

## Research Areas

### A. Modification Rules

**Allowed Changes:**

| Change | Timing | Fee | Research Needed |
|--------|--------|-----|-----------------|
| **Increase rooms** | Until cutoff | Price difference | ? |
| **Decrease rooms** | Until attrition deadline | Possibly | ? |
| **Name changes** | Until manifest due | Maybe | ? |
| **Date changes** | Early only | High fee | ? |

**Attrition:**

| Attrition Clause | Description | Research Needed |
|-----------------|-------------|-----------------|
| **10%** | Can reduce 10% free | Standard? |
| **20%** | Can reduce 20% free | Generous? |
| **None** | Pay for all booked | Strict? |

### B. Cancellation Policies

**Standard Group Cancellation:**

| Days Before | Refund | Research Needed |
|-------------|--------|-----------------|
| **120+ days** | Full refund less deposit | ? |
| **90-120 days** | 50% refund | ? |
| **60-90 days** | 25% refund | ? |
| **< 60 days** | No refund | ? |

**Deposit Refund:**

| Timing | Deposit Refund | Research Needed |
|--------|----------------|-----------------|
| **> 90 days** | Full refund | ? |
| **60-90 days** | 50% refund | ? |
| **< 60 days** | Forfeited | ? |

### C. During Travel Support

**Common Issues:**

| Issue | Frequency | Resolution | Research Needed |
|-------|-----------|------------|-----------------|
| **Room problems** | Medium | Move rooms | ? |
| **Guest disputes** | Low | Mediation | ? |
| **Transport issues** | Medium | Alternative arrangements | ? |
| **Activity cancellations** | Low | Refund or reschedule | ? |
| **Medical emergencies** | Low | Medical assistance | ? |

**Support Levels:**

| Level | Issues | Resolution | Research Needed |
|-------|--------|------------|-----------------|
| **Self-service** | FAQs, info | Guest portal | ? |
| **On-site coordinator** | Most issues | Immediate resolution | ? |
| **Our support** | Escalations | Remote support | ? |
| **Emergency** | Medical, safety | 24/7 response | ? |

### D. Post-Travel

**Feedback Collection:**

| Method | Timing | Research Needed |
|--------|--------|-----------------|
| **In-trip survey** | During travel | Immediate feedback | ? |
| **Post-trip survey** | 1 week after | Detailed feedback | ? |
| **Organizer feedback** | 2 weeks after | Business feedback | ? |

**Settlement:**

| Item | Timing | Research Needed |
|------|--------|-----------------|
| **Final invoice** | Post-trip | Any adjustments? |
| **Refunds** | If applicable | Timeline? |
| **Deposits returned** | If applicable | Security deposits? |

---

## Data Model Sketch

```typescript
interface GroupModification {
  id: string;
  bookingId: string;
  type: ModificationType;
  status: ModificationStatus;

  // Changes
  originalRooms: number;
  newRooms: number;
  priceAdjustment: Money;
  modificationFee: Money;

  // Processing
  requestedAt: Date;
  processedAt?: Date;
}

type ModificationType =
  | 'increase_rooms'
  | 'decrease_rooms'
  | 'date_change'
  | 'name_changes';

interface GroupCancellation {
  id: string;
  bookingId: string;
  reason: CancellationReason;

  // Refund
  refundAmount: Money;
  refundPercentage: number;
  depositForfeited: Money;

  // Guests
  notifyGuests: boolean;
  guestRefunds?: GuestRefund[];

  // Processing
  requestedAt: Date;
  processedAt?: Date;
}

interface GuestRefund {
  guestId: string;
  amount: Money;
  method: string;
}
```

---

## Open Problems

### 1. Attrition Management
**Challenge:** Groups drop below minimum

**Options:** Attrition clauses, renegotiated pricing, cancellation

### 2. Partial Cancellation
**Challenge:** Some guests cancel

**Options:** Replace guests, adjust pricing, no refund

### 3. On-Site Issues
**Challenge:** Problems during travel

**Options:** On-site coordinator, local contacts, insurance

### 4. Dispute Resolution
**Challenge:** Post-trip disagreements

**Options:** Clear contracts, documentation, mediation

---

## Next Steps

1. Define modification policies
2. Build cancellation system
3. Create on-site support protocols
4. Design feedback collection

---

**Status:** Research Phase — Operations patterns unknown

**Last Updated:** 2026-04-27
