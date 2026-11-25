"""Carry Phase 8 evidence across the stored-trip boundary and verify it on reopen."""

import hashlib
import json

from src.intake.safety import TRAVELER_DRAFT_CHECK_VERSION, traveler_draft_digest


def _source_digest(trip: dict) -> str:
    # Bind only retained inquiry content, facts and the producing run. Assignment,
    # bookings and other operational writes should not expire an unchanged draft.
    submission = (trip.get("raw_input") or {}).get("submission") or {}
    source = {key: submission.get(key) for key in ("raw_note", "owner_note", "itinerary_text", "structured_json")}
    facts = (trip.get("extracted") or {}).get("facts") or {}
    payload = json.dumps(
        [trip["run_id"], trip.get("stage"), source, facts],
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def trip_safety(trip: dict, *, bind_source: bool = False) -> dict | None:
    """Preserve aggregate diagnostics. Surface a scoped check only for its exact inputs."""
    if not isinstance(trip.get("safety"), dict):
        return None
    safety = dict(trip["safety"])
    check = safety.pop("draft_check", None)
    stored_source = safety.pop("draft_check_source_sha256", None)
    if not trip.get("run_id") or not isinstance(check, dict):
        return safety or None
    if type(check.get("version")) is not int or check["version"] != TRAVELER_DRAFT_CHECK_VERSION:
        return safety or None
    bundle = trip.get("traveler_bundle") or {}
    decision = trip.get("decision") or {}
    if not isinstance(bundle, dict) or not isinstance(decision, dict):
        return safety or None
    digest = traveler_draft_digest(bundle, decision.get("decision_state"), decision.get("operating_mode"))
    leaks = safety.get("traveler_bundle_leaks")
    if not digest or digest != check.get("digest_sha256") or not isinstance(leaks, list):
        return safety or None
    if check.get("status") != ("failed" if leaks else "passed"):
        return safety or None
    source = _source_digest(trip)
    if bind_source or stored_source == source:
        safety["draft_check"] = check
        if bind_source:
            safety["draft_check_source_sha256"] = source
    return safety or None
