# Flow Spec: Reasoning-Loop-Architecture (FLW-001)

**Status**: Research/Draft
**Area**: Agentic Reasoning & Reliability

---

## 1. The Problem: "The Blind Booking"
Generic LLM agents often "Hallucinate-and-Commit." They might find a flight that technically exists but ignores complex operational constraints (e.g., a 45-minute international connection in LHR, which is physically impossible). If the agent doesn't have a built-in "Self-Correction-Loop," it will present a "Broken-Itinerary" as a success.

## 2. The Solution: 'Think-Act-Verify' (TAV) Loop

The TAV protocol forces the agent to audit its own proposals before externalizing them.

### Loop Stages:

1.  **Stage 1: Intent-Decomposition (Think)**:
    *   **Action**: Breaking a user request ("Find me a flight to Tokyo tomorrow") into specific constraints: Date, Price-Cap, Minimum-Connection-Time (MCT), Passport-Validity, and Visa-Requirement.
2.  **Stage 2: GDS-Interrogation (Act)**:
    *   **Action**: Executing the search via API/GDS tools.
3.  **Stage 3: Operational-Audit (Verify)**:
    *   **Internal Monologue**: "I found Flight A. It has a 55-minute connection. My 'Safety-Threshold' for this airport is 90 minutes. This proposal is INVALID. Searching for alternatives with >90m connections."
4.  **Stage 4: Proposal-Finalization**:
    *   **Action**: Presenting the *verified* solution to the user with the audit trail: "I found a cheaper flight via LHR, but I discarded it because the connection was only 55 minutes. This 2-hour connection is safer."

## 3. Data Schema: `Agentic_Reasoning_Step`

```json
{
  "step_id": "TAV-99221",
  "agent_id": "ORCHESTRATOR_01",
  "current_hypothesis": "Route_A_via_FRA",
  "audit_results": [
    {"constraint": "MCT", "passed": false, "reason": "55m < 90m_THRESHOLD"},
    {"constraint": "PRICE", "passed": true}
  ],
  "decision": "DISCARD_AND_RETRY",
  "next_action": "SEARCH_LONGER_LAYOVER",
  "trace_log": "Self-corrected route A due to connection risk."
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Backtrack-First' Rule**: The agent MUST NOT present any recommendation that fails a single "Hard-Operational-Constraint" (e.g., MCT or Passport-Expiry).
- **Rule 2: Trace-Visibility**: The "Internal-Monologue" of the self-correction MUST be available for debugging but condensed for the user.
- **Rule 3: Confidence-Thresholding**: If the agent cannot find a 100% compliant route, it MUST NOT fake one. It must return a "Constraint-Violation-Report" to the user asking for a preference trade-off.

## 5. Success Metrics (Agentic)

- **Self-Correction-Rate**: % of internal proposals that were discarded by the agent before being shown to the user.
- **Human-Overrule-Ratio**: How often a user has to correct a flight choice (target: <2%).
- **Reasoning-Depth**: Number of "Verify" cycles per complex multi-hop itinerary.
