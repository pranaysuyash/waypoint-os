# Fin Spec: Agentic 'Fraud-Network' Watchdog (FIN-REAL-022)

**Status**: Research/Draft
**Area**: Ecosystem Security & Fraud Prevention

---

## 1. The Problem: "The Cross-Tenant Fraudster"
Fraudulent actors often use stolen identities or payment methods across multiple travel agencies to maximize their take before being detected. If Agency A identifies a fraudster, currently Agency B has no way of knowing that the same "Identity-Signature" is about to attempt a high-value booking on their platform. This "Security-Silo" makes the entire ecosystem vulnerable.

## 2. The Solution: 'Ecosystem-Security-Protocol' (ESP)

The ESP acts as the "Ecosystem-Immune-System."

### Security Actions:

1.  **Identity-Signature Fingerprinting**:
    *   **Action**: Creating an anonymized "Fraud-Fingerprint" for any traveler identity or payment method that is verified as fraudulent by a tenant. This includes device IDs, email patterns, and booking behaviors.
2.  **Cross-Agency Fraud-Alert**:
    *   **Action**: If a "High-Confidence-Match" is detected on *any* other tenant's booking (e.g., Agency B), the agent autonomously triggers a "High-Risk-Security-Hold."
3.  **Behavioral-Anomaly-Detection**:
    *   **Action**: Monitoring for "Ecosystem-Wide" anomalies (e.g., a single IP address attempting bookings across 5 different agencies within 10 minutes).
4.  **Collaborative-Verification-Circuit**:
    *   **Action**: If a traveler is flagged as "Suspicious" but not yet "Fraudulent," the agent can request a "Verified-Identity-Check" that, once completed, clears the traveler across the entire ecosystem.

## 3. Data Schema: `Ecosystem_Fraud_Alert`

```json
{
  "alert_id": "ESP-88221",
  "anonymized_identity_hash": "SHA256_A99221X",
  "fraud_type": "STOLEN_CARD_PATTERN",
  "detection_tenant_id": "AGENCY_ALPHA",
  "risk_score": 0.95,
  "impacted_tenants_alerted": 3,
  "status": "SECURITY_BLOCK_ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Privacy-First' Fingerprint**: Identity data used for fraud detection MUST be hashed and anonymized. No PII (Personally Identifiable Information) is shared between agencies—only the "Fraud-Signature."
- **Rule 2: The 'False-Positive' Relief**: There MUST be a clear "Identity-Recovery-Path" for travelers who are incorrectly flagged as fraudulent (e.g., someone with a similar email pattern but legitimate intent).
- **Rule 3: Autonomous-Block Authority**: If the "Risk-Score" exceeds a specific threshold (e.g., 0.90), the agent has the authority to autonomously block the transaction and notify the agency owner *after* the safety action is taken.

## 5. Success Metrics (Security)

- **Fraud-Containment-Rate**: % of cross-agency fraud attempts successfully blocked by the ESP.
- **Ecosystem-Loss-Avoidance**: Total USD saved across all tenants by preventing "Contagion-Fraud."
- **False-Positive-Rate (Security)**: % of legitimate transactions blocked by the fraud watchdog.
