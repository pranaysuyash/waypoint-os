# Forex & Currency Services 01: Provider Landscape

> Currency exchange, forex cards, and international payment services

---

## Document Overview

**Focus:** Understanding the forex and currency services ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Provider Types
- Who provides forex cards in India? (BookMyForex, etc.)
- Who provides currency exchange?
- How do banks compare to specialized providers?
- What about international providers? (Wise, Revolut, etc.)

### 2. Product Types
- What is a forex card? (Prepaid travel card)
- How does it differ from credit/debit cards abroad?
- What about currency notes?
- What about travel cheques? (Still relevant?)

### 3. Economics
- How do providers make money?
- What are the fee structures?
- What are the exchange rate margins?
- How do we earn commission?

### 4. Regulatory
- What are the RBI regulations?
- What are the KYC requirements?
- What are the limits for forex purchase?
- What compliance is needed?

---

## Research Areas

### A. Indian Forex Providers

**Specialized Providers:**

| Provider | Products | API? | Notes |
|----------|----------|------|-------|
| **BookMyForex** | Cards, currency | ? | Market leader? |
| **Thomas Cook** | Cards, currency, wire | ? | ? |
| **EbixCash** | Cards, currency | ? | ? |
| **BuyForex** | Cards, currency | ? | ? |
| **Orient Exchange** | Cards, currency | ? | ? |

**Banks:**

| Bank | Products | Notes |
|------|----------|-------|
| **HDFC** | Forex cards, wire | ? |
| **ICICI** | Forex cards, wire | ? |
| **Axis** | Forex cards, wire | ? |
| **SBI** | Forex cards, wire | ? |

**Research Needed:**
- API availability
- Commission structures
- Integration complexity
- Service quality

### B. International Providers

**Fintech Providers:**

| Provider | Available in India? | Products | Notes |
|----------|---------------------|----------|-------|
| **Wise** | Yes | Transfers, card | ? |
| **Revolut** | No | Multi-currency | Not in India |
| **N26** | No | Bank account | Not in India |
| **PingPong** | No? | Business | ? |

**Research:**
- Which providers work for Indian residents?
- What are the RBI restrictions?
- Can we integrate with Wise?

### C. Product Types

**Forex Cards:**

| Feature | Description | Research Needed |
|---------|-------------|-----------------|
| **Prepaid** | Load before travel | ? |
| **Multi-currency** | Hold multiple currencies | ? |
| **Reloadable** | Add more money while traveling | ? |
| **Contactless** | Tap to pay | ? |
| **Online management** | App/portal to manage | ? |

**Currency Exchange:**

| Type | Description | Notes |
|------|-------------|-------|
| **Cash notes** | Physical currency | Commission-based |
| **Wire transfer** | Bank to bank | For large amounts |
| **Travel cheques** | Old school | Largely obsolete |

### D. Fee Structures

**Fee Components:**

| Fee Type | Description | Typical Amount |
|----------|-------------|----------------|
| **Exchange margin** | Built into rate | 1-3% |
| **Issuance fee** | Card fee | ₹100-500 |
| **Reload fee** | Adding money | ₹50-200 |
| **ATM fee** | Withdrawal abroad | Varies |
| **Cross-currency fee** | Using card in different currency | 2-3% |
| **Inactivity fee** | If not used | Varies |

**Research:**
- What are the actual fees by provider?
- How do we compare total cost?
- What are the hidden fees?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface ForexProvider {
  id: string;
  name: string;
  type: 'specialized' | 'bank' | 'fintech';

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;

  // Products
  products: ForexProductType[];

  // Commercial
  commissionRate?: number;
  pricing: PricingStructure;

  // Regulatory
  rbiCompliant: boolean;
  kycRequired: boolean;
  kycLevel: KYCLevel;
}

type ForexProductType =
  | 'forex_card'
  | 'currency_notes'
  | 'wire_transfer'
  | 'travel_cheques';

interface ForexCard {
  id: string;
  providerId: string;
  name: string;

  // Features
  multiCurrency: boolean;
  supportedCurrencies: string[];
  reloadable: boolean;
  contactless: boolean;

  // Fees
  fees: {
    issuance: Money;
    reload: Money;
    atmAbroad: Money;
    crossCurrency: Percentage;
    inactivity: Money;
  };

  // Limits
  limits: {
    maxLoad: Money;
    minLoad: Money;
    maxATMWithdrawal: Money;
  };

  // Delivery
  deliveryMethods: DeliveryMethod[];
}

type DeliveryMethod =
  | 'courier'
  | 'pickup_branch'
  | 'pickup_airport';
```

---

## Exchange Rate Mechanics

**How Rates Work:**

```
Interbank Rate (Mid-market)
    +
Provider Margin
    =
Rate Offered to Customer
```

**Margin Examples:**

| Provider Type | Typical Margin |
|---------------|---------------|
| **Banks** | 2-3% |
| **Specialized** | 1-2% |
| **Online** | 0.5-1% |

**Research:**
- What are actual margins?
- How do we get live rates?
- Can we show margin transparency?

---

## Regulatory Considerations

**RBI Regulations:**

| Regulation | Description | Impact |
|------------|-------------|--------|
| **Forex limit** | $2.5L per person per year | Max purchase |
| **KYC** | PAN card required | Customer verification |
| **Purpose** | Travel, education, medical | Documentation needed |
| **AD Category-II** | License required for forex | Provider requirement |

**Research:**
- What licenses do we need?
- Can we operate as a referrer only?
- What are the compliance requirements?

---

## Open Problems

### 1. Rate Volatility
**Challenge:** Exchange rates change constantly

**Options:**
- Real-time rates
- Rate lock for X hours
- Rate at time of delivery

**Research:** How do providers handle this?

### 2. Physical Delivery
**Challenge:** Forex cards need physical delivery

**Questions:**
- How long does delivery take?
- What if delivery fails?
- Who pays for shipping?

### 3. Card Blocking
**Challenge:** Cards sometimes get blocked

**Options:**
- Pre-travel notification
- 24/7 support
- Backup cards

**Research:** How common is blocking?

### 4. Leftover Currency
**Challenge:** Customer returns with unused forex

**Options:**
- Reload for next trip (within validity)
- Sell back (at worse rate)
| Expires after

**Research:** What happens to leftover balances?

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **BookMyForex** | ? | ? |
| **Thomas Cook** | ? | ? |
| **Bank sites** | ? | ? |

---

## Experiments to Run

1. **API availability test:** Which providers have APIs?
2. **Rate comparison study:** How do providers compare?
3. **Fee analysis:** What are the total costs?
4. **Delivery test:** How long does delivery take?

---

## References

- [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Add-on component
- [Internationalization](./INTERNATIONALIZATION_MASTER_INDEX.md) — Currency handling
- [Payment Processing](./PAYMENT_PROCESSING_DEEP_DIVE_MASTER_INDEX.md) — Payment flows

---

## Next Steps

1. Audit forex provider APIs
2. Analyze fee structures
3. Understand RBI regulations
4. Design comparison framework
5. Build ordering flow

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
