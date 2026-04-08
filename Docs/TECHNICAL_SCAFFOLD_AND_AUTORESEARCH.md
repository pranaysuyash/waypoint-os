# Technical Scaffold and Autoresearch Optimization

## 1. The Two-Loop Architecture
The system separates the **Live Production Path** (stability) from the **Offline Improvement Path** (evolution).

### A. The Production Path (The Compiler Pipeline)
Every user turn follows this deterministic sequence:
1. **Source Adaptation**: Raw input (text, URL, PDF) $\rightarrow$ Common Ingestion Envelope.
2. **Canonical Normalization**: Ingestion Envelope $\rightarrow$ Canonical State Packet.
3. **Validation**: Check against MVB (Minimum Viable Brief) for blockers and contradictions.
4. **Inference**: Generate derived signals and soft hypotheses (separated from facts).
5. **Decision Policy**: Determine if the system should `Proceed`, `Ask`, `Branch`, or `Escalate`.
6. **Session Strategy**: Generate the goals and question priority for the turn.
7. **Modular Prompting**: Compose the final prompt from a registry of blocks.
8. **Execution & Verification**: Generate response and run the Verifier pass.
9. **Memory/Log Update**: Update the state and log telemetry for the offline loop.


---

## 2. The Offline Loop (The Autoresearch Path)
Inspired by Karpathy's autoresearch, the system optimizes itself based on measurable evidence.

### A. The Eval Harness
A fixed dataset of 200-500 "Gold Labeled" cases.
- **Case**: {Input Context, User Message}.
- **Gold Label**: {Correct Domain, Correct Tool, Correct Escalation, Quality Score}.

### B. The Mutation Loop
The system autonomously experiments with its own configuration:
1. **Target Selection**: Pick one dimension to mutate (e.g., the Router Prompt or a specific Few-Shot example).
2. **Mutation**: Propose a constrained change.
3. **Execution**: Run the entire Eval Harness with the new config.
4. **Scoring**: Calculate a `Composite Score`:
   - $\text{Score} = (0.3 \times \text{Routing Acc}) + (0.2 \times \text{Tool F1}) + (0.2 \times \text{Escalation Acc}) + (0.2 \times \text{Quality}) - \text{Latency Penalty}$.
5. **Persistence**: If the score improves, commit the change. Otherwise, revert.

---

## 3. Prompt Registry Model
To ensure stability and versioning, the system uses a modular registry.

**Registry Structure:**
```json
{
  "profiles": {
    "billing_agent_v2": {
      "system_base": "base_support_v3",
      "domain_block": "billing_block_v2",
      "policy_block": "refund_policy_v1",
      "tool_block": "billing_api_v1",
      "fewshot_set": "billing_dispute_v3"
    }
  }
}
```

---

## 4. The Normalized Context Packet
To prevent "Context Bloat," data is normalized before hitting the LLM.

**Schema:**
- `agency_context`: Service line, plan tier, brand voice, business rules.
- `customer_context`: Account age, risk level, language.
- `conversation_state`: Summary, open tasks, last active agent.
- `latest_user_message`: The current turn.
- `tool_state`: Available APIs and current session flags.

---

## 5. Implementation Roadmap (Technical Phasing)
- **Phase 1 (Skeleton)**: Fixed taxonomy $\rightarrow$ Router $\rightarrow$ Registry $\rightarrow$ Generalist $\rightarrow$ Verifier $\rightarrow$ Logs.
- **Phase 2 (Eval)**: Build the 200-case gold dataset and the scoring harness.
- **Phase 3 (Optimization)**: Enable the Autoresearch loop for Router and Prompt Packs.
- **Phase 4 (Specialization)**: Split agents only when error clusters in the logs justify a new specialist.
