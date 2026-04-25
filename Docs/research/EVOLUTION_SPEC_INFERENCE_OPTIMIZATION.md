# Evolution Spec: Inference Optimization & Distillation (EV-003)

**Status**: Research/Draft
**Area**: Intelligence Cost-Reduction & Knowledge Compression

---

## 1. The Problem: "The Reasoning-Cost Floor"
High-integrity reasoning (Tier 3) is expensive ($15+ per 1M tokens). To scale to millions of travelers, we must move the "Brains" of the system into lower-cost models (Tier 1) without losing the "Integrity."

## 2. The Solution: 'Ultra-to-Flash' (U2F) Distillation

U2F is a systematic process for fine-tuning small models using the "Teacher-Student" paradigm.

### U2F Workflow:

1.  **Synthetic Dataset Generation**: Use Tier 3 models (o1/Opus) to generate 50,000 "Perfect Execution Traces" based on the `Scenario_Library`.
2.  **Rationale Extraction**: Ensure every trace includes the "Hidden Reasoning" (Chain-of-Thought) that led to the decision.
3.  **Fine-Tuning**: Fine-tune a Tier 1 model (Gemini 1.5 Flash / GPT-4o-mini) on this "Reasoning-Rich" dataset.
4.  **Verification (The 'Bar' Test)**: Run the fine-tuned T1 model against the original T3 model on a blind set of 500 scenarios.
5.  **Deployment**: If the T1 model matches T3's accuracy > 95%, it becomes the primary "Reasoning Engine" for that specific category.

## 3. Data Schema: `Distillation_Audit`

```json
{
  "target_model": "agency-flash-v2",
  "teacher_model": "o1-preview",
  "dataset_size": 50000,
  "categories_distilled": ["RE-PROTECTION", "COMPLIANCE_CHECK"],
  "validation_metrics": {
    "accuracy_vs_teacher": 0.96,
    "latency_reduction_factor": 15.0,
    "cost_reduction_factor": 100.0
  }
}
```

## 4. Operational Guardrails

- **Integrity Floor**: If a distilled model's confidence falls below 0.85 on a live task, the system must "Escalate to Teacher" (T3).
- **Periodic Re-Distillation**: Models are re-distilled every 30 days to incorporate new "Batch" scenarios and human overrides.
- **Safety Pruning**: During distillation, ensure the student model does not inherit any "Harmful or Biased" reasoning patterns from the teacher.

## 5. Success Metrics (Inference)

- **Token Spend Reduction**: % decrease in total LLM API costs while maintaining accuracy.
- **System Latency**: % improvement in end-to-end recovery planning speed.
- **Scalability**: Ability to handle 10x more concurrent exceptions without increasing the "Ultra-Tier" budget.
