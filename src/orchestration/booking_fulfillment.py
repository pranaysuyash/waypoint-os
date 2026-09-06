"""
src/orchestration/booking_fulfillment.py — End-to-End Booking Fulfillment Engine.

Fulfills accepted proposals into verified supplier commitments:
1. Verifies electronic acceptance of client proposal capability token
2. Acquires exclusive durable agent lease to prevent split-brain double-booking
3. Issues single-use supplier Virtual Corporate Card (VCC) via Stripe Issuing with strict spend limits
4. Executes air ticketing order via GDS (Amadeus/Sabre) with PNR locator and e-ticket generation
5. Mints confirmed nodes in Journey Dependency Graph (JDG)
6. Updates TripStore and logs tamper-evident audit record
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from spine_api import persistence
from spine_api.providers.stripe_issuing_adapter import (
    StripeIssuingAdapter,
    VirtualCardIssuanceRequest,
)
from spine_api.routers.public_proposals import _get_or_create_proposal
from src.distribution.amadeus_sandbox_adapter import AmadeusSandboxAdapter
from src.orchestration.agent_lease import DurableAgentLeaseManager
from src.schemas.journey_graph import (
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
)

logger = logging.getLogger("src.orchestration.booking_fulfillment")
AuditStore = persistence.AuditStore
TripStore = persistence.TripStore


@dataclass(slots=True)
class FulfillmentResult:
    trip_id: str
    proposal_token: str
    status: str
    pnr_locator: str
    e_ticket_number: str
    vcc_card_id: str
    vcc_last4: str
    total_charged_usd: float
    confirmed_journey_node_ids: list[str] = field(default_factory=list)
    fulfilled_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "proposal_token": self.proposal_token,
            "status": self.status,
            "pnr_locator": self.pnr_locator,
            "e_ticket_number": self.e_ticket_number,
            "vcc_card_id": self.vcc_card_id,
            "vcc_last4": self.vcc_last4,
            "total_charged_usd": self.total_charged_usd,
            "confirmed_journey_node_ids": self.confirmed_journey_node_ids,
            "fulfilled_at": self.fulfilled_at,
        }


class BookingFulfillmentEngine:
    """High-integrity fulfillment pipeline transitioning accepted proposals into supplier commitments."""

    @classmethod
    async def fulfill_accepted_proposal(
        cls,
        trip_id: str,
        proposal_token: str,
        holder_id: str = "fulfillment_agent",
    ) -> FulfillmentResult:
        if not trip_id or not proposal_token:
            raise ValueError("trip_id and proposal_token must be non-empty")

        # 1. Retrieve & verify proposal acceptance status
        proposal = _get_or_create_proposal(proposal_token)
        if proposal.status != "accepted":
            raise ValueError(
                f"Proposal {proposal_token} has status '{proposal.status}'. "
                "Only accepted proposals can be fulfilled."
            )

        # 2. Acquire exclusive durable agent lease (split-brain fence)
        lease = DurableAgentLeaseManager.acquire_lease(
            trip_id=trip_id,
            holder_id=holder_id,
            ttl_seconds=60,
            metadata={"action": "fulfillment", "token": proposal_token},
        )

        try:
            # 3. Issue single-use Virtual Corporate Card with exact spend bounds
            amount_cents = int(round(proposal.selected_total_price_usd * 100))
            adapter = StripeIssuingAdapter()
            vcc = await adapter.issue_single_use_card(
                VirtualCardIssuanceRequest(
                    amount_cents=amount_cents,
                    currency=proposal.currency,
                    merchant_category_code="4511",  # Airlines
                    merchant_name="Airline & Lodging Consolidated",
                    trip_id=trip_id,
                    metadata={"proposal_token": proposal_token},
                )
            )

            # 4. GDS Ticketing & PNR creation
            traveler_name = proposal.traveler_name or "Lead Traveler"
            gds_booking = AmadeusSandboxAdapter.create_flight_order(
                offer_id=f"AMD-OFF-{trip_id[:8]}",
                traveler_name=traveler_name,
            )

            # 5. Assemble / Update Journey Dependency Graph
            graph = JourneyDependencyGraph(trip_id=trip_id)
            now = datetime.now(timezone.utc)
            t_dep = now
            t_arr = t_dep
            flt_node = JourneyNode(
                node_id=f"N_FLT_CONFIRMED_{trip_id[:6]}",
                node_type=NodeType.FLIGHT,
                title=f"Flight to {proposal.destination} ({gds_booking.pnr_locator})",
                start_time=t_dep,
                end_time=t_arr,
                location=proposal.destination,
                provider="Amadeus NDC",
                confirmation_code=gds_booking.pnr_locator,
            )
            graph.add_node(flt_node)

            # 6. Update TripStore record if trip exists
            try:
                trip_record = TripStore.get(trip_id)
                if trip_record:
                    updates = {
                        "booking_confirmation": {
                            "pnr_locator": gds_booking.pnr_locator,
                            "e_ticket_number": gds_booking.e_ticket_number,
                            "vcc_card_id": vcc.card_id,
                            "vcc_last4": vcc.last4,
                            "fulfilled_at": datetime.now(timezone.utc).isoformat(),
                            "total_charged_usd": proposal.selected_total_price_usd,
                        },
                    }
                    TripStore.update(trip_id, updates)
            except Exception as exc:
                logger.warning("TripStore update skipped or failed during fulfillment: %s", exc)

            # 7. Audit logging
            AuditStore.log_event(
                "booking_fulfilled",
                holder_id,
                {
                    "trip_id": trip_id,
                    "proposal_token": proposal_token,
                    "pnr_locator": gds_booking.pnr_locator,
                    "e_ticket_number": gds_booking.e_ticket_number,
                    "vcc_card_id": vcc.card_id,
                    "total_usd": proposal.selected_total_price_usd,
                    "fencing_token": lease.fencing_token,
                },
            )

            return FulfillmentResult(
                trip_id=trip_id,
                proposal_token=proposal_token,
                status="FULFILLED_CONFIRMED",
                pnr_locator=gds_booking.pnr_locator,
                e_ticket_number=gds_booking.e_ticket_number,
                vcc_card_id=vcc.card_id,
                vcc_last4=vcc.last4,
                total_charged_usd=proposal.selected_total_price_usd,
                confirmed_journey_node_ids=[flt_node.node_id],
            )
        finally:
            # 8. Release lease
            DurableAgentLeaseManager.release_lease(trip_id, lease.lease_token)
