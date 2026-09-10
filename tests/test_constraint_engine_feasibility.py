"""
tests/test_constraint_engine_feasibility.py — TS-01 hard itinerary-feasibility
validators (2026-09-09 training-session register).

Covers the four families added to ConstraintEngine.evaluate_itinerary_graph:
1. Ground-access transfer buffer (explicit requirement -> HARD; heuristic -> SOFT advisory)
2. First-night lodging coverage
3. Hotel occupancy vs party size (CAPACITY_ROOMING)
4. Ticket pax mismatch + product age rules (COMMERCIAL_SUPPLIER_POLICY)

Sensitivity per Testing Doctrine: each family has a failing case (S1) paired
with a passing case that differs only in the violating dimension (S3-style
mutation — the same itinerary with a corrected buffer/room/age is feasible).
"""

from datetime import datetime

from src.decision.constraint_engine import ConstraintEngine
from src.schemas.constraints import ConstraintCategory, ConstraintType
from src.schemas.journey_graph import (
    DependencyRelation,
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
)


def _flight(node_id: str = "f1", land_hour: int = 10, land_minute: int = 40) -> JourneyNode:
    return JourneyNode(
        node_id=node_id,
        node_type=NodeType.FLIGHT,
        title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 1, 0),
        end_time=datetime(2026, 10, 5, land_hour, land_minute),
        location="Tokyo",
    )


def _disney(node_id: str = "a1", start_hour: int = 11, start_minute: int = 0, **metadata) -> JourneyNode:
    return JourneyNode(
        node_id=node_id,
        node_type=NodeType.ACTIVITY,
        title="Tokyo Disney",
        start_time=datetime(2026, 10, 5, start_hour, start_minute),
        end_time=datetime(2026, 10, 5, start_hour + 6, start_minute),
        location="Tokyo",
        metadata=dict(metadata),
    )


# --- 1. Ground-access transfer buffer -----------------------------------------


def test_ground_access_deficit_hard_reject():
    """The tutor's canonical case: lands 10:40, Disney 11:00, 70-minute transfer."""
    graph = JourneyDependencyGraph("trip_ground_deficit")
    graph.add_node(_flight())
    graph.add_node(_disney(required_transfer_minutes=70))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert len(report.hard_violations) == 1
    v = report.hard_violations[0]
    assert v.constraint_id == "GROUND_ACCESS_DEFICIT_f1_a1"
    assert v.category == ConstraintCategory.SPATIAL_CONTINUITY
    assert v.constraint_type == ConstraintType.HARD
    assert v.relaxation_option is not None


def test_ground_access_satisfied_when_buffer_sufficient():
    """Same itinerary, activity pushed 90 minutes out — feasible."""
    graph = JourneyDependencyGraph("trip_ground_ok")
    graph.add_node(_flight())
    graph.add_node(_disney(start_hour=12, start_minute=10, required_transfer_minutes=70))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert report.is_feasible
    assert report.hard_violations == []
    assert report.soft_violations == []


def test_ground_overlap_activity_before_arrival():
    """Activity scheduled before the flight physically lands."""
    graph = JourneyDependencyGraph("trip_ground_overlap")
    graph.add_node(_flight(land_hour=14, land_minute=0))
    graph.add_node(_disney(start_hour=11, start_minute=30))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert any(v.constraint_id == "GROUND_OVERLAP_f1_a1" for v in report.hard_violations)


def test_ground_access_heuristic_default_is_advisory_only():
    """Without an explicit requirement, a short buffer is SOFT — the engine
    does not fabricate a hard supplier-side fact from a heuristic default."""
    graph = JourneyDependencyGraph("trip_ground_tight")
    graph.add_node(_flight(land_hour=10, land_minute=40))
    graph.add_node(_disney(start_hour=11, start_minute=10))  # 30m gap, no explicit requirement

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert report.is_feasible  # advisory only — not a physical reject
    assert len(report.soft_violations) == 1
    soft = report.soft_violations[0]
    assert soft.constraint_id == "GROUND_BUFFER_TIGHT_f1_a1"
    assert soft.constraint_type == ConstraintType.SOFT


