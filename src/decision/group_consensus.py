"""
src/decision/group_consensus.py — Multi-Party Group Travel Preference Consensus Optimizer.

Grounding doctrine:
- Family/Group Travel Architect: Resolve multi-traveler budget, pacing, and activity conflicts using Pareto-optimal scoring.

Validity-first scoring (exploration topic 50 zero-out rule, adopted 2026-10-22):
a declared hard bound — a traveler's max budget — is a validity constraint, not
a preference. An option that breaches it is INFEASIBLE: its consensus composite
contributes zero, it can never be Pareto-optimal, and it can never dominate a
valid option out of the ranking. Individual satisfaction numbers are retained
as diagnostics only ("preference scores are not a bypass"). Pacing and activity
misalignment remain ordinary tradeoffs and score normally.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# T15 consolidation (2026-10-25): this module is the canonical group-consensus
# engine. The former parallel engine (src/decision/group_pareto_engine.py) is
# superseded — its harmonic-ranked solve, split-payment ledger, and pacing
# vocabulary are absorbed here so both serving routers
# (/api/v1/group-consensus and /api/v1/group-pareto) answer from ONE engine.
# Wire contracts are preserved; behavior improves: the harmonic ranking now
# applies the same validity-first zero-out as the composite scoring, so a
# budget-breached option can no longer win the ranked solve.
# ---------------------------------------------------------------------------

# The two serving surfaces historically used different pacing vocabularies
# (pareto wire: RELAXED/MODERATE/FAST_PACED; canonical scoring:
# RELAXED/BALANCED/INTENSE). Normalized so cross-vocab clients never get a
# false pacing mismatch.
_PACE_ALIASES: Dict[str, str] = {
    "relaxed": "RELAXED",
    "moderate": "BALANCED",
    "balanced": "BALANCED",
    "fast_paced": "INTENSE",
    "fastpaced": "INTENSE",
    "intense": "INTENSE",
}


def normalize_pacing(pacing: str) -> str:
    return _PACE_ALIASES.get((pacing or "").strip().lower(), (pacing or "").strip().upper())


@dataclass(slots=True)
class GroupLedgerMember:
    """Lightweight member input for the split-payment ledger (tracking-only)."""

    traveler_id: str
    name: str
    requires_private_room: bool = False


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


@dataclass(slots=True)
class GroupConsensusBinding:
    """The consensus artifact for a solved group decision.

    Emitted by ``solve_group_consensus_ranked``: names the best option, each
    traveler's acceptance (satisfaction at/above the acceptable threshold),
    and recorded dissent. Tracking/decision-record only — booking-gate wiring
    is a trigger-based follow-up (group-booking persona entering launch scope).
    """

    trip_scope: str
    best_option_id: Optional[str]
    best_option_title: Optional[str]
    accepted_traveler_ids: List[str]
    dissent: List[Dict[str, Any]]  # [{traveler_id, name, satisfaction, reason}]
    infeasible_winner_zeroed: bool  # best-ranked option breached a hard bound
    emitted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_scope": self.trip_scope,
            "best_option_id": self.best_option_id,
            "best_option_title": self.best_option_title,
            "accepted_traveler_ids": self.accepted_traveler_ids,
            "dissent": self.dissent,
            "infeasible_winner_zeroed": self.infeasible_winner_zeroed,
            "emitted_at": self.emitted_at,
        }


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
    # Validity-first zero-out (topic 50): populated when a hard bound is breached.
    hard_violations: list[str] = field(default_factory=list)
    preference_scoring_suppressed: bool = False


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

                # 1. Budget check — a HARD bound. A breach docks the member's
                # diagnostic satisfaction AND records a validity failure that
                # zeroes the composite below; the penalty can never smuggle the
                # option back into contention.
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

            # Validity-first zero-out: a hard budget breach zeroes the composite.
            if budget_violations:
                consensus_score = 0.0
                tier = "INFEASIBLE"
            else:
                avg_score = sum(satisfactions.values()) / len(satisfactions)
                min_score = min(satisfactions.values())

                # Weighted composite favoring fairness
                consensus_score = round((avg_score * 0.7) + (min_score * 0.3), 1)

                tier = "STRONG_MATCH"
                if consensus_score < 70.0:
                    tier = "ACCEPTABLE_COMPROMISE"
                if consensus_score < 50.0:
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
                    hard_violations=list(set(budget_violations)),
                    preference_scoring_suppressed=bool(budget_violations),
                )
            )

        # Mark Pareto optimal options (options where no other VALID option is
        # strictly better for all members). Zero-scored options are never
        # Pareto-optimal and never dominate a valid option out of the ranking —
        # a disqualified plan cannot eliminate a qualifying one.
        for i, res_a in enumerate(results):
            if res_a.preference_scoring_suppressed:
                results[i] = replace(res_a, is_pareto_optimal=False)
                continue
            is_dominated = False
            for j, res_b in enumerate(results):
                if i == j or res_b.preference_scoring_suppressed:
                    continue
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
            results[i] = replace(res_a, is_pareto_optimal=not is_dominated)

        results.sort(key=lambda x: x.overall_consensus_score, reverse=True)
        return results

    @staticmethod
    def _traveler_satisfaction_fraction(
        t: TravelerPreferenceProfile,
        opt: ItineraryOptionProposal,
    ) -> Tuple[float, Optional[str]]:
        """Per-traveler satisfaction in 0..1 with a validity reason on breach.

        Shared by the composite (0-100) and harmonic-ranked surfaces so both
        answer from one scoring truth. Budget is a HARD bound (validity);
        pacing/activity are ordinary tradeoffs.
        """
        if opt.total_cost_per_person_usd > t.max_budget_usd:
            return 0.0, (
                f"{t.name}: cost ${opt.total_cost_per_person_usd:.0f} exceeds "
                f"max budget ${t.max_budget_usd:.0f}"
            )
        score = 1.0
        if normalize_pacing(t.preferred_pacing) != normalize_pacing(opt.pacing):
            score -= 0.3
        if t.priority_activities:
            overlap = (
                {a.strip().lower() for a in t.priority_activities}
                & {a.strip().lower() for a in opt.included_activities}
            )
            score -= (1.0 - len(overlap) / len(t.priority_activities)) * 0.4
        return max(0.0, round(score, 3)), None

    @classmethod
    def solve_group_consensus_ranked(
        cls,
        travelers: List[TravelerPreferenceProfile],
        options: List[ItineraryOptionProposal],
        trip_scope: str = "",
    ) -> Dict[str, Any]:
        """Harmonic-ranked solve (the former pareto engine's wire contract),
        now validity-first: a budget-breaching option zeroes its scores and
        carries an INFEASIBLE verdict — it can still appear ranked (as a
        diagnostic), but its score can never win while a valid option exists.
        Emits a GroupConsensusBinding for the top option."""
        if not travelers or not options:
            binding = GroupConsensusBinding(
                trip_scope=trip_scope, best_option_id=None, best_option_title=None,
                accepted_traveler_ids=[], dissent=[],
                infeasible_winner_zeroed=False,
            )
            return {
                "travelers_count": len(travelers),
                "ranked_options": [],
                "best_consensus_option_id": None,
                "binding": binding.to_dict(),
            }

        evaluations: List[Dict[str, Any]] = []
        for opt in options:
            scores: List[float] = []
            hard_violations: List[str] = []
            for t in travelers:
                s, violation = cls._traveler_satisfaction_fraction(t, opt)
                scores.append(s)
                if violation:
                    hard_violations.append(violation)

            zeroed = bool(hard_violations)
            if zeroed:
                harmonic = 0.0
                avg = 0.0
                min_s = 0.0
                verdict = "INFEASIBLE"
            else:
                harmonic = (
                    len(scores) / sum(1.0 / s for s in scores)
                    if all(s > 0 for s in scores) else 0.0
                )
                min_s = min(scores)
                avg = sum(scores) / len(scores)
                verdict = (
                    "STRONG_CONSENSUS" if min_s >= 0.70
                    else "ACCEPTABLE_COMPROMISE" if min_s >= 0.45
                    else "DIVISIVE_DISPUTE"
                )

            evaluations.append({
                "option_id": opt.option_id,
                "title": opt.title,
                "harmonic_consensus_score": round(harmonic, 3),
                "average_satisfaction": round(avg, 3),
                "minimum_satisfaction": round(min_s, 3),
                "consensus_verdict": verdict,
                "hard_violations": hard_violations,  # additive: validity evidence
                "traveler_scores": [
                    {
                        "traveler_id": t.traveler_id,
                        "name": t.name,
                        "satisfaction": round(s, 2),
                    }
                    for t, s in zip(travelers, scores)
                ],
            })

        # Rank: valid options by harmonic desc; INFEASIBLE options always sink
        # below every valid option, preserving relative order among themselves.
        valid = [e for e in evaluations if e["consensus_verdict"] != "INFEASIBLE"]
        zeroed_rows = [e for e in evaluations if e["consensus_verdict"] == "INFEASIBLE"]
        valid.sort(key=lambda x: x["harmonic_consensus_score"], reverse=True)
        ranked = valid + zeroed_rows

        best = ranked[0] if ranked else None
        binding = GroupConsensusBinding(
            trip_scope=trip_scope,
            best_option_id=best["option_id"] if best else None,
            best_option_title=best["title"] if best else None,
            accepted_traveler_ids=[
                ts["traveler_id"]
                for ts in (best["traveler_scores"] if best else [])
                if ts["satisfaction"] >= 0.45
            ],
            dissent=[
                {
                    "traveler_id": ts["traveler_id"],
                    "name": ts["name"],
                    "satisfaction": ts["satisfaction"],
                    "reason": "below acceptable-compromise threshold (0.45)",
                }
                for ts in (best["traveler_scores"] if best else [])
                if ts["satisfaction"] < 0.45
            ],
            infeasible_winner_zeroed=bool(best and best["consensus_verdict"] == "INFEASIBLE"),
        )

        return {
            "travelers_count": len(travelers),
            "ranked_options": ranked,
            "best_consensus_option_id": best["option_id"] if best else None,
            "binding": binding.to_dict(),
        }

    @staticmethod
    def generate_split_payment_ledger(
        trip_id: str,
        total_shared_cost: float,
        travelers: List[GroupLedgerMember],
        single_room_supplement_amount: float = 350.0,
        activity_opt_ins: Optional[Dict[str, float]] = None,
    ) -> List[TravelerPaymentShare]:
        """Itemized payment shares with room supplements and activity opt-ins.

        Tracking-only: this computes WHO OWES WHAT on paper; it never moves
        money and never touches a payment provider (FND-0233 boundary).
        """
        n = len(travelers)
        base_per_person = round(total_shared_cost / n, 2) if n else 0.0
        opt_ins = activity_opt_ins or {}

        ledger: List[TravelerPaymentShare] = []
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
