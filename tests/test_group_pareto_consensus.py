"""
Group Travel Pareto Consensus & Split Ledgers Tests (PER-GRP, GRP-01..12).
"""

from src.decision.group_pareto_engine import (
    GroupParetoEngine,
    ItineraryProposalOption,
    TravelerPreferenceProfile,
)


def test_pareto_consensus_harmonic_dissatisfaction():
    t1 = TravelerPreferenceProfile("T1", "Alice", max_budget=2000, preferred_pace="RELAXED", activity_interests=["CULTURE"])
    t2 = TravelerPreferenceProfile("T2", "Bob", max_budget=5000, preferred_pace="FAST_PACED", activity_interests=["ADVENTURE"])
    t3 = TravelerPreferenceProfile("T3", "Charlie", max_budget=3500, preferred_pace="MODERATE", activity_interests=["CULTURE", "CULINARY"])

    # Opt 1: High cost ($4000) -> Leaves Alice severely dissatisfied
    opt_expensive = ItineraryProposalOption("OPT-EXP", "Luxury Adventure", cost_per_person=4000, pace="FAST_PACED", activities=["ADVENTURE"])
    # Opt 2: Balanced ($2200) -> Moderate compromise for all
    opt_balanced = ItineraryProposalOption("OPT-BAL", "Cultural Explorer", cost_per_person=2200, pace="MODERATE", activities=["CULTURE", "CULINARY"])

    res = GroupParetoEngine.solve_pareto_consensus([t1, t2, t3], [opt_expensive, opt_balanced])
    assert res["best_consensus_option_id"] == "OPT-BAL"
    assert res["ranked_options"][0]["harmonic_consensus_score"] > res["ranked_options"][1]["harmonic_consensus_score"]


def test_split_payment_ledger_generation():
    t1 = TravelerPreferenceProfile("T1", "Alice", max_budget=2000, preferred_pace="MODERATE", activity_interests=[], requires_private_room=True)
    t2 = TravelerPreferenceProfile("T2", "Bob", max_budget=2000, preferred_pace="MODERATE", activity_interests=[], requires_private_room=False)

    # Shared cost $2000 ($1000 base each), single room supplement $350 for Alice, Bob opts in for $150 winery tour
    ledger = GroupParetoEngine.generate_split_payment_ledger(
        trip_id="TRIP-GRP-10",
        total_shared_cost=2000.0,
        travelers=[t1, t2],
        single_room_supplement_amount=350.0,
        activity_opt_ins={"T2": 150.0},
    )

    assert len(ledger) == 2
    assert ledger[0].name == "Alice"
    assert ledger[0].total_owed == 1350.0  # 1000 + 350
    assert ledger[1].name == "Bob"
    assert ledger[1].total_owed == 1150.0  # 1000 + 150
