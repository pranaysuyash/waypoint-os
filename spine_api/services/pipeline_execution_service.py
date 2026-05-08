from __future__ import annotations

import time
from typing import Any, Optional, Callable, List

from spine_api.contract import RunMeta, SpineRunRequest
from spine_api.services.live_checker_service import (
    apply_live_checker_adjustments,
    build_consented_submission,
    collect_raw_text_sources,
)


def _update_draft_for_terminal_state(
    run_id: str,
    run_state: str,
    logger: Any,
    run_ledger: Any,
    draft_store: Any,
    trip_id: Optional[str] = None,
    snapshot: Optional[dict] = None,
) -> None:
    """Update the draft linked to this run with its final state.

    Looks up draft_id from RunLedger meta and calls DraftStore.update_run_state.
    No-ops if no draft is linked.
    """
    _ = trip_id
    try:
        meta = run_ledger.get_meta(run_id)
        if not meta:
            return
        draft_id = meta.get("draft_id")
        if not draft_id:
            return
        draft_store.update_run_state(
            draft_id=draft_id,
            run_id=run_id,
            run_state=run_state,
            run_snapshot=snapshot,
        )
    except Exception as exc:
        logger.debug("Draft state update skipped for run %s: %s", run_id, exc)


def execute_spine_pipeline(
    run_id: str,
    request_dict: dict[str, Any],
    agency_id: str,
    user_id: str,
    *,
    build_envelopes: Callable[[dict[str, Any]], Any],
    load_fixture_expectations: Callable[[Optional[str]], Optional[dict[str, Any]]],
    to_dict: Callable[[Any], Any],
    close_inherited_lock_fds: Callable[[], None],
    save_processed_trip: Callable[..., str],
    trip_store: Any,
    audit_store: Any,
    run_spine_once_fn: Callable[..., Any],
    logger: Any,
    otel_tracer: Any,
    run_ledger: Any,
    run_state_running: Any,
    draft_store: Any,
    agency_settings_store: Any,
    set_strict_mode_fn: Callable[[bool], None],
    build_live_checker_signals_fn: Callable[[dict[str, Any], str], Any],
    emit_run_started_fn: Callable[..., None],
    emit_run_completed_fn: Callable[..., None],
    emit_run_failed_fn: Callable[..., None],
    emit_run_blocked_fn: Callable[..., None],
    emit_stage_entered_fn: Callable[..., None],
    emit_stage_completed_fn: Callable[..., None],
    target_trip_id: Optional[str] = None,
    audit_event_type: str = "trip_created",
    existing_trip_status: Optional[str] = None,
) -> None:
    """Run the spine pipeline in the background and persist status/events."""
    t0 = time.perf_counter()
    current_stage: Optional[str] = None

    def _checkpoint_result_steps(run_id: str, result: Any) -> None:
        """Persist core result artifacts for observability even on partial/early exits."""
        try:
            existing = run_ledger.get_all_steps(run_id)
            if "packet" not in existing and hasattr(result, "packet"):
                run_ledger.save_step(run_id, "packet", to_dict(result.packet))
            if "validation" not in existing and hasattr(result, "validation"):
                run_ledger.save_step(run_id, "validation", to_dict(result.validation))
            if "decision" not in existing and hasattr(result, "decision"):
                run_ledger.save_step(run_id, "decision", to_dict(result.decision))
            if "strategy" not in existing and hasattr(result, "strategy"):
                run_ledger.save_step(run_id, "strategy", to_dict(result.strategy))
        except Exception as e:
            logger.error("Wave A: result step checkpointing failed for run %s: %s", run_id, e)

    try:
        # Close inherited lock file descriptors to prevent fork-deadlock on macOS.
        # When multiprocessing forks, the child inherits all parent fds including
        # fcntl.flock-held files. Closing them here ensures the child can acquire
        # fresh locks via the file_lock context manager.
        close_inherited_lock_fds()

        request = SpineRunRequest(**request_dict)
        consented_submission = build_consented_submission(
            request_dict=request_dict,
            retention_consent=request.retention_consent,
        )

        if request.strict_leakage:
            set_strict_mode_fn(True)

        meta = RunMeta(
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_id=request.scenario_id,
            execution_ms=0.0,
        )

        run_ledger.set_state(run_id, run_state_running)

        # Update linked draft status if draft_id was provided
        draft_id = request_dict.get("draft_id")
        if draft_id:
            try:
                draft_store.update_run_state(draft_id, run_id, "running")
                audit_store.log_event("draft_process_started", user_id, {
                    "draft_id": draft_id,
                    "run_id": run_id,
                    "stage": request.stage,
                    "operating_mode": request.operating_mode,
                    "scenario_id": request.scenario_id,
                })
            except Exception as draft_err:
                logger.warning("Failed to update draft state for draft_id=%s: %s", draft_id, draft_err)

        emit_run_started_fn(
            run_id=run_id,
            trip_id=None,
            stage=request.stage,
            operating_mode=request.operating_mode,
        )

        envelopes = build_envelopes(request.model_dump(exclude_none=True))
        fixture_expectations = load_fixture_expectations(request.scenario_id)
        agency_settings = agency_settings_store.load(agency_id)
        stage_started_at: dict[str, float] = {}

        def _stage_checkpoint(stage_name: str, data: Any) -> None:
            """Emit lifecycle-aware stage events and checkpoint data."""
            nonlocal current_stage
            try:
                event = "completed"
                payload_data = data
                error_message: Optional[str] = None

                if isinstance(data, dict) and isinstance(data.get("event"), str):
                    event = data.get("event", "completed")
                    payload_data = data.get("data")
                    error_message = data.get("error")

                if event == "entered":
                    current_stage = stage_name
                    stage_started_at[stage_name] = time.perf_counter()
                    emit_stage_entered_fn(run_id, stage_name, trip_id=None)
                    return

                if event == "failed":
                    current_stage = stage_name
                    run_ledger.save_step(run_id, f"{stage_name}_failed", {
                        "stage_name": stage_name,
                        "error": error_message or "stage_failed",
                    })
                    return

                stage_start = stage_started_at.get(stage_name)
                if stage_start is None:
                    current_stage = stage_name
                    emit_stage_entered_fn(run_id, stage_name, trip_id=None)
                    stage_start = time.perf_counter()
                    stage_started_at[stage_name] = stage_start

                val = to_dict(payload_data) if payload_data is not None else None
                if val is not None:
                    run_ledger.save_step(run_id, stage_name, val)

                emit_stage_completed_fn(
                    run_id,
                    stage_name,
                    execution_ms=(time.perf_counter() - stage_start) * 1000,
                    trip_id=None,
                )
                current_stage = stage_name
            except Exception as e:
                logger.error("Wave A: mid-run checkpoint failed stage=%s error=%s", stage_name, e)

        with otel_tracer.start_as_current_span("spine_pipeline") as pipeline_span:
            pipeline_span.set_attribute("stage", request.stage)
            pipeline_span.set_attribute("run_id", run_id)
            pipeline_span.set_attribute("agency_id", agency_id)
            pipeline_span.set_attribute("user_id", user_id)

        result = run_spine_once_fn(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_expectations=fixture_expectations,
            agency_settings=agency_settings,
            stage_callback=_stage_checkpoint,
        )

        execution_ms = (time.perf_counter() - t0) * 1000
        meta.execution_ms = round(execution_ms, 2)
        pipeline_span.set_attribute("execution_ms", round(execution_ms, 2))
        if hasattr(result, "packet"):
            pipeline_span.set_attribute("trip_id", result.packet.packet_id if hasattr(result.packet, "packet_id") else "")

        raw_text = collect_raw_text_sources(
            raw_note=request.raw_note,
            owner_note=request.owner_note,
            itinerary_text=request.itinerary_text,
            structured_json=request.structured_json,
        )

        packet_payload = to_dict(result.packet) if hasattr(result, "packet") else {}
        live_checker = build_live_checker_signals_fn(packet_payload or {}, raw_text)
        if live_checker:
            validation_payload = to_dict(result.validation) if hasattr(result, "validation") else {}
            decision_payload = to_dict(result.decision) if hasattr(result, "decision") else {}
            packet_payload, validation_payload, decision_payload = apply_live_checker_adjustments(
                packet_payload=packet_payload,
                validation_payload=validation_payload,
                decision_payload=decision_payload,
                live_checker=live_checker,
            )
            result.validation = validation_payload
            result.decision = decision_payload
            result.packet = packet_payload

        _checkpoint_result_steps(run_id, result)

        if getattr(result, "early_exit", False):
            logger.warning(
                "spine_run early_exit run_id=%s reason=%s execution_ms=%.2f",
                run_id,
                result.early_exit_reason,
                execution_ms,
            )
            run_ledger.save_step(run_id, "blocked_result", {
                "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                "early_exit_reason": result.early_exit_reason,
                "meta": meta.model_dump(),
            })
            block_reason = result.early_exit_reason or "Pipeline blocked"
            run_ledger.block(run_id, block_reason=block_reason)
            _update_draft_for_terminal_state(run_id, "blocked", logger, run_ledger, draft_store, snapshot={"block_reason": block_reason, "stage_at_block": current_stage})
            emit_run_blocked_fn(
                run_id=run_id,
                block_reason=block_reason,
                stage_at_block=current_stage,
                trip_id=None,
            )
            return

        if getattr(result, "partial_intake", False):
            logger.info(
                "spine_run partial_intake run_id=%s reason=%s execution_ms=%.2f",
                run_id,
                result.early_exit_reason,
                execution_ms,
            )
            # Save the partial trip with incomplete status
            # (packet is valid but missing quote-ready fields)
            trip_id_saved = save_processed_trip(
                {
                    "run_id": run_id,
                    "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                    "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                    "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                    "strategy": to_dict(result.strategy) if hasattr(result, "strategy") else None,
                    "plan_candidate": to_dict(result.plan_candidate) if hasattr(result, "plan_candidate") and result.plan_candidate else None,
                    "traveler_bundle": to_dict(result.traveler_bundle) if hasattr(result, "traveler_bundle") and result.traveler_bundle else None,
                    "internal_bundle": to_dict(result.internal_bundle) if hasattr(result, "internal_bundle") and result.internal_bundle else None,
                    "safety": to_dict(result.safety) if hasattr(result, "safety") else None,
                    "fees": to_dict(result.fees) if hasattr(result, "fees") and result.fees else None,
                    "frontier_result": to_dict(result.frontier_result) if hasattr(result, "frontier_result") and result.frontier_result else None,
                    "meta": {
                        **meta.model_dump(),
                        "submission": consented_submission,
                        "retention_consent": request.retention_consent,
                    },
                },
                source="spine_api",
                agency_id=agency_id,
                user_id=user_id,
                trip_status=existing_trip_status or "incomplete",
                preserve_trip_id=target_trip_id,
                audit_event_type=audit_event_type,
            )
            if not trip_id_saved:
                raise RuntimeError("save_processed_trip returned no trip_id for partial intake")
            run_ledger.update_meta(run_id, trip_id=trip_id_saved)
            logger.info("Partial trip saved: %s", trip_id_saved)

            run_ledger.complete(run_id, total_ms=execution_ms)
            _update_draft_for_terminal_state(run_id, "completed", logger, run_ledger, draft_store, trip_id=trip_id_saved, snapshot={"early_exit_reason": "partial_intake", "trip_id": trip_id_saved})
            emit_run_completed_fn(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
            return

        if hasattr(result, "validation") and result.validation and not getattr(result.validation, "is_valid", True):
            logger.warning(
                "spine_run validation_invalid run_id=%s execution_ms=%.2f",
                run_id,
                execution_ms,
            )
            run_ledger.save_step(run_id, "blocked_result", {
                "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                "early_exit_reason": "validation_invalid",
                "meta": meta.model_dump(),
            })
            run_ledger.block(run_id, block_reason="Validation failed (defense-in-depth)")
            _update_draft_for_terminal_state(run_id, "blocked", logger, run_ledger, draft_store, snapshot={"block_reason": "Validation failed (defense-in-depth)", "stage_at_block": current_stage})
            emit_run_blocked_fn(
                run_id=run_id,
                block_reason="Validation failed (defense-in-depth)",
                stage_at_block=current_stage,
                trip_id=None,
            )
            return

        logger.info(
            "spine_run ok=True run_id=%s stage=%s mode=%s scenario_id=%s execution_ms=%.2f agency_id=%s",
            run_id,
            request.stage,
            request.operating_mode,
            request.scenario_id,
            execution_ms,
            agency_id,
        )

        # Save the trip to persistence scoped to the user's agency
        trip_id_saved = save_processed_trip(
            {
                "run_id": run_id,
                "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                "strategy": to_dict(result.strategy) if hasattr(result, "strategy") else None,
                "plan_candidate": to_dict(result.plan_candidate) if hasattr(result, "plan_candidate") and result.plan_candidate else None,
                "traveler_bundle": to_dict(result.traveler_bundle) if hasattr(result, "traveler_bundle") and result.traveler_bundle else None,
                "internal_bundle": to_dict(result.internal_bundle) if hasattr(result, "internal_bundle") and result.internal_bundle else None,
                "safety": to_dict(result.safety) if hasattr(result, "safety") else None,
                "fees": to_dict(result.fees) if hasattr(result, "fees") and result.fees else None,
                "frontier_result": to_dict(result.frontier_result) if hasattr(result, "frontier_result") and result.frontier_result else None,
                "meta": {
                    **meta.model_dump(),
                    "submission": consented_submission,
                    "retention_consent": request.retention_consent,
                },
            },
            source="spine_api",
            agency_id=agency_id,
            user_id=user_id,
            trip_status=existing_trip_status or "new",
            preserve_trip_id=target_trip_id,
            audit_event_type=audit_event_type,
        )
        if not trip_id_saved:
            raise RuntimeError("save_processed_trip returned no trip_id")
        run_ledger.update_meta(run_id, trip_id=trip_id_saved)
        logger.info("Trip saved: %s", trip_id_saved)

        # Wave 10: Feedback-Driven Recovery Trigger
        trip_post = trip_store.get_trip(trip_id_saved)
        if trip_post and trip_post.get("analytics", {}).get("feedback_reopen"):
            from src.analytics.review import trigger_feedback_recovery
            trigger_feedback_recovery(trip_id_saved, reason=trip_post["analytics"].get("review_reason"))
            logger.info("Feedback recovery triggered for trip: %s", trip_id_saved)

        # Compute leakage results first — used both by checkpoint and response
        all_leaks: List[str] = (
            result.leakage_result.get("leaks", [])
            if hasattr(result, "leakage_result") and result.leakage_result
            else []
        )
        is_safe: bool = (
            result.leakage_result.get("is_safe", len(all_leaks) == 0)
            if hasattr(result, "leakage_result") and result.leakage_result
            else len(all_leaks) == 0
        )
        _ = is_safe

        # Wave A: complete the ledger and emit terminal event
        # (All pipeline steps were already checkpointed incrementally via
        # stage_callback inside run_spine_once above.)
        try:
            run_ledger.complete(run_id, total_ms=execution_ms)
            _update_draft_for_terminal_state(run_id, "completed", logger, run_ledger, draft_store, trip_id=trip_id_saved, snapshot={"trip_id": trip_id_saved})
            emit_run_completed_fn(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
        except Exception as e:
            logger.error("Wave A: ledger complete failed for run %s: %s", run_id, e)

    except ValueError as e:
        # Strict leakage violation — traveler_bundle suppressed, ok=False
        execution_ms = (time.perf_counter() - t0) * 1000
        meta.execution_ms = round(execution_ms, 2)

        error_message = str(e)
        logger.warning(
            "spine_run ok=False run_id=%s strict_leakage=True error=%s execution_ms=%.2f",
            run_id,
            error_message,
            execution_ms,
        )

        # Wave A: mark as BLOCKED (distinct from FAILED)
        try:
            run_ledger.block(run_id, block_reason=error_message)
            _update_draft_for_terminal_state(run_id, "blocked", logger, run_ledger, draft_store, snapshot={"block_reason": error_message, "stage_at_block": current_stage})
            emit_run_blocked_fn(
                run_id=run_id,
                block_reason=error_message,
                stage_at_block=current_stage,
                trip_id=None,
            )
        except Exception as ledger_err:
            logger.error("Wave A: block ledger failed for run %s: %s", run_id, ledger_err)

    except Exception as e:
        execution_ms = (time.perf_counter() - t0) * 1000
        logger.error(
            "spine_run error run_id=%s type=%s error=%s execution_ms=%.2f",
            run_id,
            type(e).__name__,
            str(e),
            execution_ms,
        )

        # Wave A: mark as FAILED
        try:
            run_ledger.fail(run_id, error_type=type(e).__name__, error_message=str(e))
            _update_draft_for_terminal_state(run_id, "failed", logger, run_ledger, draft_store, snapshot={"error_type": type(e).__name__, "error_message": str(e), "stage_at_failure": current_stage})
            emit_run_failed_fn(
                run_id=run_id,
                error_type=type(e).__name__,
                error_message=str(e),
                stage_at_failure=current_stage,
                trip_id=None,
            )
        except Exception as ledger_err:
            logger.error("Wave A: fail ledger failed for run %s: %s", run_id, ledger_err)

    finally:
        # Reset strict mode after every request to prevent state leaking to the next
        set_strict_mode_fn(False)