def test_timed_entry_vocabulary_honored():
    """recommended_arrival_buffer_minutes (TimedEntrySlot vocabulary) is an
    authoritative requirement too."""
    graph = JourneyDependencyGraph("trip_ground_timed_entry")
    graph.add_node(_flight())
    graph.add_node(_disney(recommended_arrival_buffer_minutes=70))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert any(
        v.constraint_id == "GROUND_ACCESS_DEFICIT_f1_a1" for v in report.hard_violations
    )


# --- 2. First-night lodging coverage ------------------------------------------


def test_uncovered_first_night():
    """Lands Oct 5 23:30, first check-in begins Oct 6 15:00 (>12h later)."""
    graph = JourneyDependencyGraph("trip_uncovered_night")
    graph.add_node(JourneyNode(
        node_id="f_in",
        node_type=NodeType.FLIGHT,
        title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 18, 0),
        end_time=datetime(2026, 10, 5, 23, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1",
        node_type=NodeType.HOTEL_CHECKIN,
        title="Kyoto Hotel check-in",
        start_time=datetime(2026, 10, 6, 15, 0),
        end_time=datetime(2026, 10, 9, 11, 0),
        location="Kyoto",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    v = next(v for v in report.hard_violations if v.constraint_id == "UNCOVERED_FIRST_NIGHT_f_in")
    assert v.category == ConstraintCategory.CAPACITY_ROOMING
    assert v.constraint_type == ConstraintType.HARD


def test_first_night_same_day_passes():
    graph = JourneyDependencyGraph("trip_covered_night")
    graph.add_node(JourneyNode(
        node_id="f_in",
        node_type=NodeType.FLIGHT,
        title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 18, 0),
        end_time=datetime(2026, 10, 5, 23, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1",
        node_type=NodeType.HOTEL_CHECKIN,
        title="Tokyo Hotel check-in",
        start_time=datetime(2026, 10, 6, 0, 30),  # late-night same-night check-in
        end_time=datetime(2026, 10, 9, 11, 0),
        location="Tokyo",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )


def test_multi_city_two_checkins_no_false_first_night():
    """Review cycle 1 P0 regression: each arrival must be compared against
    lodging coverage, not against the earliest trip arrival. Tokyo leg then
    Kyoto leg, each with a check-in 1h after its own flight — must pass."""
    graph = JourneyDependencyGraph("trip_multi_city")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 18, 0), end_time=datetime(2026, 10, 5, 23, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h_tokyo", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel",
        start_time=datetime(2026, 10, 6, 0, 30), end_time=datetime(2026, 10, 8, 11, 0),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="f2", node_type=NodeType.FLIGHT, title="Tokyo -> Kyoto",
        start_time=datetime(2026, 10, 8, 12, 0), end_time=datetime(2026, 10, 8, 14, 0),
        location="Kyoto",
    ))
    graph.add_node(JourneyNode(
        node_id="h_kyoto", node_type=NodeType.HOTEL_CHECKIN, title="Kyoto Hotel",
        start_time=datetime(2026, 10, 8, 15, 0), end_time=datetime(2026, 10, 11, 11, 0),
        location="Kyoto",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )


def test_hotel_change_without_new_flight_no_false_first_night():
    """Review cycle 1 P0 regression: a mid-trip hotel change with no second
    flight is not an uncovered arrival — the second stay starts when the
    first ends."""
    graph = JourneyDependencyGraph("trip_hotel_change")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 18, 0), end_time=datetime(2026, 10, 5, 23, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel A",
        start_time=datetime(2026, 10, 6, 0, 30), end_time=datetime(2026, 10, 10, 11, 0),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h2", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel B",
        start_time=datetime(2026, 10, 10, 15, 0), end_time=datetime(2026, 10, 12, 11, 0),
        location="Tokyo",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )


# --- 3. Occupancy vs party size ------------------------------------------------


def _hotel_stay(node_id: str = "h_stay", **metadata) -> JourneyNode:
    return JourneyNode(
        node_id=node_id,
        node_type=NodeType.HOTEL_STAY,
        title="Tokyo Hotel 4-star",
        start_time=datetime(2026, 10, 5, 15, 0),
        end_time=datetime(2026, 10, 12, 11, 0),
        location="Tokyo",
        metadata=dict(metadata),
    )


def test_occupancy_exceeded_rooms_list():
    graph = JourneyDependencyGraph("trip_occupancy")
    graph.add_node(_hotel_stay(rooms=[{"max_occupancy": 2}, {"max_occupancy": 2}]))

    report = ConstraintEngine.evaluate_itinerary_graph(graph, party_size=5)
    assert not report.is_feasible
    v = next(v for v in report.hard_violations if v.constraint_id == "OCCUPANCY_EXCEEDED_h_stay")
    assert v.category == ConstraintCategory.CAPACITY_ROOMING
    assert v.constraint_type == ConstraintType.HARD
    assert "5" in v.description


def test_occupancy_exceeded_room_count_shape():
    graph = JourneyDependencyGraph("trip_occupancy_count")
    graph.add_node(_hotel_stay(room_count=1, max_occupancy_per_room=3))

    report = ConstraintEngine.evaluate_itinerary_graph(graph, party_size=4)
    assert not report.is_feasible
    assert any(
        v.constraint_id == "OCCUPANCY_EXCEEDED_h_stay" for v in report.hard_violations
    )


def test_occupancy_passes_and_abstains():
    # Capacity 4, party 4 -> clean
    graph_ok = JourneyDependencyGraph("trip_occupancy_ok")
    graph_ok.add_node(_hotel_stay(room_count=2, max_occupancy_per_room=2))
    report_ok = ConstraintEngine.evaluate_itinerary_graph(graph_ok, party_size=4)
    assert report_ok.is_feasible

    # No capacity metadata at all -> the engine abstains (no fabricated fact)
    graph_abstain = JourneyDependencyGraph("trip_occupancy_abstain")
    graph_abstain.add_node(_hotel_stay())
    report_abstain = ConstraintEngine.evaluate_itinerary_graph(graph_abstain, party_size=6)
    assert report_abstain.is_feasible


def test_travelers_list_drives_party_size():
    """When a travelers list is supplied, its length wins over party_size."""
    graph = JourneyDependencyGraph("trip_occupancy_travelers")
    graph.add_node(_hotel_stay(max_guests=2))
    travelers = [{"name": "A"}, {"name": "B"}, {"name": "C"}]

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers, party_size=2)
    assert not report.is_feasible
    assert any(
        v.constraint_id == "OCCUPANCY_EXCEEDED_h_stay" for v in report.hard_violations
    )


