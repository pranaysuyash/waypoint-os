"""
tools/sim4_wave3_probes.py — Sim #4 targeted wave-3 probes (beta posture lane).

Closes the grading gaps left by wave 2: ask-loop answers with the trip's real
question field names → reassess (P30), stage-gated document uploads (P44-46),
PAN-at-rest scan for the adversarial trip (P10, beta posture), group public
share page (P5), and the memory-forget door vs Art.17 erasure (P27).

Usage:
    SIM_BACKEND_URL=http://127.0.0.1:8010 SIM4_EVIDENCE_DIR=Docs/sims/assets/sim4/evidence_beta \
        .venv/bin/python tools/sim4_wave3_probes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.sim4_runner import EVIDENCE, SimClient, get_trip, pack  # noqa: E402
from tools.sim4_sims import PNG_1PX, ZIP_BYTES  # noqa: E402


def _ev(sim: str) -> list:
    return json.loads((EVIDENCE / f"sim4_{sim}_evidence.json").read_text())


def _last(log: list, step: str) -> dict:
    out = {}
    for e in log:
        if e.get("step") == step:
            out = e
    return out


def main() -> int:
    client = SimClient()
    client.login()

    # ── G: answers with the real field names, then reassess ─────────────
    g = _ev("G")
    send = _last(g, "G-send-direct")
    token = (send.get("response") or {}).get("token")
    trip_id = (send.get("response") or {}).get("trip_id")
    if token and trip_id:
        page = requests.get(f"{client.backend}/api/public/asks/{token}", timeout=60).json()
        fields = [q.get("field_name") for q in page.get("questions") or []]
        client.log.append({"step": "W3-G-question-fields", "fields": fields})
        answers = []
        canned = {
            "date_window": "arriving nov 16 evening, leaving nov 19 morning",
            "origin_city": "kolkata",
            "trip_purpose": "45th anniversary pilgrimage for my parents",
        }
        for f in fields:
            if f in canned:
                answers.append({"field_name": f, "answer": canned[f]})
        r = requests.post(f"{client.backend}/api/public/asks/{token}/answers",
                          json={"answers": answers, "respondent_name": "Priyanka Sen"}, timeout=60)
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text[:300]}
        client.log.append({"step": "W3-G-answers-post", "request": {"answers": answers, "auth": False},
                           "status": r.status_code, "response": body})
        t_after = get_trip(client, trip_id)
        client.log.append({"step": "W3-G-after-answers", "packet_summary": pack(t_after),
                           "traveler_answers_raw": t_after.get("traveler_answers")})
        client.call("W3-G-reassess", "POST", f"/trips/{trip_id}/reassess", json={})
        import time
        time.sleep(20)
        t_re = get_trip(client, trip_id)
        client.log.append({"step": "W3-G-after-reassess", "packet_summary": pack(t_re),
                           "traveler_answers_raw": t_re.get("traveler_answers")})

    # ── K: advance stage, then exercise the documents door ──────────────
    k = _ev("K")
    k_trip = None
    for e in k:
        if e.get("step", "").startswith("K1-poll"):
            k_trip = (e.get("response") or {}).get("trip_id") or k_trip
    if k_trip:
        client.call("W3-K-stage-proposal", "PATCH", f"/trips/{k_trip}/stage",
                    json={"target_stage": "proposal", "reason": "sim4-K: passports needed for VoA paperwork"})

        def upload(step: str, filename: str, data: bytes, mime: str) -> dict:
            r = client.s.post(f"{client.backend}/trips/{k_trip}/documents",
                              files={"file": (filename, data, mime)},
                              data={"document_type": "passport"}, timeout=120)
            try:
                body = r.json()
            except ValueError:
                body = {"raw": r.text[:300]}
            return client._record(step, {"method": "POST", "path": f"/trips/{k_trip}/documents",
                                         "filename": filename, "mime": mime, "bytes": len(data)}, r, body)

        up1 = upload("W3-K-upload-valid-png", "farhan_passport.png", PNG_1PX, "image/png")
        upload("W3-K-upload-zip-as-png", "farhan_passport2.png", ZIP_BYTES, "image/png")
        upload("W3-K-upload-duplicate", "farhan_passport_again.png", PNG_1PX, "image/png")
        doc = up1.get("response") or {}
        doc_id = doc.get("document_id") or doc.get("id") or ((doc.get("document") or {}).get("id"))
        client.log.append({"step": "W3-K-upload-summary", "doc_id": doc_id,
                           "keys": sorted(doc.keys())[:12] if isinstance(doc, dict) else None})
        if doc_id:
            client.call("W3-K-extract", "POST", f"/trips/{k_trip}/documents/{doc_id}/extract", json={})
            client.call("W3-K-accept", "POST", f"/trips/{k_trip}/documents/{doc_id}/accept",
                        json={"note": "sim4-K accepted"})
            client.call("W3-K-download-url", "GET", f"/trips/{k_trip}/documents/{doc_id}/download-url")
        client.call("W3-K-list", "GET", f"/trips/{k_trip}/documents")

    # ── C: PAN at rest for the beta-lane adversarial trip ───────────────
    c = _ev("C")
    c_trip = (_last(c, "C1-final-state") or {}).get("trip_id")
    client.log.append({"step": "W3-C-trip-id", "trip_id": c_trip})

    # ── A: public group share page ──────────────────────────────────────
    a = _ev("A")
    inv = (_last(a, "A-invites") or {}).get("response") or {}
    tok = None
    for it in (inv.get("invites") or inv.get("passengers") or inv.get("items") or []):
        tok = (it or {}).get("token") or (it or {}).get("share_token") or tok
    client.log.append({"step": "W3-A-invite-keys", "keys": sorted(inv.keys())[:14], "token_present": bool(tok)})
    if tok:
        r = requests.get(f"{client.backend}/api/v1/group/token/{tok}", timeout=60)
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text[:300]}
        client.log.append({"step": "W3-A-public-share", "request": {"auth": False},
                           "status": r.status_code, "response": body})

    # ── F: standalone memory-forget door (what erasure should have called) ─
    client.call("W3-F-memory-forget", "POST", "/api/v1/customers/memory/forget",
                json={"customer_id": "cust_meera.krishnan.sim4@waypointtest.dev"})
    client.call("W3-F-lookup-after-forget", "GET",
                "/api/v1/customers/memory?email=meera.krishnan.sim4@waypointtest.dev")

    out = client.dump("W3")
    print("wave-3 evidence:", out, len(client.log), "steps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
