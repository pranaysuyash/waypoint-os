from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Callable, Optional

from src.agents.risk_contracts import to_structured_risk
from src.evals.audit.public_authority import resolve_public_authority

from .feasibility_follow_up import FollowUp, SUPPLIER_SOURCES, supplier_follow_ups

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
    return "\n".join(dict.fromkeys(str(item) for item in raw_text_sources if item))


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


def overnight_hotel_finding(packet: dict[str, Any], raw_text: str) -> Optional[str]:
    """Use explicit next-day itinerary times and the outbound booking date."""
    facts = packet.get("facts") or {}
    start = (facts.get("date_start") or {}).get("value")
    origin = (facts.get("origin_city") or {}).get("value")
    destinations = (facts.get("destination_candidates") or {}).get("value")
    if not isinstance(start, str) or not isinstance(origin, str) or not isinstance(destinations, list) or len(destinations) != 1:
        return None
    try:
        departure = date.fromisoformat(start)
    except ValueError:
        return None

    clock = r"(?:[01]?\d|2[0-3]):[0-5]\d"
    leg = re.search(
        rf"\b{re.escape(origin)}[ \t]+{clock}[ \t]+to[ \t]+{re.escape(destinations[0])}"
        rf"[ \t]+(?P<arrives>{clock})[ \t]+next[ \t]+day\b",
        raw_text,
        re.IGNORECASE,
    )
    check_in = re.search(
        rf"\bhotel[ \t]+check[- ]?in[ \t]+0?{departure.day}[ \t]+"
        rf"(?:{departure:%b}|{departure:%B})(?:[ \t]+(?P<year>20\d{{2}}))?\b",
        raw_text,
        re.IGNORECASE,
    )
    if not leg or not check_in or (check_in["year"] and int(check_in["year"]) != departure.year):
        return None

    arrival = departure + timedelta(days=1)
    return (
        f"Your plan says you land at {leg['arrives']} on {arrival.day} {arrival:%B}, "
        f"after your proposed {departure.day} {departure:%B} hotel check-in date. "
        "If you book the previous night so the room is ready on arrival, "
        "tell the hotel you'll arrive after midnight and confirm it will hold the room."
    )


_GOA_DAY_PLAN_CUE = re.compile(
    r"\bek[ \t]+hi[ \t]+din\b|\b(?:same|one)[ \t]+day\b|^\s*day[ \t]+\d+[ \t]*:"
    r"|\bon\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\b",
    re.IGNORECASE,
)
_GOA_DAY_STOPS = re.compile(r"\b(?:baga|dudh[ \t]*sagar|old[ \t]+goa)\b", re.IGNORECASE)
_UPDATE = re.compile(r" (?:Correction from the traveler or operator:|The earlier note is incomplete or unreliable\. Update:) ", re.I)
_CLOCK = r"(?:[01]?\d|2[0-3]):[0-5]\d"
_DATE = r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+20\d{2})?"
_PROSE_FLIGHT = re.compile(
    rf"\b(?P<origin>[A-Z][\w-]*) to (?P<destination>[A-Z][\w-]*) flight leaves at {_CLOCK}"
    rf" on (?P<outbound>{_DATE}) and lands at (?P<arrival>{_CLOCK})(?P<rollover> (?:the )?next day)?",
    re.I,
)


_OLD_GOA_DATE_UPDATE = re.compile(
    rf"[.!;\n]\s*(?:actually\s+)?(?:we will|we'll) (?:do|visit)"
    rf" Old Goa on (?P<day>{_DATE}) instead(?=\s*[.!;\n]|\s*$)",
    re.I,
)


