# Multi-Currency & Exchange Rate Management 04: Forex Products for Travelers

> Research document for forex cards, currency notes, wire transfers, RBI LRS compliance, and forex product recommendation engines.

---

## Document Overview

**Focus:** Forex products that travel agencies can offer or facilitate for their customers
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Forex Card Issuance
- What multi-currency prepaid forex cards are available in India? (BookMyForex, Thomas Cook, HDFC Multicurrency, ICICI Travel Card, Axis Multi-Currency)
- Can travel agencies issue forex cards directly, or do they partner with authorized dealers (AD-II category)?
- What are the RBI-authorized dealer categories for forex? (AD-I: Banks, AD-II: Non-bank entities like Thomas Cook, EbixCash)
- What is the commission structure for agencies? (1-2% of load amount? Per-card issuance fee split?)
- How does API integration work with forex card providers?
- What currencies can be loaded on multi-currency cards? (Typically 15-20 currencies)
- What are the fees: issuance, reload, cross-currency conversion, ATM withdrawal, inactivity?

### 2. Currency Notes (Cash) Delivery
- Which providers offer doorstep delivery of foreign currency notes?
- What are the delivery timelines? (Same day in metros, 1-2 days in tier-2/3 cities)
- What denominations are available? (USD: 1, 5, 10, 20, 50, 100; EUR: 5, 10, 20, 50, 100, 200, 500)
- What is the buy-sell spread on currency notes vs. forex cards? (Notes typically 1-2% wider)
- What are the KYC requirements? (Passport, visa, ticket for purchase above USD 3,000)
- What is the maximum currency notes a traveler can carry? (USD 3,000 per trip for most currencies; unlimited for USD in notes up to annual LRS limit)

### 3. Wire Transfer / Outward Remittance
- When do travelers need wire transfers? (Education fees, medical treatment, emigration, business travel)
- What are the RBI LRS (Liberalised Remittance Scheme) limits and rules?
- What is the TCS on outward remittances? (5% up to Rs 7 lakh, 20% beyond)
- Which providers offer outward remittance? (Banks, BookMyForex, Wise, Western Union)
- What are the typical charges? (Bank: INR 500-2,500 + cable charges; Wise: 0.5-2% variable)
- How long does a wire transfer take? (1-5 business days depending on destination and provider)

### 4. RBI LRS Compliance
- What is the current LRS annual limit? (USD 250,000 per resident individual per financial year)
- What are the permissible purposes under LRS? (Travel, education, medical, gifts, donations, investment)
- What is the TCS structure? (5% up to Rs 7 lakh for most purposes; 20% above Rs 7 lakh; different rates for education/medical)
- What documentation is required? (Form A2, PAN, purpose code, beneficiary details)
- How does the agency track cumulative LRS utilization per PAN?
- What are the reporting requirements for authorized dealers?

### 5. Forex Product Recommendation
- How do we recommend the optimal forex product mix for a trip?
- Forex card vs. cash vs. credit card vs. debit card -- when is each optimal?
- What is the cost comparison across products for different trip profiles?
- Can we build a recommendation engine that considers trip destination, duration, spending pattern, and customer preferences?

---

## Research Areas

### A. Forex Card Products

```typescript
interface ForexCard {
  id: string;
  providerId: string;                 // "bookmyforex", "thomas_cook", "hdfc"
  providerName: string;
  productName: string;                // "Multi-Currency Forex Card", "Borderless Prepaid"
  cardType: 'single_currency' | 'multi_currency';
  supportedCurrencies: string[];      // ISO 4217 codes
  maxCurrenciesPerCard: number;       // Typically 15-20 for multi-currency
  issuanceFee: number;                // INR (typically 300-500)
  reloadFee: number;                  // INR per reload (typically 75-150)
  crossCurrencyFee: number;           // Percentage (typically 2-3.5% if not pre-loaded in that currency)
  atmWithdrawalFee: number;           // INR per withdrawal (typically 100-200)
  atmWithdrawalLimit: number;         // Daily limit in foreign currency
  inactivityFee: number;              // Monthly fee after 6-12 months of inactivity
  balanceInquiryFee: number;          // INR (for non-network ATMs)
  replacementFee: number;             // INR for lost card replacement
  encashmentFee: number;              // Fee to convert back to INR (typically 1-2%)
  minLoadAmount: number;              // INR or USD equivalent
  maxLoadAmount: number;              // Per load, subject to LRS limits
  validityMonths: number;             // Typically 36-60 months
  contactless: boolean;               // NFC-enabled
  virtualCard: boolean;               // Instant virtual card for online use
  mobileApp: boolean;                 // Provider mobile app for balance/reload
  emergencyAssistance: boolean;       // 24x7 global assistance
  insurance: {                        // Complimentary insurance
    coverage: string;                 // "Card misuse insurance up to USD 10,000"
    provider: string;
  };
  exchangeRateSource: string;         // "visa_rate" | "mastercard_rate" | "provider_rate"
  rateMarkup: number;                 // Markup over network rate (0-3%)
}
```

