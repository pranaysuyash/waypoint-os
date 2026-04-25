# Meta Spec: Logic-Autopsy & Patching (META-001)

**Status**: Research/Draft
**Area**: Autonomous Self-Improvement & Meta-Learning

---

## 1. The Problem: "The Static Failure"
If an agent makes a sub-optimal decision during a disruption (e.g., choosing a route that was technically valid but logically frustrating for the traveler), and that logic remains unchanged, the agent will repeat the mistake. Most systems require manual "Developer-Intervention" to fix logic bugs.

## 2. The Solution: 'Logic-Autopsy' (LA)

The LA protocol allows the agent to "Backpropagate" its failures and successes into a "Logic-Refinement" loop.

### Autopsy Stages:

1.  **Divergence Detection**:
    *   **Action**: Identifying when a traveler "Rejected" an agent's recommendation or when an outcome was "Inefficient" compared to a theoretical optimum.
2.  **Root-Cause-Inference**:
    *   **Action**: The agent re-reads its own `AuditStore` and `Reasoning Trace` to find the specific "Rule" or "Weighting" that caused the divergence.
3.  **Autonomous Patch Proposal**:
    *   **Action**: The agent drafts a new `OPERATIONAL_LOGIC_SPEC` or modifies an existing one to prevent the failure in the future.

## 3. Data Schema: `Logic_Patch_Proposal`

```json
{
  "patch_id": "PATCH-2026-005",
  "incident_reference": "INC-8877 (LHR Hub Collapse)",
  "failed_logic_node": "REBOOK_STRATEGY_NODE_04",
  "identified_issue": "Agent prioritized 'Fastest-Arrival' over 'Direct-Rest', causing traveler exhaustion.",
  "proposed_change": {
    "parameter": "FATIGUE_WEIGHT",
    "old_value": 0.25,
    "new_value": 0.65
  },
  "simulation_evidence": "Re-running INC-8877 with new_value results in 22% higher traveler satisfaction score.",
  "hitl_approval_required": true
}
```

## 4. Key Logic Rules

- **Rule 1: No-Shadow-Updates**: The agent CANNOT update its "Core Logic" (the .py/ts code) without a human-in-the-loop "Merge Approval." It can only propose patches.
- **Rule 2: Counter-Factual Validation**: Every patch must be "Proven" by running it against at least 50 historical scenarios from the `Scenario Corpus` to ensure it doesn't cause regressions.
- **Rule 3: Reasoning-Integrity**: Patches cannot violate "Hard-Guardrails" (e.g., Safety, Legality, Financial Caps).

## 5. Success Metrics (Learning)

- **Learning Rate**: Average time from "Incident" to "Logic-Patch-Submission."
- **Regression Rate**: % of autonomous patches that caused a failure in a different scenario (Target: < 1%).
- **Developer-Efficiency**: Reduction in manual hours spent "Tuning" agent behavior.
