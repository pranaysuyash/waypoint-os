"""
src/decision/constraint_engine.py — Spatial-Temporal & Regulatory Constraint Satisfaction Engine.

Authoritative implementation of PER-0711 (Constraint-Satisfaction Designer) & PER-0706.
Guarantees that physical, temporal, regulatory, and capacity feasibility strictly precedes
optimization and client presentation.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from src.schemas.constraints import (
    ConstraintCategory,
    ConstraintEvaluationReport,
    ConstraintType,
    ConstraintViolation,
)
from src.schemas.journey_graph import JourneyDependencyGraph, NodeType

# Recognised Schengen area countries and major gateway destinations
SCHENGEN_DESTINATIONS = {
    "france", "paris", "nice", "lyon", "mrs", "nce", "cdg", "ory",
    "italy", "rome", "florence", "venice", "milan", "amalfi", "fco", "mxp", "vce",
    "spain", "barcelona", "madrid", "seville", "mallorca", "bcn", "mad",
    "germany", "berlin", "munich", "frankfurt", "fra", "muc", "ber",
    "greece", "athens", "santorini", "mykonos", "crete", "ath", "jtr", "jmz",
    "switzerland", "zurich", "geneva", "interlaken", "zrh", "gva",
    "austria", "vienna", "salzburg", "vie",
    "portugal", "lisbon", "porto", "lis", "opo",
    "netherlands", "amsterdam", "ams",
    "belgium", "brussels", "bruges", "bru",
    "norway", "oslo", "sweden", "stockholm", "denmark", "copenhagen",
    "finland", "helsinki", "iceland", "reykjavik",
    "czech republic", "prague", "hungary", "budapest",
    "poland", "warsaw", "krakow",
}

# Granular Airport Terminal-to-Terminal MCT Matrix (in minutes)
TERMINAL_MCT_MATRIX: Dict[Tuple[str, str, str], int] = {
    # LHR (London Heathrow)
    ("LHR", "T2", "T2"): 45,
    ("LHR", "T3", "T3"): 45,
    ("LHR", "T4", "T4"): 45,
    ("LHR", "T5", "T5"): 60,
    ("LHR", "T2", "T3"): 60,
    ("LHR", "T3", "T2"): 60,
    ("LHR", "T2", "T5"): 90,
    ("LHR", "T5", "T2"): 90,
    ("LHR", "T3", "T5"): 90,
    ("LHR", "T5", "T3"): 90,
    ("LHR", "T4", "T5"): 105,
    ("LHR", "T5", "T4"): 105,
    # CDG (Paris Charles de Gaulle)
    ("CDG", "2E", "2F"): 75,
    ("CDG", "2F", "2E"): 75,
    ("CDG", "2E", "2E"): 45,
    ("CDG", "2F", "2F"): 45,
    ("CDG", "1", "2E"): 90,
    ("CDG", "2E", "1"): 90,
    # JFK (New York John F. Kennedy)
    ("JFK", "T4", "T4"): 45,
    ("JFK", "T8", "T8"): 45,
    ("JFK", "T4", "T8"): 90,
    ("JFK", "T8", "T4"): 90,
    ("JFK", "T4", "T7"): 75,
    # NRT (Tokyo Narita)
    ("NRT", "T1", "T2"): 60,
    ("NRT", "T2", "T1"): 60,
}


# --- TS-01 ground-access feasibility families (2026-09-09) -------------------
#
# Transport modes whose END is an "arrival" that gates downstream ground
# commitments (activities, meals, hotel check-ins).
TRANSPORT_ARRIVAL_TYPES: Set[Any] = {
    NodeType.FLIGHT,
    NodeType.RAIL,
    NodeType.RAIL_HIGH_SPEED,
    NodeType.FERRY,
    NodeType.CRUISE,
}

# Nodes that represent a ground commitment the traveler must physically
# reach after arriving (the "lands 10:40, Disney 11:00" family).
GROUND_COMMITMENT_TYPES: Set[Any] = {
    NodeType.ACTIVITY,
    NodeType.RESTAURANT,
    NodeType.HOTEL_CHECKIN,
}

# Heuristic default minutes from transport arrival to a ground commitment
# when the node carries no explicit transfer requirement. FLIGHT includes
# immigration + baggage + city transfer; rail/ferry/cruise include station
# exit only. These defaults produce SOFT (advisory) violations — only an
# explicit per-node requirement can produce a hard physical reject.
GROUND_ACCESS_DEFAULT_MINUTES: Dict[str, int] = {
    NodeType.FLIGHT.value: 90,
    NodeType.RAIL.value: 45,
    NodeType.RAIL_HIGH_SPEED.value: 45,
    NodeType.FERRY.value: 45,
    NodeType.CRUISE.value: 45,
}


def _as_utc(value: datetime) -> datetime:
    """Normalize naive datetimes to UTC so mixed-provenance nodes never crash comparisons."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _node_required_transfer_minutes(node: Any) -> Optional[int]:
    """Explicit ground-transfer requirement declared by the node itself.

    Honors the TimedEntrySlot vocabulary (``recommended_arrival_buffer_minutes``)
    and the planner-facing ``required_transfer_minutes``. Returns ``None`` when
    the node declares nothing — the caller then falls back to heuristic
    defaults, which can only ever yield an advisory, never a hard reject.
    """
    for key in ("required_transfer_minutes", "recommended_arrival_buffer_minutes"):
        raw = node.metadata.get(key)
        if raw is None:
            continue
        try:
            minutes = int(raw)
        except (TypeError, ValueError):
            continue
        if minutes >= 0:
            return minutes
    return None