**Forex Card Comparison (India Market):**

| Feature | BookMyForex | Thomas Cook | HDFC Multicurrency | ICICI Travel | Wise |
|---------|------------|-------------|-------------------|--------------|------|
| Currencies | 15+ | 10+ | 15+ | 15+ | 50+ |
| Issuance fee | INR 0 (promo) | INR 500 | INR 500 | INR 499 | Free |
| Reload fee | INR 75 | INR 150 | INR 75 | INR 100 | Free |
| Cross-currency fee | 2% | 3.5% | 2% | 3.5% | 0.4-2% |
| ATM fee | INR 125 | INR 200 | INR 125 | INR 150 | INR 0-150 |
| Virtual card | Yes | No | No | Yes | Yes |
| Mobile app | Yes | Yes | Yes | Yes | Yes |
| Rate lock | Yes (48h) | No | No | No | Real-time |
| Doorstep delivery | Yes | Yes | Bank visit | Bank visit | N/A (virtual) |
| API integration | Yes | Unknown | Yes (corp) | Yes (corp) | Yes |

### B. Currency Notes (Cash)

```typescript
interface CurrencyOrder {
  id: string;
  agencyId: string;
  customerId: string;
  orderType: 'currency_notes' | 'forex_card' | 'both';
  currency: string;
  amount: number;                     // In foreign currency
  denominations: {
    denomination: number;             // 100 for USD 100 notes
    quantity: number;                 // 5 = five USD 100 notes
  }[];
  exchangeRate: number;               // INR per unit (includes markup)
  totalInINR: number;
  deliveryMethod: 'doorstep' | 'branch_pickup' | 'airport_pickup';
  deliveryAddress: string | null;
  deliveryDate: string;
  deliveryFee: number;                // INR (free above certain threshold, 100-300 otherwise)
  kycDocuments: {
    panCard: string;                  // PAN number
    passport: string;                 // Passport number
    visa: string | null;              // Visa number (required for some currencies)
    ticket: string | null;            // Confirmed ticket (required above USD 3,000)
    purposeCode: string;              // RBI purpose code
  };
  status: 'pending_kyc' | 'confirmed' | 'processing' | 'dispatched' | 'delivered' | 'cancelled';
  providerReference: string;
  createdAt: string;
}

// Currency notes: Key regulations
//
// RBI Master Direction -- Foreign Exchange Management (Export and Import of
// Currency Notes) Directions, 2016 (as amended):
//
// 1. Maximum foreign currency notes per trip:
//    - USD 3,000 per person per trip (for most currencies)
//    - Unlimited for USD notes up to annual LRS limit (USD 250,000)
//    - BUT: Best practice is to limit cash to immediate needs
//
// 2. KYC requirements for purchase:
//    - PAN mandatory for all forex purchases
//    - Passport mandatory
//    - For amounts > USD 3,000: Confirmed return ticket required
//    - For amounts > USD 25,000: Additional documentation
//
// 3. Buy-sell spread on notes:
//    - Typically 1-2% wider than forex card rates
//    - Popular currencies (USD, EUR, GBP): 1-1.5% spread
//    - Less common currencies (THB, MYR): 2-3% spread
//    - Very exotic currencies: May not be available as notes
```

### C. Wire Transfer / Outward Remittance

