# Ops Spec: Local-Connectivity-Audit (OPS-REAL-015)

**Status**: Research/Draft
**Area**: Connectivity & Digital Infrastructure

---

## 1. The Problem: "Roaming Bill Shock"
Travelers often face a binary choice: pay exorbitant carrier roaming fees ($10+/day) or waste time finding a local physical SIM card at the airport. eSIM technology exists, but comparing the best provider (Airalo, Holafly, Nomad, Ubigi) for a specific country's network coverage is a complex "Network-Arbitrage" problem.

## 2. The Solution: 'Network-Arbitrage-Protocol' (NAP)

The NAP allows the agent to act as a "Global-ISP-Manager."

### Connectivity Actions:

1.  **Carrier-Rate-Audit**:
    *   **Action**: Pinging the traveler's home carrier API to determine the exact roaming cost and data cap for the destination.
2.  **eSIM-Marketplace-Arbitrage**:
    *   **Action**: Querying multiple eSIM providers to find the "Lowest-Cost-per-GB" for the specific destination, prioritized by "Local-Carrier-Quality" (e.g., preferring a provider that uses Spark in NZ vs a lesser roaming partner).
3.  **Autonomous-Provisioning-Push**:
    *   **Action**: Buying the eSIM and pushing the "QR-Code" or "Direct-Install-Link" to the traveler's device T-24h before landing.
4.  **Data-Threshold-Watchdog**:
    *   **Action**: Monitoring the traveler's data usage. If they reach 80% of their plan, the agent autonomously "Top-Ups" the existing plan to prevent a connectivity gap.

## 3. Data Schema: `Connectivity_Audit_Engagement`

```json
{
  "engagement_id": "NAP-88221",
  "traveler_id": "GUID_9911",
  "destination": "JAPAN_NRT",
  "home_carrier": "VERIZON_US",
  "selected_provider": "AIRALO_JAPAN_MOSHI_MOSHI",
  "plan_details": "10GB_30DAYS",
  "cost_usd": 18.00,
  "roaming_savings_usd": 132.00,
  "install_status": "SENT_TO_TRAVELER"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Dual-SIM-Conflict' Warning**: The agent MUST check the traveler's device compatibility and provide clear "Toggle-Instructions" (e.g., "Turn off Primary SIM for Data") to prevent accidental roaming charges.
- **Rule 2: The 'Coverage-Priority' Rule**: The agent MUST prioritize network quality over cost if the traveler is on a "Business-Mission-Critical" trip (e.g., preferring 5G/LTE over 3G).
- **Rule 3: Airplane-Mode-Transition**: The agent sends a reminder as the traveler boards to install the eSIM, ensuring they have data the moment they touch down.

## 5. Success Metrics (Connectivity)

- **Roaming-Cost-Avoidance**: Total USD saved compared to the traveler's home carrier roaming rates.
- **Touchdown-Latency**: Time from "Landing" to "First-Successful-Data-Ping" at the destination.
- **Zero-Gap-Ratio**: % of trips where the traveler never experienced a data outage.
