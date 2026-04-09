# Notebook 03: Session Strategy and Prompt Bundle — Contract Definition

## Environment

- **Package manager**: `uv` — run with `uv run python <script>` or `.venv/bin/python`
- **Python**: 3.13, venv at `.venv/`

## Purpose

Transform a `DecisionResult` (from Notebook 02) into:

1. **SessionStrategy** — What the agent should do next, in what order, with what guardrails
2. **PromptBundle** — The actual text blocks that compose the next interaction

This notebook does NOT:
- Execute voice calls or external research
- Perform sourcing or booking
- Run multi-agent choreography

It plans the next turn. That is all.

---

## Inputs

| Input | Type | Source | Description |
|-------|------|--------|-------------|
| `decision_result` | DecisionResult | Notebook 02 | The decision state + blockers + questions + contradictions |
| `packet` | CanonicalPacket | Notebook 01 | The facts, derived signals, hypotheses, unknowns |
| `session_context` | dict (optional) | External | Prior session history, previous questions asked, previous answers |
| `agent_profile` | dict (optional) | External | Agent's style preferences, language, tone |

### DecisionResult Shape (from NB02)

```python
{
    "packet_id": str,
    "current_stage": str,              # discovery | shortlist | proposal | booking
    "hard_blockers": List[str],        # e.g. ["destination_city", "travel_dates"]
    "soft_blockers": List[str],        # e.g. ["budget_range", "trip_purpose"]
    "contradictions": List[dict],      # e.g. [{"field_name": "budget_range", "values": [...], ...}]
    "decision_state": str,             # ASK_FOLLOWUP | BRANCH_OPTIONS | PROCEED_INTERNAL_DRAFT | PROCEED_TRAVELER_SAFE | STOP_NEEDS_REVIEW
    "follow_up_questions": List[dict], # e.g. [{"field_name": "...", "question": "...", "priority": "critical", "can_infer": bool, "inference_confidence": float, "suggested_values": [...]}, ...]
    "branch_options": List[dict],      # e.g. [{"label": "Budget-tier options", "description": "...", "contradictions": [...]}]
    "rationale": dict,                 # e.g. {"hard_blockers": [...], "confidence": 0.824, "reason": "..."}
    "confidence_score": float          # 0.0 - 1.0
}
```

---

## Outputs

### 1. SessionStrategy

```python
@dataclass
class SessionStrategy:
    session_goal: str                    # One sentence: what this session must achieve
    priority_sequence: List[str]         # Ordered steps (max 5)
    tonal_guardrails: List[str]          # Tone rules for this session
    risk_flags: List[str]                # Things to watch for
    suggested_opening: str               # First message to the traveler/owner
    exit_criteria: List[str]             # What must be true to end the session
    next_action: str                     # Mirrors decision_state
    assumptions: List[str]               # What we're assuming (for internal draft)
```

### 2. PromptBundle

```python
@dataclass
class PromptBundle:
    system_context: str                  # What the LLM must know about this situation
    user_message: str                    # The actual message to send
    follow_up_sequence: List[dict]       # Ordered follow-ups with triggers
    branch_prompts: List[dict]           # Branch options (if BRANCH_OPTIONS state)
    internal_notes: str                  # Notes for the agent (not shown to traveler)
    constraints: List[str]               # What the LLM must NOT do
```

---

## Decision-State-Specific Behavior

Each of the 5 decision states produces different outputs.

### ASK_FOLLOWUP

**Session goal**: Collect missing blocking information.

**Priority sequence**:
1. Ask hard blocker questions in order (from DecisionResult.follow_up_questions, sorted by priority)
2. If hypothesis exists for a blocked field, offer it as a suggested value
3. If all hard blockers answered, check soft blockers
4. End session once hard blockers are collected

