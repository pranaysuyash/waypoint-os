"""
tools/sim4_sims.py — the eleven Sim #4 scenario implementations.

Called only through tools/sim4_runner.py (which owns auth, evidence, UI
shots). Every step is recorded into the client's evidence log; assertions are
NOT hard failures — a wrong result is evidence, recorded and graded later in
Docs/sims/SIM4_RESULTS_2026-10-21.md against the design predictions P1..P47.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import requests

from tools.sim3_runner import TEST_PASSWORD, TEST_USER  # single credential source
from tools.sim4_runner import VOICES, SimClient, find_trip, get_trip, pack, submit_and_poll

FRONTEND = "http://localhost:3005"

# Canonical 1x1 transparent PNG (valid magic bytes, valid IHDR/IDAT/IEND).
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
ZIP_BYTES = b"PK\x03\x04" + b"\x00" * 64  # real zip magic, wrong content type


def _fetch_bff_session() -> requests.Session:
    s = requests.Session()
    r = s.post(f"{FRONTEND}/api/auth/login",
               json={"email": TEST_USER, "password": TEST_PASSWORD}, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"bff login failed: {r.status_code}")
    return s


def _record_bff(client: SimClient, step: str, method: str, path: str, **kw) -> None:
    """Call the product BFF (deny-by-default) and record it as evidence."""
    bff = getattr(client, "_bff", None)
    if bff is None:
        bff = client._bff = _fetch_bff_session()
    r = bff.request(method, f"{FRONTEND}{path}", timeout=90, **kw)
    try:
        body = r.json()
    except ValueError:
        body = {"raw": r.text[:400]}
    client.log.append({"step": step, "request": {"via": "bff", "method": method, "path": path,
                                                 **({"json": kw.get("json")} if kw.get("json") else {})},
                       "status": r.status_code, "response": body})


def _public_get(step: str, url: str) -> dict:
    """Unauthenticated fetch (fresh session, no cookies) — the traveler view."""
    r = requests.get(url, timeout=60)
    try:
        body = r.json()
    except ValueError:
        body = {"raw": r.text[:400]}
    return {"step": step, "request": {"via": "public", "url": url, "auth": False},
            "status": r.status_code, "response": body}


# ────────────────────────────── A: group / MICE ──────────────────────────────

def run_sim_A(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, _ = submit_and_poll(client, "A1", VOICES["A1"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "A-abort", "reason": "no trip_id"})
        return
    trip = get_trip(client, trip_id)
    client.log.append({"step": "A1-packet", "packet_summary": pack(trip)})

    # Group door: invite tokens per passenger (2 of the 12 is enough to grade
    # the mechanics; all writes additive).
    inv = client.call("A-invites", "POST", f"/api/v1/group/{trip_id}/invites", json={
        "trip_id": trip_id,
        "passengers": [
            {"name": "Kavya Nair", "email": "kavya.nair.sim4@waypointtest.dev"},
            {"name": "Team Member Two", "email": "team.two.sim4@waypointtest.dev"},
        ],
    })
    token = None
    items = ((inv["response"] or {}).get("invites") or (inv["response"] or {}).get("items") or [])
    for it in items if isinstance(items, list) else []:
        token = (it or {}).get("token") or token
        break
    client.log.append({"step": "A-invite-summary", "token_present": bool(token),
                       "count": len(items) if isinstance(items, list) else None})
    if token:
        client.log.append(_public_get("A-public-share", f"{client.backend}/api/v1/group/token/{token}"))

    # Supplier soft-hold honesty: no real contract exists in this env.
    client.call("A-soft-hold-no-contract", "POST", "/api/v1/supplier/inventory/soft-hold", json={
        "contract_id": "SIM4-NONEXISTENT-CONTRACT",
        "room_type": "twin shared",
        "check_in": "2027-02-11",
        "check_out": "2027-02-14",
        "guest_name": "Kavya Nair",
    })
    if not skip_ui:
        client.shot("A", f"http://localhost:3005/trips/{trip_id}", "trip_A_group")


# ─────────────────────────── B: corporate policy ─────────────────────────────

def run_sim_B(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    client.call("B-policy-rules", "GET", "/api/v1/corporate/policy-rules")
    status, _ = submit_and_poll(client, "B1", VOICES["B1"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "B-abort", "reason": "no trip_id"})
        return
    trip = get_trip(client, trip_id)
    client.log.append({"step": "B1-packet", "packet_summary": pack(trip)})
    audit = client.call("B-audit", "POST", f"/api/v1/corporate/audit-policy/{trip_id}", json={})
    client.log.append({"step": "B-audit-summary", "violations": (audit["response"] or {}).get("violations"),
                       "warnings": (audit["response"] or {}).get("warnings"),
                       "cost_source": (audit["response"] or {}).get("cost_source"),
                       "nights_source": (audit["response"] or {}).get("nights_source"),
                       "source": (audit["response"] or {}).get("source")})
    client.call("B-override", "POST", f"/api/v1/corporate/approve-policy-override/{trip_id}", json={
        "trip_id": trip_id,
        "reason": "sim4-B: VP grade entitles business class on 9h sector; line-manager signoff on file (synthetic).",
    })


# ───────────────────────────── C: adversarial ────────────────────────────────

def run_sim_C(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    # C-full: PAN + injection → expect fail-closed 422 (P10).
    d = client.call("C1-draft", "POST", "/api/drafts",
                    json={"name": VOICES["C_full"][:60], "customer_message": VOICES["C_full"]})
    draft_id = (d["response"] or {}).get("draft_id")
    acc = client.call("C1-run", "POST", "/run",
                      json={"raw_note": VOICES["C_full"], "draft_id": draft_id})
    client.log.append({"step": "C1-run-summary", "status": acc["status"],
                       "detail": (acc["response"] or {}).get("detail") if isinstance(acc["response"], dict) else acc["response"]})
    run_id = (acc["response"] or {}).get("run_id")
    if run_id:
        final = client.poll_run("C1-poll", run_id)
        client.log.append({"step": "C1-final-state", "state": final.get("state"),
                           "trip_id": final.get("trip_id"),
                           "error_message": (final.get("error_message") or "")[:400]})
    # Negative control: no trip may contain the test PAN.
    lst = client.call("C1-negative-control", "GET", "/trips?limit=200")
    blob = json.dumps(lst["response"])
    client.log.append({"step": "C1-pan-leak-check", "pan_present_in_trips": ("4111 1111 1111 1111" in blob) or ("4111111111111111" in blob.replace(" ", ""))})

    # C-inject only: must survive with budget intact (P11) and party absent (P12).
    status, _ = submit_and_poll(client, "C2", VOICES["C_inject"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if trip_id:
        trip = get_trip(client, trip_id)
        client.log.append({"step": "C2-packet", "packet_summary": pack(trip)})


# ─────────────────────── D: honeymoon → money path ───────────────────────────

def run_sim_D(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, _ = submit_and_poll(client, "D1", VOICES["D1"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "D-abort", "reason": "no trip_id"})
        return
    trip = get_trip(client, trip_id)
    client.log.append({"step": "D1-packet", "packet_summary": pack(trip)})

    q = client.call("D-quotes", "GET", f"/api/v1/trips/{trip_id}/quotes")
    client.log.append({"step": "D-quotes-summary", "quote_ready": (q["response"] or {}).get("quote_ready"),
                       "missing": (q["response"] or {}).get("missing"),
                       "quotes": (q["response"] or {}).get("quotes") or (q["response"] or {}).get("items")})

    comp = client.call("D-proposal-compile", "POST", "/api/v1/proposal-compiler/compile", json={
        "trip_id": trip_id,
        "raw_intake_text": VOICES["D1"],
        "destination": "Bali",
        "departure_date": "2026-12-08",
        "return_date": "2026-12-15",
        "traveler_count": 2,
    })
    token = None
    for key in ("token", "proposal_token", "link_token", "share_token"):
        token = (comp["response"] or {}).get(key) or token
        if token:
            break
    client.log.append({"step": "D-proposal-summary", "token_present": bool(token),
                       "response_keys": sorted((comp["response"] or {}).keys())[:12] if isinstance(comp["response"], dict) else None})
    if token:
        client.log.append(_public_get("D-public-proposal", f"{client.backend}/api/public/proposals/{token}"))
    if not skip_ui:
        client.shot("D", f"http://localhost:3005/trips/{trip_id}", "trip_D_money")


# ───────────────────────────── E: visa corridor ──────────────────────────────

def run_sim_E(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, _ = submit_and_poll(client, "E1", VOICES["E1"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "E-abort", "reason": "no trip_id"})
        return
    trip = get_trip(client, trip_id)
    client.log.append({"step": "E1-packet", "packet_summary": pack(trip)})

    client.call("E-visa-check-IN-JP", "POST", "/api/v1/visa-radar/check", json={
        "passport_country": "IN",
        "destination_country": "JP",
        "passport_expiry_date": "2027-08-15",
        "travel_date": "2027-03-25",
    })
    client.call("E-visa-check-IN-TH-contrast", "POST", "/api/v1/visa-radar/check", json={
        "passport_country": "IN",
        "destination_country": "TH",
        "passport_expiry_date": "2027-08-15",
        "travel_date": "2027-03-25",
    })
    client.call("E-trip-requirements", "GET", f"/api/v1/visa-radar/{trip_id}/requirements")


# ───────────────────────────── F: GDPR / DSR ─────────────────────────────────

def run_sim_F(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, draft_id = submit_and_poll(client, "F1", VOICES["F1"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "F-abort", "reason": "no trip_id"})
        return
    trip = get_trip(client, trip_id)
    client.log.append({"step": "F1-packet", "packet_summary": pack(trip)})

    client.call("F-remember", "POST", "/api/v1/customers/remember", json={
        "name": "Meera Krishnan",
        "email": "meera.krishnan.sim4@waypointtest.dev",
        "dietary_requirements": "vegetarian",
        "room_preference": "quiet, hill view",
        "source_trip_id": trip_id,
    })
    client.call("F-lookup-before", "GET", "/api/v1/customers/memory?email=meera.krishnan.sim4@waypointtest.dev")

    exp = client.call("F-data-export", "GET", f"/api/v1/trips/{trip_id}/data-export")
    blob = json.dumps(exp["response"])
    client.log.append({"step": "F-export-summary", "status": exp["status"],
                       "contains_email": "meera.krishnan.sim4@waypointtest.dev" in blob,
                       "dotted_literal_keys": '"packet.' in blob.replace("\\\"", "'")})

    era = client.call("F-erasure", "POST", f"/api/v1/trips/{trip_id}/erasure", json={
        "reason": "Art.17 request exercised in Sim #4 on synthetic data",
        "confirm": True,
    })
    client.log.append({"step": "F-erasure-summary", "status": era["status"],
                       "scrubbed_fields": (era["response"] or {}).get("scrubbed_fields"),
                       "stores": (era["response"] or {}).get("stores"),
                       "certificate": bool((era["response"] or {}).get("certificate"))})

    trip2 = get_trip(client, trip_id)
    blob2 = json.dumps(trip2)
    client.log.append({"step": "F-trip-after-erase", "email_still_present": "meera.krishnan.sim4@waypointtest.dev" in blob2,
                       "name_still_present": "Meera Krishnan" in blob2})
    client.call("F-lookup-after", "GET", "/api/v1/customers/memory?email=meera.krishnan.sim4@waypointtest.dev")
    if draft_id:
        client.call("F-draft-after-erase", "GET", f"/api/drafts/{draft_id}")


# ──────────────────────── G: ask-loop round-trip two ─────────────────────────

def run_sim_G(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, _ = submit_and_poll(client, "G1", VOICES["G1"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "G-abort", "reason": "no trip_id"})
        return
    trip = get_trip(client, trip_id)
    client.log.append({"step": "G1-packet", "packet_summary": pack(trip)})

    client.call("G-dashboard", "GET", "/followups/dashboard")

    # Operator send via the PRODUCT BFF (AUD-06 BFF mapping verification).
    _record_bff(client, "G-send-via-bff", "POST", f"/api/followups/{trip_id}/send",
                json={"recipient": "priyanka.sen.sim4@waypointtest.dev", "channel": "email"})
    # Direct send too — the ask link/token mint happens either way.
    send = client.call("G-send-direct", "POST", f"/followups/{trip_id}/send", json={
        "recipient": "priyanka.sen.sim4@waypointtest.dev", "channel": "email"})
    token = (send["response"] or {}).get("token") or (send["response"] or {}).get("ask_token")
    asks = (send["response"] or {}).get("ask_path") or (send["response"] or {}).get("link") or ""
    if not token and "/a/" in str(asks):
        token = str(asks).rsplit("/a/", 1)[-1].split("?")[0].strip('"/')
    client.log.append({"step": "G-send-summary", "status": send["status"],
                       "token_present": bool(token), "dispatch": (send["response"] or {}).get("dispatch")})

    if token:
        client.log.append(_public_get("G-public-page", f"{client.backend}/api/public/asks/{token}"))
        ans = requests.post(f"{client.backend}/api/public/asks/{token}/answers", json={
            "answers": [
                {"field_name": "travel_dates", "answer": "arriving nov 16 evening, leaving nov 19 morning"},
                {"field_name": "room_preferences", "answer": "one accessible double room, ground floor"},
            ],
            "respondent_name": "Priyanka Sen",
        }, timeout=60)
        try:
            abody = ans.json()
        except ValueError:
            abody = {"raw": ans.text[:400]}
        client.log.append({"step": "G-answers-post", "request": {"via": "public", "auth": False},
                           "status": ans.status_code, "response": abody})

    trip2 = get_trip(client, trip_id)
    client.log.append({"step": "G2-trip-after-answers", "packet_summary": pack(trip2)})
    client.call("G-reassess", "POST", f"/trips/{trip_id}/reassess", json={})
    trip3 = get_trip(client, trip_id)
    client.log.append({"step": "G3-after-reassess", "packet_summary": pack(trip3)})
    if not skip_ui:
        client.shot("G", f"http://localhost:3005/trips/{trip_id}", "trip_G_ask")


# ────────────────────── H: inbound panic + pre-departure ─────────────────────

def run_sim_H(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, _ = submit_and_poll(client, "H1", VOICES["H_seed"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "H-abort", "reason": "no trip_id"})
        return
    trip = get_trip(client, trip_id)
    client.log.append({"step": "H1-packet", "packet_summary": pack(trip)})

    client.call("H-triage", "POST", "/api/triage/message", json={
        "text": VOICES["H_inbound"], "channel": "whatsapp"})
    client.call("H-inbound-parse", "POST", "/api/v1/inbound/parse", json={
        "channel": "whatsapp_web", "raw_text": VOICES["H_inbound"], "customer_name": "Dinesh Kulkarni"})
    msgs = client.call("H-messages", "GET", f"/api/v1/trips/{trip_id}/messages")
    client.log.append({"step": "H-messages-count", "count": (msgs["response"] or {}).get("count",
                       len((msgs["response"] or {}).get("messages") or (msgs["response"] or {}).get("items") or []))})
    client.call("H-predeparture", "GET", f"/api/v1/trips/{trip_id}/pre-departure-bundle")


# ─────────────────────── I: owner money ops (Elena) ──────────────────────────

def run_sim_I(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    seed = ("shimla weekend for 2, 2 nights next month, budget 60000, from chandigarh. "
            "heritage hotel preferred.")
    status, _ = submit_and_poll(client, "I1", seed)
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "I-abort", "reason": "no trip_id"})
        return

    reg = client.call("I-mandate-register", "POST", "/api/v1/financial-ops/payment-mandates", json={
        "trip_id": trip_id,
        "customer_id": "sim4-customer-elena",
        "max_authorized_cents": 6000000,
        "purpose": "INITIAL_DEPOSIT",
        "consent_text": "I authorize Waypoint to record my deposit mandate (max Rs 60,000). Tracking only.",
        "consent_artifact_ref": "sim4-consent-artifact-1",
        "currency": "INR",
        "customer_name": "Sim Four Ops",
        "customer_email": "ops.sim4@waypointtest.dev",
        "validity_days": 30,
        "scope": "deposit",
        "idempotency_key": "sim4-mandate-idem-1",
    })
    mandate_id = ((reg["response"] or {}).get("mandate") or {}).get("mandate_id") or ((reg["response"] or {}).get("mandate") or {}).get("id")
    if mandate_id:
        client.call("I-mandate-get", "GET", f"/api/v1/financial-ops/payment-mandates/{mandate_id}")
        client.call("I-mandate-revoke", "POST", f"/api/v1/financial-ops/payment-mandates/{mandate_id}/revoke", json={
            "reason": "owner revoked after plan change (sim)"})
        client.call("I-mandate-revoke-again", "POST", f"/api/v1/financial-ops/payment-mandates/{mandate_id}/revoke", json={
            "reason": "CAS probe — must be 409"})
    client.call("I-mandate-list", "GET", f"/api/v1/financial-ops/payment-mandates?trip_id={trip_id}")

    client.call("I-commission-split", "POST", "/api/v1/settlement/commission/split", json={
        "gross_commission": 15000.0, "contractor_split_pct": 70.0})
    client.call("I-accounting-export", "GET", f"/api/v1/trips/{trip_id}/accounting-export")
    client.call("I-analytics-revenue", "GET", "/analytics/revenue")
    client.call("I-analytics-summary", "GET", "/analytics/summary")


# ───────────────────────── J: reprocess stress (4 notes) ─────────────────────

def run_sim_J(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, draft_id = submit_and_poll(client, "J1", VOICES["J1"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id or not draft_id:
        client.log.append({"step": "J-abort", "reason": "no trip_id/draft_id"})
        return
    client.call("J1-ask-generate", "POST", "/followups/generate", json={"trip_id": trip_id})
    t1 = get_trip(client, trip_id)
    client.log.append({"step": "J1-packet", "packet_summary": pack(t1)})

    merged = VOICES["J1"] + "\n\n" + VOICES["J2"]
    client.call("J2-patch-draft", "PATCH", f"/api/drafts/{draft_id}", json={"customer_message": merged})
    st2, _ = submit_and_poll(client, "J2", merged, draft_id=draft_id)
    client.log.append({"step": "J2-run-status", "status": st2.get("state") if isinstance(st2, dict) else None})
    client.log.append({"step": "J2-packet", "packet_summary": pack(get_trip(client, trip_id))})

    merged += "\n\n" + VOICES["J3"]
    client.call("J3-patch-draft", "PATCH", f"/api/drafts/{draft_id}", json={"customer_message": merged})
    submit_and_poll(client, "J3", merged, draft_id=draft_id)
    client.log.append({"step": "J3-packet", "packet_summary": pack(get_trip(client, trip_id))})

    merged += "\n\n" + VOICES["J4"]
    client.call("J4-patch-draft", "PATCH", f"/api/drafts/{draft_id}", json={"customer_message": merged})
    submit_and_poll(client, "J4", merged, draft_id=draft_id)
    t4 = get_trip(client, trip_id)
    client.log.append({"step": "J4-trip", "packet_summary": pack(t4)})
    client.log.append({"step": "J4-asks-survival", "traveler_asks_present": bool(t4.get("traveler_asks")),
                       "ask_count": len(t4.get("traveler_asks") or [])})
    if not skip_ui:
        client.shot("J", f"http://localhost:3005/trips/{trip_id}", "trip_J_supersession")


# ───────────────────────────── K: documents door ─────────────────────────────

def run_sim_K(client: SimClient, skip_ui: bool = False) -> None:
    client.login()
    status, _ = submit_and_poll(client, "K1", VOICES["K_seed"])
    trip_id = (status or {}).get("trip_id") or find_trip(client, status or {})
    if not trip_id:
        client.log.append({"step": "K-abort", "reason": "no trip_id"})
        return

    def upload(step: str, filename: str, data: bytes, mime: str) -> dict:
        r = client.s.post(
            f"{client.backend}/trips/{trip_id}/documents",
            files={"file": (filename, data, mime)},
            data={"document_type": "passport"},
            timeout=120,
        )
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text[:400]}
        return client._record(step, {"method": "POST", "path": f"/trips/{trip_id}/documents",
                                     "filename": filename, "mime": mime, "bytes": len(data)}, r, body)

    up1 = upload("K-upload-valid-png", "farhan_passport.png", PNG_1PX, "image/png")
    upload("K-upload-zip-as-png", "farhan_passport2.png", ZIP_BYTES, "image/png")
    upload("K-upload-oversize", "farhan_passport_big.png", PNG_1PX + b"\x00" * (13 * 1024 * 1024), "image/png")
    upload("K-upload-duplicate", "farhan_passport_again.png", PNG_1PX, "image/png")

    doc_id = None
    docs = (up1["response"] or {})
    for key in ("document_id", "id"):
        doc_id = docs.get(key) or doc_id
        if doc_id:
            break
    items = docs.get("documents") or docs.get("items") or []
    if not doc_id and isinstance(items, list) and items:
        doc_id = (items[0] or {}).get("id") or (items[0] or {}).get("document_id")
    client.log.append({"step": "K-upload-summary", "doc_id": doc_id,
                       "resp_keys": sorted(docs.keys())[:10] if isinstance(docs, dict) else None})
    if doc_id:
        client.call("K-extract", "POST", f"/trips/{trip_id}/documents/{doc_id}/extract", json={})
        client.call("K-accept", "POST", f"/trips/{trip_id}/documents/{doc_id}/accept", json={
            "note": "sim4-K: accepted for visa paperwork drill"})
        client.call("K-download-url", "GET", f"/trips/{trip_id}/documents/{doc_id}/download-url")
    client.call("K-documents-list", "GET", f"/trips/{trip_id}/documents")


# ───────────────────────────── P: BFF parity probe ───────────────────────────

def run_sim_P(client: SimClient, skip_ui: bool = True) -> None:
    """Deny-by-default BFF reachability for every door used by the sims.

    The BFF maps frontend keys like ``trips/{id}/quotes`` (called as
    ``/api/trips/{id}/quotes``) to backend ``api/v1/...`` paths, so every
    door is probed in BOTH shapes; only a 404 in both is a true parity gap.
    """
    doors = [
        ("GET", "followups/dashboard"),
        ("POST", "triage/message"),
        ("GET", "v1/customers/memory?email=parity@probe.invalid"),
        ("POST", "v1/visa-radar/check"),
        ("GET", "v1/corporate/policy-rules"),
        ("GET", "v1/trips/parity/data-export"),
        ("POST", "v1/trips/parity/erasure"),
        ("GET", "trips/parity/data-export"),
        ("GET", "trips/parity/accounting-export"),
        ("GET", "trips/parity/quotes"),
        ("GET", "trips/parity/pre-departure-bundle"),
        ("POST", "trips/parity/reassess"),
        ("GET", "trips/parity/passenger-rights/claims"),
        ("POST", "v1/proposal-compiler/compile"),
        ("POST", "v1/supplier/inventory/soft-hold"),
        ("GET", "v1/financial-ops/payment-mandates"),
        ("GET", "financial-ops/payment-mandates"),
        ("GET", "analytics/summary"),
        ("GET", "analytics/revenue"),
        ("GET", "v1/group/token/parity"),
        ("GET", "trips"),
    ]
    for method, door in doors:
        for prefix in ("/api/", "/api/v1/"):
            path = door
            if prefix == "/api/" and door.startswith("v1/"):
                continue  # v1/ keys are already tried under /api/v1/
            path = door.removeprefix("v1/") if prefix == "/api/v1/" else door
            kw: dict[str, Any] = {}
            if method == "POST":
                kw["json"] = {"trip_id": "parity", "text": "parity", "passport_country": "IN",
                              "destination_country": "JP", "passport_expiry_date": "2027-08-15",
                              "travel_date": "2027-03-25"}
            _record_bff(client, f"P[{method} /{door} as {prefix}]".replace("//", "/"), method, prefix + path, **kw)
