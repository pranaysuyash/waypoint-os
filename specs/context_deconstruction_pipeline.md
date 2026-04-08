# Spec: Agency Context Deconstruction Pipeline

## 1. Purpose
This specification defines the process of transforming unstructured agency notes (the "First Call" data) into a machine-readable, confidence-tagged state that drives the subsequent Traveler Voice Session.

The goal is to convert **human intuition** into **operational constraints**.

---

## 2. The Pipeline Flow
The deconstruction process follows a four-stage sequence:

### Stage 1: Normalized Entity Extraction
**Input**: Raw text/notes from the agency owner.
**Process**: The agent maps raw text to the `Shared State Model`.
**Output**: A structured JSON packet where every field is tagged with a confidence score.

**Field Mapping Examples:**
- "Bangalore" $\rightarrow$ `departure_city: { value: "Bangalore", confidence: 0.99, source: "explicit" }`
- "Maybe Singapore" $\rightarrow$ `destination_status: { value: "semi-open", confidence: 0.85, source: "explicit" }`
- "Parents + kid" $\rightarrow$ `traveler_profile.members: [ {type: "elderly", count: 2}, {type: "toddler", count: 1} ]`

### Stage 2: Bracket Classification (The Hypothesis)
**Input**: The normalized packet from Stage 1.
**Process**: The system applies a set of "Bracket Rules" to categorize the trip.
**Logic**:
- `members` contains (`elderly` AND `toddler`) $\rightarrow$ Classify as `Mixed-Age Family`.
- `budget` is $\sim 2.5\text{L}$ for 5 people $\rightarrow$ Classify as `Mid-Budget International`.
- `pace` is "relaxed" $\rightarrow$ Classify as `Low-Friction/Slow-Travel`.

**The Hypothesis**: "This is a High-Comfort, Mid-Budget, Mixed-Age Family trip." (This hypothesis determines the initial sourcing route and the specific risks to check).

### Stage 3: Gap and Contradiction Analysis
**Input**: The hypothesized state and the `Minimum Viable Brief (MVB)` checklist.
**Process**:
- **Gap Detection**: Identify missing blocking fields (e.g., "We have a budget, but no departure city").
- **Contradiction Detection**: Identify logic clashes (e.g., "Budget: Lean" vs "Hotel: Luxury").
- **Risk Identification**: Flag suitability risks based on the la-category (e.g., "Elderly + Toddler $\rightarrow$ High risk of exhaustion if itinerary is packed").

**Output**: A `Session_Requirement_List` (The "Must-Ask" list for the voice agent).

### Stage 4: Session Strategy & Prompt Generation
**Input**: The structured state + Gap list + Hypothesis.
**Process**: Generate a "Battle Plan" for the Voice Agent.
**Output**:
1. **The Session Goal**: (e.g., "Resolve destination ambiguity and verify budget splits").
2. **The Prompt Profile**: A tailored system prompt for the Voice Agent that includes:
    - **Context**: "You are talking to a family who is open to Singapore but worried about toddler naps."
    - **Priority Sequence**: "1. Confirm dates $\rightarrow$ 2. Validate budget $\rightarrow$ 3. Probe for shopping intent."
    - **Tonal Guardrails**: "Professional, empathetic, avoid sounding like a form."

---

## 3. Data Contracts

### Input (Agency Raw)
```text
"Family of 5 from Bangalore, maybe Singapore, 5 nights, parents + small child, budget around 2.5L excluding shopping, they want it relaxed."
```

### Output (Deconstructed State)
```json
{
  "extracted_state": {
    "departure_city": "Bangalore",
    "destination": "Singapore (semi-open)",
    "duration": 5,
    "members": ["adult x 2", "elderly x 2", "toddler x 1"],
    "budget_total": 250000,
    "budget_scope": "excluding_shopping",
    "pace": "relaxed"
  },
  "classifications": {
    "traveler_type": "mixed_age_family",
    "budget_tier": "mid",
    "routing_path": "preferred_supplier_custom"
  },
  "session_requirements": {
    "blocking_questions": ["passport_status", "exact_dates"],
    "contradictions": [],
    "risks": ["toddler_nap_pacing", "elderly_mobility"]
  },
  "voice_agent_strategy": {
    "primary_objective": "verify_budget_and_destination",
    "suggested_opening": "Mention we've drafted a relaxed family-friendly plan for Singapore and want to refine it with them."
  }
}
```
