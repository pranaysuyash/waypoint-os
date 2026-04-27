# Travel Insurance 03: Policy Issuance

> Binding policies, collecting payment, and delivering documents

---

## Document Overview

**Focus:** Converting quotes into active insurance policies
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Binding Process
- How do we convert a quote to a policy?
- What additional information is needed?
- When is the policy effective?
- What if payment fails after binding?

### 2. Payment Collection
- When is payment taken? (At quote? At bind?)
- What payment methods are accepted?
- How do we handle partial payments?
- What about installment payments?

### 3. Document Delivery
- What documents must be provided?
- How are documents delivered? (Email? App? Download?)
- What information must be included?
- How do we handle certificate requests?

### 4. Policy Management
- Can customers modify policies after purchase?
- How do we handle cancellations?
- What about extensions?
- How do we handle mid-trip changes?

---

## Research Areas

### A. Binding Requirements

**Additional Data at Bind:**

| Field | Required | Why |
|-------|----------|-----|
| **Full traveler details** | Yes | Names, dates of birth |
| **Contact information** | Yes | Email, phone |
| **Payment details** | Yes | Card or other method |
| **Declaration** | Yes | Health declaration signature |
| **Beneficiary** | Sometimes | For life coverage |

**Research:**
- What is the minimum data for binding?
- Can we use trip data we already have?
- How do we handle missing information?

### B. Payment Timing

**Payment Models:**

| Model | When Payment | Risk |
|-------|--------------|------|
| **Pay at bind** | Immediately | No risk, lower conversion |
| **Pay within X hours** | Short window | Some risk, higher conversion |
| **Installment** | Split over time | Higher risk, most expensive |

**Research:**
- Which model do insurers prefer?
- What do customers expect?
- What are the implications for cash flow?

### C. Document Requirements

**Mandatory Documents:**

| Document | Purpose | Timing |
|----------|---------|--------|
| **Policy Certificate** | Proof of coverage | Immediately |
| **Policy Wording** | Full terms and conditions | Immediately |
| **PDS** | Product Disclosure Statement | Immediately |
| **Claims Guide** | How to make claims | Immediately |
| **Emergency Card** | 24/7 contact details | Immediately |

**Certificate Content:**

| Field | Required |
|-------|----------|
| Policy number |
| Insurer name |
| Insured names |
| Policy period |
| Coverage summary |
| Limits |
| Deductibles |
| Emergency contact |
| Claims contact |

### D. Policy Effective Timing

| Scenario | Effective Time |
|----------|----------------|
| **Future trip** | From payment/issue date |
| **Immediate departure** | From payment (if eligible) |
| **Already traveling** | Usually not eligible |

**Research:**
- What are the "already traveling" rules?
- Can we backdate policies?
- What are the cut-off times?

---

## Binding State Machine

```
QUOTE_SELECTED → COLLECTING_DETAILS → AWAITING_PAYMENT → PAYMENT_PROCESSING
                                                                      ↓
                                                                    POLICY_ISSUED
                     ↓           ↓           ↓
                  ABANDONED   DECLINED    PAYMENT_FAILED
```

**States Explained:**

| State | Meaning | Next Actions |
|-------|---------|--------------|
| QUOTE_SELECTED | Customer selected a quote | Collect details |
| COLLECTING_DETAILS | Gathering required information | Validate, proceed to payment |
| AWAITING_PAYMENT | Details collected, awaiting payment | Process payment |
| PAYMENT_PROCESSING | Payment in progress | Await result |
| POLICY_ISSUED | Payment successful, policy active | Deliver documents |
| ABANDONED | Customer left flow | Follow-up? |
| DECLINED | Insurer declined | Offer alternatives |
| PAYMENT_FAILED | Payment unsuccessful | Retry or abandon |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface InsurancePolicy {
  id: string;
  policyNumber: string;  // Insurer's reference
  quoteId: string;
  tripId?: string;

  // Status
  status: PolicyStatus;
  issuedAt: Date;
  effectiveFrom: Date;
  effectiveTo: Date;

  // Insurer
  insurer: string;
  product: string;

  // Insured
  insured: InsuredPerson[];

  // Coverage
  coverage: PolicyCoverage;
  limits: PolicyLimits;
  deductibles: PolicyDeductibles;

  // Premium
  premium: {
    base: Money;
    taxes: Money;
    fees: Money;
    total: Money;
    currency: string;
  };

  // Payment
  payment: {
    status: PaymentStatus;
    method: string;
    transactionId?: string;
    paidAt?: Date;
  };

  // Documents
  documents: {
    certificateUrl: string;
    policyWordingUrl: string;
    pdsUrl: string;
    emergencyCardUrl?: string;
  };

  // Assistance
  emergencyContact: {
    global: string;
    regional?: { [region: string]: string };
    email: string;
  };
}

type PolicyStatus =
  | 'pending'
  | 'active'
  | 'cancelled'
  | 'expired'
  | 'claimed'
  | 'void';

interface InsuredPerson {
  id: string;
  type: 'primary' | 'spouse' | 'child' | 'other';
  title: string;
  firstName: string;
  lastName: string;
  dateOfBirth: Date;
  contactNumber: string;
  email?: string;
  preExistingConditions?: string[];
}
```

---

## Post-Purchase Modifications

| Modification | Allowed? | Timing | Impact |
|--------------|----------|--------|--------|
| **Add traveler** | Sometimes | Before departure | Additional premium |
| **Extend duration** | Sometimes | Before expiry | Additional premium |
| **Upgrade coverage** | Sometimes | Before departure | Additional premium |
| **Cancel** | Yes | Within free-look period | Full refund |
| **Cancel** | Yes | After free-look | Partial refund |
| **Reduce coverage** | Rarely | Before departure | Partial refund |

**Research:**
- What is the "free-look" period? (usually 10-14 days)
- What modifications do insurers allow?
- How are additional premiums calculated?

---

## Open Problems

### 1. Already Traveling
**Challenge:** Customer wants insurance while already traveling

**Questions:**
- Is this allowed?
- What restrictions apply?
- How do we verify departure date?

### 2. Pre-Existing Conditions Disclosure
**Challenge:** Customer didn't declare condition, now needs to claim

**Questions:**
- How do we handle this?
- Can claims be denied?
- What is our liability?

### 3. Payment Reconciliation
**Challenge:** Payment collected, but insurer policy not issued

**Questions:**
- How do we handle this?
- What is the customer experience?
- Who bears the risk?

### 4. Certificate Delivery
**Challenge:** Customer needs certificate immediately

**Options:**
- Generate in-app immediately
- Wait for insurer
- Email automatically

**Research:** What are customer expectations?

---

## Competitor Research Needed

| Competitor | Issuance Flow | Notable Patterns |
|------------|---------------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **Direct insurers** | ? | ? |

---

## Experiments to Run

1. **Binding API test:** How fast do insurers issue policies?
2. **Document delivery test:** What format works best?
3. **Modification test:** What changes can be made post-purchase?
4. **Cancellation test:** How smooth is the process?

---

## References

- [Booking Engine - Confirmation](./BOOKING_ENGINE_04_CONFIRMATION.md) — Confirmation patterns
- [Payment Processing](./PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) — Payment flows

---

## Next Steps

1. Test insurer binding APIs
2. Design policy issuance flow
3. Create document templates
4. Build modification system
5. Implement cancellation process

---

**Status:** Research Phase — Issuance patterns unknown

**Last Updated:** 2026-04-27
