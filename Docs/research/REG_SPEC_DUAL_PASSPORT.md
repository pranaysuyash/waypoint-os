# Reg Spec: Secondary-Passport-Liaison (REG-REAL-005)

**Status**: Research/Draft
**Area**: Regulatory Compliance & Identity Management

---

## 1. The Problem: "The Entry Friction"
Travelers with multiple nationalities (Dual-Passport holders) often struggle to optimize their travel. They may use the "Wrong" passport for a destination, resulting in unnecessary visa fees, shorter stay limits, or increased interrogation at border control. Furthermore, maintaining two sets of visa-stamps and ensuring consistency in "Entry/Exit" records across different sovereign systems is a high-cognitive-load task.

## 2. The Solution: 'Dual-Nationality-Routing-Protocol' (DNRP)

The DNRP allows the agent to act as a "Sovereign-Identity-Strategist."

### Optimization Actions:

1.  **Optimal-Passport-Selection**:
    *   **Action**: For every destination, the agent autonomously compares all held passports against the destination's current entry requirements (Visa-on-arrival vs. E-visa vs. Visa-free).
2.  **Consular-Consistency-Audit**:
    *   **Action**: Ensuring the traveler exits a country on the *same* passport they used to enter, avoiding "Ghost-Traveler" flags in national immigration databases.
3.  **Visa-Reciprocity-Arbitrage**:
    *   **Action**: Identifying destinations where one passport has higher fees due to geopolitical tensions (e.g., US vs. Brazil) and autonomously switching to the "Neutral" or "Preferred" secondary passport.
4.  **Passport-Expiry-Synchronization**:
    *   **Action**: Managing the "Valid-For-6-Months" rule for *both* passports, alerting the traveler if their secondary passport is nearing a limit that would disqualify it for the next planned trip.

## 3. Data Schema: `Dual_Passport_Audit`

```json
{
  "audit_id": "DNRP-88221",
  "traveler_id": "GUID_9911",
  "active_passports": [
    {"country": "USA", "expiry": "2030-01-01", "id": "P-USA-1122"},
    {"country": "IRELAND", "expiry": "2028-05-05", "id": "P-IRE-3344"}
  ],
  "destination": "BRAZIL",
  "routing_verdict": "USE_IRELAND",
  "rationale": "IRELAND_IS_VISA_FREE;USA_REQUIRES_160_USD_EVISA",
  "entry_exit_consistency_check": "VERIFIED_SAME_AS_PREVIOUS_ENTRY"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Exit-Entry-Matching' Rule**: The agent MUST NOT recommend switching passports between entry and exit of a single jurisdiction.
- **Rule 2: Geopolitical-Sensitivity-Filter**: The agent MUST autonomously flag if using a specific passport for a destination would create "Future-Friction" (e.g., having a specific stamp that might complicate entry into a rival nation later).
- **Rule 3: Sovereign-Registration-Auto-Fill**: For E-visas, the agent autonomously populates the form using the "Optimized" passport's metadata.

## 5. Success Metrics (Compliance)

- **Visa-Fee-Savings**: Total $ saved for dual-nationals by avoiding unnecessary visa costs.
- **Stay-Duration-Yield**: % increase in available stay days achieved by using the preferred passport.
- **Border-Friction-Index**: Reduction in reported "Interrogation-Time" or "Secondary-Inspection" events.
