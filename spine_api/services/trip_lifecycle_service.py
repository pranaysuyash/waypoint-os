"""Trip lifecycle helpers shared by server shell and lifecycle routers."""

from __future__ import annotations

import threading
import uuid
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from spine_api.run_ledger import RunLedger
from src.intake.fact_overrides import (
    AUTHORITATIVE_FACT_SNAPSHOT,
    CORRECTION_MODES,
    TRIP_FIELD_FACTS,
    canonical_fact_name,
    explicit_fact_override,
)

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore
TripStore = persistence.TripStore

VALID_STAGES = {"discovery", "shortlist", "proposal", "booking"}


class ReassessmentPersistenceError(RuntimeError):
    """A reassessment could not safely persist against its source revision."""

REASSESS_EDIT_TRIGGER_FIELDS = {
    "origin",
    "destination",
    "budget",
    "party_composition",
    "party",
    "pace_preference",
    "date_year_confidence",
    "dateWindow",
    "lead_source",
    "activity_provenance",
    "trip_priorities",
    "date_flexibility",
    "follow_up_due_date",
    "owner_note",
    "raw_note",
    "structured_json",
    "itinerary_text",
    "tripPurpose", "trip_purpose", "tripPriorities", "dateFlexibility",
    "date_window", "customer_message", "agent_notes", "assumption_actions",
}


def authoritative_facts_from_trip(trip: Dict[str, Any]) -> dict[str, Any]:
    """Select persisted corrections, keeping evidence accumulation separate.

    Direct extraction is replayed from retained source text. Explicit edits and
    traveler answers replace it. When source text was not retained, existing
    fact slots supply the replay baseline instead of losing the whole brief.
    """
    extracted = trip.get("extracted") if isinstance(trip.get("extracted"), dict) else {}
    facts = extracted.get("facts") if isinstance(extracted.get("facts"), dict) else {}
    raw_input = trip.get("raw_input") if isinstance(trip.get("raw_input"), dict) else {}
    submission = raw_input.get("submission") if isinstance(raw_input.get("submission"), dict) else {}
    source_retained = any(submission.get(key) for key in ("raw_note", "owner_note", "itinerary_text"))
    selected: dict[str, Any] = {}
    # Canonical names win same-revision alias ties. Writer timestamps take
    # precedence across revisions; all newly written timestamps are UTC ISO.
    for name, payload in sorted(facts.items(), key=lambda item: (str((item[1] or {}).get("updated_at") or "") if isinstance(item[1], dict) else "", item[0] == canonical_fact_name(item[0]))):
        if not isinstance(payload, dict) or "value" not in payload:
            continue
        authority = payload.get("authority_level")
        mode = payload.get("extraction_mode")
        if mode == "invalidated_by_override":
            continue
        correction = authority == "manual_override" or (
            authority in {"explicit_user", "explicit_user_raw"}
            and (mode in CORRECTION_MODES or not mode or payload.get("value") is None)
        )
        replay_baseline = not source_retained and authority in {
            "manual_override", "explicit_user", "imported_structured", "explicit_owner",
        }
        if correction or replay_baseline:
            selected[canonical_fact_name(name)] = deepcopy(payload)

    for trip_field, canonical in TRIP_FIELD_FACTS.items():
        if canonical in selected or trip_field not in trip or trip.get(trip_field) is None:
            continue
        value = trip[trip_field]
        previous = facts.get(canonical)
        if isinstance(previous, dict) and previous.get("value") == value:
            continue
        selected[canonical] = explicit_fact_override(
            canonical, value, source_ref=f"trip_column:{trip.get('id', 'unknown')}:{trip_field}",
        )
    return selected


def build_reassessment_envelope_from_trip(trip: Dict[str, Any]):
    """Build trusted in-process context from a tenant-authorized stored trip.

    This metadata never comes from the public run request schema. A nested
    structured_json key cannot manufacture SourceEnvelope metadata.
    """
    from src.intake.packet_models import SourceEnvelope

    envelope = SourceEnvelope.from_structured({}, "structured_import", "system")
    envelope.metadata[AUTHORITATIVE_FACT_SNAPSHOT] = authoritative_facts_from_trip(trip)
    envelope.metadata["trip_id"] = trip.get("id")
    return envelope