def _node_room_capacity(node: Any) -> Optional[int]:
    """Maximum guest capacity a hotel node declares, or None when unknown.

    Recognized metadata shapes (abstains on anything unrecognized):
    - ``max_guests`` / ``capacity``: int
    - ``room_count`` + ``max_occupancy_per_room``: product
    - ``rooms``: list of ints, list of ``{"max_occupancy"|"capacity": int}``,
      or a bare int room count (then requires ``max_occupancy_per_room``)
    """
    meta = node.metadata or {}

    def _to_int(raw: Any) -> Optional[int]:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if value >= 0 else None

    for key in ("max_guests", "capacity"):
        if key in meta:
            value = _to_int(meta.get(key))
            if value is not None:
                return value

    per_room = _to_int(meta.get("max_occupancy_per_room"))
    room_count = _to_int(meta.get("room_count"))
    rooms_raw = meta.get("rooms")

    if rooms_raw is not None:
        if isinstance(rooms_raw, (int, float)):
            count = _to_int(rooms_raw)
            if count is not None and per_room is not None:
                return count * per_room
            return None
        if isinstance(rooms_raw, list):
            total = 0
            matched_any = False
            for entry in rooms_raw:
                if isinstance(entry, dict):
                    value = _to_int(entry.get("max_occupancy") or entry.get("capacity"))
                else:
                    value = _to_int(entry)
                if value is None:
                    continue
                total += value
                matched_any = True
            if matched_any:
                return total
            if room_count is not None and per_room is not None:
                return room_count * per_room
            return None

    if room_count is not None and per_room is not None:
        return room_count * per_room
    return None


def _node_declared_pax(node: Any) -> Optional[int]:
    """Traveler count a node claims to cover (ticket / booking pax), if declared."""
    meta = node.metadata or {}
    for key in ("traveler_count", "pax", "passenger_count"):
        if key in meta:
            try:
                value = int(meta[key])
            except (TypeError, ValueError):
                continue
            if value > 0:
                return value
    return None


def _node_age_bounds(node: Any) -> Tuple[Optional[int], Optional[int]]:
    """(min_age, max_age) product rules a node declares, e.g. fare or ticketed-entry age categories."""
    meta = node.metadata or {}
    bounds: List[Optional[int]] = []
    for key in ("min_age", "child_fare_min_age", "infant_max_age"):
        raw = meta.get(key)
        try:
            bounds.append(int(raw) if raw is not None else None)
        except (TypeError, ValueError):
            bounds.append(None)
    min_age = bounds[0]
    if min_age is None:
        min_age = bounds[1]
    # infant_max_age expresses "this product only covers ages <= X"
    max_age = bounds[2]
    if "max_age" in meta:
        try:
            max_age = int(meta["max_age"])
        except (TypeError, ValueError):
            pass
    return min_age, max_age


