# Prompt Spec: GDS-Grounded-Prompting (PRM-001)

**Status**: Research/Draft
**Area**: Prompt Engineering & Hallucination Mitigation

---

## 1. The Problem: "The Creative Hallucination"
LLMs are trained to be helpful, often leading them to "invent" flight numbers, times, or prices when they lose context or when the search tool returns a partial failure. In travel, a hallucinated flight is a catastrophic failure that destroys user trust.

## 2. The Solution: 'Source-Attribution-Protocol' (SAP)

The SAP enforces a strict "No-Source, No-Statement" policy.

### Prompt Components:

1.  **System-Anchor-Instruction**:
    *   "You are an agentic travel operator. Your primary constraint is **Fidelity**. You are prohibited from mentioning any flight, hotel, or price that was not returned in a JSON response from your tools within the last 300 seconds."
2.  **Citation-Requirement**:
    *   "Every recommendation MUST include a `source_id` and a `timestamp`. If you are suggesting a flight, the format must be: `Flight [X] ($[Y]) [Source: GDS_AMADEUS_772] [Verified: 2s ago]`."
3.  **Ambiguity-Handling-Prompt**:
    *   "If a tool returns an empty list, DO NOT suggest 'typical' flights. Instead, state: 'My real-time search of [PROVIDER] returned no direct results for [DATE]. I am now searching for 1-stop alternatives.'"
4.  **Verification-Challenge**:
    *   "Before outputting a final list, perform a 'Mental-Checksum': Match the `price` in your output to the `price` in the last raw tool response. If they do not match exactly, you have failed."

## 3. Data Schema: `Grounded_Prompt_Audit`

```json
{
  "audit_id": "SAP-88112",
  "llm_output": "Flight LH401 ($850) [Source: NDC_LH_1]",
  "tool_state": {
    "last_json_price": 850.00,
    "last_json_flight": "LH401",
    "stale_check": "PASS (4s)"
  },
  "grounding_score": 1.0,
  "hallucination_detected": false
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Zero-Invention' Rule**: If the agent "guesses" a price based on "historical knowledge," the supervisor agent MUST trigger an immediate shutdown of the session.
- **Rule 2: The 'Stale-Data' Guardrail**: If the tool data is >300 seconds old, the agent MUST re-poll before presenting it as "Live-Pricing."
- **Rule 3: Transparency-of-Failure**: If the GDS API is down, the agent must say "My connection to the Global Distribution System is currently interrupted" rather than trying to provide "estimated" advice.

## 5. Success Metrics (Prompting)

- **Hallucination-Incidents**: Number of non-grounded statements detected per 1000 interactions (target: 0).
- **Citation-Density**: % of factual claims supported by a tool-output reference.
- **Data-Freshness-Delta**: Average age of the data presented to the user.
