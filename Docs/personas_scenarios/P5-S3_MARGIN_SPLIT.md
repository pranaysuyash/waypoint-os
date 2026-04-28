# Scenario P5-S3: Margin Split Calculator

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P1 (High — commercial protection)

---

## Scenario Description**

An agency quotes a client: "Maldives, 4 days, $3,000." Anjali's DMC needs 18% margin, agency needs 15% margin. Total margin "cake" = 35%.

The agency quotes the client at $3,000. But they don't know: DMC's cost is $2,000. So DMC margin = ($3,000 - $2,000) / $3,000 = 33%. Agency margin = 0% (they didn't add their commission).

Anjali receives the booking. She sees: "Agency made $0 on this? That's not sustainable for them." She needs to tell the agency: "Add your 15% commission. New total: $3,450."

---

## Input (Margin Calculation Request)**

```json
{
  "trip_id": "dmc-2026-0430",
  "destination": "Maldives",
  "client_quote": 3000,
  "dmc_cost": 2000,
  "dmc_margin_target": "18%",
  "agency_margin_target": "15%",
  "total_margin_cake": null,
  "dmc_margin_actual": null,
  "agency_margin_actual": null,
  "corrected_quote": null
}
```

---

## Expected System Behavior**

1. **Margin Calculator** (`src/dmc/margin_calc.py` — to be built) processes: 
   - DMC margin = ($3,000 - $2,000) / $3,000 = 33% (above 18% target)
   - Agency margin = $0 (below 15% target)
   - Total margin = 33% (DMC is eating the whole cake)
2. **Decision:** `MARGIN_IMBALANCE` — agency made $0, not sustainable.
3. **Correction:** "Add agency 15%: $3,000 + $450 = $3,450. New split: DMC $1,000 (33%), Agency $450 (15%)."
4. **Output to agency:** "⚠️ MARGIN IMBALANCE: Agency made $0 on this quote. Corrected: Add 15% commission. New total: $3,450."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Margin calculator** | ❌ Not implemented | No `src/dmc/` directory |
| **Split analysis** | ❌ Not implemented | No DMC vs. agency split |
| **Commission tracker** | ❌ Not implemented | No commission validation |
| **Quote correction** | ❌ Not implemented | No auto-corrected quotes |

---

## Success Criteria**

- [ ] System calculates DMC margin: 33% (above 18% target) within 5 seconds
- [ ] Agency margin detected: $0 (below 15% target)
- [ ] Imbalance flagged: "Agency made $0, not sustainable"
- [ ] Corrected quote generated: $3,450 (adds agency 15%)
- [ ] Agency receives margin alert with corrected quote

---

## Failure Mode (If System Doesn't Calculate)**

Anjali receives 50+ bookings like this per month. Agencies consistently forget to add their 15% commission. They make $0. After 3 months, they stop booking with Anjali because "there's no money in it." Anjali loses 50 bookings/month = $150K revenue.

---

## Notes**

- This is the #1 commercial pain for DMCs. Agencies forget to add their own commission, then drop out.
- The `margin_split{}` object needs to be added to the canonical packet as `dmc_commercial.margin_split`.
- Both DMC AND agency margins should be tracked (not just one side).
- **Related files to create:** `src/dmc/margin_calc.py`, `src/dmc/commission_tracker.py`, `frontend/components/MarginDashboard.tsx`
