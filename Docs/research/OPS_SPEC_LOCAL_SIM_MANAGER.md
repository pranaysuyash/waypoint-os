# Ops Spec: Agentic Local-SIM-Logistics-Manager (OPS-REAL-017)

**Status**: Research/Draft
**Area**: Connectivity & Digital Infrastructure

---

## 1. The Problem: "The Roaming Data Trap"
Travelers frequently experience "Connectivity-Blackouts" due to poor roaming agreements or exorbitant data costs (e.g., "$10/day for 500MB"). While eSIMs are a common solution, identifying the *best* local provider for specific regions (e.g., "Vodafone has better coverage in the Scottish Highlands than EE") and managing the "Installation-Latency" is a point of friction that leaves travelers disconnected when they need the agent most.

## 2. The Solution: 'Connectivity-Assurance-Protocol' (CAP)

The CAP allows the agent to act as a "Virtual-Network-Operator."

### Connectivity Actions:

1.  **Roaming-Performance-Monitoring**:
    *   **Action**: Monitoring the traveler's "Mobile-Signal-Quality" and "Data-Latency" (via the Waypoint App) upon arrival in a new country.
2.  **eSIM-Arbitrage-Engine**:
    *   **Action**: Comparing the traveler's current roaming plan against 10+ local eSIM providers (e.g., Airalo, Holafly, local carriers) to identify the best "Data-per-USD" ratio.
3.  **Local-SIM Physical-Sourcing**:
    *   **Action**: If the traveler's device is not eSIM-compatible, the agent identifies the nearest "Physical-SIM" retailer (e.g., airport kiosk, convenience store) and provides a "Local-SIM-Request-Card" in the host language.
4.  **Data-Cap-Watchdog**:
    *   **Action**: Monitoring the traveler's "Data-Consumption." If they reach 80% of their local allowance, the agent autonomously identifies the "Top-Up" path or suggests a more efficient plan.

## 3. Data Schema: `Connectivity_Assurance_Event`

```json
{
  "event_id": "CAP-88221",
  "traveler_id": "GUID_9911",
  "current_country": "JAPAN",
  "roaming_provider": "VERIZON",
  "measured_latency_ms": 450,
  "esim_option_identified": "U_MOBI_JAPAN",
  "cost_usd": 12.00,
  "data_allowance_gb": 10,
  "status": "ESIM_INSTALLATION_LINK_SENT"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Zero-Downtime' Goal**: Connectivity alerts and eSIM options MUST be delivered *before* the traveler leaves the airport's free Wi-Fi zone.
- **Rule 2: Device-Compatibility-Check**: The agent MUST verify the traveler's "Device-Model" (e.g., iPhone 15 vs. older Android) before suggesting an eSIM to avoid "Incompatible-Hardware" errors.
- **Rule 3: Backup-Communication-Path**: If data is lost entirely, the agent MUST provide a "Offline-Map-Snippet" and "Local-Language-Emergency-Card" to the traveler's device for critical safety.

## 5. Success Metrics (Connectivity)

- **Connection-Uptime-Ratio**: % of trip time where the traveler has >1Mbps data speed.
- **Data-Cost-Savings**: USD saved by using agentic arbitrage vs. generic roaming plans.
- **Onboarding-Latency**: Time from arrival to "First-Byte" of local data connectivity.