def persist_reassessment_result(
    trip: Dict[str, Any], output: dict[str, Any], *, agency_id: str,
    user_id: str, trip_store: Any, audit_store: Any,
) -> str:
    """Refresh only assessment-owned state with the canonical tenant CAS.

    Lifecycle, assignment, accepted proposals and booking/payment fields remain
    owned by their existing writers. A concurrent edit cannot be overwritten by
    a long-running assessment. The original builder and assumption carry-forward
    rules remain canonical; this is an adapter over them, not a second store.
    """
    expected_version = trip.get("updated_at")
    if not expected_version:
        raise ReassessmentPersistenceError("Reassessment requires a persisted trip revision; save the current trip and retry.")
    built = persistence._build_processed_trip(
        output, source=trip.get("source") or "spine_api", user_id=trip.get("user_id"),
        follow_up_due_date=trip.get("follow_up_due_date"),
        party_composition=trip.get("party_composition"), pace_preference=trip.get("pace_preference"),
        date_year_confidence=trip.get("date_year_confidence"), lead_source=trip.get("lead_source"),
        activity_provenance=trip.get("activity_provenance"), trip_status=trip.get("status") or "incomplete",
        preserve_trip_id=trip["id"], preserve_created_at=trip.get("created_at"),
    )
    persistence._carry_forward_acknowledged_assumptions(built, trip)
    assessment_fields = (
        "run_id", "stage", "extracted", "validation", "decision", "strategy",
        "traveler_bundle", "internal_bundle", "safety", "frontier_result", "fees", "raw_input",
    )
    updates = {field: built.get(field) for field in assessment_fields}
    # Preserve operational extras (including commercial records) in analytics.
    # The persistence CAS merges extras, but replacing the complete analytics
    # document from a freshly computed draft would broaden this writer's scope.
    updated = trip_store.update_trip_if_version_for_agency(
        trip["id"], agency_id, updates, expected_updated_at=str(expected_version),
    )
    if updated is None:
        raise ReassessmentPersistenceError("Trip changed while reassessment was running. Newer edits were preserved; run reassessment again.")
    audit_store.log_event("trip_reassessed", user_id, {
        "trip_id": trip["id"], "run_id": output.get("run_id"),
        "assessment_outcome": "blocked" if (output.get("meta") or {}).get("blocked") else "completed",
        "source_revision": str(expected_version),
    })
    return trip["id"]


def build_reassessment_request_from_trip(
    trip: Dict[str, Any],
    *,
    stage_override: Optional[str] = None,
    operating_mode_override: Optional[str] = None,
    strict_leakage_override: Optional[bool] = None,
) -> dict[str, Any]:
    raw_input = trip.get("raw_input") if isinstance(trip.get("raw_input"), dict) else {}
    submission = raw_input.get("submission") if isinstance(raw_input.get("submission"), dict) else {}
    extracted = trip.get("extracted") if isinstance(trip.get("extracted"), dict) else {}
    structured_overlay: dict[str, Any] = {}

    raw_note_value = submission.get("raw_note")

    def _set_overlay(field_name: str, trip_value: Any) -> None:
        if trip_value is None:
            structured_overlay[field_name] = None
            return
        if isinstance(trip_value, str):
            normalized = trip_value.strip()
            if not normalized:
                structured_overlay[field_name] = None
                return
            structured_overlay[field_name] = normalized
            return
        structured_overlay[field_name] = trip_value

    # FND-0351 (Sim #4): draft-flow trips carry the traveler's words ONLY in
    # the linked draft (raw_input.submission is empty), so a reassessment built
    # without the note re-extracts from the structured overlay alone and DROPS
    # every fact the overlay doesn't map (destination/party/budget vanished in
    # the live run). Fall back to the linked draft's customer_message.
    if not raw_note_value:
        try:
            from spine_api.draft_store import DraftStore

            agency_id_hint = trip.get("agency_id")
            if agency_id_hint:
                for draft in DraftStore.list_by_agency(agency_id_hint, limit=500):
                    linked = draft.promoted_trip_id == trip.get("id") or trip.get("id") in (
                        getattr(draft, "linked_trip_ids", None) or []
                    )
                    if linked and getattr(draft, "customer_message", None):
                        raw_note_value = draft.customer_message
                        break
        except Exception:
            pass

    request_dict: dict[str, Any] = {
        "raw_note": raw_note_value,
        "owner_note": submission.get("owner_note"),
        "structured_json": submission.get("structured_json"),
        "itinerary_text": submission.get("itinerary_text"),
        "retention_consent": bool(raw_input.get("retention_consent", False)),
        "stage": stage_override or trip.get("stage") or raw_input.get("stage") or "discovery",
        "operating_mode": operating_mode_override or raw_input.get("operating_mode") or "normal_intake",
        "strict_leakage": bool(strict_leakage_override if strict_leakage_override is not None else raw_input.get("strict_leakage", False)),
        "scenario_id": raw_input.get("fixture_id"),
        "follow_up_due_date": trip.get("follow_up_due_date"),
        "pace_preference": trip.get("pace_preference"),
        "lead_source": trip.get("lead_source"),
        "activity_provenance": trip.get("activity_provenance"),
        "date_year_confidence": trip.get("date_year_confidence"),
    }

    _set_overlay("origin", trip.get("origin"))
    _set_overlay("destination", trip.get("destination"))
    _set_overlay("budget", trip.get("budget"))
    _set_overlay("dates", trip.get("dateWindow"))
    _set_overlay("date_window", trip.get("dateWindow"))
    _set_overlay("trip_purpose", trip.get("tripPurpose"))
    _set_overlay("trip_priorities", trip.get("tripPriorities"))
    _set_overlay("date_flexibility", trip.get("dateFlexibility"))
    _set_overlay("follow_up_due_date", trip.get("follow_up_due_date"))
    _set_overlay("pace_preference", trip.get("pace_preference"))
    _set_overlay("lead_source", trip.get("lead_source"))
    _set_overlay("activity_provenance", trip.get("activity_provenance"))
    _set_overlay("date_year_confidence", trip.get("date_year_confidence"))

    authoritative = authoritative_facts_from_trip(trip)
    request_field = {
        "origin_city": "origin", "destination_candidates": "destination",
        "budget_raw_text": "budget", "date_window": "date_window",
    }
    for field_name, slot in authoritative.items():
        value = slot.get("value")
        field = request_field.get(field_name, field_name)
        if field == "destination" and isinstance(value, list) and len(value) == 1:
            value = value[0]
        _set_overlay(field, deepcopy(value))
        if field == "date_window":
            _set_overlay("dates", deepcopy(value))

    existing_structured_json = request_dict.get("structured_json")
    if isinstance(existing_structured_json, dict):
        merged_structured_json = dict(existing_structured_json)
        explicit_clear_fields = {
            request_field.get(name, name) for name, slot in authoritative.items() if slot.get("value") is None
        }
        for k, v in structured_overlay.items():
            if v is None and k not in explicit_clear_fields:
                merged_structured_json.pop(k, None)
            else:
                merged_structured_json[k] = v
        if merged_structured_json:
            request_dict["structured_json"] = merged_structured_json
        else:
            request_dict["structured_json"] = None
    elif structured_overlay:
        explicit_clear_fields = {
            request_field.get(name, name) for name, slot in authoritative.items() if slot.get("value") is None
        }
        cleaned_overlay = {k: v for k, v in structured_overlay.items() if v is not None or k in explicit_clear_fields}
        if cleaned_overlay:
            request_dict["structured_json"] = cleaned_overlay

    if not any(request_dict.get(k) for k in ("raw_note", "owner_note", "structured_json", "itinerary_text")):
        request_dict["structured_json"] = {"extracted_snapshot": extracted}

    return request_dict


