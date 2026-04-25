# Ethical Spec: Moral-Utility-Weighting (ETHIC-001)

**Status**: Research/Draft
**Area**: Agentic Ethics & Moral Decision-Making

---

## 1. The Problem: "The One-Seat Dilemma"
In a crisis, resources are finite. If two agents (both using this system) are fighting for the last seat on a flight, and both travelers have high-priority needs, how does the "Spine" resolve the conflict without descending into a "Budget War"?

## 2. The Solution: 'Ethical-Decision-Matrix' (EDM)

The EDM provides a "Moral Framework" for resolving zero-sum conflicts based on "Weighted-Necessity" rather than just "Wealth."

### Priority Tiers:

1.  **Tier 1: Life & Safety (Absolute)**:
    *   **Examples**: Medical emergencies, Organ transport, Escaping active conflict zones.
    *   **Action**: Auto-Preempt all other tiers.
2.  **Tier 2: Critical Life-Events (High)**:
    *   **Examples**: Funerals, Weddings, Childbirth.
    *   **Action**: Preempt professional/business tiers.
3.  **Tier 3: Systemic Professional (Medium)**:
    *   **Examples**: Surgeons, Utility-Repair Crews, Peace-Negotiators.
    *   **Action**: Preempt standard business/leisure.
4.  **Tier 4: Standard/Leisure (Baseline)**:
    *   **Examples**: Vacations, Routine meetings.
    *   **Action**: Default state.

## 3. Data Schema: `Moral_Conflict_Resolution`

```json
{
  "conflict_id": "MORAL-9911",
  "resource": "SEAT_LH400_10MAY",
  "parties": [
    {
      "agent_id": "AGENT_A",
      "traveler_priority_score": 0.95,
      "justification": "SURGEON_FOR_SCHEDULED_OPERATION"
    },
    {
      "agent_id": "AGENT_B",
      "traveler_priority_score": 0.88,
      "justification": "PARENT_FOR_CHILDBIRTH_EVENT"
    }
  ],
  "verdict": "ALLOCATE_TO_AGENT_A",
  "ethical_rationale": "Medical life-saving professional utility outweighs time-sensitive personal life-event.",
  "compensation_offer_to_party_b": {
    "type": "PRIVATE_CHARTER_VOUCHER",
    "value": 5000
  }
}
```

## 4. Key Logic Rules

- **Rule 1: Transparency-of-Sacrifice**: If Agent B is asked to relinquish their seat for Agent A, the system MUST provide a "Reasoning Trace" (while anonymizing Agent A) and offer "Immediate-Compensation-Bounties" (funded by a global agency contingency pool).
- **Rule 2: No-Bribery**: A Tier 4 traveler cannot "Outbid" a Tier 1 traveler. The Ethical Matrix overrides the Financial Wallet (FIN-002) in high-urgency states.
- **Rule 3: Verification-of-Justification**: Justifications (e.g., "Medical Emergency") must be backed by "Signed Evidence" in the `Evidence Vault` (e.g., a hospital admission letter or professional ID) to prevent "Priority-Spoofing."

## 5. Success Metrics (Ethics)

- **Utility Alignment**: % of high-priority life/safety events successfully reached during disruptions.
- **Fairness Score**: Subjective traveler rating of the "Fairness" of the agent's conflict resolution logic.
- **Legal Defensibility**: % of ethical choices that were upheld during post-incident legal review.
