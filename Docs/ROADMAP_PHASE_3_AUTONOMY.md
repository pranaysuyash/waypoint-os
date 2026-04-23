# Roadmap: Phase 3 - Agentic Autonomy & Self-Healing

**Date**: Wednesday, April 22, 2026
**Scope**: Moving from an Auditable Cockpit to an Autonomous/Self-Healing System.

---

## 1. The "Auto-Fix" Service (Self-Healing)
**Objective**: Transition from passive "Integrity Watchdog" alerts to active self-remediation.

- **Current State**: Watchdog detects drift (orphans, staging errors) and logs them to `AuditStore`.
- **Target State**: 
    - Implement `src/agents/recovery_agent.py`.
    - Automated execution: If an "orphan" is detected, the agent checks if a simple "Repair" (Move to Intake) is viable.
    - **Guardrails**: The agent must log its repair actions back to the `AuditStore`, allowing operators to review "AI-repaired" vs "Human-repaired" actions in the `TimelinePanel`.

## 2. The "Self-Tuning" Feedback Loop (AI Coaching)
**Objective**: Automate the prompt engineering cycle using our "Systemic Error" logs.

- **Current State**: Systemic errors (e.g., "Constraint Ignored") are captured via `ReviewControls.tsx`.
- **Target State**:
    - Build a "Tuning Agent" that periodically analyzes the `DashboardAggregator` report for "Top 3 Systemic Errors."
    - Output: An automated PR or "Proposed Prompt Change" that updates the `SystemInstructions` to specifically address the highest-frequency error category.
- **Benefit**: Continuous agent improvement without manual intervention.

## 3. Compliance Enforcement (Governance-as-Code)
**Objective**: Move from flagging risks to blocking invalid outcomes.

- **Current State**: `SuitabilitySignals` surface warnings to operators.
- **Target State**:
    - Hard-block triggers: If a `SuitabilitySignal` of severity `critical` is detected, the `Spine` pipeline MUST NOT reach the `OutputDelivery` stage without a manager-level override.
    - **UI Impact**: Introduce "Compliance Guardrails" in the `StrategyTab` that forces the operator to acknowledge suitability risks before the trip can be quoted.

---

## Strategic Implementation Guidelines
1. **Never Automate Untracked Actions**: Any "self-healing" action taken by an agent MUST be logged as a `system_event` in the `AuditStore`.
2. **Policy-Driven Autonomy**: All auto-fixes must adhere to the `AgencyAutonomyPolicy` gates (e.g., if a fix is "Dangerous," it MUST remain human-gated).
3. **Observability First**: Before turning on "Auto-Fix," we must verify the "Watchdog" logs for 7 days to ensure the AI's logic is perfectly understood.

*Note: This roadmap is the next evolution of our existing traceability infrastructure. We are leveraging the "Cockpit" visibility to give the agents the "Hands" required to fix the system.*
