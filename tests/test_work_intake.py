"""
tests/test_work_intake.py — the work-intake classification choke point
(A1/A2/C1/C2/C3/E2 of Docs/architecture/INCOMING_WORK_CLASSIFICATION_MAP_2026-10-24.md).

Covers: door contracts, identity normalization + hashing, urgency heuristics,
duplicate flagging (C3), returning-guest annotation (C2, via the memory-lookup
seam), PII-never-persisted invariant, queue ranking (C1), the /work-items
router, the inbound/parse door closed loop (recorded item after a real parse),
and triage consuming the classifier (E2).

Sensitivity: S1 for behavior assertions; S3 mutations noted inline
(queue-order shuffle, dedup-window intent mutation, no-PII content check).
"""

import json
import os
import uuid

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import pytest

from spine_api.services import work_intake


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    # Isolated per-test store (FND-0366 discipline: never touch shared stores).
    monkeypatch.setenv("WAYPOINT_WORK_ITEMS_DIR", str(tmp_path / "work_items"))
    yield


AGENCY = "agency_work_intake_test"


# ---------------------------------------------------------------------------
# Classifier core (A1/A2)
# ---------------------------------------------------------------------------

def test_door_contracts_are_complete_and_valid():
    """Every registered door classifies into the legal vocabularies."""
    for door, contract in work_intake.DOOR_CONTRACTS.items():
        assert contract["origin"] in work_intake.WORK_ORIGINS, door
        assert contract["intent"] in work_intake.WORK_INTENTS, door
        assert contract["authority"] in work_intake.WORK_AUTHORITIES, door


def test_unknown_door_is_rejected():
    """A door must declare its class at the seam — unregistered doors fail loud."""
    with pytest.raises(ValueError):
        work_intake.classify("not_a_door", agency_id=AGENCY)


def test_door_defaults_and_overrides():
    item = work_intake.classify("run", agency_id=AGENCY, text=None)
    assert item["origin"] == "demand"
    assert item["intent"] == "new_demand"
    assert item["authority"] == "operator"  # operator submits on the traveler's behalf

    item = work_intake.classify(
        "channel_webhook", agency_id=AGENCY, text=None, intent_override="new_demand"
    )
    assert item["intent"] == "new_demand"
    assert item["authority"] == "explicit_user"  # traveler's own words (A2)


def test_identity_key_normalized_stable_and_scoped():
    """Same traveler (case/format variants) -> same key; other agency -> other key."""
    a1 = work_intake.identity_key(AGENCY, "Ravi.K@example.COM")
    a2 = work_intake.identity_key(AGENCY, "ravi.k@example.com")
    assert a1 == a2

    p1 = work_intake.identity_key(AGENCY, "+91 98765-43210")
    p2 = work_intake.identity_key(AGENCY, "919876543210")
    assert p1 == p2 and p1 is not None

    other = work_intake.identity_key("agency_other", "ravi.k@example.com")
    assert other != a1
    assert work_intake.identity_key(AGENCY, "") is None
    assert work_intake.identity_key(AGENCY, None) is None


def test_urgency_heuristics():
    assert work_intake.urgency_from_text("URGENT: need to fly tomorrow") == "high"
    assert work_intake.urgency_from_text("just exploring, no rush, sometime next year") == "low"
    assert work_intake.urgency_from_text("Planning a trip to Japan.") == "normal"
    assert work_intake.urgency_from_text(None) == "normal"


# ---------------------------------------------------------------------------
# Recording (store invariants)
# ---------------------------------------------------------------------------

def test_recorded_item_never_persists_pii():
    """S3: the stored JSONL must not contain the raw email/phone — only the hash."""
    email = f"ravi.{uuid.uuid4().hex[:6]}@example.com"
    item = work_intake.classify_and_record(
        "inbound_parse",
        agency_id=AGENCY,
        text=f"Trip to Goa, reach me at {email} or +91 98765 43210",
        contact=email,
    )
    assert item["pii_present"] is True
    assert item["identity_key"]

    path = work_intake._agency_path(AGENCY)
    raw = path.read_text(encoding="utf-8")
    assert email not in raw
    assert "98765" not in raw
    stored = json.loads(raw.strip().splitlines()[-1])
    assert stored["identity_key"] == item["identity_key"]
    assert stored["payload_summary"] == {"text_chars": len(f"Trip to Goa, reach me at {email} or +91 98765 43210")}


