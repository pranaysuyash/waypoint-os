# Multi-Currency & Exchange Rate Management 02: Multi-Currency Booking & Invoicing

> Research document for multi-currency trip pricing, GST implications, TCS calculation, and customer-facing currency display.

---

## Document Overview

**Focus:** How multi-currency trips are priced, invoiced, and reconciled across different currencies
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Multi-Currency Trip Pricing
- A single trip may involve 4-5 currencies: flights in INR, hotels in SGD, activities in THB, transfers in MYR. How do we present a unified price?
- At what point is currency conversion applied: at quoting, at booking confirmation, or at payment?
- How do we handle price quotes that are valid for 24-48 hours when exchange rates fluctuate?
- Should each line item show its original currency or convert everything to INR?
- What about packages where the customer pays a single amount in INR but the agency settles suppliers in multiple currencies?

### 2. GST on Multi-Currency Invoices
- India's GST law requires invoices in INR. Can any part of a customer invoice be in a foreign currency?
- What is the GST treatment for services consumed outside India? (Export of services -- zero-rated?)
- How do we determine the place of supply for a multi-country trip?
- What exchange rate should be used for GST computation: RBI reference rate or agreed commercial rate?
- What about IGST vs. CGST+SGST for international vs. domestic components?

### 3. TCS (Tax Collected at Source)
- TCS under Section 206(1G) applies to overseas remittances. How is it computed for multi-currency bookings?
- TCS must be in INR regardless of booking currency. What exchange rate is used?
- The LRS threshold is Rs 7 lakh per PAN per year. How do we track cumulative remittances per PAN across bookings?
- What about the 5% TCS rate (20% above Rs 7 lakh) introduced in the 2023 budget?
- How does TCS interact with GST? Are they computed on the same base?

### 4. Customer-Facing Currency Display
- Should we show prices in the customer's preferred currency with an "approximate" disclaimer?
- How do we make clear that the actual charge will be in INR (or the booking currency)?
- What disclaimers are legally required for indicative currency conversions?
- How do we handle the UX of showing "SGD 1,200 (approx. INR 76,800)"?

### 5. Supplier Settlement Currencies
- Airlines: INR (via BSP) or airline's local currency?
- Hotels: Local currency (SGD for Singapore, THB for Thailand) or USD?
- Activity providers: Varies widely -- some accept only local currency
- How do we match the customer payment currency with the supplier settlement currency?

---

## Research Areas

### A. Multi-Currency Price Modeling

```typescript
interface MultiCurrencyPrice {
  id: string;
  tripId: string;
  bookingId: string;
  lineItems: CurrencyLineItem[];
  totals: CurrencyTotal[];
  baseCurrency: string;               // "INR" — agency's accounting currency
  displayCurrency: string;            // "INR" or customer's preferred currency
  conversionTimestamp: string;        // When rates were applied
  rateSource: string;                 // "RBI", "Fixer", "locked"
}

interface CurrencyLineItem {
  id: string;
  description: string;                // "Marina Bay Sands - 3 nights"
  category: 'flight' | 'hotel' | 'activity' | 'transfer' | 'visa' | 'insurance' | 'forex' | 'other';
  supplierCurrency: string;           // "SGD" — currency the supplier charges
  supplierAmount: number;             // 1200.00 (in supplier currency)
  supplierAmountInBase: number;       // 76812.00 (converted to INR)
  exchangeRateUsed: number;           // 64.01 (INR per SGD, including markup)
  rateLockId: string | null;          // Reference to rate lock if rate was locked
  customerCurrency: string;           // "INR" — currency shown to customer
  customerAmount: number;             // 76812.00 (amount customer pays)
  gstApplicable: boolean;
  gstRate: number | null;             // 0.18 for 18%, 0.05 for 5%, 0 for export
  gstAmount: number;                  // In INR
  tcsApplicable: boolean;
  tcsRate: number | null;
  tcsAmount: number;                  // In INR
}

interface CurrencyTotal {
  currency: string;
  subtotal: number;                   // Sum of line items in this currency
  taxTotal: number;                   // GST + TCS in this currency
  grandTotal: number;
  percentageOfTotal: number;          // What % of the total trip cost this currency represents
}
```

**Practical Example -- Singapore Trip:**

