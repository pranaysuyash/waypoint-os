# Area Deep Dive: Financial Operations & Treasury

**Domain**: Agency Financial Stability  
**Focus**: Forex management, credit lines, and high-accuracy reconciliation.

---

## 1. Forex Volatility & Management

International travel agencies operate across multiple currencies, exposing them to "Forex Risk".

### Currency Hedging
- **Risk**: Quoting a traveler in INR but paying a supplier in USD. If the USD strengthens between the quote and the payment, the agency's margin evaporates.
- **System Action**: Automating "Live Forex Surcharges" or recommending a "Buy Now, Pay Now" strategy for high-volatility currencies.

### Multi-Currency Wallets
- **Logic**: Holding balances in USD, EUR, and GBP to avoid double-conversion fees.
- **System Action**: Tracking wallet balances in the `AuditStore` and alerting the Owner (P2) when a specific currency is low.

---

## 2. Supplier Credit Lines & Payments

### The "Credit Cycle"
- **Mechanics**: Agencies often have "Credit Lines" with GDS or major Bed Banks (e.g., "Pay within 30 days").
- **Risk**: Exceeding the credit limit leads to immediate booking blockage.
- **System Action**: Proactively monitoring credit utilization across all major vendors.

### Instant Payouts vs Traditional
- **Focus**: Using Virtual Credit Cards (VCCs) for instant supplier payments to lock in prices.
- **System Action**: Generating a one-time VCC for every Phase 2 (Fulfillment) booking.

---

## 3. Remittance & Statutory Compliance (LRS/TCS)

### LRS (Liberalized Remittance Scheme)
- **Complexity**: Monitoring the $250k limit for Indian residents.
- **System Action**: Prompting for PAN card verification and checking past remittance history before approving high-value international bookings.

### TCS (Tax Collected at Source)
- **Rule**: Collecting 5% to 20% TCS from the traveler and remitting it to the government.
- **System Action**: Automated TCS calculation based on the traveler's total "International Spend" for the financial year.

---

## 4. Proposed Scenarios for this Domain

| Scenario ID | Title | Persona | Category |
|-------------|-------|---------|----------|
| FIN-001 | Forex Margin Erosion Alert | P2 | Risk |
| FIN-002 | Supplier Credit Limit Breach | P1 | Operations |
| FIN-003 | TCS Threshold Auto-Calculation | P3 | Compliance |
| FIN-004 | VCC Payment Failure at Check-in | S1 | Recovery |
| FIN-005 | Double-Currency Conversion Catch | P2 | Optimization |
| FIN-006 | LRS Limit Warning for VIP | S1 | Compliance |
