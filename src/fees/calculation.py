"""
fees.calculation — Risk-adjusted fee calculation engine.

Calculates service fees based on risk assessments from the suitability engine.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FeeBreakdown:
    """Detailed fee calculation breakdown."""

    base_fee: float
    risk_multiplier: float
    adjusted_fee: float
    risk_severity: str
    risk_factors: List[str]
    explanation: str


class FeeCalculator:
    """Calculates risk-adjusted fees for travel services."""

    # Risk multipliers based on highest severity risk
    RISK_MULTIPLIERS = {
        "low": 1.0,
        "medium": 1.2,
        "high": 1.4,
        "critical": 2.0
    }

    # Base fees per service type (configurable)
    BASE_FEES = {
        "flights": 500.0,  # USD per flight
        "accommodations": 300.0,  # USD per night per person
        "activities": 100.0,  # USD per activity per person
        "transfers": 50.0,  # USD per transfer per person
        "insurance": 20.0,  # USD per person
    }

    @staticmethod
    def calculate_adjusted_fee(
        service_type: str,
        quantity: float,
        risks: List[Dict],
        custom_base_fee: Optional[float] = None
    ) -> FeeBreakdown:
        """
        Calculate risk-adjusted fee for a service.

        Args:
            service_type: Type of service (flights, accommodations, etc.)
            quantity: Quantity (nights, persons, etc.)
            risks: List of risk dicts with 'severity' field
            custom_base_fee: Override default base fee

        Returns:
            FeeBreakdown with calculation details
        """
        # Get base fee
        base_fee_per_unit = custom_base_fee or FeeCalculator.BASE_FEES.get(service_type, 0.0)

        # Determine highest risk severity
        severities = [risk.get("severity", "low") for risk in risks]
        if severities:
            highest_severity = max(severities, key=lambda s: ["low", "medium", "high", "critical"].index(s))
        else:
            highest_severity = "low"

        # Get multiplier
        multiplier = FeeCalculator.RISK_MULTIPLIERS.get(highest_severity, 1.0)

        # Calculate fees
        base_total = base_fee_per_unit * quantity
        adjusted_total = base_total * multiplier

        # Risk factors
        risk_factors = [f"{risk.get('flag', 'unknown')} ({risk.get('severity', 'low')})" for risk in risks]

        # Explanation
        if service_type not in FeeCalculator.BASE_FEES and base_fee_per_unit == 0.0:
            explanation = f"Unknown service type '{service_type}'. No fee applied."
        elif not risks:
            explanation = "No significant risks detected. Base fee applies."
        else:
            explanation = f"Base fee: ₹{base_fee_per_unit:.0f} × {quantity} = ₹{base_total:.0f}. " \
                         f"Risk multiplier: {multiplier:.1f} ({highest_severity} severity). " \
                         f"Adjusted total: ₹{adjusted_total:.0f}."

        return FeeBreakdown(
            base_fee=base_total,
            risk_multiplier=multiplier,
            adjusted_fee=adjusted_total,
            risk_severity=highest_severity,
            risk_factors=risk_factors,
            explanation=explanation
        )


def _extract_slot_value(packet: Any, field_name: str, default: Any = None) -> Any:
    """Extract a slot value from either a dict-backed or object-backed packet."""
    facts = None
    if isinstance(packet, dict):
        facts = packet.get("facts", {})
    else:
        facts = getattr(packet, "facts", {})

    slot = None
    if isinstance(facts, dict):
        slot = facts.get(field_name)
    else:
        slot = getattr(facts, field_name, None)

    if isinstance(slot, dict):
        return slot.get("value", default)
    if hasattr(slot, "value"):
        return getattr(slot, "value")
    return default


def _normalize_risk_list(risks: Any) -> List[Dict[str, Any]]:
    """Normalize the risk_flags structure into a list of risk dicts."""
    normalized = []
    if risks is None:
        return []
    if isinstance(risks, dict):
        return [risks]
    if not isinstance(risks, list):
        return []

    for item in risks:
        if isinstance(item, dict):
            normalized.append(item)
        else:
            normalized.append({"flag": str(item), "severity": "low"})
    return normalized


def calculate_trip_fees(packet: Any, decision: Any) -> Dict[str, Any]:
    """
    Calculate fees for an entire trip based on risks.

    Args:
        packet: The canonical packet or packet dict
        decision: Decision result object or dict

    Returns:
        Dict with fee breakdowns and totals
    """
    if isinstance(decision, dict):
        raw_risks = decision.get("risk_flags", [])
    else:
        raw_risks = getattr(decision, "risk_flags", [])
    risks = _normalize_risk_list(raw_risks)

    participants = _extract_slot_value(packet, "party_size", default=1)
    if isinstance(participants, list):
        num_participants = len(participants)
    else:
        try:
            num_participants = int(participants)
        except (TypeError, ValueError):
            num_participants = 1
    if num_participants < 1:
        num_participants = 1

    duration_nights = _extract_slot_value(packet, "duration_nights", default=1)
    try:
        duration_nights = int(duration_nights)
    except (TypeError, ValueError):
        duration_nights = 1
    if duration_nights < 1:
        duration_nights = 1

    num_days = duration_nights + 1

    services = [
        ("flights", 2 * num_participants),
        ("accommodations", duration_nights * num_participants),
        ("activities", 2 * num_days * num_participants),
    ]

    breakdowns = {}
    total_base = 0.0
    total_adjusted = 0.0

    for service_type, quantity in services:
        breakdown = FeeCalculator.calculate_adjusted_fee(service_type, quantity, risks)
        breakdowns[service_type] = {
            "base_fee": breakdown.base_fee,
            "adjusted_fee": breakdown.adjusted_fee,
            "multiplier": breakdown.risk_multiplier,
            "severity": breakdown.risk_severity,
            "explanation": breakdown.explanation,
        }
        total_base += breakdown.base_fee
        total_adjusted += breakdown.adjusted_fee

    highest_severity = max(
        [risk.get("severity", "low") for risk in risks] or ["low"],
        key=lambda s: ["low", "medium", "high", "critical"].index(s),
    )

    return {
        "service_breakdowns": breakdowns,
        "total_base_fee": total_base,
        "total_adjusted_fee": total_adjusted,
        "fee_adjustment": total_adjusted - total_base,
        "risk_summary": f"Highest risk: {highest_severity}",
    }
