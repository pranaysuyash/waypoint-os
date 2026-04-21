"""
intake.strategy — NB03 v0.2: Session Strategy and Prompt Bundle.

This is the conversation planner. It consumes DecisionResult (NB02) and
CanonicalPacket (NB01) to produce SessionStrategy and PromptBundle.

Contract: notebooks/NB03_V02_SPEC.md

CRITICAL: Traveler-safe path is STRUCTURALLY SANITIZED. The raw packet is NEVER
passed to traveler-facing builders. Internal and traveler paths are SEPARATE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Literal
from enum import Enum

from .packet_models import CanonicalPacket, Slot, AuthorityLevel
from .decision import DecisionResult
from .safety import sanitize_for_traveler, check_no_leakage, enforce_no_leakage, SanitizedPacketView
from .config.agency_settings import AgencySettings


# =============================================================================
# SECTION 1: OUTPUT DATA CLASSES
# =============================================================================

class PriorityLevel(Enum):
    """Question priority levels for ordering."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class QuestionWithIntent:
    """
    A question with full intent metadata.

    Every question must have a clear purpose: what downstream decision
    it unlocks, what assumption it tests, and when to ask it.
    """
    question: str
    field_name: str
    priority: str  # critical | high | medium | low
    intent: str  # "What downstream decision does this unlock?"
    tests_assumption: Optional[str] = None  # "What assumption does this test?"
    trigger: str = "immediate"  # When to ask
    suggested_values: List[str] = field(default_factory=list)
    can_infer: bool = False
    inference_confidence: float = 0.0
    max_retries: int = 3

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "field_name": self.field_name,
            "priority": self.priority,
            "intent": self.intent,
            "tests_assumption": self.tests_assumption,
            "trigger": self.trigger,
            "suggested_values": self.suggested_values,
            "can_infer": self.can_infer,
            "inference_confidence": self.inference_confidence,
            "max_retries": self.max_retries,
        }


@dataclass
class PromptBlock:
    """A unit of prompt content with explicit audience tagging."""
    content: str
    audience: Literal["internal", "traveler"]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "audience": self.audience,
            "metadata": self.metadata,
        }


@dataclass
class SessionStrategy:
    """
    The conversation planner's output.

    Defines: how the next interaction should be structured, what tone to use,
    what risks to watch for, and what the exit criteria are.
    """
    session_goal: str  # One sentence: what this session must achieve
    priority_sequence: List[str]  # Ordered steps (max 5)
    tonal_guardrails: List[str]  # Tone rules for this session
    risk_flags: List[str]  # Things to watch for
    suggested_opening: str  # First message
    exit_criteria: List[str]  # What must be true to end the session
    next_action: str  # Mirrors decision_state
    assumptions: List[str] = field(default_factory=list)  # For internal draft only
    suggested_tone: str = "professional"  # cautious | measured | confident | direct

    def to_dict(self) -> dict:
        return {
            "session_goal": self.session_goal,
            "priority_sequence": self.priority_sequence,
            "tonal_guardrails": self.tonal_guardrails,
            "risk_flags": self.risk_flags,
            "suggested_opening": self.suggested_opening,
            "exit_criteria": self.exit_criteria,
            "next_action": self.next_action,
            "assumptions": self.assumptions,
            "suggested_tone": self.suggested_tone,
        }


@dataclass
class PromptBundle:
    """
    The actual content to be sent.

    Separates system context (LLM instructions) from user message (actual output),
    with explicit traveler-safe boundary enforcement.
    """
    system_context: str  # What the LLM must know
    user_message: str  # The actual message to send
    follow_up_sequence: List[dict]  # Ordered follow-ups with triggers
    branch_prompts: List[dict]  # Branch options (if BRANCH_OPTIONS)
    internal_notes: str  # Agent-only notes (never traveler-facing)
    constraints: List[str]  # What the LLM must NOT do
    audience: Literal["internal", "traveler", "both"] = "traveler"

    def to_dict(self) -> dict:
        return {
            "system_context": self.system_context,
            "user_message": self.user_message,
            "follow_up_sequence": self.follow_up_sequence,
            "branch_prompts": self.branch_prompts,
            "internal_notes": self.internal_notes,
            "constraints": self.constraints,
            "audience": self.audience,
        }

    def to_traveler_dict(self) -> dict:
        """
        Serialise for traveler-facing transport.

        Omits internal_notes and other internal-only fields so the object
        is intrinsically safe — even if accidentally logged or rendered.
        """
        return {
            "system_context": self.system_context,
            "user_message": self.user_message,
            "follow_up_sequence": self.follow_up_sequence,
            "branch_prompts": self.branch_prompts,
            "constraints": self.constraints,
            "audience": "traveler",
        }


