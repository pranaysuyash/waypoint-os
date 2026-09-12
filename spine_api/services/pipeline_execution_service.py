from __future__ import annotations

import time
from typing import Any, Optional, Callable, List

from spine_api.contract import RunMeta, SpineRunRequest
from spine_api.failure_taxonomy import (
    FailureClass,
    classify_failure,
)
from spine_api.services.live_checker_service import (
    build_consented_submission,
    collect_raw_text_sources,
    finalize_result_with_live_checker,
)
from src.intake.safety import StrictLeakageViolation


class LeadPersistenceError(RuntimeError):
    """PA-27: the ESCALATE lead could not be persisted after retry.

    Raised after the run has already been marked FAILED with
    ``failure_class="state"`` so the operator sees a loud, classified failure
    instead of a silently dropped customer inquiry.
    """


def _complete_ledger_reconciled(
    run_ledger: Any,
    run_id: str,
    execution_ms: float,
    logger: Any,
) -> None:
    """Complete a run, reconciling the sweep race (PA-17).

    The stale-run sweep can mark a live run FAILED while its pipeline thread
    is still working. If the trip then saves successfully, a plain
    ``complete()`` raises on the illegal failed→completed transition and the
    ledger would say FAILED forever while the trip exists. This helper:
      1. completes normally when the ledger is still running (common case);
      2. when the ledger already says failed (sweep raced a live thread),
         reconciles via RunLedger.complete_after_timeout() so the honest
         terminal state is COMPLETED with ``recovered_after_timeout: true``;
      3. re-raises any other completion failure so the existing isolation
         (logger.error in the caller) still applies.
    """
    meta_now = None
    try:
        meta_now = run_ledger.get_meta(run_id)
    except Exception:
        meta_now = None

    if isinstance(meta_now, dict) and meta_now.get("state") == "failed":
        logger.warning(
            "PA-17 sweep race detected for run %s: ledger says failed but the "
            "pipeline completed and the trip saved — reconciling as "
            "completed_after_timeout",
            run_id,
        )
        run_ledger.complete_after_timeout(run_id, total_ms=execution_ms)
        return

    run_ledger.complete(run_id, total_ms=execution_ms)
    _record_terminal_metrics("completed")
    _finalize_run_idempotency(run_ledger, run_id, "completed", logger)


def _record_terminal_metrics(outcome: str, failure_class: Any = None) -> None:
    """Increment the real /metrics run counters (PA-10).

    Observability side-effect only: must never break the pipeline.
    """
    try:
        from spine_api import metrics_registry

        metrics_registry.inc_run_outcome(outcome)
        if outcome == "failed":
            metrics_registry.inc_run_failure(
                getattr(failure_class, "value", None) or str(failure_class or "unclassified")
            )
    except Exception:
        pass


def _finalize_run_idempotency(
    run_ledger: Any,
    run_id: str,
    outcome: str,
    logger: Any,
) -> None:
    """Finalize the durable Idempotency-Key record at terminal state (PA-13).

    Reads the key + fencing token stashed into run meta at submission time
    (spine_api/server.py POST /run) and closes the registry record so replays
    return the original run_id instead of aging out via TTL. Blocked runs are
    terminal and replayable; failed runs mark_failed so the same key may retry.
    """
    try:
        meta = run_ledger.get_meta(run_id) or {}
        idem_key = meta.get("idempotency_key")
        if not idem_key:
            return
        from src.agents.idempotency import IdempotencyRegistry

        registry = IdempotencyRegistry.get_instance()
        fencing = meta.get("idempotency_fencing_token")
        if outcome in {"completed", "blocked"}:
            registry.mark_completed(
                idem_key,
                {"run_id": run_id, "state": outcome},
                fencing_token=fencing,
            )
        else:
            registry.mark_failed(
                idem_key,
                error_message=f"run reached terminal state '{outcome}'",
                fencing_token=fencing,
            )
    except Exception as exc:
        logger.warning(
            "PA-13 idempotency finalize skipped for run %s: %s", run_id, exc
        )


def _set_usage_correlation(run_id: str, trip_id: Optional[str] = None) -> None:
    """Bind run/trip correlation for LLM usage events (PA-20).

    usage_store writes the bound context into usage_events both as real
    ``run_id``/``trip_id`` columns (Wave 2, matching the nullable String
    columns the alembic revision adds in PG) and into metadata_json
    (back-compat with rows written before the migration). Trip id is unknown
    at run start; when it is materialized the caller re-binds so later calls
    carry both (trip correlation for earlier events lands via run_id → run
    meta lookup).
    """
    try:
        from src.llm.usage_store import set_usage_context

        set_usage_context(run_id=run_id, trip_id=trip_id)
    except Exception:
        # Observability wiring must never break the pipeline.
        pass


