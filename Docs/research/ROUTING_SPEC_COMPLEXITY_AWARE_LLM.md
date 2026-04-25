# Routing Spec: Complexity-Aware LLM Tiers (RO-001)

**Status**: Research/Draft
**Area**: Model Orchestration & Cost-Aware Routing

---

## 1. The Problem: "The Intelligence-Cost Imbalance"
Using a high-cost "Reasoning" model for a simple heartbeat check is wasteful. Using a "Flash" model for a multi-party bankruptcy recovery is dangerous. We need **Complexity-Aware Routing**.

## 2. The Solution: 'Tiered-Inference' Architecture

The system routes every AI request to one of three Intelligence Tiers based on a `Task_Complexity_Score`.

### Tier 1: 'Flash' Monitoring (Latency-First)
- **Models**: GPT-4o-mini, Gemini 1.5 Flash.
- **Tasks**: Heartbeat monitoring, simple intent classification, sentiment analysis, basic data extraction.
- **Goal**: Sub-second response for high-frequency low-risk tasks.

### Tier 2: 'Reasoning' Recovery (Logic-First)
- **Models**: GPT-4o, Claude 3.5 Sonnet.
- **Tasks**: Trip recovery planning, multi-tool orchestration, constraint-solving, drafting emails/messages.
- **Goal**: Deep logical consistency for active operational changes.

### Tier 3: 'Ultra' Post-Mortem (Integrity-First)
- **Models**: o1-preview, Claude 3 Opus.
- **Tasks**: Root-cause analysis, complex policy intersections, adversarial verification (DBV), generating new "Batch" scenarios.
- **Goal**: Uncompromising reasoning depth for system-wide hardening.

## 3. The 'Router' Logic

Every task is pre-scored by a **Meta-Agent** (running on Tier 1) before routing:

```json
{
  "task": "Re-protect 50 travelers after airline bankruptcy",
  "complexity_factors": {
    "num_travelers": 50,
    "legal_implications": "HIGH",
    "budget_impact": "CRITICAL"
  },
  "recommended_tier": 3,
  "rationale": "High-volume, high-stakes recovery requiring massive constraint solving."
}
```

## 4. Operational Guardrails

- **Fallback Routing**: If a Tier 2 model fails to reach consensus, it is automatically "Promoted" to Tier 3.
- **Cost Quota**: Daily "Ultra" tier usage is capped to prevent budget blowouts during a mass-disruption event.
- **Cache-First**: Common recovery patterns are cached at the "Flash" tier to avoid redundant high-cost reasoning.

## 5. Success Metrics (Routing)

- **Cost Efficiency**: % reduction in token spend by using Flash models for T1 tasks.
- **Reasoning Accuracy**: % of complex recoveries that succeed on the first attempt after being routed to T2/T3.
- **Latency Balancing**: Maintaining sub-second UX for monitoring while allowing 10s+ for deep recovery planning.
