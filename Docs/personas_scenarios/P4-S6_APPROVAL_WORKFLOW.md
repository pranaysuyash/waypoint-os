# Scenario P4-S6: Approval Workflow#

**Persona:** P4 — Corporate Travel Manager (Vikram)
**Date:** 2026-04-28
**Priority:** P1 (High — policy enforcement)

---

## Scenario Description

A VP-grade employee (Grade 7) books a trip: "Tokyo, 5 days, business class, ₹3.5L total." Company policy:
- **VP-grade:** Max ₹4L, business class allowed
- **Approval needed:** >₹2L → Manager approval; >₹5L → VP approval

The system should auto-route to VP for approval since it's >₹2L. If the VP doesn't respond within 24 hours, escalate to CFO.

---

## Input (Approval Request)**

```json
{
  "trip_id": "corp-2026-0430",
  "traveler_name": "Rajesh Gupta",
  "traveler_grade": "7",
  "destination": "Tokyo",
  "total_cost": 350000,
  "grade_limit": 400000,
  "approval_threshold": 200000,
  "approval_status": null,
  "escalation_timer": null
}
```

---

## Expected System Behavior**

1. **Approval Engine** (`src/approval/workflow.py` — to be built) detects: `total_cost` (₹3.5L) > `approval_threshold` (₹2L).
2. **Routing:** Auto-route to VP for approval. Send email: "Approve or reject trip for Rajesh Gupta (₹3.5L)."
3. **Timer:** Start 24-hour clock. If no response, escalate to CFO: "VP hasn't responded in 24h. CFO, please approve/reject."
4. **Output to travel coordinator:** "⏳️ APPROVAL PENDING: VP approval required (₹3.5L > ₹2L threshold). Auto-escalate to CFO in 24h."

---

## Current System State**

| Component | Status | Evidence |
|------------|--------|----------|
| **Approval workflow** | ❌ Not implemented | No `src/approval/` directory |
| **Grade-based routing** | ❌ Not implemented | No escalation logic |
| **Timer/reminder** | ❌ Not implemented | No auto-escalation |
| **Email notifications** | ❌ Not implemented | No approval emails |

---

## Success Criteria**

- [ ] System detects approval needed (₹3.5L > ₹2L) within 5 seconds
- [ ] VP auto-notified via email within 60 seconds
- [ ] 24-hour timer starts on notification
- [ ] Auto-escalate to CFO after 24h of no response
- [ ] Travel coordinator sees "Pending" status with timer

---

## Failure Mode (If System Doesn't Help)**

Rajesh books the ₹3.5L trip without approval. CFO sees the expense: "Who approved this?" Answer: "Nobody." Vikram is reprimanded for not enforcing approval workflow.

---

## Notes**

- This is a core compliance feature for corporate travel.
- The `approval_status` field needs to be added to the canonical packet as `corporate.approval`.
- Email templates should be configurable per company (not hardcoded).
- **Related files to create:** `src/approval/workflow.py`, `src/approval/notifier.py`, `frontend/components/ApprovalBanner.tsx`