```typescript
interface WireTransfer {
  id: string;
  agencyId: string;
  customerId: string;
  purposeCode: string;                // RBI purpose code (see below)
  beneficiary: {
    name: string;
    bankName: string;
    bankAddress: string;
    accountNumber: string;            // IBAN for Europe
    swiftCode: string;                // BIC/SWIFT code
    routingNumber: string | null;     // ABA routing (for USD to US)
    country: string;
  };
  remittanceAmount: {
    currency: string;                 // "USD", "EUR", "SGD"
    amount: number;
    inINR: number;                    // Converted at applicable rate
    exchangeRate: number;
  };
  charges: {
    remittanceFee: number;            // INR 500-2,500
    cableCharges: number;             // INR 250-500 (SWIFT messaging)
    correspondentBankCharges: number; // Variable, deducted from amount or added
    gstOnCharges: number;             // 18% GST on service charges
    tcs: number;                      // TCS amount
    totalCharges: number;
  };
  totalDebitINR: number;              // Amount debited from customer's account
  lrsDeclaration: {
    panNumber: string;
    financialYear: string;
    cumulativeRemittedThisFY: number; // Before this transfer
    thisTransferAmount: number;
    totalAfterThisTransfer: number;
    remainingLRSLimit: number;
    formA2Submitted: boolean;
  };
  status: 'draft' | 'submitted' | 'processing' | 'dispatched' | 'credited' | 'returned' | 'cancelled';
  referenceNumber: string | null;     // Bank reference / UTR number
  estimatedCreditDate: string;
  actualCreditDate: string | null;
  provider: string;                   // "HDFC", "ICICI", "Wise", "BookMyForex"
  createdAt: string;
}

// RBI Purpose Codes for outward remittance:
//
// Travel related:
//   S0301 - Travel - Business
//   S0302 - Travel - Personal (including religious travel -- Hajj, etc.)
//   S0303 - Travel for Education
//   S0304 - Travel for Medical Treatment
//   S0305 - Travel - Employment / Emigration
//
// Other common:
//   S0306 - Gifts and Donations
//   S0307 - Investment in Equity/Debt
//   S0308 - Maintenance of relatives abroad
//   S0309 - International credit card settlement
//
// Key rule: Purpose code determines documentation requirements and TCS rate.
```

### D. LRS Compliance

```typescript
interface LRSCompliance {
  id: string;
  customerPAN: string;
  financialYear: string;              // "2026-27" (April-March)
  lrsLimit: number;                   // 250000 (USD 250,000)
  utilizedAmount: number;             // In USD equivalent
  remainingLimit: number;
  transactions: {
    transactionId: string;
    date: string;
    purposeCode: string;
    purposeDescription: string;
    amountUSD: number;
    amountINR: number;
    tcsRate: number;
    tcsAmount: number;
    provider: string;
    formA2Reference: string;
  }[];
  tcsSummary: {
    totalTCS Collected: number;
    depositedWithITDepartment: boolean;
    form16FGenerated: boolean;
    form16FIssuedToCustomer: boolean;
  };
  complianceFlags: {
    flag: string;
    description: string;
    action: string;
  }[];
  lastUpdated: string;
}

// LRS Rules Summary (as of 2023-24 amendments):
//
// 1. Annual Limit: USD 250,000 per resident individual per financial year
//    - Includes all permissible current account and capital account transactions
//    - Cannot be enhanced without RBI approval
//
// 2. TCS on LRS (Section 206(1G) and 206(1H)):
//
//    | Purpose | TCS Rate | Threshold |
//    |---------|----------|-----------|
//    | Education (loan-funded) | 0.5% | Rs 7 lakh |
//    | Education / Medical | 5% | Rs 7 lakh |
//    | Travel / Other | 5% | Rs 7 lakh |
//    | Above Rs 7 lakh (all purposes) | 20% | N/A |
//    | Investment (MF, equity abroad) | 20% | Rs 7 lakh |
//
// 3. Documentation:
//    - Form A2 (mandatory for all outward remittances)
//    - PAN card
//    - Purpose-specific documentation:
//      - Education: Admission letter, fee structure
//      - Medical: Hospital estimate, doctor's letter
//      - Travel: Ticket, visa
//      - Investment: KYC, demat details
//
// 4. Reporting:
//    - Authorized Dealer must report to RBI via EDPMS/IDPMS
//    - Monthly returns on LRS transactions
//    - Annual return on foreign assets (for amounts > threshold)
//
// 5. Prohibited under LRS:
//    - Remittance to countries identified by FATF as high-risk
//    - Remittance for margin trading or lottery
//    - Remittance to accounts in OFAC-sanctioned countries

// Customer self-declaration form for LRS tracking:
interface LRSSelfDeclaration {
  id: string;
  customerId: string;
  panNumber: string;
  financialYear: string;
  declaredUtilizedAmount: number;     // Amount already remitted via other channels
  declarationDate: string;
  supportingDocuments: string[];      // Optional: bank statements, receipts
  acceptedByAgency: boolean;
  disclaimer: string;                 // "Customer is responsible for accuracy..."
}
```

