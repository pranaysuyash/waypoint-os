# The "First Mile" Implementation Plan (v1)

## 1. Goal
Convert a raw agency note into a validated, canonical state packet and a session strategy.

## 2. Implementation Sequence (The "Safe" Path)

### Stage 1: The Foundation (State & Schema)
- Define the **Canonical Packet Schema** (Facts, Signals, Hypotheses, Unknowns).
- Define the **MVB (Minimum Viable Brief)** blocker list.
- Setup the `src/schemas/` and `src/config/` directories.

### Stage 2: Source Adaptation (The Intake)
- Build `src/adapters/freeform.py` to handle raw notes.
- Build `src/adapters/structured_form.py` to handle partial CRM data.
- Implement a "Source Envelope" to preserve provenance.

### Stage 3: The Normalization Pipeline
- Build `src/pipelines/normalize.py`: Raw $\rightarrow$ Canonical Packet.
- Build `src/pipelines/validate.py`: Check for blockers and contradictions.
- Build `src/pipelines/infer.py`: Generate derived signals and soft hypotheses.

### Stage 4: The Decision Engine
- Implement the **Decision Policy** (Proceed $\rightarrow$ Ask $\rightarrow$ Branch $\rightarrow$ Escalate).
- Map "Gaps" to specific "Next-Best Questions" from the Question Bank.

### Stage 5: Session Strategy & Prompting
- Build `src/pipelines/prompt_bundle.py`: Assemble modular prompts.
- Generate the "Session Strategy" (Goal, Sequence, Tone).

## 3. The `.ipynb` Experimental Lab
We will use notebooks for **rapid prototyping** before moving to `src/`.

- **Notebook 01**: `intake_normalization_lab.ipynb` (Testing the extraction of raw notes $\rightarrow$ JSON).
- **Notebook 02**: `blocker_and_contradiction_lab.ipynb` (Testing the MVB logic).
- **Notebook 03**: `inference_and_hypothesis_lab.ipynb` (Testing "Derived Signals" vs "Hypotheses").
- **Notebook 04**: `session_strategy_lab.ipynb` (Testing the transition from state $\rightarrow$ prompt).

## 4. Success Metrics for v1
- **Extraction Accuracy**: Does "Parents + kid" always result in `elderly` and `toddler` members?
- **Blocker Precision**: Does the system correctly identify a missing budget as a blocking field?
- **Contradiction Recall**: Does it catch "Luxury" vs "Budget" mismatches?
- **Provenance Integrity**: Can we trace every fact back to its raw source?