def _old_goa_revised_visit(raw_text: str) -> tuple[str, str] | None:
    """Recognize an explicit dated correction after an explicitly dated Goa day."""
    correction = _OLD_GOA_DATE_UPDATE.search(raw_text)
    if not correction:
        return None
    prior_clause = re.split(r"[.!?;\n]", raw_text[:correction.start()])[-1]
    original = re.search(rf"\bon (?P<day>{_DATE})", prior_clause, re.I)
    stops = {re.sub(r"\s+", "", stop.casefold()) for stop in _GOA_DAY_STOPS.findall(prior_clause)}
    if not original or stops != {"baga", "dudhsagar", "oldgoa"}:
        return None
    old_day, new_day = original["day"], correction["day"]
    dates = []
    for day in (old_day, new_day):
        parts = day.split()
        try:
            dates.append(datetime.strptime(
                f"{parts[0]} {parts[1][:3]} {parts[2] if len(parts) == 3 else '2000'}", "%d %b %Y",
            ).date())
        except ValueError:
            return None
    if (dates[0].month, dates[0].day) == (dates[1].month, dates[1].day):
        return None
    return old_day, new_day


def _prose_itinerary_evidence(packet: dict[str, Any], raw_text: str, supplier_evidence: dict[str, FollowUp],
) -> tuple[str | None, str | None]:
    """Keep scoped leg roles and partial dates when an intake summary has no slot for them."""
    base, *updates = _UPDATE.split(raw_text, maxsplit=1)
    update = updates[0] if updates else ""
    facts = packet.setdefault("facts", {})
    flight = _PROSE_FLIGHT.search(base)
    hotel = re.search(rf"\b(?:the )?(?P<night>{_DATE}) hotel night\b", base, re.I)
    if flight and hotel:
        revised = re.search(rf"\bbooking begins on (?P<night>{_DATE})", update, re.I)
        night = (revised or hotel)["night"]
        arrival_unknown = not flight["rollover"] or bool(re.search(r"no day or date", update, re.I))
        packet["itinerary_feasibility_context"] = (
            f"{flight['origin']} → {flight['destination']} · Outbound {flight['outbound']} · "
            f"Hotel night {night}"
        )
        if arrival_unknown:
            return None, f"What local date does the flight land at {flight['arrival']}?"
        if revised or night.casefold() != flight["outbound"].casefold():
            return None, "What time will the hotel make the room available on the arrival date?"
        parts = flight["outbound"].split()
        try:
            departure = datetime.strptime(f"{parts[0]} {parts[1][:3]} {parts[2] if len(parts) == 3 else '2000'}", "%d %b %Y").date()
        except ValueError:
            return None, "What is the local departure date shown on the ticket?"
        if len(parts) == 2 and departure.month == 2 and departure.day >= 28:
            return None, "What year is the outbound flight? It affects the next calendar date."
        arrival = departure + timedelta(days=1)
        return (
            f"Your flight lands at {flight['arrival']} on {arrival.day} {arrival:%B}, after the "
            f"proposed {night} hotel check-in. If booking the previous night, confirm the hotel will "
            "hold the room for an after-midnight arrival.",
            "Will the hotel hold the room until you arrive after midnight?",
        )

    stops = {re.sub(r"\s+", "", stop.casefold()) for stop in _GOA_DAY_STOPS.findall(base)}
    if stops == {"baga", "dudhsagar", "oldgoa"}:
        destination = facts.get("destination_candidates") or {}
        if destination.get("value") == ["Old Goa"]:
            facts["destination_candidates"] = {**destination, "value": ["Goa"]}
        calendar = re.search(rf"\bon (?P<day>{_DATE})", base, re.I)
        if calendar:
            packet["itinerary_feasibility_context"] = f"Goa sightseeing · Proposed visit date {calendar['day']}"
        if re.search(r"no dates", update, re.I):
            packet["itinerary_feasibility_context"] = "Goa sightseeing · Visit dates unconfirmed"
            return None, "Which day are you planning to visit Dudhsagar, Baga and Old Goa?"
        if re.search(r"move Old Goa to the next day", update, re.I):
            packet["itinerary_feasibility_context"] = "Goa sightseeing · Old Goa moved to the following day"
            return None, "What time do you expect to return from Dudhsagar before visiting Baga?"
        if revision := _old_goa_revised_visit(base):
            original_day, revised_day = revision
            packet["itinerary_feasibility_context"] = (
                f"Goa sightseeing · Baga and Dudhsagar on {original_day} · Old Goa on {revised_day}"
            )
            return None, "What time do you expect to return from Dudhsagar before visiting Baga?"
        if calendar:
            return None, "What Dudhsagar entry slot do you have, and when will you be back in Collem?"

    if re.search(r"\blands at Heathrow at .*?departs from Gatwick at\b", base, re.I):
        onward = "Heathrow" if re.search(r"depart from Heathrow", update, re.I) else "Gatwick"
        if re.search(r"only as .London", update, re.I):
            onward = "London airport unconfirmed"
        facts.pop("destination_candidates", None)
        facts.pop("destination_status", None)
        packet["itinerary_feasibility_context"] = f"Arrival airport Heathrow · Onward departure {onward}"
        if onward.startswith("London"):
            return None, "Which London airport is printed on the onward ticket?"
        return None, f"What is the onward check-in cutoff at {onward}, after collecting your checked bags?"

    if re.search(r"\barrives at Paris-CDG at .*?train leaves Gare du Nord at\b", base, re.I):
        station = "CDG Airport" if re.search(r"changes to CDG Airport station", update, re.I) else "Gare du Nord"
        if re.search(r"station cropped out", update, re.I):
            station = "unconfirmed"
        facts.pop("destination_candidates", None)
        facts.pop("destination_status", None)
        packet["itinerary_feasibility_context"] = f"Arrival airport Paris-CDG · Onward rail station {station}"
        if station == "unconfirmed":
            return None, "Which departure station is printed on the train ticket?"
        return None, f"What is the boarding cutoff for your train at {station}?"
    if supplier_evidence:
        context, question, _ = next(iter(supplier_evidence.values()))
        packet["itinerary_feasibility_context"] = context
        destination = facts.get("destination_candidates") or {}
        values = destination.get("value")
        if isinstance(values, list):
            excluded = {value.casefold() for _, _, misplaced in supplier_evidence.values() for value in misplaced}
            remaining = [value for value in values if not isinstance(value, str) or value.casefold() not in excluded]
            if remaining:
                facts["destination_candidates"] = {**destination, "value": remaining}
            else:
                facts.pop("destination_candidates", None)
                facts.pop("destination_status", None)
        return None, question
    return None, None


