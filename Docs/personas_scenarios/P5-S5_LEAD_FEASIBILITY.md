# Scenario P5-S5: Lead Feasibility Pre-Check#

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P0 (Blocking — time waster)

---

## Scenario Description**

An agency sends: "Family of 10, 2 days, Maldives." Anjali's DMC knows: "Maldives minimum = 4 days (includes seaplane transfer + resort check-in + activity day)."

The system should auto-reject: "2 days for family of 10 in Maldives = IMPOSSIBLE. Minimum 4 days. Suggest: (a) Extend to 4 days, (b) Switch to Sri Lanka (2 days feasible)."

---

## Input (Lead Feasibility Check)**

```json
{
  "lead_id": "dmc-2026-0432",
  "destination": "Maldives",
  "travelers": "2 adults + 8 kids (ages 4-12)",
  "duration_nights": 2,
  "dmc_minimum_nights": 4,
  "feasibility_score": null,
  "auto_reject_reason": null
}
```

---

## Expected System Behavior**

1. **Feasibility Engine** (`src/dmc/lead_check.py` — to be built) detects: 2 nights < 4 minimum = IMPOSSIBLE.
2. **Decision:** `NOT_FEASIBLE` — family of 10 needs 4+ days in Maldives (transfer + check-in + activities).
3. **Alternatives:** 
   - "Extend to 4 days (minimum for Maldives)"
   - "Switch to Sri Lanka (2 days feasible, family-friendly)"
4. **Output to agency:** "❌ NOT FEASIBLE: 2 days for family of 10 in Maldives = impossible. Minimum 4 days. Alternative: Sri Lanka (2 days feasible)."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Lead feasibility engine** | ❌ Not implemented | No `src/dmc/lead_check.py` |
| **Minimum duration DB** | ❌ Not implemented | No destination minimums |
| **Auto-reject logic** | ❌ Not implemented | No pre-check |
| **Alternative suggester** | ❌ Not implemented | No fallbacks |

---

## Success Criteria**

- [ ] System detects 2 nights < 4 minimum within 5 seconds
- [ ] Feasibility score: 0/10 (impossible)
- [ ] Auto-reject with clear reason: "Minimum 4 days for Maldives"
- [ ] Alternatives auto-suggested: Extend to 4 days OR switch to Sri Lanka
- [ ] Agency saves 2 hours of quoting impossible lead

---

## Failure Mode (If System Doesn't Pre-Check)**

Anjali receives the lead. Spends 2 hours building a 2-day Maldives itinerary. Sends to agency. Client says: "2 days? We can't even settle in!" Agency looks incompetent. Anjali wasted 2 hours.

---

## Notes**

- This is the #3 time-sink for DMCs (impossible leads).
- The `dmc_minimum_nights` field needs to be in destination intelligence DB.
- Family size should affect minimum duration (10 people = +1 day minimum).
- **Related files to create:** `src/dmc/lead_check.py`, `data/destination_intelligence/maldives.json`, `frontend/components/LeadFeasibilityBanner.tsx`