def _emit_decision_evidence(
    audit_store: Any,
    user_id: str,
    *,
    run_id: str,
    trip_id: Optional[str],
    stage: str,
    result: Any,
    path_outcome: str,
    logger: Any,
) -> None:
    """Write the decision evidence onto the trip timeline (PA-04).

    Production always passes a stage_callback, so run_spine_once's internal
    audit-event branch never fires and the operator trip timeline
    (GET /api/trips/{id}/timeline, matched on details.trip_id) stays blind to
    decisions. This emits the decision record HERE, after trip materialization,
    with the REAL trip id — fixing both the missing emission and the
    ``packet_id`` vs trip id mismatch. Best-effort: must never crash the run.
    """
    try:
        if not trip_id or audit_store is None:
            return

        decision = getattr(result, "decision", None)
        autonomy = getattr(result, "autonomy_outcome", None)

        def _field(obj: Any, name: str, default: Any = None) -> Any:
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(name, default)
            return getattr(obj, name, default)

        nb02: Optional[dict[str, Any]] = None
        if autonomy is not None:
            nb02 = {
                "raw_verdict": _field(autonomy, "raw_verdict"),
                "effective_action": _field(autonomy, "effective_action"),
                "approval_required": _field(autonomy, "approval_required"),
                "rule_source": _field(autonomy, "rule_source"),
            }

        confidence = _field(decision, "confidence")
        rationale = _field(decision, "rationale") or {}
        if not isinstance(rationale, dict):
            rationale = {}

        evidence = {
            "trip_id": trip_id,
            "run_id": run_id,
            "stage": stage,
            "decision_state": _field(decision, "decision_state"),
            "nb01": {
                "gate": "intake_completion",
                "outcome": path_outcome,  # "pass" | "degrade" | "escalate"
            },
            "nb02": nb02,
            "rationale": {
                "hard_blockers": list(_field(decision, "hard_blockers") or []),
                "soft_blockers": list(_field(decision, "soft_blockers") or []),
                "confidence": {
                    "overall": _field(confidence, "overall"),
                    "data_quality": _field(confidence, "data_quality"),
                    "judgment_confidence": _field(confidence, "judgment_confidence"),
                    "commercial_confidence": _field(confidence, "commercial_confidence"),
                },
                "feasibility": rationale.get("budget_feasibility"),
                "autonomy_reasons": (rationale.get("autonomy") or {}).get("reasons"),
            },
            "source": "pipeline_execution_service",
        }
        audit_store.log_event("spine_decision", user_id, evidence)
    except Exception as evidence_err:
        # Broad catch is intentional: decision-evidence emission is an
        # observability side-effect that must never crash the pipeline.
        logger.warning(
            "PA-04 decision evidence emission skipped for run %s: %s",
            run_id,
            evidence_err,
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
    No-ops if no draft is linked. When trip_id is provided, the draft records the
    linkage so draft-scoped reprocesses update the same trip instead of duplicating.
    """
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
            linked_trip_id=trip_id,
        )
    except Exception as exc:
        # Broad catch is intentional: draft state update is an observability
        # side-effect that must never crash the pipeline. Covers asyncpg,
        # serialization, and any DB transient errors.
        logger.debug("Draft state update skipped for run %s: %s", run_id, exc)


def _resolve_draft_reprocess_target(
    draft_store: Any,
    run_ledger: Any,
    trip_store: Any,
    run_id: str,
    logger: Any,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve an existing trip for a draft-scoped reprocess (draft → trip is 1:1).

    Returns (trip_id, current_status) so a re-run updates the lead in place via
    ``preserve_trip_id`` instead of duplicating it, preserving the trip's current
    lifecycle status. See ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.
    """
    try:
        meta = run_ledger.get_meta(run_id)
        draft_id = (meta or {}).get("draft_id")
        if not draft_id:
            return None, None
        draft = draft_store.get(draft_id)
        if not draft:
            return None, None
        trip_id = getattr(draft, "promoted_trip_id", None) or (getattr(draft, "linked_trip_ids", None) or [None])[-1]
        if not trip_id:
            return None, None
        # FND-0277 (Sim #2): this resolver runs in the pipeline executor where
        # the request-scoped RLS ContextVar is not reliably set. ContextVar-
        # based get_trip() then sees an RLS-filtered empty set and returns
        # None — "never resurrect a dead id" — so every reprocess created a
        # NEW lead instead of updating one (6 duplicates in Sim #2). Resolve
        # with the explicit-agency RLS session instead; the draft carries the
        # agency. Fallback keeps test doubles without the method working.
        draft_agency_id = getattr(draft, "agency_id", None)
        agency_lookup = getattr(trip_store, "get_trip_for_agency", None)
        if draft_agency_id and callable(agency_lookup):
            existing = agency_lookup(trip_id, draft_agency_id) or {}
        else:
            existing = trip_store.get_trip(trip_id) or {}
        if not existing:
            # Linked trip no longer exists — never resurrect a dead id.
            return None, None
        return trip_id, (existing.get("status") or None)
    except Exception as exc:
        # Broad catch is intentional: reprocess resolution is a safety
        # optimization; falling back to create-new must never crash the run.
        logger.warning("Draft trip resolution skipped for run %s: %s", run_id, exc)
        return None, None


def _serialize_traveler_bundle_for_persistence(bundle: Any, to_dict: Callable[[Any], Any]) -> Any:
    """Persist only the public traveler projection when the bundle provides one."""
    if not bundle:
        return None
    to_traveler_dict = getattr(bundle, "to_traveler_dict", None)
    if callable(to_traveler_dict):
        return to_traveler_dict()
    return to_dict(bundle)


def _is_validation_valid(validation: Any) -> bool:
    """Support both object and dict validation payloads."""
    if isinstance(validation, dict):
        return bool(validation.get("is_valid", True))
    return bool(getattr(validation, "is_valid", True))


# ---------------------------------------------------------------------------
# PA-13 — per-trip/draft in-flight execution lock (Wave 2)
# ---------------------------------------------------------------------------

# 30-minute TTL = crash-reclaim window: a holder that dies without releasing
# (process kill, lost thread) cannot wedge the trip/draft for longer than the
# pipeline's maximum sane runtime.
_TRIP_RUN_LOCK_TTL_SECONDS = 1800
_TRIP_RUN_LOCK_CONFLICT_REASON = "concurrent run already in flight for this trip/draft"


def _derive_trip_run_lock_key(
    request_dict: dict[str, Any],
    target_trip_id: Optional[str],
) -> Optional[str]:
    """Derive the PA-13 execution lock key, or None when no lock applies.

    Draft reprocesses lock on the draft (draft → trip is 1:1); trip
    reassessments (queue_trip_reassessment passes ``target_trip_id``) lock on
    the trip. Brand-new /run submissions (no draft, no existing trip) create
    independent trips with ``preserve_trip_id=None`` — two concurrent runs
    cannot clobber each other, so they deliberately take no lock.
    """
    draft_id = request_dict.get("draft_id") if isinstance(request_dict, dict) else None
    if draft_id:
        return f"trip-run:draft:{draft_id}"
    if target_trip_id:
        return f"trip-run:trip:{target_trip_id}"
    return None


def _acquire_trip_run_lock(
    run_id: str,
    request_dict: dict[str, Any],
    target_trip_id: Optional[str],
    logger: Any,
) -> tuple[Optional[str], Optional[str]]:
    """Acquire the per-trip/draft in-flight execution lock (PA-13 Wave 2).

    Reuses the durable ``IdempotencyRegistry`` (src/agents/idempotency.py —
    CAS acquisition, fencing tokens, TTL reclaim); no second locking system.
    Returns ``(lock_key, fencing_token)``:

    - ``(None, None)``  → no lock applies, or the registry itself failed
      (fail-open: the lock suppresses duplicate side-effects; it must never
      gate real runs on registry unavailability).
    - ``(key, token)``  → acquired; the caller MUST release in ``finally``.
    - ``(key, None)``   → conflict: a PENDING holder owns the key; the caller
      must BLOCK the run (policy rejection, not a failure).
    """
    lock_key = _derive_trip_run_lock_key(request_dict, target_trip_id)
    if not lock_key:
        return None, None
    try:
        from src.agents.idempotency import IdempotencyRegistry

        acquired, existing = IdempotencyRegistry.get_instance().try_acquire(
            lock_key,
            trip_id="",
            action_name="trip_run_lock",
            payload={"run_id": run_id},
            ttl_seconds=_TRIP_RUN_LOCK_TTL_SECONDS,
        )
    except Exception as acquire_err:
        logger.warning(
            "PA-13 trip-run lock acquire failed for run %s (proceeding unlocked): %s",
            run_id,
            acquire_err,
        )
        return None, None

    if acquired:
        # ``existing`` is the freshly minted PENDING record carrying our fence.
        return lock_key, (getattr(existing, "fencing_token", None) or None)

    from src.agents.idempotency import IdempotencyStatus

    status = getattr(existing, "status", None)
    if status == IdempotencyStatus.PENDING:
        return lock_key, None  # genuine in-flight conflict → caller blocks
    # Non-PENDING holder (COMPLETED/FAILED): this implementation always
    # releases via mark_failed (see _release_trip_run_lock), so a record in
    # any other state here is a foreign/legacy writer on the same key
    # namespace. Treat the lock as free and proceed WITHOUT acquisition rather
    # than wedging a real run behind a finished record.
    logger.info(
        "PA-13 trip-run lock key %s held by finished record; proceeding unlocked for run %s",
        lock_key,
        run_id,
    )
    return None, None


def _release_trip_run_lock(
    run_id: str,
    lock_key: Optional[str],
    fencing_token: Optional[str],
    run_ledger: Any,
    logger: Any,
) -> None:
    """Release the PA-13 trip-run lock (fenced, best-effort) from ``finally``.

    Outcome is read from the ledger ``state`` every terminal path writes.
    Deliberate release semantics — ``mark_failed`` for EVERY outcome: the
    registry answers re-acquire with ``(False, COMPLETED)`` until the 30-min
    TTL lapses (verified at runtime against the memory backend), which would
    falsely BLOCK legitimate reprocesses of the same draft/trip after a
    successful run. FAILED is the registry's only immediately re-acquirable
    terminal state, so it is the only correct "lock released" signal; the
    actual run outcome is preserved in the error message. Stale releases
    (TTL reclaim, lost race) are rejected by the fencing CAS, so this can
    never clobber a newer owner, and the release never masks the run outcome.
    """
    if not lock_key or not fencing_token:
        return  # never acquired — nothing to release
    try:
        outcome = None
        try:
            outcome = (run_ledger.get_meta(run_id) or {}).get("state")
        except Exception:
            outcome = None
        if outcome not in ("completed", "failed", "blocked"):
            # Never terminalized (thread died mid-run): free the slot now so
            # the next attempt is not wedged until the TTL reclaim.
            outcome = "failed"
        from src.agents.idempotency import IdempotencyRegistry

        IdempotencyRegistry.get_instance().mark_failed(
            lock_key,
            f"trip run reached terminal state '{outcome}' — lock released",
            fencing_token=fencing_token,
        )
    except Exception as release_err:
        # Best-effort: the lock must never mask the real run outcome. A leaked
        # lock self-heals via the 30-minute TTL reclaim.
        logger.warning(
            "PA-13 trip-run lock release skipped for run %s: %s", run_id, release_err
        )


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
    meta = RunMeta(stage="", operating_mode="", fixture_id=None, execution_ms=0.0)

    # --- PA-13: per-trip/draft in-flight execution lock ----------------------
    # SINGLE CHOKE POINT: both entry paths funnel into THIS function —
    # POST /run (server.py) for draft reprocesses (draft_id in request_dict)
    # and trip reassessment (trip_lifecycle_service.queue_trip_reassessment →
    # execute_pipeline_fn, which passes target_trip_id and no draft_id).
    # Locking here therefore covers both with ONE acquisition site;
    # trip_lifecycle_service deliberately does not double-lock.
    trip_run_lock_key, trip_run_lock_token = _acquire_trip_run_lock(
        run_id, request_dict, target_trip_id, logger
    )
    if trip_run_lock_key is not None and trip_run_lock_token is None:
        # Another run already holds the trip/draft lock: a concurrency-policy
        # rejection, not a failure — BLOCK (terminal, replayable, excluded
        # from auto-requeue) so recovery never re-queues it.
        try:
            # queued→blocked is an illegal ledger transition; the run DID
            # start (it reached the lock gate), so walk queued→running→blocked
            # exactly like every other blocked terminal path.
            run_ledger.set_state(run_id, run_state_running)
            run_ledger.block(run_id, block_reason=_TRIP_RUN_LOCK_CONFLICT_REASON)
            _record_terminal_metrics("blocked")
            _finalize_run_idempotency(run_ledger, run_id, "blocked", logger)
            try:
                run_ledger.update_meta(
                    run_id,
                    trip_run_lock=trip_run_lock_key,
                    trip_run_lock_conflict=True,
                )
            except Exception:
                pass
            _update_draft_for_terminal_state(
                run_id,
                "blocked",
                logger,
                run_ledger,
                draft_store,
                trip_id=target_trip_id,
                snapshot={
                    "block_reason": _TRIP_RUN_LOCK_CONFLICT_REASON,
                    "conflict": True,
                    "lock_key": trip_run_lock_key,
                },
            )
            emit_run_blocked_fn(
                run_id=run_id,
                block_reason=_TRIP_RUN_LOCK_CONFLICT_REASON,
                stage_at_block=None,
                trip_id=target_trip_id,
            )
        except Exception as ledger_err:
            # Broad catch is intentional: block ledger update is an observability
            # side-effect that must never crash the pipeline during error handling.
            # Covers asyncpg, serialization, and any DB transient errors.
            logger.error(
                "PA-13 concurrent-run block ledger failed for run %s: %s",
                run_id,
                ledger_err,
            )
        logger.warning(
            "PA-13 run %s blocked: %s (lock_key=%s)",
            run_id,
            _TRIP_RUN_LOCK_CONFLICT_REASON,
            trip_run_lock_key,
        )
        return

    if trip_run_lock_key is not None and trip_run_lock_token is not None:
        try:
            run_ledger.update_meta(
                run_id,
                trip_run_lock=trip_run_lock_key,
                trip_run_lock_fencing=trip_run_lock_token,
            )
        except Exception as meta_err:
            # Best-effort observability stash; the local token above is what
            # the fenced ``finally`` release actually uses.
            logger.debug(
                "PA-13 trip-run lock meta stash skipped for run %s: %s",
                run_id,
                meta_err,
            )

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
            # Broad catch is intentional: result checkpointing is an observability
            # side-effect that must never crash the pipeline. Covers asyncpg,
            # serialization, to_dict failures, and any DB transient errors.
            logger.error("Wave A: result step checkpointing failed for run %s: %s", run_id, e)

    def _finalize_result(result: Any) -> None:
        raw_text = collect_raw_text_sources(
            raw_note=request.raw_note,
            owner_note=request.owner_note,
            itinerary_text=request.itinerary_text,
            structured_json=request.structured_json,
        )

        def _on_adjusted(
            packet_payload: dict[str, Any],
            validation_payload: dict[str, Any],
            decision_payload: dict[str, Any],
        ) -> None:
            try:
                run_ledger.save_step(run_id, "packet_live_adjusted", packet_payload)
                run_ledger.save_step(run_id, "validation_live_adjusted", validation_payload)
                run_ledger.save_step(run_id, "decision_live_adjusted", decision_payload)
            except Exception as e:
                logger.debug("Wave A: live-check adjusted checkpoint skipped for run %s: %s", run_id, e)

        finalize_result_with_live_checker(
            result=result,
            raw_text=raw_text,
            build_live_checker_signals_fn=build_live_checker_signals_fn,
            to_dict=to_dict,
            on_adjusted=_on_adjusted,
        )

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

        meta = RunMeta(
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_id=request.scenario_id,
            execution_ms=0.0,
        )

        run_ledger.set_state(run_id, run_state_running)

        # PA-20: bind run correlation so any LLM usage event recorded during
        # this pipeline carries run_id in metadata_json (zero-migration cost
        # correlation). Trip id is unknown here — re-bound after save below.
        _set_usage_correlation(run_id)

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
                # Broad catch is intentional: draft state update is an observability
                # side-effect that must never interrupt pipeline startup. Covers
                # asyncpg, serialization, and any DB transient errors.
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
                # PA-17 heartbeat: prove this run is alive so the stale-run
                # sweep cannot race a long-running live pipeline.
                try:
                    run_ledger.touch(run_id)
                except Exception as touch_err:
                    # Observability must never break a run; debug-level because
                    # fake ledgers in tests may not implement touch().
                    logger.debug("Heartbeat touch skipped for run %s: %s", run_id, touch_err)

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
                # Broad catch is intentional: stage checkpointing is an observability
                # side-effect that must never interrupt the pipeline. Covers asyncpg,
                # serialization, to_dict failures, and any DB transient errors.
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
                strict_leakage=request.strict_leakage,
                result_finalizer=_finalize_result,
            )

            execution_ms = (time.perf_counter() - t0) * 1000
            meta.execution_ms = round(execution_ms, 2)
            pipeline_span.set_attribute("execution_ms", round(execution_ms, 2))
            if hasattr(result, "packet"):
                pipeline_span.set_attribute(
                    "trip_id",
                    result.packet.packet_id if hasattr(result.packet, "packet_id") else "",
                )

            _checkpoint_result_steps(run_id, result)

            if getattr(result, "early_exit", False):
                logger.warning(
                    "spine_run early_exit run_id=%s reason=%s execution_ms=%.2f",
                    run_id,
                    result.early_exit_reason,
                    execution_ms,
                )

                # ESCALATE persists the inquiry as an incomplete lead
                # (ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31): a customer contact
                # exists regardless of packet completeness. Gates still refuse
                # quote generation; the lead surfaces in the inbox for follow-up.
                # An existing trip is NEVER overwritten here: the early-exit
                # packet is definitionally incomplete, so when this run belongs
                # to a trip that already has a record (auto-reassess-on-edit,
                # draft reprocess), the save is skipped and the record stands.
                reprocess_trip_id, _reprocess_status_unused = _resolve_draft_reprocess_target(
                    draft_store, run_ledger, trip_store, run_id, logger,
                )
                preserve_id = target_trip_id or reprocess_trip_id
                trip_id_saved: Optional[str] = None
                if preserve_id:
                    trip_id_saved = preserve_id
                    logger.info(
                        "ESCALATE skipped lead save for run %s: existing trip %s preserved",
                        run_id,
                        preserve_id,
                    )
                else:
                    # PA-27 fail-loud lead persistence: retry once immediately;
                    # if the retry also fails, mark the run FAILED (not
                    # blocked) with failure_class="state" and re-raise so the
                    # lost customer inquiry is loud AND classified instead of
                    # a blocked run quietly missing its lead.
                    last_save_err: Optional[Exception] = None
                    for attempt in (1, 2):
                        try:
                            trip_id_saved = save_processed_trip(
                                {
                                    "run_id": run_id,
                                    "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                                    "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                                    "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                                    "strategy": to_dict(result.strategy) if hasattr(result, "strategy") else None,
                                    "plan_candidate": to_dict(result.plan_candidate) if hasattr(result, "plan_candidate") and result.plan_candidate else None,
                                    "traveler_bundle": _serialize_traveler_bundle_for_persistence(
                                        result.traveler_bundle,
                                        to_dict,
                                    ) if hasattr(result, "traveler_bundle") else None,
                                    "internal_bundle": to_dict(result.internal_bundle) if hasattr(result, "internal_bundle") and result.internal_bundle else None,
                                    "safety": to_dict(result.safety) if hasattr(result, "safety") else None,
                                    "fees": to_dict(result.fees) if hasattr(result, "fees") and result.fees else None,
                                    "frontier_result": to_dict(result.frontier_result) if hasattr(result, "frontier_result") and result.frontier_result else None,
                                    "meta": {
                                        **meta.model_dump(),
                                        "submission": consented_submission,
                                        "retention_consent": request.retention_consent,
                                        "blocked": True,
                                        "early_exit_reason": result.early_exit_reason,
                                    },
                                },
                                source="spine_api",
                                agency_id=agency_id,
                                user_id=user_id,
                                trip_status=existing_trip_status or "incomplete",
                                preserve_trip_id=None,
                                audit_event_type=audit_event_type,
                            )
                            last_save_err = None
                            break
                        except Exception as save_err:
                            last_save_err = save_err
                            logger.error(
                                "ESCALATE lead persistence failed for run %s "
                                "(attempt %d/2): %s",
                                run_id,
                                attempt,
                                save_err,
                            )
                    if last_save_err is not None:
                        # Two consecutive persistence failures: state
                        # divergence — requeue cannot fix it. Fail the run
                        # loudly with the taxonomy class, then propagate.
                        try:
                            run_ledger.fail(
                                run_id,
                                error_type=type(last_save_err).__name__,
                                error_message=(
                                    f"Lead persistence failed after retry "
                                    f"(ESCALATE early exit): {last_save_err}"
                                ),
                                failure_class=FailureClass.STATE.value,
                                stage=current_stage,
                            )
                            _record_terminal_metrics("failed", FailureClass.STATE.value)
                            _finalize_run_idempotency(run_ledger, run_id, "failed", logger)
                            _update_draft_for_terminal_state(
                                run_id,
                                "failed",
                                logger,
                                run_ledger,
                                draft_store,
                                snapshot={
                                    "error_type": type(last_save_err).__name__,
                                    "error_message": str(last_save_err),
                                    "stage_at_failure": current_stage,
                                    "failure_class": FailureClass.STATE.value,
                                    "lead_persistence_failed": True,
                                },
                            )
                            emit_run_failed_fn(
                                run_id=run_id,
                                error_type=type(last_save_err).__name__,
                                error_message=(
                                    f"Lead persistence failed after retry (ESCALATE early exit): {last_save_err}"
                                ),
                                stage_at_failure=current_stage,
                                trip_id=None,
                            )
                        except Exception as fail_err:
                            logger.error(
                                "PA-27 failed-run marking also failed for run %s: %s",
                                run_id,
                                fail_err,
                            )
                        raise LeadPersistenceError(
                            f"Lead persistence failed after retry for run {run_id}: {last_save_err}"
                        ) from last_save_err
                    logger.info("Blocked lead saved (ESCALATE): %s", trip_id_saved)
                if trip_id_saved:
                    try:
                        run_ledger.update_meta(run_id, trip_id=trip_id_saved)
                        # PA-20: re-bind so later usage events carry trip_id too.
                        _set_usage_correlation(run_id, trip_id=trip_id_saved)
                    except Exception as meta_err:
                        logger.warning(
                            "ESCALATE run meta update failed for run %s: %s",
                            run_id,
                            meta_err,
                        )

                run_ledger.save_step(run_id, "blocked_result", {
                    "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                    "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                    "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                    "early_exit_reason": result.early_exit_reason,
                    "trip_id": trip_id_saved,
                    "meta": meta.model_dump(),
                })
                block_reason = result.early_exit_reason or "Pipeline blocked"
                # PA-04: decision evidence on the trip timeline (real trip id,
                # even when it is the preserved/incomplete trip) — the
                # ESCALATE terminal path is otherwise invisible to operators.
                _emit_decision_evidence(
                    audit_store,
                    user_id,
                    run_id=run_id,
                    trip_id=trip_id_saved,
                    stage=request.stage,
                    result=result,
                    path_outcome="escalate",
                    logger=logger,
                )
                run_ledger.block(run_id, block_reason=block_reason)
                _record_terminal_metrics("blocked")
                _finalize_run_idempotency(run_ledger, run_id, "blocked", logger)
                _update_draft_for_terminal_state(run_id, "blocked", logger, run_ledger, draft_store, trip_id=trip_id_saved, snapshot={"block_reason": block_reason, "stage_at_block": current_stage, "trip_id": trip_id_saved})
                emit_run_blocked_fn(
                    run_id=run_id,
                    block_reason=block_reason,
                    stage_at_block=current_stage,
                    trip_id=trip_id_saved,
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
                reprocess_trip_id, reprocess_status = _resolve_draft_reprocess_target(
                    draft_store, run_ledger, trip_store, run_id, logger,
                )
                trip_id_saved = save_processed_trip(
                    {
                        "run_id": run_id,
                        "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                        "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                        "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                        "strategy": to_dict(result.strategy) if hasattr(result, "strategy") else None,
                        "plan_candidate": to_dict(result.plan_candidate) if hasattr(result, "plan_candidate") and result.plan_candidate else None,
                        "traveler_bundle": _serialize_traveler_bundle_for_persistence(
                            result.traveler_bundle,
                            to_dict,
                        ) if hasattr(result, "traveler_bundle") else None,
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
                    trip_status=existing_trip_status or reprocess_status or "incomplete",
                    preserve_trip_id=target_trip_id or reprocess_trip_id,
                    audit_event_type=audit_event_type,
                )
                if not trip_id_saved:
                    raise RuntimeError("save_processed_trip returned no trip_id for partial intake")
                run_ledger.update_meta(run_id, trip_id=trip_id_saved)
                logger.info("Partial trip saved: %s", trip_id_saved)

                # PA-04: decision evidence on the partial (incomplete) trip.
                _emit_decision_evidence(
                    audit_store,
                    user_id,
                    run_id=run_id,
                    trip_id=trip_id_saved,
                    stage=request.stage,
                    result=result,
                    path_outcome="degrade",
                    logger=logger,
                )

                _complete_ledger_reconciled(run_ledger, run_id, execution_ms, logger)
                _update_draft_for_terminal_state(run_id, "completed", logger, run_ledger, draft_store, trip_id=trip_id_saved, snapshot={"early_exit_reason": "partial_intake", "trip_id": trip_id_saved})
                emit_run_completed_fn(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
                return

            if hasattr(result, "validation") and result.validation and not _is_validation_valid(result.validation):
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
                _record_terminal_metrics("blocked")
                _finalize_run_idempotency(run_ledger, run_id, "blocked", logger)
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
            reprocess_trip_id, reprocess_status = _resolve_draft_reprocess_target(
                draft_store, run_ledger, trip_store, run_id, logger,
            )
            trip_id_saved = save_processed_trip(
                {
                    "run_id": run_id,
                    "packet": to_dict(result.packet) if hasattr(result, "packet") else None,
                    "validation": to_dict(result.validation) if hasattr(result, "validation") else None,
                    "decision": to_dict(result.decision) if hasattr(result, "decision") else None,
                    "strategy": to_dict(result.strategy) if hasattr(result, "strategy") else None,
                    "plan_candidate": to_dict(result.plan_candidate) if hasattr(result, "plan_candidate") and result.plan_candidate else None,
                    "traveler_bundle": _serialize_traveler_bundle_for_persistence(
                        result.traveler_bundle,
                        to_dict,
                    ) if hasattr(result, "traveler_bundle") else None,
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
                trip_status=existing_trip_status or reprocess_status or "new",
                preserve_trip_id=target_trip_id or reprocess_trip_id,
                audit_event_type=audit_event_type,
            )
            if not trip_id_saved:
                raise RuntimeError("save_processed_trip returned no trip_id")
            run_ledger.update_meta(run_id, trip_id=trip_id_saved)
            logger.info("Trip saved: %s", trip_id_saved)
            # PA-20: re-bind so later usage events carry trip_id too.
            _set_usage_correlation(run_id, trip_id=trip_id_saved)

            # PA-04: decision evidence on the operator trip timeline with the
            # REAL trip id (fixes both the callback-only emission gap and the
            # packet_id-vs-trip_id mismatch).
            _emit_decision_evidence(
                audit_store,
                user_id,
                run_id=run_id,
                trip_id=trip_id_saved,
                stage=request.stage,
                result=result,
                path_outcome="pass",
                logger=logger,
            )

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
                _complete_ledger_reconciled(run_ledger, run_id, execution_ms, logger)
                _update_draft_for_terminal_state(run_id, "completed", logger, run_ledger, draft_store, trip_id=trip_id_saved, snapshot={"trip_id": trip_id_saved})
                emit_run_completed_fn(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
            except Exception as e:
                # Broad catch is intentional: ledger completion is an observability
                # side-effect that must never crash the pipeline after successful
                # trip save. Covers asyncpg, serialization, and any DB transient errors.
                logger.error("Wave A: ledger complete failed for run %s: %s", run_id, e)

    except LeadPersistenceError:
        # PA-27: the run was already marked FAILED (failure_class="state") and
        # the terminal events emitted inside the ESCALATE path. Nothing further
        # to record — re-raising is the loud signal; do not double-fail.
        raise

    except StrictLeakageViolation as e:
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
            _record_terminal_metrics("blocked")
            _finalize_run_idempotency(run_ledger, run_id, "blocked", logger)
            _update_draft_for_terminal_state(run_id, "blocked", logger, run_ledger, draft_store, snapshot={"block_reason": error_message, "stage_at_block": current_stage})
            emit_run_blocked_fn(
                run_id=run_id,
                block_reason=error_message,
                stage_at_block=current_stage,
                trip_id=None,
            )
        except Exception as ledger_err:
            # Broad catch is intentional: block ledger update is an observability
            # side-effect that must never crash the pipeline during error handling.
            # Covers asyncpg, serialization, and any DB transient errors.
            logger.error("Wave A: block ledger failed for run %s: %s", run_id, ledger_err)

    except Exception as e:
        # Broad catch is intentional: this is the top-level pipeline error handler.
        # It must catch ALL exception types (asyncpg, SQLAlchemy, ValueError-like
        # subclasses, serialization, and unexpected errors) to mark the run as
        # FAILED and emit terminal events. The pipeline must never crash silently.
        execution_ms = (time.perf_counter() - t0) * 1000
        logger.error(
            "spine_run error run_id=%s type=%s error=%s execution_ms=%.2f",
            run_id,
            type(e).__name__,
            str(e),
            execution_ms,
        )

        # Wave A: mark as FAILED with the PA-07 failure class + stage so
        # recovery can branch on cause instead of requeueing class-blind.
        try:
            _failure_class = classify_failure(e, current_stage)
            run_ledger.fail(
                run_id,
                error_type=type(e).__name__,
                error_message=str(e),
                failure_class=_failure_class,
                stage=current_stage,
            )
            _record_terminal_metrics("failed", _failure_class)
            _finalize_run_idempotency(run_ledger, run_id, "failed", logger)
            _update_draft_for_terminal_state(run_id, "failed", logger, run_ledger, draft_store, snapshot={"error_type": type(e).__name__, "error_message": str(e), "stage_at_failure": current_stage})
            emit_run_failed_fn(
                run_id=run_id,
                error_type=type(e).__name__,
                error_message=str(e),
                stage_at_failure=current_stage,
                trip_id=None,
            )
        except Exception as ledger_err:
            # Broad catch is intentional: fail ledger update is an observability
            # side-effect that must never crash the pipeline during error handling.
            # Covers asyncpg, serialization, and any DB transient errors.
            logger.error("Wave A: fail ledger failed for run %s: %s", run_id, ledger_err)

    finally:
        # PA-13: always release the trip-run lock (fenced; no-op when never
        # acquired), whichever terminal path ran — including LeadPersistenceError
        # re-raises, where the run is already FAILED and the lock must not
        # wedge the next attempt.
        _release_trip_run_lock(
            run_id, trip_run_lock_key, trip_run_lock_token, run_ledger, logger
        )
