# Operational Logic Spec: Fractional Sponsorship & Hybrid Finance (OE-007)

**Status**: Research/Draft
**Area**: Financial Reconciliation & Multi-Party Ledgers

---

## 1. The Problem: "The Bleeisure Split"
A corporate traveler (The Mehta's employee) goes on a business trip and brings their family. The company agrees to pay for the "Business Class" flight for the employee, but the employee pays for the "Economy" flights for their spouse and children, and the "Suite Upgrade" at the hotel. Currently, this requires manual invoice hacking by the agent.

## 2. The Solution: Shadow Ledgers (Fractional Attribution)

The system must implement a **Fractional Attribution Ledger** that allows a single trip component (e.g., a $20,000 Villa) to be split across multiple "Paying Entities" with different tax and billing rules.

### Attribution Logic:

- **Entity A (Sponsor)**: 
  - Rules: "Pay only for Base Employee Flight + Standard Single Room."
  - Constraint: No Alcohol, No Spa, GST-Invoice required.
- **Entity B (Personal)**:
  - Rules: "Pay for all Family Flights + Difference between Standard Room and Suite."
  - Constraint: Standard VAT Invoice.

### The "Suite-Diff" Calculation:
`Personal_Share = Total_Room_Cost - (Standard_Single_Rate * Corporate_Policy_Cap)`

## 3. Data Schema: `Hybrid_Ledger`

```json
{
  "trip_id": "T-9900",
  "components": [
    {
      "type": "ACCOMMODATION",
      "total_amount": 5000,
      "splits": [
        {
          "entity_id": "CORP-IBM-INDIA",
          "amount": 3000,
          "attribution": "BASE_POLICY_COVERAGE",
          "invoice_type": "GST_B2B"
        },
        {
          "entity_id": "PERSONAL-MEHTA",
          "amount": 2000,
          "attribution": "UPGRADE_DIFF + FAMILY_PAX",
          "invoice_type": "B2C_RETAIL"
        }
      ]
    }
  ]
}
```

## 4. Key Logic Rules

- **Rule 1: Policy-First Clamp**: The Sponsor's share must always be "Clamped" to the corporate policy limit. Any excess MUST overflow to the Personal ledger.
- **Rule 2: Atomic Cancellation**: If a shared component is cancelled, the refund must be auto-distributed back to the original entities proportional to their initial split.
- **Rule 3: Settlement Isolation**: The system must support separate payment gateways for each ledger (e.g., Corporate Credit Card for Entity A, Personal UPI for Entity B).

## 5. Success Metrics

- **Split Accuracy**: 100% reconciliation between `Supplier_Total` and `Sum(Entity_Invoices)`.
- **Tax Compliance**: Group A's GST invoice is valid even if Group B's invoice is for the same period/location.
- **Agent Productivity**: Reduction in manual "Excel-based split calculations" for bleisure trips.
