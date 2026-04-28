# Scenario P5-S6: Crisis Protocol Generation#

**Persona:** P5 — DMC Liaison (Anjali)
**Date:** 2026-04-28
**Priority:** P2 (Medium — crisis response)

---

## Scenario Description**

A cyclone warning is issued for Maldives. 3 of Anjali's agency clients are arriving tomorrow. She needs a crisis protocol in <2 hours: "Rearrange itineraries, rebook resorts, manage client anxiety."

The system should auto-generate:
1. **Client A:** "Cyclone warning. Reschedule to next week OR move to resort with cyclone shelter."
2. **Client B:** "Flight cancelled? Auto-rebook on next available."
3. **Client C:** "Day 2 activity cancelled. Alternative: Resort kids' club + spa day."

---

## Input (Crisis Alert)**

```json
{
  "crisis_id": "dmc-2026-0433",
  "crisis_type": "cyclone_warning",
  "destination": "Maldives",
  "affected_trips": [
    {"client": "Agency X", "arrival": "2026-04-29", "resort": "Resort A"},
    {"client": "Agency Y", "arrival": "2026-04-29", "resort": "Resort B"},
    {"client": "Agency Z", "arrival": "2026-04-29", "resort": "Resort C"}
  ],
  "crisis_protocol": null,
  "rebooking_options": null
}
```

---

## Expected System Behavior**

1. **Crisis Engine** (`src/dmc/crisis.py` — to be built) detects: Cyclone warning → auto-generate protocols.
2. **Protocols:**
   - Client A: "Reschedule to May 5-10 (post-cyclone). Alt: Move to Resort B (cyclone shelter available)."
   - Client B: "Flight cancelled. Auto-rebook on Airline Y (next available, 6 AM tomorrow)."
   - Client C: "Day 2 activity cancelled. Alt: Resort kids' club (ages 4-12) + spa day (parents)."
3. **Time:** All protocols generated in <30 minutes.
4. **Output to Anjali:** "🌀 CRISIS PROTOCOL: 3 clients affected. Protocols generated in 25 minutes. Client A: Reschedule. Client B: Rebook. Client C: Alt activity."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Crisis engine** | ❌ Not implemented | No `src/dmc/crisis.py` |
| **Protocol generator** | ❌ Not implemented | No crisis playbooks |
| **Rebooking logic** | ❌ Not implemented | No auto-rebooking |
| **Alert system** | ❌ Not implemented | No crisis alerts |

---

## Success Criteria**

- [ ] System detects cyclone warning → generates protocols in <30 minutes
- [ ] 3 client protocols auto-generated with rebooking options
- [ ] Alternative activities suggested for cancelled events
- [ ] Anjali saves 4+ hours of manual crisis management
- [ ] Clients feel "taken care of" despite the crisis

---

## Failure Mode (If System Doesn't Generate Protocols)**

Anjali spends 6 hours on crisis calls: "Resort A, move clients. Resort B, rebook flights. Agency Y, find alt activities." Clients are anxious. Anjali looks disorganized. 1 client cancels = ₹2L lost revenue.

---

## Notes**

- This is the "premium service" DMCs provide during crises.
- The `crisis_protocols{}` dictionary needs to be built per destination (cyclone, coup, pandemic, etc.).
- Protocol templates should be customizable per DMC ("Our resort has shelter" vs. "Move to sister resort").
- **Related files to create:** `src/dmc/crisis.py`, `data/crisis_protocols/maldives.json`, `frontend/components/CrisisDashboard.tsx`
