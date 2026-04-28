# Currency Reconciliation — Multi-Currency Management

> Research document for handling multi-currency transactions, conversion, and reconciliation.

---

## Key Questions

1. **What currencies will we transact in, and what are the regulatory requirements for each?**
2. **How do we handle currency conversion between booking time and payment time?**
3. **Who bears the conversion risk — agency, customer, or supplier?**
4. **What exchange rate sources are authoritative?**
5. **How do we reconcile across currencies without conversion artifacts?**
6. **What RBI regulations apply to outward remittances for travel services?**

---

## Research Areas

### Currency Transaction Model

```typescript
interface CurrencyTransaction {
  transactionId: string;
  bookingId: string;
  originalCurrency: string;      // Supplier's billing currency
  settlementCurrency: string;    // Customer's payment currency
  accountingCurrency: string;    // Agency's base currency (INR)
  amounts: CurrencyAmounts;
  conversion: CurrencyConversion;
  hedgePosition?: HedgePosition;
}

interface CurrencyAmounts {
  original: number;              // Amount in supplier currency
  settlement: number;            // Amount in customer currency
  accounting: number;            // Amount in base currency (INR)
}

interface CurrencyConversion {
  rate: number;
  source: RateSource;
  timestamp: Date;
  markup: number;                // FX margin applied
  markupType: 'percentage' | 'flat' | 'none';
}

type RateSource =
  | 'live_market'        // Real-time forex rate
  | 'daily_card_rate'    // Card network daily rate
  | 'bank_rate'          // Bank's TT buying/selling rate
  | 'fixed_contract'     // Pre-agreed rate with supplier
  | 'platform_rate';     // Our own rate with margin
```

### RBI Regulations for Travel Forex

**Key regulations (India):**
- LRS (Liberalised Remittance Scheme): $250,000 per year per resident
- Travel-related remittances under LRS
- PAN mandatory for forex transactions above ₹25,000
- TCS (Tax Collected at Source) on overseas travel packages:
  - 5% for packages up to ₹7L
  - 20% above ₹7L (since Oct 2023)
- Forex card issuance and reload regulations

**Open questions:**
- How do we automate TCS calculation and reporting?
- What's the compliance workflow for LRS limit tracking?
- How do we handle remittances for B2B travel?

### Conversion Risk Management

```typescript
interface CurrencyRisk {
  bookingId: string;
  exposureType: 'receivable' | 'payable';
  currency: string;
  amount: number;
  bookingDate: Date;
  settlementDate: Date;
  daysOutstanding: number;
  currentRate: number;
  bookingRate: number;
  unrealizedGainLoss: number;
}

type RiskMitigationStrategy =
  | 'natural_hedge'       // Matching receivables and payables in same currency
  | 'forward_contract'    // Lock in rate for future settlement
  | 'daily_settlement'    // Minimize time between booking and settlement
  | 'pass_through'        // Customer bears all conversion risk
  | 'buffer_rate';        // Build margin into conversion rate
```

---

## Open Problems

1. **Rate timing mismatch** — Customer sees a price in INR based on today's rate, but pays 3 days later when the rate has changed. Who absorbs the difference?

2. **Multi-segment currency chains** — Customer pays in INR → Agency converts to USD → Hotel in Thailand charges in THB. Three conversion points, each with potential loss.

3. **TCS compliance at scale** — Calculating and collecting TCS correctly across hundreds of bookings with varying thresholds requires automation.

4. **Forex accounting** — Unrealized forex gains/losses need to be tracked for accounting purposes but don't affect cash flow until settlement.

5. **Reconciliation across conversion** — When a ₹3L booking involves INR→USD→THB conversions, reconciling the original amount to the settled amount requires tracking the full conversion chain.

---

## Next Steps

- [ ] Research RBI compliance requirements for travel forex transactions
- [ ] Map currency corridors for top 10 international destinations
- [ ] Design TCS calculation and reporting automation
- [ ] Study forex risk management practices in Indian travel industry
- [ ] Investigate forex card and prepaid currency product integration
