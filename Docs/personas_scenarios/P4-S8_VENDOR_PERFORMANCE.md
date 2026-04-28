# Scenario P4-S8: Vendor Performance Scoring#

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P2 (Medium — vendor optimization)

---

## Scenario Description**

Vikram wants to renew the contract with Hotel X (₹3.2Cr annual spend). But he's heard complaints: "Room too small," "Dirty carpets," "Slow wifi." He needs a performance score: "3.2/5 based on 15 complaints + 200 room-nights."

The system should analyze:
- **Complaints:** 15 in 12 months (12 for room size, 3 for cleanliness)
- **Score:** (200 - 15) / 200 × 5 = **4.6/5** (but weighted: room size = high severity = 3.2/5)
- **Recommendation:** "Renew at 5% discount (not 15%). Fix room size complaints first."

---

## Input (Vendor Performance Request)**

```json
{
  "company_id": "techcorp-001",
  "vendor": "Hotel X (Whitefield)",
  "annual_spend": 32000000,
  "room_nights": 200,
  "complaints": [
    {"type": "room_too_small", "count": 12, "severity": "high"},
    {"type": "dirty_carpet", "count": 3, "severity": "medium"}
  ],
  "current_discount": "15%",
  "performance_score": null,
  "recommended_discount": null
}
```

---

## Expected System Behavior**

1. **Performance Engine** (`src/vendor/performance.py` — to be built) calculates:
   - High severity: 12 × 3 weight = 36 points
   - Medium severity: 3 × 1 weight = 3 points
   - Total penalty: 39 points / 200 nights = 0.195 per night
   - Score: 5.0 - 0.195 = **4.8/5** (adjusted for severity = **3.2/5**)
2. **Decision:** "Score 3.2/5. High complaints on room size (12). Renew at 5% (not 15%)."
3. **Action Items:** "Tell Hotel X: 'Fix room size complaints (12 in 12 months) or discount drops to 0% next renewal.'"
4. **Output to Vikram:** "📊 VENDOR SCORE: Hotel X = 3.2/5. Room size complaints: 12 (high severity). Recommend: Renew at 5% (not 15%). Fix rooms first."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Performance scorer** | ❌ Not implemented | No `src/vendor/performance.py` |
| **Complaint tracker** | ❌ Not implemented | No complaint logging |
| **Renewal recommender** | ❌ Not implemented | No data-driven renewals |
| **Severity weighting** | ❌ Not implemented | No weighted scoring |

---

## Success Criteria**

- [ ] System calculates performance score: 3.2/5 within 10 seconds
- [ ] Severity weighted: room size (high) = 3x weight
- [ ] Renewal recommendation: 5% (not 15%) with justification
- [ ] Action items for vendor: "Fix X or discount drops to 0%"
- [ ] Vikram saves ₹32L/year (10% reduction on ₹3.2Cr)

---

## Failure Mode (If System Doesn't Score)**

Vikram renews Hotel X at 15% discount. Next year: 20 more complaints. Employees frustrated. CFO asks: "Why are we paying 15% for a 3.2/5 hotel?" Vikram: "I didn't know the score." Lost trust + ₹48L wasted.

---

## Notes**

- This turns vendor renewals from "relationship-based" to "data-driven."
- The `vendor_complaints[]` array needs to be added as `corporate.vendor_performance`.
- Complaint severity should be: low (1x), medium (2x), high (3x), critical (5x).
- **Related files to create:** `src/vendor/performance.py`, `src/vendor/renewal.py`, `frontend/components/VendorScoreDashboard.tsx`
