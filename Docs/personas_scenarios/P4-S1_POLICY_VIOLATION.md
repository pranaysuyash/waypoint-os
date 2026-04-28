# Scenario P4-S1: Policy Violation Catch

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P0 (Blocking — policy engine missing)

---

## Scenario Description**

Vikram receives a booking request from a Mid-level Manager (Grade M2) for a hotel in Mumbai. The company policy is:
- **Junior/Mid-grade (M1-M3):** Max ₹8,000/night
- **Senior-grade (M4+):** Max ₹15,000/night  
- **VP-grade:** Max ₹25,000/night, business class allowed

The manager requests "Taj Lands End, ₹14,000/night" — which is 75% above their allowed limit.

---

## Input (Trip Brief)**

```json
{
  "trip_id": "corp-2026-0428",
  "traveler_name": "Rahul Sharma",
  "traveler_grade": "M2",
  "destination": "Mumbai",
  "dates": "2026-06-10 to 2026-06-12",
  "hotel_requested": "Taj Lands End",
  "hotel_rate": 14000,
  "company_policy_limit": 8000,
  "policy_violation": null,
  "approval_required": null
}
```

---

## Expected System Behavior**

1. **Policy Engine** (`src/policy/engine.py` — to be built) detects: `hotel_rate` (14,000) > `company_policy_limit` (8,000) for grade M2.
2. **Decision:** `POLICY_VIOLATION` with severity `HIGH` (75% over limit).
3. **Alternatives:** Suggest "Taj Santacruz" (₹7,500/night) — within policy, preferred vendor.
4. **Approval Workflow:** `approval_required: true`, escalate to VP level (2x policy limit rule).
5. **Output to travel coordinator:** "⚠️ POLICY VIOLATION: ₹14K > ₹8K (M2 limit). VP approval required. Alternative: Taj Santacruz ₹7.5K (within policy)."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Policy engine** | ❌ Not implemented | No `src/policy/` directory |
| **Grade-based limits** | ❌ Not implemented | No traveler grade in schema |
| **Approval workflow** | ❌ Not implemented | No escalation routing |
| **Preferred vendor check** | ❌ Not implemented | Sourcing hierarchy is documented, not built |

---

## Success Criteria**

- [ ] System detects policy violation within 5 seconds of brief creation
- [ ] Severity is correctly calculated: `(14000-8000)/8000 = 75% over = HIGH`
- [ ] Alternative within policy is suggested automatically
- [ ] Approval workflow triggers: `approval_required: true`, escalate to VP
- [ ] Travel coordinator sees clear violation message with alternative

---

## Failure Mode (If System Doesn't Catch It)**

Rahul's booking goes through at ₹14,000/night. CFO sees the expense report: "Why is a Mid-grade manager staying at Taj Lands End?" Vikram is asked: "Who approved this?" Answer: "The system didn't flag it." Vikram is reprimanded.

---

## Notes**

- This is the #1 use-case for Corporate Travel Managers. If the tool can't enforce policy, they won't buy.
- The `traveler_grade` field needs to be added to the canonical packet as `corporate.grade`.
- Policy rules should be configurable per company (not hardcoded).
- **Related files to create:** `src/policy/engine.py`, `src/policy/rules.yaml`, `frontend/components/PolicyViolationBanner.tsx`
