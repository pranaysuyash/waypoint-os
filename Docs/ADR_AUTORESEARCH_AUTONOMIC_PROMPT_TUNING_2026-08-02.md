# ADR 17: Karpathy AutoResearch Autonomic Prompt & Strategy Tuning Engine

**Date**: 2026-08-02  
**Status**: APPROVED  
**Deciders**: AI Research Team, Agentic Engineering Lead  
**Governing Rule**: `motto_v4.md` (Rule 0.9: Prompt & Model Governance, Rule 0.15: Third-Layer Decoupling)

---

## 1. Context & Business Need

Hardcoded system prompts, RAG chunking parameters, and suitability scoring weights can gradually degrade in accuracy as traveler request patterns evolve across markets. Rather than manually tweaking prompts, we require an autonomous self-optimization loop inspired by Andrej Karpathy's `autoresearch` paradigm.

## 2. Technical Architecture & Decision

We implement the `AutoResearchLoop` framework in [`src/evals/autoresearch_loop.py`](file:///Users/pranay/Projects/travel_agency_agent/src/evals/autoresearch_loop.py):

1. **Autonomous Experimentation Loop**:
   - **Step 1 (Baseline Metric)**: Run baseline scenario evaluations against test inquiries in `data/fixtures/scenarios/`.
   - **Step 2 (Hypothesis Mutation)**: Propose controlled parameter mutations (e.g. system prompt framing, RAG retriever top-k, suitability weight parameters).
   - **Step 3 (Evaluation & Scoring)**: Execute scenario evaluation and compute composite score:
     $$\text{Score} = 0.4 \cdot \text{Accuracy} + 0.3 \cdot \text{Safety} + 0.2 \cdot \text{Speed} + 0.1 \cdot \text{Cost}$$
   - **Step 4 (Accept/Revert Decision)**: If $\text{Score}_{\text{new}} > \text{Score}_{\text{best}}$, commit winning configuration and record experiment lineage to `data/audit/autoresearch_experiments.jsonl`. Otherwise, revert mutation.

2. **Decoupled Experiment Lineage**:
   - AutoResearch mutations do not touch production code directly. All winning parameters are logged into structured lineage files and versioned via ADRs.

## 3. CLI Command & Inspection

```bash
# Run 5 iterations of autonomic prompt & strategy optimization
python3 -m src.evals.autoresearch_loop --iterations 5
```