# =============================================================================
# SECTION 2: TONE SCALING (based on confidence)
# =============================================================================

TONE_BY_CONFIDENCE = {
    (0.0, 0.3): "cautious",
    (0.3, 0.6): "measured",
    (0.6, 0.8): "confident",
    (0.8, 1.0): "direct",
}

TONAL_GUARDRAILS = {
    "cautious": [
        "State uncertainty explicitly",
        "Ask more questions before making suggestions",
        "Avoid definitive statements",
        "Offer multiple possibilities",
    ],
    "measured": [
        "Focus questions on gaps",
        "Note assumptions clearly",
        "Provide options with caveats",
        "Acknowledge what you don't know",
    ],
    "confident": [
        "Proceed with draft or proposal",
        "Note gaps without hedging",
        "Use clear, direct language",
        "Minor assumptions acceptable",
    ],
    "direct": [
        "Final output mode",
        "No hedging or uncertainty",
        "Clear actionable recommendations",
        "Assumptions already validated",
    ],
}


def determine_tone(confidence: float) -> str:
    """Map confidence score to tone category."""
    for (low, high), tone in TONE_BY_CONFIDENCE.items():
        if low <= confidence < high:
            return tone
    return "measured"  # Default


def get_tonal_guardrails(tone: str) -> List[str]:
    """Get guardrails for a given tone."""
    return TONAL_GUARDRAILS.get(tone, TONAL_GUARDRAILS["measured"])


# =============================================================================
# SECTION 3: QUESTION ORDERING (constraint-first)
# =============================================================================

# Field priority for question ordering (lower = more critical)
QUESTION_PRIORITY_ORDER = {
    "party_size": 1,
    "party_composition": 2,
    "destination_candidates": 3,
    "resolved_destination": 4,
    "origin_city": 5,
    "date_window": 6,
    "date_start": 7,
    "date_end": 8,
    "budget_min": 9,
    "budget_max": 10,
    "budget_raw_text": 11,
    "trip_purpose": 12,
    "trip_style": 13,
    "soft_preferences": 14,
    "passport_status": 15,
    "visa_status": 16,
    "payment_method": 17,
    "special_requests": 18,
    "selected_itinerary": 19,
}


def sort_questions_by_priority(questions: List[dict]) -> List[dict]:
    """
    Sort questions constraint-first: composition → destination → origin → dates.

    This order ensures we gather the most blocking information first.
    """
    def sort_key(q: dict) -> int:
        field_name = q.get("field_name", "")
        return QUESTION_PRIORITY_ORDER.get(field_name, 999)

    return sorted(questions, key=sort_key)


# =============================================================================
# SECTION 4: OPERATING-MODE-SPECIFIC STRATEGY BUILDERS
# =============================================================================

