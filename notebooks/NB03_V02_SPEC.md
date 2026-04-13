# Notebook 03 v0.2: Session Strategy and Prompt Bundle

**Date**: 2026-04-12
**Co-locked with**: `specs/canonical_packet.schema.json` v0.2, NB02 v0.2 contract
**Input**: `DecisionResult` v0.2 + `CanonicalPacket` v0.2
**Output**: `SessionStrategy` + `PromptBundle`

---

## Purpose

NB03 answers: **"Given the decision state and context, how should the next interaction be structured, what should be said, and to whom?"**

It is the conversation planner. It does NOT:
- Extract facts (NB01)
- Make judgment calls (NB02)
- Execute external actions (calls, bookings, research)
- Run the conversation loop

---

## Input Contract

| Input | Type | Source |
|-------|------|--------|
| `decision_result` | DecisionResult v0.2 | NB02 |
| `packet` | CanonicalPacket v0.2 | NB01 |
| `session_context` | dict (optional) | External — prior turns |
| `agent_profile` | dict (optional) | External — agent preferences |

---

## Output Contract

### SessionStrategy

```python
@dataclass
class SessionStrategy:
    session_goal: str                    # One sentence: what this session must achieve
    priority_sequence: List[str]         # Ordered steps (max 5)
    tonal_guardrails: List[str]          # Tone rules for this session
    risk_flags: List[str]                # Things to watch for
    suggested_opening: str               # First message
    exit_criteria: List[str]             # What must be true to end the session
    next_action: str                     # Mirrors decision_state
    assumptions: List[str]               # For internal draft mode only
```

### PromptBundle

```python
@dataclass
class PromptBundle:
    system_context: str                  # What the LLM must know
    user_message: str                    # The actual message to send
    follow_up_sequence: List[dict]       # Ordered follow-ups with triggers
    branch_prompts: List[dict]           # Branch options (if BRANCH_OPTIONS)
    internal_notes: str                  # Agent-only notes (never traveler-facing)
    constraints: List[str]               # What the LLM must NOT do
```

---

## Operating-Mode-Specific Strategy Builders

NB03 selects a strategy builder based on `decision_state` AND `operating_mode`. Same decision state, different behavior.

### Mode Matrix

| Operating Mode | ASK_FOLLOWUP Behavior | PROCEED_TRAVELER_SAFE Behavior | STOP_NEEDS_REVIEW Behavior |
|---------------|----------------------|-------------------------------|--------------------------|
| `normal_intake` | Standard constraint-first questions | Confident proposal | Standard review briefing |
| `audit` | Focus on gaps: "Here's what's missing vs market" | Audit report, not proposal | Value-gap briefing |
| `emergency` | Crisis questions only: docs, contacts, timeline | N/A (never safe in emergency) | Emergency protocol with step-by-step actions |
| `follow_up` | Re-engagement: "Any thoughts on the options?" | Re-send proposal with new context | N/A |
| `cancellation` | Policy questions: "Reason? Insurance?" | Cancellation summary with options | Policy briefing |
| `post_trip` | Feedback questions | Review request (timed) | N/A |
| `coordinator_group` | Per-group questions + coordinator summary | Per-group proposals + group summary | Coordinator escalation briefing |
| `owner_review` | N/A (not a traveler-facing mode) | Quote quality brief + margin analysis | Owner briefing with commercial data |

---

## Structural Sanitization (Traveler-Safe Boundary)

### The Rule

Every prompt block has an explicit `audience` field:

```python
@dataclass
class PromptBlock:
    content: str
    audience: Literal["internal", "traveler"]
    metadata: dict
```

### Sanitization Pipeline

`build_traveler_safe_prompts()` receives a **sanitized packet view**, not the raw packet:

