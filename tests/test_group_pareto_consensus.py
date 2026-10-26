"""
Group Travel Pareto Consensus & Split Ledgers Tests (PER-GRP, GRP-01..12).

T15 consolidation (2026-10-25): these pins now target the CANONICAL engine
(src.decision.group_consensus.GroupConsensusOptimizer) — the parallel
group_pareto_engine module is superseded. Original behavioral pins preserved;
new pins cover the consolidation's behavior improvements (validity-first
zero-out in the ranked solve, cross-vocab pacing, binding artifact).
"""

from src.decision.group_consensus import (
    GroupConsensusOptimizer,
    GroupLedgerMember,
    ItineraryOptionProposal,
    TravelerPreferenceProfile,
)


def test_pareto_consensus_harmonic_dissatisfaction():
    t1 = TravelerPreferenceProfile("T1", "Alice", max_budget_usd=2000, preferred_pacing="RELAXED", priority_activities=["CULTURE"])
    t2 = TravelerPreferenceProfile("T2", "Bob", max_budget_usd=5000, preferred_pacing="FAST_PACED", priority_activities=["ADVENTURE"])
    t3 = TravelerPreferenceProfile("T3", "Charlie", max_budget_usd=3500, preferred_pacing="MODERATE", priority_activities=["CULTURE", "CULINARY"])

    # Opt 1: High cost ($4000) -> breaches Alice's AND Charlie's hard budgets
    # (INFEASIBLE under the canonical validity-first rule)
    opt_expensive = ItineraryOptionProposal("OPT-EXP", "Luxury Adventure", total_cost_per_person_usd=4000, pacing="FAST_PACED", included_activities=["ADVENTURE"], rooming_configuration="")
    # Opt 2: $1800 — within EVERY traveler's max budget. (The old fixture's
    # $2200 was itself a breach under validity-first; the compromise must be
    # genuinely valid now — the semantic tightening of this merge.)
    opt_balanced = ItineraryOptionProposal("OPT-BAL", "Cultural Explorer", total_cost_per_person_usd=1800, pacing="MODERATE", included_activities=["CULTURE", "CULINARY"], rooming_configuration="")

    res = GroupConsensusOptimizer.solve_group_consensus_ranked([t1, t2, t3], [opt_expensive, opt_balanced])
    assert res["best_consensus_option_id"] == "OPT-BAL"
    assert res["ranked_options"][0]["harmonic_consensus_score"] > res["ranked_options"][1]["harmonic_consensus_score"]


def test_split_payment_ledger_generation():
    t1 = GroupLedgerMember("T1", "Alice", requires_private_room=True)
    t2 = GroupLedgerMember("T2", "Bob", requires_private_room=False)

    # Shared cost $2000 ($1000 base each), single room supplement $350 for Alice, Bob opts in for $150 winery tour
    ledger = GroupConsensusOptimizer.generate_split_payment_ledger(
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


# ---------------------------------------------------------------------------
# T15 consolidation pins — behavior improvements from the merge
# ---------------------------------------------------------------------------


def test_ranked_solve_zeroes_breached_budget_option():
    """Validity-first (topic 50) now holds in the ranked solve too: an option
    breaching a traveler's hard budget is INFEASIBLE — zeroed scores, sinks
    below every valid option, and can never be the best consensus option even
    when its un-zeroed harmonic would have ranked first."""
    rich = TravelerPreferenceProfile("T1", "Rich", max_budget_usd=5000, preferred_pacing="INTENSE", priority_activities=["ADVENTURE"])
    frugal = TravelerPreferenceProfile("T2", "Frugal", max_budget_usd=1500, preferred_pacing="RELAXED", priority_activities=["CULTURE"])

    # OPT-LUX: perfect for Rich, breaches Frugal's hard budget. Under the old
    # parallel engine its harmonic (dragged only by Frugal's dissatisfaction)
    # could still outrank a valid compromise.
    opt_lux = ItineraryOptionProposal("OPT-LUX", "Luxury Blast", total_cost_per_person_usd=4500, pacing="INTENSE", included_activities=["ADVENTURE"], rooming_configuration="")
    # OPT-MID: acceptable compromise, nobody's budget breached.
    opt_mid = ItineraryOptionProposal("OPT-MID", "Middle Path", total_cost_per_person_usd=1200, pacing="BALANCED", included_activities=["ADVENTURE", "CULTURE"], rooming_configuration="")

    res = GroupConsensusOptimizer.solve_group_consensus_ranked([rich, frugal], [opt_lux, opt_mid])
    assert res["best_consensus_option_id"] == "OPT-MID"
    lux_row = next(r for r in res["ranked_options"] if r["option_id"] == "OPT-LUX")
    assert lux_row["consensus_verdict"] == "INFEASIBLE"
    assert lux_row["harmonic_consensus_score"] == 0.0
    assert lux_row["hard_violations"], "breach evidence must travel with the row"
    # The binding marks the winner and records the dissenting member.
    assert res["binding"]["best_option_id"] == "OPT-MID"
    assert res["binding"]["infeasible_winner_zeroed"] is False


def test_ranked_solve_cross_vocab_pacing_no_false_mismatch():
    """The two historical pacing vocabularies must not create false penalties:
    MODERATE (pareto wire) == BALANCED (canonical), FAST_PACED == INTENSE."""
    t = TravelerPreferenceProfile("T1", "Alice", max_budget_usd=3000, preferred_pacing="BALANCED", priority_activities=[])
    opt = ItineraryOptionProposal("OPT-1", "Trip", total_cost_per_person_usd=1000, pacing="MODERATE", included_activities=[], rooming_configuration="")
    res = GroupConsensusOptimizer.solve_group_consensus_ranked([t], [opt])
    row = res["ranked_options"][0]
    assert row["consensus_verdict"] == "STRONG_CONSENSUS"
    assert row["traveler_scores"][0]["satisfaction"] == 1.0

    # Binding: full acceptance, no dissent.
    assert res["binding"]["accepted_traveler_ids"] == ["T1"]
    assert res["binding"]["dissent"] == []


def test_ranked_solve_empty_inputs_emit_empty_binding():
    res = GroupConsensusOptimizer.solve_group_consensus_ranked([], [])
    assert res["ranked_options"] == []
    assert res["best_consensus_option_id"] is None
    assert res["binding"]["best_option_id"] is None
    assert res["binding"]["emitted_at"]