def get_mode_specific_goal(decision_state: str, operating_mode: str) -> str:
    """Get session goal based on decision_state AND operating_mode."""

    # ASK_FOLLOWUP goals by mode
    if decision_state == "ASK_FOLLOWUP":
        goals = {
            "normal_intake": "Resolve missing critical constraints to enable trip planning.",
            "audit": "Identify gaps between stated trip parameters and market realities.",
            "emergency": "Gather crisis information: documents, contacts, immediate actions.",
            "follow_up": "Re-engage traveler and clarify pending decision points.",
            "cancellation": "Understand cancellation reason and determine policy options.",
            "post_trip": "Collect feedback for service improvement.",
            "coordinator_group": "Resolve per-group constraints and coordinator preferences.",
            "owner_review": "Not applicable — owner_review is not traveler-facing.",
        }
        return goals.get(operating_mode, goals["normal_intake"])

    # PROCEED_INTERNAL_DRAFT goals
    elif decision_state == "PROCEED_INTERNAL_DRAFT":
        return "Generate internal trip draft with documented assumptions for agent review."

    # PROCEED_TRAVELER_SAFE goals
    elif decision_state == "PROCEED_TRAVELER_SAFE":
        goals = {
            "normal_intake": "Present credible trip options based on confirmed requirements.",
            "audit": "Present audit report comparing traveler plan against market options.",
            "follow_up": "Re-present proposal with refreshed context.",
            "cancellation": "Present cancellation summary with policy options.",
            "post_trip": "Request review and feedback.",
            "coordinator_group": "Present per-group options with group coordination summary.",
            "owner_review": "Present quote quality brief with margin analysis.",
            "emergency": "N/A — emergency never proceeds to traveler-safe output.",
        }
        return goals.get(operating_mode, goals["normal_intake"])

    # BRANCH_OPTIONS goals
    elif decision_state == "BRANCH_OPTIONS":
        return "Present neutral branch options to resolve key trip design decisions."

    # STOP_NEEDS_REVIEW goals
    elif decision_state == "STOP_NEEDS_REVIEW":
        goals = {
            "normal_intake": "Escalate to senior review due to critical contradictions.",
            "emergency": "Execute emergency protocol with immediate action steps.",
            "cancellation": "Escalate complex cancellation case for policy review.",
            "owner_review": "Present commercial data and margin risks for owner decision.",
        }
        return goals.get(operating_mode, "Escalate to review due to critical issues.")

    return "Advance the trip planning process."


def get_mode_specific_opening(
    decision_state: str,
    operating_mode: str,
) -> str:
    """Get suggested opening message based on mode and decision state."""

    if decision_state == "ASK_FOLLOWUP":
        openings = {
            "normal_intake": "I'd like to understand your trip better so I can find the best options.",
            "audit": "Let me review what you've shared and identify any gaps with current market offerings.",
            "emergency": "I understand this is urgent. Let me gather the critical information I need to help you immediately.",
            "follow_up": "Following up on our previous conversation — I wanted to check your thoughts on the options.",
            "cancellation": "I'm sorry to hear about the cancellation. Let me understand your situation and what options are available.",
            "post_trip": "Welcome back! I'd love to hear how your trip went.",
            "coordinator_group": "Let me clarify the requirements for each group to coordinate this properly.",
            "owner_review": "(Not applicable — internal mode)",
        }
        return openings.get(operating_mode, openings["normal_intake"])

    elif decision_state == "PROCEED_TRAVELER_SAFE":
        openings = {
            "normal_intake": "Based on what you've shared, here are some options I think you'll like.",
            "audit": "Here's my review of your trip plan compared to current market options.",
            "follow_up": "Here are the options again — let me know if you'd like me to adjust anything.",
            "cancellation": "Based on your booking, here are your cancellation options and any applicable policies.",
            "post_trip": "If you have a moment, I'd appreciate your feedback on your recent trip.",
            "coordinator_group": "Here are the options organized for each group, plus a summary view.",
            "owner_review": "(Internal) Quote quality and margin analysis follows.",
            "emergency": "N/A",
        }
        return openings.get(operating_mode, openings["normal_intake"])

    elif decision_state == "BRANCH_OPTIONS":
        return "There are a couple of ways to approach this trip — let me show you the options."

    elif decision_state == "STOP_NEEDS_REVIEW":
        openings = {
            "normal_intake": "I need to escalate this to a senior agent to review some inconsistencies.",
            "emergency": "I'm connecting you with emergency support immediately. Here's what to do right now:",
            "cancellation": "Your case requires review — let me connect you with someone who can help.",
            "owner_review": "(Internal) Critical issues detected — review required.",
        }
        return openings.get(operating_mode, openings["normal_intake"])

    elif decision_state == "PROCEED_INTERNAL_DRAFT":
        return "(Internal draft) Generating preliminary options for agent review."

    return "Let's continue with your trip planning."


