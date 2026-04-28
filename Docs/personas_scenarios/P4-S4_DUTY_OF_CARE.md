# Scenario P4-S4: Duty-of-Care Dashboard

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P1 (High — legal liability)

---

## Scenario Description**

A coup erupts in Country X (Thailand). Vikram needs to know: which of his 1,200 employees are currently there? Which ones are traveling there next week? Do they have valid visas and travel insurance?

Current process: WhatsApp groups. "Who's in Thailand? Reply with dates." Takes 2-3 hours. Employees might not even see the message.

The system should provide: "3 employees in Thailand RIGHT NOW. 5 traveling next week. 2 don't have valid visas. 1 doesn't have insurance."

---

## Input (Duty-of-Care Query)**

```json
{
  "company_id": "techcorp-001",
  "query": "coup in Thailand",
  "date": "2026-04-28",
  "travelers_currently_in": {
    "Thailand": ["EMP001", "EMP045", "EMP078"],
    "upcoming_7days": ["EMP102", "EMP156", "EMP203", "EMP301", "EMP445"]
  },
  "visa_status": {
    "EMP001": "valid_thai_visa",
    "EMP045": "visa_on_arrival",
    "EMP078": "NO_VISA",
    "EMP102": "valid",
    "EMP156": "valid",
    "EMP203": "NO_VISA",
    "EMP301": "valid",
    "EMP445": "valid"
  },
  "insurance_status": {
    "EMP001": "covered",
    "EMP045": "covered",
    "EMP078": "NOT_COVERED",
    "EMP102": "covered",
    "EMP156": "covered",
    "EMP203": "covered",
    "EMP301": "NOT_COVERED",
    "EMP445": "covered"
  },
  "alert_level": null
}
```

---

## Expected System Behavior**

1. **Live Traveler Map** (`src/duty/map.py` — to be built) detects: 3 employees in Thailand NOW, 5 upcoming.
2. **Visa Check:** EMP078 (currently in Thailand) has NO visa. Flag as HIGH priority.
3. **Insurance Check:** EMP078 + EMP301 don't have travel insurance. Flag for evacuation coverage.
4. **Evacuation Protocol:** Auto-generate: "3 employees in coup zone. Options: (a) Earliest flight home, (b) Move to safe zone, (c) Embassy contact."
5. **Output to Vikram:** "🚨 DUTY OF CARE ALERT: 3 employees in coup-affected Thailand. EMP078 has NO visa + NO insurance. Evacuation options generated."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Live traveler tracking** | ❌ Not implemented | No `src/duty/` directory |
| **Visa status checker** | ❌ Not implemented | No visa tracking |
| **Insurance validator** | ❌ Not implemented | No coverage checks |
| **Evacuation protocol** | ❌ Not implemented | No crisis response |
| **Safety alerts** | ❌ Not implemented | No external feed integration |

---

## Success Criteria**

- [ ] System detects 3 employees in Thailand within 5 seconds
- [ ] Visa gaps flagged: 2 employees (current + upcoming) without valid visas
- [ ] Insurance gaps flagged: 2 employees without coverage
- [ ] Evacuation protocol auto-generated with 3 options
- [ ] Vikram sees alert within 60 seconds of coup notification

---

## Failure Mode (If System Doesn't Help)**

Coup in Thailand. Vikram doesn't know EMP078 is there without visa or insurance. EMP078 gets stranded. Company is sued for negligence. "You didn't know your employee was in a coup zone?"

---

## Notes**

- This is a legal compliance feature, not just convenience. Duty of Care is mandated in many jurisdictions.
- The `traveler_locations[]` array needs to be added to the canonical packet as `corporate.duty_map`.
- External feeds (state department alerts, news APIs) should be integrated for automatic crisis detection.
- **Related files to create:** `src/duty/map.py`, `src/duty/evacuation.py`, `frontend/components/DutyOfCareDashboard.tsx`
