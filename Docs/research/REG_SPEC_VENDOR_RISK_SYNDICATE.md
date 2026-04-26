# Reg Spec: Agentic 'Vendor-Risk-Syndicate' (REG-REAL-016)

**Status**: Research/Draft
**Area**: Ecosystem Safety & Collective Intelligence

---

## 1. The Problem: "The Isolated Vendor Failure"
A vendor failure (e.g., a hotel fire, a tour operator bankruptcy, or a systemic maintenance issue with a specific car rental branch) often impacts multiple agencies simultaneously. Currently, each agency is an "Information-Silo." If Agency A discovers a major safety issue at a property, Agency B might book a family into that same property an hour later, unaware of the risk.

## 2. The Solution: 'Collective-Intelligence-Protocol' (CIP)

The CIP acts as the "Ecosystem-Warning-System."

### Syndicate Actions:

1.  **Anonymized Incident-Pooling**:
    *   **Action**: Aggregating safety, reliability, and service-failure reports from all agencies in the SaaS network. Reports are anonymized to protect traveler privacy but maintain "Vendor-Fidelity."
2.  **Systemic-Risk-Trigger**:
    *   **Action**: If a specific vendor ID receives >3 "Critical-Failure" reports (e.g., "Non-functioning smoke detectors," "Stranded travelers due to no-show") within a 24h window, the agent triggers an "Ecosystem-Alert."
3.  **Autonomous Booking-Blocker**:
    *   **Action**: Once a vendor is "High-Risk-Flagged," the agent autonomously blocks new bookings for that vendor across *all* tenants until the risk is mitigated or verified.
4.  **Existing-Booking 'Proactive-Review'**:
    *   **Action**: The agent identifies all *pending* or *active* bookings with the high-risk vendor across the entire network and suggests "Proactive-Pivots" to the respective agency owners.

## 3. Data Schema: `Vendor_Risk_Alert`

```json
{
  "alert_id": "CIP-77221",
  "vendor_id": "HOTEL_LUXE_NYC",
  "risk_type": "FIRE_SAFETY_FAILURE",
  "incident_count": 4,
  "confidence_score": 0.98,
  "impacted_tenants": 12,
  "active_bookings_at_risk": 45,
  "status": "ECOSYSTEM_ALERT_ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Truth-Verification' Guardrail**: To prevent "Malicious-Reporting" (e.g., an agency flagging a competitor's partner), reports MUST be verified against independent data sources (e.g., local news, social media, or official safety registries) before triggering an ecosystem-wide block.
- **Rule 2: Anonymity-by-Design**: Tenant-identifiable information MUST be stripped from the risk alerts. Agencies only see the "Vendor-ID" and the "Risk-Type."
- **Rule 3: Graduated-Response-Scale**: Risks are categorized (e.g., Low: Service Delay, Moderate: Amenity Missing, High: Life Safety). The agent's autonomous response (Warning vs. Block) is mapped to this scale.

## 5. Success Metrics (Ecosystem Safety)

- **Risk-Containment-Velocity**: Time from the first incident report to the ecosystem-wide booking block.
- **Avoided-Incident-Count**: Estimated number of travelers protected from a high-risk vendor through the syndicate alert.
- **False-Positive-Rate**: % of vendor blocks that were later found to be based on inaccurate or malicious reports.
