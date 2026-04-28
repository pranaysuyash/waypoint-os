# Scenario P4-S5: CFO Analytics Report

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P1 (High — reporting burden)

---

## Scenario Description**

Vikram spends 3-4 DAYS per quarter building a PowerPoint for the CFO: "₹18Cr travel spend, here's the breakdown, here's what we can optimize."

The system should auto-generate a quarterly report:
- Total spend: ₹18Cr (flights 40%, hotels 35%, cabs 15%, other 10%)
- Top vendors: Hotel X ₹3.2Cr (21% overpayment), Airline Y ₹5.1Cr (good deal)
- Policy violations: 12 this quarter (₹8L wasted)
- Savings opportunity: Switch Hotel X → IHG, save ₹45L/year

---

## Input (CFO Report Request)**

```json
{
  "company_id": "techcorp-001",
  "quarter": "Q1-2026",
  "total_spend": 180000000,
  "spend_breakdown": {
    "flights": 72000000,
    "hotels": 63000000,
    "cabs": 27000000,
    "other": 18000000
  },
  "top_vendors": [
    {"name": "Hotel X", "spend": 32000000, "overpayment_rate": "21%", "market_rate": 7000, "our_rate": 8500},
    {"name": "Airline Y", "spend": 51000000, "savings_rate": "14%", "market_rate": 52000, "our_rate": 45000}
  ],
  "policy_violations": {"count": 12, "wasted": 800000},
  "savings_opportunities": [
    {"action": "Switch Hotel X → IHG", "savings": 4500000},
    {"action": "Renegotiate Airline Y bulk rates", "savings": 2000000}
  ],
  "report_status": null
}
```

---

## Expected System Behavior**

1. **Analytics Engine** (`src/analytics/cfo_report.py` — to be built) processes Q1-2026 data.
2. **Spend Breakdown:** Auto-calculated: flights 40%, hotels 35%, cabs 15%, other 10%.
3. **Vendor Analysis:** "Hotel X: ₹3.2Cr, 21% overpayment (₹45L wasted). Switch to IHG, save 21%."
4. **Policy Violations:** "12 violations, ₹8L wasted. Top violator: Grade 3 employees booking >₹8K hotels."
5. **CFO PDF:** Auto-generated with charts, savings opportunities, and trend analysis.
6. **Output to Vikram:** "📊 CFO REPORT Q1-2026: ₹18Cr spend. Top savings: Switch Hotel X → IHG (₹45L/year). Generated in 5 minutes."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Analytics engine** | ❌ Not implemented | No `src/analytics/` directory |
| **CFO report generator** | ❌ Not implemented | No PDF generation for reports |
| **Spend breakdown** | ❌ Not implemented | No category analysis |
| **Vendor performance** | ❌ Not implemented | No overpayment detection |
| **Trend analysis** | ❌ Not implemented | No quarter-over-quarter comparison |

---

## Success Criteria**

- [ ] System analyzes ₹18Cr spend data within 60 seconds
- [ ] Spend breakdown auto-calculated with percentages
- [ ] Vendor overpayment detected: Hotel X 21% (₹45L wasted)
- [ ] Policy violations summarized: 12 incidents, ₹8L wasted
- [ ] CFO PDF generated with charts and savings recommendations
- [ ] Vikram saves 3-4 days per quarter (12-16 days/year)

---

## Failure Mode (If System Doesn't Help)**

Vikram spends 3-4 days building the report. CFO asks: "Why did Hotel X costs go up 15%?" Vikram spends 2 MORE days investigating. Total: 5-6 days per quarter = 20-24 days/year on ONE report.

---

## Notes**

- This is the #2 time-sink for corporate travel managers (after policy enforcement).
- The `quarterly_spend[]` array needs to be added to the canonical packet as `corporate.analytics`.
- Integration with accounting systems (SAP, Tally) would automate data ingestion (no manual Excel entry).
- **Related files to create:** `src/analytics/cfo_report.py`, `src/analytics/chart_generator.py`, `frontend/components/CFODashboard.tsx`
