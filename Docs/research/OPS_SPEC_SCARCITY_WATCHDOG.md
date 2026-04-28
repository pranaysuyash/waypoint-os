# Ops Spec: Agentic 'Destination-Scarcity' Watchdog (OPS-REAL-033)

**Status**: Research/Draft
**Area**: Scarce-Access Intelligence, Permit Quota Management & Conservation-Constrained Inventory

---

## 1. The Problem: "The Scarcity-Blindspot"
The world's most desirable destinations increasingly operate under strict access controls: Machu Picchu limits daily visitors to 5,600; Gorilla trekking permits in Rwanda sell out 12 months ahead; Bhutan enforces a $200/day Sustainable Development Fee with limited licensed operator slots; the Galápagos has strict cruise capacity limits. Most agencies discover these constraints only when their traveler is already committed to a destination — and the permits are already sold out. This "Scarcity-Blindspot" causes devastating booking failures at the highest-stakes moments.

## 2. The Solution: 'Inventory-Scarcity-Protocol' (ISP)

The ISP acts as the "Scarce-Access-Intelligence-Engine."

### Scarcity Actions:

1.  **Destination-Scarcity-Registry**:
    *   **Action**: Maintaining a continuously updated "Scarcity-Registry" covering 200+ destinations with permit quotas, conservation caps, seasonal windows, UNESCO visitor limits, and licensed operator slot availabilities — with real-time monitoring of remaining inventory.
2.  **Permit-Lead-Time-Modeling**:
    *   **Action**: For each constrained destination, modeling the "Permit-Lead-Time-Distribution" — the number of months in advance that permits typically sell out, segmented by season and global travel demand patterns.
3.  **Proactive-Permit-Procurement**:
    *   **Action**: When a traveler's interest in a scarcity-constrained destination is detected (even at the "inspiration" stage, before booking), the agent immediately alerts the agency to the permit availability status and recommends securing access now — not at booking confirmation.
4.  **Scarcity-Driven-Urgency-Communication**:
    *   **Action**: Communicating permit scarcity to travelers in honest, non-manipulative terms: "Gorilla trekking permits for June 2027 have 4 slots remaining across all operators. This isn't a sales tactic — this is what the conservation quota looks like."

## 3. Data Schema: `Scarcity_Watchdog_Alert`

```json
{
  "alert_id": "ISP-88221",
  "destination": "RWANDA_GORILLA_TREKKING",
  "permit_quota_daily": 96,
  "permits_remaining_target_date": 4,
  "target_date": "2027-06-15",
  "lead_time_model_months": 14,
  "traveler_interest_detected": true,
  "procurement_recommendation": "SECURE_NOW_CRITICAL",
  "last_availability_check": "2026-04-27T12:00:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Interest-Stage-Detection'**: Scarcity alerts MUST trigger at the traveler's "Inspiration-Stage" — when they first mention a destination, not when they confirm a booking. Early detection is the entire value.
- **Rule 2: The 'Honest-Scarcity-Communication' Standard**: Scarcity language MUST be factual and verifiable. The agent MUST cite the specific quota number and remaining availability. No manufactured urgency.
- **Rule 3: The 'No-Speculative-Holds' Rule**: The agent MUST NOT secure permit holds without agency owner authorization. Permit deposits are real financial commitments, not provisional reservations.

## 5. Success Metrics (Scarcity)

- **Permit-Procurement-Lead-Time**: Average days before departure that scarcity-constrained permits are secured vs. industry baseline.
- **Scarcity-Failure-Rate**: % of bookings involving scarcity-constrained destinations that fail due to unavailability.
- **Interest-to-Alert-Latency**: Average minutes from traveler mentioning a constrained destination to Scarcity-Alert being delivered to the agency.