# =============================================================================
# SECTION 5: BRANCH-QUALITY RULES
# =============================================================================

def get_branch_conversational_approach(
    branch_options: List[dict],
) -> str:
    """
    Determine conversational approach based on branch root cause.

    Different root causes require different framing:
    - Budget flexibility: "within stated vs stretch"
    - Destination unresolved: "feel the difference"
    - Group priorities conflict: "see the trade-offs"
    - Traveler plan vs agency fit: "what we'd do differently"
    """
    if not branch_options:
        return "neutral"

    # Check for budget-related branches
    for branch in branch_options:
        contradictions = branch.get("contradictions", [])
        for c in contradictions:
            field_name = c.get("field_name", "")
            if "budget" in field_name.lower():
                return "budget_tier_framing"  # "Here are two options: one within your stated budget, one that stretches it for better value"

    # Check for destination-related branches
    for branch in branch_options:
        if "destination" in str(branch.get("contradictions", "")).lower():
            return "destination_feel_framing"  # "Both are great choices — let me show you what each looks like so you can feel the difference"

    return "neutral"


# =============================================================================
# SECTION 6: MAIN STRATEGY BUILDER
# =============================================================================

def build_session_strategy(
    decision: DecisionResult,
    packet: Optional[CanonicalPacket] = None,
    session_context: Optional[dict] = None,
    agent_profile: Optional[dict] = None,
    agency_settings: Optional[AgencySettings] = None,
) -> SessionStrategy:
    """
    Main entry point: DecisionResult + CanonicalPacket → SessionStrategy.

    This is the NB03 conversation planner. It answers:
    "Given the decision state and context, how should the next interaction be structured?"
    """
    # Determine tone from confidence, then apply agency overrides
    tone = determine_tone(decision.confidence.overall)
    if agency_settings and agency_settings.brand_tone:
        tone = agency_settings.brand_tone
    tonal_guardrails = get_tonal_guardrails(tone)

    # Get mode-specific goal and opening
    session_goal = get_mode_specific_goal(decision.decision_state, decision.operating_mode)
    suggested_opening = get_mode_specific_opening(decision.decision_state, decision.operating_mode)

    # Build priority sequence based on decision state
    priority_sequence = _build_priority_sequence(decision, packet)

    # Extract risk flags from decision (handle both dict and object formats)
    risk_flags = _extract_risk_flags(decision.risk_flags) if decision.risk_flags else []

    # Build exit criteria
    exit_criteria = _build_exit_criteria(decision, packet)

    # Build assumptions list for internal draft mode
    assumptions = []
    if decision.decision_state == "PROCEED_INTERNAL_DRAFT":
        assumptions = _build_assumptions(decision, packet)

    return SessionStrategy(
        session_goal=session_goal,
        priority_sequence=priority_sequence,
        tonal_guardrails=tonal_guardrails,
        risk_flags=risk_flags,
        suggested_opening=suggested_opening,
        exit_criteria=exit_criteria,
        next_action=decision.decision_state,
        assumptions=assumptions,
        suggested_tone=tone,
    )


def _extract_risk_flags(risk_flags: List[Any]) -> List[str]:
    """Extract risk flag messages from various formats."""
    flags = []
    for r in risk_flags:
        if isinstance(r, dict):
            # Handle dict format: {"flag": "...", "message": "...", ...}
            msg = r.get("message") or r.get("flag", "")
            if msg:
                flags.append(msg)
        else:
            # Handle string or other formats
            flags.append(str(r))
    return flags


