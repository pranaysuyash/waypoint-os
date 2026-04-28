# Scenario P4-S7: Traveler Grade Mismatch#

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P0 (Blocking — policy violation)

---

## Scenario Description**

A Junior engineer (Grade 1) books a business class flight: "Delhi to Mumbai, business class, ₹45K." Company policy:
- **Grade 1-3:** Economy only, max ₹15K for flights <6 hours
- **Grade 4+:** Business allowed for flights >6 hours

The system should BLOCK: "Grade 1 + business class = POLICY VIOLATION. Economy only for Grade 1-3."

---

## Input (Grade Mismatch)**

```json
{
  "trip_id": "corp-2026-0431",
  "traveler_name": "Amit Kumar",
  "traveler_grade": "1",
  "flight_type": "business",
  "flight_cost": 45000,
  "grade_policy": {
    "grade_1_3": {"class": "economy", "max_cost_under_6h": 15000},
    "grade_4_plus": {"class": "business_allowed", "min_duration": "6h"}
  },
  "policy_violation": null,
  "block_booking": null
}
```

---

## Expected System Behavior**

1. **Grade Check** (`src/policy/grade_checker.py` — to be built) detects: Grade 1 + business class = VIOLATION.
2. **Decision:** `POLICY_VIOLATION` — Grade 1-3: economy only.
3. **Action:** BLOCK booking. Suggest: "Economy flight, ₹12K (within policy)."
4. **Alternate:** "Upgrade to Grade 4? (Requires promotion 😊)."
5. **Output to coordinator:** "❌ GRADE MISMATCH: Grade 1 + business class = violation. Book economy (₹12K) or escalate to HR for grade review."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Grade checker** | ❌ Not implemented | No `src/policy/grade_checker.py` |
| **Class enforcement** | ❌ Not implemented | No economy/business validation |
| **Booking blocker** | ❌ Not implemented | No pre-booking blocks |
| **HR escalation** | ❌ Not implemented | No grade review workflow |

---

## Success Criteria**

- [ ] System detects Grade 1 + business = violation within 5 seconds
- [ ] Booking BLOCKED with clear reason
- [ ] Economy alternative auto-suggested (₹12K)
- [ ] Optional: "Escalate to HR for grade review" (humor + practical)
- [ ] Travel coordinator cannot proceed until fixed

---

## Failure Mode (If System Doesn't Block)**

Amit books business class for ₹45K. CFO sees: "Junior engineer in business class? Who approved?" Vikram: "The system didn't flag it." Reprimand + Amit's flight downgraded = embarrassed employee.

---

## Notes**

- This is a common violation (juniors "testing the system").
- The `traveler_grade` field needs to be in the schema as `corporate.grade`.
- Grade policies should be configurable YAML (not hardcoded per company).
- **Related files to create:** `src/policy/grade_checker.py`, `src/policy/rules.yaml`, `frontend/components/GradeViolationBanner.tsx`
