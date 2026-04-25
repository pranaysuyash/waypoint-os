# Supply Spec: Predatory Pattern Detection (SU-003)

**Status**: Research/Draft
**Area**: API Auditing & Ethical Supply Chains

---

## 1. The Problem: "The Black-Box API"
Vendors often use dynamic pricing algorithms that can be predatory (e.g., "Agency-Tax" or "High-Volume Discrimination"). Since the API is a "Black Box," these patterns are invisible to human auditors.

## 2. The Solution: 'API-Audit-Watchdog' (AAW)

The AAW runs persistent, "Blind-Comparison" queries to detect price discrimination and dark patterns.

### Audit Mechanisms:

1.  **Blind-Rate Comparison**:
    *   AI simultaneously queries the Vendor API using the "Agency Token" vs. a "Anonymous/Public Token."
    *   **Alert**: If the Agency Rate is consistently > 2% higher than the Public Rate for the same inventory.
2.  **Inventory 'Ghosting' Detection**:
    *   AI checks if certain "Low-Cost" inventory is hidden from the Agency but visible to public users.
    *   **Alert**: Discrepancy in availability for the same segment/room.
3.  **Surge-Pattern Audit**:
    *   AI monitors if prices "Surge" specifically when the Agency starts a mass-recovery (e.g., "Price spikes 50% immediately after 10 agency travelers start re-booking").

## 3. Data Schema: `Predatory_Pattern_Alert`

```json
{
  "alert_id": "PRED-1122",
  "vendor_id": "CAR-HERTZ",
  "pattern_type": "PRICE_DISCRIMINATION",
  "evidence": {
    "agency_rate": 145.00,
    "public_rate": 120.00,
    "delta_percentage": 20.8,
    "sample_size": 50
  },
  "impact": "Estimated annual loss: $250,000",
  "recommendation": "Switch to 'Enterprise-Rent-A-Car' for this hub until parity is restored."
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Adversarial-Query'**: The AAW must use rotated IPs and user-agents to ensure the vendor doesn't detect the audit.
- **Rule 2: Parity-Enforcement Mode**: If a vendor is "Caught" discriminating, the system can auto-apply a `Search_Penalty` to their SRI score.
- **Rule 3: Transparency Reporting**: All predatory alerts are shared with the "Procurement" and "Legal" teams for use in contract negotiations.

## 5. Success Metrics (Auditing)

- **Parity Gap**: % reduction in the delta between Agency and Public rates.
- **Supplier Fairness**: Increase in the number of "Integrity-Verified" suppliers in the system.
- **Cost Savings**: Dollars saved by avoiding discriminated rates.