```
Trip: Singapore, 5 days, couple

Line Items:
1. Flights (DEL-SIN-DEL)        INR  42,000  x 2 = INR  84,000  (BSP, INR)
2. Hotel (MBS, 4 nights)       SGD   300     x 4 = SGD  1,200   (Hotel, SGD)
3. Activities (USS, Gardens)   SGD   350              = SGD    350   (Provider, SGD)
4. Transfers (Airport + local) SGD   180              = SGD    180   (Provider, SGD)
5. Street food tour            SGD    85              = SGD     85   (Provider, SGD)
6. Travel insurance            INR  3,200              = INR   3,200  (Insurer, INR)
7. Visa processing             INR  1,800  x 2 = INR   3,600  (VFS, INR)

Currency Breakdown:
- INR components: 84,000 + 3,200 + 3,600 = INR 90,800
- SGD components: 1,200 + 350 + 180 + 85 = SGD 1,815

Conversion (SGD at locked rate 64.01 INR/SGD):
- SGD 1,815 * 64.01 = INR 1,16,178

Trip total before tax: INR 90,800 + 1,16,178 = INR 2,06,978
GST (export of services, 0% on international): INR 0
TCS (5% on overseas remittance): INR 5,809 (on SGD component: 1,16,178 * 5%)

Grand total: INR 2,12,787
```

### B. GST Currency Rules

```typescript
interface GSTCurrencyRule {
  id: string;
  ruleName: string;
  serviceCategory: string;           // "hotel", "flight", "activity", "visa"
  placeOfSupply: 'domestic' | 'international';
  gstRate: number;                    // 0.05, 0.12, 0.18, 0.28, 0 (export)
  invoiceCurrency: 'INR_only' | 'foreign_allowed';
  rateForConversion: 'rbi_reference' | 'agreed_commercial' | 'customs_rate';
  conditions: string[];
}

// India GST rules for travel services:
//
// 1. Domestic hotel stay:  CGST + SGST (or IGST if inter-state)
//    - 5% for room tariff < INR 1,000
//    - 12% for room tariff INR 1,000 - 7,499
//    - 18% for room tariff >= INR 7,500
//
// 2. International hotel:  Export of services (0% GST) if:
//    - Service recipient is outside India
//    - Service is provided outside India
//    - Payment is in convertible foreign exchange
//    BUT: Indian customer paying in INR for overseas hotel is NOT export.
//    The agency charges GST on its service fee/margin, not on the hotel cost.
//
// 3. Airline tickets:  Airlines charge GST directly (5% economy, 12% business)
//    Agency commission is subject to 18% GST
//
// 4. Visa processing:  18% GST on service fee
//
// 5. Tour packages:  5% GST on tour cost (abridged rate for tour operators)
//    - This is a special composition scheme under Section 10(1) of CGST Act
//    - Only if tour operator opts for composition scheme
//
// Key rule: GST invoice MUST be in INR. Foreign currency can be shown
// as additional information but the taxable value must be in INR.

interface GSTInvoice {
  invoiceId: string;
  bookingId: string;
  invoiceDate: string;
  placeOfSupply: string;             // State code for domestic, "96" for international
  gstin: string;                     // Agency's GSTIN
  customerGstin: string | null;      // B2B customer GSTIN
  lineItems: {
    description: string;
    sacCode: string;                 // Service Accounting Code
    originalCurrency: string;
    originalAmount: number;
    amountInINR: number;
    exchangeRateUsed: number;
    gstRate: number;
    cgstAmount: number;
    sgstAmount: number;
    igstAmount: number;
    totalInINR: number;
  }[];
  totalOriginalCurrencies: { currency: string; amount: number }[];
  totalINR: number;
  totalGST: number;
  grandTotalINR: number;
  roundOff: number;                  // Rounded to nearest rupee per GST rules
  exchangeRateSource: string;
  exchangeRateDate: string;
}
```

### C. TCS Calculation

