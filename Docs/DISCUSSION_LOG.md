# Discussion and Feedback Log

This document serves as the "Decision Audit Trail" for the project. It captures queries, feedback, and pivots derived from consultations with other AI agents (e.g., ChatGPT) and human experts.

## Log Entry: 2026-04-08 - The "Compiler" Pivot

### Context
Initial plan was "Agent-Centric" (Agent understands $\rightarrow$ Agent la-hypothesizes $\rightarrow$ Agent prompts).

### Feedback Received
- **Core Critique**: "Agentic" workflows are brittle. The system should be a "Compiler Pipeline."
- **Key Shift**: Move from `Prompting` $\rightarrow$ `State Integrity`.
- **New Pipeline**: `Normalize` $\rightarrow$ `Validate` $\rightarrow$ `Infer Cautiously` $\rightarrow$ `Decide Action` $\rightarrow$ `Generate Session Plan` $\rightarrow$ `Generate Prompt Bundle`.

### Key Decisions Made:
1. **Separation of Concerns**:
    - **Facts**: Explicitly stated.
    - **Derived Signals**: Direct implications (e.g., toddler $\rightarrow$ nap sensitivity).
    - **Hypotheses**: Soft patterns (e.g., "likely comfort-first").
    - **Unknowns**: Gaps and contradictions.
2. **Decision Policy**: The system must have a "Gating Rule" to decide if it can proceed to planning or must ask follow-ups first.
3. **Prompting Strategy**: Shift from monolithic prompts to "Modular Prompt Blocks" (System Frame + Context + Objective + Response Policy).
4. **Input Model**: Support both freeform and structured intake, normalizing both into a single canonical packet.
5. **Tooling**: Use `uv` with Python 3.13 for strict environment management.

### Action Items for Implementation:
- [ ] Implement `Source Adapters` for heterogeneous input.
- [ ] Define the `Canonical Packet Schema`.
- [ ] Build the `MVB (Minimum Viable Brief)` blocker check.
- [ ] Create a `Prompt Registry` instead of freeform prompt generation.
