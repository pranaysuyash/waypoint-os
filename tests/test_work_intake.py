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


# ---------------------------------------------------------------------------
# Fourth W4 tranche (map §13): disruption_feed (IROPS watch),
# supervisor_escalation (AgentSupervisor terminal poison),
# stale_run_timeout (RunLedger stale sweep)
# ---------------------------------------------------------------------------

def test_fourth_tranche_door_contracts():
    """The three new W4 writers declare their class at the seam."""
    expected = {
        "disruption_feed": ("world", "exception", "system"),
        "supervisor_escalation": ("system", "exception", "system"),
        "stale_run_timeout": ("system", "exception", "system"),
    }
    for door, (origin, intent, authority) in expected.items():
        item = work_intake.classify(door, agency_id=AGENCY, text=None)
        assert (item["origin"], item["intent"], item["authority"]) == (origin, intent, authority), door


def test_door_display_covers_every_door():
    """Operator-display exhaustiveness (map §15): every registered door has a
    human headline, so a new door cannot ship jargon. Unknown doors degrade
    to a title-cased name (never raw underscores, never a raise)."""
    for door in work_intake.DOOR_CONTRACTS:
        assert door in work_intake.DOOR_DISPLAY, f"door {door!r} has no DOOR_DISPLAY entry"
        item = work_intake.classify(door, agency_id=AGENCY, text=None)
        d = work_intake.display_for(item)
        assert d["headline"], door
        assert "_" not in d["headline"], door
    # channel substitution composes into the headline for channel-template doors
    d = work_intake.display_for(
        {"door": "channel_webhook", "origin": "demand", "intent": "info", "authority": "explicit_user", "channel": "whatsapp"}
    )
    assert d["headline"] == "WhatsApp message received"
    # unknown door degrades gracefully (no raise, no underscores)
    d2 = work_intake.display_for({"door": "some_future_door", "origin": "system", "intent": "meta", "authority": "system"})
    assert d2["headline"] == "Some Future Door"


def test_actor_display_classes():
    """Actor vocabulary (map §15.3): system slugs map to human labels; user
    UUIDs resolve via the router-provided actor_label; raw UUIDs NEVER reach
    prose (unresolved ones drop the 'by' line); emails pass through."""
    item = {"door": "run", "origin": "demand", "intent": "new_demand", "authority": "operator"}
    # system slug → ACTOR_DISPLAY
    d = work_intake.display_for({**item, "actor": "irops_watch"})
    assert d["meta"] == ["by the disruption watch"]
    # router-resolved user name
    d = work_intake.display_for({**item, "actor": "323468de-ba3d-437b-aa10-35b281a0c6a6"}, actor_label="New User")
    assert d["meta"] == ["by New User"]
    # unresolved UUID → no 'by' line (id stays on the entry, not in prose)
    d = work_intake.display_for({**item, "actor": "323468de-ba3d-437b-aa10-35b281a0c6a6"})
    assert not any("by " in m for m in d["meta"])
    # email actor passes through
    d = work_intake.display_for({**item, "actor": "op@agency.test"})
    assert d["meta"] == ["by op@agency.test"]
    # supervisor prefixed slug degrades to raw (not a UUID, not mapped) —
    # acceptable: it is a named agent, and the map is the extension point
    d = work_intake.display_for({**item, "actor": "agent_supervisor:test_agent"})
    assert d["meta"] == ["by agent_supervisor:test_agent"]


