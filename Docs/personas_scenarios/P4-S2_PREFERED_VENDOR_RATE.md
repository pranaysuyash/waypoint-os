# Scenario P4-S2: Preferred Vendor Rate Check

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P0 (Blocking — vendor rate tracking missing)

---

## Scenario Description**

Vikram's company has a negotiated rate with IHG (Holiday Inn, Crowne Plaza) at ₹6,500/night for Mumbai (standard room, includes breakfast). An agency books a Mid-grade manager at "Hotel Suba Palace" for ₹9,000/night — which is ₹2,500 MORE than the preferred IHG rate.

The agency didn't know about the IHG partnership. Vikram's company overpaid by ₹2,500/night × 3 nights = ₹7,500 for ONE trip. Across 200 trips/year, this type of mistake costs ₹15-20L annually.

---

## Input (Trip Brief)**

```json
{
  "trip_id": "corp-2026-0429",
  "traveler_name": "Anjali Mehta",
  "traveler_grade": "M3",
  "destination": "Mumbai (Andheri East)",
  "dates": "2026-07-05 to 2026-07-08",
  "hotel_requested": "Hotel Suba Palace",
  "hotel_rate": 9000,
  "company_policy_limit": 8000,
  "preferred_vendors": [
    {"name": "Holiday Inn Andheri", "rate": 6500, "includes": "breakfast", "status": "preferred"},
    {"name": "Crowne Plaza", "rate": 7200, "includes": "breakfast", "status": "preferred"}
  ],
  "rate_check_result": null
}
```

---

## Expected System Behavior**

1. **Preferred Vendor Check** (`src/vendor/rate_checker.py` — to be built) detects Suba Palace (₹9K) vs. preferred IHG (₹6.5K).
2. **Decision:** `PREFERRED_VENDOR_OVERPAY` — booking is 38% above preferred rate.
3. **Action:** Auto-suggest "Holiday Inn Andheri (₹6.5K, within policy, includes breakfast)."
4. **Savings Alert:** "Switching saves ₹2.5K/night = ₹7.5K total. Across 200 trips/year: ₹15L savings."
5. **Output to travel coordinator:** "⚠️ OVERPAY ALERT: Suba Palace ₹9K vs. Preferred IHG ₹6.5K. Switch saves ₹7.5K."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Preferred vendor database** | ❌ Not implemented | No `src/vendor/` directory |
| **Rate comparison engine** | ❌ Not implemented | No rate checking logic |
| **Savings calculation** | ❌ Not implemented | No cost optimization |
| **Agency awareness** | ❌ Not implemented | Juniors don't know partnerships |

---

## Success Criteria**

- [ ] System detects preferred vendor rate is 38% cheaper within 5 seconds
- [ ] Alternative (Holiday Inn, ₹6.5K) is auto-suggested
- [ ] Savings calculation: ₹2.5K/night × 3 nights = ₹7.5K
- [ ] Annualized savings estimate shown: "200 trips/year = ₹15L"
- [ ] Travel coordinator can one-click switch to preferred vendor

---

## Failure Mode (If System Doesn't Catch It)**

Vikram's CFO asks: "Why did we spend ₹18Cr this year when our IHG partnership gives us 30% discount?" Vikram can't answer because he doesn't know which trips OVERPAID.

The system should have flagged: "200 trips this year, 60 used non-preferred vendors. Overpayment: ₹45L."

---

## Notes**

- This is the #2 use-case for Corporate Travel Managers (cost optimization).
- The `preferred_vendors[]` array needs to be added to the canonical packet as `corporate.preferred_vendors`.
- Rate sheets should be uploadable as CSV/Excel (not manual entry).
- **Related files to create:** `src/vendor/rate_checker.py`, `src/vendor/preferred_db.py`, `frontend/components/VendorRateAlert.tsx`
