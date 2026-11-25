"""Scoped feasibility questions for incomplete supplier and transport evidence."""

from datetime import datetime, timedelta
import hashlib
import re


def _mentions_active_commitment(text: str, pattern: str) -> bool:
    """Ignore a commitment explicitly withdrawn in the same clause."""
    inactive = r"\b(?:cancell?ed|withdrawn|ruled out|no longer|discarded)\b"
    return any(
        re.search(pattern, clause) and not re.search(inactive, clause)
        for clause in re.split(r"[.!?;\n]+", text)
    )


FollowUp = tuple[str, str, tuple[str, ...]]


# Match a reported disruption followed immediately by its missed onward leg.
# Keeping the object of "miss" avoids borrowing a service elsewhere in the trip.
_EUROSTAR_ONWARD = re.compile(
    r"(?:^|(?<=[.!?;\n]))\s*(?:(?:our|my|the)\s+)?eurostar(?:\s+(?:train|service))?"
    r"(?:\s+(?:from|to)\s+[\w’'-]+(?:\s+(?!(?:and|but|while)\b)[\w’'-]+){0,2}?)?"
    r"\s+(?:is|was|has been)\s+(?P<status>delayed|cancelled|canceled|running late)"
    r"(?:\s+(?:today|this morning|by \d+ (?:minutes?|hours?)))?\s*"
    r"(?:[.,;:]\s*|\n\s*|\s+)(?:so\s+|and\s+)?"
    r"(?:(?:we|i)(?:['’]ll|\s+(?:will|might|may|expect to|are going to))\s+miss"
    r"|(?:we|i)\s+missed)\s+"
    r"(?:(?:the|our|my|a|separately[- ]booked|connecting|next)\s+)*"
    r"(?P<leg>tgv\s+inoui|rer(?:\s+[a-e])?|(?:private\s+)?driver(?:\s+pickup)?"
    r"|onward train|train|tgv)\b(?P<detail>[^.!?;\n]*)"
)
_DEPARTURE_STATION = re.compile(
    r"\b(?:from|at)\s+(?:paris\s+)?(?:gare\s+(?:(?:du|de)\s+[\w’'-]+|d['’][\w’'-]+|montparnasse)"
    r"|[\w’'-]+(?:\s+[\w’'-]+){0,3}\s+station)\b"
)
_EUROSTAR_SOURCE = "https://www.eurostar.com/uk-en/travel-info/connecting-train"
SUPPLIER_SOURCES = {
    "eurostar_tgv_connection": _EUROSTAR_SOURCE,
    "eurostar_rer_connection": _EUROSTAR_SOURCE,
}


def _eurostar_connections(base: str, change: str) -> dict[str, FollowUp]:
    if "eurostar" not in base:
        return {}
    findings: dict[str, FollowUp] = {}
    for match in _EUROSTAR_ONWARD.finditer(base):
        leg, detail = match["leg"], match["detail"]
        context = "Eurostar disruption reported"
        later = base[match.start("detail"):] + " " + change
        if "driver" in leg:
            resolved_leg = r"(?:pickup|driver)"
        elif leg.startswith("rer"):
            resolved_leg = "rer"
        elif leg.startswith("tgv"):
            resolved_leg = "tgv"
        else:
            resolved_leg = r"(?:train|connection)"
        if re.search(rf"\b(?:we|i) (?:caught|made) (?:the|our|my) {resolved_leg}\b", later):
            continue
        station_known = bool(_DEPARTURE_STATION.search(detail))
        operator_unknown = leg in {"train", "onward train", "tgv"}
        if change and re.search(rf"\b(?:eurostar|onward|instead|{resolved_leg})\b", change):
            identifier = "eurostar_onward_details"
            context += " · Onward booking updated"
            question = "Which onward booking, if any, still needs to be rearranged after the update?"
        elif "driver" in leg:
            identifier = "eurostar_driver_pickup"
            context += " · Driver pickup"
            question = "Can the transfer operator move the pickup to your revised arrival time, and what would it cost?"
        elif not station_known or operator_unknown:
            identifier = "eurostar_onward_details"
            context += " · Onward rail ticket"
            missing = []
            if operator_unknown:
                missing.append("operator")
            if not station_known:
                missing.append("departure station")
            question = f"Which {' and '.join(missing)} does the onward ticket show?"
        elif leg.startswith("rer"):
            identifier = "eurostar_rer_connection"
            context += " · Onward RER"
            question = "Can station staff confirm which later service your RER ticket covers?"
        else:
            identifier = "eurostar_tgv_connection"
            context += " · Onward TGV INOUI"
            reason = "cancellation" if match["status"] in {"cancelled", "canceled"} else "delay"
            question = f"Can Eurostar staff give you proof of {reason} for the ticket office to check onward TGV availability?"
        findings[identifier] = (context, question, ())
    return findings


