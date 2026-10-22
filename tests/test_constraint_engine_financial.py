"""FINANCIAL_BOUND constraint family — exploration topic 50 (2026-10-21).

Completes the family declared by the PER-0711 design (ConstraintCategory
.FINANCIAL_BOUND, the ``budget_cents`` / ``hard_budget_ceiling`` parameters)
but never implemented. Rules are evidence-backed: ChinaTravel's commonsense
catalog (cost = price × tickets; price must match its source) and the
2026-10-20 producer probe (30% unpriced rows, converted estimates, five
currencies in one result set).

Honesty contract pinned here:
  * a graph with no costed nodes produces NO financial findings (existing
    callers unaffected);
  * a cost that cannot be verified is a warning/advisory, never a block;
  * a cost that is WRONG (arithmetic, mixed currency, hard ceiling) blocks.
"""

from datetime import datetime, timedelta, timezone


from src.decision.constraint_engine import ConstraintEngine
from src.schemas.constraints import ConstraintCategory
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType

T0 = datetime(2027, 2, 10, 8, 0, tzinfo=timezone.utc)


def _graph(*nodes: JourneyNode) -> JourneyDependencyGraph:
    graph = JourneyDependencyGraph(trip_id="TRIP-FIN")
    for node in nodes:
        graph.add_node(node)
    return graph


def _flight(cost=None, node_id="N_FLT"):
    return JourneyNode(node_id, NodeType.FLIGHT, "Flight BOM→DXB", T0, T0 + timedelta(hours=3), "BOM", provider="Air Test",
                       metadata={"cost": cost} if cost is not None else {})


def _hotel(cost=None, node_id="N_HTL"):
    start = T0 + timedelta(hours=5)
    return JourneyNode(node_id, NodeType.HOTEL_CHECKIN, "Hotel Dubai", start, start + timedelta(days=3), "DXB", provider="Hotel Test",
                       metadata={"cost": cost} if cost is not None else {})


def _financial(report):
    return {
        "hard": {v.constraint_id: v for v in report.hard_violations if v.category == ConstraintCategory.FINANCIAL_BOUND},
        "soft": {v.constraint_id: v for v in report.soft_violations if v.category == ConstraintCategory.FINANCIAL_BOUND},
    }


GOOD_FLIGHT = {"unit_price": 14868.0, "quantity": 2, "total": 29736.0, "currency": "INR", "basis": "live", "source": "google_flights"}
GOOD_HOTEL = {"unit_price": 9000.0, "quantity": 3, "total": 27000.0, "currency": "INR", "basis": "live", "source": "agoda"}


def test_uncosted_graph_emits_no_financial_findings():
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(_flight(), _hotel()), budget_cents=1, hard_budget_ceiling=True)
    fin = _financial(report)
    assert fin["hard"] == {} and fin["soft"] == {}


def test_consistent_costs_pass_cleanly():
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(_flight(GOOD_FLIGHT), _hotel(GOOD_HOTEL)))
    fin = _financial(report)
    assert fin["hard"] == {} and fin["soft"] == {}


def test_arithmetic_mismatch_blocks_with_evidence():
    bad = {**GOOD_FLIGHT, "total": 25000.0}
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(_flight(bad), _hotel(GOOD_HOTEL)))
    fin = _financial(report)
    violation = fin["hard"]["COST_ARITHMETIC_N_FLT"]
    assert violation.severity == "blocking"
    assert violation.metadata["expected_total"] == 29736.0
    assert violation.metadata["declared_total"] == 25000.0
    assert report.is_feasible is False


def test_arithmetic_tolerates_rounding():
    almost = {**GOOD_HOTEL, "unit_price": 8999.99, "total": 27000.0}
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(_hotel(almost)))
    assert _financial(report)["hard"] == {}


def test_mixed_currencies_block_and_suppress_budget_check():
    usd_hotel = {**GOOD_HOTEL, "currency": "usd"}
    report = ConstraintEngine.evaluate_itinerary_graph(
        _graph(_flight(GOOD_FLIGHT), _hotel(usd_hotel)), budget_cents=100, hard_budget_ceiling=True
    )
    fin = _financial(report)
    mixed = fin["hard"]["COST_CURRENCY_MIXED"]
    assert set(mixed.metadata["currencies"]) == {"INR", "USD"}
    assert "BUDGET_CEILING_EXCEEDED" not in fin["hard"], "a mixed-currency sum would be a fabricated number"


def test_missing_provenance_warns_but_never_blocks():
    no_source = {**GOOD_FLIGHT, "basis": None, "source": None}
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(_flight(no_source)))
    fin = _financial(report)
    assert fin["hard"] == {}
    assert fin["soft"]["COST_SOURCE_MISSING_N_FLT"].severity == "warning"


def test_partial_costing_is_a_single_advisory_naming_the_gaps():
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(_flight(GOOD_FLIGHT), _hotel()))
    fin = _financial(report)
    advisory = fin["soft"]["COST_PROVENANCE_UNVERIFIED"]
    assert advisory.severity == "advisory"
    assert advisory.metadata["uncosted"] == ["N_HTL"]
    assert advisory.metadata["costed"] == ["N_FLT"]
    assert fin["hard"] == {}


