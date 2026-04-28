"""
intake.orchestration — Single spine entrypoint for the Operator Workbench.

This is the ONLY entrypoint the Streamlit app (or any other caller) should use.
It chains the frozen shared modules in the correct order and returns a
complete, deterministic result bundle.

Contract: Docs/pre_build_corrections_2026-04-15.md (Correction 1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .packet_models import SourceEnvelope
from .extractors import ExtractionPipeline
from .validation import validate_packet, PacketValidationReport
from .decision import run_gap_and_decision, DecisionResult
from .strategy import (
    build_session_strategy,
    build_traveler_safe_bundle,
    build_internal_bundle,
    SessionStrategy,
    PromptBundle,
)
from .safety import (
    sanitize_for_traveler,
    check_no_leakage,
    enforce_no_leakage,
    SanitizedPacketView,
)
from .config.agency_settings import AgencySettings
from .gates import NB01CompletionGate, NB02JudgmentGate, GateVerdict, AutonomyOutcome
from src.fees.calculation import calculate_trip_fees
from src.suitability.integration import assess_activity_suitability
from .frontier_orchestrator import run_frontier_orchestration, FrontierOrchestrationResult
import json


# =============================================================================
# SECTION 0: AUDIT EVENT LOGGING (via AuditStore)
# =============================================================================

def _emit_audit_event(
    trip_id: str,
    stage: str,
    state: str,
    decision_type: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """
    Emit an audit event via TripEventLogger (unified timeline source of truth).
    """
    try:
        from src.analytics.logger import TripEventLogger
        
        description = f"Stage: {stage} | State: {state}"
        if reason:
            description += f" | Reason: {reason}"
        if decision_type:
            description += f" | Decision Type: {decision_type}"
            
        TripEventLogger.log_stage_transition(
            trip_id=trip_id,
            stage=stage,
            actor="system",
            description=description,
            pre_state={"state": "previous"}, # Placeholder for actual packet delta
            post_state={"state": state},
            state=state,
            decision_type=decision_type,
            reason=reason,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger("orchestration.audit")
        logger.warning(f"Failed to emit audit event for trip {trip_id}: {e}")


# =============================================================================
# SECTION 1: SPINE RESULT
# =============================================================================

@dataclass
class SpineResult:
    """
    Complete output of one spine run.

    This is the single return type of run_spine_once().
    All fields are populated from shared spine modules only.
    """
    # Core spine outputs
    packet: Any  # CanonicalPacket
    validation: PacketValidationReport
    decision: DecisionResult
    strategy: SessionStrategy
    internal_bundle: PromptBundle
    traveler_bundle: PromptBundle
    sanitized_view: SanitizedPacketView

    # Safety outputs
    leakage_result: Dict[str, Any]  # { "leaks": [...], "is_safe": bool }

    # Fee calculation
    fees: Optional[Dict[str, Any]] = None

    # D1 Autonomy outcomes (raw verdict preserved, effective gate recorded)
    autonomy_outcome: Optional["AutonomyOutcome"] = None

    # Optional compare-mode output
    assertion_result: Optional[Dict[str, Any]] = None

    # Frontier Autonomic outcomes
    frontier_result: Optional[FrontierOrchestrationResult] = None

    # Metadata
    run_timestamp: str = ""
    early_exit: bool = False
    early_exit_reason: Optional[str] = None
    partial_intake: bool = False


# =============================================================================
# SECTION 2: MAIN ENTRYPOINT
# =============================================================================

def run_spine_once(
    envelopes: List[SourceEnvelope],
    stage: str = "discovery",
    operating_mode: Optional[str] = None,
    feasibility_table: Optional[Dict[str, Any]] = None,
    fixture_expectations: Optional[Dict[str, Any]] = None,
    agency_settings: Optional[AgencySettings] = None,
    stage_callback: Optional[callable] = None,
) -> SpineResult:
    """
    Single spine entrypoint: envelopes → complete result bundle.

    This function chains the frozen shared modules in the correct order:
    1. ExtractionPipeline → CanonicalPacket
    2. validate_packet → PacketValidationReport
    3. run_gap_and_decision → DecisionResult
    4. build_session_strategy → SessionStrategy
    5. build_internal_bundle → PromptBundle (internal)
    6. build_traveler_safe_bundle → PromptBundle (traveler)
    7. sanitize_for_traveler → SanitizedPacketView
    8. check_no_leakage → leakage result
    9. (optional) fixture compare → assertion result

    Args:
        envelopes: One or more SourceEnvelope objects with raw input
        stage: Trip stage (discovery | shortlist | proposal | booking)
        operating_mode: Override operating mode (normal_intake | audit | etc.)
        feasibility_table: Optional budget feasibility data
        fixture_expectations: Optional fixture schema for compare-mode assertions

    Returns:
        SpineResult with all outputs from the spine
    """
    run_timestamp = datetime.now(timezone.utc).isoformat()
    actual_settings = agency_settings or AgencySettings(agency_id="default")

    # --- Phase 1: Extraction ---
    pipeline = ExtractionPipeline()
    packet = pipeline.extract(envelopes)

    # Override stage and operating mode if specified
    packet.stage = stage
    if operating_mode is not None:
        packet.operating_mode = operating_mode

    if stage_callback:
        stage_callback("packet", packet if hasattr(packet, "model_dump") else vars(packet))
    else:
        # Emit intake event to AuditStore
        _emit_audit_event(
            trip_id=packet.packet_id,
            stage="intake",
            state="extracted",
            reason="Extraction pipeline completed"
        )

    # --- Phase 2: Validation ---
    validation = validate_packet(packet, stage=stage)

    # --- Quality Gate: NB01 Completion ---
    nb01_gate = NB01CompletionGate()
    nb01_result = nb01_gate.evaluate(packet, validation)

    if nb01_result.verdict == GateVerdict.ESCALATE:
        # If extraction is structurally broken, we must stop
        from .decision import DecisionResult
        decision = DecisionResult(
            packet_id=packet.packet_id,
            current_stage=stage,
            operating_mode=packet.operating_mode,
            decision_state="STOP_NEEDS_REVIEW",
            hard_blockers=["extraction_quality"],
            rationale={"gate_failure": "NB01_ESCALATE", "reasons": nb01_result.reasons}
        )
        if stage_callback:
            stage_callback("validation", {"status": "ESCALATED", "gate": "NB01", "reasons": nb01_result.reasons})
        else:
            _emit_audit_event(
                trip_id=packet.packet_id,
                stage="packet",
                state="escalated",
                reason="NB01 gate escalation - extraction quality issues"
            )
        return _create_empty_spine_result(packet, validation, decision, run_timestamp)

    if nb01_result.verdict == GateVerdict.DEGRADE:
        # Intake minimum is met but quote-ready fields are incomplete.
        # Save the trip for later enrichment — don't block, don't generate a quote.
        from .decision import DecisionResult
        empty_decision = DecisionResult(
            packet_id=packet.packet_id,
            current_stage=stage,
            operating_mode=packet.operating_mode,
            decision_state="ASK_FOLLOWUP",
            hard_blockers=[],
            soft_blockers=["incomplete_intake"],
            rationale={"gate_degrade": "NB01_DEGRADE", "reasons": nb01_result.reasons},
            follow_up_questions=[
                {"field_name": f, "priority": "medium", "question": f"Please provide {f.replace('_', ' ')} to generate a quote."}
                for f in ("origin_city", "budget_raw_text", "trip_purpose", "party_size")
                if f not in packet.facts
            ],
        )
        if stage_callback:
            stage_callback("validation", {"status": "DEGRADED", "gate": "NB01", "reasons": nb01_result.reasons})
        else:
            _emit_audit_event(
                trip_id=packet.packet_id,
                stage="packet",
                state="degraded",
                reason="NB01 degrade - partial intake saved"
            )
        return _create_partial_intake_result(packet, validation, empty_decision, run_timestamp)

    if stage_callback:
        stage_callback("validation", validation if hasattr(validation, "model_dump") else vars(validation))
    else:
        # Emit packet stage completion to AuditStore
        _emit_audit_event(
            trip_id=packet.packet_id,
            stage="packet",
            state="validated",
            reason="Validation completed successfully"
        )

    # --- Phase 3: Decision ---
    decision = run_gap_and_decision(packet, feasibility_table=feasibility_table, agency_settings=actual_settings)

    # Update packet decision_state from decision result
    packet.decision_state = decision.decision_state

    if stage_callback:
        stage_callback("decision", decision if hasattr(decision, "model_dump") else vars(decision))
    else:
        # Emit decision stage event to AuditStore
        _emit_audit_event(
            trip_id=packet.packet_id,
            stage="decision",
            state=decision.decision_state,
            decision_type="gap_and_decision",
            reason="Decision engine analysis completed"
        )

    # --- Phase 3.5: Suitability Assessment (P0-01) ---
    suitability_flags = assess_activity_suitability(packet)
    packet.suitability_flags = suitability_flags
    
    # Check for CRITICAL flags
    critical_flags = [f for f in suitability_flags if f.severity == "critical"]
    if critical_flags:
        # Override decision_state to require operator review
        packet.decision_state = "suitability_review_required"
        decision.decision_state = "suitability_review_required"
        # Add hard blockers to decision for tracking
        decision.hard_blockers.append("suitability_critical_flags_present")

    # --- Quality Gate: NB02 Judgment (D1 Autonomy Gate) ---
    # This gate enforces the agency autonomy policy WITHOUT mutating decision_state.
    # The raw NB02 verdict is preserved in autonomy_outcome.raw_verdict.
    nb02_gate = NB02JudgmentGate()
    autonomy_outcome = nb02_gate.evaluate(decision, actual_settings)

    # Record gate metadata on the decision rationale (additive, not destructive)
    decision.rationale["autonomy"] = {
        "raw_verdict": autonomy_outcome.raw_verdict,
        "effective_action": autonomy_outcome.effective_action,
        "approval_required": autonomy_outcome.approval_required,
        "rule_source": autonomy_outcome.rule_source,
        "safety_invariant_applied": autonomy_outcome.safety_invariant_applied,
        "mode_override_applied": autonomy_outcome.mode_override_applied,
        "warning_override_applied": autonomy_outcome.warning_override_applied,
        "reasons": autonomy_outcome.reasons,
    }

    # --- Phase 3.2: Frontier Orchestration (Ghost Concierge & Sentiment) ---
    frontier_result = run_frontier_orchestration(packet, decision, agency_settings=actual_settings)
    
    # Record frontier metadata in decision rationale
    decision.rationale["frontier"] = {
        "ghost_triggered": frontier_result.ghost_triggered,
        "ghost_workflow_id": frontier_result.ghost_workflow_id,
        "sentiment_score": frontier_result.sentiment_score,
        "anxiety_alert": frontier_result.anxiety_alert,
        "intelligence_hits": frontier_result.intelligence_hits,
    }

    # --- Phase 4: Strategy ---
    strategy = build_session_strategy(decision, packet, agency_settings=actual_settings)

    if stage_callback:
        stage_callback("strategy", strategy if hasattr(strategy, "model_dump") else vars(strategy))
    else:
        # Emit strategy stage event to AuditStore
        _emit_audit_event(
            trip_id=packet.packet_id,
            stage="strategy",
            state="built",
            reason="Session strategy constructed"
        )

    # --- Phase 5: Internal Bundle ---
    internal_bundle = build_internal_bundle(strategy, decision, packet)

    # --- Phase 6: Traveler-Safe Bundle ---
    # If decision state dropped to INTERNAL_DRAFT or STOP, traveler bundle should be empty/minimal
    traveler_bundle = build_traveler_safe_bundle(strategy, decision)

    # Callback for bundles
    if stage_callback:
        stage_callback("output", {
            "internal_bundle": internal_bundle if hasattr(internal_bundle, "model_dump") else vars(internal_bundle),
            "traveler_bundle": traveler_bundle if hasattr(traveler_bundle, "model_dump") else vars(traveler_bundle),
        })

    # --- Phase 7: Sanitized View ---
    sanitized_view = sanitize_for_traveler(packet)

    # --- Phase 8: Leakage Check ---
    traveler_leaks = check_no_leakage(traveler_bundle)
    sanitized_leaks = _check_sanitized_view_leakage(sanitized_view)
    all_leaks = traveler_leaks + sanitized_leaks

    leakage_result = {
        "leaks": all_leaks,
        "is_safe": len(all_leaks) == 0,
        "traveler_bundle_leaks": traveler_leaks,
        "sanitized_view_leaks": sanitized_leaks,
    }

    if stage_callback:
        stage_callback("safety", leakage_result)
    else:
        # Emit safety stage event to AuditStore
        _emit_audit_event(
            trip_id=packet.packet_id,
            stage="safety",
            state="validated",
            reason=f"Leakage check completed - {'safe' if leakage_result['is_safe'] else 'unsafe'}"
        )

    # --- Phase 9.5: Fee Calculation ---
    fees = calculate_trip_fees(packet, decision)

    # --- Phase 10: Fixture Compare (optional) ---
    assertion_result = None
    if fixture_expectations is not None:
        assertion_result = _compare_against_fixture(
            packet=packet,
            decision=decision,
            traveler_bundle=traveler_bundle,
            leakage_result=leakage_result,
            expectations=fixture_expectations,
        )

    return SpineResult(
        packet=packet,
        validation=validation,
        decision=decision,
        strategy=strategy,
        internal_bundle=internal_bundle,
        traveler_bundle=traveler_bundle,
        sanitized_view=sanitized_view,
        leakage_result=leakage_result,
        fees=fees,
        autonomy_outcome=autonomy_outcome,
        assertion_result=assertion_result,
        frontier_result=frontier_result,
        run_timestamp=run_timestamp,
    )


def _human_block_reason(reasons: list) -> str:
    _BLOCK_COPY = {
        "MVB_MISSING": "Some key trip details are missing",
        "NUMERIC_BUDGET_REQUIRED": "Budget details are needed for this request type",
        "DERIVED_IN_FACTS": "Internal data issue — needs review",
        "FACT_BAD_AUTHORITY": "Internal data issue — needs review",
        "LEGACY_FIELD": "Internal data issue — needs review",
        "Structural validation": "Trip details are incomplete",
    }
    if not reasons:
        return "Could not process this request — some details may be missing or unclear."
    parts = []
    for r in reasons:
        matched = False
        for code, human in _BLOCK_COPY.items():
            if code in r:
                parts.append(human)
                matched = True
                break
        if not matched:
            parts.append(r)
    return " ".join(parts) + ". Please add the missing information and try again."


def _create_empty_spine_result(packet, validation, decision, timestamp):
    """Helper for early exit on gate failure."""
    from .strategy import SessionStrategy, PromptBundle
    from .safety import SanitizedPacketView
    return SpineResult(
        packet=packet,
        validation=validation,
        decision=decision,
        strategy=SessionStrategy(
            session_goal="Gate failure — early exit.",
            priority_sequence=[],
            tonal_guardrails=[],
            risk_flags=[],
            suggested_opening="",
            exit_criteria=[],
            next_action=decision.decision_state,
        ),
        internal_bundle=PromptBundle(
            system_context="",
            user_message="",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes="",
            constraints=[],
        ),
        traveler_bundle=PromptBundle(
            system_context="",
            user_message="",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes="",
            constraints=[],
        ),
        sanitized_view=SanitizedPacketView(
            facts={},
            derived_signals={},
        ),
        leakage_result={"leaks": [], "is_safe": True},
        fees=None,
        autonomy_outcome=None,
        assertion_result=None,
        frontier_result=None,
        run_timestamp=timestamp,
        early_exit=True,
        early_exit_reason=_human_block_reason(nb01_result.reasons),
    )


def _create_partial_intake_result(packet, validation, decision, timestamp):
    """Helper for degraded intake — save trip but block quote generation."""
    from .strategy import SessionStrategy, PromptBundle
    from .safety import SanitizedPacketView
    from .validation import QUOTE_READY, INTAKE_MINIMUM

    missing_quote_fields = [f for f in QUOTE_READY if f not in packet.facts]
    existing_intake_fields = [f for f in INTAKE_MINIMUM if f in packet.facts]

    incomplete_reason = (
        f"Trip saved with {len(existing_intake_fields)}/{len(INTAKE_MINIMUM)} intake fields. "
        f"Missing quote-ready fields: {', '.join(missing_quote_fields)}. "
        f"Add the missing information and reprocess to generate a quote."
    )

    return SpineResult(
        packet=packet,
        validation=validation,
        decision=decision,
        strategy=SessionStrategy(
            session_goal="Partial intake — awaiting enrichment.",
            priority_sequence=[],
            tonal_guardrails=[],
            risk_flags=[],
            suggested_opening="",
            exit_criteria=[],
            next_action="ASK_FOLLOWUP",
        ),
        internal_bundle=PromptBundle(
            system_context="",
            user_message="",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes=incomplete_reason,
            constraints=[],
        ),
        traveler_bundle=PromptBundle(
            system_context="",
            user_message="",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes="",
            constraints=[],
        ),
        sanitized_view=SanitizedPacketView(
            facts={},
            derived_signals={},
        ),
        leakage_result={"leaks": [], "is_safe": True},
        fees=None,
        autonomy_outcome=None,
        assertion_result=None,
        frontier_result=None,
        run_timestamp=timestamp,
        early_exit=False,
        partial_intake=True,
        early_exit_reason=incomplete_reason,
    )


# =============================================================================
# SECTION 3: LEAKAGE HELPERS
# =============================================================================

def _check_sanitized_view_leakage(sanitized_view: SanitizedPacketView) -> List[str]:
    """
    Check the sanitized view for any leakage of internal concepts.

    The sanitized view should contain only traveler-safe facts and derived signals.
    We scan all text values in the sanitized view for forbidden concepts.
    """
    leaks = []
    forbidden_terms = _get_forbidden_terms()

    # Scan facts
    for field_name, slot in sanitized_view.facts.items():
        value = slot.value if hasattr(slot, "value") else slot
        text = _extract_text_from_value(value)
        if text:
            term_found = _scan_for_forbidden_terms(text, forbidden_terms)
            if term_found:
                leaks.append(
                    f"Leakage in sanitized view facts: '{term_found}' in {field_name}"
                )

    # Scan derived signals
    for field_name, slot in sanitized_view.derived_signals.items():
        value = slot.value if hasattr(slot, "value") else slot
        text = _extract_text_from_value(value)
        if text:
            term_found = _scan_for_forbidden_terms(text, forbidden_terms)
            if term_found:
                leaks.append(
                    f"Leakage in sanitized view derived signals: '{term_found}' in {field_name}"
                )

    return leaks


def _get_forbidden_terms() -> set:
    """Get the set of forbidden traveler concepts (from safety module)."""
    from .safety import FORBIDDEN_TRAVELER_CONCEPTS
    return FORBIDDEN_TRAVELER_CONCEPTS


def _extract_text_from_value(value: Any) -> str:
    """Extract text from a slot value for leakage scanning."""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values())
    return str(value)


def _scan_for_forbidden_terms(text: str, forbidden_terms: set) -> Optional[str]:
    """
    Scan text for forbidden terms. Returns the first forbidden term found, or None.
    """
    import re
    text_lower = text.lower()
    for term in forbidden_terms:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, text_lower):
            return term
    return None


# =============================================================================
# SECTION 4: FIXTURE COMPARE
# =============================================================================

def _compare_against_fixture(
    packet: Any,
    decision: DecisionResult,
    traveler_bundle: PromptBundle,
    leakage_result: Dict[str, Any],
    expectations: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare spine outputs against fixture expectations.

    Evaluates each assertion in the fixture's expected.assertions list.

    Returns:
        {
            "passed": bool,
            "assertions": [
                {"type": str, "passed": bool, "message": str},
                ...
            ],
            "summary": str
        }
    """
    assertions = expectations.get("assertions", [])
    results = []
    all_passed = True

    for assertion in assertions:
        a_type = assertion.get("type", "")
        a_field = assertion.get("field", "")
        a_value = assertion.get("value")
        a_message = assertion.get("message", "")

        passed = _evaluate_assertion(a_type, a_field, a_value, packet, decision, traveler_bundle, leakage_result)
        results.append({
            "type": a_type,
            "field": a_field,
            "passed": passed,
            "message": a_message if not passed else "OK",
        })
        if not passed:
            all_passed = False

    # Also check allowed_decision_states
    allowed_states = expectations.get("allowed_decision_states", [])
    if allowed_states:
        state_ok = decision.decision_state in allowed_states
        results.append({
            "type": "decision_state_in",
            "field": "decision.decision_state",
            "passed": state_ok,
            "message": f"Expected one of {allowed_states}, got {decision.decision_state}" if not state_ok else "OK",
        })
        if not state_ok:
            all_passed = False

    # Check required_packet_fields
    required_fields = expectations.get("required_packet_fields", [])
    if required_fields:
        for req_field in required_fields:
            field_ok = req_field in packet.facts
            results.append({
                "type": "field_present",
                "field": req_field,
                "passed": field_ok,
                "message": f"Required field '{req_field}' not found in packet" if not field_ok else "OK",
            })
            if not field_ok:
                all_passed = False

    # Check forbidden_traveler_terms
    forbidden_terms = expectations.get("forbidden_traveler_terms", [])
    if forbidden_terms:
        for term in forbidden_terms:
            term_found = _term_in_bundle(term, traveler_bundle)
            results.append({
                "type": "field_absent",
                "field": f"traveler_bundle:{term}",
                "passed": not term_found,
                "message": f"Forbidden term '{term}' found in traveler bundle" if term_found else "OK",
            })
            if term_found:
                all_passed = False

    # Check leakage_expected
    leakage_expected = expectations.get("leakage_expected", False)
    actual_safe = leakage_result.get("is_safe", True)
    if leakage_expected != (not actual_safe):
        results.append({
            "type": "leakage_detected" if leakage_expected else "no_leakage",
            "field": "leakage_result.is_safe",
            "passed": False,
            "message": f"Expected leakage={leakage_expected}, got is_safe={actual_safe}",
        })
        all_passed = False

    return {
        "passed": all_passed,
        "assertions": results,
        "summary": _build_assertion_summary(all_passed, results),
    }


