# Scenario P5-S2: Destination Intelligence Application

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P0 (Blocking — local intelligence missing)

---

## Scenario Description**

An agency sends a lead: "Family of 4, Maldives, July, whale watching + snorkeling." Anjali's DMC knows: "Whale watching season in Maldives is December-March. July = off-season, only 5% sighting rate."

The agency doesn't know this. They promise the client "guaranteed whale watching." The client arrives in July, no whales. They complain to the agency. The agency complains to Anjali. Everyone looks incompetent.

---

## Input (Lead Inquiry)**

```json
{
  "lead_id": "dmc-2026-0429",
  "destination": "Maldives",
  "travelers": "2 adults + 2 kids (ages 10, 12)",
  "dates": "2026-07-10 to 2026-07-14",
  "activities_requested": ["whale watching", "snorkeling"],
  "destination_intelligence": {
    "whale_watching_season": "December-March",
    "july_sighting_rate": "5%",
    "alternative": "dolphin watching (July success rate 60%)"
  },
  "intelligence_flag": null,
  "corrected_recommendation": null
}
```

---

## Expected System Behavior**

1. **Destination Intelligence** (`src/dmc/intelligence.py` — to be built) detects: "whale watching" in July = off-season (5% success rate).
2. **Flag:** `DESTINATION_INTELLIGENCE_WARNING`: "Whale watching in July = 5% sighting rate. Season: Dec-Mar."
3. **Alternative:** Auto-suggest "Dolphin watching (60% success rate in July)" or "Reschedule to December."
4. **DMC Response:** "⚠️ Whale watching in July = 5% chance. Suggest dolphins (60%) or reschedule to Dec-Mar."
5. **Output to agency:** "🐋 INTELLIGENCE FLAG: Whale watching July = 5% success. Suggest: Dolphins (60%) or reschedule to Dec-Mar."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Destination intelligence DB** | ❌ Not implemented | No `src/dmc/intelligence.py` |
| **Seasonal activity checker** | ❌ Not implemented | No seasonality data |
| **Alternative suggester** | ❌ Not implemented | No fallback activities |
| **Agency education** | ❌ Not implemented | Agencies keep promising wrong things |

---

## Success Criteria**

- [ ] System detects "whale watching" + July = off-season within 5 seconds
- [ ] Intelligence flag: "5% sighting rate, season is Dec-Mar"
- [ ] Alternative auto-suggested: "Dolphins (60% success) or reschedule"
- [ ] Agency receives educational note for future: "Whale season = Dec-Mar"
- [ ] Client gets realistic expectations = no complaints

---

## Failure Mode (If System Doesn't Apply Intelligence)**

The agency promises whale watching in July. Client arrives, no whales. Complaint: "You said we'd see whales!" Agency blames DMC: "You didn't tell us!" DMC loses trust. Agency loses client.

---

## Notes**

- This is the DMC's core moat: local intelligence agencies don't have.
- The `destination_intelligence` dictionary needs to be built per destination (Maldives, Sri Lanka, Thailand, etc.).
- Seasonality data can be crowdsourced from DMC experiences ( "Anjali says July = 5%").
- **Related files to create:** `src/dmc/intelligence.py`, `data/destination_intelligence/maldives.json`, `frontend/components/IntelligenceFlag.tsx`
