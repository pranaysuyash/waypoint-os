"""
Booking Fulfillment API Router (PER-FULFILL-OPS).

Provides endpoints to execute accepted proposals into supplier commitments:
VCC generation, GDS PNR creation, and Journey Dependency Graph node minting.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional
from spine_api.core.auth import get_current_user
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from spine_api.services.authority_approval_service import AuthorityApprovalLedger
from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus
from src.governance.registry import (
    AuthorityApprovalRequired,
    AuthorityDenied,
    ratified_authority_scope,
)
from src.orchestration.booking_fulfillment import (
    FULFILLMENT_TIER_METADATA,
    BookingFulfillmentEngine,
)

logger = logging.getLogger("spine_api.routers.fulfillment")

router = APIRouter(prefix="/api/v1/fulfillment", tags=["fulfillment"])

# PA-08: the fulfillment execution identity + action in the governance registry.
_FULFILLMENT_AGENT_ID = "agent_fulfillment_01"
_FULFILLMENT_ACTION = "fulfill_accepted_proposal"

# PA-40: in-flight reclaim window for a fulfill idempotency key. A fulfillment
# attempt that neither completes nor fails within this window is treated as
# stale and becomes retryable.
_FULFILLMENT_IDEMPOTENCY_TTL_SECONDS = 1800


def _bound_holder_id(user) -> str:
    """Approving principal derived from the authenticated JWT user — never
    from a client-asserted field (ADR-008 item 1 amendment)."""
    if user is None:
        return "unauthenticated"
    return f"user:{getattr(user, 'email', None) or getattr(user, 'id', 'unknown')}"



_HOW_TO_RATIFY = (
    "Request a dual-control approval via POST /api/v1/boundaries/authority-approvals "
    "(action, subject_type, subject_id, amount_usd), then collect two DISTINCT "
    "owner/admin approvals via POST /api/v1/boundaries/authority-approvals/{approval_id}/approve. "
    "Once ratified, retry this request."
)


class FulfillProposalRequest(BaseModel):
    trip_id: str = Field(..., description="Unique trip identifier")
    proposal_token: str = Field(..., description="Cryptographically signed proposal capability token")
    holder_id: Optional[str] = Field(
        None,
        description="DEPRECATED client assertion — ignored. The approving principal is "
        "bound to the authenticated JWT user server-side (ADR-008 item 1 amendment: "
        "a client-asserted denylist let the fully_human gate pass by default).",
    )


@router.post("/proposals/fulfill")
async def fulfill_proposal(
    payload: FulfillProposalRequest,
    user = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional client-supplied idempotency key (PA-40). "
        "Scopes to the trip's agency + trip id; a COMPLETED key replays the "
        "original fulfillment result, an in-flight key yields 409.",
    ),
) -> Dict[str, Any]:
    """Execute accepted client proposal into confirmed supplier bookings and VCC settlement.

    PA-05/PA-08 (2026-09-06): the fulfillment is a deterministic preview over
    simulated provider adapters — the tier metadata says so explicitly — and
    governance authority (PA-08) is enforced pre-execution: over-cap or
    unregistered actions return 403 with ``escalation_required``.

    PA-08 wave 2 (2026-09-07): an over-cap amount raises
    ``AuthorityApprovalRequired`` — when a ratified dual-control approval
    exists for (action, subject_id=trip_id) the fulfillment proceeds and the
    response metadata carries ``authority_approval_id``; otherwise the 403
    body includes ``approval_required`` plus the exact subject ids an operator
    needs to ratify.

    PA-40 (2026-09-07): with an ``Idempotency-Key`` header, the key
    ``(agency_id, trip_id, header)`` is resolved against the durable
    idempotency registry (src/agents/idempotency.py — the same CAS machinery
    wired at ``/run`` and ``routers/inbound.py``). A COMPLETED record replays
    the original fulfillment response with ``idempotent_replay: true``; a
    PENDING record yields 409; FAILED records are retryable. This sits on top
    of the engine's own once-booked replay guard (AT-03) — the guard makes a
    double-fulfill a no-op, the registry makes the retry observable.
    """
    # Tenancy anchor for the ratified-approval lookup: resolved via the
    # approval service (never an unscoped router-level trip read).
    agency_scope = AuthorityApprovalLedger.subject_agency_id("trip", payload.trip_id)

    # PA-40: acquire the idempotency key before any authority or engine work.
    registry: Optional[IdempotencyRegistry] = None
    idem_key: Optional[str] = None
    fencing_token: Optional[str] = None
    if idempotency_key:
        registry = IdempotencyRegistry.get_instance()
        idem_key = f"fulfill:{agency_scope or 'unscoped'}:{payload.trip_id}:{idempotency_key}"
        acquired, existing = registry.try_acquire(
            idem_key,
            trip_id=payload.trip_id,
            action_name=_FULFILLMENT_ACTION,
            # Include the body hash so one key cannot silently alias different
            # payloads into a replay.
            payload=payload.model_dump(exclude_none=True),
            ttl_seconds=_FULFILLMENT_IDEMPOTENCY_TTL_SECONDS,
        )
        fencing_token = getattr(existing, "fencing_token", None)
        if not acquired and existing is not None:
            if existing.status == IdempotencyStatus.COMPLETED:
                # Part-H P2: a key may only replay the SAME request. The
                # registry stores the request hash; a different body under a
                # known key is a client error, not a replay.
                incoming_hash = hashlib.sha256(
                    json.dumps(
                        payload.model_dump(exclude_none=True),
                        sort_keys=True,
                        default=str,
                    ).encode("utf-8")
                ).hexdigest()
                if existing.request_hash != incoming_hash:
                    # Strict compare (Part-J #10): a record without a matching
                    # stored hash (legacy/partial write) cannot prove request
                    # identity, so it must not replay.
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "reason": "idempotency_key_payload_mismatch",
                            "idempotency_key": idempotency_key,
                            "message": "This Idempotency-Key was used with a different request body.",
                        },
                    )
                replay = dict(existing.response_payload or {})
                replay["idempotent_replay"] = True
                return replay
            if existing is not None and existing.status == IdempotencyStatus.UNKNOWN:
                # TS-08: the previous attempt ended without a definitive
                # outcome. Retrying blindly could duplicate the booking —
                # refuse and require verification-driven resolution.
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "reason": "idempotency_outcome_unknown",
                        "idempotency_key": idempotency_key,
                        "outcome_unknown": True,
                        "message": (
                            "A previous attempt with this Idempotency-Key ended "
                            "without a definitive outcome (timeout or dropped "
                            "connection). Verify the booking state before "
                            "retrying; the key must be resolved, not replayed."
                        ),
                    },
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "reason": "fulfillment_already_in_flight_for_idempotency_key",
                    "idempotency_key": idempotency_key,
                },
            )

    def _mark_idempotency_failed(reason: str) -> None:
        # Terminal for this attempt; FAILED keys are retryable per the
        # registry's FAILED→retry semantics.
        if registry is not None and idem_key:
            registry.mark_failed(idem_key, reason, fencing_token=fencing_token)

    def _mark_idempotency_unknown(reason: str) -> None:
        # TS-08: the call ended WITHOUT a definitive outcome. UNKNOWN keys
        # are not retryable — they block re-execution until resolved via
        # verification (registry.resolve_unknown).
        if registry is not None and idem_key:
            registry.mark_unknown(idem_key, reason, fencing_token=fencing_token)

    authority_approval_id: Any = None
    try:
        try:
            result = await BookingFulfillmentEngine.fulfill_accepted_proposal(
                trip_id=payload.trip_id,
                proposal_token=payload.proposal_token,
                holder_id=_bound_holder_id(user),
            )
        except AuthorityApprovalRequired as exc:
            # Over-cap: a ratified dual-control approval for this exact trip
            # is sufficient authority. Re-entry is safe — the engine raises
            # at its pre-execution gate, before any side effect.
            ratified = (
                AuthorityApprovalLedger.get_approved(
                    agency_id=agency_scope,
                    action=_FULFILLMENT_ACTION,
                    subject_id=payload.trip_id,
                )
                if agency_scope
                else None
            )
            if ratified is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "authority_denied",
                        "escalation_required": True,
                        "approval_required": True,
                        "agent": exc.agent_id,
                        "action": exc.action,
                        "amount_usd": exc.amount_usd,
                        "subject": {"type": "trip", "id": payload.trip_id},
                        "reason": exc.reason,
                        "approval": {
                            "action": _FULFILLMENT_ACTION,
                            "subject_type": "trip",
                            "subject_id": payload.trip_id,
                            "amount_usd": exc.amount_usd,
                            "how_to_ratify": _HOW_TO_RATIFY,
                        },
                    },
                ) from exc
            authority_approval_id = ratified["approval_id"]
            with ratified_authority_scope(exc.agent_id, exc.action, float(exc.amount_usd or 0.0)):
                result = await BookingFulfillmentEngine.fulfill_accepted_proposal(
                    trip_id=payload.trip_id,
                    proposal_token=payload.proposal_token,
                    holder_id=_bound_holder_id(user),
                )
    except HTTPException:
        # Authority denials (unregistered agent / forbidden action) arrive as
        # 403 HTTPException from the engine's pre-execution gate — pass them
        # through untouched, but release the idempotency key so a retry after
        # ratification is not blocked by a stuck in-flight record.
        _mark_idempotency_failed("authority_denial_pre_execution")
        raise
    except AuthorityDenied as exc:
        _mark_idempotency_failed(f"authority_denied: {exc}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "authority_denied",
                "escalation_required": True,
                "reason": str(exc),
            },
        )
    except ValueError as exc:
        _mark_idempotency_failed(f"validation_error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        # TS-08 classification: a timeout or connection-class failure means
        # the provider may have processed the request — the outcome is
        # UNKNOWN, not FAILED, and the key must block blind retries.
        # Everything else is a definitive failure (retryable as FAILED).
        if isinstance(exc, (TimeoutError, OSError)):
            _mark_idempotency_unknown(f"outcome_unknown: {exc}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "error": "fulfillment_outcome_unknown",
                    "outcome_unknown": True,
                    "reason": str(exc),
                    "message": (
                        "The booking request ended without a definitive outcome. "
                        "Do not retry blindly — verify the booking state first; "
                        "this Idempotency-Key is locked until resolved."
                    ),
                },
            )
        _mark_idempotency_failed(f"fulfillment_error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fulfillment error: {exc}",
        )

    metadata: Dict[str, Any] = dict(FULFILLMENT_TIER_METADATA)
    if authority_approval_id is not None:
        metadata["authority_approval_id"] = authority_approval_id
    response = {
        "status": "success",
        "fulfillment": result.to_dict(),
        "metadata": metadata,
    }
    if registry is not None and idem_key:
        # PA-40: close the record so replays return this exact response.
        # A False return means this owner lost its fencing (reclaimed) — the
        # booking itself is still durable (engine-level guard), but the replay
        # record may not be, so log rather than claim silently.
        completed = registry.mark_completed(
            idem_key,
            response,
            fencing_token=fencing_token,
        )
        if not completed:
            logger.warning(
                "PA-40: mark_completed lost the fencing race for fulfill key %s; "
                "the booking is durable but this execution may not be replayable.",
                idem_key,
            )
    return response