def goa_day_pacing_finding(packet: dict[str, Any], raw_text: str) -> Optional[str]:
    """Flag a narrowly supported same-day combination without guessing travel times."""
    destination = ((packet.get("facts") or {}).get("destination_candidates") or {}).get("value")
    if destination != ["Goa"] or _old_goa_revised_visit(raw_text):
        return None

    for clause in re.split(r"[.!?;\n]", raw_text):
        if not _GOA_DAY_PLAN_CUE.search(clause):
            continue
        stops = {re.sub(r"\s+", "", stop.casefold()) for stop in _GOA_DAY_STOPS.findall(clause)}
        if stops == {"baga", "dudhsagar", "oldgoa"}:
            return (
                "Baga, Dudhsagar and Old Goa could make for a packed day. "
                "Dudhsagar includes a separate access leg from Collem. "
                "Confirm the falls entry arrangements and when you expect to return to Collem, "
                "then check whether the transfers and time at Baga and Old Goa still fit. "
                "Your plan does not give enough timing detail to confirm all three will fit."
            )
    return None


def finalize_result_with_live_checker(
    *,
    result: Any,
    raw_text: str,
    build_live_checker_signals_fn: Callable[[dict[str, Any], str], Any],
    to_dict: Callable[[Any], Any],
    on_adjusted: Optional[Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None]] = None,
    build_entity_checks_fn: Optional[Callable[[dict[str, Any], str], list]] = None,
) -> None:
    """Apply live-check adjustments to a SpineResult in one canonical step.

    ``build_entity_checks_fn`` (Ghost Hotel Test, WOBS 2026-09-09 P1) runs after
    live-check adjustments and attaches advisory entity-existence findings to
    the packet/validation payloads under ``public_checker_entity_checks``. It
    must never raise into the pipeline: a gazetteer outage degrades to no
    entity findings, never a failed run.
    """
    packet_payload = to_dict(result.packet) if hasattr(result, "packet") else {}
    packet_payload = packet_payload or {}
    base, *updates = _UPDATE.split(raw_text, maxsplit=1)
    supplier_evidence = supplier_follow_ups(base, updates[0] if updates else "")
    prose_hotel, feasibility_question = _prose_itinerary_evidence(packet_payload, raw_text, supplier_evidence)
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
        if on_adjusted is not None:
            on_adjusted(packet_payload, validation_payload, decision_payload)

    facts = packet_payload.get("facts") or {}
    return_open = (
        (facts.get("date_confidence") or {}).get("value") == "outbound_only"
        and not (facts.get("date_end") or {}).get("value")
        and re.search(
            r"\breturn(?:[ \t]+ka)?[ \t]+date[ \t]+(?:abhi[ \t]+)?(?:decide[ \t]+nahi|undecided|tbd)\b",
            raw_text,
            re.IGNORECASE,
        )
    )
    hotel_finding = prose_hotel or overnight_hotel_finding(packet_payload, raw_text)
    pacing_finding = None if _UPDATE.search(raw_text) else goa_day_pacing_finding(packet_payload, raw_text)
    if feasibility_question:
        packet_payload["itinerary_feasibility_question"] = feasibility_question
    if return_open:
        packet_payload["public_checker_return_date_pending"] = True
    if hotel_finding:
        packet_payload["public_checker_overnight_hotel_finding"] = hotel_finding
    if pacing_finding:
        packet_payload["public_checker_day_pacing_finding"] = pacing_finding
    findings = []
    for flag, category, title, message, context, source_url in (
        (
            "overnight_hotel_arrival", "timing", "Confirm late hotel arrival", hotel_finding,
            "Overnight flight and proposed hotel check-in", None,
        ),
        (
            "goa_day_pacing", "activity", "Check whether all three stops fit", pacing_finding,
            "Baga, Dudhsagar and Old Goa day plan", "https://www.goa.gov.in/places/dudhsagar-waterfalls/",
        ),
    ):
        if message:
            findings.append(to_structured_risk(
                flag=flag,
                severity="medium",
                category=category,
                message=message,
                details={
                    "title": title, "context": context, "source_url": source_url,
                    "authority": "advisory",
                },
                detected_by="itinerary_feasibility",
            ))
    for identifier, (context, question, _) in supplier_evidence.items():
        source_url = SUPPLIER_SOURCES.get(identifier)
        if question == feasibility_question and context == packet_payload.get("itinerary_feasibility_context"):
            packet_payload["itinerary_feasibility_id"] = identifier
            if source_url:
                packet_payload["itinerary_feasibility_source_url"] = source_url
            continue
        findings.append(to_structured_risk(
            flag=identifier,
            severity="medium",
            category="routing",
            message=question,
            details={"title": context, "authority": "advisory", "source_url": source_url},
            detected_by="itinerary_feasibility",
        ))
    if findings:
        packet_payload["itinerary_feasibility_findings"] = findings
    if return_open or findings or feasibility_question:
        result.packet = packet_payload

    if build_entity_checks_fn is None:
        return

    entity_results: list = []
    try:
        entity_results = build_entity_checks_fn(packet_payload or {}, raw_text) or []
    except Exception:
        # Advisory layer: never fail a run over entity verification.
        entity_results = []
    if not entity_results:
        return

    serialized = [item.as_dict() if hasattr(item, "as_dict") else dict(item) for item in entity_results]
    packet_payload = to_dict(result.packet) if hasattr(result, "packet") else packet_payload
    validation_payload = to_dict(result.validation) if hasattr(result, "validation") else {}
    packet_payload["public_checker_entity_checks"] = serialized
    validation_payload["public_checker_entity_checks"] = serialized
    result.packet = packet_payload
    result.validation = validation_payload