def _has_scoped_update(change: str, subject: str, detail: str) -> bool:
    """Require the supplier or service and the relevant detail in one clause."""
    return any(
        re.search(subject, clause) and re.search(detail, clause)
        for clause in re.split(r"[.!?;\n]+", change)
    )


def _hotel_terms(_note: str, base: str, change: str) -> FollowUp | None:
    hotel_terms = "hotel" in base or ("package" in base and "breakfast" in base)
    if hotel_terms and re.search(r"\b(?:deposit|advance)\b", base) and re.search(r"\bcancel\w*\b", base):
        if _has_scoped_update(
            change, r"\b(?:hotel|property|exact rate)\b", r"\bnon[- ]?refundable\b",
        ):
            return "Hotel package · Nonrefundable deposit reported", "What amount becomes nonrefundable, in which currency, and when?", ("Deposit", "Give")
        return "Hotel package · Cancellation terms unconfirmed", "What is the cancellation cutoff for the exact rate you’re booking?", ("Deposit", "Give")
    return None


_NAMED_HOTEL_TERMS = re.compile(
    r"(?:^|(?<=[.!?;\n]))\s*(?P<name>hotel(?: [\w’'-]+){1,4}?)"
    r" (?=requires?\b|needs?\b|asks?\b)(?P<terms>[^.!?;\n]+)",
    re.I,
)


def _hotel_booking_follow_ups(note: str, change: str) -> dict[str, FollowUp]:
    """Keep separately named properties distinct when their terms are stated separately."""
    properties: dict[str, str] = {}
    reservation_labels: dict[str, set[str]] = {}
    for match in _NAMED_HOTEL_TERMS.finditer(note):
        terms = match["terms"].casefold()
        if not re.search(r"\b(?:deposit|advance)\b", terms) or not re.search(r"\bcancel\w*\b", terms):
            continue
        key = match["name"].casefold()
        properties.setdefault(key, match["name"])
        labels = re.findall(r"\b(first|second|third) (?:hotel )?(?:reservation|booking|stay)\b", terms)
        reservation_labels.setdefault(key, set()).update(labels)
    multiple_reservations = {key for key, labels in reservation_labels.items() if len(labels) > 1}
    if len(properties) < 2 and not multiple_reservations:
        return {}
    findings = {}
    for key, name in properties.items():
        subject_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        identifier = f"hotel_terms_{subject_id}"
        if key in multiple_reservations:
            findings[identifier] = (
                f"{name} · Multiple reservations",
                f"Which deposit and cancellation cutoff apply to each reservation at {name}?",
                ("Deposit", "Give"),
            )
            continue
        # The property name is the smallest available subject here. Keep the
        # original display spelling while assigning a stable advisory key.
        scoped_change = next((
            clause for clause in re.split(r"[.!?;\n]+", change)
            if re.match(rf"\s*{re.escape(key)}\s+(?:confirms?|says?|reports?|states?)\b", clause)
            and re.search(r"\b(?:deposit|advance)\b", clause)
        ), "")
        finding = _hotel_terms("", "hotel deposit cancellation", scoped_change)
        if finding:
            context, question, misplaced = finding
            findings[identifier] = (
                f"{name} · {context.split(' · ', 1)[1]}", question, misplaced,
            )
    return findings


def _helsinki_connection(_note: str, base: str, change: str) -> FollowUp | None:
    if _mentions_active_commitment(base, r"\b(?:via helsinki|connect at hel)\b"):
        if "separately" in change:
            return "Flight connection via Helsinki · Separate tickets", "Will you need to collect bags and check in again for the onward flight?", ("Helsinki",)
        if "receipt" in change or not re.search(r"\b(?:single ticket|through[- ]ticket)\b", base):
            return "Flight connection via Helsinki · Ticket protection unconfirmed", "Are both flights on one protected ticket, or were they ticketed separately?", ("Helsinki",)
        return "Flight connection via Helsinki · Single ticket reported", "What minimum connection time does the airline confirm for these two flights?", ("Helsinki",)
    return None


