"""
tools/sim3_runner.py — Sim #3 "Four Doors" live runner (reusable tool).

Drives the real product end-to-end for the four Sim #3 scenarios:
  A. Hinglish Homecoming  — intake origin semantics (se/side), VFR, occasion
  B. Return Guest         — durable customer memory + leakage negative control
  C. Disruption Desk      — inbound message, claim engine, disposition, ghost concierge
  D. Golden Hour          — constraints, ask-traveler loop (public /a/{token}), confirmations

Auth: real login against the backend (/api/auth/login) with the canonical
test agency (newuser@test.com). All data writes are ADDITIVE — new trips,
new memory entities, no truncation/deletes.

Evidence: JSON per sim under Docs/sims/assets/sim3/evidence/ and PNG
screenshots under Docs/sims/assets/sim3/ (browser shots for the UI surfaces).

Usage:
    .venv/bin/python tools/sim3_runner.py --sim A|B|C|D|all [--skip-ui]

Screenshots require Playwright (already a repo tool dependency) and both
servers up (backend :8000, frontend :3005).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "Docs" / "sims" / "assets" / "sim3"
EVIDENCE = ASSETS / "evidence"
FRONTEND = "http://localhost:3005"
BACKEND = "http://localhost:8000"
TEST_USER = "newuser@test.com"
TEST_PASSWORD = "testpass123"

VOICES = {
    "A1": (
        "bhai bohot ho gaya cube ki life. main bangalore se hoon, diwali pe ghar "
        "jaana hai — jaipur side, mummy-papa ke saath 4 din. aur haan unke liye ek "
        "chhota sa varanasi add karna chahta hoon, 2 din. budget: ₹45,000 se zyada "
        "nahi total, flights included. dates flexible hain diwali ke aas paas."
    ),
    "A2": (
        "arre ek correction — diwali nahi, chhath ke baad karte hain trip, around "
        "nov last week. family visit hi main purpose hai, mummy-papa ko hi milna "
        "hai. baat same hai warna."
    ),
    "B1": (
        "hi — ananya here (ananya.rao.sim3@waypointtest.dev). you planned japan for "
        "me last year and it was genuinely perfect. i want something with the same "
        "feeling but vietnam this time — 10 days in march, 2 people, around $2400 "
        "excluding international flights. same kind of quiet heritage stays please."
    ),
    "C1": (
        "hi, vikram shetty here — you booked our bangkok trip (booking SIM3-WP7K2M). "
        "our flight TG318 bkk to bom yesterday got cancelled at the gate, 2 of us "
        "travelling. airline put us on a flight 19 hours later, no hotel, no meal "
        "voucher. this can't be right? what are our options, what is the airline "
        "supposed to give us?"
    ),
    "D1": (
        "hello, i'm booking for my parents — they don't use apps much so i manage "
        "everything. col. arvind sen, 72, uses a wheelchair and needs step-free "
        "access everywhere; my mother kamala sen, 68, has knee trouble so please "
        "plan a slow pace for her. they want varanasi for their 45th anniversary on "
        "november 18th, 3 nights, pure veg meals only. budget around ₹90,000 total. "
        "i can share exact travel dates once you confirm ghats access is doable for "
        "a wheelchair."
    ),
    "D2": (
        "dates: arriving nov 16 evening, leaving nov 19 morning. room: one "
        "accessible double room, ground floor preferred. extra: please book a boat "
        "that has handrails, my mother is nervous on water."
    ),
}


class SimClient:
    """Authenticated API client for the backend, with evidence capture."""

    def __init__(self) -> None:
        self.s = requests.Session()
        self.token: str | None = None
        self.agency_id: str | None = None
        self.log: list[dict] = []

    def _record(self, step: str, req: dict, resp: requests.Response, body: dict) -> dict:
        entry = {
            "step": step,
            "request": req,
            "status": resp.status_code,
            "response": body,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.log.append(entry)
        return entry

    def login(self) -> dict:
        r = self.s.post(
            f"{BACKEND}/api/auth/login",
            json={"email": TEST_USER, "password": TEST_PASSWORD},
            timeout=30,
        )
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:300]}
        self._record("login", {"url": "/api/auth/login"}, r, body)
        if r.status_code != 200:
            raise SystemExit(f"login failed: {r.status_code} {body}")
        data = body.get("data") or body
        self.token = data.get("access_token") or data.get("accessToken")
        agency = data.get("agency") or {}
        self.agency_id = agency.get("id")
        # Auth is cookie-based (httpOnly session cookie from the login
        # response); a bearer header is only attached when a token exists.
        if self.token:
            self.s.headers["Authorization"] = f"Bearer {self.token}"
        return body

    def call(self, step: str, method: str, path: str, **kw) -> dict:
        url = path if path.startswith("http") else f"{BACKEND}{path}"
        r = self.s.request(method, url, timeout=90, **kw)
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text[:500]}
        return self._record(step, {"method": method, "path": path, **({"json": kw.get("json")} if kw.get("json") else {})}, r, body)

    def submit_run(self, step: str, raw_note: str) -> dict:
        e = self.call(step, "POST", "/run", json={"raw_note": raw_note})
        return e["response"]

    def poll_run(self, step: str, run_id: str, timeout_s: int = 240) -> dict:
        deadline = time.time() + timeout_s
        last = {}
        while time.time() < deadline:
            e = self.call(step, "GET", f"/runs/{run_id}")
            last = e["response"]
            state = str(last.get("state") or last.get("status") or "")
            if state in {"completed", "blocked", "failed", "escalated", "done"}:
                return last
            time.sleep(3)
        return {"timeout": True, "last": last}

    def dump(self, sim: str) -> Path:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        out = EVIDENCE / f"sim3_{sim}_evidence.json"
        out.write_text(json.dumps(self.log, indent=2, ensure_ascii=False))
        return out


def shot(sim: str, name: str, url: str, out_name: str | None = None) -> str | None:
    """Playwright screenshot of a frontend URL. Best-effort; UI sims only."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[shot] playwright unavailable, skipping", name)
        return None
    out = ASSETS / f"{sim}_{out_name or name}.png"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        # Login via the BFF so the agency session cookie exists for protected routes.
        page.request.post(
            f"{FRONTEND}/api/auth/login",
            data=json.dumps({"email": TEST_USER, "password": TEST_PASSWORD}),
            headers={"content-type": "application/json"},
        )
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(out), full_page=False)
        browser.close()
    return str(out)