def test_ranked_queue_collapses_entity_bound_runs_honestly():
    """Run collapse (map §15.3): identical OPEN entity-bound items share one
    row (group_count=N, newest first); claimed/unbound items never collapse;
    every count stays the uncollapsed actionable/log truth."""
    agency = f"agency_collapse_{uuid.uuid4().hex[:8]}"
    trip_id = f"trip_collapse_{uuid.uuid4().hex[:8]}"
    for _ in range(3):
        work_intake.classify_and_record(
            "operator_action", agency_id=agency, trip_id=trip_id, text=None
        )
    # claimed sibling on the same trip must NOT collapse into the open group
    claimed = work_intake.classify_and_record(
        "operator_action", agency_id=agency, trip_id=trip_id, text=None
    )
    work_intake.record_lifecycle(agency, claimed["item_id"], "claim", actor="op@agency.test")
    # unbound item with the same door must NOT collapse
    work_intake.classify_and_record("operator_action", agency_id=agency, text=None)

    queue = work_intake.ranked_queue(agency)
    rows = [i for i in queue["items"] if i["door"] == "operator_action"]
    grouped = [i for i in rows if i.get("group_count", 1) > 1]
    assert len(grouped) == 1 and grouped[0]["group_count"] == 3
    assert grouped[0]["trip_id"] == trip_id
    # one claimed + one unbound remain separate rows
    assert len(rows) == 3
    # honesty: actionable counts ALL five items; log total = 5
    assert queue["total"] == 5 and queue["actionable"] == 5
    assert queue["counts"]["by_origin"]["operator"] == 5
    assert queue["count_basis"] == "work_item_log_total"


def test_irops_watch_disruption_records_world_item(monkeypatch):
    """Closed loop: an IROPS-watch detection records a high-urgency WORLD
    item (origin=world — the disruption is an external-world event) on the
    trip's agency queue."""
    import asyncio
    from types import SimpleNamespace

    from spine_api.persistence import AuditStore, TripStore
    from src.orchestration import irops_healer
    from src.orchestration import irops_watch_service as watch

    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_irops_{suffix}"
    trip_id = f"trip_irops_{suffix}"

    def fake_heal(**kwargs):
        return SimpleNamespace(
            incident_id=f"inc_{suffix}",
            delay_minutes=180,
            to_dict=lambda: {"incident_id": f"inc_{suffix}", "steps": []},
        )

    monkeypatch.setattr(
        irops_healer.IROPSAutoHealerEngine, "execute_healing_protocol", staticmethod(fake_heal)
    )
    monkeypatch.setattr(
        TripStore, "get_trip", lambda tid: {"id": tid, "agency_id": agency, "irops_incidents": []}
    )
    monkeypatch.setattr(TripStore, "update_trip", lambda tid, patch: None)
    monkeypatch.setattr(AuditStore, "log_event", lambda *a, **k: None)

    trip = {
        "trip_id": trip_id,
        "agency_id": agency,
        "journey_graph_nodes": [
            {
                "node_id": f"fl_{suffix}",
                "node_type": "FLIGHT",
                "title": "XY123 BLR→DXB",
                "metadata": {"disrupted": True},
            }
        ],
        "journey_graph_edges": [],
    }
    result = asyncio.run(watch._scan_trip(trip_id, trip))
    assert result is not None and result["healing_results"], "fixture must detect the disruption"

    queue = work_intake.ranked_queue(agency)
    item = next(i for i in queue["items"] if i["door"] == "disruption_feed")
    assert item["origin"] == "world"
    assert item["intent"] == "exception"
    assert item["authority"] == "system"
    assert item["urgency"] == "high"
    assert item["trip_id"] == trip_id
    assert item["actor"] == "irops_watch"


def test_supervisor_terminal_poison_records_tenant_item(monkeypatch):
    """Closed loop: an agent work item that terminally poisons under the
    AgentSupervisor records a high-urgency system item on the TRIP's agency
    queue (tenanted — unlike the agency-less requeue queue)."""
    from types import SimpleNamespace

    from spine_api.persistence import TripStore
    from src.agents.runtime import (
        AgentSupervisor,
        InMemoryWorkCoordinator,
        RetryPolicy,
        WorkItem,
    )

    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_sup_{suffix}"
    trip_id = f"trip_sup_{suffix}"
    monkeypatch.setattr(TripStore, "get_trip", lambda tid: {"id": tid, "agency_id": agency})

    item = WorkItem(
        agent_name="test_agent",
        trip_id=trip_id,
        action="probe",
        idempotency_key=f"idem_{suffix}",
    )

    def _boom(work, repo):
        raise RuntimeError("synthetic agent failure")

    failing_agent = SimpleNamespace(
        definition=SimpleNamespace(
            name="test_agent",
            retry_policy=RetryPolicy(max_attempts=1),
            failure_contract="test_failure",
        ),
        scan=lambda repo: [item],
        execute=_boom,
    )
    supervisor = AgentSupervisor(
        registry=SimpleNamespace(agents=lambda: [failing_agent], get=lambda n: failing_agent),
        trip_repo=SimpleNamespace(),
        audit=None,
        coordinator=InMemoryWorkCoordinator(),
    )

    results = supervisor.run_once()
    assert len(results) == 1
    assert not results[0].success

    queue = work_intake.ranked_queue(agency)
    found = next(i for i in queue["items"] if i["door"] == "supervisor_escalation")
    assert found["origin"] == "system"
    assert found["urgency"] == "high"
    assert found["trip_id"] == trip_id
    assert found["actor"] == "agent_supervisor:test_agent"
    # the synthetic failure reason never persists in the classified record
    stored = work_intake._agency_path(agency).read_text(encoding="utf-8")
    assert "synthetic agent failure" not in stored