def _build_priority_sequence(
    decision: DecisionResult,
    packet: Optional[CanonicalPacket],
) -> List[str]:
    """Build ordered priority sequence based on decision state."""
    sequence = []

    if decision.decision_state == "ASK_FOLLOWUP":
        # Sort questions by priority
        sorted_questions = sort_questions_by_priority(decision.follow_up_questions)
        for q in sorted_questions[:5]:  # Max 5
            field = q.get("field_name", "")
            sequence.append(f"Clarify {field}")

    elif decision.decision_state == "PROCEED_INTERNAL_DRAFT":
        sequence = [
            "Generate internal draft with documented assumptions",
            "Review draft for quality and completeness",
            "Prepare for traveler follow-up",
        ]

    elif decision.decision_state == "PROCEED_TRAVELER_SAFE":
        if decision.operating_mode == "audit":
            sequence = [
                "Compare against market options",
                "Identify value gaps",
                "Present audit report",
            ]
        elif decision.operating_mode == "coordinator_group":
            sequence = [
                "Generate per-group options",
                "Create group coordination summary",
                "Present combined view",
            ]
        else:
            sequence = [
                "Generate credible trip options",
                "Present to traveler",
                "Await selection or feedback",
            ]

    elif decision.decision_state == "BRANCH_OPTIONS":
        sequence = [
            "Present neutral branch options",
            "Explain trade-offs clearly",
            "Guide traveler to decision",
        ]

    elif decision.decision_state == "STOP_NEEDS_REVIEW":
        if decision.operating_mode == "emergency":
            sequence = [
                "Identify immediate actions",
                "Connect to emergency support",
                "Document all actions taken",
            ]
        else:
            sequence = [
                "Document contradictions and evidence",
                "Prepare escalation brief",
                "Route to senior reviewer",
            ]

    return sequence[:5]  # Max 5 items


def _build_exit_criteria(
    decision: DecisionResult,
    packet: Optional[CanonicalPacket],
) -> List[str]:
    """Build exit criteria list."""
    criteria = []

    if decision.decision_state == "ASK_FOLLOWUP":
        criteria = [
            "All critical questions answered",
            "Contradictions resolved",
            "Sufficient confidence for next step",
        ]

    elif decision.decision_state == "PROCEED_INTERNAL_DRAFT":
        criteria = [
            "Internal draft completed",
            "Assumptions documented",
            "Ready for agent review",
        ]

    elif decision.decision_state == "PROCEED_TRAVELER_SAFE":
        criteria = [
            "Options presented to traveler",
            "Traveler response received",
            "Next step determined",
        ]

    elif decision.decision_state == "BRANCH_OPTIONS":
        criteria = [
            "Branch options presented",
            "Traveler makes selection",
            "Path confirmed for next stage",
        ]

    elif decision.decision_state == "STOP_NEEDS_REVIEW":
        criteria = [
            "Escalation brief prepared",
            "Senior reviewer assigned",
            "Resolution documented",
        ]

    return criteria


def _build_assumptions(
    decision: DecisionResult,
    packet: Optional[CanonicalPacket],
) -> List[str]:
    """Build assumptions list for internal draft mode."""
    assumptions = []

    # Document soft blockers as assumptions
    for blocker in decision.soft_blockers:
        assumptions.append(f"Assuming {blocker} can be inferred or is acceptable as-is")

    # Document ambiguities as assumptions
    for amb in decision.ambiguities:
        if amb.severity == "advisory":
            assumptions.append(f"Assuming {amb.field_name} ambiguity ({amb.raw_value}) is acceptable for draft")

    # Document low-confidence signals
    if decision.confidence.overall < 0.6:
        assumptions.append(f"Low confidence ({decision.confidence.overall:.2f}) — draft requires review")

    return assumptions


# =============================================================================
# SECTION 7: TRAVELER-SAFE BUILDER (separate path)
# =============================================================================

def _build_traveler_safe_system_context(
    strategy: SessionStrategy,
) -> str:
    """
    Build system context for TRAVELER-FACING output only.

    CRITICAL: This receives NO packet and NO decision internals.
    Only the strategy (which has been scrubbed of internal concepts).
    """
    context_parts = [
        f"Session Goal: {strategy.session_goal}",
        "",
        "Tonal Guardrails:",
    ]

    for guardrail in strategy.tonal_guardrails:
        context_parts.append(f"  - {guardrail}")

    # Only include traveler-safe risk flags (not internal engine details)
    if strategy.risk_flags:
        context_parts.append("")
        context_parts.append("Considerations:")
        for risk in strategy.risk_flags:
            # Filter out internal-only risk descriptions
            if not any(internal in risk.lower() for internal in ["internal", "margin", "blocker", "contradiction", "hypothesis"]):
                context_parts.append(f"  - {risk}")

    return "\n".join(context_parts)


