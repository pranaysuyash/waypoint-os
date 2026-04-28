# Scenario P5-S8: Rate Sheet Freshness Check#

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P1 (High — stale data)

---

## Scenario Description**

Anjali's rate sheet is 45 days old. She's updated rates (₹380/night now, sheet says ₹300), but agencies are still quoting clients at ₹300. Clients complain: "Why is it ₹380 now? You said ₹300!"

The system should alert: "Rate sheet is 45 days old. Update needed. Agencies quoting stale rate: ₹300 (now ₹380). Auto-notify agencies: 'Rate update: ₹380/night effective immediately.'"

---

## Input (Rate Sheet Check)**

```json
{
  "dmc_id": "dmc-island-001",
  "rate_sheet_date": "2026-03-14",
  "days_since_update": 45,
  "sheet_rate": 300,
  "current_rate": 380,
  "agencies_quoting_stale": 8,
  "freshness_alert": null
}
```

---

## Expected System Behavior**

1. **Freshness Checker** (`src/dmc/rate_freshness.py` — to be built) detects: 45 days > 30-day threshold = STALE.
2. **Alert:** "Rate sheet 45 days old. Update needed. 8 agencies quoting stale ₹300 (now ₹380)."
3. **Actions:**
   - "Auto-notify 8 agencies: 'Rate update: ₹380/night effective immediately.'"
   - "Generate new rate sheet PDF with ₹380 rates."
4. **Output to Anjali:** "⚠️ RATE SHEET STALE: 45 days old. 8 agencies quoting ₹300 (now ₹380). Auto-notified. New sheet generated."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Freshness checker** | ❌ Not implemented | No `src/dmc/rate_freshness.py` |
| **Agency notifier** | ❌ Not implemented | No auto-alerts |
| **Rate sheet generator** | ❌ Not implemented | No PDF generation |
| **Stale rate tracker** | ❌ Not implemented | No expiry alerts |

---

## Success Criteria**

- [ ] System detects 45 days > 30-day threshold within 5 seconds
- [ ] Freshness alert: "Rate sheet stale, update needed"
- [ ] 8 agencies auto-notified with new ₹380 rate
- [ ] New rate sheet PDF generated automatically
- [ ] Anjali saves 3+ hours/week on rate update calls

---

## Failure Mode (If System Doesn't Alert)**

Anjali's rate sheet stays stale for 60+ days. 15 agencies quote ₹300. Clients complain about ₹380 "price jump." Anjali loses 5 agencies = ₹25L revenue. Reputation damaged: "DMC doesn't communicate rate changes."

---

## Notes**

- This is the #1 operational pain for DMCs (stale rates = lost trust).
- The `rate_sheet_date` field needs to be tracked as `dmc.rate_sheet.last_updated`.
- Threshold should be configurable (default: 30 days = alert).
- **Related files to create:** `src/dmc/rate_freshness.py`, `src/dmc/agency_notifier.py`, `frontend/components/RateFreshnessAlert.tsx`
