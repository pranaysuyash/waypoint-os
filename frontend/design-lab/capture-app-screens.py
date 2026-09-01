#!/usr/bin/env python3
"""
capture-app-screens.py — log into the running app and screenshot the real UI.

Purpose: ground design work in what actually shipped, not just DESIGN.md.
DESIGN.md is the spec; this is the evidence.

Prereqs:
  - spine_api on   http://127.0.0.1:8000
  - Next.js on     http://127.0.0.1:3001   (see --port)

Usage:
  python3 capture-app-screens.py                 # default routes
  python3 capture-app-screens.py --port 3001 -o ./shots

Notes:
  - --no-proxy-server is required: the sandbox sets HTTP_PROXY, which makes
    Chromium try to fetch localhost through the proxy and fail.
  - Auth is set by replaying the backend login response into the browser
    context (same pattern as the repo's capture_nav_screenshots.py).
"""
import argparse
import os
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

# Sandbox proxy breaks localhost; make sure Chromium goes direct.
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

API = "http://127.0.0.1:8000"
USER = os.environ.get("WP_USER", "newuser@test.com")
PASSWORD = os.environ.get("WP_PASSWORD", "testpass123")

DEFAULT_ROUTES = [
    ("landing", "/"),
    ("overview", "/overview"),
    ("inbox", "/inbox"),
    ("quotes", "/quotes"),
    ("settings", "/settings"),
]


def login(session):
    r = session.post(f"{API}/api/auth/login",
                     json={"email": USER, "password": PASSWORD}, timeout=20)
    r.raise_for_status()
    body = r.json()
    print(f"  logged in as {body['user']['email']} "
          f"({body['membership']['role']}) · agency {body['agency']['name']!r}")
    return body


def first_trip(session):
    """Find a real trip id so /trips/[id]/intake renders with data."""
    for url in (f"{API}/api/v1/trips", f"{API}/api/trips", f"{API}/api/v1/inbox"):
        try:
            r = session.get(url, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
        except Exception:
            continue
        items = data if isinstance(data, list) else (
            data.get("trips") or data.get("items") or data.get("results") or [])
        if items and isinstance(items[0], dict):
            tid = items[0].get("trip_id") or items[0].get("id")
            if tid:
                print(f"  found trip {tid} via {url}")
                return tid
    print("  no trip found — intake screenshot may render empty")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="3001")
    ap.add_argument("-o", "--out", default="./app-shots")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--full", action="store_true", help="full-page screenshots")
    args = ap.parse_args()

    base = f"http://127.0.0.1:{args.port}"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    try:
        login(session)
        trip = first_trip(session)
    except Exception as e:
        print(f"FATAL: login failed — {e}", file=sys.stderr)
        print("Is spine_api running on 127.0.0.1:8000?", file=sys.stderr)
        return 1

    routes = list(DEFAULT_ROUTES)
    if trip:
        routes.append(("trip-intake", f"/trips/{trip}/intake"))
        routes.append(("trip-workspace", f"/trips/{trip}"))

    cookies = [{"name": n, "value": v, "domain": "127.0.0.1", "path": "/"}
               for n, v in session.cookies.items()]

    # Playwright's bundled chromium may not be downloaded; fall back to any
    # Chrome/Chromium/Edge already on the machine.
    exe = None
    for cand in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ):
        if os.path.exists(cand):
            exe = cand
            print(f"  using browser: {cand}")
            break

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=exe,          # None → Playwright's own build
            args=["--no-proxy-server"],
        )
        ctx = browser.new_context(viewport={"width": args.width, "height": args.height})
        if cookies:
            ctx.add_cookies(cookies)
        page = ctx.new_page()

        for name, path in routes:
            url = base + path
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(1800)
                dest = out / f"{name}.png"
                page.screenshot(path=str(dest), full_page=args.full)
                print(f"  ✓ {name:<16} {url}")
            except Exception as e:
                print(f"  ✗ {name:<16} {url} — {str(e)[:90]}")

        browser.close()

    print(f"\nSaved to {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