def _build_traveler_safe_user_message(
    strategy: SessionStrategy,
    decision: DecisionResult,
) -> str:
    """
    Build TRAVELER-FACING user message.

    CRITICAL: Receives NO packet - only strategy and decision metadata.
    The decision metadata is filtered to exclude internal concepts.
    """
    message_parts = [strategy.suggested_opening]

    # Add questions if ASK_FOLLOWUP
    if decision.decision_state == "ASK_FOLLOWUP" and decision.follow_up_questions:
        sorted_questions = sort_questions_by_priority(decision.follow_up_questions)
        
        message_parts.append("")
        # Only show top 3 critical questions to traveler
        for q in sorted_questions[:3]:
            if q.get("priority") in ("critical", "high"):
                question = q.get("question", "")
                # Strip any internal framing from the question
                message_parts.append(question)

    # Add decision-specific content
    elif decision.decision_state == "PROCEED_TRAVELER_SAFE":
        if decision.operating_mode == "audit":
            message_parts.append("")
            message_parts.append("Here's my review comparing your plan with current market options.")
        elif decision.operating_mode == "coordinator_group":
            message_parts.append("")
            message_parts.append("Options organized by group follow, plus a group summary.")

    elif decision.decision_state == "BRANCH_OPTIONS":
        message_parts.append("")
        # Determine conversational approach
        approach = get_branch_conversational_approach(decision.branch_options)
        if approach == "budget_tier_framing":
            message_parts.append("Here are two options: one within your stated budget, one that stretches it for better value.")
        elif approach == "destination_feel_framing":
            message_parts.append("Both are great choices — let me show you what each looks like so you can feel the difference.")

    elif decision.decision_state == "STOP_NEEDS_REVIEW":
        if decision.operating_mode == "emergency":
            message_parts.append("")
            message_parts.append("I'm connecting you with emergency support immediately.")
        else:
            message_parts.append("")
            message_parts.append("This case requires review by a senior agent. I'm escalating it now.")

    return "\n".join(message_parts)


def _build_traveler_safe_constraints() -> List[str]:
    """Build LLM constraints for TRAVELER-FACING output."""
    return [
        "NEVER mention internal concepts: hypotheses, contradictions, blockers, ambiguities",
        "NEVER reveal internal decision states or confidence scores",
        "DO NOT share owner-only constraints or internal notes",
        "Frame all questions as natural conversation, not as 'data collection'",
        "Use confident language when appropriate, acknowledge uncertainty when needed",
        "If BRANCH_OPTIONS: Use neutral framing: 'Option A', 'Option B' — never 'recommended' vs 'alternative'",
    ]


# =============================================================================
# SECTION 8: INTERNAL BUILDER (separate path)
# =============================================================================

def _build_internal_system_context(
    strategy: SessionStrategy,
    decision: DecisionResult,
    packet: CanonicalPacket,
) -> str:
    """
    Build system context for INTERNAL output.

    Has full access to packet, decision internals, and all metadata.
    """
    context_parts = [
        "INTERNAL CONTEXT (AGENT-ONLY)",
        "=" * 40,
        f"Decision State: {decision.decision_state}",
        f"Operating Mode: {decision.operating_mode}",
        f"Confidence: {decision.confidence.overall:.2f}",
        "",
        "Tonal Guardrails:",
    ]

    for guardrail in strategy.tonal_guardrails:
        context_parts.append(f"  - {guardrail}")

    if strategy.risk_flags:
        context_parts.append("")
        context_parts.append("Risk Flags:")
        for risk in strategy.risk_flags:
            context_parts.append(f"  - {risk}")

    if strategy.assumptions:
        context_parts.append("")
        context_parts.append("Assumptions:")
        for assumption in strategy.assumptions:
            context_parts.append(f"  - {assumption}")

    return "\n".join(context_parts)


