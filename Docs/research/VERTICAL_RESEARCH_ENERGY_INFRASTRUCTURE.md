# Vertical Research: Energy, Utilities & Infrastructure

**Status**: Research/Draft
**Area**: High-Stakes Logistics & Operational Windows

---

## 1. Context: The 'Mission-Critical' Rotation
In the energy sector (Oil & Gas, Renewables, Mining), travel is about **Crew Rotations**. If a specialist doesn't arrive on an offshore rig or a remote mine site on time, the entire operation can stop, costing $100k+ per day.

## 2. Specialized Operational Requirements

### [A] Logistical Window Sync (The 'Heli-Lift' Problem)
- **Constraint**: Commercial flights must sync with specialized private transfers (Helicopters, Crew Boats). These transfers have strict windows due to weather and maritime rules.
- **Action**: The system must track the "Transfer Window" as a hard constraint. If the commercial flight is delayed by 30m, it must auto-flag the "Missed Heli-Lift" risk.

### [B] Certification & Safety Compliance
- **Constraint**: Travelers must have specific certifications (e.g., HUET - Helicopter Underwater Escape Training) to board certain transfers.
- **Action**: Include `Safety_Certifications` in the traveler persona. Block booking if certifications are expired or missing.

### [C] Multi-Modal Ghost Bookings
- **Constraint**: Rotations often involve "Ghost" segments (e.g., a boat transfer that isn't in a GDS).
- **Action**: Support `Manual_Logistics_Nodes` that the AI monitors for delay impacts, even if it can't "book" them directly.

## 3. Frontier Scenarios (Energy)

1.  **EN-001: The 'Rig-Down' Escalation**:
    *   **Scenario**: A flight delay for a turbine engineer risks a 24h delay in a rig-up operation.
    *   **Recovery**: AI calculates the "Cost of Delay" ($150k) vs. "Cost of Charter" ($20k) and auto-escalates to `CRITICAL` with a "Pre-Approved Charter Solution."

2.  **EN-002: The 'Certification-Block' at Check-in**:
    *   **Scenario**: A traveler is at the heli-port but their safety certificate is not in the system.
    *   **Recovery**: AI retrieves the certificate from the `Corporate_Compliance_Vault` and pushes it to the heli-port operator's tablet in real-time.

3.  **EN-003: The 'Remote-Mine' Mass Reroute**:
    *   **Scenario**: A cyclone closes the primary air-strip for a remote mine. 50 crew members need to be rerouted via a 10-hour bus journey + 3 charter flights.
    *   **Recovery**: `Mass_Action` logic that splits the 50 crew members across available charter capacity based on "Role Priority" (e.g., Safety Officers first).

## 4. Key Logic Extensions

- **Extension 1: Cost-of-Delay Ledger**: Integrating the company's "Production Loss per Hour" into the `Urgency_Score`.
- **Extension 2: Certification Heartbeat**: Proactive alerts 60 days before a safety certification expires.
- **Extension 3: Role-Based Priority**: In a mass-disruption, the system prioritizes "Essential Operators" over "Support Staff."

## 5. Success Metrics (Energy)

- **Rotation Integrity**: 100% success rate for crew members meeting their private transfer windows.
- **Penalty Mitigation**: Dollars saved by avoiding production downtime via proactive rerouting.
- **Compliance Rate**: Zero travelers arriving at site without valid safety credentials.