def shots_pass() -> None:
    """Capture the visual evidence for the results doc (reads evidence JSONs)."""
    def trip_of(sim: str, *steps: str) -> str | None:
        try:
            log = json.loads((EVIDENCE / f"sim3_{sim}_evidence.json").read_text())
        except FileNotFoundError:
            return None
        for e in log:
            if e.get("step") in steps:
                for src in (e.get("response") or {}, e.get("packet_summary") or {}, e.get("status") or {}):
                    tid = src.get("trip_id") if isinstance(src, dict) else None
                    if tid:
                        return tid
        return None

    a_trip = trip_of("A", "A2-run-status", "A1-packet")
    c_trip = trip_of("C", "C-seed", "C-trip-after-ghost")
    d_trip = trip_of("D", "D1-run", "D-trip-after-answers")
    print("trip ids:", {"A": a_trip, "C": c_trip, "D": d_trip})

    shot("UI", "overview", "http://localhost:3005/overview", "agency_overview")
    shot("UI", "inbox", "http://localhost:3005/inbox", "inbox_feed")
    shot("UI", "trips", "http://localhost:3005/trips", "leads_table")
    if a_trip:
        shot("UI", f"tripA_{a_trip}", f"http://localhost:3005/trips/{a_trip}", "packet_A_hinglish")
    if c_trip:
        shot("UI", f"tripC_{c_trip}", f"http://localhost:3005/trips/{c_trip}/decision", "decision_C_claim_card")
    if d_trip:
        shot("UI", f"tripD_{d_trip}", f"http://localhost:3005/trips/{d_trip}", "packet_D_accessibility")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default="all", choices=["A", "B", "C", "D", "all"])
    ap.add_argument("--skip-ui", action="store_true")
    ap.add_argument("--shots", action="store_true", help="capture UI screenshots only")
    args = ap.parse_args()
    ASSETS.mkdir(parents=True, exist_ok=True)

    if args.shots:
        shots_pass()
        return 0

    which = [args.sim] if args.sim != "all" else ["A", "B", "C", "D"]
    sys.path.insert(0, str(REPO))
    rc = 0
    for sim in which:
        mod = __import__("tools.sim3_sims", fromlist=[f"run_sim_{sim}"])
        fn = getattr(mod, f"run_sim_{sim}")
        print(f"=== SIM3-{sim} ===", flush=True)
        client = SimClient()
        try:
            fn(client, skip_ui=args.skip_ui)
        except Exception as exc:  # noqa: BLE001 — sims record failures as evidence
            print(f"SIM3-{sim} ERROR: {exc!r}")
            rc = 1
        finally:
            out = client.dump(sim)
            print(f"SIM3-{sim} evidence: {out} ({len(client.log)} steps)", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
