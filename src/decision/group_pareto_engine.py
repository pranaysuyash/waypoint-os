"""
Group Travel Pareto Consensus & Split-Payment Ledger Engine (PER-GRP, GRP-01..12).

Models multi-traveler preference profiles, computes non-dominated Pareto consensus
with harmonic dissatisfaction penalties, manages asymmetric activity opt-ins,
and generates itemized split payment ledgers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class TravelerPreferenceProfile:
    """Individual traveler preference and constraint vector."""
    traveler_id: str
    name: str
    max_budget: float
    preferred_pace: str  # "RELAXED" | "MODERATE" | "FAST_PACED"
    activity_interests: List[str]  # e.g. ["CULTURE", "CULINARY", "ADVENTURE"]
    dietary_needs: List[str] = field(default_factory=list)
    requires_private_room: bool = False


@dataclass(slots=True)
class ItineraryProposalOption:
    """Itinerary candidate option being evaluated for group consensus."""
    option_id: str
    title: str
    cost_per_person: float
    pace: str
    activities: List[str]


@dataclass(slots=True)
class TravelerPaymentShare:
    """Itemized payment allocation for an individual group member."""
    traveler_id: str
    name: str
    base_share: float
    room_supplement: float
    opt_in_activities_amount: float
    total_owed: float
    amount_paid: float
    payment_status: str  # "PENDING" | "PAID" | "OVERDUE"
    payment_link: str = ""


class GroupParetoEngine:
    """Multi-Traveler Pareto Frontier Solver & Split Payment Manager."""

    @staticmethod
    def evaluate_traveler_satisfaction(
        traveler: TravelerPreferenceProfile,
        option: ItineraryProposalOption,
    ) -> float:
        """Computes a 0.0 to 1.0 individual satisfaction score for a traveler."""
        score = 1.0

        # Budget fit
        if option.cost_per_person > traveler.max_budget:
            overage_ratio = (option.cost_per_person - traveler.max_budget) / traveler.max_budget
            score -= min(0.6, overage_ratio * 0.8)

        # Pace alignment
        if traveler.preferred_pace != option.pace:
            score -= 0.2

        # Activity overlap
        if traveler.activity_interests:
            overlap = set(traveler.activity_interests) & set(option.activities)
            activity_ratio = len(overlap) / len(traveler.activity_interests)
            score *= (0.5 + 0.5 * activity_ratio)

        return max(0.05, min(1.0, score))

    @classmethod
    def solve_pareto_consensus(
        cls,
        travelers: List[TravelerPreferenceProfile],
        options: List[ItineraryProposalOption],
    ) -> Dict[str, Any]:
        """
        Evaluates itinerary options using harmonic mean satisfaction.
        Harmonic mean severely penalizes options that leave even one traveler deeply dissatisfied.
        """
        if not travelers or not options:
            return {"ranked_options": [], "best_consensus_option_id": None}

        evaluations = []

        for opt in options:
            scores = [cls.evaluate_traveler_satisfaction(t, opt) for t in travelers]
            # Harmonic Mean: N / sum(1 / s_i)
            harmonic_score = len(scores) / sum(1.0 / s for s in scores)
            min_score = min(scores)
            avg_score = sum(scores) / len(scores)

            verdict = "STRONG_CONSENSUS" if min_score >= 0.70 else "ACCEPTABLE_COMPROMISE" if min_score >= 0.45 else "DIVISIVE_DISPUTE"

            evaluations.append({
                "option_id": opt.option_id,
                "title": opt.title,
                "harmonic_consensus_score": round(harmonic_score, 3),
                "average_satisfaction": round(avg_score, 3),
                "minimum_satisfaction": round(min_score, 3),
                "consensus_verdict": verdict,
                "traveler_scores": [
                    {
                        "traveler_id": t.traveler_id,
                        "name": t.name,
                        "satisfaction": round(s, 2),
                    }
                    for t, s in zip(travelers, scores)
                ],
            })

        # Sort options descending by harmonic consensus score
        evaluations.sort(key=lambda x: x["harmonic_consensus_score"], reverse=True)

        return {
            "travelers_count": len(travelers),
            "ranked_options": evaluations,
            "best_consensus_option_id": evaluations[0]["option_id"] if evaluations else None,
        }

    @staticmethod
    def generate_split_payment_ledger(
        trip_id: str,
        total_shared_cost: float,
        travelers: List[TravelerPreferenceProfile],
        single_room_supplement_amount: float = 350.0,
        activity_opt_ins: Optional[Dict[str, float]] = None,
    ) -> List[TravelerPaymentShare]:
        """Generates itemized payment shares with custom room supplements and activity opt-ins."""
        n = len(travelers)
        base_per_person = round(total_shared_cost / n, 2)
        opt_ins = activity_opt_ins or {}

        ledger = []
        for t in travelers:
            room_supp = single_room_supplement_amount if t.requires_private_room else 0.0
            act_cost = opt_ins.get(t.traveler_id, 0.0)
            total = base_per_person + room_supp + act_cost

            ledger.append(
                TravelerPaymentShare(
                    traveler_id=t.traveler_id,
                    name=t.name,
                    base_share=base_per_person,
                    room_supplement=room_supp,
                    opt_in_activities_amount=act_cost,
                    total_owed=round(total, 2),
                    amount_paid=0.0,
                    payment_status="PENDING",
                    payment_link=f"https://pay.waypointos.com/group/{trip_id}/{t.traveler_id}",
                )
            )
        return ledger