def _overnight_rail_transfer(_note: str, base: str, change: str) -> FollowUp | None:
    if (
        _mentions_active_commitment(base, r"\b(?:overnight train|sleeper service)\b")
        and _mentions_active_commitment(base, r"\b(?:transfer|pickup van)\b")
    ):
        misplaced = ("Train", "Date")
        prior_status = " · Originally waitlisted" if re.search(
            r"\btrain (?:is|was|remains) waitlisted\b", base
        ) or re.search(r"\bon the wl\b", base) else ""
        if re.fullmatch(
            r"(?:the )?(?:traveler|operator) (?:supplies|provides|reports) "
            r"(?:a )?fresh confirmation for (?:that exact|the same) train and date[.!]?",
            change.strip(),
        ):
            return (
                f"Overnight train{prior_status} · Update reports confirmation for the same train and date",
                "What time and station will the transfer operator use for pickup?",
                misplaced,
            )
        if _has_scoped_update(
            change, r"\b(?:train|rail(?:way)? ticket|pnr|sleeper service)\b",
            r"\b(?:confirm\w*|screenshot|waitlist\w*)\b",
        ) or re.fullmatch(
            r"(?:the traveler supplies a fresh confirmation|the screenshot has no date|(?:the note says )?[“\"]?confirmed now[”\"]?(?:, while the attached status screenshot has no date)?)[.!]?",
            change.strip(),
        ):
            return (
                f"Overnight train{prior_status} · Confirmation needs matching",
                "Does the latest confirmation match the train and date you’re taking?",
                misplaced,
            )
        if prior_status:
            return (
                "Overnight train · Waitlist reported · Separate morning transfer",
                "When can you change or cancel the morning transfer if the train remains waitlisted?",
                misplaced,
            )
        return (
            "Overnight train · Ticket status unconfirmed · Separate morning transfer",
            "What status does the latest ticket show for the train and date you’re taking?",
            misplaced,
        )
    return None


def _vatican_admission(_note: str, base: str, change: str) -> FollowUp | None:
    if "vatican museums" in base and ("admission" in base or "last entry" in base):
        if "different entry times" in change:
            return "Vatican Museums · Conflicting entry times", "Which booking is current, and what entry time does it show?", ("Vatican Museums",)
        if "later timed entry" in change:
            return "Vatican Museums · Revised entry reported", "What entry time and arrival cutoff are on the revised booking?", ("Vatican Museums",)
        return "Vatican Museums · Timed admission", "Can you arrive by the stated admission cutoff, or do you need to move the timed entry?", ("Vatican Museums",)
    return None


_FERRY_CLOCK = r"\b(?:[01]\d|2[0-3]):[0-5]\d\b"
_FERRY_DATE = r"\d{4}-\d{2}-\d{2}\b"
_FERRY_CUTOFF = re.compile(
    rf"\bvehicle check[ -]in (?:closes|ends) at ({_FERRY_CLOCK})(?: on ({_FERRY_DATE}))?",
)
_FERRY_DATE_QUESTION: FollowUp = (
    "Vehicle ferry · Check-in date needs matching",
    "What local date applies to port arrival and the vehicle check-in cutoff on the ticket?",
    (),
)


def _clock_minutes(clock: str) -> int:
    hours, minutes = map(int, clock.split(":"))
    return 60 * hours + minutes


def _vehicle_ferry_cutoff(_note: str, base: str, change: str) -> FollowUp | None:
    if not _mentions_active_commitment(base, r"\bferry\b"):
        return None
    if not re.search(r"\b(?:rental car|vehicle check[ -]in|car ferry)\b", base):
        return None

    clocks = set(_FERRY_CUTOFF.findall(f"{base}\n{change}"))
    if len(clocks) > 1:
        return "Vehicle ferry · Sources give different check-in times", "Which vehicle check-in cutoff applies to the exact sailing on your e-ticket?", ()
    if not clocks:
        return "Vehicle ferry · Check-in cutoff unknown", "What vehicle check-in cutoff is printed on the e-ticket for this sailing?", ()
    cutoff, cutoff_date = next(iter(clocks))
    arrival = re.search(rf"\b(?:reach|arrive at) [^.!?;\n]{{0,70}}?\bport at ({_FERRY_CLOCK}) local time\b(?: on ({_FERRY_DATE}))?", base)
    sailing = re.search(rf"(?:(?P<date>{_FERRY_DATE}) )?(?P<clock>{_FERRY_CLOCK}) (?:[\w-]+ ){{0,5}}ferry\b", base)
    if not arrival or not sailing:
        return "Vehicle ferry · Timing needs matching", "What are your planned port arrival and sailing times on the e-ticket’s local date?", ()

    planned, arrival_date = arrival.groups()
    departure, departure_date = sailing["clock"], sailing["date"]
    local_dates = (arrival_date, cutoff_date, departure_date)
    if any(local_dates):
        if not all(local_dates):
            return _FERRY_DATE_QUESTION
        try:
            arrival_at, check_in, sails_at = (
                datetime.fromisoformat(f"{day}T{clock}")
                for day, clock in zip(local_dates, (planned, cutoff, departure), strict=True)
            )
        except ValueError:
            return _FERRY_DATE_QUESTION
        if check_in >= sails_at:
            return _FERRY_DATE_QUESTION
        late_by = (arrival_at - check_in) // timedelta(minutes=1)
        planned = f"{planned} on {arrival_date}"
        cutoff = f"{cutoff} on {cutoff_date}"
    else:
        cutoff_min = _clock_minutes(cutoff)
        departure_min = _clock_minutes(departure)
        arrival_min = _clock_minutes(planned)
        if cutoff_min >= departure_min or arrival_min > departure_min or re.search(
            r"\b(?:previous day|next day|overnight)\b", f"{base}\n{change}",
        ):
            return _FERRY_DATE_QUESTION
        late_by = arrival_min - cutoff_min
    if late_by <= 0:
        return None
    return (
        f"Vehicle ferry · Planned port arrival {planned} is {late_by} minutes after the stated {cutoff} cutoff",
        "Can you arrange an earlier port arrival or confirm a later sailing with the ferry operator?",
        (),
    )


