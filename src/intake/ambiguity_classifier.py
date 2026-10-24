"""
intake.ambiguity_classifier — Semantic intake completeness and ambiguity gating.

Uses TypeSafe System One (Jev) calibrated decisions (Noul / Choice) to evaluate
whether an inbound customer trip inquiry has sufficient clarity across the four
core travel dimensions:
  1. Destination: is destination or region actionable?
  2. Dates: is a date window, duration, or specific period provided?
  3. Party: is traveler count/composition clear?
  4. Budget: is a budget tier or limit specified?

And decides the recommended next action:
  - PROCEED: sufficient info to draft initial itinerary/proposal
  - ASK_FOLLOWUP: actionable inquiry, but missing 1+ critical slots
  - ESCALATE: contradictory, unresolvable, or non-travel input

First principles:
  - Semantic judgments handled by Jev (calibrated noul/choice).
  - Deterministic fallback rule-engine when offline or client unavailable.
  - Zero PII required (sanitized message text only).
  - Calibrated confidence gating: low confidence on PROCEED triggers ASK_FOLLOWUP.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.llm.typesafe_client import TypesafeJevClient

logger = logging.getLogger(__name__)

# Minimum Noul probability to consider a dimension "clear"
_CLARITY_THRESHOLD = 0.50

# Minimum confidence required to trust a PROCEED choice autonomously
_AUTONOMOUS_PROCEED_CONFIDENCE = 0.60

# Confidence provenance (FND-0352). A confidence number is data, not
# decoration: it must trace to a calibrated model output or be absent.
#   model_calibrated — Jev's own calibrated ``jev_confidence``.
#   rule_heuristic   — the deterministic keyword scan. It has NO calibration,
#                      so it reports ``confidence=None`` ("unknown"), never a
#                      constant chosen to feel right. Downstream routing
#                      (decision.py, ADR-008 Lane A3) treats an unknown
#                      confidence as not autonomously trustworthy and raises
#                      the operator-review flag — the honest degradation when
#                      the model lane is unavailable.
CONFIDENCE_METHOD_MODEL = "model_calibrated"
CONFIDENCE_METHOD_RULE = "rule_heuristic"

# Why the rule path served instead of the model lane (FND-0352). Downstream
# routing distinguishes a DELIBERATE posture (lane unconfigured per ADR-008 —
# rule mode by design, provenance recorded, no advisory nag on every run)
# from a FAILURE (lane configured but the call failed — advisory raised so
# ops can see the degradation).
FALLBACK_MODEL_LANE_UNCONFIGURED = "model_lane_unconfigured"
FALLBACK_MODEL_CALL_FAILED = "model_call_failed"
FALLBACK_EMPTY_INPUT = "empty_input"


@dataclass(slots=True)
class DimensionClarity:
    """Clarity assessment for a single intake dimension."""
    dimension: str
    is_clear: bool
    probability: float
    notes: str = ""


@dataclass(slots=True)
class AmbiguityReport:
    """Complete semantic ambiguity and completeness evaluation."""
    action: str  # "PROCEED" | "ASK_FOLLOWUP" | "ESCALATE"
    confidence: Optional[float]
    dimensions: Dict[str, DimensionClarity] = field(default_factory=dict)
    missing_dimensions: List[str] = field(default_factory=list)
    source: str = "jev"  # "jev" | "deterministic_fallback"
    reasoning: str = ""
    raw_decision: Dict[str, Any] = field(default_factory=dict)
    confidence_method: str = CONFIDENCE_METHOD_MODEL
    fallback_reason: Optional[str] = None

    @property
    def is_proceed(self) -> bool:
        return self.action == "PROCEED"

    @property
    def needs_followup(self) -> bool:
        return self.action == "ASK_FOLLOWUP"

    @property
    def is_escalate(self) -> bool:
        return self.action == "ESCALATE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "confidence_method": self.confidence_method,
            "fallback_reason": self.fallback_reason,
            "missing_dimensions": self.missing_dimensions,
            "source": self.source,
            "reasoning": self.reasoning,
            "dimensions": {
                k: {
                    "is_clear": v.is_clear,
                    "probability": v.probability,
                    "notes": v.notes,
                }
                for k, v in self.dimensions.items()
            },
        }


class IntakeAmbiguityClassifier:
    """Evaluates raw customer inquiries for semantic completeness."""

    # Sentinel: ``IntakeAmbiguityClassifier()`` constructs the default live
    # client (orchestration path); explicit ``client=None`` means "no client"
    # — deterministic fallback only (tests, offline determinism).
    _DEFAULT_CLIENT = object()

    def __init__(
        self,
        client: Optional[TypesafeJevClient] = _DEFAULT_CLIENT,
        model: str = "jev-1.13.0",
    ):
        self.client = TypesafeJevClient(model=model) if client is IntakeAmbiguityClassifier._DEFAULT_CLIENT else client

    def evaluate(self, text: str) -> AmbiguityReport:
        """Evaluate text completeness and return an AmbiguityReport."""
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return AmbiguityReport(
                action="ESCALATE",
                confidence=None,
                missing_dimensions=["destination", "dates", "party", "budget"],
                source="deterministic_fallback",
                reasoning="Empty input text",
                confidence_method=CONFIDENCE_METHOD_RULE,
                fallback_reason=FALLBACK_EMPTY_INPUT,
            )

        if self.client and self.client.is_available():
            try:
                return self._evaluate_with_jev(cleaned_text)
            except Exception as exc:
                logger.warning(
                    "IntakeAmbiguityClassifier: Jev call failed (%s); using deterministic fallback",
                    exc,
                )
                return self._evaluate_deterministic(
                    cleaned_text, fallback_reason=FALLBACK_MODEL_CALL_FAILED
                )

        return self._evaluate_deterministic(
            cleaned_text, fallback_reason=FALLBACK_MODEL_LANE_UNCONFIGURED
        )

    def _evaluate_with_jev(self, text: str) -> AmbiguityReport:
        schema = {
            "type": "object",
            "properties": {
                "destination_clarity": {
                    "type": "boolean",
                    "description": "Is a specific destination, country, or region clearly indicated?",
                },
                "dates_clarity": {
                    "type": "boolean",
                    "description": "Is a specific departure date, month, season, or duration clearly stated?",
                },
                "party_clarity": {
                    "type": "boolean",
                    "description": "Is party size or composition (adults, kids, solo, couple) clearly stated or implied?",
                },
                "budget_clarity": {
                    "type": "boolean",
                    "description": "Is a budget number, range, or clear budget tier explicitly provided?",
                },
                "intake_action": {
                    "type": "string",
                    "enum": ["PROCEED", "ASK_FOLLOWUP", "ESCALATE"],
                    "description": "Recommended action: PROCEED if destination and timing/party are clear enough to plan; ASK_FOLLOWUP if missing key travel details; ESCALATE if contradictory or non-travel.",
                },
            },
        }

        # Override prompt instructions for Jev
        prompt = (
            "Analyze this travel inquiry message for planning completeness:\n\n"
            f"'''{text}'''\n\n"
            'Action criteria:\n'
            '- "PROCEED": The destination and at least timing or party size are clear enough to produce an itinerary draft.\n'
            '- "ASK_FOLLOWUP": The inquiry is genuine travel intent but lacks essential details like destination, dates, or traveler count.\n'
            '- "ESCALATE": The message is nonsensical, contradictory, spam, or not a travel inquiry.\n'
        )

        decision = self.client.decide(prompt=prompt, schema=schema)

        # Parse noul results
        dest_clear = bool(decision.get("destination_clarity", False))
        dates_clear = bool(decision.get("dates_clarity", False))
        party_clear = bool(decision.get("party_clarity", False))
        budget_clear = bool(decision.get("budget_clarity", False))

        action = str(decision.get("intake_action", "ASK_FOLLOWUP"))
        confidence = decision.get("jev_confidence")

        dimensions = {
            "destination": DimensionClarity(
                dimension="destination",
                is_clear=dest_clear,
                probability=1.0 if dest_clear else 0.0,
            ),
            "dates": DimensionClarity(
                dimension="dates",
                is_clear=dates_clear,
                probability=1.0 if dates_clear else 0.0,
            ),
            "party": DimensionClarity(
                dimension="party",
                is_clear=party_clear,
                probability=1.0 if party_clear else 0.0,
            ),
            "budget": DimensionClarity(
                dimension="budget",
                is_clear=budget_clear,
                probability=1.0 if budget_clear else 0.0,
            ),
        }

        missing: List[str] = [dim for dim, cl in dimensions.items() if not cl.is_clear]

        # First-principles invariant check:
        # Destination is non-negotiable for PROCEED. If destination is missing, force ASK_FOLLOWUP.
        if action == "PROCEED" and not dest_clear:
            action = "ASK_FOLLOWUP"
            logger.info("Overrode PROCEED to ASK_FOLLOWUP: destination is not clear")

        # If confidence on PROCEED is too low, degrade to ASK_FOLLOWUP
        if action == "PROCEED" and confidence is not None and confidence < _AUTONOMOUS_PROCEED_CONFIDENCE:
            action = "ASK_FOLLOWUP"
            logger.info("Overrode PROCEED to ASK_FOLLOWUP: confidence %.2f < threshold", confidence)

        return AmbiguityReport(
            action=action,
            confidence=confidence,
            dimensions=dimensions,
            missing_dimensions=missing,
            source="jev",
            confidence_method=CONFIDENCE_METHOD_MODEL,
            reasoning=decision.get("reasoning", ""),
            raw_decision=decision,
        )

    def _evaluate_deterministic(
        self,
        text: str,
        fallback_reason: str = FALLBACK_MODEL_LANE_UNCONFIGURED,
    ) -> AmbiguityReport:
        """Deterministic rule-based fallback when Jev is offline.

        Reports ``confidence=None``: a keyword indicator scan has no
        calibration, and a fabricated constant would silently pass the
        downstream autonomy gate (FND-0352). ``fallback_reason`` records why
        the rule path served so routing can tell posture from failure.
        """
        lower = text.lower()

        # Destination heuristic: look for prepositions / keywords
        dest_indicators = [
            "to ", "in ", "visit", "trip to", "travel to", "explore",
            "paris", "bali", "tokyo", "dubai", "london", "kashmir", "rome", "singapore",
            "goa", "kerala", "switzerland", "thailand", "japan", "france", "italy",
        ]
        has_dest = any(ind in lower for ind in dest_indicators)

        # Dates heuristic: months, days, weeks, seasons
        date_indicators = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "days", "weeks", "nights", "summer", "winter", "tomorrow", "next week", "next month",
            "2026", "2027", "weekend", "departure",
        ]
        has_dates = any(ind in lower for ind in date_indicators) or bool(re.search(r"\b\d{1,2}[/-]\d{1,2}\b", lower))

        # Party heuristic: people, adults, kids, family, couple, solo
        party_indicators = [
            "family", "couple", "solo", "adult", "adults", "kids", "children",
            "pax", "people", "persons", "friends", "we are", "traveling with",
        ]
        has_party = any(ind in lower for ind in party_indicators) or bool(re.search(r"\b\d+\s*(people|pax|adults|travelers)\b", lower))

        # Budget heuristic: currency symbols, lakh, k, budget
        budget_indicators = ["$", "€", "₹", "eur", "usd", "inr", "gbp", "budget", "lakh", "cost", "cheap", "luxury"]
        has_budget = any(ind in lower for ind in budget_indicators) or bool(re.search(r"\b\d+k\b", lower))

        missing = []
        if not has_dest:
            missing.append("destination")
        if not has_dates:
            missing.append("dates")
        if not has_party:
            missing.append("party")
        if not has_budget:
            missing.append("budget")

        # Action resolution
        if not has_dest:
            action = "ASK_FOLLOWUP"
        elif has_dest and (has_dates or has_party):
            action = "PROCEED"
        else:
            action = "ASK_FOLLOWUP"

        dimensions = {
            "destination": DimensionClarity("destination", has_dest, 1.0 if has_dest else 0.0),
            "dates": DimensionClarity("dates", has_dates, 1.0 if has_dates else 0.0),
            "party": DimensionClarity("party", has_party, 1.0 if has_party else 0.0),
            "budget": DimensionClarity("budget", has_budget, 1.0 if has_budget else 0.0),
        }

        return AmbiguityReport(
            action=action,
            confidence=None,
            dimensions=dimensions,
            missing_dimensions=missing,
            source="deterministic_fallback",
            confidence_method=CONFIDENCE_METHOD_RULE,
            fallback_reason=fallback_reason,
            reasoning="[rule] deterministic indicator scan",
        )