# --- 4. Ticket pax mismatch + product age rules --------------------------------


def test_pax_mismatch_on_booked_node():
    graph = JourneyDependencyGraph("trip_pax")
    graph.add_node(_hotel_stay(pax=2))

    report = ConstraintEngine.evaluate_itinerary_graph(graph, party_size=4)
    assert not report.is_feasible
    v = next(v for v in report.hard_violations if v.constraint_id == "PAX_MISMATCH_h_stay")
    assert v.category == ConstraintCategory.COMMERCIAL_SUPPLIER_POLICY


def test_pax_overbooked_is_always_hard():
    """More travelers booked than exist in the party — supplier will
    mischarge; hard regardless of node type."""
    graph = JourneyDependencyGraph("trip_pax_over")
    graph.add_node(JourneyNode(
        node_id="act1", node_type=NodeType.ACTIVITY, title="Spa afternoon",
        start_time=datetime(2026, 10, 6, 14, 0), end_time=datetime(2026, 10, 6, 17, 0),
        location="Tokyo", metadata={"pax": 6},
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph, party_size=4)
    assert not report.is_feasible
    assert any(v.constraint_id == "PAX_OVERBOOKED_act1" for v in report.hard_violations)


def test_pax_partial_on_optional_node_is_advisory():
    """Review cycle 1 P2 regression: an optional activity booked for part of
    the party is legitimate — advisory, not a hard reject."""
    graph = JourneyDependencyGraph("trip_pax_partial")
    graph.add_node(JourneyNode(
        node_id="act1", node_type=NodeType.ACTIVITY, title="Couples spa",
        start_time=datetime(2026, 10, 6, 14, 0), end_time=datetime(2026, 10, 6, 17, 0),
        location="Tokyo", metadata={"pax": 2},
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph, party_size=4)
    assert report.is_feasible  # advisory only
    assert len(report.soft_violations) == 1
    assert report.soft_violations[0].constraint_id == "PAX_PARTIAL_act1"


def test_fare_category_keys_are_not_hard_age_bounds():
    """Review cycle 1 P1 regression: fare-CATEGORY definitions
    (infant_max_age, child_fare_min_age) describe a fare class boundary,
    not whole-party eligibility — must never hard-reject a family."""
    graph = JourneyDependencyGraph("trip_fare_categories")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 1, 0), end_time=datetime(2026, 10, 5, 10, 40),
        location="Tokyo",
        metadata={"infant_max_age": 2, "child_fare_min_age": 2},
    ))
    travelers = [{"name": "Parent", "age": 38}, {"name": "Infant", "age": 1}]

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers)
    assert report.is_feasible
    assert not any(v.constraint_id.startswith("AGE_RULE_") for v in report.hard_violations)


