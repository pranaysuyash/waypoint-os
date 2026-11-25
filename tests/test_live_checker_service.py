from spine_api.services.live_checker_service import (
    _attach_d6_public_authority,
    apply_live_checker_adjustments,
    build_consented_submission,
    collect_raw_text_sources,
)


def test_build_consented_submission_retention_true_returns_original() -> None:
    payload = {"raw_note": "a", "destination": "Tokyo"}
    assert build_consented_submission(payload, retention_consent=True) == payload


def test_build_consented_submission_retention_false_redacts_text_fields() -> None:
    payload = {
        "raw_note": "a",
        "owner_note": "b",
        "itinerary_text": "c",
        "structured_json": {"source_payload": {}},
        "destination": "Tokyo",
    }
    assert build_consented_submission(payload, retention_consent=False) == {"destination": "Tokyo"}


def test_collect_raw_text_sources_includes_uploaded_file_text() -> None:
    raw_text = collect_raw_text_sources(
        raw_note="raw",
        owner_note="owner",
        itinerary_text="itinerary",
        structured_json={
            "source_payload": {
                "uploaded_file": {
                    "extracted_text": "file text",
                }
            }
        },
    )
    assert raw_text == "raw\nowner\nitinerary\nfile text"


def test_apply_live_checker_adjustments_merges_blockers_and_adjusts_score() -> None:
    packet_payload = {"quality_score": 90}
    validation_payload = {"overall_score": 88}
    decision_payload = {"hard_blockers": ["A"], "soft_blockers": ["B"]}
    live_checker = {"score_penalty": 10, "hard_blockers": ["A", "C"], "soft_blockers": ["D"]}

    packet, validation, decision = apply_live_checker_adjustments(
        packet_payload=packet_payload,
        validation_payload=validation_payload,
        decision_payload=decision_payload,
        live_checker=live_checker,
    )

    assert validation["overall_score"] == 78
    assert packet["score"] == 78
    assert validation["public_checker_live_checks"]["score_penalty"] == 10
    assert decision["public_checker_live_checks"]["score_penalty"] == 10
    assert "d6_public_surface" in validation["public_checker_live_checks"]
    assert "d6_public_surface" in decision["public_checker_live_checks"]
    assert decision["hard_blockers"] == ["A"]
    assert decision["soft_blockers"] == ["B"]
    assert decision["advisory_hard_blockers"] == ["A", "C"]
    assert decision["advisory_soft_blockers"] == ["D"]


def test_apply_live_checker_adjustments_uses_decision_baseline_fallback() -> None:
    packet, validation, decision = apply_live_checker_adjustments(
        packet_payload={},
        validation_payload={},
        decision_payload={"decision_state": "ASK_FOLLOWUP"},
        live_checker={"score_penalty": 4},
    )
    assert validation["overall_score"] == 60
    assert packet["score"] == 60
    assert decision["public_checker_live_checks"]["score_penalty"] == 4
    assert "d6_public_surface" in decision["public_checker_live_checks"]


def test_attach_d6_public_authority_marks_untracked_weather_as_advisory() -> None:
    live_checker = {
        "hard_blockers": ["Heavy rain"],
        "soft_blockers": ["Regional advisory"],
        "structured_risks": [
            {"flag": "weather_monsoon", "severity": "high", "category": "weather", "message": "Heavy rain"},
            {"flag": "regional_safety_advisory", "severity": "high", "category": "safety", "message": "Regional advisory"},
        ],
    }

    enriched = _attach_d6_public_authority(live_checker)
    d6_meta = enriched["d6_public_surface"]

    assert d6_meta["category_status"]["weather"] == "shadow"
    assert d6_meta["category_authority"]["weather"] == "advisory"
    assert d6_meta["category_status"]["safety"] == "shadow"
    assert d6_meta["advisory_hard_blockers"] == ["Heavy rain"]
    assert d6_meta["advisory_soft_blockers"] == ["Regional advisory"]
    assert d6_meta["authoritative_hard_blockers"] == []
    assert d6_meta["authoritative_soft_blockers"] == []
    assert all(risk["public_surface_authority"] == "advisory" for risk in enriched["structured_risks"])


