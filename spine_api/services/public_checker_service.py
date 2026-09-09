from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from fastapi import HTTPException

from spine_api.contract import RunStatusResponse, SpineRunRequest
from spine_api.product_b_events import ProductBEventStore
from spine_api.services.live_checker_service import (
    build_consented_submission,
    collect_raw_text_sources,
    finalize_result_with_live_checker,
)
from src.intake.config.agency_settings import AgencySettingsStore
from src.intake.orchestration import run_spine_once
from src.public_checker.entity_checks import run_entity_checks
from src.public_checker.live_checks import build_live_checker_signals, extract_destination

_DECISION_BASELINE_CATEGORY_COST = ("price", "budget", "cost", "fare", "expensive")
_DECISION_BASELINE_CATEGORY_POLICY = ("visa", "policy", "entry", "insurance", "passport")
_DECISION_BASELINE_CATEGORY_LOGISTICS = ("timing", "transfer", "connection", "delay", "distance", "weather")

# ---------------------------------------------------------------------------
# S-07 (audit RT-04/RT-05) — unauthenticated endpoint resource caps.
#
# /api/public-checker/run is rate-limited (12/min/IP) but runs the full
# pipeline synchronously. PUBLIC_CHECKER_MAX_BYTES / RequestBodySizeMiddleware
# only bound the raw HTTP body — they do not bound per-field text lengths or
# the shape of structured_json. These caps close that gap:
#   - text fields (raw_note / owner_note / itinerary_text) each and combined
#     are capped at PUBLIC_CHECKER_MAX_TEXT_CHARS -> 413;
#   - structured_json nesting depth and total node count are bounded -> 422,
#     so a 100k-deep document can never reach the serializer (RecursionError)
#     or drive superlinear extraction.
# ---------------------------------------------------------------------------

PUBLIC_CHECKER_MAX_TEXT_CHARS = 32_000
PUBLIC_CHECKER_MAX_JSON_DEPTH = 10
PUBLIC_CHECKER_MAX_JSON_NODES = 2_000

_TEXT_INPUT_FIELDS = ("raw_note", "owner_note", "itinerary_text")


def scan_structured_json_limits(
    value: Any,
    *,
    max_depth: int = PUBLIC_CHECKER_MAX_JSON_DEPTH,
    max_nodes: int = PUBLIC_CHECKER_MAX_JSON_NODES,
    max_string_chars: int = PUBLIC_CHECKER_MAX_TEXT_CHARS,
) -> tuple[int, int]:
    """Return (max_depth, node_count) of a JSON-like structure.

    Pure helper. Implemented iteratively (explicit stack) so hostile input can
    never hit Python's recursion limit; the node-count bound also guarantees
    termination on self-referential structures. Raises ValueError as soon as
    any bound (depth, nodes, individual string length) is exceeded.
    """
    max_seen_depth = 0
    nodes = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            raise ValueError(
                f"structured_json exceeds maximum node count ({max_nodes})"
            )
        if depth > max_seen_depth:
            max_seen_depth = depth
        if depth > max_depth:
            raise ValueError(
                f"structured_json exceeds maximum nesting depth ({max_depth})"
            )
        if isinstance(node, str) and len(node) > max_string_chars:
            # P3 closure (review 2026-09-02): depth/node bounds alone allowed a
            # single multi-megabyte string through to the pipeline.
            raise ValueError(
                f"structured_json contains a string longer than {max_string_chars} characters"
            )
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, (list, tuple)):
            stack.extend((child, depth + 1) for child in node)
    return max_seen_depth, nodes


