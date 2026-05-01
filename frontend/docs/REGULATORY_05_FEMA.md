# Regulatory & Licensing — FEMA Compliance for Travel Agencies

> Research document for Foreign Exchange Management Act compliance, LRS limits, overseas remittances, forex documentation, and RBI guidelines specific to travel agencies selling international packages.

---

## Key Questions

1. **What FEMA regulations apply to travel agencies selling international packages?**
2. **What are the Liberalised Remittance Scheme (LRS) limits and how do they affect booking flows?**
3. **What documentation is required for overseas remittances?**
4. **How does TCS on LRS interact with forex payments for travel?**
5. **What are the penalties for non-compliance?**

---

## Research Areas

### FEMA Framework for Travel Agencies

```typescript
interface FEMACompliance {
  agencyId: string;
  lrs: LRSConfig;
  remittances: RemittanceConfig;
  documentation: FEMA Documentation;
  reporting: RBIReporting;
}

// LRS (Liberalised Remittance Scheme) limits:
// - All resident individuals: USD 250,000 per financial year
// - Purpose: Travel, education, medical, gifts, donations, investment
// - For travel agencies: customer payments for international packages fall under LRS
// - No separate approval needed up to USD 250,000
// - Beyond USD 250,000: prior approval from RBI required
```

### LRS & Travel Payments

```typescript
interface LRSTravelPayment {
  customer_id: string;
  pan: string;                          // Mandatory for LRS
  financial_year: string;               // FY2026-27
  utilized_limit: number;               // USD already remitted this FY
  remaining_limit: number;              // USD 250,000 - utilized

  // Per-transaction checks
  transaction: {
    amount_usd: number;
    purpose: "travel" | "education" | "medical" | "business";
    destination_country: string;
    supplier_details: string;           // Hotel/airline/DMC name
  };

  // TCS on LRS (effective Oct 2023)
  tcs: {
    threshold: 700000;                  // ₹7 lakh per FY threshold for travel
    rate_below_threshold: 0.05;         // 5% TCS (no threshold for overseas tour packages)
    rate_above_threshold: 0.20;         // 20% TCS above threshold (non-education/medical)
    // Exception: Overseas tour packages → 5% TCS from first rupee (no threshold)
  };
}
```

### Remittance Documentation

```typescript
interface RemittanceDoc {
  // Mandatory documents for every overseas remittance:
  form_a2: string;                      // Application for remittance (Form A2)
  pan_copy: string;                     // PAN card copy
  purpose_code: string;                 // RBI purpose code (e.g., S0301 for travel)
  invoice: string;                      // Supplier invoice / booking confirmation
  identity_proof: string;               // Passport copy
  // For amounts > USD 25,000:
  bank_certificate: string;             // Certificate from AD-Category I bank

  // Retention: 5 years from end of financial year
  retention_period: "5FY";
}
```

### RBI Reporting Requirements

```typescript
interface RBIReporting {
  // Authorized Dealer (AD) Category I banks handle reporting:
  // - All remittances reported to RBI via FETERS (Foreign Exchange Transaction Electronic Reporting System)
  // - Agency must maintain records for 5 years
  // - Quarterly statements to AD bank
  // - Annual compliance certificate from AD bank

  // Key reports:
  feters: {
    frequency: "per_transaction";
    submitted_by: "AD_CATEGORY_I_BANK";   // Bank submits, not agency
    agency_role: "provide_documentation";
  };

  // Overseas Direct Investment (if agency has foreign suppliers/subsidiaries)
  odi: {
    reporting: "ARF + APR";               // Annual Return File + Annual Performance Report
    threshold: "any_overseas_investment";
  };
}
```

### Forex Card & Currency Compliance

```typescript
interface ForexCompliance {
  // Forex cards issued by AD-Category I banks
  // Loading limits: LRS limit (USD 250,000/FY)
  // Reload: Online or at branch, within LRS limit
  // Encashment: Must be done within 180 days of return
  // Unspent forex: Must be surrendered to bank within 180 days

  // Currency notes:
  // Maximum: USD 3,000 per trip (for general travel)
  // Exception: USD 5,000 for Hajj/Umrah pilgrims
  // Higher amounts: Only via forex card or wire transfer

  encashment_deadline: 180;               // Days from return date
  currency_note_limit: 3000;              // USD per trip
  hajj_exception: 5000;                   // USD for pilgrims
}
```

---

## Open Problems

### 1. LRS Limit Tracking Across Channels
A customer may book through multiple channels (agency A for flights, agency B for hotels). The LRS limit is per-individual, not per-agency. How does the platform track and warn about approaching limits?

### 2. TCS Collection on Mixed Packages
An international package includes flights (5% GST) + hotel (outside India) + tours (outside India). TCS applies to the full overseas component at 5% from the first rupee for "overseas tour packages." But if the customer pays the airline directly, the agency only collects TCS on the non-airline portion.

### 3. Repatriation of Unspent Funds
When a customer cancels mid-trip, the refund from overseas supplier may be in foreign currency. The agency must repatriate within 180 days. Tracking these refund flows is complex.

### 4. Digital Documentation Chain
Every overseas payment requires Form A2 + PAN + purpose code + invoice. The platform must generate and store this documentation chain automatically.

---

## Next Steps

- [ ] Map FEMA compliance checks into the booking engine pipeline
- [ ] Build LRS utilization tracker (per customer, per FY)
- [ ] Automate Form A2 generation with purpose codes
- [ ] Design TCS calculation engine for mixed domestic/international packages
- [ ] Build repatriation tracking for cancellations
- [ ] Integrate with AD-Category I bank APIs for real-time reporting

---

**Created:** 2026-05-01
**Series:** Regulatory & Licensing (REGULATORY_05)
