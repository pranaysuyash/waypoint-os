from __future__ import annotations

from typing import Any

from src.evals.audit.public_authority import resolve_public_authority

_REDACTED_FIELDS = {"raw_note", "owner_note", "itinerary_text", "structured_json"}
_DECISION_BASELINE_MAP = {
    "PROCEED_TRAVELER_SAFE": 82,
    "PROCEED_INTERNAL_DRAFT": 74,
    "ASK_FOLLOWUP": 64,
    "STOP_NEEDS_REVIEW": 42,
}


def _attach_d6_public_authority(live_checker: dict[str, Any]) -> dict[str, Any]:
    """Attach D6 public-surface authority metadata to live-check findings."""
    if not live_checker:
        return live_checker

    enriched = dict(live_checker)
    structured_risks = [item for item in (enriched.get("structured_risks") or []) if isinstance(item, dict)]

    raw_hard_blockers = [str(item) for item in enriched.get("hard_blockers") or []]
    raw_soft_blockers = [str(item) for item in enriched.get("soft_blockers") or []]

    category_statuses: dict[str, str] = {}
    category_authority: dict[str, str] = {}
    category_authority_source: dict[str, str] = {}
    category_authority_reasons: dict[str, list[str]] = {}
    normalized_risks: list[dict[str, Any]] = []
    authoritative_messages: set[str] = set()

    for risk in structured_risks:
        category = str(risk.get("category") or "unknown")
        authority_decision = resolve_public_authority(category)
        status = authority_decision.category_status
        authority = authority_decision.authority
        category_statuses[category] = status
        category_authority[category] = authority
        category_authority_source[category] = authority_decision.source
        category_authority_reasons[category] = list(authority_decision.reasons)

        normalized_risks.append(
            {
                **risk,
                "d6_category_status": status,
                "public_surface_authority": authority,
                "public_surface_authority_source": authority_decision.source,
            }
        )
        if authority == "authoritative":
            message = str(risk.get("message") or "").strip()
            if message:
                authoritative_messages.add(message)

    authoritative_hard = [item for item in raw_hard_blockers if item in authoritative_messages]
    authoritative_soft = [item for item in raw_soft_blockers if item in authoritative_messages]
    advisory_hard = [item for item in raw_hard_blockers if item not in authoritative_messages]
    advisory_soft = [item for item in raw_soft_blockers if item not in authoritative_messages]

    enriched["structured_risks"] = normalized_risks
    enriched["d6_public_surface"] = {
        "category_status": category_statuses,
        "category_authority": category_authority,
        "category_authority_source": category_authority_source,
        "category_authority_reasons": category_authority_reasons,
        "authoritative_hard_blockers": authoritative_hard,
        "authoritative_soft_blockers": authoritative_soft,
        "advisory_hard_blockers": advisory_hard,
        "advisory_soft_blockers": advisory_soft,
    }
    return enriched


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
    live_checker = _attach_d6_public_authority(live_checker)

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
    d6_public_surface = live_checker.get("d6_public_surface") if isinstance(live_checker.get("d6_public_surface"), dict) else {}
    authoritative_hard = [str(item) for item in d6_public_surface.get("authoritative_hard_blockers") or []]
    authoritative_soft = [str(item) for item in d6_public_surface.get("authoritative_soft_blockers") or []]
    advisory_hard = [str(item) for item in d6_public_surface.get("advisory_hard_blockers") or []]
    advisory_soft = [str(item) for item in d6_public_surface.get("advisory_soft_blockers") or []]

    decision_payload["hard_blockers"] = list(dict.fromkeys([
        *([str(item) for item in decision_payload.get("hard_blockers") or []]),
        *authoritative_hard,
    ]))
    decision_payload["soft_blockers"] = list(dict.fromkeys([
        *([str(item) for item in decision_payload.get("soft_blockers") or []]),
        *authoritative_soft,
    ]))
    decision_payload["advisory_hard_blockers"] = list(dict.fromkeys([
        *([str(item) for item in decision_payload.get("advisory_hard_blockers") or []]),
        *advisory_hard,
    ]))
    decision_payload["advisory_soft_blockers"] = list(dict.fromkeys([
        *([str(item) for item in decision_payload.get("advisory_soft_blockers") or []]),
        *advisory_soft,
    ]))
    packet_payload["public_checker_live_checks"] = live_checker
    packet_payload["score"] = adjusted_score
    return packet_payload, validation_payload, decision_payload
