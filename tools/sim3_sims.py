"""
tools/sim3_sims.py — the four Sim #3 scenario implementations.

Called only through tools/sim3_runner.py (which owns auth, evidence, UI shots).
Every step is recorded into the client's evidence log; assertions are NOT
hard failures — a wrong result is evidence, recorded and graded later in
Docs/sims/SIM3_RESULTS_2026-10-05.md.
"""

from __future__ import annotations

from typing import Any

from tools.sim3_runner import VOICES, SimClient, shot

MAX_POLL_SECONDS = 300


def _find_trip(client: SimClient, run_resp: dict) -> str | None:
    """Pull trip_id from a run status payload, else search the trip list."""
    for key in ("trip_id", "tripId"):
        v = run_resp.get(key)
        if v:
            return v
    e = client.call("locate-trip", "GET", "/trips?limit=5")
    rows = e["response"].get("trips") or e["response"].get("items") or []
    for row in rows:
        return row.get("id") or row.get("trip_id")
    return None


def _packet_summary(trip: dict) -> dict:
    """Compact view of the business surfaces we grade."""
    extracted = trip.get("extracted") or {}
    facts = extracted.get("facts") or {}
    packet = trip.get("packet") or {}
    decision = trip.get("decision") or {}
    out: dict[str, Any] = {
        "trip_id": trip.get("id"),
        "status": trip.get("status"),
        "decision_state": trip.get("decision_state"),
        "packet_facts": {
            k: v for k, v in facts.items()
            if k in {
                "origin_city", "destination_candidates", "destinations",
                "budget_amount", "budget_min", "budget_max", "budget_scope",
                "budget_flexibility", "travel_dates", "duration_days",
                "purpose", "party_size", "party_composition", "constraints",
                "soft_preferences", "mobility_constraints", "meal_preferences",
                "occasion", "season_preference", "hard_constraints",
            }
        },
        "packet_fields": {
            k: packet.get(k) for k in (
                "origin_city", "destination", "destinations", "budget_min",
                "budget_max", "budget_scope", "travel_dates", "purpose",
                "party_size", "constraints", "meal_preferences",
                "mobility_constraints", "occasion",
            ) if packet.get(k) is not None
        },
        "open_questions": extracted.get("open_questions") or packet.get("open_questions"),
        "ambiguities": extracted.get("ambiguities") or packet.get("ambiguities"),
        "follow_ups": (trip.get("follow_ups") or decision.get("follow_ups")) if isinstance(decision, dict) else trip.get("follow_ups"),
        "traveler_asks": trip.get("traveler_asks"),
        "ghost_concierge": trip.get("ghost_concierge"),
        "passenger_claim": trip.get("passenger_claim"),
        "validation": trip.get("validation"),
        "history": (trip.get("decision_history") or trip.get("history") or [])[:6] if isinstance(trip.get("decision_history") or trip.get("history"), list) else None,
    }
    return out


def _submit_and_poll(client: SimClient, step: str, note: str, draft_id: str | None = None) -> tuple[dict, str | None]:
    """Canonical New-Inquiry door: create a draft, then run scoped to it."""
    if draft_id is None:
        d = client.call(f"{step}-draft", "POST", "/api/drafts",
                        json={"name": note[:60], "customer_message": note})
        draft_id = (d["response"] or {}).get("draft_id")
    acc = client.call(f"{step}-run", "POST", "/run",
                      json={"raw_note": note, "draft_id": draft_id})
    run_id = (acc["response"] or {}).get("run_id")
    status = client.poll_run(step, run_id, timeout_s=MAX_POLL_SECONDS) if run_id else {}
    if draft_id:
        status = dict(status or {})
        status["draft_id"] = draft_id
    return status, run_id