class ConstraintEngine:
    """Deterministic Constraint Satisfaction Engine for Travel Itineraries."""

    @classmethod
    def calculate_schengen_rolling_90_180(
        cls,
        historical_stays: List[Tuple[date, date]],
        planned_stay: Tuple[date, date],
    ) -> Dict[str, Any]:
        """
        Calculates exact day-by-day Schengen stay count over a sliding 180-day rolling window.
        Returns whether stay is compliant, maximum days accumulated in any 180-day window,
        and the earliest date of violation if any.
        """
        # Collect all individual historical Schengen stay dates
        schengen_dates: Set[date] = set()
        for start_d, end_d in historical_stays:
            curr = start_d
            while curr <= end_d:
                schengen_dates.add(curr)
                curr += timedelta(days=1)

        # Iterate through each day of the planned stay
        plan_start, plan_end = planned_stay
        max_accumulated = 0
        violation_date: Optional[date] = None
        violation_count = 0

        curr_plan = plan_start
        while curr_plan <= plan_end:
            schengen_dates.add(curr_plan)
            # Count how many days in [curr_plan - 179 days, curr_plan] are in schengen_dates
            window_start = curr_plan - timedelta(days=179)
            days_in_window = sum(1 for d in range(180) if (window_start + timedelta(days=d)) in schengen_dates)

            if days_in_window > max_accumulated:
                max_accumulated = days_in_window

            if days_in_window > 90 and violation_date is None:
                violation_date = curr_plan
                violation_count = days_in_window

            curr_plan += timedelta(days=1)

        is_valid = max_accumulated <= 90
        return {
            "is_valid": is_valid,
            "max_days_in_any_180_window": max_accumulated,
            "max_allowed_days": 90,
            "overstay_days": max(0, max_accumulated - 90),
            "earliest_violation_date": violation_date.isoformat() if violation_date else None,
            "recommendation": (
                "Compliant with Schengen 90/180-day short-stay rule."
                if is_valid
                else f"Overstay detected on {violation_date}: {violation_count} days in 180-day window. Reduce planned stay by {max_accumulated - 90} days or obtain Type-D Visa."
            ),
        }

    @classmethod
    def get_terminal_mct(
        cls,
        airport_code: str,
        from_terminal: Optional[str],
        to_terminal: Optional[str],
        is_international: bool = True,
    ) -> int:
        """Returns exact terminal-to-terminal minimum connect time in minutes."""
        if from_terminal and to_terminal:
            key = (airport_code.upper(), from_terminal.upper(), to_terminal.upper())
            if key in TERMINAL_MCT_MATRIX:
                return TERMINAL_MCT_MATRIX[key]
        # Default standard fallback
        return 90 if is_international else 45

    @classmethod
    def evaluate_itinerary_graph(
        cls,
        graph: JourneyDependencyGraph,
        travelers: Optional[List[Dict[str, Any]]] = None,
        budget_cents: Optional[int] = None,
        hard_budget_ceiling: bool = False,
        party_size: Optional[int] = None,
    ) -> ConstraintEvaluationReport:
        """Evaluate all hard and soft constraints across a JourneyDependencyGraph.

        ``party_size`` lets callers without per-traveler detail (e.g. the
        proposal compiler, which only knows a count) still participate in
        occupancy and pax checks. When both ``travelers`` and ``party_size``
        are supplied, the traveler list wins.
        """
        trip_id = graph.trip_id
        hard_violations: List[ConstraintViolation] = []
        soft_violations: List[ConstraintViolation] = []
        relaxation_hierarchy: List[Dict[str, Any]] = []

        now_iso = datetime.now(timezone.utc).isoformat()

        # Sort nodes chronologically
        sorted_nodes = sorted(graph.nodes.values(), key=lambda n: n.start_time)

        # 1. Temporal MCT & Connection Feasibility Checks
        for i in range(len(sorted_nodes) - 1):
            curr_node = sorted_nodes[i]
            next_node = sorted_nodes[i + 1]

            # If adjacent nodes are connecting flights or flight -> transfer
            if curr_node.node_type == NodeType.FLIGHT and next_node.node_type in (NodeType.FLIGHT, NodeType.TRANSFER):
                buffer_minutes = int((next_node.start_time - curr_node.end_time).total_seconds() / 60.0)
                is_international = "international" in curr_node.title.lower() or "international" in next_node.title.lower()

                # Check for granular terminal MCT if available
                airport = curr_node.location[:3].upper() if len(curr_node.location) >= 3 else "LHR"
                from_term = curr_node.metadata.get("terminal")
                to_term = next_node.metadata.get("terminal")
                min_mct = cls.get_terminal_mct(airport, from_term, to_term, is_international=is_international)

                if buffer_minutes < 0:
                    # Impossible overlap (teleportation)
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id=f"SPATIAL_OVERLAP_{curr_node.node_id}_{next_node.node_id}",
                            name="Impossible Temporal/Spatial Overlap",
                            category=ConstraintCategory.SPATIAL_CONTINUITY,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[curr_node.node_id, next_node.node_id],
                            description=(
                                f"Departure of {next_node.title} ({next_node.start_time.strftime('%H:%M')}) "
                                f"occurs before arrival of {curr_node.title} ({curr_node.end_time.strftime('%H:%M')})."
                            ),
                            relaxation_option=f"Shift {next_node.title} to start at least {min_mct}m after {curr_node.end_time.strftime('%H:%M')}.",
                        )
                    )
                elif buffer_minutes < min_mct:
                    # MCT deficit
                    deficit = min_mct - buffer_minutes
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id=f"MCT_DEFICIT_{curr_node.node_id}_{next_node.node_id}",
                            name="Minimum Connect Time (MCT) Deficit",
                            category=ConstraintCategory.TEMPORAL_MCT,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[curr_node.node_id, next_node.node_id],
                            description=(
                                f"Layover between {curr_node.title} and {next_node.title} is {buffer_minutes}m, "
                                f"which is {deficit}m below the required {min_mct}m minimum connect time."
                            ),
                            relaxation_option=f"Re-book connection on next departure at least {deficit}m later.",
                        )
                    )
                elif buffer_minutes < min_mct + 30:
                    # Soft warning for tight layover
                    soft_violations.append(
                        ConstraintViolation(
                            constraint_id=f"TIGHT_LAYOVER_{curr_node.node_id}",
                            name="Tight Connection Layover",
                            category=ConstraintCategory.TEMPORAL_PACING,
                            constraint_type=ConstraintType.SOFT,
                            severity="warning",
                            affected_elements=[curr_node.node_id, next_node.node_id],
                            description=f"Layover is {buffer_minutes}m. Meets legal MCT ({min_mct}m) but leaves minimal buffer for gate transfers.",
                            relaxation_option="Consider booking flight with >= 2hr buffer for comfortable transit.",
                        )
                    )

        # 1b. Ground-Access Feasibility: transport arrival -> ground commitment
        # (TS-01, 2026-09-09). The "flight lands 10:40, Disney at 11:00,
        # 70-minute transfer" family. Only an explicit per-node transfer
        # requirement (or a negative gap, i.e. physically starting before the
        # arrival) can produce a HARD reject; heuristic defaults stay advisory.
        for i in range(len(sorted_nodes) - 1):
            curr_node = sorted_nodes[i]
            next_node = sorted_nodes[i + 1]

            if curr_node.node_type not in TRANSPORT_ARRIVAL_TYPES:
                continue
            if next_node.node_type not in GROUND_COMMITMENT_TYPES:
                continue
            if curr_node.end_time is None or next_node.start_time is None:
                continue

            gap_minutes = int(
                (_as_utc(next_node.start_time) - _as_utc(curr_node.end_time)).total_seconds() / 60.0
            )
            explicit_required = _node_required_transfer_minutes(next_node)
            mode_default = GROUND_ACCESS_DEFAULT_MINUTES.get(str(curr_node.node_type))
            heuristic_required = (
                explicit_required if explicit_required is not None else mode_default
            )

            if gap_minutes < 0:
                hard_violations.append(
                    ConstraintViolation(
                        constraint_id=f"GROUND_OVERLAP_{curr_node.node_id}_{next_node.node_id}",
                        name="Ground Commitment Starts Before Arrival",
                        category=ConstraintCategory.SPATIAL_CONTINUITY,
                        constraint_type=ConstraintType.HARD,
                        severity="blocking",
                        affected_elements=[curr_node.node_id, next_node.node_id],
                        description=(
                            f"{next_node.title} starts at {next_node.start_time.strftime('%H:%M')} "
                            f"but {curr_node.title} does not arrive until {curr_node.end_time.strftime('%H:%M')}. "
                            "The commitment is scheduled before the traveler can physically be there."
                        ),
                        relaxation_option=(
                            f"Move {next_node.title} to start after {curr_node.end_time.strftime('%H:%M')} "
                            "plus the required ground transfer time."
                        ),
                    )
                )
            elif explicit_required is not None and gap_minutes < explicit_required:
                deficit = explicit_required - gap_minutes
                hard_violations.append(
                    ConstraintViolation(
                        constraint_id=f"GROUND_ACCESS_DEFICIT_{curr_node.node_id}_{next_node.node_id}",
                        name="Ground Transfer Time Deficit",
                        category=ConstraintCategory.SPATIAL_CONTINUITY,
                        constraint_type=ConstraintType.HARD,
                        severity="blocking",
                        affected_elements=[curr_node.node_id, next_node.node_id],
                        description=(
                            f"Only {gap_minutes}m between arrival of {curr_node.title} "
                            f"({curr_node.end_time.strftime('%H:%M')}) and {next_node.title} "
                            f"({next_node.start_time.strftime('%H:%M')}), but the node requires "
                            f"{explicit_required}m of ground transfer."
                        ),
                        relaxation_option=(
                            f"Shift {next_node.title} at least {deficit}m later, or arrange a faster transfer."
                        ),
                    )
                )
            elif heuristic_required is not None and gap_minutes < heuristic_required:
                soft_violations.append(
                    ConstraintViolation(
                        constraint_id=f"GROUND_BUFFER_TIGHT_{curr_node.node_id}_{next_node.node_id}",
                        name="Tight Ground-Access Buffer",
                        category=ConstraintCategory.TEMPORAL_PACING,
                        constraint_type=ConstraintType.SOFT,
                        severity="advisory",
                        affected_elements=[curr_node.node_id, next_node.node_id],
                        description=(
                            f"Only {gap_minutes}m between arrival of {curr_node.title} and "
                            f"{next_node.title}. Typical {str(curr_node.node_type).lower()} "
                            f"egress (exit, baggage, city transfer) needs ~{heuristic_required}m."
                        ),
                        relaxation_option=(
                            f"Consider starting {next_node.title} at least {heuristic_required}m "
                            "after arrival, or declare an explicit required_transfer_minutes "
                            "on the node to make this check authoritative."
                        ),
                    )
                )

        # 1c. First-Night Lodging Coverage (TS-01). If the traveler arrives on
        # date D but the first hotel check-in at that destination begins on a
        # later date, the arrival night has no accommodation.
        arrival_nodes = [n for n in sorted_nodes if n.node_type in TRANSPORT_ARRIVAL_TYPES and n.end_time is not None]
        checkin_nodes = [n for n in sorted_nodes if n.node_type == NodeType.HOTEL_CHECKIN and n.start_time is not None]
        for checkin in checkin_nodes:
            prior_arrivals = [a for a in arrival_nodes if _as_utc(a.end_time) <= _as_utc(checkin.start_time)]
            if not prior_arrivals:
                continue
            first_arrival = min(prior_arrivals, key=lambda a: _as_utc(a.end_time))
            arrival_day = _as_utc(first_arrival.end_time).date()
            checkin_day = _as_utc(checkin.start_time).date()
            if checkin_day > arrival_day:
                nights = (checkin_day - arrival_day).days
                hard_violations.append(
                    ConstraintViolation(
                        constraint_id=f"UNCOVERED_FIRST_NIGHT_{checkin.node_id}",
                        name="Arrival Night Has No Accommodation",
                        category=ConstraintCategory.CAPACITY_ROOMING,
                        constraint_type=ConstraintType.HARD,
                        severity="blocking",
                        affected_elements=[first_arrival.node_id, checkin.node_id],
                        description=(
                            f"Traveler arrives {first_arrival.title} on {arrival_day.isoformat()} "
                            f"but the first hotel check-in ({checkin.title}) begins "
                            f"{checkin_day.isoformat()} — {nights} night(s) uncovered."
                        ),
                        relaxation_option=(
                            f"Book the arrival night at {first_arrival.location or 'the arrival city'} "
                            f"or move check-in to {arrival_day.isoformat()}."
                        ),
                    )
                )

        # 2. Regulatory Passport Validity & Schengen Rules
        trip_start: Optional[datetime] = sorted_nodes[0].start_time if sorted_nodes else None
        trip_end: Optional[datetime] = sorted_nodes[-1].end_time if sorted_nodes else None

        if travelers and trip_end:
            for idx, traveler in enumerate(travelers):
                trav_name = traveler.get("name") or f"Traveler #{idx + 1}"
                passport_exp = traveler.get("passport_expiry")
                if passport_exp:
                    exp_date = (
                        datetime.fromisoformat(passport_exp).date()
                        if isinstance(passport_exp, str)
                        else passport_exp
                    )
                    days_remaining = (exp_date - trip_end.date()).days
                    if days_remaining < 180:
                        hard_violations.append(
                            ConstraintViolation(
                                constraint_id=f"PASSPORT_EXPIRY_{idx}",
                                name="Passport 6-Month Validity Rule Violation",
                                category=ConstraintCategory.REGULATORY_PASSPORT,
                                constraint_type=ConstraintType.HARD,
                                severity="blocking",
                                affected_elements=[trav_name],
                                description=(
                                    f"{trav_name}'s passport expires on {exp_date} ({days_remaining} days after return date {trip_end.date()}). "
                                    "International immigration requires >= 6 months (180 days) validity from return date."
                                ),
                                relaxation_option=f"Traveler must renew passport prior to departure or advance trip dates before {exp_date}.",
                            )
                        )

        # 3. Schengen 90/180-Day Rule
        if trip_start and trip_end:
            dest_locations = [n.location.lower() for n in sorted_nodes if n.location]
            is_schengen = any(
                any(schengen in loc for schengen in SCHENGEN_DESTINATIONS)
                for loc in dest_locations
            )
            if is_schengen:
                trip_duration_days = (trip_end.date() - trip_start.date()).days + 1
                if trip_duration_days > 90:
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id="SCHENGEN_90_DAY_LIMIT",
                            name="Schengen 90/180-Day Maximum Stay Violation",
                            category=ConstraintCategory.REGULATORY_VISA_SCHENGEN,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=["itinerary_dates"],
                            description=(
                                f"Total stay in Schengen Area is {trip_duration_days} days. Short-stay tourist entry "
                                "strictly caps visits at 90 days within any rolling 180-day window."
                            ),
                            relaxation_option=f"Shorten Schengen itinerary by {trip_duration_days - 90} days or apply for National Long-Stay Visa (Type D).",
                        )
                    )

        # 4. Passport Blank Visa Pages & Vaccination Checks
        if travelers:
            for t in travelers:
                t_name = t.get("name", "Traveler")
                blank_pages = t.get("blank_visa_pages")
                if blank_pages is not None and blank_pages < 2:
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id="PASSPORT_BLANK_PAGES_DEFICIT",
                            name=f"Insufficient Blank Visa Pages for {t_name}",
                            category=ConstraintCategory.REGULATORY_PASSPORT_VALIDITY,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[f"traveler:{t_name}"],
                            description=f"Passport has only {blank_pages} blank visa pages. International transit requires >= 2 blank pages.",
                            relaxation_option="Traveler must obtain a renewed passport booklet with blank pages prior to travel.",
                        )
                    )

                # Driver Age Check for Car Rentals
                has_car_rental = any(n.node_type == NodeType.TRANSFER and "car" in n.title.lower() for n in sorted_nodes)
                driver_age = t.get("age")
                if has_car_rental and driver_age is not None and driver_age < 21:
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id="DRIVER_UNDERAGE_VIOLATION",
                            name=f"Underage Driver ({driver_age} yrs) for Car Rental",
                            category=ConstraintCategory.COMMERCIAL_SUPPLIER_POLICY,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[f"traveler:{t_name}"],
                            description=f"Driver age {driver_age} violates minimum supplier rental requirement of 21 years.",
                            relaxation_option="Designate an alternative traveler >= 21 years old as primary driver or switch to private chauffeur transfers.",
                        )
                    )

        # 4b. Capacity & Product-Rule Checks (TS-01). Occupancy vs party size,
        # declared ticket pax vs actual party, and product age bounds (child /
        # infant fare rules). Every check abstains unless the node declares
        # the relevant rule — no fabricated defaults on the supplier side.
        effective_party_size = len(travelers) if travelers else party_size
        if effective_party_size is not None:
            for node in sorted_nodes:
                # Occupancy vs party size (hotel stays / check-ins)
                if node.node_type in (NodeType.HOTEL_CHECKIN, NodeType.HOTEL_STAY):
                    capacity = _node_room_capacity(node)
                    if capacity is not None and capacity < effective_party_size:
                        hard_violations.append(
                            ConstraintViolation(
                                constraint_id=f"OCCUPANCY_EXCEEDED_{node.node_id}",
                                name="Hotel Capacity Below Party Size",
                                category=ConstraintCategory.CAPACITY_ROOMING,
                                constraint_type=ConstraintType.HARD,
                                severity="blocking",
                                affected_elements=[node.node_id],
                                description=(
                                    f"{node.title} provides capacity for {capacity} guest(s) "
                                    f"but the party has {effective_party_size} traveler(s)."
                                ),
                                relaxation_option=(
                                    f"Add room(s) at {node.title} to cover "
                                    f"{effective_party_size - capacity} more traveler(s)."
                                ),
                            )
                        )

                # Declared ticket pax vs actual party size
                declared_pax = _node_declared_pax(node)
                if declared_pax is not None and declared_pax != effective_party_size:
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id=f"PAX_MISMATCH_{node.node_id}",
                            name="Booked Traveler Count Mismatch",
                            category=ConstraintCategory.COMMERCIAL_SUPPLIER_POLICY,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[node.node_id],
                            description=(
                                f"{node.title} is booked for {declared_pax} traveler(s) "
                                f"but the trip party is {effective_party_size}."
                            ),
                            relaxation_option=(
                                f"Re-book {node.title} for {effective_party_size} traveler(s) "
                                "before any payment is taken."
                            ),
                        )
                    )

                # Product age bounds (fare / ticketed-entry age categories)
                if travelers:
                    min_age, max_age = _node_age_bounds(node)
                    if min_age is None and max_age is None:
                        continue
                    for idx, traveler in enumerate(travelers):
                        trav_name = traveler.get("name") or f"Traveler #{idx + 1}"
                        age = traveler.get("age")
                        if not isinstance(age, (int, float)):
                            continue
                        violated_bound = None
                        if min_age is not None and age < min_age:
                            violated_bound = f"minimum age {min_age}"
                        elif max_age is not None and age > max_age:
                            violated_bound = f"maximum age {max_age}"
                        if violated_bound:
                            hard_violations.append(
                                ConstraintViolation(
                                    constraint_id=f"AGE_RULE_{node.node_id}_{idx}",
                                    name=f"Traveler Age Violates Product Rule ({node.title})",
                                    category=ConstraintCategory.COMMERCIAL_SUPPLIER_POLICY,
                                    constraint_type=ConstraintType.HARD,
                                    severity="blocking",
                                    affected_elements=[node.node_id, f"traveler:{trav_name}"],
                                    description=(
                                        f"{trav_name} is {int(age)} years old, but {node.title} "
                                        f"requires {violated_bound}."
                                    ),
                                    relaxation_option=(
                                        f"Move {trav_name} to an age-appropriate fare/product "
                                        f"for {node.title}, or select a different product."
                                    ),
                                )
                            )

        # 5. Synthesize 4-Tier Relaxation Hierarchy
        # Priority 0: HARD_SAFETY (Never relaxed)
        # Priority 1: REGULATORY (Passport / Visa / Schengen)
        # Priority 2: COMMERCIAL (Supplier policies / rooming)
        # Priority 3: SOFT_PREFERENCE (Pacing / tight buffers)
        for hv in hard_violations:
            tier_num = 0 if hv.category in (ConstraintCategory.SPATIAL_CONTINUITY, ConstraintCategory.REGULATORY_HEALTH_VACCINATION) else 1
            if hv.relaxation_option:
                relaxation_hierarchy.append({
                    "priority_tier": tier_num,
                    "tier_name": "HARD_SAFETY" if tier_num == 0 else "REGULATORY",
                    "constraint_id": hv.constraint_id,
                    "violation": hv.name,
                    "action": hv.relaxation_option,
                })
        for sv in soft_violations:
            tier_num = 2 if sv.category in (ConstraintCategory.COMMERCIAL_SUPPLIER_POLICY, ConstraintCategory.CAPACITY_ROOMING) else 3
            if sv.relaxation_option:
                relaxation_hierarchy.append({
                    "priority_tier": tier_num,
                    "tier_name": "COMMERCIAL" if tier_num == 2 else "SOFT_PREFERENCE",
                    "constraint_id": sv.constraint_id,
                    "violation": sv.name,
                    "action": sv.relaxation_option,
                })

        # Sort hierarchy by priority_tier ascending (Tier 0 first, Tier 3 last)
        relaxation_hierarchy.sort(key=lambda item: item["priority_tier"])

        is_feasible = len(hard_violations) == 0

        return ConstraintEvaluationReport(
            trip_id=trip_id,
            is_feasible=is_feasible,
            hard_violations=hard_violations,
            soft_violations=soft_violations,
            relaxation_hierarchy=relaxation_hierarchy,
            evaluated_at=now_iso,
        )
