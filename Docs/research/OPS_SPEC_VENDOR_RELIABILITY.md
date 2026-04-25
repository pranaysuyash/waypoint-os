# Ops Spec: Vendor-Reliability-Index (OPS-REAL-004)

**Status**: Research/Draft
**Area**: Supply Chain Integrity & Quality Control

---

## 1. The Problem: "The Ghost Booking"
Travelers frequently encounter "Operational-Friction" that isn't captured by public reviews: a hotel claiming they don't have the Expedia booking, a car rental desk forcing a "Mandatory" insurance upsell, or an airline consistently losing luggage on a specific hub-connection. The agency needs a "Private-Intelligence" layer to protect its travelers.

## 2. The Solution: 'Fulfillment-Fidelity-Protocol' (FFP)

The FFP allows the agent to act as a "Supply-Chain-Auditor" by tracking every interaction with a vendor and converting it into a 'Reliability-Score.'

### Auditor Actions:

1.  **Friction-Event-Logging**:
    *   **Action**: Capturing structured reports from travelers (via QA-REAL-001) such as: "Denied Check-in," "Room Type Mismatch," "Hidden Fee at Counter."
2.  **API-Fidelity-Monitoring**:
    *   **Action**: Measuring the delta between "GDS-Confirmed-Price" and "Actual-Final-Cost." Vendors with high "Hidden-Fee-Skew" are penalized.
3.  **Trust-Weighted-Recommendation**:
    *   **Action**: When presenting options, the agent MUST include a "Fidelity-Rating" (e.g., "98% Fulfillment Success"). The engine MUST deprioritize vendors with a score < 80% regardless of price.

## 3. Data Schema: `Vendor_Reliability_Profile`

```json
{
  "vendor_id": "HOTEL-PARIS-8822",
  "fidelity_score": 94.2,
  "incident_history": [
    {"type": "DENIED_CHECK_IN", "count": 1, "last_occurrence": "2026-03-12"},
    {"type": "HIDDEN_RESORT_FEE", "count": 12, "avg_impact_usd": 45.00}
  ],
  "api_stability": "STABLE",
  "fulfillment_verdict": "RELIABLE_WITH_FEES"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Blacklist-Trigger'**: If a vendor has > 2 "Denied-Service" incidents in 30 days, the agent MUST autonomously "Blacklist" them from all recommendations for 14 days.
- **Rule 2: Forced-Confirmation-Protocol**: For vendors with "Medium-Fidelity" (80-90%), the agent MUST perform a manual "Re-Confirmation-Call/Email" (OPS-001) 48 hours before arrival.
- **Rule 3: Transparency-of-Risk**: The agent MUST warn the traveler if they choose a "Low-Fidelity" vendor based on price (e.g., "Warning: This rental agency has a 30% reported rate of forced insurance upsells").

## 5. Success Metrics (Quality)

- **Operational-Friction-Rate**: % of trips with reported vendor-fulfillment issues.
- **Hidden-Fee-Capture**: Total $ value of hidden fees avoided or recovered through fidelity data.
- **Traveler-Confidence-Score**: Increase in traveler satisfaction when booking with "High-Fidelity" vendors.