def test_apply_live_checker_adjustments_merges_authoritative_blockers(monkeypatch) -> None:
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", "/tmp/does-not-exist-d6-snapshot.json")
    live_checker = {
        "score_penalty": 5,
        "hard_blockers": ["budget mismatch found"],
        "soft_blockers": ["possible budget drift"],
        "structured_risks": [
            {
                "flag": "budget_overrun",
                "severity": "high",
                "category": "budget",
                "message": "budget mismatch found",
            },
            {
                "flag": "budget_warning",
                "severity": "medium",
                "category": "budget",
                "message": "possible budget drift",
            },
        ],
    }
    _, _, decision = apply_live_checker_adjustments(
        packet_payload={},
        validation_payload={},
        decision_payload={"hard_blockers": ["existing_hard"], "soft_blockers": ["existing_soft"]},
        live_checker=live_checker,
    )

    assert "budget mismatch found" in decision["hard_blockers"]
    assert "possible budget drift" in decision["soft_blockers"]
    assert decision["advisory_hard_blockers"] == []
    assert decision["advisory_soft_blockers"] == []


# ---------------------------------------------------------------------------
# WOBS 2026-09-09 P1 — Ghost Hotel entity-check wiring (advisory, fail-open)
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, packet, validation, decision):
        self.packet = packet
        self.validation = validation
        self.decision = decision


def _identity(value):
    return value


def test_rail_follow_up_respects_fresh_and_undated_confirmation():
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    note = "An overnight train is waitlisted. There is a separately booked morning transfer."
    correction = " Correction from the traveler or operator: "
    for update, context, expected in (
        ("", "Waitlist reported", "cancel the morning transfer"),
        (correction + "The traveler supplies a fresh confirmation for that exact train and date.",
         "Originally waitlisted", "station will the transfer operator use"),
        (correction + "The traveler supplies a fresh confirmation.",
         "Confirmation needs matching", "confirmation match the train and date"),
        (correction + "There is no fresh confirmation for that exact train and date.",
         "Confirmation needs matching", "confirmation match the train and date"),
        (correction + "The traveler supplies a fresh confirmation for that exact train and date, but the screenshot has no date.",
         "Confirmation needs matching", "confirmation match the train and date"),
        (correction + "The traveler supplies a fresh confirmation for a different train and date.",
         "Confirmation needs matching", "confirmation match the train and date"),
        (" The earlier note is incomplete or unreliable. Update: The screenshot has no date.",
         "Confirmation needs matching", "confirmation match the train and date"),
    ):
        result = _FakeResult(
            packet={"facts": {"destination_candidates": {"value": ["Train"]}}},
            validation={},
            decision={"hard_blockers": []},
        )
        finalize_result_with_live_checker(
            result=result, raw_text=note + update,
            build_live_checker_signals_fn=lambda *_: None, to_dict=_identity,
        )
        assert context in result.packet["itinerary_feasibility_context"]
        assert expected in result.packet["itinerary_feasibility_question"]
        assert "destination_candidates" not in result.packet["facts"]
        assert result.decision["hard_blockers"] == []


def test_prose_goa_pacing_preserves_calendar_day_and_respects_correction():
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    note = "We propose Baga, Dudhsagar and Old Goa on 19 December."
    for update, expected in (
        ("", True),
        (" Correction from the traveler or operator: Move Old Goa to the next day.", False),
        (" The earlier note is incomplete or unreliable. Update: No dates.", False),
    ):
        result = _FakeResult(
            packet={"facts": {"destination_candidates": {"value": ["Old Goa"]}}},
            validation={},
            decision={},
        )
        finalize_result_with_live_checker(
            result=result, raw_text=note + update,
            build_live_checker_signals_fn=lambda *_: None, to_dict=_identity,
        )
        assert result.packet["facts"]["destination_candidates"]["value"] == ["Goa"]
        assert bool(result.packet.get("itinerary_feasibility_findings")) is expected
        assert result.packet["itinerary_feasibility_question"]