def test_duplicate_flagging_c3():
    """C3 S2/S3: same contact + new_demand within window flags; different intent does not."""
    contact = f"same.{uuid.uuid4().hex[:6]}@example.com"
    first = work_intake.classify_and_record(
        "inbound_parse", agency_id=AGENCY, text="Want Japan trip", contact=contact
    )
    assert first["duplicate_of"] is None

    second = work_intake.classify_and_record(
        "inbound_parse", agency_id=AGENCY, text="Japan again please", contact=contact
    )
    assert second["duplicate_of"] == first["item_id"]

    # S3 mutation: a different intent on the same identity must NOT flag.
    answer = work_intake.classify_and_record(
        "ask_answers", agency_id=AGENCY, text=None, contact=contact
    )
    assert answer["duplicate_of"] is None


def test_returning_guest_annotation_c2(monkeypatch):
    """C2: memory facts at the canonical entity id -> returning_customer; none -> False.
    Seam: _memory_facts_for_contact is the memory-read seam (display-only contract)."""
    contact = f"elena.{uuid.uuid4().hex[:6]}@example.com"
    monkeypatch.setattr(
        work_intake,
        "_memory_facts_for_contact",
        lambda agency_id, c: (
            {"returning_customer": True, "memory_entity_id": f"cust_{c}", "memory_fact_count": 3}
            if c == contact
            else {"returning_customer": False, "memory_entity_id": None, "memory_fact_count": 0}
        ),
    )
    known = work_intake.classify("inbound_parse", agency_id=AGENCY, text=None, contact=contact)
    assert known["returning_customer"] is True
    assert known["memory_fact_count"] == 3

    fresh = work_intake.classify(
        "inbound_parse", agency_id=AGENCY, text=None, contact=f"new.{uuid.uuid4().hex[:6]}@example.com"
    )
    assert fresh["returning_customer"] is False


def test_ranked_queue_c1():
    """C1 with S3 shuffle: ranking = urgency, then returning guest, then recency."""
    plain = work_intake.classify_and_record(
        "inbound_parse", agency_id=AGENCY, text="trip to Bali", contact=f"a{uuid.uuid4().hex[:6]}@x.com"
    )
    low = work_intake.classify_and_record(
        "inbound_parse", agency_id=AGENCY, text="just exploring no rush", contact=f"b{uuid.uuid4().hex[:6]}@x.com"
    )
    urgent = work_intake.classify_and_record(
        "inbound_parse", agency_id=AGENCY, text="URGENT flight tonight", contact=f"c{uuid.uuid4().hex[:6]}@x.com"
    )
    assert urgent["urgency"] == "high" and low["urgency"] == "low"

    queue = work_intake.ranked_queue(AGENCY)
    ids = [i["item_id"] for i in queue["items"]]
    # urgency dominates insertion order (plain was recorded first but urgent ranks above it)
    assert ids.index(urgent["item_id"]) < ids.index(plain["item_id"]) < ids.index(low["item_id"])
    assert queue["counts"]["by_urgency"]["high"] == 1
    assert queue["counts"]["by_origin"]["demand"] >= 3
    assert queue["count_basis"] == "work_item_log_total"


def test_duplicate_risk_preview_seam():
    contact = f"prev.{uuid.uuid4().hex[:6]}@example.com"
    assert work_intake.duplicate_risk(AGENCY, contact) is False
    work_intake.classify_and_record(
        "inbound_parse", agency_id=AGENCY, text="new demand", contact=contact
    )
    assert work_intake.duplicate_risk(AGENCY, contact) is True
    assert work_intake.duplicate_risk(AGENCY, None) is False


# ---------------------------------------------------------------------------
# Router + doors (Tier 2/3)
# ---------------------------------------------------------------------------

