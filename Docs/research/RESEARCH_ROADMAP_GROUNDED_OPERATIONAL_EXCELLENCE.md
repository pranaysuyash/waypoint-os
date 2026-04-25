# Research Roadmap: Grounded Operational Excellence (2026-04-25)

**Status**: Discovery phase
**Goal**: Transition from "Speculative Frontier" to "Real-World Industrial Hardening."

---

## 1. Track: GDS Connectivity & Protocol Translation (GDS-001)
The 'Plumbing' of Travel.

- **Concept**: Hardening the agent's ability to communicate with legacy Global Distribution Systems (Sabre, Amadeus) and modern NDC (New Distribution Capability) APIs.
- **Exploration Areas**:
    - **Schema-Bridge-Dynamics**: Handling the mismatch between NDC JSON structures and legacy EDIFACT XML.
    - **Session-Persistence-Logic**: Maintaining stateful GDS sessions during high-latency network conditions.
    - **Inventory-Staleness-Threshold**: Quantifying the decay-rate of cached seat-availability vs. API cost.

## 2. Track: Financial Settlement & Fraud Integrity (FIN-REAL-001)
The 'Money' Loop.

- **Concept**: Defending the agency's bottom line against industry-standard financial risks.
- **Exploration Areas**:
    - **Chargeback-Defense-Automation**: Autonomously generating evidence packets (logs, screenshots, traveler-approvals) to fight 'Friendly-Fraud.'
    - **Split-Payment-Reconciliation**: Managing the complex flow of funds between the traveler, the agency, and multiple sub-vendors (Hotels, Airlines, Cars).
    - **Merchant-Category-Code (MCC) Optimization**: Ensuring transactions are routed through the correct gateways to minimize processing fees.

## 3. Track: Regulatory Automation & Passenger Rights (REG-REAL-001)
The 'Legal' Shield.

- **Concept**: Automating the enforcement of passenger rights and agency compliance.
- **Exploration Areas**:
    - **EC 261/2004 Claim-Bot**: Autonomously detecting flight delays/cancellations and filing compensation claims for the traveler.
    - **GDPR-compliant Traveler-Purge**: Automating the 'Right-to-be-Forgotten' while preserving necessary financial-audit trails.
    - **Insurance-Trigger-Detection**: Monitoring real-world events (weather, strikes) to proactively trigger travel-insurance claims.

## 4. Track: Multi-Modal Intent Extraction (NLP-REAL-001)
The 'Intelligence' Core.

- **Concept**: Refining the extraction of 'Hard-and-Soft' constraints from unstructured communication.
- **Exploration Areas**:
    - **Voice-Note-Parsing**: Extracting nuanced preferences from 60-second WhatsApp voice notes with background noise.
    - **Hidden-Constraint-Inference**: Identifying contradictions in traveler requests (e.g., "I want the cheapest flight but I hate layovers").
    - **Multi-Lingual-Support**: Handling travel jargon across different languages and cultures.

## 5. Track: Operational Latency & Edge Case Triage (OPS-REAL-001)
The 'Speed' Factor.

- **Concept**: Optimizing the agent's response time during high-load periods.
- **Exploration Areas**:
    - **Degraded-Connectivity-UI**: Researching the 'Minimal-Viable-UI' for travelers in low-bandwidth zones.
    - **Human-Handoff-Triggers**: Defining the exact 'Complexity-Threshold' where an agent must escalate to a human operator.
    - **Real-Time-Event-Correlation**: Connecting global news (e.g., a strike in Italy) to specific active itineraries.

---

## Next Steps:
1.  Draft logic specs for **GDS Connectivity**.
2.  Draft protocol specs for **Chargeback-Defense-Automation**.
3.  Draft audit specs for **EC 261/2004 Compliance**.
