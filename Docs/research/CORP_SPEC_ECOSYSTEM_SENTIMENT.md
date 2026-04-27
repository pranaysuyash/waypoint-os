# Corp Spec: Agentic 'Ecosystem-Sentiment' Pulse (CORP-REAL-028)

**Status**: Research/Draft
**Area**: Network-Wide Traveler Sentiment & Systemic Quality Intelligence

---

## 1. The Problem: "The Blind Ecosystem"
Individual agencies can monitor their own traveler reviews and CSAT scores. However, the SaaS platform itself lacks a "Macro-View" of collective traveler sentiment. If 30 agencies across the network are all seeing negative feedback about a specific vendor (e.g., a hotel chain's new management), the platform doesn't know unless each agency independently raises the issue. This "Ecosystem-Blindness" prevents the platform from taking proactive systemic actions.

## 2. The Solution: 'Network-Health-Protocol' (NHP)

The NHP acts as the "Ecosystem-Cardiologist."

### Pulse Actions:

1.  **Cross-Agency-Sentiment-Aggregation**:
    *   **Action**: Aggregating anonymized CSAT and review signals from across all agencies in the network, normalized by trip type and destination.
2.  **Systemic-Vendor-Failure-Detection**:
    *   **Action**: Identifying when a specific vendor's sentiment score drops below a "Network-Threshold" across multiple agencies simultaneously (e.g., "Hotel Chain X's score has dropped -15% across 12 agencies in the past 7 days").
3.  **Platform-Wide-Advisory-Broadcast**:
    *   **Action**: Autonomously broadcasting a "Vendor-Advisory" or "Destination-Advisory" to all affected agencies in the network, warning them before they commit new bookings.
4.  **Ecosystem-Recovery-Tracking**:
    *   **Action**: Monitoring vendor sentiment over time to detect recovery patterns and broadcasting "All-Clear" signals when a vendor's quality has normalized.

## 3. Data Schema: `Ecosystem_Sentiment_Signal`

```json
{
  "signal_id": "NHP-99221",
  "signal_type": "VENDOR_SYSTEMIC_FAILURE",
  "vendor_name": "HOTEL_CHAIN_X",
  "affected_agency_count": 14,
  "sentiment_drop_percent": -18.5,
  "network_advisory_status": "ADVISORY_BROADCAST_ACTIVE",
  "estimated_recovery_date": "2026-05-15"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Anonymity-Firewall'**: Sentiment signals MUST be fully anonymized. No agency should be able to identify which specific competitor's traveler left a specific review.
- **Rule 2: Statistical-Significance-Gate**: A "Vendor-Advisory" MUST only be triggered after crossing both a "Magnitude-Threshold" (>10% drop) AND a "Volume-Threshold" (>5 agencies affected).
- **Rule 3: Opt-In-Participation**: Agencies MUST opt in to share their anonymized sentiment data to receive platform-wide advisories.

## 5. Success Metrics (Ecosystem)

- **Systemic-Issue-Detection-Lag**: Average time between a vendor quality drop and the platform's "Vendor-Advisory" broadcast.
- **Pre-emptive-Booking-Avoidance**: Total revenue saved by agencies who received advisories before committing new bookings to a failing vendor.
- **Network-CSAT-Growth**: Aggregate improvement in ecosystem-wide traveler CSAT scores attributed to advisory actions.