def _evaluate_assertion(
    a_type: str,
    a_field: str,
    a_value: Any,
    packet: Any,
    decision: DecisionResult,
    traveler_bundle: PromptBundle,
    leakage_result: Dict[str, Any],
) -> bool:
    """Evaluate a single assertion."""
    if a_type == "field_present":
        return a_field in packet.facts

    elif a_type == "field_absent":
        return a_field not in packet.facts

    elif a_type == "field_equals":
        slot = packet.facts.get(a_field)
        if slot is None:
            return False
        return slot.value == a_value

    elif a_type == "decision_state_in":
        if isinstance(a_value, list):
            return decision.decision_state in a_value
        return decision.decision_state == a_value

    elif a_type == "no_leakage":
        return leakage_result.get("is_safe", True)

    elif a_type == "leakage_detected":
        return not leakage_result.get("is_safe", True)

    return False


def _term_in_bundle(term: str, bundle: PromptBundle) -> bool:
    """Check if a term appears anywhere in a PromptBundle."""
    import re
    text = " ".join([
        bundle.user_message or "",
        bundle.system_context or "",
        bundle.internal_notes or "",
    ]).lower()
    pattern = r'\b' + re.escape(term) + r'\b'
    return bool(re.search(pattern, text))


def _build_assertion_summary(all_passed: bool, results: List[Dict]) -> str:
    """Build a human-readable assertion summary."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    if all_passed:
        return f"All {total} assertions passed"
    failed = total - passed
    return f"{passed}/{total} assertions passed ({failed} failed)"