def test_work_items_router_requires_agency_and_ranks(session_client):
    unique = uuid.uuid4().hex[:8]
    work_intake.classify_and_record(
        "inbound_parse",
        agency_id=f"agency_q_{unique}",
        text="URGENT trip to Delhi tomorrow",
        contact=f"q{unique}@example.com",
    )
    work_intake.classify_and_record(
        "inbound_parse",
        agency_id=f"agency_q_{unique}",
        text="thinking about japan sometime",
        contact=f"r{unique}@example.com",
    )
    res = session_client.get(
        "/api/v1/work-items", headers={"X-Agency-ID": f"agency_q_{unique}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["items"][0]["urgency"] == "high"
    assert data["items"][0]["origin"] == "demand"
    assert data["counts"]["by_intent"]["new_demand"] == 2
    # tenant isolation: another agency sees none of these
    other = session_client.get(
        "/api/v1/work-items", headers={"X-Agency-ID": f"agency_z_{unique}"}
    ).json()
    assert other["total"] == 0


def test_inbound_parse_door_records_work_item_closed_loop(session_client):
    """Invariant-4 style closed loop: exercise the door -> the queue surface changes."""
    suffix = uuid.uuid4().hex[:8]
    contact = f"closedloop.{suffix}@example.com"
    res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "whatsapp_web",
            "raw_text": f"Family of 4 to Paris in December, budget 12000 USD. Contact {contact}",
            "customer_name": f"CL Tester {suffix}",
            "customer_contact": contact,
            "strict_leakage": False,
        },
        headers={"X-Agency-ID": f"agency_cl_{suffix}"},
    )
    assert res.status_code == 200
    trip_id = res.json()["trip_id"]

    queue = session_client.get(
        "/api/v1/work-items", headers={"X-Agency-ID": f"agency_cl_{suffix}"}
    ).json()
    assert queue["total"] >= 1
    item = queue["items"][0]
    assert item["door"] == "inbound_parse"
    assert item["trip_id"] == trip_id
    assert item["identity_known"] is True
    assert item["authority"] == "explicit_user"


def test_messaging_webhook_door_records_work_item(session_client):
    """Closed loop for the channel door: webhook message -> classified item."""
    suffix = uuid.uuid4().hex[:8]
    res = session_client.post(
        "/api/v1/messaging/webhook/testprovider",
        json={"event": "message", "from": f"+1555019{suffix[:4]}", "body": "hi, need urgent visa help"},
    )
    assert res.status_code == 200
    assert res.json()["inbound_messages_stored"] == 1

    queue = session_client.get(
        "/api/v1/work-items",
        headers={"X-Agency-ID": os.environ.get("MESSAGING_WEBHOOK_AGENCY_ID", "").strip() or "webhook-unattributed"},
    ).json()
    assert queue["total"] >= 1
    assert any(i["door"] == "channel_webhook" and i["urgency"] == "high" for i in queue["items"])