```typescript
interface TCSCalculation {
  id: string;
  bookingId: string;
  customerPAN: string;
  assessmentYear: string;             // "2026-27"
  remittanceType: 'tour_package' | 'overseas_program' | 'forex_purchase' | 'other';
  overseasAmountINR: number;          // Total overseas component in INR
  cumulativeRemittanceFY: number;    // Total remitted this financial year for this PAN
  thresholdExceeded: boolean;         // Has cumulative crossed Rs 7 lakh?
  thresholdAmount: number;            // 700000 (Rs 7 lakh)
  tcsRate: number;                    // 0.05 (5%) or 0.20 (20% above threshold)
  tcsAmount: number;
  tcsBreakdown: {
    atFivePercent: number;           // Amount taxed at 5%
    fivePercentTax: number;
    atTwentyPercent: number;         // Amount taxed at 20% (above threshold)
    twentyPercentTax: number;
  };
  collectedAt: string;
  depositedBy: string;                // Date by which agency must deposit TCS
  certificateIssued: boolean;
  form16FGenerated: boolean;
}

// TCS Rules (as of 2023-24 budget):
//
// Section 206(1G) -- TCS on overseas remittance:
// - 5% if cumulative LRS remittance in FY <= Rs 7 lakh
// - 20% on amount exceeding Rs 7 lakh
// - No TCS if remittance is for medical treatment or education (under LRS)
//   and funded by education loan: 0.5%
// - Tour packages: 5% up to Rs 7 lakh, 20% beyond
//
// Key considerations:
// - TCS is on the foreign component only (not on domestic flights, visa, insurance)
// - TCS must be deposited by the 7th of the following month
// - Agency issues Form 16F as TCS certificate
// - Customer can claim TCS as credit against income tax liability

// PAN-level tracking across bookings:
interface PANRemittanceTracker {
  pan: string;
  financialYear: string;
  totalRemitted: number;
  bookings: {
    bookingId: string;
    remittanceDate: string;
    overseasAmountINR: number;
    tcsCollected: number;
  }[];
  remainingThreshold: number;        // 700000 - totalRemitted (if positive)
  currentRate: 'five_percent' | 'twenty_percent';
  lastUpdated: string;
}
```

### D. Customer-Facing Currency Display

```typescript
interface CurrencyDisplayConfig {
  agencyId: string;
  defaultDisplayCurrency: string;     // "INR" for Indian agencies
  allowCustomerPreference: boolean;   // Show in customer's preferred currency?
  showOriginalCurrency: boolean;      // Show supplier currency alongside?
  disclaimerText: string;
  disclaimerRequired: boolean;
  roundingRule: 'nearest_rupee' | 'nearest_paisa' | 'floor' | 'ceil';
  formatPattern: string;              // "INR {amount}" or "{currency} {amount} (approx. INR {inrAmount})"
}

// Example display formats:
//
// Option A: INR only (default for Indian agencies)
//   "Marina Bay Sands (4 nights): INR 76,812"
//
// Option B: Original + INR
//   "Marina Bay Sands (4 nights): SGD 1,200 (INR 76,812)"
//
// Option C: Customer's preferred currency with disclaimer
//   "Marina Bay Sands (4 nights): SGD 1,200 (approx. INR 76,800)*"
//   "*Amount in INR is indicative. Actual charge in INR at locked rate."

interface CurrencyBreakdown {
  tripId: string;
  displayCurrency: string;
  lineItems: {
    description: string;
    supplierCurrency: string;
    supplierAmount: number;
    displayAmount: number;
    isApproximate: boolean;
    rateUsed: number;
    rateDate: string;
  }[];
  currencySummary: {
    currency: string;
    totalAmount: number;
    percentageOfTrip: number;
  }[];
  totalInDisplayCurrency: number;
  totalInBaseCurrency: number;
  disclaimer: string;
}
```

### E. Currency Conversion Timing

```typescript
type ConversionTiming = 
  | 'at_quote'       // Convert when generating quote (customer sees INR)
  | 'at_booking'     // Convert when customer confirms booking (lock rate)
  | 'at_payment'     // Convert when payment is processed (live rate)
  | 'at_invoicing';  // Convert when generating invoice (actual settlement rate)

interface ConversionPolicy {
  agencyId: string;
  defaultTiming: ConversionTiming;
  perCategory: {
    category: string;
    timing: ConversionTiming;
    rateLockDuration: number;         // Hours the rate is locked after booking
    requoteThreshold: number;         // Re-quote if rate moves > this %
  }[];
  rules: {
    rule: string;
    condition: string;
    action: string;
  }[];
}

// Recommended policy for boutique agencies:
// - At quote: Show indicative INR conversion (market rate + markup)
// - At booking: Lock the rate for 48 hours
// - If payment within 48 hours: Use locked rate
// - If payment after 48 hours: Re-quote at current rate
// - At invoicing: Use the locked/booked rate (not current rate)
// - At supplier settlement: Use market rate at time of payment (agency bears risk)
```

