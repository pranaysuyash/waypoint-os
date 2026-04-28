# Scenario P5-S1: Impossible Budget Rejection

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P0 (Blocking — lead qualification missing)

---

## Scenario Description**

An agency sends a lead to Anjali: "Family of 4, Maldives, 4 days, $2,000 budget." Anjali's DMC has a minimum: $800/person for 4 days in Maldives (standard resort, meals, transfers) = $3,200 minimum.

The agency doesn't know this. They quote the client $2,000. Client says yes. Anjali receives the booking request and has to call: "Sorry, $2,000 doesn't cover flights + resort + transfers. Minimum is $3,200."

The client is upset. The agency looks incompetent. Anjali loses the booking.

---

## Input (Lead Inquiry)**

```json
{
  "lead_id": "dmc-2026-0428",
  "destination": "Maldives",
  "travelers": "2 adults + 2 kids (ages 5, 8)",
  "duration_nights": 4,
  "budget_usd": 2000,
  "budget_per_person": 500,
  "dmc_minimum_usd": 3200,
  "feasibility_score": null,
  "auto_reject_reason": null
}
```

---

## Expected System Behavior**

1. **Feasibility Check** (`src/dmc/feasibility.py` — to be built) detects: `budget_per_person` ($500) < `dmc_minimum` ($800) for Maldives.
2. **Decision:** `NOT_FEASIBLE` with reason: "Maldives minimum $800/person (4 days). Your budget: $500/person."
3. **Alternatives:** Auto-suggest "Sri Lanka (similar beaches, $400/person feasible)" or "Increase budget to $3,200."
4. **DMC Response:** Auto-reject with explanation: "Sorry, $2,000 doesn't cover Maldives (min $3,200). Suggest Sri Lanka at $1,600."
5. **Output to agency:** "❌ NOT FEASIBLE: $500/person < $800 minimum. Alternative: Sri Lanka ($400/person) or increase budget to $3,200."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **DMC feasibility engine** | ❌ Not implemented | No `src/dmc/` directory |
| **Destination minimum checker** | ❌ Not implemented | No minimum cost database |
| **Auto-reject with alternatives** | ❌ Not implemented | No lead qualification |
| **Agency education** | ❌ Not implemented | Agencies keep quoting impossible budgets |

---

## Success Criteria**

- [ ] System detects budget $500/person < minimum $800/person within 5 seconds
- [ ] Feasibility score: 0/10 (impossible)
- [ ] Auto-reject with clear reason: "Maldives minimum $800/person"
- [ ] Alternatives auto-suggested: Sri Lanka ($400/person)
- [ ] Agency receives educational note: "Next time, Maldives minimum is $800/person"

---

## Failure Mode (If System Doesn't Catch It)**

Anjali receives 15 impossible leads per month. She spends 2 hours each explaining "why $2,000 doesn't work." That's 30 hours/month wasted. She stops prioritizing this agency's leads. The agency loses commission on 15 trips/month = ₹3-5L lost revenue.

---

## Notes**

- This is the #1 pain for DMCs. 70% of agency leads are poorly qualified.
- The `dmc_minimum_usd` field needs to be added to the DMC rate sheet upload.
- Educational notes should be persistent: "Agency X has been told 3 times: Maldives min $800."
- **Related files to create:** `src/dmc/feasibility.py`, `src/dmc/minimums_db.py`, `frontend/components/FeasibilityReject.tsx`
