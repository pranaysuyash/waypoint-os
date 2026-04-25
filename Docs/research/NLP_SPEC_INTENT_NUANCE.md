# NLP Spec: Intent Nuance Extraction (NLP-REAL-001)

**Status**: Research/Draft
**Area**: LLM Reasoning & Intent Extraction

---

## 1. The Problem: "The Contradictory Request"
Travelers often provide incomplete or contradictory instructions. Example: "I want the most luxurious hotel in Paris but my budget is $150/night." Or they leave out "Implicit-Constraints" (e.g., "I need a flight to NYC"—forgetting they have a 9 AM meeting in Brooklyn). A "Dumb" agent books the $150 hotel (which is a hostel) or a flight that arrives too late.

## 2. The Solution: 'Nuance-Detection-Protocol' (NDP)

The NDP uses "Reasoning-Chains" to identify "Intent-Gaps" before searching.

### Extraction Actions:

1.  **Constraint-Conflict-Detection**:
    *   **Action**: Running a "Feasibility-Check" on the initial request. If `Luxury` + `$150` = `Impossible`, the agent flags a "Constraint-Conflict."
2.  **Context-Back-Filling**:
    *   **Action**: Querying the traveler's "Linked-Calendar" and "Historical-Preferences" to find "Hidden-Meeting-Constraints" or "Preferred-Neighborhoods."
3.  **Clarification-Generation**:
    *   **Action**: Instead of just erroring, the agent proposes "Trade-Offs": "I found hotels at $150, but they aren't luxury. I found luxury hotels at $600. Or I can find a 'Boutique' hotel at $250. Which dimension should we prioritize?"

## 3. Data Schema: `Intent_Extraction_Result`

```json
{
  "request_id": "NDP-88221",
  "raw_input": "Luxury hotel Paris, $150 budget",
  "extracted_entities": {
    "location": "Paris",
    "tier": "Luxury",
    "budget_cap": 150
  },
  "confidence_scores": {
    "intent": 0.98,
    "feasibility": 0.12
  },
  "detected_conflicts": [
    {
      "type": "BUDGET_VS_TIER",
      "severity": "CRITICAL"
    }
  ],
  "proposed_trade_offs": ["INCREASE_BUDGET", "DECREASE_TIER", "SHIFT_LOCATION"]
}
```

## 4. Key Logic Rules

- **Rule 1: Never-Assume-Ambiguity**: If a request is ambiguous (e.g., "Paris" - which one? France or Texas?), the agent MUST NOT book the most likely one without a 1-click confirmation.
- **Rule 2: The 'Why' Extraction**: The agent should attempt to extract the "Purpose-of-Trip" (e.g., Business, Anniversary, Crisis) to weight constraints. (Anniversary = Tier > Budget; Crisis = Speed > Tier).
- **Rule 3: Sentiment-Aware-Throttling**: If the traveler sounds "Stressed" or "Angry" in their voice note (AFFECT-001), the agent MUST prioritize "Speed-and-Simplicity" over "Infinite-Options."

## 5. Success Metrics (NLP)

- **Clarification-Rate**: % of requests that required a follow-up question (Lower = better extraction, but higher risk of assumption).
- **Traveler-Correction-Rate**: % of bookings where the traveler said "No, that's not what I meant."
- **Constraint-Capture-Efficiency**: Number of "Hidden-Constraints" successfully identified before traveler input.
