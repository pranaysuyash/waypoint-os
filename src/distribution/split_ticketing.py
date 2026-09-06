"""
src/distribution/split_ticketing.py — Multi-Supplier Split-Ticketing Arbitrage Analyzer.

Analyzes through-fares vs separate ticket combinations (outbound Carrier A + return Carrier B)
to uncover price arbitrage while evaluating separate-ticket connection protection risks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(slots=True)
class FlightFareSegment:
    carrier_code: str
    flight_number: str
    origin_iata: str
    destination_iata: str
    fare_usd: float
    fare_basis_code: str
    ticket_type: str  # "outbound" | "return" | "through"


@dataclass(slots=True)
class SplitTicketingAnalysis:
    origin_iata: str
    destination_iata: str
    unified_roundtrip_fare_usd: float
    split_outbound_fare_usd: float
    split_return_fare_usd: float
    total_split_fare_usd: float
    savings_usd: float
    savings_percent: float
    is_arbitrage_profitable: bool
    self_transfer_risk_warning: bool
    recommended_booking_strategy: str
    segments: List[FlightFareSegment]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SplitTicketingAnalyzer:
    """Evaluates cross-airline fare combinations for split-ticketing savings."""

    @classmethod
    def evaluate_arbitrage(
        cls,
        origin_iata: str,
        destination_iata: str,
        unified_roundtrip_fare_usd: float,
        outbound_options: List[FlightFareSegment],
        return_options: List[FlightFareSegment],
    ) -> SplitTicketingAnalysis:
        if not outbound_options or not return_options:
            raise ValueError("Must provide at least one outbound and one return flight segment.")

        cheapest_out = min(outbound_options, key=lambda s: s.fare_usd)
        cheapest_ret = min(return_options, key=lambda s: s.fare_usd)

        total_split = cheapest_out.fare_usd + cheapest_ret.fare_usd
        savings = unified_roundtrip_fare_usd - total_split
        savings_pct = (savings / unified_roundtrip_fare_usd * 100.0) if unified_roundtrip_fare_usd > 0 else 0.0

        is_profitable = savings >= 50.0 and savings_pct >= 8.0
        is_cross_carrier = cheapest_out.carrier_code != cheapest_ret.carrier_code

        if is_profitable:
            strategy = f"Book split tickets: {cheapest_out.carrier_code} outbound + {cheapest_ret.carrier_code} return (Save ${savings:.2f})."
        else:
            strategy = "Book unified through-ticket for seamless baggage check and IATA rebooking protection."

        return SplitTicketingAnalysis(
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            unified_roundtrip_fare_usd=round(unified_roundtrip_fare_usd, 2),
            split_outbound_fare_usd=round(cheapest_out.fare_usd, 2),
            split_return_fare_usd=round(cheapest_ret.fare_usd, 2),
            total_split_fare_usd=round(total_split, 2),
            savings_usd=round(max(0.0, savings), 2),
            savings_percent=round(max(0.0, savings_pct), 2),
            is_arbitrage_profitable=is_profitable,
            self_transfer_risk_warning=is_cross_carrier,
            recommended_booking_strategy=strategy,
            segments=[cheapest_out, cheapest_ret],
        )
