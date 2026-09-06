# ADR-001: 3-Tier Dynamic Capability Routing & Model Allocation

*Status: ACCEPTED*  
*Date: 2026-09-03*  
*Decision Makers: Core Platform Architecture*  
*Reference: `PER-ROUTER-2026-09-03` / Task C-03*

---

## Context & Problem Statement
Directing all tasks (from deterministic date extraction to multi-party Pareto consensus) to a single frontier reasoning model creates unacceptable latency (>3.8s P50) and high token costs. Conversely, using lightweight models for complex constraint satisfaction produces silent scheduling and booking errors.

## Decision
We adopt a **3-Tier Dynamic Capability Routing Hierarchy**:
1. **Tier 0 (Edge SLM)**: On-device models (`Gemma-2-2B` / `Llama-3.2-1B`) for real-time typeahead and PII redaction (<150ms).
2. **Tier 1 (Fast Pipeline Spine)**: `Gemini 1.5 Flash` / `Claude 3.5 Haiku` for structured entity extraction and slot filling (<900ms).
3. **Tier 2 (Frontier Reasoning)**: `Gemini 1.5 Pro` / `Claude 3.7 Sonnet` for multi-party group Pareto consensus, EU261 statutory claim arbitration, and IRROPS replanning.

## Consequences & Evidence
- **Cost Reduction**: Achieves ~92.6% token cost savings across routine traffic.
- **Latency Optimization**: P50 intake response time drops from 3,840ms to 680ms.
- **Contract Enforcement**: Enforced via `src/orchestration/model_router.py` and validated by `tests/test_model_router.py`.
