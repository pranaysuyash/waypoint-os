from __future__ import annotations

from typing import Any

_REDACTED_FIELDS = {"raw_note", "owner_note", "itinerary_text", "structured_json"}
_DECISION_BASELINE_MAP = {
    "PROCEED_TRAVELER_SAFE": 82,
    "PROCEED_INTERNAL_DRAFT": 74,
    "ASK_FOLLOWUP": 64,
    "STOP_NEEDS_REVIEW": 42,
}


def build_consented_submission(request_dict: dict[str, Any], retention_consent: bool) -> dict[str, Any]:
    if retention_consent:
        return request_dict
    return {
        key: value
        for key, value in request_dict.items()
        if key not in _REDACTED_FIELDS
    }


def collect_raw_text_sources(
    raw_note: Any,
    owner_note: Any,
    itinerary_text: Any,
    structured_json: Any,
) -> str:
    raw_text_sources = [
        raw_note,
        owner_note,
        itinerary_text,
    ]
    if isinstance(structured_json, dict):
        source_payload = structured_json.get("source_payload")
        if isinstance(source_payload, dict):
            uploaded_file = source_payload.get("uploaded_file")
            if isinstance(uploaded_file, dict):
                raw_text_sources.append(str(uploaded_file.get("extracted_text") or ""))
    return "\n".join(str(item) for item in raw_text_sources if item)


def apply_live_checker_adjustments(
    packet_payload: dict[str, Any],
    validation_payload: dict[str, Any],
    decision_payload: dict[str, Any],
    live_checker: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not live_checker:
        return packet_payload, validation_payload, decision_payload

    validation_base = validation_payload.get("overall_score")
    if not isinstance(validation_base, (int, float)):
        validation_base = validation_payload.get("quality_score")
    if not isinstance(validation_base, (int, float)):
        validation_base = packet_payload.get("quality_score")
    if not isinstance(validation_base, (int, float)):
        validation_base = packet_payload.get("score")
    if not isinstance(validation_base, (int, float)):
        decision_state = str(decision_payload.get("decision_state") or "").upper()
        decision_base = _DECISION_BASELINE_MAP.get(decision_state)
        validation_base = decision_base if decision_base is not None else 70

    adjusted_score = max(0, min(100, round(float(validation_base) - float(live_checker.get("score_penalty", 0)))))
    validation_payload["overall_score"] = adjusted_score
    validation_payload["public_checker_live_checks"] = live_checker
    decision_payload["public_checker_live_checks"] = live_checker
    decision_payload["hard_blockers"] = list(dict.fromkeys([
        *([str(item) for item in decision_payload.get("hard_blockers") or []]),
        *([str(item) for item in live_checker.get("hard_blockers") or []]),
    ]))
    decision_payload["soft_blockers"] = list(dict.fromkeys([
        *([str(item) for item in decision_payload.get("soft_blockers") or []]),
        *([str(item) for item in live_checker.get("soft_blockers") or []]),
    ]))
    packet_payload["public_checker_live_checks"] = live_checker
    packet_payload["score"] = adjusted_score
    return packet_payload, validation_payload, decision_payload
