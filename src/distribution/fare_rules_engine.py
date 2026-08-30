"""
Fare Rules Engine (PER-950895, PER-0967).

Evaluates ATPCO Category 16 (Penalties & Cancellations) and Category 35
(Negotiated Fares & Commission Markups) to prevent debit memos (ADMs)
and guarantee fare compliance.
"""

from __future__ import annotations

from typing import Any, Dict


class FareRulesEngine:
    """Automated ATPCO Category 16/35 Fare Rules Evaluator."""

    @staticmethod
    def evaluate_penalties(
        fare_basis: str,
        is_departure_passed: bool = False,
        is_no_show: bool = False,
    ) -> Dict[str, Any]:
        """Evaluates Category 16 cancellation and change penalties."""
        code = fare_basis.upper()

        # Premium unrestricted fares (e.g. J, F, Y flex)
        if code.startswith(("FF", "YF", "JF", "WFULL")):
            return {
                "fare_basis": fare_basis,
                "is_refundable": True,
                "cancellation_fee": 0.0,
                "change_fee": 0.0,
                "penalty_code": "FULLY_REFUNDABLE_UNRESTRICTED",
                "rules_text": "CHANGES PERMITTED ANYTIME AT NO CHARGE. CANCELLATION PERMITTED BEFORE DEPARTURE WITH FULL REFUND.",
            }

        # Non-refundable restricted fares (e.g. Basic Economy / Promo)
        if "PROMO" in code or "BASIC" in code or code.endswith("NR"):
            return {
                "fare_basis": fare_basis,
                "is_refundable": False,
                "cancellation_fee": 0.0,
                "change_fee": 200.0 if not is_departure_passed else 400.0,
                "penalty_code": "STRICT_NON_REFUNDABLE",
                "rules_text": "TICKET IS NON-REFUNDABLE. CHANGES PERMITTED WITH USD 200 FEE PLUS FARE DIFFERENCE. NO-SHOW FORFEITS ENTIRE VALUE.",
            }

        # Standard commercial discounted business / economy
        cancellation = 250.0 if not is_no_show else 500.0
        change = 100.0 if not is_no_show else 300.0

        return {
            "fare_basis": fare_basis,
            "is_refundable": not is_departure_passed,
            "cancellation_fee": cancellation,
            "change_fee": change,
            "penalty_code": "STANDARD_RESTRICTED",
            "rules_text": f"CANCELLATION BEFORE DEPARTURE CHARGE USD {cancellation}. CHANGES USD {change} SUBJECT TO CLASS AVAILABILITY.",
        }

    @staticmethod
    def evaluate_cat35_negotiated_markup(
        net_fare: float,
        agency_markup_percent: float,
        contract_code: str = "CORP-WP-2026",
    ) -> Dict[str, Any]:
        """Evaluates Category 35 negotiated fare markup limits to prevent ADMs."""
        max_allowed_markup = 0.25  # 25% cap under standard IATA Cat 35 contract

        clamped_markup = min(agency_markup_percent, max_allowed_markup)
        selling_fare = net_fare * (1.0 + clamped_markup)
        agency_profit = selling_fare - net_fare

        return {
            "net_fare": round(net_fare, 2),
            "requested_markup_percent": round(agency_markup_percent * 100, 2),
            "effective_markup_percent": round(clamped_markup * 100, 2),
            "selling_fare": round(selling_fare, 2),
            "agency_commission_profit": round(agency_profit, 2),
            "contract_code": contract_code,
            "is_adm_risk_free": agency_markup_percent <= max_allowed_markup,
            "endorsement_box_text": f"NON-REF / NET FARE VALID ON {contract_code} ONLY",
        }