def enforce_public_checker_payload_limits(request_dict: dict[str, Any]) -> None:
    """Reject oversized text (413) or over-complex structured_json (422).

    Must run before any pipeline work on the unauthenticated path.
    """
    combined_chars = 0
    for field in _TEXT_INPUT_FIELDS:
        text = request_dict.get(field)
        if not isinstance(text, str):
            continue
        combined_chars += len(text)
        if len(text) > PUBLIC_CHECKER_MAX_TEXT_CHARS:
            raise HTTPException(
                status_code=413,
                detail=f"{field} exceeds {PUBLIC_CHECKER_MAX_TEXT_CHARS} characters",
            )
    if combined_chars > PUBLIC_CHECKER_MAX_TEXT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Combined text input exceeds {PUBLIC_CHECKER_MAX_TEXT_CHARS} characters",
        )

    structured_json = request_dict.get("structured_json")
    if structured_json is None:
        return
    try:
        scan_structured_json_limits(structured_json)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _derive_product_b_finding_category(finding_text: str) -> str:
    text = finding_text.lower()
    if any(token in text for token in _DECISION_BASELINE_CATEGORY_COST):
        return "cost"
    if any(token in text for token in _DECISION_BASELINE_CATEGORY_POLICY):
        return "policy"
    if any(token in text for token in _DECISION_BASELINE_CATEGORY_LOGISTICS):
        return "logistics"
    return "suitability"


def _safe_log_product_b_event(payload: dict[str, Any], *, logger: logging.Logger) -> None:
    try:
        ProductBEventStore.log_event(payload)
    except Exception as event_err:
        logger.warning("product_b_event_log_failed event=%s error=%s", payload.get("event_name"), event_err)


def build_check_completed_event(
    *,
    session_id: str,
    inquiry_id: str,
    trip_id: Optional[str],
    workspace_id: str,
    input_mode: str,
    finding_count: int,
    hard_blocker_count: int,
    soft_blocker_count: int,
    overall_score: Optional[float],
    execution_ms: float,
) -> dict[str, Any]:
    """Sealed server-side completion event (WOBS P1, Poisoned-Pipe Gate 0).

    Client-fed events are untrusted by construction (RDA_EX03); the funnel's
    completion count must come from here — emitted only after the trip row is
    successfully persisted, never from the browser.
    """
    properties: dict[str, Any] = {
        "input_mode": input_mode,
        "finding_count": int(finding_count),
        "hard_blocker_count": int(hard_blocker_count),
        "soft_blocker_count": int(soft_blocker_count),
        "execution_ms": int(round(execution_ms)),
    }
    if isinstance(overall_score, (int, float)):
        properties["overall_score"] = int(overall_score)
    return ProductBEventStore.build_event(
        event_name="check_completed",
        session_id=session_id,
        inquiry_id=inquiry_id,
        trip_id=trip_id,
        actor_type="system",
        actor_id=None,
        workspace_id=workspace_id,
        channel="api",
        locale=None,
        currency=None,
        properties=properties,
    )


def build_entity_checks_for_submission(
    packet_payload: dict[str, Any],
    raw_text: str,
) -> list:
    """Ghost Hotel Test wiring (WOBS P1): advisory entity-existence findings.

    Bounded to 3 entities per run to cap added synchronous latency (~1s per
    uncached gazetteer lookup). Raises are caught downstream (fail-open).
    """
    city = extract_destination(packet_payload or {}, raw_text)
    return run_entity_checks(raw_text, city=city, max_entities=3)


