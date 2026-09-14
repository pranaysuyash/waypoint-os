"""
End-to-End Autonomous Proposal Compiler (PER-INT-E2E).

Unifies epistemic extraction, constraint satisfaction, dual-stack GDS/NDC inventory,
dynamic margin take-rate optimization, and Journey Dependency Graph assembly
into a single-click verified proposal package.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from spine_api.core.reality_tier import RealityTier
from src.decision.constraint_engine import ConstraintEngine
from src.distribution.amadeus_sandbox_adapter import AmadeusSandboxAdapter
from src.intake.epistemic_arbiter import EpistemicArbiter, EpistemicStatus, ProvenanceSlot
from src.negotiation.margin_optimizer import MarginOptimizer
from src.schemas.journey_graph import DependencyRelation, JourneyDependencyGraph, JourneyNode, NodeType

logger = logging.getLogger("src.orchestration.proposal_compiler")


@dataclass(slots=True)
class CompiledProposalPackage:
    """End-to-end compiled proposal artifact.

    PA-25 honesty notes: the compiled inventory is SYNTHETIC (sandbox air
    offers plus fabricated lodging/transfer providers), so the package carries
    reality-tier metadata and share-token minting is blocked by default —
    a signed credential is never minted for fabricated inventory unless the
    caller explicitly opts in via ``allow_share_for_simulated``.
    """

    proposal_id: str
    trip_id: str
    title: str
    destination: str
    traveler_count: int
    net_supplier_cost_usd: float
    optimized_take_rate_pct: float
    gross_customer_price_usd: float
    gross_margin_usd: float
    is_feasibility_passed: bool
    journey_graph_node_count: int
    provenance_assertion_count: int
    proposal_share_url: Optional[str] = None
    share_token: Optional[str] = None
    share_blocked_reason: Optional[str] = None
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    provider_connected: bool = False
    # FND-0268 council amendment (Addendum 9 → margin-basis decision):
    # per-component cost basis (preview|live|modeled_synthetic) and the
    # derived package margin_basis (min of components: live > mixed >
    # preview). Binding contract: NO floor comparison may run against any
    # margin whose cost basis is not live (PA-25 precedent — block, don't
    # label); margin is excluded from composite scores while non-live.
    breakdown_items: List[Dict[str, Any]] = field(default_factory=list)
    margin_basis: str = "preview"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "trip_id": self.trip_id,
            "title": self.title,
            "destination": self.destination,
            "traveler_count": self.traveler_count,
            "net_supplier_cost_usd": self.net_supplier_cost_usd,
            "optimized_take_rate_pct": self.optimized_take_rate_pct,
            "gross_customer_price_usd": self.gross_customer_price_usd,
            "gross_margin_usd": self.gross_margin_usd,
            "is_feasibility_passed": self.is_feasibility_passed,
            "journey_graph_node_count": self.journey_graph_node_count,
            "provenance_assertion_count": self.provenance_assertion_count,
            "proposal_share_url": self.proposal_share_url,
            "share_token": self.share_token,
            "share_blocked_reason": self.share_blocked_reason,
            "reality_tier": self.reality_tier,
            "provider_connected": self.provider_connected,
            "margin_basis": self.margin_basis,
            "breakdown_items": self.breakdown_items,
            "created_at": self.created_at,
        }


class AutonomousProposalCompiler:
    """High-speed pipeline compiling raw intake into verified, margin-optimized proposals."""

    @classmethod
    def compile_from_intake(
        cls,
        trip_id: str,
        raw_intake_text: str,
        destination: str,
        departure_date: date,
        return_date: date,
        traveler_count: int = 2,
        price_sensitivity: float = 0.2,  # Luxury / Low sensitivity
        peak_season: bool = True,
        allow_share_for_simulated: bool = False,
    ) -> CompiledProposalPackage:
        # 1. Epistemic extraction & constraint parsing
        epistemic_data = EpistemicArbiter.extract_implicit_and_negative_constraints(raw_intake_text)
        slots = [
            ProvenanceSlot("destination", destination, EpistemicStatus.FACT, 1.0, "TURN-1", f"destination: {destination}"),
            ProvenanceSlot("traveler_count", traveler_count, EpistemicStatus.FACT, 1.0, "TURN-1", f"travelers: {traveler_count}"),
        ]

        # 2. Dual-Stack GDS/NDC air shopping & inventory synthesis
        dest_code = "CDG" if destination.lower() in ("paris", "france") else "LHR"
        try:
            offers = AmadeusSandboxAdapter.search_flight_offers(
                origin_iata="JFK",
                destination_iata=dest_code,
                departure_date=departure_date.isoformat(),
            )
            selected_offer = offers[0] if offers else None
            flight_price_per_pax = selected_offer.total_price_usd if selected_offer else 1250.0
            flight_provider = f"{selected_offer.carrier_code} ({selected_offer.flight_number})" if selected_offer else "Delta Air Lines"
        except Exception:
            flight_price_per_pax = 1250.0
            flight_provider = "Delta Air Lines"

        flight_cost = round(flight_price_per_pax * traveler_count, 2)
        lodging_days = max(1, (return_date - departure_date).days)

        # G-3: Wholesale hotel rate shopping via Hotelbeds adapter.
        # Falls back to $450/night synthetic rate when credentials are absent.
        from src.distribution.hotelbeds_adapter import HotelbedsAdapter
        try:
            dest_city_code = dest_code  # Use same IATA city code
            htb_adapter = HotelbedsAdapter()
            htb_offers = htb_adapter.search_hotel_rates(
                destination_code=dest_city_code,
                check_in=departure_date.isoformat(),
                check_out=return_date.isoformat(),
                adults=traveler_count,
            )
            if htb_offers:
                best_hotel = htb_offers[0]
                hotel_cost = round(best_hotel.retail_rate_usd, 2)
                hotel_provider = best_hotel.hotel_name
                hotel_rate_key = best_hotel.rate_key
            else:
                hotel_cost = round(450.0 * lodging_days, 2)
                hotel_provider = "Bedsonline Partner Hotel"
                hotel_rate_key = ""
        except Exception:
            hotel_cost = round(450.0 * lodging_days, 2)
            hotel_provider = "Bedsonline Partner Hotel"
            hotel_rate_key = ""

        transfer_cost = 180.0
        # Per-component cost basis (FND-0268 council amendment): flights carry
        # the Amadeus lane's tier; lodging follows the Hotelbeds adapter's
        # provider_connected state (live net rates vs preview fallback);
        # transfers are a modeled constant. Package basis = weakest component
        # (live > mixed > preview) — one live component inside synthetic ones
        # must not make the package look live.
        flight_basis = "preview" if flight_price_per_pax == 1250.0 else "live"
        hotel_basis = "live" if htb_offers and getattr(htb_adapter, "provider_connected", False) else "preview"
        component_bases = {flight_basis, hotel_basis, "modeled_synthetic"}
        if component_bases == {"live"}:
            margin_basis = "live"
        elif "live" in component_bases:
            margin_basis = "mixed"
        else:
            margin_basis = "preview"
        net_supplier_cost = round(flight_cost + hotel_cost + transfer_cost, 2)

        # 3. Dynamic Margin Take-Rate Optimization
        lead_time_days = max(1, (departure_date - date.today()).days)
        margin_res = MarginOptimizer.calculate_optimal_margin(
            net_supplier_cost=net_supplier_cost,
            lead_time_days=lead_time_days,
            customer_price_sensitivity=price_sensitivity,
            is_peak_season=peak_season,
        )
        gross_customer_price = round(margin_res.optimized_selling_price, 2)
        gross_margin = round(margin_res.gross_profit_usd, 2)
        take_rate = round(margin_res.effective_margin_percent * 100.0, 1)

        # 4. Assemble Journey Dependency Graph
        graph = JourneyDependencyGraph(trip_id=trip_id)
        t_dep = datetime.combine(departure_date, datetime.min.time()).replace(hour=8, minute=30)
        t_arr = t_dep + timedelta(hours=7, minutes=30)
        t_trans = t_arr + timedelta(minutes=45)
        t_hotel = t_trans + timedelta(hours=1)

        f_node = JourneyNode("N_FLT_01", NodeType.FLIGHT, f"Flight to {destination}", t_dep, t_arr, "NYC", provider=flight_provider)
        t_node = JourneyNode("N_TRF_01", NodeType.TRANSFER, "Chauffeur Airport Transfer", t_trans, t_trans + timedelta(hours=1), destination, provider="Blacklane")
        h_node = JourneyNode(
            "N_HTL_01",
            NodeType.HOTEL_CHECKIN,
            f"Hotel Stay ({destination}) — {hotel_provider}",
            t_hotel,
            t_hotel + timedelta(days=max(1, (return_date - departure_date).days)),
            destination,
            provider=hotel_provider,
            metadata={"rate_key": hotel_rate_key} if hotel_rate_key else {},
        )

        graph.add_node(f_node)
        graph.add_node(t_node)
        graph.add_node(h_node)
        graph.add_edge("N_FLT_01", "N_TRF_01", DependencyRelation.TRANSFER_CONNECTS, min_connection_minutes=45)
        graph.add_edge("N_TRF_01", "N_HTL_01", DependencyRelation.HOTEL_NIGHT_FOR, min_connection_minutes=30)
        for node in graph.nodes.values():
            node.commitment_status = "quoted"
            node.metadata = {
                **node.metadata,
                "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
                "provider_connected": False,
            }

        # AT-01: persist the compiled DAG onto an existing trip; never overwrite
        # ticketed/booked nodes and never invent a trip record.
        try:
            from spine_api.persistence import TripStore

            existing = TripStore.get_trip(trip_id)
            if existing:
                prior = existing.get("journey_graph_nodes") or []
                locked = any(
                    isinstance(n, dict)
                    and str(n.get("commitment_status") or "") in {"booked", "ticketed"}
                    for n in prior
                )
                if not locked:
                    TripStore.update_trip(trip_id, graph.to_stored_payload())
        except Exception:
            logger.warning("compiler did not persist journey graph for trip %s", trip_id)

        # 5. Feasibility Constraint Evaluation
        feasibility_report = ConstraintEngine.evaluate_itinerary_graph(
            graph,
            party_size=traveler_count,
        )

        proposal_id = f"PROP-{trip_id[-6:].upper()}"

        # PA-25: share-token minting is gated on inventory reality. The
        # compiled package is synthetic (sandbox air offers, fabricated
        # lodging/transfer providers), so the default path does NOT mint a
        # signed credential for it. Callers that explicitly accept the
        # simulated nature may opt in via allow_share_for_simulated.
        share_token: Optional[str] = None
        share_url: Optional[str] = None
        share_blocked_reason: Optional[str] = "simulated_inventory"
        if allow_share_for_simulated:
            share_blocked_reason = None
            try:
                from spine_api.routers.public_proposals import generate_signed_proposal_token
                share_token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
            except Exception:
                share_token = proposal_id
            share_url = f"https://proposals.waypointos.com/view/{share_token}"

        return CompiledProposalPackage(
            proposal_id=proposal_id,
            trip_id=trip_id,
            title=f"Bespoke {destination.title()} Itinerary for {traveler_count} Travelers",
            destination=destination,
            traveler_count=traveler_count,
            net_supplier_cost_usd=net_supplier_cost,
            optimized_take_rate_pct=take_rate,
            gross_customer_price_usd=gross_customer_price,
            gross_margin_usd=gross_margin,
            is_feasibility_passed=feasibility_report.is_feasible,
            journey_graph_node_count=len(graph.nodes),
            provenance_assertion_count=len(slots) + len(epistemic_data.get("implicit_needs", [])),
            proposal_share_url=share_url,
            share_token=share_token,
            share_blocked_reason=share_blocked_reason,
            reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
            provider_connected=False,
            margin_basis=margin_basis,
            breakdown_items=[
                {"category": "Flights", "provider": flight_provider,
                 "amount_usd": flight_cost, "cost_basis": flight_basis},
                {"category": "Lodging", "provider": hotel_provider,
                 "amount_usd": hotel_cost, "cost_basis": hotel_basis},
                {"category": "Transfers", "provider": "Private Chauffeur",
                 "amount_usd": transfer_cost, "cost_basis": "modeled_synthetic"},
            ],
        )