```python
def sanitize_for_traveler(packet: CanonicalPacket) -> dict:
    """
    Strip all internal-only data from packet before passing to traveler-safe builder.
    This is structural — the data is not even available to the builder, not just hidden.
    """
    facts = {}
    for field_name, slot in packet.facts.items():
        # Skip owner-only fields entirely
        if field_name in ("agency_notes", "owner_priority_signals"):
            continue
        # Skip owner_constraints with internal_only visibility
        if field_name == "owner_constraints":
            visible = [c for c in slot.value if c.get("visibility") == "traveler_safe_transformable"]
            if visible:
                facts[field_name] = {"value": visible, **{k: v for k, v in asdict(slot).items() if k != "value"}}
            continue
        facts[field_name] = slot

    # Never pass hypotheses, contradictions, or internal data
    return {
        "facts": facts,
        # No hypotheses, no contradictions, no unknowns, no ambiguities,
        # no derived_signals, no internal_data_present
    }
```

### Leakage Checks (Automated Tests)

Every `build_traveler_safe_prompts()` output is validated:

```python
def check_no_leakage(bundle: PromptBundle) -> List[str]:
    """
    Verify that traveler-facing content contains no internal concepts.
    """
    leaks = []
    forbidden = ["unknown", "hypothesis", "contradiction", "blocker",
                 "internal_only", "owner_constraint", "agency_note"]
    for text_field in [bundle.user_message, bundle.system_context]:
        text_lower = text_field.lower()
        for term in forbidden:
            if term in text_lower:
                leaks.append(f"Leakage detected: '{term}' in {text_field[:50]}...")
    return leaks
```

---

## Question Intent Model

Every question carries intent metadata:

```python
@dataclass
class QuestionWithIntent:
    question: str
    field_name: str
    priority: str                  # critical | high | medium | low
    intent: str                    # "What downstream decision does this unlock?"
    tests_assumption: str | None   # "What assumption does this question test?"
    trigger: str                   # When to ask
    suggested_values: List[str]    # If hypothesis exists
    max_retries: int               # How many times to re-ask
```

**Examples**:

| Question | Intent | Tests Assumption |
|----------|--------|-----------------|
| "Between Andaman and Sri Lanka, which do you prefer?" | Resolve destination to select sourcing path | That traveler has a preference between the two |
| "Can you confirm the exact travel dates?" | Enable urgency and availability checks | That dates are flexible, not fixed |
| "Is the ₹2L budget total or per person?" | Clarify budget scope for feasibility | That scope is unclear |
| "For your parents: wheelchair needed or just slower pace?" | Determine mobility constraint severity | That elderly have mobility needs |

---

## Dynamic Risk Generation

NB03 generates risk flags from packet content, not from static strings.

```python
def generate_risk_flags(packet: CanonicalPacket, decision: DecisionResult) -> List[str]:
    """
    Generate contextual risk flags based on actual packet data.
    NOT static templates — these emerge from fact combinations.
    """
    risks = []

    # Toddler + late-night flight + long transfer
    comp = packet.facts.get("party_composition", {}).value
    dest = packet.facts.get("destination_candidates", {}).value
    if comp and comp.get("children"):
        ages = packet.facts.get("child_ages", {}).value or []
        if any(a < 3 for a in ages) and dest:
            risks.append(f"Toddler ({min(ages)}yo) + {dest} — flag pacing and transfer complexity")

    # Elderly + island destination + weak medical access
    if comp and comp.get("elderly"):
        if dest and dest[0] in ("Maldives", "Andaman", "Lakshadweep"):
            risks.append(f"Elderly travelers + {dest[0]} — verify medical access before booking")

    # Group disagreement + fixed budget
    if packet.facts.get("sub_groups"):
        budget = packet.facts.get("budget_max", {}).value
        if budget:
            groups = packet.facts["sub_groups"].value
            budget_spread = max(g.get("budget_share", 0) for g in groups.values()) - min(g.get("budget_share", budget) for g in groups.values())
            if budget_spread > 0.3 * budget:
                risks.append(f"Budget spread of ₹{budget_spread:,} across groups — coordination risk")

    # Self-booked hotel + agency-fit mismatch (audit mode)
    if decision.operating_mode == "audit":
        plan = packet.facts.get("traveler_plan", {}).value
        if plan and packet.facts.get("owner_notes"):
            risks.append("Self-booked plan detected — compare against agency-fit signals")

    # Visa timeline risk
    urgency = packet.derived_signals.get("urgency", {}).value
    visa = packet.facts.get("visa_status", {}).value
    if urgency == "high" and visa and visa.get("requirement") == "required":
        risks.append(f"High urgency + visa required — timeline risk")

    return risks
```