**Question sequencing rules** (see section below):
- Hard blocker questions first, all critical priority
- If multiple hard blockers, ask the most constraining one first:
  1. traveler_composition (changes everything downstream)
  2. destination_city (determines sourcing path)
  3. origin_city (affects flight pricing)
  4. travel_dates (affects availability)
  5. Other blockers
- Soft blocker questions only after hard blockers are resolved

**Prompt structure**:
- System context: "You are collecting missing information for a travel booking."
- User message: Direct questions from follow_up_questions
- Follow-up sequence: Each question with trigger conditions
- Internal notes: "Do not proceed to drafting until hard blockers are filled."

**Branch prompts**: None.

---

### BRANCH_OPTIONS

**Session goal**: Present alternative paths and let the decision-maker choose.

**Priority sequence**:
1. Explain that multiple valid interpretations exist
2. Present each branch option with:
   - What it means
   - Trade-offs (budget, time, experience)
   - Which path the data slightly favors (if any)
3. Ask for preference
4. Once chosen, proceed with normal flow for that path

**Branch presentation rules**:
- Each branch has a label, description, and trade-off summary
- Branches are presented as options, not recommendations
- The data that caused the branch is explained neutrally
- Maximum 3 branches per session
- If more than 3 branches exist, ask for clarification to narrow

**Prompt structure**:
- System context: "Present options neutrally. Do not push any option."
- User message: Branch descriptions with trade-offs
- Branch prompts: One prompt per branch option, each with:
  - Branch label
  - What this path means
  - Pros/cons
  - Suggested question: "Does this fit your vision?"
- Internal notes: "Record which branch the traveler chooses for future routing."

---

### PROCEED_INTERNAL_DRAFT

**Session goal**: Generate a draft for the agent's internal review. NOT for traveler.

**Priority sequence**:
1. Acknowledge soft blockers that remain
2. Generate draft with explicit assumptions documented
3. Flag assumptions that could significantly change the output
4. Recommend next steps for resolution

**Prompt structure**:
- System context: "Generate an INTERNAL DRAFT. Mark as NOT FOR TRAVELER. List all assumptions."
- User message: Request for draft with current known facts
- Internal notes: Full list of soft blockers, assumptions, and what would change if they were resolved
- Constraints: "Do not present this to the traveler. This is a working draft only."

**Branch prompts**: None.

---

### PROCEED_TRAVELER_SAFE

**Session goal**: Generate a traveler-ready output.

**Priority sequence**:
1. Generate the proposal/itinerary based on all known facts
2. Ground all claims in facts (cite evidence refs)
3. Include rationale for recommendations
4. Present with confidence

**Prompt structure**:
- System context: "Generate a traveler-ready proposal. All claims must be grounded in facts."
- User message: Request for proposal with full context
- Internal notes: None needed — this is safe for external use
- Constraints: "Do not mention unknowns, hypotheses, or contradictions."

**Branch prompts**: None.

---

### STOP_NEEDS_REVIEW

**Session goal**: Escalate to human review. Generate a review briefing.

**Priority sequence**:
1. Explain why automated processing cannot continue
2. Summarize the critical issues
3. Provide context for the human reviewer
4. Suggest resolution options if possible

**Prompt structure**:
- System context: "Generate a human review briefing. Be specific about the issue."
- User message: Review request with issue summary
- Internal notes: Full contradiction details, evidence refs, and suggested resolutions
- Constraints: "This is for internal review only. Do not contact traveler until resolved."

**Branch prompts**: None.

---

## Question Sequencing Rules

When ASK_FOLLOWUP, questions must be ordered by:

### Rule 1: Constraint-first
Ask questions that constrain the solution space first.

Order:
1. **traveler_composition** — changes everything (group size, age bands, mobility needs)
2. **destination_city** — determines sourcing path (domestic vs international, preferred suppliers)
3. **origin_city** — affects flight pricing and availability
4. **travel_dates** — narrows availability window
5. **budget_range** — sets the financial boundary
6. **trip_purpose** — refines the experience type
7. **traveler_preferences** — fine-tunes the recommendations