def test_stale_run_sweep_records_per_run_item(monkeypatch, tmp_path):
    """Closed loop: the heartbeat-aware stale sweep records one work item per
    timed-out run, on the run's OWN agency (tenanted), with agency-less runs
    falling to the system scope."""
    import datetime as dt
    import json as _json

    from spine_api import run_ledger as rl
    from spine_api.services.work_intake import SYSTEM_WORK_SCOPE

    runs_dir = tmp_path / "runs"
    monkeypatch.setattr(rl, "RUNS_DIR", runs_dir)

    suffix = uuid.uuid4().hex[:8]
    run_id = f"run_stale_{suffix}"
    trip_id = f"trip_stale_{suffix}"
    rl.RunLedger.create(
        run_id, trip_id, stage="intake", operating_mode="standard", agency_id=AGENCY
    )

    # S3: age the fixture run past the threshold by rewriting created_at
    # (heartbeat stays absent → legacy created-age check applies).
    meta_path = runs_dir / run_id / "meta.json"
    meta = _json.loads(meta_path.read_text(encoding="utf-8"))
    meta["created_at"] = (
        dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=3600)
    ).isoformat()
    meta_path.write_text(_json.dumps(meta), encoding="utf-8")

    timed_out = rl.RunLedger.timeout_stale_runs(max_age_seconds=300)
    assert timed_out == [run_id]

    queue = work_intake.ranked_queue(AGENCY)
    item = next(i for i in queue["items"] if i["door"] == "stale_run_timeout")
    assert item["origin"] == "system"
    assert item["urgency"] == "high"
    assert item["run_id"] == run_id
    assert item["trip_id"] == trip_id
    assert item["actor"] == "run_ledger_sweep"

    # Agency-less run → system scope (observable, not on any tenant queue).
    run2 = f"run_stale2_{suffix}"
    rl.RunLedger.create(run2, None, stage="intake", operating_mode="standard")
    meta2_path = runs_dir / run2 / "meta.json"
    meta2 = _json.loads(meta2_path.read_text(encoding="utf-8"))
    meta2["created_at"] = meta["created_at"]
    meta2_path.write_text(_json.dumps(meta2), encoding="utf-8")

    timed_out2 = rl.RunLedger.timeout_stale_runs(max_age_seconds=300)
    assert timed_out2 == [run2]
    system_queue = work_intake.ranked_queue(SYSTEM_WORK_SCOPE)
    found2 = next(
        i
        for i in system_queue["items"]
        if i["door"] == "stale_run_timeout" and i["run_id"] == run2
    )
    assert found2["trip_id"] is None


# ---------------------------------------------------------------------------
# Outcome-state lifecycle (map §14): event-sourced claim/dismiss/resolve
# ---------------------------------------------------------------------------

