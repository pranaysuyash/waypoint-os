# Scenario P5-S4: Local Activity Curation

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P1 (High — DMC moat)

---

## Scenario Description**

An agency asks: "Family of 4, Maldives, kids ages 6 and 10. Recommend activities."

Anjali's DMC knows: "Best house reef for snorkeling = Resort X (north atoll). Best kids' club = Resort Y (south atoll). Best sunset dolphin cruise = Resort Z (west side)."

Generic OTAs recommend "snorkeling at House Reef" — but WHICH resort's house reef? Anjali's local intelligence is the differentiator.

The system should provide: "Resort X (north) — best house reef for kids 6-10. Resort Y (south) — kids' club rated 4.8/5. Resort Z (west) — dolphin cruise with 85% sighting rate."

---

## Input (Activity Curation Request)**

```json
{
  "trip_id": "dmc-2026-0431",
  "destination": "Maldives",
  "travelers": "2 adults + 2 kids (ages 6, 10)",
  "activity_type": "snorkeling + kids_activities",
  "local_intelligence": {
    "best_house_reef_kids_6_10": "Resort X (north atoll), visibility 20m, shallow 3-5ft",
    "best_kids_club": "Resort Y (south atoll), rated 4.8/5, ages 4-12",
    "best_dolphin_cruise": "Resort Z (west side), 85% sighting rate, sunset timing"
  },
  "ota_generic_recommendation": "House Reef snorkeling",
  "curated_recommendation": null
}
```

---

## Expected System Behavior**

1. **Local Intelligence Layer** (`src/dmc/local_intel.py` — to be built) applies: 
   - Kids 6+10 → Resort X house reef (shallow 3-5ft, visibility 20m)
   - Kids' club needed → Resort Y (rated 4.8/5, ages 4-12)
   - Dolphin cruise → Resort Z (85% sighting rate, sunset timing)
2. **Curated Output:** "Resort X (north) — best house reef for kids 6-10. Includes shallow areas (3-5ft). Resort Y (south) — kids' club 4.8/5. Resort Z (west) — dolphin cruise 85% success."
3. **Differentiation:** "OTA says 'House Reef.' We say WHICH resort and WHY it fits YOUR kids."
4. **Output to agency:** "📍 CURATED ACTIVITIES: Resort X house reef (shallow 3-5ft for ages 6-10). OTA would say 'House Reef' — we tell you WHICH one and WHY."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Local intelligence DB** | ❌ Not implemented | No `src/dmc/local_intel.py` |
| **Activity curation** | ❌ Not implemented | No destination-specific activities |
| **Resort intelligence** | ❌ Not implemented | No "which resort has best X" |
| **Differentiation engine** | ❌ Not implemented | No OTA vs. DMC comparison |

---

## Success Criteria**

- [ ] System curates 3 activities within 5 seconds based on traveler profile
- [ ] Local intelligence applied: "Resort X house reef (shallow 3-5ft)"
- [ ] Differentiation shown: "OTA says 'House Reef', we say WHICH resort"
- [ ] Agency receives DMC-specific intelligence (not generic OTA recs)
- [ ] Client gets better recommendation than any OTA can provide

---

## Failure Mode (If System Doesn't Curate)**

Anjali sends generic "House Reef snorkeling" like every OTA. The agency thinks: "Why am I paying DMC rates? I could just use Booking.com." Anjali loses the differentiation. Agency switches to OTA for "better prices."

---

## Notes**

- This is the DMC's core moat: local intelligence OTAs don't have.
- The `local_intelligence{}` dictionary needs to be built per destination (Maldives, Sri Lanka, Thailand, etc.).
- Crowdsourced from DMC experiences: "Anjali says Resort X has best house reef" → stored in DB.
- **Related files to create:** `src/dmc/local_intel.py`, `data/local_intelligence/maldives.json`, `frontend/components/LocalIntelDashboard.tsx`