### E. Forex Product Comparison and Recommendation

```typescript
interface ForexRecommendation {
  id: string;
  tripId: string;
  customerId: string;
  destination: string;
  tripDuration: number;               // Days
  estimatedSpend: {
    currency: string;
    amount: number;
  }[];
  customerPreferences: {
    comfortWithCards: 'high' | 'medium' | 'low';
    preferCash: boolean;
    techSavvy: boolean;               // Likely to use mobile app / virtual card
    existingCards: string[];           // Cards customer already has
  };
  recommendations: {
    product: 'forex_card' | 'currency_notes' | 'international_credit_card' | 'international_debit_card' | 'mix';
    provider: string;
    currency: string;
    amount: number;
    reasoning: string;
    estimatedCost: number;            // Total fees and charges in INR
    estimatedRateSavings: number;     // Savings vs. worst option
    priority: number;                 // 1 = primary recommendation
  }[];
  totalEstimatedSpendINR: number;
  totalFeesINR: number;
  effectiveRate: number;              // Blended rate after all fees
}

// Recommendation logic:
//
// Rule 1: Always recommend forex card as primary product for trips > 3 days
//   - Better exchange rates than credit/debit cards
//   - Lock rates at load time
//   - Budget control (can't overspend)
//   - Wide acceptance (Visa/Mastercard network)
//
// Rule 2: Recommend USD 200-500 in currency notes for emergencies
//   - Cash needed for taxis, tips, small vendors, street food
//   - USD is universally accepted even in non-USD countries
//   - Don't over-recommend cash (loss/theft risk, poor re-conversion rate)
//
// Rule 3: For tech-savvy travelers, add virtual card option
//   - Instant issuance (no waiting for physical card)
//   - Good for online bookings (hotels, activities)
//   - Can coexist with physical card
//
// Rule 4: Avoid international credit/debit card as primary
//   - 3.5-4% markup on foreign transactions
//   - Dynamic Currency Conversion (DCC) trap at POS terminals
//   - No rate lock (rate applied at transaction time)
//
// Rule 5: For education/medical remittances, recommend wire transfer
//   - Direct transfer to institution account
//   - Documentary evidence for favorable TCS rates
//   - Wise for smaller amounts, bank wire for larger amounts

// Product cost comparison (example: Singapore trip, SGD 2,000 spend):
//
// | Method | Rate (INR/SGD) | Markup | Fees | Total Cost (INR) |
// |--------|---------------|--------|------|------------------|
// | Forex card (BookMyForex) | 64.50 | 2.5% | 499 (issuance) | 1,29,499 |
// | Forex card (HDFC) | 64.80 | 3.0% | 500 (issuance) | 1,30,100 |
// | Credit card (HDFC Regalia) | 65.50 | 3.5% | 0 | 1,31,000 |
// | Debit card (HDFC) | 66.00 | 3.5% + GST | 0 | 1,32,000 |
// | Currency notes | 65.00 | 3.0% | 150 (delivery) | 1,30,150 |
// | INR cash (exchange there) | 66.50 | 5.0% | 0 | 1,33,000 |
//
// Recommendation: Forex card (BookMyForex) + SGD 200 in cash
// Total: INR 1,29,499 + (200 * 65.00) + 150 = INR 1,42,649
// Savings vs. credit card only: INR 1,31,000 - 1,29,499 = INR 1,501 on card portion
```

---

## Open Problems