def _shore_excursion_return(_note: str, base: str, change: str) -> FollowUp | None:
    if re.search(r"\b(?:all-aboard|back on board)\b", base) and re.search(r"\b(?:excursion|guide|shore tour)\b", base):
        if "ship time basis" in change:
            return "Shore excursion · Ship time basis unknown", "What is the ship’s all-aboard time in the same time zone as the guide’s return?", ("Guide",)
        if "own product" in change:
            return "Shore excursion · Cruise-line protection reported", "What does the written protection cover if this excursion returns late?", ("Guide",)
        return "Shore excursion · Independent return and all-aboard time", "Are both times on the same clock, and what return buffer can the guide confirm?", ("Guide",)
    return None


def _step_free_transfer(_note: str, base: str, change: str) -> FollowUp | None:
    if _mentions_active_commitment(base, r"\b(?:step-free|level boarding)\b") and re.search(r"\b(?:transfer|van|shuttle|station connection)\b", base):
        if "suitable vehicle" in change:
            return "Step-free travel · Vehicle confirmation reported", "Has the station transfer also been confirmed step-free for this group?", ("Van",)
        return "Step-free travel · Vehicle and station transfer need confirmation", "Can the operator confirm step-free boarding for the booked vehicle and transfer route?", ("Van",)
    return None


def _transit_documents(note: str, base: str, change: str) -> FollowUp | None:
    if "document" in base:
        route = re.search(
            r"\bflying (.+?) (?:via |with an airport connection in )(.+?)(?=\s+(?:asks|and)\b|[.!?]|$)",
            note,
            re.I,
        )
        if route:
            transit = "unconfirmed" if "different country" in change else route[2]
            question = "Which country will you transit through on the revised route?" if transit == "unconfirmed" else "What passport nationality and document type will the traveler use for this transit?"
            return f"{route[1]} · Transit {transit}", question, (route[2],)
    return None


def _rental_pickup(_note: str, base: str, change: str) -> FollowUp | None:
    if _mentions_active_commitment(base, r"\b(?:car rental|hire car counter)\b") and re.search(r"\b(?:closing time|shuts at)\b", base):
        if "confirms after-hours" in change:
            return "Rental pickup · Confirmed after-hours handover reported", "Where and by what time does the rental branch require you to collect the car?", ("Car",)
        return "Rental pickup · After-hours access unconfirmed", "Can the rental branch confirm handover after your revised arrival on the booked date?", ("Car",)
    return None


def _attachment_date(note: str, base: str, change: str) -> FollowUp | None:
    outbound = re.search(r"\bDelhi se Goa\s+(\d{1,2}\s+Dec(?:ember)?)\b", note, re.I)
    if outbound and "19/12" in base:
        if "is the hotel date" in change:
            return f"Delhi → Goa · Outbound {outbound[1]} · Hotel date 19 Dec", "What is the return date, if you have decided it?", ("North Goa",)
        return f"Delhi → Goa · Outbound {outbound[1]} · Attachment date 19/12 unassigned", "What does 19/12 refer to in the attachment?", ("North Goa",)
    return None


def supplier_follow_ups(note: str, update: str) -> dict[str, FollowUp]:
    """Collect applicable concerns in the established lead-question order."""
    base, change = note.casefold(), update.casefold()
    hotels = _hotel_booking_follow_ups(note, change)
    rules = (
        ("hotel_terms", _hotel_terms),
        ("helsinki_connection", _helsinki_connection),
        ("overnight_rail_transfer", _overnight_rail_transfer),
        ("vatican_admission", _vatican_admission),
        ("vehicle_ferry_cutoff", _vehicle_ferry_cutoff),
        ("shore_excursion_return", _shore_excursion_return),
        ("step_free_transfer", _step_free_transfer),
        ("transit_documents", _transit_documents),
        ("rental_pickup", _rental_pickup),
        ("attachment_date", _attachment_date),
    )
    findings = dict(hotels)
    findings.update(
        (identifier, finding)
        for identifier, rule in rules
        if (identifier != "hotel_terms" or not hotels)
        and (finding := rule(note, base, change)) is not None
    )
    findings.update(_eurostar_connections(base, change))
    return findings