---

## Branch-Quality Rules

`BRANCH_OPTIONS` behavior varies by root cause:

| Branch Root Cause | Conversational Approach |
|------------------|------------------------|
| Budget flexibility (stretch vs fixed) | "Here are two options: one within your stated budget, one that stretches it for better value" |
| Destination unresolved | "Both are great choices — let me show you what each looks like so you can feel the difference" |
| Group priorities conflict | "Here's how each priority shapes the trip — you'll see the trade-offs clearly" |
| Traveler plan vs agency fit | "Your plan works well for X. Here's what the agency would do differently and why" |

---

## Confidence/Tone Scaling

| Confidence | Tone | Behavior |
|------------|------|----------|
| 0.0–0.3 | Cautious | Ask more questions, state uncertainty |
| 0.3–0.6 | Measured | Focused questions, note assumptions |
| 0.6–0.8 | Confident | Proceed with draft, note gaps |
| 0.8–1.0 | Direct | Final output, no hedging |

> **Invariant**: Tone adjusts communication style but never changes decision_state or suppresses required questions.

---

## Test Requirements v0.2

| # | Test | What It Validates |
|---|------|------------------|
| 1 | ASK_FOLLOWUP → constraint-first question order | Questions ordered: composition → destination → origin → dates |
| 2 | ASK_FOLLOWUP → hypothesis hints used | "Maybe Singapore" → offered as suggestion, not generic "where?" |
| 3 | ASK_FOLLOWUP + ambiguity | "Andaman or Sri Lanka" → clarification question even if NB02 said PROCEED |
| 4 | ASK_FOLLOWUP + emergency mode | Only crisis questions (docs, contacts, timeline) — no soft blockers |
| 5 | ASK_FOLLOWUP + coordinator_group | Per-group questions + coordinator summary |
| 6 | BRANCH_OPTIONS → neutral framing | No "recommended" vs "alternative" — "Option A", "Option B" |
| 7 | BRANCH_OPTIONS → root-cause quality | Budget branch vs destination branch use different conversational approach |
| 8 | PROCEED_INTERNAL_DRAFT → assumptions documented | Soft blockers listed as explicit assumptions |
| 9 | PROCEED_TRAVELER_SAFE → grounded in facts | No mention of unknowns, hypotheses, contradictions |
| 10 | PROCEED_TRAVELER_SAFE → sanitization | Owner-only fields not present in traveler-facing output |
| 11 | PROCEED_TRAVELER_SAFE + ambiguity | Ambiguous values trigger post-proposal confirmation question |
| 12 | STOP_NEEDS_REVIEW → review briefing | Contradiction details + evidence refs + suggested resolutions |
| 13 | STOP_NEEDS_REVIEW + emergency mode | Step-by-step emergency protocol with immediate actions |
| 14 | Sanitization → no leakage | user_message and system_context contain no internal concepts |
| 15 | Tone scaling → 0.2 cautious / 0.9 direct | Tone matches confidence, decision_state unchanged |
| 16 | Urgency suppression → soft blockers skipped | High urgency → only budget_min in soft blockers |

---

## Known Limitations Resolved in v0.2

| v0.1 Limitation | v0.2 Resolution |
|-----------------|-----------------|
| Static risk text | Dynamic risk generation from fact combinations |
| Procedural sanitization | Structural sanitization — internal data not even passed to builder |
| Same ASK_FOLLOWUP for all contexts | Operating-mode-specific builders (8 modes) |
| Questions without intent | QuestionWithIntent model — every question has purpose |
| Generic branch presentation | Branch-quality rules — different approach per root cause |
| No urgency awareness | Urgency-aware question suppression and reordering |
| No sanitization tests | 3 dedicated leakage-checking tests (#10, #14) |

---

## Files

- **This contract**: `notebooks/NB03_V02_SPEC.md`
- **Schema**: `specs/canonical_packet.schema.json` (v0.2)
- **NB02 contract**: `notebooks/NB02_V02_SPEC.md`
- **NB01 spec**: `Docs/NB01_V02_SPEC.md`
- **Governing principles**: `Docs/V02_GOVERNING_PRINCIPLES.md`