def test_triage_consumes_classifier_e2(session_client, boundary_principal_factory):
    """E2: triage response carries the canonical work axes (preview-only).
    Triage resolves the SQL Agency object, so the tenant must exist."""
    boundary_principal_factory("usr_triage_e2", "agency_triage_e2")
    res = session_client.post(
        "/api/triage/message",
        json={"text": "urgent: my flight tomorrow was cancelled, need help now", "channel": "whatsapp"},
        headers={"X-Agency-ID": "agency_triage_e2"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["work_origin"] == "demand"
    assert data["work_authority"] == "explicit_user"
    assert data["urgency_class"] == "high"
    assert "returning_customer" in data and "duplicate_risk" in data
    # preview-only: nothing recorded for this agency by a triage call alone
    queue = session_client.get(
        "/api/v1/work-items", headers={"X-Agency-ID": "agency_triage_e2"}
    ).json()
    assert queue["total"] == 0


# ---------------------------------------------------------------------------
# E3 — W4 system-generated work joins the queue
# ---------------------------------------------------------------------------

def test_system_doors_registered():
    """Ghost-concierge and poison doors classify as system/exception/system."""
    for door in ("ghost_concierge", "requeue_poison"):
        item = work_intake.classify(door, agency_id=AGENCY, text=None)
        assert item["origin"] == "system", door
        assert item["intent"] == "exception", door
        assert item["authority"] == "system", door


def test_ghost_concierge_drafts_land_on_agency_queue():
    """Closed loop: a disruption evaluation with draft interventions records
    a high-urgency system item on THAT agency's queue."""
    from spine_api.services import ghost_concierge_monitor as mon

    agency = f"agency_gc_{uuid.uuid4().hex[:8]}"
    trip = {
        "id": f"trip_gc_{uuid.uuid4().hex[:8]}",
        "flight_status_updates": [
            {
                "flight_number": "XY123",
                "origin_iata": "BLR",
                "destination_iata": "DXB",
                "status": "cancelled",
                "delay_minutes": 0,
            }
        ],
    }
    wf = mon.run_ghost_concierge_for_trip(trip, agency)
    assert wf is not None
    assert wf["drafted_interventions"], "fixture must produce drafts for the wiring to fire"

    queue = work_intake.ranked_queue(agency)
    assert queue["total"] == 1
    item = queue["items"][0]
    assert item["door"] == "ghost_concierge"
    assert item["origin"] == "system"
    assert item["urgency"] == "high"
    assert item["trip_id"] == trip["id"]
    assert queue["counts"]["by_origin"]["system"] == 1

    # No interventions -> no queue spam (S3: healthy trip records nothing).
    healthy_agency = f"agency_gc_ok_{uuid.uuid4().hex[:8]}"
    ok_trip = {
        "id": f"trip_gcok_{uuid.uuid4().hex[:8]}",
        "flight_status_updates": [
            {
                "flight_number": "OK1",
                "origin_iata": "BLR",
                "destination_iata": "DXB",
                "status": "scheduled",
                "delay_minutes": 0,
            }
        ],
    }
    mon.run_ghost_concierge_for_trip(ok_trip, healthy_agency)
    assert work_intake.ranked_queue(healthy_agency)["total"] == 0


def test_poison_transition_records_system_scope_not_tenant_queue():
    """Closed loop: poison side-effects record under SYSTEM_WORK_SCOPE and are
    NOT visible on any tenant queue (the agency-less ownership boundary in
    agent_requeue_jobs.list_poisoned is preserved)."""
    from spine_api.services.agent_requeue_jobs import _emit_poisoned_side_effects
    from spine_api.services.work_intake import SYSTEM_WORK_SCOPE

    trip_id = f"trip_poison_{uuid.uuid4().hex[:8]}"
    _emit_poisoned_side_effects(
        job_id=f"job_{uuid.uuid4().hex[:8]}",
        error="boom: synthetic test failure",
        info={"trip_id": trip_id, "attempts": 3, "payload": "{}"},
    )

    system_queue = work_intake.ranked_queue(SYSTEM_WORK_SCOPE)
    assert system_queue["total"] >= 1
    item = next(i for i in system_queue["items"] if i["door"] == "requeue_poison")
    assert item["origin"] == "system"
    assert item["urgency"] == "high"
    assert item["trip_id"] == trip_id
    # the raw error string must not leak into the classified record
    assert "boom" not in work_intake._agency_path(SYSTEM_WORK_SCOPE).read_text(encoding="utf-8")

    # S3 boundary: an unrelated tenant queue never sees the poison item.
    tenant = work_intake.ranked_queue(f"agency_never_{uuid.uuid4().hex[:8]}")
    assert tenant["total"] == 0


# ---------------------------------------------------------------------------
# Second door tranche (map §9.1): collection_submit, proposal_acceptance,
# group_share, public_checker, operator_action, knowledge_admin
# ---------------------------------------------------------------------------

def test_second_tranche_door_contracts():
    """Each newly wired door classifies on the axes the map specifies."""
    expectations = {
        "collection_submit": ("demand", "info", "explicit_user"),
        "proposal_acceptance": ("demand", "decision", "explicit_user"),
        "group_share": ("demand", "decision", "explicit_user"),
        "public_checker": ("demand", "new_demand", "explicit_user"),
        "operator_action": ("operator", "meta", "operator"),
        "knowledge_admin": ("operator", "meta", "operator"),
    }
    for door, (origin, intent, authority) in expectations.items():
        item = work_intake.classify(door, agency_id=AGENCY, text=None)
        assert item["origin"] == origin, door
        assert item["intent"] == intent, door
        assert item["authority"] == authority, door


def test_operator_action_patch_closed_loop(session_client, boundary_principal_factory):
    """Closed loop: an operator edit that triggers auto-reassessment records an
    operator-classified work item on the agency queue."""
    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_opact_{suffix}"
    boundary_principal_factory(f"usr_opact_{suffix}", agency)

    created = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "manual_paste",
            "raw_text": "Couple to Kyoto in late March, budget 4000 USD total.",
            "customer_name": f"Op Act {suffix}",
            "strict_leakage": False,
        },
        headers={"X-Agency-ID": agency},
    )
    assert created.status_code == 200
    trip_id = created.json()["trip_id"]

    patched = session_client.patch(
        f"/trips/{trip_id}",
        json={"destination": "Osaka"},
        headers={"X-Agency-ID": agency, "X-User-ID": f"usr_opact_{suffix}"},
    )
    assert patched.status_code == 200

    queue = work_intake.ranked_queue(agency)
    doors = {i["door"] for i in queue["items"]}
    assert "inbound_parse" in doors  # first tranche (setup door)
    assert "operator_action" in doors
    op_item = next(i for i in queue["items"] if i["door"] == "operator_action")
    assert op_item["origin"] == "operator"
    assert op_item["authority"] == "operator"
    assert op_item["trip_id"] == trip_id
    assert op_item["run_id"]  # linked to the queued reassessment run