def test_goa_pacing_changes_only_for_a_confirmed_different_day():
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    for correction, expected in (
        ("Actually we will do Old Goa on 20 December instead.", "before visiting Baga"),
        ("Actually we will do Old Goa on 19 Dec instead.", "Dudhsagar entry slot"),
        ("Maybe we will do Old Goa on 20 December instead.", "Dudhsagar entry slot"),
        ("Actually we will do Old Goa on 32 December instead.", "Dudhsagar entry slot"),
    ):
        result = _FakeResult(packet={"facts": {}}, validation={}, decision={})
        finalize_result_with_live_checker(
            result=result,
            raw_text=f"We propose Baga, Dudhsagar and Old Goa on 19 December. {correction}",
            build_live_checker_signals_fn=lambda *_: None,
            to_dict=_identity,
        )
        assert expected in result.packet["itinerary_feasibility_question"]


def test_prose_overnight_preserves_partial_date_without_inventing_year():
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    note = "A Delhi to Goa flight leaves at 23:55 on 18 December and lands at 02:25 the next day. The 18 December hotel night is on the draft."
    for update, expected in (
        ("", True),
        (" Correction from the traveler or operator: The hotel booking begins on 19 December.", False),
        (" The earlier note is incomplete or unreliable. Update: The arrival has no day or date.", False),
    ):
        result = _FakeResult(packet={"facts": {}}, validation={}, decision={})
        finalize_result_with_live_checker(
            result=result, raw_text=note + update,
            build_live_checker_signals_fn=lambda *_: None, to_dict=_identity,
        )
        assert "Outbound 18 December" in result.packet["itinerary_feasibility_context"]
        assert "date_start" not in result.packet["facts"]
        assert bool(result.packet.get("itinerary_feasibility_findings")) is expected
        assert result.packet["itinerary_feasibility_question"]


def test_finalize_overnight_and_pacing_as_shared_advisories() -> None:
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    result = _FakeResult(
        packet={"facts": {
            "origin_city": {"value": "Delhi"},
            "destination_candidates": {"value": ["Goa"]},
            "date_start": {"value": "2026-12-18"},
        }},
        validation={},
        decision={"hard_blockers": [], "soft_blockers": []},
    )
    finalize_result_with_live_checker(
        result=result,
        raw_text=(
            "Delhi 23:55 to Goa 02:25 next day. Hotel check-in 18 Dec. "
            "Baga + Dudhsagar + Old Goa ek hi din?"
        ),
        build_live_checker_signals_fn=lambda *_: None,
        to_dict=_identity,
    )

    hotel, pacing = result.packet["itinerary_feasibility_findings"]
    assert hotel["flag"] == "overnight_hotel_arrival"
    assert hotel["message"] == result.packet["public_checker_overnight_hotel_finding"]
    assert "02:25 on 19 December" in hotel["message"]
    assert pacing["flag"] == "goa_day_pacing"
    assert pacing["message"] == result.packet["public_checker_day_pacing_finding"]
    assert all(finding["details"]["authority"] == "advisory" for finding in (hotel, pacing))
    assert result.decision == {"hard_blockers": [], "soft_blockers": []}


def test_finalize_attaches_entity_checks_without_live_signals() -> None:
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    result = _FakeResult(packet={"quality_score": 70}, validation={}, decision={})
    calls = []

    def fake_entity_fn(packet, raw_text):
        calls.append((packet, raw_text))
        return [
            {
                "name": "Taj Palace",
                "status": "verified",
                "confidence": 0.7,
                "message": "Found.",
            }
        ]

    finalize_result_with_live_checker(
        result=result,
        raw_text="check-in at Taj Palace Hotel",
        build_live_checker_signals_fn=lambda packet, text: None,  # no live signals
        to_dict=_identity,
        build_entity_checks_fn=fake_entity_fn,
    )

    assert calls and calls[0][1] == "check-in at Taj Palace Hotel"
    assert result.packet["public_checker_entity_checks"][0]["name"] == "Taj Palace"
    assert result.validation["public_checker_entity_checks"][0]["status"] == "verified"


def test_finalize_entity_fn_failure_fails_open_without_breaking_run() -> None:
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    result = _FakeResult(packet={"quality_score": 70}, validation={}, decision={})

    def bomb(packet, raw_text):
        raise RuntimeError("gazetteer down")

    finalize_result_with_live_checker(
        result=result,
        raw_text="check-in at Hotel Nowhere",
        build_live_checker_signals_fn=lambda packet, text: None,
        to_dict=_identity,
        build_entity_checks_fn=bomb,
    )

    assert "public_checker_entity_checks" not in (result.packet or {})


