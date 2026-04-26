# Fin Spec: Multi-Currency Agency Settlement-Bridge (FIN-REAL-020)

**Status**: Research/Draft
**Area**: SaaS Financial Operations & Global Clearing

---

## 1. The Problem: "The Currency and Tax Labyrinth"
In a multi-tenant global SaaS, agencies collect payments in dozens of currencies and operate under diverse tax jurisdictions (VAT, GST, Sales Tax). Manually reconciling these payments, calculating tax liabilities, and settling funds into the agency's home currency is a massive operational burden. Agencies risk "Tax-Compliance-Failures" and "Currency-Volatility-Losses" if this process is not automated and segregated.

## 2. The Solution: 'Global-Clearing-Protocol' (GCP)

The GCP acts as the "Agency-CFO."

### Settlement Actions:

1.  **Multi-Tenant Fund Segregation**:
    *   **Action**: Ensuring that every transaction is mapped to a specific "Agency-Ledger-ID" and that funds are stored in segregated accounts to prevent "Tenant-Cross-Contamination."
2.  **Automated Tax-Withholding (Jurisdictional-Logic)**:
    *   **Action**: Identifying the "Tax-Nexus" for each transaction based on the Traveler's location, the Agency's location, and the Service location (e.g., "Applying 20% UK VAT for a UK agency booking a London hotel for a US traveler").
3.  **Real-Time Currency-Hedging**:
    *   **Action**: Monitoring exchange rates and autonomously triggering "Settlement-Conversion" into the agency's home currency at optimal intervals to minimize "Forex-Risk."
4.  **Agency 'Net-Settlement' Reporting**:
    *   **Action**: Providing a "Clear-Settlement-Dashboard" for the agency owner, showing Gross Revenue, Net Fees (SaaS fee, Transaction fee), Tax Withheld, and Final Settled Amount.

## 3. Data Schema: `Agency_Settlement_Event`

```json
{
  "settlement_id": "GCP-99221",
  "agency_id": "AGENCY_ALPHA_99",
  "transaction_currency": "JPY",
  "settlement_currency": "USD",
  "gross_amount": 150000.00,
  "tax_withheld_amount": 15000.00,
  "tax_jurisdiction": "JP_CONSUMPTION_TAX",
  "saas_platform_fee": 50.00,
  "net_settled_amount": 880.45,
  "status": "SETTLEMENT_COMPLETED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Tax-Priority' Rule**: Tax liabilities MUST be calculated and segregated *at the moment of transaction* to ensure the agency remains solvent for future tax filings.
- **Rule 2: Dynamic-Settlement-Windows**: Agencies MUST be able to configure their "Settlement-Frequency" (e.g., Daily, Weekly, or "On-Demand") to manage their own cash flow requirements.
- **Rule 3: Compliance-Documentation-Vault**: The agent MUST autonomously generate and store "Tax-Invoices" and "Settlement-Certificates" for every transaction to support future audits.

## 5. Success Metrics (Settlement)

- **Tax-Accuracy-Rate**: % of transactions with correctly calculated tax liabilities vs. auditor benchmarks.
- **Currency-Spread-Efficiency**: Average % loss during currency conversion vs. interbank rates.
- **Reconciliation-Latency**: Time from traveler payment to "Ready-for-Settlement" status in the agency ledger.
