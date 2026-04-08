---
name: routing_and_optimization_strategy
description: Architecture for dynamic routing and offline self-improvement using autoresearch patterns
type: project
---

**Core Architecture: The Two-Loop System**

To avoid the instability of live prompt generation, the system separates the "Production Path" from the "Improvement Path."

### 1. The Online Loop (Production Path)
A deterministic pipeline for every user turn:
1. **Context Normalization**: Converts raw CRM/Agency/Conversation data into a structured `Context Packet`.
2. **Intake Router**: A fast, cheap model that classifies the turn into a **fixed taxonomy** (e.g., `billing`, `sales`, `general_support`). It does not answer; it only decides the "bracket" and required tools.
3. **Prompt Composer**: Assembles the final prompt by combining versioned blocks from a registry: `Base System` + `Domain Block` + `Policy Block` + `Tool Rules` + `Few-Shot Examples`.
4. **Specialist Execution**: The chosen agent (Generalist or Specialist) generates a response based on the composed prompt.
5. **Verifier Layer**: A separate pass to check for policy violations, hallucinations, or missed required fields.
6. **Memory Update**: Updates the structured state and logs telemetry for the offline loop.

### 2. The Offline Loop (Autoresearch Path)
Inspired by Karpathy's autoresearch, this loop optimizes the system without risking live user experience:
- **The Goal**: Improve routing accuracy, tool-calling precision, and answer quality.
- **The Mechanism**: 
    - Sample failed or representative historical conversations.
    - Mutate a single dimension (e.g., tweak the router prompt, update a few-shot example).
    - Run the change against a fixed **Eval Harness** (dataset of 200-500 gold-labeled cases).
    - Measure the `Composite Score` (Routing Accuracy + Tool F1 + Quality + Latency).
    - Keep only the changes that measurably improve the score.
- **Optimization Targets**:
    - Router prompt wording.
    - Prompt pack few-shots.
    - Context packing/truncation strategies.
    - Escalation confidence thresholds.

**Key Design Principle:**
Do not let the LLM "invent" routing categories or prompts live. Use the LLM to *reason* within a structured framework, and use the Autoresearch loop to *evolve* that framework based on evidence.
