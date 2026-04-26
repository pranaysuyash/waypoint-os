# Reg Spec: Agentic Visa-Expiry-Watchdog (REG-REAL-007)

**Status**: Research/Draft
**Area**: Regulatory Compliance & Traveler Safety

---

## 1. The Problem: "The Schengen Shuffle"
Travelers visiting multi-country zones (like the Schengen Area) or digital nomads moving frequently often lose track of their "Days-Consumed" vs. their "Stay-Allowance" (e.g., the 90/180-day rule). Overstaying a visa, even by one day, can result in heavy fines, immediate deportation, and long-term bans from the region.

## 2. The Solution: 'Stay-Duration-Monitor' (SDM)

The SDM allows the agent to act as a "Compliance-Officer."

### Compliance Actions:

1.  **GPS-to-Visa-Region Mapping**:
    *   **Action**: Continuously mapping the traveler's GPS coordinates to "Regulatory-Jurisdictions" (e.g., "Currently inside the Schengen Zone").
2.  **Rolling-Allowance-Calculation**:
    *   **Action**: Maintaining a "Rolling-Count" of days spent in a specific region over a defined window (e.g., "72 of 90 days used in the last 180 days").
3.  **Overstay-Risk-Alerting**:
    *   **Action**: Triggering "High-Severity-Alerts" at T-14d, T-7d, and T-48h before the stay allowance is exhausted.
4.  **Autonomous Exit/Extension-Planning**:
    *   **Action**: If an overstay risk is detected, the agent identifies the nearest "Non-Region" country for a "Border-Run" or provides a direct link to the local "Immigration-Extension-Portal."

## 3. Data Schema: `Visa_Stay_Telemetry`

```json
{
  "telemetry_id": "SDM-88221",
  "traveler_id": "GUID_9911",
  "region_id": "SCHENGEN_ZONE",
  "allowance_days": 90,
  "days_consumed": 78,
  "remaining_days": 12,
  "expiry_date": "2026-05-10",
  "planned_departure_date": "2026-05-15",
  "risk_status": "CRITICAL_OVERSTAY_PREDICTED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Partial-Day' Default**: Any portion of a day spent in the region (even a 2-hour airport layover outside the transit zone) MUST be counted as a "Full-Day" consumed for compliance safety.
- **Rule 2: Planned-Itinerary-Audit**: The agent MUST cross-reference the traveler's "Future-Itinerary" with their "Remaining-Allowance." If the planned departure is *after* the allowance expires, the agent MUST block any further bookings in that region until a "Compliance-Pivot" is confirmed.
- **Rule 3: Multi-Passport-Optimization**: For dual-citizens (REG-004), the agent autonomously identifies which passport provides the longest legal stay for the current region.

## 5. Success Metrics (Compliance)

- **Overstay-Incident-Rate**: Target: 0.00%.
- **Compliance-Alert-Lead-Time**: Average days of notice provided before stay expiry.
- **Pivot-Resolution-Velocity**: Time from risk detection to booking a "Border-Run" or extension.