### Rule 2: Group by topic
Don't interleave unrelated topics.

Bad: "Where are you going? How many people? What's your budget? When are you traveling?"
Good: "Who's traveling and what's the group composition? → Where are you thinking of going? → When and what's the budget?"

### Rule 3: Use hypothesis hints when available
If a hypothesis exists for a blocked field, offer it:

- "You mentioned maybe Singapore — is that still your top choice, or are you considering alternatives?"
- NOT: "Where would you like to go?"

### Rule 4: Never ask more than 3 questions at once
If more than 3 hard blockers remain, ask the top 3 first, then follow up.

### Rule 5: Context-aware re-asking
If a field was previously asked about but the answer was unclear or contradictory, re-ask with context:

- "Last time you mentioned March 15, but also April 1. Could you confirm which dates work?"
- NOT: "When are you traveling?"

---

## Branch Presentation Rules

When BRANCH_OPTIONS:

### Rule 1: Maximum 3 branches
If more than 3 branches exist, ask for clarification to narrow first.

### Rule 2: Neutral framing
Each branch is presented as "Option A", "Option B", etc. — not "Recommendation" vs "Alternative."

### Rule 3: Trade-off summary
Each branch includes:
- What you get
- What you give up
- Budget implication
- Timeline implication

### Rule 4: One question per branch
After presenting all branches, ask: "Which of these feels closest to what you have in mind?"

### Rule 5: Record the choice
Once chosen, log it as a fact with explicit_user authority for future sessions.

---

## Prompt Block Structure

Every prompt in the PromptBundle follows this structure:

```python
{
    "role": "system" | "user" | "assistant",
    "content": str,
    "metadata": {
        "decision_state": str,
        "stage": str,
        "question_index": int,       # For follow-up sequence
        "total_questions": int,
        "is_internal": bool,         # True if not for traveler
        "evidence_refs": List[str],  # Evidence refs grounding this prompt
    }
}
```

### System Context Block

Always includes:
1. Current decision state
2. Current stage
3. Known facts summary
4. What to ask/produce
5. What NOT to do

```
You are a travel planning assistant.

Context:
- Stage: discovery
- Decision: ASK_FOLLOWUP
- Known: Travelers from Bangalore, 3 people, family with young kids
- Missing: Destination, exact dates, budget

Your task:
- Ask the following 3 questions in order
- Do not proceed to drafting until answers are received
- Do not make assumptions about missing fields

Questions:
1. Where would you like to go?
2. When are you planning to travel?
3. What's your approximate budget?
```

### User Message Block

The actual message sent to the traveler or agent:

```
Hi! I'd love to help plan your trip. A few quick questions:

1. Where would you like to go?
2. When are you planning to travel?
3. What's your approximate budget?
```

### Follow-Up Sequence Block

For multi-turn conversations, each follow-up has:

```python
{
    "question": str,
    "field_name": str,
    "priority": "critical" | "high" | "medium" | "low",
    "trigger": str,           # When to ask this (e.g. "after destination answered")
    "suggested_values": List[str],  # If hypothesis exists
    "max_retries": int,       # How many times to re-ask if unclear
}
```

### Internal Notes Block

Only for the agent, never shown to traveler:

```python
{
    "assumptions": List[str],      # What we're assuming
    "soft_blockers": List[str],    # What's still missing
    "contradictions": List[dict],  # Active contradictions
    "risks": List[str],            # Things to watch for
    "next_steps": List[str],       # What to do after this session
}
```

---

## Confidence and Tone Scaling

The session strategy adjusts tone based on confidence score:

| Confidence | Tone | Behavior |
|------------|------|----------|
| 0.0 - 0.3 | Cautious | Ask more questions, state uncertainty explicitly |
| 0.3 - 0.6 | Measured | Ask focused questions, note assumptions |
| 0.6 - 0.8 | Confident | Proceed with draft, note remaining gaps |
| 0.8 - 1.0 | Direct | Produce final output, no hedging |

