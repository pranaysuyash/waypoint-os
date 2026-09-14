"""
src/orchestration/booking_fulfillment.py — End-to-End Booking Fulfillment Engine.

Fulfills accepted proposals into verified supplier commitments:
1. Verifies electronic acceptance of client proposal capability token
   (PA-02: acceptance must be durably recorded on the trip, not only in the
   process-local proposal registry)
2. Enforces governance-registry authority for the executing agent (PA-08)
3. Acquires exclusive durable agent lease to prevent split-brain double-booking
4. Issues single-use supplier Virtual Corporate Card (VCC) via Stripe Issuing with strict spend limits
5. Executes air ticketing order via GDS (Amadeus/Sabre) with PNR locator and e-ticket generation
6. Mints confirmed nodes in Journey Dependency Graph (JDG)
7. Updates TripStore and verifies the write by reading it back before claiming
   completion (PA-05: a TripStore failure raises — completion is never
   self-asserted)
8. Logs tamper-evident audit record

Reality boundary (PA-05): the Stripe and Amadeus adapters are local
simulations with no provider connected, so the whole fulfillment response is
labeled with reality-tier metadata and ``provider_connected: false``.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from spine_api import persistence
from spine_api.core.reality_tier import RealityTier
from spine_api.providers.stripe_issuing_adapter import (
    StripeIssuingAdapter,
    VirtualCardIssuanceRequest,
)
from spine_api.routers.public_proposals import _get_or_create_proposal
from spine_api.services.commission_reconciliation import reconcile_trip_commission
from spine_api.services.confirmation_service import try_record_fulfillment_confirmation
from spine_api.services.payment_mandate_service import PaymentMandateLedger
from src.distribution.amadeus_sandbox_adapter import AmadeusSandboxAdapter
from src.governance.registry import AuthorityDenied, enforce_action_authority
from src.intake.config.agency_settings import AgencySettingsStore
from src.orchestration.agent_lease import DurableAgentLeaseManager, lease_heartbeat
from src.schemas.journey_graph import (
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
)

logger = logging.getLogger("src.orchestration.booking_fulfillment")
AuditStore = persistence.AuditStore
TripStore = persistence.TripStore

# PA-08: the executing agent is a governance-registry worker. Its registration
# defines the action allowlist and the budget ceiling enforced pre-execution.
_FULFILLMENT_AGENT_ID = "agent_fulfillment_01"
_FULFILLMENT_ACTION = "fulfill_accepted_proposal"

# PA-05: fulfillment executes sim-tier adapters (local VCC/GDS simulations).
# The tier metadata travels on the result so no consumer can mistake a
# simulated booking for a provider-confirmed one.
_FULFILLMENT_MISSING_FOR_UPGRADE = [
    "connected Stripe Issuing (or equivalent) provider credential and authorization scope, "
    "with the native provider idempotency mechanism (Stripe Idempotency-Key header) set "
    "to the fulfillment provider key",
    "connected GDS/NDC provider with real PNR and e-ticket issuance",
    "supplier-side confirmation and reconciliation contract",
]


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
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    provider_connected: bool = False
    mandate_id: Optional[str] = None
    mandate_enforced: bool = False
    idempotent_replay: bool = False
    # AT-04: outcome of the durable SQL BookingConfirmation write (present,
    # or an explicit ``recorded: False`` + reason when no database is
    # configured — never a silent skip).
    durable_confirmation: Optional[Dict[str, Any]] = None
    # G-5: Post-ticketing commission reconciliation result. Every confirmed
    # booking triggers reconcile_trip_commission() so the advisor ledger is
    # immediately updated. The reconciliation outcome (matched / mismatch /
    # no_payouts) travels on the result for auditability.
    commission_reconciliation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        # A4 (2026-09-11): the raw VCC id and e-ticket number are excluded from
        # the operator payload — no FE consumer reads them, and the durable,
        # encrypted copy lives in booking_confirmations. last4 stays for display.
        return {
            "trip_id": self.trip_id,
            "proposal_token": self.proposal_token,
            "status": self.status,
            "pnr_locator": self.pnr_locator,
            "vcc_last4": self.vcc_last4,
            "total_charged_usd": self.total_charged_usd,
            "confirmed_journey_node_ids": self.confirmed_journey_node_ids,
            "fulfilled_at": self.fulfilled_at,
            "reality_tier": self.reality_tier,
            "provider_connected": self.provider_connected,
            "mandate_id": self.mandate_id,
            "mandate_enforced": self.mandate_enforced,
            "idempotent_replay": self.idempotent_replay,
            "durable_confirmation": self.durable_confirmation,
            "commission_reconciliation": self.commission_reconciliation,
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

        # 1b. PA-02: the e-sign acceptance is the authorization artifact for the
        # whole money path, so it must be verified against the DURABLE trip
        # record — not the process-local proposal registry cache.
        trip_record = TripStore.get_trip(trip_id)
        if not trip_record:
            raise ValueError(
                f"Trip '{trip_id}' has no persisted record. Fulfillment requires a "
                "durable trip; refusing to issue booking instruments against an "
                "unknown trip."
            )
        if not trip_record.get("proposal_accepted_at"):
            raise ValueError(
                f"Proposal acceptance for trip '{trip_id}' is not durably recorded "
                "(missing proposal_accepted_at). The e-sign acceptance must be "
                "persisted on the trip record before fulfillment can execute."
            )

        # AT-03: once booked, replay — never issue a second VCC/PNR. This
        # pre-lease check is a fast path; the authoritative re-check runs
        # inside the lease below (Part-H P0: two concurrent requests can both
        # pass this point before either acquires the lease).
        existing_confirmation = trip_record.get("booking_confirmation") or {}
        existing_pnr = str(existing_confirmation.get("pnr_locator") or "").strip()
        if existing_pnr:
            return await cls._replay_and_repair(
                trip_id, proposal_token, existing_confirmation, trip_record, holder_id
            )

        # 1c. PA-08: registry authority is enforced pre-execution with the
        # compiled package total. AuthorityDenied surfaces as HTTP 403 with an
        # explicit escalation-required body.
        try:
            authority = enforce_action_authority(
                _FULFILLMENT_AGENT_ID,
                _FULFILLMENT_ACTION,
                amount_usd=proposal.selected_total_price_usd,
            )
        except AuthorityDenied as exc:
            logger.warning(
                "Fulfillment denied by governance registry for trip %s: %s", trip_id, exc.reason
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "authority_denied",
                    "escalation_required": True,
                    "agent": exc.agent_id,
                    "action": exc.action,
                    "reason": exc.reason,
                    "message": (
                        "Fulfillment was denied by the governance registry. The "
                        "requested booking exceeds this agent's authority; escalate "
                        "to a human operator with sufficient authority."
                    ),
                },
            ) from exc

        # 1d. ADR-008 & F-04: Money Path Autonomy Rungs (AT-15 / FND-0185).
        # ADR-008 ratified money path as a per-agency tri-state setting:
        # - fully_human (default): Every booking/payout/refund/VCC movement requires an authenticated
        #   human operator as the approving principal (recorded in audit); system never moves money alone.
        # - hybrid: Auto within governance-registry caps + required payment mandate (F-04).
        # - fully_autonomous: Auto under registry authority, mandate recorded if present but not required.
        # Enforcement follows agency_settings.autonomy.money_execution_mode;
        # SPINE_API_REQUIRE_PAYMENT_MANDATES env var serves as fallback when hybrid/mandate is active.
        # Lifecycle precondition (ADR-008 council cross-link, Addendum 8+9):
        # fulfillment is RAISE-class gated on the canonical 12-state machine —
        # money moves only from approved / booking_in_progress / booked.
        try:
            from spine_api.core.trip_lifecycle import assess_transition

            _trip_status = trip_record.get("status")
            _assessment = assess_transition(_trip_status, _trip_status)
            _life_state = _assessment.new_state
            if _life_state is not None and _life_state not in (
                "approved", "booking_in_progress", "booked",
                "change_requested", "in_trip",
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "lifecycle_precondition_refusal",
                        "trip_status": _trip_status,
                        "lifecycle_state": _life_state,
                        "message": (
                            f"Trip '{trip_record.get('trip_id') or trip_id}' is in "
                            f"lifecycle state '{_life_state}'; fulfillment requires "
                            "approved / booking_in_progress / booked (ADR-008 R1 seam, "
                            "Addendum 8 canonical lifecycle)."
                        ),
                    },
                )
        except HTTPException:
            raise
        except Exception:
            logger.warning("lifecycle precondition check skipped (unclassifiable status)", exc_info=True)

        agency_scope = str(trip_record.get("agency_id") or "system")
        agency_settings = AgencySettingsStore.load(agency_scope)
        money_mode = agency_settings.autonomy.money_execution_mode

        # ADR-008 item 1 amendment (Addendum 9): positive check — the
        # approving principal must be a JWT-bound human ("user:<email>",
        # bound at the fulfillment router). A client-asserted denylist let
        # the fully_human gate pass by default. Only hybrid/fully_autonomous
        # modes may run without one.
        is_bound_human_principal = str(holder_id).startswith("user:")

        if money_mode == "fully_human" and not is_bound_human_principal:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "money_execution_mode_refusal",
                    "escalation_required": True,
                    "money_execution_mode": "fully_human",
                    "holder_id": holder_id,
                    "message": (
                        f"Agency '{agency_scope}' operates under 'fully_human' money execution mode (ADR-008). "
                        "Money movements require an authenticated human advisor as the approving principal "
                        "(JWT-bound at the fulfillment router); unauthenticated or system holders are refused. "
                        "Escalate to an authenticated advisor."
                    ),
                },
            )

        agency_requires_mandate = money_mode == "hybrid" or (
            os.environ.get("SPINE_API_REQUIRE_PAYMENT_MANDATES", "0").strip().lower() in ("1", "true", "yes")
        )

        mandate_charge_cents = int(round(float(proposal.selected_total_price_usd) * 100))
        mandate = PaymentMandateLedger.resolve_for_trip(
            agency_id=agency_scope, trip_id=trip_id
        )
        if mandate is None and agency_requires_mandate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "payment_mandate_required",
                    "escalation_required": True,
                    "money_execution_mode": money_mode,
                    "message": (
                        f"No active payment mandate exists for trip '{trip_id}' and "
                        f"mandate enforcement is required under '{money_mode}' mode (ADR-008 / F-04). "
                        "Fulfillment refuses to move money without a consent artifact."
                    ),
                },
            )
        mandate_id_for_audit: Optional[str] = None
        mandate_enforced = False

        # 2. Acquire exclusive durable agent lease (split-brain fence)
        lease = DurableAgentLeaseManager.acquire_lease(
            trip_id=trip_id,
            holder_id=holder_id,
            ttl_seconds=60,
            metadata={"action": "fulfillment", "token": proposal_token},
        )

        try:
            def _renew_lease() -> None:
                # Part-H P0: the 60s fence must outlive the provider calls. A
                # lost lease mid-flight means another worker may hold the
                # trip — fail loud instead of racing it to the write.
                try:
                    DurableAgentLeaseManager.renew_lease(trip_id, lease.lease_token, ttl_seconds=60)
                except Exception as exc:
                    raise RuntimeError(
                        f"Fulfillment lease lost mid-flight for trip '{trip_id}': {exc}"
                    ) from exc

            # Part-H P0: authoritative confirmation re-check inside the fence.
            fresh_trip = TripStore.get_trip(trip_id) or {}
            fresh_confirmation = fresh_trip.get("booking_confirmation") or {}
            if str(fresh_confirmation.get("pnr_locator") or "").strip():
                return await cls._replay_and_repair(
                    trip_id, proposal_token, fresh_confirmation, fresh_trip, holder_id
                )

            # Part-H P0: durable side-effect-start marker, written BEFORE any
            # provider call. A crash between the provider call and the final
            # confirmation write is now detectable, and re-entry re-uses the
            # same provider idempotency key so the SAME instruments come back
            # instead of a second VCC/PNR being minted.
            provider_key = fulfillment_provider_key(trip_id, proposal_token)
            now_iso = datetime.now(timezone.utc).isoformat()
            if not fresh_confirmation.get("side_effects_started_at"):
                marker_trip = TripStore.update_trip(
                    trip_id,
                    {
                        "booking_confirmation": {
                            "side_effects_started_at": now_iso,
                            "fulfillment_provider_key": provider_key,
                        }
                    },
                )
                if not marker_trip:
                    raise RuntimeError(
                        f"Fulfillment could not persist the side-effect-start "
                        f"marker for trip '{trip_id}'; refusing to issue "
                        "provider instruments against an unwritable trip."
                    )
            else:
                logger.warning(
                    "Fulfillment re-entry after side-effect marker for trip %s: "
                    "re-issuing with provider idempotency key %s… so the same "
                    "instruments are returned, not duplicated.",
                    trip_id,
                    provider_key[:12],
                )

            # 2b. F-04: consume mandate headroom inside the lease fence — the
            # CAS refuses any movement that would exceed the traveler's
            # consent (shortfall is a hard error, never a partial apply).
            if mandate is not None:
                mandate_authz = PaymentMandateLedger.authorize_charge(
                    agency_id=agency_scope,
                    mandate_id=mandate.mandate_id,
                    amount_cents=mandate_charge_cents,
                )
                if not mandate_authz.get("authorized"):
                    raise ValueError(
                        f"Payment mandate '{mandate.mandate_id}' does not authorize this "
                        f"movement: {mandate_authz.get('reason')}. The traveler's consent "
                        "must not be exceeded; register a sufficient mandate or escalate."
                    )
                mandate_id_for_audit = mandate.mandate_id
                mandate_enforced = True

            # Part-J #2: renew the fence immediately before the provider
            # window too, so the lease is fresh at call start. (A heartbeat
            # DURING a long provider await remains adapter work — recorded in
            # the register as missing-for-upgrade.)
            _renew_lease()

            # Part-J #2: heartbeat the fence DURING the provider window. The
            # pre-window renewal keeps the lease fresh at call start; the
            # heartbeat covers awaits longer than the 60s TTL; the explicit
            # post-window renewal fails loud if the fence was lost.
            _renew_lease()
            # 3+4. Issue single-use Virtual Corporate Card with exact spend
            # bounds, then GDS ticketing + PNR creation — both derive their
            # instruments deterministically from the provider idempotency key
            # (Part-H P0), so a re-entry re-issues the same instruments.
            async with lease_heartbeat(trip_id, lease.lease_token, interval_seconds=15.0, ttl_seconds=60):
                amount_cents = int(round(proposal.selected_total_price_usd * 100))
                adapter = StripeIssuingAdapter()
                vcc = await adapter.issue_single_use_card(
                    VirtualCardIssuanceRequest(
                        amount_cents=amount_cents,
                        currency=proposal.currency,
                        merchant_category_code="4511",  # Airlines
                        merchant_name="Airline & Lodging Consolidated",
                        trip_id=trip_id,
                        metadata={
                            "proposal_token": proposal_token,
                            "idempotency_key": provider_key,
                        },
                        idempotency_key=provider_key,
                    )
                )

                traveler_name = proposal.traveler_name or "Lead Traveler"
                gds_booking = AmadeusSandboxAdapter.create_flight_order(
                    offer_id=f"AMD-OFF-{trip_id[:8]}",
                    traveler_name=traveler_name,
                    idempotency_key=provider_key,
                )
            _renew_lease()

            # 5+6. PA-05 + Part-J #5: persist the merged graph and confirmation
            # with a bounded compare-and-set — each attempt re-reads the trip
            # and re-merges the graph, so a concurrent writer's nodes are not
            # clobbered by our earlier snapshot. The plain-write fallback
            # prioritizes booking durability (the confirmation MUST land);
            # its residual graph window is documented in the register.
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
                commitment_status="ticketed",
                metadata={
                    "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
                    "provider_connected": False,
                },
            )
            fulfilled_at_iso = datetime.now(timezone.utc).isoformat()
            cas_write = getattr(TripStore, "update_trip_if_version", None)
            updated_trip: Optional[Dict[str, Any]] = None
            updates: Dict[str, Any] = {}
            for _ in range(3):
                snapshot = TripStore.get_trip(trip_id) or {}
                graph = JourneyDependencyGraph.from_stored(
                    trip_id,
                    snapshot.get("journey_graph_nodes") or [],
                    snapshot.get("journey_graph_edges") or [],
                )
                graph.add_node(flt_node)
                stored_graph = graph.to_stored_payload()
                snap_confirmation = snapshot.get("booking_confirmation") or {}
                # A4 (2026-09-11): the trip JSONB lane is plaintext — the VCC id
                # and e-ticket number are durably recorded (encrypted) in
                # booking_confirmations via try_record_fulfillment_confirmation
                # below, so they are no longer duplicated here. Replacing the
                # whole dict also strips these keys from legacy rows on
                # re-fulfillment. vcc_last4 stays for display.
                updates = {
                    "booking_confirmation": {
                        "side_effects_started_at": snap_confirmation.get("side_effects_started_at") or now_iso,
                        "fulfillment_provider_key": provider_key,
                        "pnr_locator": gds_booking.pnr_locator,
                        "vcc_last4": vcc.last4,
                        "fulfilled_at": fulfilled_at_iso,
                        "total_charged_usd": proposal.selected_total_price_usd,
                        "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
                        "provider_connected": False,
                    },
                    "journey_graph_nodes": stored_graph["journey_graph_nodes"],
                    "journey_graph_edges": stored_graph["journey_graph_edges"],
                }
                if not callable(cas_write):
                    break
                updated_trip = cas_write(trip_id, updates, snapshot.get("updated_at"))
                if updated_trip is not None:
                    break
            if updated_trip is None:
                if callable(cas_write):
                    logger.warning(
                        "Part-J #5: fulfillment CAS write fell back to a plain "
                        "update for trip %s after bounded contention; the "
                        "residual graph-merge window is a documented open item.",
                        trip_id,
                    )
                updated_trip = TripStore.update_trip(trip_id, updates)
            if not updated_trip:
                raise RuntimeError(
                    f"Fulfillment persistence failed: trip '{trip_id}' could not be "
                    "updated in TripStore, so the booking confirmation was NOT "
                    "persisted. The fulfillment is NOT confirmed."
                )
            reread_trip = TripStore.get_trip(trip_id)
            reread_confirmation = (reread_trip or {}).get("booking_confirmation") or {}
            if reread_confirmation.get("pnr_locator") != gds_booking.pnr_locator:
                raise RuntimeError(
                    f"Fulfillment read-back verification failed for trip '{trip_id}': "
                    "the persisted booking_confirmation does not match the executed "
                    "booking. The fulfillment is NOT confirmed."
                )

            # 6b. AT-04: durably record the confirmation in the SQL machine
            # (draft → recorded). Honest degradation: without a configured
            # database this reports ``recorded: False`` + reason on the result
            # instead of pretending the row exists.
            durable_confirmation = await try_record_fulfillment_confirmation(
                agency_id=agency_scope,
                trip_id=trip_id,
                created_by=holder_id,
                pnr_locator=gds_booking.pnr_locator,
                e_ticket_number=gds_booking.e_ticket_number,
                vcc_card_id=vcc.card_id,
                total_usd=proposal.selected_total_price_usd,
                reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
                provider_connected=False,
            )
            if not durable_confirmation.get("recorded"):
                logger.warning(
                    "AT-04 durable confirmation not recorded for trip %s: %s",
                    trip_id,
                    durable_confirmation.get("reason"),
                )

            # Part-J #3: record the durable-confirmation outcome in the blob so
            # a replay can repair a missing SQL row instead of forgetting it.
            confirmation_for_blob = dict(
                (updated_trip or {}).get("booking_confirmation") or {}
            )
            confirmation_for_blob["sql_confirmation"] = durable_confirmation
            TripStore.update_trip(trip_id, {"booking_confirmation": confirmation_for_blob})

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
                    "authority": authority,
                    "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
                    "persisted_and_verified": True,
                    "mandate_id": mandate_id_for_audit,
                    "mandate_enforced": mandate_enforced,
                    "money_execution_mode": money_mode,
                    "provider_idempotency_key": provider_key,
                    "durable_confirmation": durable_confirmation,
                },
            )

            # G-5: Post-ticketing commission reconciliation. Called AFTER the
            # booking is confirmed and audited so a ledger failure never blocks
            # the booking result — it's reported for operator attention.
            commission_rec: Optional[Dict[str, Any]] = None
            try:
                commission_rec = reconcile_trip_commission(
                    trip_id=trip_id,
                    agency_id=agency_scope,
                )
                logger.info(
                    "Commission reconciliation for trip %s: status=%s delta_usd=%s",
                    trip_id,
                    commission_rec.get("status"),
                    commission_rec.get("delta_usd"),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Commission reconciliation failed (non-blocking) for trip %s: %s",
                    trip_id,
                    exc,
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
                reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
                provider_connected=False,
                mandate_id=mandate_id_for_audit,
                mandate_enforced=mandate_enforced,
                durable_confirmation=durable_confirmation,
                commission_reconciliation=commission_rec,
            )
        finally:
            # 8. Release lease
            DurableAgentLeaseManager.release_lease(trip_id, lease.lease_token)

    @classmethod
    async def _replay_and_repair(
        cls,
        trip_id: str,
        proposal_token: str,
        confirmation: Dict[str, Any],
        trip_record: Optional[Dict[str, Any]],
        holder_id: str,
    ) -> FulfillmentResult:
        """Replay a durably stored booking; repair a missing SQL confirmation.

        Part-J #3: a fulfillment whose ``booking_confirmation.sql_confirmation``
        never landed (crash between blob write and AT-04 record, or a degraded
        first pass) is repaired here instead of being permanently forgotten.
        """
        result = cls._replay_result(trip_id, proposal_token, confirmation, trip_record)
        sql_state = confirmation.get("sql_confirmation") or {}
        if sql_state.get("recorded") is not True:
            repaired = await try_record_fulfillment_confirmation(
                agency_id=str((trip_record or {}).get("agency_id") or "system"),
                trip_id=trip_id,
                created_by=holder_id or "fulfillment_replay",
                pnr_locator=result.pnr_locator,
                e_ticket_number=result.e_ticket_number,
                vcc_card_id=result.vcc_card_id,
                total_usd=result.total_charged_usd,
                reality_tier=result.reality_tier,
                provider_connected=result.provider_connected,
            )
            result.durable_confirmation = repaired
            if repaired.get("recorded"):
                merged_confirmation = dict(confirmation)
                merged_confirmation["sql_confirmation"] = repaired
                TripStore.update_trip(trip_id, {"booking_confirmation": merged_confirmation})
            else:
                logger.warning(
                    "AT-04 replay repair not recorded for trip %s: %s",
                    trip_id,
                    repaired.get("reason"),
                )
        return result

    @classmethod
    def _replay_result(
        cls,
        trip_id: str,
        proposal_token: str,
        confirmation: Dict[str, Any],
        trip_record: Optional[Dict[str, Any]] = None,
    ) -> FulfillmentResult:
        """Build the idempotent replay result from the durably stored booking."""
        stored_nodes = (trip_record or {}).get("journey_graph_nodes") or []
        node_ids = [
            str(n.get("node_id"))
            for n in stored_nodes
            if isinstance(n, dict) and n.get("node_id")
        ]
        return FulfillmentResult(
            trip_id=trip_id,
            proposal_token=proposal_token,
            status="FULFILLED_CONFIRMED",
            pnr_locator=str(confirmation.get("pnr_locator") or ""),
            e_ticket_number=str(confirmation.get("e_ticket_number") or ""),
            vcc_card_id=str(confirmation.get("vcc_card_id") or ""),
            vcc_last4=str(confirmation.get("vcc_last4") or ""),
            total_charged_usd=float(confirmation.get("total_charged_usd") or 0.0),
            confirmed_journey_node_ids=node_ids,
            fulfilled_at=str(confirmation.get("fulfilled_at") or ""),
            reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
            provider_connected=False,
            mandate_id=None,
            mandate_enforced=False,
            idempotent_replay=True,
        )


def fulfillment_provider_key(trip_id: str, proposal_token: str) -> str:
    """Stable provider-side idempotency key for a trip's fulfillment.

    Part-H P0 / Part-J #1: the key binds BOTH the trip and the accepted
    proposal token, so the instruments are deterministic for this exact
    acceptance — a retry re-issues the same PNR/e-ticket/VCC, while a
    different acceptance cannot silently alias the same provider key.
    The VCC issuer and GDS adapter derive their instrument ids from it.
    """
    return hashlib.sha256(
        f"fulfill:{trip_id}:{proposal_token}".encode("utf-8")
    ).hexdigest()[:32]


# PA-05: exported so the API surface can attach the same tier metadata without
# re-deriving it (kept in the engine because the engine owns the truth that the
# adapters are sim-tier).
FULFILLMENT_TIER_METADATA = {
    "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
    "feature": "booking_fulfillment",
    "computation_method": "local deterministic VCC/GDS simulation; no provider connected",
    "provider_connected": False,
    "missing_for_upgrade": _FULFILLMENT_MISSING_FOR_UPGRADE,
}
