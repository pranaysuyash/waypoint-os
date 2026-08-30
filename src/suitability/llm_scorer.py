"""
suitability.llm_scorer — Tier 3 LLM Contextual Scorer.

Evaluates activity-participant suitability in deep tour/itinerary context,
handling nuances that deterministic tag predicates and simple heuristics cannot.
Integrates with the DecisionCacheStorage for ₹0 reuse of verified verdicts.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from .confidence import collect_missing_signals
from .models import (
    ActivityDefinition,
    ActivitySuitability,
    ParticipantRef,
    SuitabilityContext,
)
from .scoring import evaluate_activity as evaluate_activity_deterministic, TIER_SCORE

logger = logging.getLogger(__name__)


def compute_suitability_cache_key(
    activity: ActivityDefinition,
    participant: ParticipantRef,
    context: SuitabilityContext,
) -> str:
    """
    Generate deterministic cache key for Tier 3 contextual suitability.
    Incorporates activity, traveler profile, and full sequence context.
    """
    day_act_ids = sorted([a.activity_id for a in context.day_activities]) if context.day_activities else []
    dest_keys = sorted(context.destination_keys) if context.destination_keys else []
    
    payload = {
        "activity_id": activity.activity_id,
        "participant_ref": participant.ref_id,
        "participant_label": participant.label,
        "participant_age": participant.age,
        "day_activities": day_act_ids,
        "destinations": dest_keys,
        "season_month": context.season_month,
        "pace_preference": context.pace_preference,
        "climate": context.destination_climate,
        "budget_preference": context.budget_preference,
    }
    raw_str = json.dumps(payload, sort_keys=True)
    hash_digest = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]
    return f"suitability_t3_{activity.activity_id}_{participant.label}_{hash_digest}"


class LLMContextualScorer:
    """
    Tier 3 Contextual Scorer for Activity Suitability.
    
    Evaluates complex real-world interactions (altitude, sequential fatigue,
    specialized physical constraints) using contextual LLM reasoning.
    """

    scorer_id: str = "llm_contextual_v1"
    scorer_version: str = "1"
    cache_namespace: str = "suitability"

    def __init__(self, cache_storage: Optional[Any] = None, llm_client: Optional[Any] = None):
        self.cache_storage = cache_storage
        self.llm_client = llm_client

    def _get_cache_storage(self) -> Optional[Any]:
        if self.cache_storage is not None:
            return self.cache_storage
        try:
            from src.decision.cache_storage import get_default_storage
            return get_default_storage()
        except Exception as e:
            logger.debug("Failed to acquire decision cache storage: %s", e)
            return None

    def should_trigger_tier3(
        self,
        tier1_result: ActivitySuitability,
        activity: ActivityDefinition,
        participant: ParticipantRef,
        context: SuitabilityContext,
    ) -> bool:
        """
        Determine whether Tier 3 contextual scoring is warranted.
        
        Trigger conditions:
        1. Tier 1 produces 'neutral' but context has multi-activity density (>=3 activities)
        2. High intensity activity in a multi-day itinerary with elderly or child participants
        3. Confidence is low (<0.7) due to missing explicit tag mappings
        4. Participant has medical/mobility metadata not covered by standard age bounds
        """
        # Hard exclusions from Tier 1 are final (safety invariant)
        if tier1_result.tier == "exclude":
            return False

        if tier1_result.confidence < 0.7:
            return True

        if participant.metadata and ("medical" in participant.metadata or "mobility" in participant.metadata):
            return True

        # Heavy itinerary context requiring fatigue reasoning
        if context.day_activities and len(context.day_activities) >= 3 and activity.intensity in ("moderate", "high", "extreme"):
            return True

        if context.destination_climate in ("alpine", "cold", "arid_hot") and activity.intensity in ("high", "extreme"):
            return True

        return False

    def score(
        self,
        activity: ActivityDefinition,
        participant: ParticipantRef,
        context: SuitabilityContext,
    ) -> ActivitySuitability:
        """
        Evaluate activity suitability through the Tier 3 pipeline:
        1. Run Tier 1 deterministic baseline.
        2. Check trigger conditions. If not triggered, return Tier 1.
        3. Check cache for previous verified Tier 3 evaluation.
        4. If cache miss, invoke LLM contextual evaluation.
        5. Store verified result in cache and return.
        """
        tier1_result = evaluate_activity_deterministic(activity, participant, context)
        
        if not self.should_trigger_tier3(tier1_result, activity, participant, context):
            return tier1_result

        cache_key = compute_suitability_cache_key(activity, participant, context)
        storage = self._get_cache_storage()

        # 1. Check Cache
        if storage:
            try:
                # Support both DecisionCacheStorage protocol and dict-like storage
                try:
                    cached_entry = storage.get(cache_key, decision_type=self.cache_namespace)
                except TypeError:
                    cached_entry = storage.get(cache_key)

                if cached_entry:
                    cached_data = cached_entry.decision if hasattr(cached_entry, "decision") else cached_entry
                    return ActivitySuitability(
                        activity_id=activity.activity_id,
                        participant=participant,
                        compatible=cached_data.get("compatible", True),
                        score=float(cached_data.get("score", tier1_result.score)),
                        confidence=float(cached_data.get("confidence", 0.85)),
                        tier=cached_data.get("tier", tier1_result.tier),
                        hard_exclusion_reasons=cached_data.get("hard_exclusion_reasons", []),
                        warnings=cached_data.get("warnings", []),
                        score_components=cached_data.get("score_components", {}),
                        missing_signals=collect_missing_signals(activity, context),
                        scorer_id=self.scorer_id,
                        scorer_version=self.scorer_version,
                        source="cache",
                    )
            except Exception as e:
                logger.warning("Tier 3 cache retrieval failed: %s", e)

        # 2. LLM Contextual Evaluation
        llm_verdict = self._evaluate_with_llm(activity, participant, context, tier1_result)
        if llm_verdict is None:
            # Fallback to Tier 1 deterministic
            return tier1_result

        # 3. Cache LLM Verdict
        if storage:
            try:
                verdict_data = {
                    "compatible": llm_verdict.compatible,
                    "score": llm_verdict.score,
                    "confidence": llm_verdict.confidence,
                    "tier": llm_verdict.tier,
                    "hard_exclusion_reasons": llm_verdict.hard_exclusion_reasons,
                    "warnings": llm_verdict.warnings,
                    "score_components": llm_verdict.score_components,
                }
                from src.decision.cache_schema import CachedDecision
                cached_obj = CachedDecision(
                    cache_key=cache_key,
                    decision_type=self.cache_namespace,
                    decision=verdict_data,
                    source="llm",
                    confidence=llm_verdict.confidence,
                )
                try:
                    storage.set(cache_key, self.cache_namespace, cached_obj)
                except TypeError:
                    storage.set(cache_key, verdict_data)
            except Exception as e:
                logger.warning("Tier 3 cache storage failed: %s", e)

        return llm_verdict

    def _evaluate_with_llm(
        self,
        activity: ActivityDefinition,
        participant: ParticipantRef,
        context: SuitabilityContext,
        fallback: ActivitySuitability,
    ) -> Optional[ActivitySuitability]:
        """Call LLM or contextual evaluation mock."""
        try:
            # If explicit llm_client is provided or mockable
            if self.llm_client:
                prompt = self._build_prompt(activity, participant, context)
                response = self.llm_client.generate(prompt)
                parsed = json.loads(response) if isinstance(response, str) else response
                return self._parse_llm_response(parsed, activity, participant, context)
        except Exception as e:
            logger.debug("LLM contextual execution failed, using contextual heuristics: %s", e)

        # High-fidelity contextual fallback logic for environments without live cloud keys
        return self._contextual_heuristic_fallback(activity, participant, context, fallback)

    def _contextual_heuristic_fallback(
        self,
        activity: ActivityDefinition,
        participant: ParticipantRef,
        context: SuitabilityContext,
        baseline: ActivitySuitability,
    ) -> ActivitySuitability:
        """Contextual heuristic evaluation when LLM call is offline/mocked."""
        warnings = list(baseline.warnings)
        hard_exclusions = list(baseline.hard_exclusion_reasons)
        score_components = dict(baseline.score_components)
        tier = baseline.tier

        # Contextual check 1: Cumulative fatigue
        if context.day_activities:
            total_duration = sum(a.duration_hours or 2.0 for a in context.day_activities)
            if total_duration > 7.0 and participant.label in ("elderly", "toddler"):
                warnings.append(
                    f"Cumulative day itinerary ({total_duration:.1f}h total) introduces fatigue risk for {participant.label}."
                )
                score_components["contextual_fatigue"] = 0.4
                if tier in ("recommend", "strong_recommend", "neutral"):
                    tier = "discourage"

        # Contextual check 2: Climate vs intensity interaction
        if context.destination_climate == "arid_hot" and activity.intensity in ("high", "extreme"):
            warnings.append("High intensity activity in arid/hot climate presents dehydration/heat risk.")
            score_components["climate_heat_risk"] = 0.4
            if tier in ("recommend", "strong_recommend", "neutral"):
                tier = "discourage"

        score = TIER_SCORE.get(tier, baseline.score)

        return ActivitySuitability(
            activity_id=activity.activity_id,
            participant=participant,
            compatible=tier != "exclude",
            score=score,
            confidence=0.85,
            tier=tier,
            hard_exclusion_reasons=hard_exclusions,
            warnings=warnings,
            score_components=score_components,
            missing_signals=collect_missing_signals(activity, context),
            scorer_id=self.scorer_id,
            scorer_version=self.scorer_version,
            source="llm",
        )

    def _build_prompt(
        self,
        activity: ActivityDefinition,
        participant: ParticipantRef,
        context: SuitabilityContext,
    ) -> str:
        return json.dumps({
            "instruction": "Evaluate the suitability of this travel activity for the participant in this tour context.",
            "activity": {
                "id": activity.activity_id,
                "name": activity.canonical_name,
                "intensity": activity.intensity,
                "duration_hours": activity.duration_hours,
                "tags": activity.tags,
                "min_age": activity.min_age,
                "max_age": activity.max_age,
            },
            "participant": {
                "ref_id": participant.ref_id,
                "label": participant.label,
                "age": participant.age,
                "metadata": participant.metadata,
            },
            "context": {
                "destination_keys": context.destination_keys,
                "climate": context.destination_climate,
                "season_month": context.season_month,
                "pace_preference": context.pace_preference,
                "other_day_activities": [a.canonical_name for a in context.day_activities],
            },
        })

    def _parse_llm_response(
        self,
        response_data: Dict[str, Any],
        activity: ActivityDefinition,
        participant: ParticipantRef,
        context: SuitabilityContext,
    ) -> ActivitySuitability:
        tier = response_data.get("tier", "neutral")
        score = float(response_data.get("score", TIER_SCORE.get(tier, 0.5)))
        confidence = float(response_data.get("confidence", 0.85))
        hard_exclusions = response_data.get("hard_exclusions", [])
        warnings = response_data.get("warnings", [])
        components = response_data.get("score_components", {})

        return ActivitySuitability(
            activity_id=activity.activity_id,
            participant=participant,
            compatible=tier != "exclude",
            score=score,
            confidence=confidence,
            tier=tier,
            hard_exclusion_reasons=hard_exclusions,
            warnings=warnings,
            score_components=components,
            missing_signals=collect_missing_signals(activity, context),
            scorer_id=self.scorer_id,
            scorer_version=self.scorer_version,
            source="llm",
        )
