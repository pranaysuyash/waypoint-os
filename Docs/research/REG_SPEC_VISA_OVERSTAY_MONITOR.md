# Reg Spec: Visa-Overstay-Monitor (REG-REAL-003)

**Status**: Research/Draft
**Area**: Regulatory Compliance & Immigration

---

## 1. The Problem: "The Schengen 90/180 Trap"
For "Digital-Nomads" or frequent leisure/business travelers, tracking stay limits across regions is an architectural nightmare. The "Schengen 90/180" rule (90 days of stay in a rolling 180-day window) is notoriously difficult for humans to calculate accurately. Overstaying leads to fines, deportation, and multi-year entry bans.

## 2. The Solution: 'Stay-Limit-Auditor' (SLA)

The SLA allows the agent to act as a "Compliance-Officer" for the traveler's movement.

### Auditing Actions:

1.  **Rolling-Window-Calculation**:
    *   **Action**: Analyzing the past 180 days of flight/hotel data to calculate the *exact* number of days spent inside a specific visa-free zone (e.g., Schengen, UK, Thailand).
2.  **Itinerary-Conflict-Detection**:
    *   **Action**: Before finalizing any *future* booking, the agent MUST simulate the "Stay-Count." If the proposed trip would trigger an overstay, the booking is "Hard-Flagged."
3.  **Autonomous-Compliance-Alerting**:
    *   **Action**: Providing "T-Minus" countdowns. E.g., "You have 12 days remaining in the Schengen zone. Your current exit flight is scheduled for T-Minus 4 days. You are safe."
4.  **Visa-Run-Logistics-Automation**:
    *   **Action**: If the traveler is approaching a limit, the agent autonomously suggests "Visa-Run" destinations (e.g., moving from Spain to Morocco) to reset or pause the clock.

## 3. Data Schema: `Stay_Compliance_Report`

```json
{
  "report_id": "SLA-88221",
  "traveler_id": "GUID_9911",
  "region_zone": "SCHENGEN_ZONE",
  "days_spent_in_180_window": 74,
  "days_remaining_budget": 16,
  "next_proposed_entry": "2026-12-01",
  "next_proposed_duration": 10,
  "compliance_verdict": "COMPLIANT_WITH_MARGIN",
  "warning_threshold_triggered": false
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Exit-Buffer' Rule**: The agent MUST suggest an exit date at least 48 hours *before* the absolute legal limit to account for flight cancellations or delays.
- **Rule 2: Transit-Count-Rule**: The agent MUST accurately handle "Transit-Days." Even if a traveler is in a zone for 2 hours during a layover, some jurisdictions count this as a full "Day-In-Zone."
- **Rule 3: Sovereign-Entry-Check**: For non-visa-free zones, the agent MUST verify that the traveler's specific passport has the required entry-stamp or e-visa for the duration of the stay.

## 5. Success Metrics (Compliance)

- **Overstay-Incident-Rate**: Target: 0%.
- **Compliance-Detection-Accuracy**: % of calculated days vs actual border-control records.
- **Proactive-Intervention-Rate**: % of potentially non-compliant bookings prevented or corrected by the agent.