def test_finalize_entity_checks_run_after_live_adjustments() -> None:
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    result = _FakeResult(
        packet={"quality_score": 90, "destination": "Singapore"},
        validation={"overall_score": 88},
        decision={"hard_blockers": [], "soft_blockers": []},
    )
    live_checker = {
        "score_penalty": 5,
        "hard_blockers": [],
        "soft_blockers": ["monsoon window"],
        "destination": "Singapore",
    }
    seen_packets = []

    finalize_result_with_live_checker(
        result=result,
        raw_text="check-in at Marina Bay Hotel",
        build_live_checker_signals_fn=lambda packet, text: live_checker,
        to_dict=_identity,
        build_entity_checks_fn=lambda packet, text: (seen_packets.append(packet) or [
            {"name": "Marina Bay", "status": "not_found", "confidence": 0.5, "message": "no record"}
        ]),
    )

    # Entity fn saw the post-adjustment packet (score already applied).
    assert seen_packets[0]["score"] == 83
    assert result.packet["public_checker_entity_checks"][0]["status"] == "not_found"
    # Advisory: score and blockers untouched by entity layer.
    assert result.validation["overall_score"] == 83
    assert result.decision["hard_blockers"] == []


def test_compound_itinerary_retains_each_supplier_concern() -> None:
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    hotel = "The hotel needs an advance today. When do I lose it if I cancel?"
    rail = "The overnight train is waitlisted. Our morning transfer is booked separately."
    access = "One guest needs step-free boarding. The van and station transfer are unconfirmed."
    for notes in ((hotel, rail, access), (rail, access, hotel), (rail, access)):
        result = _FakeResult(packet={}, validation={}, decision={})
        finalize_result_with_live_checker(
            result=result,
            raw_text=" ".join(notes),
            build_live_checker_signals_fn=lambda packet, text: None,
            to_dict=_identity,
        )
        expected_flags = ["overnight_rail_transfer", "step_free_transfer"] if hotel in notes else ["step_free_transfer"]
        assert result.packet["itinerary_feasibility_question"].startswith(
            "What is the cancellation cutoff" if hotel in notes else "When can you change or cancel"
        )
        findings = result.packet["itinerary_feasibility_findings"]
        assert [finding["flag"] for finding in findings] == expected_flags
        assert all(finding["details"]["authority"] == "advisory" for finding in findings)
        assert result.decision == {}


def test_eurostar_disruption_asks_about_the_affected_onward_booking():
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    delay = "Our Eurostar to Paris is delayed today. We expect to miss the separately booked "
    operator_source = "https://www.eurostar.com/uk-en/travel-info/connecting-train"
    for onward, identifier, expected, sourced in (
        ("TGV INOUI from Gare de Lyon.", "eurostar_tgv_connection", "proof of delay", True),
        ("RER B from Gare du Nord.", "eurostar_rer_connection", "RER ticket", True),
        ("driver pickup at Gare du Nord.", "eurostar_driver_pickup", "pickup", False),
        ("onward train, and I do not have the operator or station.",
         "eurostar_onward_details", "operator and departure station", False),
        ("TGV INOUI, station unknown.", "eurostar_onward_details", "departure station", False),
        ("onward train from Gare de Lyon.", "eurostar_onward_details", "operator", False),
    ):
        result = _FakeResult(packet={}, validation={}, decision={})
        finalize_result_with_live_checker(
            result=result, raw_text=delay + onward,
            build_live_checker_signals_fn=lambda *_: None, to_dict=_identity,
        )
        assert result.packet["itinerary_feasibility_id"] == identifier
        assert expected in result.packet["itinerary_feasibility_question"]
        assert result.packet.get("itinerary_feasibility_source_url") == (operator_source if sourced else None)
        assert not result.packet.get("itinerary_feasibility_findings")
        assert result.decision == {}