---

## Open Problems

### 1. GST on Package Tours -- Composition Scheme vs. Regular
- Tour operators can opt for a 5% composition scheme (on gross tour cost) instead of regular GST rates. This simplifies invoicing but the agency cannot claim input tax credit.
- For multi-currency packages, is the 5% computed on INR value at booking or at payment?
- **Research needed:** Consultation with a GST practitioner on optimal scheme for multi-currency tour operators.

### 2. Export of Services Classification
- If an Indian agency books a Singapore hotel for an Indian customer paying in INR, is this "export of services" (0% GST)?
- CBIC circulars suggest the service must be "provided outside India" and "paid in foreign exchange" for export classification.
- Indian customer paying in INR likely makes it a domestic service, subject to 18% GST on agency margin.
- **Critical:** Misclassifying can lead to GST demand + penalty.

### 3. TCS Tracking Across Agencies
- TCS is tracked per PAN across ALL remittances, not just from one agency. If a customer uses two travel agencies, neither knows the other's remittances.
- The Rs 7 lakh threshold is cumulative across the financial year. How does an agency know if the customer has already remitted through another channel?
- **Research needed:** Is there an API or mechanism to query PAN-level LRS utilization? (Likely no -- agencies must rely on self-declaration from the customer.)

### 4. Currency Conversion in Payment Gateway
- If a customer pays via international credit card, the card network does its own conversion (typically at 3-4% markup over market rate).
- This is independent of the agency's locked rate. The customer may see a different INR amount on their card statement vs. the invoice.
- How do we reconcile this? Is a disclaimer sufficient?

### 5. Supplier Settlement Mismatch
- The agency books a hotel at SGD 1,200 at rate 64.01 INR/SGD. By the time the agency settles (30 days later), SGD has moved to 66.50 INR/SGD.
- The agency's cost increased from INR 76,812 to INR 79,800 -- a difference of INR 2,988 that eats into margin.
- This is the core currency risk problem (addressed in FOREX_MGMT_03_HEDGING).

---

## Next Steps

1. **GST classification research** -- Consult with GST practitioner on export-of-services rules for Indian travel agencies booking foreign hotels for Indian customers. Document clear classification rules per service type.
2. **TCS calculation engine** -- Implement `TCSCalculation` with PAN-level tracking, threshold detection, and Form 16F generation.
3. **Multi-currency invoice template** -- Design invoice template that shows original currency, INR conversion, GST, and TCS in a compliant format.
4. **Customer self-declaration for LRS** -- Build a form for customers to declare cumulative LRS remittances (since there is no API to check this).
5. **Currency display UX prototype** -- Build the customer-facing currency display with disclaimer, rate date, and approximate indicator.
6. **Conversion policy configurator** -- Allow agencies to set conversion timing per category (at quote vs. at booking vs. at payment).
7. **Reconciliation with payment gateway** -- Research how Razorpay/Stripe handle multi-currency settlements and what conversion rates they apply.

---

## Cross-References

| Document | Relevance |
|----------|-----------|
| [FOREX_MGMT_01_RATES](FOREX_MGMT_01_RATES.md) | Provides exchange rates and rate locks |
| [FOREX_MGMT_03_HEDGING](FOREX_MGMT_03_HEDGING.md) | Manages currency risk from settlement mismatches |
| [FOREX_MGMT_04_FOREX_PRODUCTS](FOREX_MGMT_04_FOREX_PRODUCTS.md) | Forex products that customers can use for payment |
| [FINANCE_01_ACCOUNTING](FINANCE_01_ACCOUNTING.md) | Journal entries for multi-currency transactions |
| [PAYMENT_PROCESSING_03_COMPLIANCE](PAYMENT_PROCESSING_03_COMPLIANCE_DEEP_DIVE.md) | Payment compliance, TCS, GST |
| [BOOKING_ENGINE_02_RESERVATION_FLOW](BOOKING_ENGINE_02_RESERVATION_FLOW.md) | Booking flow integration for currency selection |
| [DOCUMENT_GEN_01_TEMPLATES](DOCUMENT_GEN_01_TEMPLATES.md) | Invoice template generation |
| [TRIP_BUILDER_03_PRICING_ESTIMATION](TRIP_BUILDER_03_PRICING_ESTIMATION.md) | Trip pricing with multi-currency support |

---

**Last Updated:** 2026-04-28
