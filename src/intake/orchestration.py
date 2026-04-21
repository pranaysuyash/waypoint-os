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
from typing import Any, Dict, List, Optional

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
from .gates import NB01CompletionGate, NB02JudgmentGate, GateVerdict


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

    # Optional compare-mode output
    assertion_result: Optional[Dict[str, Any]] = None

    # Metadata
    run_timestamp: str = ""


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
        return _create_empty_spine_result(packet, validation, decision, run_timestamp)

    # --- Phase 3: Decision ---
    decision = run_gap_and_decision(packet, feasibility_table=feasibility_table, agency_settings=actual_settings)

    # Update packet decision_state from decision result
    packet.decision_state = decision.decision_state

    # --- Quality Gate: NB02 Judgment ---
    # This gate enforces the agency's autonomy policy
    nb02_gate = NB02JudgmentGate()
    nb02_result = nb02_gate.evaluate(decision, actual_settings)

    if nb02_result.verdict == GateVerdict.ESCALATE:
        decision.decision_state = "STOP_NEEDS_REVIEW"
        decision.hard_blockers.append("confidence_threshold")
        decision.rationale["gate_failure"] = "NB02_ESCALATE"
        decision.rationale["gate_reasons"] = nb02_result.reasons
        packet.decision_state = "STOP_NEEDS_REVIEW"
    elif nb02_result.verdict == GateVerdict.DEGRADE:
        if decision.decision_state == "PROCEED_TRAVELER_SAFE":
            decision.decision_state = "PROCEED_INTERNAL_DRAFT"
            decision.rationale["gate_degraded"] = True
            decision.rationale["gate_reasons"] = nb02_result.reasons
            packet.decision_state = "PROCEED_INTERNAL_DRAFT"

    # --- Phase 4: Strategy ---
    strategy = build_session_strategy(decision, packet, agency_settings=actual_settings)

    # --- Phase 5: Internal Bundle ---
    internal_bundle = build_internal_bundle(strategy, decision, packet)

    # --- Phase 6: Traveler-Safe Bundle ---
    # If decision state dropped to INTERNAL_DRAFT or STOP, traveler bundle should be empty/minimal
    traveler_bundle = build_traveler_safe_bundle(strategy, decision)

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

    # --- Phase 9: Fixture Compare (optional) ---
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
        assertion_result=assertion_result,
        run_timestamp=run_timestamp,
    )


def _create_empty_spine_result(packet, validation, decision, timestamp):
    """Helper for early exit on gate failure."""
    from .strategy import SessionStrategy, PromptBundle
    from .safety import SanitizedPacketView
    return SpineResult(
        packet=packet,
        validation=validation,
        decision=decision,
        strategy=SessionStrategy(decision_state=decision.decision_state),
        internal_bundle=PromptBundle(),
        traveler_bundle=PromptBundle(),
        sanitized_view=SanitizedPacketView(packet_id=packet.packet_id),
        leakage_result={"leaks": [], "is_safe": True},
        run_timestamp=timestamp
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
