# Additional Scenario 316: The GST/VAT Ghost in the Machine

**Scenario**: A complex multi-family group booking requires fractional invoicing across three different tax jurisdictions (e.g., India GST, UK VAT, and US Sales Tax).

---

## Situation

- 5 families are sharing a $50k luxury villa in Bali.
- Family A is based in India (requires GST invoice for corporate deduction).
- Family B is based in the UK (requires VAT-compliant receipt).
- Family C is based in the US (requires standard receipt).
- The total bill must be split 40/30/30 based on room sizes, but the deposit was paid by one party.

## What the system should do

- Calculate the fractional tax liability for each party based on their local jurisdiction and the supplier's location.
- Reconcile the single deposit payment against the three separate final invoices.
- Generate three distinct, compliant PDF invoices.
- Log the "Tax Rationale" for the agency's back-office audit.

## Why this matters

Manual reconciliation of cross-border tax for groups is a high-error-rate task that consumes hours of agent time.
Automating this allows agencies to handle larger, more complex groups with zero back-office overhead.

## Success criteria

- Invoices match the 40/30/30 split exactly.
- Each invoice passes local tax validation (GST numbers, VAT IDs).
- The total sums to the supplier's gross amount plus agency fees.