def test_lifecycle_state_machine_unit():
    """Unit: transitions validate; terminal states reject; unknown items raise;
    events append without mutating the original item line."""
    agency = f"agency_lc_{uuid.uuid4().hex[:8]}"
    item = work_intake.classify_and_record(
        "inbound_parse", agency_id=agency, text="lifecycle probe", contact=f"lc{uuid.uuid4().hex[:6]}@x.com"
    )
    iid = item["item_id"]

    r1 = work_intake.record_lifecycle(agency, iid, "claim", actor="op@agency.test")
    assert r1["previous_state"] == "open" and r1["state"] == "claimed"
    assert r1["claimed_by"] == "op@agency.test"

    r2 = work_intake.record_lifecycle(agency, iid, "unclaim", actor="op@agency.test")
    assert r2["state"] == "open"

    work_intake.record_lifecycle(agency, iid, "claim", actor="op2@agency.test")
    r4 = work_intake.record_lifecycle(agency, iid, "resolve", actor="op2@agency.test", note="handled via call")
    assert r4["previous_state"] == "claimed" and r4["state"] == "resolved"

    # terminal: no further transitions
    with pytest.raises(ValueError):
        work_intake.record_lifecycle(agency, iid, "claim", actor="op@agency.test")
    with pytest.raises(ValueError):
        work_intake.record_lifecycle(agency, iid, "unclaim", actor="op@agency.test")

    # unknown item / unknown action
    with pytest.raises(KeyError):
        work_intake.record_lifecycle(agency, "wi_missing", "claim", actor="op@agency.test")
    with pytest.raises(ValueError):
        work_intake.record_lifecycle(agency, iid, "explode", actor="op@agency.test")

    # append-only discipline: the original item line is untouched; events are
    # separate records (record_type=lifecycle_event) in the same log.
    raw = [
        json.loads(line)
        for line in work_intake._agency_path(agency).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    item_records = [r for r in raw if r.get("item_id") == iid]
    assert len(item_records) == 1 and "state" not in item_records[0]
    events = [r for r in raw if r.get("record_type") == "lifecycle_event"]
    assert [e["action"] for e in events] == ["claim", "unclaim", "claim", "resolve"]
    assert events[-1]["note"] == "handled via call"


def test_ranked_queue_lifecycle_aware_and_honest():
    """Resolved/dismissed leave the ranked list; totals stay log totals;
    class counts describe actionable work only."""
    agency = f"agency_lq_{uuid.uuid4().hex[:8]}"
    open_item = work_intake.classify_and_record(
        "inbound_parse", agency_id=agency, text="queue me", contact=f"lq{uuid.uuid4().hex[:6]}@x.com"
    )
    done_item = work_intake.classify_and_record(
        "inbound_parse", agency_id=agency, text="finish me fast", contact=f"lq2{uuid.uuid4().hex[:6]}@x.com"
    )
    dismissed_item = work_intake.classify_and_record(
        "inbound_parse", agency_id=agency, text="drop me", contact=f"lq3{uuid.uuid4().hex[:6]}@x.com"
    )
    claimed_item = work_intake.classify_and_record(
        "inbound_parse", agency_id=agency, text="hold me", contact=f"lq4{uuid.uuid4().hex[:6]}@x.com"
    )
    work_intake.record_lifecycle(agency, done_item["item_id"], "resolve", actor="op@agency.test")
    work_intake.record_lifecycle(agency, dismissed_item["item_id"], "dismiss", actor="op@agency.test")
    work_intake.record_lifecycle(agency, claimed_item["item_id"], "claim", actor="op@agency.test")

    queue = work_intake.ranked_queue(agency)
    visible_ids = {i["item_id"] for i in queue["items"]}
    assert visible_ids == {open_item["item_id"], claimed_item["item_id"]}
    by_id = {i["item_id"]: i for i in queue["items"]}
    assert by_id[claimed_item["item_id"]]["state"] == "claimed"
    assert by_id[claimed_item["item_id"]]["claimed_by"] == "op@agency.test"

    # honest counts: total = everything ever recorded; by_state covers all
    assert queue["total"] == 4
    assert queue["actionable"] == 2
    assert queue["counts"]["by_state"] == {"open": 1, "claimed": 1, "resolved": 1, "dismissed": 1}
    # class counts describe actionable work (2), not the log total (4)
    assert sum(queue["counts"]["by_origin"].values()) == 2
    assert queue["count_basis"] == "work_item_log_total"


def test_work_item_action_endpoint_closed_loop(session_client):
    """PATCH on the existing router: claim -> visible as claimed; resolve ->
    leaves the ranked list while total stays honest; 404 unknown/other-tenant;
    409 invalid transition; 422 bad action."""
    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_act_{suffix}"
    other = f"agency_act2_{suffix}"
    item = work_intake.classify_and_record(
        "channel_webhook", agency_id=agency, text="action surface probe"
    )
    iid = item["item_id"]
    headers = {"X-Agency-ID": agency}

    res = session_client.patch(f"/api/v1/work-items/{iid}", json={"action": "claim"}, headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["state"] == "claimed" and body["previous_state"] == "open"

    queue = session_client.get("/api/v1/work-items", headers=headers).json()
    entry = next(i for i in queue["items"] if i["item_id"] == iid)
    assert entry["state"] == "claimed"

    # tenant isolation: the other agency cannot act on this item
    cross = session_client.patch(
        f"/api/v1/work-items/{iid}", json={"action": "resolve"}, headers={"X-Agency-ID": other}
    )
    assert cross.status_code == 404

    res = session_client.patch(
        f"/api/v1/work-items/{iid}", json={"action": "resolve", "note": "handled"}, headers=headers
    )
    assert res.status_code == 200
    queue2 = session_client.get("/api/v1/work-items", headers=headers).json()
    assert all(i["item_id"] != iid for i in queue2["items"]), "resolved item leaves the ranked list"
    assert queue2["total"] == 1 and queue2["actionable"] == 0
    assert queue2["counts"]["by_state"]["resolved"] == 1

    # terminal state -> 409; unknown id -> 404; bad action -> 422
    assert (
        session_client.patch(f"/api/v1/work-items/{iid}", json={"action": "claim"}, headers=headers).status_code
        == 409
    )
    assert (
        session_client.patch(
            "/api/v1/work-items/wi_nope", json={"action": "claim"}, headers=headers
        ).status_code
        == 404
    )
    assert (
        session_client.patch(
            f"/api/v1/work-items/{iid}", json={"action": "explode"}, headers=headers
        ).status_code
        == 422
    )


def test_include_done_history_reader(session_client):
    """?include_done=true appends resolved/dismissed items (state-annotated)
    AFTER the actionable list; the default view is unchanged."""
    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_hist_{suffix}"
    open_item = work_intake.classify_and_record(
        "inbound_parse", agency_id=agency, text="history probe", contact=f"h{suffix}@x.com"
    )
    done_item = work_intake.classify_and_record(
        "inbound_parse", agency_id=agency, text="already handled urgent", contact=f"h2{suffix}@x.com"
    )
    work_intake.record_lifecycle(agency, done_item["item_id"], "resolve", actor="op@agency.test")

    headers = {"X-Agency-ID": agency}
    default_view = session_client.get("/api/v1/work-items", headers=headers).json()
    assert [i["item_id"] for i in default_view["items"]] == [open_item["item_id"]]
    assert default_view["actionable"] == 1

    history_view = session_client.get(
        "/api/v1/work-items?include_done=true", headers=headers
    ).json()
    ids = [i["item_id"] for i in history_view["items"]]
    # done item appended after the actionable one, state-annotated
    assert ids == [open_item["item_id"], done_item["item_id"]]
    done_entry = history_view["items"][1]
    assert done_entry["state"] == "resolved"
    # actionable count and totals identical in both views
    assert history_view["actionable"] == 1
    assert history_view["total"] == default_view["total"] == 2


# ---------------------------------------------------------------------------
# Operator display projection (2026-10-25): read-time headline/meta composition
# ---------------------------------------------------------------------------

def test_display_for_channel_aware_headlines():
    """Channel-sensitive doors name the channel in the headline and do not
    repeat it in the meta line; channel-less items degrade honestly."""
    item = work_intake.classify(
        "channel_webhook", agency_id=AGENCY, channel="whatsapp"
    )
    out = work_intake.display_for(item)
    assert out["headline"] == "WhatsApp message received"
    assert out["meta"] == []

    no_channel = work_intake.classify("channel_webhook", agency_id=AGENCY)
    assert work_intake.display_for(no_channel)["headline"] == "Message received"

    unknown_channel = work_intake.classify(
        "channel_webhook", agency_id=AGENCY, channel="pigeon_post"
    )
    out_unknown = work_intake.display_for(unknown_channel)
    assert out_unknown["headline"] == "Pigeon Post message received"


def test_display_for_meta_composition():
    """Meta carries channel (when the headline did not), the bound-entity
    label, and the actor; unresolvable trips stay off the prose line."""
    item = work_intake.classify(
        "inbound_parse",
        agency_id=AGENCY,
        channel="email",
        trip_id="trip_abc123",
        actor=None,
    )
    out = work_intake.display_for(item, trip_label="Bali · 10 June 2027 to 17 June 2027")
    assert out["headline"] == "New trip request"
    assert out["meta"] == ["Email", "Trip — Bali · 10 June 2027 to 17 June 2027"]

    unresolved = work_intake.display_for(item, trip_label=None)
    assert unresolved["meta"] == ["Email"]  # raw trip id stays on the entry, not in prose

    operator_item = work_intake.classify(
        "operator_action", agency_id=AGENCY, trip_id="trip_abc123", actor="op-7f3a"
    )
    out_op = work_intake.display_for(operator_item, trip_label="Bali")
    assert out_op["headline"] == "Operator updated a trip"
    assert out_op["meta"] == ["Trip — Bali", "by op-7f3a"]


def test_display_for_unknown_door_degrades_not_raises():
    """Display can never fail a queue read: an unregistered door (only possible
    via a hand-written legacy row) renders a title-cased fallback."""
    legacy = {"door": "old_door_gone", "origin": "demand", "intent": "info",
              "authority": "explicit_user"}
    out = work_intake.display_for(legacy)
    assert out["headline"] == "Old Door Gone"


def test_display_projection_contains_no_raw_contact_text():
    """PII honesty: the display projection derives from axes only — it can
    never leak the traveler text or contact that classification stripped."""
    item = work_intake.classify(
        "inbound_parse",
        agency_id=AGENCY,
        text="urgent Bali trip, email me at secret.person@example.com or +1 555 010 9999",
        contact="secret.person@example.com",
    )
    out = work_intake.display_for(item)
    blob = json.dumps(out)
    assert "secret.person@example.com" not in blob
    assert "5550109999" not in blob and "555 010 9999" not in blob


def test_work_items_router_serves_display_projection(session_client):
    """The queue endpoint composes headline/meta at READ time: a row written
    before the display vocabulary existed still renders a human headline, and
    bound trips resolve through the canonical field resolver to
    'Trip — destination · date window'."""
    suffix = uuid.uuid4().hex[:8]
    agency = f"agency_disp_{suffix}"
    trip_id = f"trip_disp_{suffix}"
    from spine_api.persistence import TripStore

    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": agency,
            "source": "pytest",
            "status": "assigned",
            "extracted": {
                "facts": {
                    "destination_candidates": {"value": ["Bali"], "authority_level": "explicit_user"},
                    "date_window": {"value": "10 June 2027 to 17 June 2027", "authority_level": "explicit_user"},
                }
            },
        }
    )
    work_intake.classify_and_record(
        "inbound_parse",
        agency_id=agency,
        channel="email",
        trip_id=trip_id,
        contact=f"d{suffix}@x.com",
    )

    headers = {"X-Agency-ID": agency}
    view = session_client.get("/api/v1/work-items", headers=headers).json()
    entry = view["items"][0]
    assert entry["headline"] == "New trip request"
    assert entry["meta"][0] == "Email"
    assert any(m.startswith("Trip — Bali") for m in entry["meta"]), entry["meta"]

    # Missing trip: label degrades to nothing human — no opaque id in prose.
    ghost = work_intake.classify_and_record(
        "inbound_parse",
        agency_id=agency,
        channel="email",
        trip_id="trip_never_existed",
        contact=f"g{suffix}@x.com",
    )
    view2 = session_client.get("/api/v1/work-items", headers=headers).json()
    ghost_entry = next(i for i in view2["items"] if i["item_id"] == ghost["item_id"])
    assert not any(m.startswith("Trip —") for m in ghost_entry["meta"])
    assert ghost_entry["trip_id"] == "trip_never_existed"  # raw id stays on the entry
