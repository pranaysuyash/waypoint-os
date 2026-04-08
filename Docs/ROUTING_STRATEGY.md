# Routing and Optimization Architecture

## The Two-Loop System

### 1. Online Loop (Production Path)
A deterministic pipeline for every user turn:
- **Context Normalization**: Raw data $\rightarrow$ Structured Context Packet.
- **Intake Router**: A fast model that classifies the turn into a fixed taxonomy (e.g., `billing`, `sales`).
- **Prompt Composer**: Assembles prompts from a versioned registry (Base + Domain + Policy + Few-Shot).
- **Specialist Execution**: The chosen agent generates the response.
- **Verifier Layer**: A second pass to check for policy violations and hallucinations.
- **Memory Update**: Updates structured state and logs telemetry.

### 2. Offline Loop (Autoresearch Path)
Inspired by Karpathy's autoresearch, this loop optimizes the system offline:
- **Eval Harness**: A dataset of 200-500 gold-labeled cases.
- **Mutation**: Tweak router prompts, prompt packs, or context packing.
- **Scoring**: Measure a `Composite Score` (Accuracy + Tool F1 + Quality + Latency).
- **Persistence**: Keep only improvements that measurably increase the score.

## Key Design Principles
- **No Live Prompt Generation**: Avoid improvising prompts on every turn. Use a registry.
- **Classify, Don't Solve**: The router's only job is to route, not to answer.
- **Evidence-Based Improvement**: Only change production prompts after they pass the eval harness.
