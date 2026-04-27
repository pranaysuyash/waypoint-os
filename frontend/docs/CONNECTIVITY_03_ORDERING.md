# SIM Cards & Connectivity 03: Ordering & Activation

> Purchasing connectivity and activating service

---

## Document Overview

**Focus:** Converting selection to active service
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Ordering Flow
- What information is needed to order?
- How do we handle device compatibility checks?
- What about immediate vs. delayed activation?
- How do we handle payment?

### 2. eSIM Provisioning
- How does eSIM activation work?
- What is the QR code flow?
- What if scanning fails?
- How do we track activation status?

### 3. Physical SIM Fulfillment
- How do physical SIMs get delivered?
- What are the timing options?
- What about international delivery?
- How do we handle lost shipments?

### 4. Post-Purchase Support
- What if activation fails?
- How do customers get support?
- What about refunds?
- How do we handle top-ups?

---

## Research Areas

### A. Ordering Data Requirements

**Required Information:**

| Field | Required | Purpose |
|-------|----------|---------|
| **Destination** | Yes | Plan availability |
| **Travel dates** | Yes | Validity period |
| **Email** | Yes | QR code delivery |
| **Device compatibility** | Yes | eSIM vs. physical |
| **Payment** | Yes | Purchase |

**Optional Information:**

| Field | Why Optional |
|-------|--------------|
| **Device model** | For compatibility, but can self-report |
| **Data needs estimate** | For recommendation, not required |
| **Phone number** | Not needed for eSIM |

**Research:**
- What is the minimum viable data?
- Can we use trip data we already have?

### B. eSIM Activation Flow

**Standard Flow:**

```
1. Order placed → Payment processed
2. Provider generates eSIM profile
3. We receive QR code (LPA string)
4. Display QR code to customer
5. Customer scans in phone settings
6. Phone downloads profile
7. Profile activated
8. Customer can use data
```

**Alternative Flows:**

| Method | When Used | How |
|--------|-----------|-----|
| **QR code** | Most common | Scan with camera |
| **LPA string** | Manual entry | Copy-paste string |
| **Deep link** | Some providers | Direct activation |
| **App-based** | Provider apps | In-app activation |

**Research:**
- Which methods are most reliable?
- What if customer can't scan?
- How do we handle activation failures?

### C. Physical SIM Fulfillment

**Delivery Options:**

| Option | Timing | Cost | Research Needed |
|--------|--------|------|-----------------|
| **International courier** | 3-7 days | High | ? |
| **Airport pickup** | At arrival | Medium | ? |
| **Hotel delivery** | At arrival | Medium | ? |
| **Local pickup** | At destination | Low | ? |

**Activation:**

| Step | Method |
|------|--------|
| **Insert SIM** | Physical |
| **Call to activate** | Phone call |
| **App activation** | Provider app |
| **Auto-activation** | Automatic on first use |

**Research:**
- Which delivery methods are reliable?
- How do we track delivery?
- What if SIM is lost in mail?

### D. Payment & Pricing

**Payment Timing:**

| Model | When | How |
|-------|------|-----|
| **Pre-pay** | At order | Full amount |
| **Pay later** | After activation | May be limited |

**Pricing Components:**

| Component | Included? | Notes |
|-----------|-----------|-------|
| **Data allowance** | Yes | Core product |
| **Validity period** | Yes | Days of use |
| **Voice minutes** | Sometimes | Add-on |
| **SMS** | Sometimes | Add-on |
| **Taxes** | Sometimes | Varies by region |

**Research:**
- What payment methods work?
- How do we handle international cards?
- What about UPI/NetBanking?

---

## Ordering State Machine

```
SELECTED → COLLECTING_INFO → PAYMENT_PROCESSING → PAYMENT_COMPLETE
                                                         ↓
                                      PROVIDER_ORDERING → QR_GENERATED
                                                         ↓
                                                    ACTIVATED → COMPLETED
           ↓           ↓              ↓                ↓
        ABANDONED   PAYMENT_FAILED   ORDER_FAILED    ACTIVATION_FAILED
```

---

## Data Model

```typescript
interface ConnectivityOrder {
  id: string;
  tripId?: string;
  customerId: string;

  // Selection
  planId: string;
  provider: string;

  // Order details
  type: 'esim' | 'physical_sim';
  destination: string;
  travelDates: { start: Date; end: Date };

  // Status
  status: OrderStatus;
  createdAt: Date;
  activatedAt?: Date;

  // eSIM specific
  esim?: {
    qrCode: string;  // Base64 or URL
    lpaString?: string;
    activationCode?: string;
    expiresAt?: Date;
  };

  // Physical SIM specific
  physicalSim?: {
    deliveryMethod: string;
    trackingNumber?: string;
    shippingAddress?: Address;
    iccid?: string;  // SIM card number
  };

  // Payment
  payment: {
    amount: Money;
    currency: string;
    status: PaymentStatus;
    transactionId?: string;
  };
}

type OrderStatus =
  | 'pending'
  | 'payment_processing'
  | 'payment_failed'
  | 'ordered'
  | 'qr_generated'
  | 'delivered'
  | 'activated'
  | 'activation_failed'
  | 'cancelled'
  | 'refunded';
```

---

## Activation Tracking

**Tracking Methods:**

| Method | Capability | Implementation |
|--------|-----------|----------------|
| **Provider webhook** | Real-time | If provider supports |
| **Provider polling** | Near real-time | Periodic checks |
| **Customer confirmation** | Self-report | Customer marks as active |
| **No tracking** | Fire and forget | Simple but limited |

**Status Updates:**

| Status | Meaning | Customer Action |
|--------|---------|-----------------|
| **QR Ready** | Scan to activate | Scan QR code |
| **Profile Downloaded** | Phone has profile | Wait for activation |
| **Active** | Data working | None needed |
| **Failed** | Activation failed | Contact support |

---

## Open Problems

### 1. Activation Failure
**Challenge:** Customer scans QR, nothing happens

**Troubleshooting Steps:**
- Check eSIM is enabled
- Check device compatibility
- Try manual LPA string entry
- Contact provider support

**Research:** What are common failure points?

### 2. Timing Mismatch
**Challenge:** Customer activates before trip, validity starts

**Options:**
- Warn customer
- Allow delayed activation
- Plan starts on first use

**Research:** How do providers handle this?

### 3. Multiple Devices
**Challenge:** Customer has multiple devices

**Questions:**
- Can eSIM be moved between devices?
- Can they buy multiple plans?
- How do we handle transfers?

### 4. Top-Ups & Extensions
**Challenge:** Customer runs out of data

**Options:**
- Buy new plan
- Top-up existing plan
- Extend validity

**Research:** What do providers allow?

---

## Competitor Research Needed

| Competitor | Ordering UX | Notable Patterns |
|------------|-------------|------------------|
| **Airalo** | ? | ? |
| **Nomad** | ? | ? |
| **Physical SIM providers** | ? | ? |

---

## Experiments to Run

1. **Order flow test:** How smooth is the process?
2. **Activation success rate:** What % succeed on first try?
3. **Support analysis:** What are common issues?
4. **Refund rate:** Why do customers refund?

---

## References

- [Activities - Booking](./ACTIVITIES_03_BOOKING.md) — Similar order patterns
- [Payment Processing](./PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) — Payment flows

---

## Next Steps

1. Test provider ordering APIs
2. Design ordering flow
3. Build activation tracking
4. Create troubleshooting guide
5. Implement support system

---

**Status:** Research Phase — Ordering patterns unknown

**Last Updated:** 2026-04-27
