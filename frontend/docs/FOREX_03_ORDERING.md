# Forex & Currency Services 03: Ordering & Delivery

> Purchasing forex and receiving cards/currency

---

## Document Overview

**Focus:** Converting selection to delivered product
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Ordering Flow
- What information is needed to order?
- How do we handle KYC requirements?
- What about payment?
- How do we handle RBI limits?

### 2. Card Fulfillment
- How are forex cards delivered?
- What are the delivery options?
- How long does delivery take?
- What if delivery fails?

### 3. Currency Notes
- How are physical notes delivered?
| What about denominations?
| What is the secure delivery process?
| What if customer refuses delivery?

### 4. Activation
- How are forex cards activated?
| What about PIN generation?
| How do customers check balances?
| What if card doesn't work?

---

## Research Areas

### A. Ordering Requirements

**Mandatory Information:**

| Field | Purpose | Validation |
|-------|---------|------------|
| **PAN card** | KYC, RBI requirement | Must be valid |
| **Aadhaar** | KYC (sometimes) | If required |
| **Travel dates** | Purpose validation | Future dates |
| **Destination** | Currency selection | Country code |
| **Amount** | Within RBI limits | Max $2.5L/year |
| **Purpose** | RBI requirement | Travel/education/medical |

**Optional Information:**

| Field | Why Optional |
|-------|-------------|
| **Passport copy** | Sometimes required |
| **Visa copy** | For specific purposes |
| **Ticket copy** | Proof of travel |

**Research:**
- What is the minimum KYC?
- How do we validate documents?
- What are the RBI limit checks?

### B. Card Delivery

**Delivery Options:**

| Option | Timing | Cost | Research Needed |
|--------|--------|------|-----------------|
| **Courier to home** | 2-5 days | ₹200-500 | ? |
| **Branch pickup** | Same/next day | Free | ? |
| **Airport pickup** | At departure | Variable | ? |

**Delivery Process:**

```
1. Order placed → KYC verified
2. Provider processes → Card prepared
3. Card shipped → Tracking available
4. Customer receives → Activation required
5. Customer sets PIN → Card ready to use
```

**Research:**
- What are the exact timelines?
- Who are the courier partners?
- How do we track delivery?

### C. Currency Notes

**Denominations:**

| Currency | Common Denominations | Customer Preference |
|----------|---------------------|-------------------|
| **USD** | $1, $5, $10, $20, $50, $100 | Mix |
| **EUR** | €5, €10, €20, €50, €100, €200 | Mix |
| **GBP** | £5, £10, £20, £50 | Mix |

**Research:**
- Can customers request denominations?
- What are the availability constraints?
- How do we handle large amounts?

### D. Payment & Limits

**RBI Limits:**

| Purpose | Limit | Documentation |
|---------|-------|----------------|
| **Leisure travel** | $2.5L/year | Basic KYC |
| **Business travel** | $2.5L/year | Company letter |
| **Education** | Higher limits | University proof |
| **Medical** | Higher limits | Medical proof |

**Payment Methods:**

| Method | Availability | Notes |
|--------|--------------|-------|
| **UPI** | Most providers | Instant |
| **NetBanking** | All providers | 1-3 days |
| **Card** | Most providers | Instant |
| **IMPS/RTGS** | Large amounts | Bank transfer |

---

## Ordering State Machine

```
SELECTED → COLLECTING_KYC → KYC_VERIFICATION → PAYMENT_PROCESSING
                                                              ↓
                                        PROVIDER_PROCESSING → CARD_PREPARED
                                                              ↓
                                                    SHIPPED → DELIVERED
                                                              ↓
                                                    ACTIVATED → COMPLETED
      ↓           ↓              ↓              ↓                ↓
   ABANDONED   KYC_FAILED    PAYMENT_FAILED   ORDER_FAILED    DELIVERY_FAILED
```

---

## Data Model

```typescript
interface ForexOrder {
  id: string;
  tripId?: string;
  customerId: string;

  // Selection
  provider: string;
  product: ForexProductType;
  currency: string;
  amount: Money;

  // Order details
  status: OrderStatus;
  purpose: TravelPurpose;
  travelDates: DateRange;

  // KYC
  kyc: {
    panNumber: string;
    panVerified: boolean;
    documents: Document[];
    verifiedAt?: Date;
  };

  // Payment
  payment: {
    amount: Money;
    method: string;
    status: PaymentStatus;
    transactionId?: string;
  };

  // Delivery
  delivery: {
    method: DeliveryMethod;
    address?: Address;
    trackingNumber?: string;
    expectedDelivery?: Date;
    deliveredAt?: Date;
  };

  // Card specific
  card?: {
    cardNumberLast4: string;
    activationRequired: boolean;
    pinSet: boolean;
    expiresAt: Date;
  };

  // Currency specific
  currencyNotes?: {
    denominations: DenominationBreakdown;
    totalAmount: Money;
  };
}

type TravelPurpose = 'leisure' | 'business' | 'education' | 'medical';

interface DenominationBreakdown {
  denomination: number;
  count: number;
  total: Money;
}
```

---

## Activation Flow

**Card Activation Steps:**

| Step | Method | Notes |
|------|--------|-------|
| **Receive card** | Physical delivery | Customer confirms |
| **Generate PIN** | IVR, app, website | First time only |
| **First transaction** | ATM or POS | Activates card |
| **Load currency** | Already loaded | Or reload later |

**Research:**
- How does PIN generation work?
- What if activation fails?
- Can card be used immediately?

---

## Open Problems

### 1. KYC Friction
**Challenge:** KYC adds significant friction

**Options:**
- Pre-verify customers
- Use existing KYC (DigiLocker?)
- Minimal KYC for small amounts

**Research:** What is the minimum viable KYC?

### 2. Delivery Timing
**Challenge:** Customer leaves in 2 days, delivery takes 5

**Options:**
- Airport pickup
| Branch pickup
| Express delivery (higher cost)

**Research:** What are the fastest options?

### 3. Leftover Currency
**Challenge:** Customer returns with unused forex

**Options:**
- Reload for future use (within validity)
- Sell back at current rate (loss)
- Keep as souvenir (loss)

**Research:** What are the sell-back terms?

### 4. Card Issues Abroad
**Challenge:** Card doesn't work, customer stranded

**Options:**
- 24/7 international support
| Emergency replacement
| Backup card

**Research:** How do providers handle this?

---

## Competitor Research Needed

| Competitor | Ordering UX | Notable Patterns |
|------------|-------------|------------------|
| **BookMyForex** | ? | ? |
| **Thomas Cook** | ? | ? |
| **Banks** | ? | ? |

---

## Experiments to Run

1. **Order flow test:** How smooth is the process?
2. **KYC study:** What is the drop-off rate?
3. **Delivery accuracy test:** On-time delivery rate?
4. **Activation success rate:** What % succeed on first try?

---

## References

- [Connectivity - Ordering](./CONNECTIVITY_03_ORDERING.md) — Similar order patterns
| [Payment Processing](./PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) — Payment flows

---

## Next Steps

1. Test provider ordering APIs
2. Design KYC flow
3. Implement delivery tracking
4. Build activation system
5. Create support documentation

---

**Status:** Research Phase — Ordering patterns unknown

**Last Updated:** 2026-04-27