def test_transfer_end_to_commitment_gap_is_advisory():
    """Review cycle 1 P2: transfer ends 12:00, activity at 12:10 — at least
    an advisory (TRANSFER end gates ground commitments with a small default)."""
    graph = JourneyDependencyGraph("trip_transfer_gap")
    graph.add_node(JourneyNode(
        node_id="trf1", node_type=NodeType.TRANSFER, title="Airport transfer",
        start_time=datetime(2026, 10, 5, 11, 0), end_time=datetime(2026, 10, 5, 12, 0),
        location="Tokyo",
    ))
    graph.add_node(_disney(start_hour=12, start_minute=10))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert report.is_feasible  # advisory
    assert any(
        v.constraint_id == "GROUND_BUFFER_TIGHT_trf1_a1" for v in report.soft_violations
    )


def test_rail_to_transfer_overlap_is_caught():
    """Review cycle 1 P2: a transfer departing before the train arrives is
    physically impossible — section 1 now gates all transport modes."""
    graph = JourneyDependencyGraph("trip_rail_overlap")
    graph.add_node(JourneyNode(
        node_id="rail1", node_type=NodeType.RAIL, title="Tokyo -> Kyoto Shinkansen",
        start_time=datetime(2026, 10, 6, 9, 0), end_time=datetime(2026, 10, 6, 11, 30),
        location="Kyoto",
    ))
    graph.add_node(JourneyNode(
        node_id="trf1", node_type=NodeType.TRANSFER, title="Station taxi",
        start_time=datetime(2026, 10, 6, 11, 0), end_time=datetime(2026, 10, 6, 11, 40),
        location="Kyoto",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert any(v.constraint_id == "SPATIAL_OVERLAP_rail1_trf1" for v in report.hard_violations)


def test_surface_mode_pickup_30m_after_train_is_not_mct_violation():
    """Review cycle 2 P2: airport MCT minimums must not apply to surface
    modes — a station pickup 30m after train arrival is normal."""
    graph = JourneyDependencyGraph("trip_rail_pickup")
    graph.add_node(JourneyNode(
        node_id="rail1", node_type=NodeType.RAIL, title="Tokyo -> Kyoto Shinkansen",
        start_time=datetime(2026, 10, 6, 9, 0), end_time=datetime(2026, 10, 6, 11, 30),
        location="Kyoto",
    ))
    graph.add_node(JourneyNode(
        node_id="trf1", node_type=NodeType.TRANSFER, title="Station taxi pickup",
        start_time=datetime(2026, 10, 6, 12, 0), end_time=datetime(2026, 10, 6, 12, 40),
        location="Kyoto",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert report.is_feasible
    assert not any(
        v.constraint_id.startswith("MCT_DEFICIT_") for v in report.hard_violations
    )


def test_transfer_to_hotel_checkin_zero_gap_is_not_advisory():
    """Review cycle 2 P2: a transfer ending at the hotel door with check-in
    starting at that instant is a door drop-off — no advisory (the compiler
    constructs exactly this shape)."""
    graph = JourneyDependencyGraph("trip_door_dropoff")
    graph.add_node(JourneyNode(
        node_id="trf1", node_type=NodeType.TRANSFER, title="Chauffeur airport transfer",
        start_time=datetime(2026, 10, 5, 16, 45), end_time=datetime(2026, 10, 5, 17, 45),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel check-in",
        start_time=datetime(2026, 10, 5, 17, 45), end_time=datetime(2026, 10, 9, 11, 0),
        location="Tokyo",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("GROUND_BUFFER_TIGHT_") for v in report.soft_violations
    )


# --- review cycle 2: return-leg / transit discriminators ------------------------


def _round_trip_graph(with_return_edge: bool = False) -> JourneyDependencyGraph:
    """Outbound flight, hotel, return flight, home transfer — the reviewer's
    P1 case: the homeward arrival must NOT be flagged as an uncovered night."""
    graph = JourneyDependencyGraph("trip_round_trip")
    graph.add_node(JourneyNode(
        node_id="f_out", node_type=NodeType.FLIGHT, title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 1, 0), end_time=datetime(2026, 10, 5, 10, 40),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel",
        start_time=datetime(2026, 10, 5, 17, 45), end_time=datetime(2026, 10, 9, 11, 0),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="f_ret", node_type=NodeType.FLIGHT, title="Tokyo -> BLR",
        start_time=datetime(2026, 10, 9, 18, 0), end_time=datetime(2026, 10, 9, 22, 0),
        location="BLR",
    ))
    graph.add_node(JourneyNode(
        node_id="trf_home", node_type=NodeType.TRANSFER, title="Airport -> home",
        start_time=datetime(2026, 10, 9, 22, 30), end_time=datetime(2026, 10, 9, 23, 30),
        location="BLR",
    ))
    if with_return_edge:
        graph.add_edge("f_out", "f_ret", DependencyRelation.RETURN_LEG_OF)
    return graph


def test_return_flight_then_home_transfer_not_uncovered_night():
    report = ConstraintEngine.evaluate_itinerary_graph(_round_trip_graph(with_return_edge=False))
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )


def test_return_leg_edge_marks_arrival_as_homeward():
    """Explicit RETURN_LEG_OF edge: the edge target is skipped even when it
    is not the final arrival by end_time (e.g. trailing dinner after landing)."""
    graph = _round_trip_graph(with_return_edge=True)
    # trailing dinner after the homeward landing — makes f_ret not-last
    graph.add_node(JourneyNode(
        node_id="dinner", node_type=NodeType.RESTAURANT, title="Late dinner home",
        start_time=datetime(2026, 10, 10, 0, 0), end_time=datetime(2026, 10, 10, 1, 30),
        location="BLR",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )


def test_long_transit_day_with_onward_departure_not_uncovered():
    """Review cycle 2 P1 case 2: arrive 06:00 on a connecting leg, second leg
    departs 08:00, final arrival 20:00 with hotel 21:00 — the 06:00 arrival
    is a transit continuation, not a stranded night."""
    graph = JourneyDependencyGraph("trip_transit_day")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> SIN",
        start_time=datetime(2026, 10, 5, 20, 0), end_time=datetime(2026, 10, 6, 6, 0),
        location="SIN",
    ))
    graph.add_node(JourneyNode(
        node_id="f2", node_type=NodeType.FLIGHT, title="SIN -> Tokyo",
        start_time=datetime(2026, 10, 6, 8, 0), end_time=datetime(2026, 10, 6, 20, 0),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel",
        start_time=datetime(2026, 10, 6, 21, 0), end_time=datetime(2026, 10, 10, 11, 0),
        location="Tokyo",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )


def test_overnight_layover_without_lodging_still_flagged():
    """The transit exemption must not swallow genuine overnight layovers: a
    14-hour layover with no onward departure inside 12h and no hotel is an
    uncovered night."""
    graph = JourneyDependencyGraph("trip_overnight_layover")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> DOH",
        start_time=datetime(2026, 10, 5, 20, 0), end_time=datetime(2026, 10, 5, 23, 0),
        location="DOH",
    ))
    graph.add_node(JourneyNode(
        node_id="f2", node_type=NodeType.FLIGHT, title="DOH -> London",
        start_time=datetime(2026, 10, 6, 13, 30), end_time=datetime(2026, 10, 6, 18, 0),
        location="London",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="London Hotel",
        start_time=datetime(2026, 10, 6, 19, 30), end_time=datetime(2026, 10, 9, 11, 0),
        location="London",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert any(
        v.constraint_id == "UNCOVERED_FIRST_NIGHT_f1" for v in report.hard_violations
    )


def test_long_layover_no_hotel_is_soft_operator_suggestion():
    """Owner-confirmed policy (2026-09-09): a <12h overnight connection with
    no transit hotel never blocks — it earns a SOFT advisory (transit-room
    upsell) for the operator. Lands 22:00, departs 08:00 (10h wait)."""
    graph = JourneyDependencyGraph("trip_long_layover")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> SIN",
        start_time=datetime(2026, 10, 5, 16, 0), end_time=datetime(2026, 10, 5, 22, 0),
        location="SIN",
    ))
    graph.add_node(JourneyNode(
        node_id="f2", node_type=NodeType.FLIGHT, title="SIN -> Tokyo",
        start_time=datetime(2026, 10, 6, 8, 0), end_time=datetime(2026, 10, 6, 16, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel",
        start_time=datetime(2026, 10, 6, 17, 30), end_time=datetime(2026, 10, 10, 11, 0),
        location="Tokyo",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    # never a hard block
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )
    # soft operator suggestion fires for the 10h lodging-less layover
    advisory = next(
        (v for v in report.soft_violations if v.constraint_id == "LONG_LAYOVER_NO_HOTEL_f1"),
        None,
    )
    assert advisory is not None
    assert advisory.constraint_type == ConstraintType.SOFT
    assert "transit hotel" in advisory.relaxation_option.lower()


def test_short_connection_no_hotel_stays_silent():
    """A 2h connection with no hotel is a normal transit — no advisory, no
    violation (advisory threshold is 6h)."""
    graph = JourneyDependencyGraph("trip_short_connection")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> SIN",
        start_time=datetime(2026, 10, 5, 16, 0), end_time=datetime(2026, 10, 5, 22, 0),
        location="SIN",
    ))
    graph.add_node(JourneyNode(
        node_id="f2", node_type=NodeType.FLIGHT, title="SIN -> Tokyo",
        start_time=datetime(2026, 10, 6, 0, 0), end_time=datetime(2026, 10, 6, 8, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel",
        start_time=datetime(2026, 10, 6, 9, 30), end_time=datetime(2026, 10, 10, 11, 0),
        location="Tokyo",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )
    assert not any(
        v.constraint_id.startswith("LONG_LAYOVER_NO_HOTEL_") for v in report.soft_violations
    )


def test_long_layover_with_transit_hotel_no_advisory():
    """A transit hotel covering the layover answers the question — no
    advisory even for a 10h connection."""
    graph = JourneyDependencyGraph("trip_transit_hotel")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> SIN",
        start_time=datetime(2026, 10, 5, 16, 0), end_time=datetime(2026, 10, 5, 22, 0),
        location="SIN",
    ))
    graph.add_node(JourneyNode(
        node_id="h_transit", node_type=NodeType.HOTEL_STAY, title="Changi transit hotel",
        start_time=datetime(2026, 10, 5, 23, 0), end_time=datetime(2026, 10, 6, 7, 0),
        location="SIN",
    ))
    graph.add_node(JourneyNode(
        node_id="f2", node_type=NodeType.FLIGHT, title="SIN -> Tokyo",
        start_time=datetime(2026, 10, 6, 8, 0), end_time=datetime(2026, 10, 6, 16, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel",
        start_time=datetime(2026, 10, 6, 17, 30), end_time=datetime(2026, 10, 10, 11, 0),
        location="Tokyo",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("LONG_LAYOVER_NO_HOTEL_") for v in report.soft_violations
    )


def test_hotel_stay_interval_counts_as_lodging_coverage():
    """Review cycle 2 P2: graphs modeling lodging as HOTEL_STAY (no
    HOTEL_CHECKIN node) still declare lodging intent and provide coverage."""
    graph = JourneyDependencyGraph("trip_stay_only")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> Tokyo",
        start_time=datetime(2026, 10, 5, 1, 0), end_time=datetime(2026, 10, 5, 23, 30),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="stay1", node_type=NodeType.HOTEL_STAY, title="Tokyo Hotel 4-star",
        start_time=datetime(2026, 10, 6, 0, 30), end_time=datetime(2026, 10, 9, 11, 0),
        location="Tokyo",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not any(
        v.constraint_id.startswith("UNCOVERED_FIRST_NIGHT_") for v in report.hard_violations
    )


# --- review cycle 3: exemption-scope regression tests ---------------------------


def test_lands_transfer_no_hotel_that_night_still_fires():
    """Review cycle 3 P1 #1: a transfer is NOT evidence of onward transit —
    lands 20:00, transfer 20:30, no city-A hotel, next-day flight out, hotel
    in city B: the city-A arrival night is genuinely uncovered and must fire."""
    graph = JourneyDependencyGraph("trip_transfer_trap")
    graph.add_node(JourneyNode(
        node_id="f1", node_type=NodeType.FLIGHT, title="BLR -> Singapore",
        start_time=datetime(2026, 10, 5, 12, 0), end_time=datetime(2026, 10, 5, 20, 0),
        location="Singapore",
    ))
    graph.add_node(JourneyNode(
        node_id="trf1", node_type=NodeType.TRANSFER, title="Airport -> city transfer",
        start_time=datetime(2026, 10, 5, 20, 30), end_time=datetime(2026, 10, 5, 21, 30),
        location="Singapore",
    ))
    graph.add_node(JourneyNode(
        node_id="f2", node_type=NodeType.FLIGHT, title="Singapore -> Tokyo",
        start_time=datetime(2026, 10, 6, 14, 0), end_time=datetime(2026, 10, 6, 22, 0),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h_tokyo", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel",
        start_time=datetime(2026, 10, 6, 23, 0), end_time=datetime(2026, 10, 10, 11, 0),
        location="Tokyo",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert any(
        v.constraint_id == "UNCOVERED_FIRST_NIGHT_f1" for v in report.hard_violations
    )


def test_transfer_to_checkin_negative_gap_still_hard_fails():
    """Review cycle 3 P1 #2: the door-drop-off exemption suppresses only the
    heuristic advisory — a check-in starting while the traveler is still in
    the car remains a hard physical violation."""
    graph = JourneyDependencyGraph("trip_dropoff_overlap")
    graph.add_node(JourneyNode(
        node_id="trf1", node_type=NodeType.TRANSFER, title="Chauffeur transfer",
        start_time=datetime(2026, 10, 5, 10, 0), end_time=datetime(2026, 10, 5, 11, 0),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel check-in",
        start_time=datetime(2026, 10, 5, 10, 15), end_time=datetime(2026, 10, 9, 11, 0),
        location="Tokyo",
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert any(v.constraint_id == "GROUND_OVERLAP_trf1_h1" for v in report.hard_violations)


def test_transfer_to_checkin_explicit_requirement_still_hard_fails():
    """Review cycle 3 P1 #2: an explicit per-node transfer requirement is
    authoritative even for the transfer→check-in pair."""
    graph = JourneyDependencyGraph("trip_dropoff_requirement")
    graph.add_node(JourneyNode(
        node_id="trf1", node_type=NodeType.TRANSFER, title="Chauffeur transfer",
        start_time=datetime(2026, 10, 5, 10, 0), end_time=datetime(2026, 10, 5, 11, 0),
        location="Tokyo",
    ))
    graph.add_node(JourneyNode(
        node_id="h1", node_type=NodeType.HOTEL_CHECKIN, title="Tokyo Hotel check-in",
        start_time=datetime(2026, 10, 5, 11, 0), end_time=datetime(2026, 10, 9, 11, 0),
        location="Tokyo", metadata={"required_transfer_minutes": 30},
    ))
    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert any(v.constraint_id == "GROUND_ACCESS_DEFICIT_trf1_h1" for v in report.hard_violations)


def test_age_rule_child_below_fare_minimum():
    """A product declaring min_age=12 (adult fare) with a 6-year-old traveler."""
    graph = JourneyDependencyGraph("trip_age_rule")
    graph.add_node(_hotel_stay(min_age=12))
    travelers = [{"name": "Parent", "age": 38}, {"name": "Child", "age": 6}]

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers)
    assert not report.is_feasible
    v = next(
        v for v in report.hard_violations if v.constraint_id.startswith("AGE_RULE_h_stay_")
    )
    assert "Child" in " ".join(v.affected_elements)
    assert v.category == ConstraintCategory.COMMERCIAL_SUPPLIER_POLICY


def test_age_rule_max_age_senior_fare():
    """A child-fare product (max_age=11) with a 38-year-old traveler."""
    graph = JourneyDependencyGraph("trip_age_rule_max")
    graph.add_node(_hotel_stay(max_age=11))
    travelers = [{"name": "Adult", "age": 38}]

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers)
    assert not report.is_feasible
    assert any(
        v.constraint_id.startswith("AGE_RULE_h_stay_") for v in report.hard_violations
    )


def test_age_rule_abstains_when_traveler_age_unknown():
    graph = JourneyDependencyGraph("trip_age_rule_abstain")
    graph.add_node(_hotel_stay(min_age=12))
    travelers = [{"name": "Traveler"}]  # no age declared

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers)
    assert report.is_feasible


def test_party_size_alone_suffices_without_travelers():
    """Proposal-compiler shape: count only, no traveler dicts."""
    graph = JourneyDependencyGraph("trip_party_only")
    graph.add_node(_hotel_stay(max_guests=2))

    report = ConstraintEngine.evaluate_itinerary_graph(graph, party_size=4)
    assert not report.is_feasible
    assert any(
        v.constraint_id == "OCCUPANCY_EXCEEDED_h_stay" for v in report.hard_violations
    )


def test_no_new_checks_fire_on_legacy_shapes():
    """Regression guard: graphs without ground nodes, room metadata, or age
    rules produce no TS-01 violations (all new checks abstain). Pre-existing
    advisories (e.g. TIGHT_LAYOVER) are untouched."""
    graph = JourneyDependencyGraph("trip_legacy")
    graph.add_node(JourneyNode(
        node_id="f1",
        node_type=NodeType.FLIGHT,
        title="Domestic Flight A -> B",
        start_time=datetime(2026, 11, 1, 10, 0),
        end_time=datetime(2026, 11, 1, 14, 0),
        location="Airport B",
    ))
    graph.add_node(JourneyNode(
        node_id="f2",
        node_type=NodeType.FLIGHT,
        title="Domestic Flight B -> C",
        start_time=datetime(2026, 11, 1, 15, 0),
        end_time=datetime(2026, 11, 1, 17, 0),
        location="Airport C",
    ))

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert report.is_feasible
    assert report.hard_violations == []
    ts01_prefixes = (
        "GROUND_OVERLAP_", "GROUND_ACCESS_DEFICIT_", "GROUND_BUFFER_TIGHT_",
        "UNCOVERED_FIRST_NIGHT_", "OCCUPANCY_EXCEEDED_", "PAX_MISMATCH_", "AGE_RULE_",
    )
    for v in report.hard_violations + report.soft_violations:
        assert not v.constraint_id.startswith(ts01_prefixes)
