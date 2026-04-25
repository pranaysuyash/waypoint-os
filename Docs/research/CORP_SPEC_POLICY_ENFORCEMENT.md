# Corp Spec: Policy Extraction & Enforcement (CORP-001)

**Status**: Research/Draft
**Area**: B2B Compliance & Enterprise Logic

---

## 1. The Problem: "The Policy Breaker"
Corporate travelers often book flights or hotels that violate their company's travel policy (e.g., booking Business Class for a short flight, or staying at a $500/night hotel when the cap is $300). This results in "Expense-Rejection" and friction for the traveler. The agency needs to proactively enforce these rules at the "Search-and-Selection" stage.

## 2. The Solution: 'Policy-Alignment-Protocol' (PAP)

The PAP allows the agent to ingest and enforce complex, multi-variable corporate travel policies.

### Enforcement Actions:

1.  **Policy-Extraction-Reasoning**:
    *   **Action**: Parsing the client's `Travel-Policy-JSON` (or PDF) to extract "Hard-Rules" (e.g., "Max $200 for NYC") and "Soft-Rules" (e.g., "Prefer direct flights").
2.  **In-Line-Compliance-Filtering**:
    *   **Action**: Automatically hiding or "Graying-Out" search results that violate the policy, with a clear explanation: "Violates Policy: Max Flight Cost Exceeded."
3.  **Approval-Workflow-Trigger**:
    *   **Action**: If a traveler insists on a non-compliant booking, the agent MUST autonomously "Request-Approval" from the traveler's manager via a linked Slack/Email integration.

## 3. Data Schema: `Corporate_Policy_Constraint`

```json
{
  "policy_id": "CORP-ACME-8822",
  "client_name": "ACME CORP",
  "rules": [
    {
      "scope": "FLIGHT_CABIN",
      "condition": "DURATION_HOURS < 6",
      "allow_value": "ECONOMY_ONLY",
      "exception_allowed": true
    },
    {
      "scope": "HOTEL_NIGHTLY_RATE",
      "region": "NORTH_AMERICA",
      "max_value": 350,
      "currency": "USD"
    }
  ],
  "approval_delegate": "manager_email@acme.com"
}
```

## 4. Key Logic Rules

- **Rule 1: Hard-Stop-on-Critical-Violation**: The agent is FORBIDDEN from ticketing a booking that violates a "Tier-0" corporate rule (e.g., "Non-Preferred-Carrier" without manager override).
- **Rule 2: Policy-Savings-Report**: The agent must track "Potential-Savings" (the difference between the chosen flight and the cheapest compliant flight) to report back to the corporate client.
- **Rule 3: Contextual-Exception-Inference**: The agent can autonomously "Propose-an-Exception" if it detects a "Systemic-Event" (e.g., all Economy seats are sold out due to a strike), providing the manager with the justification upfront.

## 5. Success Metrics (Compliance)

- **Policy-Compliance-Rate**: % of bookings that were fully compliant with corporate rules.
- **Approval-Turnaround-Time**: Time from "Request-Approval" to "Manager-Decision."
- **Client-Savings-Accrued**: Total dollars saved by enforcing policy-caps.
