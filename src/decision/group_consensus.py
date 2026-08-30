"""
src/decision/group_consensus.py — Multi-Party Group Travel Preference Consensus Optimizer.

Grounding doctrine:
- Family/Group Travel Architect: Resolve multi-traveler budget, pacing, and activity conflicts using Pareto-optimal scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TravelerPreferenceProfile:
    """Individual traveler preference bounds and priorities."""
    traveler_id: str
    name: str
    max_budget_usd: float
    preferred_pacing: str  # RELAXED, BALANCED, INTENSE
    priority_activities: list[str]  # e.g. ["culinary", "historical", "beach", "nightlife"]
    requires_private_room: bool = True
    dietary_restrictions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ItineraryOptionProposal:
    """Candidate itinerary option to be scored across group members."""
    option_id: str
    title: str
    total_cost_per_person_usd: float
    pacing: str
    included_activities: list[str]
    rooming_configuration: str


@dataclass(slots=True)
class GroupConsensusScore:
    """Evaluation of an itinerary option against the collective group."""
    option_id: str
    title: str
    overall_consensus_score: float  # 0.0 - 100.0
    individual_satisfaction: dict[str, float]  # traveler_id -> satisfaction score 0.0 - 100.0
    is_pareto_optimal: bool
    budget_violations: list[str]  # traveler names whose max budget is exceeded
    compromises_made: list[str]
    recommendation_tier: str  # STRONG_MATCH, ACCEPTABLE_COMPROMISE, INFEASIBLE


class GroupConsensusOptimizer:
    """Computes Pareto-optimal group itinerary choices minimizing individual dissatisfaction."""

    @classmethod
    def evaluate_group_consensus(
        cls,
        travelers: list[TravelerPreferenceProfile],
        candidate_options: list[ItineraryOptionProposal],
    ) -> list[GroupConsensusScore]:
        """Evaluate and rank all candidate itineraries across all travelers in the group."""
        if not travelers or not candidate_options:
            return []

        results: list[GroupConsensusScore] = []

        for opt in candidate_options:
            satisfactions: dict[str, float] = {}
            budget_violations: list[str] = []
            compromises: list[str] = []

            for t in travelers:
                t_score = 100.0

                # 1. Budget check
                if opt.total_cost_per_person_usd > t.max_budget_usd:
                    excess_pct = (opt.total_cost_per_person_usd - t.max_budget_usd) / t.max_budget_usd
                    penalty = min(50.0, excess_pct * 100.0)
                    t_score -= penalty
                    budget_violations.append(f"{t.name} (budget ${t.max_budget_usd:.0f} vs cost ${opt.total_cost_per_person_usd:.0f})")

                # 2. Pacing alignment
                if t.preferred_pacing != opt.pacing:
                    t_score -= 15.0
                    compromises.append(f"{t.name} prefers {t.preferred_pacing} pacing (option is {opt.pacing})")

                # 3. Activity overlap
                if t.priority_activities:
                    overlap = set(t.priority_activities).intersection(set(opt.included_activities))
                    overlap_ratio = len(overlap) / len(t.priority_activities)
                    t_score -= (1.0 - overlap_ratio) * 20.0

                satisfactions[t.traveler_id] = max(0.0, round(t_score, 1))

            # Overall group score is the harmonic average (penalizes extreme dissatisfaction for any single member)
            avg_score = sum(satisfactions.values()) / len(satisfactions)
            min_score = min(satisfactions.values())

            # Weighted composite favoring fairness
            consensus_score = round((avg_score * 0.7) + (min_score * 0.3), 1)

            tier = "STRONG_MATCH"
            if consensus_score < 70.0:
                tier = "ACCEPTABLE_COMPROMISE"
            if len(budget_violations) > 0 or consensus_score < 50.0:
                tier = "INFEASIBLE" if min_score < 40.0 else "ACCEPTABLE_COMPROMISE"

            results.append(
                GroupConsensusScore(
                    option_id=opt.option_id,
                    title=opt.title,
                    overall_consensus_score=consensus_score,
                    individual_satisfaction=satisfactions,
                    is_pareto_optimal=False,  # Evaluated below
                    budget_violations=list(set(budget_violations)),
                    compromises_made=list(set(compromises)),
                    recommendation_tier=tier,
                )
            )

        # Mark Pareto optimal options (options where no other option is strictly better for all members)
        for i, res_a in enumerate(results):
            is_dominated = False
            for j, res_b in enumerate(results):
                if i != j:
                    all_b_better_or_equal = all(
                        res_b.individual_satisfaction[t.traveler_id] >= res_a.individual_satisfaction[t.traveler_id]
                        for t in travelers
                    )
                    at_least_one_b_strictly_better = any(
                        res_b.individual_satisfaction[t.traveler_id] > res_a.individual_satisfaction[t.traveler_id]
                        for t in travelers
                    )
                    if all_b_better_or_equal and at_least_one_b_strictly_better:
                        is_dominated = True
                        break
            # Update slots dataclass
            results[i] = GroupConsensusScore(
                option_id=res_a.option_id,
                title=res_a.title,
                overall_consensus_score=res_a.overall_consensus_score,
                individual_satisfaction=res_a.individual_satisfaction,
                is_pareto_optimal=not is_dominated,
                budget_violations=res_a.budget_violations,
                compromises_made=res_a.compromises_made,
                recommendation_tier=res_a.recommendation_tier,
            )

        results.sort(key=lambda x: x.overall_consensus_score, reverse=True)
        return results
