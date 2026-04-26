# Corp Spec: Multi-Tenant Agency-Policy-Engine (CORP-SPEC-002)

**Status**: Research/Draft
**Area**: Agency Governance & B2B Operations

---

## 1. The Problem: "The One-Size-Fits-All Agent"
A global travel agent platform serves many different types of agencies. A "Luxury-Boutique" agency has completely different operational priorities (High-Touch, High-Commission) compared to a "Corporate-Efficiency" agency (Cost-Savings, Policy-Compliance). If the AI agent uses the same global logic for all, it will fail to meet the specific business goals of individual agency owners.

## 2. The Solution: 'House-Rule-Injection-Protocol' (HRIP)

The HRIP allows the agent to act as a "Business-Aligned-Proxy" for each agency tenant.

### Governance Actions:

1.  **Agency-Bias-Injection**:
    *   **Action**: Each agency defines a set of "Business-Tokens" (e.g., `PRIORITIZE_LUXURY_COLLECTION`, `BLOCK_NON_NDC_CONTENT`, `FAVOR_SUSTAINABLE_CERTIFIED`). These are injected into the LLM system prompt for all trips managed by that agency.
2.  **Spending-Autonomy-Caps**:
    *   **Action**: Defining the "Transactional-Safety-Threshold" (INT-001) at the agency level. (e.g., "This agency allows the AI to spend up to $100 on service recovery without human approval; everything above needs a human ping").
3.  **Preferred-Vendor-Steering**:
    *   **Action**: Allowing the agency to upload a "Partner-Whitelist" (e.g., specific hotel groups or car rental firms with whom they have negotiated rates). The agent autonomously biases results toward these partners.
4.  **Agency-Tone-Voice-Mapping**:
    *   **Action**: Defining the "Communication-Persona" for the agency. (e.g., "Professional & Direct" for corporate vs "Warm & Enthusiastic" for leisure).

## 3. Data Schema: `Agency_Policy_Profile`

```json
{
  "agency_id": "TENANT-44112",
  "plan_tier": "ENTERPRISE_PLUS",
  "operational_biases": {
    "sustainability_weight": 0.8,
    "commission_optimization": "AGGRESSIVE",
    "vendor_steering": ["MARRIOTT_BONVOY", "HERTZ_GOLD"]
  },
  "autonomy_config": {
    "max_autonomous_spend": 250.00,
    "human_handoff_threshold": "MEDIUM_STAKES"
  },
  "support_mode": "HYBRID_AUGMENTATION",
  "status": "ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: Policy-Supersession**: Agency-level policies ALWAYS supersede global default policies. Traveler-level preferences (TWO) are balanced against agency policies using a "Negotiation-Weight" (e.g., if a traveler wants a cheap flight but the agency policy is 'NDC-Only', the agent must explain the constraint).
- **Rule 2: Compliance-Audit-Trail**: Every decision made by the agent MUST be mapped back to a specific Agency-Policy-Token to ensure accountability for the agency owner.
- **Rule 3: Tiered-Access-Control**: Agency owners can see aggregated performance metrics, but they cannot access individual traveler "Bio-Vault" data unless explicitly authorized for a specific manual intervention.

## 5. Success Metrics (Governance)

- **Policy-Adherence-Rate**: % of AI recommendations that align with the agency's preferred vendor list and spend caps.
- **Agency-Customization-Depth**: Number of unique "House-Rules" defined per tenant.
- **Business-Objective-Alignment**: Actual commission or cost-saving targets met vs predicted.