def test_eurostar_rejects_hypothetical_unrelated_negated_and_resolved_connections():
    from spine_api.services.feasibility_follow_up import supplier_follow_ups

    for note, update in (
        ("If our Eurostar to Paris is delayed, we will miss our TGV INOUI.", ""),
        ("Our Eurostar to Paris is on time. Our TGV INOUI is delayed.", ""),
        ("Our Eurostar is not delayed. We expect to miss our TGV INOUI.", ""),
        ("Our Eurostar is delayed. We will not miss our TGV INOUI.", ""),
        ("Our Eurostar is delayed. We missed our flight. Tomorrow we take the TGV INOUI.", ""),
        ("Our Eurostar is delayed. We expect to miss our RER B from Gare du Nord.",
         "We caught the RER after all."),
    ):
        assert not any(key.startswith("eurostar_") for key in supplier_follow_ups(note, update))


def test_eurostar_supplement_retains_its_distinct_source_and_onward_leg():
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    result = _FakeResult(packet={}, validation={}, decision={})
    note = (
        "The hotel needs a deposit. When can I cancel? "
        "Our Eurostar is running late, so we'll miss our separately booked TGV INOUI from Gare de Lyon."
    )
    finalize_result_with_live_checker(
        result=result, raw_text=note, build_live_checker_signals_fn=lambda *_: None, to_dict=_identity,
    )
    assert result.packet["itinerary_feasibility_id"] == "hotel_terms"
    assert "itinerary_feasibility_source_url" not in result.packet
    rail, = result.packet["itinerary_feasibility_findings"]
    assert rail["flag"] == "eurostar_tgv_connection"
    assert rail["details"]["source_url"] == "https://www.eurostar.com/uk-en/travel-info/connecting-train"
    assert rail["details"]["authority"] == "advisory"


def test_disruption_resolution_is_scoped_to_the_named_onward_leg():
    from spine_api.services.feasibility_follow_up import supplier_follow_ups

    note = "Our Eurostar to Paris was cancelled. We missed our TGV INOUI from Gare de Lyon."
    findings = supplier_follow_ups(note, "")
    assert "proof of cancellation" in findings["eurostar_tgv_connection"][1]
    changed = supplier_follow_ups(note, "Our onward train was replaced by a driver pickup.")
    assert set(changed) == {"eurostar_onward_details"}
    mixed = supplier_follow_ups(note.replace("TGV INOUI from Gare de Lyon", "driver pickup"), "We caught the RER.")
    assert set(mixed) == {"eurostar_driver_pickup"}
    assert not supplier_follow_ups("Our Eurostar to Paris and bus is delayed. We missed our TGV INOUI.", "")


def test_compound_rule_evaluation_preserves_hinglish_attachment_check():
    from spine_api.services.feasibility_follow_up import supplier_follow_ups

    findings = supplier_follow_ups("Delhi se Goa 18 Dec. Attached page shows 19/12.", "")
    assert "19/12" in findings["attachment_date"][1]


def test_supplier_updates_preserve_unrelated_hotel_and_rail_findings():
    from spine_api.services.feasibility_follow_up import supplier_follow_ups

    note = (
        "Hotel Alpha requires a deposit and says cancellation is free. "
        "The overnight train is waitlisted. Our morning transfer is booked separately."
    )
    original = supplier_follow_ups(note, "")
    hotel_update = supplier_follow_ups(note, "Hotel Alpha confirms its deposit is nonrefundable.")
    transfer_update = supplier_follow_ups(note, "The morning transfer deposit is nonrefundable.")
    rail_update = supplier_follow_ups(note, "The train confirmation screenshot has no date.")
    assert hotel_update["overnight_rail_transfer"] == original["overnight_rail_transfer"]
    assert "Nonrefundable deposit reported" in hotel_update["hotel_terms"][0]
    assert transfer_update == original
    assert rail_update["hotel_terms"] == original["hotel_terms"]
    assert "Confirmation needs matching" in rail_update["overnight_rail_transfer"][0]


def test_collect_raw_text_sources_joins_unique_text_in_original_order():
    note = "The train is waitlisted. Correction: Hotel Alpha confirmed the deposit."
    assert collect_raw_text_sources(note, "Advisor note", note, {
        "source_payload": {"uploaded_file": {"extracted_text": "Distinct attachment"}},
    }) == f"{note}\nAdvisor note\nDistinct attachment"