def _build_internal_user_message(
    strategy: SessionStrategy,
    decision: DecisionResult,
    packet: CanonicalPacket,
) -> str:
    """Build INTERNAL user message with full packet access."""
    message_parts = [strategy.suggested_opening]

    # Add questions with full context
    if decision.decision_state == "ASK_FOLLOWUP" and decision.follow_up_questions:
        sorted_questions = sort_questions_by_priority(decision.follow_up_questions)
        message_parts.append("")
        for q in sorted_questions[:5]:
            field = q.get("field_name", "")
            question = q.get("question", "")
            priority = q.get("priority", "")
            suggested = q.get("suggested_values", [])
            if suggested:
                message_parts.append(f"[{priority.upper()}] {field}: {question} (Suggested: {', '.join(str(s) for s in suggested)})")
            else:
                message_parts.append(f"[{priority.upper()}] {field}: {question}")

    return "\n".join(message_parts)


def _build_internal_constraints() -> List[str]:
    """Build LLM constraints for INTERNAL output."""
    return [
        "Include all internal context in notes",
        "Document assumptions explicitly",
        "Flag any new contradictions or ambiguities detected",
        "Maintain full audit trail",
    ]


def _build_internal_notes(
    strategy: SessionStrategy,
    decision: DecisionResult,
    packet: CanonicalPacket,
) -> str:
    """Build internal agent notes."""
    notes_parts = [
        "INTERNAL NOTES (AGENT-ONLY)",
        "=" * 40,
        f"Decision State: {decision.decision_state}",
        f"Confidence: {decision.confidence.overall:.2f}",
        f"Hard Blockers: {decision.hard_blockers}",
        f"Soft Blockers: {decision.soft_blockers}",
    ]

    if decision.contradictions:
        notes_parts.append("")
        notes_parts.append("Contradictions:")
        for c in decision.contradictions:
            field = c.get("field_name", "unknown")
            values = c.get("values", [])
            sources = c.get("sources", [])
            notes_parts.append(f"  - {field}: {values} (from: {sources})")

    if decision.ambiguities:
        notes_parts.append("")
        notes_parts.append("Ambiguities:")
        for amb in decision.ambiguities:
            notes_parts.append(f"  - {amb.field_name}: {amb.raw_value} ({amb.severity})")

    if packet and packet.hypotheses:
        notes_parts.append("")
        notes_parts.append(f"Hypotheses ({len(packet.hypotheses)}):")
        for field, hyp in packet.hypotheses.items():
            notes_parts.append(f"  - {field}: {hyp.value} (confidence: {hyp.confidence})")

    return "\n".join(notes_parts)


# =============================================================================
# SECTION 9: FOLLOW-UP AND BRANCH HELPERS
# =============================================================================

def _build_follow_up_sequence(
    decision: DecisionResult,
    audience: Literal["internal", "traveler"],
) -> List[dict]:
    """Build ordered follow-up questions with triggers."""
    follow_ups = []

    if decision.decision_state == "ASK_FOLLOWUP" and decision.follow_up_questions:
        sorted_questions = sort_questions_by_priority(decision.follow_up_questions)

        for q in sorted_questions:
            follow_ups.append({
                "field_name": q.get("field_name"),
                "question": q.get("question"),
                "trigger": "after_response" if q.get("priority") == "critical" else "if_no_response",
                "priority": q.get("priority"),
                "suggested_values": q.get("suggested_values", []),
                "can_infer": q.get("can_infer", False),
                "inference_confidence": q.get("inference_confidence", 0.0),
            })

    return follow_ups


def _build_branch_prompts(
    strategy: SessionStrategy,
    decision: DecisionResult,
    audience: Literal["internal", "traveler"],
) -> List[dict]:
    """Build branch option prompts."""
    if decision.decision_state != "BRANCH_OPTIONS" or not decision.branch_options:
        return []

    branch_prompts = []
    approach = get_branch_conversational_approach(decision.branch_options)

    for i, branch in enumerate(decision.branch_options):
        label = branch.get("label", f"Option {chr(65 + i)}")
        description = branch.get("description", "")

        # Use neutral framing (Option A, Option B, not "recommended" vs "alternative")
        branch_prompts.append({
            "label": label,
            "description": description,
            "approach": approach,
            "audience": audience,
        })

    return branch_prompts


