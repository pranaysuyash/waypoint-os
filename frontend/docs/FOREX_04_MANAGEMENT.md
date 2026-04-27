# Forex & Currency Services 04: Card Management

> Reloads, balance tracking, and ongoing support

---

## Document Overview

**Focus:** Managing forex cards after delivery
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Reloads
- How do customers reload cards?
- What are the fees for reloading?
- How do we handle reloads while abroad?
- What are the limits?

### 2. Balance Tracking
- How do customers check balances?
- How do we show transaction history?
- What about real-time updates?
- How do customers get alerts?

### 3. Support Issues
- What if card is lost/stolen?
- What if card doesn't work?
- What if PIN is forgotten?
- What about disputed transactions?

### 4. Expiry & Closure
- What happens when card expires?
| How do customers get refunds?
| What about leftover balance?
| How is card closed?

---

## Research Areas

### A. Reload Process

**Reload Methods:**

| Method | Availability | Timing | Fees |
|--------|--------------|--------|------|
| **Online portal** | 24/7 | Instant | ₹50-200 |
| **App** | 24/7 | Instant | ₹50-200 |
| **Branch** | Business hours | Immediate | May be lower |
| **Phone banking** | Business hours | 1-2 days | Varies |

**Reload Limits:**

| Limit Type | Amount | Notes |
|------------|--------|-------|
| **Per transaction** | Varies | Provider dependent |
| **Per day** | Varies | Provider dependent |
| **Overall** | RBI $2.5L/year | Including initial load |

**Research:**
- What are the exact limits by provider?
- How do we handle reloads while abroad?
- What are the fees for international reloads?

### B. Balance & Transaction Tracking

**Tracking Methods:**

| Method | Real-time | Detail Level |
|--------|-----------|--------------|
| **Provider app** | Yes | Full transactions |
| **Provider portal** | Yes | Full transactions |
| **SMS alerts** | Near real-time | Transaction only |
| **Our platform** | Cached | Depends on API |

**Information Available:**

| Field | Available | Notes |
|-------|-----------|-------|
| **Current balance** | Yes | Per currency |
| **Transaction history** | Yes | Last N transactions |
| **Pending transactions** | Sometimes | Varies |
| **ATM locations** | Yes | Provider network |

**Research:**
- Do providers offer balance check APIs?
- How do we present multi-currency balances?
- What is the latency of updates?

### C. Common Support Issues

| Issue | Resolution | Escalation |
|-------|-----------|------------|
| **Card not working** | Check activation, try different ATM | Provider |
| **PIN forgotten** | Reset via IVR/app | Provider |
| **Card lost/stolen** | Block immediately, emergency card | Provider |
| **Wrong currency** | Cross-currency fee applies | None |
| **ATM declined** | Check limit, try different ATM | Provider |
| **Overcharged** | Dispute process | Provider |

**Research:**
- What can we resolve vs. provider?
- What is the emergency card process?
- How long does dispute resolution take?

### D. Expiry & Refunds

**Card Lifecycle:**

```
Card issued → Valid for 3-5 years → Expired
                                       ↓
                            Surrender card → Refund balance
```

**Refund Process:**

| Step | Method | Timing |
|------|--------|--------|
| **Request surrender** | Branch, app, phone | Immediate |
| **Return card** | Branch or mail | Varies |
| **Process refund** | Bank transfer | 7-15 days |
| **Receive funds** | Customer account | Depends on bank |

**Leftover Balance:**

| Situation | Resolution |
|-----------|------------|
| **Expired card, has balance** | Surrender for refund (fee may apply) |
| **Valid card, no longer needed** | Withdraw or spend, or surrender |
| **Small balance** | May not be worth refund fee |

**Research:**
- What are the surrender fees?
- How long do refunds take?
- What happens if card is lost but has balance?

---

## Card Management Data Model

```typescript
interface ForexCardManagement {
  cardId: string;
  orderId: string;
  customerId: string;

  // Status
  status: CardStatus;
  issuedAt: Date;
  expiresAt: Date;

  // Balances (multi-currency)
  balances: {
    currency: string;
    amount: Money;
    lastUpdated: Date;
  }[];

  // Transactions
  transactions: ForexTransaction[];

  // Reloads
  reloads: Reload[];

  // Support
  issues: SupportIssue[];
}

type CardStatus =
  | 'active'
  | 'blocked'
  | 'expired'
  | 'surrendered'
  | 'lost'
  | 'stolen';

interface ForexTransaction {
  id: string;
  date: Date;
  type: 'purchase' | 'atm_withdrawal' | 'reload' | 'fee';
  amount: Money;
  currency: string;
  description: string;
  location?: string;
}

interface Reload {
  id: string;
  date: Date;
  amount: Money;
  currency: string;
  method: string;
  fee: Money;
  status: 'pending' | 'completed' | 'failed';
}
```

---

## Customer Communication

**Touchpoints:**

| Timing | Channel | Content |
|--------|---------|---------|
| **After delivery** | Email/SMS | Activation instructions |
| **First transaction** | None | Silent |
| **Low balance** | App/SMS | Warning to reload |
| **Unusual activity** | Call/SMS | Security alert |
| **Expiry warning** | Email/SMS | 30 days before |
| **Post-expiry** | Email | Surrender instructions |

**Research:**
- Which alerts are most valuable?
- How do we avoid spam?
- What about international SMS?

---

## Open Problems

### 1. Balance Check Abroad
**Challenge:** Customer abroad needs to check balance

**Options:**
- Provider app (requires data)
- SMS (may be expensive)
| IVR call (may be expensive)

**Research:** What works best?

### 2. Currency Confusion
**Challenge:** Customer has USD card, travels to EUR country

**Issue:** Cross-currency fee applies

**Options:**
- Warn customer
- Suggest separate EUR card
| Show fees clearly

### 3. Emergency Cash
**Challenge:** Card lost, customer stranded without cash

**Options:**
- Emergency card replacement (difficult abroad)
- Wire transfer (expensive)
| Hotel help (maybe)

**Research:** How do providers handle this?

### 4. Small Refunds
**Challenge:** Card has $5 left, refund fee is $10

**Options:**
- Warn customer
- Don't refund
| Absorb fee

---

## Competitor Research Needed

| Competitor | Card Management UX | Notable Patterns |
|------------|---------------------|------------------|
| **BookMyForex** | ? | ? |
| **Thomas Cook** | ? | ? |
| **Wise** | ? | ? |

---

## Experiments to Run

1. **Reload ease test:** How smooth is the process?
2. **Balance accuracy study:** How accurate are real-time balances?
3. **Support ticket analysis:** What are common issues?
4. **Refund processing test:** How long do refunds take?

---

## References

- [Connectivity - Support](./CONNECTIVITY_04_SUPPORT.md) — Similar support patterns
| [Payment Processing - Reconciliation](./PAYMENT_PROCESSING_04_RECONCILIATION_DEEP_DIVE.md) — Transaction tracking

---

## Next Steps

1. Build card management dashboard
2. Implement balance tracking
3. Create reload flow
4. Design support documentation
5. Set up alerts system

---

**Status:** Research Phase — Card management patterns unknown

**Last Updated:** 2026-04-27