# ---------------------------------------------------------------------------
# Third tranche (map §11): social_inbound, checker_route_request, multimodal,
# recovery_escalation
# ---------------------------------------------------------------------------

def test_third_tranche_door_contracts():
    expectations = {
        "social_inbound": ("demand", "new_demand", "explicit_user"),
        "checker_route_request": ("demand", "new_demand", "explicit_user"),
        "multimodal": ("demand", "info", "explicit_user"),
        "recovery_escalation": ("system", "exception", "system"),
    }
    for door, (origin, intent, authority) in expectations.items():
        item = work_intake.classify(door, agency_id=AGENCY, text=None)
        assert item["origin"] == origin, door
        assert item["intent"] == intent, door
        assert item["authority"] == authority, door


def test_multimodal_voice_note_door_closed_loop(session_client):
    """Closed loop: a voice-note transcript records a demand/info item; the
    transcript text itself never lands in the store."""
    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_mm_{suffix}"
    transcript = "Hi, this is Ravi, we need an urgent visa check for tomorrow's flight to Colombo"
    res = session_client.post(
        "/api/v1/multimodal/voice-note",
        json={"transcript_text": transcript, "speaker_name": f"Ravi {suffix}"},
        headers={"X-Agency-ID": agency},
    )
    assert res.status_code == 200

    queue = work_intake.ranked_queue(agency)
    assert queue["total"] == 1
    item = queue["items"][0]
    assert item["door"] == "multimodal"
    assert item["channel"] == "voice_note"
    assert item["urgency"] == "high"  # "urgent ... tomorrow" in the transcript
    # the raw transcript (and speaker name) never persists
    stored = work_intake._agency_path(agency).read_text(encoding="utf-8")
    assert "Colombo" not in stored and "Ravi" not in stored


def test_social_inbound_door_closed_loop(session_client):
    """Closed loop: a social DM records a demand/new_demand item."""
    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_soc_{suffix}"
    res = session_client.post(
        "/api/v1/inbox/parse_social",
        json={
            "raw_text": "Hey! Planning a Bali trip for 2 in June, no rush, what would it cost?",
            "creator_id": f"creator_{suffix}",
            "source": "instagram_dm",
        },
        headers={"X-Agency-ID": agency},
    )
    assert res.status_code == 200

    queue = work_intake.ranked_queue(agency)
    assert queue["total"] == 1
    item = queue["items"][0]
    assert item["door"] == "social_inbound"
    assert item["origin"] == "demand"
    assert item["intent"] == "new_demand"
    assert item["urgency"] == "low"  # "no rush" in the DM
    assert item["channel"] == "instagram_dm"

