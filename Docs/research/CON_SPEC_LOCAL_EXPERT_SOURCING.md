# Con Spec: Local-Expert-On-Demand (CON-REAL-001)

**Status**: Research/Draft
**Area**: Concierge Services & Local Intelligence

---

## 1. The Problem: "The Generic Tour Trap"
Most travelers end up on generic, mass-market tours because they don't have access to "High-Fidelity" local experts. In complex or high-stakes regions (e.g., Lagos, Mumbai, Mexico City), a generic tour guide is insufficient. Travelers need "Fixers" who can navigate local bureaucracy, provide security, or offer deep-vertical expertise (e.g., "Industrial-Supply-Chain-Expert" in Shenzhen).

## 2. The Solution: 'Hyper-Local-Expertise-Protocol' (HLEP)

The HLEP allows the agent to act as a "Global-Vetting-Bureau" for local human intelligence.

### Sourcing Actions:

1.  **Vertical-Expert-Matching**:
    *   **Action**: Identifying the *specific* expertise required (e.g., "Need a fixer who speaks Yoruba and understands the local tech ecosystem") and querying specialized local marketplaces (e.g., vetted Telegram groups, local industry associations).
2.  **Reputation-Proof-Audit**:
    *   **Action**: Going beyond public reviews. The agent MUST autonomously verify the expert's "Proof-of-Work" (e.g., social proof, local business registration, or a "Vetting-Ping" to the agent's internal trusted network).
3.  **Encrypted-Briefing-Handoff**:
    *   **Action**: Providing the local expert with a structured, encrypted brief of the traveler's needs without exposing sensitive PII (Identity Vault ID-REAL-001).
4.  **Real-Time-Check-In-Loop**:
    *   **Action**: During the engagement, the agent performs "Active-Pulse" checks with the traveler to ensure the expert's performance matches the brief.

## 3. Data Schema: `Local_Expert_Engagement`

```json
{
  "engagement_id": "HLEP-88221",
  "traveler_id": "GUID_9911",
  "expert_id": "EXPERT-LAGOS-01",
  "expertise_vertical": "SECURITY_LOGISTICS",
  "languages": ["ENGLISH", "YORUBA"],
  "engagement_window": "2026-11-12T09:00:00Z - 18:00:00Z",
  "vetting_score": 98.2,
  "briefing_status": "SENT_ENCRYPTED",
  "contract_verdict": "FIXED_FEE_USD_250"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Vetting-Depth' Rule**: For "High-Risk" regions, the agent MUST NOT book an expert who does not have at least 3 "Verified-Fulfillment-Events" in the agency's private network (Vendor-Reliability-Index OPS-REAL-004).
- **Rule 2: The 'No-Kickback' Guarantee**: The agent MUST autonomously verify that the expert's pricing is "Net-Rate" and does not include hidden kickbacks from vendors (e.g., shops the guide takes you to).
- **Rule 3: Emergency-Escalation-Bridge**: The local expert MUST have a direct, high-priority communication channel to the agent's "Crisis-Routing" system (OPS-REAL-003).

## 5. Success Metrics (Expertise)

- **Expertise-Match-Score**: Traveler rating of the expert's vertical knowledge vs the brief.
- **Incident-Free-Engagements**: % of expert-led days without security or logistics failures.
- **Local-Intelligence-Yield**: $ value of "Local-Insights" or "Efficiency-Gains" reported by the traveler.