---

## Test Requirements

### Test 1: ASK_FOLLOWUP → Correct question sequence
- Input: DecisionResult with 3 hard blockers
- Expected: SessionStrategy with 3 questions in constraint-first order
- Expected: PromptBundle with max 3 questions per turn

### Test 2: ASK_FOLLOWUP → Hypthesis hints used
- Input: DecisionResult with blocked field that has hypothesis
- Expected: Question uses suggested value as hint, not generic question

### Test 3: BRANCH_OPTIONS → Neutral branch presentation
- Input: DecisionResult with budget contradiction
- Expected: SessionStrategy with 2 branches, neutrally framed
- Expected: PromptBundle with trade-off summaries

### Test 4: BRANCH_OPTIONS → Max 3 branches
- Input: DecisionResult with 5 contradictions
- Expected: Only 3 branches presented, ask for clarification first

### Test 5: PROCEED_INTERNAL_DRAFT → Assumptions documented
- Input: DecisionResult with soft blockers
- Expected: SessionStrategy with assumptions listed
- Expected: PromptBundle marked as internal-only

### Test 6: PROCEED_TRAVELER_SAFE → Grounded in facts
- Input: DecisionResult with all blockers filled
- Expected: SessionStrategy with no assumptions
- Expected: PromptBundle with no mention of unknowns

### Test 7: STOP_NEEDS_REVIEW → Review briefing
- Input: DecisionResult with date contradiction
- Expected: SessionStrategy with escalation goal
- Expected: PromptBundle for internal review

### Test 8: Question sequencing → Constraint-first order
- Input: DecisionResult with all 4 hard blockers
- Expected: Questions ordered: traveler_composition → destination → origin → dates

### Test 9: Question sequencing → Max 3 per turn
- Input: DecisionResult with 5 hard blockers (custom MVB)
- Expected: Only first 3 questions in first turn

### Test 10: Confidence → Tone scaling
- Input: DecisionResult with confidence 0.2
- Expected: Cautious tone, uncertainty stated explicitly
- Input: DecisionResult with confidence 0.9
- Expected: Direct tone, no hedging

---

## Implementation Notes

1. **Decision state drives everything** — The SessionStrategy and PromptBundle are entirely determined by decision_state
2. **Questions are pre-built** — DecisionResult.follow_up_questions already has the questions; NB03 sequences and formats them
3. **Branches are derived from contradictions** — branch_options in DecisionResult becomes the branch prompts
4. **Internal vs external is a hard boundary** — PROCEED_INTERNAL_DRAFT outputs are NEVER shown to travelers
5. **PromptBundle is serializable** — Must be JSON-serializable for API transport
6. **Session context is append-only** — Previous questions and answers are added to context, never overwritten

---

## Known Limitations (from NB02 scenario testing)

### 1. Ambiguous values not detected
**Gap**: "Andaman or Sri Lanka" is treated as a valid destination.
**NB03 mitigation**: If destination value contains "or" or "maybe", add a clarification question even if NB02 said PROCEED_TRAVELER_SAFE.

### 2. No urgency handling
**Gap**: Last-minute trips still get soft blocker questions.
**NB03 mitigation**: If travel_dates contain "this weekend" or dates within 7 days, suppress soft blocker questions.

### 3. Budget stretch not structured
**Gap**: "200000 (can stretch)" — stretch signal lost.
**NB03 mitigation**: Parse value string for stretch signals and use in question generation.

---

## Files

- **This contract**: `notebooks/03_session_strategy_contract.md`
- **NB02 output**: `notebooks/02_gap_and_decision.ipynb`
- **NB02 test results**: `notebooks/02_SCENARIO_TEST_RESULTS.md`
- **NB02 scenario analysis**: `notebooks/scenario_analysis.md`
