# Prompt Spec: Operational Few-Shot Injection (PR-001)

**Status**: Research/Draft
**Area**: Dynamic Context & Prompt Engineering

---

## 1. The Problem: "Context Blindness"
Standard "Static" system prompts are too generic for high-stakes exceptions. An agent handling a "LCC Bankruptcy" needs different few-shot examples than an agent handling a "MedEvac Logistic."

## 2. The Solution: 'Context-Hydration' Pattern

The system should dynamically construct the prompt based on the **Detected Intent** and **Current Failure Category**.

### Components of the 'Hydrated' Prompt:

1.  **Static Foundation**: The core personality and safety rules of the agency.
2.  **Dynamic Intent Block**: Pulled from the `Scenario_Library` based on the current situation (e.g., Injecting `OPERATIONAL_LOGIC_SPEC_BANKRUPTCY.md` snippets).
3.  **Few-Shot 'Closest-Fit' Examples**: 3-5 historic successful recoveries that most closely match the current telemetry.
4.  **Live Constraints**: Direct injection of real-time limitations (e.g., "Airport XYZ is closed for the next 4 hours").

### Prompt Construction Flow:

1.  **Event Detect**: `Watchdog` detects a "Flight Cancellation."
2.  **Vector Search**: Search the `Scenario_Library` for "Flight Cancellation + High-Value-Client."
3.  **Hydrate**: Assemble the prompt components into a single payload.
4.  **Execute**: Send the hydrated prompt to the L2/L3 Reasoning Model.

## 3. The 'Operational-Guardrail' Template

Every system prompt should include this mandatory footer:

```markdown
### OPERATIONAL_GUARDRAILS (MANDATORY)
1. NEVER assume availability without a tool call.
2. If the 'Risk_Budget' is exceeded, you MUST escalate.
3. Every suggestion must include an 'Integrity_Hash' from the AuditStore.
4. Prioritize Traveler SAFETY > Cost > Schedule.
```

## 4. Prompt Template Example (Pseudo-Markdown)

```markdown
{{ foundation_rules }}

### CURRENT SITUATION: {{ situation_summary }}
{{ relevant_scenario_logic }}

### LESSONS FROM RELEVANT CASES:
{{ few_shot_examples }}

### CURRENT CONSTRAINTS:
{{ live_ground_truth_constraints }}

{{ agent_instructions }}
```

## 5. Success Metrics (Prompting)

- **Scenario Recall**: 100% of relevant "Batch 05" logic is injected when the matching scenario occurs.
- **Instruction Adherence**: % of agent responses that correctly apply the dynamically injected constraints.
- **Hallucination Delta**: Reduction in hallucinations compared to static-prompt baseline.
