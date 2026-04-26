# Corp Spec: Multi-Tenant Agency-Governance-Protocol (CORP-REAL-016)

**Status**: Research/Draft
**Area**: SaaS Multi-Tenancy & Governance

---

## 1. The Problem: "The One-Size-Fits-All Agent"
In a multi-tenant SaaS environment, different travel agencies have vastly different business models, risk appetites, and operational workflows. A generic agent logic that re-books flights autonomously might be a "Feature" for a high-volume budget agency but a "Liability" for a high-touch boutique luxury agency that prefers human-curated alternatives. Without "Agency-Sovereignty," the platform cannot scale across diverse agency profiles.

## 2. The Solution: 'SaaS-Sovereignty-Protocol' (SSP)

The SSP allows each agency to define the "Operating-Parameters" of the AI.

### Governance Actions:

1.  **Autonomy-Tier Assignment**:
    *   **Action**: Defining the agency's "Autonomy-Level" (e.g., Tier 1: Advisor-Only, Tier 2: Semi-Autonomous with Approval, Tier 3: Fully-Autonomous within Spend-Limits).
2.  **Spend-Threshold Authorization**:
    *   **Action**: Configuring the maximum "Autonomous-Spend" (e.g., "$200 per traveler per incident"). Any amount exceeding this threshold triggers a "Human-Approval-Request."
3.  **Brand-Voice Customization**:
    *   **Action**: Each agency can inject its own "Personality-Profile" (e.g., "Formal-Corporate," "Adventurous-Wanderer," "Concierge-Luxury") to ensure the agent's communication aligns with the agency's brand.
4.  **Vendor-Priority Logic**:
    *   **Action**: Agencies can define "Preferred-Vendors" or "Blacklisted-Carriers" based on their specific commercial agreements or past performance history.

## 3. Data Schema: `Agency_Governance_Config`

```json
{
  "agency_id": "AGENCY_ALPHA_99",
  "autonomy_tier": "SEMI_AUTONOMOUS",
  "max_autonomous_spend_usd": 500,
  "human_approval_required_for": ["HOTEL_UPGRADES", "REFUND_REJECTIONS"],
  "brand_voice": "CONCIERGE_LUXURY",
  "preferred_airlines": ["EK", "QR", "SQ"],
  "status": "CONFIG_ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Policy-Supremacy' Rule**: Agency-level governance configurations MUST override global agent defaults. The agent cannot act outside the bounds defined by the specific tenant.
- **Rule 2: Audit-Log Fidelity**: Every autonomous action MUST be tagged with the specific "Governance-Token" that authorized it, providing a clear "Accountability-Trail" for the agency owner.
- **Rule 3: The 'Safety-Brake'**: If the agent detects "High-Ambiguity" in a situation (e.g., conflicting traveler preferences and agency policy), it MUST default to Tier 1 (Advisor-Only) and request human intervention.

## 5. Success Metrics (Governance)

- **Tenant-Satisfaction-Score**: Agency owner satisfaction with the level of control over the AI.
- **Autonomous-Success-Rate**: % of agentic actions that remained within agency-defined spend and policy bounds.
- **Governance-Latency**: Time taken to update and propagate new agency policies across the agent cluster.