def test_distinct_named_hotels_keep_their_own_questions_in_shared_packet():
    from spine_api.services.live_checker_service import finalize_result_with_live_checker

    result = _FakeResult(packet={"facts": {}}, validation={}, decision={})
    finalize_result_with_live_checker(
        result=result,
        raw_text=(
            "Hotel Alpha requires a deposit and says cancellation is free. "
            "Hotel Beta requires a deposit and says cancellation is free. "
            "The overnight train is waitlisted. Our morning transfer is booked separately. "
            "Correction from the traveler or operator: Hotel Alpha confirms its deposit is nonrefundable."
        ),
        build_live_checker_signals_fn=lambda *_: None,
        to_dict=_identity,
    )
    assert "Hotel Alpha" in result.packet["itinerary_feasibility_context"]
    assert "nonrefundable" in result.packet["itinerary_feasibility_question"]
    findings = result.packet["itinerary_feasibility_findings"]
    assert any("Hotel Beta" in finding["details"]["title"] and "cutoff" in finding["message"] for finding in findings)
    assert any("remains waitlisted" in finding["message"] for finding in findings)



def test_same_hotel_reservations_require_update_attribution():
    from spine_api.services.feasibility_follow_up import supplier_follow_ups

    first = "Hotel Alpha requires a deposit and says cancellation is free for the first reservation."
    second = "Hotel Alpha requires another deposit and says cancellation is free for the second reservation."
    update = "Hotel Alpha confirms its deposit is nonrefundable."
    for note in (f"{first} {second}", f"{second} {first}"):
        findings = supplier_follow_ups(note, update)
        assert len(findings) == 1
        context, question, _ = next(iter(findings.values()))
        assert context == "Hotel Alpha · Multiple reservations"
        assert "each reservation" in question
    repeated = supplier_follow_ups(f"{first} {first}", update)
    assert "Nonrefundable" in repeated["hotel_terms"][0]



def test_vehicle_ferry_compares_arrival_with_ticketed_cutoff():
    from spine_api.services.feasibility_follow_up import supplier_follow_ups

    base = "Our rental car will reach Cairnryan port at 03:00 local time. Our 03:30 Stena Line ferry to Belfast"
    ticket = " shows vehicle check-in closes at 02:45 on the e-ticket."
    lead = supplier_follow_ups(base + ticket, "")["vehicle_ferry_cutoff"]
    assert "15 minutes after" in lead[0]
    assert "earlier port arrival" in lead[1]

    early = supplier_follow_ups(base.replace("03:00", "02:20") + ticket, "")
    assert "vehicle_ferry_cutoff" not in early

    missing = supplier_follow_ups(base + " is booked.", "")["vehicle_ferry_cutoff"]
    assert "e-ticket" in missing[1]

    rollover = supplier_follow_ups(base.replace("03:30", "00:30") + ticket.replace("02:45", "23:45"), "")
    assert "local date" in rollover["vehicle_ferry_cutoff"][1]

    conflict = supplier_follow_ups(base + ticket + " Vehicle check-in closes at 03:10 on the timetable.", "")
    assert "different check-in times" in conflict["vehicle_ferry_cutoff"][0]

    cruise = supplier_follow_ups("The independent cruise excursion returns at 16:45. Ship all-aboard is at 17:00.", "")
    assert "vehicle_ferry_cutoff" not in cruise


def test_vehicle_ferry_uses_all_explicit_local_dates_across_midnight():
    from spine_api.services.feasibility_follow_up import supplier_follow_ups

    note = (
        "Our rental car will reach Cairnryan port at 23:50 local time on 2026-12-18. "
        "Our 2026-12-19 00:30 Stena Line ferry to Belfast shows "
        "vehicle check-in closes at 23:45 on 2026-12-18 on the e-ticket."
    )
    context, question, _ = supplier_follow_ups(note, "")["vehicle_ferry_cutoff"]
    assert "5 minutes after" in context
    assert "2026-12-18" in context
    assert "earlier port arrival" in question
    assert "vehicle_ferry_cutoff" not in supplier_follow_ups(note.replace("23:50", "23:25"), "")
    for uncertain in (
        note.replace("local time on 2026-12-18", "local time"),
        note.replace("23:45 on 2026-12-18", "23:45 on 2026-12-19"),
        note.replace("2026-12-18", "2026-12-32"),
    ):
        assert "local date" in supplier_follow_ups(uncertain, "")["vehicle_ferry_cutoff"][1]
