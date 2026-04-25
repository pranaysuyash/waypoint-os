# Model Spec: Model-Routing-Architecture (MOD-001)

**Status**: Research/Draft
**Area**: LLM Orchestration & Cost Optimization

---

## 1. The Problem: "The Over-Powered Request"
Using a flagship "Reasoning" model (e.g., Gemini 1.5 Pro or GPT-4o) for a simple task like "Notify the user that their flight landed" is a waste of both latency and budget. Conversely, using a "Lightweight" model (e.g., Gemini 1.5 Flash) for a 10-city multi-hop itinerary optimization leads to logical errors.

## 2. The Solution: 'Task-Based-Inference-Protocol' (TBIP)

The TBIP implements a "Smart-Router" between the user/agent and the LLM providers.

### Routing Logic:

1.  **Task-Classification-Layer**:
    *   **Action**: Analyzing the complexity of the prompt.
    *   **Class A (Routine)**: Status updates, simple Q&A, formatting, intent extraction.
    *   **Class B (Strategic)**: Itinerary construction, constraint-satisfaction, vendor-comparison.
    *   **Class C (Negotiation/Emergency)**: Crisis re-booking, dual-passport routing, legal-liability auditing.
2.  **Model-Mapping**:
    *   **Class A -> Lightweight**: Fast, cheap, high-throughput (e.g., Gemini 1.5 Flash).
    *   **Class B -> Mid-Range**: Balanced reasoning and speed (e.g., GPT-4o-mini or Claude 3.5 Haiku).
    *   **Class C -> Flagship Reasoning**: Deep logic, large context window (e.g., Gemini 1.5 Pro or Claude 3.5 Sonnet).
3.  **Latency-Failover**:
    *   **Action**: If the Flagship model has a latency spike (>10s), the router autonomously drops to a Mid-Range model for a "Partial-Draft" to keep the UI responsive.
4.  **Cost-Audit-Watchdog**:
    *   **Action**: Monitoring the "Tokens-per-Trip." If a single trip's LLM cost exceeds $2.00, the router triggers a "Context-Compression-Pass" to reduce token usage.

## 3. Data Schema: `Inference_Router_Log`

```json
{
  "request_id": "TBIP-7711",
  "task_type": "ITINERARY_RE_ROUTING",
  "complexity_score": 0.85,
  "selected_model": "GEMINI_1_5_PRO",
  "reason": "HIGH_LOGICAL_DENSITY_REQUIRED",
  "latency_ms": 1200,
  "token_count": 4500,
  "estimated_cost_usd": 0.035,
  "cache_hit": false
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Emergency-Escalation' Rule**: During a flight cancellation or crisis, the agent MUST always use the **Flagship** model to ensure maximum logical reliability, regardless of cost.
- **Rule 2: The 'Context-Pruning' Requirement**: Before sending a 50-page GDS response to a model, the router MUST run a "Keyword-Filter" to remove irrelevant data, saving context tokens.
- **Rule 3: Prompt-Caching-Preference**: The router MUST prioritize models with "Prompt-Caching" (e.g., Gemini) for repetitive tasks like "Daily-Itinerary-Sync."

## 5. Success Metrics (Architecture)

- **Inference-Cost-Efficiency**: USD saved compared to a "Flagship-Only" architecture.
- **Average-Response-Latency**: Reduction in time-to-first-token.
- **Model-Accuracy-Parity**: Ensure Class A tasks don't suffer performance degradation when moved to lightweight models.