def run_public_checker_submission(
    request_dict: dict[str, Any],
    *,
    build_envelopes: Callable[[dict[str, Any]], Any],
    load_fixture_expectations: Callable[[Optional[str]], Optional[dict[str, Any]]],
    to_dict: Callable[[Any], Any],
    save_processed_trip: Callable[..., str],
    get_public_checker_agency_id: Callable[[], str],
    logger: logging.Logger,
) -> RunStatusResponse:
    """Run the public checker synchronously and return a result payload."""
    t0 = time.perf_counter()
    # S-07: bound untrusted input before any pipeline work (see constants above).
    enforce_public_checker_payload_limits(request_dict)
    request = SpineRunRequest(**request_dict)
    consented_submission = build_consented_submission(
        request_dict=request_dict,
        retention_consent=request.retention_consent,
    )
    run_id = str(uuid.uuid4())
    steps_completed: list[str] = []

    source_payload: dict[str, Any] = {}
    if isinstance(request.structured_json, dict):
        maybe_source_payload = request.structured_json.get("source_payload")
        if isinstance(maybe_source_payload, dict):
            source_payload = maybe_source_payload

    public_checker_agency_id = get_public_checker_agency_id()
    session_id = str(source_payload.get("session_id") or request_dict.get("session_id") or f"sess_{uuid.uuid4()}")
    inquiry_id = str(source_payload.get("inquiry_id") or request_dict.get("inquiry_id") or run_id)

    input_mode = "freeform_text"
    if source_payload.get("kind") == "file_upload":
        input_mode = "upload"
    elif source_payload.get("kind") == "mixed":
        input_mode = "mixed"

    trip_context = source_payload.get("trip_context") if isinstance(source_payload.get("trip_context"), dict) else {}
    has_destination = bool(trip_context.get("destination_candidates") or trip_context.get("destination") or request_dict.get("destination"))
    has_dates = bool(trip_context.get("date_window") or trip_context.get("travel_window") or request_dict.get("date_window"))
    has_budget_band = bool(trip_context.get("budget_raw_text") or request_dict.get("budget") or request_dict.get("budget_band"))
    has_traveler_profile = bool(trip_context.get("party_size") or request_dict.get("party_size") or request_dict.get("traveler_profile"))

    intake_event = ProductBEventStore.build_event(
        event_name="intake_started",
        session_id=session_id,
        inquiry_id=inquiry_id,
        trip_id=None,
        actor_type="traveler",
        actor_id=None,
        workspace_id=public_checker_agency_id,
        channel="web",
        locale=None,
        currency=None,
        properties={
            "input_mode": input_mode,
            "has_destination": has_destination,
            "has_dates": has_dates,
            "has_budget_band": has_budget_band,
            "has_traveler_profile": has_traveler_profile,
        },
    )
    _safe_log_product_b_event(intake_event, logger=logger)

    try:
        envelopes = build_envelopes(request.model_dump(exclude_none=True))
        fixture_expectations = load_fixture_expectations(request.scenario_id)
        agency_settings = AgencySettingsStore.load(public_checker_agency_id)
        stage_started_at: dict[str, float] = {}
        current_stage: Optional[str] = None

        def _finalize_result(result: Any) -> None:
            raw_text = collect_raw_text_sources(
                raw_note=request.raw_note,
                owner_note=request.owner_note,
                itinerary_text=request.itinerary_text,
                structured_json=request.structured_json,
            )
            finalize_result_with_live_checker(
                result=result,
                raw_text=raw_text,
                build_live_checker_signals_fn=build_live_checker_signals,
                to_dict=to_dict,
                build_entity_checks_fn=build_entity_checks_for_submission,
            )

        def _stage_checkpoint(stage_name: str, data: Any) -> None:
            nonlocal current_stage
            event = "completed"
            payload_data = data

            if isinstance(data, dict) and isinstance(data.get("event"), str):
                event = data.get("event", "completed")
                payload_data = data.get("data")

            if event == "entered":
                current_stage = stage_name
                stage_started_at[stage_name] = time.perf_counter()
                return

            if event == "completed":
                if stage_name not in steps_completed:
                    steps_completed.append(stage_name)
            current_stage = stage_name
            _ = payload_data

        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_expectations=fixture_expectations,
            agency_settings=agency_settings,
            stage_callback=_stage_checkpoint,
            strict_leakage=request.strict_leakage,
            result_finalizer=_finalize_result,
        )

        execution_ms = (time.perf_counter() - t0) * 1000
        packet_payload = to_dict(result.packet) if hasattr(result, "packet") else {}
        validation_payload = to_dict(result.validation) if hasattr(result, "validation") else {}
        decision_payload = to_dict(result.decision) if hasattr(result, "decision") else {}

        result_state = "completed"
        error_type: Optional[str] = None
        error_message: Optional[str] = None
        block_reason: Optional[str] = None

        if getattr(result, "early_exit", False):
            result_state = "blocked"
            block_reason = result.early_exit_reason or "Pipeline blocked"

        if hasattr(result, "validation") and result.validation and not getattr(result.validation, "is_valid", True):
            result_state = "blocked"
            block_reason = "Validation failed (defense-in-depth)"

        if getattr(result, "partial_intake", False):
            trip_status = "incomplete"
        elif result_state == "blocked":
            trip_status = "blocked"
        else:
            trip_status = "new"

        trip_id_saved = save_processed_trip(
            {
                "run_id": run_id,
                "packet": packet_payload if packet_payload else None,
                "validation": validation_payload if validation_payload else None,
                "decision": decision_payload if decision_payload else None,
                "strategy": to_dict(result.strategy) if hasattr(result, "strategy") else None,
                "meta": {
                    "stage": request.stage,
                    "operating_mode": request.operating_mode,
                    "fixture_id": request.scenario_id,
                    "execution_ms": round(execution_ms, 2),
                    "submission": consented_submission,
                    "retention_consent": request.retention_consent,
                    "session_id": session_id,
                    "inquiry_id": inquiry_id,
                },
            },
            source="public_checker",
            agency_id=public_checker_agency_id,
            user_id=None,
            trip_status=trip_status,
        )

        primary_hard_blockers = [str(item) for item in decision_payload.get("hard_blockers") or [] if str(item).strip()]
        primary_soft_blockers = [str(item) for item in decision_payload.get("soft_blockers") or [] if str(item).strip()]
        first_finding_text = ""
        finding_severity = "optional"
        if primary_hard_blockers:
            first_finding_text = primary_hard_blockers[0]
            finding_severity = "must_fix"
        elif primary_soft_blockers:
            first_finding_text = primary_soft_blockers[0]
            finding_severity = "should_review"

        if first_finding_text:
            confidence_score_raw = validation_payload.get("overall_score")
            if isinstance(confidence_score_raw, (int, float)):
                confidence_score = max(0.0, min(1.0, float(confidence_score_raw) / 100.0))
            else:
                confidence_score = 0.5

            first_finding_event = ProductBEventStore.build_event(
                event_name="first_credible_finding_shown",
                session_id=session_id,
                inquiry_id=inquiry_id,
                trip_id=trip_id_saved,
                actor_type="system",
                actor_id=None,
                workspace_id=public_checker_agency_id,
                channel="api",
                locale=None,
                currency=None,
                properties={
                    "time_from_intake_start_ms": int(round(execution_ms)),
                    "finding_id": f"fnd_{abs(hash(first_finding_text)) % 10_000_000}",
                    "finding_category": _derive_product_b_finding_category(first_finding_text),
                    "severity": finding_severity,
                    "confidence_score": round(confidence_score, 3),
                    "evidence_present": True,
                },
            )
            _safe_log_product_b_event(first_finding_event, logger=logger)

        finding_count = len(primary_hard_blockers) + len(primary_soft_blockers)
        check_completed_event = build_check_completed_event(
            session_id=session_id,
            inquiry_id=inquiry_id,
            trip_id=trip_id_saved,
            workspace_id=public_checker_agency_id,
            input_mode=input_mode,
            finding_count=finding_count,
            hard_blocker_count=len(primary_hard_blockers),
            soft_blocker_count=len(primary_soft_blockers),
            overall_score=validation_payload.get("overall_score")
            if isinstance(validation_payload.get("overall_score"), (int, float))
            else None,
            execution_ms=execution_ms,
        )
        _safe_log_product_b_event(check_completed_event, logger=logger)

        now_iso = datetime.now(timezone.utc).isoformat()

        decision_state_value = decision_payload.get("decision_state")

        return RunStatusResponse(
            run_id=run_id,
            state=result_state,
            trip_id=trip_id_saved,
            stage=request.stage,
            operating_mode=request.operating_mode,
            agency_id=public_checker_agency_id,
            created_at=now_iso,
            started_at=now_iso,
            completed_at=now_iso,
            total_ms=round(execution_ms, 2),
            steps_completed=steps_completed,
            events=[],
            error_type=error_type,
            error_message=error_message,
            stage_at_failure=None,
            block_reason=block_reason,
            validation=validation_payload if validation_payload else None,
            packet=packet_payload if packet_payload else None,
            decision_state=str(decision_state_value) if decision_state_value else None,
            follow_up_questions=list(result.follow_up_questions) if hasattr(result, "follow_up_questions") else [],
            hard_blockers=list(decision_payload.get("hard_blockers") or []),
            soft_blockers=list(decision_payload.get("soft_blockers") or []),
        )
    except Exception as exc:
        logger.exception("Public checker submission failed")
        raise HTTPException(status_code=500, detail="Public checker submission failed") from exc
