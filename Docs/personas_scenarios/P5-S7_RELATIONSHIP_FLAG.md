# Scenario P5-S7: DMC-Agency Relationship Flag#

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P2 (Medium — relationship intelligence)

---

## Scenario Description**

Anjali notices: "Agency X has overpromised 5 times this month. They told clients 'suites available' when we only have deluxe. Each time, the client complains. I need to flag them: 'Agency X = overpromiser. Reduce their leads or educate them.'"

The system should track: "Agency X: 15 leads, 5 overpromised (33%). Flag: OVERPROMISE_RISK. Action: Send education email OR reduce lead flow."

---

## Input (Relationship Flag Request)**

```json
{
  "dmc_id": "dmc-island-001",
  "agency_id": "agency-x",
  "leads_received": 15,
  "overpromised_count": 5,
  "overpromise_rate": "33%",
  "relationship_flag": null,
  "recommended_action": null
}
```

---

## Expected System Behavior**

1. **Relationship Engine** (`src/dmc/relationship.py` — to be built) calculates: 5/15 = 33% overpromise rate.
2. **Flag:** `OVERPROMISE_RISK` — agency overpromises 33% of the time.
3. **Actions:**
   - "Send education email: 'Agency X, you've overpromised 5 times. Suites ≠ Deluxe. Here's the difference.'"
   - "Reduce lead flow: Send 50% fewer leads until they improve."
4. **Output to Anjali:** "⚠️ RELATIONSHIP FLAG: Agency X overpromises 33% of leads (5/15). Recommend: Education email + reduce leads 50%."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Relationship tracker** | ❌ Not implemented | No `src/dmc/relationship.py` |
| **Overpromise detector** | ❌ Not implemented | No flag system |
| **Agency education** | ❌ Not implemented | No auto-emails |
| **Lead flow control** | ❌ Not implemented | No throttling |

---

## Success Criteria**

- [ ] System detects 33% overpromise rate within 10 seconds
- [ ] Flag: OVERPROMISE_RISK (33% > 20% threshold)
- [ ] Education email auto-generated with examples
- [ ] Lead flow reduction suggestion: 50% fewer leads
- [ ] Anjali protects her DMC's reputation + saves 10 hours/month

---

## Failure Mode (If System Doesn't Flag)**

Anjali keeps sending leads to Agency X. They keep overpromising. Clients complain: "DMC said suites available!" DMC loses reputation. Anjali loses 3 agency partners = ₹30L annual revenue.

---

## Notes**

- This is DMC's "quality control" over agencies.
- The `agency_relationship{}` object needs to be added as `dmc.relationships`.
- Overpromise rate thresholds should be configurable (default: 20% = flag).
- **Related files to create:** `src/dmc/relationship.py`, `src/dmc/education.py`, `frontend/components/AgencyRelationshipDashboard.tsx`
