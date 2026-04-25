# Evolution Spec: Agent-Led Policy Refinement (EV-002)

**Status**: Research/Draft
**Area**: Feedback Loops & Policy Evolution

---

## 1. The Problem: "The Static Policy Trap"
Operational policies (e.g., "Max $500 for hotel re-booking") are often arbitrary and become outdated. If an agent follows a static policy that consistently leads to traveler dissatisfaction or human overrides, the system is failing to learn.

## 2. The Solution: The 'Feedback-Audit-Update' (FAU) Loop

The FAU loop monitors the **Delta** between AI suggestion and Human action to identify "Policy Friction."

### FAU Mechanism:

1.  **Monitor Override**: Track every instance where a human operator rejects the AI's suggestion in the Workbench.
2.  **Analyze Rationale**: A background agent analyzes the "Human-Action-Delta" (e.g., "Human spent $800 instead of $500 because the $500 hotel was in a high-crime area").
3.  **Propose Refinement**: If a pattern emerges (e.g., 5 overrides for the same reason), the system generates a **Policy Improvement Proposal (PIP)**.
4.  **PIP Approval**: The PIP is presented to the System Owner for 1-click approval.
5.  **Hot-Reload**: Upon approval, the new rule is injected into the `Prompt_Hydration` layer and `Compliance_Engine`.

## 3. Data Schema: `Policy_Proposal`

```json
{
  "proposal_id": "PIP-2026-001",
  "affected_rule": "HOTEL_REBOOK_LIMIT",
  "current_value": 500,
  "proposed_value": 850,
  "trigger_evidence": {
    "num_overrides": 12,
    "total_lost_time_mins": 450,
    "common_rationale": "Safety-Zone Requirements"
  },
  "estimated_roi": "Reduced human intervention by 80% for this exception category."
}
```

## 4. Operational Guardrails

- **Drift-Limit**: The AI cannot propose a change > 50% from the baseline without "Multi-Factor Approval."
- **Regression Testing**: Every proposed policy change is run against the *entire* historical `AuditStore` to ensure it doesn't break previous successful recoveries.
- **Auditable Evolution**: Every policy change is tagged with the `proposal_id` and the evidence that triggered it.

## 5. Success Metrics (Policy)

- **Override Rate**: Decrease in % of AI suggestions that require human modification.
- **Policy Freshness**: Average time from "Discovery of Friction" to "Policy Update" < 24 hours.
- **Operational Velocity**: Increase in "Zero-Touch" recoveries.
