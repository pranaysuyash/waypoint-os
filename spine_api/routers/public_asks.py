"""
spine_api/routers/public_asks.py — Token-gated traveler ask/answer loop (FND-0301).

Closes the loop the decision engine opens: follow-up questions generated for
``ASK_FOLLOWUP``/``DEGRADE`` trips become answerable by the traveler through a
signed, expiring, revocable link (same credential machinery as public
proposals), and answers are written back onto the trip with
``authority=explicit_user`` so downstream decisions see them as traveler
statements, not system inference.

Trust boundaries:
- Every request verifies the signed token (TTL + revocation enforced per
  request, mirroring public_proposals).
- The GET projection is traveler-safe: questions + destination label only.
- Answers are appended (never overwrite) as timestamped records; the
  assumption/epistemic integration reads them on the next run.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from spine_api.contract import TravelerAnswerSubmission, TravelerAskPublicView
from spine_api.persistence import AuditStore, TripStore
from spine_api.routers.public_proposals import (
    _verified_agency_for_token,
    verify_proposal_token,
)

logger = logging.getLogger("spine_api.public_asks")

router = APIRouter(prefix="/api/public/asks", tags=["public-asks"])


def _verify(token: str) -> tuple[str, str]:
    """Shared token gate. Returns (trip_id, agency_id) or raises 401/410."""
    is_valid, reason, trip_id = verify_proposal_token(token, expected_purpose="ask")
    if not is_valid or not trip_id:
        unauthorized = "signature" in (reason or "").lower() or "malformed" in (reason or "").lower() or "purpose" in (reason or "").lower()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED if unauthorized else status.HTTP_410_GONE,
            detail=f"Ask link is not valid: {reason or 'unknown'}",
        )
    agency_id = _verified_agency_for_token(token)
    if not agency_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ask link is not bound to an agency")
    return trip_id, agency_id


def _open_questions(trip: dict) -> List[Dict[str, Any]]:
    """Extract the trip's open follow-up questions from the persisted decision."""
    decision = trip.get("decision") or {}
    questions = decision.get("follow_up_questions") or []
    extracted: List[Dict[str, Any]] = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        field_name = str(q.get("field_name") or "general")
        text = str(q.get("question") or q.get("text") or "").strip()
        if not text:
            try:
                from src.intake.decision import generate_question
                text = generate_question(field_name)
            except Exception:
                text = f"Can you provide details for {field_name}?"
        extracted.append(
            {
                "field_name": field_name,
                "question": text,
                "priority": str(q.get("priority") or "medium"),
            }
        )
    return extracted


def _existing_answers(trip: dict) -> List[Dict[str, Any]]:
    return trip.get("traveler_answers") or []


@router.get("/{token}", response_model=TravelerAskPublicView)
def get_traveler_ask(token: str) -> TravelerAskPublicView:
    """Traveler-safe view: the trip's open questions for a verified ask link."""
    trip_id, agency_id = _verify(token)
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Ask link resource not found")

    answered_fields = {
        a.get("field_name") for a in _existing_answers(trip) if isinstance(a, dict)
    }
    questions = [q for q in _open_questions(trip) if q["field_name"] not in answered_fields]
    destination = (trip.get("packet") or {}).get("destination") or trip.get("destination")

    return TravelerAskPublicView(
        token=token,
        trip_id=trip_id,
        destination=str(destination) if destination else None,
        status="open" if questions else "answered",
        questions=questions,
        asked_count=len(trip.get("traveler_asks") or []),
    )


@router.post("/{token}/answers")
def submit_traveler_answers(token: str, body: TravelerAnswerSubmission) -> dict:
    """Record traveler answers (append-only, timestamped, explicit_user)."""
    trip_id, agency_id = _verify(token)
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Ask link resource not found")

    known_fields = {q["field_name"] for q in _open_questions(trip)}
    answers = _existing_answers(trip)
    now = datetime.now(timezone.utc).isoformat()
    recorded = 0
    for entry in body.answers:
        field_name = str(entry.get("field_name") or "").strip()
        answer = str(entry.get("answer") or "").strip()
        if not field_name or not answer:
            raise HTTPException(status_code=422, detail="Each answer needs field_name and answer")
        if field_name not in known_fields:
            # Answers only attach to questions the system actually asked —
            # the ask page cannot be used to inject arbitrary packet fields.
            raise HTTPException(status_code=422, detail=f"Unknown question for this trip: {field_name}")
        answers.append(
            {
                "field_name": field_name,
                "answer": answer[:2000],
                "question": str(entry.get("question") or "")[:500],
                "respondent_name": (body.respondent_name or "").strip()[:120] or None,
                "authority": "explicit_user",
                "channel": "ask_link",
                "token": token,
                "answered_at": now,
            }
        )
        recorded += 1

    if recorded == 0:
        raise HTTPException(status_code=422, detail="No answers submitted")

    updates: Dict[str, Any] = {
        "traveler_answers": answers,
    }
    extracted = dict(trip.get("extracted") or {})
    facts = list(extracted.get("facts") or [])

    import re
    for entry in body.answers:
        field_name = str(entry.get("field_name") or "").strip()
        answer = str(entry.get("answer") or "").strip()
        if not field_name or not answer:
            continue
        facts.append({
            "fact": f"{field_name}: {answer}",
            "field": field_name,
            "value": answer,
            "source": "traveler_ask",
            "authority": "explicit_user",
            "timestamp": now,
        })
        if field_name in ("destination", "destinations"):
            updates["destination"] = answer
            extracted["destination"] = answer
        elif field_name in ("origin", "origin_city"):
            updates["origin"] = answer
            extracted["origin"] = answer
        elif field_name in ("party_size", "party", "travelers", "traveler_count"):
            nums = re.findall(r"\d+", answer)
            if nums:
                try:
                    psize = int(nums[0])
                    updates["party"] = psize
                    extracted["party_size"] = psize
                except Exception:
                    pass
            updates["partyComposition"] = answer
            extracted["party"] = answer
        elif field_name in ("budget", "total_budget", "budget_range"):
            updates["budget"] = answer
            extracted["budget"] = answer
        elif field_name in ("dates", "date_start", "date_window", "dateWindow"):
            updates["dateWindow"] = answer
            extracted["dateWindow"] = answer

    extracted["facts"] = facts
    updates["extracted"] = extracted

    updated = TripStore.update_trip_for_agency(
        trip_id,
        agency_id,
        updates,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Ask link resource not found")

    AuditStore.log_event(
        event_type="traveler_answers_recorded",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "recorded": recorded,
            "fields": [a["field_name"] for a in answers[-recorded:]],
            "authority": "explicit_user",
        },
    )

    # If the execution pipeline is configured, trigger reassessment to resolve blockers immediately
    try:
        from spine_api.routers import trip_lifecycle
        from spine_api.services import trip_lifecycle_service
        if getattr(trip_lifecycle, "_execute_pipeline", None) is not None and updated:
            req_dict = trip_lifecycle_service.build_reassessment_request_from_trip(updated)
            trip_lifecycle_service.queue_trip_reassessment(
                updated,
                agency_id=agency_id,
                user_id="traveler_ask",
                request_dict=req_dict,
                trigger="traveler_answer",
                reason="Traveler submitted follow-up answers",
                execute_pipeline_fn=trip_lifecycle._execute_pipeline,
            )
    except Exception as exc:
        logger.warning("Auto-reassessment after traveler answers skipped or failed: %s", exc)

    return {"ok": True, "recorded": recorded, "answered_at": now}