def run_sim_A(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, run_id = _submit_and_poll(client, "A1-run", VOICES["A1"])
    draft_id = (status or {}).get("draft_id")
    trip_id = (status or {}).get("trip_id") or _find_trip(client, status or {})
    trip = {}
    if trip_id:
        e = client.call("A1-trip", "GET", f"/trips/{trip_id}")
        trip = e["response"].get("trip") or e["response"]
    client.log.append({"step": "A1-packet", "draft_id": draft_id, "packet_summary": _packet_summary(trip)})

    # Note 2 — festival shift through the canonical append door:
    # PATCH the draft's customer_message (server.py:2738 writes it into
    # raw_input.submission.raw_note), then POST /run with the same draft_id
    # so the reprocess lands on the same trip (T2 supersession trail).
    if draft_id:
        merged_note = VOICES["A1"] + "\n\n" + VOICES["A2"]
        client.call("A2-patch-draft", "PATCH", f"/api/drafts/{draft_id}",
                    json={"customer_message": merged_note})
        re_status, _ = _submit_and_poll(client, "A2-run", merged_note, draft_id=draft_id)
        client.log.append({"step": "A2-run-status", "status": re_status})
        if trip_id:
            e2 = client.call("A2-trip", "GET", f"/trips/{trip_id}")
            trip2 = e2["response"].get("trip") or e2["response"]
            client.log.append({"step": "A2-packet", "packet_summary": _packet_summary(trip2)})
        if not skip_ui:
            shot("A", "workbench", "http://localhost:3005/workbench", "workbench_packet")


def run_sim_B(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    # Seed the durable profile (additive; dedicated sim email).
    seed = client.call("B-seed", "POST", "/api/v1/customers/remember", json={
        "name": "Ananya Rao",
        "email": "ananya.rao.sim3@waypointtest.dev",
        "dietary_requirements": "strict vegetarian",
        "room_preference": "traditional heritage stays (ryokan-equivalent), quiet",
        "seating_preference": "window",
        "source_trip_id": "sim3_seed_japan_2026",
    })
    client.log.append({"step": "B-seed-result", "status": seed["status"], "response": seed["response"]})

    # Durability + scope lookups (positive, then leakage negative control).
    client.call("B-lookup-pos", "GET", "/api/v1/customers/memory?email=ananya.rao.sim3@waypointtest.dev")
    client.call("B-lookup-neg", "GET", "/api/v1/customers/memory?email=wrong.customer@waypointtest.dev")

    status, run_id = _submit_and_poll(client, "B1-run", VOICES["B1"])
    trip_id = _find_trip(client, status or {})
    if trip_id:
        e = client.call("B1-trip", "GET", f"/trips/{trip_id}")
        trip = e["response"].get("trip") or e["response"]
        client.log.append({"step": "B1-packet", "packet_summary": _packet_summary(trip)})
        client.call("B1-hydrate", "POST", f"/api/v1/customers/hydrate-trip/{trip_id}", json={
            "trip_id": trip_id, "email": "ananya.rao.sim3@waypointtest.dev"})
        # Did the run path upsert her profile with the Vietnam facts?
        client.call("B1-lookup-after", "GET", "/api/v1/customers/memory?email=ananya.rao.sim3@waypointtest.dev")
    if not skip_ui:
        shot("B", "inbox", "http://localhost:3005/inbox", "inbox_feed")


def run_sim_C(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    # T6 door first (realistic inbound email): recorded live — in the default
    # dev env the privacy guard fail-closes on the plaintext customer_contact
    # (R-15 mode matrix), so the canonical /run door seeds the trip instead.
    client.call("C-inbound-probe", "POST", "/api/v1/inbound/parse", json={
        "channel": "email",
        "raw_text": VOICES["C1"],
        "customer_name": "Vikram Shetty",
        "customer_contact": "vikram.shetty.sim3@waypointtest.dev",
    })
    booking_note = (
        "booking confirmation for vikram shetty — bangkok return trip, booking "
        "reference SIM3-WP7K2M, 2 passengers (vikram shetty, lata shetty), "
        "outbound TG318 bkk-bom. hotel: riverside bangkok, 4 nights. traveler "
        "contact on file: vikram dot shetty dot sim3 at waypointtest dot dev"
    )
    status, _ = _submit_and_poll(client, "C-seed", booking_note)
    trip_id = (status or {}).get("trip_id")
    if not trip_id:
        client.log.append({"step": "C-abort", "reason": "no trip_id from seed run"})
        return

    # Operator-reported flight facts via the T11b door. booking_reference is
    # deliberately absent — TripPatchRequest has no such field (observation
    # recorded in the results doc).
    fsu = [{
        "flight_number": "TG318",
        "status": "CANCELLED",
        "delay_hours": 19,
        "reported_at": "2026-10-04T09:00:00Z",
        "source": "traveler_message",
    }]
    client.call("C-flight-facts", "PATCH", f"/trips/{trip_id}", json={
        "flight_status_updates": fsu,
    })
    client.call("C-trip-after-ghost", "GET", f"/trips/{trip_id}")

    # Statutory evaluation + claim letter.
    client.call("C-evaluate", "POST", "/api/v1/passenger-rights/evaluate", json={
        "trip_id": trip_id,
        "flight_number": "TG318",
        "disruption_type": "CANCELLED",
        "delay_hours": 19,
        "distance_km": 2400,
        "passengers_count": 2,
        "airline_name": "Thai Airways",
    })
    gen = client.call("C-generate-claim", "POST", f"/api/v1/passenger-rights/{trip_id}/generate-claim", json={
        "trip_id": trip_id,
        "passenger_names": ["Vikram Shetty", "Lata Shetty"],
        "booking_reference": "SIM3-WP7K2M",
        "advisor_notes": "Sim #3 — gate cancellation, 19h rebooking, no care provided.",
    })
    claim_id = (gen["response"] or {}).get("claim_id")

    if claim_id:
        base = f"/api/v1/passenger-rights/{trip_id}/claims/{claim_id}/disposition"
        client.call("C-dispo-get-initial", "GET", base)
        # generate-claim auto-advances to SUBMITTED — the happy path from here:
        # SUBMITTED -> AIRLINE_PARTIAL -> TRAVELER_PAID -> CLOSED.
        # Illegal jump first: SUBMITTED -> TRAVELER_PAID must be rejected.
        client.call("C-dispo-illegal", "PATCH", base, json={"new_state": "TRAVELER_PAID", "note": "sim3 illegal jump probe"})
        client.call("C-dispo-backwards", "PATCH", base, json={"new_state": "DRAFTED", "note": "sim3 backwards probe"})
        client.call("C-dispo-partial", "PATCH", base, json={"new_state": "AIRLINE_PARTIAL", "note": "airline offered 50%"})
        client.call("C-dispo-paid", "PATCH", base, json={
            "new_state": "TRAVELER_PAID", "note": "airline paid traveler directly",
            "outcome": {"amount": "EUR 300", "channel": "airline_direct", "recorded_only": True}})
        client.call("C-dispo-closed", "PATCH", base, json={"new_state": "CLOSED", "note": "resolved"})
        client.call("C-dispo-after-terminal", "PATCH", base, json={"new_state": "SUBMITTED", "note": "terminal probe"})
        client.call("C-dispo-final", "GET", base)

    client.call("C-messages", "GET", f"/api/v1/trips/{trip_id}/messages")
    if not skip_ui:
        shot("C", "workbench", "http://localhost:3005/workbench", "workbench_claims")
        shot("C", "inbox", "http://localhost:3005/inbox", "inbox_disruption")


def run_sim_D(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, run_id = _submit_and_poll(client, "D1-run", VOICES["D1"])
    trip_id = _find_trip(client, status or {})
    trip = {}
    if trip_id:
        e = client.call("D1-trip", "GET", f"/trips/{trip_id}")
        trip = e["response"].get("trip") or e["response"]
    client.log.append({"step": "D1-packet", "packet_summary": _packet_summary(trip)})

    token = None
    if trip_id:
        send = client.call("D-send-ask", "POST", f"/followups/{trip_id}/send", json={
            "recipient": "priyanka.sen.sim3@waypointtest.dev",
            "channel": "email",
            "ttl_hours": 168,
        })
        token = (send["response"] or {}).get("token")
        ask_path = (send["response"] or {}).get("ask_path")
        client.log.append({"step": "D-ask-minted", "token": token, "ask_path": ask_path})

    if token:
        # Unauthenticated traveler view (the real public door).
        anon = client.call("D-public-view", "GET",
                           f"http://localhost:8000/api/public/asks/{token}")
        # Answer exactly the questions the trip asked (field names come from
        # the public view — the endpoint validates against open questions).
        asked = ((anon.get("response") or {}).get("questions")) or []
        canned = {
            "origin_city": "bangalore",
            "date_window": "nov 16 evening - nov 19 morning",
            "trip_purpose": "anniversary pilgrimage with my parents",
            "party_size": "2",
            "budget_raw_text": "around ₹90,000 total",
            "destination_candidates": "varanasi",
        }
        answer_entries = [
            {"field_name": q.get("field_name"),
             "answer": canned.get(q.get("field_name"),
                                  "accessible room, ground floor please")}
            for q in asked if isinstance(q, dict) and q.get("field_name")
        ] or [{"field_name": "general", "answer": VOICES["D2"]}]
        answers = client.call("D-public-answer", "POST",
                              f"http://localhost:8000/api/public/asks/{token}/answers",
                              json={
                                  "answers": answer_entries,
                                  "respondent_name": "Priyanka Sen",
                              })
        client.log.append({"step": "D-public-result",
                           "view_status": anon["status"],
                           "answer_status": answers["status"]})
        if not skip_ui:
            shot("D", "public_ask", f"http://localhost:3005/a/{token}", "public_ask_page")

    if trip_id:
        e = client.call("D-trip-after-answers", "GET", f"/trips/{trip_id}")
        trip2 = e["response"].get("trip") or e["response"]
        client.log.append({"step": "D1-packet-after-answers", "packet_summary": _packet_summary(trip2)})
        # T9: confirmation extraction/grading on a supplier voucher text.
        client.call("D-confirm-extract", "POST", f"/api/trips/{trip_id}/confirmations/extract", json={
            "raw_text": (
                "Booking confirmed — Ganga View Heritage, Varanasi. Accessible "
                "Deluxe Room, ground floor, 2 guests. Check-in 16 Nov 2026, "
                "check-out 19 Nov 2026. Confirmation #GV-88231. Total INR 38,400. "
                "Step-free entrance via river-side gate."
            ),
            "document_name": "ganga_view_voucher.txt",
            "auto_record": True,
        })
        client.call("D-confirmations-list", "GET", f"/api/v1/trips/{trip_id}/confirmations")
        if not skip_ui:
            shot("D", "workbench", "http://localhost:3005/workbench", "workbench_ask")