def test_budget_target_is_a_warning_and_ceiling_is_a_block():
    graph = _graph(_flight(GOOD_FLIGHT), _hotel(GOOD_HOTEL))  # total 56736.00 INR
    under = ConstraintEngine.evaluate_itinerary_graph(graph, budget_cents=5_673_600, budget_currency="INR")
    assert _financial(under)["hard"] == {} and _financial(under)["soft"] == {}

    target = ConstraintEngine.evaluate_itinerary_graph(graph, budget_cents=5_000_000, budget_currency="INR")
    warning = _financial(target)["soft"]["BUDGET_TARGET_EXCEEDED"]
    assert warning.metadata["overage_cents"] == 673_600
    assert target.is_feasible is True

    ceiling = ConstraintEngine.evaluate_itinerary_graph(graph, budget_cents=5_000_000, hard_budget_ceiling=True, budget_currency="INR")
    block = _financial(ceiling)["hard"]["BUDGET_CEILING_EXCEEDED"]
    assert block.metadata["currency"] == "INR"
    assert block.metadata["partial_costing"] is False
    assert ceiling.is_feasible is False


def test_budget_without_matching_currency_is_reported_not_enforced():
    graph = _graph(_flight(GOOD_FLIGHT), _hotel(GOOD_HOTEL))  # total 56736.00 INR

    # No budget currency at all: the ceiling must not block on a fabricated
    # cross-currency comparison — it is reported as unverifiable.
    unknown = ConstraintEngine.evaluate_itinerary_graph(graph, budget_cents=100, hard_budget_ceiling=True)
    fin = _financial(unknown)
    assert "BUDGET_CEILING_EXCEEDED" not in fin["hard"]
    advisory = fin["soft"]["BUDGET_CURRENCY_UNVERIFIED"]
    assert advisory.severity == "warning"
    assert advisory.metadata["component_currency"] == "INR"
    assert advisory.metadata["budget_currency"] is None
    assert unknown.is_feasible is True

    # A mismatched budget currency behaves the same way.
    mismatched = ConstraintEngine.evaluate_itinerary_graph(graph, budget_cents=100, hard_budget_ceiling=True, budget_currency="usd")
    assert "BUDGET_CEILING_EXCEEDED" not in _financial(mismatched)["hard"]
    assert _financial(mismatched)["soft"]["BUDGET_CURRENCY_UNVERIFIED"].metadata["budget_currency"] == "USD"


def test_budget_over_partial_costing_is_flagged_as_lower_bound():
    report = ConstraintEngine.evaluate_itinerary_graph(
        _graph(_flight(GOOD_FLIGHT), _hotel()), budget_cents=100, hard_budget_ceiling=True, budget_currency="INR"
    )
    block = _financial(report)["hard"]["BUDGET_CEILING_EXCEEDED"]
    assert block.metadata["partial_costing"] is True
    assert "lower bound" in block.description


def test_flat_metadata_keys_are_accepted():
    node = JourneyNode("N_FLAT", NodeType.ACTIVITY, "Desert safari", T0 + timedelta(days=1), T0 + timedelta(days=1, hours=4), "DXB",
                       metadata={"cost_unit_price": 300, "cost_quantity": 2, "cost_total": 650, "cost_currency": "aed", "cost_basis": "preview", "cost_source": "viator"})
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(node))
    violation = _financial(report)["hard"]["COST_ARITHMETIC_N_FLAT"]
    assert violation.metadata["currency"] == "AED"


def test_financial_hard_violations_sit_in_the_commercial_relaxation_tier():
    bad = {**GOOD_FLIGHT, "total": 1.0}
    report = ConstraintEngine.evaluate_itinerary_graph(_graph(_flight(bad)))
    entry = next(e for e in report.relaxation_hierarchy if e["constraint_id"] == "COST_ARITHMETIC_N_FLT")
    assert entry["priority_tier"] == 2
    assert entry["tier_name"] == "COMMERCIAL"


# ---------------------------------------------------------------------------
# Real compile path: the proposal compiler now costs its nodes, and its own
# output must pass the family it just gained.
# ---------------------------------------------------------------------------


def test_proposal_compiler_nodes_are_costed_and_pass(monkeypatch):
    from datetime import date

    from src.orchestration.proposal_compiler import AutonomousProposalCompiler

    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")

    captured = {}
    real = ConstraintEngine.evaluate_itinerary_graph

    def spy(graph, **kwargs):
        captured["graph"] = graph
        return real(graph, **kwargs)

    monkeypatch.setattr(ConstraintEngine, "evaluate_itinerary_graph", spy)

    dep = date.today() + timedelta(days=60)
    package = AutonomousProposalCompiler.compile_from_intake(
        trip_id="TRIP-FIN-COMPILER",
        raw_intake_text="Luxury week in Paris, private transfers.",
        destination="Paris",
        departure_date=dep,
        return_date=dep + timedelta(days=7),
        traveler_count=2,
        price_sensitivity=0.1,
        peak_season=True,
    )

    graph = captured["graph"]
    costs = {nid: node.metadata.get("cost") for nid, node in graph.nodes.items()}
    assert all(costs.values()), f"every compiled node must carry cost metadata: {costs}"
    assert {c["currency"] for c in costs.values()} == {"USD"}
    assert all(c["basis"] and c["source"] for c in costs.values())
    fin = _financial(real(graph, party_size=2))
    assert fin["hard"] == {}, fin["hard"]
    assert fin["soft"] == {}, fin["soft"]
    assert package.is_feasibility_passed is True