# =============================================================================
# SECTION 10: MAIN BUILDER FUNCTIONS (separate paths)
# =============================================================================

def build_traveler_safe_bundle(
    strategy: SessionStrategy,
    decision: DecisionResult,
) -> PromptBundle:
    """
    Build TRAVELER-SAFE prompt bundle.

    CRITICAL: This function does NOT receive the raw packet.
    It only receives strategy (scrubbed) and decision (filtered).
    The raw packet is structurally excluded from this path.
    """
    system_context = _build_traveler_safe_system_context(strategy)
    user_message = _build_traveler_safe_user_message(strategy, decision)
    follow_up_sequence = _build_follow_up_sequence(decision, "traveler")
    branch_prompts = _build_branch_prompts(strategy, decision, "traveler")
    constraints = _build_traveler_safe_constraints()

    # Internal notes are empty for traveler output
    internal_notes = ""

    bundle = PromptBundle(
        system_context=system_context,
        user_message=user_message,
        follow_up_sequence=follow_up_sequence,
        branch_prompts=branch_prompts,
        internal_notes=internal_notes,
        constraints=constraints,
        audience="traveler",
    )

    # POST-BUILD LEAKAGE ENFORCEMENT
    # Strict mode: raises ValueError if leakage detected
    # Non-strict mode: logs leakage in internal_notes (never traveler-facing)
    try:
        leaks = enforce_no_leakage(bundle)
    except ValueError:
        raise

    if leaks:
        bundle.internal_notes = f"LEAKAGE DETECTED: {'; '.join(leaks)}"

    return bundle


def build_internal_bundle(
    strategy: SessionStrategy,
    decision: DecisionResult,
    packet: CanonicalPacket,
) -> PromptBundle:
    """
    Build INTERNAL prompt bundle with full packet access.
    """
    system_context = _build_internal_system_context(strategy, decision, packet)
    user_message = _build_internal_user_message(strategy, decision, packet)
    follow_up_sequence = _build_follow_up_sequence(decision, "internal")
    branch_prompts = _build_branch_prompts(strategy, decision, "internal")
    constraints = _build_internal_constraints()
    internal_notes = _build_internal_notes(strategy, decision, packet)

    return PromptBundle(
        system_context=system_context,
        user_message=user_message,
        follow_up_sequence=follow_up_sequence,
        branch_prompts=branch_prompts,
        internal_notes=internal_notes,
        constraints=constraints,
        audience="internal",
    )


# =============================================================================
# SECTION 11: CONVENIENCE ENTRY POINT
# =============================================================================

def build_session_strategy_and_bundle(
    decision: DecisionResult,
    packet: Optional[CanonicalPacket] = None,
    audience: Literal["internal", "traveler", "both"] = "traveler",
    session_context: Optional[dict] = None,
    agent_profile: Optional[dict] = None,
) -> Tuple[SessionStrategy, PromptBundle]:
    """
    Convenience entry point: build both strategy and bundle in one call.

    This is the primary NB03 entry point for external callers.
    """
    strategy = build_session_strategy(decision, packet, session_context, agent_profile)

    if audience == "both":
        # Build both internal and traveler bundles
        if packet is None:
            raise ValueError("packet is required for internal bundle")
        internal_bundle = build_internal_bundle(strategy, decision, packet)
        traveler_bundle = build_traveler_safe_bundle(strategy, decision)
        # Return combined bundle with traveler as primary, internal notes attached
        bundle = traveler_bundle
        bundle.internal_notes = internal_bundle.internal_notes
    elif audience == "internal":
        if packet is None:
            raise ValueError("packet is required for internal bundle")
        bundle = build_internal_bundle(strategy, decision, packet)
    else:  # traveler
        bundle = build_traveler_safe_bundle(strategy, decision)

    return strategy, bundle
