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
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from spine_api.contract import TravelerAnswerSubmission, TravelerAskPublicView
from spine_api.persistence import AuditStore, TripStore
from spine_api.routers.public_proposals import (
    _verified_agency_for_token,
    verify_proposal_token,
)
from src.intake.fact_overrides import canonical_fact_name, record_fact_override

logger = logging.getLogger("spine_api.public_asks")

router = APIRouter(prefix="/api/public/asks", tags=["public-asks"])


def _apply_answers_to_facts(
    extracted: Dict[str, Any],
    answers: List[Dict[str, Any]],
    token: str,
    now: str,
) -> Dict[str, Any]:
    """Merge traveler answers into ``extracted["facts"]`` in the CANONICAL slot
    shape, and return the trip-column alias updates the reassessment overlay
    consumes (``build_reassessment_request_from_trip`` reads trip-level
    ``origin`` / ``dateWindow`` / ``budget`` / ... columns).

    FND-0328 (Sim #4): the previous implementation did
    ``facts = list(extracted.get("facts") or [])`` — when facts was the
    canonical DICT of slots, ``list(dict)`` produced the dict's KEYS, so the
    answer write corrupted the container (19 bare field-name strings) and no
    downstream reader (``blocking_unknowns``, decision ask-floor, quote
    readiness) could see the answered values. Facts are a dict of slots here;
    legacy corrupted lists are healed in place (dict items survive, bare-key
    strings are dropped — their values were lost by the old write and cannot
    be recovered from this row).
    """
    facts = extracted.get("facts")
    if not isinstance(facts, dict):
        healed: Dict[str, Any] = {}
        if isinstance(facts, list):
            for item in facts:
                if isinstance(item, dict) and (item.get("field") or item.get("field_name")):
                    key = str(item.get("field") or item.get("field_name"))
                    healed[key] = item  # value kept as-is; shape normalized below
        logger.warning(
            "traveler answers: healed non-dict extracted.facts (%s items) into slot dict",
            len(facts) if isinstance(facts, list) else "non-list",
        )
        facts = healed
        extracted["facts"] = facts

    alias_updates: Dict[str, Any] = {}
    for entry in answers:
        field_name = str(entry.get("field_name") or "").strip()
        answer = str(entry.get("answer") or "").strip()
        if not field_name or not answer:
            continue
        canonical = canonical_fact_name(field_name)
        source_ref = "ask_" + hashlib.sha256(f"{token}:{now}:{field_name}".encode()).hexdigest()[:24]
        slot = record_fact_override(
            facts, canonical, answer, source_ref=source_ref,
            mode="traveler_ask_link", updated_at=now,
        )
        slot["evidence_refs"][0]["metadata"]["original_question_field"] = field_name

        if field_name in ("destination", "destinations"):
            alias_updates["destination"] = answer
            extracted["destination"] = answer
        elif field_name in ("origin", "origin_city"):
            alias_updates["origin"] = answer
            extracted["origin"] = answer
        elif canonical == "party_size":
            if isinstance(slot["value"], int) and 0 < slot["value"] <= 1000:
                alias_updates["party"] = slot["value"]
        elif field_name in ("budget", "total_budget", "budget_range"):
            alias_updates["budget"] = answer
        elif field_name in ("dates", "date_start", "date_window", "dateWindow"):
            alias_updates["dateWindow"] = answer
        elif canonical == "trip_purpose":
            alias_updates["tripPurpose"] = answer
    return alias_updates


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
    alias_updates = _apply_answers_to_facts(extracted, body.answers, token, now)
    updates.update(alias_updates)
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

    # A1 work-intake classification: traveler answers are a demand-side work
    # item (intent=answer, authority=explicit_user). No text persisted — only
    # derived metadata. Best-effort.
    try:
        from spine_api.services.work_intake import classify_and_record

        classify_and_record(
            "ask_answers",
            agency_id=agency_id,
            text=None,
            trip_id=trip_id,
            actor="traveler_ask",
        )
    except Exception as work_item_err:
        logger.debug("Work-item classification skipped for asks %s: %s", trip_id, work_item_err)

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
