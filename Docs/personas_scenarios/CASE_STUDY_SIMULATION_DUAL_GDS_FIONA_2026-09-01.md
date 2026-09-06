# Case Study: Dual-Stack Live GDS Sandbox Simulation (Fiona Gallagher — P10-GDS-01)

**Persona Profile**: Fiona Gallagher, Director of Global Distribution & NDC Engineering at Amadeus-Sabre Multi-Host Solutions\
**Simulation Date**: September 1, 2026\
**Primary Scenario**: Dual-Host Sandbox Flight Query & Instant PNR / E-Ticket Issuance on JFK-LHR (`EXP-GDS-JFK-LHR-01`)\
**Underlying Architecture**: Dual GDS Sandbox Connector (`GDSSandboxPanel.tsx`), Amadeus Travel Innovation API & Sabre Dev Studio Bridge, and Fare Basis Parser.

---

## 1. Executive Summary & Business Challenge

TMCs and high-volume corporate travel agencies cannot rely on a single distribution pipe:

1. **Single-GDS Vulnerability**: When a primary GDS gateway experiences downtime or rate limiting, travel consultants lose the ability to quote and ticket flights.
2. **EDIFACT / NDC Fragmentation**: Airlines distribute different seat inventory and private corporate fares across Amadeus 1A, Sabre 1S, and direct NDC channels.
3. **Unified Air Search**: Waypoint OS abstracts the underlying GDS complexity, querying both systems simultaneously and returning unified flight offers with clear fare basis codes and instant ticketing capabilities.

---

## 2. Live Simulation Trajectory & Verification

```text
+----------------------------------------------------------------------------------------------------+
|                                  FIONA GALLAGHER WORKFLOW TRAJECTORY                               |
+----------------------------------------------------------------------------------------------------+
| [Stage 1: Multi-GDS Query]       -> Submitted JFK to LHR query via Amadeus Travel Innovation API   |
| [Stage 2: Offer Normalization]   -> Decoded BA #BA178 ($3,620) with Fare Basis JFFLEX26 (4 left)   |
| [Stage 3: Protocol Validation]   -> Verified dual-stack 1A/1S fallback readiness & NDC compliance  |
| [Stage 4: Instant Issuance Gate] -> Triggered 1-click Instant Issue PNR & 13-digit E-Ticket coupon |
+----------------------------------------------------------------------------------------------------+
```

### Stage 1 & 2: Multi-Host Sandbox Search & Offer Normalization

- **Origin / Destination**: `JFK` (New York) to `LHR` (London Heathrow).
- **GDS Provider**: `Amadeus Travel Innovation Sandbox` (with Sabre Dev Studio standby).
- **Returned Offer**:
  - `Flight`: `British Airways #BA178 (JFK -> LHR)` — Retail Price: **`\$3,620.00`**.
  - `Fare Basis`: **`JFFLEX26`** (Business Flexible, fully refundable, 3 checked bags included).
  - `Inventory`: `4 Seats Left`.
- **Visual Proof**: `Docs/review/assets/fiona_01_dual_gds_sandbox.png`

---

## 3. Verified Artifact Registry

| Stage / Asset Name | Artifact URI | Status | Key Metric / Capability |
| :--- | :--- | :--- | :--- |
| **01 Dual GDS Sandbox** | `Docs/review/assets/fiona_01_dual_gds_sandbox.png` | Verified | Amadeus/Sabre Flight Query (BA178 JFFLEX26 \$3,620) |

---

## 4. Key Architectural Insights & Business Takeaways

1. **Carrier-Agnostic Distribution**: Providing native dual-stack GDS sandboxes allows agency developers and operations leads to test high-volume booking workflows without incurring live GDS look-to-book transaction fees.
2. **Transparent Fare Basis Parsing**: Surfacing fare rules like `JFFLEX26` directly in the UI prevents booking non-refundable tickets for corporate travelers who require flexible change policies.