### 1. Agency Authorization to Sell Forex
- Only RBI-authorized dealers (AD-I banks, AD-II non-bank entities) can sell foreign exchange.
- Travel agencies are typically not authorized dealers. They must partner with AD-I or AD-II entities.
- Revenue model: Commission per transaction (0.5-1.5% of transaction value) or flat referral fee.
- **Research needed:** Partnership terms with BookMyForex, Thomas Cook, EbixCash for agency referral programs. Is API-based white-label forex possible?

### 2. Forex Product Bundling with Trip
- Can the agency bundle forex card + currency notes into the trip package? (Legal if agency is not directly selling forex.)
- Customer convenience: One booking includes flights + hotel + forex card + insurance.
- Operational challenge: Forex requires separate KYC and documentation. Cannot be fully automated in the booking flow.
- Should forex be offered as an upsell during booking, or as a separate step post-booking?

### 3. TCS Collection on Forex Products
- When the agency facilitates forex card load or wire transfer, who collects TCS?
- If the forex provider (BookMyForex) collects TCS directly, the agency does not need to worry about TCS compliance for forex products.
- But if the forex cost is embedded in the package price, TCS must be collected by the agency.
- **Critical:** Double TCS risk -- agency collects TCS on the trip, forex provider also collects TCS on the forex card load. Must ensure no double collection.

### 4. Rate Comparison Transparency
- Customers can easily compare forex rates across providers (Google, BookMyForex website, Wise website).
- If the agency recommends a specific provider, the customer may find a better rate elsewhere.
- Should the agency show a comparison table or just recommend one provider?
- **Risk:** Recommending a sub-optimal provider (due to higher commission for the agency) could damage trust.

### 5. Post-Trip Forex Encashment
- Unused forex on the card: Customer can hold (no interest), spend online, or encash.
- Encashment rate is typically worse than the purchase rate (1-2% spread).
- Should the agency proactively remind customers to encash unused forex?
- What about regulatory requirements for repatriation of unused forex? (RBI rules require surrendering unused foreign exchange within 180 days of return.)

---

## Next Steps

1. **Provider partnership evaluation** -- Contact BookMyForex, Thomas Cook, EbixCash for API access, commission structures, and white-label capabilities. Document integration options.
2. **Forex product comparison engine** -- Build the `ForexRecommendation` engine with rate comparison, fee calculation, and cost optimization.
3. **LRS tracking module** -- Implement `LRSCompliance` with PAN-level tracking, TCS calculation, Form A2 generation, and cumulative limit monitoring.
4. **Forex card order flow** -- Design the customer journey from trip booking to forex card order, including KYC collection, document upload, and delivery scheduling.
5. **TCS compliance flow** -- Map TCS collection across both trip booking and forex products to ensure no double collection.
6. **Currency notes delivery integration** -- Evaluate doorstep delivery providers and build order tracking.
7. **Post-trip encashment reminder** -- Automated notification for unused forex card balances with encashment instructions.

---

## Cross-References

| Document | Relevance |
|----------|-----------|
| [FOREX_MGMT_01_RATES](FOREX_MGMT_01_RATES.md) | Exchange rates for forex product pricing |
| [FOREX_MGMT_02_MULTI_CURRENCY_BOOKING](FOREX_MGMT_02_MULTI_CURRENCY_BOOKING.md) | TCS interaction between bookings and forex products |
| [FOREX_MGMT_03_HEDGING](FOREX_MGMT_03_HEDGING.md) | Natural hedging via customer forex card loads |
| [FOREX_01_PROVIDERS](FOREX_01_PROVIDERS.md) | Detailed forex provider landscape |
| [FOREX_02_COMPARISON](FOREX_02_COMPARISON.md) | Rate and fee comparison across providers |
| [FOREX_03_ORDERING](FOREX_03_ORDERING.md) | Forex ordering and delivery workflows |
| [PAYMENT_PROCESSING_03_COMPLIANCE](PAYMENT_PROCESSING_03_COMPLIANCE_DEEP_DIVE.md) | Payment compliance and TCS |
| [IDENTITY_01_KYC](IDENTITY_01_KYC.md) | KYC document collection and verification |
| [TRIP_BUILDER_05_BOOKING_MANAGEMENT](TRIP_BUILDER_05_BOOKING_MANAGEMENT.md) | Upselling forex products during trip booking |

---

**Last Updated:** 2026-04-28