def queue_trip_reassessment(
    trip: Dict[str, Any],
    *,
    agency_id: str,
    user_id: str,
    request_dict: dict[str, Any],
    trigger: str,
    execute_pipeline_fn: Callable[..., None],
    reason: Optional[str] = None,
) -> str:
    """Queue a background reassessment run for an existing trip.

    PA-13 note — the reassess path takes NO lock here. Both this path (via
    ``execute_pipeline_fn`` with ``target_trip_id=trip["id"]`` and no
    draft_id) and draft reprocesses (POST /run with ``draft_id``) funnel into
    the SINGLE lock choke point:
    ``spine_api.services.pipeline_execution_service.execute_spine_pipeline``,
    which derives ``trip-run:trip:{trip_id}`` for reassessment and
    ``trip-run:draft:{draft_id}`` for drafts against the durable
    IdempotencyRegistry. Do NOT add a second lock here — reassessment would
    be double-locked.
    """
    run_id = str(uuid.uuid4())
    RunLedger.create(
        run_id=run_id,
        trip_id=trip.get("id"),
        stage=request_dict.get("stage", trip.get("stage") or "discovery"),
        operating_mode=request_dict.get("operating_mode", "normal_intake"),
        agency_id=agency_id,
        draft_id=None,
    )
    thread = threading.Thread(
        target=execute_pipeline_fn,
        args=(run_id, request_dict, agency_id, user_id, trip.get("id"), "trip_reassessed", trip.get("status")),
        daemon=True,
        name=f"reassess-{run_id[:8]}",
    )
    thread.start()

    AuditStore.log_event(
        "trip_reassess_queued",
        user_id,
        {
            "trip_id": trip.get("id"),
            "run_id": run_id,
            "trigger": trigger,
            "reason": reason,
            "stage": request_dict.get("stage"),
            "operating_mode": request_dict.get("operating_mode"),
        },
    )
    return run_id


def transition_trip_stage(
    trip_id: str,
    *,
    agency_id: str,
    target_stage: str,
    reason: Optional[str] = None,
    expected_current_stage: Optional[str] = None,
) -> dict[str, Any]:
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise KeyError("Trip not found")

    if target_stage not in VALID_STAGES:
        raise ValueError(f"Invalid target_stage '{target_stage}'. Must be one of {sorted(VALID_STAGES)}")

    current_stage = trip.get("stage", "discovery")
    if expected_current_stage is not None and expected_current_stage != current_stage:
        return {
            "conflict": True,
            "expected": expected_current_stage,
            "actual": current_stage,
        }

    if target_stage == current_stage:
        return {
            "trip_id": trip_id,
            "old_stage": current_stage,
            "new_stage": current_stage,
            "changed": False,
            "readiness": trip.get("validation", {}).get("readiness"),
        }

    TripStore.update_trip(trip_id, {"stage": target_stage})
    AuditStore.log_event("stage_transition", agency_id, {
        "trip_id": trip_id,
        "from": current_stage,
        "to": target_stage,
        "trigger": "manual",
        "reason": reason,
        "actor": "operator",
    })

    return {
        "trip_id": trip_id,
        "old_stage": current_stage,
        "new_stage": target_stage,
        "changed": True,
        "readiness": trip.get("validation", {}).get("readiness"),
    }
